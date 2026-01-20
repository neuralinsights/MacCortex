// MacCortex PatternKit - Extract Pattern
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20
//
// 从文本中提取结构化信息

import Foundation

/// 提取 Pattern
///
/// 从非结构化文本中提取结构化信息（日期、人名、地点、联系方式等）
public class ExtractPattern: AIPattern {
    public let id = "extract"
    public let name = "Extract"
    public let description = "Extract structured information from unstructured text"
    public let version = "1.0.0"
    public let type: PatternType = .python

    // MARK: - Configuration

    /// 提取类型
    public enum ExtractionType: String {
        case dates = "dates"           // 日期
        case names = "names"           // 人名
        case locations = "locations"   // 地点
        case contacts = "contacts"     // 联系方式（email、电话）
        case urls = "urls"             // 网址
        case numbers = "numbers"       // 数字/金额
        case keywords = "keywords"     // 关键词
        case entities = "entities"     // 命名实体（综合）
        case custom = "custom"         // 自定义模式
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
        let types = extractTypes(from: input.parameters)
        let customPattern = input.parameters["custom_pattern"] as? String

        // TODO: 实际调用 Python 后端
        let extracted = try await performExtraction(
            text: input.text,
            types: types,
            customPattern: customPattern
        )

        let duration = Date().timeIntervalSince(startTime)

        return PatternResult(
            output: extracted,
            metadata: [
                "types": types.map { $0.rawValue },
                "has_custom_pattern": customPattern != nil
            ],
            duration: duration,
            success: true
        )
    }

    // MARK: - Private Methods

    private func extractTypes(from parameters: [String: Any]) -> [ExtractionType] {
        // 如果指定了类型，使用指定的
        if let typesStr = parameters["types"] as? [String] {
            return typesStr.compactMap { ExtractionType(rawValue: $0) }
        }

        // 如果指定了单个类型
        if let typeStr = parameters["type"] as? String,
           let type = ExtractionType(rawValue: typeStr) {
            return [type]
        }

        // 默认提取所有实体
        return [.entities]
    }

    private func performExtraction(
        text: String,
        types: [ExtractionType],
        customPattern: String?
    ) async throws -> String {
        // TODO: 集成 Python 后端（Day 8-9）
        // 当前返回模拟结果

        // 模拟处理延迟
        try await Task.sleep(nanoseconds: 150_000_000) // 0.15 秒

        var results: [String] = []

        for type in types {
            switch type {
            case .dates:
                results.append("日期: [待 Python 后端实现]")
            case .names:
                results.append("人名: [待 Python 后端实现]")
            case .locations:
                results.append("地点: [待 Python 后端实现]")
            case .contacts:
                results.append("联系方式: [待 Python 后端实现]")
            case .urls:
                results.append("网址: [待 Python 后端实现]")
            case .numbers:
                results.append("数字: [待 Python 后端实现]")
            case .keywords:
                results.append("关键词: [待 Python 后端实现]")
            case .entities:
                results.append("实体: [待 Python 后端实现]")
            case .custom:
                if let pattern = customPattern {
                    results.append("自定义模式 '\(pattern)': [待 Python 后端实现]")
                }
            }
        }

        return results.joined(separator: "\n")
    }
}
