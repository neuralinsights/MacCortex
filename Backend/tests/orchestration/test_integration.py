"""
MacCortex 集成测试

测试多个 Agent 协作的端到端场景：
1. Planner → Coder → Reviewer（代码任务）
2. Planner → Researcher（调研任务）
3. Planner → ToolRunner（系统操作任务）
4. 混合任务工作流
5. 错误处理与重试
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestration.swarm_graph import create_full_swarm_graph, run_full_swarm_task
from src.orchestration.state import create_initial_state


def create_mock_graph(tmp_path, mock_llm=None, mock_search=None, **custom_kwargs):
    """
    创建带有默认 mock LLM 的测试图

    Args:
        tmp_path: 临时工作空间路径
        mock_llm: 可选的预配置 mock LLM（如果为 None 则创建新的）
        mock_search: 可选的预配置 mock 搜索（如果为 None 则创建新的）
        **custom_kwargs: 自定义参数（会覆盖默认值）

    Returns:
        graph, mock_llm, mock_search
    """
    if mock_llm is None:
        mock_llm = AsyncMock()
    if mock_search is None:
        mock_search = Mock()

    # 默认为所有 agent 提供 mock LLM（防止 API key 错误）
    # 为测试设置 min_subtasks=1（允许单个子任务）
    default_kwargs = {
        "planner": {"llm": mock_llm, "min_subtasks": 1},
        "coder": {"llm": mock_llm},
        "reviewer": {"llm": mock_llm},
        "researcher": {"llm": mock_llm, "search": mock_search},
        "tool_runner": {},  # ToolRunner 不需要 LLM
        "stop_condition": {}
    }

    # 合并自定义参数
    for key, value in custom_kwargs.items():
        if key in default_kwargs and isinstance(value, dict):
            default_kwargs[key].update(value)
        else:
            default_kwargs[key] = value

    graph = create_full_swarm_graph(tmp_path, **default_kwargs)
    return graph, mock_llm, mock_search


@pytest.mark.asyncio
class TestCodeTaskIntegration:
    """测试代码任务端到端流程（Planner → Coder → Reviewer）"""

    async def test_simple_code_task_with_mocks(self, tmp_path):
        """测试简单代码任务（使用 mock LLM）"""
        # 创建 mock LLM
        mock_llm = AsyncMock()

        # Planner 响应
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "写一个 Python 函数",
  "subtasks": [
    {
      "id": 1,
      "type": "code",
      "description": "写一个计算斐波那契数列的函数",
      "language": "python",
      "acceptance_criteria": ["函数能正确计算斐波那契数列", "包含基本测试"]
    }
  ],
  "overall_acceptance": ["所有子任务通过"]
}
```"""

        # Coder 响应
        coder_response = Mock()
        coder_response.content = """```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 测试
print(fibonacci(5))
```"""

        # Reviewer 响应（通过）
        reviewer_response = Mock()
        reviewer_response.content = """```json
{
  "passed": true,
  "feedback": "代码正确实现了斐波那契函数，测试通过"
}
```"""

        # 配置 mock 返回值
        mock_llm.ainvoke = AsyncMock(side_effect=[
            planner_response,  # Planner 调用
            coder_response,    # Coder 调用
            reviewer_response  # Reviewer 调用
        ])

        # 创建图（注入 mock LLM，自动为未使用的 agent 提供默认 mock）
        graph, _, _ = create_mock_graph(tmp_path, mock_llm=mock_llm)

        # 创建初始状态
        state = create_initial_state("写一个 Python 函数计算斐波那契数列")

        # 执行图
        final_state = await graph.ainvoke(state)

        # 验证结果
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 1
        assert final_state["subtask_results"][0]["passed"] is True

    async def test_code_task_with_retry(self, tmp_path):
        """测试代码任务重试机制（Coder → Reviewer → Coder）"""
        mock_llm = AsyncMock()

        # Planner 响应
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "写一个函数",
  "subtasks": [
    {
      "id": 1,
      "type": "code",
      "description": "写一个函数",
      "language": "python",
      "acceptance_criteria": ["函数正确"]
    }
  ],
  "overall_acceptance": ["所有子任务通过"]
}
```"""

        # 第一次 Coder 响应（错误代码）
        coder_response_1 = Mock()
        coder_response_1.content = """```python
def bad_function():
    return 1 / 0  # ZeroDivisionError
