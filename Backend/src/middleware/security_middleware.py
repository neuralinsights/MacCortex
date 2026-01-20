#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - 安全中间件
Phase 1.5 - Day 4-5
创建时间: 2026-01-21

请求级安全：审计日志 + 请求 ID + 性能监控
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from security.audit_logger import get_audit_logger


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件（审计日志 + 请求追踪）"""

    def __init__(self, app, enable_audit_log: bool = True):
        """
        初始化安全中间件

        Args:
            app: FastAPI 应用
            enable_audit_log: 是否启用审计日志（默认 True）
        """
        super().__init__(app)
        self.enable_audit_log = enable_audit_log
        if self.enable_audit_log:
            self.audit_logger = get_audit_logger()
        logger.info(f"✓ SecurityMiddleware 初始化: audit_log={enable_audit_log}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求（请求前 + 请求后）

        Args:
            request: FastAPI 请求
            call_next: 下一个中间件/路由处理器

        Returns:
            Response: 响应
        """
        # 生成请求 ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 获取客户端 IP
        client_ip = self._get_client_ip(request)

        # 记录请求开始
        start_time = time.time()
        if self.enable_audit_log:
            self.audit_logger.log_request_start(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
            )

        # 执行请求
        try:
            response = await call_next(request)
            success = True
            status_code = response.status_code
        except Exception as e:
            logger.error(f"请求处理失败: {e}")
            # 记录失败的请求
            if self.enable_audit_log:
                self.audit_logger.log_security_event(
                    request_id=request_id,
                    event_subtype="request_error",
                    severity="high",
                    details={
                        "error": str(e),
                        "path": request.url.path,
                    },
                    client_ip=client_ip,
                )
            # 重新抛出异常，让 FastAPI 处理
            raise
        finally:
            # 计算请求耗时
            duration_ms = (time.time() - start_time) * 1000

            # 记录请求结束（如果成功执行了）
            if self.enable_audit_log and 'success' in locals():
                self.audit_logger.log_request_end(
                    request_id=request_id,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    success=success,
                    client_ip=client_ip,
                )

        # 添加响应头（请求 ID）
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端 IP 地址

        Args:
            request: FastAPI 请求

        Returns:
            客户端 IP 地址
        """
        # 优先从 X-Forwarded-For 获取（支持反向代理）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # 取第一个 IP（客户端 IP）
            return forwarded.split(",")[0].strip()

        # 从 X-Real-IP 获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # 从连接信息获取
        if request.client:
            return request.client.host

        return "unknown"
