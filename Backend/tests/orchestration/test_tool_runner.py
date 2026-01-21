"""
MacCortex ToolRunner 测试

测试系统工具执行节点功能，包括：
- 文件操作（移动、复制、删除、重命名、读写）
- 系统命令执行
- workspace 安全边界
- 超时控制
- 错误处理
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestration.nodes.tool_runner import (
    ToolRunnerNode,
    create_tool_runner_node
)
from src.orchestration.state import create_initial_state


class TestToolRunnerNode:
    """测试 ToolRunnerNode 基础功能"""

    def test_init_default_parameters(self, tmp_path):
        """测试默认参数初始化"""
        tool_runner = ToolRunnerNode(tmp_path)

        assert tool_runner.workspace == tmp_path.resolve()
        assert tool_runner.timeout == 30
        assert tool_runner.allow_dangerous_ops is False
        assert tmp_path.exists()

    def test_init_custom_parameters(self, tmp_path):
        """测试自定义参数初始化"""
        tool_runner = ToolRunnerNode(
            tmp_path,
            timeout=60,
            allow_dangerous_ops=True
        )

        assert tool_runner.workspace == tmp_path.resolve()
        assert tool_runner.timeout == 60
        assert tool_runner.allow_dangerous_ops is True

    def test_allowed_operations(self):
        """测试允许的操作清单"""
        assert "move_file" in ToolRunnerNode.ALLOWED_FILE_OPERATIONS
        assert "copy_file" in ToolRunnerNode.ALLOWED_FILE_OPERATIONS
        assert "delete_file" in ToolRunnerNode.ALLOWED_FILE_OPERATIONS
        assert "rename_file" in ToolRunnerNode.ALLOWED_FILE_OPERATIONS
        assert "create_directory" in ToolRunnerNode.ALLOWED_FILE_OPERATIONS
        assert "read_file" in ToolRunnerNode.ALLOWED_FILE_OPERATIONS
        assert "write_file" in ToolRunnerNode.ALLOWED_FILE_OPERATIONS

    def test_allowed_commands(self):
        """测试允许的系统命令清单"""
        assert "ls" in ToolRunnerNode.ALLOWED_COMMANDS
        assert "cat" in ToolRunnerNode.ALLOWED_COMMANDS
        assert "echo" in ToolRunnerNode.ALLOWED_COMMANDS
        # 危险命令不应在白名单中
        assert "rm" not in ToolRunnerNode.ALLOWED_COMMANDS
        assert "sudo" not in ToolRunnerNode.ALLOWED_COMMANDS


@pytest.mark.asyncio
class TestToolRunnerWorkflow:
    """测试 ToolRunner 工作流程"""

    async def test_run_tool_skip_non_tool_task(self, tmp_path):
        """测试跳过非工具任务"""
        tool_runner = ToolRunnerNode(tmp_path)

        state = create_initial_state("测试任务")
        state["plan"] = {
            "task": "测试任务",
            "subtasks": [{
                "id": 1,
                "type": "code",  # 非工具任务
                "description": "编写代码"
            }]
        }
        state["current_subtask_index"] = 0

        result_state = await tool_runner.run_tool(state)

        # 应该跳过并返回 planning 状态
        assert result_state["status"] == "planning"
        assert result_state["current_subtask_index"] == 1
        assert len(result_state["subtask_results"]) == 0

    async def test_run_tool_create_directory(self, tmp_path):
        """测试创建目录任务"""
        tool_runner = ToolRunnerNode(tmp_path)

        test_dir = tmp_path / "test_dir"
        state = create_initial_state("创建目录")
        state["plan"] = {
            "task": "创建目录",
            "subtasks": [{
                "id": 1,
                "type": "tool",
                "description": "创建测试目录",
                "tool_name": "create_directory",
                "tool_args": {"path": str(test_dir)}
            }]
        }
        state["current_subtask_index"] = 0

        result_state = await tool_runner.run_tool(state)

        # 验证结果
        assert result_state["status"] == "completed"
        assert result_state["current_subtask_index"] == 1
        assert len(result_state["subtask_results"]) == 1

        result = result_state["subtask_results"][0]
        assert result["subtask_id"] == 1
        assert result["passed"] is True
        assert "成功" in result["tool_result"]
        assert test_dir.exists()

    async def test_run_tool_write_and_read_file(self, tmp_path):
        """测试写入和读取文件任务"""
        tool_runner = ToolRunnerNode(tmp_path)

        test_file = tmp_path / "test.txt"
        test_content = "Hello, MacCortex!"

        # 写入文件
        state_write = create_initial_state("写入文件")
        state_write["plan"] = {
            "task": "写入文件",
            "subtasks": [{
                "id": 1,
                "type": "tool",
                "description": "写入测试文件",
                "tool_name": "write_file",
                "tool_args": {
                    "path": str(test_file),
                    "content": test_content
                }
            }]
        }
        state_write["current_subtask_index"] = 0

        result_write = await tool_runner.run_tool(state_write)

        # 验证写入结果
        assert result_write["subtask_results"][0]["passed"] is True
        assert test_file.exists()
        assert test_file.read_text() == test_content

        # 读取文件
        state_read = create_initial_state("读取文件")
        state_read["plan"] = {
            "task": "读取文件",
            "subtasks": [{
                "id": 2,
                "type": "tool",
                "description": "读取测试文件",
                "tool_name": "read_file",
                "tool_args": {"path": str(test_file)}
            }]
        }
        state_read["current_subtask_index"] = 0

        result_read = await tool_runner.run_tool(state_read)

        # 验证读取结果
        assert result_read["subtask_results"][0]["passed"] is True
        assert test_content in result_read["subtask_results"][0]["tool_result"]

    async def test_run_tool_handles_failure(self, tmp_path):
        """测试处理工具执行失败"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 尝试读取不存在的文件
        state = create_initial_state("读取失败")
        state["plan"] = {
            "task": "读取失败",
            "subtasks": [{
                "id": 1,
                "type": "tool",
                "description": "读取不存在的文件",
                "tool_name": "read_file",
                "tool_args": {"path": str(tmp_path / "nonexistent.txt")}
            }]
        }
        state["current_subtask_index"] = 0

        result_state = await tool_runner.run_tool(state)

        # 应该记录失败但不阻塞流程
        assert result_state["status"] == "completed"
        assert len(result_state["subtask_results"]) == 1
        result = result_state["subtask_results"][0]
        assert result["passed"] is False
        assert "错误" in result["error_message"] or "不存在" in result["error_message"]