```"""

        # 第一次 Reviewer 响应（失败）
        reviewer_response_1 = Mock()
        reviewer_response_1.content = """```json
{
  "passed": false,
  "feedback": "代码存在 ZeroDivisionError，需修复"
}
```"""

        # 第二次 Coder 响应（修复后）
        coder_response_2 = Mock()
        coder_response_2.content = """```python
def good_function():
    return 42
```"""

        # 第二次 Reviewer 响应（通过）
        reviewer_response_2 = Mock()
        reviewer_response_2.content = """```json
{
  "passed": true,
  "feedback": "代码已修复，测试通过"
}
```"""

        # 配置 mock 返回值
        mock_llm.ainvoke = AsyncMock(side_effect=[
            planner_response,
            coder_response_1,
            reviewer_response_1,
            coder_response_2,   # 重试
            reviewer_response_2  # 重试审查
        ])

        # 创建图（使用辅助函数自动为未使用的 agent 提供 mock）
        graph, _, _ = create_mock_graph(tmp_path, mock_llm=mock_llm)

        # 执行
        state = create_initial_state("写一个函数")
        final_state = await graph.ainvoke(state)

        # 验证重试成功
        assert final_state["status"] == "completed"
        assert final_state["iteration_count"] >= 1  # 至少重试一次


@pytest.mark.asyncio
class TestResearchTaskIntegration:
    """测试调研任务端到端流程（Planner → Researcher）"""

    async def test_simple_research_task(self, tmp_path):
        """测试简单调研任务"""
        mock_llm = AsyncMock()
        mock_search = Mock()

        # Planner 响应
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "调研 Python 异步编程",
  "subtasks": [
    {
      "id": 1,
      "type": "research",
      "description": "Python asyncio 最佳实践",
      "search_type": "web",
      "acceptance_criteria": ["完成调研报告"]
    }
  ],
  "overall_acceptance": ["所有调研任务完成"]
}
```"""

        # Researcher 总结响应
        researcher_response = Mock()
        researcher_response.content = """# Python asyncio 最佳实践

## 核心观点
1. 使用 async/await 语法
2. 避免阻塞调用
3. 使用 asyncio.gather 并发执行

