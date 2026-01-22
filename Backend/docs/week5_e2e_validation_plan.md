# Week 5: 端到端验收项目 - CLI Todo App

> **版本**: v1.0
> **创建时间**: 2026-01-22
> **目标**: 使用完整的 Slow Lane UI + LangGraph Swarm 编排构建真实 CLI Todo 应用
> **工期**: 3-5 天

---

## 📋 项目概览

### 项目目标

通过构建一个**功能完整的 CLI Todo 应用**，验证以下系统组件：

1. ✅ **Slow Lane UI** - SwiftUI 前端界面
2. ✅ **Swarm API** - Backend RESTful API + WebSocket
3. ✅ **LangGraph 编排** - 5 个 Agent 协作
4. ✅ **HITL 机制** - 人机回环审批
5. ✅ **端到端流程** - 从用户输入到代码生成与执行

### 应用需求

**CLI Todo App 功能列表**:
```
mytodo - 极简 CLI 任务管理工具

命令:
  mytodo add <task>           添加新任务
  mytodo list [--all]         列出任务（默认仅未完成）
  mytodo done <task_id>       标记任务为完成
  mytodo delete <task_id>     删除任务
  mytodo clear --done         清除所有已完成任务
  mytodo help                 显示帮助信息

数据存储:
  ~/.mytodo/tasks.json        JSON 文件持久化

技术栈:
  - Python 3.9+
  - Click (CLI 框架)
  - JSON 文件存储
  - 彩色输出 (colorama)
```

---

## 🎯 验收标准（10 项必须全部通过）

| # | 验收项 | 测试方法 | 期望结果 |
|---|--------|----------|----------|
| 1 | **任务提交成功** | 在 Slow Lane UI 输入"创建 CLI Todo App" | Backend 创建任务，WebSocket 连接成功 |
| 2 | **Planner 拆解任务** | 观察工作流可视化 | Planner 输出 5+ 子任务 |
| 3 | **Coder 生成代码** | 等待 Coder 完成 | 生成 `mytodo.py` + `tasks.json` 模板 |
| 4 | **Reviewer 审查代码** | 观察 Reviewer 状态 | 检测代码质量，无严重问题 |
| 5 | **HITL 触发（文件写入）** | 等待 HITL 中断 | 弹出审批窗口，显示文件路径 |
| 6 | **HITL 批准执行** | 点击"批准"按钮 | 文件成功创建到工作空间 |
| 7 | **ToolRunner 执行** | 观察 ToolRunner 状态 | 安装依赖、执行测试（如有） |
| 8 | **Reflector 总结** | 等待任务完成 | 输出执行总结与改进建议 |
| 9 | **生成的应用可运行** | 执行 `python mytodo.py add "测试任务"` | 成功添加任务，输出确认 |
| 10 | **任务历史可查询** | 在 TaskHistoryView 搜索 | 显示完整任务记录与输出 |

**通过条件**: 10/10 必须全部通过 ✅

---

## 📐 实施计划（5 天）

### Day 1: 环境准备与任务提交

**目标**: 启动 Backend + Frontend，提交第一个任务

**步骤**:
1. 启动 Backend API
   ```bash
   cd /Users/jamesg/projects/MacCortex/Backend
   source venv/bin/activate
   python src/main.py
   # 验证: http://localhost:8000/docs
   ```

2. 启动 SwiftUI 前端（手动）
   - 在 Xcode 中打开 MacCortex 项目
   - 运行 MacCortexApp target
   - 验证 SwarmOrchestrationView 加载成功

3. 提交第一个任务
   - **用户输入**: "创建一个 CLI Todo 应用，支持 add/list/done/delete 命令，使用 JSON 文件存储"
   - **工作空间路径**: `/tmp/mytodo_workspace`
   - **启用 HITL**: ✅
   - **启用代码审查**: ✅

4. 观察初始响应
   - 验证任务 ID 生成
   - 验证 WebSocket 连接成功
   - 验证 Planner 开始执行

