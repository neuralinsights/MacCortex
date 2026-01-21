# Phase 3 Week 2 详细执行计划

> **版本**: v1.0
> **创建时间**: 2026-01-22
> **状态**: 待执行
> **前置条件**: Backend 优化完成（缓存 + 批量 API）

---

## 执行摘要

Phase 3 Week 2 的核心目标是**开发 SwiftUI Desktop GUI**，将 Backend 能力（翻译、缓存、批量处理）通过原生 macOS 界面呈现给用户。

**核心目标**:
1. ✅ Xcode 项目迁移（用户手动执行，30-45 分钟）
2. ✅ 翻译 GUI 界面（输入框、语言选择、实时预览）
3. ✅ 批量处理面板（文件拖放、批量队列、进度显示）
4. ✅ 缓存统计显示（命中率、节省时间、缓存管理）
5. ✅ 用户体验优化（快捷键、自动检测、历史记录）

**工期**: 5 天（2026-01-22 ~ 2026-01-26）
**验收标准**: 5 项核心功能全部实现 + GUI 交互流畅 + Backend 集成稳定

---

## Phase 3 Week 1 成果回顾

### 已完成工作

| 任务 | 状态 | 成果 |
|------|------|------|
| aya-23 模型集成 | ✅ 完成 | 9/10 质量评分，95% 术语准确率 |
| 翻译缓存系统 | ✅ 完成 | 393.6x 加速（3.5s → 9ms） |
| 批量翻译 API | ✅ 完成 | 604.4x 加速（全缓存），支持最多 100 条目 |
| Xcode 迁移指南 | ✅ 完成 | 6000+ 字详细指南（XCODE_MIGRATION_GUIDE.md） |

### Backend API 能力

**当前可用 Endpoints**:

```
GET  /health             # 健康检查
GET  /version            # 版本信息
GET  /patterns           # 列出所有 Pattern
POST /execute            # 执行单个 Pattern
POST /execute/batch      # 批量执行翻译（新增）
```

**翻译 API 示例**:

```json
// 单次翻译
POST /execute
{
  "pattern_id": "translate",
  "text": "Hello, world!",
  "parameters": {
    "target_language": "zh-CN",
    "style": "formal"
  }
}

// 批量翻译
POST /execute/batch
{
  "pattern_id": "translate",
  "items": [
    {"text": "Hello", "parameters": {"target_language": "zh-CN"}},
    {"text": "World", "parameters": {"target_language": "zh-CN"}}
  ]
}
```

**缓存统计字段**:

```json
{
  "metadata": {
    "cached": true,
    "cache_stats": {
      "cache_size": 42,
      "max_size": 1000,
      "hits": 120,
      "misses": 80,
      "hit_rate": 0.6,
      "ttl_seconds": 3600
    }
  }
}
```

---

## Week 2 Day 0: 用户前置任务（手动执行）

### 任务清单

**时间**: 30-45 分钟
**文档**: `XCODE_MIGRATION_GUIDE.md`（已创建）

| 步骤 | 任务 | 预计时间 | 验收标准 |
|------|------|----------|----------|
| 1 | 创建 Xcode Workspace | 5 分钟 | Workspace 可打开，包含 MacCortex.xcodeproj |
| 2 | 添加 Backend 通信层 | 10 分钟 | BackendClient.swift 编译通过 |
| 3 | 创建基础 SwiftUI 界面 | 10 分钟 | ContentView.swift 显示"Hello, MacCortex" |
| 4 | 验证 Backend 连接 | 10 分钟 | 健康检查成功，版本信息显示 |
| 5 | 配置快捷键与热重载 | 5 分钟 | Cmd+R 构建成功，修改代码即时刷新 |

### 执行步骤

#### 步骤 1: 创建 Xcode Workspace

```bash
cd /Users/jamesg/projects/MacCortex
mkdir -p MacCortex.xcworkspace
```

在 Xcode 中:
1. File → New → Workspace
2. 命名: `MacCortex.xcworkspace`
3. 保存到项目根目录

#### 步骤 2: 添加 Backend 通信层

参考 `XCODE_MIGRATION_GUIDE.md` 第 3 节：

