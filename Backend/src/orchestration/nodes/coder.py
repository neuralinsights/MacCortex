"""
MacCortex Coder Agent

代码生成节点，根据子任务需求生成可执行代码。
支持多语言（Python、Swift、Bash）并能根据审查反馈修复问题。
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import SwarmState, Subtask


class CoderNode:
    """
    代码生成节点

    功能：
    - 根据子任务需求生成代码
    - 支持多语言（Python、Swift、Bash）
    - 根据 Reviewer 反馈修复问题
    - 写入工作空间文件
    """

    def __init__(
        self,
        workspace_path: Path,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.3,
        llm: Optional[Any] = None,
        fallback_to_local: bool = True
    ):
        """
        初始化 Coder Node

        Args:
            workspace_path: 工作空间路径（用于写入生成的代码）
            model: Claude 模型名称
            temperature: 温度参数（0.3 为代码生成推荐值）
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
                    print("⚠️  CoderNode: 降级使用本地 Ollama 模型（qwen3:14b）")
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
        self.workspace.mkdir(parents=True, exist_ok=True)

        # 支持的语言及其文件扩展名
        self.language_extensions = {
            "python": ".py",
            "swift": ".swift",
            "bash": ".sh",
            "shell": ".sh",
            "javascript": ".js",
            "typescript": ".ts"
        }

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个专业的软件工程师。根据任务需求编写高质量、可执行的代码。

要求：
1. **代码必须完整可运行** - 包含所有必要的 import、函数定义、主程序
2. **包含必要的错误处理** - 使用 try-except、边界检查、输入验证
3. **添加清晰的注释** - 解释关键逻辑、复杂算法、边界条件
4. **遵循最佳实践** - 符合语言惯例、代码风格、安全规范
5. **满足验收标准** - 仔细阅读验收标准，确保代码满足所有要求

输出格式：
- 使用 Markdown 代码块格式（```language ... ```）
- 明确指定语言（python、swift、bash 等）
- 只输出代码，不要额外解释（除非需要特别说明）

示例输出：
```python
#!/usr/bin/env python3
# 任务：计算斐波那契数列

def fibonacci(n: int) -> list[int]:
    \"\"\"生成斐波那契数列前 n 项\"\"\"
    if n <= 0:
        return []
    elif n == 1:
        return [0]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

if __name__ == "__main__":
    result = fibonacci(10)
    print(result)
```
"""

    async def code(self, state: SwarmState) -> SwarmState:
        """
        执行代码生成

        Args:
            state: 当前 Swarm 状态

        Returns:
            更新后的状态（包含生成的代码）
        """
        # 获取当前子任务
        plan = state.get("plan")
        if not plan:
            raise ValueError("状态中缺少 plan 字段")

        current_index = state.get("current_subtask_index", 0)
        if current_index >= len(plan["subtasks"]):
            raise ValueError(f"子任务索引越界: {current_index}")

        subtask = plan["subtasks"][current_index]

        # 检查是否有 Reviewer 反馈（需要修复）
        feedback = state.get("review_feedback", "")
        previous_code = state.get("current_code", "")

        # 构建用户提示词
        user_prompt = self._build_user_prompt(
            subtask=subtask,
            feedback=feedback,
            previous_code=previous_code
        )

        # 调用 LLM 生成代码
        response = await self.llm.ainvoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ])

        # 提取代码
        code, language = self._extract_code(response.content)

        # 推断文件名和扩展名
        extension = self._get_extension(language)
        code_file = self.workspace / f"subtask_{subtask['id']}{extension}"

        # 写入文件
        code_file.write_text(code, encoding="utf-8")

        # 如果是 shell 脚本，添加执行权限
        if extension == ".sh":
            code_file.chmod(0o755)

        # 更新状态
        state["current_code"] = code
        state["current_code_file"] = str(code_file)
        state["review_feedback"] = ""  # 清空旧反馈
        state["status"] = "reviewing"  # 下一步：审查

        return state

    def _build_user_prompt(
        self,
        subtask: Subtask,
        feedback: str,
        previous_code: str
    ) -> str:
        """
        构建用户提示词

        Args:
            subtask: 当前子任务
            feedback: Reviewer 反馈（如果有）
            previous_code: 之前生成的代码（如果有）

        Returns:
            完整的用户提示词
        """
        if feedback and previous_code:
            # 修复模式
            return f"""任务: {subtask['description']}

