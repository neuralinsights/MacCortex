#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
MacCortex Backend - Summarize Pattern
Phase 1 - Week 2 Day 8-9
创建时间: 2026-01-20
更新时间: 2026-01-21 (Phase 1.5 - Day 3: 集成 PromptGuard)

文本总结 Pattern（使用 MLX 或 Ollama）
Phase 1.5: 增强安全防护（Prompt Injection 检测、指令隔离、输出清理）
"""

import asyncio
from typing import Any, Dict

from loguru import logger

from utils.config import settings
from patterns.base import BasePattern


class SummarizePattern(BasePattern):
    """文本总结 Pattern"""

    def __init__(self):
        """初始化 Pattern"""
        super().__init__()
        self._mlx_model = None
        self._ollama_client = None

    @property
    def pattern_id(self) -> str:
        return "summarize"

    @property
    def name(self) -> str:
        return "Summarize"

    @property
    def description(self) -> str:
        return "Summarize long text into concise key points"

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
            from mlx_lm import load, generate

            logger.info(f"  🍎 加载 MLX 模型: {settings.mlx_model}")

            # 异步加载模型（避免阻塞）
            loop = asyncio.get_event_loop()
            self._mlx_model, self._mlx_tokenizer = await loop.run_in_executor(
                None, load, settings.mlx_model
            )

            logger.info("  ✅ MLX 模型加载成功")
        except ImportError:
            raise RuntimeError("MLX not installed. Install with: pip install mlx mlx-lm")
        except Exception as e:
            raise RuntimeError(f"Failed to load MLX model: {e}")

    async def _initialize_ollama(self):
        """初始化 Ollama 客户端"""
        try:
            import ollama

            self._ollama_client = ollama.AsyncClient(host=settings.ollama_host)

            # 测试连接
            await self._ollama_client.list()
            logger.info(f"  ✅ Ollama 客户端初始化成功 ({settings.ollama_model})")
        except ImportError:
            raise RuntimeError("Ollama not installed. Install with: pip install ollama")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Ollama: {e}")

    def validate(self, text: str, parameters: Dict[str, Any]) -> bool:
        """验证输入"""
        if not super().validate(text, parameters):
            return False

        # 检查文本长度（词数）
        text = text.strip()
        language = parameters.get("language", "zh-CN")

        if language.startswith("zh") or language.startswith("ja") or language.startswith("ko"):
            # 中日韩：每个字符约等于一个词
            word_count = len(text)
            min_words = 15
        else:
            # 西文：按空格分词
            word_count = len([w for w in text.split() if w])
            min_words = 30

        if word_count < min_words:
            logger.warning(
                f"文本过短: {word_count} 词 < {min_words} 词（语言: {language}）"
            )
            return False

        return True

    async def execute(
        self, text: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行总结（Phase 1.5: 增强安全防护）"""
        # 提取参数
        length = parameters.get("length", "medium")
        style = parameters.get("style", "bullet")
        language = parameters.get("language", "zh-CN")
        source = parameters.get("source", "user")  # Phase 1.5: 输入来源

        logger.info(
            f"📝 总结文本: length={length}, style={style}, language={language}, source={source}"
        )

        # ==================== Phase 1.5: Layer 3 - 检测 Prompt Injection ====================
        injection_result = self._check_injection(text, source=source)
        if injection_result["is_malicious"]:
            logger.warning(
                f"🔒 检测到潜在 Prompt Injection: "
                f"置信度={injection_result['confidence']:.2%}, "
                f"严重程度={injection_result['severity']}"
            )
            # 标记为不可信输入（继续处理，但加强防护）

        # 构建系统提示（不含用户输入）
        system_prompt = self._build_system_prompt(length, style, language)

        # ==================== Phase 1.5: Layer 1+2 - 保护提示词 ====================
        protected_prompt = self._protect_prompt(system_prompt, text, source=source)

        # 使用 MLX 或 Ollama 生成总结
        if self._mlx_model is not None:
            output = await self._generate_with_mlx(protected_prompt)
        elif self._ollama_client is not None:
            output = await self._generate_with_ollama(protected_prompt)
        else:
            # Mock 模式（用于测试）
            logger.info("  ⚠️  使用 Mock 输出（MLX/Ollama 未安装）")
            output = await self._generate_mock(text, length, style, language)

        # ==================== Phase 1.5: Layer 5 - 清理输出 ====================
        output = self._sanitize_output(output, text)

        return {
            "output": output,
            "metadata": {
                "length": length,
                "style": style,
                "language": language,
                "source": source,
                "original_length": len(text),
                "summary_length": len(output),
                # Phase 1.5: 安全元数据
                "security": {
                    "injection_detected": injection_result["is_malicious"],
                    "injection_confidence": injection_result["confidence"],
                    "injection_severity": injection_result["severity"],
                },
            },
        }

    def _build_system_prompt(self, length: str, style: str, language: str) -> str:
        """构建系统提示（Phase 1.5: 不含用户输入）"""
        # 长度目标
        length_target = {"short": 50, "medium": 150, "long": 300}.get(length, 150)

        # 风格描述
        style_desc = {
            "bullet": "使用要点列表形式",
            "paragraph": "使用段落形式",
            "headline": "使用简短标题形式",
        }.get(style, "使用要点列表形式")

        # 语言提示
        lang_prompt = {
            "zh-CN": "请用简体中文回答",
            "zh-TW": "請用繁體中文回答",
            "en": "Please respond in English",
            "ja": "日本語で答えてください",
            "ko": "한국어로 답변해 주세요",
        }.get(language, "请用中文回答")

        system_prompt = f"""你是一个专业的文本总结助手。
请根据以下要求总结用户提供的文本：
- 风格：{style_desc}
- 目标长度：约 {length_target} 字
- 语言：{lang_prompt}

重要规则：
1. 仅总结用户提供的文本内容，不要添加额外信息
2. 保持客观中立，不要添加个人观点
3. 专注于核心要点和关键信息
"""

        return system_prompt

    def _build_prompt(
        self, text: str, length: str, style: str, language: str
    ) -> str:
        """构建 LLM 提示词（兼容性方法，Phase 1 代码使用）"""
        system = self._build_system_prompt(length, style, language)
        return f"{system}\n\n原文：\n{text}\n\n总结："

    async def _generate_with_mlx(self, prompt: str) -> str:
        """使用 MLX 生成文本"""
        from mlx_lm import generate

        logger.debug("  🍎 使用 MLX 生成...")

        try:
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                generate,
                self._mlx_model,
                self._mlx_tokenizer,
                prompt,
                settings.mlx_max_tokens,
            )
            return output.strip()
        except Exception as e:
            logger.error(f"MLX 生成失败: {e}")
            raise RuntimeError(f"MLX generation failed: {e}")

    async def _generate_with_ollama(self, prompt: str) -> str:
        """使用 Ollama 生成文本"""
        logger.debug(f"  🦙 使用 Ollama 生成 (model={settings.ollama_model})...")

        try:
            response = await self._ollama_client.generate(
                model=settings.ollama_model,
                prompt=prompt,
                options={
                    "temperature": settings.mlx_temperature,
                    "num_predict": settings.mlx_max_tokens,
                },
            )
            return response["response"].strip()
        except Exception as e:
            logger.error(f"Ollama 生成失败: {e}")
            raise RuntimeError(f"Ollama generation failed: {e}")

    async def _generate_mock(
        self, text: str, length: str, style: str, language: str
    ) -> str:
        """使用 Mock 模式生成总结（用于测试）"""
        import asyncio

        # 模拟处理延迟
        await asyncio.sleep(0.1)

        word_count = {"short": 50, "medium": 150, "long": 300}.get(length, 150)

        if style == "bullet":
            return f"""• 核心要点 1：[Mock 输出，MLX/Ollama 未安装]
• 核心要点 2：原文长度 {len(text)} 字符
• 核心要点 3：目标总结长度 {word_count} 字

⚠️ 这是测试用 Mock 输出，请安装 MLX 或 Ollama 以使用真实 LLM。"""
        elif style == "paragraph":
            return f"[Mock 输出] 这是一段总结性的段落文本。原文长度 {len(text)} 字符，目标总结长度 {word_count} 字。请安装 MLX 或 Ollama 以使用真实 LLM。"
        else:  # headline
            return f"[Mock 输出] 核心标题：关键信息摘要（{word_count} 字目标）"

    async def cleanup(self):
        """清理资源"""
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._ollama_client = None
        logger.debug(f"  🧹 {self.name} Pattern 资源已清理")