@pytest.mark.asyncio
class TestFileOperations:
    """测试文件操作"""

    async def test_move_file(self, tmp_path):
        """测试移动文件"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 创建源文件
        src_file = tmp_path / "source.txt"
        src_file.write_text("test content")

        dst_file = tmp_path / "destination.txt"

        # 执行移动
        result = await tool_runner._execute_tool(
            "move_file",
            {"src": str(src_file), "dst": str(dst_file)}
        )

        assert "成功" in result
        assert not src_file.exists()
        assert dst_file.exists()
        assert dst_file.read_text() == "test content"

    async def test_copy_file(self, tmp_path):
        """测试复制文件"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 创建源文件
        src_file = tmp_path / "source.txt"
        src_file.write_text("test content")

        dst_file = tmp_path / "copy.txt"

        # 执行复制
        result = await tool_runner._execute_tool(
            "copy_file",
            {"src": str(src_file), "dst": str(dst_file)}
        )

        assert "成功" in result
        assert src_file.exists()  # 源文件仍存在
        assert dst_file.exists()
        assert dst_file.read_text() == "test content"

    async def test_delete_file_requires_permission(self, tmp_path):
        """测试删除文件需要权限"""
        tool_runner = ToolRunnerNode(tmp_path, allow_dangerous_ops=False)

        # 创建测试文件
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("test")

        # 尝试删除（应该失败）
        result = await tool_runner._execute_tool(
            "delete_file",
            {"path": str(test_file)}
        )

        assert "错误" in result
        assert "禁用" in result
        assert test_file.exists()  # 文件仍存在

    async def test_delete_file_with_permission(self, tmp_path):
        """测试有权限时删除文件"""
        tool_runner = ToolRunnerNode(tmp_path, allow_dangerous_ops=True)

        # 创建测试文件
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("test")

        # 执行删除（应该成功）
        result = await tool_runner._execute_tool(
            "delete_file",
            {"path": str(test_file)}
        )

        assert "成功" in result
        assert not test_file.exists()

    async def test_rename_file(self, tmp_path):
        """测试重命名文件"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 创建源文件
        old_file = tmp_path / "old_name.txt"
        old_file.write_text("test content")

        new_file = tmp_path / "new_name.txt"

        # 执行重命名
        result = await tool_runner._execute_tool(
            "rename_file",
            {"old_name": str(old_file), "new_name": str(new_file)}
        )

        assert "成功" in result
        assert not old_file.exists()
        assert new_file.exists()
        assert new_file.read_text() == "test content"

    async def test_create_directory(self, tmp_path):
        """测试创建目录"""
        tool_runner = ToolRunnerNode(tmp_path)

        test_dir = tmp_path / "subdir" / "nested"

        # 执行创建
        result = await tool_runner._execute_tool(
            "create_directory",
            {"path": str(test_dir)}
        )

        assert "成功" in result
        assert test_dir.exists()
        assert test_dir.is_dir()


@pytest.mark.asyncio
class TestWorkspaceSecurity:
    """测试 workspace 安全边界（异步测试）"""

    async def test_move_file_outside_workspace_fails(self, tmp_path):
        """测试移动文件到 workspace 外失败"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 创建源文件
        src_file = tmp_path / "test.txt"
        src_file.write_text("test")

        # 尝试移动到 workspace 外
        outside_path = "/tmp/outside.txt"

        result = await tool_runner._execute_tool(
            "move_file",
            {"src": str(src_file), "dst": outside_path}
        )

        assert "错误" in result
        assert "不在 workspace 内" in result
        assert src_file.exists()  # 文件未移动

    async def test_read_file_outside_workspace_fails(self, tmp_path):
        """测试读取 workspace 外文件失败"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 尝试读取 workspace 外的文件
        outside_file = "/etc/passwd"

        result = await tool_runner._execute_tool(
            "read_file",
            {"path": outside_file}
        )

        assert "错误" in result
        assert "不在 workspace 内" in result

    async def test_write_file_outside_workspace_fails(self, tmp_path):
        """测试写入 workspace 外文件失败"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 尝试写入 workspace 外
        outside_path = "/tmp/outside.txt"

        result = await tool_runner._execute_tool(
            "write_file",
            {"path": outside_path, "content": "test"}
        )

        assert "错误" in result
        assert "不在 workspace 内" in result


