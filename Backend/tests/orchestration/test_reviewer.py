"""
MacCortex Reviewer 测试

测试 ReviewerNode 代码审查功能，包括：
- 代码执行（subprocess）
- 输出捕获（stdout/stderr）
- LLM 审查
- 反馈生成
- Coder ↔ Reviewer 循环
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

from src.orchestration.nodes.reviewer import ReviewerNode
from src.orchestration.state import create_initial_state


class TestReviewerInitialization:
    """测试 Reviewer 初始化"""

    def test_init_without_api_key(self, monkeypatch):
        """测试缺少 API 密钥时抛出异常"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="未设置 ANTHROPIC_API_KEY"):
                ReviewerNode(Path(tmpdir))

    def test_init_with_api_key(self, monkeypatch):
        """测试成功初始化"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            reviewer = ReviewerNode(Path(tmpdir))

            assert reviewer.workspace == Path(tmpdir)
            assert reviewer.llm is not None
            assert reviewer.timeout == 30
            assert reviewer.max_iterations == 3

    def test_init_custom_parameters(self, monkeypatch):
        """测试自定义参数"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            reviewer = ReviewerNode(
                Path(tmpdir),
                timeout=60,
                max_iterations=5
            )

            assert reviewer.timeout == 60
            assert reviewer.max_iterations == 5


class TestCodeExecution:
    """测试代码执行功能"""

    def test_run_python_success(self, monkeypatch):
        """测试成功执行 Python 代码"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # 创建测试代码文件
            code_file = workspace / "test.py"
            code_file.write_text("""#!/usr/bin/env python3
print("Hello, World!")
""")

            reviewer = ReviewerNode(workspace)

            success, output, error = reviewer._run_code(code_file)

            assert success is True
            assert "Hello, World!" in output
            assert error == ""

    def test_run_python_with_error(self, monkeypatch):
        """测试执行有错误的 Python 代码"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # 创建有错误的代码
            code_file = workspace / "test.py"
            code_file.write_text("""#!/usr/bin/env python3
def divide(a, b):
    return a / b

print(divide(10, 0))
""")

            reviewer = ReviewerNode(workspace)

            success, output, error = reviewer._run_code(code_file)

            assert success is False
            assert "ZeroDivisionError" in error or "division by zero" in error.lower()

    def test_run_python_timeout(self, monkeypatch):
        """测试代码执行超时"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # 创建会超时的代码
            code_file = workspace / "test.py"
            code_file.write_text("""#!/usr/bin/env python3
import time
time.sleep(100)
""")

            reviewer = ReviewerNode(workspace, timeout=1)  # 1 秒超时

            success, output, error = reviewer._run_code(code_file)

            assert success is False
            assert "超时" in error

    def test_run_code_file_not_found(self, monkeypatch):
        """测试文件不存在时的错误处理"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            reviewer = ReviewerNode(workspace)

            code_file = workspace / "nonexistent.py"

            success, output, error = reviewer._run_code(code_file)

            assert success is False
            assert error != ""

    def test_get_interpreter_python(self, monkeypatch):
        """测试 Python 解释器识别"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            reviewer = ReviewerNode(Path(tmpdir))

            interpreter = reviewer._get_interpreter(Path("test.py"))

            assert interpreter == [sys.executable]

    def test_get_interpreter_bash(self, monkeypatch):
        """测试 Bash 解释器识别"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            reviewer = ReviewerNode(Path(tmpdir))

            interpreter = reviewer._get_interpreter(Path("test.sh"))

            assert interpreter == ["/bin/bash"]


class TestJSONParsing:
    """测试 JSON 解析功能"""

    def test_parse_review_result_with_code_block(self, monkeypatch):
        """测试解析包含代码块的 JSON"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            reviewer = ReviewerNode(Path(tmpdir))

            content = """```json
{
  "passed": true,
  "feedback": "代码成功运行"
}
```"""

            result = reviewer._parse_review_result(content)

            assert result["passed"] is True
            assert "成功" in result["feedback"]

    def test_parse_review_result_plain_json(self, monkeypatch):
        """测试解析纯 JSON"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            reviewer = ReviewerNode(Path(tmpdir))

            content = '{"passed": false, "feedback": "缺少错误处理"}'

            result = reviewer._parse_review_result(content)

            assert result["passed"] is False
            assert "错误处理" in result["feedback"]

    def test_parse_review_result_invalid_json(self, monkeypatch):
        """测试解析无效 JSON"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            reviewer = ReviewerNode(Path(tmpdir))

            content = "This is not valid JSON at all"

            result = reviewer._parse_review_result(content)

            # 应该返回保守结果（标记为失败）
            assert result["passed"] is False
            assert "解析失败" in result["feedback"]

    def test_parse_review_result_missing_passed(self, monkeypatch):
        """测试缺少 passed 字段"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            reviewer = ReviewerNode(Path(tmpdir))

            content = '{"feedback": "Some feedback"}'

            result = reviewer._parse_review_result(content)

            # 应该返回失败
            assert result["passed"] is False


