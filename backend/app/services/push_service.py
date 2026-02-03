"""
推送服务
支持多渠道推送：Telegram、Discord、Email、Webhook、企业微信、飞书、钉钉
支持从数据库读取配置，优先于环境变量配置
"""
import httpx
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from app.config import settings
from app.models.schemas import PushMessage, HotItem, PushChannel
from app.utils.logger import logger


def get_proxy_config() -> Optional[str]:
    """获取代理配置"""
    return settings.https_proxy or settings.http_proxy


class BasePusher(ABC):
    """推送器基类"""

    def __init__(self):
        self._config: Dict[str, Any] = {}

    def set_config(self, config: Dict[str, Any]):
        """设置配置"""
        self._config = config or {}

    @abstractmethod
    async def push(self, message: PushMessage) -> bool:
        """发送推送"""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """检查是否已配置"""
        pass


class TelegramPusher(BasePusher):
    """Telegram 推送"""

    @property
    def bot_token(self) -> Optional[str]:
        return self._config.get("bot_token") or settings.telegram_bot_token

    @property
    def chat_id(self) -> Optional[str]:
        return self._config.get("chat_id") or settings.telegram_chat_id

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def push(self, message: PushMessage) -> bool:
        if not self.is_configured():
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        # 格式化消息并分割
        texts = self._format_message(message)

        try:
            proxy = get_proxy_config()
            async with httpx.AsyncClient(proxy=proxy, timeout=30.0) as client:
                for text in texts:
                    response = await client.post(url, json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True
                    })
                    response.raise_for_status()
                logger.info(f"Telegram 推送成功，共 {len(texts)} 条消息")
                return True
        except Exception as e:
            logger.error(f"Telegram 推送失败: {e}")
            return False

    def _format_message(self, message: PushMessage) -> list:
        """格式化 Telegram 消息，返回消息列表（支持分割长消息）"""
        # 摘要和合并消息显示更多条目
        max_items = 50 if message.source in ["digest", "combined"] else 10
        items = message.items[:max_items]
        
        # Telegram 消息长度限制
        MAX_LENGTH = 4000
        
        messages = []
        current_lines = [f"<b>🔥 {message.title}</b>\n"]
        current_length = len(current_lines[0])
        
        # 合并推送和摘要：按平台分组显示
        if message.source in ["digest", "combined"]:
            # 按 source 分组
            from collections import OrderedDict
            grouped = OrderedDict()
            for item in items:
                if item.source not in grouped:
                    grouped[item.source] = []
                grouped[item.source].append(item)
            
            for source, source_items in grouped.items():
                # 从标题中提取平台名（格式：[平台名] 标题）
                platform_name = source
                if source_items and source_items[0].title.startswith("["):
                    end_idx = source_items[0].title.find("]")
                    if end_idx > 0:
                        platform_name = source_items[0].title[1:end_idx]
                
                # 添加平台标题
                section_header = f"\n<b>📌 {platform_name}</b>"
                if current_length + len(section_header) > MAX_LENGTH:
                    messages.append("\n".join(current_lines))
                    current_lines = [f"<b>🔥 {message.title}（续）</b>\n"]
                    current_length = len(current_lines[0])
                
                current_lines.append(section_header)
                current_length += len(section_header) + 1
                
                # 添加该平台的条目
                for i, item in enumerate(source_items, 1):
                    # 去掉标题中的 [平台名] 前缀
                    title = item.title
                    if title.startswith("[") and "]" in title:
                        title = title[title.find("]")+1:].strip()
                    title = title[:55] + "..." if len(title) > 55 else title
                    line = f"  {i}. <a href='{item.url}'>{title}</a>"
                    
                    if current_length + len(line) + 1 > MAX_LENGTH:
                        messages.append("\n".join(current_lines))
                        current_lines = [f"<b>🔥 {message.title}（续）</b>\n"]
                        current_length = len(current_lines[0])
                    
                    current_lines.append(line)
                    current_length += len(line) + 1
        else:
            # 普通消息格式
            for i, item in enumerate(items, 1):
                title = item.title[:60] + "..." if len(item.title) > 60 else item.title
                line = f"{i}. <a href='{item.url}'>{title}</a>"
                
                if current_length + len(line) + 1 > MAX_LENGTH:
                    messages.append("\n".join(current_lines))
                    current_lines = [f"<b>🔥 {message.title}（续）</b>\n"]
                    current_length = len(current_lines[0])
                
                current_lines.append(line)
                current_length += len(line) + 1
            
            if message.source not in ["digest", "combined"]:
                current_lines.append(f"\n📍 来源: {message.source}")
        
        messages.append("\n".join(current_lines))
        
        return messages


class DiscordPusher(BasePusher):
    """Discord Webhook 推送"""

    @property
    def webhook_url(self) -> Optional[str]:
        return self._config.get("webhook_url") or settings.discord_webhook_url

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def push(self, message: PushMessage) -> bool:
        if not self.is_configured():
            return False

        # 格式化为 Discord Embed
        embed = {
            "title": f"🔥 {message.title}",
            "description": self._format_items(message),
            "color": 16750592,  # 橙色
            "footer": {"text": f"来源: {message.source}"}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json={
                    "embeds": [embed]
                })
                response.raise_for_status()
                logger.info("Discord 推送成功")
                return True
        except Exception as e:
            logger.error(f"Discord 推送失败: {e}")
            return False

    def _format_items(self, message: PushMessage) -> str:
        max_items = 50 if message.source in ["digest", "combined"] else 10
        items = message.items[:max_items]
        
        lines = []
        
        # 合并推送：按平台分组显示
        if message.source in ["digest", "combined"]:
            from collections import OrderedDict
            grouped = OrderedDict()
            for item in items:
                if item.source not in grouped:
                    grouped[item.source] = []
                grouped[item.source].append(item)
            
            for source, source_items in grouped.items():
                platform_name = source
                if source_items and source_items[0].title.startswith("["):
                    end_idx = source_items[0].title.find("]")
                    if end_idx > 0:
                        platform_name = source_items[0].title[1:end_idx]
                
                lines.append(f"\n**📌 {platform_name}**")
                for i, item in enumerate(source_items, 1):
                    title = item.title
                    if title.startswith("[") and "]" in title:
                        title = title[title.find("]")+1:].strip()
                    title = title[:50] + "..." if len(title) > 50 else title
                    lines.append(f"{i}. [{title}]({item.url})")
        else:
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. [{item.title}]({item.url})")
        
        return "\n".join(lines)


class WeComPusher(BasePusher):
    """企业微信 Webhook 推送"""

    @property
    def webhook_url(self) -> Optional[str]:
        return self._config.get("webhook_url") or settings.wecom_webhook_url

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def push(self, message: PushMessage) -> bool:
        if not self.is_configured():
            return False

        # 格式化为 Markdown
        content = self._format_markdown(message)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json={
                    "msgtype": "markdown",
                    "markdown": {"content": content}
                })
                response.raise_for_status()
                logger.info("企业微信推送成功")
                return True
        except Exception as e:
            logger.error(f"企业微信推送失败: {e}")
            return False

    def _format_markdown(self, message: PushMessage) -> str:
        max_items = 50 if message.source in ["digest", "combined"] else 10
        items = message.items[:max_items]
        
        lines = [f"### 🔥 {message.title}\n"]
        
        # 合并推送：按平台分组显示
        if message.source in ["digest", "combined"]:
            from collections import OrderedDict
            grouped = OrderedDict()
            for item in items:
                if item.source not in grouped:
                    grouped[item.source] = []
                grouped[item.source].append(item)
            
            for source, source_items in grouped.items():
                platform_name = source
                if source_items and source_items[0].title.startswith("["):
                    end_idx = source_items[0].title.find("]")
                    if end_idx > 0:
                        platform_name = source_items[0].title[1:end_idx]
                
                lines.append(f"\n**📌 {platform_name}**\n")
                for i, item in enumerate(source_items, 1):
                    title = item.title
                    if title.startswith("[") and "]" in title:
                        title = title[title.find("]")+1:].strip()
                    title = title[:50] + "..." if len(title) > 50 else title
                    lines.append(f"{i}. [{title}]({item.url})")
        else:
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. [{item.title}]({item.url})")
            lines.append(f"\n> 来源: {message.source}")
        
        return "\n".join(lines)


class FeishuPusher(BasePusher):
    """飞书 Webhook 推送"""

    @property
    def webhook_url(self) -> Optional[str]:
        return self._config.get("webhook_url") or settings.feishu_webhook_url

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def push(self, message: PushMessage) -> bool:
        if not self.is_configured():
            return False

        # 飞书富文本消息
        content = self._build_content(message)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json={
                    "msg_type": "post",
                    "content": {
                        "post": {
                            "zh_cn": {
                                "title": message.title,
                                "content": content
                            }
                        }
                    }
                })
                response.raise_for_status()
                logger.info("飞书推送成功")
                return True
        except Exception as e:
            logger.error(f"飞书推送失败: {e}")
            return False

    def _build_content(self, message: PushMessage) -> list:
        max_items = 50 if message.source in ["digest", "combined"] else 10
        items = message.items[:max_items]
        
        content = []
        
        # 合并推送：按平台分组显示
        if message.source in ["digest", "combined"]:
            from collections import OrderedDict
            grouped = OrderedDict()
            for item in items:
                if item.source not in grouped:
                    grouped[item.source] = []
                grouped[item.source].append(item)
            
            for source, source_items in grouped.items():
                platform_name = source
                if source_items and source_items[0].title.startswith("["):
                    end_idx = source_items[0].title.find("]")
                    if end_idx > 0:
                        platform_name = source_items[0].title[1:end_idx]
                
                # 平台标题
                content.append([{"tag": "text", "text": f"\n📌 {platform_name}\n"}])
                
                # 该平台的条目
                for i, item in enumerate(source_items, 1):
                    title = item.title
                    if title.startswith("[") and "]" in title:
                        title = title[title.find("]")+1:].strip()
                    title = title[:50] + "..." if len(title) > 50 else title
                    content.append([
                        {"tag": "text", "text": f"{i}. "},
                        {"tag": "a", "text": title, "href": item.url},
                        {"tag": "text", "text": "\n"}
                    ])
        else:
            for i, item in enumerate(items, 1):
                content.append([
                    {"tag": "text", "text": f"{i}. "},
                    {"tag": "a", "text": item.title, "href": item.url},
                    {"tag": "text", "text": "\n"}
                ])
        
        return content