```swift
// Sources/MacCortex/Network/BackendClient.swift
import Foundation

class BackendClient: ObservableObject {
    static let shared = BackendClient()
    private let baseURL = "http://localhost:8000"

    @Published var isConnected = false
    @Published var backendVersion = "未知"

    // 健康检查
    func checkHealth() async throws -> Bool { ... }

    // 翻译单个文本
    func translate(text: String, targetLanguage: String, style: String) async throws -> TranslationResponse { ... }

    // 批量翻译（新增）
    func translateBatch(items: [TranslationItem]) async throws -> BatchTranslationResponse { ... }
}
```

#### 步骤 3-5: 基础界面与验证

参考 `XCODE_MIGRATION_GUIDE.md` 第 4-6 节。

### 验收检查

```bash
# 1. Backend 运行中
curl http://localhost:8000/health

# 2. Xcode 项目可构建
cd /Users/jamesg/projects/MacCortex
xcodebuild -workspace MacCortex.xcworkspace -scheme MacCortex build

# 3. 应用可启动
open /Users/jamesg/projects/MacCortex/build/MacCortex.app
```

**未通过则不得进入 Week 2 开发阶段。**

---

## Week 2 Day 1-2: 翻译 GUI 界面

### 目标

开发**单次翻译界面**，支持：
- 输入文本框（多行，自动扩展）
- 语言选择器（源语言 + 目标语言）
- 风格选择器（formal / casual / technical）
- 实时翻译预览（带缓存指示）
- 快捷键支持（Cmd+Enter 翻译）

### 界面设计

```
┌─────────────────────────────────────────────────────────┐
│ MacCortex - 翻译助手                          [⚙️] [❓] │
├─────────────────────────────────────────────────────────┤
│ 源语言: [自动检测 ▼]   目标语言: [English ▼]          │
│ 风格: [○ Formal  ○ Casual  ○ Technical]                │
├─────────────────────────────────────────────────────────┤
│ 输入文本 (Cmd+V 粘贴):                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ MacCortex 是一个专为 macOS 设计的智能助手。        │ │
│ │                                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [🔄 翻译 (Cmd+Enter)]  [📋 复制结果]  [🗑️ 清空]        │
├─────────────────────────────────────────────────────────┤
│ 翻译结果:                                 🚀 缓存命中   │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ MacCortex is an intelligent assistant designed for │ │
│ │ macOS.                                              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 耗时: 0.009s  |  缓存命中率: 85%  |  节省时间: 12.5s   │
└─────────────────────────────────────────────────────────┘
```

### 实现代码

#### TranslationView.swift（核心界面）

```swift
import SwiftUI

struct TranslationView: View {
    @StateObject private var viewModel = TranslationViewModel()

    var body: some View {
        VStack(spacing: 16) {
            // 语言选择器
            HStack {
                Picker("源语言", selection: $viewModel.sourceLanguage) {
                    ForEach(Language.allCases) { language in
                        Text(language.displayName).tag(language)
                    }
                }
                .frame(width: 150)

                Image(systemName: "arrow.right")
                    .foregroundColor(.secondary)

                Picker("目标语言", selection: $viewModel.targetLanguage) {
                    ForEach(Language.allCases.filter { $0 != .auto }) { language in
                        Text(language.displayName).tag(language)
                    }
                }
                .frame(width: 150)
            }

            // 风格选择器
            Picker("风格", selection: $viewModel.style) {
                Text("正式").tag(TranslationStyle.formal)
                Text("随意").tag(TranslationStyle.casual)
                Text("技术").tag(TranslationStyle.technical)
            }
            .pickerStyle(.segmented)

            Divider()

            // 输入文本框
            VStack(alignment: .leading) {
                Text("输入文本 (Cmd+V 粘贴)")
                    .font(.caption)
                    .foregroundColor(.secondary)

                TextEditor(text: $viewModel.inputText)
                    .frame(height: 100)
                    .border(Color.gray.opacity(0.3))
                    .onChange(of: viewModel.inputText) { oldValue, newValue in
                        viewModel.onInputChange()
                    }
            }

            // 操作按钮
            HStack {
                Button(action: {
                    Task { await viewModel.translate() }
                }) {
                    Label("翻译", systemImage: "arrow.triangle.2.circlepath")
                }
                .buttonStyle(.borderedProminent)
                .keyboardShortcut(.return, modifiers: .command)
                .disabled(viewModel.inputText.isEmpty || viewModel.isTranslating)

                Button(action: {
                    viewModel.copyResult()
                }) {
                    Label("复制结果", systemImage: "doc.on.doc")
                }
                .disabled(viewModel.outputText.isEmpty)

                Button(action: {
                    viewModel.clear()
                }) {
                    Label("清空", systemImage: "trash")
                }

                Spacer()

                if viewModel.isTranslating {
                    ProgressView()
                        .scaleEffect(0.8)
                }
            }

            Divider()

            // 输出文本框
            VStack(alignment: .leading) {
                HStack {
                    Text("翻译结果")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Spacer()

                    if viewModel.isCached {
                        Label("缓存命中", systemImage: "bolt.fill")
                            .font(.caption)
                            .foregroundColor(.green)
                    }
                }

                TextEditor(text: .constant(viewModel.outputText))
                    .frame(height: 100)
                    .border(Color.gray.opacity(0.3))
                    .disabled(true)
            }

            // 统计信息
            if let stats = viewModel.stats {
                HStack {
                    Text("耗时: \(stats.duration, specifier: "%.3f")s")
                    Text("|")
                    Text("缓存命中率: \(stats.hitRate, specifier: "%.1f")%")
                    Text("|")
                    Text("节省时间: \(stats.timeSaved, specifier: "%.1f")s")
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }
        }
        .padding()
        .frame(width: 600, height: 500)
    }
}
```

