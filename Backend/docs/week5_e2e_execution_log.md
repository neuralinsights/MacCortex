# Week 5: 端到端验收项目执行日志

> **项目**: CLI Todo App
> **开始时间**: 2026-01-22
> **状态**: 🔄 执行中

---

## Day 1: 环境准备与任务提交

**日期**: 2026-01-22
**执行时间**: 开始于 15:13

### ✅ 步骤 1: 环境检查

```bash
# 验证 Backend 目录
pwd
# 输出: /Users/jamesg/projects/MacCortex/Backend

# 检查关键文件
ls -la src/main.py src/api/swarm_routes.py
# ✅ src/main.py: 26,208 bytes
# ✅ src/api/swarm_routes.py: 16,800 bytes
```

### ✅ 步骤 2: 创建工作空间

```bash
# 创建工作空间目录
mkdir -p /tmp/mytodo_workspace
chmod 755 /tmp/mytodo_workspace

# 验证权限
ls -ld /tmp/mytodo_workspace
# 输出: drwxr-xr-x@ 2 jamesg wheel 64 22 Jan 15:13 /tmp/mytodo_workspace
# ✅ 工作空间已创建，权限正确
```

### ✅ 步骤 3: 启动 Backend API（已修复）

**问题排查过程**:
1. **问题 1**: `pip: command not found`
   - 原因: 系统使用 Homebrew Python，只有 `pip3`
   - 修复: 将脚本中的 `python` 改为 `python3`，`pip` 改为 `python3 -m pip`

2. **问题 2**: `externally-managed-environment`
   - 原因: Homebrew Python (PEP 668) 禁止系统级安装包
   - 修复: 修改 `start_backend.sh` 自动创建并激活虚拟环境
   - 修改文件: `/Users/jamesg/projects/MacCortex/Backend/scripts/start_backend.sh`
   - 修改时间: 2026-01-22 15:30 (NZDT)

3. **问题 3**: `依赖冲突 - numpy 版本不兼容`
   - 错误信息: `langchain 0.1.0 depends on numpy<2 and >=1`（与 numpy==2.4.1 冲突）
   - 原因: 旧版 langchain 不支持 numpy 2.x
   - 修复策略: 升级所有包到最新版本
   - 修改内容:
     - `numpy>=2.0.0`（升级到 numpy 2.x）
     - `langchain>=0.3.0`（升级到支持 numpy 2.x 的版本）
     - `langchain-community>=0.3.0`
     - `langgraph>=0.2.0`
   - 修改文件: `/Users/jamesg/projects/MacCortex/Backend/requirements.txt`
   - 修改时间: 2026-01-22 15:35 (NZDT)
   - 注意: langchain API 可能有变更，需在启动后验证

4. **问题 4**: `依赖冲突 - httpx 版本不兼容`
   - 错误信息: `ollama 0.6.1 depends on httpx>=0.27`（与 httpx==0.26.0 冲突）
   - 原因: 旧版 httpx 不满足 ollama 0.6.1 的要求
   - 修复: `httpx>=0.27.0`（升级到兼容版本）
   - 修改文件: `/Users/jamesg/projects/MacCortex/Backend/requirements.txt`
   - 修改时间: 2026-01-22 15:37 (NZDT)

5. **问题 5**: `ChromaDB 与 Python 3.14 不兼容`
   - 错误信息: `Could not find a version that satisfies the requirement onnxruntime>=1.14.1`
   - 环境信息: Python 3.14.2, macOS ARM64
   - 原因: ChromaDB 的依赖 onnxruntime 尚未发布 Python 3.14 兼容版本
   - 修复策略: 暂时禁用 ChromaDB
   - 理由: Week 5 CLI Todo App 验收项目不需要向量数据库
   - 修改: 注释掉 `chromadb==0.4.22`
   - 修改文件: `/Users/jamesg/projects/MacCortex/Backend/requirements.txt`
   - 修改时间: 2026-01-22 15:40 (NZDT)
   - 后续: 待 onnxruntime 支持 Python 3.14 后再启用，或使用 Python 3.11/3.12 虚拟环境

6. **问题 6**: `LangGraph 1.0+ API 变更`
   - 错误信息: `ModuleNotFoundError: No module named 'langgraph.checkpoint.sqlite'`
   - 原因: LangGraph 1.0+ 重构了 checkpoint API，移除了 SQLite checkpoint
   - 修复:
     - 移除 `SqliteSaver` 和 `AsyncSqliteSaver` 导入
     - 创建 `src/orchestration/checkpoints.py` 提供 `InMemorySaver` 别名
     - 修改类型注解为仅支持 `MemorySaver`
   - 修改文件:
     - `/Users/jamesg/projects/MacCortex/Backend/src/orchestration/graph.py`
     - `/Users/jamesg/projects/MacCortex/Backend/src/orchestration/checkpoints.py` (新建)
   - 修改时间: 2026-01-22 15:45 (NZDT)

