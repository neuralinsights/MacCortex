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

// GetContextIntent - 获取当前上下文 Intent（供 Shortcuts 调用）
// Phase 2 Week 3 Day 13-14: Shortcuts 自动化集成
// 创建时间：2026-01-21

import AppIntents
import Foundation
import AppKit

/// 获取当前上下文 Intent（供 macOS Shortcuts 调用）
/// 返回当前活跃应用、选中文本等信息，用于智能化 Shortcuts 工作流
@available(macOS 13.0, *)
struct GetContextIntent: AppIntent {
    static var title: LocalizedStringResource = "获取当前上下文"
    static var description = IntentDescription("获取当前活跃应用、选中文本等上下文信息")

    static var openAppWhenRun: Bool = false

    // MARK: - 执行逻辑

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        // 收集上下文信息
        var context: [String: String] = [:]

        // 1. 当前活跃应用
        if let frontmostApp = NSWorkspace.shared.frontmostApplication {
            context["app_name"] = frontmostApp.localizedName ?? "Unknown"
            context["app_bundle_id"] = frontmostApp.bundleIdentifier ?? "Unknown"
        }

        // 2. 剪贴板内容（前 200 字符）
        if let clipboardString = NSPasteboard.general.string(forType: .string) {
            let preview = String(clipboardString.prefix(200))
            context["clipboard_preview"] = preview
            context["clipboard_length"] = "\(clipboardString.count)"
        }

        // 3. 当前时间
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        context["timestamp"] = formatter.string(from: Date())

        // 4. 系统语言
        if let languageCode = Locale.current.language.languageCode?.identifier {
            context["system_language"] = languageCode
        }

        // 5. 场景检测（如果 SceneDetector 可用）
        // 注意：Shortcuts 后台运行时可能无法访问 AppState
        // 这里返回基本信息即可

        // 转换为 JSON 字符串
        let jsonString = try contextToJSON(context)

        return .result(
            value: jsonString,
            dialog: IntentDialog("✅ 已获取当前上下文")
        )
    }

    // MARK: - 辅助方法

    /// 将上下文字典转换为 JSON 字符串
    private func contextToJSON(_ context: [String: String]) throws -> String {
        let data = try JSONSerialization.data(withJSONObject: context, options: .prettyPrinted)
        guard let jsonString = String(data: data, encoding: .utf8) else {
            throw GetContextError.jsonConversionFailed
        }
        return jsonString
    }
}

// MARK: - 错误类型

enum GetContextError: LocalizedError {
    case jsonConversionFailed

    var errorDescription: String? {
        switch self {
        case .jsonConversionFailed:
            return "无法将上下文转换为 JSON 格式"
        }
    }
}
