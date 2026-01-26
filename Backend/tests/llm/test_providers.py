#
# MacCortex - LLM Provider Tests
# Phase 5 - Multi-LLM Support (P1/P2 Extension)
# Created: 2026-01-26
#

"""
LLM Provider 单元测试

测试新增的 Provider：
- DeepSeekProvider
- GeminiProvider
- MLXProvider
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.models import (
    ModelConfig,
    ModelInfo,
    ProviderType,
    TokenUsage,
)


# ============================================================================
# DeepSeek Provider Tests
# ============================================================================

class TestDeepSeekProvider:
    """DeepSeek Provider 测试"""

    def test_import(self):
        """测试导入"""
        from src.llm.providers.deepseek import DeepSeekProvider
        assert DeepSeekProvider is not None

    def test_init_without_api_key(self):
        """测试无 API Key 初始化"""
        from src.llm.providers.deepseek import DeepSeekProvider

        with patch.dict("os.environ", {}, clear=True):
            provider = DeepSeekProvider()
            assert provider.name == "DeepSeek"
            assert provider.provider_type == ProviderType.DEEPSEEK
            assert not provider.is_available

    def test_init_with_api_key(self):
        """测试带 API Key 初始化"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="sk-test-key")
        assert provider.is_available

    def test_models_registered(self):
        """测试模型注册"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")
        models = provider.models

        assert len(models) >= 2
        model_ids = [m.id for m in models]
        assert "deepseek-chat" in model_ids
        assert "deepseek-reasoner" in model_ids

    def test_pricing(self):
        """测试定价"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")

        input_price, output_price = provider.get_pricing("deepseek-chat")
        assert input_price == 0.27
        assert output_price == 1.10

    def test_model_info(self):
        """测试模型信息"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")
        model = provider.get_model_info("deepseek-chat")

        assert model is not None
        assert model.display_name == "DeepSeek Chat"
        assert model.context_window == 65536
        assert model.supports_streaming

    @pytest.mark.asyncio
    async def test_invoke_mock(self):
        """测试调用（使用 Mock）"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")

        # Mock OpenAI 客户端
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(content="Hello!"),
            finish_reason="stop"
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch.object(provider, "_get_async_client", return_value=mock_client):
            response = await provider.invoke(
                model_id="deepseek-chat",
                messages=[{"role": "user", "content": "Hi"}],
            )

            assert response.content == "Hello!"
            assert response.usage.total_tokens == 15
            assert response.provider == ProviderType.DEEPSEEK


# ============================================================================
# Gemini Provider Tests
# ============================================================================