class TestWorkspaceSecuritySync:
    """测试 workspace 安全边界（同步测试）"""

    def test_is_within_workspace(self, tmp_path):
        """测试 workspace 边界检查"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 内部路径
        inside_path = tmp_path / "subdir" / "file.txt"
        assert tool_runner._is_within_workspace(inside_path) is True

        # 外部路径
        outside_path = Path("/tmp/outside.txt")
        assert tool_runner._is_within_workspace(outside_path) is False


@pytest.mark.asyncio
class TestSystemCommands:
    """测试系统命令执行"""

    async def test_run_allowed_command_ls(self, tmp_path):
        """测试执行允许的命令（ls）"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 创建测试文件
        (tmp_path / "test1.txt").write_text("test")
        (tmp_path / "test2.txt").write_text("test")

        # 执行 ls 命令
        result = await tool_runner._execute_tool(
            "run_command",
            {"command": "ls", "arguments": []}
        )

        assert "成功" in result
        assert "test1.txt" in result
        assert "test2.txt" in result

    async def test_run_allowed_command_echo(self, tmp_path):
        """测试执行允许的命令（echo）"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 执行 echo 命令
        result = await tool_runner._execute_tool(
            "run_command",
            {"command": "echo", "arguments": ["Hello, World!"]}
        )

        assert "成功" in result
        assert "Hello, World!" in result

    async def test_run_disallowed_command_fails(self, tmp_path):
        """测试执行禁止的命令失败"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 尝试执行不在白名单中的命令
        result = await tool_runner._execute_tool(
            "run_command",
            {"command": "rm", "arguments": ["-rf", "/"]}
        )

        assert "错误" in result
        assert "不在白名单中" in result

    async def test_run_command_timeout(self, tmp_path):
        """测试命令执行超时"""
        tool_runner = ToolRunnerNode(tmp_path, timeout=1)

        # 执行会超时的命令（sleep）
        # 注意：sleep 不在白名单中，所以会被拒绝
        result = await tool_runner._execute_tool(
            "run_command",
            {"command": "sleep", "arguments": ["10"]}
        )

        assert "错误" in result
        assert "不在白名单中" in result


