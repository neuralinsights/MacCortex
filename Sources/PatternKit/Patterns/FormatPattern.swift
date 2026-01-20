// MacCortex PatternKit - Format Pattern
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20
//
// 文本格式化与转换

import Foundation

/// 格式化 Pattern
///
/// 转换文本格式，包括 Markdown、HTML、JSON、YAML 等格式之间的转换
public class FormatPattern: Pattern {
    public let id = "format"
    public let name = "Format"
    public let description = "Convert text between different formats"
    public let version = "1.0.0"
    public let type: PatternType = .local  // 格式转换可以在本地完成

    // MARK: - Configuration

    /// 支持的格式
    public enum Format: String, CaseIterable {
        case markdown = "markdown"
        case html = "html"
        case plaintext = "plaintext"
        case json = "json"
        case yaml = "yaml"
        case xml = "xml"
        case csv = "csv"

        var displayName: String {
            switch self {
            case .markdown: return "Markdown"
            case .html: return "HTML"
            case .plaintext: return "Plain Text"
            case .json: return "JSON"
            case .yaml: return "YAML"
            case .xml: return "XML"
            case .csv: return "CSV"
            }
        }
    }

    /// 格式化选项
    public struct FormatOptions {
        /// 是否美化输出
        var prettify: Bool = true

        /// 缩进大小
        var indentSize: Int = 2

        /// 是否保留注释
        var preserveComments: Bool = true

        /// 自定义选项
        var custom: [String: Any] = [:]
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
        let sourceFormat = extractSourceFormat(from: input.parameters)
        let targetFormat = extractTargetFormat(from: input.parameters)
        let options = extractOptions(from: input.parameters)

        // 执行格式转换
        let formatted = try await performFormatConversion(
            text: input.text,
            from: sourceFormat,
            to: targetFormat,
            options: options
        )

        let duration = Date().timeIntervalSince(startTime)

        return PatternResult(
            output: formatted,
            metadata: [
                "source_format": sourceFormat.rawValue,
                "target_format": targetFormat.rawValue,
                "prettify": options.prettify,
                "original_length": input.text.count,
                "formatted_length": formatted.count
            ],
            duration: duration,
            success: true
        )
    }

    // MARK: - Private Methods

    private func extractSourceFormat(from parameters: [String: Any]) -> Format {
        guard let formatStr = parameters["source_format"] as? String,
              let format = Format(rawValue: formatStr) else {
            return .markdown // 默认源格式：Markdown
        }
        return format
    }

    private func extractTargetFormat(from parameters: [String: Any]) -> Format {
        guard let formatStr = parameters["target_format"] as? String,
              let format = Format(rawValue: formatStr) else {
            return .html // 默认目标格式：HTML
        }
        return format
    }

    private func extractOptions(from parameters: [String: Any]) -> FormatOptions {
        var options = FormatOptions()

        if let prettify = parameters["prettify"] as? Bool {
            options.prettify = prettify
        }

        if let indentSize = parameters["indent_size"] as? Int {
            options.indentSize = indentSize
        }

        if let preserveComments = parameters["preserve_comments"] as? Bool {
            options.preserveComments = preserveComments
        }

        return options
    }

    private func performFormatConversion(
        text: String,
        from sourceFormat: Format,
        to targetFormat: Format,
        options: FormatOptions
    ) async throws -> String {
        // 如果格式相同，只做美化
        if sourceFormat == targetFormat {
            return prettifyIfNeeded(text, format: sourceFormat, options: options)
        }

        // 格式转换
        switch (sourceFormat, targetFormat) {
        case (.markdown, .html):
            return try convertMarkdownToHTML(text, options: options)

        case (.html, .markdown):
            return try convertHTMLToMarkdown(text, options: options)

        case (.markdown, .plaintext):
            return try convertMarkdownToPlaintext(text)

        case (.json, .yaml):
            return try convertJSONToYAML(text, options: options)

        case (.yaml, .json):
            return try convertYAMLToJSON(text, options: options)

        default:
            // 其他转换暂时返回原文
            return """
            [格式转换: \(sourceFormat.displayName) → \(targetFormat.displayName)]
            (本地格式转换功能开发中)

            原文:
            \(text)
            """
        }
    }

    // MARK: - Format Conversion Helpers

    private func prettifyIfNeeded(_ text: String, format: Format, options: FormatOptions) -> String {
        guard options.prettify else { return text }

        // TODO: 实现各种格式的美化
        return text
    }

    private func convertMarkdownToHTML(_ markdown: String, options: FormatOptions) throws -> String {
        // TODO: 实现 Markdown → HTML 转换
        // 可以使用 Swift Markdown 库或自定义解析器
        return "<p>[Markdown → HTML 转换开发中]</p>"
    }

    private func convertHTMLToMarkdown(_ html: String, options: FormatOptions) throws -> String {
        // TODO: 实现 HTML → Markdown 转换
        return "[HTML → Markdown 转换开发中]"
    }

    private func convertMarkdownToPlaintext(_ markdown: String) throws -> String {
        // 简单移除 Markdown 标记
        var text = markdown

        // 移除标题标记
        text = text.replacingOccurrences(of: #"^#+\s+"#, with: "", options: .regularExpression)

        // 移除粗体、斜体
        text = text.replacingOccurrences(of: #"\*\*([^\*]+)\*\*"#, with: "$1", options: .regularExpression)
        text = text.replacingOccurrences(of: #"\*([^\*]+)\*"#, with: "$1", options: .regularExpression)

        // 移除链接但保留文本
        text = text.replacingOccurrences(of: #"\[([^\]]+)\]\([^\)]+\)"#, with: "$1", options: .regularExpression)

        return text
    }

    private func convertJSONToYAML(_ json: String, options: FormatOptions) throws -> String {
        // TODO: 实现 JSON → YAML 转换
        return "[JSON → YAML 转换开发中]"
    }

    private func convertYAMLToJSON(_ yaml: String, options: FormatOptions) throws -> String {
        // TODO: 实现 YAML → JSON 转换
        return "[YAML → JSON 转换开发中]"
    }
}
