"""
MacCortex Reflector Agent

整体反思节点，负责：
1. 在所有子任务完成后进行整体评估
2. 检查是否满足整体验收标准（overall_acceptance）
3. 生成任务总结与改进建议
4. 决定是否需要重新规划或继续迭代
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import SwarmState


class ReflectorNode:
    """
    整体反思节点

    在所有子任务完成后，评估整体质量并决定下一步行动。
    """

    def __init__(
        self,
        workspace_path: Path,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.3,
        llm: Optional[Any] = None,  # 可选的 LLM 实例（用于测试）
        fallback_to_local: bool = True
    ):
        """
        初始化 Reflector 节点

        Args:
            workspace_path: 工作空间路径
            model: LLM 模型名称
            temperature: LLM 温度（0.3 适合反思任务）
            llm: 可选的 LLM 实例（用于测试时注入 mock）
            fallback_to_local: 当 API Key 缺失时是否降级到本地模型
        """
        # 使用提供的 LLM 或创建新的
        if llm is not None:
            self.llm = llm
            self.using_local_model = False
        else:
            # Anthropic API Key
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                if fallback_to_local:
                    # 使用新版 langchain-ollama 包
                    from langchain_ollama import ChatOllama
                    print("⚠️  ReflectorNode: 降级使用本地 Ollama 模型（qwen3:14b）")
                    self.llm = ChatOllama(
                        model=os.getenv("OLLAMA_MODEL", "qwen3:14b"),
                        temperature=temperature,
                        base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
                    )
                    self.using_local_model = True
                else:
                    raise ValueError("未设置 ANTHROPIC_API_KEY 环境变量")
            else:
                self.llm = ChatAnthropic(
                    model=model,
                    temperature=temperature,
                    anthropic_api_key=api_key
                )
                self.using_local_model = False

        self.workspace = Path(workspace_path)

        # 系统提示词（根据是否使用本地模型选择）
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        # 本地模型使用简化的提示词
        if self.using_local_model:
            return """你是任务评估专家。评估任务是否完成。

⚠️ 必须输出 JSON 格式！

输出格式（直接输出 JSON）：
{"passed": true, "summary": "总结", "recommendation": "completed"}
或
{"passed": false, "summary": "总结", "feedback": "问题", "recommendation": "retry"}

只输出 JSON，不要其他文字。"""

        # Claude API 使用详细的提示词
        return """你是 MacCortex Swarm 的 Reflector Agent，负责整体反思与质量评估。

你的职责：
1. 审查所有已完成的子任务结果
2. 评估是否满足整体验收标准（overall_acceptance）
3. 生成任务执行总结
4. 提供改进建议（如果未达标）

输出 JSON 格式：
```json
{
  "passed": true/false,
  "summary": "整体执行总结（2-3 段）",
  "feedback": "改进建议（如果未通过）",
  "achievements": ["成功完成的关键点"],
  "issues": ["存在的问题或不足"],
  "recommendation": "continue（继续）/ retry（重新规划）/ completed（完全满足）"
}
```

评估标准：
- 所有子任务是否都通过（passed=True）
- 是否满足 overall_acceptance 中的每一条标准
- 代码/研究/工具执行的质量是否达标
- 是否存在明显的缺陷或遗漏

如果未通过，明确指出：
- 哪些验收标准未满足
- 哪些子任务需要重新执行
- 建议的改进方向
"""

    async def reflect(self, state: SwarmState) -> SwarmState:
        """
        执行整体反思

        Args:
            state: 当前 Swarm 状态

        Returns:
            SwarmState: 更新后的状态
        """
        user_task = state["user_input"]
        plan = state.get("plan", {})
        subtask_results = state.get("subtask_results", [])
        overall_acceptance = plan.get("overall_acceptance", []) if plan else []

        # 检查是否有子任务结果
        if not subtask_results:
            state["status"] = "completed"
            state["final_output"] = {
                "passed": True,
                "summary": "无子任务需要执行，任务自动完成。",
                "achievements": [],
                "issues": []
            }
            return state

        # 构建反思提示
        prompt = self._build_reflection_prompt(
            user_task=user_task,
            subtask_results=subtask_results,
            overall_acceptance=overall_acceptance
        )

        print(f"[Reflector] 开始整体反思...")
        print(f"[Reflector] 评估 {len(subtask_results)} 个子任务结果")

        # 调用 LLM 进行反思
        response = await self.llm.ainvoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ])

        # 解析反思结果
        try:
            reflection = self._parse_reflection(response.content)

            # 更新状态
            state["final_output"] = reflection

            # 根据反思结果决定下一步
            if reflection["passed"]:
                state["status"] = "completed"
                print(f"[Reflector] ✅ 整体验收通过")
            else:
                # 未通过，但不再重试（Reflector 是最后一步）
                state["status"] = "failed"
                state["error_message"] = f"整体验收未通过：{reflection.get('feedback', '未满足验收标准')}"
                print(f"[Reflector] ❌ 整体验收未通过")

            print(f"[Reflector] 总结: {reflection['summary'][:100]}...")

            return state

        except Exception as e:
            # 反思失败，标记错误
            state["status"] = "failed"
            state["error_message"] = f"反思失败：{str(e)}"
            state["final_output"] = {
                "passed": False,
                "summary": f"反思过程出错：{str(e)}",
                "issues": [str(e)]
            }
            print(f"[Reflector] 错误: {state['error_message']}")
            return state

    def _build_reflection_prompt(
        self,
        user_task: str,
        subtask_results: List[Dict[str, Any]],
        overall_acceptance: List[str]
    ) -> str:
        """
        构建反思提示词

        Args:
            user_task: 原始用户任务
            subtask_results: 所有子任务结果
            overall_acceptance: 整体验收标准

        Returns:
            str: 反思提示词
        """
        prompt_parts = []

        # 1. 原始任务
        prompt_parts.append(f"## 原始任务\n{user_task}")

        # 2. 整体验收标准
        if overall_acceptance:
            prompt_parts.append("\n## 整体验收标准")
            for idx, criterion in enumerate(overall_acceptance, 1):
                prompt_parts.append(f"{idx}. {criterion}")

        # 3. 子任务执行结果
        prompt_parts.append(f"\n## 子任务执行结果（共 {len(subtask_results)} 个）\n")

        for idx, result in enumerate(subtask_results, 1):
            passed_emoji = "✅" if result.get("passed") else "❌"
            desc = result.get("subtask_description", result.get("description", f"子任务 {idx}"))

            prompt_parts.append(f"### {idx}. {passed_emoji} {desc}")
            prompt_parts.append(f"- **状态**: {'通过' if result.get('passed') else '失败'}")

            # 显示不同类型的输出
            if result.get("code"):
                prompt_parts.append(f"- **代码**:\n```\n{result['code'][:200]}...\n```")
            if result.get("output"):
                prompt_parts.append(f"- **输出**: {result['output'][:200]}...")
            if result.get("research_result"):
                prompt_parts.append(f"- **调研结果**: {result['research_result'][:200]}...")
            if result.get("tool_result"):
                prompt_parts.append(f"- **工具结果**: {result['tool_result'][:200]}...")
            if result.get("error_message"):
                prompt_parts.append(f"- **错误信息**: {result['error_message']}")

            prompt_parts.append("")

        # 4. 反思要求
        prompt_parts.append("""
