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
        llm: Optional[Any] = None
    ):
        """
        初始化 Planner Node

        Args:
            model: Claude 模型名称
            temperature: 温度参数（0.2 更确定性，适合任务拆解）
            max_subtasks: 最大子任务数量
            min_subtasks: 最小子任务数量
            llm: 可选的 LLM 实例（用于测试时依赖注入）
        """
        # 使用注入的 LLM 或创建新的 LLM
        if llm is not None:
            self.llm = llm
        else:
            # 检查 API Key
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("未设置 ANTHROPIC_API_KEY 环境变量")

            self.llm = ChatAnthropic(
                model=model,
                temperature=temperature,
                anthropic_api_key=api_key
            )
        self.max_subtasks = max_subtasks
        self.min_subtasks = min_subtasks

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词

        Returns:
            str: 详细的系统提示词
        """
        return f"""你是一个专业的任务规划师（Task Planner），擅长将复杂任务拆解为可执行的子任务。

你的职责：
1. 分析用户提供的复杂任务描述
2. 将其拆解为 {self.min_subtasks}-{self.max_subtasks} 个清晰、可执行的子任务
3. 为每个子任务定义类型、描述、依赖关系和验收标准
4. 确保子任务之间的逻辑顺序合理

子任务类型定义：
- **code**: 编写代码实现某个功能（如：写一个函数、创建一个类、实现一个算法）
- **research**: 调研信息、搜索资料、学习知识（如：查找最佳实践、研究技术文档）
- **tool**: 执行系统操作（如：创建文件、移动文件、写入 Notes）

输出格式要求（严格遵守 JSON 格式）：
```json
{{
  "subtasks": [
    {{
      "id": "task-1",
      "type": "code|research|tool",
      "description": "具体的子任务描述，清晰、可执行",
      "dependencies": [],
      "acceptance_criteria": [
        "验收标准1：明确、可测试",
        "验收标准2：具体、可衡量"
      ]
    }}
  ],
  "overall_acceptance": [
    "整体验收标准1：任务的最终目标",
    "整体验收标准2：质量和完成度要求"
  ]
}}
```

重要原则：
1. **子任务粒度适中**：每个子任务应该能在 5-15 分钟内完成
2. **依赖关系清晰**：如果 task-2 需要 task-1 的输出，dependencies 应该包含 ["task-1"]
3. **验收标准具体**：避免模糊的标准，如"代码质量好"，应具体化为"代码包含错误处理"
4. **类型选择准确**：
   - 需要编程 → code
   - 需要查资料 → research
   - 需要操作文件/系统 → tool
5. **优先简单方案**：如果有多种实现方式，优先选择简单、稳定的方案

示例任务："写一个命令行待办事项管理工具（Python）"

好的拆解示例：
```json
{{
  "subtasks": [
    {{
      "id": "task-1",
      "type": "code",
      "description": "设计数据结构：定义 Todo 任务的 JSON schema（包含 id, title, completed, created_at 字段）",
      "dependencies": [],
      "acceptance_criteria": [
        "JSON schema 清晰定义了所有必需字段",
        "包含字段类型说明和示例"
      ]
    }},
    {{
      "id": "task-2",
      "type": "code",
      "description": "实现数据持久化：编写 load_todos() 和 save_todos() 函数，使用 JSON 文件存储",
      "dependencies": ["task-1"],
      "acceptance_criteria": [
        "能正确读取和写入 JSON 文件",
        "包含文件不存在时的初始化逻辑",
        "包含错误处理（文件损坏、权限不足等）"
      ]
    }},
    {{
      "id": "task-3",
      "type": "code",
      "description": "实现核心业务逻辑：add_todo, list_todos, complete_todo, delete_todo 四个函数",
      "dependencies": ["task-2"],
      "acceptance_criteria": [
        "add_todo 能添加新任务并返回 ID",
        "list_todos 能列出所有任务并显示状态",
        "complete_todo 能标记任务为已完成",
        "delete_todo 能删除指定 ID 的任务"
      ]
    }},
    {{
      "id": "task-4",
      "type": "code",
      "description": "实现 CLI 接口：使用 argparse 解析命令行参数，支持 add/list/done/delete 子命令",
      "dependencies": ["task-3"],
      "acceptance_criteria": [
        "支持 'python todo.py add <title>' 添加任务",
        "支持 'python todo.py list' 列出任务",
        "支持 'python todo.py done <id>' 标记完成",
        "支持 'python todo.py delete <id>' 删除任务",
        "包含 --help 帮助信息"
      ]
    }},
    {{
      "id": "task-5",
      "type": "code",
      "description": "美化输出：使用 rich 库美化终端输出，显示彩色表格和状态图标",
      "dependencies": ["task-4"],
      "acceptance_criteria": [
        "使用 rich.table 显示任务列表",
        "已完成任务显示绿色 ✓，未完成显示橙色 ○",
        "输出清晰易读"
      ]
    }}
  ],
  "overall_acceptance": [
    "工具能完整实现 add/list/done/delete 四个功能",
    "数据能正确持久化到 JSON 文件",
    "命令行界面美观、易用",
    "代码包含基本的错误处理",
    "可以直接运行：python todo.py list"
  ]
}}
```

现在，请根据用户提供的任务描述，生成任务计划。"""

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

        # 调用 LLM
        print(f"[Planner] 开始拆解任务: {user_task}")
        response = await self.llm.ainvoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ])

        # 解析 LLM 输出
        try:
            plan = self._parse_plan(response.content)

            # 验证计划
            self._validate_plan(plan)

            # 更新状态
            state["plan"] = plan
            state["current_subtask_index"] = 0
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
                "acceptance_criteria": subtask_data["acceptance_criteria"]
            }

            plan["subtasks"].append(subtask)

        return plan

    def _validate_plan(self, plan: Plan):
        """
        验证计划的合理性

        Args:
            plan: 待验证的计划

        Raises:
            ValueError: 如果计划不合理
        """
        subtasks = plan["subtasks"]

        # 1. 检查子任务数量
        if len(subtasks) < self.min_subtasks:
            raise ValueError(f"子任务数量过少（{len(subtasks)}），至少需要 {self.min_subtasks} 个")

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
