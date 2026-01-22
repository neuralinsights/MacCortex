#!/usr/bin/env python3
"""
三节点完整验证：Planner → Coder → Reviewer

验证提示词优化在三个节点的综合效果。
目标：总体优化 64.3%（1,098 → 392 tokens）
"""

import asyncio
import time
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.nodes.planner import create_planner_node
from src.orchestration.nodes.coder import create_coder_node
from src.orchestration.nodes.reviewer import create_reviewer_node
from src.orchestration.state import SwarmState


async def test_three_nodes_complete():
    """测试完整的三节点流程"""
    print("="*60)
    print("三节点完整验证：Planner → Coder → Reviewer")
    print("="*60)
    print()

    workspace = Path("/tmp/three_nodes_test")
    workspace.mkdir(exist_ok=True, parents=True)

    # 检查 API Key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 错误: 需要 ANTHROPIC_API_KEY")
        print("请设置环境变量后重试")
        return

    print("✅ LangSmith 追踪已启用")
    print(f"📊 访问 https://smith.langchain.com/projects 查看实时数据")
    print()

    # =====================================================
    # 阶段 1: Planner - 任务拆解
    # =====================================================
    print("="*60)
    print("阶段 1/3: Planner - 任务拆解")
    print("="*60)
    print()
    print("任务: 创建一个 Python 计算器程序，支持加减乘除四则运算")
    print()

    planner = create_planner_node(workspace)

    state = SwarmState(
        user_input="创建一个 Python 计算器程序，支持加减乘除四则运算",
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

    print("[Planner] 开始任务拆解...")
    start_time = time.time()

    try:
        result = await planner(state)
        elapsed = time.time() - start_time

        plan = result.get('plan', {})
        subtasks = plan.get('subtasks', [])

        print(f"✅ 任务拆解完成")
        print(f"⏱️  执行时间: {elapsed:.2f} 秒")
        print(f"📋 子任务数量: {len(subtasks)}")
        print()
        print("子任务列表:")
        for i, subtask in enumerate(subtasks, 1):
            print(f"  {i}. {subtask.get('description', '未知')}")
        print()
        print(f"💡 提示: 访问 LangSmith Dashboard 查看 Planner 节点的 Token 使用")
        print()

        # 保存状态
        state.update(result)
        planner_success = True
        planner_time = elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 失败: {e}")
        print(f"⏱️  执行时间: {elapsed:.2f} 秒")
        planner_success = False
        planner_time = elapsed
        return

    # =====================================================
    # 阶段 2: Coder - 代码生成
    # =====================================================
    print("="*60)
    print("阶段 2/3: Coder - 代码生成")
    print("="*60)
    print()

    # 获取第一个子任务
    if not subtasks:
        print("❌ 错误: 没有可执行的子任务")
        return

    first_subtask = subtasks[0]
    print(f"子任务: {first_subtask.get('description', '未知')}")
    print()

    coder = create_coder_node(workspace)

    state['status'] = 'coding'
    state['current_subtask_index'] = 0

    print("[Coder] 开始生成代码...")
    start_time = time.time()

    try:
        result = await coder(state)
        elapsed = time.time() - start_time

        code = result.get('current_code', '')
        code_file = result.get('current_code_file', '')

        print(f"✅ 代码生成完成")
        print(f"⏱️  执行时间: {elapsed:.2f} 秒")
        print(f"📄 生成文件: {code_file}")
        print(f"📏 代码行数: {len(code.splitlines())}")
        print()
        print("生成的代码预览:")
        print("-" * 60)
        for i, line in enumerate(code.splitlines()[:15], 1):
            print(f"  {i:2d} | {line}")
        if len(code.splitlines()) > 15:
            print(f"  ... (省略 {len(code.splitlines()) - 15} 行)")
        print("-" * 60)
        print()
        print(f"💡 提示: 访问 LangSmith Dashboard 查看 Coder 节点的 Token 使用")
        print()

        # 保存状态
        state.update(result)
        coder_success = True
        coder_time = elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 失败: {e}")
        print(f"⏱️  执行时间: {elapsed:.2f} 秒")
        coder_success = False
        coder_time = elapsed
        return

    # =====================================================
    # 阶段 3: Reviewer - 代码审查
    # =====================================================
    print("="*60)
    print("阶段 3/3: Reviewer - 代码审查")
    print("="*60)
    print()

    reviewer = create_reviewer_node(workspace)

    state['status'] = 'reviewing'

    print("[Reviewer] 开始代码审查...")
    start_time = time.time()

    try:
        result = await reviewer(state)
        elapsed = time.time() - start_time

        feedback = result.get('review_feedback', {})
        passed = feedback.get('passed', False)
        issues = feedback.get('issues', [])
        suggestions = feedback.get('suggestions', [])

        print(f"✅ 代码审查完成")
        print(f"⏱️  执行时间: {elapsed:.2f} 秒")
        print(f"📋 审查结果: {'✅ 通过' if passed else '❌ 需要修改'}")
        print()

        if issues:
            print(f"发现 {len(issues)} 个问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            print()

        if suggestions:
            print(f"改进建议 ({len(suggestions)} 条):")
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"  {i}. {suggestion}")
            if len(suggestions) > 3:
                print(f"  ... (省略 {len(suggestions) - 3} 条)")
            print()

        print(f"💡 提示: 访问 LangSmith Dashboard 查看 Reviewer 节点的 Token 使用")
        print()

        reviewer_success = True
        reviewer_time = elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 失败: {e}")
        print(f"⏱️  执行时间: {elapsed:.2f} 秒")
        reviewer_success = False
        reviewer_time = elapsed

    # =====================================================
    # 总结
    # =====================================================
    print("="*60)
    print("三节点验证总结")
    print("="*60)
    print()

    total_time = planner_time + coder_time + reviewer_time

    print("执行时间:")
    print(f"  Planner:  {planner_time:6.2f} 秒 {'✅' if planner_success else '❌'}")
    print(f"  Coder:    {coder_time:6.2f} 秒 {'✅' if coder_success else '❌'}")
    print(f"  Reviewer: {reviewer_time:6.2f} 秒 {'✅' if reviewer_success else '❌'}")
    print(f"  总计:     {total_time:6.2f} 秒")
    print()

    print("下一步: 验证 Token 使用")
    print("="*60)
    print()
    print("请访问 LangSmith Dashboard 查看详细的 Token 使用数据：")
    print()
    print("1. 打开: https://smith.langchain.com/projects")
    print("2. 选择项目: MacCortex")
    print("3. 查看最近的 3 次追踪（Planner, Coder, Reviewer）")
    print("4. 记录每个节点的 Input Tokens 和 Output Tokens")
    print()
    print("预期优化效果:")
    print("  - Planner:  722 → 235 tokens (-67.5%)")
    print("  - Coder:    186 →  79 tokens (-57.5%)")
    print("  - Reviewer: 190 →  78 tokens (-58.9%)")
    print("  - 总体:    1098 → 392 tokens (-64.3%)")
    print()
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_three_nodes_complete())
