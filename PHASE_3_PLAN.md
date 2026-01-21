# Phase 3: Desktop GUI + 高级功能集成 - 详细实施计划

> **创建时间**: 2026-01-21
> **状态**: 待开始
> **预计工期**: 4 周（Week 1-4，20 个工作日）
> **前置依赖**: Phase 2 完成 ✅（phase-2-complete Tag）

---

## 📊 当前状态

### ✅ Phase 2 完成（Week 1-4）

**核心成就**:
- ✅ 5 个 AI Pattern（Summarize, Extract, Translate, Format, Search）
- ✅ Python FastAPI Backend（5,369 行）
- ✅ SwiftUI CLI 接口（8,195 行）
- ✅ 企业级安全防护（Prompt Injection, 审计日志）
- ✅ 性能优化（1.638s 响应，103.89 MB 内存）
- ✅ 完整文档（32,500+ 字）

**验收**: ✅ 6/6 P0 标准通过

### ⚠️ Phase 2 遗留问题（需在 Phase 3 解决）

| # | 问题 | 严重程度 | 影响范围 | Phase 3 解决方案 |
|---|------|----------|----------|------------------|
| 1 | **Translate Pattern 质量限制** | 中 | 翻译功能体验差 | Week 1: 升级 aya-23 模型 |
| 2 | **XCTest 无法运行** | 中 | 无自动化测试 | Week 1: Xcode 项目迁移 |
| 3 | **CLI 交互体验差** | 中 | 用户体验不佳 | Week 2-3: SwiftUI Desktop GUI |
| 4 | **MCP 工具未实际测试** | 低 | 功能未验证 | Week 3: MCP 服务器部署 |
| 5 | **性能未达理想目标** | 低 | 响应时间可优化 | Week 4: 深度优化（< 1s） |
| 6 | **/version 端点错误** | 低 | MLX 版本属性缺失 | Week 1: Bug 修复 |

---

## 🎯 Phase 3 核心目标

### 主要目标（P0）

1. **Xcode 项目迁移**
   - 从 SPM 迁移到完整 Xcode 项目
   - 启用 XCTest UI 自动化（15 个测试）
   - Shortcuts 实际测试与集成

2. **SwiftUI Desktop GUI**
   - 全功能桌面应用（替换 CLI）
   - 多窗口支持
   - 实时状态反馈

3. **高级 LLM 集成**
   - Translate Pattern 升级到 aya-23（23B）
   - 多模型切换支持（Llama/Qwen/Gemma）

4. **MCP 工具生态**
   - 安装并测试 MCP 服务器
   - 动态工具调用验证
   - MCP 工具白名单管理

5. **性能深度优化**
   - Pattern 响应时间 < 1s（p50）
   - 启动时间 < 1s
   - 内存占用 < 100 MB

### 次要目标（P1）

6. **智能场景识别**（Week 4）
   - 自动检测用户意图
   - Pattern 推荐系统

7. **Shell 执行器基础**（Week 4）
   - 安全 Shell 命令执行
   - Dry-run 模式

### 非目标（Phase 4 延后）

- ❌ Swarm 编排（复杂任务多步骤）
- ❌ Coder↔Reviewer 回路
- ❌ Notes 深度集成
- ❌ OCR 功能
- ❌ 浮动工具栏（Apple Intelligence 风格）

---

## 📅 4 周详细计划

### Week 1: Xcode 迁移 + aya-23 集成（Day 1-5）

#### Day 1-2: Xcode 项目迁移

**目标**: 将 Swift Package Manager 项目迁移到完整 Xcode 项目

**任务**:

1. **创建 Xcode 项目**（Day 1）
   - 文件 → New → Project → macOS App
   - 项目名称: MacCortex
   - Bundle Identifier: com.maccortex.app
   - 团队: 开发者账号（签名用）
   - 接口: SwiftUI, 生命周期: SwiftUI App

2. **迁移现有代码**（Day 1）
   - 复制 `Sources/MacCortexApp/*.swift` 到新项目
   - 配置 Info.plist（权限、URL Scheme）
   - 配置 Entitlements（Full Disk Access, Accessibility）

