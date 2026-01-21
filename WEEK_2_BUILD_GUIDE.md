# Phase 3 Week 2 构建指南

> **版本**: v1.0
> **创建时间**: 2026-01-22
> **状态**: 可立即执行
> **预计时间**: 10-15 分钟

---

## 执行摘要

本指南将帮助您在 Xcode 中构建并运行 MacCortex Phase 3 Week 2 Day 1-2 的**翻译 GUI 界面**。

**已完成工作**:
- ✅ SwiftUI 翻译界面（1,700+ 行代码）
- ✅ Backend 通信层（BackendClient.swift）
- ✅ 数据模型（Language + TranslationModels）
- ✅ ViewModel 业务逻辑（TranslationViewModel.swift）
- ✅ ContentView 集成（TabView 架构）

**本次构建将实现**:
- 完整的翻译界面（输入/输出/语言选择/风格选择）
- Backend API 集成（单次翻译 + 批量翻译）
- 缓存指示（命中率、节省时间）
- 历史记录（最近 20 条）
- 快捷键支持（Cmd+Enter / Cmd+K / Cmd+E / Cmd+H）

---

## 前置条件检查

### 1. Backend 服务状态

```bash
# 检查 Backend 是否运行
curl http://localhost:8000/health

# 预期输出：
# {"status":"healthy","timestamp":"...","version":"0.1.0",...}

# 如果 Backend 未运行，启动它：
cd /Users/jamesg/projects/MacCortex/Backend
.venv/bin/python src/main.py
```

### 2. Xcode 版本

```bash
# 检查 Xcode 版本
xcodebuild -version

# 预期：Xcode 15+ (支持 macOS 13+ SDK)
```

### 3. 项目文件

```bash
# 检查项目文件是否存在
ls -la /Users/jamesg/projects/MacCortex/Package.swift
ls -la /Users/jamesg/projects/MacCortex/Sources/MacCortexApp/TranslationView.swift
ls -la /Users/jamesg/projects/MacCortex/Sources/MacCortexApp/Network/BackendClient.swift
```

**所有文件应存在，否则执行**:
```bash
cd /Users/jamesg/projects/MacCortex
git pull origin main
```

---

## 构建步骤（3 步，10-15 分钟）

### 步骤 1: 打开项目

有两种方式：

#### 方式 A: 使用 Xcode GUI（推荐）

1. 打开 Xcode
2. File → Open
3. 选择 `/Users/jamesg/projects/MacCortex/Package.swift`
4. 点击 "Open"

#### 方式 B: 使用命令行

```bash
cd /Users/jamesg/projects/MacCortex
open Package.swift
```

**预期结果**: Xcode 打开项目，显示 Package Dependencies 和 Targets。

---

### 步骤 2: 解决依赖（自动）

Xcode 将自动解析 SPM 依赖（Sparkle 2.5.0）。

**等待时间**: 1-2 分钟

**验证**: 左侧导航栏显示：
```
Package Dependencies
  └─ Sparkle (2.5.0)
```

**如果出现错误**:
1. Product → Clean Build Folder (Shift+Cmd+K)
2. File → Packages → Reset Package Caches
3. File → Packages → Resolve Package Versions

---

### 步骤 3: 构建并运行

#### 选择 Scheme

1. 顶部工具栏，Scheme 下拉菜单
2. 选择 **MacCortexApp** (而非 MacCortex)
3. 选择 "My Mac" 作为目标设备

#### 构建

```bash
# 方式 A: Xcode GUI
点击顶部左侧的 ▶️ 按钮
# 或按 Cmd+R

# 方式 B: 命令行
cd /Users/jamesg/projects/MacCortex
xcodebuild -scheme MacCortexApp -configuration Debug build
```

**预计构建时间**: 2-3 分钟（首次构建）

**预期输出**（命令行）:
```
...
** BUILD SUCCEEDED **
```

#### 运行应用

应用将自动启动，或手动运行：

```bash
# 查找构建产物
find . -name "MacCortexApp" -type f

# 运行应用
open .build/arm64-apple-macosx/debug/MacCortexApp
```

---

## 验收测试（8 项，10 分钟）

### 1. 应用启动

✅ **验收标准**:
- 应用成功启动，无崩溃
- 显示 4 个标签页：翻译 / 批量 / 统计 / 权限
- 默认选中"翻译"标签页

**测试步骤**:
1. 启动应用
2. 观察标签页是否显示

---

### 2. Backend 连接检查

✅ **验收标准**:
- 右上角显示**绿色圆点**（Backend 已连接）
- 如果显示红色圆点，应用显示警告弹窗

**测试步骤**:
1. 查看右上角连接状态
2. 如果红色，检查 Backend 是否运行：
   ```bash
   curl http://localhost:8000/health
   ```

---

### 3. 语言选择器

✅ **验收标准**:
- 源语言默认"自动检测"，包含 13 种语言
- 目标语言默认"English"，包含 12 种语言（无自动检测）
- 语言选择器显示国旗 Emoji
- 点击交换按钮（↔️）交换语言

**测试步骤**:
1. 点击源语言下拉菜单，查看选项
2. 点击目标语言下拉菜单，查看选项
3. 点击交换按钮，验证语言是否交换

