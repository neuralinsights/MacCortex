"""
MacCortex Coder 测试

测试 CoderNode 代码生成功能，包括：
- 基础代码生成
- 多语言支持
- 反馈修复
- 文件写入
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

from src.orchestration.nodes.coder import CoderNode
from src.orchestration.state import create_initial_state


class TestCoderInitialization:
    """测试 Coder 初始化"""

    def test_init_without_api_key_fallback_disabled(self, monkeypatch):
        """测试缺少 API 密钥且禁用降级时抛出异常"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="未设置 ANTHROPIC_API_KEY"):
                CoderNode(Path(tmpdir), fallback_to_local=False)

    def test_init_without_api_key_fallback_enabled(self, monkeypatch):
        """测试缺少 API 密钥时降级到本地 Ollama 模型"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir), fallback_to_local=True)

            assert coder.workspace == Path(tmpdir)
            assert coder.workspace.exists()
            assert coder.llm is not None
            assert coder.using_local_model is True

    def test_init_with_api_key(self, monkeypatch):
        """测试成功初始化"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            assert coder.workspace == Path(tmpdir)
            assert coder.workspace.exists()
            assert coder.llm is not None

    def test_init_creates_workspace(self, monkeypatch):
        """测试自动创建工作空间目录"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "non_existent_dir"
            assert not workspace.exists()

            coder = CoderNode(workspace)

            assert workspace.exists()
            assert workspace.is_dir()


class TestCodeExtraction:
    """测试代码提取功能"""

    def test_extract_python_code(self, monkeypatch):
        """测试提取 Python 代码块"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            content = """这是一些解释文字

```python
def hello():
    print("Hello, World!")

hello()
```

