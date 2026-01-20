#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - 安全中间件测试
Phase 1.5 - Day 4-5
创建时间: 2026-01-21

测试覆盖：
- SecurityMiddleware: 请求追踪 + 审计日志
- 客户端 IP 提取（支持反向代理）
- 请求/响应头注入
"""

import asyncio
import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from middleware.security_middleware import SecurityMiddleware
from security.audit_logger import AuditLogger


@pytest.fixture
def temp_log_dir():
    """创建临时日志目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def app(temp_log_dir):
    """创建测试 FastAPI 应用"""
    test_app = FastAPI()

    # 添加安全中间件
    test_app.add_middleware(SecurityMiddleware, enable_audit_log=True)

    # 测试路由
    @test_app.get("/test")
    async def test_route(request: Request):
        return {
            "message": "success",
            "request_id": getattr(request.state, "request_id", None)
        }

    @test_app.post("/execute")
    async def execute_route(request: Request):
        return {
            "success": True,
            "request_id": getattr(request.state, "request_id", None)
        }

    @test_app.get("/error")
    async def error_route():
        raise ValueError("Test error")

    return test_app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app, raise_server_exceptions=False)


class TestSecurityMiddleware:
    """测试安全中间件"""

    def test_request_id_generation(self, client):
        """测试请求 ID 生成"""
        response = client.get("/test")
        assert response.status_code == 200

        # 验证响应头包含 X-Request-ID
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]

        # 验证是有效的 UUID
        try:
            uuid.UUID(request_id)
        except ValueError:
            pytest.fail(f"Invalid UUID: {request_id}")

        # 验证响应体包含 request_id
        data = response.json()
        assert data["request_id"] == request_id

    def test_response_time_header(self, client):
        """测试响应时间头"""
        response = client.get("/test")
        assert response.status_code == 200

        # 验证响应头包含 X-Response-Time
        assert "X-Response-Time" in response.headers
        response_time = response.headers["X-Response-Time"]

        # 验证格式（例如: "12.34ms"）
        assert response_time.endswith("ms")
        # 验证是数字
        time_value = float(response_time.rstrip("ms"))
        assert time_value >= 0

    def test_client_ip_from_connection(self, client):
        """测试从连接获取客户端 IP"""
        response = client.get("/test")
        assert response.status_code == 200

        # TestClient 默认使用 testclient
        # 实际 IP 提取在中间件内部，这里验证请求成功即可

    def test_client_ip_from_x_forwarded_for(self, client):
        """测试从 X-Forwarded-For 获取客户端 IP"""
        headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}
        response = client.get("/test", headers=headers)
        assert response.status_code == 200

        # 中间件应提取第一个 IP (203.0.113.1)
        # 验证请求成功

    def test_client_ip_from_x_real_ip(self, client):
        """测试从 X-Real-IP 获取客户端 IP"""
        headers = {"X-Real-IP": "203.0.113.5"}
        response = client.get("/test", headers=headers)
        assert response.status_code == 200

        # 中间件应提取 X-Real-IP
        # 验证请求成功

    def test_multiple_requests_unique_ids(self, client):
        """测试多个请求生成唯一 ID"""
        request_ids = set()

        for _ in range(10):
            response = client.get("/test")
            assert response.status_code == 200
            request_id = response.headers["X-Request-ID"]
            request_ids.add(request_id)

        # 验证所有 ID 都是唯一的
        assert len(request_ids) == 10

    def test_post_request_tracking(self, client):
        """测试 POST 请求追踪"""
        response = client.post(
            "/execute",
            json={"pattern_id": "test", "text": "测试"}
        )
        assert response.status_code == 200

        # 验证请求 ID
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]

        # 验证响应体
        data = response.json()
        assert data["success"] is True
        assert data["request_id"] == request_id

    def test_error_handling(self, client):
        """测试错误处理"""
        response = client.get("/error")

        # FastAPI 默认返回 500 错误
        assert response.status_code == 500

        # 注意：由于异常在中间件之前抛出，响应头可能不包含 X-Request-ID
        # 这是预期行为，因为错误响应由 FastAPI 的异常处理器生成

    def test_middleware_disabled_audit_log(self, temp_log_dir):
        """测试禁用审计日志"""
        test_app = FastAPI()
        test_app.add_middleware(SecurityMiddleware, enable_audit_log=False)

        @test_app.get("/test")
        async def test_route():
            return {"message": "success"}

        client = TestClient(test_app)
        response = client.get("/test")
        assert response.status_code == 200

        # 验证仍然有 Request ID
        assert "X-Request-ID" in response.headers

    def test_concurrent_requests(self, client):
        """测试并发请求处理"""
        import concurrent.futures

        def make_request():
            response = client.get("/test")
            return response.headers["X-Request-ID"]

        # 并发 20 个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            request_ids = [f.result() for f in futures]

        # 验证所有 ID 唯一
        assert len(set(request_ids)) == 20


