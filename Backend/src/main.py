#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MacCortex Python Backend - FastAPI Application
Phase 1 - Week 2 Day 8-9
创建时间: 2026-01-20
更新时间: 2026-01-21 (Phase 1.5 - Day 8-9: 集成速率限制系统)

FastAPI 服务，用于执行需要 Python 后端的 AI Pattern

Copyright (c) 2026 Yu Geng. All rights reserved.
This software is proprietary and confidential.
"""

__author__ = "Yu Geng"
__copyright__ = "Copyright 2026, Yu Geng"
__license__ = "Proprietary"
__version__ = "1.0.0"
__maintainer__ = "Yu Geng"
__email__ = "james.geng@gmail.com"
__status__ = "Production"

# Project watermark (DO NOT REMOVE)
_PROJECT_ID = "MacCortex-YG-2026-0121-PROD"
_OWNER_HASH = "8f3b5c7a9e1d2f4b6a8c0e3f5d7b9a1c3e5f7d9b"  # Hidden identifier

import os
import sys
import unicodedata
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field, field_validator

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from patterns.registry import PatternRegistry
from utils.config import Settings
from utils.watermark import verify_ownership, check_integrity, get_project_info
from middleware.security_middleware import SecurityMiddleware  # Phase 1.5: 审计日志
from middleware.rate_limit_middleware import RateLimitMiddleware  # Phase 1.5: 速率限制

# 加载配置
settings = Settings()

# 验证项目所有权（静默）
_ownership_verified = verify_ownership()
_integrity_checked = check_integrity()

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
)


# Lifespan 管理（启动/关闭）
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 MacCortex Backend 启动中...")

    # 初始化 Pattern Registry
    registry = PatternRegistry()
    await registry.initialize()
    app.state.registry = registry

    logger.info(f"✅ 已加载 {len(registry.list_patterns())} 个 Pattern")
    logger.info(f"🌐 服务地址: http://{settings.host}:{settings.port}")

    yield

    # 清理资源
    logger.info("👋 MacCortex Backend 关闭中...")
    await registry.cleanup()


# 创建 FastAPI 应用
app = FastAPI(
    title="MacCortex Backend API",
    description="AI Pattern Execution Engine for macOS",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件（允许 Swift 应用访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1.5 Day 8-9: 速率限制中间件（60 req/min, 1000 req/hour）
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    exempt_paths=["/health", "/version", "/docs", "/redoc", "/openapi.json"],
)

# Phase 1.5 Day 4-5: 安全中间件（审计日志 + 请求追踪）
app.add_middleware(SecurityMiddleware, enable_audit_log=True)


# ==================== Pydantic 模型 ====================


class PatternRequest(BaseModel):
    """Pattern 执行请求（Phase 1.5 Day 6-7: 增强输入验证）"""

    pattern_id: str = Field(..., description="Pattern ID", max_length=50)
    text: str = Field(..., description="输入文本", max_length=50_000)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数字典")
    request_id: str = Field(default="", description="请求 ID（可选）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "pattern_id": "summarize",
                    "text": "长文本内容...",
                    "parameters": {"length": "medium", "language": "zh-CN"},
                    "request_id": "req-12345",
                }
            ]
        }
    }

    @field_validator("pattern_id")
    @classmethod
    def validate_pattern_id(cls, v: str) -> str:
        """验证 Pattern ID（白名单检查）"""
        from security.input_validator import get_input_validator

        validator = get_input_validator()
        is_valid, error = validator.validate_pattern_id(v)

        if not is_valid:
            raise ValueError(error)

        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """验证并清理输入文本"""
        if not isinstance(v, str):
            raise ValueError(f"文本必须是字符串，当前类型: {type(v).__name__}")

        from security.input_validator import get_input_validator

        validator = get_input_validator()
        is_valid, error, cleaned_text = validator.validate_text(v)

        if not is_valid:
            raise ValueError(error)

        return cleaned_text


class PatternResponse(BaseModel):
    """Pattern 执行响应"""

    request_id: str = Field(..., description="请求 ID")
    success: bool = Field(..., description="是否成功")
    output: str | None = Field(None, description="输出结果")
    metadata: Dict[str, Any] | None = Field(None, description="元数据")
    error: str | None = Field(None, description="错误信息")
    duration: float = Field(..., description="执行时间（秒）")


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="服务状态")
    timestamp: str = Field(..., description="检查时间")
    version: str = Field(..., description="服务版本")
    uptime: float = Field(..., description="运行时间（秒）")
    patterns_loaded: int = Field(..., description="已加载的 Pattern 数量")


class VersionResponse(BaseModel):
    """版本信息响应"""

    python: str = Field(..., description="Python 版本")
    backend: str = Field(..., description="Backend 版本")
    mlx: str | None = Field(None, description="MLX 版本")
    ollama: str | None = Field(None, description="Ollama 版本")


# ==================== 路由 ====================

# 启动时间（用于计算 uptime）
startup_time = datetime.now()


@app.get("/", summary="Root endpoint")
async def root():
    """根路径"""
    return {
        "name": "MacCortex Backend API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """健康检查"""
    try:
        registry: PatternRegistry = app.state.registry
        uptime = (datetime.now() - startup_time).total_seconds()

        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="0.1.0",
            uptime=uptime,
            patterns_loaded=len(registry.list_patterns()),
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy",
        )


@app.get("/version", response_model=VersionResponse, summary="Version info")
async def get_version():
    """获取版本信息"""
    try:
        import platform

        python_version = platform.python_version()

        # 尝试获取 MLX 版本
        mlx_version = None
        try:
            import mlx

            mlx_version = mlx.__version__
        except ImportError:
            pass

        # 尝试获取 Ollama 版本
        ollama_version = None
        try:
            import ollama

            ollama_version = ollama.__version__
        except ImportError:
            pass

        return VersionResponse(
            python=python_version,
            backend="0.1.0",
            mlx=mlx_version,
            ollama=ollama_version,
        )
    except Exception as e:
        logger.error(f"获取版本信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.get("/copyright", summary="Copyright information")
async def get_copyright():
    """
    获取版权信息

    Copyright (c) 2026 Yu Geng. All rights reserved.
    """
    project_info = get_project_info()
    return {
        "copyright": "Copyright (c) 2026 Yu Geng. All rights reserved.",
        "project": "MacCortex - Next-Generation macOS Personal Intelligence Infrastructure",
        "owner": "Yu Geng",
        "email": "james.geng@gmail.com",
        "license": "Proprietary",
        "watermark": project_info.get("watermark"),
        "verified": project_info.get("verified"),
        "warning": "This software is proprietary and confidential. Unauthorized use is prohibited.",
    }


@app.post("/execute", response_model=PatternResponse, summary="Execute pattern")
async def execute_pattern(request: PatternRequest):
    """执行 AI Pattern（Phase 1.5: 含审计日志 + 输入验证）"""
    start_time = datetime.now()

    # Phase 1.5: 获取审计日志器
    from security.audit_logger import get_audit_logger
    audit_logger = get_audit_logger()

    # Phase 1.5 Day 6-7: 获取输入验证器
    from security.input_validator import get_input_validator
    input_validator = get_input_validator()

    try:
        logger.info(f"📥 收到请求: pattern={request.pattern_id}, request_id={request.request_id}")

        # Phase 1.5 Day 6-7: 验证参数（白名单检查）
        is_valid, error, validated_params = input_validator.validate_parameters(
            pattern_id=request.pattern_id,
            parameters=request.parameters,
        )

        if not is_valid:
            logger.warning(f"⚠️ 参数验证失败: {error}")
            raise ValueError(error)

        logger.debug(f"✅ 参数验证通过: {validated_params}")

        registry: PatternRegistry = app.state.registry

        # 执行 Pattern（使用验证后的参数）
        result = await registry.execute(
            pattern_id=request.pattern_id,
            text=request.text,
            parameters=validated_params,
        )

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"✅ 执行成功: duration={duration:.2f}s")

        # Phase 1.5: 记录 Pattern 执行
        security_flags = []
        metadata = result.get("metadata", {})
        if isinstance(metadata, dict) and "security" in metadata:
            security_info = metadata["security"]
            if security_info.get("injection_detected"):
                security_flags.append("injection_detected")

        audit_logger.log_pattern_execution(
            request_id=request.request_id,
            pattern_id=request.pattern_id,
            input_length=len(request.text),
            output_length=len(result["output"]) if result["output"] else 0,
            duration_ms=duration * 1000,
            success=True,
            security_flags=security_flags,
        )

        return PatternResponse(
            request_id=request.request_id,
            success=True,
            output=result["output"],
            metadata=result.get("metadata"),
            error=None,
            duration=duration,
        )

    except ValueError as e:
        # Pattern 不存在或参数无效
        logger.warning(f"⚠️ 请求无效: {e}")
        duration = (datetime.now() - start_time).total_seconds()

        # Phase 1.5: 记录失败
        audit_logger.log_pattern_execution(
            request_id=request.request_id,
            pattern_id=request.pattern_id,
            input_length=len(request.text),
            output_length=0,
            duration_ms=duration * 1000,
            success=False,
        )

        return PatternResponse(
            request_id=request.request_id,
            success=False,
            output=None,
            metadata=None,
            error=str(e),
            duration=duration,
        )

    except Exception as e:
        # 执行失败
        logger.error(f"❌ 执行失败: {e}")
        duration = (datetime.now() - start_time).total_seconds()

        # Phase 1.5: 记录异常
        audit_logger.log_security_event(
            request_id=request.request_id,
            event_subtype="pattern_error",
            severity="high",
            details={
                "pattern_id": request.pattern_id,
                "error": str(e),
            },
        )

        return PatternResponse(
            request_id=request.request_id,
            success=False,
            output=None,
            metadata=None,
            error=str(e),
            duration=duration,
        )


@app.get("/patterns", summary="List patterns")
async def list_patterns():
    """列出所有可用的 Pattern"""
    try:
        registry: PatternRegistry = app.state.registry
        patterns = registry.list_patterns()

        return {
            "total": len(patterns),
            "patterns": patterns,
        }
    except Exception as e:
        logger.error(f"获取 Pattern 列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.exception(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# ==================== 主函数 ====================


def main():
    """启动服务"""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
