#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

# MacCortex SearchPattern - 搜索模式
# Phase 1 - Week 2 Day 9
# 创建时间: 2026-01-20
# 更新时间: 2026-01-21 (Phase 1.5 - Day 3: 集成 PromptGuard)
#
# Phase 1.5: 增强安全防护（Prompt Injection 检测、指令隔离、输出清理）
#
# Web 搜索 + 语义搜索（本地知识库查询）

import asyncio
import hashlib
import time
from typing import Any, Dict, List, Optional
from loguru import logger

from .base import BasePattern
from utils.config import settings


class SearchPattern(BasePattern):
    """
    搜索 Pattern

    支持多种搜索方式：
    - Web 搜索（Google、DuckDuckGo、Bing）
    - 语义搜索（本地向量数据库）
    - 混合搜索（Web + 本地）
    - 结果排序与过滤
    """

    def __init__(self):
        super().__init__()  # Phase 1.5: 初始化安全模块
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._ollama_client = None
        self._vector_db = None  # ChromaDB 客户端
        self._mode = "uninitialized"  # uninitialized | mlx | ollama | mock

        # 缓存机制（Phase 2 Week 4 Day 17）
        self._search_cache: Dict[str, tuple[List[Dict[str, Any]], float]] = {}
        self._cache_ttl = 300  # 5 分钟 TTL

    # MARK: - BasePattern Protocol

    @property
    def pattern_id(self) -> str:
        return "search"

    @property
    def name(self) -> str:
        return "Search"

    @property
    def description(self) -> str:
        return "Web 搜索 + 语义搜索（本地知识库查询）"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def initialize(self):
        """初始化模型与搜索客户端"""
        logger.info(f"🔧 初始化 {self.name} Pattern...")

        # 初始化 LLM（用于查询重写与结果总结）
        try:
            await self._initialize_mlx()
        except Exception as e:
            logger.warning(f"MLX 初始化失败，回退到 Ollama: {e}")
            try:
                await self._initialize_ollama()
            except Exception as e2:
                logger.warning(f"Ollama 初始化失败，使用 Mock 模式: {e2}")
                logger.info("  ⚠️  使用 Mock 模式（用于测试）")

        # 初始化向量数据库（用于语义搜索）
        try:
            await self._initialize_vector_db()
        except Exception as e:
            logger.warning(f"向量数据库初始化失败: {e}")

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

    async def _initialize_vector_db(self):
        """初始化向量数据库（ChromaDB）"""
        try:
            import chromadb

            logger.info("  🗄️  连接 ChromaDB...")
            self._vector_db = chromadb.Client()
            logger.info("  ✅ ChromaDB 连接成功")
        except ImportError:
            logger.warning("ChromaDB 未安装，语义搜索功能不可用")
        except Exception as e:
            logger.warning(f"ChromaDB 初始化失败: {e}")

    async def cleanup(self):
        """清理资源"""
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._ollama_client = None
        self._vector_db = None
        logger.info(f"✅ {self.name} Pattern 清理完成")

    async def execute(self, text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行搜索

        Args:
            text: 搜索查询
            parameters: 搜索参数
                - search_type: 搜索类型 ("web" | "semantic" | "hybrid", 默认 "web")
                - engine: 搜索引擎 ("google" | "duckduckgo" | "bing", 默认 "duckduckgo")
                - num_results: 返回结果数量 (默认: 5)
                - summarize: 是否总结搜索结果 (默认: true)
                - language: 搜索语言 (默认: "zh-CN")
                - collection: 语义搜索的集合名称 (默认: "default")

        Returns:
            搜索结果字典
        """
        # 解析参数
        search_type = parameters.get("search_type", "web")
        engine = parameters.get("engine", "duckduckgo")
        num_results = parameters.get("num_results", 5)
        summarize = parameters.get("summarize", True)
        language = parameters.get("language", "zh-CN")
        collection = parameters.get("collection", "default")

        # 执行搜索
        if search_type == "web":
            results = await self._web_search(text, engine, num_results, language)
        elif search_type == "semantic":
            results = await self._semantic_search(text, collection, num_results)
        elif search_type == "hybrid":
            web_results = await self._web_search(text, engine, num_results // 2, language)
            semantic_results = await self._semantic_search(text, collection, num_results // 2)
            results = web_results + semantic_results
        else:
            raise ValueError(f"不支持的搜索类型: {search_type}")

        # 总结搜索结果（如果需要）
        summary = None
        if summarize and results:
            summary = await self._summarize_results(text, results)

        # 序列化搜索结果为 JSON 字符串（统一输出格式）
        search_result = {
            "results": results[:num_results],
            "summary": summary,
        }

        import json
        output = json.dumps(search_result, ensure_ascii=False, indent=2)

        return {
            "output": output,  # 统一输出格式
            "metadata": {
                "search_type": search_type,
                "engine": engine,
                "num_results": num_results,
                "query": text,
                "total_found": len(results),
                "mode": self._mode,
            },
        }

    async def _web_search(self, query: str, engine: str, num_results: int, language: str) -> List[Dict[str, Any]]:
        """Web 搜索"""
        if engine == "duckduckgo":
            return await self._search_duckduckgo(query, num_results, language)
        elif engine == "google":
            return await self._search_google(query, num_results, language)
        elif engine == "bing":
            return await self._search_bing(query, num_results, language)
        else:
            raise ValueError(f"不支持的搜索引擎: {engine}")

    async def _search_duckduckgo(self, query: str, num_results: int, language: str) -> List[Dict[str, Any]]:
        """
        DuckDuckGo 搜索（Phase 2 Week 4 Day 17 优化）

        改进：
        1. 5 分钟缓存（减少 API 调用）
        2. 更好的错误处理（超时、速率限制）
        3. 语言映射扩展（支持更多语言）
        4. 日志记录优化
        """
        # 1. 检查缓存
        cache_key = self._generate_cache_key(query, num_results, language)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"🚀 使用缓存结果: {query} ({len(cached_result)} 条)")
            return cached_result

        # 2. 执行搜索
        try:
            from duckduckgo_search import DDGS

            # 语言/区域映射（Phase 2 Week 4 Day 17 扩展）
            region_map = {
                "zh-CN": "cn-zh",  # 中国简体
                "zh": "cn-zh",
                "en-US": "us-en",  # 美国英文
                "en": "us-en",
                "ja-JP": "jp-jp",  # 日本
                "ja": "jp-jp",
                "ko-KR": "kr-kr",  # 韩国
                "ko": "kr-kr",
                "auto": "wt-wt",    # 全球（无地区限制）
            }
            region = region_map.get(language, "wt-wt")

            logger.info(f"🔍 DuckDuckGo 搜索: '{query}' (region={region}, num={num_results})")

            # 执行搜索（同步方法，需要在线程池中运行以避免阻塞）
            loop = asyncio.get_event_loop()
            results = []

            def _sync_search():
                """同步搜索函数（在线程池中运行）"""
                nonlocal results
                try:
                    with DDGS() as ddgs:
                        search_results = ddgs.text(
                            keywords=query,
                            region=region,
                            max_results=num_results * 2,  # 多获取一些以防过滤后不够
                        )
                        for i, result in enumerate(search_results):
                            # 过滤无效结果
                            if not result.get("title") or not result.get("href"):
                                continue

                            results.append(
                                {
                                    "title": result.get("title", ""),
                                    "url": result.get("href", ""),
                                    "snippet": result.get("body", ""),
                                    "source": "duckduckgo",
                                    "rank": i + 1,
                                }
                            )

                            # 限制结果数量
                            if len(results) >= num_results:
                                break
                except Exception as e:
                    logger.error(f"DuckDuckGo 搜索内部错误: {e}")
                    raise

            # 在线程池中执行（避免阻塞事件循环）
            await loop.run_in_executor(None, _sync_search)

            if not results:
                logger.warning(f"DuckDuckGo 搜索无结果: '{query}'")
                return []

            logger.info(f"✅ DuckDuckGo 搜索成功: {len(results)} 条结果")

            # 3. 缓存结果
            self._save_to_cache(cache_key, results)

            return results

        except ImportError:
            logger.error("duckduckgo_search 未安装（但已在 requirements.txt 中）")
            logger.info("  ⚠️  回退到 Mock 搜索")
            return await self._mock_web_search(query, num_results)
        except Exception as e:
            logger.error(f"DuckDuckGo 搜索失败: {type(e).__name__}: {e}")
            logger.info("  ⚠️  回退到 Mock 搜索")
            return await self._mock_web_search(query, num_results)

    async def _search_google(self, query: str, num_results: int, language: str) -> List[Dict[str, Any]]:
        """Google 搜索（需要 API Key）"""
        # TODO: 实现 Google Custom Search API
        logger.warning("Google 搜索暂未实现，使用 Mock 搜索")
        return await self._mock_web_search(query, num_results)

    async def _search_bing(self, query: str, num_results: int, language: str) -> List[Dict[str, Any]]:
        """Bing 搜索（需要 API Key）"""
        # TODO: 实现 Bing Search API
        logger.warning("Bing 搜索暂未实现，使用 Mock 搜索")
        return await self._mock_web_search(query, num_results)

    async def _mock_web_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Mock Web 搜索（用于测试）"""
        await asyncio.sleep(0.1)

        return [
            {
                "title": f"MacCortex 搜索结果 {i + 1}",
                "url": f"https://example.com/result{i + 1}",
                "snippet": f"这是关于 '{query}' 的搜索结果 {i + 1}。MacCortex 是下一代 macOS 个人智能基础设施。",
                "source": "mock",
                "rank": i + 1,
            }
            for i in range(num_results)
        ]

    async def _semantic_search(self, query: str, collection: str, num_results: int) -> List[Dict[str, Any]]:
        """语义搜索（向量数据库）"""
        if not self._vector_db:
            logger.warning("ChromaDB 未初始化，使用 Mock 语义搜索")
            return await self._mock_semantic_search(query, num_results)

        try:
            # 获取集合
            col = self._vector_db.get_or_create_collection(name=collection)

            # 查询
            results = col.query(query_texts=[query], n_results=num_results)

            # 格式化结果
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(
                    zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
                ):
                    formatted_results.append(
                        {
                            "title": metadata.get("title", f"文档 {i + 1}"),
                            "content": doc,
                            "metadata": metadata,
                            "similarity": 1.0 - distance,  # 转换为相似度
                            "source": "chromadb",
                            "rank": i + 1,
                        }
                    )

            return formatted_results
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return await self._mock_semantic_search(query, num_results)

    async def _mock_semantic_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Mock 语义搜索（用于测试）"""
        await asyncio.sleep(0.1)

        return [
            {
                "title": f"本地文档 {i + 1}",
                "content": f"这是关于 '{query}' 的本地文档 {i + 1}。包含相关信息和上下文。",
                "metadata": {"source": "mock", "created_at": "2026-01-20"},
                "similarity": 0.9 - (i * 0.1),
                "source": "mock_vector_db",
                "rank": i + 1,
            }
            for i in range(num_results)
        ]

    async def _summarize_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """总结搜索结果"""
        if not results:
            return "未找到相关结果。"

        # 构建总结提示词
        results_text = "\n\n".join(
            [f"结果 {i + 1}: {r.get('title', '')}\n{r.get('snippet', '') or r.get('content', '')}" for i, r in enumerate(results[:5])]
        )

        prompt = f"""根据以下搜索结果，简要回答用户的问题：

用户问题：{query}

搜索结果：
{results_text}

请用 2-3 句话总结最相关的信息。"""

        # 使用 LLM 生成总结
        if self._mode == "mlx":
            from mlx_lm import generate

            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                generate,
                self._mlx_model,
                self._mlx_tokenizer,
                prompt,
                256,  # max_tokens
            )
            return summary.strip()
        elif self._mode == "ollama":
            response = await self._ollama_client.generate(
                model=settings.ollama_model, prompt=prompt, options={"temperature": 0.7, "num_predict": 256}
            )
            return response["response"].strip()
        else:
            # Mock 总结
            return f"根据搜索结果，关于 '{query}' 的主要信息如下：{results[0].get('title', '')}。详见搜索结果。"

    # MARK: - 缓存辅助方法（Phase 2 Week 4 Day 17）

    def _generate_cache_key(self, query: str, num_results: int, language: str) -> str:
        """生成缓存键（基于查询参数的哈希）"""
        key_string = f"{query}|{num_results}|{language}"
        return hashlib.md5(key_string.encode("utf-8")).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """从缓存获取结果（检查 TTL）"""
        if cache_key not in self._search_cache:
            return None

        cached_results, cached_time = self._search_cache[cache_key]

        # 检查是否过期（5 分钟 TTL）
        if time.time() - cached_time > self._cache_ttl:
            # 过期，删除缓存
            del self._search_cache[cache_key]
            return None

        return cached_results

    def _save_to_cache(self, cache_key: str, results: List[Dict[str, Any]]):
        """保存结果到缓存"""
        self._search_cache[cache_key] = (results, time.time())

        # 清理过期缓存（限制缓存大小）
        if len(self._search_cache) > 100:
            self._cleanup_expired_cache()

    def _cleanup_expired_cache(self):
        """清理过期缓存条目"""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, cached_time) in self._search_cache.items()
            if current_time - cached_time > self._cache_ttl
        ]

        for key in expired_keys:
            del self._search_cache[key]

        logger.debug(f"🧹 清理过期缓存: 删除 {len(expired_keys)} 条，剩余 {len(self._search_cache)} 条")
