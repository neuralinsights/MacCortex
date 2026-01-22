"""
MacCortex Researcher Agent

调研与搜索节点，负责：
1. 网络搜索（DuckDuckGo）
2. 文档检索（本地向量库）
3. API 调用（GitHub、天气等）
4. LLM 总结与结构化输出
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import SwarmState


class ResearcherNode:
    """
    调研与搜索节点

    负责处理需要外部信息的子任务，支持：
    - 网络搜索（DuckDuckGo）
    - 文档检索（本地向量库）
    - API 调用（GitHub、天气等）
    - LLM 总结与结构化输出
    """

    def __init__(
        self,
        workspace_path: Path,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.2,
        max_search_results: int = 5,
        api_keys: Optional[Dict[str, str]] = None,
        llm: Optional[Any] = None,  # 可选的 LLM 实例（用于测试）
        search: Optional[Any] = None,  # 可选的搜索工具（用于测试）
        fallback_to_local: bool = True
    ):
        """
        初始化 Researcher 节点

        Args:
            workspace_path: 工作空间路径
            model: LLM 模型名称
            temperature: LLM 温度（0.2 适合调研任务）
            max_search_results: 最大搜索结果数量
            api_keys: 外部 API 密钥字典（如 GitHub、OpenWeather）
            llm: 可选的 LLM 实例（用于测试时注入 mock）
            search: 可选的搜索工具（用于测试时注入 mock）
            fallback_to_local: 当 API Key 缺失时是否降级到本地模型
        """
        # 使用提供的 LLM 或创建新的
        if llm is not None:
            self.llm = llm
            self.using_local_model = False
        else:
            # Anthropic API Key
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                if fallback_to_local:
                    from langchain_community.chat_models import ChatOllama
                    print("⚠️  ResearcherNode: 降级使用本地 Ollama 模型（qwen3:14b）")
                    self.llm = ChatOllama(
                        model=os.getenv("OLLAMA_MODEL", "qwen3:14b"),
                        temperature=temperature,
                        base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
                    )
                    self.using_local_model = True
                else:
                    raise ValueError("ANTHROPIC_API_KEY 环境变量未设置")
            else:
                self.llm = ChatAnthropic(
                    model=model,
                    temperature=temperature,
                    anthropic_api_key=api_key
            )

        self.workspace = Path(workspace_path)
        self.max_search_results = max_search_results
        self.api_keys = api_keys or {}

        # DuckDuckGo 搜索工具
        self.search = search if search is not None else DuckDuckGoSearchRun()

        # 系统提示词
        self.system_prompt = """你是一个专业的研究助手，负责调研和信息收集。

你的任务是：
1. 基于用户的调研需求，分析搜索结果
2. 提取关键信息，过滤无关内容
3. 生成结构化的总结（Markdown 格式）
4. 确保信息准确、客观、来源可靠

