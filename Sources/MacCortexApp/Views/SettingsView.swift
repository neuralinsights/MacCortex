//
//  SettingsView.swift
//  MacCortex
//
//  Phase 3 Week 3 后续 - 偏好设置界面
//  Created on 2026-01-22
//

import SwiftUI
import AppKit

/// 偏好设置视图
///
/// 包含 4 个设置 Tab：
/// 1. 通用（General）- 默认语言对、风格、流式模式
/// 2. 剪贴板（Clipboard）- 启用、最小长度、过滤规则
/// 3. 快捷键（Shortcuts）- 全局快捷键配置
/// 4. 高级（Advanced）- 缓存大小、Backend URL、调试选项
struct SettingsView: View {
    @StateObject private var settings = SettingsManager.shared
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            TabView {
                // Tab 1: 通用设置
                GeneralSettingsView()
                    .tabItem {
                        Label("通用", systemImage: "gear")
                    }
                    .tag(0)

                // Tab 2: LLM 模型设置 (Phase 4)
                LLMSettingsTabView()
                    .tabItem {
                        Label("模型", systemImage: "brain.head.profile")
                    }
                    .tag(1)

                // Tab 3: 剪贴板设置
                ClipboardSettingsView()
                    .tabItem {
                        Label("剪贴板", systemImage: "doc.on.clipboard")
                    }
                    .tag(2)

                // Tab 4: 快捷键设置
                ShortcutsSettingsView()
                    .tabItem {
                        Label("快捷键", systemImage: "command")
                    }
                    .tag(3)

                // Tab 5: 高级设置
                AdvancedSettingsView()
                    .tabItem {
                        Label("高级", systemImage: "slider.horizontal.3")
                    }
                    .tag(4)
            }

            Divider()

            // 底部按钮区域
            HStack {
                Spacer()

                Button("关闭") {
                    dismiss()
                }
                .keyboardShortcut(.escape, modifiers: [])
            }
            .padding()
        }
        .frame(width: 500, height: 450)
    }
}

// MARK: - Tab 1: 通用设置

struct GeneralSettingsView: View {
    @StateObject private var settings = SettingsManager.shared

    var body: some View {
        Form {
            Section("默认语言") {
                Picker("源语言", selection: $settings.defaultSourceLanguage) {
                    ForEach(Language.allCases) { language in
                        HStack {
                            Text(language.flag)
                            Text(language.displayName)
                        }
                        .tag(language)
                    }
                }
                .pickerStyle(.menu)

                Picker("目标语言", selection: $settings.defaultTargetLanguage) {
                    ForEach(Language.allCases.filter { $0 != .auto }) { language in
                        HStack {
                            Text(language.flag)
                            Text(language.displayName)
                        }
                        .tag(language)
                    }
                }
                .pickerStyle(.menu)
            }

            Section("默认风格") {
                Picker("翻译风格", selection: $settings.defaultStyle) {
                    ForEach(TranslationStyle.allCases) { style in
                        HStack {
                            Image(systemName: style.icon)
                            Text(style.displayName)
                        }
                        .tag(style)
                    }
                }
                .pickerStyle(.segmented)
            }

            Section("翻译模式") {
                Toggle("默认使用流式模式", isOn: $settings.defaultUseStreaming)
                    .help("启用后，翻译结果将逐字显示（类似 ChatGPT）")

                Toggle("自动保存翻译历史", isOn: $settings.autoSaveHistory)
                    .help("自动保存最近 20 条翻译记录")
            }

            Section("界面") {
                Toggle("启动时显示主窗口", isOn: $settings.showMainWindowOnLaunch)
                    .help("关闭后，启动时仅显示菜单栏图标")

                Picker("主题", selection: $settings.appTheme) {
                    Text("系统默认").tag(AppTheme.system)
                    Text("浅色").tag(AppTheme.light)
                    Text("深色").tag(AppTheme.dark)
                }
                .pickerStyle(.segmented)
            }
        }
        .formStyle(.grouped)
        .padding()
    }
}

// MARK: - Tab 2: 剪贴板设置

struct ClipboardSettingsView: View {
    @StateObject private var settings = SettingsManager.shared

