#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# LLM Provider Protocol
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""
LLM Provider 协议定义

提供统一的 Provider 接口抽象：
- LLMProviderProtocol: 所有 Provider 必须实现的协议
- 支持同步和异步调用
- 内置 Token 计数和成本计算
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from .models import (
    CostInfo,
    LLMResponse,
    ModelConfig,
    ModelInfo,
    ProviderType,
    TokenUsage,
)


class LLMProviderProtocol(ABC):
    """
    LLM Provider 协议 (Abstract Base Class)

    所有 LLM Provider 必须实现此协议：
    - Anthropic (Claude)
    - OpenAI (GPT-4, o1)
    - Ollama (本地)
    - DeepSeek
    - Google Gemini
    - MLX (Apple Silicon)

    Example:
        >>> class ClaudeProvider(LLMProviderProtocol):
        ...     @property
        ...     def name(self) -> str:
        ...         return "Anthropic"
        ...
        ...     async def invoke(self, model_id, messages, config):
        ...         # 实现调用逻辑
        ...         pass
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider 名称

        Returns:
            str: Provider 显示名称（如 "Anthropic", "OpenAI"）
        """
        ...

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """
        Provider 类型枚举

        Returns:
            ProviderType: Provider 类型
        """
        ...

    @property
    @abstractmethod
    def models(self) -> list[ModelInfo]:
        """
        获取该 Provider 支持的所有模型

        Returns:
            list[ModelInfo]: 模型信息列表
        """
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查 Provider 是否可用

        检查条件：
        - Cloud Provider: API Key 已配置且有效
        - Local Provider: 服务正在运行

        Returns:
            bool: 是否可用
        """
        ...

    @abstractmethod
    async def invoke(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        """
        调用 LLM 生成响应

        Args:
            model_id: 模型标识符（如 "claude-sonnet-4", "gpt-4o"）
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            config: 模型配置（可选，使用默认配置）

        Returns:
            LLMResponse: 统一响应格式，包含内容、Token 使用量和成本

        Raises:
            ValueError: 模型 ID 无效
            ConnectionError: 网络连接失败
            TimeoutError: 请求超时
            RuntimeError: API 调用失败
        """
        ...

    @abstractmethod
    async def stream(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        """
        流式调用 LLM 生成响应

        Args:
            model_id: 模型标识符
            messages: 消息列表
            config: 模型配置

        Yields:
            str: 响应内容片段

        Note:
            流式调用结束后，应调用 get_last_usage() 获取 Token 使用量
        """
        ...

    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        获取指定模型的详细信息

        Args:
            model_id: 模型标识符

        Returns:
            ModelInfo: 模型信息，如果模型不存在则返回 None
        """
        ...

    @abstractmethod
    def get_pricing(self, model_id: str) -> tuple[float, float]:
        """
        获取模型定价

        Args:
            model_id: 模型标识符

        Returns:
            tuple[float, float]: (每百万输入 Token 价格, 每百万输出 Token 价格) USD

        Raises:
            ValueError: 模型 ID 无效
        """
        ...

    def calculate_cost(self, model_id: str, usage: TokenUsage) -> CostInfo:
        """
        计算调用成本

        Args:
            model_id: 模型标识符
            usage: Token 使用统计

        Returns:
            CostInfo: 成本信息
        """
        input_price, output_price = self.get_pricing(model_id)
        from decimal import Decimal
        return CostInfo.calculate(
            usage,
            Decimal(str(input_price)),
            Decimal(str(output_price)),
        )

    def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> CostInfo:
        """
        预估调用成本

        Args:
            model_id: 模型标识符
            input_tokens: 预估输入 Token 数量
            output_tokens: 预估输出 Token 数量

        Returns:
            CostInfo: 预估成本信息
        """
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
        return self.calculate_cost(model_id, usage)

    async def health_check(self) -> bool:
        """
        健康检查

        验证 Provider 是否正常工作（可选实现）

        Returns:
            bool: 是否健康
        """
        return self.is_available

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} available={self.is_available}>"


class BaseLLMProvider(LLMProviderProtocol):
    """
    LLM Provider 基类

    提供通用实现，减少子类代码重复：
    - 模型注册与查找
    - 定价管理
    - 错误处理
    """

    def __init__(self):
        self._models: dict[str, ModelInfo] = {}
        self._last_usage: Optional[TokenUsage] = None

    def register_model(self, model: ModelInfo) -> None:
        """注册模型"""
        self._models[model.id] = model

    def register_models(self, models: list[ModelInfo]) -> None:
        """批量注册模型"""
        for model in models:
            self.register_model(model)

    @property
    def models(self) -> list[ModelInfo]:
        """获取所有已注册模型"""
        return list(self._models.values())

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        return self._models.get(model_id)

    def get_pricing(self, model_id: str) -> tuple[float, float]:
        """获取模型定价"""
        model = self.get_model_info(model_id)
        if not model:
            raise ValueError(f"Unknown model: {model_id}")
        return float(model.input_price_per_1m), float(model.output_price_per_1m)

    def get_last_usage(self) -> Optional[TokenUsage]:
        """获取最后一次调用的 Token 使用量（用于流式调用后）"""
        return self._last_usage

    def _validate_model(self, model_id: str) -> ModelInfo:
        """验证模型 ID 并返回模型信息"""
        model = self.get_model_info(model_id)
        if not model:
            available = ", ".join(self._models.keys())
            raise ValueError(
                f"Unknown model: {model_id}. Available models: {available}"
            )
        return model

    def _validate_messages(self, messages: list[dict]) -> None:
        """验证消息格式"""
        if not messages:
            raise ValueError("Messages cannot be empty")
        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Each message must have 'role' and 'content' keys")
            if msg["role"] not in ("system", "user", "assistant", "tool"):
                raise ValueError(f"Invalid role: {msg['role']}")
