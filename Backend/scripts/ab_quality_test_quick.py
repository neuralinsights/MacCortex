#!/usr/bin/env python3
"""
A/B 质量测试脚本（快速版本 - 仅 3 个简单任务）

快速验证脚本是否工作，然后再运行完整的 10 个任务
"""

import asyncio
import time
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.nodes.planner import create_planner_node
from src.orchestration.nodes.coder import create_coder_node
from src.orchestration.nodes.reviewer import create_reviewer_node
from src.orchestration.state import SwarmState


# 仅测试 3 个简单任务
TEST_TASKS = [
    {
        "id": "simple-1",
        "category": "简单",
        "task": "创建一个 Python 函数，打印 'Hello, World!'",
        "expected_features": ["函数定义正确", "输出包含 'Hello, World!'", "代码可执行"],
        "acceptance_threshold": 8.0
    },
    {
        "id": "simple-2",
        "category": "简单",
        "task": "写一个 Python 计算器函数，支持两个数字的加法运算",
        "expected_features": ["函数接受两个参数", "返回正确的和", "有基本的类型检查"],
        "acceptance_threshold": 8.0
    },
    {
        "id": "simple-3",
        "category": "简单",
        "task": "创建一个 Python 函数，读取文本文件并返回行数",
        "expected_features": ["文件读取正确", "行数统计准确", "有文件不存在的错误处理"],
        "acceptance_threshold": 8.0
    }
]


