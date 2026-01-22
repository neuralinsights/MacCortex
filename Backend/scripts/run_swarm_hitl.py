#!/usr/bin/env python3
"""
MacCortex HITL 交互式执行脚本

支持人机回环（Human-in-the-Loop）的 Swarm 工作流执行。
"""

import asyncio
import sys
from pathlib import Path
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

# 添加父目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.swarm_graph import create_full_swarm_graph
from src.orchestration.state import create_initial_state
from src.orchestration.hitl import HITLHelper


async def run_interactive_swarm(
    user_input: str,
    workspace_path: Path,
    enable_tool_approval: bool = True,
    enable_code_review: bool = False
):
    """
    运行交互式 Swarm 工作流

    Args:
        user_input: 用户任务描述
        workspace_path: 工作空间路径
        enable_tool_approval: 是否启用工具执行审批
        enable_code_review: 是否启用代码生成审查
    """
    print(f"{'=' * 60}")
    print(f"MacCortex HITL 交互式执行")
    print(f"{'=' * 60}")
    print(f"任务: {user_input}")
    print(f"工作空间: {workspace_path}")
    print(f"工具审批: {'启用' if enable_tool_approval else '禁用'}")
    print(f"代码审查: {'启用' if enable_code_review else '禁用'}")
    print(f"{'=' * 60}\n")

    # 1. 创建 Graph + InMemorySaver
    print("[系统] 初始化 Swarm 工作流...")
    checkpointer = InMemorySaver()
    graph = create_full_swarm_graph(
        workspace_path=workspace_path,
        checkpointer=checkpointer,
        tool_runner={"require_approval": enable_tool_approval},
        coder={"enable_code_review": enable_code_review}
    )

    # 2. 创建初始状态
    initial_state = create_initial_state(user_input)
    thread = {"configurable": {"thread_id": "hitl-session"}}

    print("[系统] 开始执行工作流...\n")

    # 3. 执行到第一个中断点或完成
    try:
        async for event in graph.astream(initial_state, thread, stream_mode="updates"):
            # 打印进度
            for node_name, node_state in event.items():
                print(f"[{node_name}] 执行完成")
    except Exception as e:
        print(f"[错误] 工作流执行异常: {e}")
        return

    # 4. 循环处理中断
    interrupt_count = 0
    while True:
        # 获取当前状态
        current_state = graph.get_state(thread)

        # 检查是否有中断
        if not current_state.interrupts:
            # 工作流完成
            print(f"\n[系统] 工作流完成")
            break

        interrupt_count += 1
        interrupt_data = current_state.interrupts[0]

        # 5. 显示中断信息
        print(f"\n{'~' * 60}")
        print(f"中断 #{interrupt_count}")
        formatted_message = HITLHelper.format_interrupt_message(interrupt_data)
        print(formatted_message)

        # 6. 收集用户输入
        operation = interrupt_data["operation"]
        available_actions = interrupt_data["available_actions"]

        while True:
            user_input_str = input(f"请选择操作 ({'/'.join(available_actions)}): ").strip()

            try:
                decision = HITLHelper.parse_user_decision(user_input_str, operation)

                # 如果是 modify，需要额外输入
                if decision["action"] == "modify":
                    print("\n[系统] 修改模式（输入新参数，JSON 格式）:")
                    # 简化处理：跳过修改功能（可后续扩展）
                    print("[系统] 修改功能尚未实现，将按原参数执行")
                    decision["action"] = "approve"

                break
            except ValueError as e:
                print(f"[错误] {e}")
                print(f"[提示] 有效选项：{', '.join(available_actions)}")

        # 7. 恢复执行
        print(f"\n[系统] 用户决策: {decision['action']}")
        print(f"[系统] 恢复工作流执行...\n")

        try:
            async for event in graph.astream(
                Command(resume=decision),
                thread,
                stream_mode="updates"
            ):
                # 打印进度
                for node_name, node_state in event.items():
                    print(f"[{node_name}] 执行完成")
        except Exception as e:
            print(f"[错误] 恢复执行异常: {e}")
            break

    # 8. 输出最终结果
    final_state = graph.get_state(thread)
    values = final_state.values

    print(f"\n{'=' * 60}")
    print(f"最终结果")
    print(f"{'=' * 60}")
    print(f"状态: {values.get('status', 'unknown')}")

    if values.get("status") == "completed":
        print(f"✅ 工作流成功完成")

        # 显示子任务结果
        subtask_results = values.get("subtask_results", [])
        if subtask_results:
            print(f"\n子任务结果:")
            for idx, result in enumerate(subtask_results, 1):
                status_emoji = "✅" if result.get("passed") else "❌"
                desc = result.get("subtask_description", f"子任务 {idx}")
                print(f"  {idx}. {status_emoji} {desc}")

        # 显示 Reflector 总结
        final_output = values.get("final_output")
        if final_output:
            print(f"\n整体评估:")
            print(f"  通过: {final_output.get('passed', False)}")
            print(f"  总结: {final_output.get('summary', 'N/A')}")
    else:
        print(f"❌ 工作流失败或终止")
        error_msg = values.get("error_message")
        if error_msg:
            print(f"错误信息: {error_msg}")

    print(f"{'=' * 60}\n")
    print(f"[统计] 总中断次数: {interrupt_count}")


async def main():
    """主函数"""
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="MacCortex HITL 交互式执行")
    parser.add_argument(
        "--task",
        type=str,
        default="创建测试文件 hello.txt，内容为 'Hello, MacCortex!'",
        help="任务描述"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=None,
        help="工作空间路径（默认使用临时目录）"
    )
    parser.add_argument(
        "--no-tool-approval",
        action="store_true",
        help="禁用工具执行审批"
    )
    parser.add_argument(
        "--enable-code-review",
        action="store_true",
        help="启用代码生成审查"
    )

    args = parser.parse_args()

    # 确定工作空间
    if args.workspace:
        workspace = Path(args.workspace)
        workspace.mkdir(parents=True, exist_ok=True)
    else:
        workspace = Path(tempfile.mkdtemp())

    # 运行交互式 Swarm
    await run_interactive_swarm(
        user_input=args.task,
        workspace_path=workspace,
        enable_tool_approval=not args.no_tool_approval,
        enable_code_review=args.enable_code_review
    )


if __name__ == "__main__":
    asyncio.run(main())
