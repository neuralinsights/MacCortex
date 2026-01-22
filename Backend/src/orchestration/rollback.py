"""
MacCortex Rollback Manager - 错误恢复与状态回滚

支持在 Swarm 执行过程中创建状态快照，并在错误发生时回滚到之前的稳定状态。

适用场景：
1. Coder 生成的代码破坏了现有文件
2. ToolRunner 执行危险操作后需要恢复
3. 网络错误导致状态不一致
4. 用户取消任务需要清理中间状态

回滚策略：
- 每个子任务开始前创建快照
- 快照包含状态副本 + 工作空间文件列表
- 支持多级回滚（最多保留 10 个快照）
"""

import shutil
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Snapshot:
    """状态快照"""
    id: str
    timestamp: float
    subtask_index: int
    subtask_id: str
    state: Dict[str, Any]  # SwarmState 副本
    workspace_files: List[str]  # 工作空间文件路径列表
    description: str


class RollbackManager:
    """回滚管理器"""

    def __init__(
        self,
        workspace_path: Path,
        max_snapshots: int = 10,
        snapshot_dir: Optional[Path] = None
    ):
        """
        初始化回滚管理器

        Args:
            workspace_path: 工作空间路径
            max_snapshots: 最大快照数量
            snapshot_dir: 快照存储目录（默认为 workspace/.snapshots）
        """
        self.workspace = Path(workspace_path)
        self.max_snapshots = max_snapshots

        # 快照存储目录
        if snapshot_dir:
            self.snapshot_dir = Path(snapshot_dir)
        else:
            self.snapshot_dir = self.workspace / ".snapshots"

        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        # 快照栈（LIFO）
        self.snapshots: List[Snapshot] = []

        # 统计
        self.total_snapshots_created = 0
        self.total_rollbacks = 0

    def create_snapshot(
        self,
        state: Dict[str, Any],
        description: str = "自动快照"
    ) -> str:
        """
        创建状态快照

        Args:
            state: SwarmState 字典
            description: 快照描述

        Returns:
            snapshot_id: 快照 ID
        """
        # 生成快照 ID
        snapshot_id = f"snapshot_{int(time.time() * 1000)}"

        # 获取当前子任务信息
        subtask_index = state.get("current_subtask_index", -1)
        plan = state.get("plan") or {}
        subtasks = plan.get("subtasks", []) if isinstance(plan, dict) else []

        if 0 <= subtask_index < len(subtasks):
            subtask_id = subtasks[subtask_index].get("id", "unknown")
        else:
            subtask_id = "none"

        # 获取工作空间文件列表
        workspace_files = self._list_workspace_files()

        # 创建快照对象
        snapshot = Snapshot(
            id=snapshot_id,
            timestamp=time.time(),
            subtask_index=subtask_index,
            subtask_id=subtask_id,
            state=self._copy_state(state),
            workspace_files=workspace_files,
            description=description
        )

        # 保存快照到文件
        self._save_snapshot(snapshot)

        # 添加到栈
        self.snapshots.append(snapshot)

        # LRU 淘汰
        if len(self.snapshots) > self.max_snapshots:
            old_snapshot = self.snapshots.pop(0)
            self._delete_snapshot(old_snapshot.id)

        self.total_snapshots_created += 1

        print(f"📸 创建快照: {snapshot_id} ({description})")
        return snapshot_id

    def rollback_to_last(self) -> Optional[Dict[str, Any]]:
        """
        回滚到最后一个快照

        Returns:
            恢复的状态（如果有快照），否则 None
        """
        if not self.snapshots:
            print("⚠️  无可用快照，无法回滚")
            return None

        # 弹出最后一个快照
        snapshot = self.snapshots.pop()

        # 恢复状态和文件
        restored_state = self._restore_snapshot(snapshot)

        self.total_rollbacks += 1

        print(f"🔄 回滚到快照: {snapshot.id} ({snapshot.description})")
        return restored_state

    def rollback_to_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        回滚到指定快照

        Args:
            snapshot_id: 快照 ID

        Returns:
            恢复的状态（如果找到），否则 None
        """
        # 查找快照
        snapshot_index = -1
        for i, snapshot in enumerate(self.snapshots):
            if snapshot.id == snapshot_id:
                snapshot_index = i
                break

        if snapshot_index == -1:
            print(f"⚠️  快照不存在: {snapshot_id}")
            return None

        # 获取目标快照
        snapshot = self.snapshots[snapshot_index]

        # 删除后续快照
        for i in range(len(self.snapshots) - 1, snapshot_index, -1):
            removed = self.snapshots.pop()
            self._delete_snapshot(removed.id)

        # 恢复
        restored_state = self._restore_snapshot(snapshot)

        self.total_rollbacks += 1

        print(f"🔄 回滚到快照: {snapshot_id} (索引: {snapshot_index})")
        return restored_state

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        列出所有快照

        Returns:
            快照列表（元数据）
        """
        snapshots_info = []
        for snapshot in self.snapshots:
            snapshots_info.append({
                "id": snapshot.id,
                "timestamp": snapshot.timestamp,
                "datetime": datetime.fromtimestamp(snapshot.timestamp).isoformat(),
                "subtask_id": snapshot.subtask_id,
                "subtask_index": snapshot.subtask_index,
                "description": snapshot.description,
                "file_count": len(snapshot.workspace_files)
            })
        return snapshots_info

    def clear_all_snapshots(self):
        """清空所有快照"""
        for snapshot in self.snapshots:
            self._delete_snapshot(snapshot.id)

        self.snapshots.clear()
        print("🗑️  清空所有快照")

    def _copy_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """深拷贝状态（避免引用修改）"""
        import copy
        return copy.deepcopy(state)

    def _list_workspace_files(self) -> List[str]:
        """列出工作空间文件（相对路径）"""
        files = []
        for file_path in self.workspace.rglob("*"):
            if file_path.is_file() and ".snapshots" not in file_path.parts:
                relative_path = file_path.relative_to(self.workspace)
                files.append(str(relative_path))
        return sorted(files)

    def _save_snapshot(self, snapshot: Snapshot):
        """保存快照到文件"""
        snapshot_file = self.snapshot_dir / f"{snapshot.id}.json"

        data = asdict(snapshot)
        with open(snapshot_file, "w") as f:
            json.dump(data, f, indent=2)

    def _restore_snapshot(self, snapshot: Snapshot) -> Dict[str, Any]:
        """
        恢复快照（状态 + 文件）

        Returns:
            恢复的状态
        """
        # 1. 恢复状态
        restored_state = self._copy_state(snapshot.state)

        # 2. 恢复文件系统（删除新增文件）
        current_files = set(self._list_workspace_files())
        snapshot_files = set(snapshot.workspace_files)

        # 删除新增的文件
        new_files = current_files - snapshot_files
        for file_path in new_files:
            full_path = self.workspace / file_path
            if full_path.exists():
                full_path.unlink()
                print(f"   删除新增文件: {file_path}")

        # 注意：不恢复已存在文件的内容（避免复杂性，仅删除新增文件）
        # 如需完整恢复，需保存文件内容快照（增加存储成本）

        return restored_state

    def _delete_snapshot(self, snapshot_id: str):
        """删除快照文件"""
        snapshot_file = self.snapshot_dir / f"{snapshot_id}.json"
        if snapshot_file.exists():
            snapshot_file.unlink()

    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "current_snapshots": len(self.snapshots),
            "max_snapshots": self.max_snapshots,
            "total_created": self.total_snapshots_created,
            "total_rollbacks": self.total_rollbacks,
            "workspace_path": str(self.workspace),
            "snapshot_dir": str(self.snapshot_dir)
        }
