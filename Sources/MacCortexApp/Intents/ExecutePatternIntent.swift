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

// ExecutePatternIntent - 执行 Pattern Intent（供 Shortcuts 调用）
// Phase 2 Week 3 Day 13-14: Shortcuts 自动化集成
// 创建时间：2026-01-21

import AppIntents
import Foundation

/// 执行 Pattern Intent（供 macOS Shortcuts 调用）
@available(macOS 13.0, *)
struct ExecutePatternIntent: AppIntent {
    static var title: LocalizedStringResource = "执行 MacCortex Pattern"
    static var description = IntentDescription("使用 MacCortex Pattern 处理文本（总结、翻译、提取等）")

    static var openAppWhenRun: Bool = false // Shortcuts 后台运行，无需打开 App

    // MARK: - 参数定义

    @Parameter(title: "Pattern ID", description: "Pattern 类型：summarize, translate, extract, format, search")
    var patternId: String

    @Parameter(title: "输入文本", description: "要处理的文本内容")
    var text: String

    @Parameter(
        title: "参数（JSON 格式）",
        description: "可选参数，JSON 格式，例如：{\"length\": \"short\", \"language\": \"zh-CN\"}",
        default: "{}"
    )
    var parametersJSON: String

    // MARK: - 执行逻辑

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        // 1. 解析参数
        let parameters: [String: String]
        do {
            parameters = try parseParameters(parametersJSON)
        } catch {
            throw ExecutePatternError.invalidParameters("参数 JSON 格式错误: \(error.localizedDescription)")
        }

        // 2. 验证 Pattern ID
        let validPatternIds = ["summarize", "translate", "extract", "format", "search"]
        guard validPatternIds.contains(patternId) else {
            throw ExecutePatternError.invalidPatternId(
                "无效的 Pattern ID: \(patternId)。有效值: \(validPatternIds.joined(separator: ", "))"
            )
        }

        // 3. 调用 Backend API 执行 Pattern
        // 注意：这里使用 Backend API 而非 AppState，因为 Shortcuts 后台运行时 App 可能未启动
        let result: PatternExecutionResult
        do {
            result = try await executePatternViaAPI(
                patternId: patternId,
                text: text,
                parameters: parameters
            )
        } catch {
            throw ExecutePatternError.executionFailed("Pattern 执行失败: \(error.localizedDescription)")
        }

        // 4. 检查执行结果
        guard result.success else {
            throw ExecutePatternError.executionFailed(result.output)
        }

        // 5. 返回结果（供 Shortcuts 后续操作使用）
        return .result(
            value: result.output,
            dialog: IntentDialog("✅ Pattern \(patternId) 执行成功")
        )
    }

    // MARK: - 辅助方法

    /// 解析 JSON 参数
    private func parseParameters(_ json: String) throws -> [String: String] {
        // 空 JSON 返回空字典
        let trimmed = json.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed == "{}" || trimmed.isEmpty {
            return [:]
        }

        guard let data = json.data(using: .utf8) else {
            throw NSError(domain: "ExecutePatternIntent", code: 1, userInfo: [
                NSLocalizedDescriptionKey: "无法将参数转换为 Data"
            ])
        }

        guard let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw NSError(domain: "ExecutePatternIntent", code: 2, userInfo: [
                NSLocalizedDescriptionKey: "参数不是有效的 JSON 对象"
            ])
        }

        // 将所有值转换为 String
        return dict.compactMapValues { "\($0)" }
    }

    /// 通过 Backend API 执行 Pattern
    private func executePatternViaAPI(
        patternId: String,
        text: String,
        parameters: [String: String]
    ) async throws -> PatternExecutionResult {
        // 构建请求
        let baseURL = UserDefaults.standard.string(forKey: "BackendAPIBaseURL") ?? "http://localhost:8000"
        guard let url = URL(string: "\(baseURL)/execute") else {
            throw NSError(domain: "ExecutePatternIntent", code: 3, userInfo: [
                NSLocalizedDescriptionKey: "无效的 API URL"
            ])
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let requestBody: [String: Any] = [
            "pattern_id": patternId,
            "text": text,
            "parameters": parameters
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)

        // 发送请求
        let (data, response) = try await URLSession.shared.data(for: request)

        // 检查 HTTP 状态码
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "ExecutePatternIntent", code: 4, userInfo: [
                NSLocalizedDescriptionKey: "无效的 HTTP 响应"
            ])
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw NSError(domain: "ExecutePatternIntent", code: 5, userInfo: [
                NSLocalizedDescriptionKey: "HTTP 错误: \(httpResponse.statusCode)"
            ])
        }

        // 解析响应
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw NSError(domain: "ExecutePatternIntent", code: 6, userInfo: [
                NSLocalizedDescriptionKey: "无法解析 API 响应"
            ])
        }

        let success = json["success"] as? Bool ?? false
        let output = json["output"] as? String ?? ""

        return PatternExecutionResult(success: success, output: output)
    }
}

// MARK: - 辅助结构

/// Pattern 执行结果
private struct PatternExecutionResult {
    let success: Bool
    let output: String
}

/// ExecutePattern 错误类型
enum ExecutePatternError: LocalizedError {
    case invalidPatternId(String)
    case invalidParameters(String)
    case executionFailed(String)

    var errorDescription: String? {
        switch self {
        case .invalidPatternId(let message),
             .invalidParameters(let message),
             .executionFailed(let message):
            return message
        }
    }
}
