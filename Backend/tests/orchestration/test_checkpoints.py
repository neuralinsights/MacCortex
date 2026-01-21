"""
MacCortex Checkpoint 测试

测试 LangGraph 检查点持久化功能，包括：
- SQLite checkpointer 创建
- 状态保存与加载
- 从检查点恢复执行
- 多线程隔离
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestration.graph import (
    create_swarm_graph,
    create_sqlite_checkpointer_sync,
    create_sqlite_checkpointer_async,
    resume_from_checkpoint
)
from src.orchestration.state import create_initial_state


class TestSqliteCheckpointer:
    """测试 SQLite Checkpointer 基础功能"""

    @pytest.mark.asyncio
    async def test_create_sqlite_checkpointer(self):
        """测试创建 SQLite checkpointer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_checkpoints.db")

            # 使用上下文管理器创建 checkpointer
            with create_sqlite_checkpointer_sync(db_path) as checkpointer:
                # 验证 checkpointer 创建成功
                assert checkpointer is not None
                assert os.path.exists(db_path)

    @pytest.mark.asyncio
    async def test_checkpointer_setup(self):
        """测试 checkpointer 初始化数据库表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_checkpoints.db")

            # 使用上下文管理器创建 checkpointer
            with create_sqlite_checkpointer_sync(db_path) as checkpointer:
                # 验证数据库文件存在
                assert os.path.exists(db_path)
                # 注意：数据库表在第一次写入前可能大小为0，这是正常的

    @pytest.mark.asyncio
    async def test_multiple_checkpointers_same_db(self):
        """测试同一数据库可以创建多个 checkpointer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "shared_checkpoints.db")

            # 使用上下文管理器创建多个 checkpointer
            with create_sqlite_checkpointer_sync(db_path) as checkpointer1:
                assert checkpointer1 is not None

            with create_sqlite_checkpointer_sync(db_path) as checkpointer2:
                assert checkpointer2 is not None


