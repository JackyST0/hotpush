"""
配置管理服务
统一管理配置读写，支持数据库配置优先于环境变量配置
"""
from typing import Optional, Dict, Any, List
from app.services.database import db
from app.config import settings


class ConfigService:
    """配置服务 - 统一管理所有配置的读写"""

    # 推送渠道名称映射
    PUSH_CHANNEL_NAMES = {
        "telegram": "Telegram",
        "discord": "Discord",
        "wecom": "企业微信",
        "feishu": "飞书",
        "dingtalk": "钉钉",
        "email": "邮件",
        "webhook": "Webhook"
    }

    # ===== 系统设置 =====

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """获取系统设置"""
        value = db.get_setting(key)
        return value if value is not None else default

    def set_setting(self, key: str, value: str):
        """设置系统设置"""
        db.set_setting(key, value)

    def get_all_settings(self) -> Dict[str, str]:
        """获取所有系统设置"""
        return db.get_all_settings()

    # ===== 推送渠道配置 =====

    def get_push_channel_config(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        获取推送渠道配置
        优先从数据库读取，如果没有则尝试从环境变量读取
        """
        # 先从数据库读取
        db_config = db.get_push_channel(channel_id)
        if db_config:
            return db_config

        # 回退到环境变量
        env_config = self._get_env_push_config(channel_id)
        if env_config:
            return {
                "id": channel_id,
                "name": self.PUSH_CHANNEL_NAMES.get(channel_id, channel_id),
                "enabled": True,
                "config": env_config
            }

        return None

    def _get_env_push_config(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """从环境变量读取推送配置"""
        if channel_id == "telegram":
            if settings.telegram_bot_token and settings.telegram_chat_id:
                return {
                    "bot_token": settings.telegram_bot_token,
                    "chat_id": settings.telegram_chat_id
                }
        elif channel_id == "discord":
            if settings.discord_webhook_url:
                return {"webhook_url": settings.discord_webhook_url}
        elif channel_id == "wecom":
            if settings.wecom_webhook_url:
                return {"webhook_url": settings.wecom_webhook_url}
        elif channel_id == "feishu":
            if settings.feishu_webhook_url:
                return {"webhook_url": settings.feishu_webhook_url}
        elif channel_id == "dingtalk":
            if settings.dingtalk_webhook_url:
                return {"webhook_url": settings.dingtalk_webhook_url}
        return None

    def get_all_push_channels(self) -> List[Dict[str, Any]]:
        """获取所有推送渠道配置（合并数据库和环境变量）"""
        # 从数据库获取
        db_channels = {c["id"]: c for c in db.get_all_push_channels()}

        # 合并环境变量配置
        all_channels = []
        for channel_id, name in self.PUSH_CHANNEL_NAMES.items():
            if channel_id in db_channels:
                all_channels.append(db_channels[channel_id])
            else:
                env_config = self._get_env_push_config(channel_id)
                all_channels.append({
                    "id": channel_id,
                    "name": name,
                    "enabled": bool(env_config),
                    "config": env_config or {},
                    "from_env": bool(env_config)
                })

        return all_channels

    def save_push_channel(self, channel_id: str, enabled: bool, config: Dict[str, Any]):
        """保存推送渠道配置"""
        name = self.PUSH_CHANNEL_NAMES.get(channel_id, channel_id)
        db.save_push_channel(channel_id, name, enabled, config)

    def delete_push_channel(self, channel_id: str):
        """删除推送渠道配置（恢复使用环境变量）"""
        db.delete_push_channel(channel_id)

    def is_push_channel_configured(self, channel_id: str) -> bool:
        """检查推送渠道是否已配置"""
        config = self.get_push_channel_config(channel_id)
        if not config:
            return False
        if not config.get("enabled"):
            return False

        # 检查必要的配置项
        channel_config = config.get("config", {})
        if channel_id == "telegram":
            return bool(channel_config.get("bot_token") and channel_config.get("chat_id"))
        elif channel_id in ["discord", "wecom", "feishu", "dingtalk", "webhook"]:
            return bool(channel_config.get("webhook_url"))
        elif channel_id == "email":
            return bool(channel_config.get("smtp_host") and channel_config.get("to_email"))
        return False


# 全局实例
config_service = ConfigService()
