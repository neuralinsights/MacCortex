#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - RateLimiter 测试
Phase 1.5 - Day 8-9
创建时间: 2026-01-21

测试速率限制系统（令牌桶算法）
"""

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from security.rate_limiter import RateLimiter, TokenBucket, get_rate_limiter
from middleware.rate_limit_middleware import RateLimitMiddleware


# ==================== Fixtures ====================


@pytest.fixture
def token_bucket():
    """创建令牌桶实例"""
    return TokenBucket(capacity=10, tokens=10, refill_rate=1.0, last_refill=time.time())


@pytest.fixture
def rate_limiter():
    """创建速率限制器实例"""
    return RateLimiter(requests_per_minute=60, requests_per_hour=1000)


@pytest.fixture
def app():
    """创建测试应用"""
    test_app = FastAPI()

    @test_app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}

    @test_app.get("/health")
    async def health():
        return {"status": "healthy"}

    # 添加速率限制中间件
    test_app.add_middleware(
        RateLimitMiddleware, requests_per_minute=5, requests_per_hour=20, exempt_paths=["/health"]
    )

    return test_app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app, raise_server_exceptions=False)


# ==================== TokenBucket 测试 ====================


class TestTokenBucket:
    """测试令牌桶"""

    def test_consume_success(self, token_bucket):
        """测试成功消费令牌"""
        assert token_bucket.tokens == 10
        assert token_bucket.consume(3) is True
        assert token_bucket.tokens == 7

    def test_consume_failure(self, token_bucket):
        """测试消费失败（令牌不足）"""
        token_bucket.tokens = 2
        token_bucket.last_refill = time.time()  # 重置时间防止补充
        assert token_bucket.consume(5) is False
        # 令牌数应该接近 2（可能因为极微小的时间差有轻微补充）
        assert token_bucket.tokens >= 2.0
        assert token_bucket.tokens <= 2.01

    def test_refill(self):
        """测试令牌补充"""
        bucket = TokenBucket(capacity=10, tokens=0, refill_rate=2.0, last_refill=time.time())
        time.sleep(1.1)  # 等待 1.1 秒
        bucket.refill()

        # 应该补充约 2.2 个令牌
        assert bucket.tokens >= 2.0
        assert bucket.tokens <= 3.0

    def test_refill_not_exceed_capacity(self):
        """测试令牌补充不超过容量"""
        bucket = TokenBucket(capacity=10, tokens=9, refill_rate=10.0, last_refill=time.time())
        time.sleep(1.1)
        bucket.refill()

        # 不应超过容量
        assert bucket.tokens == 10

    def test_get_wait_time_zero(self, token_bucket):
        """测试等待时间为 0（令牌充足）"""
        assert token_bucket.get_wait_time(5) == 0.0

    def test_get_wait_time_positive(self):
        """测试等待时间大于 0（令牌不足）"""
        bucket = TokenBucket(capacity=10, tokens=2, refill_rate=1.0, last_refill=time.time())
        wait_time = bucket.get_wait_time(5)

        # 需要等待约 3 秒（需要 3 个令牌，补充速率 1/s）
        assert wait_time >= 2.9
        assert wait_time <= 3.1


# ==================== RateLimiter 测试 ====================


class TestRateLimiter:
    """测试速率限制器"""

    def test_initialization(self, rate_limiter):
        """测试初始化"""
        assert rate_limiter.requests_per_minute == 60
        assert rate_limiter.requests_per_hour == 1000

    def test_check_rate_limit_allow(self, rate_limiter):
        """测试允许请求"""
        allowed, error, retry_after = rate_limiter.check_rate_limit("client1")
        assert allowed is True
        assert error is None
        assert retry_after is None

    def test_check_rate_limit_reject_minute(self):
        """测试每分钟限制拒绝"""
        limiter = RateLimiter(requests_per_minute=3, requests_per_hour=1000)

        # 发送 3 个请求（应该成功）
        for _ in range(3):
            allowed, _, _ = limiter.check_rate_limit("client2")
            assert allowed is True

        # 第 4 个请求（应该失败）
        allowed, error, retry_after = limiter.check_rate_limit("client2")
        assert allowed is False
        assert "每分钟限制" in error
        assert retry_after is not None
        assert retry_after > 0

    def test_check_rate_limit_reject_hour(self):
        """测试每小时限制拒绝"""
        limiter = RateLimiter(requests_per_minute=100, requests_per_hour=5)

        # 发送 5 个请求（应该成功）
        for _ in range(5):
            allowed, _, _ = limiter.check_rate_limit("client3")
            assert allowed is True

        # 第 6 个请求（应该失败）
        allowed, error, retry_after = limiter.check_rate_limit("client3")
        assert allowed is False
        assert "每小时限制" in error
        assert retry_after is not None

    def test_get_remaining_requests(self, rate_limiter):
        """测试获取剩余配额"""
        # 消费 10 个请求
        for _ in range(10):
            rate_limiter.check_rate_limit("client4")

        remaining = rate_limiter.get_remaining_requests("client4")

        assert remaining["per_minute"] <= 60 - 10
        assert remaining["per_hour"] <= 1000 - 10

    def test_reset_client(self, rate_limiter):
        """测试重置客户端配额"""
        # 消费一些配额
        for _ in range(10):
            rate_limiter.check_rate_limit("client5")

        # 重置
        rate_limiter.reset_client("client5")

        # 配额应该恢复
        remaining = rate_limiter.get_remaining_requests("client5")
        assert remaining["per_minute"] == 60
        assert remaining["per_hour"] == 1000

    def test_multiple_clients(self, rate_limiter):
        """测试多客户端隔离"""
        # 客户端 A 消费 10 个请求
        for _ in range(10):
            rate_limiter.check_rate_limit("client_a")

        # 客户端 B 消费 5 个请求
        for _ in range(5):
            rate_limiter.check_rate_limit("client_b")

        # 检查配额隔离
        remaining_a = rate_limiter.get_remaining_requests("client_a")
        remaining_b = rate_limiter.get_remaining_requests("client_b")

        assert remaining_a["per_minute"] < remaining_b["per_minute"]

    def test_get_stats(self, rate_limiter):
        """测试统计信息"""
        rate_limiter.check_rate_limit("client6")
        rate_limiter.check_rate_limit("client7")

        stats = rate_limiter.get_stats()
        assert stats["active_clients_minute"] >= 2
        assert stats["active_clients_hour"] >= 2

    def test_cleanup(self):
        """测试自动清理（需要模拟时间流逝）"""
        limiter = RateLimiter(
            requests_per_minute=10, requests_per_hour=100, cleanup_interval=1  # 1 秒清理间隔
        )

        # 创建一些客户端
        limiter.check_rate_limit("temp_client1")
        limiter.check_rate_limit("temp_client2")

        initial_stats = limiter.get_stats()
        assert initial_stats["active_clients_minute"] >= 2

        # 等待清理间隔
        time.sleep(1.1)

        # 触发清理（通过新请求）
        limiter.check_rate_limit("new_client")

        # 注意：由于清理条件是 5 分钟/2 小时未使用，短时间测试中客户端不会被清理
        # 这个测试主要验证清理逻辑不会崩溃


# ==================== 单例模式测试 ====================


class TestRateLimiterSingleton:
    """测试单例模式"""

    def test_get_rate_limiter_singleton(self):
        """测试单例实例"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2  # 应该是同一个实例


