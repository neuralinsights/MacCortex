#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# LLM Providers Package
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""
LLM Provider 实现模块

包含各 LLM 服务的具体实现：
- ClaudeProvider: Anthropic Claude 模型
- OpenAIProvider: OpenAI GPT/o1 模型
- OllamaProvider: Ollama 本地模型
- DeepSeekProvider: DeepSeek 模型 (P1)
- GeminiProvider: Google Gemini 模型 (P1)
- MLXProvider: Apple MLX 本地模型 (P2)
"""

from .claude import ClaudeProvider
from .openai import OpenAIProvider
from .ollama import OllamaProvider

# P1 Providers (可选导入)
try:
    from .deepseek import DeepSeekProvider
except ImportError:
    DeepSeekProvider = None

try:
    from .gemini import GeminiProvider
except ImportError:
    GeminiProvider = None

# P2 Providers (可选导入)
try:
    from .mlx import MLXProvider
except ImportError:
    MLXProvider = None

__all__ = [
    # P0 Providers (核心)
    "ClaudeProvider",
    "OpenAIProvider",
    "OllamaProvider",
    # P1 Providers (扩展)
    "DeepSeekProvider",
    "GeminiProvider",
    # P2 Providers (实验)
    "MLXProvider",
]