#### TranslationViewModel.swift（业务逻辑）

```swift
import SwiftUI
import Combine

@MainActor
class TranslationViewModel: ObservableObject {
    @Published var sourceLanguage: Language = .auto
    @Published var targetLanguage: Language = .english
    @Published var style: TranslationStyle = .formal

    @Published var inputText: String = ""
    @Published var outputText: String = ""
    @Published var isTranslating: Bool = false
    @Published var isCached: Bool = false
    @Published var stats: TranslationStats?

    private let client = BackendClient.shared
    private var debounceTimer: Timer?

    // 实时翻译（防抖）
    func onInputChange() {
        debounceTimer?.invalidate()
        debounceTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: false) { [weak self] _ in
            Task { await self?.translate() }
        }
    }

    // 执行翻译
    func translate() async {
        guard !inputText.isEmpty else { return }

        isTranslating = true

        do {
            let response = try await client.translate(
                text: inputText,
                targetLanguage: targetLanguage.code,
                style: style.rawValue
            )

            outputText = response.output
            isCached = response.metadata.cached
            stats = TranslationStats(
                duration: response.duration,
                hitRate: response.metadata.cacheStats.hitRate * 100,
                timeSaved: Double(response.metadata.cacheStats.hits) * 2.5
            )
        } catch {
            outputText = "翻译失败: \(error.localizedDescription)"
        }

        isTranslating = false
    }

    // 复制结果
    func copyResult() {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(outputText, forType: .string)
    }

    // 清空
    func clear() {
        inputText = ""
        outputText = ""
        isCached = false
        stats = nil
    }
}

// 数据模型
enum Language: String, CaseIterable, Identifiable {
    case auto, chinese, english, japanese, korean

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .auto: return "自动检测"
        case .chinese: return "中文"
        case .english: return "English"
        case .japanese: return "日本語"
        case .korean: return "한국어"
        }
    }

    var code: String {
        switch self {
        case .auto: return "auto"
        case .chinese: return "zh-CN"
        case .english: return "en-US"
        case .japanese: return "ja-JP"
        case .korean: return "ko-KR"
        }
    }
}

enum TranslationStyle: String {
    case formal, casual, technical
}

struct TranslationStats {
    let duration: Double
    let hitRate: Double
    let timeSaved: Double
}
```

### 验收标准

