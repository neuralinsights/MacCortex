#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# Google Gemini Provider Implementation
# Phase 5 - Multi-LLM Support (P1 Extension)
# Created: 2026-01-26
#

"""
Google Gemini Provider 实现

支持的模型：
- gemini-2.0-flash: 最新快速模型（高性价比）
- gemini-1.5-pro: 专业版模型
- gemini-1.5-flash: 快速轻量版

特点：
- 超长上下文窗口（最高 2M tokens）
- 多模态支持
- 竞争力价格
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


# Google Gemini 模型定价表 (2026-01, USD per 1M tokens)
# 参考: https://ai.google.dev/pricing
GEMINI_PRICING = {
    "gemini-2.0-flash": {
        "input": Decimal("0.10"),
        "output": Decimal("0.40"),
        "display_name": "Gemini 2.0 Flash",
        "max_tokens": 8192,
        "context_window": 1048576,  # 1M tokens
    },
    "gemini-1.5-pro": {
        "input": Decimal("1.25"),
        "output": Decimal("5.00"),
        "display_name": "Gemini 1.5 Pro",
        "max_tokens": 8192,
        "context_window": 2097152,  # 2M tokens
    },
    "gemini-1.5-flash": {
        "input": Decimal("0.075"),
        "output": Decimal("0.30"),
        "display_name": "Gemini 1.5 Flash",
        "max_tokens": 8192,
        "context_window": 1048576,  # 1M tokens
    },
}


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini Provider

    使用 Google Generative AI SDK 调用 Gemini 模型

    Example:
        >>> provider = GeminiProvider(api_key="...")
        >>> response = await provider.invoke(
        ...     model_id="gemini-2.0-flash",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.content)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        """
        初始化 Gemini Provider

        Args:
            api_key: Google AI API Key（可选，从环境变量读取）
        """
        super().__init__()
        self._api_key = api_key
        self._client = None

        # 注册模型
        self._register_models()

    def _register_models(self) -> None:
        """注册 Gemini 模型"""
        for model_id, pricing in GEMINI_PRICING.items():
            self.register_model(
                ModelInfo(
                    id=model_id,
                    display_name=pricing["display_name"],
                    provider=ProviderType.GEMINI,
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
        """获取或创建 Gemini 客户端"""
        if self._client is None:
            try:
                import google.generativeai as genai
                import os

                api_key = self._api_key or os.environ.get("GOOGLE_API_KEY")

                if not api_key:
                    raise ValueError(
                        "Google API key not found. "
                        "Set GOOGLE_API_KEY environment variable or pass api_key parameter."
                    )

                genai.configure(api_key=api_key)
                self._client = genai
            except ImportError:
                raise ImportError(
                    "google-generativeai package not installed. "
                    "Install with: pip install google-generativeai"
                )
        return self._client

    @property
    def name(self) -> str:
        return "Google Gemini"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GEMINI

    @property
    def is_available(self) -> bool:
        """检查 API Key 是否已配置"""
        import os

        key = self._api_key or os.environ.get("GOOGLE_API_KEY")
        return bool(key)

    def _convert_messages(self, messages: list[dict]) -> tuple[Optional[str], list[dict]]:
        """
        转换消息格式为 Gemini 格式

        Gemini 使用不同的消息格式：
        - role: "user" 或 "model"（不是 "assistant"）
        - parts: 内容列表（不是 "content"）

        Returns:
            tuple: (system_instruction, converted_messages)
        """
        system_instruction = None
        converted = []

        for msg in messages:
            if msg["role"] == "system":
                # Gemini 将 system 消息作为 system_instruction
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                converted.append({
                    "role": "user",
                    "parts": [msg["content"]],
                })
            elif msg["role"] == "assistant":
                # Gemini 使用 "model" 而不是 "assistant"
                converted.append({
                    "role": "model",
                    "parts": [msg["content"]],
                })

        return system_instruction, converted

    async def invoke(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        """
        调用 Gemini API

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

        # 转换消息格式
        system_instruction, gemini_messages = self._convert_messages(messages)

        # 调用 API
        start_time = time.perf_counter()
        try:
            genai = self._get_client()

            # 创建模型实例
            generation_config = {
                "temperature": config.temperature,
                "max_output_tokens": min(config.max_tokens, model.max_tokens),
                "top_p": config.top_p,
            }
            if config.top_k:
                generation_config["top_k"] = config.top_k
            if config.stop_sequences:
                generation_config["stop_sequences"] = config.stop_sequences

            model_instance = genai.GenerativeModel(
                model_name=model_id,
                generation_config=generation_config,
                system_instruction=system_instruction,
            )

            # 发送消息（异步）
            import asyncio
            response = await asyncio.to_thread(
                model_instance.generate_content,
                gemini_messages,
            )

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API call failed: {e}") from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        # 提取 Token 使用量
        usage_metadata = response.usage_metadata
        usage = TokenUsage(
            input_tokens=usage_metadata.prompt_token_count,
            output_tokens=usage_metadata.candidates_token_count,
            total_tokens=usage_metadata.total_token_count,
        )

        # 计算成本
        cost = self.calculate_cost(model_id, usage)

        # 提取内容
        content = response.text if response.text else ""

        # 提取结束原因
        finish_reason = "stop"
        if response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "finish_reason"):
                finish_reason = str(candidate.finish_reason.name).lower()

        self._last_usage = usage

        return LLMResponse(
            content=content,
            usage=usage,
            cost=cost,
            model_id=model_id,
            provider=self.provider_type,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            raw_response=response,
        )

    async def stream(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        """
        流式调用 Gemini API

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
        system_instruction, gemini_messages = self._convert_messages(messages)

        genai = self._get_client()

        generation_config = {
            "temperature": config.temperature,
            "max_output_tokens": min(config.max_tokens, model.max_tokens),
            "top_p": config.top_p,
        }

        model_instance = genai.GenerativeModel(
            model_name=model_id,
            generation_config=generation_config,
            system_instruction=system_instruction,
        )

        # 流式生成
        import asyncio
        response = await asyncio.to_thread(
            model_instance.generate_content,
            gemini_messages,
            stream=True,
        )

        total_input_tokens = 0
        total_output_tokens = 0

        for chunk in response:
            if chunk.text:
                yield chunk.text

            # 最后一个 chunk 包含使用量
            if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                total_input_tokens = chunk.usage_metadata.prompt_token_count
                total_output_tokens = chunk.usage_metadata.candidates_token_count

        self._last_usage = TokenUsage(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
        )

    async def health_check(self) -> bool:
        """健康检查"""
        if not self.is_available:
            return False

        try:
            response = await self.invoke(
                model_id="gemini-1.5-flash",
                messages=[{"role": "user", "content": "ping"}],
                config=ModelConfig(max_tokens=1, temperature=0),
            )
            return bool(response.content)
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False
