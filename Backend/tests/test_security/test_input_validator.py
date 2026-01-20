#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - InputValidator 测试
Phase 1.5 - Day 6-7
创建时间: 2026-01-21

测试输入验证与参数白名单功能
"""

import pytest

from security.input_validator import InputValidator, get_input_validator


# ==================== Fixtures ====================


@pytest.fixture
def validator():
    """创建输入验证器实例"""
    return InputValidator()


@pytest.fixture
def singleton_validator():
    """获取单例验证器"""
    return get_input_validator()


# ==================== Pattern ID 验证测试 ====================


class TestPatternIDValidation:
    """测试 Pattern ID 验证"""

    def test_valid_pattern_ids(self, validator):
        """测试有效的 Pattern ID"""
        valid_ids = ["summarize", "extract", "translate", "format", "search"]
        for pattern_id in valid_ids:
            is_valid, error = validator.validate_pattern_id(pattern_id)
            assert is_valid is True
            assert error is None

    def test_invalid_pattern_id(self, validator):
        """测试无效的 Pattern ID"""
        is_valid, error = validator.validate_pattern_id("invalid_pattern")
        assert is_valid is False
        assert "无效的 Pattern ID" in error
        assert "invalid_pattern" in error

    def test_empty_pattern_id(self, validator):
        """测试空 Pattern ID"""
        is_valid, error = validator.validate_pattern_id("")
        assert is_valid is False
        assert "不能为空" in error

    def test_pattern_id_type_validation(self, validator):
        """测试 Pattern ID 类型验证"""
        is_valid, error = validator.validate_pattern_id(123)
        assert is_valid is False
        assert "必须是字符串" in error

    def test_pattern_id_case_sensitive(self, validator):
        """测试 Pattern ID 大小写敏感"""
        is_valid, error = validator.validate_pattern_id("SUMMARIZE")
        assert is_valid is False  # 不应该接受大写


# ==================== 文本验证测试 ====================


class TestTextValidation:
    """测试文本验证"""

    def test_valid_text(self, validator):
        """测试有效文本"""
        text = "这是一段正常的中文文本。This is normal English text."
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is True
        assert error is None
        assert cleaned == text

    def test_text_with_null_bytes(self, validator):
        """测试包含 null 字节的文本"""
        text = "Hello\x00World"
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is True
        assert "\x00" not in cleaned  # null 字节应被移除
        assert cleaned == "HelloWorld"

    def test_text_unicode_normalization(self, validator):
        """测试 Unicode 标准化"""
        # 使用分解形式的字符
        text = "café"  # 可能包含分解形式的 é
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is True
        # 应该被标准化为 NFKC 形式
        assert cleaned == "café"

    def test_text_max_length(self, validator):
        """测试文本长度限制"""
        # 超过 50,000 字符
        long_text = "a" * 60_000
        is_valid, error, cleaned = validator.validate_text(long_text)
        assert is_valid is False
        assert "超过最大长度" in error
        assert "50,000" in error

    def test_text_with_control_characters(self, validator):
        """测试包含控制字符的文本"""
        text = "Hello\x01\x02World"  # 包含控制字符
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is False
        assert "危险字符或模式" in error

    def test_text_with_script_tags(self, validator):
        """测试包含 script 标签的文本"""
        text = "Hello <script>alert('xss')</script> World"
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is False
        assert "危险字符或模式" in error

    def test_text_with_javascript_protocol(self, validator):
        """测试包含 JavaScript 协议的文本"""
        text = "Click <a href='javascript:alert(1)'>here</a>"
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is False
        assert "危险字符或模式" in error

    def test_text_with_event_handlers(self, validator):
        """测试包含事件处理器的文本"""
        text = "<img src='x' onerror='alert(1)'>"
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is False
        assert "危险字符或模式" in error

    def test_text_type_validation(self, validator):
        """测试文本类型验证"""
        is_valid, error, cleaned = validator.validate_text(12345)
        assert is_valid is False
        assert "必须是字符串" in error

    def test_empty_text(self, validator):
        """测试空文本"""
        is_valid, error, cleaned = validator.validate_text("")
        assert is_valid is True
        assert cleaned == ""

    def test_text_with_tabs_and_newlines(self, validator):
        """测试包含制表符和换行符的文本（应该允许）"""
        text = "Line 1\nLine 2\tTabbed"
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is True
        assert cleaned == text


# ==================== 参数验证测试 ====================


class TestParameterValidation:
    """测试参数验证"""

    # --- summarize Pattern ---

    def test_summarize_valid_parameters(self, validator):
        """测试 summarize Pattern 的有效参数"""
        params = {"length": "medium", "style": "bullet", "language": "zh-CN"}
        is_valid, error, validated = validator.validate_parameters("summarize", params)
        assert is_valid is True
        assert error is None
        assert validated == params

    def test_summarize_invalid_length(self, validator):
        """测试 summarize Pattern 的无效 length"""
        params = {"length": "super_long"}
        is_valid, error, validated = validator.validate_parameters("summarize", params)
        assert is_valid is False
        assert "length" in error
        assert "super_long" in error

    def test_summarize_invalid_parameter_name(self, validator):
        """测试 summarize Pattern 的无效参数名"""
        params = {"invalid_param": "value"}
        is_valid, error, validated = validator.validate_parameters("summarize", params)
        assert is_valid is False
        assert "不支持参数" in error
        assert "invalid_param" in error

    # --- extract Pattern ---

    def test_extract_valid_parameters(self, validator):
        """测试 extract Pattern 的有效参数"""
        params = {
            "entity_types": ["person", "organization"],
            "extract_keywords": True,
            "language": "zh-CN",
        }
        is_valid, error, validated = validator.validate_parameters("extract", params)
        assert is_valid is True
        assert validated == params

    def test_extract_invalid_entity_type(self, validator):
        """测试 extract Pattern 的无效 entity_types"""
        params = {"entity_types": ["person", "invalid_type"]}
        is_valid, error, validated = validator.validate_parameters("extract", params)
        assert is_valid is False
        assert "entity_types" in error
        assert "invalid_type" in error

    def test_extract_invalid_boolean(self, validator):
        """测试 extract Pattern 的无效布尔值"""
        params = {"extract_keywords": "yes"}  # 应该是 True/False
        is_valid, error, validated = validator.validate_parameters("extract", params)
        assert is_valid is False
        assert "extract_keywords" in error

    # --- translate Pattern ---

    def test_translate_valid_parameters(self, validator):
        """测试 translate Pattern 的有效参数"""
        params = {"target_language": "en-US", "source_language": "auto", "style": "formal"}
        is_valid, error, validated = validator.validate_parameters("translate", params)
        assert is_valid is True
        assert validated == params

    def test_translate_invalid_target_language(self, validator):
        """测试 translate Pattern 的无效目标语言"""
        params = {"target_language": "ru-RU"}  # 不支持俄语
        is_valid, error, validated = validator.validate_parameters("translate", params)
        assert is_valid is False
        assert "target_language" in error

    # --- format Pattern ---

    def test_format_valid_parameters(self, validator):
        """测试 format Pattern 的有效参数"""
        params = {"from_format": "json", "to_format": "yaml", "prettify": True}
        is_valid, error, validated = validator.validate_parameters("format", params)
        assert is_valid is True
        assert validated == params

    def test_format_invalid_format(self, validator):
        """测试 format Pattern 的无效格式"""
        params = {"from_format": "xml", "to_format": "invalid_format"}
        is_valid, error, validated = validator.validate_parameters("format", params)
        assert is_valid is False
        assert "to_format" in error

    # --- search Pattern ---

    def test_search_valid_parameters(self, validator):
        """测试 search Pattern 的有效参数"""
        params = {"search_type": "web", "engine": "duckduckgo", "num_results": 10}
        is_valid, error, validated = validator.validate_parameters("search", params)
        assert is_valid is True
        assert validated == params

    def test_search_invalid_num_results(self, validator):
        """测试 search Pattern 的无效结果数量"""
        params = {"num_results": 25}  # 超过 20 的上限
        is_valid, error, validated = validator.validate_parameters("search", params)
        assert is_valid is False
        assert "num_results" in error

    def test_search_zero_num_results(self, validator):
        """测试 search Pattern 的零结果数量"""
        params = {"num_results": 0}  # 低于 1 的下限
        is_valid, error, validated = validator.validate_parameters("search", params)
        assert is_valid is False
        assert "num_results" in error

    # --- 边界测试 ---

    def test_empty_parameters(self, validator):
        """测试空参数字典"""
        is_valid, error, validated = validator.validate_parameters("summarize", {})
        assert is_valid is True
        assert validated == {}

    def test_invalid_pattern_id_in_parameters(self, validator):
        """测试参数验证时的无效 Pattern ID"""
        params = {"length": "medium"}
        is_valid, error, validated = validator.validate_parameters("invalid_pattern", params)
        assert is_valid is False
        assert "无效的 Pattern ID" in error


# ==================== 完整请求验证测试 ====================


class TestRequestValidation:
    """测试完整请求验证"""

    def test_valid_request(self, validator):
        """测试有效请求"""
        is_valid, error, validated_data = validator.validate_request(
            pattern_id="summarize",
            text="这是一段测试文本。",
            parameters={"length": "medium", "language": "zh-CN"},
        )
        assert is_valid is True
        assert error is None
        assert validated_data["pattern_id"] == "summarize"
        assert validated_data["text"] == "这是一段测试文本。"
        assert validated_data["parameters"]["length"] == "medium"

    def test_request_with_invalid_pattern_id(self, validator):
        """测试无效 Pattern ID 的请求"""
        is_valid, error, validated_data = validator.validate_request(
            pattern_id="invalid", text="测试", parameters={}
        )
        assert is_valid is False
        assert "无效的 Pattern ID" in error

    def test_request_with_invalid_text(self, validator):
        """测试无效文本的请求"""
        is_valid, error, validated_data = validator.validate_request(
            pattern_id="summarize", text="a" * 60_000, parameters={}  # 超长文本
        )
        assert is_valid is False
        assert "超过最大长度" in error

    def test_request_with_invalid_parameters(self, validator):
        """测试无效参数的请求"""
        is_valid, error, validated_data = validator.validate_request(
            pattern_id="summarize",
            text="测试",
            parameters={"length": "invalid_length"},
        )
        assert is_valid is False
        assert "length" in error

    def test_request_with_none_parameters(self, validator):
        """测试 None 参数的请求"""
        is_valid, error, validated_data = validator.validate_request(
            pattern_id="summarize", text="测试", parameters=None
        )
        assert is_valid is True
        assert validated_data["parameters"] == {}

    def test_request_text_sanitization(self, validator):
        """测试请求文本清理"""
        is_valid, error, validated_data = validator.validate_request(
            pattern_id="summarize", text="Hello\x00World", parameters={}
        )
        assert is_valid is True
        assert "\x00" not in validated_data["text"]
        assert validated_data["text"] == "HelloWorld"


# ==================== 辅助方法测试 ====================


class TestHelperMethods:
    """测试辅助方法"""

    def test_get_allowed_parameters(self, validator):
        """测试获取允许的参数"""
        allowed = validator.get_allowed_parameters("summarize")
        assert allowed is not None
        assert "length" in allowed
        assert "style" in allowed
        assert "language" in allowed

    def test_get_allowed_parameters_invalid_pattern(self, validator):
        """测试获取无效 Pattern 的参数"""
        allowed = validator.get_allowed_parameters("invalid_pattern")
        assert allowed is None

    def test_sanitize_parameter_value_string(self, validator):
        """测试清理字符串参数值"""
        value = "Hello\x00World"
        sanitized = validator.sanitize_parameter_value(value)
        assert "\x00" not in sanitized
        assert sanitized == "HelloWorld"

    def test_sanitize_parameter_value_list(self, validator):
        """测试清理列表参数值"""
        value = ["Hello\x00World", "Test"]
        sanitized = validator.sanitize_parameter_value(value)
        assert "\x00" not in sanitized[0]
        assert sanitized == ["HelloWorld", "Test"]

    def test_sanitize_parameter_value_dict(self, validator):
        """测试清理字典参数值"""
        value = {"key": "Hello\x00World"}
        sanitized = validator.sanitize_parameter_value(value)
        assert "\x00" not in sanitized["key"]
        assert sanitized == {"key": "HelloWorld"}

    def test_sanitize_parameter_value_nested(self, validator):
        """测试清理嵌套参数值"""
        value = {"list": ["Hello\x00World", {"nested": "Test\x00"}]}
        sanitized = validator.sanitize_parameter_value(value)
        assert "\x00" not in str(sanitized)


# ==================== 单例模式测试 ====================


class TestSingleton:
    """测试单例模式"""

    def test_singleton_instance(self, singleton_validator):
        """测试单例实例"""
        validator1 = get_input_validator()
        validator2 = get_input_validator()
        assert validator1 is validator2  # 应该是同一个实例

    def test_singleton_functionality(self, singleton_validator):
        """测试单例功能"""
        is_valid, error = singleton_validator.validate_pattern_id("summarize")
        assert is_valid is True


# ==================== 边界与特殊情况测试 ====================


class TestEdgeCases:
    """测试边界与特殊情况"""

    def test_max_length_boundary(self, validator):
        """测试最大长度边界"""
        # 正好 50,000 字符（应该通过）
        text = "a" * 50_000
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is True

        # 50,001 字符（应该失败）
        text = "a" * 50_001
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is False

    def test_unicode_edge_cases(self, validator):
        """测试 Unicode 边界情况"""
        # 表情符号
        text = "Hello 😀 World"
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is True

        # 中文字符
        text = "你好世界 🌍"
        is_valid, error, cleaned = validator.validate_text(text)
        assert is_valid is True

    def test_num_results_boundary(self, validator):
        """测试 num_results 边界"""
        # 1（最小值，应该通过）
        params = {"num_results": 1}
        is_valid, error, validated = validator.validate_parameters("search", params)
        assert is_valid is True

        # 20（最大值，应该通过）
        params = {"num_results": 20}
        is_valid, error, validated = validator.validate_parameters("search", params)
        assert is_valid is True

    def test_language_code_variations(self, validator):
        """测试语言代码变体"""
        # 所有支持的语言代码
        languages = ["zh-CN", "en-US", "ja-JP", "ko-KR", "es-ES", "fr-FR", "de-DE", "auto"]
        for lang in languages:
            params = {"language": lang}
            is_valid, error, validated = validator.validate_parameters("summarize", params)
            assert is_valid is True

    def test_all_pattern_ids(self, validator):
        """测试所有支持的 Pattern ID"""
        pattern_ids = ["summarize", "extract", "translate", "format", "search"]
        for pattern_id in pattern_ids:
            is_valid, error = validator.validate_pattern_id(pattern_id)
            assert is_valid is True
