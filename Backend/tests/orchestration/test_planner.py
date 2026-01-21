"""
MacCortex Planner Node 测试

测试 PlannerNode 的任务拆解功能。
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from src.orchestration.nodes.planner import PlannerNode
from src.orchestration.state import create_initial_state, Plan


class TestPlannerNodeBasic:
    """测试 Planner Node 基本功能"""

    @pytest.fixture
    def mock_api_key(self, monkeypatch):
        """Mock ANTHROPIC_API_KEY 环境变量"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-12345")

    def test_planner_initialization(self, mock_api_key):
        """测试 Planner 初始化"""
        planner = PlannerNode(
            model="claude-sonnet-4-20250514",
            temperature=0.2,
            max_subtasks=10,
            min_subtasks=3
        )

        assert planner.max_subtasks == 10
        assert planner.min_subtasks == 3
        assert planner.llm is not None
        assert planner.system_prompt is not None

    def test_planner_requires_api_key(self, monkeypatch):
        """测试 Planner 需要 API Key"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError, match="未设置 ANTHROPIC_API_KEY"):
            PlannerNode()

    def test_build_system_prompt(self, mock_api_key):
        """测试系统提示词构建"""
        planner = PlannerNode(min_subtasks=3, max_subtasks=10)
        prompt = planner.system_prompt

        assert "任务规划师" in prompt
        assert "3-10" in prompt
        assert "code|research|tool" in prompt
        assert "JSON" in prompt

    def test_build_user_prompt_simple(self, mock_api_key):
        """测试用户提示词构建（无上下文）"""
        planner = PlannerNode()
        user_task = "写一个 Hello World 程序"

        prompt = planner._build_user_prompt(user_task, {})

        assert "写一个 Hello World 程序" in prompt
        assert "用户任务" in prompt
        assert "JSON 格式" in prompt

    def test_build_user_prompt_with_context(self, mock_api_key):
        """测试用户提示词构建（含上下文）"""
        planner = PlannerNode()
        user_task = "优化这段代码"
        context = {"file_path": "/path/to/code.py", "language": "Python"}

        prompt = planner._build_user_prompt(user_task, context)

        assert "优化这段代码" in prompt
        assert "上下文信息" in prompt
        assert "file_path" in prompt
        assert "language" in prompt


class TestPlannerParsing:
    """测试计划解析功能"""

    @pytest.fixture
    def mock_api_key(self, monkeypatch):
        """Mock ANTHROPIC_API_KEY 环境变量"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-12345")

    @pytest.fixture
    def planner(self, mock_api_key):
        """创建 Planner 实例"""
        return PlannerNode()

    @pytest.fixture
    def valid_plan_json(self):
        """有效的计划 JSON"""
        return {
            "subtasks": [
                {
                    "id": "task-1",
                    "type": "code",
                    "description": "编写函数",
                    "dependencies": [],
                    "acceptance_criteria": ["函数能正常运行"]
                },
                {
                    "id": "task-2",
                    "type": "code",
                    "description": "编写测试",
                    "dependencies": ["task-1"],
                    "acceptance_criteria": ["测试通过"]
                }
            ],
            "overall_acceptance": ["功能完整", "代码质量高"]
        }

    def test_parse_plan_from_json_block(self, planner, valid_plan_json):
        """测试从 Markdown JSON 代码块解析计划"""
        content = f"```json\n{json.dumps(valid_plan_json, indent=2)}\n```"

        plan = planner._parse_plan(content)

        assert len(plan["subtasks"]) == 2
        assert plan["subtasks"][0]["id"] == "task-1"
        assert plan["subtasks"][1]["dependencies"] == ["task-1"]
        assert len(plan["overall_acceptance"]) == 2

    def test_parse_plan_from_plain_json(self, planner, valid_plan_json):
        """测试从纯 JSON 解析计划"""
        content = json.dumps(valid_plan_json)

        plan = planner._parse_plan(content)

        assert len(plan["subtasks"]) == 2
        assert plan["subtasks"][0]["type"] == "code"

    def test_parse_plan_invalid_json(self, planner):
        """测试解析无效 JSON"""
        content = "这不是 JSON"

        with pytest.raises(ValueError, match="无法解析 JSON"):
            planner._parse_plan(content)

    def test_parse_plan_missing_subtasks(self, planner):
        """测试缺少 subtasks 字段"""
        content = json.dumps({"overall_acceptance": ["完成"]})

        with pytest.raises(ValueError, match="缺少 'subtasks' 字段"):
            planner._parse_plan(content)

    def test_parse_plan_missing_overall_acceptance(self, planner):
        """测试缺少 overall_acceptance 字段"""
        content = json.dumps({"subtasks": []})

        with pytest.raises(ValueError, match="缺少 'overall_acceptance' 字段"):
            planner._parse_plan(content)

    def test_parse_plan_missing_required_fields(self, planner):
        """测试子任务缺少必需字段"""
        content = json.dumps({
            "subtasks": [
                {
                    "id": "task-1",
                    "type": "code"
                    # 缺少 description 和 acceptance_criteria
                }
            ],
            "overall_acceptance": ["完成"]
        })

        with pytest.raises(ValueError, match="缺少必需字段"):
            planner._parse_plan(content)

    def test_parse_plan_invalid_type(self, planner):
        """测试无效的任务类型"""
        content = json.dumps({
            "subtasks": [
                {
                    "id": "task-1",
                    "type": "invalid_type",  # 无效类型
                    "description": "描述",
                    "acceptance_criteria": ["标准"]
                }
            ],
            "overall_acceptance": ["完成"]
        })

        with pytest.raises(ValueError, match="类型无效"):
            planner._parse_plan(content)


