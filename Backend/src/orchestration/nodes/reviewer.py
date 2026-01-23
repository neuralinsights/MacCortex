"""
MacCortex Reviewer Agent

代码审查节点，执行 Coder 生成的代码并审查结果。
提供反馈以驱动 Coder ↔ Reviewer 自纠错回路。
"""

import os
import subprocess
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import SwarmState, Subtask


class ReviewerNode:
    """
    代码审查节点

    功能：
    - 执行 Coder 生成的代码
    - 捕获运行时输出和错误
    - 使用 LLM 审查执行结果
    - 检查是否满足验收标准
    - 提供具体修复建议
    """

    def __init__(
        self,
        workspace_path: Path,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.0,
        timeout: int = 30,
        max_iterations: int = 3,
        llm: Optional[Any] = None,
        fallback_to_local: bool = True
    ):
        """
        初始化 Reviewer Node

        Args:
            workspace_path: 工作空间路径（代码执行目录）
            model: Claude 模型名称
            temperature: 温度参数（0.0 为审查推荐值，确保一致性）
            timeout: 代码执行超时时间（秒）
            max_iterations: 最大迭代次数（防止无限循环）
            llm: 可选的 LLM 实例（用于测试时依赖注入）
            fallback_to_local: 当 API Key 缺失时是否降级到本地模型
        """
        # 使用注入的 LLM 或创建新的 LLM
        if llm is not None:
            self.llm = llm
            self.using_local_model = False
        else:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                if fallback_to_local:
                    # 使用新版 langchain-ollama 包
                    from langchain_ollama import ChatOllama
                    print("⚠️  ReviewerNode: 降级使用本地 Ollama 模型（qwen3:14b）")
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
        self.timeout = timeout
        self.max_iterations = max_iterations

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        # 本地模型使用简化的提示词（减少 token 生成时间）
        if self.using_local_model:
            return """你是代码审查专家。审查代码执行结果。

⚠️ 必须输出 JSON 格式！

审查：
1. 代码是否运行成功
2. 输出是否符合预期

输出格式（直接输出 JSON）：
{"passed": true, "feedback": "通过"}
或
{"passed": false, "feedback": "问题：xxx 修复：xxx"}

只输出 JSON，不要其他文字。"""

        # Claude API 使用优化的提示词（Phase 5: -58.9% Input, Phase 6: -40% Output）
        return """审查代码执行结果。

检查：
1. 运行成功（退出 0，无异常）
2. 输出符合标准
3. 边界检查

输出（JSON）：
```json
{"passed": true, "feedback": "通过"}
```
或
```json
{"passed": false, "feedback": "问题：xxx 修复：xxx"}
```

**极简反馈：通过 = "通过"，失败 = 具体问题 + 修复方案（1 行）**
"""

    async def review(self, state: SwarmState) -> SwarmState:
        """
        执行代码审查

        Args:
            state: 当前 Swarm 状态

        Returns:
            更新后的状态（包含审查结果或反馈）
        """
        # 类型验证：确保 review_feedback 是字典或 None
        if "review_feedback" in state:
            feedback = state["review_feedback"]
            if feedback is not None and not isinstance(feedback, dict):
                # 防御性编程：如果是字符串，转换为字典格式
                state["review_feedback"] = {
                    "passed": False,
                    "feedback": str(feedback)
                }

        # 获取当前子任务和代码文件
        plan = state.get("plan")
        if not plan:
            raise ValueError("状态中缺少 plan 字段")

        current_index = state["current_subtask_index"]
        if current_index >= len(plan["subtasks"]):
            raise ValueError(f"子任务索引越界: {current_index}")

        subtask = plan["subtasks"][current_index]
        code_file = Path(state.get("current_code_file", ""))

        if not code_file.exists():
            raise FileNotFoundError(f"代码文件不存在: {code_file}")

        # 检查是否超过最大迭代次数
        iteration_count = state.get("iteration_count", 0)
        if iteration_count >= self.max_iterations:
            # 强制标记为失败，进入下一个子任务或结束
            state["subtask_results"].append({
                "subtask_id": subtask["id"],
                "subtask_description": subtask["description"],
                "code": state["current_code"],
                "output": "",
                "passed": False,
                "error_message": f"超过最大迭代次数（{self.max_iterations}）"
            })
            state["current_subtask_index"] += 1
            state["status"] = "planning"  # 回到 Planner
            state["error_message"] = f"子任务 {subtask['id']} 失败：超过最大迭代次数"
            return state

        # 1. 执行代码
        success, output, error = self._run_code(code_file)

        # 2. 使用 LLM 审查结果
        review_result = await self._review_with_llm(
            code=state["current_code"],
            output=output,
            error=error,
            acceptance_criteria=subtask["acceptance_criteria"],
            subtask_description=subtask["description"]
        )

        # 3. 根据审查结果更新状态
        if review_result["passed"]:
            # ✅ 审查通过 - 保存结果，进入下一个子任务
            state["subtask_results"].append({
                "subtask_id": subtask["id"],
                "subtask_description": subtask["description"],
                "code": state["current_code"],
                "output": output,
                "passed": True
            })
            state["current_subtask_index"] += 1

            # 检查是否所有子任务都完成
            if state["current_subtask_index"] >= len(plan["subtasks"]):
                state["status"] = "completed"  # 所有子任务完成
            else:
                state["status"] = "planning"  # 继续下一个子任务

            # 清空反馈和当前代码
            state["review_feedback"] = {}
            state["current_code"] = ""
            state["current_code_file"] = ""
        else:
            # ❌ 审查失败 - 提供反馈给 Coder 重新生成
            # 存储完整的审查结果（字典），包含 passed 和 feedback 字段
            state["review_feedback"] = review_result
            state["status"] = "executing"  # 重新交给 Coder
            state["iteration_count"] += 1

        return state

    def _run_code(self, code_file: Path) -> Tuple[bool, str, str]:
        """
        在沙箱中执行代码

        Args:
            code_file: 要执行的代码文件路径

        Returns:
            (是否成功, 标准输出, 错误输出)
        """
        try:
            # 根据文件扩展名选择解释器
            interpreter = self._get_interpreter(code_file)

            result = subprocess.run(
                interpreter + [str(code_file)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.workspace,
                env=os.environ.copy()  # 继承环境变量
            )

            success = result.returncode == 0
            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", f"执行超时（{self.timeout} 秒）"
        except FileNotFoundError as e:
            return False, "", f"解释器未找到: {e}"
        except Exception as e:
            return False, "", f"执行异常: {str(e)}"

    def _get_interpreter(self, code_file: Path) -> list:
        """
        根据文件扩展名获取解释器

        Args:
            code_file: 代码文件路径

        Returns:
            解释器命令列表
        """
        extension = code_file.suffix.lower()

        interpreters = {
            ".py": [sys.executable],  # Python
            ".sh": ["/bin/bash"],     # Bash
            ".js": ["node"],          # JavaScript
            ".swift": ["swift"],      # Swift
            ".ts": ["ts-node"],       # TypeScript
        }

        if extension in interpreters:
            return interpreters[extension]
        else:
            # 默认尝试 Python
            return [sys.executable]

    async def _review_with_llm(
        self,
        code: str,
        output: str,
        error: str,
        acceptance_criteria: list,
        subtask_description: str
    ) -> Dict[str, Any]:
        """
        使用 LLM 审查代码执行结果

        Args:
            code: 代码内容
            output: 标准输出
            error: 错误输出
            acceptance_criteria: 验收标准列表
            subtask_description: 子任务描述

        Returns:
            {"passed": bool, "feedback": str}
        """
        # 构建用户提示词
        user_prompt = f"""任务描述：
{subtask_description}

代码：
```
{code}
```

执行结果：
- **退出状态**：{"✅ 成功 (exit code 0)" if not error or "error" not in error.lower() else "❌ 失败 (非零退出码或异常)"}
- **标准输出**：
{output if output else "(无输出)"}

- **错误输出**：
{error if error else "(无错误)"}

验收标准：
{self._format_acceptance_criteria(acceptance_criteria)}

请审查此代码是否满足所有验收标准。如果不满足，提供具体修复建议。

输出格式（JSON）：
{{
  "passed": true/false,
  "feedback": "反馈内容"
}}
"""

        # 动态 max_tokens（Output Tokens 优化）
        # Reviewer 输出固定格式：JSON (passed + feedback)，非常简短
        max_output_tokens = 150  # 足够输出 {"passed": bool, "feedback": "..."}

        # 调用 LLM
        print(f"[Reviewer] max_tokens={max_output_tokens}")
        response = await self.llm.ainvoke(
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt)
            ],
            max_tokens=max_output_tokens
        )

        # 解析 JSON 响应
        return self._parse_review_result(response.content)

    def _format_acceptance_criteria(self, criteria: list) -> str:
        """格式化验收标准为编号列表"""
        return "\n".join(f"{i+1}. {c}" for i, c in enumerate(criteria))

    def _parse_review_result(self, content: str) -> Dict[str, Any]:
        """
        解析 LLM 响应为审查结果

        Args:
            content: LLM 响应内容

        Returns:
            {"passed": bool, "feedback": str}
        """
        # 尝试从 Markdown 代码块中提取 JSON
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = content

        try:
            result = json.loads(json_str)

            # 验证必需字段
            if "passed" not in result:
                # 缺少必需字段，返回失败结果
                return {
                    "passed": False,
                    "feedback": f"LLM 响应缺少 passed 字段\n原始响应:\n{content[:200]}"
                }

            # 确保 feedback 字段存在
            if "feedback" not in result:
                result["feedback"] = ""

            return result

        except (json.JSONDecodeError, ValueError) as e:
            # JSON 解析失败，返回保守结果（标记为失败）
            return {
                "passed": False,
                "feedback": f"LLM 响应解析失败: {e}\n原始响应:\n{content[:200]}"
            }