3. **集成 XCTest UI 测试**（Day 2）
   - 创建 UI Testing Target（MacCortexUITests）
   - 复制 `Tests/UITests/MacCortexUITests.swift`
   - 添加 Accessibility Identifiers 到 SwiftUI 视图
   - 运行测试验证（15 个测试用例）

4. **集成 Shortcuts**（Day 2）
   - 验证 URL Scheme（`maccortex://execute?pattern=...`）
   - 测试 5 个快捷指令模板
   - 文档化 Shortcuts 使用方法

**交付物**:
- `MacCortex.xcodeproj/`（新增）
- `MacCortexUITests.swift`（可运行的 XCTest）
- `XCODE_MIGRATION.md`（迁移文档）

**验收标准**:
- ✅ Xcode 项目可编译通过
- ✅ 15 个 XCTest UI 测试全部通过
- ✅ Shortcuts 可调用 MacCortex

---

#### Day 3-4: aya-23 翻译模型集成

**目标**: 升级 Translate Pattern，解决质量问题

**背景**:
- 当前模型: Llama-3.2-1B-Instruct（1B 参数）
- 问题: 翻译质量差，长文本不完整
- 解决方案: Ollama aya-23（23B 参数，专业翻译模型）

**任务**:

1. **安装 aya-23 模型**（Day 3）
   ```bash
   # 检查 Ollama 状态
   ollama list

   # 下载 aya-23 模型（~13 GB）
   ollama pull aya-23:latest

   # 验证模型
   ollama run aya-23:latest "Translate to Chinese: Hello, how are you?"
   ```

2. **修改 Translate Pattern**（Day 3）
   - 文件: `Backend/src/patterns/translate.py`
   - 添加 Ollama 后端支持
   - 保留 MLX 作为回退（aya-23 不可用时）
   - 优化 Prompt 模板（利用 aya-23 多语言能力）

**代码修改**:
```python
# Backend/src/patterns/translate.py

async def execute(self, text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    target_language = parameters.get("target_language", "en-US")

    # 优先使用 Ollama aya-23（质量更高）
    if self._is_ollama_available() and self._has_model("aya-23"):
        return await self._translate_with_aya23(text, target_language, parameters)
    else:
        # 回退到 MLX（兼容性）
        logger.warning("aya-23 不可用，使用 MLX 模型（质量有限）")
        return await self._translate_with_mlx(text, target_language, parameters)

async def _translate_with_aya23(self, text: str, target_language: str, parameters: Dict[str, Any]):
    """使用 Ollama aya-23 进行翻译"""
    prompt = f"""Translate the following text to {target_language}.
Only output the translation, no explanations.

Text:
{text}

Translation:"""

    response = await self._generate_with_ollama(
        model="aya-23:latest",
        prompt=prompt,
        temperature=0.3,
        max_tokens=len(text) * 3
    )

    return {
        "output": response.strip(),
        "metadata": {
            "model": "aya-23:latest",
            "input_length": len(text),
            "output_length": len(response),
            # ...
        }
    }
```

3. **性能测试**（Day 4）
   - 对比测试（MLX vs aya-23）
   - 测试用例: 10+ 语言对，5 种文本长度
   - 记录性能指标（响应时间、质量评分）

4. **文档更新**（Day 4）
   - 更新 `Backend/TRANSLATE_LIMITATION.md`
   - 更新 `USER_GUIDE.md`（新增 aya-23 说明）
   - 更新 `FAQ.md`（Q8: 翻译质量问题）

**交付物**:
- `Backend/src/patterns/translate.py`（aya-23 集成）
- `Backend/tests/test_translate_aya23.py`（新增测试）
- `TRANSLATE_AYA23_INTEGRATION.md`（技术文档）

**验收标准**:
- ✅ aya-23 模型成功安装
- ✅ Translate Pattern 可使用 aya-23
- ✅ 翻译质量提升 3-5 倍（人工评估）
- ✅ MLX 回退机制正常工作

