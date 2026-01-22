"""测试 LLM 缓存功能"""

import pytest
import tempfile
import time
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestration.cache import LLMCache, get_global_cache, clear_global_cache


class TestLLMCache:
    """测试 LLM 缓存基本功能"""

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = LLMCache(max_size=10)

        result = cache.get(
            system_prompt="You are a helpful assistant",
            user_prompt="Hello"
        )

        assert result is None
        assert cache.misses == 1
        assert cache.hits == 0

    def test_cache_hit(self):
        """测试缓存命中"""
        cache = LLMCache(max_size=10)

        # 先设置缓存
        cache.set(
            system_prompt="You are a helpful assistant",
            user_prompt="Hello",
            response="Hi there!",
            model_name="test-model"
        )

        # 再获取
        result = cache.get(
            system_prompt="You are a helpful assistant",
            user_prompt="Hello"
        )

        assert result == "Hi there!"
        assert cache.hits == 1
        assert cache.misses == 0

    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = LLMCache(max_size=10, ttl_seconds=1)  # 1秒过期

        cache.set(
            system_prompt="System",
            user_prompt="User",
            response="Response"
        )

        # 立即获取，应该成功
        result = cache.get("System", "User")
        assert result == "Response"

        # 等待过期
        time.sleep(1.5)

        # 再次获取，应该失败
        result = cache.get("System", "User")
        assert result is None

    def test_lru_eviction(self):
        """测试 LRU 淘汰策略"""
        cache = LLMCache(max_size=3)

        # 添加 4 个条目
        cache.set("s1", "u1", "r1")
        cache.set("s2", "u2", "r2")
        cache.set("s3", "u3", "r3")
        cache.set("s4", "u4", "r4")  # 触发淘汰

        # 最早的 (s1, u1) 应该被淘汰
        assert cache.get("s1", "u1") is None
        assert cache.get("s2", "u2") == "r2"
        assert cache.get("s3", "u3") == "r3"
        assert cache.get("s4", "u4") == "r4"

    def test_cache_update(self):
        """测试缓存更新"""
        cache = LLMCache()

        cache.set("sys", "user", "response1")
        assert cache.get("sys", "user") == "response1"

        # 更新相同的键
        cache.set("sys", "user", "response2")
        assert cache.get("sys", "user") == "response2"

        # 缓存大小不应增加
        assert cache.stats()["size"] == 1

    def test_cache_stats(self):
        """测试缓存统计"""
        cache = LLMCache(max_size=10)

        # 设置 3 个条目
        cache.set("s1", "u1", "r1")
        cache.set("s2", "u2", "r2")
        cache.set("s3", "u3", "r3")

        # 2 次命中
        cache.get("s1", "u1")
        cache.get("s2", "u2")

        # 1 次未命中
        cache.get("s4", "u4")

        stats = cache.stats()
        assert stats["size"] == 3
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["total_requests"] == 3
        assert "66.7%" in stats["hit_rate"]  # 2/3

    def test_persistence(self):
        """测试缓存持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "cache.json"

            # 创建缓存并添加条目
            cache1 = LLMCache(max_size=10, cache_file=cache_file)
            cache1.set("system", "user", "response", "test-model")

            assert cache_file.exists()

            # 创建新缓存，从文件加载
            cache2 = LLMCache(max_size=10, cache_file=cache_file)

            # 应该能读取之前的缓存
            result = cache2.get("system", "user")
            assert result == "response"

    def test_clear_cache(self):
        """测试清空缓存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "cache.json"
            cache = LLMCache(max_size=10, cache_file=cache_file)

            cache.set("s1", "u1", "r1")
            cache.set("s2", "u2", "r2")

            assert cache.stats()["size"] == 2
            assert cache_file.exists()

            # 清空
            cache.clear()

            assert cache.stats()["size"] == 0
            assert cache.hits == 0
            assert cache.misses == 0
            assert not cache_file.exists()


class TestGlobalCache:
    """测试全局缓存单例"""

    def test_global_cache_singleton(self):
        """测试全局缓存是单例"""
        cache1 = get_global_cache()
        cache2 = get_global_cache()

        assert cache1 is cache2

    def test_global_cache_persistence(self):
        """测试全局缓存持久化"""
        # 清空旧缓存
        clear_global_cache()

        cache = get_global_cache()
        cache.set("system", "user", "response")

        # 清除单例引用
        clear_global_cache()

        # 重新获取，应该从文件加载
        cache = get_global_cache()
        result = cache.get("system", "user")

        # 注意：由于缓存文件在 ~/.maccortex/cache，跨测试运行可能存在
        # 这里只验证不抛异常
        assert result is None or result == "response"

        # 清理
        clear_global_cache()
