#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# MLX Provider Implementation
# Phase 5 - Multi-LLM Support (P2 Extension)
# Created: 2026-01-26
#

"""
MLX Provider 实现（Apple Silicon 本地模型）

支持的模型：
- Qwen2.5-14B: 通义千问 2.5（推荐）
- Llama-3.2-3B: Meta Llama 3.2 轻量版
- 其他 MLX 格式模型...

特点：
- 零成本（本地运行）
- Apple Silicon 原生加速（Metal）
- 比 Ollama 快 8-10 倍
- 无需网络连接
"""

import logging
import time
from decimal import Decimal
from pathlib import Path
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


# MLX 预配置模型列表
# HuggingFace Hub 上的 MLX 格式模型
MLX_MODELS = {
    "mlx-community/Qwen2.5-14B-Instruct-4bit": {
        "display_name": "Qwen2.5 14B (MLX 4-bit)",
        "max_tokens": 8192,
        "context_window": 131072,
    },
    "mlx-community/Qwen2.5-7B-Instruct-4bit": {
        "display_name": "Qwen2.5 7B (MLX 4-bit)",
        "max_tokens": 8192,
        "context_window": 131072,
    },
    "mlx-community/Llama-3.2-3B-Instruct-4bit": {
        "display_name": "Llama 3.2 3B (MLX 4-bit)",
        "max_tokens": 8192,
        "context_window": 131072,
    },
    "mlx-community/Llama-3.2-1B-Instruct-4bit": {
        "display_name": "Llama 3.2 1B (MLX 4-bit)",
        "max_tokens": 8192,
        "context_window": 131072,
    },
    "mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit": {
        "display_name": "DeepSeek Coder V2 Lite (MLX 4-bit)",
        "max_tokens": 8192,
        "context_window": 131072,
    },
}