    var body: some View {
        Form {
            Section("剪贴板监听") {
                Toggle("启用剪贴板监听", isOn: $settings.clipboardMonitorEnabled)
                    .help("自动检测剪贴板文本变化并翻译")

                HStack {
                    Text("最小触发长度")
                    Spacer()
                    TextField("", value: $settings.clipboardMinimumLength, format: .number)
                        .frame(width: 60)
                        .textFieldStyle(.roundedBorder)
                    Text("字符")
                }
                .disabled(!settings.clipboardMonitorEnabled)

                HStack {
                    Text("轮询间隔")
                    Spacer()
                    Slider(value: $settings.clipboardPollingInterval, in: 0.3...2.0, step: 0.1) {
                        Text("轮询间隔")
                    }
                    Text("\(settings.clipboardPollingInterval, specifier: "%.1f")s")
                        .frame(width: 40)
                }
                .disabled(!settings.clipboardMonitorEnabled)
            }

            Section("过滤规则") {
                Toggle("排除 URL", isOn: $settings.clipboardExcludeURLs)
                    .help("不翻译以 http:// 或 https:// 开头的文本")

                Toggle("排除纯数字", isOn: $settings.clipboardExcludeNumbers)
                    .help("不翻译只包含数字的文本")

                Toggle("排除代码片段", isOn: $settings.clipboardExcludeCode)
                    .help("不翻译包含大量符号的代码")

                HStack {
                    Text("最大长度限制")
                    Spacer()
                    TextField("", value: $settings.clipboardMaxLength, format: .number)
                        .frame(width: 80)
                        .textFieldStyle(.roundedBorder)
                    Text("字符")
                }
                .help("超过此长度的文本将被忽略")
            }

            Section("自动操作") {
                Toggle("复制翻译结果到剪贴板", isOn: $settings.clipboardAutoCopyResult)
                    .help("翻译完成后自动复制结果")

                Toggle("翻译后显示通知", isOn: $settings.clipboardShowNotification)
                    .help("翻译完成后显示系统通知")
            }
        }
        .formStyle(.grouped)
        .padding()
    }
}

// MARK: - Tab 3: 快捷键设置

struct ShortcutsSettingsView: View {
    @StateObject private var settings = SettingsManager.shared

    var body: some View {
        Form {
            Section("全局快捷键") {
                Toggle("启用全局快捷键", isOn: $settings.globalHotKeyEnabled)
                    .help("允许在任何应用中使用快捷键")
                    .onChange(of: settings.globalHotKeyEnabled) { oldValue, newValue in
                        GlobalHotKeyManager.shared.isEnabled = newValue
                    }

                HStack {
                    Text("显示悬浮窗口")
                    Spacer()
                    KeyboardShortcutView(
                        modifiers: $settings.floatingPanelModifiers,
                        key: $settings.floatingPanelKey
                    )
                }
                .disabled(!settings.globalHotKeyEnabled)
                .help("当前: Cmd+Shift+T（自定义功能开发中）")
            }

            Section("应用内快捷键") {
                VStack(alignment: .leading, spacing: 8) {
                    ShortcutRow(name: "翻译", shortcut: "Cmd+Enter")
                    ShortcutRow(name: "清空", shortcut: "Cmd+K")
                    ShortcutRow(name: "交换语言", shortcut: "Cmd+E")
                    ShortcutRow(name: "历史记录", shortcut: "Cmd+H")
                    ShortcutRow(name: "设置", shortcut: "Cmd+,")
                }
            }

            Section("提示") {
                Text("⚠️ 自定义全局快捷键功能将在未来版本中提供")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .formStyle(.grouped)
        .padding()
    }
}

/// 快捷键行显示
struct ShortcutRow: View {
    let name: String
    let shortcut: String

    var body: some View {
        HStack {
            Text(name)
            Spacer()
            Text(shortcut)
                .font(.system(.body, design: .monospaced))
                .foregroundColor(.secondary)
        }
    }
}

/// 键盘快捷键选择器（简化版，完整功能待实现）
struct KeyboardShortcutView: View {
    @Binding var modifiers: [String]
    @Binding var key: String

    var body: some View {
        HStack(spacing: 4) {
            ForEach(modifiers, id: \.self) { modifier in
                Text(modifier)
                    .font(.system(.body, design: .monospaced))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.secondary.opacity(0.2))
                    .cornerRadius(4)
            }

            Text(key)
                .font(.system(.body, design: .monospaced))
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.blue.opacity(0.2))
                .cornerRadius(4)
        }
    }
}

// MARK: - Tab 4: 高级设置

struct AdvancedSettingsView: View {
    @StateObject private var settings = SettingsManager.shared
    @State private var showResetAlert = false

