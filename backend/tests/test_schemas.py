"""
数据模型测试
"""
from datetime import datetime
from app.models.schemas import PushChannel, HotItem, HotList, PushMessage


class TestPushChannel:
    def test_channel_values(self):
        assert PushChannel.TELEGRAM == "telegram"
        assert PushChannel.DISCORD == "discord"
        assert PushChannel.EMAIL == "email"
        assert PushChannel.WEBHOOK == "webhook"
        assert PushChannel.WECOM == "wecom"
        assert PushChannel.FEISHU == "feishu"
        assert PushChannel.DINGTALK == "dingtalk"

    def test_channel_count(self):
        assert len(PushChannel) == 7


class TestHotItem:
    def test_create_hot_item(self):
        item = HotItem(
            id="test-1",
            title="测试热搜",
            url="https://example.com",
            source="weibo",
            hot_score="1000万"
        )
        assert item.id == "test-1"
        assert item.title == "测试热搜"
        assert item.source == "weibo"

    def test_hot_item_optional_fields(self):
        item = HotItem(id="1", title="test", url="https://example.com", source="zhihu")
        assert item.hot_score is None
        assert item.description is None
        assert item.image is None


class TestHotList:
    def test_create_hot_list(self):
        items = [
            HotItem(id="1", title="热搜1", url="https://example.com/1", source="weibo"),
            HotItem(id="2", title="热搜2", url="https://example.com/2", source="weibo"),
        ]
        hot_list = HotList(
            source="weibo",
            source_name="微博热搜",
            items=items,
            updated_at=datetime.now()
        )
        assert hot_list.source == "weibo"
        assert len(hot_list.items) == 2


class TestPushMessage:
    def test_create_push_message(self):
        msg = PushMessage(
            title="测试推送",
            content="这是测试内容",
            source="weibo"
        )
        assert msg.title == "测试推送"
        assert msg.items == []
        assert msg.url is None
