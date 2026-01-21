# Phase 3 Week 3 详细执行计划

> **版本**: v1.0
> **创建时间**: 2026-01-22
> **状态**: 待执行
> **前置条件**: Week 2 完成（翻译 GUI + 批量处理 + 缓存统计）

---

## 执行摘要

Phase 3 Week 3 的核心目标是**增强用户体验与高级功能**，通过流式输出、剪贴板监听、悬浮窗口等功能，将 MacCortex 打造为真正的"Apple Intelligence 风格"智能助手。

**核心目标**:
1. ✅ 流式输出（Server-Sent Events）—— 实时显示翻译进度
2. ✅ 剪贴板监听（可选功能）—— 自动检测剪贴板变化并翻译
3. ✅ 悬浮窗口（Apple Intelligence 风格）—— 快速访问翻译功能
4. ✅ 全局快捷键（Cmd+Shift+T）—— 任何位置快速调用
5. ✅ 偏好设置（Settings Window）—— 自定义用户体验

**工期**: 5 天（2026-01-22 ~ 2026-01-26）
**验收标准**: 5 项核心功能全部实现 + 用户体验流畅 + 性能优秀

---

## Week 2 成果回顾

### 已完成工作

| 任务 | 状态 | 代码量 |
|------|------|--------|
| 翻译 GUI 界面 | ✅ 完成 | 1,700+ 行 |
| 批量处理面板 | ✅ 完成 | 1,100+ 行 |
| 缓存统计显示 | ✅ 完成 | 900+ 行 |
| Backend 通信层 | ✅ 完成 | 273 行 |
| **总计** | **✅** | **3,973 行** |

### 当前 GUI 功能

**已实现**:
- ✅ 单次翻译（13 种语言，3 种风格）
- ✅ 批量翻译（文件拖放，CSV/JSON 导出）
- ✅ 缓存统计（命中率，节省时间）
- ✅ 翻译历史（最近 20 条）
- ✅ 快捷键支持（Cmd+R, Cmd+T, Cmd+C 等）

**未实现**（Week 3 目标）:
- ❌ 流式输出（逐字显示）
- ❌ 剪贴板监听
- ❌ 悬浮窗口
- ❌ 全局快捷键
- ❌ 偏好设置

---

## Week 3 Day 1-2: 流式输出（SSE 支持）

### 目标

实现**流式翻译输出**，让用户实时看到翻译进度（类似 ChatGPT 打字效果）。

### 技术方案

**Server-Sent Events (SSE)**:
- Backend: FastAPI 流式响应
- Frontend: SwiftUI AsyncSequence 接收

### 任务清单

#### Day 1: Backend SSE 支持

**1. 修改 Backend translate.py**

在 `Backend/src/patterns/translate.py` 添加流式方法：

```python
# Backend/src/patterns/translate.py

from fastapi import StreamingResponse
import asyncio
import json

async def execute_stream(self, text: str, parameters: Dict[str, Any]) -> StreamingResponse:
    """流式翻译（SSE）"""

    async def event_generator():
        """生成 SSE 事件"""
        try:
            # 1. 发送开始事件
            yield f"event: start\n"
            yield f"data: {json.dumps({'status': 'started', 'input_length': len(text)})}\n\n"

            # 2. 检查缓存
            cache_key = self._build_cache_key(text, parameters)
            cached = self.cache.get(cache_key)

            if cached:
                # 缓存命中：一次性返回
                yield f"event: cached\n"
                yield f"data: {json.dumps({'cached': True})}\n\n"

                # 模拟打字效果（逐字发送）
                for i in range(0, len(cached["output"]), 5):
                    chunk = cached["output"][i:i+5]
                    yield f"event: chunk\n"
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
                    await asyncio.sleep(0.05)  # 50ms 延迟

                yield f"event: done\n"
                yield f"data: {json.dumps(cached)}\n\n"
            else:
                # 缓存未命中：流式翻译
                yield f"event: translating\n"
                yield f"data: {json.dumps({'cached': False})}\n\n"

                # 使用 Ollama 流式 API
                full_text = ""
                async for chunk in self._translate_stream_ollama(text, parameters):
                    full_text += chunk
                    yield f"event: chunk\n"
                    yield f"data: {json.dumps({'text': chunk})}\n\n"

                # 保存到缓存
                result = {
                    "output": full_text,
                    "metadata": {
                        "cached": False,
                        "model": "aya-23:latest",
                        "duration": "...",
                        # ...
                    }
                }
                self.cache.set(cache_key, result)

                yield f"event: done\n"
                yield f"data: {json.dumps(result)}\n\n"

        except Exception as e:
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

async def _translate_stream_ollama(self, text: str, parameters: Dict[str, Any]):
    """使用 Ollama 流式翻译"""
    target_language = parameters.get("target_language", "en-US")
    style = parameters.get("style", "formal")

    prompt = self._build_prompt(text, target_language, style)

    # Ollama Python 客户端流式调用
    response = await self.ollama_client.chat(
        model="aya-23:latest",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    async for part in response:
        if 'message' in part and 'content' in part['message']:
            yield part['message']['content']
```

