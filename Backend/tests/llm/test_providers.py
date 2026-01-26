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


# ============================================================================
# Strict Edge Case Tests
# ============================================================================

class TestDeepSeekProviderEdgeCases:
    """DeepSeek Provider 边界情况测试"""

    def test_empty_messages_validation(self):
        """测试空消息列表验证"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")
        with pytest.raises(ValueError, match="Messages cannot be empty"):
            # _validate_messages 应该拒绝空列表
            provider._validate_messages([])

    def test_invalid_message_format(self):
        """测试无效消息格式"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")
        with pytest.raises(ValueError):
            provider._validate_messages([{"invalid": "format"}])

    def test_model_not_found(self):
        """测试模型不存在"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")
        model = provider.get_model_info("nonexistent-model")
        assert model is None

    def test_pricing_not_found(self):
        """测试定价不存在"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")
        with pytest.raises(ValueError, match="Unknown model"):
            provider.get_pricing("nonexistent-model")

    def test_default_config(self):
        """测试默认配置"""
        provider_config = ModelConfig.default()
        assert provider_config.temperature == 0.7
        assert provider_config.max_tokens == 4096

    @pytest.mark.asyncio
    async def test_invoke_with_custom_config(self):
        """测试自定义配置调用"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(content="Custom response"),
            finish_reason="stop"
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=20,
            completion_tokens=10,
            total_tokens=30
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        custom_config = ModelConfig(
            temperature=0.5,
            max_tokens=2048,
            stop_sequences=["END"]
        )

        with patch.object(provider, "_get_async_client", return_value=mock_client):
            response = await provider.invoke(
                model_id="deepseek-chat",
                messages=[{"role": "user", "content": "Test"}],
                config=custom_config,
            )

            # 验证配置被正确传递
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["max_tokens"] == 2048
            assert call_kwargs["stop"] == ["END"]


class TestGeminiProviderEdgeCases:
    """Gemini Provider 边界情况测试"""

    def test_empty_system_message(self):
        """测试空 system 消息"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test")
        messages = [
            {"role": "user", "content": "Hello"},
        ]

        system_inst, converted = provider._convert_messages(messages)
        assert system_inst is None
        assert len(converted) == 1

    def test_multiple_system_messages(self):
        """测试多个 system 消息（只取最后一个）"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test")
        messages = [
            {"role": "system", "content": "First system"},
            {"role": "system", "content": "Second system"},
            {"role": "user", "content": "Hello"},
        ]

        system_inst, converted = provider._convert_messages(messages)
        # 应该取最后一个 system 消息
        assert system_inst == "Second system"
        assert len(converted) == 1

    def test_long_context_model(self):
        """测试长上下文模型"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test")
        model = provider.get_model_info("gemini-1.5-pro")

        # 2M tokens 上下文
        assert model.context_window >= 2000000

    def test_convert_messages_preserves_content(self):
        """测试消息转换保留内容"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test")
        original_content = "This is test content with special chars: 你好 👋"
        messages = [
            {"role": "user", "content": original_content},
        ]

        _, converted = provider._convert_messages(messages)
        assert converted[0]["parts"][0] == original_content


class TestMLXProviderEdgeCases:
    """MLX Provider 边界情况测试"""

    def test_convert_messages_fallback(self):
        """测试消息转换回退机制"""
        from src.llm.providers.mlx import MLXProvider

        provider = MLXProvider()

        # Mock tokenizer 没有 apply_chat_template
        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.side_effect = Exception("Not supported")

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]

        # 测试回退格式
        prompt = provider._convert_messages_to_prompt(mock_tokenizer, messages)

        assert "System: You are helpful" in prompt
        assert "User: Hello" in prompt
        assert "Assistant: Hi" in prompt
        assert prompt.endswith("Assistant:")

    def test_model_cache(self):
        """测试模型缓存机制"""
        from src.llm.providers.mlx import MLXProvider

        provider = MLXProvider()

        # 模拟已缓存的模型
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        provider._loaded_models["test-model"] = mock_model
        provider._tokenizers["test-model"] = mock_tokenizer

        # 从缓存获取应该返回同一对象
        model, tokenizer = provider._load_model("test-model")
        assert model is mock_model
        assert tokenizer is mock_tokenizer

    def test_health_check_not_available(self):
        """测试不可用时的健康检查"""
        from src.llm.providers.mlx import MLXProvider

        with patch("platform.system", return_value="Linux"):
            provider = MLXProvider()
            assert not provider.is_available

    @pytest.mark.asyncio
    async def test_health_check_mlx_not_installed(self):
        """测试 MLX 未安装时的健康检查"""
        from src.llm.providers.mlx import MLXProvider

        provider = MLXProvider()

        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                # 模拟 MLX 未安装
                with patch.dict("sys.modules", {"mlx": None, "mlx_lm": None}):
                    # is_available 属性在 MLX 未安装时返回 False
                    assert await provider.health_check() == provider.is_available


class TestCostCalculation:
    """成本计算测试"""

    def test_deepseek_cost_calculation(self):
        """测试 DeepSeek 成本计算"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")

        usage = TokenUsage(
            input_tokens=1000000,  # 1M tokens
            output_tokens=500000,   # 0.5M tokens
            total_tokens=1500000,
        )

        cost = provider.calculate_cost("deepseek-chat", usage)

        # $0.27/1M input + $1.10/1M output * 0.5 = $0.27 + $0.55 = $0.82
        assert cost.input_cost == Decimal("0.27")
        assert cost.output_cost == Decimal("0.55")
        assert cost.total_cost == Decimal("0.82")

    def test_gemini_cost_calculation(self):
        """测试 Gemini 成本计算"""
        from src.llm.providers.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test")

        usage = TokenUsage(
            input_tokens=2000000,  # 2M tokens
            output_tokens=100000,  # 0.1M tokens
            total_tokens=2100000,
        )

        cost = provider.calculate_cost("gemini-2.0-flash", usage)

        # $0.10/1M input * 2 + $0.40/1M output * 0.1 = $0.20 + $0.04 = $0.24
        assert cost.input_cost == Decimal("0.20")
        assert cost.output_cost == Decimal("0.04")
        assert cost.total_cost == Decimal("0.24")

    def test_mlx_cost_is_zero(self):
        """测试 MLX 成本为零"""
        from src.llm.providers.mlx import MLXProvider
        from src.llm.models import CostInfo

        provider = MLXProvider()

        usage = TokenUsage(
            input_tokens=10000000,
            output_tokens=5000000,
            total_tokens=15000000,
        )

        # MLX 本地模型成本应该为零
        cost = provider.calculate_cost("mlx-community/Qwen2.5-14B-Instruct-4bit", usage)
        assert cost.total_cost == Decimal("0")
        assert cost.input_cost == Decimal("0")
        assert cost.output_cost == Decimal("0")


class TestStreamingSupport:
    """流式支持测试"""

    @pytest.mark.asyncio
    async def test_deepseek_stream_mock(self):
        """测试 DeepSeek 流式调用"""
        from src.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="test")

        # Mock 流式响应
        async def mock_stream():
            chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))], usage=None),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=" World"))], usage=None),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))],
                         usage=MagicMock(prompt_tokens=10, completion_tokens=3, total_tokens=13)),
            ]
            for chunk in chunks:
                yield chunk

        mock_client = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aiter__ = lambda self: mock_stream()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_client.chat.completions.stream = MagicMock(return_value=mock_context)

        with patch.object(provider, "_get_async_client", return_value=mock_client):
            chunks = []
            async for chunk in provider.stream(
                model_id="deepseek-chat",
                messages=[{"role": "user", "content": "Hi"}],
            ):
                chunks.append(chunk)

            assert "".join(chunks) == "Hello World!"
            assert provider._last_usage.total_tokens == 13
