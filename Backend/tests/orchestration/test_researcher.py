"""
MacCortex Researcher 测试

测试 Researcher 节点功能，包括：
- 网络搜索（DuckDuckGo）
- API 调用（GitHub、天气）
- 本地文档检索
- LLM 总结
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestration.nodes.researcher import (
    ResearcherNode,
    create_researcher_node
)
from src.orchestration.state import create_initial_state


class TestResearcherNode:
    """测试 ResearcherNode 基础功能"""

    def test_init_default_parameters(self, tmp_path, monkeypatch):
        """测试默认参数初始化"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        assert researcher.workspace == tmp_path
        assert researcher.max_search_results == 5
        assert researcher.api_keys == {}
        assert researcher.search is not None
        assert researcher.llm is not None

    def test_init_custom_parameters(self, tmp_path, monkeypatch):
        """测试自定义参数初始化"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        api_keys = {"github": "test_key", "weather": "test_key"}
        researcher = ResearcherNode(
            workspace_path=tmp_path,
            temperature=0.5,
            max_search_results=10,
            api_keys=api_keys
        )

        assert researcher.max_search_results == 10
        assert researcher.api_keys == api_keys

    def test_system_prompt_structure(self, tmp_path, monkeypatch):
        """测试系统提示词结构"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        assert "研究助手" in researcher.system_prompt
        assert "Markdown" in researcher.system_prompt
        assert "结构化" in researcher.system_prompt