---

#### Day 5: Bug 修复 + Week 1 总结

**任务**:

1. **修复 /version 端点错误**
   - 问题: MLX 版本属性缺失
   - 文件: `Backend/src/main.py`
   - 修复: 添加 MLX 版本检测

2. **代码质量检查**
   - 运行所有测试（46 + 15 XCTest）
   - 修复发现的问题
   - 更新文档

3. **Week 1 总结**
   - 创建 `PHASE_3_WEEK_1_SUMMARY.md`
   - 更新 CHANGELOG.md
   - Git commit + push

**交付物**:
- 所有 Bug 修复
- `PHASE_3_WEEK_1_SUMMARY.md`
- CHANGELOG.md 更新

**验收标准**:
- ✅ 所有测试通过（61 个测试）
- ✅ /version 端点正常返回
- ✅ 文档更新完整

---

### Week 2-3: SwiftUI Desktop GUI（Day 6-15）

#### Week 2 Day 1-3: GUI 基础架构（Day 6-8）

**目标**: 替换 CLI 界面，实现全功能 Desktop GUI

**设计原则**:
- macOS 原生风格（Big Sur/Monterey 设计语言）
- 轻量快速（启动 < 1s）
- 键盘优先（支持全键盘操作）
- 响应式布局（支持窗口缩放）

**核心界面设计**:

```
┌──────────────────────────────────────────────────┐
│  MacCortex                                   ⊙ ⊗ │ (标题栏)
├──────────────────────────────────────────────────┤
│  Pattern:  [Summarize ▼]                         │ (Pattern 选择器)
├──────────────────────────────────────────────────┤
│  Input:                                          │
│  ┌────────────────────────────────────────────┐  │
│  │ 在此输入或粘贴文本...                       │  │ (输入区)
│  │                                            │  │
│  │ (支持拖放文件、快捷键粘贴)                  │  │
│  │                                            │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Parameters:                                     │
│  ┌────────────────────────────────────────────┐  │
│  │ Length: [Medium ▼]  Style: [Paragraph ▼]   │  │ (参数配置)
│  │ Language: [zh-CN ▼]                        │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  [Execute] (⌘ Return)                            │ (执行按钮)
├──────────────────────────────────────────────────┤
│  Output:                                         │
│  ┌────────────────────────────────────────────┐  │
│  │ (结果显示区)                                │  │ (输出区)
│  │                                            │  │
│  │ • MacCortex 是下一代 macOS AI 工具         │  │
│  │ • 集成 MLX 和 Ollama 双 LLM               │  │
│  │ • 提供 5 个 AI 模式                        │  │
│  │                                            │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ⏱ 1.6s | 📦 MLX | ✅ Success                    │ (状态栏)
└──────────────────────────────────────────────────┘
```

**任务**:

1. **创建主窗口**（Day 6）
   - `MainWindow.swift`: SwiftUI 主窗口
   - Pattern Picker: 下拉菜单（5 个 Pattern）
   - Input TextEditor: 多行文本输入
   - Parameters 动态配置（根据 Pattern 变化）
   - Execute 按钮 + 快捷键（⌘ Return）

2. **创建输出区域**（Day 7）
   - Output TextView: 只读文本显示
   - 支持 Markdown 渲染（可选）
   - 复制按钮（⌘ C）
   - 导出按钮（保存为文件）

3. **状态管理**（Day 7）
   - ObservableObject: PatternViewModel
   - 状态: idle, executing, success, error
   - 进度指示器（执行时显示）
   - 错误处理与显示

4. **Backend 集成**（Day 8）
   - URLSession 调用 Backend API
   - 异步执行（避免 UI 阻塞）
   - 错误处理（网络错误、Backend 错误）
   - 超时机制（30 秒）

**代码示例**:

```swift
// Sources/MacCortexApp/Views/MainWindow.swift

import SwiftUI

struct MainWindow: View {
    @StateObject private var viewModel = PatternViewModel()

    var body: some View {
        VStack(spacing: 0) {
            // Pattern 选择器
            PatternPicker(selection: $viewModel.selectedPattern)
                .padding()

            Divider()

            // 输入区
            VStack(alignment: .leading, spacing: 8) {
                Text("Input:")
                    .font(.headline)

                TextEditor(text: $viewModel.inputText)
                    .font(.body)
                    .frame(minHeight: 150)
                    .border(Color.gray.opacity(0.3))
            }
            .padding()

            // 参数配置（动态）
            if let parameters = viewModel.selectedPattern.parameters {
                ParametersView(parameters: parameters, selection: $viewModel.parameters)
                    .padding(.horizontal)
            }

            // 执行按钮
            Button(action: { viewModel.execute() }) {
                HStack {
                    if viewModel.isExecuting {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                    Text(viewModel.isExecuting ? "Executing..." : "Execute")
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .keyboardShortcut(.return, modifiers: .command)
            .disabled(viewModel.inputText.isEmpty || viewModel.isExecuting)
            .padding()

            Divider()

            // 输出区
            OutputView(output: viewModel.output, metadata: viewModel.metadata, error: viewModel.error)
                .frame(minHeight: 200)

            // 状态栏
            StatusBar(metadata: viewModel.metadata, error: viewModel.error)
        }
        .frame(width: 800, height: 700)
    }
}

// ViewModel
@MainActor
class PatternViewModel: ObservableObject {
    @Published var selectedPattern: Pattern = .summarize
    @Published var inputText: String = ""
    @Published var parameters: [String: Any] = [:]
    @Published var output: String = ""
    @Published var metadata: PatternMetadata?
    @Published var error: String?
    @Published var isExecuting: Bool = false

    func execute() {
        Task {
            isExecuting = true
            error = nil

            do {
                let result = try await BackendService.shared.executePattern(
                    patternId: selectedPattern.id,
                    text: inputText,
                    parameters: parameters
                )

                output = result.output
                metadata = result.metadata
            } catch {
                self.error = error.localizedDescription
            }

            isExecuting = false
        }
    }
}
```

**交付物**:
- `Sources/MacCortexApp/Views/MainWindow.swift`
- `Sources/MacCortexApp/Views/PatternPicker.swift`
- `Sources/MacCortexApp/Views/OutputView.swift`
- `Sources/MacCortexApp/Views/StatusBar.swift`
- `Sources/MacCortexApp/ViewModels/PatternViewModel.swift`
- `Sources/MacCortexApp/Services/BackendService.swift`

**验收标准**:
- ✅ GUI 可编译并运行
- ✅ 可选择 5 个 Pattern
- ✅ 输入文本并执行
- ✅ 输出正确显示

---

#### Week 2 Day 4-5: GUI 高级功能（Day 9-10）

**任务**:

1. **多窗口支持**（Day 9）
   - 每个任务可打开新窗口
   - 窗口独立状态管理
   - ⌘ N 新建窗口

2. **历史记录**（Day 9）
   - 保存最近 20 次执行
   - 侧边栏显示历史
   - 点击历史恢复输入/输出

3. **快捷操作**（Day 10）
   - 拖放文件（自动读取内容）
   - ⌘ V 粘贴（自动填充输入框）
   - ⌘ C 复制输出
   - ⌘ S 保存输出为文件

4. **偏好设置**（Day 10）
   - Settings Window（SwiftUI Settings）
   - 默认 Pattern
   - 默认参数
   - Backend URL 配置
   - 主题选择（Light/Dark/Auto）

**交付物**:
- `Sources/MacCortexApp/Views/HistorySidebar.swift`
- `Sources/MacCortexApp/Views/SettingsView.swift`
- `Sources/MacCortexApp/Models/ExecutionHistory.swift`

**验收标准**:
- ✅ 多窗口可正常使用
- ✅ 历史记录可查看与恢复
- ✅ 快捷键全部工作
- ✅ 偏好设置可保存

---

#### Week 3 Day 1-3: GUI 打磨与测试（Day 11-13）

**任务**:

