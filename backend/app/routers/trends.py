"""
趋势分析路由
提供热搜排名趋势和统计数据
"""
from fastapi import APIRouter
from app.services.database import db
from app.utils.sources import HOT_SOURCES, get_source_info

router = APIRouter()


@router.get("/ranking/{source_id}")
async def get_ranking_trend(source_id: str, hours: int = 24):
    """获取指定平台的排名趋势数据"""
    source_info = get_source_info(source_id)
    source_name = source_info.get("name", source_id) if source_info else source_id

    data = db.get_trend_data(source_id, hours=hours)

    time_points = sorted(set(d["snapshot_time"] for d in data))
    items_map = {}
    for d in data:
        key = d["item_id"]
        if key not in items_map:
            items_map[key] = {"item_id": key, "title": d["title"], "ranks": {}}
        items_map[key]["ranks"][d["snapshot_time"]] = d["rank"]

    items = sorted(items_map.values(), key=lambda x: min(x["ranks"].values()))[:15]

    return {
        "source": source_id,
        "source_name": source_name,
        "hours": hours,
        "time_points": time_points,
        "items": [
            {
                "item_id": item["item_id"],
                "title": item["title"],
                "ranks": [item["ranks"].get(t) for t in time_points]
            }
            for item in items
        ]
    }


@router.get("/item/{item_id}")
async def get_item_trend(item_id: str, hours: int = 24):
    """获取指定热搜条目的排名趋势"""
    data = db.get_item_trend(item_id, hours=hours)
    return {"item_id": item_id, "hours": hours, "data": data}


@router.get("/overview")
async def get_overview(hours: int = 24):
    """获取各平台热搜数量统计概览"""
    stats = db.get_platform_stats(hours=hours)

    for item in stats:
        source_info = get_source_info(item["source"])
        item["source_name"] = source_info.get("name", item["source"]) if source_info else item["source"]
        item["icon"] = source_info.get("icon", "") if source_info else ""

    return {"hours": hours, "platforms": stats}


@router.get("/top")
async def get_top_items(hours: int = 24, limit: int = 20):
    """获取热度最高的条目"""
    items = db.get_trending_items(hours=hours, limit=limit)

    for item in items:
        source_info = get_source_info(item["source"])
        item["source_name"] = source_info.get("name", item["source"]) if source_info else item["source"]

    return {"hours": hours, "items": items}