**2. 添加流式端点**

在 `Backend/src/main.py` 添加新端点：

```python
# Backend/src/main.py

@app.post("/execute/stream")
async def execute_pattern_stream(request: PatternRequest):
    """流式执行 Pattern（SSE）"""

    pattern_id = request.pattern_id
    text = request.text
    parameters = request.parameters

    # 仅支持 translate pattern
    if pattern_id != "translate":
        raise HTTPException(400, "仅 translate pattern 支持流式输出")

    pattern = registry.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(404, f"Pattern not found: {pattern_id}")

    return await pattern.execute_stream(text, parameters)
```

**3. 测试流式 API**

```bash
# 测试 SSE 端点
curl -N http://localhost:8000/execute/stream \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "translate",
    "text": "Hello, how are you?",
    "parameters": {
      "target_language": "zh-CN",
      "style": "formal"
    }
  }'

# 预期输出（逐行）:
# event: start
# data: {"status": "started", "input_length": 19}
#
# event: chunk
# data: {"text": "你好"}
#
# event: chunk
# data: {"text": "，你"}
#
# event: chunk
# data: {"text": "好吗"}
#
# event: chunk
# data: {"text": "？"}
#
# event: done
# data: {"output": "你好，你好吗？", "metadata": {...}}
```

**交付物**:
- `Backend/src/patterns/translate.py`（流式方法）
- `Backend/src/main.py`（/execute/stream 端点）
- `Backend/tests/test_stream.py`（流式测试）

---

#### Day 2: SwiftUI 流式显示

**1. 创建 SSE 客户端**

在 `Sources/MacCortexApp/Network/SSEClient.swift`:

```swift
// Sources/MacCortexApp/Network/SSEClient.swift

import Foundation

struct SSEEvent {
    let event: String
    let data: String
}

class SSEClient: NSObject, URLSessionDataDelegate {
    private var session: URLSession!
    private var task: URLSessionDataTask?
    private var buffer = ""

    var onEvent: ((SSEEvent) -> Void)?
    var onComplete: (() -> Void)?
    var onError: ((Error) -> Void)?

    override init() {
        super.init()
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 300  // 5 分钟
        session = URLSession(configuration: config, delegate: self, delegateQueue: nil)
    }

    func connect(url: URL, body: Data) {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = body

        task = session.dataTask(with: request)
        task?.resume()
    }

    func disconnect() {
        task?.cancel()
        task = nil
    }

    // URLSessionDataDelegate
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        guard let chunk = String(data: data, encoding: .utf8) else { return }
        buffer += chunk

        // 解析 SSE 事件（以双换行符分隔）
        let events = buffer.components(separatedBy: "\n\n")
        buffer = events.last ?? ""

        for eventString in events.dropLast() {
            parseEvent(eventString)
        }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            onError?(error)
        } else {
            onComplete?()
        }
    }

    private func parseEvent(_ eventString: String) {
        var event = ""
        var data = ""

        for line in eventString.components(separatedBy: "\n") {
            if line.hasPrefix("event: ") {
                event = String(line.dropFirst(7))
            } else if line.hasPrefix("data: ") {
                data = String(line.dropFirst(6))
            }
        }

        if !event.isEmpty && !data.isEmpty {
            onEvent?(SSEEvent(event: event, data: data))
        }
    }
}
```