class DingTalkPusher(BasePusher):
    """钉钉 Webhook 推送"""

    @property
    def webhook_url(self) -> Optional[str]:
        return self._config.get("webhook_url") or settings.dingtalk_webhook_url

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def push(self, message: PushMessage) -> bool:
        if not self.is_configured():
            return False

        # 钉钉 Markdown 消息
        text = self._format_markdown(message)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json={
                    "msgtype": "markdown",
                    "markdown": {
                        "title": message.title,
                        "text": text
                    }
                })
                response.raise_for_status()
                logger.info("钉钉推送成功")
                return True
        except Exception as e:
            logger.error(f"钉钉推送失败: {e}")
            return False

    def _format_markdown(self, message: PushMessage) -> str:
        max_items = 50 if message.source in ["digest", "combined"] else 10
        items = message.items[:max_items]
        
        lines = [f"### 🔥 {message.title}\n"]
        
        # 合并推送：按平台分组显示
        if message.source in ["digest", "combined"]:
            from collections import OrderedDict
            grouped = OrderedDict()
            for item in items:
                if item.source not in grouped:
                    grouped[item.source] = []
                grouped[item.source].append(item)
            
            for source, source_items in grouped.items():
                # 从标题中提取平台名
                platform_name = source
                if source_items and source_items[0].title.startswith("["):
                    end_idx = source_items[0].title.find("]")
                    if end_idx > 0:
                        platform_name = source_items[0].title[1:end_idx]
                
                lines.append(f"\n**📌 {platform_name}**\n")
                for i, item in enumerate(source_items, 1):
                    title = item.title
                    if title.startswith("[") and "]" in title:
                        title = title[title.find("]")+1:].strip()
                    title = title[:50] + "..." if len(title) > 50 else title
                    lines.append(f"{i}. [{title}]({item.url})")
        else:
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. [{item.title}]({item.url})")
            lines.append(f"\n> 来源: {message.source}")
        
        return "\n".join(lines)


class WebhookPusher(BasePusher):
    """通用 Webhook 推送"""

    @property
    def webhook_url(self) -> Optional[str]:
        return self._config.get("webhook_url")

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def push(self, message: PushMessage) -> bool:
        if not self.is_configured():
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json={
                    "title": message.title,
                    "content": message.content,
                    "source": message.source,
                    "items": [item.model_dump() for item in message.items]
                })
                response.raise_for_status()
                logger.info("Webhook 推送成功")
                return True
        except Exception as e:
            logger.error(f"Webhook 推送失败: {e}")
            return False