之前的代码有问题，审查反馈：
{feedback}

之前的代码：
```
{previous_code}
```

请修复问题并重新生成代码。确保：
1. 解决审查反馈中提到的所有问题
2. 保持代码的完整性和可运行性
3. 满足所有验收标准

验收标准：
{self._format_acceptance_criteria(subtask['acceptance_criteria'])}
"""
        else:
            # 首次生成模式
            return f"""任务: {subtask['description']}

任务类型: {subtask['type']}

验收标准：
{self._format_acceptance_criteria(subtask['acceptance_criteria'])}

依赖的其他任务: {subtask['dependencies'] if subtask['dependencies'] else '无'}

请生成完整、可运行的代码。
"""

    def _format_acceptance_criteria(self, criteria: list) -> str:
        """格式化验收标准为编号列表"""
        return "\n".join(f"{i+1}. {c}" for i, c in enumerate(criteria))

    def _extract_code(self, content: str) -> tuple[str, str]:
        """
        从 LLM 响应中提取代码

        Args:
            content: LLM 响应内容

        Returns:
            (代码内容, 语言标识)
        """
        # 匹配 Markdown 代码块：```language\ncode\n```
        pattern = r"```(\w+)?\s*\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            # 取第一个代码块
            language, code = matches[0]
            language = language.lower() if language else "python"
            return code.strip(), language

        # 如果没有代码块标记，尝试直接提取
        # 假设是 Python（默认）
        return content.strip(), "python"

    def _get_extension(self, language: str) -> str:
        """
        根据语言获取文件扩展名

        Args:
            language: 语言标识（如 "python", "swift"）

        Returns:
            文件扩展名（如 ".py", ".swift"）
        """
        language = language.lower()
        return self.language_extensions.get(language, ".txt")

    def get_generated_files(self) -> list[Path]:
        """
        获取所有生成的代码文件

        Returns:
            文件路径列表
        """
        return sorted(self.workspace.glob("subtask_*"))


def create_coder_node(
    workspace_path: Path,
    **kwargs
) -> callable:
    """
    创建 Coder 节点（用于 LangGraph）

    Args:
        workspace_path: 工作空间路径
        **kwargs: 传递给 CoderNode 的参数

    Returns:
        Coder 节点函数
    """
    coder = CoderNode(workspace_path, **kwargs)

    async def coder_node(state: SwarmState) -> SwarmState:
        """Coder 节点函数"""
        return await coder.code(state)

    return coder_node


# 用于测试的简化函数
async def test_coder():
    """测试 Coder Node 基本功能"""
    import tempfile
    from ..state import create_initial_state

    # 创建临时工作空间
    workspace = Path(tempfile.mkdtemp())
    print(f"工作空间: {workspace}")

    # 创建 Coder
    coder = CoderNode(workspace)

    # 创建测试状态
    state = create_initial_state("写一个 Hello World 程序")
    state["plan"] = {
        "subtasks": [
            {
                "id": "task-1",
                "type": "code",
                "description": "编写一个打印 'Hello, World!' 的 Python 程序",
                "dependencies": [],
                "acceptance_criteria": [
                    "程序能成功运行",
                    "输出包含 'Hello, World!'"
                ]
            }
        ],
        "overall_acceptance": ["程序能成功运行并输出正确内容"]
    }
    state["current_subtask_index"] = 0

    # 生成代码
    result_state = await coder.code(state)

    print(f"\n生成的代码文件: {result_state['current_code_file']}")
    print(f"\n代码内容:\n{result_state['current_code']}")

    return result_state


if __name__ == "__main__":
    import asyncio
    import sys
    from pathlib import Path

    # 添加父目录到 sys.path 以支持相对导入
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    asyncio.run(test_coder())