**2. 更新 TranslationViewModel**

在 `Sources/MacCortexApp/ViewModels/TranslationViewModel.swift` 添加流式翻译：

```swift
// Sources/MacCortexApp/ViewModels/TranslationViewModel.swift

@MainActor
class TranslationViewModel: ObservableObject {
    // ... 现有属性 ...

    @Published var isStreaming: Bool = false
    @Published var streamProgress: String = ""

    private var sseClient: SSEClient?

    // 流式翻译
    func translateStream() async {
        guard !inputText.isEmpty else { return }

        isStreaming = true
        outputText = ""
        streamProgress = ""
        errorMessage = nil

        let url = URL(string: "http://localhost:8000/execute/stream")!
        let body = try! JSONEncoder().encode([
            "pattern_id": "translate",
            "text": inputText,
            "parameters": [
                "target_language": targetLanguage.code,
                "style": style.rawValue
            ]
        ])

        sseClient = SSEClient()

        sseClient?.onEvent = { [weak self] event in
            Task { @MainActor in
                self?.handleSSEEvent(event)
            }
        }

        sseClient?.onComplete = { [weak self] in
            Task { @MainActor in
                self?.isStreaming = false
            }
        }

        sseClient?.onError = { [weak self] error in
            Task { @MainActor in
                self?.errorMessage = error.localizedDescription
                self?.isStreaming = false
            }
        }

        sseClient?.connect(url: url, body: body)
    }

    func stopStreaming() {
        sseClient?.disconnect()
        isStreaming = false
    }

    private func handleSSEEvent(_ event: SSEEvent) {
        switch event.event {
        case "start":
            streamProgress = "开始翻译..."

        case "cached":
            isCached = true
            streamProgress = "缓存命中！"

        case "translating":
            isCached = false
            streamProgress = "翻译中..."

        case "chunk":
            if let data = event.data.data(using: .utf8),
               let json = try? JSONDecoder().decode([String: String].self, from: data),
               let text = json["text"] {
                outputText += text
            }

        case "done":
            streamProgress = "完成！"
            if let data = event.data.data(using: .utf8),
               let response = try? JSONDecoder().decode(TranslationResponse.self, from: data) {
                updateMetadata(from: response)
            }

        case "error":
            if let data = event.data.data(using: .utf8),
               let json = try? JSONDecoder().decode([String: String].self, from: data),
               let error = json["error"] {
                errorMessage = error
            }

        default:
            break
        }
    }
}
```

**3. 更新 TranslationView UI**

在 `Sources/MacCortexApp/TranslationView.swift` 添加流式模式切换：

```swift
// Sources/MacCortexApp/TranslationView.swift

struct TranslationView: View {
    @StateObject private var viewModel = TranslationViewModel()
    @State private var useStreaming = false  // 流式模式开关

    var body: some View {
        VStack(spacing: 0) {
            // 工具栏
            HStack {
                // 语言选择器（现有代码）
                // ...

                Spacer()

                // 流式模式开关
                Toggle("流式输出", isOn: $useStreaming)
                    .font(.caption)
                    .help("启用逐字显示效果")
            }
            .padding()

            // 输出区域
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("翻译结果:")
                        .font(.headline)

                    if viewModel.isStreaming {
                        ProgressView()
                            .scaleEffect(0.7)
                        Text(viewModel.streamProgress)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                // 输出文本（流式显示时有闪烁光标）
                ScrollView {
                    Text(viewModel.outputText)
                        .font(.body)
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding()
                        .overlay(
                            Group {
                                if viewModel.isStreaming {
                                    // 闪烁光标
                                    Rectangle()
                                        .fill(Color.blue)
                                        .frame(width: 2, height: 20)
                                        .opacity(viewModel.isStreaming ? 1 : 0)
                                        .animation(.easeInOut(duration: 0.5).repeatForever(), value: viewModel.isStreaming)
                                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
                                        .padding(.leading, 5)
                                }
                            }
                        )
                }
                .frame(minHeight: 150)
            }
            .padding()
        }
    }
}
```