## 反思要求

请基于以上信息，评估任务整体执行情况：

1. 所有子任务是否都成功完成？
2. 是否满足整体验收标准的每一条？
3. 代码/研究/工具执行的质量如何？
4. 是否存在明显的缺陷、遗漏或改进空间？

请以 JSON 格式输出评估结果。
""")

        return "\n".join(prompt_parts)

    def _parse_reflection(self, content: str) -> Dict[str, Any]:
        """
        解析 LLM 反思输出

        Args:
            content: LLM 输出内容

        Returns:
            Dict: 解析后的反思结果

        Raises:
            ValueError: 如果解析失败
        """
        import re

        # 提取 JSON 部分（可能包含在 Markdown 代码块中）
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析整个内容
            json_str = content

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析 JSON: {e}\n内容：{content[:200]}...")

        # 验证必需字段
        if "passed" not in parsed:
            raise ValueError("反思结果缺少 'passed' 字段")

        if "summary" not in parsed:
            raise ValueError("反思结果缺少 'summary' 字段")

        # 设置默认值
        reflection = {
            "passed": parsed["passed"],
            "summary": parsed["summary"],
            "feedback": parsed.get("feedback", ""),
            "achievements": parsed.get("achievements", []),
            "issues": parsed.get("issues", []),
            "recommendation": parsed.get("recommendation", "completed" if parsed["passed"] else "retry")
        }

        return reflection


def create_reflector_node(
    workspace_path: Path,
    **kwargs
) -> callable:
    """
    创建 Reflector 节点（用于 LangGraph）

    Args:
        workspace_path: 工作空间路径
        **kwargs: 传递给 ReflectorNode 的参数

    Returns:
        Reflector 节点函数
    """
    reflector = ReflectorNode(workspace_path, **kwargs)

    async def reflector_node(state: SwarmState) -> SwarmState:
        """Reflector 节点函数"""
        return await reflector.reflect(state)

    return reflector_node


# 用于测试的简化函数
async def test_reflector():
    """测试 Reflector 节点"""
    import tempfile
    from ..state import create_initial_state

    workspace = Path(tempfile.mkdtemp())
    print(f"工作空间: {workspace}")

    # 模拟状态
    state = create_initial_state("创建一个简单的计算器")
    state["plan"] = {
        "subtasks": [
            {"id": "1", "type": "code", "description": "实现加法", "dependencies": [], "acceptance_criteria": ["正确计算"], "tool_name": None, "tool_args": None},
            {"id": "2", "type": "code", "description": "实现减法", "dependencies": [], "acceptance_criteria": ["正确计算"], "tool_name": None, "tool_args": None}
        ],
        "overall_acceptance": ["计算器功能完整", "代码通过测试"]
    }
    state["subtask_results"] = [
        {"subtask_id": "1", "subtask_description": "实现加法", "code": "def add(a, b): return a + b", "output": "测试通过", "passed": True},
        {"subtask_id": "2", "subtask_description": "实现减法", "code": "def sub(a, b): return a - b", "output": "测试通过", "passed": True}
    ]
    state["status"] = "reflecting"

    # 创建 Reflector
    reflector = ReflectorNode(workspace)

    # 执行反思
    final_state = await reflector.reflect(state)

    print(f"\n=== 反思结果 ===")
    print(f"状态: {final_state['status']}")
    print(f"通过: {final_state['final_output']['passed']}")
    print(f"总结: {final_state['final_output']['summary']}")


if __name__ == "__main__":
    import sys
    import asyncio

    # 添加父目录到 sys.path 以支持相对导入
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    asyncio.run(test_reflector())
