"""
推送历史路由
查询推送历史记录
"""
from fastapi import APIRouter, Depends, Query

from app.services.database import db
from app.middleware.auth import require_auth, require_admin


router = APIRouter()


@router.get("")
async def get_push_history(
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    _: dict = Depends(require_auth)
):
    """获取推送历史"""
    history = db.get_push_history(limit=limit, offset=offset)
    total = db.get_push_history_count()

    return {
        "history": history,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.get("/stats")
async def get_push_stats(_: dict = Depends(require_auth)):
    """获取推送统计"""
    history = db.get_push_history(limit=1000)

    # 统计
    total = len(history)
    success = sum(1 for h in history if h["status"] == "success")
    failed = sum(1 for h in history if h["status"] == "failed")

    # 按渠道统计
    by_channel = {}
    for h in history:
        channel = h["channel"]
        if channel not in by_channel:
            by_channel[channel] = {"total": 0, "success": 0, "failed": 0}
        by_channel[channel]["total"] += 1
        if h["status"] == "success":
            by_channel[channel]["success"] += 1
        else:
            by_channel[channel]["failed"] += 1

    # 按来源统计
    by_source = {}
    for h in history:
        source = h["source"] or "unknown"
        if source not in by_source:
            by_source[source] = 0
        by_source[source] += h.get("item_count", 0)

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": round(success / total * 100, 1) if total > 0 else 0,
        "by_channel": by_channel,
        "by_source": by_source
    }


@router.delete("/cleanup")
async def cleanup_history(
    days: int = Query(30, ge=1, le=365, description="保留天数"),
    _: dict = Depends(require_admin)
):
    """清理旧的推送历史"""
    db.cleanup_push_history(days=days)
    return {"success": True, "message": f"已清理 {days} 天前的推送历史"}
