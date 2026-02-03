"""
配置文件
"""
import secrets
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    app_name: str = "HotPush"
    debug: bool = True

    # 用户认证配置
    admin_username: str = "admin"  # 管理员用户名
    admin_password: Optional[str] = None  # 管理员密码，必须设置才能启用认证
    jwt_secret: str = secrets.token_urlsafe(32)  # JWT 密钥
    jwt_expire_hours: int = 24  # Token 有效期（小时）

    # RSSHub 实例配置
    # 主实例地址，建议自建实例以获得最佳稳定性
    rsshub_url: str = "https://rsshub.rssforever.com"

    # 备用实例列表（逗号分隔），当主实例失败时自动切换
    rsshub_fallback_urls: str = "https://rsshub.feeded.xyz,https://hub.slarker.me"

    # 抓取配置
    fetch_interval_minutes: int = 5  # 抓取间隔（分钟）
    fetch_timeout: int = 30  # 请求超时（秒）
    fetch_retry_count: int = 2  # 失败重试次数

    @property
    def rsshub_instances(self) -> List[str]:
        """获取所有 RSSHub 实例列表（主实例 + 备用实例）"""
        instances = [self.rsshub_url]
        if self.rsshub_fallback_urls:
            fallbacks = [u.strip() for u in self.rsshub_fallback_urls.split(",") if u.strip()]
            instances.extend(fallbacks)
        return instances
    
    # 数据库配置
    # MySQL: mysql://user:password@host:3306/dbname
    database_url: str = "mysql://root:123456@localhost:3306/hotpush"

    # MySQL 连接池配置
    db_pool_size: int = 5
    db_pool_recycle: int = 3600
    
    # Redis 配置
    redis_url: Optional[str] = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300  # 热榜缓存时间（秒）
    
    # 推送渠道配置
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    discord_webhook_url: Optional[str] = None
    
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from: Optional[str] = None
    
    # 企业微信配置
    wecom_webhook_url: Optional[str] = None
    
    # 飞书配置
    feishu_webhook_url: Optional[str] = None
    
    # 钉钉配置
    dingtalk_webhook_url: Optional[str] = None
    
    # 代理配置（用于访问 Telegram 等需要代理的服务）
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