**交付物**:
- `Sources/MacCortexApp/Network/SSEClient.swift`（SSE 客户端）
- `Sources/MacCortexApp/ViewModels/TranslationViewModel.swift`（流式支持）
- `Sources/MacCortexApp/TranslationView.swift`（UI 更新）

---

## Week 3 Day 3: 剪贴板监听（可选功能）

### 目标

实现**剪贴板自动检测**，当用户复制文本时，MacCortex 可自动翻译（可选功能，默认关闭）。

### 技术方案

**NSPasteboard 监听**:
- 使用 Timer 定期检查剪贴板
- 检测到新内容时自动翻译
- 用户可在设置中开关

### 任务清单

**1. 创建剪贴板监听服务**

在 `Sources/MacCortexApp/Services/ClipboardMonitor.swift`:

```swift
// Sources/MacCortexApp/Services/ClipboardMonitor.swift

import AppKit
import Combine

class ClipboardMonitor: ObservableObject {
    @Published var latestText: String = ""
    @Published var isMonitoring: Bool = false

    private var timer: Timer?
    private var lastChangeCount: Int = 0
    private var pasteboard = NSPasteboard.general

    func startMonitoring() {
        guard !isMonitoring else { return }

        isMonitoring = true
        lastChangeCount = pasteboard.changeCount

        // 每 0.5 秒检查一次剪贴板
        timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            self?.checkClipboard()
        }
    }

    func stopMonitoring() {
        timer?.invalidate()
        timer = nil
        isMonitoring = false
    }

    private func checkClipboard() {
        let currentCount = pasteboard.changeCount

        if currentCount != lastChangeCount {
            lastChangeCount = currentCount

            if let text = pasteboard.string(forType: .string),
               !text.isEmpty,
               text != latestText {
                latestText = text
            }
        }
    }

    deinit {
        stopMonitoring()
    }
}
```

**2. 集成到 TranslationViewModel**

```swift
// Sources/MacCortexApp/ViewModels/TranslationViewModel.swift

@MainActor
class TranslationViewModel: ObservableObject {
    // ... 现有属性 ...

    @Published var clipboardMonitorEnabled: Bool = false {
        didSet {
            if clipboardMonitorEnabled {
                clipboardMonitor.startMonitoring()
            } else {
                clipboardMonitor.stopMonitoring()
            }
        }
    }

    private var clipboardMonitor = ClipboardMonitor()
    private var cancellables = Set<AnyCancellable>()

    init() {
        // 监听剪贴板变化
        clipboardMonitor.$latestText
            .debounce(for: .milliseconds(500), scheduler: RunLoop.main)
            .removeDuplicates()
            .sink { [weak self] text in
                guard let self = self, !text.isEmpty else { return }

                // 自动填充输入框
                self.inputText = text

                // 自动翻译（如果启用）
                Task {
                    await self.translate()
                }
            }
            .store(in: &cancellables)
    }
}
```

**3. 添加设置开关**

在 `Sources/MacCortexApp/Views/SettingsView.swift`:

```swift
// Sources/MacCortexApp/Views/SettingsView.swift

struct SettingsView: View {
    @AppStorage("clipboardMonitoring") private var clipboardMonitoring = false
    @AppStorage("autoTranslate") private var autoTranslate = false

    var body: some View {
        Form {
            Section("剪贴板监听") {
                Toggle("启用剪贴板监听", isOn: $clipboardMonitoring)
                    .help("自动检测复制的文本")

                if clipboardMonitoring {
                    Toggle("自动翻译", isOn: $autoTranslate)
                        .help("检测到新文本时自动翻译")
                }
            }

            Section("隐私说明") {
                Text("剪贴板监听仅在应用运行时有效，所有数据仅存储在本地。")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .formStyle(.grouped)
        .frame(width: 500, height: 300)
    }
}
```

