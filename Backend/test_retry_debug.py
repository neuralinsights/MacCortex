"""临时调试脚本 - 测试重试路由逻辑"""
import asyncio
from pathlib import Path
import tempfile
from unittest.mock import Mock, AsyncMock
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.swarm_graph import create_full_swarm_graph
from src.orchestration.state import create_initial_state
from tests.orchestration.test_integration import create_mock_graph


async def test_retry_with_debug():
    """调试重试流程"""
    tmp_path = Path(tempfile.mkdtemp())
    mock_llm = AsyncMock()

    # Planner 响应
    planner_response = Mock()
    planner_response.content = """```json
{
  "task": "写一个函数",
  "subtasks": [
    {
      "id": 1,
      "type": "code",
      "description": "写一个函数",
      "language": "python",
      "acceptance_criteria": ["函数正确"]
    }
  ],
  "overall_acceptance": ["所有子任务通过"]
}
```"""

    # 第一次 Coder 响应（错误代码）
    coder_response_1 = Mock()
    coder_response_1.content = """```python
def bad_function():
    return 1 / 0  # ZeroDivisionError
```"""

    # 第一次 Reviewer 响应（失败）
    reviewer_response_1 = Mock()
    reviewer_response_1.content = """```json
{
  "passed": false,
  "feedback": "代码存在 ZeroDivisionError，需修复"
}
```"""

    # 第二次 Coder 响应（修复后）
    coder_response_2 = Mock()
    coder_response_2.content = """```python
def good_function():
    return 42
```"""

    # 第二次 Reviewer 响应（通过）
    reviewer_response_2 = Mock()
    reviewer_response_2.content = """```json
{
  "passed": true,
  "feedback": "代码已修复，测试通过"
}
```"""

    # 记录所有 LLM 调用
    call_count = [0]
    responses = [
        planner_response,
        coder_response_1,
        reviewer_response_1,
        coder_response_2,
        reviewer_response_2
    ]

    async def tracked_ainvoke(messages):
        """追踪 LLM 调用"""
        idx = call_count[0]
        call_count[0] += 1
        print(f"\n=== LLM Call #{idx + 1} ===")
        print(f"System message: {messages[0].content[:100] if messages else 'N/A'}...")
        print(f"Returning: {responses[idx].content[:100]}...")
        return responses[idx]

    mock_llm.ainvoke = tracked_ainvoke

    # 创建图
    graph, _, _ = create_mock_graph(tmp_path, mock_llm=mock_llm)

    # 执行
    state = create_initial_state("写一个函数")
    print("\n=== Starting execution ===")
    final_state = await graph.ainvoke(state)

    print(f"\n=== Final state ===")
    print(f"Status: {final_state['status']}")
    print(f"Iteration count: {final_state.get('iteration_count', 0)}")
    print(f"Total LLM calls: {call_count[0]}")


if __name__ == "__main__":
    asyncio.run(test_retry_with_debug())