@pytest.mark.asyncio
class TestErrorHandling:
    """测试错误处理"""

    async def test_execute_tool_missing_tool_name(self, tmp_path):
        """测试缺少工具名称"""
        tool_runner = ToolRunnerNode(tmp_path)

        result = await tool_runner._execute_tool("", {})

        assert "错误" in result
        assert "未指定工具名称" in result

    async def test_execute_tool_unsupported_tool(self, tmp_path):
        """测试不支持的工具"""
        tool_runner = ToolRunnerNode(tmp_path)

        result = await tool_runner._execute_tool("unsupported_tool", {})

        assert "不支持的工具" in result

    async def test_file_operation_missing_parameters(self, tmp_path):
        """测试文件操作缺少参数"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 移动文件缺少参数
        result = await tool_runner._execute_tool("move_file", {})

        assert "错误" in result
        assert "缺少" in result

    async def test_file_operation_nonexistent_file(self, tmp_path):
        """测试操作不存在的文件"""
        tool_runner = ToolRunnerNode(tmp_path)

        # 尝试移动不存在的文件
        result = await tool_runner._execute_tool(
            "move_file",
            {"src": str(tmp_path / "nonexistent.txt"), "dst": str(tmp_path / "dst.txt")}
        )

        assert "错误" in result
        assert "不存在" in result

    async def test_run_command_missing_command(self, tmp_path):
        """测试系统命令缺少命令名"""
        tool_runner = ToolRunnerNode(tmp_path)

        result = await tool_runner._execute_tool("run_command", {})

        assert "错误" in result
        assert "缺少 command 参数" in result


@pytest.mark.asyncio
class TestCreateToolRunnerNode:
    """测试工厂函数"""

    async def test_create_tool_runner_node_default(self, tmp_path):
        """测试创建默认 ToolRunner 节点"""
        node = create_tool_runner_node(tmp_path)

        assert callable(node)

    async def test_create_tool_runner_node_custom(self, tmp_path):
        """测试创建自定义 ToolRunner 节点"""
        node = create_tool_runner_node(
            tmp_path,
            timeout=60,
            allow_dangerous_ops=True
        )

        assert callable(node)

    async def test_tool_runner_node_function(self, tmp_path):
        """测试节点函数执行"""
        node = create_tool_runner_node(tmp_path)

        state = create_initial_state("测试任务")
        state["plan"] = {
            "task": "测试任务",
            "subtasks": [{
                "id": 1,
                "type": "tool",
                "description": "创建目录",
                "tool_name": "create_directory",
                "tool_args": {"path": str(tmp_path / "test_dir")}
            }]
        }
        state["current_subtask_index"] = 0

        result_state = await node(state)

        assert result_state["status"] == "completed"
        assert result_state["subtask_results"][0]["passed"] is True


@pytest.mark.asyncio
class TestMultipleSubtasks:
    """测试多个子任务"""

    async def test_multiple_tool_tasks(self, tmp_path):
        """测试执行多个工具任务"""
        tool_runner = ToolRunnerNode(tmp_path)

        state = create_initial_state("多任务")
        state["plan"] = {
            "task": "多任务",
            "subtasks": [
                {
                    "id": 1,
                    "type": "tool",
                    "description": "创建目录",
                    "tool_name": "create_directory",
                    "tool_args": {"path": str(tmp_path / "dir1")}
                },
                {
                    "id": 2,
                    "type": "tool",
                    "description": "写入文件",
                    "tool_name": "write_file",
                    "tool_args": {
                        "path": str(tmp_path / "file1.txt"),
                        "content": "test"
                    }
                },
                {
                    "id": 3,
                    "type": "tool",
                    "description": "创建另一个目录",
                    "tool_name": "create_directory",
                    "tool_args": {"path": str(tmp_path / "dir2")}
                }
            ]
        }
        state["current_subtask_index"] = 0

        # 执行第一个任务
        state = await tool_runner.run_tool(state)
        assert state["current_subtask_index"] == 1
        assert len(state["subtask_results"]) == 1

        # 执行第二个任务
        state = await tool_runner.run_tool(state)
        assert state["current_subtask_index"] == 2
        assert len(state["subtask_results"]) == 2

        # 执行第三个任务
        state = await tool_runner.run_tool(state)
        assert state["current_subtask_index"] == 3
        assert len(state["subtask_results"]) == 3
        assert state["status"] == "completed"

        # 验证所有任务都通过
        assert all(r["passed"] for r in state["subtask_results"])


@pytest.mark.asyncio
class TestEdgeCases:
    """测试边界情况"""

    async def test_empty_subtasks(self, tmp_path):
        """测试空子任务列表"""
        tool_runner = ToolRunnerNode(tmp_path)

        state = create_initial_state("空任务")
        state["plan"] = {"task": "空任务", "subtasks": []}
        state["current_subtask_index"] = 0

        result_state = await tool_runner.run_tool(state)

        assert result_state["status"] == "completed"
        assert len(result_state["subtask_results"]) == 0

    async def test_index_out_of_bounds(self, tmp_path):
        """测试索引越界"""
        tool_runner = ToolRunnerNode(tmp_path)

        state = create_initial_state("越界任务")
        state["plan"] = {
            "task": "越界任务",
            "subtasks": [
                {"id": 1, "type": "tool", "description": "任务1", "tool_name": "create_directory"}
            ]
        }
        state["current_subtask_index"] = 10  # 越界

        result_state = await tool_runner.run_tool(state)

        assert result_state["status"] == "completed"
        assert len(result_state["subtask_results"]) == 0

    async def test_missing_plan(self, tmp_path):
        """测试缺少计划"""
        tool_runner = ToolRunnerNode(tmp_path)

        state = create_initial_state("缺少计划")
        state["plan"] = None
        state["current_subtask_index"] = 0

        result_state = await tool_runner.run_tool(state)

        assert result_state["status"] == "completed"
        assert len(result_state["subtask_results"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