class MLXProvider(BaseLLMProvider):
    """
    MLX Provider（Apple Silicon 本地模型）

    使用 Apple MLX 框架运行本地模型，专为 M1/M2/M3 芯片优化

    Example:
        >>> provider = MLXProvider()
        >>> response = await provider.invoke(
        ...     model_id="mlx-community/Qwen2.5-14B-Instruct-4bit",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.content)

    Requirements:
        - macOS 14.0+ with Apple Silicon (M1/M2/M3)
        - pip install mlx mlx-lm
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        default_model: str = "mlx-community/Qwen2.5-7B-Instruct-4bit",
    ):
        """
        初始化 MLX Provider

        Args:
            cache_dir: 模型缓存目录（默认使用 HuggingFace 缓存）
            default_model: 默认模型（未找到指定模型时使用）
        """
        super().__init__()
        self._cache_dir = cache_dir
        self._default_model = default_model
        self._loaded_models: dict = {}  # 已加载的模型缓存
        self._tokenizers: dict = {}  # 已加载的 tokenizer 缓存

        # 注册预配置模型
        self._register_models()

    def _register_models(self) -> None:
        """注册 MLX 模型"""
        for model_id, config in MLX_MODELS.items():
            self.register_model(
                ModelInfo(
                    id=model_id,
                    display_name=config["display_name"],
                    provider=ProviderType.MLX,
                    input_price_per_1m=Decimal("0"),  # 本地模型免费
                    output_price_per_1m=Decimal("0"),
                    max_tokens=config["max_tokens"],
                    context_window=config["context_window"],
                    supports_streaming=True,
                    supports_tools=False,  # MLX 工具支持有限
                    is_available=self.is_available,
                )
            )

    def _load_model(self, model_id: str):
        """加载模型到内存"""
        if model_id in self._loaded_models:
            return self._loaded_models[model_id], self._tokenizers[model_id]

        try:
            from mlx_lm import load

            logger.info(f"Loading MLX model: {model_id}")
            model, tokenizer = load(model_id)
            self._loaded_models[model_id] = model
            self._tokenizers[model_id] = tokenizer
            logger.info(f"MLX model loaded: {model_id}")
            return model, tokenizer
        except Exception as e:
            logger.error(f"Failed to load MLX model {model_id}: {e}")
            raise RuntimeError(f"Failed to load MLX model: {e}") from e

    @property
    def name(self) -> str:
        return "MLX"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.MLX

    @property
    def is_available(self) -> bool:
        """检查 MLX 是否可用"""
        try:
            import platform

            # 检查是否为 macOS + Apple Silicon
            if platform.system() != "Darwin":
                return False

            # 检查是否为 ARM 架构
            if platform.machine() != "arm64":
                return False

            # 检查 MLX 是否已安装
            import mlx  # noqa: F401
            import mlx_lm  # noqa: F401

            return True
        except ImportError:
            return False

    def _convert_messages_to_prompt(
        self,
        tokenizer,
        messages: list[dict],
    ) -> str:
        """
        将消息列表转换为模型输入格式

        使用 tokenizer 的 chat template 生成正确格式
        """
        try:
            # 使用 tokenizer 的 apply_chat_template
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            return prompt
        except Exception as e:
            logger.warning(f"Chat template failed: {e}, using fallback format")
            # 回退到简单格式
            parts = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    parts.append(f"System: {content}")
                elif role == "user":
                    parts.append(f"User: {content}")
                elif role == "assistant":
                    parts.append(f"Assistant: {content}")
            parts.append("Assistant:")
            return "\n".join(parts)

    async def invoke(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        """
        调用 MLX 模型

        Args:
            model_id: 模型 ID
            messages: 消息列表
            config: 模型配置

        Returns:
            LLMResponse: 统一响应格式
        """
        self._validate_messages(messages)
        config = config or ModelConfig.default()

        # 加载模型
        start_time = time.perf_counter()
        try:
            from mlx_lm import generate
            import asyncio

            model, tokenizer = await asyncio.to_thread(self._load_model, model_id)

            # 转换消息为提示
            prompt = self._convert_messages_to_prompt(tokenizer, messages)

            # 生成响应（在线程中运行以支持异步）
            response = await asyncio.to_thread(
                generate,
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=config.max_tokens,
                temp=config.temperature,
                top_p=config.top_p,
            )

        except ImportError as e:
            raise ImportError(
                "mlx-lm package not installed. "
                "Install with: pip install mlx mlx-lm"
            ) from e
        except Exception as e:
            logger.error(f"MLX generation error: {e}")
            raise RuntimeError(f"MLX generation failed: {e}") from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        # 估算 Token 使用量
        # MLX 不直接返回 token 计数，需要估算
        input_tokens = len(tokenizer.encode(prompt))
        output_tokens = len(tokenizer.encode(response))

        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

        # 本地模型零成本
        cost = CostInfo.zero()

        self._last_usage = usage

        return LLMResponse(
            content=response,
            usage=usage,
            cost=cost,
            model_id=model_id,
            provider=self.provider_type,
            latency_ms=latency_ms,
            finish_reason="stop",
            raw_response=None,
        )

    async def stream(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        """
        流式调用 MLX 模型

        Args:
            model_id: 模型 ID
            messages: 消息列表
            config: 模型配置

        Yields:
            str: 响应内容片段
        """
        self._validate_messages(messages)
        config = config or ModelConfig.default()

        try:
            from mlx_lm import stream_generate
            import asyncio

            model, tokenizer = await asyncio.to_thread(self._load_model, model_id)

            # 转换消息为提示
            prompt = self._convert_messages_to_prompt(tokenizer, messages)
            input_tokens = len(tokenizer.encode(prompt))

            # 创建生成器
            def generate_sync():
                return stream_generate(
                    model,
                    tokenizer,
                    prompt=prompt,
                    max_tokens=config.max_tokens,
                    temp=config.temperature,
                    top_p=config.top_p,
                )

            # 在线程中运行流式生成
            import queue
            import threading

            output_queue: queue.Queue = queue.Queue()
            output_tokens = 0

            def run_generator():
                nonlocal output_tokens
                try:
                    for token in generate_sync():
                        output_queue.put(token)
                        output_tokens += 1
                except Exception as e:
                    output_queue.put(e)
                finally:
                    output_queue.put(None)  # 结束标记

            thread = threading.Thread(target=run_generator)
            thread.start()

            full_response = ""
            while True:
                try:
                    item = await asyncio.to_thread(output_queue.get, timeout=60)
                    if item is None:
                        break
                    if isinstance(item, Exception):
                        raise item
                    full_response += item
                    yield item
                except queue.Empty:
                    break

            thread.join()

            self._last_usage = TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            )

        except ImportError as e:
            raise ImportError(
                "mlx-lm package not installed. "
                "Install with: pip install mlx mlx-lm"
            ) from e

    async def health_check(self) -> bool:
        """健康检查"""
        if not self.is_available:
            return False

        try:
            # 只检查 MLX 库是否可用
            import mlx  # noqa: F401
            import mlx_lm  # noqa: F401
            return True
        except ImportError:
            return False

    def unload_model(self, model_id: str) -> None:
        """卸载指定模型释放内存"""
        if model_id in self._loaded_models:
            del self._loaded_models[model_id]
            del self._tokenizers[model_id]
            logger.info(f"Unloaded MLX model: {model_id}")

    def unload_all_models(self) -> None:
        """卸载所有模型"""
        self._loaded_models.clear()
        self._tokenizers.clear()
        logger.info("Unloaded all MLX models")
