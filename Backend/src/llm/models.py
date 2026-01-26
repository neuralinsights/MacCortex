#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# LLM Data Models
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""
LLM 数据模型定义

提供类型安全的数据结构：
- TokenUsage: Token 使用统计
- CostInfo: 成本信息
- LLMResponse: 统一响应格式
- ModelInfo: 模型元信息
- ModelConfig: 模型配置
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional


class ProviderType(str, Enum):
    """LLM Provider 类型枚举"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    MLX = "mlx"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        names = {
            ProviderType.ANTHROPIC: "Anthropic (Claude)",
            ProviderType.OPENAI: "OpenAI",
            ProviderType.OLLAMA: "Ollama (Local)",
            ProviderType.DEEPSEEK: "DeepSeek",
            ProviderType.GEMINI: "Google Gemini",
            ProviderType.MLX: "MLX (Apple Silicon)",
        }
        return names.get(self, self.value)

    @property
    def is_local(self) -> bool:
        """是否为本地模型"""
        return self in (ProviderType.OLLAMA, ProviderType.MLX)


@dataclass(frozen=True)
class TokenUsage:
    """
    Token 使用统计

    Attributes:
        input_tokens: 输入 Token 数量
        output_tokens: 输出 Token 数量
        total_tokens: 总 Token 数量
        cached_tokens: 缓存命中的 Token 数量（可选）
    """
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_tokens: int = 0

    def __post_init__(self):
        """验证 Token 数量"""
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ValueError("Token counts cannot be negative")
        # 允许 total 不等于 input + output（某些 API 会包含 reasoning tokens）

    @classmethod
    def zero(cls) -> "TokenUsage":
        """返回零使用量"""
        return cls(input_tokens=0, output_tokens=0, total_tokens=0)

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """累加 Token 使用量"""
        if not isinstance(other, TokenUsage):
            return NotImplemented
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
        )


@dataclass(frozen=True)
class CostInfo:
    """
    成本信息（USD）

    Attributes:
        input_cost: 输入成本 (USD)
        output_cost: 输出成本 (USD)
        total_cost: 总成本 (USD)
    """
    input_cost: Decimal
    output_cost: Decimal
    total_cost: Decimal

    def __post_init__(self):
        """验证成本"""
        if self.input_cost < 0 or self.output_cost < 0 or self.total_cost < 0:
            raise ValueError("Cost cannot be negative")

    @classmethod
    def zero(cls) -> "CostInfo":
        """返回零成本"""
        return cls(
            input_cost=Decimal("0"),
            output_cost=Decimal("0"),
            total_cost=Decimal("0"),
        )

    @classmethod
    def calculate(
        cls,
        usage: TokenUsage,
        input_price_per_1m: Decimal,
        output_price_per_1m: Decimal,
    ) -> "CostInfo":
        """
        根据 Token 使用量和定价计算成本

        Args:
            usage: Token 使用统计
            input_price_per_1m: 每百万输入 Token 价格 (USD)
            output_price_per_1m: 每百万输出 Token 价格 (USD)

        Returns:
            CostInfo: 计算后的成本信息
        """
        input_cost = Decimal(usage.input_tokens) * input_price_per_1m / Decimal("1000000")
        output_cost = Decimal(usage.output_tokens) * output_price_per_1m / Decimal("1000000")
        total_cost = input_cost + output_cost
        return cls(
            input_cost=input_cost.quantize(Decimal("0.000001")),
            output_cost=output_cost.quantize(Decimal("0.000001")),
            total_cost=total_cost.quantize(Decimal("0.000001")),
        )

    def __add__(self, other: "CostInfo") -> "CostInfo":
        """累加成本"""
        if not isinstance(other, CostInfo):
            return NotImplemented
        return CostInfo(
            input_cost=self.input_cost + other.input_cost,
            output_cost=self.output_cost + other.output_cost,
            total_cost=self.total_cost + other.total_cost,
        )

    @property
    def formatted_total(self) -> str:
        """格式化总成本显示"""
        return f"${self.total_cost:.6f}"


@dataclass
class LLMResponse:
    """
    统一 LLM 响应格式

    Attributes:
        content: 响应内容（文本）
        usage: Token 使用统计
        cost: 成本信息
        model_id: 模型标识符
        provider: Provider 类型
        latency_ms: 响应延迟（毫秒）
        finish_reason: 结束原因（stop, length, tool_calls 等）
        raw_response: 原始响应数据（可选，用于调试）
        created_at: 响应创建时间
    """
    content: str
    usage: TokenUsage
    cost: CostInfo
    model_id: str
    provider: ProviderType
    latency_ms: float
    finish_reason: str = "stop"
    raw_response: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """转换为字典（用于 API 响应）"""
        return {
            "content": self.content,
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
                "total_tokens": self.usage.total_tokens,
            },
            "cost": {
                "input_cost": str(self.cost.input_cost),
                "output_cost": str(self.cost.output_cost),
                "total_cost": str(self.cost.total_cost),
                "formatted_total": self.cost.formatted_total,
            },
            "model_id": self.model_id,
            "provider": self.provider.value,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class ModelInfo:
    """
    模型元信息

    Attributes:
        id: 模型标识符（如 claude-opus-4, gpt-4o）
        display_name: 显示名称
        provider: Provider 类型
        input_price_per_1m: 每百万输入 Token 价格 (USD)
        output_price_per_1m: 每百万输出 Token 价格 (USD)
        max_tokens: 最大输出 Token 数量
        context_window: 上下文窗口大小
        supports_streaming: 是否支持流式输出
        supports_tools: 是否支持工具调用
        is_available: 是否可用（已配置 API Key 且服务可达）
    """
    id: str
    display_name: str
    provider: ProviderType
    input_price_per_1m: Decimal
    output_price_per_1m: Decimal
    max_tokens: int = 4096
    context_window: int = 128000
    supports_streaming: bool = True
    supports_tools: bool = True
    is_available: bool = True

    @property
    def is_local(self) -> bool:
        """是否为本地模型"""
        return self.provider.is_local

    @property
    def is_free(self) -> bool:
        """是否为免费模型（本地模型）"""
        return self.input_price_per_1m == 0 and self.output_price_per_1m == 0

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> CostInfo:
        """估算成本"""
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
        return CostInfo.calculate(usage, self.input_price_per_1m, self.output_price_per_1m)


@dataclass
class ModelConfig:
    """
    模型调用配置

    Attributes:
        temperature: 温度参数 (0.0 - 2.0)
        max_tokens: 最大输出 Token 数量
        top_p: Top-p 采样参数
        top_k: Top-k 采样参数（部分模型支持）
        stop_sequences: 停止序列列表
        timeout_seconds: 请求超时时间（秒）
        retry_count: 重试次数
        metadata: 额外元数据
    """
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    top_k: Optional[int] = None
    stop_sequences: list[str] = field(default_factory=list)
    timeout_seconds: float = 120.0
    retry_count: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """验证配置"""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be positive")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @classmethod
    def default(cls) -> "ModelConfig":
        """返回默认配置"""
        return cls()

    @classmethod
    def for_coding(cls) -> "ModelConfig":
        """返回代码生成优化配置"""
        return cls(
            temperature=0.3,
            max_tokens=8192,
            top_p=0.95,
        )

    @classmethod
    def for_planning(cls) -> "ModelConfig":
        """返回规划任务优化配置"""
        return cls(
            temperature=0.5,
            max_tokens=4096,
            top_p=0.9,
        )

    @classmethod
    def for_review(cls) -> "ModelConfig":
        """返回代码审查优化配置"""
        return cls(
            temperature=0.2,
            max_tokens=2048,
            top_p=0.9,
        )
