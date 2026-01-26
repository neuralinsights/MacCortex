#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# Ollama Provider Implementation
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""
Ollama Provider 实现（本地模型）

支持的模型（动态检测）：
- qwen3:14b: 通义千问 3
- llama3.2:8b: Meta Llama 3.2
- 其他本地安装的模型...

特点：
- 零成本（本地运行）
- 无需 API Key
- 支持动态模型发现
"""

import logging
import time
from decimal import Decimal
from typing import AsyncIterator, Optional

import httpx

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


# 常用 Ollama 模型的默认配置
DEFAULT_OLLAMA_MODELS = {
    "qwen3:14b": {
        "display_name": "Qwen3 14B",
        "context_window": 32768,
    },
    "qwen2.5:14b": {
        "display_name": "Qwen2.5 14B",
        "context_window": 131072,
    },
    "llama3.2:8b": {
        "display_name": "Llama 3.2 8B",
        "context_window": 131072,
    },
    "llama3.2:3b": {
        "display_name": "Llama 3.2 3B",
        "context_window": 131072,
    },
    "codellama:13b": {
        "display_name": "Code Llama 13B",
        "context_window": 16384,
    },
    "deepseek-coder-v2:16b": {
        "display_name": "DeepSeek Coder V2 16B",
        "context_window": 131072,
    },
}


class OllamaProvider(BaseLLMProvider):
    """
    Ollama Provider（本地模型）

    通过 Ollama HTTP API 调用本地模型

    Example:
        >>> provider = OllamaProvider()
        >>> response = await provider.invoke(
        ...     model_id="qwen3:14b",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.content)
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        """
        初始化 Ollama Provider

        Args:
            host: Ollama 服务地址
            timeout: 请求超时时间（秒）
        """
        super().__init__()
        self._host = host.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._available_models: set[str] = set()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """确保 HTTP 客户端已创建"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._host,
                timeout=httpx.Timeout(self._timeout),
            )
        return self._client

    async def _fetch_models(self) -> list[str]:
        """从 Ollama 服务获取可用模型列表"""
        try:
            client = await self._ensure_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            self._available_models = set(models)
            return models
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama models: {e}")
            return []

    async def refresh_models(self) -> None:
        """刷新模型列表并注册"""
        models = await self._fetch_models()

        # 清空并重新注册
        self._models.clear()

        for model_name in models:
            # 获取模型配置（使用默认值或预定义配置）
            config = DEFAULT_OLLAMA_MODELS.get(
                model_name,
                {"display_name": model_name, "context_window": 32768},
            )

            self.register_model(
                ModelInfo(
                    id=model_name,
                    display_name=config["display_name"],
                    provider=ProviderType.OLLAMA,
                    input_price_per_1m=Decimal("0"),  # 本地模型免费
                    output_price_per_1m=Decimal("0"),
                    max_tokens=4096,
                    context_window=config["context_window"],
                    supports_streaming=True,
                    supports_tools=False,  # Ollama 工具支持有限
                    is_available=True,
                )
            )

        logger.info(f"Ollama: Registered {len(models)} models")

    @property
    def name(self) -> str:
        return "Ollama"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA

    @property
    def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在异步上下文中，返回缓存状态或默认 True
                return True
            return loop.run_until_complete(self._check_availability())
        except RuntimeError:
            # 没有事件循环
            return True  # 延迟检查

    async def _check_availability(self) -> bool:
        """异步检查可用性"""
        try:
            client = await self._ensure_client()
            response = await client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def invoke(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        """
        调用 Ollama API

        Args:
            model_id: 模型 ID
            messages: 消息列表
            config: 模型配置

        Returns:
            LLMResponse: 统一响应格式
        """
        self._validate_messages(messages)
        config = config or ModelConfig.default()

        # 构建请求
        payload = {
            "model": model_id,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            },
        }
        if config.top_p < 1.0:
            payload["options"]["top_p"] = config.top_p
        if config.top_k:
            payload["options"]["top_k"] = config.top_k

        # 调用 API
        start_time = time.perf_counter()
        try:
            client = await self._ensure_client()
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            raise TimeoutError(f"Ollama request timed out after {self._timeout}s")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error: {e.response.text}") from e
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Ollama API call failed: {e}") from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        # 提取 Token 使用量
        # Ollama 返回 eval_count (output) 和 prompt_eval_count (input)
        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

        # 本地模型零成本
        cost = CostInfo.zero()

        # 提取内容
        content = data.get("message", {}).get("content", "")

        self._last_usage = usage

        return LLMResponse(
            content=content,
            usage=usage,
            cost=cost,
            model_id=model_id,
            provider=self.provider_type,
            latency_ms=latency_ms,
            finish_reason="stop" if data.get("done") else "length",
            raw_response=data,
        )

    async def stream(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        """
        流式调用 Ollama API

        Args:
            model_id: 模型 ID
            messages: 消息列表
            config: 模型配置

        Yields:
            str: 响应内容片段
        """
        self._validate_messages(messages)
        config = config or ModelConfig.default()

        payload = {
            "model": model_id,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            },
        }

        total_input_tokens = 0
        total_output_tokens = 0

        client = await self._ensure_client()

        async with client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue

                import json

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # 流式输出内容
                if "message" in data and "content" in data["message"]:
                    yield data["message"]["content"]

                # 最终消息包含 Token 计数
                if data.get("done"):
                    total_input_tokens = data.get("prompt_eval_count", 0)
                    total_output_tokens = data.get("eval_count", 0)

        self._last_usage = TokenUsage(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
        )

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            client = await self._ensure_client()
            response = await client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