**交付物**:
- `Sources/MacCortexApp/Services/ClipboardMonitor.swift`
- `Sources/MacCortexApp/Views/SettingsView.swift`

---

## Week 3 Day 4: 悬浮窗口（Apple Intelligence 风格）

### 目标

实现**快速翻译悬浮窗**，类似 Apple Intelligence 的浮动面板。

### 界面设计

```
┌─────────────────────────────────────┐
│ MacCortex 快速翻译           [×]    │
├─────────────────────────────────────┤
│ [自动检测 ▼] → [English ▼]         │
├─────────────────────────────────────┤
│ Hello, how are you?                 │
│                                     │
│ ----------------------------------- │
│                                     │
│ 你好，你好吗？                      │
└─────────────────────────────────────┘
```

### 技术方案

**NSPanel + SwiftUI**:
- NSPanel（悬浮窗口）
- .utility 级别（始终在最上层）
- 半透明毛玻璃效果
- 快捷键唤起（Cmd+Shift+T）

### 任务清单

**1. 创建悬浮窗口**

在 `Sources/MacCortexApp/Views/FloatingPanel.swift`:

```swift
// Sources/MacCortexApp/Views/FloatingPanel.swift

import SwiftUI
import AppKit

class FloatingPanelController: NSWindowController {
    init() {
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 400, height: 300),
            styleMask: [.titled, .closable, .nonactivatingPanel, .resizable, .utilityWindow],
            backing: .buffered,
            defer: false
        )

        panel.title = "MacCortex 快速翻译"
        panel.isFloatingPanel = true
        panel.level = .floating
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.hasShadow = true
        panel.titlebarAppearsTransparent = true

        // SwiftUI 内容
        let contentView = FloatingTranslationView()
        panel.contentView = NSHostingView(rootView: contentView)

        super.init(window: panel)

        // 居中显示
        panel.center()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    func show() {
        window?.makeKeyAndOrderFront(nil)
        window?.orderFrontRegardless()
    }

    func hide() {
        window?.orderOut(nil)
    }
}

struct FloatingTranslationView: View {
    @StateObject private var viewModel = TranslationViewModel()

    var body: some View {
        VStack(spacing: 0) {
            // 语言选择器（简化版）
            HStack {
                Picker("", selection: $viewModel.sourceLanguage) {
                    ForEach(Language.allCases.prefix(5)) { lang in
                        Text(lang.flag).tag(lang)
                    }
                }
                .labelsHidden()
                .frame(width: 100)

                Image(systemName: "arrow.right")
                    .font(.caption)

                Picker("", selection: $viewModel.targetLanguage) {
                    ForEach(Language.allCases.filter { $0 != .auto }.prefix(5)) { lang in
                        Text(lang.flag).tag(lang)
                    }
                }
                .labelsHidden()
                .frame(width: 100)
            }
            .padding()

            Divider()

            // 输入区
            TextEditor(text: $viewModel.inputText)
                .font(.body)
                .frame(height: 80)
                .padding(8)

            Divider()

            // 输出区
            ScrollView {
                Text(viewModel.outputText)
                    .font(.body)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(8)
            }
            .frame(height: 80)

            Divider()

            // 操作按钮
            HStack {
                if viewModel.isTranslating {
                    ProgressView()
                        .scaleEffect(0.7)
                }

                Spacer()

                Button("复制") {
                    NSPasteboard.general.clearContents()
                    NSPasteboard.general.setString(viewModel.outputText, forType: .string)
                }
                .disabled(viewModel.outputText.isEmpty)

                Button("翻译") {
                    Task {
                        await viewModel.translate()
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.inputText.isEmpty || viewModel.isTranslating)
            }
            .padding()
        }
        .frame(width: 400, height: 300)
        .background(VisualEffectView(material: .hudWindow, blendingMode: .behindWindow))
    }
}

// 毛玻璃效果
struct VisualEffectView: NSViewRepresentable {
    let material: NSVisualEffectView.Material
    let blendingMode: NSVisualEffectView.BlendingMode

    func makeNSView(context: Context) -> NSVisualEffectView {
        let view = NSVisualEffectView()
        view.material = material
        view.blendingMode = blendingMode
        view.state = .active
        return view
    }

    func updateNSView(_ nsView: NSVisualEffectView, context: Context) {}
}
```

