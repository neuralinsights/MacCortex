//
// MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
// Copyright (c) 2026 Yu Geng. All rights reserved.
//
// This source code is proprietary and confidential.
// Unauthorized copying, distribution, or use is strictly prohibited.
//
// Author: Yu Geng <james.geng@gmail.com>
// License: Proprietary
//

// MacCortex PatternKit - Summarize Pattern
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20
//
// 总结文本内容，提取关键信息

import Foundation

/// 总结 Pattern
///
/// 将长文本总结为简洁的摘要，提取关键信息和要点
public class SummarizePattern: AIPattern {
    public let id = "summarize"
    public let name = "Summarize"
    public let description = "Summarize long text into concise key points"
    public let version = "1.0.0"
    public let type: PatternType = .python

    // MARK: - Configuration

    /// 摘要长度（字数）
    public enum SummaryLength: String {
        case short = "short"       // ~50 字
        case medium = "medium"     // ~150 字
        case long = "long"         // ~300 字
    }

    /// 摘要风格
    public enum SummaryStyle: String {
        case bullet = "bullet"     // 要点列表
        case paragraph = "paragraph" // 段落形式
        case headline = "headline" // 标题式
    }

    // MARK: - Initialization

    public init() {}

    // MARK: - Pattern Protocol

    public func execute(input: PatternInput) async throws -> PatternResult {
        let startTime = Date()

        // 验证输入
        guard validate(input: input) else {
            throw PatternError.invalidInput("Text is empty")
        }

        // 提取参数
        let length = extractLength(from: input.parameters)
        let style = extractStyle(from: input.parameters)
        let language = extractLanguage(from: input.parameters)

        // TODO: 实际调用 Python 后端
        // 当前返回模拟结果
        let summary = try await generateSummary(
            text: input.text,
            length: length,
            style: style,
            language: language
        )

        let duration = Date().timeIntervalSince(startTime)

        return PatternResult(
            output: summary,
            metadata: [
                "length": length.rawValue,
                "style": style.rawValue,
                "language": language,
                "original_length": input.text.count
            ],
            duration: duration,
            success: true
        )
    }

    public func validate(input: PatternInput) -> Bool {
        let text = input.text.trimmingCharacters(in: .whitespacesAndNewlines)

        // 1. 最小字符数（防止极端短文本）
        guard text.count >= 10 else { return false }

        // 2. 语言感知的词数检测
        let language = extractLanguage(from: input.parameters)

        // 3. 词数统计（而非字符数）
        let wordCount: Int
        if language.hasPrefix("zh") || language.hasPrefix("ja") || language.hasPrefix("ko") {
            // 中日韩文字：每个字符约等于一个词
            wordCount = text.count
        } else {
            // 西文：按空格分词
            wordCount = text.components(separatedBy: .whitespacesAndNewlines)
                .filter { !$0.isEmpty }
                .count
        }

        // 4. 语言特定的最小词数阈值
        let minWords = language.hasPrefix("zh") ? 15 : 30  // 中文 15 词，英文 30 词

        return wordCount >= minWords
    }

    // MARK: - Private Methods

    private func extractLength(from parameters: [String: Any]) -> SummaryLength {
        guard let lengthStr = parameters["length"] as? String,
              let length = SummaryLength(rawValue: lengthStr) else {
            return .medium // 默认中等长度
        }
        return length
    }

    private func extractStyle(from parameters: [String: Any]) -> SummaryStyle {
        guard let styleStr = parameters["style"] as? String,
              let style = SummaryStyle(rawValue: styleStr) else {
            return .bullet // 默认要点列表
        }
        return style
    }

    private func extractLanguage(from parameters: [String: Any]) -> String {
        // 修复 P1 #6: 添加参数白名单验证
        guard let lang = parameters["language"] as? String else {
            return "zh-CN"  // 类型错误，使用默认值
        }

        // 白名单验证（防止注入攻击）
        let validLanguages: Set<String> = [
            "zh-CN", "zh-TW", "en", "ja", "ko",
            "fr", "de", "es", "ru", "ar", "pt", "it"
        ]

        guard validLanguages.contains(lang) else {
            return "zh-CN"  // 无效语言代码，使用默认值
        }

        return lang
    }

    private func generateSummary(
        text: String,
        length: SummaryLength,
        style: SummaryStyle,
        language: String
    ) async throws -> String {
        // TODO: 集成 Python 后端（Day 8-9）
        // 当前返回简单的模拟结果

        // 模拟处理延迟
        try await Task.sleep(nanoseconds: 100_000_000) // 0.1 秒

        let wordCount: Int
        switch length {
        case .short: wordCount = 50
        case .medium: wordCount = 150
        case .long: wordCount = 300
        }

        // 生成模拟摘要
        switch style {
        case .bullet:
            return """
            • 核心要点 1：[待 Python 后端实现]
            • 核心要点 2：[待 Python 后端实现]
            • 核心要点 3：[待 Python 后端实现]

            (模拟总结，目标长度: \(wordCount) 字)
            """
        case .paragraph:
            return "[待 Python 后端实现] 这是一段总结性的段落文本，将在集成 MLX 和 LangGraph 后实现真实的 AI 总结功能。(目标长度: \(wordCount) 字)"
        case .headline:
            return "[待 Python 后端实现] 核心标题：关键信息摘要"
        }
    }
}
