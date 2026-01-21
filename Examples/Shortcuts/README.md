# MacCortex Shortcuts 使用指南

> **Phase 2 Week 3 Day 13-14: Shortcuts 自动化集成**
> **创建时间**: 2026-01-21
> **macOS 版本要求**: macOS 13.0+ (Ventura)

---

## 📚 概览

MacCortex 通过 **App Intents** 与 macOS Shortcuts 深度集成，让您可以：
- ✨ 通过 Shortcuts 调用 MacCortex Pattern（总结、翻译、提取、格式转换、搜索）
- 🔄 构建自动化工作流（时间触发、App 触发、位置触发）
- 🎯 与其他应用联动（Notes、Mail、Safari、Finder 等）

---

## 🚀 快速开始

### 步骤 1：打开 Shortcuts 应用

```bash
open /System/Applications/Shortcuts.app
```

或在 **启动台（Launchpad）** 中搜索 "Shortcuts"。

### 步骤 2：搜索 MacCortex

1. 点击右上角 **➕** 按钮新建快捷指令
2. 在搜索框输入 **"MacCortex"**
3. 您应该看到以下两个 Actions：
   - **执行 MacCortex Pattern** - 处理文本（总结/翻译/提取等）
   - **获取当前上下文** - 获取当前应用、剪贴板等信息

### 步骤 3：创建第一个 Shortcut

拖拽 **"执行 MacCortex Pattern"** 到工作流区域，配置参数：

| 参数 | 说明 | 示例值 |
|------|------|--------|
| **Pattern ID** | Pattern 类型 | `summarize` / `translate` / `extract` / `format` / `search` |
| **输入文本** | 要处理的文本 | 可选择剪贴板、文件内容、选中文本等 |
| **参数（JSON）** | 可选参数 | `{"length": "short", "language": "zh-CN"}` |

### 步骤 4：运行测试

1. 点击右上角 ▶️ 按钮运行
2. 查看结果输出

---

## 📖 示例 Shortcuts

### 1️⃣ 总结剪贴板内容

**使用场景**: 快速总结长文章、邮件、网页内容

**Shortcut 流程**:
```
1. 获取剪贴板
2. 执行 MacCortex Pattern
   - Pattern ID: "summarize"
   - 输入文本: [剪贴板]
   - 参数: {"length": "short", "style": "bullet"}
3. 显示结果
```

**参数说明**:
```json
{
  "length": "short",     // 长度：short（3 句）/ medium（5 句）/ long（段落）
  "style": "bullet"      // 风格：bullet（要点）/ paragraph（段落）/ headline（标题）
}
```

---

### 2️⃣ 翻译选中文本

**使用场景**: 快速翻译网页、文档中的选中文本

**Shortcut 流程**:
```
1. 运行 AppleScript：
   tell application "System Events"
       keystroke "c" using command down
       delay 0.2
   end tell

2. 获取剪贴板
3. 执行 MacCortex Pattern
   - Pattern ID: "translate"
   - 输入文本: [剪贴板]
   - 参数: {"target_language": "en-US", "style": "formal"}
4. 显示结果
5. 复制到剪贴板
```

**参数说明**:
```json
{
  "target_language": "en-US",   // 目标语言：zh-CN / en-US / ja-JP / ko-KR / es-ES / fr-FR
  "style": "formal"              // 风格：formal（正式）/ casual（随意）/ technical（技术）
}
```

---

### 3️⃣ 提取邮件联系信息

**使用场景**: 从邮件中批量提取人名、邮箱、电话

**Shortcut 流程**:
```
1. 获取选中的 Mail 邮件
2. 获取邮件正文
3. 执行 MacCortex Pattern
   - Pattern ID: "extract"
   - 输入文本: [邮件正文]
   - 参数: {"entity_types": ["person", "email", "phone"], "extract_dates": true}
4. 显示结果（格式化为列表）
5. 保存到 Notes
```

**参数说明**:
```json
{
  "entity_types": ["person", "email", "phone"],  // 实体类型
  "extract_keywords": true,                       // 提取关键词
  "extract_contacts": true,                       // 提取联系人
  "extract_dates": true                           // 提取日期
}
```

---

### 4️⃣ 格式转换（JSON ↔ YAML）

**使用场景**: 开发者工具，快速转换配置文件格式

**Shortcut 流程**:
```
1. 获取剪贴板
2. 执行 MacCortex Pattern
   - Pattern ID: "format"
   - 输入文本: [剪贴板]
   - 参数: {"from_format": "json", "to_format": "yaml", "prettify": true}
3. 复制到剪贴板
4. 显示通知："✅ 已转换为 YAML 并复制到剪贴板"
```

**参数说明**:
```json
{
  "from_format": "json",         // 源格式：json / yaml / csv / markdown / xml
  "to_format": "yaml",           // 目标格式：json / yaml / csv / markdown / xml
  "prettify": true               // 美化输出
}
```

---

### 5️⃣ 网络搜索并总结

**使用场景**: 快速研究话题，获取互联网信息摘要

**Shortcut 流程**:
```
1. 询问输入（"请输入搜索关键词"）
2. 执行 MacCortex Pattern
   - Pattern ID: "search"
   - 输入文本: [用户输入]
   - 参数: {"search_type": "hybrid", "num_results": 5}
3. 显示结果（富文本格式）
4. 保存到 Notes（标题：搜索 [关键词] - [日期]）
```

**参数说明**:
```json
{
  "search_type": "hybrid",       // 搜索类型：web / semantic / hybrid
  "engine": "duckduckgo",        // 搜索引擎：duckduckgo
  "num_results": 5,              // 结果数量：1-10
  "language": "zh-CN"            // 搜索语言
}
```