7. **问题 7**: `缺少 langchain-anthropic 包`
   - 错误信息: `ModuleNotFoundError: No module named 'langchain_anthropic'`
   - 原因: requirements.txt 未包含 Anthropic LLM 集成包
   - 修复: 添加 `langchain-anthropic>=0.3.0` 到 requirements.txt
   - 安装: `pip install langchain-anthropic` (已完成)
   - 修改时间: 2026-01-22 15:48 (NZDT)

**当前启动命令**:
```bash
cd /Users/jamesg/projects/MacCortex/Backend
./scripts/start_backend.sh
```

**脚本自动执行流程**:
1. 检查虚拟环境是否存在
2. 如不存在，自动创建虚拟环境 (`python3 -m venv venv`)
3. 激活虚拟环境
4. 在虚拟环境中安装依赖 (`pip install -r requirements.txt`)
5. 检查关键文件 (`src/main.py`, `src/api/swarm_routes.py`)
6. 启动 FastAPI 服务器

**期望输出**:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**验证 API**:
- 打开浏览器访问: http://localhost:8000/docs
- 验证 Swarm API 端点存在:
  - POST /swarm/tasks
  - GET /swarm/tasks/{task_id}
  - POST /swarm/tasks/{task_id}/approve
  - GET /swarm/tasks
  - WebSocket /swarm/ws/{task_id}

---

### ✅ 步骤 4: 启动 SwiftUI 前端

**项目类型**: Swift Package Manager (SPM) 项目

**打开方式**:
```bash
open -a Xcode /Users/jamesg/projects/MacCortex/Package.swift
```

**问题排查**:
1. **问题**: `Filename "BatchTranslationView.swift" used twice`
   - 原因: 文件同时存在于根目录和 Views 子目录
   - 修复: 删除根目录下的重复文件
   - 命令: `rm Sources/MacCortexApp/BatchTranslationView.swift`
   - 修复时间: 2026-01-22 16:45 (NZDT)

**运行步骤**:
1. ✅ Xcode 已打开项目（自动解析 SPM 依赖）
2. 选择 Scheme: **MacCortexApp**
3. 选择目标: **My Mac**
4. 点击 Run (⌘R)
5. 验证 SwarmOrchestrationView 加载成功

**预期界面**:
- 左侧边栏: "任务历史" (空列表)
- 主视图: "Swarm 编排系统" 输入表单
- 任务描述输入框
- 工作空间路径选择
- 执行选项（HITL / CodeReview）
- "开始执行"按钮

---

### 🔄 步骤 5: 提交第一个任务

**任务输入**:
```
用户输入: 创建一个 CLI Todo 应用，支持以下功能：
1. add <task> - 添加新任务
2. list [--all] - 列出任务（默认仅未完成）
3. done <task_id> - 标记任务为完成
4. delete <task_id> - 删除任务
5. clear --done - 清除所有已完成任务
6. help - 显示帮助信息

技术要求：
- 使用 Python 3.9+
- 使用 Click 框架处理命令行参数
- 使用 JSON 文件存储数据（~/.mytodo/tasks.json）
- 使用 colorama 实现彩色输出
- 包含基础单元测试
- 提供 README 使用说明

文件结构：
- mytodo.py (主程序)
- requirements.txt (依赖列表)
- README.md (使用文档)
- tests/test_mytodo.py (单元测试)

工作空间路径: /tmp/mytodo_workspace

启用 HITL: ✅
启用代码审查: ✅
```

**点击"开始执行"按钮**

**预期响应**:
1. 按钮变为"提交中..."
2. 任务创建成功
3. 返回任务 ID（格式：`task_YYYYMMDD_HHMMSS_xxxxxxxx`）
4. WebSocket 连接建立
5. 左侧边栏显示新任务
6. 主视图切换到工作流可视化

---

### 📝 待观察

- [ ] Backend 启动成功（步骤 3）
- [ ] Frontend 启动成功（步骤 4）
- [ ] 任务提交成功（步骤 5）
- [ ] WebSocket 连接建立
- [ ] Planner Agent 开始执行

---

## Day 2: Swarm 编排执行（计划）

**目标**: 观察 5 个 Agent 完整执行过程

**待完成**:
- Planner Agent 任务拆解
- Coder Agent 代码生成
- Reviewer Agent 代码审查
- HITL 中断触发与审批
- ToolRunner Agent 文件创建
- Reflector Agent 总结反思

---

## Day 3: 应用验证（计划）

**目标**: 测试生成的 CLI Todo App

**待完成**:
- 安装依赖
- 测试所有命令
- 验证数据持久化
- 运行单元测试

---

## Day 4: UI 功能测试（计划）

**目标**: 验证 Slow Lane UI 所有功能

**待完成**:
- 任务历史查看
- 任务详情验证
- WebSocket 实时性测试
- HITL 交互测试
- 错误处理测试

---

## Day 5: 文档与总结（计划）

**目标**: 编写验收报告

**待完成**:
- 验收报告编写
- 代码存档
- 录屏演示（可选）

---

**下一步**: 手动执行步骤 3-5（需要人工操作 Backend 启动与 Xcode 运行）