输出格式要求：
- 使用 Markdown 格式
- 重要信息使用列表或表格
- 引用来源链接（如果有）
- 简洁明了，突出重点"""

    async def research(self, state: SwarmState) -> SwarmState:
        """
        执行调研任务

        Args:
            state: 当前 Swarm 状态

        Returns:
            更新后的 Swarm 状态
        """
        plan = state.get("plan") or {}
        subtasks = plan.get("subtasks", []) if plan else []
        current_index = state.get("current_subtask_index", 0)

        # 检查是否有有效的子任务
        if not subtasks or current_index >= len(subtasks):
            state["status"] = "completed"
            return state

        subtask = subtasks[current_index]

        # 检查是否是调研任务
        if subtask.get("type") != "research":
            # 跳过非调研任务
            state["current_subtask_index"] += 1
            state["status"] = "planning"  # 返回 Planner 路由
            return state

        try:
            # 1. 执行调研
            research_result = await self._perform_research(
                query=subtask.get("description", ""),
                search_type=subtask.get("search_type", "web"),  # web, api, local
                api_name=subtask.get("api_name"),
                api_params=subtask.get("api_params", {})
            )

            # 2. 检查结果是否包含错误信息
            is_error = (
                isinstance(research_result, str) and
                ("搜索失败" in research_result or "错误" in research_result)
            )

            # 3. 保存结果
            state["subtask_results"].append({
                "subtask_id": subtask["id"],
                "subtask_description": subtask["description"],
                "research_result": research_result if not is_error else None,
                "passed": not is_error,
                "error_message": research_result if is_error else None,
                "completed_at": datetime.utcnow().isoformat()
            })

            # 3. 更新状态
            state["current_subtask_index"] += 1

            # 检查是否完成所有子任务
            if state["current_subtask_index"] >= len(subtasks):
                state["status"] = "completed"
            else:
                state["status"] = "planning"  # 返回 Planner 继续下一个任务

        except Exception as e:
            # 调研失败
            state["subtask_results"].append({
                "subtask_id": subtask["id"],
                "subtask_description": subtask["description"],
                "passed": False,
                "error_message": f"调研失败：{str(e)}",
                "completed_at": datetime.utcnow().isoformat()
            })

            # 继续下一个任务（调研失败不阻塞流程）
            state["current_subtask_index"] += 1
            if state["current_subtask_index"] >= len(subtasks):
                state["status"] = "completed"
            else:
                state["status"] = "planning"

        return state

    async def _perform_research(
        self,
        query: str,
        search_type: str = "web",
        api_name: Optional[str] = None,
        api_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        执行实际的调研操作

        Args:
            query: 调研问题
            search_type: 搜索类型（web, api, local）
            api_name: API 名称（如果 search_type=api）
            api_params: API 参数

        Returns:
            结构化的调研结果（Markdown 格式）
        """
        if search_type == "web":
            return await self._web_search(query)
        elif search_type == "api":
            return await self._api_call(api_name, api_params or {})
        elif search_type == "local":
            return await self._local_search(query)
        else:
            raise ValueError(f"不支持的搜索类型：{search_type}")

    async def _web_search(self, query: str) -> str:
        """
        网络搜索（DuckDuckGo）

        Args:
            query: 搜索关键词

        Returns:
            LLM 总结后的结构化结果
        """
        # 1. 执行搜索
        try:
            search_results = await asyncio.to_thread(self.search.run, query)
        except Exception as e:
            return f"搜索失败：{str(e)}"

        # 2. 使用 LLM 总结
        summary = await self._summarize_with_llm(
            query=query,
            content=search_results
        )

        return summary

    async def _api_call(self, api_name: Optional[str], params: Dict[str, Any]) -> str:
        """
        外部 API 调用

        Args:
            api_name: API 名称（如 github, weather）
            params: API 参数

        Returns:
            API 响应的结构化总结
        """
        if not api_name:
            return "错误：未指定 API 名称"

        if api_name == "github":
            return await self._call_github_api(params)
        elif api_name == "weather":
            return await self._call_weather_api(params)
        else:
            return f"不支持的 API：{api_name}"

    async def _call_github_api(self, params: Dict[str, Any]) -> str:
        """
        调用 GitHub API

        Args:
            params: 参数（如 repo, user）

        Returns:
            GitHub 数据总结
        """
        # 简化实现：返回模拟数据
        # 实际应使用 PyGithub 或 requests
        repo = params.get("repo", "unknown/repo")
        return f"""# GitHub 仓库信息

**仓库**: {repo}
**状态**: 活跃
**Stars**: 1234
**Forks**: 567
**主要语言**: Python

（注：这是模拟数据，实际实现需要真实 API 调用）"""

    async def _call_weather_api(self, params: Dict[str, Any]) -> str:
        """
        调用天气 API

        Args:
            params: 参数（如 city）

        Returns:
            天气信息总结
        """
        # 简化实现：返回模拟数据
        city = params.get("city", "Unknown")
        return f"""# {city} 天气信息

**温度**: 22°C
**天气**: 晴朗
**湿度**: 60%
**风速**: 5 m/s

（注：这是模拟数据，实际实现需要真实 API 调用）"""

    async def _local_search(self, query: str) -> str:
        """
        本地文档检索（向量数据库）

        Args:
            query: 查询关键词

        Returns:
            检索结果总结
        """
        # 简化实现：返回占位符
        # 实际应集成 ChromaDB 或其他向量数据库
        return f"""# 本地文档检索结果

**查询**: {query}
**结果**: 未找到相关文档

（注：本地检索功能待实现，需集成向量数据库）"""

    async def _summarize_with_llm(self, query: str, content: str) -> str:
        """
        使用 LLM 总结内容

        Args:
            query: 原始问题
            content: 搜索结果或原始内容

        Returns:
            结构化的 Markdown 总结
        """
        user_prompt = f"""根据以下搜索结果，回答问题：{query}

搜索结果：
{content}

请提供结构化的回答（Markdown 格式），包括：
1. 核心观点（3-5 条）
2. 重要细节
3. 来源链接（如果有）"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt)
            ])

            return response.content

        except Exception as e:
            return f"LLM 总结失败：{str(e)}\n\n原始内容：\n{content[:500]}..."


def create_researcher_node(
    workspace_path: Path,
    **kwargs
) -> callable:
    """
    创建 Researcher 节点（用于 LangGraph）

    Args:
        workspace_path: 工作空间路径
        **kwargs: 传递给 ResearcherNode 的参数

    Returns:
        Researcher 节点函数
    """
    researcher = ResearcherNode(workspace_path, **kwargs)

    async def researcher_node(state: SwarmState) -> SwarmState:
        """Researcher 节点函数"""
        return await researcher.research(state)

    return researcher_node


# 用于测试的简化函数
async def test_researcher():
    """测试 Researcher 节点"""
    from ..state import create_initial_state

    # 创建 Researcher
    workspace = Path("/tmp/test_researcher")
    workspace.mkdir(exist_ok=True)

    researcher = ResearcherNode(workspace)

    # 测试 1: 网络搜索
    state1 = create_initial_state("测试调研任务")
    state1["plan"] = {
        "task": "测试调研任务",
        "subtasks": [
            {
                "id": 1,
                "type": "research",
                "description": "Python 异步编程最佳实践",
                "search_type": "web"
            }
        ]
    }
    state1["current_subtask_index"] = 0

    result_state = await researcher.research(state1)
    print("=== 测试 1: 网络搜索 ===")
    print(f"状态: {result_state['status']}")
    print(f"结果数量: {len(result_state['subtask_results'])}")
    if result_state["subtask_results"]:
        print(f"通过: {result_state['subtask_results'][0]['passed']}")
        print(f"结果: {result_state['subtask_results'][0]['research_result'][:200]}...")

    # 测试 2: API 调用（GitHub）
    state2 = create_initial_state("测试 API 调用")
    state2["plan"] = {
        "task": "测试 API 调用",
        "subtasks": [
            {
                "id": 1,
                "type": "research",
                "description": "查询 GitHub 仓库信息",
                "search_type": "api",
                "api_name": "github",
                "api_params": {"repo": "langchain-ai/langgraph"}
            }
        ]
    }
    state2["current_subtask_index"] = 0

    result_state = await researcher.research(state2)
    print("\n=== 测试 2: API 调用 ===")
    print(f"状态: {result_state['status']}")
    print(f"结果数量: {len(result_state['subtask_results'])}")
    if result_state["subtask_results"]:
        print(f"通过: {result_state['subtask_results'][0]['passed']}")
        print(f"结果:\n{result_state['subtask_results'][0]['research_result']}")

    print("\n✅ Researcher 节点测试完成！")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加父目录到 sys.path 以支持相对导入
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    asyncio.run(test_researcher())