**预期时间**: 2-3 小时

---

### Day 2: Swarm 编排执行与 HITL 交互

**目标**: 完整观察 5 个 Agent 协作过程

**步骤**:

1. **Planner Agent** (预计 1-2 分钟)
   - 观察工作流可视化中 Planner 状态变为"🔵 执行中"
   - 等待完成后查看子任务列表（应包含）:
     ```
     1. 设计 CLI 命令行参数解析
     2. 实现 JSON 数据存储层
     3. 实现任务增删改查逻辑
     4. 添加彩色输出
     5. 编写帮助文档
     6. 单元测试
     ```

2. **Coder Agent** (预计 2-4 分钟)
   - 观察 Coder 状态
   - 等待代码生成完成
   - 预期生成文件:
     ```
     mytodo_workspace/
     ├── mytodo.py          # 主程序
     ├── requirements.txt   # 依赖（click, colorama）
     ├── README.md          # 使用说明
     └── tests/
         └── test_mytodo.py # 单元测试
     ```

3. **Reviewer Agent** (预计 1 分钟)
   - 观察 Reviewer 分析代码
   - 查看审查报告（应包含）:
     - 代码风格检查
     - 潜在 bug 检测
     - 安全性评估
     - 改进建议

4. **HITL 中断 #1 - 文件写入审批** (人工交互)
   - **触发条件**: ToolRunner 尝试创建文件
   - **中断详情**:
     ```
     操作类型: tool_execution
     工具名称: write_file
     风险等级: 🟡 中风险
     参数详情:
       - path: /tmp/mytodo_workspace/mytodo.py
       - content: [代码内容]
     ```
   - **操作**: 点击"批准"按钮
   - **验证**: 文件成功创建

5. **HITL 中断 #2 - 依赖安装审批** (可选，取决于配置)
   - **触发条件**: pip install click colorama
   - **操作**: 点击"批准"
   - **验证**: 依赖成功安装

6. **ToolRunner Agent** (预计 1-2 分钟)
   - 执行文件创建
   - 安装依赖
   - 运行测试（如有）
   - 验证所有操作成功

7. **Reflector Agent** (预计 1 分钟)
   - 分析整体执行过程
   - 生成总结报告:
     - 任务完成情况
     - 代码质量评估
     - 改进建议
     - 后续优化方向

**预期时间**: 4-6 小时（包括观察与记录）

---

### Day 3: 验证生成的应用

**目标**: 手动测试生成的 CLI Todo App

**步骤**:

1. 进入工作空间
   ```bash
   cd /tmp/mytodo_workspace
   ```

