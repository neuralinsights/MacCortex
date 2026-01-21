"""
MacCortex Stop Condition 测试

测试停止条件检查器功能，包括：
- 最大迭代次数控制
- Token 预算管理
- 时间限制
- 用户中断处理
- 剩余预算查询
"""

import pytest
import time
from pathlib import Path

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestration.nodes.stop_condition import (
    StopConditionChecker,
    create_stop_condition_node
)
from src.orchestration.state import create_initial_state


class TestStopConditionChecker:
    """测试 StopConditionChecker 基础功能"""

    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        checker = StopConditionChecker()

        assert checker.max_iterations == 3
        assert checker.max_tokens == 100000
        assert checker.max_time_seconds == 600

    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        checker = StopConditionChecker(
            max_iterations=5,
            max_tokens=50000,
            max_time_seconds=300
        )

        assert checker.max_iterations == 5
        assert checker.max_tokens == 50000
        assert checker.max_time_seconds == 300

    def test_should_not_stop_initially(self):
        """测试初始状态不应停止"""
        checker = StopConditionChecker()
        state = create_initial_state("测试任务")

        should_stop, reason = checker.should_stop(state)

        assert should_stop is False
        assert reason == ""


class TestIterationLimit:
    """测试迭代次数限制"""

    def test_below_iteration_limit(self):
        """测试未达到迭代次数限制"""
        checker = StopConditionChecker(max_iterations=3)
        state = create_initial_state("测试任务")
        state["iteration_count"] = 2

        should_stop, reason = checker.should_stop(state)

        assert should_stop is False

    def test_at_iteration_limit(self):
        """测试达到迭代次数限制"""
        checker = StopConditionChecker(max_iterations=3)
        state = create_initial_state("测试任务")
        state["iteration_count"] = 3

        should_stop, reason = checker.should_stop(state)

        assert should_stop is True
        assert "迭代次数" in reason
        assert "3" in reason

    def test_exceed_iteration_limit(self):
        """测试超过迭代次数限制"""
        checker = StopConditionChecker(max_iterations=3)
        state = create_initial_state("测试任务")
        state["iteration_count"] = 5

        should_stop, reason = checker.should_stop(state)

        assert should_stop is True
        assert "迭代次数" in reason


class TestTokenBudget:
    """测试 Token 预算限制"""

    def test_below_token_limit(self):
        """测试未达到 Token 限制"""
        checker = StopConditionChecker(max_tokens=10000)
        state = create_initial_state("测试任务")
        state["total_tokens"] = 5000

        should_stop, reason = checker.should_stop(state)

        assert should_stop is False

    def test_at_token_limit(self):
        """测试达到 Token 限制"""
        checker = StopConditionChecker(max_tokens=10000)
        state = create_initial_state("测试任务")
        state["total_tokens"] = 10000

        should_stop, reason = checker.should_stop(state)

        assert should_stop is True
        assert "Token" in reason
        assert "10000" in reason

    def test_exceed_token_limit(self):
        """测试超过 Token 限制"""
        checker = StopConditionChecker(max_tokens=10000)
        state = create_initial_state("测试任务")
        state["total_tokens"] = 15000

        should_stop, reason = checker.should_stop(state)

        assert should_stop is True
        assert "Token" in reason


class TestTimeLimit:
    """测试时间限制"""

    def test_below_time_limit(self):
        """测试未达到时间限制"""
        checker = StopConditionChecker(max_time_seconds=60)
        state = create_initial_state("测试任务")
        state["start_time"] = time.time() - 30  # 30 秒前开始

        should_stop, reason = checker.should_stop(state)

        assert should_stop is False

    def test_at_time_limit(self):
        """测试达到时间限制"""
        checker = StopConditionChecker(max_time_seconds=60)
        state = create_initial_state("测试任务")
        state["start_time"] = time.time() - 60  # 60 秒前开始

        should_stop, reason = checker.should_stop(state)

        assert should_stop is True
        assert "时间超限" in reason
        assert "60" in reason

    def test_exceed_time_limit(self):
        """测试超过时间限制"""
        checker = StopConditionChecker(max_time_seconds=60)
        state = create_initial_state("测试任务")
        state["start_time"] = time.time() - 120  # 120 秒前开始

        should_stop, reason = checker.should_stop(state)

        assert should_stop is True
        assert "时间超限" in reason