---

### 6️⃣ 智能上下文感知工作流

**使用场景**: 根据当前活跃应用自动选择 Pattern

**Shortcut 流程**:
```
1. 获取当前上下文（MacCortex Action）
2. 解析 JSON → 提取 "app_bundle_id"
3. 条件判断：
   - 如果是 Mail.app → 执行 extract（提取联系信息）
   - 如果是 Safari.app → 执行 summarize（总结网页）
   - 如果是 Notes.app → 执行 translate（翻译笔记）
   - 否则 → 显示通知"当前应用不支持自动化"
4. 获取剪贴板
5. 执行相应 Pattern
6. 显示结果
```

---

## 🔧 触发器（Triggers）

### 时间触发

**示例**: 每天早上 9:00 总结未读邮件

1. 创建上述"总结剪贴板内容" Shortcut
2. 点击右上角 **ⓘ** 图标 → **Automation**
3. 添加触发器：**Time of Day** → 9:00 AM
4. 选择要执行的 Shortcut

### App 触发

**示例**: 打开 Safari 时自动总结当前网页

1. 创建 Shortcut：
   ```
   - 运行 AppleScript（获取 Safari 当前页面内容）
   - 执行 MacCortex Pattern（summarize）
   - 显示结果
   ```
2. 添加触发器：**App**  → Safari → **Opened**

### 位置触发

**示例**: 到达办公室时整理今日待办事项

1. 创建 Shortcut：
   ```
   - 获取 Notes 中标记为"待办"的笔记
   - 执行 MacCortex Pattern（extract → 提取日期和关键词）
   - 按优先级排序
   - 显示通知
   ```
2. 添加触发器：**Location** → 到达"办公室"

---

## 🛠️ 高级技巧

### 技巧 1：批量处理文件

**场景**: 批量总结 Finder 中选中的多个文本文件

```
1. 获取 Finder 中的文件
2. 对每个文件重复：
   - 读取文件内容
   - 执行 MacCortex Pattern（summarize）
   - 保存结果到新文件（文件名 + "_summary.txt"）
3. 显示通知："✅ 已处理 [数量] 个文件"
```

### 技巧 2：链式 Pattern 调用

**场景**: 先翻译，再总结

```
1. 获取剪贴板
2. 执行 MacCortex Pattern（translate）
   - 输入：[剪贴板]
   - 参数：{"target_language": "en-US"}
3. 执行 MacCortex Pattern（summarize）
   - 输入：[上一步输出]
   - 参数：{"length": "short"}
4. 显示结果
```

### 技巧 3：与 ChatGPT Shortcut 联动

**场景**: 先用 MacCortex 提取信息，再用 ChatGPT 分析

```
1. 获取选中的 PDF 文件内容
2. 执行 MacCortex Pattern（extract）
   - 提取人名、日期、关键词
3. 执行 ChatGPT Shortcut
   - 输入："请分析以下信息：\\n[MacCortex 输出]"
4. 显示结果
```

---

## 🎤 Siri 语音命令

MacCortex 支持通过 Siri 语音调用！

**示例命令**：
- *"使用 MacCortex 总结文本"*
- *"Summarize with MacCortex"*
- *"用 MacCortex 翻译"*
- *"获取当前上下文"*

**设置自定义命令**：
1. 创建 Shortcut
2. 点击右上角 **ⓘ** → **Add to Siri**
3. 录制自定义语音命令（如 *"总结这段话"*）

---

## ❓ 常见问题

### Q1: 为什么 Shortcuts.app 搜索不到 MacCortex？

**A**: 请确认：
1. MacCortex 已安装并至少运行过一次
2. macOS 版本 ≥ 13.0（Ventura）
3. 重启 Shortcuts.app：
   ```bash
   killall Shortcuts && open /System/Applications/Shortcuts.app
   ```
4. 清除 Shortcuts 缓存：
   ```bash
   rm -rf ~/Library/Caches/com.apple.shortcuts
   ```

### Q2: Shortcut 运行失败，提示"无效的 API URL"

**A**: MacCortex Backend 未启动。请先启动 Backend：
```bash
cd MacCortex/Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

确认 Backend 运行在 `http://localhost:8000`。

### Q3: 如何修改 Backend API 地址？

**A**: 在终端运行：
```bash
defaults write com.maccortex.app BackendAPIBaseURL "http://your-server:8000"
```

### Q4: Shortcut 在后台运行时无法访问剪贴板

**A**: macOS 安全限制。解决方法：
1. 在 Shortcut 开头添加 **"获取剪贴板"** Action
2. 将结果传递给 MacCortex Pattern

### Q5: 参数 JSON 格式错误

**A**: 确保 JSON 格式正确：
- ✅ 正确：`{"length": "short", "style": "bullet"}`
- ❌ 错误：`{length: "short"}`（缺少引号）
- ❌ 错误：`{'length': 'short'}`（使用单引号）

使用 [JSONLint](https://jsonlint.com) 验证 JSON 格式。

---

## 📚 相关资源

- [App Intents 官方文档](https://developer.apple.com/documentation/appintents)
- [Shortcuts 用户指南](https://support.apple.com/guide/shortcuts-mac/welcome/mac)
- [MacCortex Pattern 参数完整文档](../../Docs/PATTERN_PARAMETERS.md)

---

## 🤝 贡献

欢迎分享您的 Shortcut 创意！

**分享步骤**：
1. 导出 Shortcut：在 Shortcuts.app 中右键 → **Export**
2. 提交到 `Examples/Shortcuts/`
3. 在本文档添加使用说明

---

**创建时间**: 2026-01-21
**更新时间**: 2026-01-21
**版本**: v1.0（Phase 2 Week 3 Day 13-14）
