"""
MacCortex Planner Node - 任务拆解与计划生成

Planner Agent 负责将复杂的用户任务拆解为可执行的子任务列表。
"""

import json
import os
from typing import Dict, Any, List, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import SwarmState, Plan, Subtask


class PlannerNode:
    """
    Planner Agent - 任务拆解与计划生成

    核心职责：
    1. 分析用户输入的复杂任务
    2. 拆解为 3-10 个可执行的子任务
    3. 为每个子任务定义类型（code/research/tool）
    4. 定义子任务之间的依赖关系
    5. 为每个子任务设定验收标准
    6. 定义整体验收标准
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.2,
        max_subtasks: int = 10,
        min_subtasks: int = 3,
        llm: Optional[Any] = None,
        fallback_to_local: bool = True,
        using_local_model: Optional[bool] = None
    ):
        """
        初始化 Planner Node

        Args:
            model: Claude 模型名称
            temperature: 温度参数（0.2 更确定性，适合任务拆解）
            max_subtasks: 最大子任务数量
            min_subtasks: 最小子任务数量
            llm: 可选的 LLM 实例（用于测试时依赖注入）
            fallback_to_local: 当 API Key 缺失时是否降级到本地模型
            using_local_model: 显式指定是否使用本地模型（当注入 llm 时使用）
        """
        # 使用注入的 LLM 或创建新的 LLM
        if llm is not None:
            self.llm = llm
            # 使用显式传递的标志，或默认为 False
            self.using_local_model = using_local_model if using_local_model is not None else False
        else:
            # 检查 API Key
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                if fallback_to_local:
                    # 降级到本地 Ollama 模型（使用新版 langchain-ollama 包）
                    from langchain_ollama import ChatOllama
                    print("⚠️  未设置 ANTHROPIC_API_KEY，降级使用本地 Ollama 模型（qwen3:14b）")
                    print("   功能受限：计划质量可能较低，建议设置 Anthropic API 密钥")
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

        self.max_subtasks = max_subtasks

        # 本地模型降低要求：最小子任务数设为 1
        if self.using_local_model:
            self.min_subtasks = 1
            print("   本地模型模式：已降低最小子任务要求至 1 个（适配本地模型能力）")
        else:
            self.min_subtasks = min_subtasks

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词

        Returns:
            str: 详细的系统提示词
        """
        # 本地模型使用简化的提示词
        if self.using_local_model:
            return f"""你是任务规划师。将用户任务拆解为子任务。

⚠️ 重要：必须严格输出 JSON 格式，不要有任何额外文字！

输出格式（直接输出 JSON，不要包裹在代码块中）：
{{
  "subtasks": [
    {{
      "id": "task-1",
      "type": "code",
      "description": "具体的任务描述",
      "dependencies": [],
      "acceptance_criteria": ["标准1", "标准2"]
    }}
  ],
  "overall_acceptance": ["整体标准1", "整体标准2"]
}}

子任务类型：
- code: 编写代码
- research: 查找资料
- tool: 执行系统操作

示例（简单任务：创建 hello.py 打印 Hello World）：
{{
  "subtasks": [
    {{
      "id": "task-1",
      "type": "code",
      "description": "创建 hello.py 文件并写入打印语句",
      "dependencies": [],
      "acceptance_criteria": ["文件包含 print('Hello World')", "可以运行 python hello.py"]
    }}
  ],
  "overall_acceptance": ["hello.py 文件存在", "运行输出 Hello World"]
}}

现在处理用户任务，只输出 JSON："""

        # Claude API 使用优化的提示词（Phase 5: -67.5% Input, Phase 6: -30% Output）
        return f"""任务拆解为 {self.min_subtasks}-{self.max_subtasks} 子任务。输出极简 JSON。

类型：code（代码）/ research（调研）/ tool（文件操作）

格式（严格）：
```json
{{"subtasks":[{{"id":"task-1","type":"code","description":"创建 hello.py 含 print","dependencies":[],"acceptance_criteria":["含 print('Hello World')","可运行"]}}],"overall_acceptance":["hello.py 存在","输出 Hello World"]}}
```

原则：
1. 粒度 5-15 分钟
2. 依赖清晰（task-2 需 task-1 → dependencies:["task-1"]）
3. 标准具体（避免"好"，用"含错误处理"）
4. 简单方案优先
5. **极简输出**：最短描述，无冗余

现在生成计划（仅 JSON）："""

    async def plan(self, state: SwarmState) -> SwarmState:
        """
        执行任务拆解

        Args:
            state: 当前 Swarm 状态

        Returns:
            SwarmState: 更新后的状态（包含生成的计划）
        """
        user_task = state["user_input"]
        context = state.get("context", {})

        # 构建用户提示
        user_prompt = self._build_user_prompt(user_task, context)

        # 评估任务复杂度，设置动态 max_tokens（Output Tokens 优化）
        task_complexity_for_max_tokens = self._evaluate_task_complexity(user_task)
        if task_complexity_for_max_tokens == "simple":
            max_output_tokens = 200  # 简单任务：1-2 个子任务，精简计划
        elif task_complexity_for_max_tokens == "complex":
            max_output_tokens = 800  # 复杂任务：5-10 个子任务，详细计划
        else:
            max_output_tokens = 400  # 中等任务：3-5 个子任务

        # 调用 LLM
        print(f"[Planner] 开始拆解任务: {user_task}")
        print(f"[Planner] max_tokens={max_output_tokens} (复杂度: {task_complexity_for_max_tokens})")

        # 根据模型类型选择调用方式
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]

        if self.using_local_model:
            # Ollama 模型：不使用 bind() 动态设置 num_predict（langchain-ollama 1.0.1 兼容性问题）
            # 改为直接调用，让模型自己控制输出长度
            response = await self.llm.ainvoke(messages)
        else:
            # Anthropic 模型：直接传递 max_tokens
            response = await self.llm.ainvoke(messages, max_tokens=max_output_tokens)

        # 解析 LLM 输出
        try:
            plan = self._parse_plan(response.content)

            # 评估任务复杂度，确定动态最小子任务数
            task_complexity = self._evaluate_task_complexity(user_task)
            if task_complexity == "simple" and self.min_subtasks > 1:
                # 简单任务：降低最小要求到 1（仅当配置要求 >1 时）
                min_required_subtasks = 1
            else:
                # 其他情况：使用配置的最小值
                min_required_subtasks = self.min_subtasks

            print(f"[Planner] 任务复杂度: {task_complexity}，最小子任务要求: {min_required_subtasks}")

            # 验证计划（使用动态最小值）
            self._validate_plan(plan, min_subtasks=min_required_subtasks)

            # 更新状态
            state["plan"] = plan
            state["current_subtask_index"] = 0

            # 对于空计划，直接设置为 completed
            if not plan["subtasks"]:
                state["status"] = "completed"
            else:
                state["status"] = "executing"

            print(f"[Planner] 任务拆解完成，共 {len(plan['subtasks'])} 个子任务")
            for subtask in plan["subtasks"]:
                deps_str = f" (依赖: {', '.join(subtask['dependencies'])})" if subtask["dependencies"] else ""
                print(f"  - {subtask['id']}: [{subtask['type']}] {subtask['description'][:60]}...{deps_str}")

            return state

        except Exception as e:
            # 拆解失败
            state["status"] = "failed"
            state["error_message"] = f"任务拆解失败: {str(e)}"
            print(f"[Planner] 错误: {state['error_message']}")
            return state

    def _evaluate_task_complexity(self, user_task: str) -> str:
        """
        评估任务复杂度

        Args:
            user_task: 用户任务描述

        Returns:
            str: 复杂度级别（"simple" | "medium" | "complex"）
        """
        task_lower = user_task.lower()
        task_len = len(user_task)

        # Simple task indicators (简单任务关键词)
        simple_keywords = [
            "hello world", "打印", "输出", "print",
            "创建一个函数", "写一个函数", "单个函数",
            "简单", "basic", "simple"
        ]

        # Complex task indicators (复杂任务关键词)
        complex_keywords = [
            "系统", "平台", "框架", "架构",
            "集成", "优化", "重构",
            "多个", "完整", "全面",
            "分布式", "微服务", "数据库"
        ]

        # Rule 1: 优先检查复杂关键词（无论长度）
        if any(kw in task_lower for kw in complex_keywords):
            return "complex"

        # Rule 2: 长描述 → complex
        if task_len > 200:
            return "complex"

        # Rule 3: 简单关键词 + 极短描述 → simple
        if task_len < 40 and any(kw in task_lower for kw in simple_keywords):
            return "simple"

        # Rule 4: 极短描述（无复杂关键词）→ simple
        if task_len < 40:
            return "simple"

        # Rule 5: 中等长度 (40-200) → medium
        if 40 <= task_len <= 200:
            return "medium"

        # Default: medium
        return "medium"

    def _build_user_prompt(self, user_task: str, context: Dict[str, Any]) -> str:
        """
        构建用户提示词

        Args:
            user_task: 用户任务描述
            context: 上下文信息

        Returns:
            str: 用户提示词
        """
        prompt_parts = [f"用户任务：\n{user_task}"]

        if context:
            context_str = "\n".join([f"- {k}: {v}" for k, v in context.items()])
            prompt_parts.append(f"\n上下文信息：\n{context_str}")

        prompt_parts.append("\n请生成任务计划（JSON 格式）：")

        return "\n".join(prompt_parts)

    def _parse_plan(self, content: str) -> Plan:
        """
        解析 LLM 输出的计划

        Args:
            content: LLM 输出内容

        Returns:
            Plan: 解析后的计划对象

        Raises:
            ValueError: 如果解析失败
        """
        # 提取 JSON 部分（可能包含在 Markdown 代码块中）
        import re

        # 尝试从代码块中提取
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
        if "subtasks" not in parsed:
            raise ValueError("计划缺少 'subtasks' 字段")

        if "overall_acceptance" not in parsed:
            raise ValueError("计划缺少 'overall_acceptance' 字段")

        # 转换为 Plan 类型
        plan: Plan = {
            "subtasks": [],
            "overall_acceptance": parsed["overall_acceptance"]
        }

        for idx, subtask_data in enumerate(parsed["subtasks"]):
            # 验证子任务字段
            required_fields = ["id", "type", "description", "acceptance_criteria"]
            for field in required_fields:
                if field not in subtask_data:
                    raise ValueError(f"子任务 {idx} 缺少必需字段: {field}")

            # 验证类型
            if subtask_data["type"] not in ["code", "research", "tool"]:
                raise ValueError(f"子任务 {subtask_data['id']} 的类型无效: {subtask_data['type']}")

            subtask: Subtask = {
                "id": subtask_data["id"],
                "type": subtask_data["type"],
                "description": subtask_data["description"],
                "dependencies": subtask_data.get("dependencies", []),
                "acceptance_criteria": subtask_data["acceptance_criteria"],
                # 工具任务专用字段
                "tool_name": subtask_data.get("tool_name"),
                "tool_args": subtask_data.get("tool_args")
            }

            plan["subtasks"].append(subtask)

        return plan

    def _validate_plan(self, plan: Plan, min_subtasks: Optional[int] = None):
        """
        验证计划的合理性

        Args:
            plan: 待验证的计划
            min_subtasks: 最小子任务数（None 则使用 self.min_subtasks）

        Raises:
            ValueError: 如果计划不合理
        """
        subtasks = plan["subtasks"]

        # Use provided min_subtasks or default
        effective_min = min_subtasks if min_subtasks is not None else self.min_subtasks

        # 1. 检查子任务数量
        if len(subtasks) < effective_min:
            raise ValueError(f"子任务数量过少（{len(subtasks)}），至少需要 {effective_min} 个")

        if len(subtasks) > self.max_subtasks:
            raise ValueError(f"子任务数量过多（{len(subtasks)}），最多 {self.max_subtasks} 个")

        # 2. 检查 ID 唯一性
        ids = [s["id"] for s in subtasks]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"子任务 ID 重复: {duplicates}")

        # 3. 检查依赖关系合理性
        for subtask in subtasks:
            for dep in subtask["dependencies"]:
                if dep not in ids:
                    raise ValueError(f"子任务 {subtask['id']} 依赖不存在的任务: {dep}")

                # 检查循环依赖（简单检查：不能依赖自己）
                if dep == subtask["id"]:
                    raise ValueError(f"子任务 {subtask['id']} 不能依赖自己")

        # 4. 检查验收标准
        for subtask in subtasks:
            if not subtask["acceptance_criteria"]:
                raise ValueError(f"子任务 {subtask['id']} 缺少验收标准")

        if not plan["overall_acceptance"]:
            raise ValueError("缺少整体验收标准")


