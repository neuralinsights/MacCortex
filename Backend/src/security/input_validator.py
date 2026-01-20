#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - 输入验证与参数白名单
Phase 1.5 - Day 6-7
创建时间: 2026-01-21

参数白名单验证，防止无效参数和参数注入攻击
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Set, Union

from loguru import logger


class InputValidator:
    """输入验证器（参数白名单 + 输入清理）"""

    # 所有 Pattern 的参数白名单
    ALLOWED_PARAMETERS = {
        "summarize": {
            "length": ["short", "medium", "long"],
            "style": ["bullet", "paragraph", "headline"],
            "language": ["zh-CN", "en-US", "ja-JP", "ko-KR", "es-ES", "fr-FR", "de-DE", "auto"],
        },
        "extract": {
            "entity_types": ["person", "organization", "location", "date", "email", "phone", "url"],
            "extract_keywords": [True, False],
            "extract_contacts": [True, False],
            "extract_dates": [True, False],
            "language": ["zh-CN", "en-US", "ja-JP", "ko-KR", "auto"],
        },
        "translate": {
            "target_language": ["zh-CN", "en-US", "ja-JP", "ko-KR", "es-ES", "fr-FR", "de-DE"],
            "source_language": ["auto", "zh-CN", "en-US", "ja-JP", "ko-KR", "es-ES", "fr-FR", "de-DE"],
            "style": ["formal", "casual", "technical"],
        },
        "format": {
            "from_format": ["json", "yaml", "csv", "markdown", "xml", "toml"],
            "to_format": ["json", "yaml", "csv", "markdown", "xml", "toml"],
            "prettify": [True, False],
        },
        "search": {
            "search_type": ["web", "semantic", "hybrid"],
            "engine": ["duckduckgo"],
            "num_results": list(range(1, 21)),  # 1-20
            "language": ["zh-CN", "en-US", "ja-JP", "ko-KR", "auto"],
        },
    }

    # 输入文本长度限制（字符数）
    MAX_TEXT_LENGTH = 50_000

    # Pattern ID 白名单
    ALLOWED_PATTERN_IDS = ["summarize", "extract", "translate", "format", "search"]

    # 危险字符模式（可能导致注入攻击）
    DANGEROUS_PATTERNS = [
        r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",  # 控制字符（除 \t, \n, \r）
        r"<script[^>]*>.*?</script>",  # Script 标签
        r"javascript:",  # JavaScript 协议
        r"on\w+\s*=",  # 事件处理器（onclick, onerror, etc.）
    ]

    def __init__(self):
        """初始化输入验证器"""
        # 编译危险字符正则表达式
        self._dangerous_regex = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.DANGEROUS_PATTERNS]

        logger.info("✓ InputValidator 初始化: 5 个 Pattern 白名单已加载")

    def validate_pattern_id(self, pattern_id: str) -> tuple[bool, Optional[str]]:
        """
        验证 Pattern ID

        Args:
            pattern_id: Pattern ID

        Returns:
            (是否有效, 错误信息)
        """
        if not pattern_id:
            return False, "Pattern ID 不能为空"

        if not isinstance(pattern_id, str):
            return False, f"Pattern ID 必须是字符串，当前类型: {type(pattern_id).__name__}"

        if pattern_id not in self.ALLOWED_PATTERN_IDS:
            return False, f"无效的 Pattern ID: '{pattern_id}'。允许值: {self.ALLOWED_PATTERN_IDS}"

        return True, None

    def validate_text(self, text: str) -> tuple[bool, Optional[str], str]:
        """
        验证并清理输入文本

        Args:
            text: 输入文本

        Returns:
            (是否有效, 错误信息, 清理后的文本)
        """
        if not isinstance(text, str):
            return False, f"文本必须是字符串，当前类型: {type(text).__name__}", text

        # 移除 null 字节（安全风险）
        cleaned_text = text.replace("\x00", "")

        # Unicode 标准化（NFKC：兼容性等价分解 + 标准组合）
        cleaned_text = unicodedata.normalize("NFKC", cleaned_text)

        # 检查长度
        if len(cleaned_text) > self.MAX_TEXT_LENGTH:
            return (
                False,
                f"输入超过最大长度 ({self.MAX_TEXT_LENGTH:,} 字符)，当前长度: {len(cleaned_text):,}",
                cleaned_text,
            )

        # 检查是否包含危险字符/模式
        for regex in self._dangerous_regex:
            match = regex.search(cleaned_text)
            if match:
                return (
                    False,
                    f"输入包含危险字符或模式: {match.group()[:50]}...",
                    cleaned_text,
                )

        return True, None, cleaned_text

    def validate_parameters(
        self, pattern_id: str, parameters: Dict[str, Any]
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """
        验证参数（白名单检查）

        Args:
            pattern_id: Pattern ID
            parameters: 参数字典

        Returns:
            (是否有效, 错误信息, 验证后的参数)
        """
        # 先验证 Pattern ID
        valid, error = self.validate_pattern_id(pattern_id)
        if not valid:
            return False, error, parameters

        # 获取该 Pattern 的参数白名单
        allowed_params = self.ALLOWED_PARAMETERS.get(pattern_id, {})

        # 验证每个参数
        validated_params = {}
        for key, value in parameters.items():
            # 检查参数名是否在白名单中
            if key not in allowed_params:
                return (
                    False,
                    f"Pattern '{pattern_id}' 不支持参数 '{key}'。允许的参数: {list(allowed_params.keys())}",
                    parameters,
                )

            # 检查参数值是否在白名单中
            allowed_values = allowed_params[key]

            # 特殊处理：entity_types 可以是列表
            if key == "entity_types" and isinstance(value, list):
                # 验证列表中的每个元素
                for item in value:
                    if item not in allowed_values:
                        return (
                            False,
                            f"参数 '{key}' 包含无效值: '{item}'。允许值: {allowed_values}",
                            parameters,
                        )
                validated_params[key] = value
            else:
                # 单值参数验证
                if value not in allowed_values:
                    return (
                        False,
                        f"参数 '{key}' 的值 '{value}' 无效。允许值: {allowed_values}",
                        parameters,
                    )
                validated_params[key] = value

        return True, None, validated_params

    def validate_request(
        self, pattern_id: str, text: str, parameters: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """
        验证完整请求（Pattern ID + 文本 + 参数）

        Args:
            pattern_id: Pattern ID
            text: 输入文本
            parameters: 参数字典（可选）

        Returns:
            (是否有效, 错误信息, 验证后的数据)
        """
        # 默认空参数
        if parameters is None:
            parameters = {}

        # 1. 验证 Pattern ID
        valid, error = self.validate_pattern_id(pattern_id)
        if not valid:
            return False, error, {}

        # 2. 验证并清理文本
        valid, error, cleaned_text = self.validate_text(text)
        if not valid:
            return False, error, {}

        # 3. 验证参数
        valid, error, validated_params = self.validate_parameters(pattern_id, parameters)
        if not valid:
            return False, error, {}

        # 返回验证后的数据
        return True, None, {
            "pattern_id": pattern_id,
            "text": cleaned_text,
            "parameters": validated_params,
        }

    def get_allowed_parameters(self, pattern_id: str) -> Optional[Dict[str, List[Any]]]:
        """
        获取指定 Pattern 的允许参数

        Args:
            pattern_id: Pattern ID

        Returns:
            允许的参数字典，如果 Pattern ID 无效则返回 None
        """
        return self.ALLOWED_PARAMETERS.get(pattern_id)

    def sanitize_parameter_value(self, value: Any) -> Any:
        """
        清理参数值（移除危险字符）

        Args:
            value: 参数值

        Returns:
            清理后的值
        """
        if isinstance(value, str):
            # 移除 null 字节
            value = value.replace("\x00", "")
            # Unicode 标准化
            value = unicodedata.normalize("NFKC", value)
        elif isinstance(value, list):
            # 递归清理列表
            value = [self.sanitize_parameter_value(v) for v in value]
        elif isinstance(value, dict):
            # 递归清理字典
            value = {k: self.sanitize_parameter_value(v) for k, v in value.items()}

        return value


# 全局单例
_input_validator: Optional[InputValidator] = None


def get_input_validator() -> InputValidator:
    """获取全局输入验证器（单例模式）"""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator
