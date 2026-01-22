# Week 5: 端到端验收项目快速启动指南

> **版本**: v1.0
> **创建时间**: 2026-01-22
> **目标**: 快速启动并测试 CLI Todo App 验收项目

---

## 🚀 快速启动（5 分钟）

### 步骤 1: 启动 Backend API

**方式 1: 使用启动脚本（推荐）**
```bash
cd /Users/jamesg/projects/MacCortex/Backend
./scripts/start_backend.sh
```

**方式 2: 手动启动**
```bash
cd /Users/jamesg/projects/MacCortex/Backend
source venv/bin/activate  # 如果使用虚拟环境
python src/main.py
```

**验证**:
- 浏览器打开: http://localhost:8000/docs
- 检查是否有以下端点:
  - POST /swarm/tasks
  - GET /swarm/tasks/{task_id}
  - POST /swarm/tasks/{task_id}/approve
  - GET /swarm/tasks
  - WebSocket /swarm/ws/{task_id}

---

### 步骤 2: 启动 SwiftUI 前端

**注意**: 需要在 Xcode 中手动运行

1. 打开 Xcode
2. 打开项目: `/Users/jamesg/projects/MacCortex/Sources/MacCortex.xcodeproj`
3. 选择 target: `MacCortexApp`
4. 点击 Run (⌘R)

**验证**:
- SwarmOrchestrationView 成功加载
- 看到"Swarm 编排系统"标题
- 任务输入表单正常显示

---

### 步骤 3: 提交 CLI Todo App 任务

**在 SwiftUI 界面中输入**:

**任务描述**:
```
创建一个 CLI Todo 应用，支持以下功能：
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
```

**工作空间路径**:
```
/tmp/mytodo_workspace
```

**执行选项**:
- ✅ 启用 Human-in-the-Loop
- ✅ 启用代码审查

**点击**: "开始执行"

---

### 步骤 4: 观察 Swarm 编排过程

**工作流可视化**:
```
┌─────────────────────────────────────────┐
│ ⚪ Planner 规划器   [待执行]            │
│         ↓                               │
│ ⚪ Coder 编码器     [待执行]            │
│         ↓                               │
│ ⚪ Reviewer 审查器  [待执行]            │
│         ↓                               │
│ ⚪ ToolRunner 执行器 [待执行]           │
│         ↓                               │
│ ⚪ Reflector 反思器  [待执行]           │
└─────────────────────────────────────────┘
```

**预期执行流程**:

1. **Planner** (1-3 分钟)
   - 状态变为 🔵 执行中
   - 拆解为 5+ 子任务
   - 完成后变为 ✅ 已完成

2. **Coder** (2-5 分钟)
   - 状态变为 🔵 执行中
   - 生成 mytodo.py 代码
   - 生成 requirements.txt
   - 生成 README.md
   - 完成后变为 ✅ 已完成

3. **Reviewer** (1-2 分钟)
   - 状态变为 🔵 执行中
   - 检查代码质量
   - 检测潜在问题
   - 完成后变为 ✅ 已完成

4. **HITL 中断** (需要人工操作)
   - **触发**: ToolRunner 尝试写入文件
   - **弹窗显示**:
     ```
     需要您的审批
     AI Agent 请求执行以下操作

     操作类型: tool_execution
     工具名称: write_file
     风险等级: 🟡 中风险

     参数详情:
       path: /tmp/mytodo_workspace/mytodo.py
       content: [代码内容]
     ```
   - **操作**: 点击"批准"按钮
   - **结果**: 文件成功创建

5. **ToolRunner** (1-2 分钟)
   - 状态变为 🔵 执行中
   - 创建所有文件
   - 安装依赖（可能触发第二次 HITL）
   - 运行测试（如有）
   - 完成后变为 ✅ 已完成

6. **Reflector** (1 分钟)
   - 状态变为 🔵 执行中
   - 分析整体执行
   - 生成总结报告
   - 完成后变为 ✅ 已完成

**总耗时**: 约 5-15 分钟

---

### 步骤 5: 测试生成的应用

**方式 1: 使用测试脚本（推荐）**
```bash
cd /Users/jamesg/projects/MacCortex/Backend
./scripts/test_mytodo_app.sh
```

**预期输出**:
```
========================================
  CLI Todo App 功能测试
========================================

📁 工作空间: /tmp/mytodo_workspace

🔍 检查生成的文件
   ✅ mytodo.py
   ✅ requirements.txt
   ✅ README.md

📦 安装依赖
   ✅ 依赖已安装

========================================
  开始功能测试
========================================

🧪 测试: 显示帮助信息
   ✅ 通过

🧪 测试: 添加任务 #1
   ✅ 通过

🧪 测试: 添加任务 #2
   ✅ 通过

...

========================================
  测试总结
========================================

✅ 通过: 11
❌ 失败: 0

🎉 所有测试通过！ (11/11)
```

**方式 2: 手动测试**
```bash
cd /tmp/mytodo_workspace

# 显示帮助
python mytodo.py help

# 添加任务
python mytodo.py add "学习 LangGraph"
python mytodo.py add "完成 MacCortex Phase 4"

# 列出任务
python mytodo.py list

# 标记任务完成
python mytodo.py done 1

# 列出所有任务（含已完成）
python mytodo.py list --all

# 删除任务
python mytodo.py delete 2

# 清除已完成任务
python mytodo.py clear --done
```

---

## 📊 验收检查清单

### 必须通过（10/10）

- [ ] 1. 任务提交成功
- [ ] 2. Planner 拆解任务
- [ ] 3. Coder 生成代码
- [ ] 4. Reviewer 审查代码
- [ ] 5. HITL 触发（文件写入）
- [ ] 6. HITL 批准执行
- [ ] 7. ToolRunner 执行
- [ ] 8. Reflector 总结
- [ ] 9. 生成的应用可运行
- [ ] 10. 任务历史可查询

### UI 功能检查

- [ ] 工作流可视化实时更新
- [ ] Agent 状态正确显示
- [ ] 进度条平滑增长
- [ ] 连接状态横幅正常
- [ ] HITL 弹窗正确显示
- [ ] 任务历史正确记录

### 应用功能检查

- [ ] `add` 命令正常工作
- [ ] `list` 命令正常工作
- [ ] `done` 命令正常工作
- [ ] `delete` 命令正常工作
- [ ] `clear` 命令正常工作
- [ ] `help` 命令正常工作
- [ ] 数据持久化到 JSON 文件
- [ ] 彩色输出正常显示

---

## 🐛 故障排除

### 问题 1: Backend 启动失败

**症状**: `ModuleNotFoundError: No module named 'fastapi'`

**解决方案**:
```bash
cd /Users/jamesg/projects/MacCortex/Backend
source venv/bin/activate
pip install -r requirements.txt
```

---

### 问题 2: WebSocket 连接失败

**症状**: 连接状态显示"错误: ..."

**解决方案**:
1. 确认 Backend 正在运行（http://localhost:8000/docs）
2. 重启 SwiftUI 应用
3. 检查防火墙设置

---

### 问题 3: HITL 中断未触发

**症状**: ToolRunner 直接执行，未弹出审批窗口

**解决方案**:
1. 检查"启用 Human-in-the-Loop"是否勾选
2. 查看 Backend 日志，确认 HITL 配置正确
3. 检查 ToolRunner 的 `require_approval` 设置

---

### 问题 4: 生成的应用无法运行

**症状**: `python mytodo.py` 报错

**解决方案**:
1. 检查文件是否成功创建: `ls -la /tmp/mytodo_workspace`
2. 安装依赖: `pip install -r /tmp/mytodo_workspace/requirements.txt`
3. 检查 Python 版本: `python --version` (需要 3.9+)

---

### 问题 5: 任务执行超时

**症状**: Planner/Coder 长时间无响应

**解决方案**:
1. 检查 LLM 配置（MLX/Ollama/OpenAI API）
2. 查看 Backend 日志
3. 考虑终止任务并重新提交

---

## 📚 相关文档

- **实施计划**: `week5_e2e_validation_plan.md`
- **执行日志**: `week5_e2e_execution_log.md`
- **验收报告**: `week5_e2e_validation_report.md` (待生成)

---

## 🆘 需要帮助？

如果遇到问题，请查看：
1. Backend 日志: 终端输出
2. Frontend 日志: Xcode Console
3. 任务历史: TaskHistoryView → 点击任务 → 查看详情
4. API 文档: http://localhost:8000/docs

---

**快速启动指南结束**

祝验收顺利！🎉
