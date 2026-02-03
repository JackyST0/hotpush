"""
数据模型定义
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PushChannel(str, Enum):
    """推送渠道"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    WEBHOOK = "webhook"
    WECOM = "wecom"
    FEISHU = "feishu"
    DINGTALK = "dingtalk"


class HotItem(BaseModel):
    """热榜条目"""
    id: str
    title: str
    url: str
    hot_score: Optional[str] = None  # 热度值
    source: str  # 热榜源 ID
    published: Optional[datetime] = None
    description: Optional[str] = None
    image: Optional[str] = None


class HotList(BaseModel):
    """热榜列表"""
    source: str  # 热榜源 ID
    source_name: str
    items: List[HotItem]
    updated_at: datetime
    icon: Optional[str] = None


class PushConfig(BaseModel):
    """推送配置"""
    channel: PushChannel
    enabled: bool = True
    # 各渠道特定配置
    config: dict = {}


class Subscription(BaseModel):
    """用户订阅"""
    sources: List[str]  # 热榜源 ID 列表
    push_channels: List[PushConfig]
    keywords: List[str] = []  # 关键词过滤
    frequency: str = "realtime"  # realtime | hourly | daily
    quiet_hours: Optional[List[int]] = None  # 免打扰时段 [开始小时, 结束小时]


class PushMessage(BaseModel):
    """推送消息"""
    title: str
    content: str
    url: Optional[str] = None
    source: str  # 热榜源 ID
    items: List[HotItem] = []