async def run_single_task(task: Dict[str, Any], workspace: Path) -> Dict[str, Any]:
    """运行单个测试任务"""
    print(f"\n{'='*60}")
    print(f"任务 {task['id']}: {task['category']}")
    print(f"{'='*60}")
    print(f"描述: {task['task']}")
    print()

    start_time = time.time()

    # 创建节点
    planner = create_planner_node(workspace)
    coder = create_coder_node(workspace)
    reviewer = create_reviewer_node(workspace)

    # 初始化状态
    state = SwarmState(
        user_input=task['task'],
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

    try:
        # 阶段 1: Planner
        print("[1/3] Planner 任务拆解...")
        planner_start = time.time()
        state = await planner(state)
        planner_time = time.time() - planner_start

        plan = state.get('plan', {})
        subtasks = plan.get('subtasks', [])
        print(f"  ✅ 完成 ({planner_time:.2f}s) - {len(subtasks)} 个子任务")

        if not subtasks:
            raise ValueError("Planner 未生成子任务")

        # 阶段 2: Coder（仅执行第一个子任务）
        print("[2/3] Coder 代码生成...")
        state['status'] = 'coding'
        state['current_subtask_index'] = 0

        coder_start = time.time()
        state = await coder(state)
        coder_time = time.time() - coder_start

        code = state.get('current_code', '')
        print(f"  ✅ 完成 ({coder_time:.2f}s) - {len(code.splitlines())} 行代码")

        # 显示生成的代码预览
        print()
        print("生成的代码预览:")
        print("-" * 60)
        for i, line in enumerate(code.splitlines()[:20], 1):
            print(f"  {i:2d} | {line}")
        if len(code.splitlines()) > 20:
            print(f"  ... (省略 {len(code.splitlines()) - 20} 行)")
        print("-" * 60)
        print()

        # 阶段 3: Reviewer
        print("[3/3] Reviewer 代码审查...")
        state['status'] = 'reviewing'

        reviewer_start = time.time()
        state = await reviewer(state)
        reviewer_time = time.time() - reviewer_start

        # 获取审查结果
        subtask_results = state.get('subtask_results', [])
        passed = False
        feedback = ""
        if subtask_results:
            passed = subtask_results[-1].get('passed', False)

        # 获取 review_feedback
        review_feedback = state.get('review_feedback', {})
        if isinstance(review_feedback, dict):
            feedback = review_feedback.get('feedback', '')

        print(f"  ✅ 完成 ({reviewer_time:.2f}s) - {'✅ 通过' if passed else '❌ 失败'}")
        if feedback:
            print(f"  反馈: {feedback[:100]}...")
        print()

        total_time = time.time() - start_time

        return {
            "task_id": task['id'],
            "category": task['category'],
            "task": task['task'],
            "success": True,
            "passed_review": passed,
            "execution_time": {
                "planner": planner_time,
                "coder": coder_time,
                "reviewer": reviewer_time,
                "total": total_time
            },
            "code": code,
            "code_lines": len(code.splitlines()),
            "feedback": feedback,
            "error": None
        }

    except Exception as e:
        total_time = time.time() - start_time
        print(f"  ❌ 失败: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "task_id": task['id'],
            "category": task['category'],
            "task": task['task'],
            "success": False,
            "passed_review": False,
            "execution_time": {"total": total_time},
            "error": str(e)
        }


async def main():
    """主测试流程"""
    print("="*60)
    print("A/B 质量测试（快速版本）")
    print("="*60)
    print()
    print(f"测试任务数: {len(TEST_TASKS)} 个简单任务")
    print()

    # 检查环境
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 错误: 需要 ANTHROPIC_API_KEY")
        return

    print("✅ 环境检查通过")
    print()

    # 创建工作空间
    workspace = Path("/tmp/ab_quality_test")
    workspace.mkdir(exist_ok=True, parents=True)

    # 运行所有测试任务
    results = []
    for i, task in enumerate(TEST_TASKS, 1):
        print(f"\n{'#'*60}")
        print(f"进度: {i}/{len(TEST_TASKS)}")
        print(f"{'#'*60}")
        result = await run_single_task(task, workspace)
        results.append(result)

        # 短暂休息避免 API 限流
        if i < len(TEST_TASKS):
            print("\n⏸️  休息 2 秒...")
            await asyncio.sleep(2)

    # 生成统计报告
    print("\n" + "="*60)
    print("测试结果统计")
    print("="*60)
    print()

    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r['success'])
    passed_review = sum(1 for r in results if r['passed_review'])

    print(f"总任务数: {total_tasks}")
    print(f"执行成功: {successful_tasks}/{total_tasks} ({successful_tasks/total_tasks*100:.1f}%)")
    print(f"审查通过: {passed_review}/{total_tasks} ({passed_review/total_tasks*100:.1f}%)")
    print()

    # 平均执行时间
    exec_times = [r['execution_time']['total'] for r in results if r['success']]
    if exec_times:
        avg_time = sum(exec_times) / len(exec_times)
        min_time = min(exec_times)
        max_time = max(exec_times)
        print(f"执行时间统计:")
        print(f"  平均: {avg_time:.2f}s")
        print(f"  最快: {min_time:.2f}s")
        print(f"  最慢: {max_time:.2f}s")
    print()

    # 代码统计
    code_lines = [r.get('code_lines', 0) for r in results if r['success']]
    if code_lines:
        avg_lines = sum(code_lines) / len(code_lines)
        print(f"生成代码行数: 平均 {avg_lines:.0f} 行")
    print()

    # 保存详细结果
    output_file = workspace / "ab_test_quick_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "passed_review": passed_review,
                "success_rate": successful_tasks/total_tasks,
                "review_pass_rate": passed_review/total_tasks,
                "avg_execution_time": avg_time if exec_times else 0
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"📄 详细结果已保存到: {output_file}")
    print()

    # 成功标准判断
    print("="*60)
    print("质量评估")
    print("="*60)
    print()

    if passed_review == total_tasks:
        print("✅ 优秀！所有任务都通过审查")
    elif passed_review >= total_tasks * 0.8:
        print("✅ 良好！80% 以上任务通过审查")
    else:
        print("⚠️  需要关注！通过率低于 80%")

    print()
    print("下一步建议:")
    if passed_review == total_tasks:
        print("  1. ✅ 继续运行完整的 10 个任务测试（包含中等和复杂任务）")
        print("  2. 生成完整的 A/B 质量测试报告")
    else:
        print("  1. 检查失败的任务代码")
        print("  2. 分析失败原因（提示词问题 vs 任务复杂度）")
        print("  3. 微调提示词并重新测试")
    print()


if __name__ == "__main__":
    asyncio.run(main())
