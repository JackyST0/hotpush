"""
数据源配置测试
"""
from app.utils.sources import HOT_SOURCES, get_source_info


class TestHotSources:
    def test_sources_not_empty(self):
        assert len(HOT_SOURCES) > 0

    def test_all_sources_have_required_fields(self):
        required_fields = {"name", "route", "icon", "category"}
        for source_id, source in HOT_SOURCES.items():
            missing = required_fields - set(source.keys())
            assert not missing, f"Source '{source_id}' missing fields: {missing}"

    def test_all_routes_are_valid(self):
        for source_id, source in HOT_SOURCES.items():
            route = source["route"]
            assert route.startswith("/") or route.startswith("http"), \
                f"Source '{source_id}' route should be a path or URL"

    def test_known_sources_exist(self):
        expected = ["weibo", "zhihu", "bilibili", "v2ex", "hackernews"]
        for source_id in expected:
            assert source_id in HOT_SOURCES, f"Expected source '{source_id}' not found"


class TestGetSourceInfo:
    def test_get_existing_source(self):
        info = get_source_info("weibo")
        assert info is not None
        assert info["name"] == "微博热搜"

    def test_get_nonexistent_source(self):
        info = get_source_info("nonexistent_source_xyz")
        assert info == {}
