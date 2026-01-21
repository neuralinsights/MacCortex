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
from typing import Any, Dict, List

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


class BatchTranslationItem(BaseModel):
    """批量翻译单个条目（Phase 3 Backend 优化 2）"""

    text: str = Field(..., description="待翻译文本", max_length=50_000)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="翻译参数")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Hello, world!",
                    "parameters": {"target_language": "zh-CN", "style": "casual"},
                }
            ]
        }
    }


class BatchPatternRequest(BaseModel):
    """批量 Pattern 执行请求（Phase 3 Backend 优化 2）"""

    pattern_id: str = Field(..., description="Pattern ID（仅支持 'translate'）", max_length=50)
    items: List[BatchTranslationItem] = Field(..., description="批量翻译条目列表", max_length=100)
    request_id: str = Field(default="", description="请求 ID（可选）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "pattern_id": "translate",
                    "items": [
                        {"text": "Hello", "parameters": {"target_language": "zh-CN"}},
                        {"text": "World", "parameters": {"target_language": "zh-CN"}},
                    ],
                    "request_id": "batch-req-12345",
                }
            ]
        }
    }

    @field_validator("pattern_id")
    @classmethod
    def validate_pattern_id(cls, v: str) -> str:
        """验证 Pattern ID（批量处理仅支持 translate）"""
        if v != "translate":
            raise ValueError("批量处理仅支持 'translate' pattern")
        return v

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: List[BatchTranslationItem]) -> List[BatchTranslationItem]:
        """验证批量条目"""
        if len(v) == 0:
            raise ValueError("批量条目列表不能为空")
        if len(v) > 100:
            raise ValueError("批量条目最多 100 个")
        return v


class BatchItemResponse(BaseModel):
    """批量处理单个条目响应"""

    index: int = Field(..., description="条目索引")
    success: bool = Field(..., description="是否成功")
    output: str | None = Field(None, description="输出结果")
    metadata: Dict[str, Any] | None = Field(None, description="元数据")
    error: str | None = Field(None, description="错误信息")
    duration: float = Field(..., description="执行时间（秒）")


class BatchPatternResponse(BaseModel):
    """批量 Pattern 执行响应（Phase 3 Backend 优化 2）"""

    request_id: str = Field(..., description="请求 ID")
    success: bool = Field(..., description="整体是否成功")
    total: int = Field(..., description="总条目数")
    succeeded: int = Field(..., description="成功条目数")
    failed: int = Field(..., description="失败条目数")
    items: List[BatchItemResponse] = Field(..., description="各条目响应")
    aggregate_stats: Dict[str, Any] = Field(..., description="聚合统计")
    duration: float = Field(..., description="总执行时间（秒）")


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