---

### 4. 风格选择器

✅ **验收标准**:
- 显示 3 个风格选项：正式 / 随意 / 技术
- 分段控件（Segmented Control）样式
- 点击切换风格

**测试步骤**:
1. 查看风格选择器
2. 点击"随意"，验证选中状态

---

### 5. 翻译功能

✅ **验收标准**:
- 输入文本后，点击"翻译"按钮（或按 Cmd+Enter）
- 调用 Backend API，显示翻译结果
- 输出区域显示译文
- 统计信息显示：耗时 / 缓存命中率 / 缓存大小

**测试步骤**:
1. 在输入框输入：
   ```
   MacCortex 是一个专为 macOS 设计的智能助手。
   ```
2. 目标语言选择"English"
3. 点击"翻译"按钮（或按 Cmd+Enter）
4. **预期输出**:
   ```
   MacCortex is an intelligent assistant designed for macOS.
   ```
5. 查看统计信息：
   - 耗时: ~2-3s（首次，未缓存）
   - 缓存命中率: 0%（如果是第一次翻译）
   - 缓存大小: 1/1000

---

### 6. 缓存指示

✅ **验收标准**:
- 重复相同翻译，显示"缓存命中"绿色标签
- 耗时 < 0.1s（~10ms）
- 缓存命中率: 50%+

**测试步骤**:
1. 再次翻译相同文本（不修改输入）
2. **预期**:
   - 输出立即显示（< 0.1s）
   - 输出区域右上角显示绿色"🚀 缓存命中"标签
   - 统计信息：
     - 耗时: ~0.009s
     - 缓存命中率: 50%（2 次请求，1 次命中）
     - 缓存大小: 1/1000

---

### 7. 历史记录

✅ **验收标准**:
- 点击右上角时钟图标（或按 Cmd+H）显示历史记录侧边栏
- 显示最近翻译记录（时间 / 语言对 / 文本预览）
- 点击历史记录项，加载到输入/输出区域

**测试步骤**:
1. 按 Cmd+H（或点击时钟图标）
2. 验证侧边栏显示
3. 查看历史记录项：
   - 时间戳（如：01-22 08:56）
   - 语言对（如：🇨🇳 → 🇺🇸 • 正式）
   - 文本预览（前 30 字符）
   - 缓存状态（如：🚀 缓存）
4. 点击历史记录项，验证输入/输出是否加载

---

### 8. 快捷键

✅ **验收标准**:
- Cmd+Enter: 翻译
- Cmd+K: 清空输入/输出
- Cmd+E: 交换语言
- Cmd+H: 显示/隐藏历史记录
- Cmd+C: 复制翻译结果（需先选中输出区域）
- Cmd+V: 粘贴到输入区域

**测试步骤**:
1. 输入文本，按 Cmd+Enter → 验证翻译
2. 按 Cmd+K → 验证清空
3. 输入文本，按 Cmd+E → 验证语言交换
4. 按 Cmd+H → 验证历史记录显示/隐藏
5. 点击"复制"按钮（或按 Cmd+C） → 验证剪贴板
6. 在其他应用粘贴，确认复制成功

---

## 常见问题排查

### 问题 1: Xcode 构建失败

**错误信息**: `Cannot find 'BackendClient' in scope`

**解决方案**:
1. 检查文件是否存在：
   ```bash
   ls -la Sources/MacCortexApp/Network/BackendClient.swift
   ```
2. Product → Clean Build Folder (Shift+Cmd+K)
3. 重新构建 (Cmd+R)

---

### 问题 2: Backend 连接失败

**错误信息**: 红色圆点 + 弹窗"Backend 连接失败"

**解决方案**:
1. 检查 Backend 是否运行：
   ```bash
   curl http://localhost:8000/health
   ```
2. 如果未运行，启动 Backend：
   ```bash
   cd Backend
   .venv/bin/python src/main.py
   ```
3. 检查端口是否被占用：
   ```bash
   lsof -i :8000
   ```

---

### 问题 3: 翻译无响应

**现象**: 点击"翻译"按钮后，无输出

**解决方案**:
1. 检查 Backend 日志：
   ```bash
   tail -f /tmp/backend.log
   ```
2. 检查 aya-23 模型是否可用：
   ```bash
   ollama list | grep aya
   ```
3. 如果模型未安装：
   ```bash
   ollama pull aya:8b
   ```

---

### 问题 4: Sparkle 依赖解析失败

**错误信息**: `Failed to resolve dependencies`

**解决方案**:
1. 检查网络连接
2. File → Packages → Reset Package Caches
3. File → Packages → Resolve Package Versions
4. 如果仍失败，临时移除 Sparkle 依赖：
   - 打开 Package.swift
   - 注释掉 Sparkle 依赖行
   - 重新构建

---

### 问题 5: 历史记录不显示

**现象**: 按 Cmd+H 无响应

**解决方案**:
1. 检查是否有翻译历史（至少翻译一次）
2. 检查 ViewModel 是否正确初始化：
   - 在 TranslationView.swift 中，确认 `@StateObject private var viewModel = TranslationViewModel()`
