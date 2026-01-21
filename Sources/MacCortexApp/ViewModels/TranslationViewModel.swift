//
//  TranslationViewModel.swift
//  MacCortex
//
//  Phase 3 Week 2 Day 1-2 - 翻译界面业务逻辑
//  Created on 2026-01-22
//

import SwiftUI
import Combine

@MainActor
class TranslationViewModel: ObservableObject {
    // MARK: - Published Properties

    @Published var sourceLanguage: Language = .auto
    @Published var targetLanguage: Language = .english
    @Published var style: TranslationStyle = .formal

    @Published var inputText: String = ""
    @Published var outputText: String = ""
    @Published var isTranslating: Bool = false
    @Published var isCached: Bool = false
    @Published var stats: TranslationStats?
    @Published var errorMessage: String?

    // 历史记录（最近 20 条）
    @Published var history: [TranslationHistory] = []

    // Phase 3 Week 3 Day 2: 流式翻译支持
    @Published var isStreaming: Bool = false
    @Published var streamProgress: String = ""
    @Published var useStreamingMode: Bool = false  // 流式模式开关

    // Phase 3 Week 3 Day 3: 剪贴板监听支持
    @Published var clipboardMonitorEnabled: Bool = false

    // MARK: - Private Properties

    private let client = BackendClient.shared
    private var debounceTimer: Timer?
    private var cancellables = Set<AnyCancellable>()

    // Phase 3 Week 3 Day 2: SSE 客户端
    private var sseClient: SSEClient?

    // Phase 3 Week 3 Day 3: 剪贴板监听器
    private var clipboardMonitor: ClipboardMonitor?

    // MARK: - Initialization

    init() {
        // Phase 3 Week 3 后续: 从 SettingsManager 加载默认值
        let settings = SettingsManager.shared
        self.sourceLanguage = settings.defaultSourceLanguage
        self.targetLanguage = settings.defaultTargetLanguage
        self.style = settings.defaultStyle
        self.useStreamingMode = settings.defaultUseStreaming
        self.clipboardMonitorEnabled = settings.clipboardMonitorEnabled

        // 监听输入变化（实时翻译）
        $inputText
            .debounce(for: .milliseconds(800), scheduler: RunLoop.main)
            .removeDuplicates()
            .sink { [weak self] _ in
                guard let self = self else { return }
                if !self.inputText.isEmpty && self.inputText.count > 3 {
                    Task {
                        await self.translate()
                    }
                }
            }
            .store(in: &cancellables)

        // 监听设置变化
        settings.$clipboardMonitorEnabled
            .sink { [weak self] isEnabled in
                self?.clipboardMonitorEnabled = isEnabled
            }
            .store(in: &cancellables)

        // 检查 Backend 连接
        Task {
            await checkBackendConnection()
        }

        // Phase 3 Week 3 Day 3: 初始化剪贴板监听器
        setupClipboardMonitor()
    }

    // MARK: - Public Methods

    /// 检查 Backend 连接
    func checkBackendConnection() async {
        do {
            let isHealthy = try await client.checkHealth()
            if !isHealthy {
                errorMessage = "Backend 服务不可用，请启动 Backend 服务"
            }
        } catch {
            errorMessage = "Backend 连接失败: \(error.localizedDescription)"
        }
    }

    /// 执行翻译
    func translate() async {
        guard !inputText.isEmpty else {
            outputText = ""
            stats = nil
            return
        }

        // 检查是否需要翻译（文本未变化）
        if !outputText.isEmpty && inputText == history.first?.sourceText {
            return
        }

        isTranslating = true
        errorMessage = nil

        do {
            let response = try await client.translate(
                text: inputText,
                targetLanguage: targetLanguage.code,
                sourceLanguage: sourceLanguage.code,
                style: style.rawValue
            )

            // 更新输出
            outputText = response.output ?? ""
            isCached = response.metadata?.cached ?? false

            // 更新统计
            if let metadata = response.metadata, let cacheStats = metadata.cache_stats {
                stats = TranslationStats(
                    duration: response.duration,
                    hitRate: cacheStats.hit_rate * 100,
                    timeSaved: Double(cacheStats.hits) * 2.5,
                    cacheSize: cacheStats.cache_size,
                    totalHits: cacheStats.hits,
                    totalMisses: cacheStats.misses
                )
            } else {
                stats = TranslationStats(
                    duration: response.duration,
                    hitRate: 0.0,
                    timeSaved: 0.0,
                    cacheSize: 0,
                    totalHits: 0,
                    totalMisses: 0
                )
            }

            // 添加到历史记录
            addToHistory(
                sourceText: inputText,
                translatedText: outputText,
                duration: response.duration,
                cached: isCached
            )

        } catch {
            errorMessage = "翻译失败: \(error.localizedDescription)"
            outputText = ""
        }

        isTranslating = false
    }

