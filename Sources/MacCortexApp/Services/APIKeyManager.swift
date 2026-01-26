//
//  APIKeyManager.swift
//  MacCortex
//
//  Phase 4 - Multi-LLM Support: Keychain API Key Management
//  Created on 2026-01-26
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import Foundation
import Security

/// LLM Provider 枚举
///
/// 支持的 LLM 服务提供商列表
enum LLMProvider: String, CaseIterable, Identifiable, Codable {
    case anthropic = "anthropic"
    case openai = "openai"
    case deepseek = "deepseek"
    case gemini = "gemini"

    var id: String { rawValue }

    /// 显示名称
    var displayName: String {
        switch self {
        case .anthropic: return "Anthropic"
        case .openai: return "OpenAI"
        case .deepseek: return "DeepSeek"
        case .gemini: return "Google Gemini"
        }
    }

    /// Provider 图标（SF Symbols）
    var icon: String {
        switch self {
        case .anthropic: return "brain.head.profile"
        case .openai: return "sparkles"
        case .deepseek: return "waveform.path.ecg"
        case .gemini: return "diamond"
        }
    }

    /// API Key 获取说明链接
    var apiKeyHelpURL: URL? {
        switch self {
        case .anthropic:
            return URL(string: "https://console.anthropic.com/settings/keys")
        case .openai:
            return URL(string: "https://platform.openai.com/api-keys")
        case .deepseek:
            return URL(string: "https://platform.deepseek.com/api_keys")
        case .gemini:
            return URL(string: "https://aistudio.google.com/app/apikey")
        }
    }

    /// API Key 格式验证正则表达式
    var keyPattern: String {
        switch self {
        case .anthropic:
            return "^sk-ant-[a-zA-Z0-9_-]{90,}$"
        case .openai:
            return "^sk-[a-zA-Z0-9]{48,}$"
        case .deepseek:
            return "^sk-[a-zA-Z0-9]{32,}$"
        case .gemini:
            return "^[a-zA-Z0-9_-]{39}$"
        }
    }

    /// 是否需要 API Key（本地模型不需要）
    var requiresAPIKey: Bool {
        return true
    }
}

/// API Key 管理器
///
/// 使用 macOS Keychain 安全存储 LLM Provider API Keys。
/// 采用 `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` 访问级别，
/// 确保 API Key 只在设备解锁时可访问，且不会同步到其他设备。
///
/// ## 使用示例
/// ```swift
/// let manager = APIKeyManager.shared
///
/// // 保存 API Key
/// manager.setKey("sk-ant-xxx", for: .anthropic)
///
/// // 读取 API Key
/// if let key = manager.getKey(for: .anthropic) {
///     print("Anthropic API Key: \(key.prefix(10))...")
/// }
///
/// // 检查是否已配置
/// if manager.hasKey(for: .anthropic) {
///     // 使用 Anthropic Provider
/// }
///
/// // 删除 API Key
/// manager.deleteKey(for: .anthropic)
/// ```
@MainActor
final class APIKeyManager: ObservableObject {

    // MARK: - Singleton

    static let shared = APIKeyManager()

    // MARK: - Published Properties

    /// 已配置的 Provider 列表（用于 UI 状态显示）
    @Published private(set) var configuredProviders: Set<LLMProvider> = []

    // MARK: - Constants

    /// Keychain Service 名称
    private let keychainService = "com.maccortex.llm-api-keys"

    // MARK: - Initialization

    private init() {
        refreshConfiguredProviders()
    }

    // MARK: - Public Methods

    /// 获取指定 Provider 的 API Key
    ///
    /// - Parameter provider: LLM Provider
    /// - Returns: API Key 字符串，如果未配置则返回 nil
    func getKey(for provider: LLMProvider) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: provider.rawValue,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let key = String(data: data, encoding: .utf8) else {
            if status != errSecItemNotFound {
                print("[APIKeyManager] ⚠️ 读取 \(provider.displayName) API Key 失败: \(status)")
            }
            return nil
        }

