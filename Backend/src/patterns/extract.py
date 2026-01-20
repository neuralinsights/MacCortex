#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

# MacCortex ExtractPattern - 信息提取模式
# Phase 1 - Week 2 Day 9
# 创建时间: 2026-01-20
#
# 从文本中提取结构化信息（实体、关键词、联系方式、日期等）

import asyncio
from typing import Any, Dict
from loguru import logger

from .base import BasePattern
from utils.config import settings


class ExtractPattern(BasePattern):
    """
    信息提取 Pattern

    从非结构化文本中提取结构化信息：
    - 实体识别（人名、地名、组织机构）
    - 关键词提取
    - 联系方式（邮箱、电话、网址）
    - 日期时间
    - 自定义实体
    """

    def __init__(self):
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._ollama_client = None
        self._mode = "uninitialized"  # uninitialized | mlx | ollama | mock

    # MARK: - BasePattern Protocol

    @property
    def pattern_id(self) -> str:
        return "extract"

    @property
    def name(self) -> str:
        return "Extract"

    @property
    def description(self) -> str:
        return "从文本中提取结构化信息（实体、关键词、联系方式等）"

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
        执行信息提取

        Args:
            text: 输入文本
            parameters: 提取参数
                - entity_types: 实体类型列表 (默认: ["person", "organization", "location"])
                - extract_keywords: 是否提取关键词 (默认: true)
                - extract_contacts: 是否提取联系方式 (默认: true)
                - extract_dates: 是否提取日期时间 (默认: true)
                - custom_entities: 自定义实体类型列表 (可选)
                - language: 语言 (默认: "zh-CN")

        Returns:
            提取结果字典
        """
        # 解析参数
        entity_types = parameters.get("entity_types", ["person", "organization", "location"])
        extract_keywords = parameters.get("extract_keywords", True)
        extract_contacts = parameters.get("extract_contacts", True)
        extract_dates = parameters.get("extract_dates", True)
        custom_entities = parameters.get("custom_entities", [])
        language = parameters.get("language", "zh-CN")

        # 根据模式选择生成方法
        if self._mode == "mlx":
            result = await self._extract_with_mlx(
                text, entity_types, extract_keywords, extract_contacts, extract_dates, custom_entities, language
            )
        elif self._mode == "ollama":
            result = await self._extract_with_ollama(
                text, entity_types, extract_keywords, extract_contacts, extract_dates, custom_entities, language
            )
        else:
            # Mock 模式
            result = await self._extract_mock(
                text, entity_types, extract_keywords, extract_contacts, extract_dates, custom_entities, language
            )

        # 构建提取结果
        extraction_result = {
            "entities": result.get("entities", {}),
            "keywords": result.get("keywords", []) if extract_keywords else [],
            "contacts": result.get("contacts", {}) if extract_contacts else {},
            "dates": result.get("dates", []) if extract_dates else [],
        }

        # 序列化为 JSON 字符串（统一输出格式）
        import json
        output = json.dumps(extraction_result, ensure_ascii=False, indent=2)

        return {
            "output": output,
            "metadata": {
                "entity_types": entity_types,
                "extract_keywords": extract_keywords,
                "extract_contacts": extract_contacts,
                "extract_dates": extract_dates,
                "custom_entities": custom_entities,
                "language": language,
                "text_length": len(text),
                "mode": self._mode,
            },
        }

    async def _extract_with_mlx(
        self,
        text: str,
        entity_types: list,
        extract_keywords: bool,
        extract_contacts: bool,
        extract_dates: bool,
        custom_entities: list,
        language: str,
    ) -> Dict[str, Any]:
        """使用 MLX 模型进行信息提取"""
        from mlx_lm import generate

        # 构建提示词
        prompt = self._build_prompt(
            text, entity_types, extract_keywords, extract_contacts, extract_dates, custom_entities, language
        )

        # 生成（同步方法，需要在线程池中运行）
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(
            None,
            generate,
            self._mlx_model,
            self._mlx_tokenizer,
            prompt,
            512,  # max_tokens
        )

        # 解析输出为结构化数据
        return self._parse_extraction_output(output)

    async def _extract_with_ollama(
        self,
        text: str,
        entity_types: list,
        extract_keywords: bool,
        extract_contacts: bool,
        extract_dates: bool,
        custom_entities: list,
        language: str,
    ) -> Dict[str, Any]:
        """使用 Ollama 进行信息提取"""
        # 构建提示词
        prompt = self._build_prompt(
            text, entity_types, extract_keywords, extract_contacts, extract_dates, custom_entities, language
        )

        # 生成
        response = await self._ollama_client.generate(
            model=settings.ollama_model, prompt=prompt, options={"temperature": 0.3, "num_predict": 512}
        )

        # 解析输出
        return self._parse_extraction_output(response["response"])

    async def _extract_mock(
        self,
        text: str,
        entity_types: list,
        extract_keywords: bool,
        extract_contacts: bool,
        extract_dates: bool,
        custom_entities: list,
        language: str,
    ) -> Dict[str, Any]:
        """Mock 模式（用于测试）"""
        await asyncio.sleep(0.1)

        result = {"entities": {}, "keywords": [], "contacts": {}, "dates": []}

        # Mock 实体提取
        if "person" in entity_types:
            result["entities"]["person"] = ["张三", "李四"] if language == "zh-CN" else ["John Doe", "Jane Smith"]
        if "organization" in entity_types:
            result["entities"]["organization"] = ["苹果公司"] if language == "zh-CN" else ["Apple Inc."]
        if "location" in entity_types:
            result["entities"]["location"] = ["北京", "上海"] if language == "zh-CN" else ["Beijing", "Shanghai"]

        # Mock 关键词提取
        if extract_keywords:
            result["keywords"] = (
                ["MacCortex", "智能", "基础设施"] if language == "zh-CN" else ["MacCortex", "intelligence", "infrastructure"]
            )

        # Mock 联系方式提取
        if extract_contacts:
            result["contacts"] = {"email": ["test@example.com"], "phone": ["+86-138-0000-0000"], "url": ["https://example.com"]}

        # Mock 日期提取
        if extract_dates:
            result["dates"] = ["2026-01-20"]

        return result

    def _build_prompt(
        self,
        text: str,
        entity_types: list,
        extract_keywords: bool,
        extract_contacts: bool,
        extract_dates: bool,
        custom_entities: list,
        language: str,
    ) -> str:
        """构建信息提取提示词"""
        if language == "zh-CN":
            prompt = f"""你是一个专业的信息提取助手。请从以下文本中提取信息：