2. 检查生成的文件
   ```bash
   ls -la
   # 预期输出:
   # mytodo.py
   # requirements.txt
   # README.md
   # tests/test_mytodo.py
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 测试基础命令
   ```bash
   # 显示帮助
   python mytodo.py help

   # 添加任务
   python mytodo.py add "学习 LangGraph"
   python mytodo.py add "完成 MacCortex Phase 4"
   python mytodo.py add "编写测试用例"

   # 列出所有任务
   python mytodo.py list

   # 标记任务完成
   python mytodo.py done 1

   # 再次列出（验证状态更新）
   python mytodo.py list --all

   # 删除任务
   python mytodo.py delete 2

   # 清除已完成任务
   python mytodo.py clear --done
   ```

5. 验证数据持久化
   ```bash
   cat ~/.mytodo/tasks.json
   # 验证 JSON 格式正确
   # 验证任务数据完整
   ```

6. 运行单元测试（如有）
   ```bash
   pytest tests/
   ```

**验收清单**:
- ✅ 所有命令正常工作
- ✅ 任务可以添加、查看、完成、删除
- ✅ 数据持久化到 JSON 文件
- ✅ 彩色输出正常显示
- ✅ 帮助信息清晰完整
- ✅ 无报错或异常

**预期时间**: 2-3 小时

---

### Day 4: UI 功能完整测试

**目标**: 验证 Slow Lane UI 所有功能

**测试场景**:

1. **任务历史查看**
   - 打开 TaskHistoryView
   - 搜索"CLI Todo"
   - 验证任务记录存在
   - 点击任务 → 查看详情

2. **任务详情验证**
   - 验证所有字段正确:
     - 用户输入
     - 工作空间路径
     - 任务状态（已完成）
     - 进度（100%）
     - 创建时间 / 更新时间
     - 耗时统计
   - 验证 Agent 执行状态:
     - 所有 5 个 Agent 状态为"已完成"
   - 验证 HITL 中断记录:
     - 显示审批历史
     - 显示操作类型与参数
   - 验证输出结果:
     - 摘要信息
     - 创建的文件列表

3. **WebSocket 实时性测试**
   - 提交第二个任务（简单任务，如"创建 Hello World 脚本"）
   - 实时观察工作流可视化:
     - Agent 状态实时更新
     - 进度条平滑增长
     - 当前 Agent 高亮动画
     - 连接状态横幅显示"已连接"

4. **HITL 交互测试**
   - 等待 HITL 中断触发
   - 测试所有 4 种审批动作:
     - ✅ **批准**: 验证操作继续执行
     - ❌ **拒绝**: 验证操作被跳过（提交新任务测试）
     - ✏️ **修改参数**: 进入编辑模式 → 修改文件路径 → 提交 → 验证使用新路径
     - ⏹️ **终止任务**: 验证整个任务立即终止

5. **错误处理测试**
   - 提交无效输入（空字符串）
   - 提交无效工作空间路径
   - 断开 Backend → 观察错误提示
   - 重新连接 Backend → 验证恢复

**预期时间**: 3-4 小时

---

### Day 5: 文档编写与总结

**目标**: 编写完整的验收报告

**交付物**:

1. **验收报告** (`week5_e2e_validation_report.md`)
   - 执行概览
   - 10 项验收标准达成情况
   - 测试截图与日志
   - 生成的代码质量分析
   - 发现的问题与改进建议
   - 性能指标统计
   - 用户体验评估

2. **生成的应用代码存档**
   ```bash
   cp -r /tmp/mytodo_workspace /Users/jamesg/projects/MacCortex/Examples/mytodo_app
   ```

3. **录屏演示**（可选）
   - 完整录制从任务提交到应用运行的过程
   - 时长: 5-10 分钟
   - 格式: MP4

**预期时间**: 2-3 小时

---

## 📊 关键指标测量

### 性能指标

| 指标 | 测量方法 | 期望值 |
|------|----------|--------|
| **任务创建延迟** | 点击提交 → 任务 ID 返回 | < 500ms |
| **WebSocket 连接延迟** | 任务创建 → 连接成功 | < 1s |
| **Planner 执行时间** | Planner 开始 → 完成 | 1-3 分钟 |
| **Coder 执行时间** | Coder 开始 → 完成 | 2-5 分钟 |
| **整体任务耗时** | 任务开始 → 完成 | 5-15 分钟 |
| **UI 响应性** | 状态更新延迟 | < 200ms |
| **内存占用** | Backend + Frontend | < 500MB |

### 质量指标

| 指标 | 测量方法 | 期望值 |
|------|----------|--------|
| **代码可运行性** | 直接执行生成的代码 | 100% 无错误 |
| **功能完整性** | 测试所有 6 个命令 | 6/6 正常工作 |
| **代码质量** | Reviewer 评分 | ≥ 80/100 |
| **测试覆盖率** | 运行单元测试 | ≥ 60% |
| **用户体验** | 手动评分（1-10） | ≥ 8/10 |

---

## 🚨 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|----------|
| LLM 生成代码有 bug | 40% | 高 | Reviewer 审查 + 人工修复 |
| HITL 中断未触发 | 10% | 中 | 检查 ToolRunner 配置 |
| WebSocket 连接不稳定 | 15% | 中 | 增加重连机制 |
| 任务执行超时 | 20% | 低 | 设置合理超时时间 |
| UI 状态不同步 | 5% | 低 | 检查 @Published 绑定 |

---

## 🎯 成功标准

### 必须达成（P0）

1. ✅ 10/10 验收标准全部通过
2. ✅ 生成的应用 100% 可运行
3. ✅ 所有 5 个 Agent 正常工作
4. ✅ HITL 机制正常触发与响应
5. ✅ UI 实时更新无延迟

### 建议达成（P1）

1. ✅ 性能指标全部满足期望值
2. ✅ 质量指标全部满足期望值
3. ✅ 无严重 bug 或异常
4. ✅ 用户体验评分 ≥ 8/10
5. ✅ 文档完整清晰

---

## 📂 文件组织

```
MacCortex/
├── Backend/
│   ├── docs/
│   │   ├── week5_e2e_validation_plan.md       ✅ 本文件
│   │   └── week5_e2e_validation_report.md     （待创建）
│   └── logs/
│       └── week5_task_*.log                    （执行日志）
│
├── Examples/
│   └── mytodo_app/                             （生成的应用）
│       ├── mytodo.py
│       ├── requirements.txt
│       ├── README.md
│       └── tests/
│
└── Demos/
    └── week5_e2e_demo.mp4                      （可选录屏）
