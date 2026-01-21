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

// AppIntents - MacCortex App Intents 注册与配置
// Phase 2 Week 3 Day 13-14: Shortcuts 自动化集成
// 创建时间：2026-01-21

import AppIntents
import Foundation

/// MacCortex App Intents（供 macOS Shortcuts 调用）
/// 注册所有可用的 Intents 和 App Shortcuts
@available(macOS 13.0, *)
struct MacCortexAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] = [
        // 1. 执行 Pattern（最常用）
        AppShortcut(
                intent: ExecutePatternIntent(),
                phrases: [
                    "使用 \(.applicationName) 总结文本",
                    "Summarize with \(.applicationName)",
                    "使用 \(.applicationName) 翻译",
                    "Translate with \(.applicationName)",
                    "用 \(.applicationName) 处理文本"
                ],
                shortTitle: "执行 Pattern",
                systemImageName: "sparkles"
            ),

            // 2. 获取上下文
            AppShortcut(
                intent: GetContextIntent(),
                phrases: [
                    "获取当前上下文",
                    "Get context with \(.applicationName)",
                    "查看当前应用"
                ],
                shortTitle: "获取上下文",
                systemImageName: "info.circle"
            )
        ]
}

// MARK: - Intent 依赖项

/// Pattern ID 枚举（用于 Shortcuts 参数选择器）
@available(macOS 13.0, *)
enum PatternIDEntity: String, AppEnum {
    case summarize = "summarize"
    case translate = "translate"
    case extract = "extract"
    case format = "format"
    case search = "search"

    static var typeDisplayRepresentation: TypeDisplayRepresentation {
        "Pattern 类型"
    }

    static var caseDisplayRepresentations: [PatternIDEntity: DisplayRepresentation] {
        [
            .summarize: DisplayRepresentation(
                title: "总结（Summarize）",
                subtitle: "总结长文本为简短摘要",
                image: .init(systemName: "text.alignleft")
            ),
            .translate: DisplayRepresentation(
                title: "翻译（Translate）",
                subtitle: "翻译文本到其他语言",
                image: .init(systemName: "character.book.closed")
            ),
            .extract: DisplayRepresentation(
                title: "提取（Extract）",
                subtitle: "提取人名、邮箱、日期等信息",
                image: .init(systemName: "doc.text.magnifyingglass")
            ),
            .format: DisplayRepresentation(
                title: "格式转换（Format）",
                subtitle: "转换 JSON、YAML、CSV 等格式",
                image: .init(systemName: "arrow.left.arrow.right")
            ),
            .search: DisplayRepresentation(
                title: "网络搜索（Search）",
                subtitle: "搜索互联网并总结结果",
                image: .init(systemName: "magnifyingglass")
            )
        ]
    }
}

// MARK: - App Intent 配置

/// MacCortex App Intent 配置
@available(macOS 13.0, *)
extension AppIntent {
    /// 应用名称（用于 Siri 语音命令）
    static var applicationName: String {
        "MacCortex"
    }
}