**2. 集成到主应用**

在 `Sources/MacCortexApp/MacCortexApp.swift`:

```swift
// Sources/MacCortexApp/MacCortexApp.swift

@main
struct MacCortexApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        // 主窗口
        WindowGroup {
            MainView()
                .environmentObject(appState)
        }
        .commands {
            CommandGroup(replacing: .newItem) {
                Button("快速翻译") {
                    appState.showFloatingPanel()
                }
                .keyboardShortcut("t", modifiers: [.command, .shift])
            }
        }

        // 设置窗口
        Settings {
            SettingsView()
        }
    }
}

@MainActor
class AppState: ObservableObject {
    private var floatingPanel: FloatingPanelController?

    func showFloatingPanel() {
        if floatingPanel == nil {
            floatingPanel = FloatingPanelController()
        }
        floatingPanel?.show()
    }

    func hideFloatingPanel() {
        floatingPanel?.hide()
    }
}
```

**交付物**:
- `Sources/MacCortexApp/Views/FloatingPanel.swift`
- `Sources/MacCortexApp/MacCortexApp.swift`（更新）

---

## Week 3 Day 5: 全局快捷键 + 偏好设置

### 目标

实现**全局快捷键**（任何应用中唤起）和**完整的偏好设置**。

### 任务清单

**1. 全局快捷键（使用 CGEvent）**

在 `Sources/MacCortexApp/Services/GlobalHotKey.swift`:

```swift
// Sources/MacCortexApp/Services/GlobalHotKey.swift

import Carbon
import AppKit

class GlobalHotKeyManager {
    static let shared = GlobalHotKeyManager()

    private var hotKeyRef: EventHotKeyRef?
    private var eventHandler: EventHandlerRef?

    var onHotKeyPressed: (() -> Void)?

    func register(keyCode: UInt32, modifiers: UInt32) {
        unregister()

        let hotKeyID = EventHotKeyID(signature: FourCharCode(bitPattern: 0x4D414378), id: 1)
        var eventType = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))

        InstallEventHandler(GetApplicationEventTarget(), { (_, event, userData) -> OSStatus in
            GlobalHotKeyManager.shared.onHotKeyPressed?()
            return noErr
        }, 1, &eventType, nil, &eventHandler)

        RegisterEventHotKey(keyCode, modifiers, hotKeyID, GetApplicationEventTarget(), 0, &hotKeyRef)
    }

    func unregister() {
        if let hotKeyRef = hotKeyRef {
            UnregisterEventHotKey(hotKeyRef)
            self.hotKeyRef = nil
        }

        if let eventHandler = eventHandler {
            RemoveEventHandler(eventHandler)
            self.eventHandler = nil
        }
    }
}

// 使用示例
// GlobalHotKeyManager.shared.register(keyCode: 17, modifiers: cmdKey | shiftKey)  // Cmd+Shift+T
// GlobalHotKeyManager.shared.onHotKeyPressed = {
//     // 显示悬浮窗
// }
```

**2. 完整偏好设置**

在 `Sources/MacCortexApp/Views/SettingsView.swift`:

