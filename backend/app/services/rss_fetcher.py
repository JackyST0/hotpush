"""
RSS 抓取服务
负责从 RSSHub 获取热榜数据
"""
import asyncio
import hashlib
from datetime import datetime
from typing import Optional, List, Tuple
import httpx
import feedparser
from app.config import settings
from app.models.schemas import HotItem, HotList
from app.utils.sources import HOT_SOURCES, get_source_info
from app.services.database import db
from app.services.cache import cache
from app.utils.logger import logger


class RSSFetcher:
    """RSS 抓取器"""

    # 请求头，模拟浏览器
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    def __init__(self):
        self.instances = [u.rstrip('/') for u in settings.rsshub_instances]
        self.timeout = settings.fetch_timeout
        self.retry_count = settings.fetch_retry_count

    async def _fetch_from_instance(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        route: str,
        source_name: str = ""
    ) -> Optional[feedparser.FeedParserDict]:
        """从单个实例获取 Feed"""
        url = f"{base_url}{route}"
        try:
            response = await client.get(url, headers=self.HEADERS)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            if feed.entries:
                return feed
            return None
        except httpx.HTTPStatusError as e:
            # 静默处理，在上层统一输出
            return None
        except Exception as e:
            # 静默处理，在上层统一输出
            return None

    async def fetch_feed(self, route: str, source_name: str = "") -> Optional[feedparser.FeedParserDict]:
        """
        获取 RSS Feed（支持多实例容错）

        依次尝试所有配置的 RSSHub 实例，直到成功获取数据
        如果 route 是完整 URL（以 http:// 或 https:// 开头），则直接请求
        """
        display_name = source_name or route
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 如果是完整 URL，直接请求
            if route.startswith("http://") or route.startswith("https://"):
                try:
                    response = await client.get(route, headers=self.HEADERS)
                    response.raise_for_status()
                    feed = feedparser.parse(response.text)
                    if feed.entries:
                        return feed, route
                except Exception:
                    pass
                return None, None

            # 否则使用 RSSHub 实例
            for instance in self.instances:
                feed = await self._fetch_from_instance(client, instance, route, source_name)
                if feed:
                    return feed, instance  # 返回 feed 和成功的实例

            # 所有实例都失败
            return None, None

    async def fetch_custom_source(self, source_config: dict) -> Optional[HotList]:
        """获取自定义数据源"""
        source_id = source_config.get("id")
        source_name = source_config.get("name", source_id)
        url = source_config.get("url")

        if not url:
            logger.warning(f"自定义源 {source_id} 没有配置 URL")
            return None

        result = await self.fetch_feed(url, source_name)

        if isinstance(result, tuple):
            feed, instance = result
        else:
            feed, instance = result, None

        if not feed or not feed.entries:
            logger.error(f"[{source_name}] 获取失败")
            return None

        logger.info(f"[{source_name}] 获取成功，共 {len(feed.entries)} 条")

        items = []
        for entry in feed.entries[:50]:
            item_id = hashlib.md5(
                f"{source_id}:{entry.get('link', entry.get('title', ''))}".encode()
            ).hexdigest()[:12]

            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])

            item = HotItem(
                id=item_id,
                title=entry.get('title', ''),
                url=entry.get('link', ''),
                hot_score=None,
                source=source_id,
                published=published,
                description=entry.get('summary', '')[:200] if entry.get('summary') else None,
                image=self._extract_image(entry)
            )
            items.append(item)

        return HotList(
            source=source_id,
            source_name=source_name,
            items=items,
            updated_at=datetime.now(),
            icon=source_config.get("icon")
        )

    async def fetch_hot_list(self, source_id: str, use_cache: bool = True) -> Optional[HotList]:
        """获取指定源的热榜"""
        source_info = get_source_info(source_id)
        if not source_info:
            logger.warning(f"未知的源: {source_id}")
            return None

        source_name = source_info.get("name", source_id)
        
        # 尝试从 Redis 缓存获取
        if use_cache and cache.is_available():
            cached_data = cache.get_hotlist(source_id)
            if cached_data:
                logger.debug(f"[{source_name}] 命中缓存")
                # 从缓存重建 HotList 对象
                items = [HotItem(**item) for item in cached_data.get("items", [])]
                return HotList(
                    source=cached_data.get("source"),
                    source_name=cached_data.get("source_name"),
                    items=items,
                    updated_at=datetime.fromisoformat(cached_data.get("updated_at")) if cached_data.get("updated_at") else datetime.now(),
                    icon=cached_data.get("icon")
                )
        
        route = source_info.get("route")
        result = await self.fetch_feed(route, source_name)

        # 处理返回值
        if isinstance(result, tuple):
            feed, instance = result
        else:
            feed, instance = result, None

        if not feed or not feed.entries:
            logger.error(f"[{source_name}] 获取失败")
            return None

        logger.info(f"[{source_name}] 获取成功，共 {len(feed.entries)} 条")
        
        # 更新抓取统计
        cache.incr_fetch_count(source_id)

        items = []
        for entry in feed.entries[:50]:  # 最多取50条
            # 生成唯一 ID
            item_id = hashlib.md5(
                f"{source_id}:{entry.get('link', entry.get('title', ''))}".encode()
            ).hexdigest()[:12]

            # 解析发布时间
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])

            # 提取热度（如果有）
            hot_score = None
            if hasattr(entry, 'slash_comments'):
                hot_score = entry.slash_comments

            item = HotItem(
                id=item_id,
                title=entry.get('title', ''),
                url=entry.get('link', ''),
                hot_score=hot_score,
                source=source_id,
                published=published,
                description=entry.get('summary', '')[:200] if entry.get('summary') else None,
                image=self._extract_image(entry)
            )
            items.append(item)

        hot_list = HotList(
            source=source_id,
            source_name=source_info.get("name", source_id),
            items=items,
            updated_at=datetime.now(),
            icon=source_info.get("icon")
        )
        
        # 写入 Redis 缓存
        if cache.is_available():
            cache_data = {
                "source": hot_list.source,
                "source_name": hot_list.source_name,
                "items": [item.model_dump() for item in hot_list.items],
                "updated_at": hot_list.updated_at.isoformat() if hot_list.updated_at else None,
                "icon": hot_list.icon
            }
            cache.set_hotlist(source_id, cache_data, ttl=settings.redis_cache_ttl)
        
        return hot_list

    def _extract_image(self, entry) -> Optional[str]:
        """从 RSS entry 中提取图片"""
        # 尝试从 media_content 提取
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if media.get('type', '').startswith('image'):
                    return media.get('url')

        # 尝试从 enclosures 提取
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href') or enc.get('url')

        return None

    async def fetch_all_hot_lists(
        self,
        source_ids: List[str] = None,
        concurrency: int = 5
    ) -> List[HotList]:
        """
        批量并发获取热榜

        Args:
            source_ids: 要抓取的源 ID 列表，为 None 时抓取全部
            concurrency: 并发数限制，避免请求过多被限流

        Returns:
            成功获取的热榜列表
        """
        if source_ids is None:
            source_ids = list(HOT_SOURCES.keys())

        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_with_limit(source_id: str) -> Optional[HotList]:
            async with semaphore:
                return await self.fetch_hot_list(source_id)

        # 并发执行所有抓取任务
        tasks = [fetch_with_limit(sid) for sid in source_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤成功的结果
        hot_lists = []
        for result in results:
            if isinstance(result, HotList):
                hot_lists.append(result)
            elif isinstance(result, Exception):
                logger.error(f"抓取异常: {result}")

        return hot_lists

    def get_new_items(self, source_id: str, items: List[HotItem]) -> Tuple[List[HotItem], bool]:
        """
        检测新增条目（优先使用 Redis，MySQL 作为备份）

        Returns:
            Tuple[List[HotItem], bool]: (新增条目列表, 是否为首次抓取)
        """
        # 检查是否首次抓取该源
        is_first = db.is_first_fetch(source_id)

        # 获取已推送的 ID（优先从 Redis 获取，否则从 MySQL）
        if cache.is_available():
            pushed_ids = cache.get_pushed_item_ids(source_id)
            # 如果 Redis 为空但不是首次抓取，从 MySQL 加载
            if not pushed_ids and not is_first:
                pushed_ids = db.get_pushed_item_ids(source_id)
                # 同步到 Redis
                if pushed_ids:
                    cache.mark_items_pushed(source_id, list(pushed_ids))
        else:
            pushed_ids = db.get_pushed_item_ids(source_id)

        new_items = []
        for item in items:
            if item.id not in pushed_ids:
                new_items.append(item)

        # 记录本次抓取
        db.record_fetch(source_id, len(items))

        # 首次抓取时，将所有条目标记为已推送（避免全量推送）
        if is_first and items:
            self.mark_as_pushed(source_id, items)
            return [], True

        return new_items, False

    def mark_as_pushed(self, source_id: str, items: List[HotItem]):
        """将条目标记为已推送（同时写入 Redis 和 MySQL）"""
        if not items:
            return
        
        # 写入 MySQL（持久化）
        db.mark_items_pushed(source_id, items)
        
        # 写入 Redis（快速查询）
        if cache.is_available():
            item_ids = [item.id for item in items]
            cache.mark_items_pushed(source_id, item_ids)


# 全局实例
rss_fetcher = RSSFetcher()
