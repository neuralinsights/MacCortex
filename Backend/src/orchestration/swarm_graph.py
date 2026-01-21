"""
MacCortex Swarm Graph - 完整实现

集成所有 Agent 的完整 LangGraph 工作流：
- Planner: 任务拆解
- Coder: 代码生成
- Reviewer: 代码审查
- Researcher: 调研与搜索
- ToolRunner: 系统工具执行
- StopCondition: 循环终止检查
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pathlib import Path
from typing import Optional

from .state import SwarmState
from .nodes.planner import create_planner_node
from .nodes.coder import create_coder_node
from .nodes.reviewer import create_reviewer_node
from .nodes.researcher import create_researcher_node
from .nodes.tool_runner import create_tool_runner_node
from .nodes.stop_condition import create_stop_condition_node


def create_full_swarm_graph(
    workspace_path: Path,
    checkpointer: Optional[MemorySaver] = None,
    **agent_kwargs
) -> StateGraph:
    """
    创建完整的 Swarm 工作流图

    工作流程：
    1. Planner 拆解任务
    2. 根据子任务类型路由到不同 Agent：
       - code → Coder → Reviewer
       - research → Researcher
       - tool → ToolRunner
    3. StopCondition 检查是否终止
    4. 返回 Planner 继续下一个子任务

    Args:
        workspace_path: 工作空间路径
        checkpointer: 可选的检查点存储器
        **agent_kwargs: 传递给各 Agent 的参数

    Returns:
        编译后的 StateGraph
    """
    # 创建状态图
    graph = StateGraph(SwarmState)

    # 创建所有 Agent 节点
    planner_node = create_planner_node(workspace_path, **agent_kwargs.get("planner", {}))
    coder_node = create_coder_node(workspace_path, **agent_kwargs.get("coder", {}))
    reviewer_node = create_reviewer_node(workspace_path, **agent_kwargs.get("reviewer", {}))
    researcher_node = create_researcher_node(workspace_path, **agent_kwargs.get("researcher", {}))
    tool_runner_node = create_tool_runner_node(workspace_path, **agent_kwargs.get("tool_runner", {}))
    stop_condition_node = create_stop_condition_node(**agent_kwargs.get("stop_condition", {}))

    # 添加节点到图
    graph.add_node("planner", planner_node)
    graph.add_node("coder", coder_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("tool_runner", tool_runner_node)
    graph.add_node("stop_condition", stop_condition_node)

    # 设置入口点
    graph.set_entry_point("planner")

    # 定义路由函数
    def route_after_planner(state: SwarmState) -> str:
        """
        Planner 后的路由逻辑

        根据当前子任务类型路由到不同 Agent
        """
        status = state.get("status", "")

        # 检查是否完成
        if status == "completed":
            return END

        # 检查是否失败
        if status == "failed":
            return END

        # 获取当前子任务
        plan = state.get("plan") or {}
        subtasks = plan.get("subtasks", []) if plan else []
        current_index = state.get("current_subtask_index", 0)

        if not subtasks or current_index >= len(subtasks):
            return END

        subtask = subtasks[current_index]
        task_type = subtask.get("type", "")

        # 根据任务类型路由
        if task_type == "code":
            return "coder"
        elif task_type == "research":
            return "researcher"
        elif task_type == "tool":
            return "tool_runner"
        else:
            # 未知类型，跳过并返回 planner
            return "planner"

    def route_after_coder(state: SwarmState) -> str:
        """Coder 后路由到 Reviewer"""
        return "reviewer"

    def route_after_reviewer(state: SwarmState) -> str:
        """
        Reviewer 后的路由逻辑

        如果审查通过 → stop_condition
        如果审查失败且未达最大迭代 → coder（重新生成）
        如果达到最大迭代 → stop_condition
        """
        # 获取最后一个结果
        subtask_results = state.get("subtask_results", [])
        if not subtask_results:
            return "stop_condition"

        last_result = subtask_results[-1]

        # 如果通过，继续下一步
        if last_result.get("passed", False):
            return "stop_condition"

        # 如果失败，检查迭代次数
        iteration_count = state.get("iteration_count", 0)
        max_iterations = 3  # TODO: 从配置读取

        if iteration_count < max_iterations:
            # 未达最大迭代，返回 Coder 重新生成
            state["iteration_count"] = iteration_count + 1
            state["review_feedback"] = last_result.get("feedback", "")
            return "coder"
        else:
            # 达到最大迭代，终止
            return "stop_condition"

    def route_after_researcher(state: SwarmState) -> str:
        """Researcher 后路由到 stop_condition"""
        return "stop_condition"

    def route_after_tool_runner(state: SwarmState) -> str:
        """ToolRunner 后路由到 stop_condition"""
        return "stop_condition"

    def route_after_stop_condition(state: SwarmState) -> str:
        """
        StopCondition 后的路由逻辑

        如果状态为 completed 或 failed → END
        否则 → planner（继续下一个子任务）
        """
        status = state.get("status", "")

        if status in ["completed", "failed"]:
            return END
        else:
            return "planner"

    # 添加条件边
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "coder": "coder",
            "researcher": "researcher",
            "tool_runner": "tool_runner",
            "planner": "planner",
            END: END
        }
    )

    graph.add_conditional_edges("coder", route_after_coder, {"reviewer": "reviewer"})

    graph.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {
            "coder": "coder",
            "stop_condition": "stop_condition"
        }
    )

    graph.add_conditional_edges(
        "researcher",
        route_after_researcher,
        {"stop_condition": "stop_condition"}
    )

    graph.add_conditional_edges(
        "tool_runner",
        route_after_tool_runner,
        {"stop_condition": "stop_condition"}
    )

    graph.add_conditional_edges(
        "stop_condition",
        route_after_stop_condition,
        {
            "planner": "planner",
            END: END
        }
    )

    # 编译图
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()


async def run_full_swarm_task(
    user_input: str,
    workspace_path: Path,
    config: Optional[dict] = None,
    **agent_kwargs
) -> dict:
    """
    执行完整的 Swarm 任务

    Args:
        user_input: 用户输入的任务描述
        workspace_path: 工作空间路径
        config: 可选的配置（如 thread_id）
        **agent_kwargs: 传递给各 Agent 的参数

    Returns:
        dict: 任务执行结果
    """
    from .state import create_initial_state

    # 创建初始状态
    initial_state = create_initial_state(user_input)

    # 创建图
    graph = create_full_swarm_graph(workspace_path, **agent_kwargs)

    # 执行
    final_state = await graph.ainvoke(initial_state, config=config)

    return {
        "status": final_state["status"],
        "plan": final_state.get("plan"),
        "subtask_results": final_state.get("subtask_results", []),
        "final_output": final_state.get("final_output"),
        "error": final_state.get("error_message"),
        "iteration_count": final_state.get("iteration_count", 0),
        "total_tokens": final_state.get("total_tokens", 0),
    }


# 用于测试的简化函数
async def test_full_graph():
    """测试完整图功能"""
    import tempfile

    workspace = Path(tempfile.mkdtemp())
    print(f"工作空间: {workspace}")

    # 测试简单任务
    result = await run_full_swarm_task(
        user_input="创建一个测试文件 hello.txt，内容为 'Hello, MacCortex!'",
        workspace_path=workspace
    )

    print(f"\n执行结果: {result}")
    return result


if __name__ == "__main__":
    import sys
    import asyncio
    from pathlib import Path

    # 添加父目录到 sys.path 以支持相对导入
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    asyncio.run(test_full_graph())
