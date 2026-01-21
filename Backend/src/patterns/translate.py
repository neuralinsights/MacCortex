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
from utils.cache import TranslationCache  # Phase 3: 翻译缓存


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
        self._mode = "uninitialized"  # uninitialized | aya | mlx | ollama | mock
        self._aya_available = False  # Phase 3: aya-23 翻译模型可用性

        # Phase 3 Backend 优化: 翻译缓存（LRU, 1000 条）
        self._cache = TranslationCache(max_size=1000, ttl_seconds=3600)  # 1 小时过期

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
        """
        初始化模型（Phase 3: 优先使用 aya-23 翻译模型）

        优先级顺序：
        1. aya:8b (Ollama) - 专业翻译模型（Phase 3 新增）
        2. MLX Llama-3.2-1B - 通用模型（质量有限）
        3. Ollama 通用模型 - 回退选项
        4. Mock 模式 - 测试用
        """
        logger.info(f"🔧 初始化 {self.name} Pattern...")

        # Phase 3: 优先尝试 aya-23 翻译模型（Ollama）
        try:
            await self._initialize_aya()
            return  # aya 成功，直接返回
        except Exception as e:
            logger.info(f"  ℹ️  aya 模型不可用: {e}")

        # 回退：尝试加载 MLX 模型（Apple Silicon 优化）
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

    async def _initialize_aya(self):
        """
        初始化 aya-23 翻译模型（Phase 3 新增）

        aya-23 是 Cohere 开发的专业多语言翻译模型，支持 100+ 语言。
        相比 Llama-3.2-1B，翻译质量提升 3-5 倍。

        优先尝试顺序：
        1. aya:8b (~5 GB) - 推荐，平衡性能与质量
        2. aya:latest (aya-23, ~13 GB) - 最高质量
        """
        try:
            import ollama

            logger.info("  🌍 检测 aya 翻译模型...")

            client = ollama.AsyncClient()

            # 获取已安装的模型列表（Phase 3 Bug 修复：ollama 返回对象非字典）
            models_response = await client.list()
            installed_models = [m.model for m in models_response.models]

            # 优先使用 aya:8b（轻量版）
            aya_model = None
            if any('aya:8b' in m for m in installed_models):
                aya_model = "aya:8b"
            elif any('aya' in m for m in installed_models):
                # 使用任何可用的 aya 模型
                aya_model = next(m for m in installed_models if 'aya' in m)

            if not aya_model:
                raise RuntimeError("aya 模型未安装（运行: ollama pull aya:8b）")

            # 测试连接
            logger.info(f"  🌍 测试 aya 模型: {aya_model}")
            test_response = await client.generate(
                model=aya_model,
                prompt="Translate to English: 你好",
                options={"num_predict": 10}
            )

            # Phase 3 Bug 修复：test_response 是对象，使用属性访问
            if not test_response.response:
                raise RuntimeError("aya 模型响应为空")

            # 成功
            self._ollama_client = client
            self._aya_available = True
            self._mode = "aya"
            logger.info(f"  ✅ aya 翻译模型就绪: {aya_model}")
            logger.info("     预期质量提升: 3-5x vs Llama-3.2-1B")

        except ImportError:
            raise RuntimeError("Ollama 未安装")
        except Exception as e:
            raise RuntimeError(f"aya 初始化失败: {e}")

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

        # Phase 3 Backend 优化: 检查缓存
        cached_translation = self._cache.get(text, target_language, source_language, style)
        if cached_translation is not None:
            logger.info(
                f"🚀 缓存命中 | hit_rate={self._cache.hit_rate:.1%} | "
                f"text_preview={text[:30]}..."
            )
            return {
                "output": cached_translation,
                "metadata": {
                    "source_language": source_language,
                    "target_language": target_language,
                    "style": style,
                    "preserve_format": preserve_format,
                    "glossary_size": len(glossary),
                    "original_length": len(text),
                    "translation_length": len(cached_translation),
                    "mode": self._mode,
                    "cached": True,  # 标记为缓存结果
                    "cache_stats": self._cache.stats,  # 缓存统计
                },
            }

        # Phase 3: 根据模式选择生成方法（优先使用 aya）
        if self._mode == "aya":
            translation = await self._translate_with_aya(
                text, source_language, target_language, style, preserve_format, glossary
            )
        elif self._mode == "mlx":
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

        # Phase 3 Backend 优化: 存入缓存
        self._cache.put(text, target_language, translation, source_language, style)
        logger.debug(
            f"缓存存入 | cache_size={len(self._cache._cache)} | "
            f"hit_rate={self._cache.hit_rate:.1%}"
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
                "cached": False,  # 标记为新翻译
                "cache_stats": self._cache.stats,  # 缓存统计
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

    async def _translate_with_aya(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: str,
        preserve_format: bool,
        glossary: Dict[str, str],
    ) -> str:
        """
        使用 aya-23 进行翻译（Phase 3 新增）

        aya-23 是专业多语言翻译模型，相比 Llama-3.2-1B 有显著提升：
        - 支持 100+ 语言
        - 翻译质量提升 3-5 倍
        - 更准确的语义理解
        - 更好的格式保留
        """
        # 获取 aya 模型名称（Phase 3 Bug 修复：ollama 返回对象非字典）
        models_response = await self._ollama_client.list()
        installed_models = [m.model for m in models_response.models]
        aya_model = next((m for m in installed_models if 'aya' in m), "aya:8b")

        # 构建优化的 aya 提示词（aya 模型特定优化）
        prompt = self._build_aya_prompt(text, source_language, target_language, style, preserve_format, glossary)

        # 生成（aya 模型推荐参数）
        response = await self._ollama_client.generate(
            model=aya_model,
            prompt=prompt,
            options={
                "temperature": 0.3,  # 低温度确保翻译准确性
                "num_predict": min(len(text) * 3, 2048),  # 动态 token 限制
                "top_p": 0.9,
                "repeat_penalty": 1.1,  # 避免重复
            }
        )

        # 提取翻译结果（Phase 3 Bug 修复：response 是对象，使用属性访问）
        translation = self._extract_translation(response.response)

        # aya 特殊清理：移除可能的元数据
        if translation.startswith("[") and "]" in translation:
            # 移除 [语言] 前缀
            translation = translation.split("]", 1)[-1].strip()

        return translation

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

        # 提取翻译结果（Phase 3 Bug 修复：response 是对象，使用属性访问）
        return self._extract_translation(response.response)

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

    def _build_aya_prompt(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: str,
        preserve_format: bool,
        glossary: Dict[str, str],
    ) -> str:
        """
        构建 aya-23 专用翻译提示词（Phase 3 新增）

        aya-23 模型特性优化：
        1. 原生支持 100+ 语言，无需复杂语言映射
        2. 更擅长理解简洁直接的指令
        3. 自带语言检测能力，source_language 可选
        4. 更好的格式保留能力

        提示词设计原则：
        - 使用英文指令（aya 模型训练优化）
        - 简洁明确的任务描述
        - 强调"直接输出翻译"
        - 利用 aya 的多语言理解优势
        """
        # 语言代码映射（aya 原生支持标准 ISO 639-1 代码）
        lang_names = {
            "auto": "detected language",
            # 简化映射：aya 支持标准代码
            "zh": "Chinese",
            "zh-CN": "Simplified Chinese",
            "zh-TW": "Traditional Chinese",
            "en": "English",
            "en-US": "English",
            "ja": "Japanese",
            "ja-JP": "Japanese",
            "ko": "Korean",
            "ko-KR": "Korean",
            "fr": "French",
            "fr-FR": "French",
            "de": "German",
            "de-DE": "German",
            "es": "Spanish",
            "es-ES": "Spanish",
            "ru": "Russian",
            "ru-RU": "Russian",
            "ar": "Arabic",
            "ar-AR": "Arabic",
            "pt": "Portuguese",
            "pt-BR": "Brazilian Portuguese",
            "it": "Italian",
            "nl": "Dutch",
            "pl": "Polish",
            "tr": "Turkish",
            "vi": "Vietnamese",
            "th": "Thai",
            "id": "Indonesian",
            "hi": "Hindi",
        }

        target_name = lang_names.get(target_language, target_language)
        source_name = lang_names.get(source_language, source_language)

        # 风格描述（aya 更理解英文指令）
        style_map = {
            "formal": "formal and professional",
            "casual": "casual and conversational",
            "technical": "technical and precise"
        }
        style_desc = style_map.get(style, "natural")

        # aya 专用简洁提示词（基于 Cohere 推荐格式）
        if source_language == "auto":
            # 无源语言，依赖 aya 的自动检测
            prompt = f"""Translate this text to {target_name} ({style_desc} style).

Rules:
- Output ONLY the translation
- NO explanations or comments
- Preserve meaning and tone"""
        else:
            # 明确源语言（提高准确性）
            prompt = f"""Translate from {source_name} to {target_name} ({style_desc} style).

Rules:
- Output ONLY the translation
- NO explanations or comments
- Preserve meaning and tone"""

        # 格式保留（aya 擅长）
        if preserve_format:
            prompt += "\n- Keep original formatting (line breaks, paragraphs, punctuation)"

        # 术语词典（aya 的上下文理解能力强）
        if glossary:
            glossary_str = ", ".join([f'"{k}" → "{v}"' for k, v in glossary.items()])
            prompt += f"\n- Use these terms: {glossary_str}"

        # 用户内容（清晰分隔）
        prompt += f"\n\nText:\n{text}\n\nTranslation:"

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

    # MARK: - Streaming Support (Phase 3 Week 3)

    async def execute_stream(self, text: str, parameters: Dict[str, Any]):
        """
        流式翻译（Server-Sent Events）

        Phase 3 Week 3 Day 1 新增功能
        返回 StreamingResponse，逐字发送翻译结果（类似 ChatGPT 打字效果）

        Args:
            text: 输入文本
            parameters: 翻译参数（同 execute）

        Returns:
            StreamingResponse（text/event-stream）
        """
        from fastapi.responses import StreamingResponse
        import json

        async def event_generator():
            """SSE 事件生成器"""
            try:
                # 1. 发送开始事件
                yield f"event: start\n"
                yield f"data: {json.dumps({'status': 'started', 'input_length': len(text)})}\n\n"
                await asyncio.sleep(0.01)  # 确保事件顺序

                # 2. 解析参数
                target_language = parameters.get("target_language")
                if not target_language:
                    yield f"event: error\n"
                    yield f"data: {json.dumps({'error': '缺少必填参数: target_language'})}\n\n"
                    return

                source_language = parameters.get("source_language", "auto")
                style = parameters.get("style", "formal")

                # 3. 检查缓存
                cached_translation = self._cache.get(text, target_language, source_language, style)

                if cached_translation is not None:
                    # 缓存命中：模拟打字效果发送缓存结果
                    yield f"event: cached\n"
                    yield f"data: {json.dumps({'cached': True, 'hit_rate': self._cache.hit_rate})}\n\n"

                    # 逐字发送（每次 5 个字符，50ms 延迟）
                    chunk_size = 5
                    for i in range(0, len(cached_translation), chunk_size):
                        chunk = cached_translation[i:i+chunk_size]
                        yield f"event: chunk\n"
                        yield f"data: {json.dumps({'text': chunk})}\n\n"
                        await asyncio.sleep(0.05)  # 50ms 打字延迟

                    # 发送完成事件（包含元数据）
                    metadata = {
                        "source_language": source_language,
                        "target_language": target_language,
                        "style": style,
                        "cached": True,
                        "cache_stats": self._cache.stats,
                        "mode": self._mode,
                    }
                    yield f"event: done\n"
                    yield f"data: {json.dumps({'output': cached_translation, 'metadata': metadata})}\n\n"

                else:
                    # 缓存未命中：流式翻译
                    yield f"event: translating\n"
                    yield f"data: {json.dumps({'cached': False})}\n\n"

                    # 根据模式选择流式方法
                    if self._mode == "aya":
                        async for chunk in self._translate_stream_aya(
                            text, source_language, target_language, style, parameters
                        ):
                            yield f"event: chunk\n"
                            yield f"data: {json.dumps({'text': chunk})}\n\n"
                    else:
                        # 非 aya 模式：回退到普通翻译 + 模拟流式
                        logger.warning("流式翻译仅支持 aya 模式，回退到模拟流式")
                        translation = await self.execute(text, parameters)
                        full_text = translation["output"]

                        # 模拟打字效果
                        chunk_size = 5
                        for i in range(0, len(full_text), chunk_size):
                            chunk = full_text[i:i+chunk_size]
                            yield f"event: chunk\n"
                            yield f"data: {json.dumps({'text': chunk})}\n\n"
                            await asyncio.sleep(0.05)

                    # 获取完整翻译结果（用于缓存）
                    # 注意：这里需要重新调用 execute 来获取元数据和缓存
                    # 但为避免重复翻译，我们直接构造元数据
                    full_translation = ""  # 从 chunk 累积

                    # TODO: 改进：在流式过程中累积完整文本
                    # 当前实现：发送完成事件但不包含完整文本（客户端自行累积）
                    yield f"event: done\n"
                    yield f"data: {json.dumps({'metadata': {'mode': self._mode, 'cached': False}})}\n\n"

            except Exception as e:
                logger.error(f"流式翻译错误: {e}")
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            }
        )

    async def _translate_stream_aya(
        self,
        text: str,
        source_language: str,
        target_language: str,
        style: str,
        parameters: Dict[str, Any],
    ):
        """
        使用 aya 模型进行流式翻译

        Phase 3 Week 3 Day 1 新增
        利用 Ollama 的流式 API 实时生成翻译

        Yields:
            str: 翻译文本片段
        """
        # 获取 aya 模型名称
        models_response = await self._ollama_client.list()
        installed_models = [m.model for m in models_response.models]
        aya_model = next((m for m in installed_models if 'aya' in m), "aya:8b")

        # 构建提示词
        preserve_format = parameters.get("preserve_format", True)
        glossary = parameters.get("glossary", {})
        prompt = self._build_aya_prompt(
            text, source_language, target_language, style, preserve_format, glossary
        )

        # 调用 Ollama 流式 API
        full_text = ""
        async for part in await self._ollama_client.generate(
            model=aya_model,
            prompt=prompt,
            stream=True,  # 启用流式
            options={
                "temperature": 0.3,
                "num_predict": min(len(text) * 3, 2048),
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            }
        ):
            # ollama 流式响应格式：{response: str, done: bool}
            if hasattr(part, 'response'):
                chunk = part.response
            elif isinstance(part, dict):
                chunk = part.get('response', '')
            else:
                chunk = str(part)

            if chunk:
                full_text += chunk
                yield chunk

        # 流式完成后：存入缓存
        if full_text:
            cleaned_text = self._extract_translation(full_text)
            self._cache.put(text, target_language, cleaned_text, source_language, style)
            logger.debug(f"流式翻译完成，已存入缓存 | length={len(cleaned_text)}")
