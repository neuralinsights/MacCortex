#!/usr/bin/env python3
"""
A/B 质量测试脚本

目标：验证 Phase 5 提示词优化后的输出质量无降级
方法：10 个真实任务，评估正确性、完整性、可用性
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


# 测试任务定义
TEST_TASKS = [
    # ============================================================
    # 简单任务（3 个）- 预期 100% 成功率
    # ============================================================
    {
        "id": "simple-1",
        "category": "简单",
        "task": "创建一个 Python 函数，打印 'Hello, World!'",
        "expected_features": [
            "函数定义正确",
            "输出包含 'Hello, World!'",
            "代码可执行"
        ],
        "acceptance_threshold": 8.0  # 低于此分数视为失败
    },
    {
        "id": "simple-2",
        "category": "简单",
        "task": "写一个 Python 计算器函数，支持两个数字的加法运算",
        "expected_features": [
            "函数接受两个参数",
            "返回正确的和",
            "有基本的类型检查"
        ],
        "acceptance_threshold": 8.0
    },
    {
        "id": "simple-3",
        "category": "简单",
        "task": "创建一个 Python 函数，读取文本文件并返回行数",
        "expected_features": [
            "文件读取正确",
            "行数统计准确",
            "有文件不存在的错误处理"
        ],
        "acceptance_threshold": 8.0
    },

    # ============================================================
    # 中等任务（4 个）- 预期 85% 成功率
    # ============================================================
    {
        "id": "medium-1",
        "category": "中等",
        "task": "实现一个 Python 类，管理待办事项列表（添加、删除、标记完成）",
        "expected_features": [
            "类结构清晰",
            "三个核心方法实现正确",
            "数据持久化（内存或文件）",
            "边界检查（空列表、重复项）"
        ],
        "acceptance_threshold": 7.5
    },
    {
        "id": "medium-2",
        "category": "中等",
        "task": "写一个 Python 函数，解析 JSON 配置文件并验证必需字段",
        "expected_features": [
            "JSON 解析正确",
            "字段验证逻辑完整",
            "错误消息清晰",
            "支持嵌套字段验证"
        ],
        "acceptance_threshold": 7.5
    },
    {
        "id": "medium-3",
        "category": "中等",
        "task": "实现快速排序算法，包含性能测试",
        "expected_features": [
            "算法实现正确",
            "时间复杂度 O(n log n)",
            "有边界情况处理（空数组、单元素）",
            "性能测试代码完整"
        ],
        "acceptance_threshold": 7.5
    },
    {
        "id": "medium-4",
        "category": "中等",
        "task": "创建一个 Python 装饰器，记录函数执行时间和参数",
        "expected_features": [
            "装饰器语法正确",
            "记录时间准确",
            "记录参数完整",
            "支持任意函数"
        ],
        "acceptance_threshold": 7.5
    },

    # ============================================================
    # 复杂任务（3 个）- 预期 70% 成功率
    # ============================================================
    {
        "id": "complex-1",
        "category": "复杂",
        "task": "设计一个 RESTful API 的基础架构（路由、中间件、错误处理）",
        "expected_features": [
            "架构设计清晰（分层）",
            "路由定义完整",
            "中间件机制合理",
            "统一错误处理",
            "可扩展性考虑"
        ],
        "acceptance_threshold": 7.0
    },
    {
        "id": "complex-2",
        "category": "复杂",
        "task": "实现一个缓存系统（LRU 策略，支持过期时间）",
        "expected_features": [
            "LRU 算法正确",
            "过期时间管理",
            "线程安全（如果提及）",
            "性能优化",
            "测试用例完整"
        ],
        "acceptance_threshold": 7.0
    },
    {
        "id": "complex-3",
        "category": "复杂",
        "task": "设计一个日志系统，支持多级别、多输出目标、日志轮转",
        "expected_features": [
            "多级别支持（DEBUG/INFO/ERROR）",
            "多输出目标（文件/控制台/网络）",
            "日志轮转机制",
            "性能考虑（异步/缓冲）",
            "配置化设计"
        ],
        "acceptance_threshold": 7.0
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

        # 阶段 3: Reviewer
        print("[3/3] Reviewer 代码审查...")
        state['status'] = 'reviewing'

        reviewer_start = time.time()
        state = await reviewer(state)
        reviewer_time = time.time() - reviewer_start

        # 获取审查结果
        subtask_results = state.get('subtask_results', [])
        passed = False
        if subtask_results:
            passed = subtask_results[-1].get('passed', False)

        print(f"  ✅ 完成 ({reviewer_time:.2f}s) - {'通过' if passed else '失败'}")

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
            "plan": plan,
            "code": code,
            "subtask_results": subtask_results,
            "error": None
        }

    except Exception as e:
        total_time = time.time() - start_time
        print(f"  ❌ 失败: {str(e)}")

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
    print("A/B 质量测试 - Phase 5 优化验证")
    print("="*60)
    print()
    print(f"测试任务数: {len(TEST_TASKS)}")
    print(f"  - 简单任务: {sum(1 for t in TEST_TASKS if t['category'] == '简单')} 个")
    print(f"  - 中等任务: {sum(1 for t in TEST_TASKS if t['category'] == '中等')} 个")
    print(f"  - 复杂任务: {sum(1 for t in TEST_TASKS if t['category'] == '复杂')} 个")
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
        print(f"\n进度: {i}/{len(TEST_TASKS)}")
        result = await run_single_task(task, workspace)
        results.append(result)

        # 短暂休息避免 API 限流
        if i < len(TEST_TASKS):
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
    print(f"执行成功: {successful_tasks} ({successful_tasks/total_tasks*100:.1f}%)")
    print(f"审查通过: {passed_review} ({passed_review/total_tasks*100:.1f}%)")
    print()

    # 按类别统计
    for category in ['简单', '中等', '复杂']:
        category_results = [r for r in results if r['category'] == category]
        if category_results:
            success = sum(1 for r in category_results if r['success'])
            passed = sum(1 for r in category_results if r['passed_review'])
            print(f"{category}任务: {success}/{len(category_results)} 成功, {passed}/{len(category_results)} 通过审查")

    print()

    # 平均执行时间
    exec_times = [r['execution_time']['total'] for r in results if r['success']]
    if exec_times:
        avg_time = sum(exec_times) / len(exec_times)
        print(f"平均执行时间: {avg_time:.2f}s")

    # 保存详细结果
    output_file = workspace / "ab_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "passed_review": passed_review,
                "success_rate": successful_tasks/total_tasks,
                "review_pass_rate": passed_review/total_tasks
            },
            "results": results,
            "test_config": TEST_TASKS
        }, f, indent=2, ensure_ascii=False)

    print(f"\n详细结果已保存到: {output_file}")
    print()

    print("="*60)
    print("下一步: 人工评估代码质量")
    print("="*60)
    print()
    print("请检查生成的代码并评分（0-10 分）：")
    print("  - 正确性：功能是否完整实现")
    print("  - 完整性：是否覆盖边缘情况")
    print("  - 可用性：代码质量与可维护性")
    print()


if __name__ == "__main__":
    asyncio.run(main())