1. **UI/UX 优化**（Day 11）
   - 动画效果（窗口切换、加载动画）
   - 错误提示（Toast/Alert）
   - 空状态设计（无历史记录时）
   - 键盘导航优化

2. **Accessibility 支持**（Day 12）
   - VoiceOver 支持
   - 键盘完全访问
   - 颜色对比度优化
   - 字体大小调整

3. **GUI 测试**（Day 13）
   - 更新 XCTest UI 测试（新增 GUI 测试）
   - 手动测试（25 个测试用例）
   - 性能测试（GUI 启动时间、响应时间）
   - Bug 修复

**交付物**:
- 更新的 XCTest UI 测试
- `GUI_TEST_REPORT.md`

**验收标准**:
- ✅ GUI 所有测试通过
- ✅ VoiceOver 可正常使用
- ✅ 启动时间 < 2s
- ✅ 无明显 Bug

---

### Week 3 Day 4-5: MCP 工具集成与测试（Day 14-15）

**目标**: 实际部署 MCP 服务器，验证 Phase 2 的 MCP 工具加载器

**背景**:
- Phase 2 已实现 MCP 工具加载器（`Backend/src/mcp/loader.py`，680 行）
- 但未实际安装 MCP 服务器进行测试

**任务**:

1. **安装 MCP 服务器**（Day 14）
   ```bash
   # 安装推荐的 MCP 服务器
   npm install -g @modelcontextprotocol/server-filesystem
   npm install -g @modelcontextprotocol/server-git
   npm install -g @modelcontextprotocol/server-github

   # 配置 MCP 服务器
   mkdir -p ~/.mcp/servers
   cat > ~/.mcp/config.json <<EOF
   {
     "mcpServers": {
       "filesystem": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/username/workspace"],
         "env": {}
       },
       "git": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-git"],
         "env": {}
       }
     }
   }
   EOF
   ```

2. **测试 MCP 工具加载**（Day 14）
   - 验证 `MCPLoader.load_tools()` 可发现 MCP 服务器
   - 测试工具白名单机制
   - 测试工具调用（read_file, list_files, git_status）

3. **集成到 Pattern**（Day 15）
   - 修改 Search Pattern: 集成 MCP 工具（如 GitHub 搜索）
   - 测试端到端工作流
   - 文档化 MCP 工具使用方法

4. **安全审计**（Day 15）
   - 验证 MCP 工具隔离
   - 测试恶意工具拦截
   - 审计日志验证

**交付物**:
- `~/.mcp/config.json`（MCP 配置）
- `Backend/tests/test_mcp_integration.py`（集成测试）
- `MCP_INTEGRATION_GUIDE.md`（用户文档）

**验收标准**:
- ✅ 至少 2 个 MCP 服务器成功安装
- ✅ MCP 工具可被加载
- ✅ MCP 工具可正常调用
- ✅ 安全机制正常工作

---

### Week 4: 性能优化 + 智能识别（Day 16-20）

#### Day 16-18: 深度性能优化

**目标**: Pattern 响应时间 < 1s（p50）

**当前性能**（Phase 2 基准）:
- Pattern 响应: 1.638s（p50）
- 内存占用: 103.89 MB
- CPU 空闲: 0%

**优化目标**:
- Pattern 响应: **< 1s**（p50）（-39%）
- 启动时间: **< 1s**（当前 2s）
- 内存占用: **< 100 MB**（-3.8%）

**优化方案**:

1. **MLX 模型预加载优化**（Day 16）
   - 问题: 首次推理冷启动慢（2-3s）
   - 方案: Backend 启动时预加载模型
   - 预期: 首次响应时间 -50%

2. **响应缓存机制**（Day 17）
   - 对相同输入缓存结果（30 分钟 TTL）
   - 基于 input hash + pattern + parameters
   - 预期: 重复请求响应时间 -90%

3. **并发优化**（Day 17）
   - 使用 asyncio 事件循环优化
   - 模型批处理（多个请求合并推理）
   - 预期: 并发吞吐量 +50%