class TestGeminiProvider:
    """Google Gemini Provider 测试"""

    def test_import(self):
        """测试导入"""
        from src.llm.providers.gemini import GeminiProvider
        assert GeminiProvider is not None

    def test_init_without_api_key(self):
        """测试无 API Key 初始化"""
        from src.llm.providers.gemini import GeminiProvider

        with patch.dict("os.environ", {}, clear=True):
            provider = GeminiProvider()
            assert provider.name == "Google Gemini"
            assert provider.provider_type == ProviderType.GEMINI
            assert not provider.is_available

    def test_init_with_api_key(self):
        """测试带 API Key 初始化"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test-key")
        assert provider.is_available

    def test_models_registered(self):
        """测试模型注册"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test")
        models = provider.models

        assert len(models) >= 3
        model_ids = [m.id for m in models]
        assert "gemini-2.0-flash" in model_ids
        assert "gemini-1.5-pro" in model_ids
        assert "gemini-1.5-flash" in model_ids

    def test_pricing(self):
        """测试定价"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test")

        input_price, output_price = provider.get_pricing("gemini-2.0-flash")
        assert input_price == 0.10
        assert output_price == 0.40

    def test_model_info(self):
        """测试模型信息"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test")
        model = provider.get_model_info("gemini-1.5-pro")

        assert model is not None
        assert model.display_name == "Gemini 1.5 Pro"
        assert model.context_window == 2097152  # 2M tokens
        assert model.supports_streaming

    def test_convert_messages(self):
        """测试消息格式转换"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test")

        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

        system_inst, converted = provider._convert_messages(messages)

        assert system_inst == "You are helpful."
        assert len(converted) == 3
        assert converted[0]["role"] == "user"
        assert converted[1]["role"] == "model"  # assistant -> model
        assert converted[2]["role"] == "user"


# ============================================================================
# MLX Provider Tests
# ============================================================================

class TestMLXProvider:
    """MLX Provider 测试"""

    def test_import(self):
        """测试导入"""
        from src.llm.providers.mlx import MLXProvider
        assert MLXProvider is not None

    def test_init(self):
        """测试初始化"""
        from src.llm.providers.mlx import MLXProvider

        provider = MLXProvider()
        assert provider.name == "MLX"
        assert provider.provider_type == ProviderType.MLX

    def test_models_registered(self):
        """测试模型注册"""
        from src.llm.providers.mlx import MLXProvider

        provider = MLXProvider()
        models = provider.models

        assert len(models) >= 4
        model_ids = [m.id for m in models]
        assert "mlx-community/Qwen2.5-14B-Instruct-4bit" in model_ids
        assert "mlx-community/Llama-3.2-3B-Instruct-4bit" in model_ids

    def test_pricing_is_free(self):
        """测试本地模型免费"""
        from src.llm.providers.mlx import MLXProvider

        provider = MLXProvider()

        for model in provider.models:
            assert model.input_price_per_1m == Decimal("0")
            assert model.output_price_per_1m == Decimal("0")
            assert model.is_free

    def test_model_info(self):
        """测试模型信息"""
        from src.llm.providers.mlx import MLXProvider

        provider = MLXProvider()
        model = provider.get_model_info("mlx-community/Qwen2.5-14B-Instruct-4bit")

        assert model is not None
        assert "Qwen2.5 14B" in model.display_name
        assert model.context_window == 131072
        assert model.supports_streaming
        assert not model.supports_tools  # MLX 工具支持有限

    def test_is_available_non_macos(self):
        """测试非 macOS 系统不可用"""
        from src.llm.providers.mlx import MLXProvider

        with patch("platform.system", return_value="Linux"):
            provider = MLXProvider()
            assert not provider.is_available

    def test_is_available_non_arm(self):
        """测试非 ARM 架构不可用"""
        from src.llm.providers.mlx import MLXProvider

        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="x86_64"):
                provider = MLXProvider()
                assert not provider.is_available

    def test_unload_models(self):
        """测试卸载模型"""
        from src.llm.providers.mlx import MLXProvider

        provider = MLXProvider()

        # 模拟已加载模型
        provider._loaded_models = {"model1": MagicMock(), "model2": MagicMock()}
        provider._tokenizers = {"model1": MagicMock(), "model2": MagicMock()}

        # 卸载单个模型
        provider.unload_model("model1")
        assert "model1" not in provider._loaded_models
        assert "model2" in provider._loaded_models

        # 卸载所有模型
        provider.unload_all_models()
        assert len(provider._loaded_models) == 0
        assert len(provider._tokenizers) == 0


# ============================================================================
# Provider Type Tests
# ============================================================================

class TestProviderType:
    """ProviderType 枚举测试"""

    def test_all_providers(self):
        """测试所有 Provider 类型"""
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.OLLAMA.value == "ollama"
        assert ProviderType.DEEPSEEK.value == "deepseek"
        assert ProviderType.GEMINI.value == "gemini"
        assert ProviderType.MLX.value == "mlx"

    def test_display_names(self):
        """测试显示名称"""
        assert ProviderType.DEEPSEEK.display_name == "DeepSeek"
        assert ProviderType.GEMINI.display_name == "Google Gemini"
        assert ProviderType.MLX.display_name == "MLX (Apple Silicon)"

    def test_is_local(self):
        """测试本地模型判断"""
        assert not ProviderType.DEEPSEEK.is_local
        assert not ProviderType.GEMINI.is_local
        assert ProviderType.MLX.is_local
        assert ProviderType.OLLAMA.is_local
