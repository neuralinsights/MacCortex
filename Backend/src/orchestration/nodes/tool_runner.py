"""
MacCortex ToolRunner Agent

系统工具执行节点，负责：
1. 文件操作（移动、复制、删除、重命名）
2. 系统命令执行（沙箱隔离）
3. 安全边界检查（workspace 限制）
4. 超时控制与资源限制
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


from ..state import SwarmState


class ToolRunnerNode:
    """
    系统工具执行节点

    支持：
    - 文件操作（move, copy, delete, rename）
    - 系统命令执行（subprocess + 超时）
    - workspace 边界检查
    - 危险操作白名单
    """

    # 允许的文件操作
    ALLOWED_FILE_OPERATIONS = [
        "move_file",
        "copy_file",
        "delete_file",
        "rename_file",
        "create_directory",
        "read_file",
        "write_file",
    ]

    # 允许的系统命令（白名单）
    ALLOWED_COMMANDS = [
        "ls",
        "cat",
        "echo",
        "pwd",
        "date",
        "grep",
        "find",
        "wc",
    ]

    def __init__(
        self,
        workspace_path: Path,
        timeout: int = 30,
        allow_dangerous_ops: bool = False,
    ):
        """
        初始化 ToolRunner 节点

        Args:
            workspace_path: 工作空间路径（安全边界）
            timeout: 命令执行超时（秒）
            allow_dangerous_ops: 是否允许危险操作（默认 False）
        """
        self.workspace = Path(workspace_path).resolve()
        self.timeout = timeout
        self.allow_dangerous_ops = allow_dangerous_ops

        # 确保 workspace 存在
        self.workspace.mkdir(parents=True, exist_ok=True)

    async def run_tool(self, state: SwarmState) -> SwarmState:
        """
        执行系统工具

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

        # 检查是否是工具任务
        if subtask.get("type") != "tool":
            # 跳过非工具任务
            state["current_subtask_index"] += 1
            state["status"] = "planning"  # 返回 Planner 路由
            return state

        try:
            # 1. 执行工具
            tool_result = await self._execute_tool(
                tool_name=subtask.get("tool_name", ""),
                tool_args=subtask.get("tool_args", {}),
            )

            # 2. 检查结果是否包含错误信息
            is_error = (
                isinstance(tool_result, str)
                and ("失败" in tool_result or "错误" in tool_result or "Error" in tool_result)
            )

            # 3. 保存结果
            state["subtask_results"].append({
                "subtask_id": subtask["id"],
                "subtask_description": subtask["description"],
                "tool_result": tool_result if not is_error else None,
                "passed": not is_error,
                "error_message": tool_result if is_error else None,
                "completed_at": datetime.utcnow().isoformat()
            })

            # 4. 更新状态
            state["current_subtask_index"] += 1

            # 检查是否完成所有子任务
            if state["current_subtask_index"] >= len(subtasks):
                state["status"] = "completed"
            else:
                state["status"] = "planning"  # 返回 Planner 继续下一个任务

        except Exception as e:
            # 工具执行失败
            state["subtask_results"].append({
                "subtask_id": subtask["id"],
                "subtask_description": subtask["description"],
                "passed": False,
                "error_message": f"工具执行失败：{str(e)}",
                "completed_at": datetime.utcnow().isoformat()
            })

            # 继续下一个任务（工具失败不阻塞流程）
            state["current_subtask_index"] += 1
            if state["current_subtask_index"] >= len(subtasks):
                state["status"] = "completed"
            else:
                state["status"] = "planning"

        return state

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> str:
        """
        执行实际的工具操作

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            执行结果（字符串）
        """
        if not tool_name:
            return "错误：未指定工具名称"

        # 文件操作
        if tool_name in self.ALLOWED_FILE_OPERATIONS:
            return self._execute_file_operation(tool_name, tool_args)

        # 系统命令
        elif tool_name == "run_command":
            return self._execute_system_command(tool_args)

        else:
            return f"不支持的工具：{tool_name}"

    def _execute_file_operation(
        self,
        operation: str,
        args: Dict[str, Any],
    ) -> str:
        """
        执行文件操作

        Args:
            operation: 操作类型（move_file, copy_file, etc.）
            args: 操作参数

        Returns:
            执行结果
        """
        try:
            if operation == "move_file":
                return self._move_file(args.get("src", ""), args.get("dst", ""))

            elif operation == "copy_file":
                return self._copy_file(args.get("src", ""), args.get("dst", ""))

            elif operation == "delete_file":
                return self._delete_file(args.get("path", ""))

            elif operation == "rename_file":
                return self._rename_file(args.get("old_name", ""), args.get("new_name", ""))

            elif operation == "create_directory":
                return self._create_directory(args.get("path", ""))

            elif operation == "read_file":
                return self._read_file(args.get("path", ""))

            elif operation == "write_file":
                return self._write_file(args.get("path", ""), args.get("content", ""))

            else:
                return f"未实现的文件操作：{operation}"

        except Exception as e:
            return f"文件操作失败：{str(e)}"

    def _move_file(self, src: str, dst: str) -> str:
        """移动文件"""
        if not src or not dst:
            return "错误：缺少 src 或 dst 参数"

        src_path = Path(src).resolve()
        dst_path = Path(dst).resolve()

        # 安全检查
        if not src_path.exists():
            return f"错误：源文件不存在：{src}"

        if not self._is_within_workspace(src_path):
            return f"错误：源文件不在 workspace 内：{src}"

        if not self._is_within_workspace(dst_path.parent):
            return f"错误：目标路径不在 workspace 内：{dst}"

        # 执行移动
        shutil.move(str(src_path), str(dst_path))
        return f"成功：文件已移动：{src} → {dst}"

    def _copy_file(self, src: str, dst: str) -> str:
        """复制文件"""
        if not src or not dst:
            return "错误：缺少 src 或 dst 参数"

        src_path = Path(src).resolve()
        dst_path = Path(dst).resolve()

        # 安全检查
        if not src_path.exists():
            return f"错误：源文件不存在：{src}"

        if not self._is_within_workspace(src_path):
            return f"错误：源文件不在 workspace 内：{src}"

        if not self._is_within_workspace(dst_path.parent):
            return f"错误：目标路径不在 workspace 内：{dst}"

        # 执行复制
        if src_path.is_dir():
            shutil.copytree(str(src_path), str(dst_path), dirs_exist_ok=True)
        else:
            shutil.copy2(str(src_path), str(dst_path))

        return f"成功：文件已复制：{src} → {dst}"

    def _delete_file(self, path: str) -> str:
        """删除文件（危险操作）"""
        if not path:
            return "错误：缺少 path 参数"

        file_path = Path(path).resolve()

        # 安全检查
        if not file_path.exists():
            return f"错误：文件不存在：{path}"

        if not self._is_within_workspace(file_path):
            return f"错误：文件不在 workspace 内：{path}"

        # 危险操作检查
        if not self.allow_dangerous_ops:
            return f"错误：删除操作被禁用（需启用 allow_dangerous_ops）"

        # 执行删除
        if file_path.is_dir():
            shutil.rmtree(str(file_path))
        else:
            file_path.unlink()

        return f"成功：文件已删除：{path}"

    def _rename_file(self, old_name: str, new_name: str) -> str:
        """重命名文件"""
        if not old_name or not new_name:
            return "错误：缺少 old_name 或 new_name 参数"

        old_path = Path(old_name).resolve()
        new_path = Path(new_name).resolve()

        # 安全检查
        if not old_path.exists():
            return f"错误：文件不存在：{old_name}"

        if not self._is_within_workspace(old_path):
            return f"错误：文件不在 workspace 内：{old_name}"

        if not self._is_within_workspace(new_path.parent):
            return f"错误：目标路径不在 workspace 内：{new_name}"

        # 执行重命名
        old_path.rename(new_path)
        return f"成功：文件已重命名：{old_name} → {new_name}"

    def _create_directory(self, path: str) -> str:
        """创建目录"""
        if not path:
            return "错误：缺少 path 参数"

        dir_path = Path(path).resolve()

        # 安全检查
        if not self._is_within_workspace(dir_path):
            return f"错误：路径不在 workspace 内：{path}"

        # 执行创建
        dir_path.mkdir(parents=True, exist_ok=True)
        return f"成功：目录已创建：{path}"

    def _read_file(self, path: str) -> str:
        """读取文件内容"""
        if not path:
            return "错误：缺少 path 参数"

        file_path = Path(path).resolve()

        # 安全检查
        if not file_path.exists():
            return f"错误：文件不存在：{path}"

        if not file_path.is_file():
            return f"错误：不是文件：{path}"

        if not self._is_within_workspace(file_path):
            return f"错误：文件不在 workspace 内：{path}"

        # 执行读取
        try:
            content = file_path.read_text(encoding="utf-8")
            return f"成功：文件内容（{len(content)} 字符）：\n{content[:500]}"
        except UnicodeDecodeError:
            return f"错误：文件非 UTF-8 编码：{path}"

    def _write_file(self, path: str, content: str) -> str:
        """写入文件内容"""
        if not path:
            return "错误：缺少 path 参数"

        if content is None:
            return "错误：缺少 content 参数"

        file_path = Path(path).resolve()

        # 安全检查
        if not self._is_within_workspace(file_path.parent):
            return f"错误：路径不在 workspace 内：{path}"

        # 执行写入
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"成功：文件已写入：{path}（{len(content)} 字符）"

    def _execute_system_command(self, args: Dict[str, Any]) -> str:
        """
        执行系统命令（沙箱隔离）

        Args:
            args: 命令参数（command, arguments）

        Returns:
            命令输出或错误信息
        """
        command = args.get("command", "")
        arguments = args.get("arguments", [])

        if not command:
            return "错误：缺少 command 参数"

        # 白名单检查
        if command not in self.ALLOWED_COMMANDS:
            return f"错误：命令不在白名单中：{command}（允许：{', '.join(self.ALLOWED_COMMANDS)}）"

        # 构建完整命令
        if isinstance(arguments, str):
            full_command = [command, arguments]
        elif isinstance(arguments, list):
            full_command = [command] + arguments
        else:
            return f"错误：无效的 arguments 类型：{type(arguments)}"

        try:
            # 执行命令（超时控制）
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.workspace),  # 限制在 workspace 内执行
                check=False,
            )

            # 返回结果
            if result.returncode == 0:
                return f"成功：命令执行成功\nStdout:\n{result.stdout}"
            else:
                return f"错误：命令执行失败（退出码 {result.returncode}）\nStderr:\n{result.stderr}"

        except subprocess.TimeoutExpired:
            return f"错误：命令执行超时（{self.timeout} 秒）"

        except Exception as e:
            return f"错误：命令执行异常：{str(e)}"

    def _is_within_workspace(self, path: Path) -> bool:
        """
        检查路径是否在 workspace 内

        Args:
            path: 待检查的路径

        Returns:
            是否在 workspace 内
        """
        try:
            path.resolve().relative_to(self.workspace)
            return True
        except ValueError:
            return False


