"""
数据源管理路由
处理自定义数据源的 CRUD 操作
"""
import re
import httpx
import feedparser
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, List

from app.services.database import db
from app.middleware.auth import require_auth, require_admin
from app.utils.sources import HOT_SOURCES


router = APIRouter()


# ===== 请求/响应模型 =====

class CustomSourceCreate(BaseModel):
    """创建自定义数据源"""
    name: str
    url: str
    category: str = "自定义"
    icon: Optional[str] = None

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('名称不能为空')
        return v.strip()

    @field_validator('url')
    @classmethod
    def url_valid(cls, v):
        if not v or not v.strip():
            raise ValueError('URL 不能为空')
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL 必须以 http:// 或 https:// 开头')
        return v.strip()


class CustomSourceUpdate(BaseModel):
    """更新自定义数据源"""
    name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    enabled: Optional[bool] = None


class SourceValidateRequest(BaseModel):
    """验证 RSS 源请求"""
    url: str


# ===== API 端点 =====

@router.get("/custom")
async def get_custom_sources(_: dict = Depends(require_auth)):
    """获取所有自定义数据源"""
    sources = db.get_all_custom_sources()
    return {"sources": sources, "count": len(sources)}


@router.post("/custom")
async def create_custom_source(
    source: CustomSourceCreate,
    _: dict = Depends(require_admin)
):
    """创建自定义数据源"""
    # 生成 ID（基于名称）
    source_id = f"custom_{re.sub(r'[^a-zA-Z0-9]', '_', source.name.lower())}"

    # 检查是否已存在
    existing = db.get_custom_source(source_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"数据源 {source.name} 已存在")

    # 检查是否与内置源冲突
    if source_id in HOT_SOURCES:
        raise HTTPException(status_code=400, detail=f"与内置数据源冲突")

    # 验证 RSS 有效性
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(source.url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; HotPush/1.0)"
            })
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            if not feed.entries:
                raise HTTPException(status_code=400, detail="无法解析 RSS 内容或内容为空")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"无法访问 RSS 源: {str(e)}")

    # 保存到数据库
    db.save_custom_source(
        source_id=source_id,
        name=source.name,
        url=source.url,
        category=source.category,
        icon=source.icon,
        enabled=True
    )

    return {
        "success": True,
        "message": f"数据源 {source.name} 创建成功",
        "source_id": source_id
    }


@router.put("/custom/{source_id}")
async def update_custom_source(
    source_id: str,
    source: CustomSourceUpdate,
    _: dict = Depends(require_admin)
):
    """更新自定义数据源"""
    existing = db.get_custom_source(source_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"数据源 {source_id} 不存在")

    # 更新字段
    name = source.name if source.name else existing["name"]
    url = source.url if source.url else existing["url"]
    category = source.category if source.category else existing["category"]
    icon = source.icon if source.icon is not None else existing["icon"]
    enabled = source.enabled if source.enabled is not None else existing["enabled"]

    db.save_custom_source(source_id, name, url, category, icon, enabled)

    return {"success": True, "message": f"数据源 {name} 更新成功"}


@router.delete("/custom/{source_id}")
async def delete_custom_source(
    source_id: str,
    _: dict = Depends(require_admin)
):
    """删除自定义数据源"""
    existing = db.get_custom_source(source_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"数据源 {source_id} 不存在")

    db.delete_custom_source(source_id)
    return {"success": True, "message": f"数据源 {existing['name']} 已删除"}


@router.post("/validate")
async def validate_rss_source(
    request: SourceValidateRequest,
    _: dict = Depends(require_auth)
):
    """验证 RSS 源是否有效"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(request.url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; HotPush/1.0)"
            })
            response.raise_for_status()
            feed = feedparser.parse(response.text)

            if not feed.entries:
                return {
                    "valid": False,
                    "message": "无法解析 RSS 内容或内容为空"
                }

            return {
                "valid": True,
                "title": feed.feed.get("title", "未知"),
                "description": feed.feed.get("description", ""),
                "item_count": len(feed.entries),
                "sample_items": [
                    {"title": entry.get("title", ""), "url": entry.get("link", "")}
                    for entry in feed.entries[:3]
                ]
            }
    except httpx.HTTPError as e:
        return {
            "valid": False,
            "message": f"无法访问 RSS 源: {str(e)}"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"验证失败: {str(e)}"
        }
