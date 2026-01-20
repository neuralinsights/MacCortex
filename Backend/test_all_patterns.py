#!/usr/bin/env python3
"""
测试所有 5 个 Pattern 的端到端功能
验证统一响应格式（output 字段）
"""

import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

class PatternTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []

    async def test_pattern(self, pattern_id: str, text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个 Pattern"""
        request_data = {
            "request_id": f"test-{pattern_id}",
            "pattern_id": pattern_id,
            "text": text,
            "parameters": parameters,
        }

        try:
            response = await self.client.post(f"{BASE_URL}/execute", json=request_data)
            response.raise_for_status()
            result = response.json()

            # 验证响应格式
            assert "success" in result, "Missing 'success' field"
            assert "output" in result, f"Missing 'output' field in {pattern_id}"
            assert "metadata" in result, "Missing 'metadata' field"
            assert "duration" in result, "Missing 'duration' field"

            return {
                "pattern_id": pattern_id,
                "status": "✅ PASS",
                "output_length": len(result["output"]),
                "duration": result["duration"],
                "metadata": result["metadata"],
            }
        except Exception as e:
            return {
                "pattern_id": pattern_id,
                "status": f"❌ FAIL",
                "error": str(e),
            }

    async def run_all_tests(self):
        """运行所有测试"""
        tests = [
            # Test 1: SummarizePattern
            {
                "pattern_id": "summarize",
                "text": "MacCortex 是下一代 macOS 个人智能基础设施，基于 Swarm Intelligence + Personal Infrastructure 融合架构，提供本地优先的 AI 能力，支持 Notes 管理、智能搜索、格式转换等核心功能。项目采用 Swift + Python 混合架构，Swift 负责 macOS 原生集成，Python 负责 AI Pattern 处理。",
                "parameters": {
                    "length": "medium",
                    "style": "bullet",
                    "language": "zh-CN",
                },
            },
            # Test 2: ExtractPattern
            {
                "pattern_id": "extract",
                "text": "张三是苹果公司的工程师，他的邮箱是 zhangsan@apple.com，电话是 +86-138-0000-0000。他在北京和上海两地工作，项目启动日期是 2026-01-20。",
                "parameters": {
                    "entity_types": ["person", "organization", "location"],
                    "extract_keywords": True,
                    "extract_contacts": True,
                    "extract_dates": True,
                    "language": "zh-CN",
                },
            },
            # Test 3: TranslatePattern
            {
                "pattern_id": "translate",
                "text": "MacCortex 是下一代 macOS 个人智能基础设施",
                "parameters": {
                    "target_language": "en",
                    "source_language": "zh-CN",
                    "style": "formal",
                },
            },
            # Test 4: FormatPattern (JSON to YAML)
            {
                "pattern_id": "format",
                "text": '{"name": "MacCortex", "version": "0.1.0", "platform": "macOS"}',
                "parameters": {
                    "from_format": "json",
                    "to_format": "yaml",
                    "prettify": True,
                },
            },
            # Test 5: SearchPattern (Web search)
            {
                "pattern_id": "search",
                "text": "macOS SwiftUI best practices 2026",
                "parameters": {
                    "search_type": "web",
                    "engine": "duckduckgo",
                    "num_results": 3,
                },
            },
        ]

        print("\n" + "="*60)
        print("MacCortex Pattern 端到端测试")
        print("="*60 + "\n")

        for test in tests:
            print(f"\n🧪 测试 {test['pattern_id']}...")
            result = await self.test_pattern(
                test["pattern_id"],
                test["text"],
                test["parameters"]
            )
            self.results.append(result)

            if result["status"] == "✅ PASS":
                print(f"   {result['status']}")
                print(f"   输出长度: {result['output_length']} 字符")
                print(f"   执行时间: {result['duration']:.3f}s")
                print(f"   模式: {result['metadata'].get('mode', 'N/A')}")
            else:
                print(f"   {result['status']}")
                print(f"   错误: {result.get('error', 'Unknown')}")

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)

        passed = sum(1 for r in self.results if "✅" in r["status"])
        total = len(self.results)

        print(f"\n✅ 通过: {passed}/{total}")
        print(f"❌ 失败: {total - passed}/{total}")
        print(f"📊 通过率: {passed/total*100:.1f}%\n")

        if passed == total:
            print("🎉 所有测试通过！统一响应格式验证成功！\n")
        else:
            print("⚠️  部分测试失败，请检查日志\n")

        await self.client.aclose()
        return passed == total

async def main():
    tester = PatternTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
