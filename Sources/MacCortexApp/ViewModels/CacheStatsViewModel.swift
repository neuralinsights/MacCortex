//
//  CacheStatsViewModel.swift
//  MacCortex
//
//  Phase 3 Week 2 Day 5 - 缓存统计业务逻辑
//  Created on 2026-01-22
//

import SwiftUI
import Combine

@MainActor
class CacheStatsViewModel: ObservableObject {
    // MARK: - Published Properties

    // 缓存统计
    @Published var cacheSize: Int = 0
    @Published var maxSize: Int = 1000
    @Published var totalHits: Int = 0
    @Published var totalMisses: Int = 0
    @Published var totalEvictions: Int = 0
    @Published var hitRate: Double = 0.0
    @Published var timeSaved: Double = 0.0
    @Published var ttl: Int = 3600

    // 历史记录（从 TranslationViewModel 共享）
    @Published var translationHistory: [TranslationHistory] = []

    // UI 状态
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var lastUpdateTime: Date?

    // MARK: - Private Properties

    private let client = BackendClient.shared
    private var refreshTimer: Timer?

    // MARK: - Initialization

    init() {
        // 启动自动刷新（每 5 秒）
        startAutoRefresh()

        // 首次加载
        Task {
            await fetchCacheStats()
        }
    }

    deinit {
        Task { @MainActor in
            stopAutoRefresh()
        }
    }

    // MARK: - Public Methods

    /// 获取缓存统计
    func fetchCacheStats() async {
        isLoading = true
        errorMessage = nil

        do {
            // 调用健康检查接口获取基础信息
            let isHealthy = try await client.checkHealth()

            if isHealthy {
                // TODO: 需要 Backend 提供专门的缓存统计 API
                // 目前从 translate API 的 metadata 中获取
                // 这里做一个测试翻译来获取缓存统计
                let response = try await client.translate(
                    text: "_cache_stats_probe_",
                    targetLanguage: "en-US",
                    style: "formal"
                )

                if let metadata = response.metadata,
                   let stats = metadata.cache_stats {
                    updateStats(from: stats)
                    lastUpdateTime = Date()
                }
            }
        } catch {
            errorMessage = "获取缓存统计失败: \(error.localizedDescription)"
        }

        isLoading = false
    }

    /// 清空缓存
    func clearCache() async {
        // TODO: 需要 Backend 提供清空缓存 API
        // 当前无法实现，仅显示提示
        errorMessage = "清空缓存功能将在后续版本实现"

        // 清空本地统计（模拟）
        cacheSize = 0
        totalHits = 0
        totalMisses = 0
        totalEvictions = 0
        hitRate = 0.0
        timeSaved = 0.0
    }

    /// 刷新统计
    func refresh() async {
        await fetchCacheStats()
    }

    /// 启动自动刷新
    func startAutoRefresh() {
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.fetchCacheStats()
            }
        }
    }

    /// 停止自动刷新
    func stopAutoRefresh() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }

    /// 导出历史记录为 CSV
    func exportHistoryCSV() {
        let csvContent = translationHistory.map { item in
            let timestamp = item.formattedTime
            let sourceLang = item.sourceLanguage.displayName
            let targetLang = item.targetLanguage.displayName
            let style = item.style.displayName
            let cached = item.cached ? "是" : "否"
            let duration = String(format: "%.3f", item.duration)
            let source = escapedCSV(item.sourceText)
            let translated = escapedCSV(item.translatedText)

            return "\"\(timestamp)\",\"\(sourceLang)\",\"\(targetLang)\",\"\(style)\",\"\(cached)\",\"\(duration)\",\"\(source)\",\"\(translated)\""
        }.joined(separator: "\n")

        let header = "\"时间\",\"源语言\",\"目标语言\",\"风格\",\"缓存\",\"耗时(s)\",\"原文\",\"译文\"\n"
        saveToFile(content: header + csvContent, filename: "translation_history.csv")
    }

    /// 导出统计报告为 JSON
    func exportStatsJSON() {
        let report: [String: Any] = [
            "timestamp": ISO8601DateFormatter().string(from: Date()),
            "cache_stats": [
                "cache_size": cacheSize,
                "max_size": maxSize,
                "hits": totalHits,
                "misses": totalMisses,
                "evictions": totalEvictions,
                "hit_rate": hitRate,
                "ttl_seconds": ttl,
                "time_saved_seconds": timeSaved
            ],
            "history": translationHistory.map { item in
                [
                    "timestamp": item.timestamp.timeIntervalSince1970,
                    "source_language": item.sourceLanguage.code,
                    "target_language": item.targetLanguage.code,
                    "style": item.style.rawValue,
                    "cached": item.cached,
                    "duration": item.duration,
                    "source_text": item.sourceText,
                    "translated_text": item.translatedText
                ]
            }
        ]

        do {
            let data = try JSONSerialization.data(withJSONObject: report, options: .prettyPrinted)
            if let jsonString = String(data: data, encoding: .utf8) {
                saveToFile(content: jsonString, filename: "cache_stats_report.json")
            }
        } catch {
            errorMessage = "导出失败: \(error.localizedDescription)"
        }
    }

    // MARK: - Private Methods

    /// 更新统计信息
    private func updateStats(from stats: CacheStats) {
        cacheSize = stats.cache_size
        maxSize = stats.max_size
        totalHits = stats.hits
        totalMisses = stats.misses
        totalEvictions = stats.evictions
        hitRate = stats.hit_rate * 100
        ttl = stats.ttl_seconds ?? 3600

        // 计算节省时间（假设未缓存平均 2.5 秒）
        timeSaved = Double(totalHits) * 2.5
    }

    /// CSV 转义
    private func escapedCSV(_ text: String) -> String {
        return text.replacingOccurrences(of: "\"", with: "\"\"")
    }

    /// 保存到文件
    private func saveToFile(content: String, filename: String) {
        let panel = NSSavePanel()
        panel.allowedContentTypes = filename.hasSuffix(".csv") ? [.commaSeparatedText] : [.json]
        panel.nameFieldStringValue = filename

        panel.begin { response in
            if response == .OK, let url = panel.url {
                do {
                    try content.write(to: url, atomically: true, encoding: .utf8)
                } catch {
                    self.errorMessage = "保存失败: \(error.localizedDescription)"
                }
            }
        }
    }
}
