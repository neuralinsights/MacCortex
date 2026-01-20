// MacCortex PatternKit - Summarize Pattern
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20
//
// 总结文本内容，提取关键信息

import Foundation

/// 总结 Pattern
///
/// 将长文本总结为简洁的摘要，提取关键信息和要点
public class SummarizePattern: Pattern {
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
        // 至少需要 50 个字符才值得总结
        return text.count >= 50
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
        return parameters["language"] as? String ?? "zh-CN" // 默认中文
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
