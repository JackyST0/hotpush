"""
推送服务测试
"""
from app.models.schemas import PushChannel
from app.services.push_service import (
    PushService,
    TelegramPusher,
    DiscordPusher,
    EmailPusher,
    WebhookPusher,
    WeComPusher,
    FeishuPusher,
    DingTalkPusher,
)


class TestPushServiceInit:
    def test_all_channels_registered(self):
        service = PushService()
        assert PushChannel.TELEGRAM in service.pushers
        assert PushChannel.DISCORD in service.pushers
        assert PushChannel.EMAIL in service.pushers
        assert PushChannel.WEBHOOK in service.pushers
        assert PushChannel.WECOM in service.pushers
        assert PushChannel.FEISHU in service.pushers
        assert PushChannel.DINGTALK in service.pushers

    def test_pusher_types(self):
        service = PushService()
        assert isinstance(service.pushers[PushChannel.TELEGRAM], TelegramPusher)
        assert isinstance(service.pushers[PushChannel.DISCORD], DiscordPusher)
        assert isinstance(service.pushers[PushChannel.EMAIL], EmailPusher)
        assert isinstance(service.pushers[PushChannel.WEBHOOK], WebhookPusher)
        assert isinstance(service.pushers[PushChannel.WECOM], WeComPusher)
        assert isinstance(service.pushers[PushChannel.FEISHU], FeishuPusher)
        assert isinstance(service.pushers[PushChannel.DINGTALK], DingTalkPusher)


class TestPusherConfiguration:
    def test_unconfigured_telegram(self):
        pusher = TelegramPusher()
        assert pusher.is_configured() is False

    def test_configured_telegram(self):
        pusher = TelegramPusher()
        pusher.set_config({"bot_token": "123:ABC", "chat_id": "456"})
        assert pusher.is_configured() is True

    def test_unconfigured_discord(self):
        pusher = DiscordPusher()
        assert pusher.is_configured() is False

    def test_unconfigured_email(self):
        pusher = EmailPusher()
        assert pusher.is_configured() is False

    def test_get_configured_channels_empty(self):
        service = PushService()
        configured = service.get_configured_channels()
        for ch in configured:
            assert service.pushers[ch].is_configured() is True
