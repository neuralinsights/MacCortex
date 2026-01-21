//
//  TranslationModels.swift
//  MacCortex
//
//  Phase 3 Week 2 Day 1 - 翻译数据模型
//  Created on 2026-01-22
//

import Foundation

/// 翻译统计信息
struct TranslationStats {
    let duration: Double
    let hitRate: Double
    let timeSaved: Double
    let cacheSize: Int
    let totalHits: Int
    let totalMisses: Int
}

/// 翻译历史记录
struct TranslationHistory: Identifiable {
    let id: UUID
    let timestamp: Date
    let sourceText: String
    let translatedText: String
    let sourceLanguage: Language
    let targetLanguage: Language
    let style: TranslationStyle
    let duration: Double
    let cached: Bool

    init(
        id: UUID = UUID(),
        timestamp: Date = Date(),
        sourceText: String,
        translatedText: String,
        sourceLanguage: Language,
        targetLanguage: Language,
        style: TranslationStyle,
        duration: Double,
        cached: Bool
    ) {
        self.id = id
        self.timestamp = timestamp
        self.sourceText = sourceText
        self.translatedText = translatedText
        self.sourceLanguage = sourceLanguage
        self.targetLanguage = targetLanguage
        self.style = style
        self.duration = duration
        self.cached = cached
    }

    /// 时间格式化
    var formattedTime: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MM-dd HH:mm:ss"
        return formatter.string(from: timestamp)
    }

    /// 文本预览（前 30 字符）
    var sourcePreview: String {
        if sourceText.count > 30 {
            return String(sourceText.prefix(30)) + "..."
        }
        return sourceText
    }

    var translatedPreview: String {
        if translatedText.count > 30 {
            return String(translatedText.prefix(30)) + "..."
        }
        return translatedText
    }
}

/// 批量翻译队列项
struct BatchQueueItem: Identifiable {
    let id: UUID
    var text: String
    var isSelected: Bool

    init(id: UUID = UUID(), text: String, isSelected: Bool = true) {
        self.id = id
        self.text = text
        self.isSelected = isSelected
    }
}

/// 批量翻译结果
struct BatchResult: Identifiable {
    let id: UUID
    let originalText: String
    let translatedText: String?
    let success: Bool
    let error: String?
    let cached: Bool

    init(
        id: UUID = UUID(),
        originalText: String,
        translatedText: String?,
        success: Bool,
        error: String? = nil,
        cached: Bool = false
    ) {
        self.id = id
        self.originalText = originalText
        self.translatedText = translatedText
        self.success = success
        self.error = error
        self.cached = cached
    }
}