def create_reviewer_node(
    workspace_path: Path,
    **kwargs
) -> callable:
    """
    创建 Reviewer 节点（用于 LangGraph）

    Args:
        workspace_path: 工作空间路径
        **kwargs: 传递给 ReviewerNode 的参数

    Returns:
        Reviewer 节点函数
    """
    # 如果未提供 llm，使用 ModelRouter
    if "llm" not in kwargs:
        from ..model_router import get_model_router, TaskComplexity
        router = get_model_router()
        llm, model_name = router.get_model(
            complexity=kwargs.pop("complexity", TaskComplexity.SIMPLE),
            temperature=kwargs.get("temperature", 0.0)
        )
        kwargs["llm"] = llm
        print(f"[Reviewer] 使用模型: {model_name}")

    reviewer = ReviewerNode(workspace_path, **kwargs)

    async def reviewer_node(state: SwarmState) -> SwarmState:
        """Reviewer 节点函数"""
        return await reviewer.review(state)

    return reviewer_node


# 用于测试的简化函数
async def test_reviewer():
    """测试 Reviewer Node 基本功能"""
    import tempfile
    from ..state import create_initial_state

    # 创建临时工作空间
    workspace = Path(tempfile.mkdtemp())
    print(f"工作空间: {workspace}")

    # 创建测试代码文件
    code_file = workspace / "test_hello.py"
    code_file.write_text("""#!/usr/bin/env python3
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")

    # 创建 Reviewer
    reviewer = ReviewerNode(workspace)

    # 创建测试状态
    state = create_initial_state("测试 Hello World")
    state["plan"] = {
        "subtasks": [
            {
                "id": "task-1",
                "type": "code",
                "description": "打印 Hello, World!",
                "dependencies": [],
                "acceptance_criteria": [
                    "程序能成功运行",
                    "输出包含 'Hello, World!'"
                ]
            }
        ],
        "overall_acceptance": ["程序能成功运行"]
    }
    state["current_subtask_index"] = 0
    state["current_code"] = code_file.read_text()
    state["current_code_file"] = str(code_file)

    # 审查代码
    result_state = await reviewer.review(state)

    print(f"\n审查结果: {result_state['status']}")
    if result_state.get("review_feedback"):
        print(f"反馈: {result_state['review_feedback']}")
    if result_state["subtask_results"]:
        print(f"子任务结果: {result_state['subtask_results'][0]}")

    return result_state


if __name__ == "__main__":
    import asyncio
    import sys
    from pathlib import Path

    # 添加父目录到 sys.path 以支持相对导入
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    asyncio.run(test_reviewer())
