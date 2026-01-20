#!/usr/bin/env python3
"""
测试 ChromaDB 语义搜索功能
"""

import asyncio
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

async def test_semantic_search():
    """测试语义搜索"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 准备测试数据
        request_data = {
            "request_id": "test-semantic-search",
            "pattern_id": "search",
            "text": "Apple Silicon 机器学习框架性能对比",
            "parameters": {
                "search_type": "semantic",
                "num_results": 5,
                "similarity_threshold": 0.7,
            },
        }

        print("\n" + "="*60)
        print("ChromaDB 语义搜索测试")
        print("="*60 + "\n")

        print(f"📝 查询: {request_data['text']}")
        print(f"🔍 搜索类型: semantic")
        print(f"📊 结果数量: 5")
        print(f"⚡️ 相似度阈值: 0.7\n")

        try:
            response = await client.post(f"{BASE_URL}/execute", json=request_data)
            response.raise_for_status()
            result = response.json()

            if result["success"]:
                print("✅ 测试成功!")
                print(f"⏱️  执行时间: {result['duration']:.3f}s")
                print(f"🤖 模式: {result['metadata'].get('mode', 'N/A')}")

                # 解析输出
                output_data = json.loads(result["output"])

                print(f"\n📊 搜索结果:")
                if "results" in output_data and output_data["results"]:
                    for i, item in enumerate(output_data["results"][:3], 1):
                        print(f"\n  {i}. {item.get('title', 'N/A')}")
                        print(f"     得分: {item.get('score', 'N/A')}")
                        print(f"     内容: {item.get('content', 'N/A')[:100]}...")
                else:
                    print("  ⚠️  无搜索结果")

                if output_data.get("summary"):
                    print(f"\n📝 摘要:\n  {output_data['summary']}")

                print("\n🎉 ChromaDB 语义搜索功能正常!\n")
                return True
            else:
                print(f"❌ 测试失败: {result.get('error', 'Unknown error')}\n")
                return False

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP 错误: {e.response.status_code}")
            print(f"   响应: {e.response.text}\n")
            return False
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}\n")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_semantic_search())
    exit(0 if success else 1)