    var body: some View {
        Form {
            Section("Backend 配置") {
                HStack {
                    Text("Backend URL")
                    Spacer()
                    TextField("http://localhost:8000", text: $settings.backendURL)
                        .frame(width: 250)
                        .textFieldStyle(.roundedBorder)
                }
                .help("MacCortex Backend 服务地址")

                HStack {
                    Text("连接超时")
                    Spacer()
                    TextField("", value: $settings.backendTimeout, format: .number)
                        .frame(width: 60)
                        .textFieldStyle(.roundedBorder)
                    Text("秒")
                }
            }

            Section("缓存设置") {
                HStack {
                    Text("缓存大小")
                    Spacer()
                    TextField("", value: $settings.cacheSize, format: .number)
                        .frame(width: 80)
                        .textFieldStyle(.roundedBorder)
                    Text("条")
                }
                .help("翻译缓存最多保存的条目数")

                HStack {
                    Text("缓存过期时间")
                    Spacer()
                    TextField("", value: $settings.cacheTTL, format: .number)
                        .frame(width: 60)
                        .textFieldStyle(.roundedBorder)
                    Text("小时")
                }

                Button("清除缓存") {
                    clearCache()
                }
                .help("清除所有翻译缓存（需要重启 Backend）")
            }

            Section("调试选项") {
                Toggle("启用调试日志", isOn: $settings.enableDebugLogging)
                    .help("在控制台输出详细日志（用于问题排查）")

                Toggle("显示 API 响应时间", isOn: $settings.showAPIResponseTime)
                    .help("在界面上显示每次 API 调用的耗时")
            }

            Section("数据管理") {
                Button("重置所有设置") {
                    showResetAlert = true
                }
                .foregroundColor(.red)
                .alert("确认重置", isPresented: $showResetAlert) {
                    Button("取消", role: .cancel) {}
                    Button("重置", role: .destructive) {
                        resetAllSettings()
                    }
                } message: {
                    Text("此操作将恢复所有默认设置，是否继续？")
                }

                Button("导出设置") {
                    exportSettings()
                }

                Button("导入设置") {
                    importSettings()
                }
            }
        }
        .formStyle(.grouped)
        .padding()
    }

    private func clearCache() {
        // TODO: 调用 Backend API 清除缓存
        print("[Settings] 清除缓存")
    }

    private func resetAllSettings() {
        settings.reset()
        print("[Settings] 重置所有设置")
    }

    private func exportSettings() {
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.json]
        panel.nameFieldStringValue = "MacCortex_Settings.json"

        if panel.runModal() == .OK, let url = panel.url {
            settings.export(to: url)
        }
    }

    private func importSettings() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.json]
        panel.allowsMultipleSelection = false

        if panel.runModal() == .OK, let url = panel.url {
            settings.importSettings(from: url)
        }
    }
}

// MARK: - 设置管理器

/// 设置管理器（单例）
@MainActor
class SettingsManager: ObservableObject {
    static let shared = SettingsManager()

    // MARK: - 通用设置

    @Published var defaultSourceLanguage: Language {
        didSet { save("defaultSourceLanguage", defaultSourceLanguage.rawValue) }
    }

    @Published var defaultTargetLanguage: Language {
        didSet { save("defaultTargetLanguage", defaultTargetLanguage.rawValue) }
    }

    @Published var defaultStyle: TranslationStyle {
        didSet { save("defaultStyle", defaultStyle.rawValue) }
    }

    @Published var defaultUseStreaming: Bool {
        didSet { save("defaultUseStreaming", defaultUseStreaming) }
    }

    @Published var autoSaveHistory: Bool {
        didSet { save("autoSaveHistory", autoSaveHistory) }
    }

    @Published var showMainWindowOnLaunch: Bool {
        didSet { save("showMainWindowOnLaunch", showMainWindowOnLaunch) }
    }

    @Published var appTheme: AppTheme {
        didSet { save("appTheme", appTheme.rawValue) }
    }

    // MARK: - 剪贴板设置

    @Published var clipboardMonitorEnabled: Bool {
        didSet { save("clipboardMonitorEnabled", clipboardMonitorEnabled) }
    }

    @Published var clipboardMinimumLength: Int {
        didSet { save("clipboardMinimumLength", clipboardMinimumLength) }
    }

    @Published var clipboardPollingInterval: Double {
        didSet { save("clipboardPollingInterval", clipboardPollingInterval) }
    }

    @Published var clipboardExcludeURLs: Bool {
        didSet { save("clipboardExcludeURLs", clipboardExcludeURLs) }
    }