| 功能 | 验收方法 | 期望结果 |
|------|----------|----------|
| 界面显示 | 启动应用 | 所有控件正常显示，布局合理 |
| 语言选择 | 切换语言 | 选择器工作正常，支持 5+ 语言 |
| 输入框 | 输入文本 | 自动扩展，支持多行，支持 Cmd+V |
| 翻译功能 | 点击翻译 | 调用 Backend API，显示结果 |
| 缓存指示 | 重复翻译 | 显示"缓存命中"标签 |
| 快捷键 | Cmd+Enter | 触发翻译 |
| 统计显示 | 翻译完成 | 显示耗时、命中率、节省时间 |

---

## Week 2 Day 3-4: 批量处理面板

### 目标

开发**批量翻译界面**，支持：
- 文件拖放（.txt / .md / .csv）
- 文本列表添加/编辑/删除
- 批量翻译队列（进度条、实时更新）
- 缓存统计（整体命中率、预估时间）
- 结果导出（CSV / JSON）

### 界面设计

```
┌─────────────────────────────────────────────────────────┐
│ MacCortex - 批量翻译                          [⚙️] [❓] │
├─────────────────────────────────────────────────────────┤
│ 目标语言: [English ▼]   风格: [Formal ▼]               │
├─────────────────────────────────────────────────────────┤
│ 待翻译列表 (拖放文件或点击添加):                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ☑ MacCortex 是一个智能助手。                 [🗑️]   │ │
│ │ ☑ 它支持多种 AI Pattern。                   [🗑️]   │ │
│ │ ☑ Phase 3 增加了 aya-23 模型。              [🗑️]   │ │
│ │ [+ 添加文本]  [📂 导入文件]                         │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [🚀 开始批量翻译]  [⏸ 暂停]  [🗑️ 清空列表]            │
├─────────────────────────────────────────────────────────┤
│ 翻译进度: ████████░░░░░░░░ 2/3 (66%)                   │
│                                                          │
│ 缓存命中率: 67% (2/3)  |  预估剩余时间: 2.5s           │
├─────────────────────────────────────────────────────────┤
│ 结果列表:                                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ✅ MacCortex is an intelligent assistant. [📋] [✏️]│ │
│ │ ✅ It supports multiple AI patterns.      [📋] [✏️]│ │
│ │ ⏳ 翻译中...                                        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [💾 导出 CSV]  [💾 导出 JSON]  [📋 复制所有结果]       │
└─────────────────────────────────────────────────────────┘
```

### 实现代码

#### BatchTranslationView.swift

