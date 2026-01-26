#
# MacCortex - LLM Router Integration Tests
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""ModelRouterV2 与 Agent 节点集成测试"""

import pytest
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile

from src.llm.models import (
    CostInfo,
    LLMResponse,
    ModelConfig,
    ModelInfo,
    ProviderType,
    TokenUsage,
)
from src.llm.router import ModelRouterV2
from src.llm.usage_tracker import UsageTracker
from src.orchestration.state import (
    SwarmState,
    create_initial_state,
    update_token_usage,
)
from src.orchestration.nodes.planner import PlannerNode
from src.orchestration.nodes.coder import CoderNode
from src.orchestration.nodes.reviewer import ReviewerNode


class MockProvider:
    """模拟 LLM Provider"""

    def __init__(self, responses: list[str] = None):
        self._responses = responses or ["Test response"]
        self._response_index = 0
        self._models = {}

    @property
    def name(self) -> str:
        return "MockProvider"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC

    @property
    def is_available(self) -> bool:
        return True

    @property
    def models(self) -> list[ModelInfo]:
        return list(self._models.values())

    def register_model(self, model: ModelInfo):
        self._models[model.id] = model

    def get_model_info(self, model_id: str) -> ModelInfo:
        return self._models.get(model_id)

    async def invoke(
        self,
        model_id: str,
        messages: list[dict],
        config: ModelConfig = None,
    ) -> LLMResponse:
        """模拟 LLM 调用"""
        response_text = self._responses[self._response_index % len(self._responses)]
        self._response_index += 1

        return LLMResponse(
            content=response_text,
            usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            cost=CostInfo(
                input_cost=Decimal("0.0003"),
                output_cost=Decimal("0.00075"),
                total_cost=Decimal("0.00105"),
            ),
            model_id=model_id,
            provider=ProviderType.ANTHROPIC,
            latency_ms=100.0,
        )


class TestSwarmStateTokenTracking:
    """SwarmState Token 追踪测试"""

    def test_create_initial_state_has_token_fields(self):
        """测试初始状态包含 Token 追踪字段"""
        state = create_initial_state("Test task")

        assert "total_tokens" in state
        assert "total_cost" in state
        assert "token_usage_by_agent" in state

        assert state["total_tokens"] == 0
        assert state["total_cost"] == "0.000000"
        assert state["token_usage_by_agent"] == {}

    def test_update_token_usage_single_agent(self):
        """测试单个 Agent 的 Token 使用更新"""
        state = create_initial_state("Test task")

        updated = update_token_usage(
            state=state,
            agent_name="planner",
            input_tokens=100,
            output_tokens=50,
            cost="0.001500",
        )

        assert updated["total_tokens"] == 150
        assert updated["total_cost"] == "0.001500"
        assert "planner" in updated["token_usage_by_agent"]

        planner_usage = updated["token_usage_by_agent"]["planner"]
        assert planner_usage["input_tokens"] == 100
        assert planner_usage["output_tokens"] == 50
        assert planner_usage["total_tokens"] == 150
        assert planner_usage["call_count"] == 1
        assert planner_usage["total_cost"] == "0.001500"

    def test_update_token_usage_multiple_agents(self):
        """测试多个 Agent 的 Token 使用累加"""
        state = create_initial_state("Test task")

        # Planner 调用
        state = update_token_usage(
            state=state,
            agent_name="planner",
            input_tokens=200,
            output_tokens=100,
            cost="0.003000",
        )

        # Coder 调用
        state = update_token_usage(
            state=state,
            agent_name="coder",
            input_tokens=500,
            output_tokens=300,
            cost="0.010500",
        )

        # Reviewer 调用
        state = update_token_usage(
            state=state,
            agent_name="reviewer",
            input_tokens=300,
            output_tokens=50,
            cost="0.001350",
        )

        # 验证总计
        assert state["total_tokens"] == 1450  # 200+100 + 500+300 + 300+50
        assert state["total_cost"] == "0.014850"

        # 验证各 Agent
        assert len(state["token_usage_by_agent"]) == 3
        assert state["token_usage_by_agent"]["planner"]["call_count"] == 1
        assert state["token_usage_by_agent"]["coder"]["call_count"] == 1
        assert state["token_usage_by_agent"]["reviewer"]["call_count"] == 1

    def test_update_token_usage_same_agent_multiple_calls(self):
        """测试同一 Agent 多次调用的累加"""
        state = create_initial_state("Test task")

        # Coder 第一次调用
        state = update_token_usage(
            state=state,
            agent_name="coder",
            input_tokens=500,
            output_tokens=300,
            cost="0.010500",
        )

        # Coder 第二次调用（修复后重新生成）
        state = update_token_usage(
            state=state,
            agent_name="coder",
            input_tokens=600,
            output_tokens=350,
            cost="0.012300",
        )

        # 验证累加
        coder_usage = state["token_usage_by_agent"]["coder"]
        assert coder_usage["input_tokens"] == 1100  # 500 + 600
        assert coder_usage["output_tokens"] == 650  # 300 + 350
        assert coder_usage["total_tokens"] == 1750
        assert coder_usage["call_count"] == 2
        assert coder_usage["total_cost"] == "0.022800"


class TestModelRouterV2Integration:
    """ModelRouterV2 集成测试"""

    @pytest.fixture
    def mock_router(self):
        """创建带 Mock Provider 的 Router"""
        router = ModelRouterV2()

        # 创建 Mock Provider
        provider = MockProvider(
            responses=[
                # Planner 响应
                '{"subtasks": [{"id": "task-1", "type": "code", "description": "Test", "dependencies": [], "acceptance_criteria": ["Works"]}], "overall_acceptance": ["Done"]}',
                # Coder 响应
                '```python\nprint("Hello")\n```',
                # Reviewer 响应
                '{"passed": true, "feedback": "Good"}',
            ]
        )

        # 注册模型
        provider.register_model(
            ModelInfo(
                id="claude-sonnet-4",
                display_name="Claude Sonnet 4",
                provider=ProviderType.ANTHROPIC,
                input_price_per_1m=Decimal("3.00"),
                output_price_per_1m=Decimal("15.00"),
            )
        )

        # 使用 patch 替换 provider
        router._providers[ProviderType.ANTHROPIC] = provider
        router._model_to_provider["claude-sonnet-4"] = ProviderType.ANTHROPIC

        return router

    def test_router_invoke_returns_llm_response(self, mock_router):
        """测试 Router invoke 返回 LLMResponse"""
        import asyncio

        async def test():
            response = await mock_router.invoke(
                model_id="claude-sonnet-4",
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert isinstance(response, LLMResponse)
            assert response.usage.total_tokens == 150
            assert response.cost.total_cost == Decimal("0.00105")

        asyncio.run(test())

    def test_router_tracks_usage(self, mock_router):
        """测试 Router 追踪使用量"""
        import asyncio

        async def test():
            # 第一次调用
            await mock_router.invoke(
                model_id="claude-sonnet-4",
                messages=[{"role": "user", "content": "Hello"}],
                agent_name="planner",
            )

            # 第二次调用
            await mock_router.invoke(
                model_id="claude-sonnet-4",
                messages=[{"role": "user", "content": "World"}],
                agent_name="coder",
            )

            # 验证使用统计
            stats = mock_router.get_usage_stats()
            assert stats["total_tokens"] == 300  # 150 * 2
            assert stats["by_agent"]["planner"]["total_tokens"] == 150
            assert stats["by_agent"]["coder"]["total_tokens"] == 150

        asyncio.run(test())


class TestPlannerWithRouter:
    """Planner 与 ModelRouterV2 集成测试"""

    @pytest.fixture
    def mock_router(self):
        """创建 Mock Router"""
        router = MagicMock(spec=ModelRouterV2)

        # 模拟 get_model_info
        mock_model_info = MagicMock()
        mock_model_info.is_local = False
        router.get_model_info.return_value = mock_model_info

        # 模拟 invoke
        router.invoke = AsyncMock(
            return_value=LLMResponse(
                content='{"subtasks": [{"id": "task-1", "type": "code", "description": "Create hello.py", "dependencies": [], "acceptance_criteria": ["Works"]}], "overall_acceptance": ["Complete"]}',
                usage=TokenUsage(input_tokens=200, output_tokens=100, total_tokens=300),
                cost=CostInfo(
                    input_cost=Decimal("0.0006"),
                    output_cost=Decimal("0.0015"),
                    total_cost=Decimal("0.0021"),
                ),
                model_id="claude-sonnet-4",
                provider=ProviderType.ANTHROPIC,
                latency_ms=150.0,
            )
        )

        return router

    @pytest.mark.asyncio
    async def test_planner_with_router_tracks_tokens(self, mock_router):
        """测试 Planner 使用 Router 时追踪 Token"""
        planner = PlannerNode(
            router=mock_router,
            model_id="claude-sonnet-4",
        )

        state = create_initial_state("Create a hello world program")
        result_state = await planner.plan(state)

        # 验证调用了 router.invoke
        mock_router.invoke.assert_called_once()

        # 验证 Token 追踪
        assert result_state["total_tokens"] == 300
        assert "planner" in result_state["token_usage_by_agent"]
        assert result_state["token_usage_by_agent"]["planner"]["input_tokens"] == 200
        assert result_state["token_usage_by_agent"]["planner"]["output_tokens"] == 100


class TestCoderWithRouter:
    """Coder 与 ModelRouterV2 集成测试"""

    @pytest.fixture
    def mock_router(self):
        """创建 Mock Router"""
        router = MagicMock(spec=ModelRouterV2)

        mock_model_info = MagicMock()
        mock_model_info.is_local = False
        router.get_model_info.return_value = mock_model_info

        router.invoke = AsyncMock(
            return_value=LLMResponse(
                content='```python\nprint("Hello, World!")\n```',
                usage=TokenUsage(input_tokens=150, output_tokens=80, total_tokens=230),
                cost=CostInfo(
                    input_cost=Decimal("0.00045"),
                    output_cost=Decimal("0.0012"),
                    total_cost=Decimal("0.00165"),
                ),
                model_id="claude-sonnet-4",
                provider=ProviderType.ANTHROPIC,
                latency_ms=120.0,
            )
        )

        return router

    @pytest.mark.asyncio
    async def test_coder_with_router_tracks_tokens(self, mock_router):
        """测试 Coder 使用 Router 时追踪 Token"""
        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderNode(
                workspace_path=Path(tmpdir),
                router=mock_router,
                model_id="claude-sonnet-4",
            )

            state = create_initial_state("Create hello.py")
            state["plan"] = {
                "subtasks": [
                    {
                        "id": "task-1",
                        "type": "code",
                        "description": "Create hello.py",
                        "dependencies": [],
                        "acceptance_criteria": ["Works"],
                    }
                ],
                "overall_acceptance": ["Done"],
            }
            state["current_subtask_index"] = 0

            result_state = await coder.code(state)

            # 验证调用了 router.invoke
            mock_router.invoke.assert_called_once()

            # 验证 Token 追踪
            assert result_state["total_tokens"] == 230
            assert "coder" in result_state["token_usage_by_agent"]
            assert result_state["token_usage_by_agent"]["coder"]["input_tokens"] == 150


class TestReviewerWithRouter:
    """Reviewer 与 ModelRouterV2 集成测试"""

    @pytest.fixture
    def mock_router(self):
        """创建 Mock Router"""
        router = MagicMock(spec=ModelRouterV2)

        mock_model_info = MagicMock()
        mock_model_info.is_local = False
        router.get_model_info.return_value = mock_model_info

        router.invoke = AsyncMock(
            return_value=LLMResponse(
                content='{"passed": true, "feedback": "Code works correctly"}',
                usage=TokenUsage(input_tokens=300, output_tokens=30, total_tokens=330),
                cost=CostInfo(
                    input_cost=Decimal("0.0009"),
                    output_cost=Decimal("0.00045"),
                    total_cost=Decimal("0.00135"),
                ),
                model_id="claude-sonnet-4",
                provider=ProviderType.ANTHROPIC,
                latency_ms=80.0,
            )
        )

        return router

    @pytest.mark.asyncio
    async def test_reviewer_with_router_tracks_tokens(self, mock_router):
        """测试 Reviewer 使用 Router 时追踪 Token"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试代码文件
            code_file = Path(tmpdir) / "test.py"
            code_file.write_text('print("Hello")')

            reviewer = ReviewerNode(
                workspace_path=Path(tmpdir),
                router=mock_router,
                model_id="claude-sonnet-4",
            )

            state = create_initial_state("Test task")
            state["plan"] = {
                "subtasks": [
                    {
                        "id": "task-1",
                        "type": "code",
                        "description": "Test",
                        "dependencies": [],
                        "acceptance_criteria": ["Works"],
                    }
                ],
                "overall_acceptance": ["Done"],
            }
            state["current_subtask_index"] = 0
            state["current_code"] = 'print("Hello")'
            state["current_code_file"] = str(code_file)
            state["subtask_results"] = []

            result_state = await reviewer.review(state)

            # 验证调用了 router.invoke
            mock_router.invoke.assert_called_once()

            # 验证 Token 追踪
            assert result_state["total_tokens"] == 330
            assert "reviewer" in result_state["token_usage_by_agent"]