```

---

## 🔧 环境准备清单

### Backend

- ✅ Python 3.9+ venv 激活
- ✅ 所有依赖已安装（requirements.txt）
- ✅ FastAPI 服务可启动
- ✅ Swarm API 路由已集成
- ✅ LangGraph agents 已实现

### Frontend

- ✅ Xcode 已安装
- ✅ macOS 12+ (支持 URLSession WebSocket)
- ✅ Swift 数据模型已编译
- ✅ SwarmAPIClient 已集成
- ✅ SwarmOrchestrationView 已实现

### 工作空间

```bash
# 创建工作空间目录
mkdir -p /tmp/mytodo_workspace
chmod 755 /tmp/mytodo_workspace

# 验证权限
ls -ld /tmp/mytodo_workspace
```

### LLM 配置

确保以下环境变量已设置:
```bash
# MLX 本地模型
export MLX_MODEL_PATH="/path/to/mlx/models"

# 或 Ollama
export OLLAMA_HOST="http://localhost:11434"

# 或 OpenAI API（备用）
export OPENAI_API_KEY="sk-..."
```

---

## 📝 执行日志模板

### Day 1 日志

```markdown
## Week 5 Day 1: 环境准备与任务提交

**日期**: 2026-01-22
**执行时间**: 10:00 - 13:00 (3 小时)

### 执行步骤

1. ✅ 启动 Backend API (10:05)
   - 命令: `python src/main.py`
   - 端口: 8000
   - 状态: 成功
   - 日志: 无错误

2. ✅ 启动 SwiftUI 前端 (10:10)
   - 平台: Xcode
   - Target: MacCortexApp
   - 状态: 成功
   - 首次加载时间: 2.3s

3. ✅ 提交第一个任务 (10:15)
   - 用户输入: "创建一个 CLI Todo 应用..."
   - 工作空间: /tmp/mytodo_workspace
   - 任务 ID: task_20260122_101500_abc123
   - WebSocket: 已连接

4. ✅ Planner 开始执行 (10:16)
   - 状态: 🔵 执行中
   - 预计完成: 10:18

### 截图
- backend_startup.png
- frontend_ui.png
- task_submitted.png

### 下一步
Day 2: 观察 Swarm 编排完整执行
```

---

## ✅ 验收签字

**验收人**: ___________
**验收日期**: ___________
**验收结果**: ⬜ 通过 / ⬜ 不通过

**备注**:

---

**计划状态**: ✅ 已批准
**创建时间**: 2026-01-22
**下一步**: 开始 Day 1 执行
