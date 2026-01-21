"""
MacCortex Swarm Graph 基础测试

测试 LangGraph 基础功能：
1. 状态图创建
2. 状态初始化
3. 基本执行流程
"""

import pytest
from pathlib import Path
import tempfile

from src.orchestration.state import SwarmState, create_initial_state
from src.orchestration.graph import create_swarm_graph, run_swarm_task


class TestSwarmStateBasic:
    """测试状态定义"""

    def test_create_initial_state(self):
        """测试初始状态创建"""
        state = create_initial_state("测试任务")

        assert state["user_input"] == "测试任务"
        assert state["status"] == "planning"
        assert state["iteration_count"] == 0
        assert state["subtask_results"] == []
        assert state["plan"] is None
        assert state["user_interrupted"] is False

    def test_create_initial_state_with_context(self):
        """测试带上下文的初始状态"""
        context = {"file_path": "/path/to/file"}
        state = create_initial_state("测试任务", context)

        assert state["context"] == context
        assert "file_path" in state["context"]


class TestSwarmGraphBasic:
    """测试图创建和执行"""

    def test_create_graph(self):
        """测试图创建"""
        workspace = Path(tempfile.mkdtemp())
        graph = create_swarm_graph(workspace)

        assert graph is not None
        # LangGraph 编译后的图应该有可调用的方法
        assert callable(graph.invoke)

    def test_run_placeholder_task(self):
        """测试占位节点执行"""
        workspace = Path(tempfile.mkdtemp())

        result = run_swarm_task(
            user_input="写一个 Hello World 程序",
            workspace_path=workspace
        )

        # 验证返回结构
        assert "status" in result
        assert "output" in result
        assert "error" in result

        # 占位实现应该返回 completed 状态
        assert result["status"] == "completed"
        assert result["output"] is not None

    def test_graph_state_flow(self):
        """测试状态流转"""
        workspace = Path(tempfile.mkdtemp())
        graph = create_swarm_graph(workspace)

        initial_state = create_initial_state("测试任务")

        # 执行图
        final_state = graph.invoke(initial_state)

        # 验证状态变化
        assert final_state["status"] == "completed"
        assert final_state["plan"] is not None  # Planner 应该生成计划
        assert "subtasks" in final_state["plan"]


class TestSwarmStateTransitions:
    """测试状态转换"""

    def test_status_transitions(self):
        """测试状态转换序列"""
        state = create_initial_state("测试任务")

        # 初始状态
        assert state["status"] == "planning"

        # 模拟状态转换
        state["status"] = "executing"
        assert state["status"] == "executing"

        state["status"] = "reviewing"
        assert state["status"] == "reviewing"

        state["status"] = "completed"
        assert state["status"] == "completed"

    def test_iteration_increment(self):
        """测试迭代计数"""
        state = create_initial_state("测试任务")

        assert state["iteration_count"] == 0

        state["iteration_count"] += 1
        assert state["iteration_count"] == 1

        state["iteration_count"] += 1
        assert state["iteration_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