```swift
import SwiftUI

struct BatchTranslationView: View {
    @StateObject private var viewModel = BatchTranslationViewModel()

    var body: some View {
        VStack(spacing: 16) {
            // 配置
            HStack {
                Picker("目标语言", selection: $viewModel.targetLanguage) {
                    ForEach(Language.allCases.filter { $0 != .auto }) { language in
                        Text(language.displayName).tag(language)
                    }
                }
                .frame(width: 150)

                Picker("风格", selection: $viewModel.style) {
                    Text("正式").tag(TranslationStyle.formal)
                    Text("随意").tag(TranslationStyle.casual)
                    Text("技术").tag(TranslationStyle.technical)
                }
                .frame(width: 120)
            }

            Divider()

            // 待翻译列表
            VStack(alignment: .leading) {
                Text("待翻译列表 (拖放文件或点击添加)")
                    .font(.caption)
                    .foregroundColor(.secondary)

                List {
                    ForEach(viewModel.items) { item in
                        HStack {
                            Toggle("", isOn: .constant(true))
                                .labelsHidden()

                            Text(item.text)
                                .lineLimit(1)

                            Spacer()

                            Button(action: {
                                viewModel.removeItem(item)
                            }) {
                                Image(systemName: "trash")
                                    .foregroundColor(.red)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .frame(height: 150)
                .border(Color.gray.opacity(0.3))
                .onDrop(of: [.fileURL], isTargeted: nil) { providers in
                    viewModel.handleDrop(providers: providers)
                    return true
                }

                HStack {
                    Button(action: {
                        viewModel.showAddItemDialog()
                    }) {
                        Label("添加文本", systemImage: "plus")
                    }

                    Button(action: {
                        viewModel.importFile()
                    }) {
                        Label("导入文件", systemImage: "folder")
                    }
                }
            }

            // 操作按钮
            HStack {
                Button(action: {
                    Task { await viewModel.startBatchTranslation() }
                }) {
                    Label("开始批量翻译", systemImage: "play.fill")
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.items.isEmpty || viewModel.isTranslating)

                if viewModel.isTranslating {
                    Button(action: {
                        viewModel.pauseTranslation()
                    }) {
                        Label("暂停", systemImage: "pause.fill")
                    }
                }

                Button(action: {
                    viewModel.clearItems()
                }) {
                    Label("清空列表", systemImage: "trash")
                }

                Spacer()
            }

            Divider()

            // 进度显示
            if viewModel.isTranslating || viewModel.results.count > 0 {
                VStack(alignment: .leading) {
                    HStack {
                        Text("翻译进度:")
                        ProgressView(value: viewModel.progress, total: 1.0)
                        Text("\(viewModel.completedCount)/\(viewModel.totalCount) (\(Int(viewModel.progress * 100))%)")
                    }

                    HStack {
                        Text("缓存命中率: \(viewModel.cacheHitRate, specifier: "%.1f")% (\(viewModel.cacheHits)/\(viewModel.totalCount))")
                        Text("|")
                        Text("预估剩余时间: \(viewModel.estimatedTimeRemaining, specifier: "%.1f")s")
                    }
                    .font(.caption)
                    .foregroundColor(.secondary)
                }
            }

            Divider()

            // 结果列表
            VStack(alignment: .leading) {
                Text("结果列表")
                    .font(.caption)
                    .foregroundColor(.secondary)

                List {
                    ForEach(viewModel.results) { result in
                        HStack {
                            if result.success {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                            } else {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundColor(.red)
                            }

                            Text(result.output ?? "翻译中...")
                                .lineLimit(1)

                            Spacer()

                            if result.success {
                                Button(action: {
                                    viewModel.copyResult(result)
                                }) {
                                    Image(systemName: "doc.on.doc")
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                }
                .frame(height: 150)
                .border(Color.gray.opacity(0.3))
            }

            // 导出按钮
            HStack {
                Button(action: {
                    viewModel.exportCSV()
                }) {
                    Label("导出 CSV", systemImage: "doc.text")
                }
                .disabled(viewModel.results.isEmpty)

                Button(action: {
                    viewModel.exportJSON()
                }) {
                    Label("导出 JSON", systemImage: "doc.badge.gearshape")
                }
                .disabled(viewModel.results.isEmpty)

                Button(action: {
                    viewModel.copyAllResults()
                }) {
                    Label("复制所有结果", systemImage: "doc.on.clipboard")
                }
                .disabled(viewModel.results.isEmpty)

                Spacer()
            }
        }
        .padding()
        .frame(width: 700, height: 600)
    }
}
```

#### BatchTranslationViewModel.swift

