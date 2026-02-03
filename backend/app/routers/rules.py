"""
推送规则路由
处理推送规则的 CRUD 操作
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.database import db
from app.middleware.auth import require_auth, require_admin


router = APIRouter()


# ===== 规则类型说明 =====
# keyword_include: 包含关键词才推送
# keyword_exclude: 排除包含关键词的内容
# time_range: 仅在指定时间段推送
# source_filter: 仅推送指定来源


# ===== 请求/响应模型 =====

class PushRuleCreate(BaseModel):
    """创建推送规则"""
    name: str
    rule_type: str  # keyword_include, keyword_exclude, time_range, source_filter
    rule_config: Dict[str, Any]
    enabled: bool = True


class PushRuleUpdate(BaseModel):
    """更新推送规则"""
    name: Optional[str] = None
    rule_type: Optional[str] = None
    rule_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


# ===== API 端点 =====

@router.get("")
async def get_push_rules(_: dict = Depends(require_auth)):
    """获取所有推送规则"""
    rules = db.get_all_push_rules()
    return {"rules": rules, "count": len(rules)}


@router.get("/types")
async def get_rule_types(_: dict = Depends(require_auth)):
    """获取支持的规则类型"""
    return {
        "types": [
            {
                "id": "keyword_include",
                "name": "关键词包含",
                "description": "只有标题包含指定关键词的内容才会推送",
                "config_schema": {
                    "keywords": {"type": "array", "description": "关键词列表，满足任一即可"}
                }
            },
            {
                "id": "keyword_exclude",
                "name": "关键词排除",
                "description": "标题包含指定关键词的内容不会推送",
                "config_schema": {
                    "keywords": {"type": "array", "description": "要排除的关键词列表"}
                }
            },
            {
                "id": "time_range",
                "name": "时间段限制",
                "description": "只在指定时间段内推送",
                "config_schema": {
                    "start_hour": {"type": "integer", "description": "开始小时 (0-23)"},
                    "end_hour": {"type": "integer", "description": "结束小时 (0-23)"},
                    "weekdays": {"type": "array", "description": "星期几 (1-7, 1=周一)，为空则每天"}
                }
            },
            {
                "id": "source_filter",
                "name": "来源过滤",
                "description": "只推送指定来源的内容",
                "config_schema": {
                    "sources": {"type": "array", "description": "数据源 ID 列表"},
                    "mode": {"type": "string", "description": "include=只推送这些, exclude=排除这些"}
                }
            }
        ]
    }


@router.post("")
async def create_push_rule(
    rule: PushRuleCreate,
    _: dict = Depends(require_admin)
):
    """创建推送规则"""
    # 验证规则类型
    valid_types = ["keyword_include", "keyword_exclude", "time_range", "source_filter"]
    if rule.rule_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的规则类型: {rule.rule_type}")

    # 验证规则配置
    _validate_rule_config(rule.rule_type, rule.rule_config)

    # 保存规则
    rule_id = db.save_push_rule(
        name=rule.name,
        rule_type=rule.rule_type,
        rule_config=rule.rule_config,
        enabled=rule.enabled
    )

    return {
        "success": True,
        "message": f"规则 {rule.name} 创建成功",
        "rule_id": rule_id
    }


@router.put("/{rule_id}")
async def update_push_rule(
    rule_id: int,
    rule: PushRuleUpdate,
    _: dict = Depends(require_admin)
):
    """更新推送规则"""
    existing = db.get_push_rule(rule_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"规则 {rule_id} 不存在")

    # 合并更新
    name = rule.name if rule.name else existing["name"]
    rule_type = rule.rule_type if rule.rule_type else existing["rule_type"]
    rule_config = rule.rule_config if rule.rule_config else existing["rule_config"]
    enabled = rule.enabled if rule.enabled is not None else existing["enabled"]

    # 验证规则配置
    _validate_rule_config(rule_type, rule_config)

    db.save_push_rule(name, rule_type, rule_config, enabled, rule_id)

    return {"success": True, "message": f"规则 {name} 更新成功"}


@router.delete("/{rule_id}")
async def delete_push_rule(
    rule_id: int,
    _: dict = Depends(require_admin)
):
    """删除推送规则"""
    existing = db.get_push_rule(rule_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"规则 {rule_id} 不存在")

    db.delete_push_rule(rule_id)
    return {"success": True, "message": f"规则 {existing['name']} 已删除"}


def _validate_rule_config(rule_type: str, config: Dict[str, Any]):
    """验证规则配置"""
    if rule_type == "keyword_include" or rule_type == "keyword_exclude":
        if "keywords" not in config or not isinstance(config["keywords"], list):
            raise HTTPException(status_code=400, detail="关键词规则需要 keywords 数组")
        if not config["keywords"]:
            raise HTTPException(status_code=400, detail="关键词列表不能为空")

    elif rule_type == "time_range":
        if "start_hour" not in config or "end_hour" not in config:
            raise HTTPException(status_code=400, detail="时间段规则需要 start_hour 和 end_hour")
        start = config["start_hour"]
        end = config["end_hour"]
        if not (0 <= start <= 23 and 0 <= end <= 23):
            raise HTTPException(status_code=400, detail="小时必须在 0-23 之间")

    elif rule_type == "source_filter":
        if "sources" not in config or not isinstance(config["sources"], list):
            raise HTTPException(status_code=400, detail="来源过滤规则需要 sources 数组")
        if "mode" not in config or config["mode"] not in ["include", "exclude"]:
            raise HTTPException(status_code=400, detail="mode 必须是 include 或 exclude")
