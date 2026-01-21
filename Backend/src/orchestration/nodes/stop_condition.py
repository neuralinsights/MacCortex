"""
MacCortex Stop Condition Checker

停止条件检查器，用于控制 Swarm 工作流的终止条件。

支持 4 种停止条件：
1. 最大迭代次数（Coder ↔ Reviewer 循环）
2. Token 预算耗尽
3. 时间超限（默认 10 分钟）
4. 用户中断
"""

import time
from typing import Tuple, Optional
from ..state import SwarmState


class StopConditionChecker:
    """
    停止条件检查器

    检查 Swarm 工作流是否应该停止执行。
    """

    def __init__(
        self,
        max_iterations: int = 3,
        max_tokens: int = 100000,
        max_time_seconds: int = 600  # 10 分钟
    ):
        """
        初始化停止条件检查器

        Args:
            max_iterations: 最大迭代次数（Coder ↔ Reviewer 循环）
            max_tokens: Token 预算上限
            max_time_seconds: 最大执行时间（秒）
        """
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.max_time_seconds = max_time_seconds

    def should_stop(self, state: SwarmState) -> Tuple[bool, str]:
        """
        检查是否应该停止

        Args:
            state: 当前 Swarm 状态

        Returns:
            (should_stop, reason): 是否停止 + 停止原因
        """
        # 1. 检查迭代次数
        iteration_count = state.get("iteration_count", 0)
        if iteration_count >= self.max_iterations:
            return True, f"达到最大迭代次数（{self.max_iterations}）"

        # 2. 检查 Token 预算
        total_tokens = state.get("total_tokens", 0)
        if total_tokens >= self.max_tokens:
            return True, f"Token 预算耗尽（{total_tokens}/{self.max_tokens}）"

        # 3. 检查时间限制
        start_time = state.get("start_time", time.time())
        elapsed = time.time() - start_time
        if elapsed >= self.max_time_seconds:
            return True, f"执行时间超限（{int(elapsed)}秒/{self.max_time_seconds}秒）"

        # 4. 检查用户中断
        if state.get("user_interrupted", False):
            return True, "用户手动中断"

        # 没有触发任何停止条件
        return False, ""

    def get_remaining_budget(self, state: SwarmState) -> dict:
        """
        获取剩余预算信息

        Args:
            state: 当前 Swarm 状态

        Returns:
            {"iterations": 剩余迭代次数, "tokens": 剩余 Token, "time": 剩余时间（秒）}
        """
        iteration_count = state.get("iteration_count", 0)
        total_tokens = state.get("total_tokens", 0)
        start_time = state.get("start_time", time.time())
        elapsed = time.time() - start_time

        return {
            "iterations": max(0, self.max_iterations - iteration_count),
            "tokens": max(0, self.max_tokens - total_tokens),
            "time": max(0, self.max_time_seconds - elapsed)
        }

    def is_near_limit(self, state: SwarmState, threshold: float = 0.8) -> dict:
        """
        检查是否接近任何限制（用于警告）

        Args:
            state: 当前 Swarm 状态
            threshold: 阈值比例（0.8 = 80%）

        Returns:
            {"iterations": bool, "tokens": bool, "time": bool}
        """
        budget = self.get_remaining_budget(state)

        return {
            "iterations": budget["iterations"] <= (self.max_iterations * (1 - threshold)),
            "tokens": budget["tokens"] <= (self.max_tokens * (1 - threshold)),
            "time": budget["time"] <= (self.max_time_seconds * (1 - threshold))
        }


def create_stop_condition_node(
    checker: Optional[StopConditionChecker] = None
) -> callable:
    """
    创建停止条件检查节点（用于 LangGraph）

    Args:
        checker: StopConditionChecker 实例（如果为 None，使用默认配置）

    Returns:
        停止条件检查节点函数
    """
    if checker is None:
        checker = StopConditionChecker()

    def stop_condition_node(state: SwarmState) -> SwarmState:
        """
        停止条件检查节点

        检查是否应该停止，如果应该停止则更新状态。
        """
        should_stop, reason = checker.should_stop(state)

        if should_stop:
            # 更新状态为失败
            state["status"] = "failed"
            state["error_message"] = f"任务终止：{reason}"

        return state

    return stop_condition_node


# 用于测试的简化函数
def test_stop_conditions():
    """测试停止条件检查器"""
    from ..state import create_initial_state

    # 创建检查器
    checker = StopConditionChecker(
        max_iterations=3,
        max_tokens=10000,
        max_time_seconds=60
    )

    # 测试 1: 正常状态（不应停止）
    state1 = create_initial_state("测试任务")
    should_stop, reason = checker.should_stop(state1)
    print(f"测试 1 - 正常状态: should_stop={should_stop}, reason='{reason}'")
    assert should_stop is False

    # 测试 2: 迭代次数超限
    state2 = create_initial_state("测试任务")
    state2["iteration_count"] = 3
    should_stop, reason = checker.should_stop(state2)
    print(f"测试 2 - 迭代次数超限: should_stop={should_stop}, reason='{reason}'")
    assert should_stop is True
    assert "迭代次数" in reason

    # 测试 3: Token 超限
    state3 = create_initial_state("测试任务")
    state3["total_tokens"] = 10000
    should_stop, reason = checker.should_stop(state3)
    print(f"测试 3 - Token 超限: should_stop={should_stop}, reason='{reason}'")
    assert should_stop is True
    assert "Token" in reason

    # 测试 4: 时间超限
    state4 = create_initial_state("测试任务")
    state4["start_time"] = time.time() - 61  # 61 秒前开始
    should_stop, reason = checker.should_stop(state4)
    print(f"测试 4 - 时间超限: should_stop={should_stop}, reason='{reason}'")
    assert should_stop is True
    assert "时间超限" in reason

    # 测试 5: 用户中断
    state5 = create_initial_state("测试任务")
    state5["user_interrupted"] = True
    should_stop, reason = checker.should_stop(state5)
    print(f"测试 5 - 用户中断: should_stop={should_stop}, reason='{reason}'")
    assert should_stop is True
    assert "用户" in reason

    # 测试 6: 剩余预算
    state6 = create_initial_state("测试任务")
    state6["iteration_count"] = 1
    state6["total_tokens"] = 5000
    state6["start_time"] = time.time() - 30
    budget = checker.get_remaining_budget(state6)
    print(f"测试 6 - 剩余预算: {budget}")
    assert budget["iterations"] == 2
    assert budget["tokens"] == 5000
    assert 25 <= budget["time"] <= 35  # 约 30 秒剩余

    # 测试 7: 接近限制
    state7 = create_initial_state("测试任务")
    state7["iteration_count"] = 2  # 2/3 = 66.7% 使用
    state7["total_tokens"] = 9000  # 9000/10000 = 90% 使用
    near_limit = checker.is_near_limit(state7, threshold=0.8)
    print(f"测试 7 - 接近限制: {near_limit}")
    assert near_limit["tokens"] is True  # 90% > 80%

    print("\n✅ 所有测试通过！")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加父目录到 sys.path 以支持相对导入
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    test_stop_conditions()