```swift
// Sources/MacCortexApp/Views/SettingsView.swift

struct SettingsView: View {
    var body: some View {
        TabView {
            GeneralSettingsView()
                .tabItem {
                    Label("通用", systemImage: "gearshape")
                }

            ClipboardSettingsView()
                .tabItem {
                    Label("剪贴板", systemImage: "doc.on.clipboard")
                }

            ShortcutsSettingsView()
                .tabItem {
                    Label("快捷键", systemImage: "command")
                }

            AdvancedSettingsView()
                .tabItem {
                    Label("高级", systemImage: "slider.horizontal.3")
                }
        }
        .frame(width: 600, height: 400)
    }
}

struct GeneralSettingsView: View {
    @AppStorage("defaultSourceLanguage") private var defaultSource = "auto"
    @AppStorage("defaultTargetLanguage") private var defaultTarget = "en-US"
    @AppStorage("defaultStyle") private var defaultStyle = "formal"
    @AppStorage("useStreaming") private var useStreaming = true

    var body: some View {
        Form {
            Section("默认设置") {
                Picker("默认源语言", selection: $defaultSource) {
                    ForEach(Language.allCases) { lang in
                        Text(lang.displayName).tag(lang.code)
                    }
                }

                Picker("默认目标语言", selection: $defaultTarget) {
                    ForEach(Language.allCases.filter { $0 != .auto }) { lang in
                        Text(lang.displayName).tag(lang.code)
                    }
                }

                Picker("默认风格", selection: $defaultStyle) {
                    Text("正式").tag("formal")
                    Text("轻松").tag("casual")
                    Text("技术").tag("technical")
                }
            }

            Section("翻译模式") {
                Toggle("启用流式输出", isOn: $useStreaming)
                    .help("逐字显示翻译结果")
            }
        }
        .formStyle(.grouped)
    }
}

struct ClipboardSettingsView: View {
    @AppStorage("clipboardMonitoring") private var monitoring = false
    @AppStorage("autoTranslate") private var autoTranslate = false
    @AppStorage("showNotifications") private var notifications = true

    var body: some View {
        Form {
            Section("剪贴板监听") {
                Toggle("启用剪贴板监听", isOn: $monitoring)
                Toggle("自动翻译", isOn: $autoTranslate)
                    .disabled(!monitoring)
                Toggle("显示通知", isOn: $notifications)
                    .disabled(!monitoring)
            }

            Section("隐私说明") {
                Text("剪贴板监听仅在应用运行时有效，所有数据仅存储在本地，不会上传到任何服务器。")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .formStyle(.grouped)
    }
}

struct ShortcutsSettingsView: View {
    var body: some View {
        Form {
            Section("全局快捷键") {
                HStack {
                    Text("快速翻译")
                    Spacer()
                    Text("⌘⇧T")
                        .font(.system(.body, design: .monospaced))
                        .foregroundColor(.secondary)
                }
            }

            Section("应用内快捷键") {
                Group {
                    shortcutRow("刷新", "⌘R")
                    shortcutRow("翻译", "⌘↩")
                    shortcutRow("复制结果", "⌘C")
                    shortcutRow("清空输入", "⌘⌫")
                    shortcutRow("交换语言", "⌘⇧X")
                    shortcutRow("显示历史", "⌘H")
                }
            }
        }
        .formStyle(.grouped)
    }

    private func shortcutRow(_ label: String, _ key: String) -> some View {
        HStack {
            Text(label)
            Spacer()
            Text(key)
                .font(.system(.body, design: .monospaced))
                .foregroundColor(.secondary)
        }
    }
}

struct AdvancedSettingsView: View {
    @AppStorage("backendURL") private var backendURL = "http://localhost:8000"
    @AppStorage("requestTimeout") private var timeout = 30.0
    @AppStorage("cacheEnabled") private var cacheEnabled = true

    var body: some View {
        Form {
            Section("Backend 配置") {
                TextField("Backend URL", text: $backendURL)
                    .help("MacCortex Backend 地址")

                Slider(value: $timeout, in: 10...120, step: 5) {
                    Text("请求超时: \(Int(timeout)) 秒")
                }
            }

            Section("性能") {
                Toggle("启用缓存", isOn: $cacheEnabled)
                    .help("缓存翻译结果以提升速度")
            }

            Section("诊断") {
                Button("测试 Backend 连接") {
                    Task {
                        await testBackendConnection()
                    }
                }

                Button("清空缓存") {
                    clearCache()
                }
            }
        }
        .formStyle(.grouped)
    }

    private func testBackendConnection() async {
        // TODO: 实现连接测试
    }

    private func clearCache() {
        // TODO: 实现缓存清空
    }
}
```