    /// 复制结果到剪贴板
    func copyResult() {
        guard !outputText.isEmpty else { return }

        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(outputText, forType: .string)
    }

    /// 复制输入到剪贴板
    func copyInput() {
        guard !inputText.isEmpty else { return }

        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(inputText, forType: .string)
    }

    /// 清空输入和输出
    func clear() {
        inputText = ""
        outputText = ""
        isCached = false
        stats = nil
        errorMessage = nil
    }

    /// 交换语言
    func swapLanguages() {
        // 如果源语言是自动检测，不执行交换
        guard sourceLanguage != .auto else { return }

        // 交换语言
        let temp = sourceLanguage
        sourceLanguage = targetLanguage
        targetLanguage = temp

        // 交换输入输出文本
        let tempText = inputText
        inputText = outputText
        outputText = tempText

        // 重新翻译
        Task {
            await translate()
        }
    }

    /// 从历史记录加载
    func loadFromHistory(_ item: TranslationHistory) {
        sourceLanguage = item.sourceLanguage
        targetLanguage = item.targetLanguage
        style = item.style
        inputText = item.sourceText
        outputText = item.translatedText

        // 更新统计（使用历史记录的数据）
        stats = TranslationStats(
            duration: item.duration,
            hitRate: item.cached ? 100.0 : 0.0,
            timeSaved: item.cached ? item.duration * 100 : 0.0,
            cacheSize: 0,
            totalHits: 0,
            totalMisses: 0
        )
        isCached = item.cached
    }

    /// 清空历史记录
    func clearHistory() {
        history.removeAll()
    }

    /// 从剪贴板粘贴
    func pasteFromClipboard() {
        let pasteboard = NSPasteboard.general
        if let string = pasteboard.string(forType: .string) {
            inputText = string
        }
    }

    // MARK: - Private Methods

    /// 添加到历史记录
    private func addToHistory(
        sourceText: String,
        translatedText: String,
        duration: Double,
        cached: Bool
    ) {
        let historyItem = TranslationHistory(
            sourceText: sourceText,
            translatedText: translatedText,
            sourceLanguage: sourceLanguage,
            targetLanguage: targetLanguage,
            style: style,
            duration: duration,
            cached: cached
        )

        // 添加到历史记录（最多保留 20 条）
        history.insert(historyItem, at: 0)
        if history.count > 20 {
            history = Array(history.prefix(20))
        }
    }

    // MARK: - Streaming Support (Phase 3 Week 3 Day 2)

    /// 流式翻译
    func translateStream() async {
        guard !inputText.isEmpty else {
            outputText = ""
            stats = nil
            return
        }

        isStreaming = true
        isTranslating = true
        outputText = ""
        streamProgress = ""
        errorMessage = nil

        let url = URL(string: "http://localhost:8000/execute/stream")!

        // 构建请求体
        let requestBody: [String: Any] = [
            "pattern_id": "translate",
            "text": inputText,
            "parameters": [
                "target_language": targetLanguage.code,
                "source_language": sourceLanguage.code,
                "style": style.rawValue
            ]
        ]

        guard let bodyData = try? JSONSerialization.data(withJSONObject: requestBody) else {
            errorMessage = "请求构建失败"
            isStreaming = false
            isTranslating = false
            return
        }

        // 创建 SSE 客户端
        sseClient = SSEClient()

        // 处理 SSE 事件
        sseClient?.onEvent = { [weak self] event in
            Task { @MainActor in
                self?.handleSSEEvent(event)
            }
        }

        // 处理完成
        sseClient?.onComplete = { [weak self] in
            Task { @MainActor in
                self?.isStreaming = false
                self?.isTranslating = false
                self?.streamProgress = "完成！"
            }
        }

        // 处理错误
        sseClient?.onError = { [weak self] error in
            Task { @MainActor in
                self?.errorMessage = "流式翻译失败: \(error.localizedDescription)"
                self?.isStreaming = false
                self?.isTranslating = false
            }
        }

        // 连接并开始接收
        sseClient?.connect(url: url, body: bodyData)
    }