@pytest.mark.asyncio
class TestReview:
    """测试审查主流程"""

    async def test_review_success(self, monkeypatch):
        """测试审查通过的情况"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # 创建测试代码文件
            code_file = workspace / "subtask_task-1.py"
            code_file.write_text("""#!/usr/bin/env python3
print("Hello, World!")
""")

            # Mock LLM 响应（审查通过）
            mock_response = MagicMock()
            mock_response.content = """```json
{
  "passed": true,
  "feedback": "代码成功运行，输出符合预期"
}
```"""

            with patch('langchain_anthropic.ChatAnthropic.ainvoke', new_callable=AsyncMock) as mock_ainvoke:
                mock_ainvoke.return_value = mock_response

                reviewer = ReviewerNode(workspace)

                # 创建测试状态
                state = create_initial_state("Hello World 程序")
                state["plan"] = {
                    "subtasks": [
                        {
                            "id": "task-1",
                            "type": "code",
                            "description": "打印 Hello World",
                            "dependencies": [],
                            "acceptance_criteria": ["输出包含 Hello, World!"]
                        }
                    ],
                    "overall_acceptance": ["程序能运行"]
                }
                state["current_subtask_index"] = 0
                state["current_code"] = code_file.read_text()
                state["current_code_file"] = str(code_file)

                # 执行审查
                result_state = await reviewer.review(state)

                # 验证状态更新
                assert len(result_state["subtask_results"]) == 1
                assert result_state["subtask_results"][0]["passed"] is True
                assert result_state["subtask_results"][0]["subtask_id"] == "task-1"
                assert result_state["current_subtask_index"] == 1
                assert result_state["status"] == "completed"  # 所有子任务完成
                assert result_state["review_feedback"] == ""

    async def test_review_failure(self, monkeypatch):
        """测试审查失败的情况"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # 创建有问题的代码
            code_file = workspace / "subtask_task-1.py"
            code_file.write_text("""#!/usr/bin/env python3
def divide(a, b):
    return a / b

print(divide(10, 0))
""")

            # Mock LLM 响应（审查失败）
            mock_response = MagicMock()
            mock_response.content = """```json
{
  "passed": false,
  "feedback": "代码在第 5 行抛出 ZeroDivisionError。修复方案：添加除零检查。"
}
```"""

            with patch('langchain_anthropic.ChatAnthropic.ainvoke', new_callable=AsyncMock) as mock_ainvoke:
                mock_ainvoke.return_value = mock_response

                reviewer = ReviewerNode(workspace)

                # 创建测试状态
                state = create_initial_state("除法函数")
                state["plan"] = {
                    "subtasks": [
                        {
                            "id": "task-1",
                            "type": "code",
                            "description": "实现除法函数",
                            "dependencies": [],
                            "acceptance_criteria": ["有除零检查"]
                        }
                    ],
                    "overall_acceptance": ["函数安全"]
                }
                state["current_subtask_index"] = 0
                state["current_code"] = code_file.read_text()
                state["current_code_file"] = str(code_file)

                # 执行审查
                result_state = await reviewer.review(state)

                # 验证状态更新
                assert len(result_state["subtask_results"]) == 0  # 没有成功的结果
                assert result_state["review_feedback"] != ""
                assert "ZeroDivisionError" in result_state["review_feedback"]
                assert result_state["status"] == "executing"  # 回到 Coder
                assert result_state["iteration_count"] == 1
                assert result_state["current_subtask_index"] == 0  # 仍在第一个子任务

    async def test_review_max_iterations(self, monkeypatch):
        """测试超过最大迭代次数"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            code_file = workspace / "subtask_task-1.py"
            code_file.write_text("print('test')")

            reviewer = ReviewerNode(workspace, max_iterations=2)

            # 创建已经迭代过 2 次的状态
            state = create_initial_state("测试任务")
            state["plan"] = {
                "subtasks": [
                    {
                        "id": "task-1",
                        "type": "code",
                        "description": "测试",
                        "dependencies": [],
                        "acceptance_criteria": ["测试"]
                    }
                ],
                "overall_acceptance": ["完成"]
            }
            state["current_subtask_index"] = 0
            state["current_code"] = code_file.read_text()
            state["current_code_file"] = str(code_file)
            state["iteration_count"] = 2  # 已经迭代 2 次

            # 执行审查（应该强制标记为失败）
            result_state = await reviewer.review(state)

            # 验证强制失败
            assert len(result_state["subtask_results"]) == 1
            assert result_state["subtask_results"][0]["passed"] is False
            assert "超过最大迭代次数" in result_state["subtask_results"][0]["error_message"]
            assert result_state["current_subtask_index"] == 1
            assert result_state["status"] == "planning"
            assert "超过最大迭代次数" in result_state["error_message"]

    async def test_review_missing_plan(self, monkeypatch):
        """测试缺少 plan 时抛出异常"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            reviewer = ReviewerNode(workspace)

            state = create_initial_state("测试任务")
            state["plan"] = None

            with pytest.raises(ValueError, match="缺少 plan 字段"):
                await reviewer.review(state)

    async def test_review_file_not_found(self, monkeypatch):
        """测试代码文件不存在"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            reviewer = ReviewerNode(workspace)

            state = create_initial_state("测试任务")
            state["plan"] = {
                "subtasks": [
                    {
                        "id": "task-1",
                        "type": "code",
                        "description": "测试",
                        "dependencies": [],
                        "acceptance_criteria": ["测试"]
                    }
                ],
                "overall_acceptance": ["完成"]
            }
            state["current_subtask_index"] = 0
            state["current_code"] = "print('test')"
            state["current_code_file"] = str(workspace / "nonexistent.py")

            with pytest.raises(FileNotFoundError, match="代码文件不存在"):
                await reviewer.review(state)

    async def test_review_multiple_subtasks(self, monkeypatch):
        """测试多个子任务的审查流程"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # 创建第一个子任务的代码
            code_file1 = workspace / "subtask_task-1.py"
            code_file1.write_text("print('Task 1')")

            # Mock LLM 响应
            mock_response = MagicMock()
            mock_response.content = '{"passed": true, "feedback": "通过"}'

            with patch('langchain_anthropic.ChatAnthropic.ainvoke', new_callable=AsyncMock) as mock_ainvoke:
                mock_ainvoke.return_value = mock_response

                reviewer = ReviewerNode(workspace)

                # 创建包含 2 个子任务的状态
                state = create_initial_state("多任务测试")
                state["plan"] = {
                    "subtasks": [
                        {
                            "id": "task-1",
                            "type": "code",
                            "description": "任务 1",
                            "dependencies": [],
                            "acceptance_criteria": ["测试 1"]
                        },
                        {
                            "id": "task-2",
                            "type": "code",
                            "description": "任务 2",
                            "dependencies": ["task-1"],
                            "acceptance_criteria": ["测试 2"]
                        }
                    ],
                    "overall_acceptance": ["完成"]
                }
                state["current_subtask_index"] = 0
                state["current_code"] = code_file1.read_text()
                state["current_code_file"] = str(code_file1)

                # 执行第一个子任务的审查
                result_state = await reviewer.review(state)

                # 验证进入下一个子任务
                assert result_state["current_subtask_index"] == 1
                assert result_state["status"] == "planning"  # 不是 completed，还有子任务
                assert len(result_state["subtask_results"]) == 1


class TestUtilityMethods:
    """测试工具方法"""

    def test_format_acceptance_criteria(self, monkeypatch):
        """测试验收标准格式化"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            reviewer = ReviewerNode(Path(tmpdir))

            criteria = ["标准1", "标准2", "标准3"]
            formatted = reviewer._format_acceptance_criteria(criteria)

            assert "1. 标准1" in formatted
            assert "2. 标准2" in formatted
            assert "3. 标准3" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
