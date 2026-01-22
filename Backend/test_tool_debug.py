"""调试工具任务执行"""
import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.swarm_graph import create_full_swarm_graph
from src.orchestration.state import create_initial_state
from tests.orchestration.test_integration import create_mock_graph


async def main():
    tmp_path = Path(tempfile.mkdtemp())
    print(f"Workspace: {tmp_path}")

    mock_llm = AsyncMock()

    # Planner 响应
    planner_response = Mock()
    planner_response.content = f"""```json
{{
  "task": "创建测试文件",
  "subtasks": [
    {{
      "id": 1,
      "type": "tool",
      "description": "创建 hello.txt",
      "tool_name": "write_file",
      "tool_args": {{
        "path": "{tmp_path}/hello.txt",
        "content": "Hello, MacCortex!"
      }},
      "acceptance_criteria": ["文件创建成功"]
    }}
  ],
  "overall_acceptance": ["所有工具任务完成"]
}}
```"""

    mock_llm.ainvoke = AsyncMock(return_value=planner_response)

    # 创建图
    graph, _, _ = create_mock_graph(tmp_path, mock_llm=mock_llm)

    # 执行
    state = create_initial_state("创建测试文件 hello.txt")
    final_state = await graph.ainvoke(state)

    print(f"\n=== 结果 ===")
    print(f"Status: {final_state['status']}")
    print(f"Subtask results: {len(final_state['subtask_results'])}")

    if final_state['subtask_results']:
        result = final_state['subtask_results'][0]
        print(f"\n首个子任务结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")

    # 检查文件是否创建
    hello_file = tmp_path / "hello.txt"
    if hello_file.exists():
        print(f"\n✅ 文件创建成功: {hello_file}")
        print(f"内容: {hello_file.read_text()}")
    else:
        print(f"\n❌ 文件未创建: {hello_file}")


if __name__ == "__main__":
    asyncio.run(main())