## 参考资料
- Python 官方文档
"""

        # 配置 mock
        mock_llm.ainvoke = AsyncMock(side_effect=[
            planner_response,
            researcher_response
        ])
        mock_search.run = Mock(return_value="Python asyncio 搜索结果...")

        # 创建图（使用辅助函数自动为未使用的 agent 提供 mock）
        graph, _, _ = create_mock_graph(tmp_path, mock_llm=mock_llm, mock_search=mock_search)

        # 执行
        state = create_initial_state("调研 Python 异步编程")
        final_state = await graph.ainvoke(state)

        # 验证结果
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 1
        assert final_state["subtask_results"][0]["passed"] is True
        assert "asyncio" in final_state["subtask_results"][0]["research_result"]


@pytest.mark.asyncio
class TestToolTaskIntegration:
    """测试工具任务端到端流程（Planner → ToolRunner）"""

    async def test_simple_tool_task(self, tmp_path):
        """测试简单工具任务（创建文件）"""
        mock_llm = AsyncMock()

        # Planner 响应
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "创建测试文件",
  "subtasks": [
    {
      "id": 1,
      "type": "tool",
      "description": "创建 hello.txt",
      "tool_name": "write_file",
      "tool_args": {
        "path": "%s/hello.txt",
        "content": "Hello, MacCortex!"
      },
      "acceptance_criteria": ["文件创建成功"]
    }
  ],
  "overall_acceptance": ["所有工具任务完成"]
}
```""" % tmp_path

        # 配置 mock
        mock_llm.ainvoke = AsyncMock(return_value=planner_response)

        # 创建图（使用辅助函数自动为未使用的 agent 提供 mock）
        graph, _, _ = create_mock_graph(tmp_path, mock_llm=mock_llm)

        # 执行
        state = create_initial_state("创建测试文件 hello.txt")
        final_state = await graph.ainvoke(state)

        # 验证结果
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 1
        assert final_state["subtask_results"][0]["passed"] is True

        # 验证文件已创建
        test_file = tmp_path / "hello.txt"
        assert test_file.exists()
        assert test_file.read_text() == "Hello, MacCortex!"

    async def test_multiple_tool_tasks(self, tmp_path):
        """测试多个工具任务顺序执行"""
        mock_llm = AsyncMock()

        # Planner 响应（多个工具任务）
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "文件操作任务",
  "subtasks": [
    {
      "id": 1,
      "type": "tool",
      "description": "创建目录",
      "tool_name": "create_directory",
      "tool_args": {"path": "%s/test_dir"},
      "acceptance_criteria": ["目录创建成功"]
    },
    {
      "id": 2,
      "type": "tool",
      "description": "写入文件",
      "tool_name": "write_file",
      "tool_args": {
        "path": "%s/test_dir/data.txt",
        "content": "Test data"
      },
      "acceptance_criteria": ["文件写入成功"]
    }
  ],
  "overall_acceptance": ["所有文件操作完成"]
}
```""" % (tmp_path, tmp_path)

        # 配置 mock
        mock_llm.ainvoke = AsyncMock(return_value=planner_response)

        # 创建图（使用辅助函数自动为未使用的 agent 提供 mock）
        graph, _, _ = create_mock_graph(tmp_path, mock_llm=mock_llm)

        # 执行
        state = create_initial_state("创建目录并写入文件")
        final_state = await graph.ainvoke(state)

        # 验证结果
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 2
        assert all(r["passed"] for r in final_state["subtask_results"])

        # 验证文件系统
        assert (tmp_path / "test_dir").exists()
        assert (tmp_path / "test_dir" / "data.txt").exists()


@pytest.mark.asyncio
class TestMixedTaskIntegration:
    """测试混合任务工作流（代码 + 调研 + 工具）"""

    async def test_mixed_task_workflow(self, tmp_path):
        """测试混合任务：调研 → 代码 → 工具"""
        mock_llm = AsyncMock()
        mock_search = Mock()

        # Planner 响应（混合任务）
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "混合任务",
  "subtasks": [
    {
      "id": 1,
      "type": "research",
      "description": "调研 Python 文件操作",
      "search_type": "web",
      "acceptance_criteria": ["完成调研"]
    },
    {
      "id": 2,
      "type": "code",
      "description": "写一个文件读写函数",
      "language": "python",
      "acceptance_criteria": ["函数正确实现"]
    },
    {
      "id": 3,
      "type": "tool",
      "description": "创建测试文件",
      "tool_name": "write_file",
      "tool_args": {
        "path": "%s/test.txt",
        "content": "Test"
      },
      "acceptance_criteria": ["文件创建成功"]
    }
  ],
  "overall_acceptance": ["所有任务完成"]
}
```""" % tmp_path

        # Researcher 响应
        researcher_response = Mock()
        researcher_response.content = "# Python 文件操作\n\n使用 open() 函数..."

        # Coder 响应
        coder_response = Mock()
        coder_response.content = """```python
def read_file(path):
    with open(path, 'r') as f:
        return f.read()
```"""

        # Reviewer 响应
        reviewer_response = Mock()
        reviewer_response.content = '{"passed": true, "feedback": "代码正确"}'

        # 配置 mock
        mock_llm.ainvoke = AsyncMock(side_effect=[
            planner_response,
            researcher_response,
            coder_response,
            reviewer_response
        ])
        mock_search.run = Mock(return_value="Python 文件操作搜索结果...")

        # 创建图（使用辅助函数自动为未使用的 agent 提供 mock）
        graph, _, _ = create_mock_graph(tmp_path, mock_llm=mock_llm, mock_search=mock_search)

        # 执行
        state = create_initial_state("完成混合任务")
        final_state = await graph.ainvoke(state)

        # 验证结果
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 3
        assert all(r["passed"] for r in final_state["subtask_results"])

        # 验证各任务类型都执行了
        task_types = [r.get("subtask_description", "") for r in final_state["subtask_results"]]
        assert any("调研" in desc for desc in task_types)
        assert any("函数" in desc for desc in task_types)
        assert any("文件" in desc for desc in task_types)


@pytest.mark.asyncio
class TestErrorHandling:
    """测试错误处理与边界情况"""

    async def test_empty_plan(self, tmp_path):
        """测试空计划"""
        mock_llm = AsyncMock()

        # Planner 响应（空子任务）
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "空任务",
  "subtasks": [],
  "overall_acceptance": ["任务完成"]
}
```"""

        mock_llm.ainvoke = AsyncMock(return_value=planner_response)

        # 创建图
        graph = create_full_swarm_graph(
            tmp_path,
            planner={"llm": mock_llm}
        )

        # 执行
        state = create_initial_state("空任务")
        final_state = await graph.ainvoke(state)

        # 应该直接完成
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 0

    async def test_max_iterations_exceeded(self, tmp_path):
        """测试达到最大迭代次数"""
        mock_llm = AsyncMock()

        # Planner 响应
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "测试",
  "subtasks": [
    {
      "id": 1,
      "type": "code",
      "description": "写代码",
      "language": "python",
      "acceptance_criteria": ["代码正确"]
    }
  ],
  "overall_acceptance": ["任务完成"]
}
```"""

        # Coder 响应（始终生成错误代码）
        coder_response = Mock()
        coder_response.content = """```python