class TestPlannerValidation:
    """测试计划验证功能"""

    @pytest.fixture
    def mock_api_key(self, monkeypatch):
        """Mock ANTHROPIC_API_KEY 环境变量"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-12345")

    @pytest.fixture
    def planner(self, mock_api_key):
        """创建 Planner 实例"""
        return PlannerNode(min_subtasks=3, max_subtasks=10)

    def test_validate_plan_too_few_subtasks(self, planner):
        """测试子任务数量过少"""
        plan: Plan = {
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

        with pytest.raises(ValueError, match="子任务数量过少"):
            planner._validate_plan(plan)

    def test_validate_plan_too_many_subtasks(self, planner):
        """测试子任务数量过多"""
        subtasks = [
            {
                "id": f"task-{i}",
                "type": "code",
                "description": f"任务{i}",
                "dependencies": [],
                "acceptance_criteria": ["标准"]
            }
            for i in range(1, 12)  # 11 个任务，超过最大值 10
        ]

        plan: Plan = {
            "subtasks": subtasks,
            "overall_acceptance": ["完成"]
        }

        with pytest.raises(ValueError, match="子任务数量过多"):
            planner._validate_plan(plan)

    def test_validate_plan_duplicate_ids(self, planner):
        """测试重复的任务 ID"""
        plan: Plan = {
            "subtasks": [
                {"id": "task-1", "type": "code", "description": "任务1", "dependencies": [], "acceptance_criteria": ["标准"]},
                {"id": "task-2", "type": "code", "description": "任务2", "dependencies": [], "acceptance_criteria": ["标准"]},
                {"id": "task-1", "type": "code", "description": "任务3", "dependencies": [], "acceptance_criteria": ["标准"]}  # 重复 ID
            ],
            "overall_acceptance": ["完成"]
        }

        with pytest.raises(ValueError, match="ID 重复"):
            planner._validate_plan(plan)

    def test_validate_plan_invalid_dependency(self, planner):
        """测试依赖不存在的任务"""
        plan: Plan = {
            "subtasks": [
                {"id": "task-1", "type": "code", "description": "任务1", "dependencies": [], "acceptance_criteria": ["标准"]},
                {"id": "task-2", "type": "code", "description": "任务2", "dependencies": [], "acceptance_criteria": ["标准"]},
                {"id": "task-3", "type": "code", "description": "任务3", "dependencies": ["task-999"], "acceptance_criteria": ["标准"]}  # 依赖不存在
            ],
            "overall_acceptance": ["完成"]
        }

        with pytest.raises(ValueError, match="依赖不存在的任务"):
            planner._validate_plan(plan)

    def test_validate_plan_self_dependency(self, planner):
        """测试任务依赖自己"""
        plan: Plan = {
            "subtasks": [
                {"id": "task-1", "type": "code", "description": "任务1", "dependencies": [], "acceptance_criteria": ["标准"]},
                {"id": "task-2", "type": "code", "description": "任务2", "dependencies": ["task-2"], "acceptance_criteria": ["标准"]},  # 依赖自己
                {"id": "task-3", "type": "code", "description": "任务3", "dependencies": [], "acceptance_criteria": ["标准"]}
            ],
            "overall_acceptance": ["完成"]
        }

        with pytest.raises(ValueError, match="不能依赖自己"):
            planner._validate_plan(plan)

    def test_validate_plan_missing_acceptance_criteria(self, planner):
        """测试缺少验收标准"""
        plan: Plan = {
            "subtasks": [
                {"id": "task-1", "type": "code", "description": "任务1", "dependencies": [], "acceptance_criteria": ["标准"]},
                {"id": "task-2", "type": "code", "description": "任务2", "dependencies": [], "acceptance_criteria": []},  # 空验收标准
                {"id": "task-3", "type": "code", "description": "任务3", "dependencies": [], "acceptance_criteria": ["标准"]}
            ],
            "overall_acceptance": ["完成"]
        }

        with pytest.raises(ValueError, match="缺少验收标准"):
            planner._validate_plan(plan)

    def test_validate_plan_missing_overall_acceptance(self, planner):
        """测试缺少整体验收标准"""
        plan: Plan = {
            "subtasks": [
                {"id": "task-1", "type": "code", "description": "任务1", "dependencies": [], "acceptance_criteria": ["标准"]},
                {"id": "task-2", "type": "code", "description": "任务2", "dependencies": [], "acceptance_criteria": ["标准"]},
                {"id": "task-3", "type": "code", "description": "任务3", "dependencies": [], "acceptance_criteria": ["标准"]}
            ],
            "overall_acceptance": []  # 空整体验收标准
        }

        with pytest.raises(ValueError, match="缺少整体验收标准"):
            planner._validate_plan(plan)

    def test_validate_plan_valid(self, planner):
        """测试有效的计划"""
        plan: Plan = {
            "subtasks": [
                {"id": "task-1", "type": "code", "description": "任务1", "dependencies": [], "acceptance_criteria": ["标准1"]},
                {"id": "task-2", "type": "code", "description": "任务2", "dependencies": ["task-1"], "acceptance_criteria": ["标准2"]},
                {"id": "task-3", "type": "research", "description": "任务3", "dependencies": [], "acceptance_criteria": ["标准3"]}
            ],
            "overall_acceptance": ["完成", "质量高"]
        }

        # 应该不抛出异常
        planner._validate_plan(plan)


@pytest.mark.asyncio
class TestPlannerIntegration:
    """测试 Planner Node 集成功能（需要 API Key）"""

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM 响应"""
        response = MagicMock()
        response.content = """```json
{
  "subtasks": [
    {
      "id": "task-1",
      "type": "code",
      "description": "编写 Hello World 函数",
      "dependencies": [],
      "acceptance_criteria": [
        "函数能打印 Hello World",
        "函数无错误"
      ]
    },
    {
      "id": "task-2",
      "type": "code",
      "description": "编写测试",
      "dependencies": ["task-1"],
      "acceptance_criteria": [
        "测试通过"
      ]
    },
    {
      "id": "task-3",
      "type": "code",
      "description": "添加文档",
      "dependencies": ["task-1"],
      "acceptance_criteria": [
        "文档清晰"
      ]
    }
  ],
  "overall_acceptance": [
    "程序能正常运行",
    "代码有测试和文档"
  ]
}
```"""
        return response

    async def test_plan_execution_success(self, mock_llm_response, monkeypatch):
        """测试计划执行成功"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        # Mock LLM ainvoke
        with patch('langchain_anthropic.ChatAnthropic.ainvoke', new_callable=AsyncMock) as mock_ainvoke:
            mock_ainvoke.return_value = mock_llm_response

            planner = PlannerNode()
            state = create_initial_state("写一个 Hello World 程序")

            result_state = await planner.plan(state)

            # 验证状态更新
            assert result_state["status"] == "executing"
            assert result_state["plan"] is not None
            assert len(result_state["plan"]["subtasks"]) == 3
            assert result_state["current_subtask_index"] == 0

            # 验证第一个子任务
            first_task = result_state["plan"]["subtasks"][0]
            assert first_task["id"] == "task-1"
            assert first_task["type"] == "code"
            assert "Hello World" in first_task["description"]

            # 验证 LLM 被调用
            mock_ainvoke.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
