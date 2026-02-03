"""
API 路由
"""
import asyncio
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
from app.services.rss_fetcher import rss_fetcher
from app.services.push_service import push_service
from app.services.scheduler import run_once
from app.services.database import db
from app.services.cache import cache
from app.models.schemas import HotList, PushMessage, PushChannel
from app.utils.sources import HOT_SOURCES, CATEGORIES, get_sources_by_category

router = APIRouter()


@router.get("/sources")
async def get_sources():
    """获取所有支持的热榜源（包含内置和自定义）"""
    sources = []
    # 内置源
    for source_id, info in HOT_SOURCES.items():
        sources.append({
            "id": source_id,
            "name": info["name"],
            "category": info.get("category", "其他"),
            "icon": info.get("icon"),
            "type": "builtin"
        })
    # 自定义源
    custom_sources = db.get_all_custom_sources()
    for cs in custom_sources:
        if cs["enabled"]:
            sources.append({
                "id": cs["id"],
                "name": cs["name"],
                "category": cs.get("category", "自定义"),
                "icon": cs.get("icon"),
                "type": "custom"
            })
    return {"sources": sources}


@router.get("/categories")
async def get_categories():
    """获取所有分类"""
    result = {}
    for category, source_ids in CATEGORIES.items():
        result[category] = get_sources_by_category(category)
    return {"categories": result}


@router.get("/hot/stream")
async def stream_hot_lists(
    request: Request,
    sources: Optional[str] = None,
    category: Optional[str] = None
):
    """
    流式获取热榜列表（SSE）
    每获取到一个数据源就立即推送，不阻塞等待所有数据源
    """
    source_ids = None

    if sources:
        source_ids = [s.strip() for s in sources.split(",")]
    elif category:
        source_ids = CATEGORIES.get(category, [])

    if source_ids is None:
        # 获取所有源（内置 + 自定义）
        source_ids = list(HOT_SOURCES.keys())
        custom_sources = db.get_all_custom_sources()
        for cs in custom_sources:
            if cs["enabled"]:
                source_ids.append(cs["id"])

    async def event_generator():
        """SSE 事件生成器"""
        total = len(source_ids)
        completed = 0
        success = 0

        # 发送开始事件
        yield f"event: start\ndata: {json.dumps({'total': total})}\n\n"

        # 使用信号量限制并发
        semaphore = asyncio.Semaphore(5)

        async def fetch_and_yield(source_id: str):
            """获取单个源并返回结果"""
            nonlocal completed, success
            async with semaphore:
                # 检查客户端是否断开连接
                if await request.is_disconnected():
                    return None

                # 获取源名称
                source_name = source_id
                if source_id in HOT_SOURCES:
                    source_name = HOT_SOURCES[source_id].get("name", source_id)

                try:
                    # 先检查内置源
                    if source_id in HOT_SOURCES:
                        hot_list = await rss_fetcher.fetch_hot_list(source_id)
                    else:
                        # 检查自定义源
                        custom_source = db.get_custom_source(source_id)
                        if custom_source:
                            source_name = custom_source.get("name", source_id)
                            hot_list = await rss_fetcher.fetch_custom_source(custom_source)
                        else:
                            hot_list = None

                    completed += 1
                    if hot_list:
                        success += 1
                        return {"type": "success", "data": hot_list}
                    else:
                        return {"type": "failed", "source_id": source_id, "source_name": source_name}
                except Exception as e:
                    completed += 1
                    return {"type": "failed", "source_id": source_id, "source_name": source_name, "error": str(e)}

        # 创建所有任务
        tasks = [asyncio.create_task(fetch_and_yield(sid)) for sid in source_ids]

        # 使用 as_completed 按完成顺序处理
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                if result:
                    if result["type"] == "success":
                        hot_list = result["data"]
                        # 将 HotList 转换为 JSON
                        data = {
                            "source": hot_list.source,
                            "source_name": hot_list.source_name,
                            "icon": hot_list.icon,
                            "updated_at": hot_list.updated_at.isoformat() if hot_list.updated_at else None,
                            "items": [
                                {
                                    "id": item.id,
                                    "title": item.title,
                                    "url": item.url,
                                    "hot_score": item.hot_score,
                                    "source": item.source,
                                    "published": item.published.isoformat() if item.published else None,
                                    "description": item.description,
                                    "image": item.image
                                }
                                for item in hot_list.items
                            ]
                        }
                        yield f"event: hotlist\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                    elif result["type"] == "failed":
                        # 发送失败事件
                        yield f"event: failed\ndata: {json.dumps({'source_id': result['source_id'], 'source_name': result['source_name']}, ensure_ascii=False)}\n\n"

                # 发送进度更新
                yield f"event: progress\ndata: {json.dumps({'completed': completed, 'total': total, 'success': success})}\n\n"

            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

            # 检查客户端是否断开
            if await request.is_disconnected():
                break

        # 发送完成事件
        yield f"event: done\ndata: {json.dumps({'total': total, 'success': success})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
        }
    )


