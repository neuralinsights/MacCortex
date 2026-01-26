#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# Model Router V2
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""
ModelRouterV2 - 智能模型路由器

核心功能：
- 多 Provider 统一管理
- 智能 Fallback 链
- Token 使用量追踪
- 成本控制与预算管理
"""

import logging
from typing import AsyncIterator, Optional

from .models import (
    CostInfo,
    LLMResponse,
    ModelConfig,
    ModelInfo,
    ProviderType,
    TokenUsage,
)
from .protocol import LLMProviderProtocol
from .usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


class ModelRouterV2:
    """
    智能模型路由器 V2

    统一管理多个 LLM Provider，提供：
    - 自动 Provider 注册与发现
    - 智能 Fallback（主模型不可用时自动切换）
    - 统一的 Token 使用量追踪
    - 成本预算控制

    Example:
        >>> router = ModelRouterV2()
        >>> router.register_provider(ClaudeProvider(api_key="..."))
        >>> router.register_provider(OllamaProvider())
        >>>
        >>> response = await router.invoke(
        ...     model_id="claude-sonnet-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(f"Cost: {response.cost.formatted_total}")
    """

    def __init__(
        self,
        fallback_chain: Optional[list[str]] = None,
        usage_tracker: Optional[UsageTracker] = None,
        budget_limit_usd: Optional[float] = None,
    ):
        """
        初始化路由器

        Args:
            fallback_chain: 模型 Fallback 链（按优先级排序）
            usage_tracker: 使用量追踪器
            budget_limit_usd: 预算上限（USD）
        """
        self._providers: dict[ProviderType, LLMProviderProtocol] = {}
        self._model_to_provider: dict[str, ProviderType] = {}
        self._fallback_chain = fallback_chain or []
        self._usage_tracker = usage_tracker or UsageTracker()
        self._budget_limit = budget_limit_usd

    def register_provider(self, provider: LLMProviderProtocol) -> None:
        """
        注册 Provider

        Args:
            provider: LLM Provider 实例
        """
        provider_type = provider.provider_type
        self._providers[provider_type] = provider

        # 注册模型到 Provider 映射
        for model in provider.models:
            self._model_to_provider[model.id] = provider_type

        logger.info(
            f"Registered provider: {provider.name} "
            f"({len(provider.models)} models)"
        )

    def unregister_provider(self, provider_type: ProviderType) -> None:
        """注销 Provider"""
        if provider_type in self._providers:
            provider = self._providers[provider_type]
            # 移除模型映射
            for model in provider.models:
                self._model_to_provider.pop(model.id, None)
            del self._providers[provider_type]
            logger.info(f"Unregistered provider: {provider_type.value}")

    def get_provider(self, provider_type: ProviderType) -> Optional[LLMProviderProtocol]:
        """获取 Provider"""
        return self._providers.get(provider_type)

    def get_provider_for_model(self, model_id: str) -> Optional[LLMProviderProtocol]:
        """根据模型 ID 获取 Provider"""
        provider_type = self._model_to_provider.get(model_id)
        if provider_type:
            return self._providers.get(provider_type)
        return None

    def get_available_models(self) -> list[ModelInfo]:
        """获取所有可用模型"""
        models = []
        for provider in self._providers.values():
            if provider.is_available:
                models.extend(provider.models)
        return models

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        provider = self.get_provider_for_model(model_id)
        if provider:
            return provider.get_model_info(model_id)
        return None

    async def invoke(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> LLMResponse:
        """
        调用 LLM

        Args:
            model_id: 模型 ID
            messages: 消息列表
            config: 模型配置
            session_id: 会话 ID（用于使用量追踪）
            agent_name: Agent 名称（用于分组统计）

        Returns:
            LLMResponse: 统一响应格式

        Raises:
            ValueError: 模型不存在
            RuntimeError: 所有 Fallback 都失败
        """
        # 检查预算
        if self._budget_limit:
            current_cost = self._usage_tracker.get_total_cost()
            if current_cost >= self._budget_limit:
                raise RuntimeError(
                    f"Budget limit exceeded: ${current_cost:.4f} >= ${self._budget_limit:.4f}"
                )

        # 构建尝试模型列表（主模型 + fallback）
        models_to_try = [model_id]
        if self._fallback_chain:
            models_to_try.extend(
                m for m in self._fallback_chain if m != model_id
            )

        last_error = None

        for try_model_id in models_to_try:
            provider = self.get_provider_for_model(try_model_id)

            if not provider:
                logger.warning(f"No provider found for model: {try_model_id}")
                continue

            if not provider.is_available:
                logger.warning(f"Provider not available: {provider.name}")
                continue

            try:
                response = await provider.invoke(try_model_id, messages, config)

                # 记录使用量
                self._usage_tracker.record_usage(
                    model_id=try_model_id,
                    provider=provider.provider_type,
                    usage=response.usage,
                    cost=response.cost,
                    session_id=session_id,
                    agent_name=agent_name,
                )

                # 如果使用了 fallback，记录日志
                if try_model_id != model_id:
                    logger.info(
                        f"Used fallback model: {try_model_id} "
                        f"(original: {model_id})"
                    )

                return response

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Model {try_model_id} failed: {e}, "
                    f"trying next fallback..."
                )
                continue

        # 所有模型都失败
        raise RuntimeError(
            f"All models failed. Last error: {last_error}"
        ) from last_error

    async def stream(
        self,
        model_id: str,
        messages: list[dict],
        config: Optional[ModelConfig] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        流式调用 LLM

        Args:
            model_id: 模型 ID
            messages: 消息列表
            config: 模型配置
            session_id: 会话 ID
            agent_name: Agent 名称

        Yields:
            str: 响应内容片段
        """
        provider = self.get_provider_for_model(model_id)
        if not provider:
            raise ValueError(f"Unknown model: {model_id}")

        if not provider.is_available:
            raise RuntimeError(f"Provider not available: {provider.name}")

        async for chunk in provider.stream(model_id, messages, config):
            yield chunk

        # 记录使用量（流式结束后）
        usage = provider.get_last_usage()
        if usage:
            cost = provider.calculate_cost(model_id, usage)
            self._usage_tracker.record_usage(
                model_id=model_id,
                provider=provider.provider_type,
                usage=usage,
                cost=cost,
                session_id=session_id,
                agent_name=agent_name,
            )

    def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> CostInfo:
        """预估调用成本"""
        provider = self.get_provider_for_model(model_id)
        if not provider:
            raise ValueError(f"Unknown model: {model_id}")
        return provider.estimate_cost(model_id, input_tokens, output_tokens)

    def get_usage_stats(self, session_id: Optional[str] = None) -> dict:
        """获取使用统计"""
        return self._usage_tracker.get_stats(session_id)

    def get_total_cost(self, session_id: Optional[str] = None) -> float:
        """获取总成本"""
        return self._usage_tracker.get_total_cost(session_id)

    def get_total_tokens(self, session_id: Optional[str] = None) -> int:
        """获取总 Token 数"""
        return self._usage_tracker.get_total_tokens(session_id)

    def reset_usage(self, session_id: Optional[str] = None) -> None:
        """重置使用统计"""
        self._usage_tracker.reset(session_id)

    async def health_check_all(self) -> dict[str, bool]:
        """检查所有 Provider 健康状态"""
        results = {}
        for provider_type, provider in self._providers.items():
            try:
                is_healthy = await provider.health_check()
                results[provider_type.value] = is_healthy
            except Exception as e:
                logger.warning(f"Health check failed for {provider_type}: {e}")
                results[provider_type.value] = False
        return results

    def set_fallback_chain(self, chain: list[str]) -> None:
        """设置 Fallback 链"""
        self._fallback_chain = chain

    def set_budget_limit(self, limit_usd: Optional[float]) -> None:
        """设置预算上限"""
        self._budget_limit = limit_usd

    @property
    def providers(self) -> dict[ProviderType, LLMProviderProtocol]:
        """获取所有已注册的 Provider"""
        return self._providers.copy()

    @property
    def usage_tracker(self) -> UsageTracker:
        """获取使用量追踪器"""
        return self._usage_tracker

    def __repr__(self) -> str:
        provider_names = [p.name for p in self._providers.values()]
        return f"<ModelRouterV2 providers={provider_names}>"


# 便捷工厂函数
async def create_router(
    anthropic_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    ollama_host: str = "http://localhost:11434",
    fallback_chain: Optional[list[str]] = None,
) -> ModelRouterV2:
    """
    创建配置好的 ModelRouterV2 实例

    Args:
        anthropic_api_key: Anthropic API Key
        openai_api_key: OpenAI API Key
        ollama_host: Ollama 服务地址
        fallback_chain: Fallback 链

    Returns:
        ModelRouterV2: 配置好的路由器实例
    """
    from .providers import ClaudeProvider, OllamaProvider, OpenAIProvider

    router = ModelRouterV2(fallback_chain=fallback_chain)

    # 注册 Claude Provider
    if anthropic_api_key:
        router.register_provider(ClaudeProvider(api_key=anthropic_api_key))

    # 注册 OpenAI Provider
    if openai_api_key:
        router.register_provider(OpenAIProvider(api_key=openai_api_key))

    # 注册 Ollama Provider（本地，总是尝试）
    ollama = OllamaProvider(host=ollama_host)
    if await ollama._check_availability():
        await ollama.refresh_models()
        router.register_provider(ollama)

    return router
