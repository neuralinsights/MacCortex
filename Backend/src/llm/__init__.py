#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# LLM Abstraction Layer
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""
LLM 抽象层模块

提供统一的多 LLM Provider 支持：
- LLMProviderProtocol: 统一接口抽象
- ModelRouterV2: 智能路由与 Fallback
- UsageTracker: Token 计数与成本追踪
- Providers: Claude, OpenAI, Ollama, DeepSeek, Gemini, MLX
"""

from .models import (
    TokenUsage,
    CostInfo,
    LLMResponse,
    ModelInfo,
    ModelConfig,
    ProviderType,
)
from .protocol import LLMProviderProtocol
from .router import ModelRouterV2, create_default_router
from .usage_tracker import UsageTracker

__all__ = [
    # Data Models
    "TokenUsage",
    "CostInfo",
    "LLMResponse",
    "ModelInfo",
    "ModelConfig",
    "ProviderType",
    # Protocol
    "LLMProviderProtocol",
    # Router
    "ModelRouterV2",
    "create_default_router",
    # Tracker
    "UsageTracker",
]
