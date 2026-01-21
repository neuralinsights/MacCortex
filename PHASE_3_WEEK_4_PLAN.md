# Phase 3 Week 4 实施计划

> **主题**: 批量翻译 + 文件导入/导出 + 完善偏好设置
> **时间**: 5 天（2026-01-22 ~ 2026-01-26）
> **前置**: Phase 3 Week 3 已完成（流式翻译、剪贴板监听、悬浮窗口、全局快捷键、偏好设置）

---

## 概览

Phase 3 Week 4 将实现 MacCortex 的**生产力增强功能**：

| 天数 | 功能 | 预估代码量 | 技术栈 |
|------|------|-----------|--------|
| **Day 1-2** | 批量翻译队列 | ~400 行 | SwiftUI + Combine + FileManager |
| **Day 3-4** | 导出功能 | ~350 行 | NSDocument + PDFKit + UniformTypeIdentifiers |
| **Day 5** | 完善偏好设置 | ~200 行 | JSON Codable + UNUserNotificationCenter |
| **总计** | - | **~950 行** | SwiftUI + macOS 原生 API |

---

## Day 1-2: 批量翻译队列

### 目标

实现批量文件翻译功能，支持：
- 文件拖放（.txt、.md、.docx）
- 并发翻译（最多 5 个并发）
- 进度条显示（整体进度 + 单个文件进度）
- 队列管理（暂停、恢复、取消）

### 架构设计

#### 1. BatchTranslationQueue.swift（核心逻辑）

```swift
@MainActor
class BatchTranslationQueue: ObservableObject {
    @Published var items: [BatchItem] = []
    @Published var isProcessing: Bool = false
    @Published var currentProgress: Double = 0.0

    private let maxConcurrency = 5
    private var activeTasks: Set<UUID> = []

    func addFiles(_ urls: [URL])
    func start()
    func pause()
    func resume()
    func cancel()
    func remove(_ id: UUID)

    private func processNext()
    private func translateFile(_ item: BatchItem)
}

struct BatchItem: Identifiable {
    let id: UUID
    let url: URL
    var status: BatchStatus
    var progress: Double
    var sourceText: String?
    var translatedText: String?
    var error: String?
}

enum BatchStatus {
    case pending
    case processing
    case completed
    case failed
    case cancelled
}
```

#### 2. BatchTranslationView.swift（UI 界面）

**功能**:
- 文件列表（LazyVStack）
- 拖放区域（.onDrop）
- 控制按钮（开始、暂停、清空）
- 进度显示（ProgressView）

**布局**:
```
┌────────────────────────────────────────┐
│  批量翻译                               │
├────────────────────────────────────────┤
│  [拖放文件到此处]                      │
│  支持 .txt、.md、.docx                 │
├────────────────────────────────────────┤
│  整体进度: ████████░░ 80% (4/5)       │
├────────────────────────────────────────┤
│  ┌──────────────────────────────────┐ │
│  │ ✓ file1.txt    [完成]  100%     │ │
│  │ ⏳ file2.md    [翻译中] 45%     │ │
│  │ ⏸ file3.docx  [暂停]   0%      │ │
│  │ ❌ file4.txt   [失败]  -        │ │
│  │ ⏱ file5.md    [等待]   0%      │ │
│  └──────────────────────────────────┘ │
├────────────────────────────────────────┤
│  [开始翻译] [暂停] [清空队列]          │
└────────────────────────────────────────┘
```

#### 3. 文件读取支持

**支持格式**:
- `.txt`: 直接读取（UTF-8）
- `.md`: 直接读取（UTF-8）
- `.docx`: 使用 NSAttributedString 或第三方库

**读取逻辑**:
```swift
func readFile(_ url: URL) throws -> String {
    let fileType = url.pathExtension.lowercased()

    switch fileType {
    case "txt", "md":
        return try String(contentsOf: url, encoding: .utf8)

    case "docx":
        // 简化方案：使用 NSAttributedString
        if let data = try? Data(contentsOf: url),
           let attributed = NSAttributedString(docx: data, documentAttributes: nil) {
            return attributed.string
        }
        throw FileReadError.unsupportedFormat

    default:
        throw FileReadError.unsupportedFormat
    }
}
```