```swift
import SwiftUI
import Combine

@MainActor
class BatchTranslationViewModel: ObservableObject {
    @Published var targetLanguage: Language = .english
    @Published var style: TranslationStyle = .formal

    @Published var items: [BatchTranslationItem] = []
    @Published var results: [BatchTranslationResult] = []

    @Published var isTranslating: Bool = false
    @Published var progress: Double = 0.0
    @Published var completedCount: Int = 0
    @Published var totalCount: Int = 0

    @Published var cacheHits: Int = 0
    @Published var cacheHitRate: Double = 0.0
    @Published var estimatedTimeRemaining: Double = 0.0

    private let client = BackendClient.shared

    // 开始批量翻译
    func startBatchTranslation() async {
        guard !items.isEmpty else { return }

        isTranslating = true
        totalCount = items.count
        completedCount = 0
        results = []
        cacheHits = 0

        let startTime = Date()

        // 调用批量 API
        do {
            let response = try await client.translateBatch(
                items: items.map { item in
                    TranslationItem(text: item.text, parameters: [
                        "target_language": targetLanguage.code,
                        "style": style.rawValue
                    ])
                }
            )

            // 更新结果
            results = response.items.map { item in
                BatchTranslationResult(
                    id: UUID(),
                    success: item.success,
                    output: item.output,
                    error: item.error
                )
            }

            // 更新统计
            completedCount = response.succeeded
            cacheHits = response.aggregateStats.cacheHits
            cacheHitRate = response.aggregateStats.cacheHitRate * 100
            progress = 1.0

        } catch {
            // 处理错误
            results = items.map { _ in
                BatchTranslationResult(
                    id: UUID(),
                    success: false,
                    output: nil,
                    error: error.localizedDescription
                )
            }
        }

        isTranslating = false
    }

    // 文件拖放处理
    func handleDrop(providers: [NSItemProvider]) {
        for provider in providers {
            if provider.hasItemConformingToTypeIdentifier(kUTTypeFileURL as String) {
                provider.loadItem(forTypeIdentifier: kUTTypeFileURL as String, options: nil) { item, error in
                    guard let data = item as? Data, let url = URL(dataRepresentation: data, relativeTo: nil) else { return }
                    self.importTextFromFile(url: url)
                }
            }
        }
    }

    // 从文件导入文本
    private func importTextFromFile(url: URL) {
        do {
            let content = try String(contentsOf: url, encoding: .utf8)
            let lines = content.components(separatedBy: .newlines).filter { !$0.isEmpty }

            DispatchQueue.main.async {
                self.items.append(contentsOf: lines.map { line in
                    BatchTranslationItem(id: UUID(), text: line)
                })
            }
        } catch {
            print("导入文件失败: \(error)")
        }
    }

    // 导出 CSV
    func exportCSV() {
        let csvContent = results.enumerated().map { index, result in
            "\"\(items[index].text)\",\"\(result.output ?? "")\""
        }.joined(separator: "\n")

        let header = "\"Original\",\"Translation\"\n"
        saveToFile(content: header + csvContent, fileExtension: "csv")
    }

    // 导出 JSON
    func exportJSON() {
        let jsonArray = results.enumerated().map { index, result in
            [
                "original": items[index].text,
                "translation": result.output ?? "",
                "success": result.success
            ]
        }

        if let data = try? JSONSerialization.data(withJSONObject: jsonArray, options: .prettyPrinted),
           let jsonString = String(data: data, encoding: .utf8) {
            saveToFile(content: jsonString, fileExtension: "json")
        }
    }

    private func saveToFile(content: String, fileExtension: String) {
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.init(filenameExtension: fileExtension)!]
        panel.nameFieldStringValue = "translations.\(fileExtension)"

        if panel.runModal() == .OK, let url = panel.url {
            try? content.write(to: url, atomically: true, encoding: .utf8)
        }
    }
}

// 数据模型
struct BatchTranslationItem: Identifiable {
    let id: UUID
    let text: String
}

struct BatchTranslationResult: Identifiable {
    let id: UUID
    let success: Bool
    let output: String?
    let error: String?
}
```

### 验收标准

| 功能 | 验收方法 | 期望结果 |
|------|----------|----------|
| 文件拖放 | 拖放 .txt 文件 | 自动解析每行文本并添加到列表 |
| 批量翻译 | 点击开始翻译 | 调用 /execute/batch API，显示进度 |
| 进度显示 | 翻译过程中 | 实时更新进度条、完成数量 |
| 缓存统计 | 翻译完成 | 显示命中率、命中数量、预估时间 |
| 结果导出 | 导出 CSV/JSON | 文件格式正确，内容完整 |

---

## Week 2 Day 5: 缓存统计与用户体验优化

### 目标

1. **缓存统计面板**:
   - 实时缓存状态（大小、命中率、淘汰数）
   - 缓存清理功能
   - 缓存效率图表（可选）

2. **用户体验优化**:
   - 快捷键支持（Cmd+T 翻译，Cmd+B 批量）
   - 历史记录（最近 20 次翻译）
   - 自动语言检测
   - 错误提示优化

### 缓存统计界面