class TestUserInterrupt:
    """测试用户中断"""

    def test_no_user_interrupt(self):
        """测试未触发用户中断"""
        checker = StopConditionChecker()
        state = create_initial_state("测试任务")
        state["user_interrupted"] = False

        should_stop, reason = checker.should_stop(state)

        assert should_stop is False

    def test_user_interrupt(self):
        """测试用户中断"""
        checker = StopConditionChecker()
        state = create_initial_state("测试任务")
        state["user_interrupted"] = True

        should_stop, reason = checker.should_stop(state)

        assert should_stop is True
        assert "用户" in reason
        assert "中断" in reason


class TestMultipleConditions:
    """测试多个停止条件同时触发"""

    def test_iteration_and_token_limit(self):
        """测试迭代次数和 Token 同时超限"""
        checker = StopConditionChecker(max_iterations=3, max_tokens=10000)
        state = create_initial_state("测试任务")
        state["iteration_count"] = 3
        state["total_tokens"] = 10000

        should_stop, reason = checker.should_stop(state)

        # 应该停止（检查第一个条件：迭代次数）
        assert should_stop is True
        assert "迭代次数" in reason  # 迭代次数先被检查到

    def test_all_conditions_triggered(self):
        """测试所有条件同时触发"""
        checker = StopConditionChecker(
            max_iterations=3,
            max_tokens=10000,
            max_time_seconds=60
        )
        state = create_initial_state("测试任务")
        state["iteration_count"] = 3
        state["total_tokens"] = 10000
        state["start_time"] = time.time() - 60
        state["user_interrupted"] = True

        should_stop, reason = checker.should_stop(state)

        # 应该停止（返回第一个触发的条件）
        assert should_stop is True


class TestRemainingBudget:
    """测试剩余预算查询"""

    def test_get_remaining_budget_full(self):
        """测试获取完整剩余预算"""
        checker = StopConditionChecker(
            max_iterations=3,
            max_tokens=10000,
            max_time_seconds=60
        )
        state = create_initial_state("测试任务")
        state["iteration_count"] = 0
        state["total_tokens"] = 0
        state["start_time"] = time.time()

        budget = checker.get_remaining_budget(state)

        assert budget["iterations"] == 3
        assert budget["tokens"] == 10000
        assert 59 <= budget["time"] <= 60  # 约 60 秒剩余

    def test_get_remaining_budget_partial(self):
        """测试获取部分使用后的剩余预算"""
        checker = StopConditionChecker(
            max_iterations=5,
            max_tokens=20000,
            max_time_seconds=120
        )
        state = create_initial_state("测试任务")
        state["iteration_count"] = 2
        state["total_tokens"] = 8000
        state["start_time"] = time.time() - 40

        budget = checker.get_remaining_budget(state)

        assert budget["iterations"] == 3
        assert budget["tokens"] == 12000
        assert 79 <= budget["time"] <= 81  # 约 80 秒剩余

    def test_get_remaining_budget_exhausted(self):
        """测试预算耗尽时的剩余预算"""
        checker = StopConditionChecker(
            max_iterations=3,
            max_tokens=10000,
            max_time_seconds=60
        )
        state = create_initial_state("测试任务")
        state["iteration_count"] = 5  # 超过限制
        state["total_tokens"] = 15000  # 超过限制
        state["start_time"] = time.time() - 100  # 超过限制

        budget = checker.get_remaining_budget(state)

        # 剩余预算应该为 0（不会为负数）
        assert budget["iterations"] == 0
        assert budget["tokens"] == 0
        assert budget["time"] == 0


