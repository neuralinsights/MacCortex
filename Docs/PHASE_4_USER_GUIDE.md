# Phase 4 用户手册

**项目**: MacCortex Swarm Intelligence (Slow Lane)
**版本**: Phase 4 完成版
**日期**: 2026-01-22
**状态**: ✅ 已完成

---

## 目录

1. [快速开始](#快速开始)
2. [使用场景](#使用场景)
3. [CLI 使用指南](#cli-使用指南)
4. [API 使用指南](#api-使用指南)
5. [GUI 使用指南](#gui-使用指南)
6. [最佳实践](#最佳实践)
7. [故障排除](#故障排除)

---

## 快速开始

### 系统要求

- **Python**: 3.14.2 或更高版本
- **macOS**: 26.2 或更高版本（其他平台未测试）
- **RAM**: 至少 8GB（本地模型需要 16GB+）
- **存储**: 至少 20GB 可用空间（本地模型占用 ~10GB）

### 安装

**1. 安装 MacCortex Backend**：

```bash
cd ~/projects/MacCortex/Backend
pip install -r requirements.txt
```

**2. 配置 API 密钥**（可选，推荐）：

```bash
# Claude API（推荐用于复杂任务）
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Tavily API（用于联网搜索）
export TAVILY_API_KEY="tvly-..."
```

**3. 安装本地模型**（免费替代方案）：

```bash
# 安装 Ollama
brew install ollama

# 下载推荐模型
ollama pull qwen3:14b

# 启动 Ollama 服务
ollama serve
```

### 第一个任务

**CLI 模式**：

```bash
cd ~/projects/MacCortex/Backend
python -m orchestration.cli run "写一个 Hello World 程序"
```

**预期输出**：

```
[Planner] 开始拆解任务: 写一个 Hello World 程序
[Planner] 任务拆解完成，共 1 个子任务
  - task-1: [code] 创建 hello.py 文件并写入打印语句

[Coder] 开始生成代码...
[Coder] 代码已保存到: /tmp/workspace/task-1.py

[Reviewer] 开始审查代码...
[Reviewer] 代码通过审查

[Reflector] 开始整体反思...
[Reflector] 任务完成

✅ 任务完成，共耗时 256.5 秒
生成文件：
  - /tmp/workspace/task-1.py
```

---

## 使用场景

### 场景 1：代码生成

**任务**：创建一个命令行待办事项管理工具（Python）

**输入**：

```bash
python -m orchestration.cli run "写一个命令行待办事项管理工具（Python），支持 add/list/done/delete 功能，数据持久化到 JSON 文件，使用 rich 库美化输出"
```

**Planner 自动拆解**：

```
1. task-1 [code]: 设计数据结构（Todo JSON schema）
2. task-2 [code]: 实现数据持久化（load_todos, save_todos）
3. task-3 [code]: 实现核心业务逻辑（add/list/complete/delete）
4. task-4 [code]: 实现 CLI 接口（argparse 参数解析）
5. task-5 [code]: 美化输出（rich 表格显示）
```

**输出**：

```
/tmp/workspace/
├── task-1.py  # JSON schema 定义
├── task-2.py  # 持久化函数
├── task-3.py  # 业务逻辑
├── task-4.py  # CLI 接口
└── todo.py    # 最终整合文件（由 Reflector 生成）
```

**使用方式**：

```bash
# 添加任务
python /tmp/workspace/todo.py add "学习 LangGraph"

# 列出任务
python /tmp/workspace/todo.py list

# 标记完成
python /tmp/workspace/todo.py done 1

# 删除任务
python /tmp/workspace/todo.py delete 1
```

---

### 场景 2：技术调研

**任务**：调研 Python 异步编程最佳实践（2025-2026）

**输入**：

```bash
python -m orchestration.cli run "调研 Python 异步编程最佳实践（2025-2026），包括 asyncio 核心模式、常见陷阱、性能优化技巧"
```

**Planner 自动拆解**：

```
1. task-1 [research]: 搜索 Python asyncio 官方文档和顶级博客
2. task-2 [research]: 总结核心模式（event loop、协程、任务）
3. task-3 [research]: 收集常见陷阱（阻塞调用、资源泄漏）
4. task-4 [code]: 编写示例代码演示最佳实践
```

**输出**：

```markdown
# Python 异步编程最佳实践（2025-2026）

## 核心模式

### 1. 使用 asyncio.run() 作为主入口
\`\`\`python
import asyncio

async def main():
    await async_task()

if __name__ == "__main__":
    asyncio.run(main())
\`\`\`

### 2. 避免在异步函数中使用阻塞调用
❌ 错误示例：
\`\`\`python
async def bad_example():
    time.sleep(1)  # 阻塞整个 event loop
\`\`\`

✅ 正确示例：
\`\`\`python
async def good_example():
    await asyncio.sleep(1)  # 非阻塞
\`\`\`

## 常见陷阱

1. **忘记 await**：异步函数不会自动执行
2. **混用同步和异步代码**：导致性能下降
3. **资源泄漏**：未关闭 asyncio.Task

## 性能优化

1. 使用 `asyncio.gather()` 并发执行多个任务
2. 使用 `asyncio.create_task()` 而非 `asyncio.ensure_future()`
3. 限制并发数量（asyncio.Semaphore）

（完整报告保存到 /tmp/workspace/research_report.md）
```

---

### 场景 3：自动化工作流

**任务**：将项目代码移动到 GitHub 仓库并提交

**输入**：

```bash
python -m orchestration.cli run "将 /tmp/workspace/todo.py 移动到 ~/Documents/my-todo-app/，初始化 Git 仓库，添加 .gitignore，提交代码并推送到 GitHub（假设远程仓库已创建）"
```

**Planner 自动拆解**：

```
1. task-1 [tool]: 创建目标目录 ~/Documents/my-todo-app/
2. task-2 [tool]: 移动文件 todo.py 到目标目录
3. task-3 [tool]: 初始化 Git 仓库（git init）
4. task-4 [code]: 生成 .gitignore 文件
5. task-5 [tool]: 提交代码（git add . && git commit -m "Initial commit"）
6. task-6 [tool]: 推送到远程（git push -u origin main）
```

**HITL 触发点**：

- task-6 执行前，系统会请求用户确认 GitHub 远程 URL

**输出**：

```
✅ 任务完成，代码已推送到 GitHub
仓库结构：
  - ~/Documents/my-todo-app/
    ├── todo.py
    ├── .gitignore
    └── .git/
```

---

## CLI 使用指南

### 基本命令

**运行任务**：

```bash
python -m orchestration.cli run "任务描述"
```

**指定工作空间**：

```bash
python -m orchestration.cli run "任务描述" --workspace /path/to/workspace
```

**使用本地模型**（免费）：

```bash
python -m orchestration.cli run "任务描述" --local-model
```

**设置最大迭代次数**：

```bash
python -m orchestration.cli run "任务描述" --max-iterations 10
```

**设置超时时间**：

```bash
python -m orchestration.cli run "任务描述" --timeout 3600  # 1 小时
```

---

### 高级用法

**恢复中断任务**：

```bash
python -m orchestration.cli resume task_20260122_184455_7c08ce94
```

**查看任务状态**：

```bash
python -m orchestration.cli status task_20260122_184455_7c08ce94
```

**列出所有任务**：

```bash
python -m orchestration.cli list
```

**取消任务**：

```bash
python -m orchestration.cli cancel task_20260122_184455_7c08ce94
```

---

## API 使用指南

### Python API

**基本用法**：

```python
from pathlib import Path
from orchestration.graph import run_swarm_task

result = run_swarm_task(
    user_input="写一个 Hello World 程序",
    workspace_path=Path("/tmp/workspace")
)

print(result["status"])  # "completed"
print(result["output"])  # {"message": "任务完成", "files": [...]}
```

**使用检查点持久化**：

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from orchestration.graph import create_swarm_graph
from orchestration.state import create_initial_state

workspace = Path("/tmp/workspace")
state = create_initial_state("写一个计算器程序")

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = create_swarm_graph(workspace, checkpointer=checkpointer)
    result = graph.invoke(
        state,
        config={"configurable": {"thread_id": "task-123"}}
    )

print(result["status"])
```

**恢复中断任务**：

```python
from orchestration.graph import resume_from_checkpoint

result = await resume_from_checkpoint(
    workspace_path=Path("/tmp/workspace"),
    thread_id="task-123",
    db_path="checkpoints.db"
)
```

---

### HTTP API

**创建任务**：

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "写一个 Hello World 程序",
    "context": {"target_language": "Python"},
    "config": {"max_iterations": 5}
  }'

# 响应
{
  "task_id": "task_20260122_184455_7c08ce94",
  "status": "planning",
  "created_at": "2026-01-22T18:44:55Z"
}
```

**查询任务状态**：

```bash
curl http://localhost:8000/api/v1/tasks/task_20260122_184455_7c08ce94

# 响应
{
  "task_id": "task_20260122_184455_7c08ce94",
  "status": "executing",
  "current_subtask": 2,
  "total_subtasks": 5,
  "elapsed_seconds": 156
}
```

**恢复中断任务**：

```bash
curl -X POST http://localhost:8000/api/v1/tasks/task_20260122_184455_7c08ce94/resume \
  -H "Content-Type: application/json" \
  -d '{"user_input": "接受当前结果"}'
```

---

## GUI 使用指南

### 启动 GUI

```bash
cd ~/projects/MacCortex/Frontend
npm start
```

浏览器打开 `http://localhost:3000`

### GUI 界面

```
┌─────────────────────────────────────────────────────┐
│ MacCortex Slow Lane                                  │
├─────────────────────────────────────────────────────┤
│ 任务输入框：                                          │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 写一个命令行待办事项管理工具（Python）...         │ │
│ └─────────────────────────────────────────────────┘ │
│ [🚀 开始任务] [📁 选择工作空间] [⚙️ 设置]           │
├─────────────────────────────────────────────────────┤
│ 任务进度：                                           │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 40%     │
│                                                      │
│ 当前步骤：Coder - 生成 task-2 代码                  │
│ 子任务进度：2 / 5 完成                               │
│ 已用时间：3 分 45 秒                                 │
│ 预计剩余：5 分 30 秒                                 │
├─────────────────────────────────────────────────────┤
│ 实时日志：                                           │
│ [18:44:55] Planner: 任务拆解完成，共 5 个子任务     │
│ [18:45:12] Coder: 开始生成 task-1 代码               │
│ [18:45:47] Reviewer: 代码通过审查                    │
│ [18:46:03] Coder: 开始生成 task-2 代码               │
│ ...                                                  │
└─────────────────────────────────────────────────────┘
```

### HITL 交互

当 Reflector 判断任务需要用户介入时，GUI 会弹出对话框：

```
┌────────────────────────────────────┐
│ 需要您的决策                        │
├────────────────────────────────────┤
│ 整体质量检查未通过：                │
│                                    │
│ 问题：生成的代码缺少错误处理        │
│                                    │
│ 建议：添加 try-except 块处理文件    │
│      不存在的情况                   │
│                                    │
│ 您的选择：                          │
│ ( ) 接受当前结果                    │
│ ( ) 提供修改建议（重新生成）        │
│ (*) 取消任务                        │
│                                    │
│ [确定] [取消]                       │
└────────────────────────────────────┘
```

---

## 最佳实践

### 1. 任务描述技巧

**✅ 好的任务描述**：

```
写一个命令行待办事项管理工具（Python），要求：
1. 支持 add/list/done/delete 四个功能
2. 数据持久化到 JSON 文件
3. 使用 rich 库美化输出（彩色表格）
4. 包含完整的错误处理
5. 可以直接运行：python todo.py list
```

**❌ 差的任务描述**：

```
写一个待办事项程序
```

**原因**：
- 好的描述：明确需求、技术栈、验收标准
- 差的描述：模糊、缺少细节、Planner 需要猜测

---

### 2. 选择合适的模型

| 任务类型 | 推荐模型 | 原因 |
|---------|---------|------|
| Hello World | Ollama (免费) | 简单任务，本地模型足够 |
| 单文件代码（<200 行） | Ollama 或 Claude API | 根据预算选择 |
| 多文件项目 | Claude API（强制） | 需要深度推理和架构设计 |
| 技术调研 | Claude API | 需要联网搜索和综合分析 |

---

### 3. 设置合理的超时时间

| 任务复杂度 | 推荐超时时间 | 备注 |
|-----------|------------|------|
| 简单（1 个子任务） | 600 秒（10 分钟） | 包含 Coder ↔ Reviewer 迭代 |
| 中等（3-5 个子任务） | 1800 秒（30 分钟） | 本地模型需要更长时间 |
| 复杂（5-10 个子任务） | 3600 秒（1 小时） | 包含调研和工具执行 |

---

### 4. 工作空间管理

**推荐目录结构**：

```
~/Documents/MacCortex-Workspaces/
├── 2026-01-22-todo-cli/      # 按日期 + 项目名命名
│   ├── task-1.py
│   ├── task-2.py
│   └── todo.py
├── 2026-01-22-calculator/
│   └── calculator.py
└── .snapshots/               # 回滚快照（自动生成）
    └── snapshot_1737564295000.json
```

**自动清理**（避免磁盘占满）：

```bash
# 删除 7 天前的工作空间
find ~/Documents/MacCortex-Workspaces -type d -mtime +7 -exec rm -rf {} \;

# 清理快照（保留最近 10 个）
python -m orchestration.cli cleanup-snapshots --keep 10
```

---

### 5. Token 预算管理

**查看 Token 消耗**：

```bash
python -m orchestration.cli stats

# 输出
Total tasks: 15
Total tokens: 1,250,000
Average tokens per task: 83,333
Estimated cost: $3.12 (at $0.0025/1K tokens)

Cache stats:
  Hit rate: 66.7%
  Saved tokens: 420,000
  Saved cost: $1.05
```

**节省 Token 的技巧**：
1. **启用缓存**：相似任务重复使用缓存响应
2. **优先本地模型**：简单任务使用 Ollama
3. **精简任务描述**：避免冗长的上下文信息
4. **减少最大迭代次数**：Coder ↔ Reviewer 最多 3 次迭代

---

## 故障排除

### 问题 1：任务一直卡在 "planning" 状态

**可能原因**：
- Planner LLM 响应超时
- API Key 无效或过期

**解决方案**：

```bash
# 检查 API Key
echo $ANTHROPIC_API_KEY

# 测试 API 连接
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model": "claude-sonnet-4-20250514", "max_tokens": 10, "messages": [{"role": "user", "content": "Hi"}]}'

# 如果失败，使用本地模型
python -m orchestration.cli run "任务描述" --local-model
```

---

### 问题 2：Coder 生成的代码无法执行

**可能原因**：
- 代码缺少 import 语句
- 语法错误
- Reviewer 达到最大迭代次数仍未通过

**解决方案**：

```bash
# 查看详细错误日志
python -m orchestration.cli logs task_20260122_184455_7c08ce94

# 手动修复代码
vim /tmp/workspace/task-1.py

# 标记为通过并继续
python -m orchestration.cli override task_20260122_184455_7c08ce94 --subtask task-1 --pass
```

---

### 问题 3：本地模型响应速度慢

**可能原因**：
- GPU 未启用
- 模型过大（如 70B 参数模型）
- 内存不足

**解决方案**：

```bash
# 检查 GPU 状态
ollama ps

# 输出示例（GPU 已启用）
NAME            ID      SIZE     PROCESSOR
qwen3:14b       abc123  9.3 GB   Metal

# 如果 PROCESSOR 显示 CPU，说明 GPU 未启用
# 解决方案：重启 Ollama
brew services restart ollama

# 如果内存不足，换用小模型
ollama pull qwen2.5:0.5b  # 仅 397MB
python -m orchestration.cli run "任务描述" --local-model --model qwen2.5:0.5b
```

---

### 问题 4：HITL 对话框未出现

**可能原因**：
- GUI 未启动
- WebSocket 连接断开

**解决方案**：

```bash
# 检查 GUI 状态
curl http://localhost:3000

# 检查 WebSocket 连接
wscat -c ws://localhost:8000/ws/tasks/task_20260122_184455_7c08ce94

# 重启 GUI
cd ~/projects/MacCortex/Frontend
npm start
```

---

### 问题 5：快照占用磁盘空间过大

**可能原因**：
- 工作空间包含大文件（如数据集、模型文件）
- 快照数量过多

**解决方案**：

```bash
# 查看快照大小
du -sh ~/Documents/MacCortex-Workspaces/.snapshots

# 清理快照（保留最近 5 个）
python -m orchestration.cli cleanup-snapshots --keep 5

# 排除大文件（在 .gitignore 风格配置中）
echo "*.csv" >> ~/Documents/MacCortex-Workspaces/.snapshotignore
echo "*.db" >> ~/Documents/MacCortex-Workspaces/.snapshotignore
echo "*.bin" >> ~/Documents/MacCortex-Workspaces/.snapshotignore
```

---

## 常见问题 (FAQ)

### Q1: Slow Lane 和 Fast Lane 有什么区别？

| 特性 | Fast Lane | Slow Lane |
|------|-----------|-----------|
| 响应时间 | 1-5 秒 | 4-23 分钟 |
| 任务复杂度 | 简单（单轮问答） | 复杂（多步骤、多文件） |
| Agent 数量 | 1 个 | 6 个（Planner、Coder、Reviewer、Researcher、ToolRunner、Reflector） |
| 自纠错能力 | 无 | 有（Coder ↔ Reviewer 循环） |
| 状态持久化 | 无 | 有（LangGraph Checkpointer） |
| HITL 支持 | 无 | 有 |

---

### Q2: 如何降低成本？

1. **优先使用本地模型**（Ollama qwen3:14b）：免费
2. **启用 Token 缓存**：节省 30-50% API 成本
3. **精简任务描述**：减少输入 Token 数量
4. **减少最大迭代次数**：`--max-iterations 3`

---

### Q3: 支持哪些编程语言？

目前主要支持 **Python**。其他语言（JavaScript、Go、Rust）的支持正在开发中（Phase 5）。

---

### Q4: 如何扩展工具集？

参见 [PHASE_4_DEVELOPER_GUIDE.md](PHASE_4_DEVELOPER_GUIDE.md) 的"添加新工具"章节。

---

### Q5: 任务执行失败后如何恢复？

使用回滚功能：

```python
from orchestration.rollback import RollbackManager

rollback = RollbackManager(workspace_path=Path("/tmp/workspace"))

# 列出可用快照
snapshots = rollback.list_snapshots()
for snap in snapshots:
    print(f"{snap['id']}: {snap['description']}")

# 回滚到指定快照
restored_state = rollback.rollback_to_snapshot("snapshot_1737564295000")
```

---

## 总结

MacCortex Slow Lane 是一个强大的多智能体协作系统，适合处理复杂的编程任务、技术调研和自动化工作流。通过合理使用本地模型、Token 缓存和智能路由，可以在保证质量的同时控制成本。

**下一步**：
- 查看 [PHASE_4_DEVELOPER_GUIDE.md](PHASE_4_DEVELOPER_GUIDE.md) 学习如何扩展系统
- 查看 [PHASE_4_ACCEPTANCE_REPORT.md](PHASE_4_ACCEPTANCE_REPORT.md) 了解验收结果

---

**文档版本**: v1.0
**最后更新**: 2026-01-22
**负责人**: MacCortex 开发团队
**审核状态**: ✅ 已完成
