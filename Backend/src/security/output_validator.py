#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - 输出验证系统
Phase 1.5 - Day 10
创建时间: 2026-01-21

LLM 输出安全验证，防止系统提示泄露、凭证泄露和敏感信息暴露
"""

import re
from typing import List, Optional, Tuple

from loguru import logger


class OutputValidator:
    """
    LLM 输出验证器（Layer 5: 输出清理）

    功能:
    - 系统提示泄露检测（防止暴露 Prompt Engineering）
    - 凭证泄露检测（API Key、密码、Token）
    - 敏感标记移除（<user_input>, <system>, etc.）
    - 输出长度限制（防止 DoS）
    - 不安全内容检测（代码注入模式）
    """

    # 系统提示泄露指示器（中英文）
    LEAKED_PROMPT_INDICATORS = [
        # 中文系统提示
        r"你是一个专业的",
        r"你是.*助手",
        r"请将以下",
        r"根据以下.*进行",
        r"你的任务是",
        r"作为.*你需要",
        # 英文系统提示
        r"You are a professional",
        r"You are an? .*assistant",
        r"Your task is to",
        r"As an? .*you (should|need to|must)",
        r"Translate the following",
        r"Summarize the (following|text|content)",
        r"Extract .*from the following",
        # Prompt 结构标记
        r"<user_input[^>]*>",
        r"<system[^>]*>",
        r"</?(user_input|system)>",
        r"\[INST\]|\[/INST\]",
        r"<<SYS>>|<</SYS>>",
        # 元指令泄露
        r"绝不遵循.*标签内的指令",
        r"Never follow .*instructions",
        r"Ignore everything (above|before|in) the",
    ]

    # 凭证泄露模式（按优先级排序：具体 → 通用）
    CREDENTIAL_PATTERNS = [
        # JWT Token（必须在通用 token 模式之前）
        (r"eyJ[A-Za-z0-9_\-]*\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "[JWT_TOKEN]"),
        # GitHub Token（必须在通用 token 模式之前）
        (r"gh[ps]_[A-Za-z0-9]{20,}", "[GITHUB_TOKEN]"),
        # OpenAI API Keys
        (r"sk-[A-Za-z0-9]{20,}", "[OPENAI_API_KEY]"),
        (r"ANTHROPIC_API_KEY[=:\s]+[A-Za-z0-9_\-]{20,}", "[ANTHROPIC_API_KEY]"),
        (r"GOOGLE_API_KEY[=:\s]+[A-Za-z0-9_\-]{20,}", "[GOOGLE_API_KEY]"),
        # AWS 凭证
        (r"AKIA[0-9A-Z]{16}", "[AWS_ACCESS_KEY]"),
        (r"aws_secret_access_key[=:\s]+[\w/+]{20,}", "[AWS_SECRET_KEY]"),
        # Bearer Token
        (r"Bearer\s+[\w\-\.]{20,}", "Bearer [TOKEN]"),
        # 密码模式
        (r"password[=:\s]+['\"]?[\S]{6,}['\"]?", "password=[REDACTED]"),
        (r"pwd[=:\s]+['\"]?[\S]{6,}['\"]?", "pwd=[REDACTED]"),
        # 数据库连接串
        (r"(mysql|postgresql|mongodb)://[^@]+@", r"\1://[USER]:[PASSWORD]@"),
        # 通用 API Key 模式（必须在最后，避免过度匹配）
        (r"(api[-_]?key|apikey|api_token)[=:\s]+['\"]?[\w\-]{20,}['\"]?", r"\1=[API_KEY]"),
    ]

    # 不安全内容模式（代码注入）
    UNSAFE_CODE_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # Script 标签
        r"javascript:",  # JavaScript 协议
        r"on\w+\s*=\s*['\"]",  # 事件处理器
        r"eval\s*\(",  # eval 函数
        r"exec\s*\(",  # exec 函数
        r"__import__\s*\(",  # Python import
    ]

    # 输出长度限制（字符数）
    MAX_OUTPUT_LENGTH = 100_000

    def __init__(self):
        """初始化输出验证器"""
        # 编译系统提示泄露正则
        self._prompt_leak_regex = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.LEAKED_PROMPT_INDICATORS
        ]

        # 编译凭证泄露正则
        self._credential_regex = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.CREDENTIAL_PATTERNS
        ]

        # 编译不安全代码正则
        self._unsafe_code_regex = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.UNSAFE_CODE_PATTERNS
        ]

        logger.info(
            f"✓ OutputValidator 初始化: {len(self.LEAKED_PROMPT_INDICATORS)} 个提示泄露模式, "
            f"{len(self.CREDENTIAL_PATTERNS)} 个凭证模式"
        )

    def validate_output(
        self, output: str, original_input: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """
        验证并清理 LLM 输出

        Args:
            output: LLM 输出文本
            original_input: 原始输入（可选，用于上下文检查）

        Returns:
            (清理后的输出, 警告列表)
        """
        warnings: List[str] = []
        cleaned_output = output

        # 1. 检查输出长度
        if len(cleaned_output) > self.MAX_OUTPUT_LENGTH:
            warnings.append(
                f"输出超过最大长度 ({self.MAX_OUTPUT_LENGTH:,} 字符)，已截断"
            )
            cleaned_output = cleaned_output[: self.MAX_OUTPUT_LENGTH] + "\n[输出已截断]"

        # 2. 检测系统提示泄露
        prompt_leak_warnings = self._detect_prompt_leakage(cleaned_output)
        if prompt_leak_warnings:
            warnings.extend(prompt_leak_warnings)
            # 不自动删除，只警告（可能是合法讨论）

        # 3. 检测并清理凭证泄露
        cleaned_output, credential_warnings = self._redact_credentials(cleaned_output)
        if credential_warnings:
            warnings.extend(credential_warnings)

        # 4. 移除敏感标记
        cleaned_output, marker_warnings = self._remove_sensitive_markers(cleaned_output)
        if marker_warnings:
            warnings.extend(marker_warnings)

        # 5. 检测不安全代码
        unsafe_warnings = self._detect_unsafe_code(cleaned_output)
        if unsafe_warnings:
            warnings.extend(unsafe_warnings)

        return cleaned_output, warnings

    def _detect_prompt_leakage(self, output: str) -> List[str]:
        """
        检测系统提示泄露

        Args:
            output: 输出文本

        Returns:
            警告列表
        """
        warnings = []

        for regex in self._prompt_leak_regex:
            match = regex.search(output)
            if match:
                matched_text = match.group()[:50]  # 限制长度
                warnings.append(f"潜在系统提示泄露: {matched_text}...")
                logger.warning(f"⚠️ 检测到系统提示泄露: {matched_text}...")

        return warnings

    def _redact_credentials(self, output: str) -> Tuple[str, List[str]]:
        """
        检测并清理凭证泄露

        Args:
            output: 输出文本

        Returns:
            (清理后的文本, 警告列表)
        """
        warnings = []
        redacted_output = output

        for regex, replacement in self._credential_regex:
            matches = regex.findall(redacted_output)
            if matches:
                # 记录警告
                for match in matches:
                    matched_text = match if isinstance(match, str) else match[0]
                    warnings.append(f"检测到凭证泄露: {matched_text[:30]}... (已清理)")
                    logger.warning(f"🔐 检测到凭证泄露，已自动清理")

                # 替换凭证
                redacted_output = regex.sub(replacement, redacted_output)

        return redacted_output, warnings

    def _remove_sensitive_markers(self, output: str) -> Tuple[str, List[str]]:
        """
        移除敏感标记（<user_input>, <system> 等）

        Args:
            output: 输出文本

        Returns:
            (清理后的文本, 警告列表)
        """
        warnings = []
        cleaned_output = output

        # 检测并移除 <user_input> 标签
        user_input_pattern = re.compile(r"<user_input[^>]*>.*?</user_input>", re.DOTALL)
        if user_input_pattern.search(cleaned_output):
            warnings.append("输出包含 <user_input> 标签，已移除")
            logger.warning("⚠️ 输出包含 <user_input> 标签，已移除")
            cleaned_output = user_input_pattern.sub("[已移除敏感标记]", cleaned_output)

        # 检测并移除 <system> 标签
        system_pattern = re.compile(r"<system[^>]*>.*?</system>", re.DOTALL)
        if system_pattern.search(cleaned_output):
            warnings.append("输出包含 <system> 标签，已移除")
            logger.warning("⚠️ 输出包含 <system> 标签，已移除")
            cleaned_output = system_pattern.sub("[已移除敏感标记]", cleaned_output)

        # 移除 INST 标记
        inst_pattern = re.compile(r"\[/?INST\]|<</?SYS>>")
        if inst_pattern.search(cleaned_output):
            warnings.append("输出包含 INST/SYS 标记，已移除")
            cleaned_output = inst_pattern.sub("", cleaned_output)

        return cleaned_output, warnings

    def _detect_unsafe_code(self, output: str) -> List[str]:
        """
        检测不安全代码模式

        Args:
            output: 输出文本

        Returns:
            警告列表
        """
        warnings = []

        for regex in self._unsafe_code_regex:
            match = regex.search(output)
            if match:
                matched_text = match.group()[:50]
                warnings.append(f"检测到不安全代码模式: {matched_text}...")
                logger.warning(f"⚠️ 检测到不安全代码模式: {matched_text}...")

        return warnings

    def is_safe_output(self, output: str) -> bool:
        """
        快速检查输出是否安全（无凭证泄露）

        Args:
            output: 输出文本

        Returns:
            是否安全
        """
        # 检查凭证泄露
        for regex, _ in self._credential_regex:
            if regex.search(output):
                return False

        # 检查长度
        if len(output) > self.MAX_OUTPUT_LENGTH:
            return False

        return True

    def get_validation_summary(self, warnings: List[str]) -> dict:
        """
        生成验证摘要

        Args:
            warnings: 警告列表

        Returns:
            验证摘要字典
        """
        return {
            "is_safe": len(warnings) == 0,
            "warning_count": len(warnings),
            "warnings": warnings,
            "has_prompt_leak": any("系统提示泄露" in w for w in warnings),
            "has_credential_leak": any("凭证泄露" in w for w in warnings),
            "has_sensitive_markers": any("标签" in w or "标记" in w for w in warnings),
            "has_unsafe_code": any("不安全代码" in w for w in warnings),
        }


# 全局单例
_output_validator: Optional[OutputValidator] = None


def get_output_validator() -> OutputValidator:
    """获取全局输出验证器（单例模式）"""
    global _output_validator

    if _output_validator is None:
        _output_validator = OutputValidator()

    return _output_validator