3. 重启应用

---

## 性能基准测试

运行以下测试，验证性能符合预期：

| 测试场景 | 预期结果 |
|----------|----------|
| 首次翻译（未缓存） | 2-8s（取决于 aya-23 模型） |
| 缓存命中翻译 | < 0.1s（~10ms） |
| 语言切换 | < 0.05s（即时） |
| 历史记录加载 | < 0.02s（即时） |
| 清空操作 | < 0.01s（即时） |

**运行测试**:
```bash
# 性能测试脚本（可选）
cd Backend
bash /tmp/test_cache.sh
```

**预期输出**:
```
=== 第一次请求（缓存未命中） ===
Backend duration: 3.529s

=== 第二次请求（缓存命中） ===
Backend duration: 0.009s
加速倍数: 392.1x
```

---

## Week 2 Day 1-2 验收清单

| # | 功能 | 测试方法 | 状态 |
|---|------|----------|------|
| 1 | 应用启动 | 启动应用，检查标签页 | ⏳ 待测试 |
| 2 | Backend 连接 | 查看右上角绿色圆点 | ⏳ 待测试 |
| 3 | 语言选择器 | 切换语言，查看选项 | ⏳ 待测试 |
| 4 | 风格选择器 | 切换风格 | ⏳ 待测试 |
| 5 | 翻译功能 | 输入文本翻译 | ⏳ 待测试 |
| 6 | 缓存指示 | 重复翻译，查看绿色标签 | ⏳ 待测试 |
| 7 | 历史记录 | 按 Cmd+H，查看侧边栏 | ⏳ 待测试 |
| 8 | 快捷键 | 测试 Cmd+Enter / Cmd+K 等 | ⏳ 待测试 |

**通过条件**: 所有 8 项必须 ✅

---

## 下一步计划

### Week 2 Day 3-4: 批量处理面板

**核心功能**:
- 文件拖放（.txt / .md / .csv）
- 批量翻译队列（进度条）
- 缓存统计（命中率、预估时间）
- 结果导出（CSV / JSON）

**预计开发时间**: 2 天

**启动命令**（当 Day 1-2 验收通过后）:
```bash
# 告诉 Claude Code 继续 Week 2 Day 3-4
# "请继续 Week 2 Day 3-4 的批量处理面板开发"
```

---

## 附录 A: 完整代码结构

```
MacCortex/
├── Package.swift                       # SPM 配置
├── Sources/MacCortexApp/
│   ├── MacCortexApp.swift             # 应用入口（已有）
│   ├── ContentView.swift              # 主视图（已更新）
│   ├── TranslationView.swift          # ★ 翻译界面 UI (670 行)
│   ├── Network/
│   │   ├── BackendClient.swift        # ★ Backend 通信层 (330 行)
│   │   ├── APIClient.swift            # 原有 API 客户端
│   │   ├── Endpoints.swift            # 原有 Endpoints
│   │   └── SecurityInterceptor.swift  # 原有安全拦截器
│   ├── Models/
│   │   ├── Language.swift             # ★ 语言枚举 (130 行)
│   │   └── TranslationModels.swift    # ★ 翻译数据模型 (120 行)
│   └── ViewModels/
│       └── TranslationViewModel.swift # ★ 翻译业务逻辑 (200 行)
└── Backend/
    └── src/
        ├── main.py                     # FastAPI 应用
        ├── patterns/translate.py       # aya-23 翻译模型
        └── utils/cache.py              # LRU 缓存（Week 1）
```

**★ 标记为 Week 2 Day 1-2 新增文件**

---

## 附录 B: Backend API 参考

### 健康检查

```bash
curl http://localhost:8000/health
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-22T08:56:00.123Z",
  "version": "0.1.0",
  "uptime": 3600.5,
  "patterns_loaded": 5
}
```

### 单次翻译

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "translate",
    "text": "Hello, world!",
    "parameters": {
      "target_language": "zh-CN",
      "style": "formal"
    }
  }'
```

**响应**:
```json
{
  "success": true,
  "output": "你好，世界！",
  "metadata": {
    "cached": false,
    "cache_stats": {
      "cache_size": 1,
      "hits": 0,
      "misses": 1,
      "hit_rate": 0.0
    }
  },
  "duration": 2.5
}
```

### 批量翻译

```bash
curl -X POST http://localhost:8000/execute/batch \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "translate",
    "items": [
      {"text": "Hello", "parameters": {"target_language": "zh-CN"}},
      {"text": "World", "parameters": {"target_language": "zh-CN"}}
    ]
  }'
```

**响应**:
```json
{
  "success": true,
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "aggregate_stats": {
    "cache_hits": 0,
    "cache_misses": 2,
    "cache_hit_rate": 0.0,
    "estimated_speedup": "1.2x"
  },
  "duration": 4.5
}
```

---

**构建指南版本**: v1.0
**创建时间**: 2026-01-22 09:00 UTC
**基于**: Phase 3 Week 2 Day 1-2 完成状态
**执行人**: 用户（手动构建）+ Claude Code（代码已生成）
**下一步**: Week 2 Day 3-4 - 批量处理面板
