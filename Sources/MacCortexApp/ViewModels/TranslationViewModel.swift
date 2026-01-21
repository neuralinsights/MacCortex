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

    // MARK: - Private Properties

    private let client = BackendClient.shared
    private var debounceTimer: Timer?
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization

    init() {
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

        // 检查 Backend 连接
        Task {
            await checkBackendConnection()
        }
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
}