@router.get("/hot")
async def get_all_hot_lists(
    sources: Optional[str] = None,
    category: Optional[str] = None
):
    """
    获取热榜列表
    - sources: 逗号分隔的源ID列表，如 "weibo,zhihu,baidu"
    - category: 分类名称，如 "热搜榜"
    """
    source_ids = None

    if sources:
        source_ids = [s.strip() for s in sources.split(",")]
    elif category:
        source_ids = CATEGORIES.get(category, [])

    hot_lists = await rss_fetcher.fetch_all_hot_lists(source_ids)

    return {
        "count": len(hot_lists),
        "data": hot_lists
    }


@router.get("/hot/{source_id}", response_model=HotList)
async def get_hot_list(source_id: str):
    """获取指定源的热榜（支持内置和自定义源）"""
    # 先检查内置源
    if source_id in HOT_SOURCES:
        hot_list = await rss_fetcher.fetch_hot_list(source_id)
        if not hot_list:
            raise HTTPException(status_code=500, detail="获取热榜失败")
        return hot_list

    # 再检查自定义源
    custom_source = db.get_custom_source(source_id)
    if custom_source:
        hot_list = await rss_fetcher.fetch_custom_source(custom_source)
        if not hot_list:
            raise HTTPException(status_code=500, detail="获取热榜失败")
        return hot_list

    raise HTTPException(status_code=404, detail=f"未知的热榜源: {source_id}")


@router.get("/push/channels")
async def get_push_channels():
    """获取已配置的推送渠道"""
    configured = push_service.get_configured_channels()
    
    all_channels = [
        {"id": "telegram", "name": "Telegram", "configured": PushChannel.TELEGRAM in configured},
        {"id": "discord", "name": "Discord", "configured": PushChannel.DISCORD in configured},
        {"id": "wecom", "name": "企业微信", "configured": PushChannel.WECOM in configured},
        {"id": "feishu", "name": "飞书", "configured": PushChannel.FEISHU in configured},
        {"id": "dingtalk", "name": "钉钉", "configured": PushChannel.DINGTALK in configured},
        {"id": "email", "name": "邮件", "configured": False},  # TODO
        {"id": "webhook", "name": "Webhook", "configured": False},  # 需要用户配置
    ]
    
    return {"channels": all_channels}


@router.post("/push/test")
async def test_push(channel: str, message: str = "这是一条测试消息"):
    """测试推送"""
    try:
        channel_enum = PushChannel(channel)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的推送渠道: {channel}")
    
    push_message = PushMessage(
        title="HotPush 测试推送",
        content=message,
        source="test",
        items=[]
    )
    
    success = await push_service.push_to_channel(channel_enum, push_message)
    
    return {"success": success, "channel": channel}


@router.post("/fetch/trigger")
async def trigger_fetch(background_tasks: BackgroundTasks):
    """手动触发一次抓取"""
    background_tasks.add_task(run_once)
    return {"message": "抓取任务已触发，请查看日志"}


@router.get("/stats")
async def get_stats():
    """获取统计信息"""
    custom_sources = db.get_all_custom_sources()
    enabled_custom = len([s for s in custom_sources if s["enabled"]])
    return {
        "sources_count": len(HOT_SOURCES) + enabled_custom,
        "builtin_sources": len(HOT_SOURCES),
        "custom_sources": enabled_custom,
        "categories_count": len(CATEGORIES),
        "configured_channels": len(push_service.get_configured_channels()),
        "redis_enabled": cache.is_available(),
        "redis_stats": cache.get_stats() if cache.is_available() else {}
    }
