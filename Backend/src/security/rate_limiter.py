#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - 速率限制系统
Phase 1.5 - Day 8-9
创建时间: 2026-01-21

令牌桶算法实现，防止 DoS 攻击和资源滥用
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional, Tuple

from loguru import logger


@dataclass
class TokenBucket:
    """令牌桶（Token Bucket）"""

    capacity: int  # 桶容量（最大令牌数）
    tokens: float  # 当前令牌数
    refill_rate: float  # 令牌补充速率（tokens/second）
    last_refill: float  # 上次补充时间（Unix 时间戳）

    def refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill

        # 计算应该补充的令牌数
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def consume(self, count: int = 1) -> bool:
        """
        消费令牌

        Args:
            count: 需要消费的令牌数

        Returns:
            是否成功消费
        """
        self.refill()

        if self.tokens >= count:
            self.tokens -= count
            return True

        return False

    def get_wait_time(self, count: int = 1) -> float:
        """
        获取等待时间（秒）

        Args:
            count: 需要的令牌数

        Returns:
            需要等待的秒数
        """
        self.refill()

        if self.tokens >= count:
            return 0.0

        needed = count - self.tokens
        return needed / self.refill_rate


class RateLimiter:
    """
    速率限制器（基于令牌桶算法）

    支持多级限制：
    - 每分钟限制（60 req/min）
    - 每小时限制（1000 req/hour）
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        cleanup_interval: int = 3600,  # 1 小时清理一次
    ):
        """
        初始化速率限制器

        Args:
            requests_per_minute: 每分钟最大请求数
            requests_per_hour: 每小时最大请求数
            cleanup_interval: 清理间隔（秒）
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.cleanup_interval = cleanup_interval

        # 每分钟桶: {client_id: TokenBucket}
        self._minute_buckets: Dict[str, TokenBucket] = {}
        # 每小时桶: {client_id: TokenBucket}
        self._hour_buckets: Dict[str, TokenBucket] = {}

        # 线程锁（确保并发安全）
        self._lock = Lock()

        # 上次清理时间
        self._last_cleanup = time.time()

        logger.info(
            f"✓ RateLimiter 初始化: {requests_per_minute} req/min, {requests_per_hour} req/hour"
        )

    def _get_or_create_bucket(
        self, client_id: str, bucket_dict: Dict[str, TokenBucket], capacity: int, refill_rate: float
    ) -> TokenBucket:
        """
        获取或创建令牌桶

        Args:
            client_id: 客户端 ID（通常是 IP 地址）
            bucket_dict: 桶字典
            capacity: 桶容量
            refill_rate: 补充速率

        Returns:
            TokenBucket
        """
        if client_id not in bucket_dict:
            bucket_dict[client_id] = TokenBucket(
                capacity=capacity,
                tokens=capacity,  # 初始满令牌
                refill_rate=refill_rate,
                last_refill=time.time(),
            )

        return bucket_dict[client_id]

    def check_rate_limit(self, client_id: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        检查速率限制

        Args:
            client_id: 客户端 ID（通常是 IP 地址）

        Returns:
            (是否允许, 错误信息, 重试延迟秒数)
        """
        with self._lock:
            # 定期清理过期记录
            self._cleanup_if_needed()

            # 检查每分钟限制
            minute_bucket = self._get_or_create_bucket(
                client_id=client_id,
                bucket_dict=self._minute_buckets,
                capacity=self.requests_per_minute,
                refill_rate=self.requests_per_minute / 60.0,  # tokens/second
            )

            if not minute_bucket.consume():
                wait_time = int(minute_bucket.get_wait_time()) + 1
                logger.warning(
                    f"⚠️ 速率限制触发: {client_id} 超过每分钟限制 ({self.requests_per_minute} req/min)"
                )
                return (
                    False,
                    f"速率限制：超过每分钟限制 ({self.requests_per_minute} 请求)",
                    wait_time,
                )

            # 检查每小时限制
            hour_bucket = self._get_or_create_bucket(
                client_id=client_id,
                bucket_dict=self._hour_buckets,
                capacity=self.requests_per_hour,
                refill_rate=self.requests_per_hour / 3600.0,  # tokens/second
            )

            if not hour_bucket.consume():
                wait_time = int(hour_bucket.get_wait_time()) + 1
                logger.warning(
                    f"⚠️ 速率限制触发: {client_id} 超过每小时限制 ({self.requests_per_hour} req/hour)"
                )
                return (
                    False,
                    f"速率限制：超过每小时限制 ({self.requests_per_hour} 请求)",
                    wait_time,
                )

            return True, None, None

    def _cleanup_if_needed(self) -> None:
        """定期清理过期的令牌桶"""
        now = time.time()

        if now - self._last_cleanup < self.cleanup_interval:
            return  # 还没到清理时间

        # 清理每分钟桶（超过 5 分钟未使用）
        expired_minute = [
            client_id
            for client_id, bucket in self._minute_buckets.items()
            if now - bucket.last_refill > 300  # 5 分钟
        ]

        for client_id in expired_minute:
            del self._minute_buckets[client_id]

        # 清理每小时桶（超过 2 小时未使用）
        expired_hour = [
            client_id
            for client_id, bucket in self._hour_buckets.items()
            if now - bucket.last_refill > 7200  # 2 小时
        ]

        for client_id in expired_hour:
            del self._hour_buckets[client_id]

        if expired_minute or expired_hour:
            logger.debug(
                f"清理过期令牌桶: {len(expired_minute)} 分钟桶, {len(expired_hour)} 小时桶"
            )

        self._last_cleanup = now

    def get_remaining_requests(self, client_id: str) -> Dict[str, int]:
        """
        获取剩余请求配额

        Args:
            client_id: 客户端 ID

        Returns:
            {"per_minute": 剩余分钟配额, "per_hour": 剩余小时配额}
        """
        with self._lock:
            # 获取或创建桶
            minute_bucket = self._get_or_create_bucket(
                client_id=client_id,
                bucket_dict=self._minute_buckets,
                capacity=self.requests_per_minute,
                refill_rate=self.requests_per_minute / 60.0,
            )

            hour_bucket = self._get_or_create_bucket(
                client_id=client_id,
                bucket_dict=self._hour_buckets,
                capacity=self.requests_per_hour,
                refill_rate=self.requests_per_hour / 3600.0,
            )

            # 补充令牌（不消费）
            minute_bucket.refill()
            hour_bucket.refill()

            return {
                "per_minute": int(minute_bucket.tokens),
                "per_hour": int(hour_bucket.tokens),
            }

    def reset_client(self, client_id: str) -> None:
        """
        重置客户端配额（用于测试或手动解除限制）

        Args:
            client_id: 客户端 ID
        """
        with self._lock:
            if client_id in self._minute_buckets:
                del self._minute_buckets[client_id]

            if client_id in self._hour_buckets:
                del self._hour_buckets[client_id]

            logger.info(f"✓ 重置客户端配额: {client_id}")

    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息

        Returns:
            {"active_clients_minute": N, "active_clients_hour": M}
        """
        with self._lock:
            return {
                "active_clients_minute": len(self._minute_buckets),
                "active_clients_hour": len(self._hour_buckets),
            }


# 全局单例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(
    requests_per_minute: int = 60, requests_per_hour: int = 1000
) -> RateLimiter:
    """
    获取全局速率限制器（单例模式）

    Args:
        requests_per_minute: 每分钟最大请求数
        requests_per_hour: 每小时最大请求数

    Returns:
        RateLimiter
    """
    global _rate_limiter

    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute, requests_per_hour=requests_per_hour
        )

    return _rate_limiter