    @Published var clipboardExcludeNumbers: Bool {
        didSet { save("clipboardExcludeNumbers", clipboardExcludeNumbers) }
    }

    @Published var clipboardExcludeCode: Bool {
        didSet { save("clipboardExcludeCode", clipboardExcludeCode) }
    }

    @Published var clipboardMaxLength: Int {
        didSet { save("clipboardMaxLength", clipboardMaxLength) }
    }

    @Published var clipboardAutoCopyResult: Bool {
        didSet { save("clipboardAutoCopyResult", clipboardAutoCopyResult) }
    }

    @Published var clipboardShowNotification: Bool {
        didSet { save("clipboardShowNotification", clipboardShowNotification) }
    }

    // MARK: - 快捷键设置

    @Published var globalHotKeyEnabled: Bool {
        didSet { save("globalHotKeyEnabled", globalHotKeyEnabled) }
    }

    @Published var floatingPanelModifiers: [String] {
        didSet { save("floatingPanelModifiers", floatingPanelModifiers) }
    }

    @Published var floatingPanelKey: String {
        didSet { save("floatingPanelKey", floatingPanelKey) }
    }

    // MARK: - 高级设置

    @Published var backendURL: String {
        didSet { save("backendURL", backendURL) }
    }

    @Published var backendTimeout: Int {
        didSet { save("backendTimeout", backendTimeout) }
    }

    @Published var cacheSize: Int {
        didSet { save("cacheSize", cacheSize) }
    }

    @Published var cacheTTL: Int {
        didSet { save("cacheTTL", cacheTTL) }
    }

    @Published var enableDebugLogging: Bool {
        didSet { save("enableDebugLogging", enableDebugLogging) }
    }

    @Published var showAPIResponseTime: Bool {
        didSet { save("showAPIResponseTime", showAPIResponseTime) }
    }

    // MARK: - 初始化

    private init() {
        // 通用设置
        self.defaultSourceLanguage = Language(rawValue: UserDefaults.standard.string(forKey: "defaultSourceLanguage") ?? "auto") ?? .auto
        self.defaultTargetLanguage = Language(rawValue: UserDefaults.standard.string(forKey: "defaultTargetLanguage") ?? "en-US") ?? .english
        self.defaultStyle = TranslationStyle(rawValue: UserDefaults.standard.string(forKey: "defaultStyle") ?? "formal") ?? .formal
        self.defaultUseStreaming = UserDefaults.standard.bool(forKey: "defaultUseStreaming")
        self.autoSaveHistory = UserDefaults.standard.object(forKey: "autoSaveHistory") as? Bool ?? true
        self.showMainWindowOnLaunch = UserDefaults.standard.object(forKey: "showMainWindowOnLaunch") as? Bool ?? true
        self.appTheme = AppTheme(rawValue: UserDefaults.standard.string(forKey: "appTheme") ?? "system") ?? .system

        // 剪贴板设置
        self.clipboardMonitorEnabled = UserDefaults.standard.bool(forKey: "clipboardMonitorEnabled")
        self.clipboardMinimumLength = UserDefaults.standard.object(forKey: "clipboardMinimumLength") as? Int ?? 3
        self.clipboardPollingInterval = UserDefaults.standard.object(forKey: "clipboardPollingInterval") as? Double ?? 0.5
        self.clipboardExcludeURLs = UserDefaults.standard.object(forKey: "clipboardExcludeURLs") as? Bool ?? true
        self.clipboardExcludeNumbers = UserDefaults.standard.object(forKey: "clipboardExcludeNumbers") as? Bool ?? true
        self.clipboardExcludeCode = UserDefaults.standard.object(forKey: "clipboardExcludeCode") as? Bool ?? false
        self.clipboardMaxLength = UserDefaults.standard.object(forKey: "clipboardMaxLength") as? Int ?? 5000
        self.clipboardAutoCopyResult = UserDefaults.standard.bool(forKey: "clipboardAutoCopyResult")
        self.clipboardShowNotification = UserDefaults.standard.bool(forKey: "clipboardShowNotification")

        // 快捷键设置
        self.globalHotKeyEnabled = UserDefaults.standard.object(forKey: "globalHotKeyEnabled") as? Bool ?? true
        self.floatingPanelModifiers = UserDefaults.standard.array(forKey: "floatingPanelModifiers") as? [String] ?? ["Cmd", "Shift"]
        self.floatingPanelKey = UserDefaults.standard.string(forKey: "floatingPanelKey") ?? "T"

        // 高级设置
        self.backendURL = UserDefaults.standard.string(forKey: "backendURL") ?? "http://localhost:8000"
        self.backendTimeout = UserDefaults.standard.object(forKey: "backendTimeout") as? Int ?? 30
        self.cacheSize = UserDefaults.standard.object(forKey: "cacheSize") as? Int ?? 1000
        self.cacheTTL = UserDefaults.standard.object(forKey: "cacheTTL") as? Int ?? 1
        self.enableDebugLogging = UserDefaults.standard.bool(forKey: "enableDebugLogging")
        self.showAPIResponseTime = UserDefaults.standard.bool(forKey: "showAPIResponseTime")
    }