    /// 停止流式翻译
    func stopStreaming() {
        sseClient?.disconnect()
        isStreaming = false
        isTranslating = false
        streamProgress = "已停止"
    }

    /// 处理 SSE 事件
    private func handleSSEEvent(_ event: SSEEvent) {
        switch event.event {
        case "start":
            streamProgress = "开始翻译..."

        case "cached":
            // 缓存命中
            if let data = event.data.data(using: .utf8),
               let json = try? JSONDecoder().decode([String: Any].self, from: data) {
                isCached = json["cached"] as? Bool ?? false
                if isCached {
                    streamProgress = "缓存命中！"
                }
            }

        case "translating":
            isCached = false
            streamProgress = "翻译中..."

        case "chunk":
            // 接收文本片段
            if let data = event.data.data(using: .utf8),
               let json = try? JSONDecoder().decode([String: String].self, from: data),
               let text = json["text"] {
                outputText += text
            }

        case "done":
            // 翻译完成
            streamProgress = "完成！"

            if let data = event.data.data(using: .utf8),
               let json = try? JSONDecoder().decode([String: Any].self, from: data) {

                // 提取完整输出（如果有）
                if let output = json["output"] as? String {
                    outputText = output
                }

                // 提取元数据
                if let metadata = json["metadata"] as? [String: Any] {
                    let cached = metadata["cached"] as? Bool ?? false
                    let mode = metadata["mode"] as? String

                    // 更新统计
                    if let cacheStats = metadata["cache_stats"] as? [String: Any] {
                        stats = TranslationStats(
                            duration: 0.0,  // 流式没有总耗时
                            hitRate: (cacheStats["hit_rate"] as? Double ?? 0.0) * 100,
                            timeSaved: 0.0,
                            cacheSize: cacheStats["cache_size"] as? Int ?? 0,
                            totalHits: cacheStats["hits"] as? Int ?? 0,
                            totalMisses: cacheStats["misses"] as? Int ?? 0
                        )
                    }

                    // 添加到历史记录
                    addToHistory(
                        sourceText: inputText,
                        translatedText: outputText,
                        duration: 0.0,
                        cached: cached
                    )
                }
            }

        case "error":
            // 错误处理
            if let data = event.data.data(using: .utf8),
               let json = try? JSONDecoder().decode([String: String].self, from: data),
               let error = json["error"] {
                errorMessage = error
            }

        default:
            break
        }
    }

    // MARK: - Clipboard Monitoring (Phase 3 Week 3 Day 3)

    /// 设置剪贴板监听器
    private func setupClipboardMonitor() {
        clipboardMonitor = ClipboardMonitor()

        // 监听启用状态变化
        $clipboardMonitorEnabled
            .sink { [weak self] isEnabled in
                guard let self = self else { return }
                self.clipboardMonitor?.isEnabled = isEnabled
            }
            .store(in: &cancellables)

        // 设置剪贴板变化回调
        clipboardMonitor?.onClipboardChange = { [weak self] text in
            Task { @MainActor in
                self?.handleClipboardText(text)
            }
        }
    }

    /// 处理剪贴板文本
    private func handleClipboardText(_ text: String) {
        // 1. 自动填充输入框
        inputText = text

        // 2. 自动触发翻译（根据流式模式选择）
        Task {
            if useStreamingMode {
                await translateStream()
            } else {
                await translate()
            }
        }
    }

    /// 切换剪贴板监听状态
    func toggleClipboardMonitor() {
        clipboardMonitorEnabled.toggle()
    }
}

// MARK: - Helper Extensions

extension JSONDecoder {
    func decode<T>(_ type: T.Type, from data: Data) throws -> T where T: Decodable {
        return try self.decode(type, from: data)
    }
}