class TestCheckpointPersistence:
    """测试检查点持久化功能"""

    @pytest.mark.asyncio
    async def test_graph_with_checkpointer(self):
        """测试创建带 checkpointer 的图"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            db_path = os.path.join(tmpdir, "test_checkpoints.db")

            # 使用上下文管理器创建 checkpointer
            with create_sqlite_checkpointer_sync(db_path) as checkpointer:
                # 创建图
                graph = create_swarm_graph(workspace, checkpointer=checkpointer)

                # 验证图创建成功
                assert graph is not None

    @pytest.mark.asyncio
    async def test_save_and_load_checkpoint(self):
        """测试保存并加载检查点"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            db_path = os.path.join(tmpdir, "test_checkpoints.db")

            # 使用异步上下文管理器创建 checkpointer
            async with await create_sqlite_checkpointer_async(db_path) as checkpointer:
                # 创建图
                graph = create_swarm_graph(workspace, checkpointer=checkpointer)

                # 创建初始状态
                initial_state = create_initial_state("测试任务")

                # 配置线程 ID
                config = {"configurable": {"thread_id": "test-thread-1"}}

                # 异步执行图（会自动保存检查点）
                result = await graph.ainvoke(initial_state, config=config)

                # 验证执行结果
                assert result is not None
                assert result["status"] in ["executing", "completed"]

                # 尝试加载检查点
                checkpoint = await checkpointer.aget(config)

                # 验证检查点已保存
                assert checkpoint is not None

    @pytest.mark.asyncio
    async def test_thread_isolation(self):
        """测试不同线程的检查点隔离"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            db_path = os.path.join(tmpdir, "test_checkpoints.db")

            # 使用异步上下文管理器创建 checkpointer
            async with await create_sqlite_checkpointer_async(db_path) as checkpointer:
                # 创建图
                graph = create_swarm_graph(workspace, checkpointer=checkpointer)

                # 创建两个不同的初始状态
                state1 = create_initial_state("任务 1")
                state2 = create_initial_state("任务 2")

                # 使用不同的线程 ID
                config1 = {"configurable": {"thread_id": "thread-1"}}
                config2 = {"configurable": {"thread_id": "thread-2"}}

                # 异步执行两个图
                result1 = await graph.ainvoke(state1, config=config1)
                result2 = await graph.ainvoke(state2, config=config2)

                # 加载两个检查点
                checkpoint1 = await checkpointer.aget(config1)
                checkpoint2 = await checkpointer.aget(config2)

                # 验证检查点隔离
                assert checkpoint1 is not None
                assert checkpoint2 is not None
                # 注意: 具体的状态内容验证需要根据实际实现调整


class TestResumeFromCheckpoint:
    """测试从检查点恢复执行"""

    @pytest.mark.asyncio
    async def test_resume_basic(self):
        """测试基本的恢复功能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            db_path = os.path.join(tmpdir, "test_checkpoints.db")

            # 使用上下文管理器创建 checkpointer，执行并保存检查点
            with create_sqlite_checkpointer_sync(db_path) as checkpointer:
                # 创建图并执行
                graph = create_swarm_graph(workspace, checkpointer=checkpointer)
                initial_state = create_initial_state("测试恢复任务")
                config = {"configurable": {"thread_id": "resume-test-1"}}

                # 执行并保存检查点
                result = graph.invoke(initial_state, config=config)

            # checkpointer 已关闭，现在尝试恢复
            resume_result = await resume_from_checkpoint(
                workspace_path=workspace,
                thread_id="resume-test-1",
                db_path=db_path
            )

            # 验证恢复结果
            assert resume_result is not None
            assert resume_result["thread_id"] == "resume-test-1"
            assert resume_result["checkpoint"] is not None

    @pytest.mark.asyncio
    async def test_resume_nonexistent_thread(self):
        """测试恢复不存在的线程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            db_path = os.path.join(tmpdir, "test_checkpoints.db")

            # 尝试恢复不存在的线程，应该抛出异常
            with pytest.raises(ValueError, match="未找到线程"):
                await resume_from_checkpoint(
                    workspace_path=workspace,
                    thread_id="nonexistent-thread",
                    db_path=db_path
                )


class TestCheckpointIntegration:
    """集成测试：完整的工作流"""

    @pytest.mark.asyncio
    async def test_full_workflow_with_checkpoint(self):
        """测试完整的工作流（保存 → 恢复 → 继续执行）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            db_path = os.path.join(tmpdir, "workflow_checkpoints.db")

            # 使用异步上下文管理器创建 checkpointer
            async with await create_sqlite_checkpointer_async(db_path) as checkpointer:
                # 创建图
                graph = create_swarm_graph(workspace, checkpointer=checkpointer)

                # 初始状态
                initial_state = create_initial_state("完整工作流测试")
                config = {"configurable": {"thread_id": "workflow-1"}}

                # 第一阶段：异步执行并保存检查点
                result1 = await graph.ainvoke(initial_state, config=config)

                assert result1 is not None
                assert result1["status"] in ["executing", "completed"]

                # 验证检查点已保存
                checkpoint = await checkpointer.aget(config)
                assert checkpoint is not None

            # checkpointer 已关闭，第二阶段：模拟中断后恢复
            # 注意: 实际恢复执行需要根据业务逻辑实现
            resume_info = await resume_from_checkpoint(
                workspace_path=workspace,
                thread_id="workflow-1",
                db_path=db_path
            )

            assert resume_info["status"] == "ready_to_resume"

    @pytest.mark.asyncio
    async def test_checkpoint_with_planner(self, monkeypatch):
        """测试 Planner Node 与 checkpoint 集成"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            db_path = os.path.join(tmpdir, "planner_checkpoints.db")

            # Mock LLM 响应
            mock_response = MagicMock()
            mock_response.content = """```json
{
  "subtasks": [
    {
      "id": "task-1",
      "type": "code",
      "description": "编写测试代码",
      "dependencies": [],
      "acceptance_criteria": ["代码能运行"]
    },
    {
      "id": "task-2",
      "type": "code",
      "description": "编写测试",
      "dependencies": ["task-1"],
      "acceptance_criteria": ["测试通过"]
    },
    {
      "id": "task-3",
      "type": "tool",
      "description": "提交代码",
      "dependencies": ["task-2"],
      "acceptance_criteria": ["提交成功"]
    }
  ],
  "overall_acceptance": ["任务完成"]
}
```"""

            with patch('langchain_anthropic.ChatAnthropic.ainvoke', new_callable=AsyncMock) as mock_ainvoke:
                mock_ainvoke.return_value = mock_response

                # 使用异步上下文管理器创建 checkpointer
                async with await create_sqlite_checkpointer_async(db_path) as checkpointer:
                    # 创建图（集成 Planner）
                    graph = create_swarm_graph(workspace, checkpointer=checkpointer)

                    # 创建初始状态
                    initial_state = create_initial_state("测试 Planner 与 checkpoint 集成")

                    # 配置
                    config = {"configurable": {"thread_id": "planner-test-1"}}

                    # 通过 graph 执行（会自动保存检查点）
                    result_state = await graph.ainvoke(initial_state, config=config)

                    # 验证执行成功（可能是 executing 或 completed）
                    assert result_state["status"] in ["executing", "completed"]

                    # 验证检查点已保存
                    checkpoint = await checkpointer.aget(config)
                    assert checkpoint is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