    // MARK: - 持久化

    private func save<T>(_ key: String, _ value: T) {
        UserDefaults.standard.set(value, forKey: key)
    }

    /// 重置所有设置
    func reset() {
        // 清除所有 UserDefaults
        let domain = Bundle.main.bundleIdentifier!
        UserDefaults.standard.removePersistentDomain(forName: domain)
        UserDefaults.standard.synchronize()

        // 重新加载默认值（重新初始化）
        // 注意：这里需要手动重置所有属性，避免触发 didSet
    }

    /// 导出设置到 JSON
    func export(to url: URL) {
        do {
            // 构建设置字典
            let settings: [String: Any] = [
                // 通用设置
                "defaultSourceLanguage": defaultSourceLanguage.rawValue,
                "defaultTargetLanguage": defaultTargetLanguage.rawValue,
                "defaultStyle": defaultStyle.rawValue,
                "defaultUseStreaming": defaultUseStreaming,
                "autoSaveHistory": autoSaveHistory,
                "showMainWindowOnLaunch": showMainWindowOnLaunch,
                "appTheme": appTheme.rawValue,

                // 剪贴板设置
                "clipboardMonitorEnabled": clipboardMonitorEnabled,
                "clipboardMinimumLength": clipboardMinimumLength,
                "clipboardPollingInterval": clipboardPollingInterval,
                "clipboardExcludeURLs": clipboardExcludeURLs,
                "clipboardExcludeNumbers": clipboardExcludeNumbers,
                "clipboardExcludeCode": clipboardExcludeCode,
                "clipboardMaxLength": clipboardMaxLength,
                "clipboardAutoCopyResult": clipboardAutoCopyResult,
                "clipboardShowNotification": clipboardShowNotification,

                // 快捷键设置
                "globalHotKeyEnabled": globalHotKeyEnabled,
                "floatingPanelModifiers": floatingPanelModifiers,
                "floatingPanelKey": floatingPanelKey,

                // 高级设置
                "backendURL": backendURL,
                "backendTimeout": backendTimeout,
                "cacheSize": cacheSize,
                "cacheTTL": cacheTTL,
                "enableDebugLogging": enableDebugLogging,
                "showAPIResponseTime": showAPIResponseTime,

                // 元数据
                "exportVersion": "1.0",
                "exportDate": ISO8601DateFormatter().string(from: Date()),
                "appVersion": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown"
            ]

            // 转换为 JSON
            let jsonData = try JSONSerialization.data(withJSONObject: settings, options: [.prettyPrinted, .sortedKeys])

            // 写入文件
            try jsonData.write(to: url)

            print("[Settings] ✅ 设置导出成功: \(url.path)")

            // 显示成功通知
            showExportSuccessNotification()
        } catch {
            print("[Settings] ❌ 设置导出失败: \(error)")
            showExportErrorAlert(error: error)
        }
    }