def create_planner_node(
    workspace_path: Path,
    **kwargs
) -> callable:
    """
    创建 Planner 节点（用于 LangGraph）

    Args:
        workspace_path: 工作空间路径
        **kwargs: 传递给 PlannerNode 的参数

    Returns:
        Planner 节点函数
    """
    # 如果未提供 llm，使用 ModelRouter
    if "llm" not in kwargs:
        from ..model_router import get_model_router, TaskComplexity
        router = get_model_router()
        llm, model_name = router.get_model(
            complexity=kwargs.pop("complexity", TaskComplexity.MEDIUM),
            temperature=kwargs.get("temperature", 0.2)
        )
        kwargs["llm"] = llm
        # 检测是否使用本地模型（通过模型名称前缀判断）
        kwargs["using_local_model"] = model_name.startswith("ollama/")
        print(f"[Planner] 使用模型: {model_name}")

    planner = PlannerNode(**kwargs)

    async def planner_node(state: SwarmState) -> SwarmState:
        """Planner 节点函数"""
        return await planner.plan(state)

    return planner_node


# 便捷函数：用于测试
async def test_planner():
    """测试 Planner Node"""
    from ..state import create_initial_state

    # 创建初始状态
    state = create_initial_state(
        user_input="写一个命令行待办事项管理工具（Python），支持 add/list/done/delete 功能，数据持久化到 JSON 文件"
    )

    # 创建 Planner
    planner = PlannerNode()

    # 执行拆解
    result_state = await planner.plan(state)

    # 打印结果
    if result_state["status"] == "failed":
        print(f"\n拆解失败: {result_state['error_message']}")
    else:
        print("\n拆解成功！")
        print(f"\n总共 {len(result_state['plan']['subtasks'])} 个子任务：")

        for subtask in result_state["plan"]["subtasks"]:
            print(f"\n{subtask['id']}: [{subtask['type']}] {subtask['description']}")
            if subtask["dependencies"]:
                print(f"  依赖: {', '.join(subtask['dependencies'])}")
            print(f"  验收标准:")
            for criteria in subtask["acceptance_criteria"]:
                print(f"    - {criteria}")

        print(f"\n整体验收标准:")
        for criteria in result_state["plan"]["overall_acceptance"]:
            print(f"  - {criteria}")

    return result_state


if __name__ == "__main__":
    import asyncio
    import sys
    from pathlib import Path

    # 添加父目录到 sys.path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    asyncio.run(test_planner())
