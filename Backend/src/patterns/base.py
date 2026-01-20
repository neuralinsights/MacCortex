#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - Base Pattern
Phase 1 - Week 2 Day 8-9
创建时间: 2026-01-20
更新时间: 2026-01-21 (Phase 1.5 - Day 3: 添加安全钩子)

Python Pattern 基类定义
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from loguru import logger


class BasePattern(ABC):
    """AI Pattern 基类（Phase 1.5: 增强安全防护）"""

    def __init__(self, enable_security: bool = True):
        """
        初始化 Pattern

        Args:
            enable_security: 是否启用安全防护（默认 True）
        """
        self._enable_security = enable_security
        self._prompt_guard: Optional[Any] = None  # 延迟加载

        # 初始化 PromptGuard（如果启用）
        if self._enable_security:
            self._init_security()

    @property
    @abstractmethod
    def pattern_id(self) -> str:
        """Pattern ID（唯一标识符）"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Pattern 名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Pattern 描述"""
        pass

    @property
    def version(self) -> str:
        """Pattern 版本"""
        return "1.0.0"

    @abstractmethod
    async def execute(
        self, text: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行 Pattern

        Args:
            text: 输入文本
            parameters: 参数字典

        Returns:
            Dict[str, Any]: 执行结果
                {
                    "output": str,           # 输出文本
                    "metadata": Dict[str, Any] | None,  # 元数据
                }

        Raises:
            ValueError: 参数无效
            RuntimeError: 执行失败
        """
        pass

    def validate(self, text: str, parameters: Dict[str, Any]) -> bool:
        """
        验证输入

        Args:
            text: 输入文本
            parameters: 参数字典

        Returns:
            bool: 是否有效
        """
        # 基本验证
        if not text or not text.strip():
            return False

        return True

    async def initialize(self):
        """初始化资源（如加载模型）"""
        pass

    async def cleanup(self):
        """清理资源"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }

    # ==================== Phase 1.5: 安全钩子 ====================

    def _init_security(self):
        """初始化安全模块（延迟加载）"""
        try:
            from security.prompt_guard import get_prompt_guard

            self._prompt_guard = get_prompt_guard()
            logger.debug(f"✓ {self.pattern_id}: 安全模块已启用")
        except ImportError as e:
            logger.warning(
                f"⚠️ {self.pattern_id}: 无法导入安全模块，安全防护已禁用: {e}"
            )
            self._enable_security = False

    def _check_injection(self, text: str, source: str = "user") -> Dict[str, Any]:
        """
        检测 Prompt Injection 攻击（Phase 1.5）

        Args:
            text: 待检测文本
            source: 输入来源（user, file, web）

        Returns:
            检测结果字典 {
                "is_malicious": bool,
                "confidence": float,
                "severity": str,
                "details": str
            }
        """
        if not self._enable_security or self._prompt_guard is None:
            return {
                "is_malicious": False,
                "confidence": 0.0,
                "severity": "none",
                "details": "Security disabled",
            }

        result = self._prompt_guard.detect_injection(text)

        return {
            "is_malicious": result.is_malicious,
            "confidence": result.confidence,
            "severity": result.severity,
            "details": result.details,
        }

    def _protect_prompt(
        self, system_prompt: str, user_input: str, source: str = "user"
    ) -> str:
        """
        保护提示词（应用 Layer 1 + Layer 2 防护）

        Args:
            system_prompt: 系统提示词
            user_input: 用户输入
            source: 输入来源

        Returns:
            保护后的完整提示词
        """
        if not self._enable_security or self._prompt_guard is None:
            return f"{system_prompt}\n\n{user_input}"

        # Layer 1: 标记不可信输入
        marked = self._prompt_guard.mark_untrusted(user_input, source=source)

        # Layer 2: 指令隔离
        protected = self._prompt_guard.isolate_instructions(
            system_prompt, marked, already_marked=True
        )

        return protected

    def _sanitize_output(self, output: str, original_input: str = "") -> str:
        """
        清理 LLM 输出（Layer 5）

        Args:
            output: LLM 输出文本
            original_input: 原始用户输入

        Returns:
            清理后的输出
        """
        if not self._enable_security or self._prompt_guard is None:
            return output

        cleaned, warnings = self._prompt_guard.sanitize_output(output, original_input)

        if warnings:
            logger.warning(
                f"🔒 {self.pattern_id}: 输出已清理 ({len(warnings)} 个警告)"
            )
            for warning in warnings:
                logger.debug(f"   - {warning}")

        return cleaned
