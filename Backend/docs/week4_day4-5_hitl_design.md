# Week 4 Day 4-5: Human-in-the-Loop 设计文档

**文档版本**: v1.0
**创建时间**: 2026-01-22 00:22:01 UTC
**状态**: 设计中

---

## 一、需求分析

### 1.1 核心需求

**目标**: 为 MacCortex Swarm 工作流添加人机交互确认机制，确保高风险操作的安全性。

**关键功能**:
1. **高风险操作确认**: 在执行高风险操作前暂停，请求用户确认
2. **中断点机制**: 支持动态中断工作流并等待用户输入
3. **断点续传**: 从中断点恢复执行，保持完整上下文
4. **状态可视化**: 用户可查看当前状态并做出决策

**适用场景**（基于 LangChain 官方建议）:
- 审批流程：文件删除/重命名、数据库写入、外部 API 调用
- 状态编辑：人工审查并修正 AI 生成的计划或代码
- 工具调用审查：ToolRunner 执行前确认工具参数
- 多轮对话：Coder/Reviewer 循环中的用户介入

---

### 1.2 技术约束

**基于 LangGraph 0.2.31+ 最佳实践**（来源：LangChain 官方文档）:

✅ **推荐方案**:
- 使用 `interrupt()` 函数（替代旧的 breakpoints/NodeInterrupt）
- 异步非阻塞设计（支持跨进程/跨时间恢复）
- MemorySaver 检查点持久化

⚠️ **注意事项**:
- 必须配置 checkpointer（InMemorySaver/MemorySaver）
- 恢复时节点会重新运行前置工作（但不包括前置节点）
- 不能使用同步阻塞的 `input()` 函数

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│              MacCortex Swarm + HITL 架构                    │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
                ┌──────────────────────────┐
                │   LangGraph StateGraph    │
                │   + MemorySaver           │
                └──────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ ToolRunner   │      │    Coder     │      │  Reviewer    │
│ (高风险)     │      │  (可选确认)  │      │  (人工介入)  │
└──────────────┘      └──────────────┘      └──────────────┘
        │                      │                      │
        │ interrupt("Confirm?")│                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  用户交互接口       │
                    │  - CLI Prompt       │
                    │  - FastAPI Endpoint │
                    │  - Web UI (Phase 4) │
                    └─────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Command(resume=...) │
                    │  继续执行            │
                    └─────────────────────┘
```

---

### 2.2 中断点设计

#### 2.2.1 ToolRunner 中断（高优先级）

**触发条件**: 所有工具执行前

**中断信息**:
```python
{
    "tool_name": "write_file",
    "tool_args": {"path": "/tmp/test.txt", "content": "..."},
    "subtask_description": "创建测试文件",
    "risk_level": "medium"  # low/medium/high
}
```

**用户决策**:
- `approve`: 批准执行
- `deny`: 拒绝执行（跳过子任务）
- `modify`: 修改参数后执行
- `abort`: 终止整个工作流

#### 2.2.2 Coder 生成确认（可选）

**触发条件**: `enable_code_review=True` 参数启用

**中断信息**:
```python
{
    "code": "def hello():\n    print('Hello')",
    "language": "python",
    "subtask_description": "生成 hello 函数",
    "file_path": "/tmp/hello.py"
}
```

**用户决策**:
- `approve`: 批准代码
- `regenerate`: 要求重新生成（附带反馈）
- `modify`: 人工修改代码
- `abort`: 终止工作流

#### 2.2.3 Reviewer 失败介入（自动触发）

**触发条件**: Reviewer 审查失败且 `iteration_count >= max_iterations - 1`

**中断信息**:
```python
{
    "failed_code": "...",
    "reviewer_feedback": "代码缺少错误处理",
    "iteration_count": 2,
    "max_iterations": 3
}
```

**用户决策**:
- `continue`: 继续重试（增加 max_iterations）
- `fix_manually`: 人工修复代码
- `skip`: 跳过子任务
- `abort`: 终止工作流

---

### 2.3 检查点配置

**开发环境**:
```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = create_full_swarm_graph(
    workspace_path=workspace,
    checkpointer=checkpointer
)
```

**生产环境**（未来）:
```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()  # 持久化到文件/数据库
```

---

### 2.4 恢复机制

**中断后状态查询**:
```python
# 获取当前状态
current_state = graph.get_state(thread)

# 检查是否中断
if current_state.interrupts:
    interrupt_data = current_state.interrupts[0]
    print(f"等待用户输入: {interrupt_data}")
```

**恢复执行**:
```python
from langgraph.types import Command

