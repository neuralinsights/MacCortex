//
//  Language.swift
//  MacCortex
//
//  Phase 3 Week 2 Day 1 - 语言枚举
//  Created on 2026-01-22
//

import Foundation

/// 支持的语言
enum Language: String, CaseIterable, Identifiable {
    case auto
    case chinese
    case english
    case japanese
    case korean
    case spanish
    case french
    case german
    case italian
    case portuguese
    case russian
    case arabic
    case hindi

    var id: String { rawValue }

    /// 显示名称
    var displayName: String {
        switch self {
        case .auto:
            return "自动检测"
        case .chinese:
            return "中文 (简体)"
        case .english:
            return "English"
        case .japanese:
            return "日本語"
        case .korean:
            return "한국어"
        case .spanish:
            return "Español"
        case .french:
            return "Français"
        case .german:
            return "Deutsch"
        case .italian:
            return "Italiano"
        case .portuguese:
            return "Português"
        case .russian:
            return "Русский"
        case .arabic:
            return "العربية"
        case .hindi:
            return "हिन्दी"
        }
    }

    /// Backend API 语言代码
    var code: String {
        switch self {
        case .auto:
            return "auto"
        case .chinese:
            return "zh-CN"
        case .english:
            return "en-US"
        case .japanese:
            return "ja-JP"
        case .korean:
            return "ko-KR"
        case .spanish:
            return "es-ES"
        case .french:
            return "fr-FR"
        case .german:
            return "de-DE"
        case .italian:
            return "it-IT"
        case .portuguese:
            return "pt-PT"
        case .russian:
            return "ru-RU"
        case .arabic:
            return "ar-SA"
        case .hindi:
            return "hi-IN"
        }
    }

    /// 国旗 Emoji
    var flag: String {
        switch self {
        case .auto:
            return "🌐"
        case .chinese:
            return "🇨🇳"
        case .english:
            return "🇺🇸"
        case .japanese:
            return "🇯🇵"
        case .korean:
            return "🇰🇷"
        case .spanish:
            return "🇪🇸"
        case .french:
            return "🇫🇷"
        case .german:
            return "🇩🇪"
        case .italian:
            return "🇮🇹"
        case .portuguese:
            return "🇵🇹"
        case .russian:
            return "🇷🇺"
        case .arabic:
            return "🇸🇦"
        case .hindi:
            return "🇮🇳"
        }
    }
}

/// 翻译风格
enum TranslationStyle: String, CaseIterable, Identifiable {
    case formal
    case casual
    case technical

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .formal:
            return "正式"
        case .casual:
            return "随意"
        case .technical:
            return "技术"
        }
    }

    var icon: String {
        switch self {
        case .formal:
            return "briefcase.fill"
        case .casual:
            return "bubble.left.fill"
        case .technical:
            return "gearshape.fill"
        }
    }
}