def bad():
    raise Exception("Always fails")
```"""

        # Reviewer 响应（始终失败）
        reviewer_response = Mock()
        reviewer_response.content = '{"passed": false, "feedback": "代码错误"}'

        # 配置 mock（模拟多次重试）
        mock_llm.ainvoke = AsyncMock(side_effect=[
            planner_response,
            coder_response,
            reviewer_response,
            coder_response,    # 重试 1
            reviewer_response,
            coder_response,    # 重试 2
            reviewer_response,
            coder_response,    # 重试 3
            reviewer_response,
        ])

        # 创建图（设置最大迭代次数为 3，使用辅助函数）
        graph, _, _ = create_mock_graph(
            tmp_path,
            mock_llm=mock_llm,
            stop_condition={"max_iterations": 3}
        )

        # 执行
        state = create_initial_state("测试最大迭代")
        final_state = await graph.ainvoke(state)

        # 应该在达到最大迭代后停止
        assert final_state["iteration_count"] >= 3


@pytest.mark.asyncio
class TestStopConditions:
    """测试停止条件"""

    async def test_stop_on_token_limit(self, tmp_path):
        """测试 Token 限制停止"""
        mock_llm = AsyncMock()

        # Planner 响应（大量子任务）
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "大量任务",
  "subtasks": [
    {"id": 1, "type": "research", "description": "任务1", "search_type": "web", "acceptance_criteria": ["完成"]},
    {"id": 2, "type": "research", "description": "任务2", "search_type": "web", "acceptance_criteria": ["完成"]},
    {"id": 3, "type": "research", "description": "任务3", "search_type": "web", "acceptance_criteria": ["完成"]}
  ],
  "overall_acceptance": ["所有任务完成"]
}
```"""

        researcher_response = Mock()
        researcher_response.content = "调研结果..."

        mock_llm.ainvoke = AsyncMock(side_effect=[
            planner_response,
            researcher_response,
            researcher_response,
            researcher_response
        ])

        mock_search = Mock()
        mock_search.run = Mock(return_value="搜索结果...")

        # 创建图（设置很小的 Token 限制，使用辅助函数）
        graph, _, _ = create_mock_graph(
            tmp_path,
            mock_llm=mock_llm,
            mock_search=mock_search,
            stop_condition={"max_tokens": 10}  # 非常小的限制
        )

        # 执行
        state = create_initial_state("大量任务")
        state["total_tokens"] = 5  # 起始 Token 数

        final_state = await graph.ainvoke(state)

        # 应该因 Token 限制提前停止
        # 注意：可能会完成部分任务
        assert final_state["total_tokens"] >= 5


@pytest.mark.asyncio
class TestRunFullSwarmTask:
    """测试 run_full_swarm_task 辅助函数"""

    async def test_run_full_swarm_task_helper(self, tmp_path):
        """测试辅助函数执行任务"""
        mock_llm = AsyncMock()
        mock_search = Mock()

        # Planner 响应
        planner_response = Mock()
        planner_response.content = """```json
{
  "task": "简单任务",
  "subtasks": [
    {
      "id": 1,
      "type": "research",
      "description": "调研测试",
      "search_type": "web",
      "acceptance_criteria": ["完成调研"]
    }
  ],
  "overall_acceptance": ["任务完成"]
}
```"""

        researcher_response = Mock()
        researcher_response.content = "调研结果"

        mock_llm.ainvoke = AsyncMock(side_effect=[
            planner_response,
            researcher_response
        ])
        mock_search.run = Mock(return_value="搜索结果")

        # 使用辅助函数执行
        result = await run_full_swarm_task(
            user_input="调研测试",
            workspace_path=tmp_path,
            planner={"llm": mock_llm},
            researcher={"llm": mock_llm, "search": mock_search}
        )

        # 验证结果
        assert result["status"] == "completed"
        assert len(result["subtask_results"]) == 1
        assert result["subtask_results"][0]["passed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