**交付物**:
- `Sources/MacCortexApp/Services/GlobalHotKey.swift`
- `Sources/MacCortexApp/Views/SettingsView.swift`（完整版）

---

## 验收标准（17 项）

| # | 验收项 | 测试方法 | 期望结果 | 优先级 |
|---|--------|----------|----------|--------|
| **流式输出** | | | | |
| 1 | Backend SSE 端点可用 | curl 测试 | 逐行返回事件 | P0 |
| 2 | GUI 流式显示正常 | 手动测试 | 逐字显示翻译 | P0 |
| 3 | 缓存命中流式播放 | 翻译相同文本 | 模拟打字效果 | P0 |
| 4 | 流式错误处理 | 断网测试 | 错误提示清晰 | P0 |
| **剪贴板监听** | | | | |
| 5 | 剪贴板检测正常 | 复制文本 | 自动填充输入框 | P1 |
| 6 | 自动翻译可用 | 启用后复制 | 自动翻译 | P1 |
| 7 | 监听可开关 | 设置中切换 | 立即生效 | P1 |
| **悬浮窗口** | | | | |
| 8 | 悬浮窗可唤起 | Cmd+Shift+T | 窗口显示 | P0 |
| 9 | 悬浮窗始终在上 | 切换其他应用 | 仍可见 | P0 |
| 10 | 悬浮窗翻译功能 | 输入文本翻译 | 正常工作 | P0 |
| 11 | 毛玻璃效果 | 视觉检查 | 半透明 | P1 |
| **快捷键** | | | | |
| 12 | 全局快捷键注册 | 应用启动后 | 快捷键可用 | P0 |
| 13 | Cmd+Shift+T 唤起 | 任何应用中按下 | 悬浮窗显示 | P0 |
| 14 | 快捷键冲突处理 | 与其他应用冲突 | 提示用户 | P1 |
| **偏好设置** | | | | |
| 15 | 设置窗口可打开 | Cmd+, | 窗口显示 | P0 |
| 16 | 设置可保存 | 修改后重启 | 保持修改 | P0 |
| 17 | 设置立即生效 | 修改设置 | 无需重启 | P1 |

**通过条件**: P0 必须 11/11 通过，P1 至少 4/6 通过

---

## 性能目标

| 指标 | Week 2 | Week 3 目标 | 提升 |
|------|--------|-------------|------|
| **流式首字延迟** | - | **< 200ms** | - |
| **剪贴板检测延迟** | - | **< 500ms** | - |
| **悬浮窗唤起时间** | - | **< 100ms** | - |
| **设置保存延迟** | - | **< 50ms** | - |

---

## 风险评估

| 风险 | 概率 | 影响 | 缓解策略 | 残余风险 |
|------|------|------|----------|----------|
| **SSE 连接不稳定** | 30% | 中 | 添加重连机制 + 降级到轮询 | 🟡 中 |
| **全局快捷键冲突** | 40% | 低 | 允许用户自定义快捷键 | 🟢 低 |
| **剪贴板隐私争议** | 20% | 中 | 默认关闭 + 明确隐私说明 | 🟢 低 |
| **悬浮窗性能差** | 10% | 低 | SwiftUI Instruments 优化 | 🟢 低 |
| **设置不生效** | 5% | 中 | 完整的集成测试 | 🟢 低 |

**总体风险评分**: 🟢 **可控**（无高残余风险）

---

## 下一步（Week 4）

### 性能优化 + 智能识别

1. **深度性能优化**（Day 16-18）
   - Pattern 响应 < 1s（p50）
   - 启动时间 < 1s
   - 内存占用 < 100 MB

2. **智能场景识别**（Day 19）
   - 意图分类器
   - Pattern 自动推荐

3. **Phase 3 总结**（Day 20）
   - 完整验收报告
   - Git Tag: phase-3-complete

---

**计划状态**: ⏳ 待执行
**创建时间**: 2026-01-22
**基于**: Week 2 完成状态 + PHASE_3_PLAN.md
**执行人**: Claude Code (Sonnet 4.5)
**预计完成**: 2026-01-26（5 天后）
