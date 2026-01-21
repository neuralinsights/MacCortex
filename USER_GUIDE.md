# MacCortex 用户指南

**版本**: 0.5.0 (Phase 2)
**更新日期**: 2026-01-21
**适用平台**: macOS Tahoe 26.2+, Apple Silicon
**语言**: 中文

---

## 目录

1. [欢迎使用 MacCortex](#欢迎使用-maccortex)
2. [核心特性](#核心特性)
3. [系统要求](#系统要求)
4. [安装与首次启动](#安装与首次启动)
5. [权限配置](#权限配置)
6. [界面概览](#界面概览)
7. [5 个 AI Pattern 使用指南](#5-个-ai-pattern-使用指南)
8. [常见操作流程](#常见操作流程)
9. [快捷键与技巧](#快捷键与技巧)
10. [性能与资源](#性能与资源)
11. [故障排查](#故障排查)
12. [获取帮助](#获取帮助)

---

## 欢迎使用 MacCortex

MacCortex 是一款**下一代 macOS 个人智能基础设施**，专为 Apple Silicon 优化，将强大的 AI 能力无缝集成到您的 macOS 工作流中。

### 为什么选择 MacCortex？

✨ **隐私优先**：所有 AI 处理在本地进行，无需联网（搜索功能除外）
⚡ **Apple Silicon 优化**：使用 MLX 框架，充分利用 M 系列芯片的 Neural Engine
🎯 **即用即走**：无需复杂配置，启动即用
🔐 **企业级安全**：内置 Prompt Injection 防护、审计日志、速率限制
🚀 **性能卓越**：Pattern 响应时间 < 2 秒，内存占用 < 110 MB

---

## 核心特性

### 5 个 AI Pattern

| Pattern | 功能 | 使用场景 |
|---------|------|----------|
| **Summarize** | 文本总结 | 长文档摘要、会议纪要、新闻快读 |
| **Extract** | 信息提取 | 联系人提取、日期识别、关键词分析 |
| **Translate** | 多语言翻译 | 英中日韩法德等 10+ 语言互译 |
| **Format** | 格式转换 | JSON↔YAML↔CSV↔Markdown 转换 |
| **Search** | Web 搜索 | DuckDuckGo 实时搜索 + AI 总结 |

### 技术亮点

- 🧠 **本地 LLM**：Llama-3.2-1B-Instruct（MLX 4-bit 量化）
- 🔄 **双 LLM 支持**：MLX（主力）+ Ollama（备选）
- 🛡️ **安全防护**：OWASP LLM01 防护率 95%+
- 📊 **审计日志**：所有操作自动记录，PII 自动脱敏
- ⚙️ **非沙盒架构**：Full Disk Access 授权，功能无阉割

---

## 系统要求

### 最低配置

| 项目 | 要求 |
|------|------|
| **操作系统** | macOS Tahoe 26.2 或更高版本 |
| **处理器** | Apple Silicon (M1/M2/M3/M4/M5) |
| **内存** | 8 GB RAM（推荐 16 GB） |
| **存储空间** | 2 GB 可用空间（MLX 模型约 700 MB） |
| **网络** | 可选（Search Pattern 需要联网） |

### 推荐配置

- **处理器**: M2 Pro 或更高（M3/M4/M5）
- **内存**: 16 GB RAM（可同时运行多个 Pattern）
- **存储**: SSD（提升模型加载速度）

### 兼容性说明

- ✅ 支持：Apple Silicon Mac（M1 及更高）
- ❌ 不支持：Intel Mac（MLX 框架仅支持 Apple Silicon）
- ✅ 支持：macOS Sonoma 14.0+、Sequoia 15.0+、Tahoe 26.0+

---

## 安装与首次启动

### 安装步骤

#### 方式 1：直接下载（推荐）

1. **下载应用**：
   - 访问 [MacCortex 官网](https://maccortex.example.com)（示例）
   - 或从 GitHub Releases 下载 `MacCortex.dmg`

2. **安装应用**：
   ```
   1. 双击 MacCortex.dmg
   2. 将 MacCortex.app 拖动到 Applications 文件夹
   3. 弹出磁盘映像
   ```

3. **首次启动**：
   - 打开 Applications 文件夹
   - 双击 MacCortex.app
   - 如果提示"无法打开"，请参见下方 Gatekeeper 说明

#### 方式 2：Homebrew Cask（开发者推荐）

```bash
# 安装（计划中）
brew install --cask maccortex

# 启动
open /Applications/MacCortex.app
```

### Gatekeeper 绕过（首次启动）

如果 macOS 提示"无法打开应用（未知开发者）"：

**方法 1：右键打开**
```
1. 在 Finder 中找到 MacCortex.app
2. 按住 Control 键并点击应用
3. 选择"打开"
4. 在弹窗中点击"打开"
```

**方法 2：系统设置**
```
1. 系统设置 → 隐私与安全性
2. 找到"MacCortex 已被阻止"提示
3. 点击"仍要打开"
```

**方法 3：命令行（高级）**
```bash
# 移除隔离标记
xattr -d com.apple.quarantine /Applications/MacCortex.app

# 验证签名（可选）
spctl --assess --verbose=4 /Applications/MacCortex.app
```

### 首次启动流程

1. **欢迎界面**：
   - 显示 MacCortex 简介
   - 说明权限需求

2. **Backend 自动启动**：
   - 应用自动启动 Python Backend 服务
   - 首次启动需加载 MLX 模型（约 5-10 秒）

3. **权限引导**：
   - 如果需要 Full Disk Access 权限，会显示引导页面
   - 按照指引完成授权（详见下节）

4. **开始使用**：
   - 授权完成后，即可使用所有 5 个 Pattern

---

## 权限配置

### Full Disk Access（完全磁盘访问）

**为什么需要？**

MacCortex 采用**非沙盒架构**，需要 Full Disk Access 权限以实现：
- 📂 访问 Notes.app 数据（未来功能）
- 🔍 全局文件搜索
- 📋 系统剪贴板增强访问

**配置步骤**：

1. **打开系统设置**：
   ```
   系统设置 → 隐私与安全性 → 完全磁盘访问
   ```

2. **添加 MacCortex**：
   ```
   1. 点击左下角"🔒"解锁
   2. 点击"+"按钮
   3. 浏览到 Applications/MacCortex.app
   4. 点击"打开"
   5. 确保 MacCortex 开关为"开启"（蓝色）
   ```

3. **重启应用**：
   - 完全退出 MacCortex（⌘Q）
   - 重新启动应用

**验证权限**：

MacCortex 会自动检测权限状态：
- ✅ 已授权：状态栏显示"已连接"
- ❌ 未授权：显示权限引导页面

### Accessibility 权限（可选）

**何时需要？**

如果您使用以下功能（Phase 3 计划）：
- 🖱️ Selection Capture（选中文本自动处理）
- ⌨️ 全局快捷键

**配置步骤**（Phase 3 启用时）：
```
系统设置 → 隐私与安全性 → 辅助功能 → 添加 MacCortex
```

---

## 界面概览

### 主界面布局

```
┌─────────────────────────────────────────────┐
│  MacCortex                            🔴🟡🟢 │
├─────────────────────────────────────────────┤
│  Pattern: [Summarize ▼]    [执行 Execute]  │
├─────────────────────────────────────────────┤
│  输入文本 (Input Text)                       │
│  ┌─────────────────────────────────────────┐│
│  │                                         ││
│  │  在这里输入或粘贴文本...                 ││
│  │                                         ││
│  └─────────────────────────────────────────┘│
├─────────────────────────────────────────────┤
│  输出结果 (Output)                          │
│  ┌─────────────────────────────────────────┐│
│  │                                         ││
│  │  AI 处理结果将显示在这里...              ││
│  │                                         ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

### 界面元素说明

| 元素 | 说明 |
|------|------|
| **Pattern 选择器** | 下拉菜单，选择 5 个 AI Pattern 之一 |
| **执行按钮** | 点击执行当前 Pattern（快捷键：⌘↩） |
| **输入文本框** | 输入或粘贴要处理的文本（支持拖拽文件） |
| **输出结果框** | 显示 AI 处理结果（可复制、导出） |
| **状态栏**（底部） | 显示连接状态、性能指标 |

---

## 5 个 AI Pattern 使用指南

### 1. Summarize（文本总结）

**功能**: 将长文本总结为简洁摘要

**适用场景**:
- 📄 长文档摘要（报告、论文、文章）
- 📧 邮件快速浏览
- 📰 新闻快读
- 📝 会议纪要生成

**使用步骤**:

1. 选择 Pattern：`Summarize`
2. 输入文本（支持中英文，50-10,000 字）
3. （可选）设置参数：
   - **Length**（长度）：`short`（短）/ `medium`（中）/ `long`（长）
   - **Style**（风格）：`bullet`（项目符号）/ `paragraph`（段落）
   - **Language**（语言）：`zh-CN`（中文）/ `en-US`（英文）
4. 点击"执行"

**示例**:

**输入**:
```
MacCortex is a next-generation macOS personal AI infrastructure
built with Swift and Python. It integrates multiple LLM models,
including MLX (Apple Silicon optimized) and Ollama (local deployment),
and provides 5 AI patterns for intelligent text processing: Summarize,
Extract, Translate, Format, and Search. The application features
enterprise-grade security with OWASP LLM01 protection, audit logging
with PII redaction, and rate limiting (60 requests/minute). Phase 2
is nearly complete with all core patterns implemented and tested.
```

**输出**（length=short, style=bullet）:
```
- MacCortex 是下一代 macOS AI 基础设施
- 集成 MLX 和 Ollama 双 LLM
- 提供 5 个 AI 模式：总结、提取、翻译、格式转换、搜索
- 企业级安全：防护、审计、速率限制
- Phase 2 即将完成
```

**参数说明**:

| 参数 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `length` | short, medium, long | medium | 摘要长度（约原文 10%/20%/30%） |
| `style` | bullet, paragraph, headline | paragraph | 输出风格 |
| `language` | zh-CN, en-US, ja-JP 等 | zh-CN | 输出语言 |

**性能**:
- 响应时间：1-2 秒（短文本）、2-5 秒（长文本）
- 最大输入：50,000 字符

---

### 2. Extract（信息提取）

**功能**: 从文本中提取结构化信息

**适用场景**:
- 📇 联系人信息提取（姓名、邮箱、电话）
- 📅 日期时间识别
- 🏢 组织机构名称提取
- 🔗 URL 链接提取
- 🏷️ 关键词提取

**使用步骤**:

1. 选择 Pattern：`Extract`
2. 输入包含实体的文本
3. 设置参数：
   - **entity_types**（实体类型）：选择要提取的类型（多选）
     - `person`（人名）
     - `organization`（机构）
     - `location`（地点）
     - `date`（日期）
     - `email`（邮箱）
     - `phone`（电话）
     - `url`（链接）
4. 点击"执行"

**示例**:

**输入**:
```
Contact John Doe at john.doe@example.com or call +1-555-0123
for the project meeting scheduled on January 25, 2026 at 2:00 PM.
The meeting will be held at Apple Park, Cupertino, CA.
Please visit https://maccortex.example.com for more details.
```

**输出**（JSON 格式）:
```json
{
  "entities": {
    "person": ["John Doe"],
    "email": ["john.doe@example.com"],
    "phone": ["+1-555-0123"],
    "date": ["January 25, 2026", "2:00 PM"],
    "location": ["Apple Park, Cupertino, CA"],
    "url": ["https://maccortex.example.com"]
  },
  "metadata": {
    "total_entities": 7,
    "entity_types": 6,
    "confidence": "high"
  }
}
```

**参数说明**:

| 参数 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `entity_types` | person, organization, location, date, email, phone, url | 全部 | 要提取的实体类型（多选） |
| `extract_keywords` | true, false | false | 是否提取关键词 |
| `language` | zh-CN, en-US | zh-CN | 文本语言 |

**准确率**:
- 邮箱/电话/URL：95%+（正则匹配）
- 人名/地点/日期：80-90%（LLM 提取）

---

### 3. Translate（多语言翻译）

**功能**: 在 10+ 种语言之间互译

**支持语言**:
- 🇨🇳 中文（简体/繁体）
- 🇺🇸 英文
- 🇯🇵 日文
- 🇰🇷 韩文
- 🇪🇸 西班牙文
- 🇫🇷 法文
- 🇩🇪 德文
- 🇷🇺 俄文
- 🇸🇦 阿拉伯文

**使用步骤**:

1. 选择 Pattern：`Translate`
2. 输入要翻译的文本
3. 设置参数：
   - **source_language**（源语言）：`auto`（自动检测）或指定语言
   - **target_language**（目标语言）：选择目标语言
   - **style**（风格）：`formal`（正式）/ `casual`（随意）/ `technical`（技术）
4. 点击"执行"

**示例**:

**输入**（英文→中文）:
```
Hello, how are you doing today? I hope this message finds you well.
```

**输出**:
```
你好，今天过得怎么样？希望你一切都好。
```

**参数说明**:

| 参数 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `source_language` | auto, zh, en, ja, ko 等 | auto | 源语言（auto 自动检测） |
| `target_language` | zh, en, ja, ko 等 | zh-CN | 目标语言（必填） |
| `style` | formal, casual, technical | formal | 翻译风格 |

**⚠️ 当前限制**（Phase 2）:

由于使用 Llama-3.2-1B-Instruct（1B 参数）模型，翻译质量可能不理想：
- 部分词汇未翻译
- 可能有重复输出
- 技术术语准确性有限

**Phase 3 改进计划**:
- 升级到 Ollama aya-23（23B 参数，专业翻译模型）
- 预期质量提升 3-5 倍
- 详见 `Backend/TRANSLATE_LIMITATION.md`

---

### 4. Format（格式转换）

**功能**: 在多种数据格式之间转换

**支持格式**:
- 📄 JSON
- 📋 YAML
- 📊 CSV
- 📝 Markdown
- 🗂️ XML
- ⚙️ TOML

**使用步骤**:

1. 选择 Pattern：`Format`
2. 输入原始格式数据
3. 设置参数：
   - **from_format**（源格式）：选择输入格式
   - **to_format**（目标格式）：选择输出格式
   - **prettify**（美化）：`true`（格式化）/ `false`（压缩）
4. 点击"执行"

**示例**:

**输入**（JSON → YAML）:
```json
{
  "name": "MacCortex",
  "version": "0.5.0",
  "platform": "macOS",
  "features": ["summarize", "extract", "translate", "format", "search"]
}
```

**输出**:
```yaml
name: MacCortex
version: 0.5.0
platform: macOS
features:
  - summarize
  - extract
  - translate
  - format
  - search
```

**参数说明**:

| 参数 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `from_format` | json, yaml, csv, markdown, xml, toml | json | 源格式 |
| `to_format` | json, yaml, csv, markdown, xml, toml | yaml | 目标格式 |
| `prettify` | true, false | true | 是否格式化美化 |

**常见转换**:
- JSON ↔ YAML（配置文件）
- CSV ↔ JSON（数据处理）
- Markdown ↔ HTML（文档转换）
- JSON ↔ TOML（配置管理）

---

### 5. Search（Web 搜索）

**功能**: Web 搜索 + AI 总结

**搜索引擎**: DuckDuckGo（隐私友好）

**使用步骤**:

1. 选择 Pattern：`Search`
2. 输入搜索查询
3. 设置参数：
   - **engine**（引擎）：`duckduckgo`
   - **num_results**（结果数）：1-20
   - **language**（语言）：搜索区域
   - **summarize**（总结）：`true`（AI 总结）/ `false`（仅结果）
4. 点击"执行"

**示例**:

**输入**:
```
Python async programming best practices 2026
```

**输出**（JSON 格式 + AI 总结）:
```json
{
  "results": [
    {
      "title": "Python Asyncio Best Practices - Real Python",
      "url": "https://realpython.com/async-io-python/",
      "snippet": "Learn about async/await patterns, event loops...",
      "source": "duckduckgo",
      "rank": 1
    },
    // ... 更多结果 ...
  ],
  "summary": "Python asyncio 最佳实践包括：使用 async/await 语法、正确处理事件循环、避免阻塞操作、合理使用 asyncio.gather() 并发执行任务，以及利用 aiohttp 进行异步网络请求。"
}
```

**参数说明**:

| 参数 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `engine` | duckduckgo | duckduckgo | 搜索引擎 |
| `num_results` | 1-20 | 5 | 返回结果数量 |
| `language` | zh, en, ja, ko 等 | zh-CN | 搜索区域/语言 |
| `summarize` | true, false | true | 是否 AI 总结 |

**⚠️ 速率限制**:

DuckDuckGo 有反爬虫速率限制：
- 连续请求间隔需 > 1 秒
- 短时间内过多请求会触发限制
- 触发后自动回退到 Mock 搜索

**缓存机制**:
- 5 分钟缓存（相同查询）
- 预期缓存命中率：70-80%
- 详见 `Backend/DUCKDUCKGO_INTEGRATION.md`

---

## 常见操作流程

### 快速总结长文章

1. 复制文章内容（⌘C）
2. 打开 MacCortex
3. Pattern 选择 `Summarize`
4. 粘贴到输入框（⌘V）
5. 点击"执行"（或按 ⌘↩）
6. 复制总结结果（⌘C）

**用时**: < 10 秒

---

### 批量提取联系人

1. 准备包含联系人的文本
2. Pattern 选择 `Extract`
3. entity_types 选择：`person`, `email`, `phone`
4. 执行后复制 JSON 输出
5. 导入到通讯录或 CRM 系统

---

### 文档格式转换

**场景**: 将 JSON 配置转为 YAML

1. 复制 JSON 配置文件内容
2. Pattern 选择 `Format`
3. from_format: `json`
4. to_format: `yaml`
5. prettify: `true`
6. 执行并保存结果

---

### 技术问题快速搜索

1. Pattern 选择 `Search`
2. 输入技术问题（英文更佳）
3. num_results 设置为 10
4. summarize 启用
5. 查看 AI 总结的答案
6. 点击链接深入阅读

---

## 快捷键与技巧

### 键盘快捷键（Phase 3 计划）

| 快捷键 | 功能 |
|--------|------|
| ⌘↩ | 执行当前 Pattern |
| ⌘N | 新建/清空输入 |
| ⌘C | 复制输出结果 |
| ⌘V | 粘贴到输入框 |
| ⌘Q | 退出应用 |
| ⌘, | 打开设置（Phase 3） |

### 效率技巧

#### 技巧 1: 链式处理

将一个 Pattern 的输出作为另一个 Pattern 的输入：

```
1. Summarize（总结文章）
   ↓ 复制输出
2. Translate（翻译总结）
   ↓ 复制输出
3. Format（转为 Markdown）
```

#### 技巧 2: 快速切换 Pattern

使用 Pattern 选择器的首字母快速定位：
- 按 `s` → Summarize
- 按 `e` → Extract
- 按 `t` → Translate
- 按 `f` → Format
- 按 `s`（再次）→ Search

#### 技巧 3: 文本预处理

**提升准确率**:
- 移除多余换行和空格
- 确保文本编码正确（UTF-8）
- 分段处理超长文本（> 10,000 字）

---

## 性能与资源

### 性能指标（实测）

| 指标 | 数值 | 说明 |
|------|------|------|
| **启动时间** | 2.0s | 首次启动需加载 MLX 模型 |
| **Pattern 响应** | 1.6s (平均) | 短文本处理时间 |
| **内存占用** | 104 MB | MacCortex.app 空闲状态 |
| **CPU 占用** | 0% | 空闲状态，执行时 < 50% |
| **Backend 内存** | 27 MB | Python 后端服务 |

### 资源优化建议

1. **减少内存占用**:
   - 定期重启应用（每周一次）
   - 避免同时运行大量 Pattern

2. **提升响应速度**:
   - 使用 SSD 存储
   - 确保系统有足够可用内存（> 4 GB）

3. **降低 CPU 负载**:
   - 避免处理超长文本（> 20,000 字）
   - 使用 Summarize 先缩短文本

---

## 故障排查

### 问题 1: 应用无法启动

**症状**: 双击应用无响应或闪退

**解决方案**:
1. 检查 macOS 版本（需 26.2+）
2. 检查是否 Apple Silicon（不支持 Intel）
3. 查看系统日志：
   ```bash
   log show --predicate 'process == "MacCortex"' --last 5m
   ```
4. 重新安装应用

---

### 问题 2: Backend 连接失败

**症状**: 界面显示"无法连接到后端服务"

**解决方案**:
1. 检查 Backend 进程：
   ```bash
   lsof -i :8000
   ```
2. 手动启动 Backend（调试模式）：
   ```bash
   cd ~/Applications/MacCortex.app/Contents/Resources/Backend
   .venv/bin/python src/main.py
   ```
3. 检查防火墙设置（允许 localhost:8000）

---

### 问题 3: Pattern 执行超时

**症状**: 执行超过 10 秒无响应

**解决方案**:
1. 检查输入文本长度（建议 < 10,000 字）
2. 重启应用（重新加载模型）
3. 检查系统资源（内存/CPU）
4. 尝试使用更短的测试文本

---

### 问题 4: 翻译质量差

**症状**: 翻译结果不准确或重复

**说明**: 这是已知限制（Llama-3.2-1B 模型）

**临时解决方案**:
1. 使用更简单的句子
2. 分段翻译长文本
3. 等待 Phase 3 升级（aya-23 模型）

详见：`Backend/TRANSLATE_LIMITATION.md`

---

### 问题 5: 搜索返回 Mock 数据

**症状**: Search Pattern 返回"MacCortex 搜索结果 1"等测试数据

**原因**: DuckDuckGo 速率限制触发

**解决方案**:
1. 等待 2-5 分钟再尝试
2. 避免连续快速搜索
3. 使用缓存（相同查询 5 分钟内有效）

详见：`Backend/DUCKDUCKGO_INTEGRATION.md`

---

## 获取帮助

### 文档资源

- **用户指南**（本文档）：基础使用说明
- **FAQ**：`FAQ.md` - 常见问题解答
- **API 文档**：`API_REFERENCE.md` - Backend API 技术文档
- **技术说明**：
  - `Backend/TRANSLATE_LIMITATION.md` - 翻译功能限制
  - `Backend/DUCKDUCKGO_INTEGRATION.md` - 搜索集成说明
  - `GUI_TEST_PLAN.md` - 测试计划（开发者）

### 社区支持

- **GitHub Issues**: [报告 Bug](https://github.com/maccortex/maccortex/issues)（示例链接）
- **GitHub Discussions**: [功能建议与讨论](https://github.com/maccortex/maccortex/discussions)
- **Email 支持**: support@maccortex.example.com（示例邮箱）

### 提交 Bug 报告

请提供以下信息：
1. macOS 版本（`sw_vers`）
2. MacCortex 版本（关于 → 版本号）
3. 问题描述（步骤、预期、实际）
4. 日志文件（如有）
5. 截图（如有）

---

## 附录

### A. 支持的语言代码

| 语言 | 简短代码 | 完整代码 |
|------|----------|----------|
| 简体中文 | zh | zh-CN |
| 繁体中文 | - | zh-TW |
| 英文 | en | en-US |
| 日文 | ja | ja-JP |
| 韩文 | ko | ko-KR |
| 西班牙文 | es | es-ES |
| 法文 | fr | fr-FR |
| 德文 | de | de-DE |
| 俄文 | ru | ru-RU |
| 阿拉伯文 | ar | ar-AR |

### B. 数据隐私说明

✅ **本地处理**: 除 Search Pattern 外，所有数据在本地处理，不上传云端

✅ **审计日志**: 所有操作记录在本地，PII 自动脱敏

✅ **无追踪**: 不收集用户行为数据

⚠️ **Search Pattern**: 使用 DuckDuckGo 搜索，遵循其隐私政策

### C. 许可证与版权

**MacCortex 0.5.0**
Copyright © 2026 Yu Geng. All rights reserved.

**许可证**: Proprietary（专有许可）

**第三方组件**:
- MLX: MIT License
- FastAPI: MIT License
- DuckDuckGo Search: MIT License
- 完整列表见：`LICENSE.md`

---

**文档版本**: 1.0
**最后更新**: 2026-01-21
**字数**: ~6,500 字

如有问题或建议，欢迎反馈！🚀