更多说明
"""
            code, language = coder._extract_code(content)

            assert "def hello()" in code
            assert 'print("Hello, World!")' in code
            assert language == "python"

    def test_extract_swift_code(self, monkeypatch):
        """测试提取 Swift 代码块"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            content = """```swift
import Foundation

print("Hello from Swift!")
```"""
            code, language = coder._extract_code(content)

            assert "import Foundation" in code
            assert language == "swift"

    def test_extract_bash_code(self, monkeypatch):
        """测试提取 Bash 代码块"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            content = """```bash
#!/bin/bash
echo "Hello from Bash!"
```"""
            code, language = coder._extract_code(content)

            assert "#!/bin/bash" in code
            assert language == "bash"

    def test_extract_code_without_language_tag(self, monkeypatch):
        """测试提取没有语言标签的代码块"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            content = """```
def test():
    pass
```"""
            code, language = coder._extract_code(content)

            assert "def test()" in code
            assert language == "python"  # 默认为 Python

    def test_extract_code_plain_text(self, monkeypatch):
        """测试提取纯文本（无代码块标记）"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            content = """def plain_code():
    return True"""
            code, language = coder._extract_code(content)

            assert "def plain_code()" in code
            assert language == "python"


class TestFileExtensions:
    """测试文件扩展名推断"""

    def test_get_python_extension(self, monkeypatch):
        """测试 Python 扩展名"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            assert coder._get_extension("python") == ".py"
            assert coder._get_extension("PYTHON") == ".py"

    def test_get_swift_extension(self, monkeypatch):
        """测试 Swift 扩展名"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            assert coder._get_extension("swift") == ".swift"

    def test_get_bash_extension(self, monkeypatch):
        """测试 Bash 扩展名"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            assert coder._get_extension("bash") == ".sh"
            assert coder._get_extension("shell") == ".sh"

    def test_get_unknown_extension(self, monkeypatch):
        """测试未知语言的扩展名"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            assert coder._get_extension("unknown") == ".txt"


class TestPromptBuilding:
    """测试提示词构建"""

    def test_build_initial_prompt(self, monkeypatch):
        """测试首次生成的提示词"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            subtask = {
                "id": "task-1",
                "type": "code",
                "description": "编写一个计算器",
                "dependencies": [],
                "acceptance_criteria": [
                    "支持加减乘除",
                    "有错误处理"
                ]
            }

            prompt = coder._build_user_prompt(subtask, "", "")

            assert "编写一个计算器" in prompt
            assert "支持加减乘除" in prompt
            assert "有错误处理" in prompt
            assert "验收标准" in prompt

    def test_build_feedback_prompt(self, monkeypatch):
        """测试包含反馈的提示词"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            subtask = {
                "id": "task-1",
                "type": "code",
                "description": "编写一个计算器",
                "dependencies": [],
                "acceptance_criteria": ["支持加减乘除"]
            }

            feedback = "缺少除零检查"
            previous_code = "def divide(a, b): return a / b"

            prompt = coder._build_user_prompt(subtask, feedback, previous_code)

            assert "缺少除零检查" in prompt
            assert "之前的代码" in prompt
            assert "def divide" in prompt
            assert "审查反馈" in prompt


@pytest.mark.asyncio
class TestCodeGeneration:
    """测试代码生成功能"""

    async def test_code_generation_success(self, monkeypatch):
        """测试成功生成代码"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # Mock LLM 响应
            mock_response = MagicMock()
            mock_response.content = """```python
#!/usr/bin/env python3

def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
```"""

            with patch('langchain_anthropic.ChatAnthropic.ainvoke', new_callable=AsyncMock) as mock_ainvoke:
                mock_ainvoke.return_value = mock_response

                coder = CoderNode(workspace)

                # 创建测试状态
                state = create_initial_state("写一个 Hello World 程序")
                state["plan"] = {
                    "subtasks": [
                        {
                            "id": "task-1",
                            "type": "code",
                            "description": "编写 Hello World",
                            "dependencies": [],
                            "acceptance_criteria": ["打印 Hello, World!"]
                        }
                    ],
                    "overall_acceptance": ["程序能运行"]
                }
                state["current_subtask_index"] = 0

                # 生成代码
                result_state = await coder.code(state)

                # 验证状态更新
                assert result_state["current_code"] is not None
                assert "def hello()" in result_state["current_code"]
                assert result_state["current_code_file"] is not None
                assert result_state["status"] == "reviewing"
                assert result_state["review_feedback"] == ""

                # 验证文件已创建
                code_file = Path(result_state["current_code_file"])
                assert code_file.exists()
                assert code_file.suffix == ".py"

    async def test_code_generation_with_feedback(self, monkeypatch):
        """测试根据反馈修复代码"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # Mock LLM 响应（修复后的代码）
            mock_response = MagicMock()
            mock_response.content = """```python
def divide(a, b):
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b
```"""

            with patch('langchain_anthropic.ChatAnthropic.ainvoke', new_callable=AsyncMock) as mock_ainvoke:
                mock_ainvoke.return_value = mock_response

                coder = CoderNode(workspace)

                # 创建包含反馈的状态
                state = create_initial_state("实现除法函数")
                state["plan"] = {
                    "subtasks": [
                        {
                            "id": "task-1",
                            "type": "code",
                            "description": "实现安全的除法函数",
                            "dependencies": [],
                            "acceptance_criteria": ["有除零检查"]
                        }
                    ],
                    "overall_acceptance": ["函数能安全运行"]
                }
                state["current_subtask_index"] = 0
                state["review_feedback"] = "缺少除零检查"
                state["current_code"] = "def divide(a, b): return a / b"

                # 生成修复后的代码
                result_state = await coder.code(state)

                # 验证修复
                assert "if b == 0" in result_state["current_code"]
                assert "raise ValueError" in result_state["current_code"]
                assert result_state["review_feedback"] == ""  # 反馈已清空

    async def test_code_generation_missing_plan(self, monkeypatch):
        """测试缺少 plan 时抛出异常"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            coder = CoderNode(workspace)

            state = create_initial_state("测试任务")
            state["plan"] = None

            with pytest.raises(ValueError, match="缺少 plan 字段"):
                await coder.code(state)

    async def test_code_generation_index_out_of_bounds(self, monkeypatch):
        """测试子任务索引越界"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            coder = CoderNode(workspace)

            state = create_initial_state("测试任务")
            state["plan"] = {
                "subtasks": [
                    {
                        "id": "task-1",
                        "type": "code",
                        "description": "任务1",
                        "dependencies": [],
                        "acceptance_criteria": ["标准1"]
                    }
                ],
                "overall_acceptance": ["完成"]
            }
            state["current_subtask_index"] = 999  # 越界

            with pytest.raises(ValueError, match="子任务索引越界"):
                await coder.code(state)

    async def test_code_generation_swift(self, monkeypatch):
        """测试生成 Swift 代码"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # Mock LLM 响应（Swift 代码）
            mock_response = MagicMock()
            mock_response.content = """```swift
import Foundation

func hello() {
    print("Hello from Swift!")
}

hello()
```"""

            with patch('langchain_anthropic.ChatAnthropic.ainvoke', new_callable=AsyncMock) as mock_ainvoke:
                mock_ainvoke.return_value = mock_response

                coder = CoderNode(workspace)

                state = create_initial_state("写一个 Swift Hello World")
                state["plan"] = {
                    "subtasks": [
                        {
                            "id": "task-1",
                            "type": "code",
                            "description": "编写 Swift Hello World",
                            "dependencies": [],
                            "acceptance_criteria": ["使用 Swift"]
                        }
                    ],
                    "overall_acceptance": ["程序能运行"]
                }
                state["current_subtask_index"] = 0

                result_state = await coder.code(state)

                # 验证 Swift 文件
                code_file = Path(result_state["current_code_file"])
                assert code_file.suffix == ".swift"
                assert "import Foundation" in result_state["current_code"]

    async def test_code_generation_bash_executable(self, monkeypatch):
        """测试生成 Bash 脚本并设置执行权限"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            # Mock LLM 响应（Bash 脚本）
            mock_response = MagicMock()
            mock_response.content = """```bash
#!/bin/bash
echo "Hello from Bash!"
```"""

            with patch('langchain_anthropic.ChatAnthropic.ainvoke', new_callable=AsyncMock) as mock_ainvoke:
                mock_ainvoke.return_value = mock_response

                coder = CoderNode(workspace)

                state = create_initial_state("写一个 Bash 脚本")
                state["plan"] = {
                    "subtasks": [
                        {
                            "id": "task-1",
                            "type": "code",
                            "description": "编写 Bash Hello World",
                            "dependencies": [],
                            "acceptance_criteria": ["使用 Bash"]
                        }
                    ],
                    "overall_acceptance": ["脚本能运行"]
                }
                state["current_subtask_index"] = 0

                result_state = await coder.code(state)

                # 验证 Bash 脚本
                code_file = Path(result_state["current_code_file"])
                assert code_file.suffix == ".sh"
                assert "#!/bin/bash" in result_state["current_code"]

                # 验证执行权限（在 Unix 系统上）
                if os.name != 'nt':  # 不是 Windows
                    assert os.access(code_file, os.X_OK)


class TestUtilityMethods:
    """测试工具方法"""

    def test_get_generated_files(self, monkeypatch):
        """测试获取生成的文件列表"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()

            coder = CoderNode(workspace)

            # 创建一些测试文件
            (workspace / "subtask_task-1.py").write_text("# Task 1")
            (workspace / "subtask_task-2.py").write_text("# Task 2")
            (workspace / "other_file.txt").write_text("Other")

            files = coder.get_generated_files()

            # 应该只返回 subtask_* 文件
            assert len(files) == 2
            assert all("subtask_" in f.name for f in files)

    def test_format_acceptance_criteria(self, monkeypatch):
        """测试验收标准格式化"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(Path(tmpdir))

            criteria = ["标准1", "标准2", "标准3"]
            formatted = coder._format_acceptance_criteria(criteria)

            assert "1. 标准1" in formatted
            assert "2. 标准2" in formatted
            assert "3. 标准3" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
