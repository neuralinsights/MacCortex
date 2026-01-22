"""
MacCortex Human-in-the-Loop 集成测试
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from src.orchestration.swarm_graph import create_full_swarm_graph
from src.orchestration.state import create_initial_state


@pytest.fixture
def tmp_path():
    """临时工作空间"""
    return Path(tempfile.mkdtemp())


def create_mock_llm_for_hitl(workspace_path=None):
    """创建用于 HITL 测试的 Mock LLM

    Args:
        workspace_path: 工作空间路径，用于生成完整的文件路径
    """
    mock_llm = AsyncMock()

    # 使用完整路径（如果提供 workspace_path）
    file_path = f"{workspace_path}/hello.txt" if workspace_path else "hello.txt"

    # Planner 响应（单个工具任务）
    planner_response = Mock()
    planner_response.content = f"""```json
{{
  "task": "创建测试文件",
  "subtasks": [
    {{
      "id": "task-1",
      "type": "tool",
      "description": "创建 hello.txt 文件",
      "dependencies": [],
      "acceptance_criteria": ["文件创建成功"],
      "tool_name": "write_file",
      "tool_args": {{
        "path": "{file_path}",
        "content": "Hello, HITL!"
      }}
    }}
  ],
  "overall_acceptance": ["文件创建成功"]
}}
```"""

    # Reflector 响应
    reflector_response = Mock()
    reflector_response.content = """```json
{
  "passed": true,
  "summary": "任务成功完成。",
  "feedback": "",
  "achievements": ["创建了 hello.txt"],
  "issues": [],
  "recommendation": "completed"
}
```"""

    mock_llm.ainvoke = AsyncMock(side_effect=[
        planner_response,
        reflector_response
    ])

    return mock_llm


@pytest.mark.asyncio
class TestToolRunnerHITL:
    """测试 ToolRunner 的 HITL 功能"""

    async def test_tool_approval_approve(self, tmp_path):
        """测试工具执行审批：批准"""

        # 创建 Mock LLM
        mock_llm = create_mock_llm_for_hitl(workspace_path=tmp_path)

        # 创建带 checkpointer 的 graph（启用工具审批）
        checkpointer = InMemorySaver()
        graph = create_full_swarm_graph(
            workspace_path=tmp_path,
            checkpointer=checkpointer,
            planner={"llm": mock_llm, "min_subtasks": 1},
            coder={"llm": mock_llm},
            reviewer={"llm": mock_llm},
            researcher={"llm": mock_llm},
            tool_runner={"require_approval": True},  # ← 启用 HITL
            stop_condition={},
            reflector={"llm": mock_llm}
        )

        thread = {"configurable": {"thread_id": "test-approval"}}

        # 1. 执行到第一个中断点
        state = create_initial_state("创建测试文件")
        result = await graph.ainvoke(state, thread)

        # 2. 验证中断
        current_state = graph.get_state(thread)
        assert current_state.interrupts, "应该在 ToolRunner 中断"

        interrupt_obj = current_state.interrupts[0]
        interrupt_data = interrupt_obj.value  # 访问 Interrupt 对象的 value 属性
        assert interrupt_data["operation"] == "tool_execution"
        assert interrupt_data["details"]["tool_name"] == "write_file"

        # 3. 用户批准
        user_decision = {
            "action": "approve",
            "operation": "tool_execution",
            "timestamp": "2026-01-22T00:00:00Z"
        }

        # 4. 恢复执行
        final_state = await graph.ainvoke(Command(resume=user_decision), thread)

        # 5. 验证完成
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 1
        assert final_state["subtask_results"][0]["passed"] is True

        # 验证文件创建
        hello_file = tmp_path / "hello.txt"
        assert hello_file.exists()
        assert hello_file.read_text() == "Hello, HITL!"

    async def test_tool_approval_deny(self, tmp_path):
        """测试工具执行审批：拒绝"""

        mock_llm = create_mock_llm_for_hitl(workspace_path=tmp_path)

        checkpointer = InMemorySaver()
        graph = create_full_swarm_graph(
            workspace_path=tmp_path,
            checkpointer=checkpointer,
            planner={"llm": mock_llm, "min_subtasks": 1},
            coder={"llm": mock_llm},
            reviewer={"llm": mock_llm},
            researcher={"llm": mock_llm},
            tool_runner={"require_approval": True},
            stop_condition={},
            reflector={"llm": mock_llm}
        )

        thread = {"configurable": {"thread_id": "test-deny"}}

        # 执行到中断点
        state = create_initial_state("创建测试文件")
        await graph.ainvoke(state, thread)

        # 验证中断
        current_state = graph.get_state(thread)
        assert current_state.interrupts

        # 用户拒绝
        user_decision = {
            "action": "deny",
            "operation": "tool_execution",
            "timestamp": "2026-01-22T00:00:00Z"
        }

        # 恢复执行
        final_state = await graph.ainvoke(Command(resume=user_decision), thread)

        # 验证工具未执行
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 1
        assert final_state["subtask_results"][0]["passed"] is False
        assert "用户拒绝" in final_state["subtask_results"][0]["error_message"]

        # 验证文件未创建
        hello_file = tmp_path / "hello.txt"
        assert not hello_file.exists()

    async def test_tool_approval_abort(self, tmp_path):
        """测试工具执行审批：终止工作流"""

        mock_llm = create_mock_llm_for_hitl(workspace_path=tmp_path)

        checkpointer = InMemorySaver()
        graph = create_full_swarm_graph(
            workspace_path=tmp_path,
            checkpointer=checkpointer,
            planner={"llm": mock_llm, "min_subtasks": 1},
            coder={"llm": mock_llm},
            reviewer={"llm": mock_llm},
            researcher={"llm": mock_llm},
            tool_runner={"require_approval": True},
            stop_condition={},
            reflector={"llm": mock_llm}
        )

        thread = {"configurable": {"thread_id": "test-abort"}}

        # 执行到中断点
        state = create_initial_state("创建测试文件")
        await graph.ainvoke(state, thread)

        # 用户终止
        user_decision = {
            "action": "abort",
            "operation": "tool_execution",
            "timestamp": "2026-01-22T00:00:00Z"
        }

        # 恢复执行
        final_state = await graph.ainvoke(Command(resume=user_decision), thread)

        # 验证工作流终止
        assert final_state["status"] == "failed"
        assert "用户终止" in final_state["error_message"]

        # 验证文件未创建
        hello_file = tmp_path / "hello.txt"
        assert not hello_file.exists()


@pytest.mark.asyncio
class TestHITLWithoutApproval:
    """测试禁用 HITL 时的正常流程"""

    async def test_tool_without_approval(self, tmp_path):
        """测试禁用工具审批时正常执行"""

        mock_llm = create_mock_llm_for_hitl(workspace_path=tmp_path)

        # 不启用 checkpointer 和 HITL
        graph = create_full_swarm_graph(
            workspace_path=tmp_path,
            planner={"llm": mock_llm, "min_subtasks": 1},
            coder={"llm": mock_llm},
            reviewer={"llm": mock_llm},
            researcher={"llm": mock_llm},
            tool_runner={"require_approval": False},  # ← 禁用 HITL
            stop_condition={},
            reflector={"llm": mock_llm}
        )

        # 直接执行完成（无中断）
        state = create_initial_state("创建测试文件")
        final_state = await graph.ainvoke(state)

        # 验证直接完成
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 1
        assert final_state["subtask_results"][0]["passed"] is True

        # 验证文件创建
        hello_file = tmp_path / "hello.txt"
        assert hello_file.exists()
        assert hello_file.read_text() == "Hello, HITL!"


@pytest.mark.asyncio
class TestMultipleInterrupts:
    """测试多次中断场景"""

    async def test_multiple_tool_approvals(self, tmp_path):
        """测试多个工具任务的连续审批"""

        mock_llm = AsyncMock()

        # Planner 响应（两个工具任务）
        planner_response = Mock()
        planner_response.content = f"""```json
{{
  "task": "创建多个文件",
  "subtasks": [
    {{
      "id": "task-1",
      "type": "tool",
      "description": "创建 file1.txt",
      "dependencies": [],
      "acceptance_criteria": ["文件创建成功"],
      "tool_name": "write_file",
      "tool_args": {{
        "path": "{tmp_path}/file1.txt",
        "content": "File 1"
      }}
    }},
    {{
      "id": "task-2",
      "type": "tool",
      "description": "创建 file2.txt",
      "dependencies": [],
      "acceptance_criteria": ["文件创建成功"],
      "tool_name": "write_file",
      "tool_args": {{
        "path": "{tmp_path}/file2.txt",
        "content": "File 2"
      }}
    }}
  ],
  "overall_acceptance": ["所有文件创建成功"]
}}
```"""

        # Reflector 响应
        reflector_response = Mock()
        reflector_response.content = """```json
{
  "passed": true,
  "summary": "所有任务成功完成。",
  "feedback": "",
  "achievements": ["创建了所有文件"],
  "issues": [],
  "recommendation": "completed"
}
```"""

        mock_llm.ainvoke = AsyncMock(side_effect=[
            planner_response,
            reflector_response
        ])

        checkpointer = InMemorySaver()
        graph = create_full_swarm_graph(
            workspace_path=tmp_path,
            checkpointer=checkpointer,
            planner={"llm": mock_llm, "min_subtasks": 1},
            coder={"llm": mock_llm},
            reviewer={"llm": mock_llm},
            researcher={"llm": mock_llm},
            tool_runner={"require_approval": True},
            stop_condition={},
            reflector={"llm": mock_llm}
        )

        thread = {"configurable": {"thread_id": "test-multiple"}}

        # 执行到第一个中断点
        state = create_initial_state("创建多个文件")
        await graph.ainvoke(state, thread)

        # 第一次审批：批准 file1.txt
        current_state = graph.get_state(thread)
        assert current_state.interrupts
        assert "file1.txt" in str(current_state.interrupts[0])

        await graph.ainvoke(
            Command(resume={"action": "approve", "operation": "tool_execution", "timestamp": "2026-01-22T00:00:00Z"}),
            thread
        )

        # 第二次审批：批准 file2.txt
        current_state = graph.get_state(thread)
        assert current_state.interrupts
        assert "file2.txt" in str(current_state.interrupts[0])

        final_state = await graph.ainvoke(
            Command(resume={"action": "approve", "operation": "tool_execution", "timestamp": "2026-01-22T00:00:01Z"}),
            thread
        )

        # 验证完成
        assert final_state["status"] == "completed"
        assert len(final_state["subtask_results"]) == 2
        assert all(r["passed"] for r in final_state["subtask_results"])

        # 验证两个文件都创建
        assert (tmp_path / "file1.txt").exists()
        assert (tmp_path / "file2.txt").exists()
