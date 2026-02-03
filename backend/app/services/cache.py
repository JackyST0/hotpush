"""
Redis 缓存服务
用于热榜数据缓存和推送去重
"""
import json
import redis
from typing import Optional, List, Dict, Any, Set
from datetime import timedelta

from app.config import settings


class CacheService:
    """Redis 缓存服务"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.enabled = False
        self._connect()
    
    def _connect(self):
        """连接 Redis"""
        if not settings.redis_url:
            print("Redis URL not configured, cache disabled")
            return
        
        try:
            self.client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # 测试连接
            self.client.ping()
            self.enabled = True
            print(f"Redis connected: {settings.redis_url}")
        except Exception as e:
            print(f"Redis connection failed: {e}, cache disabled")
            self.client = None
            self.enabled = False
    
    def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        return self.enabled and self.client is not None
    
    # ===== 热榜缓存 =====
    
    def get_hotlist(self, source: str) -> Optional[Dict[str, Any]]:
        """获取缓存的热榜数据"""
        if not self.is_available():
            return None
        
        try:
            key = f"hotlist:{source}"
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get hotlist error: {e}")
            return None
    
    def set_hotlist(self, source: str, data: Dict[str, Any], ttl: int = 300):
        """缓存热榜数据（默认 5 分钟）"""
        if not self.is_available():
            return
        
        try:
            key = f"hotlist:{source}"
            self.client.setex(key, ttl, json.dumps(data, ensure_ascii=False))
        except Exception as e:
            print(f"Redis set hotlist error: {e}")
    
    def delete_hotlist(self, source: str):
        """删除热榜缓存"""
        if not self.is_available():
            return
        
        try:
            key = f"hotlist:{source}"
            self.client.delete(key)
        except Exception as e:
            print(f"Redis delete hotlist error: {e}")
    
    def clear_all_hotlists(self):
        """清除所有热榜缓存"""
        if not self.is_available():
            return
        
        try:
            keys = self.client.keys("hotlist:*")
            if keys:
                self.client.delete(*keys)
        except Exception as e:
            print(f"Redis clear hotlists error: {e}")
    
    # ===== 推送去重 =====
    
    def is_item_pushed(self, source: str, item_id: str) -> bool:
        """检查条目是否已推送"""
        if not self.is_available():
            return False
        
        try:
            key = f"pushed:{source}"
            return self.client.sismember(key, item_id)
        except Exception as e:
            print(f"Redis check pushed error: {e}")
            return False
    
    def mark_items_pushed(self, source: str, item_ids: List[str], ttl: int = 86400 * 7):
        """标记条目为已推送（默认保留 7 天）"""
        if not self.is_available() or not item_ids:
            return
        
        try:
            key = f"pushed:{source}"
            self.client.sadd(key, *item_ids)
            self.client.expire(key, ttl)
        except Exception as e:
            print(f"Redis mark pushed error: {e}")
    
    def get_pushed_item_ids(self, source: str) -> Set[str]:
        """获取已推送的条目 ID 集合"""
        if not self.is_available():
            return set()
        
        try:
            key = f"pushed:{source}"
            return self.client.smembers(key)
        except Exception as e:
            print(f"Redis get pushed ids error: {e}")
            return set()
    
    # ===== 抓取锁 =====
    
    def acquire_fetch_lock(self, source: str, ttl: int = 60) -> bool:
        """获取抓取锁，防止并发抓取同一源"""
        if not self.is_available():
            return True  # Redis 不可用时默认允许
        
        try:
            key = f"fetch_lock:{source}"
            return self.client.set(key, "1", nx=True, ex=ttl)
        except Exception as e:
            print(f"Redis acquire lock error: {e}")
            return True
    
    def release_fetch_lock(self, source: str):
        """释放抓取锁"""
        if not self.is_available():
            return
        
        try:
            key = f"fetch_lock:{source}"
            self.client.delete(key)
        except Exception as e:
            print(f"Redis release lock error: {e}")
    
    # ===== 统计信息 =====
    
    def incr_fetch_count(self, source: str):
        """增加抓取次数计数"""
        if not self.is_available():
            return
        
        try:
            key = f"stats:fetch:{source}"
            self.client.incr(key)
            # 设置过期时间为 24 小时
            self.client.expire(key, 86400)
        except Exception as e:
            print(f"Redis incr fetch count error: {e}")
    
    def incr_push_count(self, channel: str):
        """增加推送次数计数"""
        if not self.is_available():
            return
        
        try:
            key = f"stats:push:{channel}"
            self.client.incr(key)
            self.client.expire(key, 86400)
        except Exception as e:
            print(f"Redis incr push count error: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        if not self.is_available():
            return {}
        
        try:
            stats = {}
            # 获取抓取统计
            fetch_keys = self.client.keys("stats:fetch:*")
            for key in fetch_keys:
                source = key.replace("stats:fetch:", "")
                stats[f"fetch_{source}"] = int(self.client.get(key) or 0)
            
            # 获取推送统计
            push_keys = self.client.keys("stats:push:*")
            for key in push_keys:
                channel = key.replace("stats:push:", "")
                stats[f"push_{channel}"] = int(self.client.get(key) or 0)
            
            return stats
        except Exception as e:
            print(f"Redis get stats error: {e}")
            return {}


# 全局实例
cache = CacheService()