class EmailPusher(BasePusher):
    """邮件推送"""

    @property
    def smtp_host(self) -> Optional[str]:
        return self._config.get("smtp_host")

    @property
    def smtp_port(self) -> Optional[int]:
        port = self._config.get("smtp_port")
        return int(port) if port else None

    @property
    def username(self) -> Optional[str]:
        return self._config.get("username")

    @property
    def password(self) -> Optional[str]:
        return self._config.get("password")

    @property
    def to_email(self) -> Optional[str]:
        return self._config.get("to_email")

    def is_configured(self) -> bool:
        return bool(self.smtp_host and self.username and self.password and self.to_email)

    async def push(self, message: PushMessage) -> bool:
        if not self.is_configured():
            return False

        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        try:
            # 构建邮件内容
            html_content = self._format_html(message)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🔥 {message.title}"
            msg["From"] = self.username
            msg["To"] = self.to_email

            # 添加 HTML 内容
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.username, self.to_email, msg.as_string())

            logger.info("邮件推送成功")
            return True
        except Exception as e:
            logger.error(f"邮件推送失败: {e}")
            return False

    def _format_source(self, source: str) -> str:
        """格式化来源名称为中文"""
        source_names = {
            "digest": "每日摘要",
            "test": "测试推送",
            "combined": "聚合推送",
            "weibo": "微博热搜",
            "zhihu": "知乎热榜",
            "bilibili": "B站热门",
            "douyin": "抖音热榜",
            "toutiao": "今日头条",
        }
        return source_names.get(source, source)

    def _format_html(self, message: PushMessage) -> str:
        """格式化 HTML 邮件"""
        # 摘要和合并消息显示更多条目
        max_items = 50 if message.source in ["digest", "combined"] else 10
        items = message.items[:max_items]

        content_html = ""
        
        # 合并推送：按平台分组显示
        if message.source in ["digest", "combined"]:
            from collections import OrderedDict
            grouped = OrderedDict()
            for item in items:
                if item.source not in grouped:
                    grouped[item.source] = []
                grouped[item.source].append(item)
            
            for source, source_items in grouped.items():
                # 从标题中提取平台名
                platform_name = source
                if source_items and source_items[0].title.startswith("["):
                    end_idx = source_items[0].title.find("]")
                    if end_idx > 0:
                        platform_name = source_items[0].title[1:end_idx]
                
                # 平台标题
                content_html += f'<h3 style="color: #d97706; margin: 20px 0 10px 0; padding-bottom: 8px; border-bottom: 2px solid #fef3c7; font-size: 16px;">📌 {platform_name}</h3>'
                content_html += '<ol style="padding-left: 20px; margin: 0 0 15px 0;">'
                
                for item in source_items:
                    # 去掉标题中的 [平台名] 前缀
                    title = item.title
                    if title.startswith("[") and "]" in title:
                        title = title[title.find("]")+1:].strip()
                    title = title[:70] + "..." if len(title) > 70 else title
                    content_html += f'<li style="margin-bottom: 8px;"><a href="{item.url}" style="color: #374151; text-decoration: none;">{title}</a></li>'
                
                content_html += '</ol>'
        else:
            # 普通消息格式
            content_html = '<ol style="padding-left: 20px; margin: 0;">'
            for item in items:
                title = item.title[:80] + "..." if len(item.title) > 80 else item.title
                content_html += f'<li style="margin-bottom: 8px;"><a href="{item.url}" style="color: #d97706; text-decoration: none;">{title}</a></li>'
            content_html += '</ol>'

        return f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background: linear-gradient(135deg, #f59e0b, #d97706); padding: 20px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🔥 {message.title}</h1>
            </div>
            <div style="background: white; padding: 20px; border-radius: 0 0 12px 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                {content_html}
                <p style="color: #888; font-size: 12px; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
                    📍 来源: {self._format_source(message.source)} | 由 HotPush 推送
                </p>
            </div>
        </body>
        </html>
        """


class PushService:
    """推送服务管理器"""

    def __init__(self):
        self.pushers: Dict[PushChannel, BasePusher] = {
            PushChannel.TELEGRAM: TelegramPusher(),
            PushChannel.DISCORD: DiscordPusher(),
            PushChannel.WECOM: WeComPusher(),
            PushChannel.FEISHU: FeishuPusher(),
            PushChannel.DINGTALK: DingTalkPusher(),
            PushChannel.WEBHOOK: WebhookPusher(),
            PushChannel.EMAIL: EmailPusher(),
        }
        # 初始化时加载配置
        self._load_config()

    def _load_config(self):
        """从数据库加载配置"""
        try:
            from app.services.config_service import config_service

            for channel_id, pusher in self.pushers.items():
                config = config_service.get_push_channel_config(channel_id.value)
                if config and config.get("enabled"):
                    pusher.set_config(config.get("config", {}))
                else:
                    pusher.set_config({})
        except Exception as e:
            # 如果加载失败，使用环境变量配置
            logger.warning(f"加载推送配置失败，使用环境变量配置: {e}")

    def refresh_config(self):
        """刷新配置（配置更新后调用）"""
        self._load_config()
        logger.info("推送配置已刷新")

    def get_configured_channels(self) -> List[PushChannel]:
        """获取已配置的推送渠道"""
        return [
            channel for channel, pusher in self.pushers.items()
            if pusher.is_configured()
        ]

    async def push_to_channel(self, channel: PushChannel, message: PushMessage) -> bool:
        """推送到指定渠道"""
        pusher = self.pushers.get(channel)
        if pusher and pusher.is_configured():
            return await pusher.push(message)
        return False

    async def push_to_all(self, message: PushMessage) -> dict:
        """推送到所有已配置的渠道"""
        results = {}
        for channel in self.get_configured_channels():
            results[channel.value] = await self.push_to_channel(channel, message)
        return results


# 全局实例
push_service = PushService()
