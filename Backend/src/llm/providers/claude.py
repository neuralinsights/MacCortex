#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# Claude Provider Implementation
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""
Anthropic Claude Provider 实现

支持的模型：
- claude-opus-4: 最强大的模型，适合复杂推理
- claude-sonnet-4: 平衡性能与成本
- claude-haiku-3.5: 快速响应，适合简单任务
"""

import logging
import time
from decimal import Decimal
from typing import AsyncIterator, Optional

from ..models import (
    CostInfo,
    LLMResponse,
    ModelConfig,
    ModelInfo,
    ProviderType,
    TokenUsage,
)
from ..protocol import BaseLLMProvider

logger = logging.getLogger(__name__)


# Claude 模型定价表 (2026-01, USD per 1M tokens)
CLAUDE_PRICING = {
    "claude-opus-4": {
        "input": Decimal("15.00"),
        "output": Decimal("75.00"),
        "display_name": "Claude Opus 4",
        "max_tokens": 8192,
        "context_window": 200000,
    },
    "claude-sonnet-4": {
        "input": Decimal("3.00"),
        "output": Decimal("15.00"),
        "display_name": "Claude Sonnet 4",
        "max_tokens": 8192,
        "context_window": 200000,
    },
    "claude-haiku-3.5": {
        "input": Decimal("0.80"),
        "output": Decimal("4.00"),
        "display_name": "Claude Haiku 3.5",
        "max_tokens": 8192,
        "context_window": 200000,
    },
}


class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude Provider

    使用 Anthropic Python SDK 调用 Claude API

    Example:
        >>> provider = ClaudeProvider(api_key="sk-ant-...")
        >>> response = await provider.invoke(
        ...     model_id="claude-sonnet-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.content)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化 Claude Provider

        Args:
            api_key: Anthropic API Key（可选，从环境变量读取）
            base_url: API 基础 URL（可选，用于代理）
        """
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._client = None
        self._async_client = None

        # 注册模型
        self._register_models()

    def _register_models(self) -> None:
        """注册 Claude 模型"""
        for model_id, pricing in CLAUDE_PRICING.items():
            self.register_model(
                ModelInfo(
                    id=model_id,
                    display_name=pricing["display_name"],
                    provider=ProviderType.ANTHROPIC,
                    input_price_per_1m=pricing["input"],
                    output_price_per_1m=pricing["output"],
                    max_tokens=pricing["max_tokens"],
                    context_window=pricing["context_window"],
                    supports_streaming=True,
                    supports_tools=True,
                    is_available=self.is_available,
                )
            )

    def _get_client(self):
        """获取或创建 Anthropic 客户端（同步）"""
        if self._client is None:
            try:
                import anthropic

                kwargs = {}
                if self._api_key:
                    kwargs["api_key"] = self._api_key
                if self._base_url:
                    kwargs["base_url"] = self._base_url

                self._client = anthropic.Anthropic(**kwargs)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    def _get_async_client(self):
        """获取或创建 Anthropic 异步客户端"""
        if self._async_client is None:
            try:
                import anthropic

                kwargs = {}
                if self._api_key:
                    kwargs["api_key"] = self._api_key
                if self._base_url:
                    kwargs["base_url"] = self._base_url

                self._async_client = anthropic.AsyncAnthropic(**kwargs)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
        return self._async_client

    @property
    def name(self) -> str:
        return "Anthropic"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC

    @property
    def is_available(self) -> bool:
        """检查 API Key 是否已配置"""
        import os

        key = self._api_key or os.environ.get("ANTHROPIC_API_KEY")
        return bool(key)

    async def invoke(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        """
        调用 Claude API

        Args:
            model_id: 模型 ID（claude-opus-4, claude-sonnet-4, claude-haiku-3.5）
            messages: 消息列表
            config: 模型配置

        Returns:
            LLMResponse: 统一响应格式
        """
        model = self._validate_model(model_id)
        self._validate_messages(messages)
        config = config or ModelConfig.default()

        # 转换消息格式（分离 system 消息）
        system_message = None
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                api_messages.append(msg)

        # 调用 API
        start_time = time.perf_counter()
        try:
            client = self._get_async_client()

            kwargs = {
                "model": self._get_api_model_id(model_id),
                "messages": api_messages,
                "max_tokens": min(config.max_tokens, model.max_tokens),
                "temperature": config.temperature,
            }
            if system_message:
                kwargs["system"] = system_message
            if config.stop_sequences:
                kwargs["stop_sequences"] = config.stop_sequences

            response = await client.messages.create(**kwargs)

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise RuntimeError(f"Claude API call failed: {e}") from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        # 提取 Token 使用量
        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            cached_tokens=getattr(response.usage, "cache_read_input_tokens", 0) or 0,
        )

        # 计算成本
        cost = self.calculate_cost(model_id, usage)

        # 提取内容
        content = ""
        if response.content:
            content = response.content[0].text if response.content else ""

        self._last_usage = usage

        return LLMResponse(
            content=content,
            usage=usage,
            cost=cost,
            model_id=model_id,
            provider=self.provider_type,
            latency_ms=latency_ms,
            finish_reason=response.stop_reason or "stop",
            raw_response=response,
        )

    async def stream(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        """
        流式调用 Claude API

        Args:
            model_id: 模型 ID
            messages: 消息列表
            config: 模型配置

        Yields:
            str: 响应内容片段
        """
        model = self._validate_model(model_id)
        self._validate_messages(messages)
        config = config or ModelConfig.default()

        # 转换消息格式
        system_message = None
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                api_messages.append(msg)

        client = self._get_async_client()

        kwargs = {
            "model": self._get_api_model_id(model_id),
            "messages": api_messages,
            "max_tokens": min(config.max_tokens, model.max_tokens),
            "temperature": config.temperature,
        }
        if system_message:
            kwargs["system"] = system_message

        total_input_tokens = 0
        total_output_tokens = 0

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

            # 获取最终使用量
            final_message = await stream.get_final_message()
            total_input_tokens = final_message.usage.input_tokens
            total_output_tokens = final_message.usage.output_tokens

        self._last_usage = TokenUsage(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
        )

    def _get_api_model_id(self, model_id: str) -> str:
        """将内部模型 ID 转换为 API 模型 ID"""
        # Claude 模型 ID 映射
        mapping = {
            "claude-opus-4": "claude-opus-4-20250514",
            "claude-sonnet-4": "claude-sonnet-4-20250514",
            "claude-haiku-3.5": "claude-3-5-haiku-20241022",
        }
        return mapping.get(model_id, model_id)

    async def health_check(self) -> bool:
        """健康检查：发送简单请求验证 API 可用性"""
        if not self.is_available:
            return False

        try:
            response = await self.invoke(
                model_id="claude-haiku-3.5",
                messages=[{"role": "user", "content": "ping"}],
                config=ModelConfig(max_tokens=1, temperature=0),
            )
            return bool(response.content)
        except Exception as e:
            logger.warning(f"Claude health check failed: {e}")
            return False