4. **Metal GPU 加速**（Day 18）
   - MLX Metal backend 优化
   - GPU 内存管理
   - 预期: 推理速度 +20-30%

5. **启动优化**（Day 18）
   - Backend 守护进程（常驻内存）
   - GUI lazy loading
   - 预期: 启动时间 < 1s

**测试方法**:
```bash
# 性能基准测试（更新脚本）
./performance_benchmark_phase3.sh

# 压力测试
ab -n 100 -c 10 http://localhost:8000/execute \
  -p payload.json -T application/json
```

**交付物**:
- 优化后的 Backend 代码
- `performance_benchmark_phase3.sh`
- `PHASE_3_PERFORMANCE_REPORT.md`

**验收标准**:
- ✅ Pattern 响应 < 1s（p50）
- ✅ 启动时间 < 1s
- ✅ 内存占用 < 100 MB
- ✅ 并发性能提升 50%+

---

#### Day 19: 智能场景识别（Alpha）

**目标**: 自动检测用户意图，推荐 Pattern

**实现方案**:

1. **意图分类器**
   - 使用轻量级分类模型（MLX Qwen2.5:0.5b）
   - 输入: 用户文本
   - 输出: Pattern 推荐 + 置信度

2. **分类规则**
   ```
   输入: "请总结这段文字..."
   → 推荐: Summarize（置信度 95%）

   输入: "翻译成英文: ..."
   → 推荐: Translate（置信度 98%）

   输入: "提取联系人信息: ..."
   → 推荐: Extract（置信度 92%）

   输入: "搜索 Apple Intelligence 最新资料"
   → 推荐: Search（置信度 90%）

   输入: "将 JSON 转换为 YAML: ..."
   → 推荐: Format（置信度 97%）
   ```

3. **GUI 集成**
   - 输入框实时分析
   - 推荐 Pattern 高亮显示
   - 用户可接受或忽略推荐

**交付物**:
- `Backend/src/classifier/intent_classifier.py`
- `Sources/MacCortexApp/Views/SmartSuggestion.swift`

**验收标准**（Alpha）:
- ✅ 分类准确率 > 85%（5 类）
- ✅ 响应时间 < 100ms
- ✅ GUI 可显示推荐

---

#### Day 20: Phase 3 总结与验收

**任务**:

1. **创建 Phase 3 总结报告**
   - `PHASE_3_SUMMARY.md`（类似 PHASE_2_SUMMARY.md）
   - Week 1-4 详细回顾
   - 性能对比（Phase 2 vs Phase 3）
   - 功能清单
   - 验收标准验证

2. **更新文档**
   - CHANGELOG.md（Phase 3 完整记录）
   - USER_GUIDE.md（GUI 使用指南）
   - API_REFERENCE.md（新增 API）
   - README.md（项目首页更新）

3. **Git Tag**
   - Tag: `phase-3-complete`
   - 推送到 GitHub

4. **Demo 准备**
   - 录制 30 秒 GUI 演示视频
   - 更新 15 秒演示（Phase 2 视频）

**交付物**:
- `PHASE_3_SUMMARY.md`
- 所有文档更新
- Git Tag: `phase-3-complete`
- Demo 视频

---

## ✅ Phase 3 验收标准（P0）

| # | 验收项 | 测试方法 | 期望结果 | 优先级 |
|---|--------|----------|----------|--------|
| 1 | **Xcode 项目可编译** | Xcode Build（⌘ B） | Build Succeeded | P0 |
| 2 | **XCTest UI 测试通过** | Xcode Test（⌘ U） | 15/15 通过 | P0 |
| 3 | **aya-23 翻译质量** | 人工评估（10 个样本） | 质量提升 3x+ | P0 |
| 4 | **GUI 全功能可用** | 手动测试（20 个用例） | 20/20 通过 | P0 |
| 5 | **Pattern 响应 < 1s** | 性能基准测试（p50） | < 1.0s | P0 |
| 6 | **MCP 工具可调用** | 集成测试 | ≥2 个工具正常 | P0 |
| 7 | **启动时间 < 1s** | 计时测试 | < 1.0s | P1 |
| 8 | **智能推荐准确率** | 分类测试（100 样本） | > 85% | P1 |

