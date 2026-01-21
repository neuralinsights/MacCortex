//
//  BatchTranslationViewModel.swift
//  MacCortex
//
//  Phase 3 Week 2 Day 3-4 - 批量翻译业务逻辑
//  Created on 2026-01-22
//

import SwiftUI
import UniformTypeIdentifiers
import Combine

@MainActor
class BatchTranslationViewModel: ObservableObject {
    // MARK: - Published Properties

    @Published var targetLanguage: Language = .english
    @Published var sourceLanguage: Language = .auto
    @Published var style: TranslationStyle = .formal

    // 批量队列
    @Published var queueItems: [BatchQueueItem] = []
    @Published var results: [BatchResult] = []

    // 翻译状态
    @Published var isTranslating: Bool = false
    @Published var isPaused: Bool = false
    @Published var progress: Double = 0.0
    @Published var currentIndex: Int = 0

    // 统计信息
    @Published var totalItems: Int = 0
    @Published var completedItems: Int = 0
    @Published var failedItems: Int = 0
    @Published var cacheHits: Int = 0
    @Published var cacheMisses: Int = 0
    @Published var cacheHitRate: Double = 0.0
    @Published var estimatedTimeRemaining: Double = 0.0
    @Published var totalDuration: Double = 0.0

    @Published var errorMessage: String?

    // MARK: - Private Properties

    private let client = BackendClient.shared
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Public Methods

    /// 添加文本到队列
    func addText(_ text: String) {
        guard !text.isEmpty else { return }
        let item = BatchQueueItem(text: text)
        queueItems.append(item)
        totalItems = queueItems.count
    }

    /// 添加多个文本到队列
    func addTexts(_ texts: [String]) {
        let newItems = texts.filter { !$0.isEmpty }.map { BatchQueueItem(text: $0) }
        queueItems.append(contentsOf: newItems)
        totalItems = queueItems.count
    }

    /// 移除队列项
    func removeItem(_ item: BatchQueueItem) {
        queueItems.removeAll { $0.id == item.id }
        totalItems = queueItems.count
    }

    /// 切换队列项选中状态
    func toggleItemSelection(_ item: BatchQueueItem) {
        if let index = queueItems.firstIndex(where: { $0.id == item.id }) {
            queueItems[index].isSelected.toggle()
        }
    }

    /// 清空队列
    func clearQueue() {
        queueItems.removeAll()
        results.removeAll()
        resetStats()
    }

    /// 从文件导入文本
    func importFromFile(url: URL) async {
        do {
            let content = try String(contentsOf: url, encoding: .utf8)

            // 根据文件类型解析
            let lines: [String]
            if url.pathExtension == "csv" {
                lines = parseCSV(content)
            } else {
                // .txt / .md - 按行分割
                lines = content.components(separatedBy: .newlines)
                    .map { $0.trimmingCharacters(in: .whitespaces) }
                    .filter { !$0.isEmpty }
            }

            addTexts(lines)
        } catch {
            errorMessage = "导入文件失败: \(error.localizedDescription)"
        }
    }

    /// 处理文件拖放
    func handleDrop(providers: [NSItemProvider]) -> Bool {
        for provider in providers {
            if provider.canLoadObject(ofClass: URL.self) {
                _ = provider.loadObject(ofClass: URL.self) { url, error in
                    if let url = url {
                        Task { @MainActor in
                            await self.importFromFile(url: url)
                        }
                    }
                }
                return true
            }
        }
        return false
    }

    /// 开始批量翻译
    func startBatchTranslation() async {
        guard !queueItems.isEmpty else { return }

        isTranslating = true
        isPaused = false
        resetStats()

        let selectedItems = queueItems.filter { $0.isSelected }
        guard !selectedItems.isEmpty else {
            errorMessage = "请至少选择一个条目"
            isTranslating = false
            return
        }

        totalItems = selectedItems.count
        let startTime = Date()

        do {
            // 调用批量 API
            let batchItems = selectedItems.map { item in
                BatchTranslationItem(
                    text: item.text,
                    parameters: [
                        "target_language": targetLanguage.code,
                        "source_language": sourceLanguage.code,
                        "style": style.rawValue
                    ]
                )
            }

            let response = try await client.translateBatch(items: batchItems)

            // 更新结果
            results = response.items.enumerated().map { index, item in
                BatchResult(
                    originalText: selectedItems[index].text,
                    translatedText: item.output,
                    success: item.success,
                    error: item.error,
                    cached: item.metadata?.cached ?? false
                )
            }

            // 更新统计
            completedItems = response.succeeded
            failedItems = response.failed
            cacheHits = response.aggregate_stats.cache_hits
            cacheMisses = response.aggregate_stats.cache_misses
            cacheHitRate = response.aggregate_stats.cache_hit_rate * 100
            totalDuration = response.duration
            progress = 1.0

        } catch {
            errorMessage = "批量翻译失败: \(error.localizedDescription)"

            // 创建失败结果
            results = selectedItems.map { item in
                BatchResult(
                    originalText: item.text,
                    translatedText: nil,
                    success: false,
                    error: error.localizedDescription,
                    cached: false
                )
            }
        }

        isTranslating = false
    }