@app.post("/execute/batch", response_model=BatchPatternResponse, summary="Execute batch translation")
async def execute_pattern_batch(request: BatchPatternRequest):
    """
    批量执行翻译 Pattern（Phase 3 Backend 优化 2）

    特性：
    - 支持一次请求翻译多个文本（最多 100 个）
    - 充分利用翻译缓存（重复文本直接命中）
    - 返回聚合统计（总耗时、缓存命中率、加速倍数）
    - 单个失败不影响其他条目

    使用场景：
    - 批量翻译剪贴板历史
    - 文档段落批量翻译
    - 会话记录批量翻译
    """
    start_time = datetime.now()

    # Phase 1.5: 获取审计日志器
    from security.audit_logger import get_audit_logger
    audit_logger = get_audit_logger()

    # Phase 1.5 Day 6-7: 获取输入验证器
    from security.input_validator import get_input_validator
    input_validator = get_input_validator()

    try:
        logger.info(
            f"📥 收到批量请求: pattern={request.pattern_id}, "
            f"items={len(request.items)}, request_id={request.request_id}"
        )

        registry: PatternRegistry = app.state.registry

        # 批量执行
        items_responses: List[BatchItemResponse] = []
        succeeded = 0
        failed = 0
        total_cache_hits = 0
        total_cache_misses = 0

        for idx, item in enumerate(request.items):
            item_start = datetime.now()

            try:
                # Phase 1.5 Day 6-7: 验证参数（白名单检查）
                is_valid, error, validated_params = input_validator.validate_parameters(
                    pattern_id=request.pattern_id,
                    parameters=item.parameters,
                )

                if not is_valid:
                    raise ValueError(error)

                # 执行翻译
                result = await registry.execute(
                    pattern_id=request.pattern_id,
                    text=item.text,
                    parameters=validated_params,
                )

                item_duration = (datetime.now() - item_start).total_seconds()

                # 统计缓存命中
                metadata = result.get("metadata", {})
                if isinstance(metadata, dict):
                    if metadata.get("cached"):
                        total_cache_hits += 1
                    else:
                        total_cache_misses += 1

                items_responses.append(
                    BatchItemResponse(
                        index=idx,
                        success=True,
                        output=result["output"],
                        metadata=metadata,
                        error=None,
                        duration=item_duration,
                    )
                )
                succeeded += 1

            except Exception as e:
                # 单个条目失败不影响其他条目
                logger.warning(f"⚠️ 批量请求第 {idx} 项失败: {e}")
                item_duration = (datetime.now() - item_start).total_seconds()

                items_responses.append(
                    BatchItemResponse(
                        index=idx,
                        success=False,
                        output=None,
                        metadata=None,
                        error=str(e),
                        duration=item_duration,
                    )
                )
                failed += 1

        duration = (datetime.now() - start_time).total_seconds()

        # 计算聚合统计
        total_requests = total_cache_hits + total_cache_misses
        cache_hit_rate = total_cache_hits / total_requests if total_requests > 0 else 0.0

        # 估算加速倍数（假设未缓存翻译平均 2.5 秒，缓存翻译平均 0.01 秒）
        estimated_no_cache_time = len(request.items) * 2.5  # 假设每个翻译 2.5 秒
        actual_time = duration
        speedup = estimated_no_cache_time / actual_time if actual_time > 0 else 1.0

        aggregate_stats = {
            "total_items": len(request.items),
            "succeeded": succeeded,
            "failed": failed,
            "cache_hits": total_cache_hits,
            "cache_misses": total_cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "total_duration": duration,
            "avg_item_duration": duration / len(request.items) if len(request.items) > 0 else 0.0,
            "estimated_speedup": f"{speedup:.1f}x",
        }

        logger.info(
            f"✅ 批量执行完成: total={len(request.items)}, succeeded={succeeded}, "
            f"failed={failed}, cache_hit_rate={cache_hit_rate:.1%}, duration={duration:.2f}s"
        )

        # Phase 1.5: 记录批量执行
        audit_logger.log_pattern_execution(
            request_id=request.request_id,
            pattern_id=f"{request.pattern_id}_batch",
            input_length=sum(len(item.text) for item in request.items),
            output_length=sum(
                len(resp.output) if resp.output else 0 for resp in items_responses
            ),
            duration_ms=duration * 1000,
            success=(failed == 0),
            security_flags=[],
        )

        return BatchPatternResponse(
            request_id=request.request_id,
            success=(failed == 0),
            total=len(request.items),
            succeeded=succeeded,
            failed=failed,
            items=items_responses,
            aggregate_stats=aggregate_stats,
            duration=duration,
        )

    except Exception as e:
        # 批量执行失败
        logger.error(f"❌ 批量执行失败: {e}")
        duration = (datetime.now() - start_time).total_seconds()

        # Phase 1.5: 记录异常
        audit_logger.log_security_event(
            request_id=request.request_id,
            event_subtype="batch_pattern_error",
            severity="high",
            details={
                "pattern_id": request.pattern_id,
                "items_count": len(request.items),
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量执行失败: {str(e)}",
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
