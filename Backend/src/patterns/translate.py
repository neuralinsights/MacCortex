#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

# MacCortex TranslatePattern - 翻译模式
# Phase 1 - Week 2 Day 9
# 创建时间: 2026-01-20
# 更新时间: 2026-01-21 (Phase 1.5 - Day 3: 集成 PromptGuard)
#
# Phase 1.5: 增强安全防护（Prompt Injection 检测、指令隔离、输出清理）
#
# 多语言翻译（支持中文、英文、日文、韩文等）

import asyncio
from typing import Any, Dict
from loguru import logger

from .base import BasePattern
from utils.config import settings


class TranslatePattern(BasePattern):
    """
    翻译 Pattern

    支持多种语言之间的翻译：
    - 中文 ↔ 英文、日文、韩文、法文、德文、西班牙文等
    - 自动检测源语言
    - 保留格式与术语
    - 支持专业术语词典
    """

    def __init__(self):
        super().__init__()  # Phase 1.5: 初始化安全模块
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._ollama_client = None
        self._mode = "uninitialized"  # uninitialized | mlx | ollama | mock

    # MARK: - BasePattern Protocol

    @property
    def pattern_id(self) -> str:
        return "translate"

    @property
    def name(self) -> str:
        return "Translate"

    @property
    def description(self) -> str:
        return "多语言翻译（支持中英日韩法德西等）"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def initialize(self):
        """初始化模型"""
        logger.info(f"🔧 初始化 {self.name} Pattern...")

        # 尝试加载 MLX 模型（Apple Silicon 优化）
        try:
            await self._initialize_mlx()
        except Exception as e:
            logger.warning(f"MLX 初始化失败，回退到 Ollama: {e}")
            try:
                await self._initialize_ollama()
            except Exception as e2:
                logger.warning(f"Ollama 初始化失败，使用 Mock 模式: {e2}")
                logger.info("  ⚠️  使用 Mock 模式（用于测试）")

    async def _initialize_mlx(self):
        """初始化 MLX 模型"""
        try:
            import mlx.core as mx
            from mlx_lm import load

            logger.info(f"  🍎 加载 MLX 模型: {settings.mlx_model}")

            # 异步加载模型（复用 SummarizePattern 的模型）
            loop = asyncio.get_event_loop()
            self._mlx_model, self._mlx_tokenizer = await loop.run_in_executor(
                None, load, settings.mlx_model
            )

            self._mode = "mlx"
            logger.info("  ✅ MLX 模型加载成功")
        except ImportError:
            raise RuntimeError("MLX 未安装")
        except Exception as e:
            raise RuntimeError(f"MLX 初始化失败: {e}")

    async def _initialize_ollama(self):
        """初始化 Ollama 客户端"""
        try:
            import ollama

            logger.info(f"  🦙 连接 Ollama: {settings.ollama_model}")

            # 测试连接
            client = ollama.AsyncClient()
            try:
                await client.generate(
                    model=settings.ollama_model, prompt="test", options={"num_predict": 1}
                )
                self._ollama_client = client
                self._mode = "ollama"
                logger.info("  ✅ Ollama 连接成功")
            except Exception as e:
                raise RuntimeError(f"Ollama 连接失败: {e}")
        except ImportError:
            raise RuntimeError("Ollama 未安装")

    async def cleanup(self):
        """清理资源"""
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._ollama_client = None
        logger.info(f"✅ {self.name} Pattern 清理完成")

    async def execute(self, text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行翻译

        Args:
            text: 输入文本
            parameters: 翻译参数
                - target_language: 目标语言 (必填, 如 "en", "ja", "ko", "fr", "de", "es")
                - source_language: 源语言 (可选, 默认 "auto" 自动检测)
                - style: 翻译风格 (可选, "formal"|"casual"|"technical", 默认 "formal")
                - preserve_format: 是否保留格式 (默认: true)
                - glossary: 术语词典 (可选, Dict[str, str])

        Returns:
            翻译结果字典
        """
        # 解析参数
        target_language = parameters.get("target_language")
        if not target_language:
            raise ValueError("缺少必填参数: target_language")

        source_language = parameters.get("source_language", "auto")
        style = parameters.get("style", "formal")
        preserve_format = parameters.get("preserve_format", True)
        glossary = parameters.get("glossary", {})

        # 根据模式选择生成方法
        if self._mode == "mlx":
            translation = await self._translate_with_mlx(
                text, source_language, target_language, style, preserve_format, glossary
            )
        elif self._mode == "ollama":
            translation = await self._translate_with_ollama(
                text, source_language, target_language, style, preserve_format, glossary
            )
        else:
            # Mock 模式
            translation = await self._translate_mock(
                text, source_language, target_language, style, preserve_format, glossary
            )

        return {
            "output": translation,  # 统一输出格式
            "metadata": {
                "source_language": source_language,
                "target_language": target_language,
                "style": style,
                "preserve_format": preserve_format,
                "glossary_size": len(glossary),
                "original_length": len(text),
                "translation_length": len(translation),
                "mode": self._mode,
            },
        }

    async def _translate_with_mlx(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: str,
        preserve_format: bool,
        glossary: Dict[str, str],
    ) -> str:
        """使用 MLX 模型进行翻译"""
        from mlx_lm import generate

        # 构建提示词
        prompt = self._build_prompt(text, source_language, target_language, style, preserve_format, glossary)

        # 生成（同步方法，需要在线程池中运行）
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(
            None,
            generate,
            self._mlx_model,
            self._mlx_tokenizer,
            prompt,
            1024,  # max_tokens
        )

        # 提取翻译结果
        return self._extract_translation(output)

    async def _translate_with_ollama(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: str,
        preserve_format: bool,
        glossary: Dict[str, str],
    ) -> str:
        """使用 Ollama 进行翻译"""
        # 构建提示词
        prompt = self._build_prompt(text, source_language, target_language, style, preserve_format, glossary)

        # 生成
        response = await self._ollama_client.generate(
            model=settings.ollama_model, prompt=prompt, options={"temperature": 0.5, "num_predict": 1024}
        )

        # 提取翻译结果
        return self._extract_translation(response["response"])

    async def _translate_mock(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: str,
        preserve_format: bool,
        glossary: Dict[str, str],
    ) -> str:
        """Mock 模式（用于测试）"""
        await asyncio.sleep(0.1)

        # 简单的 Mock 翻译
        mock_translations = {
            "zh-CN_en": "This is a mock translation from Chinese to English.",
            "en_zh-CN": "这是从英文到中文的模拟翻译。",
            "zh-CN_ja": "これは中国語から日本語へのモック翻訳です。",
            "zh-CN_ko": "이것은 중국어에서 한국어로의 모의 번역입니다.",
            "zh-CN_fr": "Ceci est une traduction simulée du chinois vers le français.",
            "zh-CN_de": "Dies ist eine Mock-Übersetzung vom Chinesischen ins Deutsche.",
            "zh-CN_es": "Esta es una traducción simulada del chino al español.",
        }

        # 自动检测源语言（简单判断）
        if source_language == "auto":
            # 检测是否有中文字符
            has_chinese = any("\u4e00" <= c <= "\u9fff" for c in text)
            source_language = "zh-CN" if has_chinese else "en"

        key = f"{source_language}_{target_language}"
        translation = mock_translations.get(key, f"[Mock 翻译] 原文长度: {len(text)} 字符")

        # 添加风格标记
        if style == "formal":
            translation = f"[正式风格] {translation}"
        elif style == "casual":
            translation = f"[随意风格] {translation}"
        elif style == "technical":
            translation = f"[技术风格] {translation}"

        return translation

    def _build_prompt(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: str,
        preserve_format: bool,
        glossary: Dict[str, str],
    ) -> str:
        """
        构建翻译提示词（Phase 2 Week 4 Day 16 优化）

        优化要点：
        1. 简化系统提示，明确任务目标
        2. 强调"只输出翻译"，避免重复原文
        3. 使用 IMPORTANT 标记关键规则
        """
        # 语言代码映射（Phase 2 Week 4 Day 16：同时支持简短和完整格式）
        lang_names = {
            "auto": "自动检测",
            # 中文
            "zh": "简体中文",
            "zh-CN": "简体中文",
            "zh-TW": "繁体中文",
            # 英文
            "en": "English",
            "en-US": "English",
            # 日文
            "ja": "日本語",
            "ja-JP": "日本語",
            # 韩文
            "ko": "한국어",
            "ko-KR": "한국어",
            # 法文
            "fr": "Français",
            "fr-FR": "Français",
            # 德文
            "de": "Deutsch",
            "de-DE": "Deutsch",
            # 西班牙文
            "es": "Español",
            "es-ES": "Español",
            # 俄文
            "ru": "Русский",
            "ru-RU": "Русский",
            # 阿拉伯文
            "ar": "العربية",
            "ar-AR": "العربية",
        }

        target_name = lang_names.get(target_language, target_language)

        # 风格描述映射（更简洁）
        style_map = {
            "formal": "formal and professional",
            "casual": "casual and conversational",
            "technical": "technical and precise"
        }
        style_desc = style_map.get(style, "natural")

        # 根据目标语言选择系统提示语言（Phase 2 Week 4 Day 16 优化 v2）
        # 为中文、日文、韩文等目标语言使用中文系统提示，增强模型理解
        use_chinese_prompt = target_language in ["zh", "zh-CN", "zh-TW", "ja", "ja-JP", "ko", "ko-KR"]

        if use_chinese_prompt:
            # 中文系统提示（针对亚洲语言翻译优化）
            prompt = f"""你是专业翻译助手。请将以下文本翻译为{target_name}（{style_desc} 风格）。

重要规则：
- 只输出翻译结果，不要解释
- 不要重复原文
- 保留原文的语气和意思"""

            if preserve_format:
                prompt += "\n- 保留原文格式（换行、段落、标点）"

            if glossary:
                glossary_str = ", ".join([f"{k}→{v}" for k, v in glossary.items()])
                prompt += f"\n- 使用这些术语：{glossary_str}"

            # 用户内容（明确分隔）
            prompt += f"\n\n原文：\n{text}\n\n翻译结果："
        else:
            # 英文系统提示（针对西方语言翻译）
            prompt = f"""You are a professional translator.
Translate the following text to {target_name} ({style_desc} style).

IMPORTANT:
- Only output the translation, NO explanations
- Do NOT repeat the original text
- Preserve the meaning and tone"""

            if preserve_format:
                prompt += "\n- Keep the formatting (line breaks, paragraphs, punctuation)"

            if glossary:
                glossary_str = ", ".join([f"{k}→{v}" for k, v in glossary.items()])
                prompt += f"\n- Use these terms: {glossary_str}"

            # 用户内容（明确分隔）
            prompt += f"\n\nText to translate:\n{text}\n\nTranslation:"

        return prompt

    def _extract_translation(self, output: str) -> str:
        """从模型输出中提取翻译结果"""
        # 去除可能的前缀/后缀说明
        output = output.strip()

        # 移除常见的前缀模式
        prefixes = ["翻译结果：", "Translation:", "译文：", "Result:"]
        for prefix in prefixes:
            if output.startswith(prefix):
                output = output[len(prefix) :].strip()

        # 移除代码块标记（如果有）
        if output.startswith("```") and output.endswith("```"):
            lines = output.split("\n")
            output = "\n".join(lines[1:-1])

        return output.strip()