```
┌─────────────────────────────────────────────────────────┐
│ MacCortex - 缓存统计                          [⚙️] [❓] │
├─────────────────────────────────────────────────────────┤
│ 缓存状态:                                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 缓存大小:    42 / 1000 (4.2%)                       │ │
│ │ 命中次数:    120                                    │ │
│ │ 未命中次数:  80                                     │ │
│ │ 命中率:      60.0%                                  │ │
│ │ 淘汰次数:    5                                      │ │
│ │ 节省时间:    300.0s (5.0 分钟)                      │ │
│ │ TTL:         3600s (1 小时)                         │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [🗑️ 清空缓存]  [🔄 刷新统计]                           │
├─────────────────────────────────────────────────────────┤
│ 历史记录 (最近 20 次):                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 2026-01-22 08:35  |  zh-CN → en-US  |  ✅ 缓存     │ │
│ │ "MacCortex 是..." → "MacCortex is..."              │ │
│ │                                                     │ │
│ │ 2026-01-22 08:34  |  zh-CN → en-US  |  ❌ 未缓存   │ │
│ │ "Phase 3 增加..." → "Phase 3 increased..."         │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [📋 复制历史]  [🗑️ 清空历史]                           │
└─────────────────────────────────────────────────────────┘
```

### 快捷键配置

```swift
// ContentView.swift
var body: some View {
    TabView {
        TranslationView()
            .tabItem {
                Label("翻译", systemImage: "character.bubble")
            }
            .keyboardShortcut("t", modifiers: .command)

        BatchTranslationView()
            .tabItem {
                Label("批量", systemImage: "list.bullet")
            }
            .keyboardShortcut("b", modifiers: .command)

        CacheStatsView()
            .tabItem {
                Label("缓存", systemImage: "chart.bar")
            }
            .keyboardShortcut("c", modifiers: .command)
    }
}
```

### 验收标准

| 功能 | 验收方法 | 期望结果 |
|------|----------|----------|
| 缓存统计 | 查看缓存面板 | 显示实时统计（大小、命中率、节省时间） |
| 缓存清理 | 点击清空缓存 | 调用 Backend API，缓存清空成功 |
| 历史记录 | 翻译后查看历史 | 显示最近 20 次翻译，包含时间、语言对、缓存状态 |
| 快捷键 | Cmd+T / Cmd+B | 切换到对应面板 |
| 错误提示 | Backend 离线 | 显示友好错误提示（非技术术语） |

---

## Week 2 验收清单

### 核心功能验收（P0 阻塞性）

| # | 功能 | 验收方法 | 期望结果 | 状态 |
|---|------|----------|----------|------|
| 1 | Xcode 迁移 | 用户手动执行 | Workspace 可构建，Backend 可连接 | ⏳ 待执行 |
| 2 | 翻译界面 | 输入文本翻译 | 调用 Backend API，显示结果与统计 | ⏳ 待开发 |
| 3 | 缓存指示 | 重复翻译 | 显示"缓存命中"标签，耗时 < 0.1s | ⏳ 待开发 |
| 4 | 批量翻译 | 拖放文件 | 自动解析，批量翻译，显示进度 | ⏳ 待开发 |
| 5 | 结果导出 | 导出 CSV | 格式正确，包含原文和译文 | ⏳ 待开发 |
| 6 | 缓存统计 | 查看统计面板 | 显示命中率、节省时间 | ⏳ 待开发 |
| 7 | 快捷键 | Cmd+Enter 翻译 | 触发翻译功能 | ⏳ 待开发 |
| 8 | 性能 | 单次翻译（缓存） | < 0.1s 响应时间 | ⏳ 待测试 |

**通过条件**: 所有 8 项必须 ✅（任何 ❌ 视为 Week 2 失败）

### 技术债务检查

- [ ] 代码格式化（SwiftLint）
- [ ] 错误处理完整性（所有 await 都有 try-catch）
- [ ] 日志记录（关键操作记录到 Console）
- [ ] 内存泄漏检查（Instruments Leaks）
- [ ] UI 响应性（主线程无阻塞操作）

### 文档更新

- [ ] 更新 README.md（添加 GUI 使用说明）
- [ ] 更新 CHANGELOG.md（记录 Week 2 新功能）
- [ ] 创建 GUI_GUIDE.md（GUI 用户手册）
- [ ] 更新 API_REFERENCE.md（补充批量 API 文档）

---

## 关键决策点

### 决策 1: 是否支持流式翻译输出？

**问题**: GUI 是否需要支持流式显示翻译结果（逐字显示）？

**选项**:
- **方案 A**: Week 2 实现流式输出（需 Backend 支持 SSE）
- **方案 B**: Week 2 仅支持一次性返回，Week 3 实现流式
- **方案 C**: 不实现流式（保持简单）

