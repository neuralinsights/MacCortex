"""测试回滚管理器"""

import pytest
import tempfile
import time
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestration.rollback import RollbackManager
from src.orchestration.state import create_initial_state


class TestRollbackManager:
    """测试回滚管理器基本功能"""

    def test_create_snapshot(self):
        """测试创建快照"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            manager = RollbackManager(workspace)
            state = create_initial_state("test task")

            snapshot_id = manager.create_snapshot(state, "测试快照")

            assert snapshot_id.startswith("snapshot_")
            assert len(manager.snapshots) == 1
            assert manager.total_snapshots_created == 1

    def test_rollback_to_last(self):
        """测试回滚到最后一个快照"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            manager = RollbackManager(workspace)

            # 创建初始状态
            state1 = create_initial_state("task1")
            state1["current_subtask_index"] = 0
            manager.create_snapshot(state1, "快照1")

            # 修改状态
            state2 = create_initial_state("task1")
            state2["current_subtask_index"] = 1
            manager.create_snapshot(state2, "快照2")

            # 回滚
            restored = manager.rollback_to_last()

            assert restored is not None
            assert restored["current_subtask_index"] == 1
            assert len(manager.snapshots) == 1  # 快照2被弹出

    def test_rollback_with_files(self):
        """测试回滚文件变更"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            manager = RollbackManager(workspace)

            # 创建初始文件
            file1 = workspace / "file1.txt"
            file1.write_text("content1")

            # 创建快照
            state = create_initial_state("test")
            manager.create_snapshot(state, "初始快照")

            # 添加新文件
            file2 = workspace / "file2.txt"
            file2.write_text("content2")

            assert file2.exists()

            # 回滚
            manager.rollback_to_last()

            # 新文件应该被删除
            assert not file2.exists()
            assert file1.exists()

    def test_lru_snapshot_eviction(self):
        """测试快照 LRU 淘汰"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            manager = RollbackManager(workspace, max_snapshots=3)

            # 创建 4 个快照
            for i in range(4):
                state = create_initial_state(f"task{i}")
                manager.create_snapshot(state, f"快照{i}")

            # 应该只保留最后 3 个
            assert len(manager.snapshots) == 3
            assert manager.snapshots[0].description == "快照1"
            assert manager.snapshots[2].description == "快照3"

    def test_list_snapshots(self):
        """测试列出快照"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            manager = RollbackManager(workspace)

            state1 = create_initial_state("task1")
            manager.create_snapshot(state1, "快照A")

            state2 = create_initial_state("task2")
            manager.create_snapshot(state2, "快照B")

            snapshots = manager.list_snapshots()

            assert len(snapshots) == 2
            assert snapshots[0]["description"] == "快照A"
            assert snapshots[1]["description"] == "快照B"
            assert "datetime" in snapshots[0]
            assert "file_count" in snapshots[0]

    def test_clear_all_snapshots(self):
        """测试清空所有快照"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            manager = RollbackManager(workspace)

            for i in range(3):
                state = create_initial_state(f"task{i}")
                manager.create_snapshot(state, f"快照{i}")

            assert len(manager.snapshots) == 3

            manager.clear_all_snapshots()

            assert len(manager.snapshots) == 0

    def test_snapshot_persistence(self):
        """测试快照持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            manager = RollbackManager(workspace)
            state = create_initial_state("test")

            snapshot_id = manager.create_snapshot(state, "持久化测试")

            # 快照文件应该存在
            snapshot_file = manager.snapshot_dir / f"{snapshot_id}.json"
            assert snapshot_file.exists()

    def test_rollback_to_snapshot_by_id(self):
        """测试回滚到指定快照"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            manager = RollbackManager(workspace)

            # 创建 3 个快照
            state1 = create_initial_state("task1")
            state1["current_subtask_index"] = 0
            snapshot_id1 = manager.create_snapshot(state1, "快照1")

            state2 = create_initial_state("task2")
            state2["current_subtask_index"] = 1
            manager.create_snapshot(state2, "快照2")

            state3 = create_initial_state("task3")
            state3["current_subtask_index"] = 2
            manager.create_snapshot(state3, "快照3")

            # 回滚到第一个快照
            restored = manager.rollback_to_snapshot(snapshot_id1)

            assert restored is not None
            assert restored["current_subtask_index"] == 0
            # 后续快照应该被删除
            assert len(manager.snapshots) == 1

    def test_stats(self):
        """测试统计信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            manager = RollbackManager(workspace, max_snapshots=5)

            state = create_initial_state("test")
            manager.create_snapshot(state)
            manager.create_snapshot(state)
            manager.rollback_to_last()

            stats = manager.stats()

            assert stats["current_snapshots"] == 1
            assert stats["max_snapshots"] == 5
            assert stats["total_created"] == 2
            assert stats["total_rollbacks"] == 1
            assert "workspace_path" in stats