        return key
    }

    /// 保存或更新指定 Provider 的 API Key
    ///
    /// - Parameters:
    ///   - key: API Key 字符串
    ///   - provider: LLM Provider
    /// - Returns: 是否保存成功
    @discardableResult
    func setKey(_ key: String, for provider: LLMProvider) -> Bool {
        guard let keyData = key.data(using: .utf8) else {
            print("[APIKeyManager] ❌ API Key 编码失败")
            return false
        }

        // 先尝试删除已有的 Key
        deleteKey(for: provider)

        // 创建新的 Keychain 条目
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: provider.rawValue,
            kSecValueData as String: keyData,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            kSecAttrLabel as String: "MacCortex \(provider.displayName) API Key"
        ]

        let status = SecItemAdd(query as CFDictionary, nil)

        if status == errSecSuccess {
            print("[APIKeyManager] ✅ 保存 \(provider.displayName) API Key 成功")
            refreshConfiguredProviders()
            return true
        } else {
            print("[APIKeyManager] ❌ 保存 \(provider.displayName) API Key 失败: \(status)")
            return false
        }
    }

    /// 删除指定 Provider 的 API Key
    ///
    /// - Parameter provider: LLM Provider
    /// - Returns: 是否删除成功（包括原本就不存在的情况）
    @discardableResult
    func deleteKey(for provider: LLMProvider) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: provider.rawValue
        ]

        let status = SecItemDelete(query as CFDictionary)

        if status == errSecSuccess || status == errSecItemNotFound {
            if status == errSecSuccess {
                print("[APIKeyManager] ✅ 删除 \(provider.displayName) API Key 成功")
            }
            refreshConfiguredProviders()
            return true
        } else {
            print("[APIKeyManager] ❌ 删除 \(provider.displayName) API Key 失败: \(status)")
            return false
        }
    }

    /// 检查指定 Provider 是否已配置 API Key
    ///
    /// - Parameter provider: LLM Provider
    /// - Returns: 是否已配置
    func hasKey(for provider: LLMProvider) -> Bool {
        return getKey(for: provider) != nil
    }

    /// 验证 API Key 格式是否正确
    ///
    /// - Parameters:
    ///   - key: 待验证的 API Key
    ///   - provider: LLM Provider
    /// - Returns: 格式是否有效
    func validateKeyFormat(_ key: String, for provider: LLMProvider) -> Bool {
        guard let regex = try? NSRegularExpression(pattern: provider.keyPattern) else {
            return true  // 如果正则表达式无效，跳过验证
        }

        let range = NSRange(location: 0, length: key.utf16.count)
        return regex.firstMatch(in: key, range: range) != nil
    }

    /// 获取 API Key 的脱敏显示版本
    ///
    /// - Parameters:
    ///   - key: 原始 API Key
    ///   - visibleChars: 可见字符数（前后各半）
    /// - Returns: 脱敏后的字符串，如 "sk-ant-xxxx...xxxx"
    func maskKey(_ key: String, visibleChars: Int = 8) -> String {
        guard key.count > visibleChars * 2 else {
            return String(repeating: "•", count: key.count)
        }

        let halfVisible = visibleChars / 2
        let prefix = String(key.prefix(halfVisible))
        let suffix = String(key.suffix(halfVisible))
        return "\(prefix)...\(suffix)"
    }

    /// 获取所有已配置 API Key 的 Provider 列表
    ///
    /// - Returns: 已配置的 Provider 集合
    func getConfiguredProviders() -> Set<LLMProvider> {
        return configuredProviders
    }

    /// 刷新已配置 Provider 列表
    func refreshConfiguredProviders() {
        var configured = Set<LLMProvider>()

        for provider in LLMProvider.allCases {
            if hasKey(for: provider) {
                configured.insert(provider)
            }
        }

        configuredProviders = configured
    }

    // MARK: - Backend Sync

    /// 将配置的 API Keys 发送到 Backend
    ///
    /// 通过环境变量方式传递给 Python Backend，避免在网络中传输 Keys。
    /// 注意：此方法仅用于本地 Backend 通信，不会通过网络发送 Keys。
    ///
    /// - Returns: 包含 API Key 环境变量的字典
    func getEnvironmentVariables() -> [String: String] {
        var env: [String: String] = [:]

        if let key = getKey(for: .anthropic) {
            env["ANTHROPIC_API_KEY"] = key
        }

        if let key = getKey(for: .openai) {
            env["OPENAI_API_KEY"] = key
        }

        if let key = getKey(for: .deepseek) {
            env["DEEPSEEK_API_KEY"] = key
        }

        if let key = getKey(for: .gemini) {
            env["GOOGLE_API_KEY"] = key
        }

        return env
    }
}

// MARK: - Preview Support

#if DEBUG
extension APIKeyManager {
    /// 用于 Preview 的模拟数据
    static var preview: APIKeyManager {
        let manager = APIKeyManager.shared
        // 在 Preview 中不实际保存 Key
        return manager
    }
}
#endif
