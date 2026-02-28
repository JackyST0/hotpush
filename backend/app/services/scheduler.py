"""
定时任务调度器
负责定时抓取热榜并推送，支持动态配置和状态管理
支持定时摘要功能
"""
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.config import settings
from app.services.rss_fetcher import rss_fetcher
from app.services.push_service import push_service
from app.services.database import db
from app.models.schemas import PushMessage, HotItem
from app.utils.sources import HOT_SOURCES
from app.services.config_service import config_service
from app.services.ai_service import ai_service
from app.utils.logger import logger


# 默认摘要配置
DEFAULT_DIGEST_CONFIG = {
    "enabled": False,
    "time": "08:00",  # 每天推送时间
    "sources": [],  # 空表示所有源
    "top_n": 10,  # 每个源取前 N 条
    "weekdays": [1, 2, 3, 4, 5, 6, 7]  # 每周哪几天推送，1=周一，7=周日
}


class SchedulerService:
    """调度器服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_paused = False
        self._last_run = None
        self._last_run_result = None
        self._last_digest_run = None
        self._last_digest_result = None

    def get_status(self) -> dict:
        """获取调度器状态"""
        job = self.scheduler.get_job("fetch_and_push")

        # 从数据库读取配置
        interval = self._get_interval()
        enabled_setting = db.get_setting("scheduler_enabled")
        enabled = enabled_setting != "0" if enabled_setting else True

        return {
            "running": self.scheduler.running and not self._is_paused,
            "paused": self._is_paused,
            "enabled": enabled,
            "interval_minutes": interval,
            "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "last_run_result": self._last_run_result
        }

    def _get_interval(self) -> int:
        """获取抓取间隔"""
        interval_setting = db.get_setting("fetch_interval")
        if interval_setting:
            try:
                return int(interval_setting)
            except ValueError:
                pass
        return settings.fetch_interval_minutes

    def update_interval(self, minutes: int):
        """更新抓取间隔"""
        job = self.scheduler.get_job("fetch_and_push")
        if job:
            self.scheduler.reschedule_job(
                "fetch_and_push",
                trigger=IntervalTrigger(minutes=minutes)
            )
            logger.info(f"抓取间隔已更新为 {minutes} 分钟")

    def pause(self):
        """暂停调度器"""
        job = self.scheduler.get_job("fetch_and_push")
        if job:
            job.pause()
            self._is_paused = True
            logger.info("调度器已暂停")

    def resume(self):
        """恢复调度器"""
        job = self.scheduler.get_job("fetch_and_push")
        if job:
            job.resume()
            self._is_paused = False
            logger.info("调度器已恢复")

    async def trigger_fetch(self):
        """手动触发一次抓取"""
        await self._fetch_and_push_job()

    # ===== 定时摘要相关方法 =====

    def get_digest_config(self) -> Dict[str, Any]:
        """获取摘要配置"""
        config_str = db.get_setting("digest_config")
        if config_str:
            try:
                return json.loads(config_str)
            except json.JSONDecodeError:
                pass
        return DEFAULT_DIGEST_CONFIG.copy()

    def set_digest_config(self, config: Dict[str, Any]):
        """设置摘要配置"""
        # 合并默认配置
        full_config = DEFAULT_DIGEST_CONFIG.copy()
        full_config.update(config)
        db.set_setting("digest_config", json.dumps(full_config))
        
        # 更新定时任务
        self._update_digest_job(full_config)
        logger.info(f"摘要配置已更新: {full_config}")

    def get_digest_status(self) -> dict:
        """获取摘要任务状态"""
        config = self.get_digest_config()
        job = self.scheduler.get_job("daily_digest")
        
        return {
            "enabled": config.get("enabled", False),
            "time": config.get("time", "08:00"),
            "sources": config.get("sources", []),
            "top_n": config.get("top_n", 10),
            "weekdays": config.get("weekdays", [1, 2, 3, 4, 5, 6, 7]),
            "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
            "last_run": self._last_digest_run.isoformat() if self._last_digest_run else None,
            "last_run_result": self._last_digest_result
        }

    def _update_digest_job(self, config: Dict[str, Any]):
        """更新摘要定时任务"""
        job_id = "daily_digest"
        
        # 先移除旧任务
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            self.scheduler.remove_job(job_id)
        
        if not config.get("enabled", False):
            logger.info("摘要任务已禁用")
            return
        
        # 解析时间
        time_str = config.get("time", "08:00")
        try:
            hour, minute = map(int, time_str.split(":"))
        except ValueError:
            hour, minute = 8, 0
        
        # 解析星期
        weekdays = config.get("weekdays", [1, 2, 3, 4, 5, 6, 7])
        if not weekdays:
            weekdays = [1, 2, 3, 4, 5, 6, 7]
        
        # APScheduler 使用 0-6 表示周一到周日
        cron_days = ",".join(str((d - 1) % 7) for d in weekdays)
        
        # 添加新任务
        self.scheduler.add_job(
            self._digest_job,
            trigger=CronTrigger(hour=hour, minute=minute, day_of_week=cron_days),
            id=job_id,
            name="每日热榜摘要",
            replace_existing=True
        )
        logger.info(f"摘要任务已设置: 每天 {time_str}，星期 {weekdays}")

    async def trigger_digest(self, is_test: bool = True):
        """手动触发一次摘要推送"""
        await self._digest_job(is_test=is_test)

    async def _digest_job(self, is_test: bool = False):
        """执行摘要推送任务
        
        Args:
            is_test: 是否为测试模式，测试模式下每个源只取2条，最多20条
        """
        logger.info(f"开始生成热榜摘要...{'（测试模式）' if is_test else ''}")
        self._last_digest_run = datetime.now()
        
        try:
            config = self.get_digest_config()
            
            # 定时任务才检查星期，手动触发不检查
            if not is_test:
                current_weekday = datetime.now().isoweekday()
                weekdays = config.get("weekdays", [1, 2, 3, 4, 5, 6, 7])
                if weekdays and current_weekday not in weekdays:
                    logger.info(f"今天是星期{current_weekday}，不在摘要推送日期内，跳过")
                    self._last_digest_result = {"success": True, "skipped": True, "reason": "not_in_weekdays"}
                    return
            
            # 检查推送渠道
            configured_channels = push_service.get_configured_channels()
            if not configured_channels:
                logger.warning("未配置任何推送渠道，跳过摘要推送")
                self._last_digest_result = {"success": False, "error": "no_channels"}
                return
            
            # 获取要包含的源
            source_filter = config.get("sources", [])
            # 测试模式：每个源只取2条；正式模式：按配置
            top_n = 2 if is_test else config.get("top_n", 10)
            
            # 抓取所有热榜
            hot_lists = await rss_fetcher.fetch_all_hot_lists(source_ids=list(HOT_SOURCES.keys()))
            
            # 过滤源
            if source_filter:
                hot_lists = [h for h in hot_lists if h.source in source_filter]
            
            if not hot_lists:
                logger.warning("没有可用的热榜数据")
                self._last_digest_result = {"success": False, "error": "no_data"}
                return
            
            # 尝试生成 AI 摘要
            ai_config = ai_service.get_config()
            ai_summary = None
            if ai_config.get("enabled"):
                style = ai_config.get("summary_style", "brief")
                ai_summary = await ai_service.generate_summary(hot_lists, style=style)
                if ai_summary:
                    logger.info("AI 摘要已生成，将附加到推送消息中")
                else:
                    logger.warning("AI 摘要生成失败，降级为普通摘要")

            # 构建摘要消息
            digest_items = []
            for hot_list in hot_lists:
                if hot_list.items:
                    for idx, item in enumerate(hot_list.items[:top_n]):
                        item_with_source = HotItem(
                            id=f"{hot_list.source}_{idx}",
                            title=f"[{hot_list.source_name}] {item.title}",
                            url=item.url,
                            hot_score=item.hot_score,
                            source=hot_list.source
                        )
                        digest_items.append(item_with_source)
            
            if not digest_items and not ai_summary:
                logger.warning("摘要内容为空")
                self._last_digest_result = {"success": False, "error": "empty_digest"}
                return
            
            # 构建推送消息
            today = datetime.now().strftime("%m月%d日")
            title_suffix = "（测试）" if is_test else ""
            title_prefix = "🤖 " if ai_summary else "📰 "
            message = PushMessage(
                title=f"{title_prefix}{today} 热榜摘要{title_suffix}",
                content=f"今日热榜汇总，共 {len(hot_lists)} 个来源",
                source="ai_digest" if ai_summary else "digest",
                items=digest_items,
                ai_summary=ai_summary,
            )
            
            # 推送
            results = await push_service.push_to_all(message)
            
            # 记录历史
            success_count = sum(1 for s in results.values() if s)
            for channel, success in results.items():
                db.add_push_history(
                    channel=channel,
                    source="digest",
                    title=message.title,
                    item_count=len(digest_items),
                    status="success" if success else "failed"
                )
            
            self._last_digest_result = {
                "success": True,
                "sources_count": len(hot_lists),
                "items_count": len(digest_items),
                "channels_success": success_count,
                "ai_summary": bool(ai_summary),
            }
            logger.info(f"摘要推送完成: {len(hot_lists)} 个源，{len(digest_items)} 条内容")
            
        except Exception as e:
            logger.error(f"摘要任务失败: {e}")
            self._last_digest_result = {"success": False, "error": str(e)}

    async def _fetch_and_push_job(self):
        """抓取热榜并推送新内容"""
        logger.info("开始抓取热榜...")
        self._last_run = datetime.now()

        try:
            # 检查是否有配置推送渠道
            configured_channels = push_service.get_configured_channels()
            if not configured_channels:
                logger.warning("未配置任何推送渠道，跳过推送")

            # 获取用户选择的推送数据源
            push_source_filter = config_service.get_push_sources()

            # 获取自定义数据源
            custom_sources = db.get_all_custom_sources()
            custom_source_ids = [s["id"] for s in custom_sources if s["enabled"]]

            # 确定要抓取的内置数据源
            builtin_source_ids = list(HOT_SOURCES.keys())
            if push_source_filter is not None:
                # 用户已配置数据源过滤，只抓取选中的内置源
                builtin_source_ids = [s for s in builtin_source_ids if s in push_source_filter]
                logger.info(f"推送数据源过滤：已选中 {len(builtin_source_ids)} 个内置源")

            # 合并内置和自定义数据源
            all_source_ids = builtin_source_ids + custom_source_ids

            # 抓取选中的热榜
            hot_lists = await rss_fetcher.fetch_all_hot_lists(source_ids=builtin_source_ids)

            # 抓取自定义数据源（同样受推送数据源选择限制）
            for custom in custom_sources:
                if custom["enabled"]:
                    # 如果用户配置了数据源过滤，检查自定义源是否被选中
                    if push_source_filter is not None and custom["id"] not in push_source_filter:
                        logger.debug(f"自定义源 {custom['name']} 未被选中，跳过")
                        continue
                    hot_list = await rss_fetcher.fetch_custom_source(custom)
                    if hot_list:
                        hot_lists.append(hot_list)

            # 获取推送规则
            rules = db.get_enabled_push_rules()

            total_new = 0
            total_pushed = 0
            
            # 收集所有更新内容，用于合并推送
            all_updates = []  # [(source_name, source, filtered_items, new_items)]

            for hot_list in hot_lists:
                # 检测新增内容
                new_items, is_first_fetch = rss_fetcher.get_new_items(hot_list.source, hot_list.items)

                if is_first_fetch:
                    logger.info(f"{hot_list.source_name}: 首次抓取，已缓存 {len(hot_list.items)} 条，跳过推送")
                    continue

                if new_items and configured_channels:
                    # 应用推送规则过滤
                    filtered_items = self._apply_rules(new_items, hot_list.source, rules)

                    if filtered_items:
                        logger.info(f"{hot_list.source_name} 有 {len(filtered_items)} 条新热点（过滤后）")
                        total_new += len(filtered_items)
                        # 收集更新，每个源最多取5条用于合并推送
                        all_updates.append((hot_list.source_name, hot_list.source, filtered_items[:5], new_items))
                else:
                    logger.debug(f"{hot_list.source_name}: {len(hot_list.items)} 条，无新增")
            
            # 合并推送：将所有更新合并成一条消息
            if all_updates and configured_channels:
                # 构建合并后的消息
                all_items = []
                source_names = []
                for source_name, source, items, _ in all_updates:
                    source_names.append(source_name)
                    for item in items:
                        # 给每个条目加上来源标识
                        all_items.append(HotItem(
                            id=item.id,
                            title=f"[{source_name}] {item.title}",
                            url=item.url,
                            hot_score=item.hot_score,
                            source=source
                        ))
                
                message = PushMessage(
                    title=f"🔥 热榜更新（{len(all_updates)} 个平台）",
                    content=f"来源：{', '.join(source_names)}",
                    source="combined",
                    items=all_items
                )
                
                # 推送到所有渠道
                results = await push_service.push_to_all(message)
                
                # 记录推送历史
                for channel, success in results.items():
                    db.add_push_history(
                        channel=channel,
                        source="combined",
                        title=message.title,
                        item_count=len(all_items),
                        status="success" if success else "failed"
                    )
                    if success:
                        total_pushed += 1
                
                logger.info(f"合并推送结果: {results}")
                
                # 标记所有已推送
                for _, source, _, new_items in all_updates:
                    rss_fetcher.mark_as_pushed(source, new_items)

            self._last_run_result = {
                "success": True,
                "sources_count": len(hot_lists),
                "new_items": total_new,
                "pushed_count": total_pushed
            }
            logger.info(f"抓取完成，共 {len(hot_lists)} 个源，{total_new} 条新内容")

        except Exception as e:
            logger.error(f"抓取任务失败: {e}")
            self._last_run_result = {
                "success": False,
                "error": str(e)
            }

    def _apply_rules(self, items: List[HotItem], source: str, rules: list) -> List[HotItem]:
        """应用推送规则过滤"""
        if not rules:
            return items

        filtered = items
        now = datetime.now()

        for rule in rules:
            rule_type = rule["rule_type"]
            config = rule["rule_config"]

            if rule_type == "keyword_include":
                # 只保留包含关键词的
                keywords = config.get("keywords", [])
                filtered = [
                    item for item in filtered
                    if any(kw.lower() in item.title.lower() for kw in keywords)
                ]

            elif rule_type == "keyword_exclude":
                # 排除包含关键词的
                keywords = config.get("keywords", [])
                filtered = [
                    item for item in filtered
                    if not any(kw.lower() in item.title.lower() for kw in keywords)
                ]

            elif rule_type == "time_range":
                # 时间段限制
                start_hour = config.get("start_hour", 0)
                end_hour = config.get("end_hour", 23)
                weekdays = config.get("weekdays", [])

                current_hour = now.hour
                current_weekday = now.isoweekday()  # 1=Monday, 7=Sunday

                # 检查星期
                if weekdays and current_weekday not in weekdays:
                    filtered = []
                    continue

                # 检查时间
                if start_hour <= end_hour:
                    if not (start_hour <= current_hour <= end_hour):
                        filtered = []
                else:
                    # 跨越午夜的情况
                    if not (current_hour >= start_hour or current_hour <= end_hour):
                        filtered = []

            elif rule_type == "source_filter":
                # 来源过滤
                sources_list = config.get("sources", [])
                mode = config.get("mode", "include")

                if mode == "include" and source not in sources_list:
                    filtered = []
                elif mode == "exclude" and source in sources_list:
                    filtered = []

        return filtered

    async def _cleanup_snapshots_job(self):
        """清理旧的快照数据"""
        try:
            db.cleanup_old_snapshots(days=7)
            logger.info("已清理 7 天前的快照数据")
        except Exception as e:
            logger.error(f"快照清理失败: {e}")

    def start(self):
        """启动定时任务"""
        interval = self._get_interval()

        # 检查是否应该启用
        enabled_setting = db.get_setting("scheduler_enabled")
        if enabled_setting == "0":
            self._is_paused = True

        # 添加定时任务
        self.scheduler.add_job(
            self._fetch_and_push_job,
            trigger=IntervalTrigger(minutes=interval),
            id="fetch_and_push",
            name="抓取热榜并推送",
            replace_existing=True
        )

        # 每日清理旧快照数据
        self.scheduler.add_job(
            self._cleanup_snapshots_job,
            trigger=CronTrigger(hour=3, minute=0),
            id="cleanup_snapshots",
            name="清理旧快照数据",
            replace_existing=True
        )

        # 启动调度器
        self.scheduler.start()

        if self._is_paused:
            self.pause()
            logger.info(f"定时任务已启动但暂停中，间隔 {interval} 分钟")
        else:
            logger.info(f"定时任务已启动，每 {interval} 分钟执行一次")

        # 初始化摘要任务
        digest_config = self.get_digest_config()
        if digest_config.get("enabled"):
            self._update_digest_job(digest_config)

    def stop(self):
        """停止定时任务"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("定时任务已停止")


# 全局实例
scheduler_service = SchedulerService()


# 兼容旧接口
def start_scheduler():
    scheduler_service.start()


def stop_scheduler():
    scheduler_service.stop()


async def run_once():
    await scheduler_service.trigger_fetch()
