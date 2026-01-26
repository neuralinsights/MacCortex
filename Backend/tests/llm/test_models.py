#
# MacCortex - LLM Models Tests
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""LLM 数据模型单元测试"""

from decimal import Decimal

import pytest

from src.llm.models import (
    CostInfo,
    LLMResponse,
    ModelConfig,
    ModelInfo,
    ProviderType,
    TokenUsage,
)


class TestTokenUsage:
    """TokenUsage 测试"""

    def test_create_basic(self):
        """测试基本创建"""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
        )
        assert usage.input_tokens == 100
        assert usage.output_tokens == 200
        assert usage.total_tokens == 300
        assert usage.cached_tokens == 0

    def test_create_with_cache(self):
        """测试带缓存的创建"""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            cached_tokens=50,
        )
        assert usage.cached_tokens == 50

    def test_zero(self):
        """测试零使用量"""
        usage = TokenUsage.zero()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0

    def test_add(self):
        """测试累加"""
        usage1 = TokenUsage(100, 200, 300)
        usage2 = TokenUsage(50, 100, 150)
        result = usage1 + usage2
        assert result.input_tokens == 150
        assert result.output_tokens == 300
        assert result.total_tokens == 450

    def test_negative_tokens_raises(self):
        """测试负数 Token 抛出异常"""
        with pytest.raises(ValueError):
            TokenUsage(input_tokens=-1, output_tokens=100, total_tokens=99)

    def test_immutable(self):
        """测试不可变性"""
        usage = TokenUsage(100, 200, 300)
        with pytest.raises(AttributeError):
            usage.input_tokens = 500


class TestCostInfo:
    """CostInfo 测试"""

    def test_create_basic(self):
        """测试基本创建"""
        cost = CostInfo(
            input_cost=Decimal("0.01"),
            output_cost=Decimal("0.02"),
            total_cost=Decimal("0.03"),
        )
        assert cost.input_cost == Decimal("0.01")
        assert cost.output_cost == Decimal("0.02")
        assert cost.total_cost == Decimal("0.03")

    def test_zero(self):
        """测试零成本"""
        cost = CostInfo.zero()
        assert cost.total_cost == Decimal("0")

    def test_calculate(self):
        """测试成本计算"""
        usage = TokenUsage(1000000, 500000, 1500000)  # 1M input, 0.5M output
        cost = CostInfo.calculate(
            usage,
            input_price_per_1m=Decimal("3.00"),  # $3/1M input
            output_price_per_1m=Decimal("15.00"),  # $15/1M output
        )
        assert cost.input_cost == Decimal("3.000000")
        assert cost.output_cost == Decimal("7.500000")
        assert cost.total_cost == Decimal("10.500000")

    def test_formatted_total(self):
        """测试格式化显示"""
        cost = CostInfo(
            input_cost=Decimal("0.001234"),
            output_cost=Decimal("0.002345"),
            total_cost=Decimal("0.003579"),
        )
        assert cost.formatted_total == "$0.003579"

    def test_add(self):
        """测试累加"""
        cost1 = CostInfo(
            Decimal("0.01"), Decimal("0.02"), Decimal("0.03")
        )
        cost2 = CostInfo(
            Decimal("0.005"), Decimal("0.010"), Decimal("0.015")
        )
        result = cost1 + cost2
        assert result.total_cost == Decimal("0.045")

    def test_negative_cost_raises(self):
        """测试负成本抛出异常"""
        with pytest.raises(ValueError):
            CostInfo(
                input_cost=Decimal("-0.01"),
                output_cost=Decimal("0.02"),
                total_cost=Decimal("0.01"),
            )


class TestProviderType:
    """ProviderType 测试"""

    def test_display_name(self):
        """测试显示名称"""
        assert ProviderType.ANTHROPIC.display_name == "Anthropic (Claude)"
        assert ProviderType.OPENAI.display_name == "OpenAI"
        assert ProviderType.OLLAMA.display_name == "Ollama (Local)"

    def test_is_local(self):
        """测试本地模型判断"""
        assert ProviderType.OLLAMA.is_local is True
        assert ProviderType.MLX.is_local is True
        assert ProviderType.ANTHROPIC.is_local is False
        assert ProviderType.OPENAI.is_local is False


class TestModelInfo:
    """ModelInfo 测试"""

    def test_create_basic(self):
        """测试基本创建"""
        model = ModelInfo(
            id="claude-sonnet-4",
            display_name="Claude Sonnet 4",
            provider=ProviderType.ANTHROPIC,
            input_price_per_1m=Decimal("3.00"),
            output_price_per_1m=Decimal("15.00"),
        )
        assert model.id == "claude-sonnet-4"
        assert model.provider == ProviderType.ANTHROPIC
        assert model.is_local is False
        assert model.is_free is False

    def test_local_model(self):
        """测试本地模型"""
        model = ModelInfo(
            id="qwen3:14b",
            display_name="Qwen3 14B",
            provider=ProviderType.OLLAMA,
            input_price_per_1m=Decimal("0"),
            output_price_per_1m=Decimal("0"),
        )
        assert model.is_local is True
        assert model.is_free is True

    def test_estimate_cost(self):
        """测试成本估算"""
        model = ModelInfo(
            id="gpt-4o",
            display_name="GPT-4o",
            provider=ProviderType.OPENAI,
            input_price_per_1m=Decimal("2.50"),
            output_price_per_1m=Decimal("10.00"),
        )
        cost = model.estimate_cost(input_tokens=1000, output_tokens=500)
        # 1000 * 2.5 / 1M = 0.0025
        # 500 * 10 / 1M = 0.005
        assert cost.total_cost == Decimal("0.007500")


class TestModelConfig:
    """ModelConfig 测试"""

    def test_default(self):
        """测试默认配置"""
        config = ModelConfig.default()
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.top_p == 1.0

    def test_for_coding(self):
        """测试代码生成配置"""
        config = ModelConfig.for_coding()
        assert config.temperature == 0.3
        assert config.max_tokens == 8192

    def test_for_planning(self):
        """测试规划配置"""
        config = ModelConfig.for_planning()
        assert config.temperature == 0.5
        assert config.top_p == 0.9

    def test_for_review(self):
        """测试审查配置"""
        config = ModelConfig.for_review()
        assert config.temperature == 0.2
        assert config.max_tokens == 2048

    def test_invalid_temperature_raises(self):
        """测试无效温度抛出异常"""
        with pytest.raises(ValueError):
            ModelConfig(temperature=3.0)

    def test_invalid_max_tokens_raises(self):
        """测试无效 max_tokens 抛出异常"""
        with pytest.raises(ValueError):
            ModelConfig(max_tokens=0)

    def test_invalid_top_p_raises(self):
        """测试无效 top_p 抛出异常"""
        with pytest.raises(ValueError):
            ModelConfig(top_p=1.5)


class TestLLMResponse:
    """LLMResponse 测试"""

    def test_create_basic(self):
        """测试基本创建"""
        response = LLMResponse(
            content="Hello, world!",
            usage=TokenUsage(10, 20, 30),
            cost=CostInfo(
                Decimal("0.001"),
                Decimal("0.002"),
                Decimal("0.003"),
            ),
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            latency_ms=150.5,
        )
        assert response.content == "Hello, world!"
        assert response.usage.total_tokens == 30
        assert response.cost.total_cost == Decimal("0.003")
        assert response.latency_ms == 150.5
        assert response.finish_reason == "stop"

    def test_to_dict(self):
        """测试字典转换"""
        response = LLMResponse(
            content="Test",
            usage=TokenUsage(10, 20, 30),
            cost=CostInfo(
                Decimal("0.001"),
                Decimal("0.002"),
                Decimal("0.003"),
            ),
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            latency_ms=100.0,
        )
        result = response.to_dict()
        assert result["content"] == "Test"
        assert result["usage"]["total_tokens"] == 30
        assert result["cost"]["formatted_total"] == "$0.003000"
        assert result["provider"] == "anthropic"