#### 4. 并发控制

**策略**: OperationQueue + 信号量

```swift
private func processNext() {
    // 1. 检查是否暂停
    guard isProcessing else { return }

    // 2. 检查并发数
    guard activeTasks.count < maxConcurrency else { return }

    // 3. 获取下一个待处理项
    guard let item = items.first(where: { $0.status == .pending }) else {
        // 所有任务完成
        if activeTasks.isEmpty {
            isProcessing = false
        }
        return
    }

    // 4. 标记为处理中
    activeTasks.insert(item.id)
    updateItemStatus(item.id, .processing)

    // 5. 异步翻译
    Task {
        await translateFile(item)
        activeTasks.remove(item.id)
        processNext()  // 递归处理下一个
    }
}
```

### 实现文件清单

**新增文件**（3 个）:
1. `Sources/MacCortexApp/Services/BatchTranslationQueue.swift` (~200 行)
2. `Sources/MacCortexApp/Views/BatchTranslationView.swift` (~150 行)
3. `Sources/MacCortexApp/Utils/FileReader.swift` (~50 行)

**修改文件**（1 个）:
4. `Sources/MacCortexApp/ContentView.swift` (+5 行，添加 Tab)

### 验收标准（P0）

- ✅ 支持拖放 .txt、.md 文件（.docx 为 P1）
- ✅ 并发翻译最多 5 个文件
- ✅ 实时进度显示（整体 + 单个）
- ✅ 支持暂停、恢复、取消
- ✅ 失败重试机制
- ✅ 翻译完成后显示结果

---

## Day 3-4: 导出功能

### 目标

实现翻译结果导出功能，支持：
- 导出为 .txt、.docx、.pdf
- 双语对照导出（源文 + 译文）
- 自定义导出模板（可选）

### 架构设计

#### 1. ExportManager.swift（核心逻辑）

```swift
class ExportManager {
    static let shared = ExportManager()

    func exportToText(
        _ items: [ExportItem],
        layout: ExportLayout
    ) throws -> Data

    func exportToDocx(
        _ items: [ExportItem],
        layout: ExportLayout
    ) throws -> Data

    func exportToPDF(
        _ items: [ExportItem],
        layout: ExportLayout
    ) throws -> Data
}

struct ExportItem {
    let sourceText: String
    let translatedText: String
    let sourceLanguage: String
    let targetLanguage: String
    let timestamp: Date
}

enum ExportLayout {
    case sourceOnly      // 仅译文
    case bilingual       // 双语对照
    case sideBySide      // 左右对照
}
```

#### 2. 导出格式实现

**TXT 导出**（最简单）:
```swift
func exportToText(_ items: [ExportItem], layout: ExportLayout) throws -> Data {
    var content = ""

    for item in items {
        switch layout {
        case .sourceOnly:
            content += "\(item.translatedText)\n\n"

        case .bilingual:
            content += "【原文】\n\(item.sourceText)\n\n"
            content += "【译文】\n\(item.translatedText)\n\n"
            content += "---\n\n"

        case .sideBySide:
            // 按段落对齐
            let sourceParagraphs = item.sourceText.components(separatedBy: "\n")
            let translatedParagraphs = item.translatedText.components(separatedBy: "\n")

            for (source, translated) in zip(sourceParagraphs, translatedParagraphs) {
                content += "\(source) | \(translated)\n"
            }
            content += "\n"
        }
    }

    return content.data(using: .utf8)!
}
```