# 用户提供决策
user_decision = {
    "action": "approve",  # approve/deny/modify/abort
    "modified_args": {}   # 如果 action=modify
}

# 恢复执行
final_state = await graph.ainvoke(
    Command(resume=user_decision),
    config=thread
)
```

---

## 三、实施计划

### 3.1 Day 4 任务（实现核心功能）

**任务列表**:
1. ✅ 设计文档编写（本文档）
2. ⏳ 修改 `swarm_graph.py`：集成 MemorySaver
3. ⏳ 修改 `tool_runner.py`：添加 interrupt() 调用
4. ⏳ 修改 `coder.py`：可选的代码确认中断
5. ⏳ 修改 `reviewer.py`：失败时的人工介入逻辑
6. ⏳ 创建 `src/orchestration/hitl.py`：用户交互辅助模块

**交付物**:
- 核心代码实现（~300 行）
- 单元测试（基本功能验证）

---

### 3.2 Day 5 任务（集成测试与 CLI 界面）

**任务列表**:
1. ⏳ 创建 CLI 交互脚本（`scripts/run_swarm_hitl.py`）
2. ⏳ 集成测试：ToolRunner 中断恢复
3. ⏳ 集成测试：Coder 确认流程
4. ⏳ 集成测试：Reviewer 人工介入
5. ⏳ 端到端测试：完整 HITL 工作流
6. ⏳ 文档更新与完成报告

**交付物**:
- CLI 工具（可交互运行）
- 集成测试（5+ 测试用例）
- 完成报告

---

## 四、代码结构

### 4.1 新增文件

**`src/orchestration/hitl.py`** (~150 行):
```python
"""Human-in-the-Loop 辅助模块"""

from typing import Dict, Any, Literal
from langgraph.types import Command

class HITLHelper:
    """HITL 交互辅助类"""

    @staticmethod
    def create_approval_prompt(
        operation: str,
        details: Dict[str, Any],
        risk_level: Literal["low", "medium", "high"]
    ) -> Dict[str, Any]:
        """创建审批提示信息"""
        pass

    @staticmethod
    def parse_user_decision(
        user_input: str
    ) -> Dict[str, Any]:
        """解析用户决策"""
        pass

    @staticmethod
    def create_resume_command(
        decision: Dict[str, Any]
    ) -> Command:
        """创建恢复命令"""
        pass
```

**`scripts/run_swarm_hitl.py`** (~200 行):
```python
"""CLI 交互式 Swarm 执行脚本"""

import asyncio
from pathlib import Path
from langgraph.types import Command

async def run_interactive_swarm(
    user_input: str,
    workspace_path: Path
):
    """运行交互式 Swarm 工作流"""

    # 1. 创建 Graph + MemorySaver
    graph = create_full_swarm_graph(
        workspace_path=workspace_path,
        checkpointer=InMemorySaver(),
        tool_runner={"require_approval": True}  # 启用 HITL
    )

    # 2. 执行到第一个中断点
    thread = {"configurable": {"thread_id": "hitl-session"}}
    async for event in graph.astream(initial_state, thread):
        print(f"进度: {event}")

    # 3. 检查中断
    while True:
        state = graph.get_state(thread)
        if not state.interrupts:
            break  # 工作流完成

        # 4. 显示中断信息并收集用户输入
        interrupt_data = state.interrupts[0]
        print(f"\n⚠️ 需要确认: {interrupt_data}")

        user_decision = input("决策 (approve/deny/modify/abort): ")

        # 5. 恢复执行
        decision = parse_user_decision(user_decision)
        async for event in graph.astream(
            Command(resume=decision),
            thread
        ):
            print(f"进度: {event}")

    # 6. 输出最终结果
    final_state = graph.get_state(thread)
    print(f"\n✅ 工作流完成: {final_state['status']}")
```

---

### 4.2 修改文件

**`src/orchestration/swarm_graph.py`**:
```python
# 添加 checkpointer 参数
def create_full_swarm_graph(
    workspace_path: Path,
    checkpointer: Optional[Any] = None,  # 新增
    **agent_kwargs
) -> StateGraph:
    # ... 现有代码 ...

    # 编译图（支持检查点）
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()
```

**`src/orchestration/nodes/tool_runner.py`**:
```python
from langgraph.types import interrupt

