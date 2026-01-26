#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# OpenAI Provider Implementation
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""
OpenAI Provider 实现

支持的模型：
- gpt-4o: 最新旗舰模型
- gpt-4o-mini: 轻量高效版本
- o1: 推理模型（慢但深度思考）
- o3-mini: 新一代推理模型
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


# OpenAI 模型定价表 (2026-01, USD per 1M tokens)
OPENAI_PRICING = {
    "gpt-4o": {
        "input": Decimal("2.50"),
        "output": Decimal("10.00"),
        "display_name": "GPT-4o",
        "max_tokens": 16384,
        "context_window": 128000,
    },
    "gpt-4o-mini": {
        "input": Decimal("0.15"),
        "output": Decimal("0.60"),
        "display_name": "GPT-4o Mini",
        "max_tokens": 16384,
        "context_window": 128000,
    },
    "o1": {
        "input": Decimal("15.00"),
        "output": Decimal("60.00"),
        "display_name": "o1 (Reasoning)",
        "max_tokens": 100000,
        "context_window": 200000,
        "supports_streaming": False,  # o1 不支持流式
    },
    "o3-mini": {
        "input": Decimal("1.10"),
        "output": Decimal("4.40"),
        "display_name": "o3-mini (Reasoning)",
        "max_tokens": 100000,
        "context_window": 200000,
        "supports_streaming": False,
    },
}


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI Provider

    使用 OpenAI Python SDK 调用 GPT/o1 API

    Example:
        >>> provider = OpenAIProvider(api_key="sk-...")
        >>> response = await provider.invoke(
        ...     model_id="gpt-4o",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.content)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
    ):
        """
        初始化 OpenAI Provider

        Args:
            api_key: OpenAI API Key（可选，从环境变量读取）
            base_url: API 基础 URL（可选，用于代理）
            organization: 组织 ID（可选）
        """
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._organization = organization
        self._async_client = None

        # 注册模型
        self._register_models()

    def _register_models(self) -> None:
        """注册 OpenAI 模型"""
        for model_id, pricing in OPENAI_PRICING.items():
            self.register_model(
                ModelInfo(
                    id=model_id,
                    display_name=pricing["display_name"],
                    provider=ProviderType.OPENAI,
                    input_price_per_1m=pricing["input"],
                    output_price_per_1m=pricing["output"],
                    max_tokens=pricing["max_tokens"],
                    context_window=pricing["context_window"],
                    supports_streaming=pricing.get("supports_streaming", True),
                    supports_tools=True,
                    is_available=self.is_available,
                )
            )

    def _get_async_client(self):
        """获取或创建 OpenAI 异步客户端"""
        if self._async_client is None:
            try:
                from openai import AsyncOpenAI

                kwargs = {}
                if self._api_key:
                    kwargs["api_key"] = self._api_key
                if self._base_url:
                    kwargs["base_url"] = self._base_url
                if self._organization:
                    kwargs["organization"] = self._organization

                self._async_client = AsyncOpenAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )
        return self._async_client

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI

    @property
    def is_available(self) -> bool:
        """检查 API Key 是否已配置"""
        import os

        key = self._api_key or os.environ.get("OPENAI_API_KEY")
        return bool(key)

    async def invoke(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        """
        调用 OpenAI API

        Args:
            model_id: 模型 ID
            messages: 消息列表
            config: 模型配置

        Returns:
            LLMResponse: 统一响应格式
        """
        model = self._validate_model(model_id)
        self._validate_messages(messages)
        config = config or ModelConfig.default()

        # 调用 API
        start_time = time.perf_counter()
        try:
            client = self._get_async_client()

            kwargs = {
                "model": model_id,
                "messages": messages,
                "max_completion_tokens": min(config.max_tokens, model.max_tokens),
            }

            # o1/o3 模型不支持 temperature
            if not model_id.startswith("o"):
                kwargs["temperature"] = config.temperature

            if config.stop_sequences:
                kwargs["stop"] = config.stop_sequences

            response = await client.chat.completions.create(**kwargs)

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API call failed: {e}") from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        # 提取 Token 使用量
        usage_data = response.usage
        usage = TokenUsage(
            input_tokens=usage_data.prompt_tokens,
            output_tokens=usage_data.completion_tokens,
            total_tokens=usage_data.total_tokens,
        )

        # 计算成本
        cost = self.calculate_cost(model_id, usage)

        # 提取内容
        content = response.choices[0].message.content or ""

        self._last_usage = usage

        return LLMResponse(
            content=content,
            usage=usage,
            cost=cost,
            model_id=model_id,
            provider=self.provider_type,
            latency_ms=latency_ms,
            finish_reason=response.choices[0].finish_reason or "stop",
            raw_response=response,
        )

    async def stream(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        """
        流式调用 OpenAI API

        Args:
            model_id: 模型 ID
            messages: 消息列表
            config: 模型配置

        Yields:
            str: 响应内容片段
        """
        model = self._validate_model(model_id)

        if not model.supports_streaming:
            # o1/o3 模型不支持流式，回退到普通调用
            response = await self.invoke(model_id, messages, config)
            yield response.content
            return

        self._validate_messages(messages)
        config = config or ModelConfig.default()

        client = self._get_async_client()

        kwargs = {
            "model": model_id,
            "messages": messages,
            "max_completion_tokens": min(config.max_tokens, model.max_tokens),
            "temperature": config.temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        total_tokens = 0
        input_tokens = 0
        output_tokens = 0

        async with client.chat.completions.stream(**kwargs) as stream:
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

                # 获取最终使用量
                if chunk.usage:
                    input_tokens = chunk.usage.prompt_tokens
                    output_tokens = chunk.usage.completion_tokens
                    total_tokens = chunk.usage.total_tokens

        self._last_usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    async def health_check(self) -> bool:
        """健康检查"""
        if not self.is_available:
            return False

        try:
            response = await self.invoke(
                model_id="gpt-4o-mini",
                messages=[{"role": "user", "content": "ping"}],
                config=ModelConfig(max_tokens=1, temperature=0),
            )
            return bool(response.content)
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
