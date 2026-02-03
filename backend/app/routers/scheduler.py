"""
调度器管理路由
查看和控制定时任务
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List

from app.services.scheduler import scheduler_service
from app.services.database import db
from app.middleware.auth import require_auth, require_admin


router = APIRouter()


class SchedulerConfigUpdate(BaseModel):
    """更新调度器配置"""
    fetch_interval: Optional[int] = None  # 抓取间隔（分钟）
    enabled: Optional[bool] = None


class DigestConfigUpdate(BaseModel):
    """更新摘要配置"""
    enabled: Optional[bool] = None
    time: Optional[str] = None  # 推送时间，格式 HH:MM
    sources: Optional[List[str]] = None  # 包含的源，空表示所有
    top_n: Optional[int] = None  # 每个源取前 N 条
    weekdays: Optional[List[int]] = None  # 推送星期，1-7


@router.get("/status")
async def get_scheduler_status(_: dict = Depends(require_auth)):
    """获取调度器状态"""
    status = scheduler_service.get_status()
    return status


@router.post("/trigger")
async def trigger_fetch(_: dict = Depends(require_admin)):
    """手动触发一次抓取"""
    try:
        await scheduler_service.trigger_fetch()
        return {"success": True, "message": "抓取任务已触发"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")


@router.put("/config")
async def update_scheduler_config(
    config: SchedulerConfigUpdate,
    _: dict = Depends(require_admin)
):
    """更新调度器配置"""
    if config.fetch_interval is not None:
        if config.fetch_interval < 1 or config.fetch_interval > 1440:
            raise HTTPException(status_code=400, detail="抓取间隔必须在 1-1440 分钟之间")
        db.set_setting("fetch_interval", str(config.fetch_interval))
        scheduler_service.update_interval(config.fetch_interval)

    if config.enabled is not None:
        db.set_setting("scheduler_enabled", "1" if config.enabled else "0")
        if config.enabled:
            scheduler_service.resume()
        else:
            scheduler_service.pause()

    return {"success": True, "message": "调度器配置已更新"}


@router.post("/pause")
async def pause_scheduler(_: dict = Depends(require_admin)):
    """暂停调度器"""
    scheduler_service.pause()
    db.set_setting("scheduler_enabled", "0")
    return {"success": True, "message": "调度器已暂停"}


@router.post("/resume")
async def resume_scheduler(_: dict = Depends(require_admin)):
    """恢复调度器"""
    scheduler_service.resume()
    db.set_setting("scheduler_enabled", "1")
    return {"success": True, "message": "调度器已恢复"}


# ===== 定时摘要相关接口 =====

@router.get("/digest")
async def get_digest_status(_: dict = Depends(require_auth)):
    """获取摘要任务状态和配置"""
    return scheduler_service.get_digest_status()


@router.put("/digest")
async def update_digest_config(
    config: DigestConfigUpdate,
    _: dict = Depends(require_admin)
):
    """更新摘要配置"""
    current_config = scheduler_service.get_digest_config()
    
    # 合并更新
    if config.enabled is not None:
        current_config["enabled"] = config.enabled
    if config.time is not None:
        # 验证时间格式
        try:
            parts = config.time.split(":")
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
            current_config["time"] = config.time
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="时间格式错误，应为 HH:MM")
    if config.sources is not None:
        current_config["sources"] = config.sources
    if config.top_n is not None:
        if config.top_n < 1 or config.top_n > 50:
            raise HTTPException(status_code=400, detail="top_n 必须在 1-50 之间")
        current_config["top_n"] = config.top_n
    if config.weekdays is not None:
        if not all(1 <= d <= 7 for d in config.weekdays):
            raise HTTPException(status_code=400, detail="weekdays 必须是 1-7 的数字")
        current_config["weekdays"] = config.weekdays
    
    scheduler_service.set_digest_config(current_config)
    return {"success": True, "message": "摘要配置已更新", "config": current_config}


@router.post("/digest/trigger")
async def trigger_digest(_: dict = Depends(require_admin)):
    """手动触发一次摘要推送"""
    try:
        await scheduler_service.trigger_digest()
        result = scheduler_service.get_digest_status()
        return {"success": True, "message": "摘要推送已触发", "result": result.get("last_run_result")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")
