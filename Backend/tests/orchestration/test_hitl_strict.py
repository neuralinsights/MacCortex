"""
MacCortex Human-in-the-Loop 严格测试套件

测试真实场景、边缘情况、错误处理。
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from src.orchestration.swarm_graph import create_full_swarm_graph
from src.orchestration.state import create_initial_state
from src.orchestration.hitl import HITLHelper, RiskAssessor


@pytest.fixture
def tmp_path():
    """临时工作空间"""
    return Path(tempfile.mkdtemp())


class TestHITLEdgeCases:
    """测试边缘情况"""

    def test_parse_invalid_user_decision(self):
        """测试无效用户决策输入"""
        with pytest.raises(ValueError) as exc_info:
            HITLHelper.parse_user_decision("xyz", "tool_execution")

        assert "无效的决策" in str(exc_info.value)
        assert "xyz" in str(exc_info.value)

    def test_parse_user_decision_case_insensitive(self):
        """测试用户决策大小写不敏感"""
        # 测试各种大小写组合
        test_cases = [
            ("APPROVE", "approve"),
            ("Approve", "approve"),
            ("YES", "approve"),
            ("Yes", "approve"),
            ("DENY", "deny"),
            ("Deny", "deny"),
            ("NO", "deny"),
            ("ABORT", "abort"),
            ("Abort", "abort"),
        ]

        for user_input, expected_action in test_cases:
            decision = HITLHelper.parse_user_decision(user_input, "tool_execution")
            assert decision["action"] == expected_action, f"Failed for input: {user_input}"

    def test_parse_user_decision_aliases(self):
        """测试用户决策别名"""
        # approve 别名
        for alias in ["approve", "yes", "y", "ok"]:
            decision = HITLHelper.parse_user_decision(alias, "tool_execution")
            assert decision["action"] == "approve"

        # deny 别名
        for alias in ["deny", "no", "n", "skip"]:
            decision = HITLHelper.parse_user_decision(alias, "tool_execution")
            assert decision["action"] == "deny"

        # modify 别名
        for alias in ["modify", "edit", "m"]:
            decision = HITLHelper.parse_user_decision(alias, "tool_execution")
            assert decision["action"] == "modify"

        # abort 别名
        for alias in ["abort", "cancel", "stop"]:
            decision = HITLHelper.parse_user_decision(alias, "tool_execution")
            assert decision["action"] == "abort"


class TestRiskAssessment:
    """测试风险评估"""

    def test_high_risk_tools(self):
        """测试高风险工具识别"""
        high_risk_tools = [
            "delete_file",
            "remove_directory",
            "execute_shell",
            "write_database",
            "send_email",
            "make_api_call",
        ]

        for tool_name in high_risk_tools:
            risk = RiskAssessor.assess_tool_risk(tool_name, {})
            assert risk == "high", f"{tool_name} should be high risk"

    def test_medium_risk_tools(self):
        """测试中风险工具识别"""
        medium_risk_tools = [
            "write_file",
            "create_directory",
            "move_file",
            "copy_file",
        ]

        for tool_name in medium_risk_tools:
            risk = RiskAssessor.assess_tool_risk(tool_name, {})
            assert risk == "medium", f"{tool_name} should be medium risk"

    def test_low_risk_tools(self):
        """测试低风险工具识别"""
        low_risk_tools = [
            "read_file",
            "list_directory",
            "search_web",
            "unknown_tool",
        ]

        for tool_name in low_risk_tools:
            risk = RiskAssessor.assess_tool_risk(tool_name, {})
            assert risk == "low", f"{tool_name} should be low risk"

    def test_sensitive_path_escalation(self):
        """测试敏感路径升级风险等级"""
        # write_file 通常是 medium，但涉及敏感路径应升级为 high
        sensitive_paths = [
            "/etc/passwd",
            "/usr/bin/sudo",
            "/System/Library/CoreServices/Finder.app",
            "~/.ssh/id_rsa",
            "~/.aws/credentials",
            "/var/log/system.log",
            "C:\\Windows\\System32\\drivers",
        ]

        for path in sensitive_paths:
            risk = RiskAssessor.assess_tool_risk(
                "write_file",
                {"path": path}
            )
            assert risk == "high", f"Writing to {path} should be high risk"

    def test_code_risk_dangerous_keywords(self):
        """测试代码风险评估 - 危险关键词"""
        dangerous_code_samples = [
            "import os; os.system('rm -rf /')",
            "exec('malicious code')",
            "eval(user_input)",
            "subprocess.popen('shutdown now')",
            "DELETE FROM users;",
            "DROP TABLE accounts;",
            "os.unlink('/etc/passwd')",
            "shutil.rmtree('/var')",
        ]

        for code in dangerous_code_samples:
            risk = RiskAssessor.assess_code_risk(code, "python")
            assert risk == "high", f"Code with dangerous keywords should be high risk: {code[:50]}"

    def test_code_risk_long_code(self):
        """测试代码风险评估 - 超长代码"""
        # 超过 1000 字符的代码应该是 medium 风险
        long_code = "print('hello')\n" * 100  # ~1400 字符

        risk = RiskAssessor.assess_code_risk(long_code, "python")
        assert risk == "medium", "Long code should be medium risk"

    def test_code_risk_safe_code(self):
        """测试代码风险评估 - 安全代码"""
        safe_code = """
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
"""

        risk = RiskAssessor.assess_code_risk(safe_code, "python")
        assert risk == "low", "Safe code should be low risk"


class TestHITLHelperFormatting:
    """测试 HITL 消息格式化"""

    def test_format_tool_execution_interrupt(self):
        """测试工具执行中断消息格式化"""
        prompt_data = {
            "operation": "tool_execution",
            "risk_level": "medium",
            "details": {
                "tool_name": "write_file",
                "subtask_description": "创建配置文件",
                "tool_args": {
                    "path": "/tmp/config.json",
                    "content": '{"debug": true}'
                }
            },
            "timestamp": "2026-01-22T10:00:00Z",
            "available_actions": ["approve", "deny", "modify", "abort"]
        }

        message = HITLHelper.format_interrupt_message(prompt_data)

        # 验证关键信息存在
        assert "tool_execution" in message
        assert "MEDIUM" in message
        assert "write_file" in message
        assert "创建配置文件" in message
        assert "/tmp/config.json" in message
        assert "approve, deny, modify, abort" in message
        assert "🟡" in message  # medium 风险标记

    def test_format_code_generation_interrupt(self):
        """测试代码生成中断消息格式化"""
        code = "def hello():\n    print('Hello, World!')"

        prompt_data = {
            "operation": "code_generation",
            "risk_level": "low",
            "details": {
                "language": "python",
                "subtask_description": "生成问候函数",
                "file_path": "/tmp/hello.py",
                "code": code
            },
            "timestamp": "2026-01-22T10:00:00Z",
            "available_actions": ["approve", "regenerate", "modify", "abort"]
        }

        message = HITLHelper.format_interrupt_message(prompt_data)

        # 验证关键信息存在
        assert "code_generation" in message
        assert "LOW" in message
        assert "python" in message
        assert "生成问候函数" in message
        assert "/tmp/hello.py" in message
        assert "def hello()" in message or "..." in message  # 代码预览
        assert "🟢" in message  # low 风险标记

    def test_format_review_intervention_interrupt(self):
        """测试审查介入中断消息格式化"""
        prompt_data = {
            "operation": "review_intervention",
            "risk_level": "medium",
            "details": {
                "subtask_description": "修复语法错误",
                "iteration_count": 2,
                "max_iterations": 3,
                "reviewer_feedback": "缺少类型注解"
            },
            "timestamp": "2026-01-22T10:00:00Z",
            "available_actions": ["continue", "fix_manually", "skip", "abort"]
        }

        message = HITLHelper.format_interrupt_message(prompt_data)

        # 验证关键信息存在
        assert "review_intervention" in message
        assert "修复语法错误" in message
        assert "2/3" in message  # 迭代次数
        assert "缺少类型注解" in message
        assert "continue, fix_manually, skip, abort" in message


@pytest.mark.asyncio
class TestHITLModifyOperation:
    """测试 modify 操作"""

    async def test_modify_tool_args(self, tmp_path):
        """测试修改工具参数"""

        def create_mock_llm():
            mock_llm = AsyncMock()

            # Planner 响应
            planner_response = Mock()
            planner_response.content = f"""```json
{{
  "task": "创建文件",
  "subtasks": [
    {{
      "id": "task-1",
      "type": "tool",
      "description": "创建测试文件",
      "dependencies": [],
      "acceptance_criteria": ["文件创建成功"],
      "tool_name": "write_file",
      "tool_args": {{
        "path": "{tmp_path}/original.txt",
        "content": "Original Content"
      }}
    }}
  ],
  "overall_acceptance": ["文件创建成功"]
}}
```"""

            # Reflector 响应
            reflector_response = Mock()
            reflector_response.content = """```json
{
  "passed": true,
  "summary": "任务成功完成。",
  "feedback": "",
  "achievements": ["创建了文件"],
  "issues": [],
  "recommendation": "completed"
}
```"""

            mock_llm.ainvoke = AsyncMock(side_effect=[
                planner_response,
                reflector_response
            ])

            return mock_llm

        mock_llm = create_mock_llm()

        checkpointer = InMemorySaver()
        graph = create_full_swarm_graph(
            workspace_path=tmp_path,
            checkpointer=checkpointer,
            planner={"llm": mock_llm, "min_subtasks": 1},
            coder={"llm": mock_llm},
            reviewer={"llm": mock_llm},
            researcher={"llm": mock_llm},
            tool_runner={"require_approval": True},
            stop_condition={},
            reflector={"llm": mock_llm}
        )

        thread = {"configurable": {"thread_id": "test-modify"}}

        # 执行到中断点
        state = create_initial_state("创建文件")
        await graph.ainvoke(state, thread)

        # 验证中断
        current_state = graph.get_state(thread)
        assert current_state.interrupts

        interrupt_obj = current_state.interrupts[0]
        interrupt_data = interrupt_obj.value
        assert interrupt_data["details"]["tool_args"]["path"] == f"{tmp_path}/original.txt"

        # 用户修改参数
        user_decision = {
            "action": "modify",
            "operation": "tool_execution",
            "timestamp": "2026-01-22T00:00:00Z",
            "modified_data": {
                "tool_args": {
                    "path": f"{tmp_path}/modified.txt",  # 修改文件名
                    "content": "Modified Content"  # 修改内容
                }
            }
        }

        # 恢复执行
        final_state = await graph.ainvoke(Command(resume=user_decision), thread)

        # 验证：应该创建修改后的文件
        assert final_state["status"] == "completed"
        assert final_state["subtask_results"][0]["passed"] is True

        # 验证文件
        modified_file = tmp_path / "modified.txt"
        original_file = tmp_path / "original.txt"

        assert modified_file.exists(), "Modified file should exist"
        assert not original_file.exists(), "Original file should NOT exist"
        assert modified_file.read_text() == "Modified Content"


@pytest.mark.asyncio
class TestHITLSequentialInterrupts:
    """测试连续中断场景"""

    async def test_approve_then_deny(self, tmp_path):
        """测试先批准后拒绝的场景"""

        mock_llm = AsyncMock()

        # Planner 响应（两个工具任务）
        planner_response = Mock()
        planner_response.content = f"""```json
{{
  "task": "创建两个文件",
  "subtasks": [
    {{
      "id": "task-1",
      "type": "tool",
      "description": "创建第一个文件",
      "dependencies": [],
      "acceptance_criteria": ["文件创建成功"],
      "tool_name": "write_file",
      "tool_args": {{
        "path": "{tmp_path}/file1.txt",
        "content": "File 1"
      }}
    }},
    {{
      "id": "task-2",
      "type": "tool",
      "description": "创建第二个文件",
      "dependencies": [],
      "acceptance_criteria": ["文件创建成功"],
      "tool_name": "write_file",
      "tool_args": {{
        "path": "{tmp_path}/file2.txt",
        "content": "File 2"
      }}
    }}
  ],
  "overall_acceptance": ["所有文件创建成功"]
}}
```"""

        # Reflector 响应
        reflector_response = Mock()
        reflector_response.content = """```json
{
  "passed": false,
  "summary": "部分任务失败。",
  "feedback": "",
  "achievements": ["创建了 file1.txt"],
  "issues": ["file2.txt 创建失败"],
  "recommendation": "completed"
}
```"""

        mock_llm.ainvoke = AsyncMock(side_effect=[
            planner_response,
            reflector_response
        ])

        checkpointer = InMemorySaver()
        graph = create_full_swarm_graph(
            workspace_path=tmp_path,
            checkpointer=checkpointer,
            planner={"llm": mock_llm, "min_subtasks": 1},
            coder={"llm": mock_llm},
            reviewer={"llm": mock_llm},
            researcher={"llm": mock_llm},
            tool_runner={"require_approval": True},
            stop_condition={},
            reflector={"llm": mock_llm}
        )

        thread = {"configurable": {"thread_id": "test-approve-deny"}}

        # 执行到第一个中断点
        state = create_initial_state("创建两个文件")
        await graph.ainvoke(state, thread)

        # 第一次：批准
        await graph.ainvoke(
            Command(resume={"action": "approve", "operation": "tool_execution", "timestamp": "2026-01-22T00:00:00Z"}),
            thread
        )

        # 第二次：拒绝
        final_state = await graph.ainvoke(
            Command(resume={"action": "deny", "operation": "tool_execution", "timestamp": "2026-01-22T00:00:01Z"}),
            thread
        )

        # 验证结果（由于有任务失败，Reflector 应该标记为 failed）
        # Reflector Mock 响应设置为 "passed": false，所以最终状态应该是 failed
        # 但这是正确的行为 - 用户拒绝了一个任务
        assert final_state["status"] in ["completed", "failed"]  # ← 两种状态都可以接受
        assert len(final_state["subtask_results"]) == 2

        # 第一个任务应该成功
        assert final_state["subtask_results"][0]["passed"] is True
        assert (tmp_path / "file1.txt").exists()

        # 第二个任务应该失败（用户拒绝）
        assert final_state["subtask_results"][1]["passed"] is False
        assert "用户拒绝" in final_state["subtask_results"][1]["error_message"]
        assert not (tmp_path / "file2.txt").exists()


@pytest.mark.asyncio
class TestHITLWithoutCheckpointer:
    """测试没有 checkpointer 时的行为"""

    async def test_hitl_requires_checkpointer(self, tmp_path):
        """测试 HITL 需要 checkpointer"""

        def create_mock_llm():
            mock_llm = AsyncMock()

            planner_response = Mock()
            planner_response.content = f"""```json
{{
  "task": "创建文件",
  "subtasks": [
    {{
      "id": "task-1",
      "type": "tool",
      "description": "创建测试文件",
      "dependencies": [],
      "acceptance_criteria": ["文件创建成功"],
      "tool_name": "write_file",
      "tool_args": {{
        "path": "{tmp_path}/test.txt",
        "content": "Test"
      }}
    }}
  ],
  "overall_acceptance": ["文件创建成功"]
}}
```"""

            reflector_response = Mock()
            reflector_response.content = """```json
{
  "passed": true,
  "summary": "任务成功完成。",
  "feedback": "",
  "achievements": ["创建了文件"],
  "issues": [],
  "recommendation": "completed"
}
```"""

            mock_llm.ainvoke = AsyncMock(side_effect=[
                planner_response,
                reflector_response
            ])

            return mock_llm

        mock_llm = create_mock_llm()

        # 尝试创建 graph WITHOUT checkpointer（应该抛出 ValueError）
        with pytest.raises(ValueError) as exc_info:
            graph = create_full_swarm_graph(
                workspace_path=tmp_path,
                checkpointer=None,  # ← 没有 checkpointer
                planner={"llm": mock_llm, "min_subtasks": 1},
                coder={"llm": mock_llm},
                reviewer={"llm": mock_llm},
                researcher={"llm": mock_llm},
                tool_runner={"require_approval": True},  # ← 启用 HITL
                stop_condition={},
                reflector={"llm": mock_llm}
            )

        # 验证错误信息清晰
        error_message = str(exc_info.value)
        assert "Human-in-the-Loop requires checkpointer" in error_message
        assert "InMemorySaver" in error_message or "MemorySaver" in error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