@pytest.mark.asyncio
class TestResearchWorkflow:
    """测试调研工作流程"""

    async def test_research_web_search_task(self, tmp_path, monkeypatch):
        """测试处理网络搜索任务"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        # 创建 mock LLM
        mock_llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "# 测试总结\n\n这是一个测试总结"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        # 创建 mock search
        mock_search = Mock()
        mock_search.run = Mock(return_value="测试搜索结果")

        # 注入 mock LLM 和 search
        researcher = ResearcherNode(tmp_path, llm=mock_llm, search=mock_search)

        # 创建测试状态
        state = create_initial_state("测试调研任务")
        state["plan"] = {
            "task": "测试调研任务",
            "subtasks": [
                {
                    "id": 1,
                    "type": "research",
                    "description": "Python 异步编程",
                    "search_type": "web"
                }
            ]
        }
        state["current_subtask_index"] = 0

        result_state = await researcher.research(state)

        # 验证状态更新
        assert result_state["status"] == "completed"
        assert result_state["current_subtask_index"] == 1
        assert len(result_state["subtask_results"]) == 1

        # 验证结果
        result = result_state["subtask_results"][0]
        assert result["subtask_id"] == 1
        assert result["passed"] is True
        assert "测试总结" in result["research_result"]

    async def test_research_skip_non_research_task(self, tmp_path, monkeypatch):
        """测试跳过非调研任务"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        # 创建测试状态（非 research 类型）
        state = create_initial_state("测试任务")
        state["plan"] = {
            "task": "测试任务",
            "subtasks": [
                {
                    "id": 1,
                    "type": "code",  # 非 research 类型
                    "description": "编写代码"
                }
            ]
        }
        state["current_subtask_index"] = 0

        result_state = await researcher.research(state)

        # 应该跳过并更新索引
        assert result_state["status"] == "planning"
        assert result_state["current_subtask_index"] == 1
        assert len(result_state["subtask_results"]) == 0

    async def test_research_api_call_task(self, tmp_path, monkeypatch):
        """测试 API 调用任务"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        # 创建测试状态
        state = create_initial_state("测试 API 调用")
        state["plan"] = {
            "task": "测试 API 调用",
            "subtasks": [
                {
                    "id": 1,
                    "type": "research",
                    "description": "查询 GitHub 仓库",
                    "search_type": "api",
                    "api_name": "github",
                    "api_params": {"repo": "test/repo"}
                }
            ]
        }
        state["current_subtask_index"] = 0

        result_state = await researcher.research(state)

        # 验证结果
        assert result_state["status"] == "completed"
        assert len(result_state["subtask_results"]) == 1
        result = result_state["subtask_results"][0]
        assert result["passed"] is True
        assert "GitHub" in result["research_result"]

    async def test_research_local_search_task(self, tmp_path, monkeypatch):
        """测试本地检索任务"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        # 创建测试状态
        state = create_initial_state("测试本地检索")
        state["plan"] = {
            "task": "测试本地检索",
            "subtasks": [
                {
                    "id": 1,
                    "type": "research",
                    "description": "搜索本地文档",
                    "search_type": "local"
                }
            ]
        }
        state["current_subtask_index"] = 0

        result_state = await researcher.research(state)

        # 验证结果
        assert result_state["status"] == "completed"
        assert len(result_state["subtask_results"]) == 1
        result = result_state["subtask_results"][0]
        assert result["passed"] is True
        assert "本地文档检索结果" in result["research_result"]

    async def test_research_handles_search_failure(self, tmp_path, monkeypatch):
        """测试处理搜索失败"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        # 创建 mock LLM（不会被调用，因为搜索会失败）
        mock_llm = AsyncMock()

        # 创建 mock search，模拟失败
        mock_search = Mock()
        mock_search.run = Mock(side_effect=Exception("网络错误"))

        researcher = ResearcherNode(tmp_path, llm=mock_llm, search=mock_search)

        # 创建测试状态
        state = create_initial_state("测试搜索失败")
        state["plan"] = {
            "task": "测试搜索失败",
            "subtasks": [
                {
                    "id": 1,
                    "type": "research",
                    "description": "测试查询",
                    "search_type": "web"
                }
            ]
        }
        state["current_subtask_index"] = 0

        result_state = await researcher.research(state)

        # 应该记录失败但不阻塞流程
        assert result_state["status"] == "completed"
        assert len(result_state["subtask_results"]) == 1
        result = result_state["subtask_results"][0]
        assert result["passed"] is False
        assert "搜索失败" in result["error_message"] or "网络错误" in result["error_message"]


@pytest.mark.asyncio
class TestWebSearch:
    """测试网络搜索功能"""

    async def test_web_search_success(self, tmp_path, monkeypatch):
        """测试网络搜索成功"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        # 创建 mock LLM
        mock_llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "总结内容"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        # 创建 mock search
        mock_search = Mock()
        mock_search.run = Mock(return_value="搜索结果内容")

        researcher = ResearcherNode(tmp_path, llm=mock_llm, search=mock_search)

        result = await researcher._web_search("测试查询")

        assert result == "总结内容"
        researcher.search.run.assert_called_once()
        mock_llm.ainvoke.assert_called_once()

    async def test_web_search_handles_exception(self, tmp_path, monkeypatch):
        """测试网络搜索异常处理"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        # 创建 mock LLM（不会被调用）
        mock_llm = AsyncMock()

        # 创建 mock search，模拟失败
        mock_search = Mock()
        mock_search.run = Mock(side_effect=Exception("连接超时"))

        researcher = ResearcherNode(tmp_path, llm=mock_llm, search=mock_search)

        result = await researcher._web_search("测试查询")

        assert "搜索失败" in result
        assert "连接超时" in result


@pytest.mark.asyncio
class TestAPICall:
    """测试 API 调用功能"""

    async def test_api_call_github(self, tmp_path, monkeypatch):
        """测试 GitHub API 调用"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        result = await researcher._api_call("github", {"repo": "owner/repo"})

        assert "GitHub 仓库信息" in result
        assert "owner/repo" in result
        assert "Stars" in result

    async def test_api_call_weather(self, tmp_path, monkeypatch):
        """测试天气 API 调用"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        result = await researcher._api_call("weather", {"city": "北京"})

        assert "北京 天气信息" in result
        assert "温度" in result

    async def test_api_call_unknown_api(self, tmp_path, monkeypatch):
        """测试未知 API"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        result = await researcher._api_call("unknown_api", {})

        assert "不支持的 API" in result

    async def test_api_call_missing_api_name(self, tmp_path, monkeypatch):
        """测试缺少 API 名称"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        result = await researcher._api_call(None, {})

        assert "错误" in result
        assert "未指定 API 名称" in result


@pytest.mark.asyncio
class TestLocalSearch:
    """测试本地检索功能"""

    async def test_local_search(self, tmp_path, monkeypatch):
        """测试本地文档检索"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        result = await researcher._local_search("测试查询")

        assert "本地文档检索结果" in result
        assert "测试查询" in result


@pytest.mark.asyncio
class TestLLMSummarization:
    """测试 LLM 总结功能"""

    async def test_summarize_with_llm_success(self, tmp_path, monkeypatch):
        """测试 LLM 总结成功"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        # 创建 mock LLM
        mock_llm = AsyncMock()
        mock_response = Mock()
        mock_response.content = "# 总结标题\n\n总结内容"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        researcher = ResearcherNode(tmp_path, llm=mock_llm)

        result = await researcher._summarize_with_llm(
            query="测试问题",
            content="测试内容"
        )

        assert result == "# 总结标题\n\n总结内容"
        mock_llm.ainvoke.assert_called_once()

    async def test_summarize_with_llm_failure(self, tmp_path, monkeypatch):
        """测试 LLM 总结失败"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        # 创建 mock LLM，模拟异常
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API 错误"))

        researcher = ResearcherNode(tmp_path, llm=mock_llm)

        result = await researcher._summarize_with_llm(
            query="测试问题",
            content="测试内容很长" * 1000
        )

        assert "LLM 总结失败" in result
        assert "原始内容" in result


