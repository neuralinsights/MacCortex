#!/usr/bin/env python3
"""
ModelRouter 性能基准测试脚本

测试 ModelRouter 智能路由集成后的实际性能表现。

支持两种测试模式：
1. 无 API Key：测试 ModelRouter 降级机制（全部使用 Ollama）
2. 有 API Key：测试智能路由的实际性能提升

使用方法：
    python scripts/benchmark_model_router.py
    python scripts/benchmark_model_router.py --with-api-key  # 需要配置 ANTHROPIC_API_KEY
"""

import asyncio
import time
import os
import sys
from pathlib import Path
from typing import Dict, List
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.nodes.planner import create_planner_node
from src.orchestration.nodes.coder import create_coder_node
from src.orchestration.nodes.reviewer import create_reviewer_node
from src.orchestration.state import SwarmState


class BenchmarkRunner:
    """性能基准测试运行器"""

    def __init__(self, test_mode: str = "local"):
        """
        初始化测试运行器

        Args:
            test_mode: 测试模式
                - "local": 本地模型模式（无 API Key）
                - "hybrid": 混合模式（有 API Key，智能路由）
        """
        self.test_mode = test_mode
        self.workspace = Path("/tmp/model_router_benchmark")
        self.workspace.mkdir(exist_ok=True)
        self.results = []

    async def run_planner_test(self, task_description: str, task_name: str) -> Dict:
        """运行 Planner 节点测试"""
        print(f"\n▶ 测试 Planner: {task_name}")
        print(f"   任务描述: {task_description}")

        # 创建 Planner 节点
        start_time = time.time()
        planner = create_planner_node(self.workspace)
        creation_time = time.time() - start_time

        # 准备状态
        state = SwarmState(
            task_description=task_description,
            workspace=str(self.workspace),
            subtasks=[]
        )

        # 执行 Planner
        start_time = time.time()
        try:
            result_state = await planner(state)
            execution_time = time.time() - start_time
            # 如果返回 SwarmState 对象且没有抛出异常，视为成功
            success = result_state is not None
            error = None
        except Exception as e:
            execution_time = time.time() - start_time
            success = False
            error = str(e)

        total_time = creation_time + execution_time

        result = {
            "node": "Planner",
            "task_name": task_name,
            "task_description": task_description,
            "creation_time": round(creation_time, 2),
            "execution_time": round(execution_time, 2),
            "total_time": round(total_time, 2),
            "success": success,
            "error": error
        }

        print(f"   ✅ 完成: {total_time:.2f} 秒")
        return result

    async def run_coder_test(self, task_description: str, task_name: str) -> Dict:
        """运行 Coder 节点测试"""
        print(f"\n▶ 测试 Coder: {task_name}")
        print(f"   任务描述: {task_description}")

        # 创建 Coder 节点
        start_time = time.time()
        coder = create_coder_node(self.workspace)
        creation_time = time.time() - start_time

        # 准备状态（模拟 Planner 输出）
        state = SwarmState(
            task_description=task_description,
            workspace=str(self.workspace),
            plan={
                "subtasks": [
                    {
                        "id": 1,
                        "description": task_description,
                        "language": "python",
                        "acceptance_criteria": ["代码可运行", "无语法错误"]
                    }
                ],
                "overall_acceptance": "任务完成"
            },
            current_subtask_index=0,
            subtasks=[]
        )

        # 执行 Coder
        start_time = time.time()
        try:
            result_state = await coder(state)
            execution_time = time.time() - start_time
            # 如果返回 SwarmState 对象且没有抛出异常，视为成功
            success = result_state is not None
            error = None
        except Exception as e:
            execution_time = time.time() - start_time
            success = False
            error = str(e)

        total_time = creation_time + execution_time

        result = {
            "node": "Coder",
            "task_name": task_name,
            "task_description": task_description,
            "creation_time": round(creation_time, 2),
            "execution_time": round(execution_time, 2),
            "total_time": round(total_time, 2),
            "success": success,
            "error": error
        }

        print(f"   ✅ 完成: {total_time:.2f} 秒")
        return result

    async def run_reviewer_test(self, task_name: str) -> Dict:
        """运行 Reviewer 节点测试"""
        print(f"\n▶ 测试 Reviewer: {task_name}")

        # 创建测试文件
        test_file = self.workspace / "test_hello.py"
        test_file.write_text('print("Hello World")')

        # 创建 Reviewer 节点
        start_time = time.time()
        reviewer = create_reviewer_node(self.workspace)
        creation_time = time.time() - start_time

        # 准备状态
        state = SwarmState(
            task_description="测试代码审查",
            workspace=str(self.workspace),
            plan={
                "subtasks": [
                    {
                        "id": 1,
                        "description": "审查 Hello World 代码",
                        "language": "python",
                        "acceptance_criteria": ["代码可运行"]
                    }
                ],
                "overall_acceptance": "任务完成"
            },
            current_subtask_index=0,
            generated_files=[str(test_file)],
            subtasks=[]
        )

        # 执行 Reviewer
        start_time = time.time()
        try:
            result_state = await reviewer(state)
            execution_time = time.time() - start_time
            # 如果返回 SwarmState 对象且没有抛出异常，视为成功
            success = result_state is not None
            error = None
        except Exception as e:
            execution_time = time.time() - start_time
            success = False
            error = str(e)

        total_time = creation_time + execution_time

        result = {
            "node": "Reviewer",
            "task_name": task_name,
            "task_description": "审查简单 Python 代码",
            "creation_time": round(creation_time, 2),
            "execution_time": round(execution_time, 2),
            "total_time": round(total_time, 2),
            "success": success,
            "error": error
        }

        print(f"   ✅ 完成: {total_time:.2f} 秒")
        return result

    async def run_all_tests(self):
        """运行所有测试"""
        print(f"{'='*60}")
        print(f"ModelRouter 性能基准测试")
        print(f"{'='*60}")
        print(f"测试模式: {self.test_mode}")
        print(f"工作空间: {self.workspace}")
        print(f"API Key 状态: {'✅ 已配置' if os.getenv('ANTHROPIC_API_KEY') else '❌ 未配置（使用本地模型）'}")
        print(f"{'='*60}")

        # 测试场景
        test_cases = [
            ("simple_hello", "Planner", "写一个打印 hello world 的 Python 脚本"),
            ("simple_calc", "Planner", "写一个简单的命令行计算器（仅加减法）"),
            ("simple_code", "Coder", "print('Hello, World!')"),
            ("simple_review", "Reviewer", None)
        ]

        # 运行测试
        for task_name, node_type, task_description in test_cases:
            try:
                if node_type == "Planner":
                    result = await self.run_planner_test(task_description, task_name)
                elif node_type == "Coder":
                    result = await self.run_coder_test(task_description, task_name)
                elif node_type == "Reviewer":
                    result = await self.run_reviewer_test(task_name)
                else:
                    continue

                self.results.append(result)
            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
                self.results.append({
                    "node": node_type,
                    "task_name": task_name,
                    "error": str(e),
                    "success": False
                })

        # 生成报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        print(f"\n{'='*60}")
        print("测试报告")
        print(f"{'='*60}\n")

        # 按节点分组统计
        planner_results = [r for r in self.results if r["node"] == "Planner"]
        coder_results = [r for r in self.results if r["node"] == "Coder"]
        reviewer_results = [r for r in self.results if r["node"] == "Reviewer"]

        # 统计成功率
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.get("success", False)])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"总测试数: {total_tests}")
        print(f"成功: {successful_tests} / 失败: {total_tests - successful_tests}")
        print(f"成功率: {success_rate:.1f}%\n")

        # Planner 统计
        if planner_results:
            print("Planner 节点:")
            successful_planner = [r for r in planner_results if r.get("success", False)]
            if successful_planner:
                avg_time = sum(r["total_time"] for r in successful_planner) / len(successful_planner)
                print(f"  平均执行时间: {avg_time:.2f} 秒")
            for r in planner_results:
                status = "✅" if r.get("success", False) else "❌"
                print(f"  {status} {r['task_name']}: {r.get('total_time', 0):.2f} 秒")
            print()

        # Coder 统计
        if coder_results:
            print("Coder 节点:")
            successful_coder = [r for r in coder_results if r.get("success", False)]
            if successful_coder:
                avg_time = sum(r["total_time"] for r in successful_coder) / len(successful_coder)
                print(f"  平均执行时间: {avg_time:.2f} 秒")
            for r in coder_results:
                status = "✅" if r.get("success", False) else "❌"
                print(f"  {status} {r['task_name']}: {r.get('total_time', 0):.2f} 秒")
            print()

        # Reviewer 统计
        if reviewer_results:
            print("Reviewer 节点:")
            successful_reviewer = [r for r in reviewer_results if r.get("success", False)]
            if successful_reviewer:
                avg_time = sum(r["total_time"] for r in successful_reviewer) / len(successful_reviewer)
            print(f"  平均执行时间: {avg_time:.2f} 秒")
            for r in reviewer_results:
                status = "✅" if r.get("success", False) else "❌"
                print(f"  {status} {r['task_name']}: {r.get('total_time', 0):.2f} 秒")
            print()

        # 保存 JSON 报告
        report_file = Path(__file__).parent.parent / "docs" / f"model_router_benchmark_{self.test_mode}.json"
        report_file.write_text(json.dumps({
            "test_mode": self.test_mode,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "api_key_configured": bool(os.getenv('ANTHROPIC_API_KEY')),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "results": self.results
        }, indent=2))

        print(f"详细报告已保存至: {report_file}")
        print(f"{'='*60}")


async def main():
    """主函数"""
    # 检测测试模式
    if os.getenv("ANTHROPIC_API_KEY"):
        test_mode = "hybrid"
        print("✅ 检测到 ANTHROPIC_API_KEY，使用混合模式（智能路由）")
    else:
        test_mode = "local"
        print("⚠️  未检测到 ANTHROPIC_API_KEY，使用本地模型模式")

    # 运行测试
    runner = BenchmarkRunner(test_mode=test_mode)
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