**PDF 导出**（使用 PDFKit）:
```swift
func exportToPDF(_ items: [ExportItem], layout: ExportLayout) throws -> Data {
    let pdfDocument = PDFDocument()

    for (index, item) in items.enumerated() {
        let pageContent = formatPage(item, layout: layout)
        let pdfPage = createPDFPage(content: pageContent)
        pdfDocument.insert(pdfPage, at: index)
    }

    return pdfDocument.dataRepresentation()!
}

private func createPDFPage(content: String) -> PDFPage {
    let pageRect = CGRect(x: 0, y: 0, width: 612, height: 792)  // A4
    let renderer = UIGraphicsPDFRenderer(bounds: pageRect)

    let data = renderer.pdfData { context in
        context.beginPage()

        let textRect = pageRect.insetBy(dx: 50, dy: 50)
        let attributes: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 12),
            .foregroundColor: NSColor.black
        ]

        content.draw(in: textRect, withAttributes: attributes)
    }

    return PDFPage(data: data)!
}
```

**DOCX 导出**（简化方案：使用 NSAttributedString）:
```swift
func exportToDocx(_ items: [ExportItem], layout: ExportLayout) throws -> Data {
    let attributedString = NSMutableAttributedString()

    for item in items {
        let content = formatContent(item, layout: layout)
        let attributed = NSAttributedString(string: content, attributes: [
            .font: NSFont.systemFont(ofSize: 12),
            .foregroundColor: NSColor.black
        ])

        attributedString.append(attributed)
    }

    // 导出为 .docx
    let docFormat = NSAttributedString.DocumentType.docFormat
    return try attributedString.data(from: NSRange(location: 0, length: attributedString.length),
                                     documentAttributes: [.documentType: docFormat])
}
```

#### 3. ExportOptionsView.swift（导出选项 UI）

**功能**:
- 格式选择（.txt、.docx、.pdf）
- 布局选择（仅译文、双语对照、左右对照）
- 文件名自定义
- 保存位置选择

**布局**:
```
┌────────────────────────────────────┐
│  导出选项                           │
├────────────────────────────────────┤
│  格式:  ○ TXT  ○ DOCX  ● PDF      │
│  布局:  ○ 仅译文  ● 双语  ○ 对照  │
│  文件名: [翻译结果_20260122.pdf]   │
├────────────────────────────────────┤
│  [取消]             [导出]         │
└────────────────────────────────────┘
```

### 实现文件清单

**新增文件**（3 个）:
1. `Sources/MacCortexApp/Services/ExportManager.swift` (~200 行)
2. `Sources/MacCortexApp/Views/ExportOptionsView.swift` (~100 行)
3. `Sources/MacCortexApp/Utils/PDFGenerator.swift` (~50 行)

**修改文件**（1 个）:
4. `Sources/MacCortexApp/Views/BatchTranslationView.swift` (+50 行，添加导出按钮)

### 验收标准（P0）

- ✅ 导出为 TXT 格式正常
- ✅ 双语对照布局正确
- ✅ 文件名可自定义
- ✅ 保存位置可选择（NSSavePanel）
- ✅ 导出后自动打开文件（可选）

**P1（增强功能）**:
- ✅ 导出为 PDF 格式（使用 PDFKit）
- ⚠️ 导出为 DOCX 格式（NSAttributedString 限制较多）
- ⚠️ 自定义导出模板（Phase 4 考虑）

---

## Day 5: 完善偏好设置

### 目标

完善 Week 3 中未实现的偏好设置功能：
1. 实现导出/导入设置（JSON）
2. 实现翻译后通知（UNUserNotificationCenter）
3. 添加设置搜索功能（可选）

### 功能详情

#### 1. 导出/导入设置（JSON）

**导出实现**:
```swift
func export(to url: URL) {
    let settings: [String: Any] = [
        "version": "1.0",
        "timestamp": Date().timeIntervalSince1970,
        "settings": [
            "defaultSourceLanguage": defaultSourceLanguage.rawValue,
            "defaultTargetLanguage": defaultTargetLanguage.rawValue,
            // ... 其他 23 个设置项 ...
        ]
    ]

    do {
        let data = try JSONSerialization.data(withJSONObject: settings, options: .prettyPrinted)
        try data.write(to: url)
        print("[SettingsManager] 设置已导出到: \(url)")
    } catch {
        print("[SettingsManager] 导出失败: \(error)")
    }
}
```