    /// 暂停翻译
    func pauseTranslation() {
        isPaused = true
    }

    /// 恢复翻译
    func resumeTranslation() {
        isPaused = false
        // TODO: 实现恢复逻辑
    }

    /// 取消翻译
    func cancelTranslation() {
        isTranslating = false
        isPaused = false
    }

    /// 复制结果
    func copyResult(_ result: BatchResult) {
        guard let text = result.translatedText else { return }

        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
    }

    /// 复制所有结果
    func copyAllResults() {
        let allText = results.compactMap { $0.translatedText }.joined(separator: "\n")

        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(allText, forType: .string)
    }

    /// 导出为 CSV
    func exportCSV() {
        let csvContent = results.enumerated().map { index, result in
            let original = escapedCSV(result.originalText)
            let translated = escapedCSV(result.translatedText ?? "")
            let status = result.success ? "成功" : "失败"
            let cached = result.cached ? "是" : "否"
            return "\"\(original)\",\"\(translated)\",\"\(status)\",\"\(cached)\""
        }.joined(separator: "\n")

        let header = "\"原文\",\"译文\",\"状态\",\"缓存\"\n"
        saveToFile(content: header + csvContent, filename: "translations.csv", contentType: .commaSeparatedText)
    }

    /// 导出为 JSON
    func exportJSON() {
        let jsonArray = results.map { result in
            [
                "original": result.originalText,
                "translation": result.translatedText ?? "",
                "success": result.success,
                "cached": result.cached,
                "error": result.error ?? ""
            ] as [String : Any]
        }

        do {
            let data = try JSONSerialization.data(withJSONObject: jsonArray, options: .prettyPrinted)
            if let jsonString = String(data: data, encoding: .utf8) {
                saveToFile(content: jsonString, filename: "translations.json", contentType: .json)
            }
        } catch {
            errorMessage = "JSON 导出失败: \(error.localizedDescription)"
        }
    }

    /// 显示添加文本对话框
    func showAddTextDialog() {
        // 触发弹窗（由 View 处理）
    }

    // MARK: - Private Methods

    /// 重置统计信息
    private func resetStats() {
        progress = 0.0
        currentIndex = 0
        completedItems = 0
        failedItems = 0
        cacheHits = 0
        cacheMisses = 0
        cacheHitRate = 0.0
        estimatedTimeRemaining = 0.0
        totalDuration = 0.0
        errorMessage = nil
        results.removeAll()
    }

    /// 解析 CSV 文件
    private func parseCSV(_ content: String) -> [String] {
        // 简单的 CSV 解析（仅第一列）
        return content.components(separatedBy: .newlines)
            .map { line in
                // 移除引号并取第一列
                let columns = line.components(separatedBy: ",")
                guard let first = columns.first else { return "" }
                return first.trimmingCharacters(in: CharacterSet(charactersIn: "\"").union(.whitespaces))
            }
            .filter { !$0.isEmpty }
    }

    /// CSV 转义
    private func escapedCSV(_ text: String) -> String {
        return text.replacingOccurrences(of: "\"", with: "\"\"")
    }

    /// 保存到文件
    private func saveToFile(content: String, filename: String, contentType: UTType) {
        let panel = NSSavePanel()
        panel.allowedContentTypes = [contentType]
        panel.nameFieldStringValue = filename

        panel.begin { response in
            if response == .OK, let url = panel.url {
                do {
                    try content.write(to: url, atomically: true, encoding: .utf8)
                } catch {
                    self.errorMessage = "保存文件失败: \(error.localizedDescription)"
                }
            }
        }
    }
}
