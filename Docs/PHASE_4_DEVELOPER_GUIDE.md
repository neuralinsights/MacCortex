# Phase 4 开发者指南

**项目**: MacCortex Swarm Intelligence (Slow Lane)
**版本**: Phase 4 完成版
**日期**: 2026-01-22
**状态**: ✅ 已完成

---

## 目录

1. [开发环境设置](#开发环境设置)
2. [代码结构](#代码结构)
3. [扩展指南](#扩展指南)
4. [测试指南](#测试指南)
5. [调试技巧](#调试技巧)
6. [贡献指南](#贡献指南)

---

## 开发环境设置

### 前置要求

- **Python**: 3.14.2 或更高版本
- **Git**: 2.40+
- **IDE**: VS Code / PyCharm（推荐）
- **包管理器**: pip 或 poetry

### 克隆仓库

```bash
git clone https://github.com/your-org/MacCortex.git
cd MacCortex/Backend
```

### 创建虚拟环境

```bash
# 使用 venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 或使用 poetry
poetry install
poetry shell
```

### 安装依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖（pytest、black、mypy）
```

### 配置环境变量

创建 `.env` 文件：

```bash
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
TAVILY_API_KEY=tvly-...

# Ollama 配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:14b

# 缓存配置
CACHE_DIR=~/.maccortex/cache
MAX_CACHE_SIZE=100
CACHE_TTL_SECONDS=604800  # 7 天

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/maccortex.log
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/orchestration/test_cache.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 代码结构

### 目录结构

```
MacCortex/Backend/
├── src/
│   └── orchestration/
│       ├── __init__.py
│       ├── graph.py             # LangGraph 主图
│       ├── state.py             # 状态定义
│       ├── cache.py             # Token 缓存
│       ├── rollback.py          # 错误回滚
│       ├── model_router.py      # 模型路由
│       └── nodes/
│           ├── __init__.py
│           ├── planner.py       # Planner Agent
│           ├── coder.py         # Coder Agent
│           ├── reviewer.py      # Reviewer Agent
│           ├── researcher.py    # Researcher Agent
│           ├── tool_runner.py   # ToolRunner Agent
│           └── reflector.py     # Reflector Agent
├── tests/
│   └── orchestration/
│       ├── test_graph.py
│       ├── test_cache.py
│       ├── test_rollback.py
│       └── nodes/
│           ├── test_planner.py
│           ├── test_coder.py
│           └── test_reviewer.py
├── docs/
│   ├── PHASE_4_ARCHITECTURE.md
│   ├── PHASE_4_API_REFERENCE.md
│   ├── PHASE_4_USER_GUIDE.md
│   └── PHASE_4_DEVELOPER_GUIDE.md (本文档)
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .env.example
└── README.md
```

---

### 核心模块说明

#### graph.py

**职责**：定义 LangGraph 工作流图

**关键函数**：
- `create_swarm_graph()`: 创建状态图（添加节点、边、条件边）
- `run_swarm_task()`: 执行任务的便捷函数
- `create_sqlite_checkpointer_sync/async()`: 创建检查点存储器

**示例**：

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(SwarmState)

# 添加节点
graph.add_node("planner", planner_node)
graph.add_node("coder", coder_node)

# 添加边
graph.set_entry_point("planner")
graph.add_edge("planner", "coder")

# 添加条件边
graph.add_conditional_edges(
    "coder",
    should_continue,  # 决策函数
    {
        "continue": "reviewer",
        "end": END
    }
)

# 编译
compiled_graph = graph.compile(checkpointer=checkpointer)
```

---

#### state.py

**职责**：定义 SwarmState 和子类型（Plan、Subtask、SubtaskResult）

**关键类型**：
- `SwarmState`: 完整状态定义（TypedDict）
- `Plan`: 任务计划
- `Subtask`: 子任务定义
- `SubtaskResult`: 子任务执行结果

**关键函数**：
- `create_initial_state()`: 创建初始状态

**扩展建议**：
- 添加新字段时，更新 `SwarmState` TypedDict
- 保持字段类型为 JSON 可序列化（用于检查点持久化）

---

#### nodes/planner.py

**职责**：任务拆解与计划生成

**关键类**：`PlannerNode`

**扩展点**：
1. **自定义提示词**：修改 `_build_system_prompt()` 方法
2. **自定义验证规则**：修改 `_validate_plan()` 方法
3. **支持新任务类型**：在 `Subtask` TypedDict 中添加新 `type` 选项

**示例：添加新任务类型**：

```python
# 1. 更新 state.py
class Subtask(TypedDict):
    type: Literal["code", "research", "tool", "design"]  # 新增 "design"
    # ...

# 2. 更新 planner.py 验证逻辑
def _validate_plan(self, plan: Plan):
    # ...
    if subtask_data["type"] not in ["code", "research", "tool", "design"]:
        raise ValueError(f"子任务类型无效: {subtask_data['type']}")
```

---

#### nodes/coder.py

**职责**：代码生成

**关键类**：`CoderNode`

**扩展点**：
1. **多语言支持**：根据 `subtask.get("language")` 动态生成提示词
2. **代码模板**：添加常用代码模板（CRUD、API、CLI 等）
3. **代码格式化**：集成 Black、Prettier 等格式化工具

**示例：添加多语言支持**：

```python
class CoderNode:
    def _build_system_prompt(self, language: str = "Python") -> str:
        if language == "Python":
            return """你是 Python 工程师。生成 PEP 8 风格代码。"""
        elif language == "JavaScript":
            return """你是 JavaScript 工程师。生成 ES6+ 代码。"""
        # ...
```

---

#### nodes/reviewer.py

**职责**：代码审查

**关键类**：`ReviewerNode`

**扩展点**：
1. **静态代码分析集成**：集成 Pylint、ESLint 等工具
2. **安全扫描**：集成 Bandit、Semgrep 等安全扫描工具
3. **自定义审查标准**：添加项目特定的代码规范检查

**示例：集成 Pylint**：

```python
import subprocess

async def review(self, state: SwarmState) -> SwarmState:
    code_file = state["current_code_file"]

    # 运行 Pylint
    result = subprocess.run(
        ["pylint", code_file],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        state["review_feedback"] = f"Pylint 检查失败：\n{result.stdout}"
        return state

    # ... 继续 LLM 审查
```

---

#### cache.py

**职责**：LLM 响应缓存

**关键类**：`LLMCache`

**扩展点**：
1. **分布式缓存**：替换为 Redis
2. **智能失效策略**：根据模型版本自动失效旧缓存
3. **缓存预热**：启动时预加载常见任务的缓存

**示例：使用 Redis 缓存**：

```python
import redis
import json

class RedisLLMCache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    def get(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        key = self._generate_key(system_prompt, user_prompt)
        cached = self.redis.get(key)
        return cached.decode() if cached else None

    def set(self, system_prompt: str, user_prompt: str, response: str):
        key = self._generate_key(system_prompt, user_prompt)
        self.redis.setex(key, 3600 * 24 * 7, response)  # 7 天过期
```

---

#### rollback.py

**职责**：错误回滚

**关键类**：`RollbackManager`

**扩展点**：
1. **完整文件内容恢复**：保存文件内容快照（增加存储成本）
2. **Git 集成**：使用 Git commit 作为快照
3. **云端备份**：将快照上传到 S3 / MinIO

**示例：Git 集成**：

```python
import subprocess

class GitRollbackManager(RollbackManager):
    def create_snapshot(self, state: Dict[str, Any], description: str) -> str:
        # 创建 Git commit 作为快照
        subprocess.run(["git", "add", "."], cwd=self.workspace)
        subprocess.run(
            ["git", "commit", "-m", f"Snapshot: {description}"],
            cwd=self.workspace
        )

        # 返回 commit hash 作为 snapshot_id
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.workspace,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def rollback_to_snapshot(self, snapshot_id: str):
        # 回滚到指定 commit
        subprocess.run(["git", "reset", "--hard", snapshot_id], cwd=self.workspace)
```

---

## 扩展指南

### 添加新 Agent 节点

**步骤**：

1. **创建节点文件**：`src/orchestration/nodes/my_agent.py`

```python
from typing import Optional, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import SwarmState

class MyAgentNode:
    """自定义 Agent 节点"""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.3,
        llm: Optional[Any] = None
    ):
        if llm:
            self.llm = llm
        else:
            self.llm = ChatAnthropic(model=model, temperature=temperature)

    async def process(self, state: SwarmState) -> SwarmState:
        """处理逻辑"""
        # 1. 构建提示词
        prompt = self._build_prompt(state)

        # 2. 调用 LLM
        response = await self.llm.ainvoke([
            SystemMessage(content="你是一个专业的..."),
            HumanMessage(content=prompt)
        ])

        # 3. 更新状态
        state["custom_field"] = response.content
        state["status"] = "executing"

        return state

    def _build_prompt(self, state: SwarmState) -> str:
        """构建提示词"""
        return f"处理任务：{state['user_input']}"
```

2. **更新 graph.py**：

```python
from orchestration.nodes.my_agent import MyAgentNode

def create_swarm_graph(workspace_path, checkpointer=None):
    graph = StateGraph(SwarmState)

    # 添加新节点
    my_agent = MyAgentNode()

    async def my_agent_node(state: SwarmState) -> SwarmState:
        return await my_agent.process(state)

    graph.add_node("my_agent", my_agent_node)

    # 添加边
    graph.add_edge("planner", "my_agent")
    graph.add_edge("my_agent", "coder")

    # ...
```

3. **创建测试**：`tests/orchestration/nodes/test_my_agent.py`

```python
import pytest
from orchestration.nodes.my_agent import MyAgentNode
from orchestration.state import create_initial_state

@pytest.mark.asyncio
async def test_my_agent_basic():
    agent = MyAgentNode()
    state = create_initial_state("测试任务")

    result = await agent.process(state)

    assert result["status"] == "executing"
    assert "custom_field" in result
```

---

### 添加新工具

**步骤**：

1. **创建工具函数**：`src/orchestration/tools/my_tool.py`

```python
from pathlib import Path

def my_tool(arg1: str, arg2: int, workspace: Path) -> str:
    """
    我的自定义工具

    Args:
        arg1: 参数 1
        arg2: 参数 2
        workspace: 工作空间路径

    Returns:
        执行结果
    """
    try:
        # 工具逻辑
        result = f"处理 {arg1} 和 {arg2}"
        return f"成功：{result}"
    except Exception as e:
        return f"失败：{str(e)}"
```

2. **注册工具**：`src/orchestration/nodes/tool_runner.py`

```python
from orchestration.tools.my_tool import my_tool

class ToolRunnerNode:
    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path
        self.tools = {
            "write_file": write_file_tool,
            "read_file": read_file_tool,
            "my_tool": my_tool,  # 新增
        }
```

3. **使用工具**（在 Planner 输出中）：

```json
{
  "id": "task-3",
  "type": "tool",
  "description": "使用自定义工具处理数据",
  "tool_name": "my_tool",
  "tool_args": {
    "arg1": "test",
    "arg2": 42
  }
}
```

---

### 自定义提示词

**本地模型简化提示词**（推荐）：

```python
class CoderNode:
    def _build_system_prompt(self) -> str:
        if self.using_local_model:
            return """你是软件工程师。编写可运行的代码。

要求：
1. 代码完整可运行（含 import、主程序）
2. 包含错误处理
3. 满足验收标准

输出格式：
```python
# 代码
```

只输出代码块，不要解释。"""
        else:
            # Claude API 使用详细提示词
            return """你是一个专业的软件工程师...
            （2000+ 字符的详细提示词）
            """
```

---

### 添加新语言支持

**步骤**：

1. **更新 Subtask 类型**：

```python
class Subtask(TypedDict):
    # ...
    language: Optional[str]  # 新增字段（如 "Python", "JavaScript"）
```

2. **更新 Coder 提示词**：

```python
class CoderNode:
    async def generate_code(self, state: SwarmState, workspace_path: Path):
        subtask = state["plan"]["subtasks"][state["current_subtask_index"]]
        language = subtask.get("language", "Python")  # 默认 Python

        # 根据语言选择提示词
        system_prompt = self._build_system_prompt(language)

        # ... 生成代码
```

3. **更新 Reviewer 执行逻辑**：

```python
class ReviewerNode:
    async def review(self, state: SwarmState):
        subtask = state["plan"]["subtasks"][state["current_subtask_index"]]
        language = subtask.get("language", "Python")

        # 根据语言选择执行方式
        if language == "Python":
            result = subprocess.run(["python", code_file], ...)
        elif language == "JavaScript":
            result = subprocess.run(["node", code_file], ...)
        # ...
```

---

## 测试指南

### 单元测试

**测试结构**：

```
tests/
├── orchestration/
│   ├── test_graph.py          # 图构建测试
│   ├── test_cache.py          # 缓存测试（10 个）
│   ├── test_rollback.py       # 回滚测试（9 个）
│   └── nodes/
│       ├── test_planner.py    # Planner 测试
│       ├── test_coder.py      # Coder 测试
│       └── test_reviewer.py   # Reviewer 测试
```

**测试示例**：

```python
import pytest
from orchestration.cache import LLMCache

class TestLLMCache:
    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = LLMCache(max_size=10)

        result = cache.get(
            system_prompt="You are a helpful assistant",
            user_prompt="Hello"
        )

        assert result is None
        assert cache.misses == 1
        assert cache.hits == 0

    def test_cache_hit(self):
        """测试缓存命中"""
        cache = LLMCache(max_size=10)

        # 先设置缓存
        cache.set(
            system_prompt="You are a helpful assistant",
            user_prompt="Hello",
            response="Hi there!",
            model_name="test-model"
        )

        # 再获取
        result = cache.get(
            system_prompt="You are a helpful assistant",
            user_prompt="Hello"
        )

        assert result == "Hi there!"
        assert cache.hits == 1
        assert cache.misses == 0
```

---

### 集成测试

**测试完整工作流**：

```python
import pytest
from pathlib import Path
from orchestration.graph import run_swarm_task

@pytest.mark.asyncio
@pytest.mark.integration
async def test_hello_world_task():
    """测试完整的 Hello World 任务执行"""
    result = run_swarm_task(
        user_input="写一个打印 Hello World 的程序",
        workspace_path=Path("/tmp/test_workspace")
    )

    assert result["status"] == "completed"
    assert "hello.py" in str(result["output"])

    # 验证生成的文件存在
    assert (Path("/tmp/test_workspace") / "hello.py").exists()
```

---

### Mock LLM（加速测试）

**使用 FakeLLM**：

```python
from langchain_core.language_models.fake import FakeListLLM

class TestPlannerWithMock:
    @pytest.mark.asyncio
    async def test_planner_with_fake_llm(self):
        """使用 FakeLLM 测试 Planner"""
        fake_llm = FakeListLLM(responses=[
            """```json
            {
              "subtasks": [{
                "id": "task-1",
                "type": "code",
                "description": "测试任务",
                "dependencies": [],
                "acceptance_criteria": ["标准1"]
              }],
              "overall_acceptance": ["整体标准1"]
            }
            ```"""
        ])

        planner = PlannerNode(llm=fake_llm)
        state = create_initial_state("测试任务")

        result = await planner.plan(state)

        assert result["status"] == "executing"
        assert len(result["plan"]["subtasks"]) == 1
```

---

### 测试覆盖率

**生成覆盖率报告**：

```bash
pytest --cov=src --cov-report=html --cov-report=term

# 输出
---------- coverage: platform darwin, python 3.14.2 -----------
Name                                  Stmts   Miss  Cover
---------------------------------------------------------
src/orchestration/cache.py              100      5    95%
src/orchestration/rollback.py          120      8    93%
src/orchestration/nodes/planner.py     150     12    92%
...
---------------------------------------------------------
TOTAL                                  1200     80    93%

# 查看 HTML 报告
open htmlcov/index.html
```

---

## 调试技巧

### 日志配置

**配置日志级别**：

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/maccortex.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 在代码中使用
logger.debug("调试信息")
logger.info("正常信息")
logger.warning("警告信息")
logger.error("错误信息")
```

---

### LangGraph 可视化

**导出图结构**：

```python
from orchestration.graph import create_swarm_graph
from pathlib import Path

graph = create_swarm_graph(Path("/tmp/workspace"))

# 导出 Mermaid 图
mermaid_code = graph.get_graph().draw_mermaid()
print(mermaid_code)

# 保存到文件
with open("graph.mmd", "w") as f:
    f.write(mermaid_code)

# 使用 Mermaid CLI 生成图片
# npm install -g @mermaid-js/mermaid-cli
# mmdc -i graph.mmd -o graph.png
```

---

### 检查点调试

**查看检查点内容**：

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    config = {"configurable": {"thread_id": "task-123"}}
    checkpoint = checkpointer.get(config)

    if checkpoint:
        print("Checkpoint ID:", checkpoint.id)
        print("Checkpoint values:", checkpoint.channel_values)
        print("Next nodes:", checkpoint.next)
```

---

### 断点调试

**VS Code 配置**（`.vscode/launch.json`）：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Swarm Task",
      "type": "python",
      "request": "launch",
      "module": "orchestration.cli",
      "args": ["run", "写一个 Hello World 程序", "--local-model"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "tests/orchestration/test_cache.py"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

---

## 贡献指南

### 代码规范

**使用 Black 格式化**：

```bash
# 格式化单个文件
black src/orchestration/cache.py

# 格式化整个项目
black src/ tests/

# 检查但不修改
black --check src/ tests/
```

**使用 Mypy 类型检查**：

```bash
mypy src/orchestration/
```

**使用 Pylint 代码检查**：

```bash
pylint src/orchestration/
```

---

### Git 工作流

**分支命名规范**：

- `feature/xxx`: 新功能（如 `feature/add-javascript-support`）
- `fix/xxx`: Bug 修复（如 `fix/cache-expiration-bug`）
- `refactor/xxx`: 重构（如 `refactor/simplify-planner-prompt`）
- `docs/xxx`: 文档更新（如 `docs/update-developer-guide`）

**Commit 消息规范**：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `refactor`: 重构
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具链更新

**示例**：

```bash
git commit -m "feat(cache): 添加 Redis 缓存支持

- 实现 RedisLLMCache 类
- 添加 Redis 连接池配置
- 更新测试覆盖 Redis 场景

Closes #123"
```

---

### Pull Request 流程

1. **Fork 仓库**

2. **创建功能分支**：

```bash
git checkout -b feature/add-redis-cache
```

3. **开发 + 测试**：

```bash
# 开发功能
vim src/orchestration/cache_redis.py

# 运行测试
pytest tests/orchestration/test_cache_redis.py

# 代码检查
black src/ tests/
mypy src/
pylint src/
```

4. **提交更改**：

```bash
git add .
git commit -m "feat(cache): 添加 Redis 缓存支持"
```

5. **推送到 Fork 仓库**：

```bash
git push origin feature/add-redis-cache
```

6. **创建 Pull Request**（在 GitHub 上）

7. **代码审查**：
   - 等待维护者审查
   - 根据反馈修改代码
   - Push 更新后的代码

8. **合并**：
   - 维护者批准后，PR 将被合并到 `main` 分支

---

### 文档贡献

**文档位置**：

- 架构文档：`Docs/PHASE_4_ARCHITECTURE.md`
- API 文档：`Docs/PHASE_4_API_REFERENCE.md`
- 用户手册：`Docs/PHASE_4_USER_GUIDE.md`
- 开发者指南：`Docs/PHASE_4_DEVELOPER_GUIDE.md`（本文档）

**文档更新流程**：

1. 编辑 Markdown 文件
2. 预览效果（VS Code Markdown Preview）
3. 提交 PR（类型为 `docs`）

---

## 常见开发问题

### Q1: 如何在开发时使用本地模型（避免消耗 API 额度）？

```bash
# 方式 1：环境变量
unset ANTHROPIC_API_KEY
python -m orchestration.cli run "测试任务"

# 方式 2：命令行参数
python -m orchestration.cli run "测试任务" --local-model

# 方式 3：代码中指定
planner = PlannerNode(llm=ChatOllama(model="qwen3:14b"))
```

---

### Q2: 如何加速测试（跳过 LLM 调用）？

使用 `FakeListLLM`（见"Mock LLM"章节）

---

### Q3: 如何调试 LangGraph 图结构？

```python
graph = create_swarm_graph(workspace)

# 打印节点和边
print("Nodes:", graph.get_graph().nodes)
print("Edges:", graph.get_graph().edges)

# 导出 Mermaid 图
mermaid_code = graph.get_graph().draw_mermaid()
print(mermaid_code)
```

---

### Q4: 如何查看 SQLite 检查点内容？

```bash
# 使用 sqlite3 命令行工具
sqlite3 checkpoints.db

# 查看表结构
.schema

# 查看检查点
SELECT * FROM checkpoints;

# 查看特定线程的检查点
SELECT * FROM checkpoints WHERE thread_id = 'task-123';
```

---

## 总结

本文档提供了 MacCortex Slow Lane 的完整开发指南，涵盖环境设置、代码结构、扩展指南、测试、调试和贡献流程。

**关键扩展点**：
- 添加新 Agent 节点：继承 `BaseNode`，实现 `process()` 方法
- 添加新工具：在 `ToolRunnerNode.tools` 中注册
- 自定义提示词：修改 `_build_system_prompt()` 方法
- 支持新语言：更新 `Subtask` 类型 + Coder/Reviewer 逻辑

**下一步**：
- 查看 [PHASE_4_ACCEPTANCE_REPORT.md](PHASE_4_ACCEPTANCE_REPORT.md) 了解验收结果
- 加入 [MacCortex Discord](https://discord.gg/maccortex) 讨论开发问题

---

**文档版本**: v1.0
**最后更新**: 2026-01-22
**负责人**: MacCortex 开发团队
**审核状态**: ✅ 已完成
