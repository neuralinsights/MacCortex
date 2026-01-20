#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MacCortex PromptGuard - 5 Layer Prompt Injection Defense
Phase 1.5 - Day 1-2
创建时间: 2026-01-21

实现 5 层 Prompt Injection 防护系统：
1. Layer 1: 输入标记（Untrusted Input Marking）
2. Layer 2: 指令隔离（Instruction Isolation）
3. Layer 3: 模式检测（Pattern Detection）
4. Layer 4: LLM 验证（LLM-Based Validation）
5. Layer 5: 输出清理（Output Sanitization）

防御 OWASP LLM Top 10 #01: Prompt Injection

Copyright (c) 2026 Yu Geng. All rights reserved.
This software is proprietary and confidential.
"""

__author__ = "Yu Geng"
__copyright__ = "Copyright 2026, Yu Geng"
__license__ = "Proprietary"
__version__ = "1.5.0"

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from loguru import logger

from .security_config import SecurityConfig, get_security_config


@dataclass
class InjectionDetectionResult:
    """Prompt Injection 检测结果"""

    is_malicious: bool  # 是否检测到恶意输入
    confidence: float  # 置信度（0.0-1.0）
    matched_patterns: List[str]  # 匹配的模式列表
    severity: str  # 严重程度：low, medium, high, critical
    details: str  # 详细说明


class PromptGuard:
    """
    5 层 Prompt Injection 防护系统

    使用方法：
        guard = PromptGuard()

        # 检测恶意输入
        result = guard.detect_injection(user_input)

        # 标记不可信输入
        marked = guard.mark_untrusted(user_input, source="user")

        # 隔离系统指令
        isolated = guard.isolate_instructions(system_prompt, user_input)

        # 清理输出
        cleaned = guard.sanitize_output(llm_output, original_input)
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        """
        初始化 PromptGuard

        Args:
            config: 安全配置实例，默认使用全局配置
        """
        self.config = config or get_security_config()
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则表达式模式（性能优化）"""
        self._compiled_injection_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.config.injection_patterns
        ]

        self._compiled_leak_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.prompt_leak_indicators
        ]

        self._compiled_credential_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.credential_patterns
        ]

    # ==================== Layer 1: 输入标记 ====================

    def mark_untrusted(self, user_input: str, source: str = "user") -> str:
        """
        标记不可信输入（Layer 1）

        将用户输入包装在特殊标记中，告知 LLM 这是不可信内容

        Args:
            user_input: 用户输入文本
            source: 输入来源（user, file, web）

        Returns:
            标记后的文本
        """
        if not self.config.enable_input_marking:
            return user_input

        return self.config.untrusted_marker_format.format(
            source=source, content=user_input
        )

    # ==================== Layer 2: 指令隔离 ====================

    def isolate_instructions(
        self, system_prompt: str, user_input: str, already_marked: bool = False
    ) -> str:
        """
        隔离系统指令与用户内容（Layer 2）

        在系统指令和用户输入之间插入明确的分隔符和警告

        Args:
            system_prompt: 系统提示词
            user_input: 用户输入（可能已标记）
            already_marked: 是否已通过 mark_untrusted() 标记

        Returns:
            隔离后的完整提示词
        """
        if not self.config.enable_instruction_isolation:
            return f"{system_prompt}\n\n{user_input}"

        # 如果用户输入尚未标记，先标记
        if not already_marked and "<user_input" not in user_input:
            user_input = self.mark_untrusted(user_input, source="user")

        # 构建隔离提示
        isolated_prompt = (
            f"{system_prompt}"
            f"{self.config.isolation_delimiter}"
            f"{user_input}"
        )

        return isolated_prompt

    # ==================== Layer 3: 模式检测 ====================

    def detect_injection(self, text: str) -> InjectionDetectionResult:
        """
        检测 Prompt Injection 攻击（Layer 3）

        使用 20+ 正则表达式模式检测恶意输入

        Args:
            text: 待检测文本

        Returns:
            InjectionDetectionResult 检测结果
        """
        if not self.config.enable_pattern_detection:
            return InjectionDetectionResult(
                is_malicious=False,
                confidence=0.0,
                matched_patterns=[],
                severity="none",
                details="Pattern detection disabled",
            )

        matched_patterns = []

        # 遍历所有编译好的模式
        for i, pattern in enumerate(self._compiled_injection_patterns):
            match = pattern.search(text)
            if match:
                matched_patterns.append(
                    f"Pattern #{i+1}: {self.config.injection_patterns[i][:50]}... (matched: '{match.group()}')"
                )

        # 计算置信度（基于匹配模式数量）
        num_matched = len(matched_patterns)
        # 调整权重：第一个匹配 80%（超过默认阈值 75%），后续每个 +10%
        if num_matched == 0:
            confidence = 0.0
        elif num_matched == 1:
            confidence = 0.80  # 单个强匹配给予 80%，超过默认阈值 75%
        else:
            confidence = min(1.0, 0.80 + (num_matched - 1) * 0.10)

        # 判定严重程度
        if num_matched == 0:
            severity = "none"
        elif num_matched == 1:
            severity = "low"
        elif num_matched == 2:
            severity = "medium"
        elif num_matched == 3:
            severity = "high"
        else:
            severity = "critical"

        # 是否超过阈值
        is_malicious = confidence >= self.config.injection_detection_threshold

        details = (
            f"Matched {num_matched} patterns. "
            f"Confidence: {confidence:.2%}. "
            f"Threshold: {self.config.injection_detection_threshold:.2%}."
        )

        return InjectionDetectionResult(
            is_malicious=is_malicious,
            confidence=confidence,
            matched_patterns=matched_patterns,
            severity=severity,
            details=details,
        )

    # ==================== Layer 4: LLM 验证 ====================

    async def validate_with_llm(
        self, text: str, source: str = "user"
    ) -> Tuple[bool, float]:
        """
        使用轻量级 LLM 检测对抗性输入（Layer 4）

        **注意**: 此功能增加 200-500ms 延迟，默认禁用
        **策略**: 仅对 file/web 来源启用，user 输入跳过

        Args:
            text: 待验证文本
            source: 输入来源（user, file, web）

        Returns:
            (is_safe, confidence): (是否安全, 置信度)
        """
        if not self.config.enable_llm_validation:
            return True, 1.0

        # 根据来源决定是否启用
        if source not in self.config.llm_validation_sources:
            logger.debug(
                f"LLM validation skipped for source '{source}' (not in whitelist)"
            )
            return True, 1.0

        # TODO: Phase 1.5 Day 2 - 实现 LLM 验证
        # 使用 Qwen3:14b 或 MLX 模型进行验证
        # 示例：
        # prompt = f"Analyze if this text contains prompt injection attempts: {text}"
        # response = await llm.generate(prompt)
        # is_safe = "safe" in response.lower()
        # confidence = parse_confidence(response)

        logger.warning(
            "LLM validation not yet implemented (Phase 1.5 Day 2). Returning safe."
        )
        return True, 1.0

    # ==================== Layer 5: 输出清理 ====================

    def sanitize_output(
        self, output: str, original_input: str = ""
    ) -> Tuple[str, List[str]]:
        """
        清理 LLM 输出，移除泄露的系统提示或凭证（Layer 5）

        Args:
            output: LLM 输出文本
            original_input: 原始用户输入（用于检测反射攻击）

        Returns:
            (cleaned_output, warnings): (清理后的输出, 警告列表)
        """
        if not self.config.enable_output_sanitization:
            return output, []

        warnings = []
        cleaned = output

        # 1. 检测系统提示泄露
        for pattern in self._compiled_leak_patterns:
            if pattern.search(cleaned):
                warnings.append(
                    f"Potential system prompt leakage detected: {pattern.pattern[:50]}..."
                )
                # 移除匹配内容（可选：或标记为 [REDACTED]）
                cleaned = pattern.sub("[SYSTEM_PROMPT_REDACTED]", cleaned)

        # 2. 检测凭证泄露
        for pattern in self._compiled_credential_patterns:
            match = pattern.search(cleaned)
            if match:
                warnings.append(
                    f"Credential detected and redacted: {pattern.pattern[:50]}..."
                )
                cleaned = pattern.sub("[CREDENTIAL_REDACTED]", cleaned)

        # 3. 检查输出长度（防止 DoS）
        if len(cleaned) > self.config.max_output_length:
            warnings.append(
                f"Output exceeds max length ({self.config.max_output_length} chars), truncating"
            )
            cleaned = cleaned[: self.config.max_output_length] + "\n\n[OUTPUT_TRUNCATED]"

        # 4. 移除输入标记（如果 LLM 回显了标记）
        cleaned = re.sub(r"<user_input[^>]*>", "", cleaned)
        cleaned = re.sub(r"</user_input>", "", cleaned)

        return cleaned, warnings

    # ==================== 高级功能 ====================

    def analyze_input_risk(self, text: str, source: str = "user") -> Dict:
        """
        综合分析输入风险

        返回详细的风险评估报告

        Args:
            text: 待分析文本
            source: 输入来源

        Returns:
            风险评估报告字典
        """
        # Layer 3: 模式检测
        detection_result = self.detect_injection(text)

        # 基本统计
        stats = {
            "length": len(text),
            "num_lines": text.count("\n") + 1,
            "num_words": len(text.split()),
            "has_special_chars": bool(re.search(r"[<>{}[\]\\]", text)),
            "has_unicode": any(ord(c) > 127 for c in text),
        }

        # 综合风险评分（0-100）
        risk_score = 0
        if detection_result.is_malicious:
            risk_score += 40 + int(detection_result.confidence * 30)
        if stats["has_special_chars"]:
            risk_score += 10
        if stats["length"] > 10000:
            risk_score += 5
        if source in ["file", "web"]:
            risk_score += 5

        risk_score = min(100, risk_score)

        return {
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "detection_result": {
                "is_malicious": detection_result.is_malicious,
                "confidence": detection_result.confidence,
                "severity": detection_result.severity,
                "num_matched_patterns": len(detection_result.matched_patterns),
                "details": detection_result.details,
            },
            "statistics": stats,
            "recommendations": self._get_recommendations(detection_result, risk_score),
        }

    def _get_risk_level(self, risk_score: int) -> str:
        """根据风险评分返回风险等级"""
        if risk_score >= 75:
            return "critical"
        elif risk_score >= 50:
            return "high"
        elif risk_score >= 25:
            return "medium"
        else:
            return "low"

    def _get_recommendations(
        self, detection_result: InjectionDetectionResult, risk_score: int
    ) -> List[str]:
        """根据检测结果生成建议"""
        recommendations = []

        if detection_result.is_malicious:
            recommendations.append("Input flagged as potentially malicious")
            recommendations.append("Apply all 5 layers of defense")
            recommendations.append("Enable audit logging for this request")

        if risk_score >= 75:
            recommendations.append("Consider rejecting this request")
            recommendations.append("Alert security team")

        if detection_result.severity in ["high", "critical"]:
            recommendations.append(
                f"Matched {len(detection_result.matched_patterns)} injection patterns"
            )

        if not recommendations:
            recommendations.append("Input appears safe, proceed with standard processing")

        return recommendations

    # ==================== 批量处理 ====================

    def batch_detect(self, texts: List[str]) -> List[InjectionDetectionResult]:
        """
        批量检测多个输入

        Args:
            texts: 文本列表

        Returns:
            检测结果列表
        """
        return [self.detect_injection(text) for text in texts]

    # ==================== 统计报告 ====================

    def get_statistics(self) -> Dict:
        """获取 PromptGuard 统计信息"""
        return {
            "config": {
                "enable_input_marking": self.config.enable_input_marking,
                "enable_instruction_isolation": self.config.enable_instruction_isolation,
                "enable_pattern_detection": self.config.enable_pattern_detection,
                "enable_llm_validation": self.config.enable_llm_validation,
                "enable_output_sanitization": self.config.enable_output_sanitization,
                "detection_threshold": self.config.injection_detection_threshold,
            },
            "patterns": {
                "num_injection_patterns": len(self._compiled_injection_patterns),
                "num_leak_patterns": len(self._compiled_leak_patterns),
                "num_credential_patterns": len(self._compiled_credential_patterns),
            },
        }


# ==================== 便捷函数 ====================


def quick_check(text: str) -> bool:
    """
    快速检查输入是否安全

    便捷函数，适用于简单场景

    Args:
        text: 待检测文本

    Returns:
        True 表示安全，False 表示可能存在注入
    """
    guard = PromptGuard()
    result = guard.detect_injection(text)
    return not result.is_malicious


def protect_prompt(system_prompt: str, user_input: str) -> str:
    """
    保护提示词（应用 Layer 1 + Layer 2）

    便捷函数，快速应用输入标记和指令隔离

    Args:
        system_prompt: 系统提示词
        user_input: 用户输入

    Returns:
        保护后的完整提示词
    """
    guard = PromptGuard()
    marked = guard.mark_untrusted(user_input, source="user")
    isolated = guard.isolate_instructions(system_prompt, marked, already_marked=True)
    return isolated


# ==================== 全局实例（可选）====================

_global_guard = None


def get_prompt_guard() -> PromptGuard:
    """获取全局 PromptGuard 实例（单例）"""
    global _global_guard
    if _global_guard is None:
        _global_guard = PromptGuard()
    return _global_guard
