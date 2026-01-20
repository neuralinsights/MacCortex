// MacCortex PatternKit - Translate Pattern
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20
//
// 文本翻译

import Foundation

/// 翻译 Pattern
///
/// 将文本翻译成目标语言，支持多种语言对
public class TranslatePattern: AIPattern {
    public let id = "translate"
    public let name = "Translate"
    public let description = "Translate text between languages"
    public let version = "1.0.0"
    public let type: PatternType = .python

    // MARK: - Configuration

    /// 支持的语言
    public enum Language: String, CaseIterable {
        case zhCN = "zh-CN"    // 简体中文
        case zhTW = "zh-TW"    // 繁体中文
        case en = "en"         // 英语
        case ja = "ja"         // 日语
        case ko = "ko"         // 韩语
        case fr = "fr"         // 法语
        case de = "de"         // 德语
        case es = "es"         // 西班牙语
        case ru = "ru"         // 俄语
        case ar = "ar"         // 阿拉伯语

        var displayName: String {
            switch self {
            case .zhCN: return "简体中文"
            case .zhTW: return "繁体中文"
            case .en: return "English"
            case .ja: return "日本語"
            case .ko: return "한국어"
            case .fr: return "Français"
            case .de: return "Deutsch"
            case .es: return "Español"
            case .ru: return "Русский"
            case .ar: return "العربية"
            }
        }
    }

    /// 翻译风格
    public enum TranslationStyle: String {
        case formal = "formal"     // 正式
        case casual = "casual"     // 随意
        case technical = "technical" // 技术性
        case literary = "literary" // 文学性
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
        let sourceLanguage = extractSourceLanguage(from: input.parameters)
        let targetLanguage = extractTargetLanguage(from: input.parameters)
        let style = extractStyle(from: input.parameters)

        // 注意：语言对验证已在 validate() 中完成（修复 P0 #3）

        // TODO: 实际调用 Python 后端
        let translated = try await performTranslation(
            text: input.text,
            from: sourceLanguage,
            to: targetLanguage,
            style: style
        )

        let duration = Date().timeIntervalSince(startTime)

        return PatternResult(
            output: translated,
            metadata: [
                "source_language": sourceLanguage.rawValue,
                "target_language": targetLanguage.rawValue,
                "style": style.rawValue,
                "original_length": input.text.count,
                "translated_length": translated.count
            ],
            duration: duration,
            success: true
        )
    }

    public func validate(input: PatternInput) -> Bool {
        let text = input.text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return false }

        // 验证语言对（修复 P0 #3：从 execute() 移到 validate()）
        let sourceLanguage = extractSourceLanguage(from: input.parameters)
        let targetLanguage = extractTargetLanguage(from: input.parameters)

        return sourceLanguage != targetLanguage
    }

    // MARK: - Private Methods

    private func extractSourceLanguage(from parameters: [String: Any]) -> Language {
        guard let langStr = parameters["source_language"] as? String,
              let lang = Language(rawValue: langStr) else {
            return .zhCN // 默认源语言：中文
        }
        return lang
    }

    private func extractTargetLanguage(from parameters: [String: Any]) -> Language {
        guard let langStr = parameters["target_language"] as? String,
              let lang = Language(rawValue: langStr) else {
            return .en // 默认目标语言：英语
        }
        return lang
    }

    private func extractStyle(from parameters: [String: Any]) -> TranslationStyle {
        guard let styleStr = parameters["style"] as? String,
              let style = TranslationStyle(rawValue: styleStr) else {
            return .formal // 默认正式风格
        }
        return style
    }

    private func performTranslation(
        text: String,
        from sourceLanguage: Language,
        to targetLanguage: Language,
        style: TranslationStyle
    ) async throws -> String {
        // TODO: 集成 Python 后端（Day 8-9）
        // 当前返回模拟结果

        // 模拟处理延迟
        try await Task.sleep(nanoseconds: 200_000_000) // 0.2 秒

        return """
        [待 Python 后端实现]
        翻译: \(sourceLanguage.displayName) → \(targetLanguage.displayName)
        风格: \(style.rawValue)
        原文长度: \(text.count) 字符

        (将在集成 MLX 和 LangGraph 后实现真实的翻译功能)
        """
    }

    // MARK: - Public Helpers

    /// 自动检测源语言
    public static func detectLanguage(text: String) -> Language? {
        // TODO: 实现语言检测
        // 当前返回 nil，表示需要用户手动指定
        return nil
    }
}
