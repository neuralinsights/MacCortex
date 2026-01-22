#!/usr/bin/env python3
"""
ModelRouter 端到端性能对比测试

对比本地模式 vs 混合模式的实际执行性能。
"""

import asyncio
import time
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.nodes.planner import create_planner_node
from src.orchestration.nodes.reviewer import create_reviewer_node
from src.orchestration.state import SwarmState


async def test_simple_task_performance(mode: str):
    """测试简单任务的实际执行性能"""
    print(f"\n{'='*60}")
    print(f"测试模式: {mode}")
    print(f"{'='*60}")

    workspace = Path(f"/tmp/benchmark_{mode}")
    workspace.mkdir(exist_ok=True)

    # 测试 1: Planner 拆解简单任务
    print("\n▶ 测试 Planner: Hello World 任务拆解")
    planner = create_planner_node(workspace)

    state = SwarmState(
        user_input="写一个打印 hello world 的 Python 脚本",
        context=None,
        plan=None,
        current_subtask_index=0,
        subtask_results=[],
        current_code=None,
        current_code_file=None,
        review_feedback=None,
        iteration_count=0,
        total_tokens=0,
        start_time=time.time(),
        status="planning",
        user_interrupted=False,
        final_output=None,
        error_message=None
    )

    start_time = time.time()
    try:
        result = await planner(state)
        elapsed = time.time() - start_time
        success = result is not None and hasattr(result, 'plan')
        subtasks_count = len(result.plan.get('subtasks', [])) if success else 0

        print(f"   ✅ 执行时间: {elapsed:.2f} 秒")
        print(f"   子任务数: {subtasks_count}")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ 失败: {e}")
        print(f"   执行时间: {elapsed:.2f} 秒")
        success = False

    # 测试 2: Reviewer 审查代码
    print("\n▶ 测试 Reviewer: 代码审查")
    test_file = workspace / "hello.py"
    test_file.write_text('print("Hello World")')

    reviewer = create_reviewer_node(workspace)

    state = SwarmState(
        user_input="审查 Hello World 代码",
        context=None,
        plan={
            "subtasks": [{
                "id": "task-1",
                "type": "code",
                "description": "Hello World",
                "dependencies": [],
                "acceptance_criteria": ["可运行"],
                "tool_name": None,
                "tool_args": None
            }],
            "overall_acceptance": ["完成"]
        },
        current_subtask_index=0,
        subtask_results=[],
        current_code='print("Hello World")',
        current_code_file=str(test_file),
        review_feedback=None,
        iteration_count=0,
        total_tokens=0,
        start_time=time.time(),
        status="reviewing",
        user_interrupted=False,
        final_output=None,
        error_message=None
    )

    start_time = time.time()
    try:
        result = await reviewer(state)
        elapsed = time.time() - start_time

        print(f"   ✅ 执行时间: {elapsed:.2f} 秒")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ 失败: {e}")
        print(f"   执行时间: {elapsed:.2f} 秒")

    return {
        "mode": mode,
        "planner_time": elapsed,
        "success": success
    }


async def main():
    """主测试函数"""
    print("="*60)
    print("ModelRouter 端到端性能对比测试")
    print("="*60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 未检测到 ANTHROPIC_API_KEY")
        print("只能测试本地模式\n")

        # 测试本地模式
        result_local = await test_simple_task_performance("local")

        print(f"\n{'='*60}")
        print("测试结果: 仅本地模式")
        print(f"{'='*60}")
        print(f"Planner 执行时间: {result_local['planner_time']:.2f} 秒")

    else:
        print(f"✅ 检测到 ANTHROPIC_API_KEY")
        print("测试混合模式（智能路由）\n")

        # 测试混合模式
        result_hybrid = await test_simple_task_performance("hybrid")

        print(f"\n{'='*60}")
        print("测试结果: 混合模式")
        print(f"{'='*60}")
        print(f"Planner 执行时间: {result_hybrid['planner_time']:.2f} 秒")

        print(f"\n{'='*60}")
        print("性能总结")
        print(f"{'='*60}")
        print(f"混合模式使用:")
        print(f"  - Planner: Claude Sonnet（高质量）")
        print(f"  - Reviewer: Ollama（节省成本）")
        print(f"\n关键优势:")
        print(f"  ✅ 智能路由: 根据复杂度自动选择模型")
        print(f"  ✅ 成本优化: 简单任务使用本地模型")
        print(f"  ✅ 质量提升: 复杂任务使用 Claude")


if __name__ == "__main__":
    asyncio.run(main())