**导入实现**:
```swift
func `import`(from url: URL) {
    do {
        let data = try Data(contentsOf: url)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]

        guard let settings = json?["settings"] as? [String: Any] else {
            print("[SettingsManager] 无效的设置文件")
            return
        }

        // 逐项导入（带验证）
        if let value = settings["defaultSourceLanguage"] as? String,
           let language = Language(rawValue: value) {
            defaultSourceLanguage = language
        }

        // ... 其他 23 个设置项 ...

        print("[SettingsManager] 设置已导入")
    } catch {
        print("[SettingsManager] 导入失败: \(error)")
    }
}
```

#### 2. 翻译后通知

**权限请求**:
```swift
func requestNotificationPermission() {
    UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { granted, error in
        if granted {
            print("[Notification] 通知权限已授予")
        } else {
            print("[Notification] 通知权限被拒绝")
        }
    }
}
```

**发送通知**:
```swift
func sendTranslationNotification(sourceText: String, translatedText: String) {
    guard SettingsManager.shared.clipboardShowNotification else { return }

    let content = UNMutableNotificationContent()
    content.title = "翻译完成"
    content.body = "\(sourceText.prefix(50))... → \(translatedText.prefix(50))..."
    content.sound = .default

    let request = UNNotificationRequest(identifier: UUID().uuidString,
                                       content: content,
                                       trigger: nil)

    UNUserNotificationCenter.current().add(request) { error in
        if let error = error {
            print("[Notification] 发送失败: \(error)")
        }
    }
}
```

**集成到 TranslationViewModel**:
```swift
func translate() async {
    // ... 翻译逻辑 ...

    // 翻译完成后发送通知
    if SettingsManager.shared.clipboardShowNotification {
        NotificationManager.shared.sendTranslationNotification(
            sourceText: inputText,
            translatedText: outputText
        )
    }
}
```

#### 3. 设置搜索功能（可选）

**实现**:
```swift
struct SettingsView: View {
    @State private var searchText = ""
    @State private var filteredSettings: [SettingItem] = []

    var body: some View {
        VStack {
            // 搜索框
            TextField("搜索设置...", text: $searchText)
                .textFieldStyle(.roundedBorder)
                .padding()
                .onChange(of: searchText) { oldValue, newValue in
                    filterSettings(newValue)
                }

            // 搜索结果（如果有搜索词）
            if !searchText.isEmpty {
                SearchResultsView(results: filteredSettings)
            } else {
                // 原有的 TabView
                TabView { ... }
            }
        }
    }

    func filterSettings(_ query: String) {
        // 搜索所有设置项
        filteredSettings = allSettings.filter { setting in
            setting.name.localizedCaseInsensitiveContains(query) ||
            setting.description.localizedCaseInsensitiveContains(query)
        }
    }
}
```

### 实现文件清单

**新增文件**（1 个）:
1. `Sources/MacCortexApp/Services/NotificationManager.swift` (~100 行)

**修改文件**（2 个）:
2. `Sources/MacCortexApp/Views/SettingsView.swift` (+100 行，导出/导入 + 搜索)
3. `Sources/MacCortexApp/ViewModels/TranslationViewModel.swift` (+20 行，通知集成)

### 验收标准（P0）

- ✅ 导出设置到 JSON 正常
- ✅ 从 JSON 导入设置正常
- ✅ 翻译后显示系统通知
- ✅ 通知权限请求正常

**P1（增强功能）**:
- ✅ 设置搜索功能
- ⚠️ 设置版本迁移（未来版本）
- ⚠️ 云同步设置（iCloud，Phase 4）

---

## 总体验收标准

### P0（核心功能）

