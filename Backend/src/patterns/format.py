#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

# MacCortex FormatPattern - 格式转换模式
# Phase 1 - Week 2 Day 9
# 创建时间: 2026-01-20
# 更新时间: 2026-01-21 (Phase 1.5 - Day 3: 集成 PromptGuard)
#
# Phase 1.5: 增强安全防护（Prompt Injection 检测、指令隔离、输出清理）
#
# 文本格式转换（JSON ↔ YAML, Markdown ↔ HTML, CSV ↔ JSON 等）

import asyncio
from typing import Any, Dict
from loguru import logger

from .base import BasePattern
from utils.config import settings


class FormatPattern(BasePattern):
    """
    格式转换 Pattern

    支持多种格式之间的转换：
    - JSON ↔ YAML ↔ TOML ↔ XML
    - Markdown ↔ HTML ↔ Plain Text
    - CSV ↔ JSON ↔ TSV
    - 代码美化与压缩
    - 自定义格式转换
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
        return "format"

    @property
    def name(self) -> str:
        return "Format"

    @property
    def description(self) -> str:
        return "格式转换（JSON/YAML/Markdown/HTML/CSV 等）"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def initialize(self):
        """初始化模型"""
        logger.info(f"🔧 初始化 {self.name} Pattern...")

        # 格式转换通常不需要 LLM（使用标准库即可）
        # 但对于复杂转换（如自然语言描述 → 结构化数据），可以使用 LLM
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
        """初始化 MLX 模型（可选，用于复杂转换）"""
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
        """初始化 Ollama 客户端（可选，用于复杂转换）"""
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
        执行格式转换

        Args:
            text: 输入文本
            parameters: 转换参数
                - from_format: 源格式 (必填, 如 "json", "yaml", "markdown", "html", "csv")
                - to_format: 目标格式 (必填, 如 "json", "yaml", "markdown", "html", "csv")
                - prettify: 是否美化输出 (默认: true)
                - minify: 是否压缩输出 (默认: false)
                - options: 格式特定选项 (可选)

        Returns:
            转换结果字典
        """
        # 解析参数
        from_format = parameters.get("from_format")
        to_format = parameters.get("to_format")

        if not from_format or not to_format:
            raise ValueError("缺少必填参数: from_format 或 to_format")

        prettify = parameters.get("prettify", True)
        minify = parameters.get("minify", False)
        options = parameters.get("options", {})

        # 执行转换
        try:
            converted = await self._convert_format(text, from_format, to_format, prettify, minify, options)
        except Exception as e:
            logger.error(f"格式转换失败: {e}")
            raise ValueError(f"格式转换失败: {e}")

        return {
            "output": converted,  # 统一输出格式
            "metadata": {
                "from_format": from_format,
                "to_format": to_format,
                "prettify": prettify,
                "minify": minify,
                "original_length": len(text),
                "converted_length": len(converted),
                "mode": self._mode,
            },
        }

    async def _convert_format(
        self, text: str, from_format: str, to_format: str, prettify: bool, minify: bool, options: Dict[str, Any]
    ) -> str:
        """执行实际的格式转换"""
        import json
        import yaml

        # 标准化格式名称
        from_format = from_format.lower()
        to_format = to_format.lower()

        # 使用标准库进行转换（不需要 LLM）
        if from_format == "json" and to_format == "yaml":
            return await self._json_to_yaml(text, prettify)
        elif from_format == "yaml" and to_format == "json":
            return await self._yaml_to_json(text, prettify, minify)
        elif from_format == "json" and to_format == "json":
            # JSON 美化/压缩
            return await self._prettify_json(text, prettify, minify)
        elif from_format == "markdown" and to_format == "html":
            return await self._markdown_to_html(text)
        elif from_format == "html" and to_format == "markdown":
            return await self._html_to_markdown(text)
        elif from_format == "csv" and to_format == "json":
            return await self._csv_to_json(text, options)
        elif from_format == "json" and to_format == "csv":
            return await self._json_to_csv(text, options)
        else:
            # 对于不支持的转换，使用 LLM（如果可用）
            if self._mode == "mlx":
                return await self._convert_with_llm_mlx(text, from_format, to_format)
            elif self._mode == "ollama":
                return await self._convert_with_llm_ollama(text, from_format, to_format)
            else:
                raise ValueError(f"不支持的格式转换: {from_format} → {to_format}")

    async def _json_to_yaml(self, text: str, prettify: bool) -> str:
        """JSON → YAML"""
        import json
        import yaml

        data = json.loads(text)
        return yaml.dump(data, allow_unicode=True, default_flow_style=False if prettify else None, sort_keys=False)

    async def _yaml_to_json(self, text: str, prettify: bool, minify: bool) -> str:
        """YAML → JSON"""
        import json
        import yaml

        data = yaml.safe_load(text)
        if minify:
            return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        elif prettify:
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            return json.dumps(data, ensure_ascii=False)

    async def _prettify_json(self, text: str, prettify: bool, minify: bool) -> str:
        """JSON 美化/压缩"""
        import json

        data = json.loads(text)
        if minify:
            return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        elif prettify:
            return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
        else:
            return json.dumps(data, ensure_ascii=False)

    async def _markdown_to_html(self, text: str) -> str:
        """Markdown → HTML"""
        try:
            import markdown

            return markdown.markdown(text, extensions=["extra", "codehilite"])
        except ImportError:
            # 如果 markdown 库未安装，使用简单转换
            logger.warning("markdown 库未安装，使用简化转换")
            return self._simple_markdown_to_html(text)

    def _simple_markdown_to_html(self, text: str) -> str:
        """简单的 Markdown → HTML 转换"""
        import re

        html = text

        # 标题
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)

        # 粗体和斜体
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

        # 链接
        html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', html)

        # 代码块
        html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)

        # 段落
        html = re.sub(r"\n\n", r"</p><p>", html)
        html = f"<p>{html}</p>"

        return html

    async def _html_to_markdown(self, text: str) -> str:
        """HTML → Markdown"""
        try:
            from html2text import HTML2Text

            h = HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            return h.handle(text)
        except ImportError:
            # 如果 html2text 库未安装，使用简单转换
            logger.warning("html2text 库未安装，使用简化转换")
            return self._simple_html_to_markdown(text)

    def _simple_html_to_markdown(self, text: str) -> str:
        """简单的 HTML → Markdown 转换"""
        import re

        md = text

        # 标题
        md = re.sub(r"<h1>(.+?)</h1>", r"# \1", md, flags=re.IGNORECASE)
        md = re.sub(r"<h2>(.+?)</h2>", r"## \1", md, flags=re.IGNORECASE)
        md = re.sub(r"<h3>(.+?)</h3>", r"### \1", md, flags=re.IGNORECASE)

        # 粗体和斜体
        md = re.sub(r"<strong>(.+?)</strong>", r"**\1**", md, flags=re.IGNORECASE)
        md = re.sub(r"<em>(.+?)</em>", r"*\1*", md, flags=re.IGNORECASE)

        # 链接
        md = re.sub(r'<a href="(.+?)">(.+?)</a>', r"[\2](\1)", md, flags=re.IGNORECASE)

        # 代码
        md = re.sub(r"<code>(.+?)</code>", r"`\1`", md, flags=re.IGNORECASE)

        # 移除段落标签
        md = re.sub(r"</?p>", "\n\n", md, flags=re.IGNORECASE)

        # 移除其他 HTML 标签
        md = re.sub(r"<[^>]+>", "", md)

        return md.strip()

    async def _csv_to_json(self, text: str, options: Dict[str, Any]) -> str:
        """CSV → JSON"""
        import csv
        import json
        from io import StringIO

        delimiter = options.get("delimiter", ",")
        reader = csv.DictReader(StringIO(text), delimiter=delimiter)
        data = list(reader)
        return json.dumps(data, ensure_ascii=False, indent=2)

    async def _json_to_csv(self, text: str, options: Dict[str, Any]) -> str:
        """JSON → CSV"""
        import csv
        import json
        from io import StringIO

        data = json.loads(text)
        if not isinstance(data, list):
            data = [data]

        output = StringIO()
        delimiter = options.get("delimiter", ",")

        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys(), delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)

        return output.getvalue()

    async def _convert_with_llm_mlx(self, text: str, from_format: str, to_format: str) -> str:
        """使用 MLX LLM 进行复杂格式转换"""
        from mlx_lm import generate

        prompt = f"""请将以下 {from_format} 格式的内容转换为 {to_format} 格式：

输入（{from_format}）：
{text}

请直接输出转换后的 {to_format} 格式内容，不要添加任何解释。"""

        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(
            None,
            generate,
            self._mlx_model,
            self._mlx_tokenizer,
            prompt,
            2048,  # max_tokens
        )

        return output.strip()

    async def _convert_with_llm_ollama(self, text: str, from_format: str, to_format: str) -> str:
        """使用 Ollama LLM 进行复杂格式转换"""
        prompt = f"""请将以下 {from_format} 格式的内容转换为 {to_format} 格式：

输入（{from_format}）：
{text}

请直接输出转换后的 {to_format} 格式内容，不要添加任何解释。"""

        response = await self._ollama_client.generate(
            model=settings.ollama_model, prompt=prompt, options={"temperature": 0.3, "num_predict": 2048}
        )

        return response["response"].strip()
