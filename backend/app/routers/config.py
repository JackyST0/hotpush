"""
配置管理路由
处理推送渠道配置
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from app.services.config_service import config_service
from app.services.push_service import push_service
from app.models.schemas import PushMessage, PushChannel
from app.middleware.auth import require_auth, require_admin


router = APIRouter()


# ===== 请求/响应模型 =====

class PushChannelConfig(BaseModel):
    """推送渠道配置"""
    enabled: bool
    config: Dict[str, Any]


class TestPushRequest(BaseModel):
    """测试推送请求"""
    message: str = "这是一条测试消息"


# ===== 系统设置 API =====

@router.get("/settings")
async def get_settings(_: dict = Depends(require_auth)):
    """获取所有系统设置"""
    return {"settings": config_service.get_all_settings()}


@router.put("/settings")
async def update_settings(
    settings_data: Dict[str, str],
    _: dict = Depends(require_admin)
):
    """更新系统设置"""
    for key, value in settings_data.items():
        config_service.set_setting(key, value)
    return {"success": True, "message": "设置已更新"}


# ===== 推送渠道配置 API =====

@router.get("/push")
async def get_push_channels(_: dict = Depends(require_auth)):
    """获取所有推送渠道配置"""
    channels = config_service.get_all_push_channels()

    # 对敏感配置进行脱敏处理
    for channel in channels:
        if channel.get("config"):
            channel["config"] = _mask_push_config(channel["id"], channel["config"])

    return {"channels": channels}


def _mask_push_config(channel_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """对推送配置进行脱敏处理"""
    masked = {}
    for key, value in config.items():
        if isinstance(value, str) and len(value) > 10:
            # 脱敏敏感字段
            if key in ["bot_token", "webhook_url", "password"]:
                masked[key] = value[:6] + "..." + value[-4:]
            else:
                masked[key] = value
        else:
            masked[key] = value
    return masked


@router.get("/push/{channel_id}")
async def get_push_channel(
    channel_id: str,
    _: dict = Depends(require_auth)
):
    """获取指定推送渠道配置"""
    channel = config_service.get_push_channel_config(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail=f"未找到渠道: {channel_id}")

    # 脱敏处理
    if channel.get("config"):
        channel["config"] = _mask_push_config(channel_id, channel["config"])

    return channel


@router.put("/push/{channel_id}")
async def update_push_channel(
    channel_id: str,
    channel_config: PushChannelConfig,
    _: dict = Depends(require_admin)
):
    """更新推送渠道配置"""
    # 验证渠道 ID
    if channel_id not in config_service.PUSH_CHANNEL_NAMES:
        raise HTTPException(status_code=400, detail=f"无效的渠道 ID: {channel_id}")

    # 验证必要的配置项
    config = channel_config.config
    
    # 处理脱敏密码：如果密码包含 "..."，说明是脱敏后的值，需要保留原密码
    existing_config = config_service.get_push_channel_config(channel_id)
    if existing_config and existing_config.get("config"):
        old_config = existing_config["config"]
        sensitive_fields = ["password", "bot_token", "webhook_url"]
        for field in sensitive_fields:
            if field in config and "..." in str(config.get(field, "")):
                # 使用原来的值
                if field in old_config:
                    config[field] = old_config[field]
    
    # 只有启用时才验证必填字段
    if channel_config.enabled:
        if channel_id == "telegram":
            if not config.get("bot_token") or not config.get("chat_id"):
                raise HTTPException(
                    status_code=400,
                    detail="Telegram 需要配置 bot_token 和 chat_id"
                )
        elif channel_id == "email":
            if not config.get("username") or not config.get("password") or not config.get("to_email"):
                raise HTTPException(
                    status_code=400,
                    detail="邮件需要配置用户名、密码和收件人邮箱"
                )
        elif channel_id in ["discord", "wecom", "feishu", "dingtalk"]:
            if not config.get("webhook_url"):
                raise HTTPException(
                    status_code=400,
                    detail=f"{channel_id} 需要配置 webhook_url"
                )

    # 保存配置
    config_service.save_push_channel(channel_id, channel_config.enabled, config)

    # 通知推送服务刷新配置
    push_service.refresh_config()

    return {"success": True, "message": f"{channel_id} 配置已更新"}


@router.delete("/push/{channel_id}")
async def delete_push_channel(
    channel_id: str,
    _: dict = Depends(require_admin)
):
    """删除推送渠道配置（恢复使用环境变量）"""
    config_service.delete_push_channel(channel_id)
    push_service.refresh_config()
    return {"success": True, "message": f"{channel_id} 配置已删除，将使用环境变量配置"}


@router.post("/push/{channel_id}/test")
async def test_push_channel(
    channel_id: str,
    request: TestPushRequest = TestPushRequest(),
    _: dict = Depends(require_admin)
):
    """测试推送渠道"""
    # 验证渠道是否配置
    if not config_service.is_push_channel_configured(channel_id):
        raise HTTPException(status_code=400, detail=f"渠道 {channel_id} 未配置或未启用")

    # 发送测试消息
    try:
        channel_enum = PushChannel(channel_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的推送渠道: {channel_id}")

    push_message = PushMessage(
        title="HotPush 测试推送",
        content=request.message,
        source="test",
        items=[]
    )

    success = await push_service.push_to_channel(channel_enum, push_message)

    return {"success": success, "channel": channel_id}
