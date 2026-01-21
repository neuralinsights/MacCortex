"""
翻译缓存工具（Phase 3 Backend 优化）

功能：
- LRU Cache（最近最少使用缓存）
- 自动淘汰旧条目
- 缓存命中率统计
"""

import hashlib
import time
from collections import OrderedDict
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


class TranslationCache:
    """
    翻译结果缓存（LRU 策略）

    特性：
    - 固定大小（默认 1000 条）
    - 基于 OrderedDict 的 LRU 实现
    - 线程安全（OrderedDict 是线程安全的）
    - 自动过期（可选 TTL）
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        """
        初始化缓存

        Args:
            max_size: 最大缓存条数（默认 1000）
            ttl_seconds: 过期时间（秒），None 表示永不过期
        """
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        logger.info(f"翻译缓存初始化: max_size={max_size}, ttl={ttl_seconds}s")

    def _generate_key(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        style: str = "formal",
    ) -> str:
        """
        生成缓存键（基于 SHA256 哈希）

        Args:
            text: 原文
            target_language: 目标语言
            source_language: 源语言
            style: 翻译风格

        Returns:
            缓存键（SHA256 前 16 字符）
        """
        # 构建键字符串（包含所有影响翻译结果的参数）
        key_string = f"{text}|{source_language}|{target_language}|{style}"

        # SHA256 哈希（取前 16 字符，足够避免冲突）
        hash_digest = hashlib.sha256(key_string.encode("utf-8")).hexdigest()
        return hash_digest[:16]

    def get(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        style: str = "formal",
    ) -> Optional[str]:
        """
        从缓存获取翻译结果

        Args:
            text: 原文
            target_language: 目标语言
            source_language: 源语言
            style: 翻译风格

        Returns:
            翻译结果（如果缓存命中），否则 None
        """
        key = self._generate_key(text, target_language, source_language, style)

        if key not in self._cache:
            self._misses += 1
            return None

        # 检查是否过期
        cache_entry = self._cache[key]
        if self._ttl_seconds is not None:
            age = time.time() - cache_entry["timestamp"]
            if age > self._ttl_seconds:
                # 过期，删除并返回 None
                del self._cache[key]
                self._misses += 1
                logger.debug(f"缓存过期: key={key}, age={age:.1f}s")
                return None

        # 缓存命中，移动到末尾（LRU）
        self._cache.move_to_end(key)
        self._hits += 1

        logger.debug(
            f"🚀 缓存命中: key={key}, hit_rate={self.hit_rate:.1%}, "
            f"text_preview={text[:30]}..."
        )

        return cache_entry["translation"]

    def put(
        self,
        text: str,
        target_language: str,
        translation: str,
        source_language: str = "auto",
        style: str = "formal",
    ) -> None:
        """
        将翻译结果存入缓存

        Args:
            text: 原文
            target_language: 目标语言
            translation: 译文
            source_language: 源语言
            style: 翻译风格
        """
        key = self._generate_key(text, target_language, source_language, style)

        # 如果已存在，先移除（后面会重新添加到末尾）
        if key in self._cache:
            del self._cache[key]

        # 添加新条目
        self._cache[key] = {
            "translation": translation,
            "timestamp": time.time(),
        }

        # LRU 淘汰（如果超过最大大小）
        if len(self._cache) > self._max_size:
            # 移除最旧的条目（OrderedDict 的第一个）
            evicted_key = next(iter(self._cache))
            del self._cache[evicted_key]
            self._evictions += 1
            logger.debug(f"缓存淘汰: key={evicted_key}, evictions={self._evictions}")

        logger.debug(f"缓存存入: key={key}, cache_size={len(self._cache)}")

    def clear(self) -> None:
        """清空缓存"""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(f"缓存已清空: {cache_size} 条记录")

    @property
    def hit_rate(self) -> float:
        """
        缓存命中率

        Returns:
            命中率（0.0 ~ 1.0）
        """
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    @property
    def stats(self) -> Dict[str, Any]:
        """
        缓存统计信息

        Returns:
            统计字典
        """
        return {
            "cache_size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": self.hit_rate,
            "ttl_seconds": self._ttl_seconds,
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"TranslationCache(size={len(self._cache)}/{self._max_size}, "
            f"hit_rate={self.hit_rate:.1%}, hits={self._hits}, misses={self._misses})"
        )