class ToolRunnerNode:
    def __init__(
        self,
        workspace_path: Path,
        require_approval: bool = False  # 新增
    ):
        self.require_approval = require_approval

    async def run_tool(self, state: SwarmState) -> SwarmState:
        # ... 获取工具名称和参数 ...

        # 新增：HITL 审批
        if self.require_approval:
            approval_data = {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "subtask_description": subtask["description"],
                "risk_level": self._assess_risk(tool_name)
            }

            # 中断并等待用户确认
            user_decision = interrupt(approval_data)

            # 处理用户决策
            if user_decision["action"] == "deny":
                return self._create_denied_result(state, subtask)
            elif user_decision["action"] == "abort":
                state["status"] = "failed"
                state["error_message"] = "用户终止工作流"
                return state
            elif user_decision["action"] == "modify":
                tool_args = user_decision["modified_args"]

        # 执行工具（正常流程）
        result = self._execute_tool(tool_name, tool_args)
        # ...
```

**`src/orchestration/nodes/coder.py`**:
```python
from langgraph.types import interrupt

class CoderNode:
    def __init__(
        self,
        workspace_path: Path,
        enable_code_review: bool = False  # 新增
    ):
        self.enable_code_review = enable_code_review

    async def generate_code(self, state: SwarmState) -> SwarmState:
        # ... 生成代码 ...

        # 新增：可选的人工代码审查
        if self.enable_code_review:
            review_data = {
                "code": generated_code,
                "language": language,
                "subtask_description": subtask["description"],
                "file_path": code_file
            }

            user_decision = interrupt(review_data)

            if user_decision["action"] == "regenerate":
                # 重新生成（带用户反馈）
                return await self._regenerate_with_feedback(
                    state,
                    user_decision["feedback"]
                )
            elif user_decision["action"] == "modify":
                generated_code = user_decision["modified_code"]

        # 保存代码（正常流程）
        # ...
```

---

## 五、测试策略

### 5.1 单元测试

**测试 ToolRunner 中断**:
```python
async def test_tool_runner_interrupt():
    """测试 ToolRunner 中断与恢复"""

    # 创建带 checkpointer 的 graph
    checkpointer = InMemorySaver()
    graph = create_mock_graph(
        tmp_path,
        checkpointer=checkpointer,
        tool_runner={"require_approval": True}
    )

    thread = {"configurable": {"thread_id": "test-1"}}

    # 执行到中断点
    state = await graph.ainvoke(initial_state, thread)

    # 验证中断
    current_state = graph.get_state(thread)
    assert current_state.interrupts
    assert current_state.interrupts[0]["tool_name"] == "write_file"

    # 恢复执行（批准）
    final_state = await graph.ainvoke(
        Command(resume={"action": "approve"}),
        thread
    )

    # 验证完成
    assert final_state["status"] == "completed"
```

---

### 5.2 集成测试

**端到端 HITL 流程**:
```python
async def test_full_hitl_workflow():
    """测试完整的 HITL 工作流"""

    # 模拟用户决策序列
    user_decisions = [
        {"action": "approve"},     # 批准工具 1
        {"action": "deny"},        # 拒绝工具 2
        {"action": "approve"}      # 批准 Reflector
    ]

    # ... 执行工作流并模拟用户输入 ...
```

---

## 六、风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 | 残余风险 |
|------|------|------|----------|----------|
| **节点重新运行** | 30% | 中 | 文档说明 + 幂等性设计 | 🟡 中 |
| **状态不一致** | 10% | 高 | 严格测试 + 状态验证 | 🟢 低 |
| **用户输入延迟** | 20% | 低 | 超时机制 + 默认策略 | 🟢 低 |
| **检查点存储失败** | 5% | 高 | 错误处理 + 回滚机制 | 🟢 低 |

---

## 七、未来扩展

**Phase 4 Week 4 Day 6-7**（Web UI）:
- FastAPI WebSocket 实时中断通知
- React 前端交互界面
- 批量审批队列

**Phase 5**（企业功能）:
- 审批工作流（多级审批）
- 审计日志（记录所有用户决策）
- 权限管理（不同用户的批准权限）

---

## 八、参考资料

**来源**: CLAUDE.md 议题 1（更新：2026-01-22）

1. [LangChain 官方文档 - Human-in-the-Loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
2. [LangGraph How-to 指南 - interrupt()](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/)
3. [LangChain 博客 - interrupt() 最佳实践](https://www.blog.langchain.com/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt/)
4. [LangGraph 概念文档 - HITL](https://langchain-ai.github.io/langgraphjs/concepts/human_in_the_loop/)
5. [DEV Community - 构建 HITL 工作流](https://dev.to/jamesbmour/interrupts-and-commands-in-langgraph-building-human-in-the-loop-workflows-4ngl)

---

**文档状态**: ✅ 设计完成，进入实施阶段
**下一步**: 开始 Day 4 核心功能实现
**预计完成时间**: 2026-01-23 00:00 UTC