@pytest.mark.asyncio
class TestPerformResearch:
    """测试 _perform_research 路由逻辑"""

    async def test_perform_research_web(self, tmp_path, monkeypatch):
        """测试 web 搜索路由"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        with patch.object(researcher, '_web_search', new_callable=AsyncMock, return_value="web 结果"):
            result = await researcher._perform_research(
                query="测试",
                search_type="web"
            )

            assert result == "web 结果"
            researcher._web_search.assert_called_once_with("测试")

    async def test_perform_research_api(self, tmp_path, monkeypatch):
        """测试 api 调用路由"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        with patch.object(researcher, '_api_call', new_callable=AsyncMock, return_value="api 结果"):
            result = await researcher._perform_research(
                query="测试",
                search_type="api",
                api_name="github",
                api_params={"repo": "test/repo"}
            )

            assert result == "api 结果"
            researcher._api_call.assert_called_once_with("github", {"repo": "test/repo"})

    async def test_perform_research_local(self, tmp_path, monkeypatch):
        """测试 local 搜索路由"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        with patch.object(researcher, '_local_search', new_callable=AsyncMock, return_value="local 结果"):
            result = await researcher._perform_research(
                query="测试",
                search_type="local"
            )

            assert result == "local 结果"
            researcher._local_search.assert_called_once_with("测试")

    async def test_perform_research_invalid_type(self, tmp_path, monkeypatch):
        """测试无效搜索类型"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        with pytest.raises(ValueError, match="不支持的搜索类型"):
            await researcher._perform_research(
                query="测试",
                search_type="invalid_type"
            )


class TestCreateResearcherNode:
    """测试 create_researcher_node 工厂函数"""

    def test_create_researcher_node_default(self, tmp_path, monkeypatch):
        """测试创建默认 Researcher 节点"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        node = create_researcher_node(tmp_path)

        assert callable(node)

    def test_create_researcher_node_custom(self, tmp_path, monkeypatch):
        """测试创建自定义 Researcher 节点"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        node = create_researcher_node(
            tmp_path,
            temperature=0.5,
            max_search_results=10
        )

        assert callable(node)


@pytest.mark.asyncio
class TestMultipleSubtasks:
    """测试多子任务场景"""

    async def test_multiple_research_tasks(self, tmp_path, monkeypatch):
        """测试多个调研任务"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        # 创建包含 3 个调研任务的状态
        state = create_initial_state("多任务测试")
        state["plan"] = {
            "task": "多任务测试",
            "subtasks": [
                {
                    "id": 1,
                    "type": "research",
                    "description": "任务1",
                    "search_type": "api",
                    "api_name": "github",
                    "api_params": {"repo": "test/repo"}
                },
                {
                    "id": 2,
                    "type": "research",
                    "description": "任务2",
                    "search_type": "local"
                },
                {
                    "id": 3,
                    "type": "research",
                    "description": "任务3",
                    "search_type": "api",
                    "api_name": "weather",
                    "api_params": {"city": "北京"}
                }
            ]
        }
        state["current_subtask_index"] = 0

        # 执行第一个任务
        result_state = await researcher.research(state)
        assert result_state["current_subtask_index"] == 1
        assert result_state["status"] == "planning"
        assert len(result_state["subtask_results"]) == 1

        # 执行第二个任务
        result_state = await researcher.research(result_state)
        assert result_state["current_subtask_index"] == 2
        assert result_state["status"] == "planning"
        assert len(result_state["subtask_results"]) == 2

        # 执行第三个任务
        result_state = await researcher.research(result_state)
        assert result_state["current_subtask_index"] == 3
        assert result_state["status"] == "completed"
        assert len(result_state["subtask_results"]) == 3


@pytest.mark.asyncio
class TestEdgeCases:
    """测试边界情况"""

    async def test_empty_subtasks(self, tmp_path, monkeypatch):
        """测试空子任务列表"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        state = create_initial_state("空任务")
        state["plan"] = {"task": "空任务", "subtasks": []}
        state["current_subtask_index"] = 0

        result_state = await researcher.research(state)

        assert result_state["status"] == "completed"
        assert len(result_state["subtask_results"]) == 0

    async def test_index_out_of_bounds(self, tmp_path, monkeypatch):
        """测试索引越界"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        state = create_initial_state("越界测试")
        state["plan"] = {
            "task": "越界测试",
            "subtasks": [
                {"id": 1, "type": "research", "description": "任务1", "search_type": "local"}
            ]
        }
        state["current_subtask_index"] = 999  # 越界索引

        result_state = await researcher.research(state)

        assert result_state["status"] == "completed"

    async def test_missing_plan(self, tmp_path, monkeypatch):
        """测试缺少 plan 字段"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
        researcher = ResearcherNode(tmp_path)

        state = create_initial_state("缺少 plan")
        # 不设置 plan 字段

        result_state = await researcher.research(state)

        assert result_state["status"] == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