class TestNearLimit:
    """测试接近限制检查"""

    def test_is_near_limit_none(self):
        """测试未接近任何限制"""
        checker = StopConditionChecker(
            max_iterations=10,
            max_tokens=100000,
            max_time_seconds=600
        )
        state = create_initial_state("测试任务")
        state["iteration_count"] = 2  # 20% 使用
        state["total_tokens"] = 10000  # 10% 使用
        state["start_time"] = time.time() - 60  # 10% 使用

        near_limit = checker.is_near_limit(state, threshold=0.8)

        assert near_limit["iterations"] is False
        assert near_limit["tokens"] is False
        assert near_limit["time"] is False

    def test_is_near_limit_iterations(self):
        """测试接近迭代次数限制"""
        checker = StopConditionChecker(max_iterations=10)
        state = create_initial_state("测试任务")
        state["iteration_count"] = 9  # 90% 使用

        near_limit = checker.is_near_limit(state, threshold=0.8)

        assert near_limit["iterations"] is True

    def test_is_near_limit_tokens(self):
        """测试接近 Token 限制"""
        checker = StopConditionChecker(max_tokens=10000)
        state = create_initial_state("测试任务")
        state["total_tokens"] = 9000  # 90% 使用

        near_limit = checker.is_near_limit(state, threshold=0.8)

        assert near_limit["tokens"] is True

    def test_is_near_limit_time(self):
        """测试接近时间限制"""
        checker = StopConditionChecker(max_time_seconds=100)
        state = create_initial_state("测试任务")
        state["start_time"] = time.time() - 90  # 90% 使用

        near_limit = checker.is_near_limit(state, threshold=0.8)

        assert near_limit["time"] is True

    def test_is_near_limit_custom_threshold(self):
        """测试自定义阈值"""
        checker = StopConditionChecker(max_iterations=10)
        state = create_initial_state("测试任务")
        state["iteration_count"] = 7  # 70% 使用

        # 阈值 0.5（50%）
        near_limit_50 = checker.is_near_limit(state, threshold=0.5)
        assert near_limit_50["iterations"] is True  # 70% > 50%

        # 阈值 0.8（80%）
        near_limit_80 = checker.is_near_limit(state, threshold=0.8)
        assert near_limit_80["iterations"] is False  # 70% < 80%


class TestStopConditionNode:
    """测试停止条件节点（用于 LangGraph）"""

    def test_create_stop_condition_node_default(self):
        """测试创建默认停止条件节点"""
        node = create_stop_condition_node()

        assert callable(node)

    def test_create_stop_condition_node_custom(self):
        """测试创建自定义停止条件节点"""
        checker = StopConditionChecker(max_iterations=5)
        node = create_stop_condition_node(checker)

        assert callable(node)

    def test_stop_condition_node_no_stop(self):
        """测试节点不停止时的行为"""
        checker = StopConditionChecker()
        node = create_stop_condition_node(checker)

        state = create_initial_state("测试任务")
        original_status = state["status"]

        result_state = node(state)

        # 状态不应该改变
        assert result_state["status"] == original_status
        assert result_state.get("error_message") is None

    def test_stop_condition_node_should_stop(self):
        """测试节点触发停止时的行为"""
        checker = StopConditionChecker(max_iterations=3)
        node = create_stop_condition_node(checker)

        state = create_initial_state("测试任务")
        state["iteration_count"] = 3

        result_state = node(state)

        # 状态应该更新为失败
        assert result_state["status"] == "failed"
        assert result_state["error_message"] is not None
        assert "任务终止" in result_state["error_message"]
        assert "迭代次数" in result_state["error_message"]


class TestEdgeCases:
    """测试边界情况"""

    def test_missing_iteration_count(self):
        """测试缺少 iteration_count 字段"""
        checker = StopConditionChecker()
        state = create_initial_state("测试任务")
        del state["iteration_count"]  # 删除字段

        should_stop, reason = checker.should_stop(state)

        # 应该不停止（默认为 0）
        assert should_stop is False

    def test_missing_total_tokens(self):
        """测试缺少 total_tokens 字段"""
        checker = StopConditionChecker()
        state = create_initial_state("测试任务")
        # total_tokens 可能不存在（默认为 0）

        should_stop, reason = checker.should_stop(state)

        # 应该不停止
        assert should_stop is False

    def test_missing_start_time(self):
        """测试缺少 start_time 字段"""
        checker = StopConditionChecker()
        state = create_initial_state("测试任务")
        del state["start_time"]  # 删除字段

        should_stop, reason = checker.should_stop(state)

        # 应该不停止（使用当前时间）
        assert should_stop is False

    def test_zero_limits(self):
        """测试零限制"""
        checker = StopConditionChecker(
            max_iterations=0,
            max_tokens=0,
            max_time_seconds=0
        )
        state = create_initial_state("测试任务")

        should_stop, reason = checker.should_stop(state)

        # 应该立即停止（达到限制）
        assert should_stop is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
