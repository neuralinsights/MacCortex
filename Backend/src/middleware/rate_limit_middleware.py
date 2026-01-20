#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - 速率限制中间件
Phase 1.5 - Day 8-9
创建时间: 2026-01-21

FastAPI 中间件，集成令牌桶速率限制
"""

from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from security.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件（Token Bucket）

    功能:
    - 基于客户端 IP 的速率限制
    - 60 req/min + 1000 req/hour 双重限制
    - X-RateLimit-* 响应头（配额信息）
    - Retry-After 响应头（超限时）
    - 支持白名单路径（/health, /version 等）
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        exempt_paths: list[str] = None,
    ):
        """
        初始化速率限制中间件

        Args:
            app: FastAPI 应用
            requests_per_minute: 每分钟最大请求数
            requests_per_hour: 每小时最大请求数
            exempt_paths: 免除速率限制的路径（白名单）
        """
        super().__init__(app)

        # 创建独立的 RateLimiter 实例（不使用全局单例）
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute, requests_per_hour=requests_per_hour
        )

        # 默认白名单路径
        self.exempt_paths = exempt_paths or [
            "/health",
            "/version",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        logger.info(
            f"✓ RateLimitMiddleware 初始化: {requests_per_minute} req/min, {requests_per_hour} req/hour"
        )
        logger.info(f"  白名单路径: {self.exempt_paths}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 检查是否在白名单中
        if self._is_exempt(request):
            return await call_next(request)

        # 获取客户端 IP
        client_ip = self._get_client_ip(request)

        # 检查速率限制
        allowed, error_msg, retry_after = self.rate_limiter.check_rate_limit(client_ip)

        if not allowed:
            # 超过速率限制
            logger.warning(f"🚫 速率限制拒绝: {client_ip} → {request.url.path} ({error_msg})")

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "速率限制超出（Too Many Requests）",
                    "error": error_msg,
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit-Minute": str(self.rate_limiter.requests_per_minute),
                    "X-RateLimit-Limit-Hour": str(self.rate_limiter.requests_per_hour),
                    "X-RateLimit-Remaining-Minute": "0",
                    "X-RateLimit-Remaining-Hour": "0",
                },
            )

        # 允许请求，继续处理
        response = await call_next(request)

        # 添加速率限制响应头
        remaining = self.rate_limiter.get_remaining_requests(client_ip)

        response.headers["X-RateLimit-Limit-Minute"] = str(self.rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.rate_limiter.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining["per_minute"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining["per_hour"])

        return response

    def _is_exempt(self, request: Request) -> bool:
        """
        检查路径是否在白名单中

        Args:
            request: FastAPI Request

        Returns:
            是否免除速率限制
        """
        path = request.url.path

        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True

        return False

    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端 IP 地址（支持反向代理）

        Args:
            request: FastAPI Request

        Returns:
            客户端 IP 地址
        """
        # 优先从 X-Forwarded-For 获取（反向代理）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For 可能包含多个 IP，取第一个
            return forwarded.split(",")[0].strip()

        # 从 X-Real-IP 获取（Nginx）
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # 从 request.client 获取
        if request.client and request.client.host:
            return request.client.host

        return "unknown"