**通过条件**: P0 必须 6/6 通过，P1 至少 1/2 通过

---

## 📊 Phase 3 vs Phase 2 对比目标

| 指标 | Phase 2 | Phase 3 目标 | 提升 |
|------|---------|--------------|------|
| **Pattern 响应（p50）** | 1.638s | **< 1s** | +39% |
| **启动时间** | 2.0s | **< 1s** | +50% |
| **内存占用** | 103.89 MB | **< 100 MB** | +3.8% |
| **翻译质量** | 6/10 | **9/10** | +50% |
| **GUI 体验** | CLI（3/10） | **Desktop GUI（9/10）** | +200% |
| **自动化测试** | 46 个 | **61+ 个** | +33% |
| **MCP 工具** | 未测试 | **≥2 个可用** | - |

---

## 🔧 技术栈更新

### 新增技术

| 技术 | 版本 | 用途 | Week |
|------|------|------|------|
| **Ollama aya-23** | latest | 高质量翻译 | Week 1 |
| **Xcode** | 15+ | GUI 开发 + 测试 | Week 1 |
| **MCP CLI** | latest | MCP 服务器管理 | Week 3 |
| **Metal** | - | GPU 加速 | Week 4 |

### 架构演进

```
Phase 2:
SwiftUI CLI → HTTP → FastAPI Backend → MLX/Ollama

Phase 3:
SwiftUI Desktop GUI → HTTP → FastAPI Backend（优化） → MLX/Ollama（aya-23）
                                ↓
                          MCP 工具生态
```

---

## 📂 交付文件清单（预期）

### 代码

```
MacCortex/
├── MacCortex.xcodeproj/              ← 新增（Xcode 项目）
│   ├── project.pbxproj
│   └── xcshareddata/
│
├── Sources/MacCortexApp/
│   ├── Views/                         ← 新增（GUI）
│   │   ├── MainWindow.swift
│   │   ├── PatternPicker.swift
│   │   ├── OutputView.swift
│   │   ├── StatusBar.swift
│   │   ├── HistorySidebar.swift
│   │   └── SettingsView.swift
│   ├── ViewModels/                    ← 新增
│   │   └── PatternViewModel.swift
│   ├── Services/                      ← 新增
│   │   └── BackendService.swift
│   └── Models/                        ← 新增
│       └── ExecutionHistory.swift
│
├── Backend/src/
│   ├── patterns/
│   │   └── translate.py               ← 修改（aya-23）
│   ├── classifier/                    ← 新增
│   │   └── intent_classifier.py
│   └── mcp/
│       └── loader.py                  ← 测试验证
│
└── Tests/
    └── MacCortexUITests/              ← 新增（XCTest）
        └── MacCortexUITests.swift
```

### 文档

```
MacCortex/
├── PHASE_3_PLAN.md                    ← 本文档
├── PHASE_3_SUMMARY.md                 ← Week 4 创建
├── PHASE_3_WEEK_1_SUMMARY.md          ← Week 1 创建
├── PHASE_3_PERFORMANCE_REPORT.md      ← Week 4 创建
├── XCODE_MIGRATION.md                 ← Week 1 创建
├── TRANSLATE_AYA23_INTEGRATION.md     ← Week 1 创建
├── MCP_INTEGRATION_GUIDE.md           ← Week 3 创建
├── GUI_TEST_REPORT.md                 ← Week 3 创建
└── CHANGELOG.md                       ← 持续更新
```

---

## 🚨 风险评估与缓解

| 风险 | 概率 | 影响 | 缓解策略 | 残余风险 |
|------|------|------|----------|----------|
| **aya-23 模型过大** | 30% | 中 | 提供 aya-23:8b 小版本选项 | 🟡 中 |
| **Xcode 迁移失败** | 10% | 高 | 保留 SPM 项目作为备份 | 🟢 低 |
| **GUI 性能不佳** | 20% | 中 | SwiftUI Instruments 性能分析 | 🟡 中 |
| **MCP 服务器不稳定** | 40% | 低 | 仅作为可选功能，不影响核心 | 🟢 低 |
| **< 1s 目标未达成** | 50% | 低 | 降级目标到 < 1.2s | 🟢 低 |
| **智能识别准确率低** | 60% | 低 | 标记为 Alpha，Phase 4 优化 | 🟢 低 |