    /// 从 JSON 导入设置
    func importSettings(from url: URL) {
        do {
            // 读取文件
            let jsonData = try Data(contentsOf: url)

            // 解析 JSON
            guard let settings = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any] else {
                throw SettingsError.invalidFormat
            }

            // 验证版本
            guard let version = settings["exportVersion"] as? String,
                  version == "1.0" else {
                throw SettingsError.unsupportedVersion
            }

            // 导入设置（避免触发 didSet，直接使用 UserDefaults）
            let defaults = UserDefaults.standard

            // 通用设置
            if let value = settings["defaultSourceLanguage"] as? String {
                defaults.set(value, forKey: "defaultSourceLanguage")
            }
            if let value = settings["defaultTargetLanguage"] as? String {
                defaults.set(value, forKey: "defaultTargetLanguage")
            }
            if let value = settings["defaultStyle"] as? String {
                defaults.set(value, forKey: "defaultStyle")
            }
            if let value = settings["defaultUseStreaming"] as? Bool {
                defaults.set(value, forKey: "defaultUseStreaming")
            }
            if let value = settings["autoSaveHistory"] as? Bool {
                defaults.set(value, forKey: "autoSaveHistory")
            }
            if let value = settings["showMainWindowOnLaunch"] as? Bool {
                defaults.set(value, forKey: "showMainWindowOnLaunch")
            }
            if let value = settings["appTheme"] as? String {
                defaults.set(value, forKey: "appTheme")
            }

            // 剪贴板设置
            if let value = settings["clipboardMonitorEnabled"] as? Bool {
                defaults.set(value, forKey: "clipboardMonitorEnabled")
            }
            if let value = settings["clipboardMinimumLength"] as? Int {
                defaults.set(value, forKey: "clipboardMinimumLength")
            }
            if let value = settings["clipboardPollingInterval"] as? Double {
                defaults.set(value, forKey: "clipboardPollingInterval")
            }
            if let value = settings["clipboardExcludeURLs"] as? Bool {
                defaults.set(value, forKey: "clipboardExcludeURLs")
            }
            if let value = settings["clipboardExcludeNumbers"] as? Bool {
                defaults.set(value, forKey: "clipboardExcludeNumbers")
            }
            if let value = settings["clipboardExcludeCode"] as? Bool {
                defaults.set(value, forKey: "clipboardExcludeCode")
            }
            if let value = settings["clipboardMaxLength"] as? Int {
                defaults.set(value, forKey: "clipboardMaxLength")
            }
            if let value = settings["clipboardAutoCopyResult"] as? Bool {
                defaults.set(value, forKey: "clipboardAutoCopyResult")
            }
            if let value = settings["clipboardShowNotification"] as? Bool {
                defaults.set(value, forKey: "clipboardShowNotification")
            }

            // 快捷键设置
            if let value = settings["globalHotKeyEnabled"] as? Bool {
                defaults.set(value, forKey: "globalHotKeyEnabled")
            }
            if let value = settings["floatingPanelModifiers"] as? [String] {
                defaults.set(value, forKey: "floatingPanelModifiers")
            }
            if let value = settings["floatingPanelKey"] as? String {
                defaults.set(value, forKey: "floatingPanelKey")
            }

            // 高级设置
            if let value = settings["backendURL"] as? String {
                defaults.set(value, forKey: "backendURL")
            }
            if let value = settings["backendTimeout"] as? Int {
                defaults.set(value, forKey: "backendTimeout")
            }
            if let value = settings["cacheSize"] as? Int {
                defaults.set(value, forKey: "cacheSize")
            }
            if let value = settings["cacheTTL"] as? Int {
                defaults.set(value, forKey: "cacheTTL")
            }
            if let value = settings["enableDebugLogging"] as? Bool {
                defaults.set(value, forKey: "enableDebugLogging")
            }
            if let value = settings["showAPIResponseTime"] as? Bool {
                defaults.set(value, forKey: "showAPIResponseTime")
            }

            // 同步到磁盘
            defaults.synchronize()

            print("[Settings] ✅ 设置导入成功，需要重启应用以生效")

            // 显示成功通知（需要重启）
            showImportSuccessAlert()
        } catch {
            print("[Settings] ❌ 设置导入失败: \(error)")
            showImportErrorAlert(error: error)
        }
    }

    // MARK: - Helper Methods

    private func showExportSuccessNotification() {
        // 简单的成功通知（控制台）
        // 完整的通知功能将在 NotificationManager 中实现
        print("[Settings] ✅ 设置导出成功")
    }

    private func showExportErrorAlert(error: Error) {
        let alert = NSAlert()
        alert.messageText = "导出失败"
        alert.informativeText = error.localizedDescription
        alert.alertStyle = .warning
        alert.addButton(withTitle: "确定")
        alert.runModal()
    }

    private func showImportSuccessAlert() {
        let alert = NSAlert()
        alert.messageText = "导入成功"
        alert.informativeText = "设置已导入，请重启应用以使所有设置生效。"
        alert.alertStyle = .informational
        alert.addButton(withTitle: "稍后重启")
        alert.addButton(withTitle: "立即退出")

        let response = alert.runModal()
        if response == .alertSecondButtonReturn {
            // 立即退出应用
            NSApplication.shared.terminate(nil)
        }
    }

    private func showImportErrorAlert(error: Error) {
        let alert = NSAlert()
        alert.messageText = "导入失败"
        alert.informativeText = error.localizedDescription
        alert.alertStyle = .warning
        alert.addButton(withTitle: "确定")
        alert.runModal()
    }
}

