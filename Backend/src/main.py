"""
MacCortex Python Backend - FastAPI Application
Phase 1 - Week 2 Day 8-9
创建时间: 2026-01-20

FastAPI 服务，用于执行需要 Python 后端的 AI Pattern
"""

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from patterns.registry import PatternRegistry
from utils.config import Settings

# 加载配置
settings = Settings()

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


# ==================== Pydantic 模型 ====================


class PatternRequest(BaseModel):
    """Pattern 执行请求"""

    pattern_id: str = Field(..., description="Pattern ID")
    text: str = Field(..., description="输入文本")
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


@app.post("/execute", response_model=PatternResponse, summary="Execute pattern")
async def execute_pattern(request: PatternRequest):
    """执行 AI Pattern"""
    start_time = datetime.now()

    try:
        logger.info(f"📥 收到请求: pattern={request.pattern_id}, request_id={request.request_id}")

        registry: PatternRegistry = app.state.registry

        # 执行 Pattern
        result = await registry.execute(
            pattern_id=request.pattern_id,
            text=request.text,
            parameters=request.parameters,
        )

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"✅ 执行成功: duration={duration:.2f}s")

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