def create_tool_runner_node(
    workspace_path: Path,
    **kwargs
) -> callable:
    """
    创建 ToolRunner 节点（用于 LangGraph）

    Args:
        workspace_path: 工作空间路径
        **kwargs: 传递给 ToolRunnerNode 的参数

    Returns:
        ToolRunner 节点函数
    """
    tool_runner = ToolRunnerNode(workspace_path, **kwargs)

    async def tool_runner_node(state: SwarmState) -> SwarmState:
        """ToolRunner 节点函数"""
        return await tool_runner.run_tool(state)

    return tool_runner_node


# 用于测试的简化函数
async def test_tool_runner():
    """测试 ToolRunner 节点"""
    from ..state import create_initial_state

    # 创建 ToolRunner
    workspace = Path("/tmp/test_tool_runner")
    workspace.mkdir(exist_ok=True)

    tool_runner = ToolRunnerNode(workspace, allow_dangerous_ops=True)

    # 测试 1: 创建目录
    state1 = create_initial_state("测试工具任务")
    state1["plan"] = {
        "task": "测试工具任务",
        "subtasks": [
            {
                "id": 1,
                "type": "tool",
                "description": "创建测试目录",
                "tool_name": "create_directory",
                "tool_args": {"path": str(workspace / "test_dir")}
            }
        ]
    }
    state1["current_subtask_index"] = 0

    result_state = await tool_runner.run_tool(state1)
    print("=== 测试 1: 创建目录 ===")
    print(f"状态: {result_state['status']}")
    print(f"结果数量: {len(result_state['subtask_results'])}")
    if result_state["subtask_results"]:
        print(f"通过: {result_state['subtask_results'][0]['passed']}")
        print(f"结果: {result_state['subtask_results'][0]['tool_result']}")

    # 测试 2: 写入文件
    state2 = create_initial_state("测试文件写入")
    state2["plan"] = {
        "task": "测试文件写入",
        "subtasks": [
            {
                "id": 1,
                "type": "tool",
                "description": "写入测试文件",
                "tool_name": "write_file",
                "tool_args": {
                    "path": str(workspace / "test.txt"),
                    "content": "Hello, MacCortex!"
                }
            }
        ]
    }
    state2["current_subtask_index"] = 0

    result_state = await tool_runner.run_tool(state2)
    print("\n=== 测试 2: 写入文件 ===")
    print(f"状态: {result_state['status']}")
    if result_state["subtask_results"]:
        print(f"通过: {result_state['subtask_results'][0]['passed']}")
        print(f"结果: {result_state['subtask_results'][0]['tool_result']}")

    print("\n✅ ToolRunner 节点测试完成！")


if __name__ == "__main__":
    import sys
    import asyncio
    from pathlib import Path

    # 添加父目录到 sys.path 以支持相对导入
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    asyncio.run(test_tool_runner())
