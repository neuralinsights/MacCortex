#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# DeepSeek Provider Implementation
# Phase 5 - Multi-LLM Support (P1 Extension)
# Created: 2026-01-26
#

"""
DeepSeek Provider 实现

支持的模型：
- deepseek-chat: 通用对话模型（高性价比）
- deepseek-reasoner: 推理模型（R1系列）

特点：
- 极低成本（$0.27/1M 输入，$1.10/1M 输出）
- 支持 64K 上下文
- OpenAI 兼容 API
"""

import logging
import time
from decimal import Decimal
from typing import AsyncIterator, Optional

from ..models import (
    LLMResponse,
    ModelConfig,
    ModelInfo,
    ProviderType,
    TokenUsage,
)
from ..protocol import BaseLLMProvider

logger = logging.getLogger(__name__)


# DeepSeek 模型定价表 (2026-01, USD per 1M tokens)
# 参考: https://platform.deepseek.com/api-docs/pricing
DEEPSEEK_PRICING = {
    "deepseek-chat": {
        "input": Decimal("0.27"),
        "output": Decimal("1.10"),
        "display_name": "DeepSeek Chat",
        "max_tokens": 8192,
        "context_window": 65536,
    },
    "deepseek-reasoner": {
        "input": Decimal("0.55"),
        "output": Decimal("2.19"),
        "display_name": "DeepSeek Reasoner (R1)",
        "max_tokens": 8192,
        "context_window": 65536,
        "supports_streaming": True,
    },
}


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek Provider

    使用 DeepSeek OpenAI 兼容 API 调用模型

    Example:
        >>> provider = DeepSeekProvider(api_key="sk-...")
        >>> response = await provider.invoke(
        ...     model_id="deepseek-chat",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.content)
    """

    # DeepSeek API 基础 URL
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化 DeepSeek Provider

        Args:
            api_key: DeepSeek API Key（可选，从环境变量读取）
            base_url: API 基础 URL（可选，默认使用官方 API）
        """
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._async_client = None

        # 注册模型
        self._register_models()

    def _register_models(self) -> None:
        """注册 DeepSeek 模型"""
        for model_id, pricing in DEEPSEEK_PRICING.items():
            self.register_model(
                ModelInfo(
                    id=model_id,
                    display_name=pricing["display_name"],
                    provider=ProviderType.DEEPSEEK,
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
        """获取或创建 OpenAI 兼容异步客户端"""
        if self._async_client is None:
            try:
                from openai import AsyncOpenAI

                import os
                api_key = self._api_key or os.environ.get("DEEPSEEK_API_KEY")

                if not api_key:
                    raise ValueError(
                        "DeepSeek API key not found. "
                        "Set DEEPSEEK_API_KEY environment variable or pass api_key parameter."
                    )

                self._async_client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=self._base_url,
                )
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )
        return self._async_client

    @property
    def name(self) -> str:
        return "DeepSeek"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.DEEPSEEK

    @property
    def is_available(self) -> bool:
        """检查 API Key 是否已配置"""
        import os

        key = self._api_key or os.environ.get("DEEPSEEK_API_KEY")
        return bool(key)

    async def invoke(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        """
        调用 DeepSeek API

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

        # 调用 API（使用 OpenAI 兼容接口）
        start_time = time.perf_counter()
        try:
            client = self._get_async_client()

            kwargs = {
                "model": model_id,
                "messages": messages,
                "max_tokens": min(config.max_tokens, model.max_tokens),
                "temperature": config.temperature,
            }

            if config.stop_sequences:
                kwargs["stop"] = config.stop_sequences

            response = await client.chat.completions.create(**kwargs)

        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise RuntimeError(f"DeepSeek API call failed: {e}") from e

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
        流式调用 DeepSeek API

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

        client = self._get_async_client()

        kwargs = {
            "model": model_id,
            "messages": messages,
            "max_tokens": min(config.max_tokens, model.max_tokens),
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
                model_id="deepseek-chat",
                messages=[{"role": "user", "content": "ping"}],
                config=ModelConfig(max_tokens=1, temperature=0),
            )
            return bool(response.content)
        except Exception as e:
            logger.warning(f"DeepSeek health check failed: {e}")
            return False