# ==================== RateLimitMiddleware 测试 ====================


class TestRateLimitMiddleware:
    """测试速率限制中间件"""

    def test_allow_request(self, client):
        """测试允许请求"""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "ok"}

    def test_rate_limit_headers(self, client):
        """测试速率限制响应头"""
        response = client.get("/test")

        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Limit-Hour" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers

        assert response.headers["X-RateLimit-Limit-Minute"] == "5"
        assert response.headers["X-RateLimit-Limit-Hour"] == "20"

    def test_rate_limit_reject(self, client):
        """测试速率限制拒绝"""
        # 发送 5 个请求（应该成功）
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200

        # 第 6 个请求（应该失败 429）
        response = client.get("/test")
        assert response.status_code == 429
        assert "速率限制" in response.json()["detail"]

    def test_retry_after_header(self, client):
        """测试 Retry-After 响应头"""
        # 耗尽配额
        for _ in range(5):
            client.get("/test")

        # 第 6 个请求应该返回 Retry-After
        response = client.get("/test")
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert int(response.headers["Retry-After"]) > 0

    def test_exempt_paths(self, client):
        """测试白名单路径"""
        # /health 在白名单中，应该不受速率限制
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    def test_client_ip_extraction(self, client):
        """测试客户端 IP 提取"""
        # 使用 X-Forwarded-For
        response = client.get("/test", headers={"X-Forwarded-For": "203.0.113.1, 198.51.100.1"})
        assert response.status_code == 200

        # 使用 X-Real-IP
        response = client.get("/test", headers={"X-Real-IP": "203.0.113.2"})
        assert response.status_code == 200

    def test_rate_limit_per_ip(self, client):
        """测试基于 IP 的速率限制"""
        # IP1 发送 5 个请求
        for _ in range(5):
            response = client.get("/test", headers={"X-Forwarded-For": "203.0.113.1"})
            assert response.status_code == 200

        # IP1 的第 6 个请求（应该失败）
        response = client.get("/test", headers={"X-Forwarded-For": "203.0.113.1"})
        assert response.status_code == 429

        # IP2 的请求（应该成功，配额独立）
        response = client.get("/test", headers={"X-Forwarded-For": "203.0.113.2"})
        assert response.status_code == 200


# ==================== 边界与特殊情况测试 ====================


class TestEdgeCases:
    """测试边界与特殊情况"""

    def test_zero_tokens(self):
        """测试零令牌"""
        bucket = TokenBucket(capacity=10, tokens=0, refill_rate=1.0, last_refill=time.time())
        assert bucket.consume(1) is False

    def test_exact_capacity(self):
        """测试恰好容量"""
        bucket = TokenBucket(capacity=10, tokens=10, refill_rate=1.0, last_refill=time.time())
        assert bucket.consume(10) is True
        assert bucket.tokens == 0

    def test_concurrent_requests(self, rate_limiter):
        """测试并发请求（线程安全）"""
        import concurrent.futures

        def make_request(client_id):
            return rate_limiter.check_rate_limit(client_id)

        # 同时发送 20 个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, f"client_concurrent_{i}") for i in range(20)]
            results = [f.result() for f in futures]

        # 所有请求都应该成功处理（不会崩溃）
        assert len(results) == 20

    def test_rate_limiter_with_very_low_limits(self):
        """测试极低限制"""
        limiter = RateLimiter(requests_per_minute=1, requests_per_hour=2)

        # 第 1 个请求成功
        allowed, _, _ = limiter.check_rate_limit("low_limit_client")
        assert allowed is True

        # 第 2 个请求失败（每分钟限制）
        allowed, _, _ = limiter.check_rate_limit("low_limit_client")
        assert allowed is False

    def test_rate_limiter_with_very_high_limits(self):
        """测试极高限制"""
        limiter = RateLimiter(requests_per_minute=10000, requests_per_hour=100000)

        # 发送 100 个请求都应该成功
        for _ in range(100):
            allowed, _, _ = limiter.check_rate_limit("high_limit_client")
            assert allowed is True
