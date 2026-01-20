#!/usr/bin/env python3
"""
MacCortex Pattern 性能基准测试
测试所有 5 个 Pattern 的性能指标
"""

import asyncio
import httpx
import time
import statistics
from typing import List, Dict, Any

BASE_URL = "http://127.0.0.1:8000"

class PerformanceBenchmark:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.results = {}

    async def benchmark_pattern(
        self,
        pattern_id: str,
        text: str,
        parameters: Dict[str, Any],
        iterations: int = 10
    ) -> Dict[str, Any]:
        """性能基准测试单个 Pattern"""
        latencies = []
        errors = 0

        print(f"\n🔬 测试 {pattern_id} ({iterations} 次迭代)...")

        for i in range(iterations):
            request_data = {
                "request_id": f"perf-{pattern_id}-{i}",
                "pattern_id": pattern_id,
                "text": text,
                "parameters": parameters,
            }

            try:
                start_time = time.time()
                response = await self.client.post(f"{BASE_URL}/execute", json=request_data)
                response.raise_for_status()
                result = response.json()
                end_time = time.time()

                if result["success"]:
                    latency = end_time - start_time
                    latencies.append(latency)
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                print(f"   ❌ 迭代 {i+1} 失败: {str(e)}")

        if latencies:
            return {
                "pattern_id": pattern_id,
                "iterations": len(latencies),
                "errors": errors,
                "min_latency": min(latencies),
                "max_latency": max(latencies),
                "avg_latency": statistics.mean(latencies),
                "median_latency": statistics.median(latencies),
                "stdev_latency": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            }
        else:
            return {
                "pattern_id": pattern_id,
                "errors": errors,
                "status": "failed",
            }

    async def benchmark_concurrent(
        self,
        requests: List[Dict[str, Any]],
        concurrency: int = 5
    ) -> Dict[str, Any]:
        """测试并发处理能力"""
        print(f"\n⚡️ 并发测试 ({concurrency} 并发请求)...")

        start_time = time.time()
        tasks = []

        for request_data in requests[:concurrency]:
            task = self.client.post(f"{BASE_URL}/execute", json=request_data)
            tasks.append(task)

        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
            failed = len(responses) - successful
            total_time = end_time - start_time

            return {
                "concurrency": concurrency,
                "total_requests": len(requests[:concurrency]),
                "successful": successful,
                "failed": failed,
                "total_time": total_time,
                "avg_time_per_request": total_time / concurrency,
            }
        except Exception as e:
            return {
                "concurrency": concurrency,
                "error": str(e),
                "status": "failed",
            }

    async def run_benchmarks(self):
        """运行所有性能基准测试"""
        print("\n" + "="*70)
        print("MacCortex Pattern 性能基准测试")
        print("="*70)

        # 定义测试用例
        test_cases = [
            {
                "pattern_id": "summarize",
                "text": "MacCortex 是下一代 macOS 个人智能基础设施，基于 Swarm Intelligence + Personal Infrastructure 融合架构，提供本地优先的 AI 能力，支持 Notes 管理、智能搜索、格式转换等核心功能。项目采用 Swift + Python 混合架构，Swift 负责 macOS 原生集成，Python 负责 AI Pattern 处理。系统集成 MLX（Apple Silicon 优化）和 Ollama 本地 LLM，实现端到端的本地化智能处理。",
                "parameters": {"length": "short", "style": "paragraph", "language": "zh-CN"},
            },
            {
                "pattern_id": "extract",
                "text": "张三是苹果公司的工程师，他的邮箱是 zhangsan@apple.com，电话是 +86-138-0000-0000。他在北京和上海两地工作，项目启动日期是 2026-01-20。",
                "parameters": {
                    "entity_types": ["person", "organization", "location"],
                    "extract_keywords": True,
                    "extract_contacts": True,
                    "extract_dates": True,
                },
            },
            {
                "pattern_id": "translate",
                "text": "MacCortex 是下一代 macOS 个人智能基础设施",
                "parameters": {"target_language": "en", "style": "formal"},
            },
            {
                "pattern_id": "format",
                "text": '{"name": "MacCortex", "version": "0.1.0", "platform": "macOS"}',
                "parameters": {"from_format": "json", "to_format": "yaml", "prettify": True},
            },
            {
                "pattern_id": "search",
                "text": "macOS SwiftUI best practices",
                "parameters": {"search_type": "web", "engine": "duckduckgo", "num_results": 3},
            },
        ]

        # 单个 Pattern 性能测试
        print("\n📊 单个 Pattern 性能测试 (每个 10 次迭代)")
        print("-" * 70)

        for test_case in test_cases:
            result = await self.benchmark_pattern(
                test_case["pattern_id"],
                test_case["text"],
                test_case["parameters"],
                iterations=10
            )
            self.results[test_case["pattern_id"]] = result

            if "status" not in result or result.get("status") != "failed":
                print(f"   ✅ {result['pattern_id']}")
                print(f"      平均延迟: {result['avg_latency']*1000:.1f}ms")
                print(f"      中位延迟: {result['median_latency']*1000:.1f}ms")
                print(f"      最小延迟: {result['min_latency']*1000:.1f}ms")
                print(f"      最大延迟: {result['max_latency']*1000:.1f}ms")
                print(f"      标准差:   {result['stdev_latency']*1000:.1f}ms")
                if result['errors'] > 0:
                    print(f"      ⚠️  错误: {result['errors']} 次")
            else:
                print(f"   ❌ {result['pattern_id']} - 测试失败")

        # 并发测试
        concurrent_requests = [
            {
                "request_id": f"concurrent-{i}",
                "pattern_id": test_cases[i % len(test_cases)]["pattern_id"],
                "text": test_cases[i % len(test_cases)]["text"],
                "parameters": test_cases[i % len(test_cases)]["parameters"],
            }
            for i in range(10)
        ]

        concurrent_result = await self.benchmark_concurrent(concurrent_requests, concurrency=5)
        self.results["concurrent"] = concurrent_result

        # 总结报告
        print("\n" + "="*70)
        print("性能测试总结")
        print("="*70)

        # 计算总体平均延迟
        valid_results = [
            r for r in self.results.values()
            if isinstance(r, dict) and "avg_latency" in r
        ]

        if valid_results:
            overall_avg = statistics.mean([r["avg_latency"] for r in valid_results])
            overall_median = statistics.median([r["median_latency"] for r in valid_results])

            print(f"\n📊 总体性能:")
            print(f"   平均延迟: {overall_avg*1000:.1f}ms")
            print(f"   中位延迟: {overall_median*1000:.1f}ms")

            # 性能目标检查
            target_latency = 2.5  # 目标: < 2.5s
            print(f"\n🎯 性能目标: < {target_latency*1000:.0f}ms")

            passed = [r for r in valid_results if r["avg_latency"] < target_latency]
            print(f"   通过: {len(passed)}/{len(valid_results)} Patterns")

            if overall_avg < target_latency:
                print(f"   ✅ 总体性能达标 (平均 {overall_avg*1000:.1f}ms < {target_latency*1000:.0f}ms)")
            else:
                print(f"   ⚠️  总体性能未达标 (平均 {overall_avg*1000:.1f}ms > {target_latency*1000:.0f}ms)")

        # 并发测试结果
        if "concurrent" in self.results:
            cr = self.results["concurrent"]
            if "error" not in cr:
                print(f"\n⚡️ 并发测试:")
                print(f"   并发数: {cr['concurrency']}")
                print(f"   成功: {cr['successful']}/{cr['total_requests']}")
                print(f"   总耗时: {cr['total_time']*1000:.1f}ms")
                print(f"   平均每请求: {cr['avg_time_per_request']*1000:.1f}ms")

                if cr['failed'] == 0:
                    print(f"   ✅ 并发测试通过 (无失败)")
                else:
                    print(f"   ⚠️  部分请求失败 ({cr['failed']} 失败)")

        print("\n" + "="*70 + "\n")

        await self.client.aclose()

async def main():
    benchmark = PerformanceBenchmark()
    await benchmark.run_benchmarks()

if __name__ == "__main__":
    asyncio.run(main())