文本：
{text}

提取任务：
"""
            if entity_types:
                entity_names = {"person": "人名", "organization": "组织机构", "location": "地点"}
                types_str = "、".join([entity_names.get(t, t) for t in entity_types])
                prompt += f"1. 实体识别：{types_str}\n"

            if extract_keywords:
                prompt += "2. 关键词提取：提取 3-5 个核心关键词\n"

            if extract_contacts:
                prompt += "3. 联系方式：邮箱、电话、网址\n"

            if extract_dates:
                prompt += "4. 日期时间：提取所有日期和时间信息\n"

            if custom_entities:
                prompt += f"5. 自定义实体：{', '.join(custom_entities)}\n"

            prompt += "\n请以 JSON 格式输出结果。"
        else:
            prompt = f"""You are a professional information extraction assistant. Extract information from the following text:

Text:
{text}

Extraction tasks:
"""
            if entity_types:
                prompt += f"1. Named entities: {', '.join(entity_types)}\n"

            if extract_keywords:
                prompt += "2. Keywords: Extract 3-5 core keywords\n"

            if extract_contacts:
                prompt += "3. Contact information: emails, phones, URLs\n"

            if extract_dates:
                prompt += "4. Dates and times: Extract all date/time information\n"

            if custom_entities:
                prompt += f"5. Custom entities: {', '.join(custom_entities)}\n"

            prompt += "\nPlease output the result in JSON format."

        return prompt

    def _parse_extraction_output(self, output: str) -> Dict[str, Any]:
        """解析提取输出为结构化数据"""
        import json
        import re

        # 尝试直接解析 JSON
        try:
            # 查找 JSON 代码块
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # 查找裸 JSON
            json_match = re.search(r"\{.*\}", output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

        # 如果无法解析，返回默认结构
        logger.warning(f"无法解析提取输出，返回默认结构: {output[:100]}")
        return {"entities": {}, "keywords": [], "contacts": {}, "dates": []}