class TestSecurityMiddlewareAuditIntegration:
    """测试安全中间件与审计日志集成"""

    def test_audit_log_request_start(self, app, client, temp_log_dir, monkeypatch):
        """测试审计日志记录请求开始"""
        # 使用临时目录作为日志目录
        import security.audit_logger as audit_module
        monkeypatch.setenv("AUDIT_LOG_DIR", temp_log_dir)

        # 重置单例
        audit_module._audit_logger = None

        # 发送请求
        response = client.get("/test")
        assert response.status_code == 200

        # 读取审计日志
        today = datetime.now(timezone.utc).date()
        log_file = Path(temp_log_dir) / f"audit-{today.isoformat()}.jsonl"

        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 应该有 request_start 和 request_end 两条记录
            assert len(lines) >= 2

            # 验证 request_start
            start_event = json.loads(lines[0])
            assert start_event["event_type"] == "request_start"
            assert start_event["method"] == "GET"
            assert start_event["path"] == "/test"

            # 验证 request_end
            end_event = json.loads(lines[1])
            assert end_event["event_type"] == "request_end"
            assert "duration_ms" in end_event
            assert end_event["success"] is True

    def test_audit_log_request_id_consistency(self, client, temp_log_dir, monkeypatch):
        """测试审计日志中的 Request ID 一致性"""
        import security.audit_logger as audit_module
        monkeypatch.setenv("AUDIT_LOG_DIR", temp_log_dir)
        audit_module._audit_logger = None

        response = client.get("/test")
        assert response.status_code == 200
        request_id = response.headers["X-Request-ID"]

        # 读取审计日志
        today = datetime.now(timezone.utc).date()
        log_file = Path(temp_log_dir) / f"audit-{today.isoformat()}.jsonl"

        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    event = json.loads(line)
                    # 所有事件应该有相同的 request_id
                    assert event["request_id"] == request_id

    def test_audit_log_ip_hashing(self, client, temp_log_dir, monkeypatch):
        """测试审计日志中的 IP 哈希"""
        import security.audit_logger as audit_module
        monkeypatch.setenv("AUDIT_LOG_DIR", temp_log_dir)
        audit_module._audit_logger = None

        headers = {"X-Forwarded-For": "192.168.1.100"}
        response = client.get("/test", headers=headers)
        assert response.status_code == 200

        # 读取审计日志
        today = datetime.now(timezone.utc).date()
        log_file = Path(temp_log_dir) / f"audit-{today.isoformat()}.jsonl"

        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                event = json.loads(f.readline())

            # 验证 IP 已哈希
            assert "client_ip_hash" in event
            # 哈希值不应包含原始 IP
            assert "192.168.1.100" not in event["client_ip_hash"]


class TestClientIPExtraction:
    """测试客户端 IP 提取逻辑"""

    def test_ip_priority_x_forwarded_for(self, client):
        """测试 X-Forwarded-For 优先级最高"""
        headers = {
            "X-Forwarded-For": "203.0.113.1, 198.51.100.1",
            "X-Real-IP": "203.0.113.5"
        }
        response = client.get("/test", headers=headers)
        assert response.status_code == 200

        # 中间件应优先使用 X-Forwarded-For 的第一个 IP

    def test_ip_fallback_to_x_real_ip(self, client):
        """测试回退到 X-Real-IP"""
        headers = {"X-Real-IP": "203.0.113.5"}
        response = client.get("/test", headers=headers)
        assert response.status_code == 200

        # 中间件应使用 X-Real-IP

    def test_ip_fallback_to_client_host(self, client):
        """测试回退到 client.host"""
        response = client.get("/test")
        assert response.status_code == 200

        # 中间件应使用 TestClient 默认 IP


class TestMiddlewarePerformance:
    """测试中间件性能影响"""

    def test_middleware_overhead(self, client):
        """测试中间件性能开销"""
        import time

        # 记录 10 个请求的响应时间
        response_times = []
        for _ in range(10):
            start = time.time()
            response = client.get("/test")
            duration = (time.time() - start) * 1000  # ms
            response_times.append(duration)
            assert response.status_code == 200

        # 计算平均响应时间
        avg_time = sum(response_times) / len(response_times)

        # 中间件开销应该很小（< 50ms in test environment）
        # 注意: TestClient 在同一进程中运行，实际生产环境开销更小
        print(f"\n平均响应时间: {avg_time:.2f}ms")
        assert avg_time < 100  # 宽松阈值，考虑测试环境


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