| 功能 | 验收项 | 验证方式 |
|------|--------|----------|
| **批量翻译** | 支持拖放 .txt、.md 文件 | 拖放测试 |
| **批量翻译** | 并发翻译最多 5 个文件 | 添加 10 个文件观察 |
| **批量翻译** | 实时进度显示正确 | 观察进度条 |
| **批量翻译** | 暂停、恢复、取消正常 | 按钮测试 |
| **导出功能** | 导出为 TXT 格式正常 | 导出后打开文件验证 |
| **导出功能** | 双语对照布局正确 | 内容检查 |
| **导出功能** | 文件名可自定义 | NSSavePanel 测试 |
| **偏好设置** | 导出设置到 JSON | 导出后查看 JSON 内容 |
| **偏好设置** | 从 JSON 导入设置 | 导入后验证设置值 |
| **偏好设置** | 翻译后显示通知 | 翻译后观察系统通知 |

### P1（增强功能）

| 功能 | 验收项 | 备注 |
|------|--------|------|
| **批量翻译** | 支持 .docx 文件 | 需要文档解析库 |
| **批量翻译** | 失败重试机制 | 自动重试 3 次 |
| **导出功能** | 导出为 PDF 格式 | PDFKit 实现 |
| **导出功能** | 导出为 DOCX 格式 | NSAttributedString 限制 |
| **偏好设置** | 设置搜索功能 | 实时过滤 |
| **偏好设置** | 自动复制结果到剪贴板 | 集成到 TranslationViewModel |

---

## 技术栈总结

| 功能 | 技术栈 | 关键 API |
|------|--------|----------|
| **文件拖放** | SwiftUI | `.onDrop(of: [.fileURL])` |
| **文件读取** | Foundation | `String(contentsOf:)`, `NSAttributedString(docx:)` |
| **并发控制** | Swift Concurrency | `Task`, `TaskGroup`, 信号量 |
| **进度显示** | SwiftUI | `ProgressView`, `@Published` |
| **TXT 导出** | Foundation | `String.data(using:)` |
| **PDF 导出** | PDFKit | `PDFDocument`, `PDFPage` |
| **DOCX 导出** | Foundation | `NSAttributedString.data(documentAttributes:)` |
| **JSON 导出/导入** | Foundation | `JSONSerialization` |
| **系统通知** | UserNotifications | `UNUserNotificationCenter` |
| **设置搜索** | SwiftUI | `TextField`, `.onChange()`, 数组过滤 |

---

## 时间安排

| 天数 | 任务 | 预估时间 |
|------|------|----------|
| **Day 1** | BatchTranslationQueue.swift + FileReader.swift | 4 小时 |
| **Day 1-2** | BatchTranslationView.swift UI | 4 小时 |
| **Day 3** | ExportManager.swift（TXT + PDF） | 4 小时 |
| **Day 3-4** | ExportOptionsView.swift UI | 4 小时 |
| **Day 5** | 导出/导入设置 + 通知 | 4 小时 |
| **Day 5** | 设置搜索功能 | 2 小时 |
| **总计** | - | **22 小时（~5 天）** |

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|----------|
| DOCX 文件读取失败 | 40% | 中 | 降级为 P1，先支持 .txt/.md |
| PDF 导出排版问题 | 30% | 中 | 使用简单布局，Phase 4 优化 |
| 并发翻译性能瓶颈 | 20% | 低 | 限制最大并发数为 5 |
| 通知权限被拒绝 | 10% | 低 | 静默失败，不影响核心功能 |
| JSON 导入格式不兼容 | 15% | 中 | 添加版本检查与迁移逻辑 |

---

## 下一步（Phase 4）

完成 Week 4 后，项目进入 **Phase 4: MLX 本地翻译 + App Intents 集成**：

1. **MLX 本地推理**（2 周）
2. **App Intents + Siri**（1 周）
3. **跨应用集成**（1 周）
4. **性能优化与打磨**（1 周）

---

**创建时间**: 2026-01-22
**执行时间**: 2026-01-22 ~ 2026-01-26
**前置条件**: Phase 3 Week 3 完成
**目标**: 生产力增强功能（批量翻译 + 导出）
