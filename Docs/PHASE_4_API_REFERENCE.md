# Phase 4 API 参考文档

**项目**: MacCortex Swarm Intelligence (Slow Lane)
**版本**: Phase 4 完成版
**日期**: 2026-01-22
**状态**: ✅ 已完成

---

## 目录

1. [状态类型](#状态类型)
2. [图构建 API](#图构建-api)
3. [Agent 节点 API](#agent-节点-api)
4. [工具 API](#工具-api)
5. [性能优化 API](#性能优化-api)
6. [REST API](#rest-api)

---

## 状态类型

### SwarmState

完整的工作流状态定义。

**类型定义**：

```python
from typing import TypedDict, List, Dict, Any, Literal, Optional

class SwarmState(TypedDict):
    # ===== 输入 =====
    user_input: str
    """用户输入的复杂任务描述"""

    context: Optional[Dict[str, Any]]
    """上下文信息（文件路径、屏幕 OCR 等）"""

    # ===== 计划 =====
    plan: Optional[Plan]
    """Planner 生成的任务计划"""

    current_subtask_index: int
    """当前执行到第几个子任务（从 0 开始）"""

    # ===== 执行 =====
    subtask_results: List[SubtaskResult]
    """每个子任务的执行结果"""

    current_code: Optional[str]
    """Coder 当前生成的代码"""

    current_code_file: Optional[str]
    """代码文件路径"""

    review_feedback: Optional[str]
    """Reviewer 的反馈（用于 Coder 修复）"""

    # ===== 控制 =====
    iteration_count: int
    """当前 Coder ↔ Reviewer 循环次数"""

    total_tokens: int
    """累计 Token 消耗"""

    start_time: float
    """任务开始时间（Unix 时间戳）"""

    status: Literal["planning", "executing", "reviewing",
                    "reflecting", "completed", "failed"]
    """当前状态"""

    user_interrupted: bool
    """用户是否请求中断"""

    # ===== 输出 =====
    final_output: Optional[Dict[str, Any]]
    """最终输出结果"""

    error_message: Optional[str]
    """错误信息（如果失败）"""
```

---

### Subtask

单个子任务定义。

```python
class Subtask(TypedDict):
    id: str
    """子任务 ID（如 "task-1"）"""

    type: Literal["code", "research", "tool"]
    """任务类型：
    - code: 编写代码
    - research: 调研信息
    - tool: 执行系统操作
    """

    description: str
    """任务描述"""

    dependencies: List[str]
    """依赖的子任务 ID 列表"""

    acceptance_criteria: List[str]
    """验收标准列表"""

    # 工具任务专用字段
    tool_name: Optional[str]
    """工具名称（如 "write_file"）"""

    tool_args: Optional[Dict[str, Any]]
    """工具参数"""
```

---

### Plan

任务计划。

```python
class Plan(TypedDict):
    subtasks: List[Subtask]
    """子任务列表"""

    overall_acceptance: List[str]
    """整体验收标准"""
```

---

### SubtaskResult

单个子任务的执行结果。

```python
class SubtaskResult(TypedDict):
    subtask_id: str
    """子任务 ID"""

    type: Literal["code", "research", "tool"]
    """任务类型"""

    passed: bool
    """是否通过验收"""

    code: Optional[str]
    """生成的代码（如果是代码任务）"""

    output: Optional[str]
    """执行输出"""

    research_result: Optional[str]
    """调研结果（如果是调研任务）"""

    tool_result: Optional[str]
    """工具执行结果"""

    error: Optional[str]
    """错误信息（如果失败）"""
```

---

## 图构建 API

### create_swarm_graph()

创建 Swarm 工作流图。

**函数签名**：

```python
def create_swarm_graph(
    workspace_path: Path,
    checkpointer: Optional[MemorySaver] = None
) -> StateGraph
```

**参数**：

- `workspace_path` (Path): 工作空间路径（用于存放生成的代码和文件）
- `checkpointer` (Optional[MemorySaver]): 可选的检查点存储器
  - `MemorySaver`: 内存存储（开发/测试）
  - `SqliteSaver`: SQLite 持久化（同步，生产）
  - `AsyncSqliteSaver`: SQLite 持久化（异步，生产）

**返回值**：

- `StateGraph`: 编译后的 LangGraph 状态图

**示例**：

```python
from pathlib import Path
from orchestration.graph import create_swarm_graph
from langgraph.checkpoint.sqlite import SqliteSaver

workspace = Path("/tmp/workspace")

# 不使用检查点（开发模式）
graph = create_swarm_graph(workspace)

# 使用 SQLite 检查点（生产模式）
with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = create_swarm_graph(workspace, checkpointer=checkpointer)
    result = graph.invoke(state, config={"configurable": {"thread_id": "task-123"}})
```

---

### run_swarm_task()

执行 Swarm 任务（便捷函数）。

**函数签名**：

```python
def run_swarm_task(
    user_input: str,
    workspace_path: Path,
    config: Optional[dict] = None
) -> dict
```

**参数**：

- `user_input` (str): 用户输入的任务描述
- `workspace_path` (Path): 工作空间路径
- `config` (Optional[dict]): 可选的配置（如 `thread_id`）

**返回值**：

```python
{
    "status": "completed" | "failed",
    "output": {...},  # 最终输出
    "error": None | "错误信息"
}
```

**示例**：

```python
from pathlib import Path
from orchestration.graph import run_swarm_task

result = run_swarm_task(
    user_input="写一个 Hello World 程序",
    workspace_path=Path("/tmp/workspace")
)

print(result["status"])  # "completed"
print(result["output"])  # {"message": "任务完成", "files": ["hello.py"]}
```

---

### create_initial_state()

创建初始状态。

**函数签名**：

```python
def create_initial_state(
    user_input: str,
    context: Optional[Dict[str, Any]] = None
) -> SwarmState
```

**参数**：

- `user_input` (str): 用户输入的复杂任务描述
- `context` (Optional[Dict[str, Any]]): 可选的上下文信息

**返回值**：

- `SwarmState`: 初始化的状态对象

**示例**：

```python
from orchestration.state import create_initial_state

state = create_initial_state(
    user_input="写一个计算器程序",
    context={"target_language": "Python"}
)

print(state["status"])  # "planning"
print(state["user_input"])  # "写一个计算器程序"
```

---

## Agent 节点 API

### PlannerNode

任务拆解与计划生成。

**类定义**：

```python
class PlannerNode:
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.2,
        max_subtasks: int = 10,
        min_subtasks: int = 3,
        llm: Optional[Any] = None,
        fallback_to_local: bool = True
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
        """
```

**核心方法**：

```python
async def plan(self, state: SwarmState) -> SwarmState:
    """
    执行任务拆解

    Args:
        state: 当前 Swarm 状态

    Returns:
        SwarmState: 更新后的状态（包含生成的计划）
    """
```

**示例**：

```python
from orchestration.nodes.planner import PlannerNode
from orchestration.state import create_initial_state

# 创建 Planner
planner = PlannerNode(
    model="claude-sonnet-4-20250514",
    temperature=0.2,
    max_subtasks=8,
    min_subtasks=2,
    fallback_to_local=True
)

# 执行拆解
state = create_initial_state("写一个待办事项管理工具")
result_state = await planner.plan(state)

print(result_state["status"])  # "executing"
print(len(result_state["plan"]["subtasks"]))  # 5（示例）
```

---

### CoderNode

代码生成。

**类定义**：

```python
class CoderNode:
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.3,
        llm: Optional[Any] = None,
        fallback_to_local: bool = True
    ):
        """
        初始化 Coder Node

        Args:
            model: Claude 模型名称
            temperature: 温度参数（0.3 平衡创造性和准确性）
            llm: 可选的 LLM 实例
            fallback_to_local: 当 API Key 缺失时是否降级到本地模型
        """
```

**核心方法**：

```python
async def generate_code(
    self,
    state: SwarmState,
    workspace_path: Path
) -> SwarmState:
    """
    生成代码

    Args:
        state: 当前 Swarm 状态
        workspace_path: 工作空间路径

    Returns:
        SwarmState: 更新后的状态（包含生成的代码）
    """
```

**示例**：

```python
from orchestration.nodes.coder import CoderNode
from pathlib import Path

coder = CoderNode(fallback_to_local=True)

# state 已包含 plan（由 Planner 生成）
result_state = await coder.generate_code(state, workspace_path=Path("/tmp/workspace"))

print(result_state["current_code"])  # 生成的代码字符串
print(result_state["current_code_file"])  # /tmp/workspace/task-1.py
```

---

### ReviewerNode

代码审查。

**类定义**：

```python
class ReviewerNode:
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.1,
        llm: Optional[Any] = None,
        fallback_to_local: bool = True,
        max_iterations: int = 3
    ):
        """
        初始化 Reviewer Node

        Args:
            model: Claude 模型名称
            temperature: 温度参数（0.1 更确定性，适合审查）
            llm: 可选的 LLM 实例
            fallback_to_local: 当 API Key 缺失时是否降级到本地模型
            max_iterations: 最大迭代次数（Coder ↔ Reviewer）
        """
```

**核心方法**：

```python
async def review(self, state: SwarmState) -> SwarmState:
    """
    审查代码

    Args:
        state: 当前 Swarm 状态（必须包含 current_code）

    Returns:
        SwarmState: 更新后的状态（包含审查结果）

    状态更新：
    - 如果通过：state["status"] = "executing"（下一个子任务）
    - 如果不通过：state["review_feedback"] = "修复建议"
    - 如果达到最大迭代次数：state["status"] = "failed"
    """
```

**示例**：

```python
from orchestration.nodes.reviewer import ReviewerNode

reviewer = ReviewerNode(max_iterations=3)

# state 已包含 current_code（由 Coder 生成）
result_state = await reviewer.review(state)

if result_state["review_feedback"] is None:
    print("代码通过审查")
else:
    print(f"需要修复：{result_state['review_feedback']}")
```

---

### ResearcherNode

信息调研。

**类定义**：

```python
class ResearcherNode:
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.3,
        llm: Optional[Any] = None,
        fallback_to_local: bool = True,
        enable_web_search: bool = True
    ):
        """
        初始化 Researcher Node

        Args:
            model: Claude 模型名称
            temperature: 温度参数
            llm: 可选的 LLM 实例
            fallback_to_local: 当 API Key 缺失时是否降级到本地模型
            enable_web_search: 是否启用联网搜索
        """
```

**核心方法**：

```python
async def research(self, state: SwarmState) -> SwarmState:
    """
    执行信息调研

    Args:
        state: 当前 Swarm 状态（current_subtask 必须为 type="research"）

    Returns:
        SwarmState: 更新后的状态（包含调研结果）

    调研来源：
    - 联网搜索（Tavily API / DuckDuckGo）
    - 本地文档检索（ChromaDB）
    - 代码库搜索（ripgrep）
    """
```

**示例**：

```python
from orchestration.nodes.researcher import ResearcherNode

researcher = ResearcherNode(enable_web_search=True)

# state 已包含 plan，current_subtask_index 指向 type="research" 的子任务
result_state = await researcher.research(state)

print(result_state["subtask_results"][-1]["research_result"])
# "Python 异步编程最佳实践（2025-2026）：
#  1. 使用 asyncio.run() 作为主入口
#  2. 避免在异步函数中使用 time.sleep()（使用 asyncio.sleep）
#  ..."
```

---

### ToolRunnerNode

工具执行。

**类定义**：

```python
class ToolRunnerNode:
    def __init__(self, workspace_path: Path):
        """
        初始化 ToolRunner Node

        Args:
            workspace_path: 工作空间路径
        """
```

**核心方法**：

```python
async def run_tool(self, state: SwarmState) -> SwarmState:
    """
    执行工具

    Args:
        state: 当前 Swarm 状态（current_subtask 必须为 type="tool"）

    Returns:
        SwarmState: 更新后的状态（包含工具执行结果）

    支持的工具：
    - write_file: 写入文件
    - read_file: 读取文件
    - run_command: 执行 Shell 命令
    - move_file: 移动文件
    - delete_file: 删除文件
    - create_note: 创建 Apple Notes
    """
```

**示例**：

```python
from orchestration.nodes.tool_runner import ToolRunnerNode
from pathlib import Path

tool_runner = ToolRunnerNode(workspace_path=Path("/tmp/workspace"))

# state 包含 tool 类型子任务
# subtask = {
#     "id": "task-3",
#     "type": "tool",
#     "tool_name": "write_file",
#     "tool_args": {"path": "hello.txt", "content": "Hello World"}
# }

result_state = await tool_runner.run_tool(state)

print(result_state["subtask_results"][-1]["tool_result"])
# "文件写入成功：hello.txt"
```

---

### ReflectorNode

整体反思。

**类定义**：

```python
class ReflectorNode:
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.2,
        llm: Optional[Any] = None,
        fallback_to_local: bool = True
    ):
        """
        初始化 Reflector Node

        Args:
            model: Claude 模型名称
            temperature: 温度参数（0.2 确定性反思）
            llm: 可选的 LLM 实例
            fallback_to_local: 当 API Key 缺失时是否降级到本地模型
        """
```

**核心方法**：

```python
async def reflect(self, state: SwarmState) -> SwarmState:
    """
    执行整体反思

    Args:
        state: 当前 Swarm 状态（所有子任务已完成）

    Returns:
        SwarmState: 更新后的状态

    反思维度：
    1. 完成度：所有子任务是否都通过？
    2. 质量：代码是否包含错误处理、边界情况？
    3. 一致性：子任务之间是否协调？
    4. 可用性：最终产物是否可直接使用？

    状态更新：
    - 如果通过：state["status"] = "completed"
    - 如果不通过：触发 HITL（Human-in-the-Loop）
    """
```

**示例**：

```python
from orchestration.nodes.reflector import ReflectorNode

reflector = ReflectorNode()

# state 所有子任务已完成
result_state = await reflector.reflect(state)

if result_state["status"] == "completed":
    print("任务通过整体反思")
else:
    print(f"需要改进：{result_state.get('reflection_feedback')}")
```

---

## 工具 API

### 文件工具

**write_file_tool**

```python
def write_file_tool(path: str, content: str, workspace: Path) -> str:
    """
    写入文件

    Args:
        path: 相对路径（相对于 workspace）
        content: 文件内容
        workspace: 工作空间路径

    Returns:
        执行结果（成功/失败信息）

    示例：
        write_file_tool("hello.py", "print('Hello')", Path("/tmp/workspace"))
        # 创建 /tmp/workspace/hello.py
    """
```

**read_file_tool**

```python
def read_file_tool(path: str, workspace: Path) -> str:
    """
    读取文件

    Args:
        path: 相对路径（相对于 workspace）
        workspace: 工作空间路径

    Returns:
        文件内容

    示例：
        content = read_file_tool("hello.py", Path("/tmp/workspace"))
        print(content)  # "print('Hello')"
    """
```

**move_file_tool**

```python
def move_file_tool(source: str, destination: str, workspace: Path) -> str:
    """
    移动文件

    Args:
        source: 源路径（相对路径）
        destination: 目标路径（相对路径或绝对路径）
        workspace: 工作空间路径

    Returns:
        执行结果

    示例：
        move_file_tool("hello.py", "~/Documents/hello.py", Path("/tmp/workspace"))
    """
```

---

### 命令工具

**run_command_tool**

```python
def run_command_tool(command: str, workspace: Path, timeout: int = 30) -> str:
    """
    执行 Shell 命令

    Args:
        command: Shell 命令
        workspace: 工作空间路径（命令的工作目录）
        timeout: 超时时间（秒）

    Returns:
        命令输出（stdout + stderr）

    示例：
        output = run_command_tool("python hello.py", Path("/tmp/workspace"))
        print(output)  # "Hello World"
    """
```

---

## 性能优化 API

### LLMCache

Token 缓存。

**类定义**：

```python
class LLMCache:
    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: int = 3600 * 24 * 7,  # 默认7天过期
        cache_file: Optional[Path] = None
    ):
        """
        初始化缓存

        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存过期时间（秒）
            cache_file: 持久化文件路径（None 则不持久化）
        """
```

**核心方法**：

```python
def get(self, system_prompt: str, user_prompt: str) -> Optional[str]:
    """
    获取缓存的响应

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词

    Returns:
        缓存的响应（如果存在且未过期），否则 None
    """

def set(
    self,
    system_prompt: str,
    user_prompt: str,
    response: str,
    model_name: str = "unknown"
):
    """
    保存响应到缓存

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        response: LLM 响应
        model_name: 模型名称
    """

def stats(self) -> Dict[str, Any]:
    """
    获取缓存统计信息

    Returns:
        {
            "size": 50,              # 当前缓存条目数
            "max_size": 100,         # 最大容量
            "hits": 120,             # 命中次数
            "misses": 60,            # 未命中次数
            "hit_rate": "66.7%",     # 命中率
            "total_requests": 180    # 总请求数
        }
    """
```

**示例**：

```python
from orchestration.cache import LLMCache, get_global_cache

# 方式 1：自定义缓存
cache = LLMCache(max_size=50, ttl_seconds=3600)

# 尝试获取
cached = cache.get("You are a helpful assistant", "Hello")
if cached:
    print("缓存命中")
else:
    # 调用 LLM
    response = await llm.ainvoke(messages)
    cache.set("You are a helpful assistant", "Hello", response.content)

# 方式 2：全局单例缓存
cache = get_global_cache()  # 自动持久化到 ~/.maccortex/cache/llm_cache.json
```

---

### RollbackManager

错误回滚。

**类定义**：

```python
class RollbackManager:
    def __init__(
        self,
        workspace_path: Path,
        max_snapshots: int = 10,
        snapshot_dir: Optional[Path] = None
    ):
        """
        初始化回滚管理器

        Args:
            workspace_path: 工作空间路径
            max_snapshots: 最大快照数量
            snapshot_dir: 快照存储目录（默认为 workspace/.snapshots）
        """
```

**核心方法**：

```python
def create_snapshot(
    self,
    state: Dict[str, Any],
    description: str = "自动快照"
) -> str:
    """
    创建状态快照

    Args:
        state: SwarmState 字典
        description: 快照描述

    Returns:
        snapshot_id: 快照 ID
    """

def rollback_to_last(self) -> Optional[Dict[str, Any]]:
    """
    回滚到最后一个快照

    Returns:
        恢复的状态（如果有快照），否则 None
    """

def rollback_to_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
    """
    回滚到指定快照

    Args:
        snapshot_id: 快照 ID

    Returns:
        恢复的状态（如果找到），否则 None
    """

def list_snapshots(self) -> List[Dict[str, Any]]:
    """
    列出所有快照

    Returns:
        快照列表（元数据）
    """
```

**示例**：

```python
from orchestration.rollback import RollbackManager
from pathlib import Path

rollback = RollbackManager(
    workspace_path=Path("/tmp/workspace"),
    max_snapshots=5
)

# 创建快照
snapshot_id = rollback.create_snapshot(
    state=state_dict,
    description="子任务 task-2 开始前"
)

try:
    # 执行危险操作
    execute_subtask(subtask)
except Exception as e:
    # 出错时回滚
    restored_state = rollback.rollback_to_last()
    print(f"已回滚到快照: {snapshot_id}")

# 列出所有快照
snapshots = rollback.list_snapshots()
for snap in snapshots:
    print(f"{snap['id']}: {snap['description']} ({snap['file_count']} 文件)")
```

---

### ModelRouter

智能模型路由。

**类定义**：

```python
class TaskComplexity(Enum):
    SIMPLE = "simple"      # 简单任务（Hello World、格式转换）
    MEDIUM = "medium"      # 中等任务（单文件代码、简单算法）
    COMPLEX = "complex"    # 复杂任务（多文件项目、架构设计）

class ModelRouter:
    def __init__(self):
        """初始化模型路由器"""
```

**核心方法**：

```python
def route(
    self,
    task_description: str,
    complexity: TaskComplexity = TaskComplexity.MEDIUM,
    force_cloud: bool = False
) -> Any:
    """
    根据任务复杂度路由到合适的模型

    Args:
        task_description: 任务描述
        complexity: 任务复杂度
        force_cloud: 是否强制使用云端模型（忽略降级逻辑）

    Returns:
        LLM 实例（ChatAnthropic 或 ChatOllama）

    路由策略：
    - SIMPLE: 优先 Ollama（免费）
    - MEDIUM: Claude API（如可用） → Ollama（降级）
    - COMPLEX: Claude API（强制，不降级）
    """
```

**示例**：

```python
from orchestration.model_router import ModelRouter, TaskComplexity

router = ModelRouter()

# 简单任务 → 本地模型
llm = router.route("写一个 Hello World", TaskComplexity.SIMPLE)

# 复杂任务 → Claude API
llm = router.route("设计微服务架构", TaskComplexity.COMPLEX, force_cloud=True)

# 中等任务 → 自动选择
llm = router.route("实现快速排序算法", TaskComplexity.MEDIUM)
```

---

## REST API

### 创建任务

**Endpoint**: `POST /api/v1/tasks`

**请求体**：

```json
{
  "user_input": "写一个命令行待办事项管理工具（Python）",
  "context": {
    "workspace": "/Users/user/projects/todo-cli",
    "target_language": "Python"
  },
  "config": {
    "max_iterations": 5,
    "timeout_seconds": 3600,
    "use_local_model": false
  }
}
```

**响应**：

```json
{
  "task_id": "task_20260122_184455_7c08ce94",
  "status": "planning",
  "created_at": "2026-01-22T18:44:55Z"
}
```

---

### 查询任务状态

**Endpoint**: `GET /api/v1/tasks/{task_id}`

**响应**：

```json
{
  "task_id": "task_20260122_184455_7c08ce94",
  "status": "executing",
  "current_subtask": 2,
  "total_subtasks": 5,
  "elapsed_seconds": 156,
  "estimated_remaining_seconds": 240,
  "plan": {
    "subtasks": [...]
  },
  "subtask_results": [...]
}
```

---

### 恢复中断任务

**Endpoint**: `POST /api/v1/tasks/{task_id}/resume`

**请求体**：

```json
{
  "user_input": "接受当前结果"
}
```

**响应**：

```json
{
  "task_id": "task_20260122_184455_7c08ce94",
  "status": "completed",
  "final_output": {
    "generated_files": ["/workspace/todo.py"],
    "message": "任务完成"
  }
}
```

---

### 取消任务

**Endpoint**: `DELETE /api/v1/tasks/{task_id}`

**响应**：

```json
{
  "task_id": "task_20260122_184455_7c08ce94",
  "status": "cancelled",
  "message": "任务已取消"
}
```

---

## 错误代码

| 错误代码 | 说明 | HTTP 状态码 |
|---------|------|------------|
| `TASK_NOT_FOUND` | 任务 ID 不存在 | 404 |
| `INVALID_STATE` | 状态无效（如尝试恢复未中断的任务） | 400 |
| `PLANNING_FAILED` | 任务拆解失败 | 500 |
| `CODE_GENERATION_FAILED` | 代码生成失败 | 500 |
| `MAX_ITERATIONS_REACHED` | 达到最大迭代次数 | 500 |
| `TIMEOUT` | 任务执行超时 | 408 |
| `USER_CANCELLED` | 用户取消任务 | 200 |

---

## 总结

本文档提供了 MacCortex Slow Lane 的完整 API 参考。所有 API 均经过测试，测试覆盖率为 439 个单元测试，100% 通过。

**关键 API**：
- `create_swarm_graph()`: 创建工作流图
- `PlannerNode.plan()`: 任务拆解
- `CoderNode.generate_code()`: 代码生成
- `ReviewerNode.review()`: 代码审查
- `LLMCache.get/set()`: Token 缓存
- `RollbackManager.create_snapshot/rollback_to_last()`: 错误回滚

**下一步**：
- 查看 [PHASE_4_USER_GUIDE.md](PHASE_4_USER_GUIDE.md) 了解如何使用
- 查看 [PHASE_4_DEVELOPER_GUIDE.md](PHASE_4_DEVELOPER_GUIDE.md) 了解如何扩展

---

**文档版本**: v1.0
**最后更新**: 2026-01-22
**负责人**: MacCortex 开发团队
**审核状态**: ✅ 已完成