/// 设置错误
enum SettingsError: LocalizedError {
    case invalidFormat
    case unsupportedVersion

    var errorDescription: String? {
        switch self {
        case .invalidFormat:
            return "设置文件格式无效"
        case .unsupportedVersion:
            return "不支持的设置文件版本"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .invalidFormat:
            return "请确认文件是由 MacCortex 导出的 JSON 格式"
        case .unsupportedVersion:
            return "请使用最新版本的 MacCortex 导出设置"
        }
    }
}

// MARK: - 数据模型

/// 应用主题
enum AppTheme: String, CaseIterable {
    case system = "system"
    case light = "light"
    case dark = "dark"

    var displayName: String {
        switch self {
        case .system: return "系统默认"
        case .light: return "浅色"
        case .dark: return "深色"
        }
    }
}

// MARK: - Tab 2: LLM 模型设置 (Phase 4)

/// LLM 模型设置 Tab 视图
struct LLMSettingsTabView: View {
    @StateObject private var viewModel = LLMSettingsViewModel()

    var body: some View {
        Form {
            // Section 1: API Key 配置
            Section("API Key 配置") {
                ForEach(LLMProvider.allCases) { provider in
                    LLMAPIKeyRow(
                        provider: provider,
                        isConfigured: viewModel.isProviderConfigured(provider),
                        onConfigure: { viewModel.showAPIKeySheet(for: provider) }
                    )
                }
            }

            // Section 2: 默认模型
            Section("默认模型") {
                if viewModel.isLoading {
                    HStack {
                        ProgressView()
                            .scaleEffect(0.7)
                        Text("加载模型列表...")
                            .foregroundColor(.secondary)
                    }
                } else if viewModel.models.isEmpty {
                    Text("暂无可用模型。请先配置 API Key 或启动本地模型服务。")
                        .font(.caption)
                        .foregroundColor(.secondary)
                } else {
                    Picker("选择模型", selection: $viewModel.selectedModelId) {
                        ForEach(viewModel.models) { model in
                            HStack {
                                Image(systemName: model.icon)
                                Text(model.displayName)
                                if !model.isAvailable {
                                    Text("(不可用)")
                                        .foregroundColor(.secondary)
                                }
                            }
                            .tag(model.id)
                        }
                    }
                    .pickerStyle(.menu)

                    if let selectedModel = viewModel.selectedModel {
                        HStack {
                            ForEach(selectedModel.capabilities, id: \.self) { cap in
                                Text(LLMModel.capabilityDisplayName(for: cap))
                                    .font(.caption2)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(LLMModel.capabilityColor(for: cap).opacity(0.2))
                                    .foregroundColor(LLMModel.capabilityColor(for: cap))
                                    .cornerRadius(4)
                            }
                        }

                        if !selectedModel.isLocal {
                            Text("定价: $\(NSDecimalNumber(decimal: selectedModel.pricing.inputPricePer1M).doubleValue, specifier: "%.2f") 输入 / $\(NSDecimalNumber(decimal: selectedModel.pricing.outputPricePer1M).doubleValue, specifier: "%.2f") 输出 ($/1M tokens)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }

                Button("刷新模型列表") {
                    viewModel.refreshModels()
                }
                .disabled(viewModel.isLoading)
            }

            // Section 3: 使用量统计
            Section("使用量统计") {
                if let stats = viewModel.usageStats {
                    HStack {
                        VStack(alignment: .leading) {
                            Text("总 Tokens")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text(stats.formattedTokens)
                                .font(.headline)
                        }
                        Spacer()
                        VStack(alignment: .trailing) {
                            Text("总成本")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text(stats.formattedCost)
                                .font(.headline)
                                .foregroundColor(.green)
                        }
                    }

                    Button("重置统计", role: .destructive) {
                        viewModel.resetUsageStats()
                    }
                } else {
                    Text("暂无使用量数据")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .formStyle(.grouped)
        .padding()
        .onAppear {
            viewModel.loadData()
        }
        .sheet(isPresented: $viewModel.showingAPIKeySheet) {
            if let provider = viewModel.editingProvider {
                APIKeyEditSheet(
                    provider: provider,
                    isPresented: $viewModel.showingAPIKeySheet,
                    onSave: { key in
                        viewModel.saveAPIKey(key, for: provider)
                    },
                    onDelete: {
                        viewModel.deleteAPIKey(for: provider)
                    }
                )
            }
        }
    }
}

/// LLM API Key 配置行
struct LLMAPIKeyRow: View {
    let provider: LLMProvider
    let isConfigured: Bool
    let onConfigure: () -> Void

    var body: some View {
        HStack {
            Image(systemName: provider.icon)
                .foregroundColor(isConfigured ? .green : .secondary)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(provider.displayName)
                Text(isConfigured ? "已配置" : "未配置")
                    .font(.caption)
                    .foregroundColor(isConfigured ? .green : .secondary)
            }

            Spacer()

            Button(isConfigured ? "修改" : "配置") {
                onConfigure()
            }
            .buttonStyle(.bordered)
        }
    }
}

/// API Key 编辑弹窗
struct APIKeyEditSheet: View {
    let provider: LLMProvider
    @Binding var isPresented: Bool
    let onSave: (String) -> Void
    let onDelete: () -> Void

    @State private var apiKey = ""
    @State private var showKey = false

    var body: some View {
        VStack(spacing: 20) {
            // 标题
            HStack {
                Image(systemName: provider.icon)
                    .font(.title2)
                Text("配置 \(provider.displayName) API Key")
                    .font(.headline)
            }

            // 输入框
            HStack {
                if showKey {
                    TextField("输入 API Key", text: $apiKey)
                        .textFieldStyle(.roundedBorder)
                } else {
                    SecureField("输入 API Key", text: $apiKey)
                        .textFieldStyle(.roundedBorder)
                }

                Button {
                    showKey.toggle()
                } label: {
                    Image(systemName: showKey ? "eye.slash" : "eye")
                }
                .buttonStyle(.borderless)
            }

            // 帮助链接
            if let url = provider.apiKeyHelpURL {
                Link(destination: url) {
                    HStack {
                        Image(systemName: "questionmark.circle")
                        Text("如何获取 API Key?")
                    }
                    .font(.caption)
                }
            }

            Divider()

            // 按钮
            HStack {
                Button("删除", role: .destructive) {
                    onDelete()
                    isPresented = false
                }

                Spacer()

                Button("取消") {
                    isPresented = false
                }
                .keyboardShortcut(.escape)

                Button("保存") {
                    onSave(apiKey)
                    isPresented = false
                }
                .keyboardShortcut(.return)
                .disabled(apiKey.isEmpty)
            }
        }
        .padding()
        .frame(width: 400)
    }
}

/// LLM 设置 ViewModel
@MainActor
class LLMSettingsViewModel: ObservableObject {
    @Published var models: [LLMModel] = []
    @Published var selectedModelId: String = ""
    @Published var usageStats: UsageStats?
    @Published var isLoading = false
    @Published var showingAPIKeySheet = false
    @Published var editingProvider: LLMProvider?

    private let apiKeyManager = APIKeyManager.shared

    var selectedModel: LLMModel? {
        models.first { $0.id == selectedModelId }
    }

    func loadData() {
        refreshModels()
        loadUsageStats()
    }

    func refreshModels() {
        isLoading = true

        Task {
            try? await Task.sleep(nanoseconds: 300_000_000)

            await MainActor.run {
                #if DEBUG
                self.models = [
                    .previewClaude,
                    .previewGPT,
                    .previewOllama
                ]
                if self.selectedModelId.isEmpty {
                    self.selectedModelId = "claude-sonnet-4"
                }
                #endif
                self.isLoading = false
            }
        }
    }

    func loadUsageStats() {
        #if DEBUG
        usageStats = .preview
        #endif
    }

    func isProviderConfigured(_ provider: LLMProvider) -> Bool {
        apiKeyManager.hasKey(for: provider)
    }

    func showAPIKeySheet(for provider: LLMProvider) {
        editingProvider = provider
        showingAPIKeySheet = true
    }

    func saveAPIKey(_ key: String, for provider: LLMProvider) {
        if apiKeyManager.setKey(key, for: provider) {
            refreshModels()
        }
    }

    func deleteAPIKey(for provider: LLMProvider) {
        if apiKeyManager.deleteKey(for: provider) {
            refreshModels()
        }
    }

    func resetUsageStats() {
        usageStats = .empty
    }
}

// MARK: - 预览

#Preview {
    SettingsView()
}