class TestEndToEndTokenTracking:
    """端到端 Token 追踪测试"""

    @pytest.mark.asyncio
    async def test_full_workflow_token_accumulation(self):
        """测试完整工作流的 Token 累加"""
        state = create_initial_state("Build a calculator")

        # 模拟 Planner
        state = update_token_usage(state, "planner", 500, 200, "0.010500")

        # 模拟 Coder（第一次）
        state = update_token_usage(state, "coder", 800, 400, "0.018000")

        # 模拟 Reviewer（失败）
        state = update_token_usage(state, "reviewer", 600, 50, "0.004050")

        # 模拟 Coder（修复）
        state = update_token_usage(state, "coder", 900, 450, "0.020250")

        # 模拟 Reviewer（通过）
        state = update_token_usage(state, "reviewer", 650, 30, "0.003900")

        # 验证总计
        total_expected = 500 + 200 + 800 + 400 + 600 + 50 + 900 + 450 + 650 + 30
        assert state["total_tokens"] == total_expected  # 4580

        # 验证成本
        total_cost_expected = 0.010500 + 0.018000 + 0.004050 + 0.020250 + 0.003900
        assert float(state["total_cost"]) == pytest.approx(total_cost_expected, rel=1e-6)

        # 验证各 Agent 调用次数
        assert state["token_usage_by_agent"]["planner"]["call_count"] == 1
        assert state["token_usage_by_agent"]["coder"]["call_count"] == 2
        assert state["token_usage_by_agent"]["reviewer"]["call_count"] == 2

        # 验证 Coder 累加
        assert state["token_usage_by_agent"]["coder"]["input_tokens"] == 1700  # 800 + 900
        assert state["token_usage_by_agent"]["coder"]["output_tokens"] == 850  # 400 + 450
