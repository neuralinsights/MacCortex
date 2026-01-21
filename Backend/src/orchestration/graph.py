"""
MacCortex Swarm Graph - LangGraph Workflow

This module defines the main LangGraph workflow for complex task orchestration.
Supports both in-memory and SQLite-based checkpointing for state persistence.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pathlib import Path
from typing import Optional, Union

from .state import SwarmState


def create_swarm_graph(
    workspace_path: Path,
    checkpointer: Optional[Union[MemorySaver, SqliteSaver, AsyncSqliteSaver]] = None
) -> StateGraph:
    """
    创建 Swarm 工作流图

    Args:
        workspace_path: 工作空间路径（用于存放生成的代码和文件）
        checkpointer: 可选的检查点存储器（用于状态持久化）
                     - MemorySaver: 内存存储（开发/测试）
                     - SqliteSaver: SQLite 持久化（同步，生产）
                     - AsyncSqliteSaver: SQLite 持久化（异步，生产）

    Returns:
        StateGraph: 编译后的 LangGraph 状态图
    """
    # 创建状态图
    graph = StateGraph(SwarmState)

    # ===== 占位节点（Week 1 实现）=====
    def planner_placeholder(state: SwarmState) -> SwarmState:
        """Planner 占位节点"""
        print(f"[Planner] 收到任务: {state['user_input']}")
        # 临时：直接设置一个简单的计划
        state["plan"] = {
            "subtasks": [
                {
                    "id": "task-1",
                    "type": "code",
                    "description": "生成示例代码",
                    "dependencies": [],
                    "acceptance_criteria": ["代码能成功执行"]
                }
            ],
            "overall_acceptance": ["任务完成"]
        }
        state["status"] = "executing"
        return state

    def executor_placeholder(state: SwarmState) -> SwarmState:
        """Executor 占位节点"""
        print("[Executor] 执行子任务...")
        state["status"] = "completed"
        state["final_output"] = {"message": "占位实现 - 任务完成"}
        return state

    # 添加节点
    graph.add_node("planner", planner_placeholder)
    graph.add_node("executor", executor_placeholder)

    # 定义边
    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", END)

    # 编译图
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()


def run_swarm_task(
    user_input: str,
    workspace_path: Path,
    config: Optional[dict] = None
) -> dict:
    """
    执行 Swarm 任务

    Args:
        user_input: 用户输入的任务描述
        workspace_path: 工作空间路径
        config: 可选的配置（如 thread_id）

    Returns:
        dict: 任务执行结果
    """
    from .state import create_initial_state

    # 创建初始状态
    initial_state = create_initial_state(user_input)

    # 创建图（暂不使用检查点）
    graph = create_swarm_graph(workspace_path)

    # 执行
    final_state = graph.invoke(initial_state, config=config)

    return {
        "status": final_state["status"],
        "output": final_state.get("final_output"),
        "error": final_state.get("error_message")
    }


def create_sqlite_checkpointer_sync(db_path: str = "checkpoints.db"):
    """
    创建 SQLite checkpointer（同步版本，返回上下文管理器）

    Args:
        db_path: SQLite 数据库文件路径

    Returns:
        上下文管理器，在 with 块中产生 SqliteSaver 实例

    Example:
        with create_sqlite_checkpointer_sync("checkpoints.db") as checkpointer:
            graph = create_swarm_graph(workspace, checkpointer=checkpointer)
            result = graph.invoke(state, config=config)
    """
    return SqliteSaver.from_conn_string(db_path)


async def create_sqlite_checkpointer_async(db_path: str = "checkpoints.db"):
    """
    创建 SQLite checkpointer（异步版本，返回异步上下文管理器）

    Args:
        db_path: SQLite 数据库文件路径

    Returns:
        异步上下文管理器，在 async with 块中产生 AsyncSqliteSaver 实例

    Example:
        async with create_sqlite_checkpointer_async("checkpoints.db") as checkpointer:
            graph = create_swarm_graph(workspace, checkpointer=checkpointer)
            result = graph.invoke(state, config=config)
    """
    return AsyncSqliteSaver.from_conn_string(db_path)


async def resume_from_checkpoint(
    workspace_path: Path,
    thread_id: str,
    db_path: str = "checkpoints.db"
) -> dict:
    """
    从检查点恢复执行

    Args:
        workspace_path: 工作空间路径
        thread_id: 线程 ID（用于标识检查点）
        db_path: SQLite 数据库文件路径

    Returns:
        dict: 恢复的状态或执行结果
    """
    # 使用异步上下文管理器创建 checkpointer
    async with await create_sqlite_checkpointer_async(db_path) as checkpointer:
        # 配置线程 ID
        config = {"configurable": {"thread_id": thread_id}}

        # 获取最新检查点
        checkpoint = await checkpointer.aget(config)

        if checkpoint is None:
            raise ValueError(f"未找到线程 {thread_id} 的检查点")

        print(f"[恢复] 从检查点恢复: thread_id={thread_id}")
        print(f"[恢复] 检查点状态: {checkpoint}")

        # 从检查点继续执行
        # 注意: 实际恢复逻辑需要根据业务需求实现
        # 这里仅演示如何获取检查点
        return {
            "thread_id": thread_id,
            "checkpoint": checkpoint,
            "status": "ready_to_resume"
        }


# 用于测试的示例函数
async def test_basic_graph():
    """
    测试基础图功能
    """
    import tempfile

    workspace = Path(tempfile.mkdtemp())
    print(f"工作空间: {workspace}")

    result = run_swarm_task(
        user_input="写一个 Hello World 程序",
        workspace_path=workspace
    )

    print(f"执行结果: {result}")
    return result


if __name__ == "__main__":
    import asyncio
    import sys
    from pathlib import Path

    # 添加父目录到 sys.path 以支持相对导入
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    asyncio.run(test_basic_graph())
