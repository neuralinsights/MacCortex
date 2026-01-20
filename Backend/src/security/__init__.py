#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MacCortex Security Module
Phase 1.5 - Security Enhancement
创建时间: 2026-01-21

安全模块，提供 5 层 Prompt Injection 防护、审计日志、输入/输出验证等功能

Copyright (c) 2026 Yu Geng. All rights reserved.
This software is proprietary and confidential.
"""

__author__ = "Yu Geng"
__copyright__ = "Copyright 2026, Yu Geng"
__license__ = "Proprietary"
__version__ = "1.5.0"

from .security_config import SecurityConfig, get_security_config
from .prompt_guard import (
    PromptGuard,
    InjectionDetectionResult,
    get_prompt_guard,
    quick_check,
    protect_prompt,
)

__all__ = [
    "SecurityConfig",
    "get_security_config",
    "PromptGuard",
    "InjectionDetectionResult",
    "get_prompt_guard",
    "quick_check",
    "protect_prompt",
]