**总体风险评分**: 🟢 **可控**（无高残余风险）

---

## 📝 每日工作流程（严格执行）

### 每日启动

1. **时间校验**（CLAUDE.md 要求）
   - 双源校验当前时间
   - 记录到 CHANGELOG.md

2. **读取计划**
   - 查看当日任务（本文档）
   - 确认前置依赖

3. **创建 Todo**
   - 使用 TodoWrite 工具
   - 分解为小任务

### 每日执行

4. **编码/测试**
   - 严格按计划执行
   - 每完成一项标记 Todo
   - 遇到问题立即记录

5. **文档更新**（实时）
   - 代码注释
   - API 文档
   - CHANGELOG.md

### 每日收尾

6. **测试验证**
   - 运行相关测试
   - 性能基准测试（如涉及）
   - 修复发现的问题

7. **Git 提交**
   - 清晰的 commit message
   - 引用相关任务（Day X）
   - Co-Authored-By: Claude Sonnet 4.5

8. **日报**（可选）
   - 完成任务
   - 发现问题
   - 明日计划

---

## 🎯 成功标准

**Phase 3 成功** = 所有 6 个 P0 验收标准通过 ✅

**完成后**:
- ✅ Desktop GUI 全功能可用
- ✅ 翻译质量显著提升（aya-23）
- ✅ 性能达到理想目标（< 1s）
- ✅ MCP 工具生态初步建立
- ✅ 自动化测试覆盖率提升
- ✅ 代码质量与文档完整性

**Phase 4 预览**（Q2 2026）:
- Swarm 编排（复杂任务多步骤）
- Coder↔Reviewer 回路
- Shell 执行器（安全沙箱）
- Notes 深度集成
- OCR 功能

---

## 附录

### A. Xcode 项目结构（推荐）

```
MacCortex.xcodeproj/
├── MacCortex/                         (主应用 Target)
│   ├── Views/
│   ├── ViewModels/
│   ├── Services/
│   ├── Models/
│   ├── Resources/
│   │   ├── Assets.xcassets
│   │   └── Info.plist
│   └── MacCortexApp.swift
│
├── MacCortexUITests/                  (UI Testing Target)
│   └── MacCortexUITests.swift
│
└── MacCortexTests/                    (Unit Testing Target)
    └── MacCortexTests.swift
```

### B. aya-23 模型规格

| 属性 | 值 |
|------|------|
| 模型名称 | aya-23 |
| 参数量 | 23B（或 8B 轻量版） |
| 下载大小 | ~13 GB（23B）/ ~5 GB（8B） |
| 内存需求 | 16 GB+（23B）/ 8 GB+（8B） |
| 推理速度 | 15-25 tok/s（M1 Pro）|
| 支持语言 | 100+ 语言 |
| 用途 | 专业翻译、多语言理解 |

### C. MCP 服务器推荐列表

| 服务器 | 功能 | 安装命令 | 优先级 |
|--------|------|----------|--------|
| filesystem | 文件读写 | `npm install -g @modelcontextprotocol/server-filesystem` | P0 |
| git | Git 操作 | `npm install -g @modelcontextprotocol/server-git` | P0 |
| github | GitHub API | `npm install -g @modelcontextprotocol/server-github` | P1 |
| brave-search | Web 搜索 | `npm install -g @modelcontextprotocol/server-brave-search` | P1 |

---

**计划状态**: ⏳ 待批准
**创建时间**: 2026-01-21
**基于**: Phase 2 完成状态 + README_ARCH.md + PHASE_2_SUMMARY.md
**执行人**: Claude Code (Sonnet 4.5)
**预计完成**: 2026-02-18（4 周后）