**建议**: **方案 B** - Week 2 仅支持一次性返回，Week 3 实现流式

**理由**:
- Week 2 重点是基础 GUI，流式输出需要 Backend SSE 支持（Backend 优化 3）
- 单次翻译有缓存后，响应时间 < 0.1s，流式收益不明显
- Week 3 结合长文本翻译场景再实现流式更合理

---

### 决策 2: 批量翻译是否支持暂停/恢复？

**问题**: 批量翻译进行中，用户是否可以暂停并稍后恢复？

**选项**:
- **方案 A**: 支持暂停/恢复（需保存中间状态）
- **方案 B**: 不支持暂停，但支持取消（丢弃所有未完成项）
- **方案 C**: 完全不可中断（等待完成）

**建议**: **方案 B** - 支持取消但不保存状态

**理由**:
- 批量 API 已经很快（100 条目 < 10s），暂停场景不常见
- 保存/恢复状态增加复杂度（需持久化队列）
- 用户可重新添加文本后再次执行

---

### 决策 3: 是否集成系统剪贴板监听？

**问题**: GUI 是否自动监听剪贴板，检测到文本后自动翻译？

**选项**:
- **方案 A**: 自动监听 + 悬浮窗（Apple Intelligence 风格）
- **方案 B**: 手动触发（Cmd+Shift+V 粘贴并翻译）
- **方案 C**: 不集成剪贴板（保持简单）

**建议**: **方案 B** - 手动快捷键触发

**理由**:
- 自动监听需要辅助功能权限（Accessibility），用户抵触较高
- 手动快捷键平衡了便利性与隐私
- Week 3 可升级为可选的自动监听（Settings 开关）

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 | 残余风险 |
|------|------|------|----------|----------|
| Xcode 迁移失败 | 15% | 高 | 详细指南 + 视频教程 | 🟡 中 |
| SwiftUI 学习曲线 | 20% | 中 | 参考 Apple 官方示例 + ChatGPT 辅助 | 🟢 低 |
| Backend 离线 | 5% | 高 | 健康检查 + 自动重启提示 | 🟢 低 |
| 性能不达标 | 10% | 中 | 缓存已验证 + 异步加载 | 🟢 低 |
| UI 响应性差 | 8% | 中 | MainActor + Task | 🟢 低 |
| 批量处理 OOM | 3% | 中 | 限制最多 100 条目 + 分页处理 | 🟢 低 |

**总体风险评分**: 🟢 **可控**（无高残余风险）

---

## 时间规划

| 阶段 | 时间 | 任务 | 交付物 |
|------|------|------|--------|
| Day 0 | 0.5-0.75 天 | 用户执行 Xcode 迁移 | Workspace 可构建 |
| Day 1-2 | 2 天 | 翻译 GUI 界面 | TranslationView + ViewModel |
| Day 3-4 | 2 天 | 批量处理面板 | BatchTranslationView + ViewModel |
| Day 5 | 1 天 | 缓存统计 + UX 优化 | CacheStatsView + 快捷键 |
| **总计** | **5.5-5.75 天** | **完整 GUI** | **可用 macOS 应用** |

---

## 下一步行动（立即执行）

### Day 0: 用户前置任务（今天）

**用户需手动执行**:
1. 阅读 `XCODE_MIGRATION_GUIDE.md`（10 分钟）
2. 创建 Xcode Workspace（5 分钟）
3. 添加 Backend 通信层（10 分钟）
4. 验证 Backend 连接（10 分钟）
5. 配置快捷键与热重载（5 分钟）

**验收**:
```bash
# Backend 运行中
curl http://localhost:8000/health

# Xcode 项目可构建
xcodebuild -workspace MacCortex.xcworkspace -scheme MacCortex build

# 应用可启动
open build/MacCortex.app
```

**完成后回复**: "Xcode 迁移已完成，可以开始 Day 1 开发"

---

**计划状态**: ⏳ 待批准
**创建时间**: 2026-01-22 08:40 UTC
**基于**: Phase 3 Week 1 成果 + Backend 优化完成
**执行人**: Claude Code (Sonnet 4.5) + 用户
**验证方式**: 8 项 P0 验收标准 + GUI 交互流畅性测试
