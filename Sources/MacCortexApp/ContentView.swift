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

// MacCortex 主视图
// Phase 0.5 - 基础设施
// Phase 2 Day 1 - Observation Framework 升级
// 创建时间：2026-01-20
// 更新时间：2026-01-21

import SwiftUI
import PermissionsKit
import AppKit

struct ContentView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        Group {
            if appState.isFirstRun {
                // Phase 0.5 Day 8: 首次启动引导
                FirstRunView()
            } else {
                // 主界面
                MainView()
            }
        }
    }
}

struct MainView: View {
    @Environment(AppState.self) private var appState
    @State private var showSettings = false
    @State private var showUndoHistory = false  // Phase 2 Week 2 Day 10: 撤销历史
    @State private var showMCPServerList = false  // Phase 2 Week 3 Day 11-12: MCP 服务器列表
    @State private var selectedTab = 0  // Week 5: 默认显示Swarm编排界面

    var body: some View {
        TabView(selection: $selectedTab) {
            // Week 5: Swarm编排界面（默认显示）
            SwarmOrchestrationView()
                .tabItem {
                    Label("Swarm", systemImage: "gearshape.2.fill")
                }
                .tag(0)

            // Phase 3 Week 2 Day 1-2: 翻译界面
            TranslationView()
                .tabItem {
                    Label("翻译", systemImage: "character.bubble")
                }
                .tag(1)

            // Phase 3 Week 2 Day 3-4: 批量翻译界面
            BatchTranslationView()
                .tabItem {
                    Label("批量", systemImage: "list.bullet")
                }
                .tag(2)

            // Phase 3 Week 2 Day 5: 缓存统计界面
            CacheStatsView()
                .tabItem {
                    Label("统计", systemImage: "chart.bar")
                }
                .tag(3)

            // 原有的权限状态页面
            permissionsView
                .tabItem {
                    Label("权限", systemImage: "lock.shield")
                }
                .tag(4)
        }
    }

    // 权限与系统状态视图（生产版本）
    private var permissionsView: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // 顶部应用信息
                    appInfoSection

                    // 权限管理
                    permissionsSection

                    // 连接状态
                    connectionStatusSection

                    // 数据与隐私
                    dataPrivacySection

                    // 帮助与支持
                    helpSupportSection
                }
                .padding()
            }
            .navigationTitle("系统状态")
            .toolbar {
                ToolbarItem(placement: .navigation) {
                    Button(action: {
                        showSettings = true
                    }) {
                        Image(systemName: "gear")
                    }
                }

                ToolbarItem(placement: .automatic) {
                    Button(action: {
                        showUndoHistory = true
                    }) {
                        Label("撤销历史", systemImage: "arrow.uturn.backward.circle")
                    }
                }

                ToolbarItem(placement: .automatic) {
                    Button(action: {
                        showMCPServerList = true
                    }) {
                        Label("MCP 服务器", systemImage: "server.rack")
                    }
                }
            }
        }
        .sheet(isPresented: $showSettings) {
            SettingsView()
                .environment(appState)
        }
        .sheet(isPresented: $showUndoHistory) {
            // Phase 2 Week 2 Day 10: 撤销历史视图
            UndoHistoryView()
        }
        .sheet(isPresented: $showMCPServerList) {
            // Phase 2 Week 3 Day 11-12: MCP 服务器列表
            MCPServerListView()
        }
        .sheet(isPresented: Binding(
            get: { appState.showRiskConfirmation },
            set: { _ in }
        )) {
            // Phase 2 Week 2 Day 8-9: 风险确认对话框
            if let assessment = appState.currentRiskAssessment {
                RiskConfirmationDialog(
                    assessment: assessment,
                    onConfirm: {
                        appState.confirmRiskOperation()
                    },
                    onCancel: {
                        appState.cancelRiskOperation()
                    }
                )
            }
        }
    }

    // MARK: - 应用信息区域

    private var appInfoSection: some View {
        VStack(spacing: 16) {
            // Logo 和名称
            HStack(spacing: 16) {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 50))
                    .foregroundColor(.blue)

                VStack(alignment: .leading, spacing: 4) {
                    Text("MacCortex")
                        .font(.title)
                        .fontWeight(.bold)

                    Text("macOS 智能助手")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()

                // 版本信息
                VStack(alignment: .trailing, spacing: 2) {
                    Text("v\(Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0")")
                        .font(.system(size: 14, weight: .medium, design: .monospaced))

                    Text("Build \(Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1")")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Divider()

            // 系统兼容性
            HStack {
                Image(systemName: "desktopcomputer")
                    .foregroundColor(.secondary)
                    .frame(width: 20)

                Text("macOS 14.0+ (Sonoma)")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Spacer()

                Text("Apple Silicon")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.1))
                    .foregroundColor(.blue)
                    .cornerRadius(4)
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
    }

    // MARK: - 权限管理区域

    private var permissionsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "lock.shield.fill")
                    .foregroundColor(.blue)
                Text("权限管理")
                    .font(.headline)

                Spacer()

                Button(action: {
                    Task {
                        await appState.checkPermissions()
                    }
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: "arrow.clockwise")
                        Text("刷新")
                    }
                    .font(.caption)
                    .foregroundColor(.blue)
                }
                .buttonStyle(.plain)
            }

            // Full Disk Access
            PermissionManagementRow(
                icon: "folder.fill",
                name: "Full Disk Access",
                description: "读取笔记、文件和文档",
                isGranted: appState.hasFullDiskAccess,
                isRequired: true,
                onOpenSettings: {
                    FullDiskAccessManager.shared.openSystemPreferences()
                }
            )

            // Accessibility
            PermissionManagementRow(
                icon: "cursorarrow.rays",
                name: "Accessibility",
                description: "自动化工作流程",
                isGranted: appState.hasAccessibilityPermission,
                isRequired: false,
                onOpenSettings: {
                    AccessibilityManager.shared.openSystemPreferences()
                }
            )
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
    }

    // MARK: - 连接状态区域

    private var connectionStatusSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "network")
                    .foregroundColor(.blue)
                Text("服务状态")
                    .font(.headline)
            }

            // Backend 状态
            ConnectionStatusRow(
                icon: "server.rack",
                name: "Python Backend",
                checkConnection: {
                    await APIClient.shared.isBackendAvailable()
                }
            )

            // Ollama 状态
            ConnectionStatusRow(
                icon: "cpu",
                name: "Ollama (本地 AI)",
                checkConnection: {
                    // 检查 Ollama 是否运行
                    let url = URL(string: "http://127.0.0.1:11434/api/tags")!
                    do {
                        let (_, response) = try await URLSession.shared.data(from: url)
                        return (response as? HTTPURLResponse)?.statusCode == 200
                    } catch {
                        return false
                    }
                }
            )
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
    }

    // MARK: - 数据与隐私区域

    private var dataPrivacySection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "hand.raised.fill")
                    .foregroundColor(.blue)
                Text("数据与隐私")
                    .font(.headline)
            }

            // 数据存储位置
            HStack {
                Image(systemName: "folder")
                    .foregroundColor(.secondary)
                    .frame(width: 24)

                VStack(alignment: .leading, spacing: 2) {
                    Text("本地数据存储")
                        .font(.subheadline)
                    Text("~/Library/Application Support/MacCortex/")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                Button("打开") {
                    let path = FileManager.default.homeDirectoryForCurrentUser
                        .appendingPathComponent("Library/Application Support/MacCortex")
                    NSWorkspace.shared.open(path)
                }
                .font(.caption)
                .buttonStyle(.bordered)
            }

            Divider()

            // 隐私说明
            HStack(alignment: .top) {
                Image(systemName: "checkmark.shield")
                    .foregroundColor(.green)
                    .frame(width: 24)

                VStack(alignment: .leading, spacing: 4) {
                    Text("您的数据安全")
                        .font(.subheadline)
                        .fontWeight(.medium)

                    Text("所有数据处理均在本地完成，不会上传到云端。翻译和 AI 功能使用本地 Ollama 模型。")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }

            Divider()

            // 清除数据按钮
            HStack {
                Button(action: {
                    clearCache()
                }) {
                    HStack {
                        Image(systemName: "trash")
                        Text("清除缓存")
                    }
                }
                .buttonStyle(.bordered)

                Spacer()
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
    }

    // MARK: - 帮助与支持区域

    private var helpSupportSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "questionmark.circle.fill")
                    .foregroundColor(.blue)
                Text("帮助与支持")
                    .font(.headline)
            }

            HStack(spacing: 12) {
                // 使用文档
                Button(action: {
                    if let url = URL(string: "https://github.com/anthropics/maccortex") {
                        NSWorkspace.shared.open(url)
                    }
                }) {
                    VStack(spacing: 8) {
                        Image(systemName: "book")
                            .font(.title2)
                        Text("使用文档")
                            .font(.caption)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.secondary.opacity(0.1))
                    .cornerRadius(8)
                }
                .buttonStyle(.plain)

                // 问题反馈
                Button(action: {
                    if let url = URL(string: "https://github.com/anthropics/maccortex/issues") {
                        NSWorkspace.shared.open(url)
                    }
                }) {
                    VStack(spacing: 8) {
                        Image(systemName: "exclamationmark.bubble")
                            .font(.title2)
                        Text("问题反馈")
                            .font(.caption)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.secondary.opacity(0.1))
                    .cornerRadius(8)
                }
                .buttonStyle(.plain)

                // 导出诊断
                Button(action: {
                    exportDiagnostics()
                }) {
                    VStack(spacing: 8) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.title2)
                        Text("导出诊断")
                            .font(.caption)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.secondary.opacity(0.1))
                    .cornerRadius(8)
                }
                .buttonStyle(.plain)
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
    }

    // MARK: - Helper Methods

    private func clearCache() {
        let path = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/MacCortex/cache")
        try? FileManager.default.removeItem(at: path)
        print("[Settings] 缓存已清除")
    }

    private func exportDiagnostics() {
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.json]
        panel.nameFieldStringValue = "MacCortex_Diagnostics_\(Date().ISO8601Format()).json"

        if panel.runModal() == .OK, let url = panel.url {
            let diagnostics: [String: Any] = [
                "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown",
                "build_number": Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "Unknown",
                "os_version": ProcessInfo.processInfo.operatingSystemVersionString,
                "has_full_disk_access": appState.hasFullDiskAccess,
                "has_accessibility": appState.hasAccessibilityPermission,
                "timestamp": ISO8601DateFormatter().string(from: Date())
            ]

            if let data = try? JSONSerialization.data(withJSONObject: diagnostics, options: .prettyPrinted) {
                try? data.write(to: url)
            }
        }
    }
}

// MARK: - 权限管理行

struct PermissionManagementRow: View {
    let icon: String
    let name: String
    let description: String
    let isGranted: Bool
    let isRequired: Bool
    let onOpenSettings: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // 图标
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(isGranted ? .green : .orange)
                .frame(width: 32)

            // 信息
            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(name)
                        .font(.subheadline)
                        .fontWeight(.medium)

                    if isRequired {
                        Text("必需")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 1)
                            .background(Color.red.opacity(0.2))
                            .foregroundColor(.red)
                            .cornerRadius(3)
                    }
                }

                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            // 状态和操作
            if isGranted {
                HStack(spacing: 4) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    Text("已授予")
                        .font(.caption)
                        .foregroundColor(.green)
                }
            } else {
                Button("授予权限") {
                    onOpenSettings()
                }
                .font(.caption)
                .buttonStyle(.borderedProminent)
                .tint(.blue)
            }
        }
        .padding(12)
        .background(isGranted ? Color.green.opacity(0.05) : Color.orange.opacity(0.05))
        .cornerRadius(8)
    }
}

// MARK: - 连接状态行

struct ConnectionStatusRow: View {
    let icon: String
    let name: String
    let checkConnection: () async -> Bool

    @State private var isConnected: Bool? = nil
    @State private var isChecking = false

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundColor(.secondary)
                .frame(width: 24)

            Text(name)
                .font(.subheadline)

            Spacer()

            if isChecking {
                ProgressView()
                    .scaleEffect(0.7)
            } else if let connected = isConnected {
                HStack(spacing: 4) {
                    Circle()
                        .fill(connected ? Color.green : Color.red)
                        .frame(width: 8, height: 8)
                    Text(connected ? "已连接" : "未连接")
                        .font(.caption)
                        .foregroundColor(connected ? .green : .red)
                }
            } else {
                Button("检测") {
                    Task {
                        await checkStatus()
                    }
                }
                .font(.caption)
                .buttonStyle(.bordered)
            }
        }
        .onAppear {
            Task {
                await checkStatus()
            }
        }
    }

    private func checkStatus() async {
        isChecking = true
        let result = await checkConnection()
        await MainActor.run {
            isConnected = result
            isChecking = false
        }
    }
}

struct PermissionStatusRow: View {
    let icon: String
    let name: String
    let isGranted: Bool
    let isRequired: Bool

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(isGranted ? .green : .orange)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(name)
                        .font(.subheadline)

                    if isRequired {
                        Text("必需")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 1)
                            .background(Color.red.opacity(0.2))
                            .foregroundColor(.red)
                            .cornerRadius(3)
                    }
                }

                Text(isGranted ? "已授予" : "未授予")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Image(systemName: isGranted ? "checkmark.circle.fill" : "xmark.circle")
                .foregroundColor(isGranted ? .green : .orange)
        }
    }
}

struct StatusRow: View {
    let icon: String
    let text: String
    let status: Status

    enum Status {
        case completed, pending, inProgress

        var color: Color {
            switch self {
            case .completed: return .green
            case .pending: return .gray
            case .inProgress: return .blue
            }
        }
    }

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(status.color)
            Text(text)
            Spacer()
        }
    }
}

// MARK: - Backend API 测试面板（Phase 2 Week 2 Day 6-7）

struct BackendAPITestPanel: View {
    @Environment(AppState.self) private var appState
    @State private var backendStatus: String = "检查中..."
    @State private var statusColor: Color = .gray
    @State private var isTestingAPI: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Backend API 连接")
                    .font(.subheadline)
                    .fontWeight(.medium)

                Spacer()

                // 连接状态指示器
                HStack(spacing: 4) {
                    Circle()
                        .fill(statusColor)
                        .frame(width: 8, height: 8)
                    Text(backendStatus)
                        .font(.system(size: 10))
                        .foregroundStyle(.secondary)
                }
            }

            // API 测试按钮
            HStack(spacing: 8) {
                Button(action: {
                    Task {
                        await checkBackendStatus()
                    }
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: "arrow.triangle.2.circlepath")
                            .font(.system(size: 10))
                        Text("检查连接")
                            .font(.system(size: 10))
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color.blue.opacity(0.1))
                    .foregroundColor(.blue)
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)

                Button(action: {
                    Task {
                        await testPatternExecution()
                    }
                }) {
                    HStack(spacing: 4) {
                        if isTestingAPI {
                            ProgressView()
                                .scaleEffect(0.6)
                        } else {
                            Image(systemName: "play.fill")
                                .font(.system(size: 10))
                        }
                        Text("测试 Pattern")
                            .font(.system(size: 10))
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color.green.opacity(0.1))
                    .foregroundColor(.green)
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
                .disabled(isTestingAPI || appState.isProcessingPattern)
            }

            // 显示最后的执行结果
            if let result = appState.lastPatternResult {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("最后执行:")
                            .font(.system(size: 10))
                            .foregroundStyle(.secondary)
                        Text(result.patternId)
                            .font(.system(size: 10, weight: .medium))
                        Spacer()
                        Text(result.success ? "✅" : "❌")
                            .font(.system(size: 10))
                    }

                    Text(result.output)
                        .font(.system(size: 9))
                        .lineLimit(3)
                        .foregroundStyle(.primary)

                    HStack {
                        Text("耗时: \(String(format: "%.2f", result.duration))s")
                            .font(.system(size: 9))
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(result.timestamp, style: .time)
                            .font(.system(size: 9))
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 6)
                .padding(.horizontal, 8)
                .background(result.success ? Color.green.opacity(0.05) : Color.red.opacity(0.05))
                .cornerRadius(6)
            }

            // 显示错误信息
            if let error = appState.lastError {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 10))
                        .foregroundColor(.red)
                    Text(error)
                        .font(.system(size: 9))
                        .foregroundColor(.red)
                        .lineLimit(2)
                }
                .padding(.vertical, 4)
                .padding(.horizontal, 8)
                .background(Color.red.opacity(0.05))
                .cornerRadius(6)
            }
        }
        .onAppear {
            Task {
                await checkBackendStatus()
            }
        }
    }

    // MARK: - 私有方法

    /// 检查 Backend 连接状态
    private func checkBackendStatus() async {
        let apiClient = APIClient.shared

        let isAvailable = await apiClient.isBackendAvailable()

        await MainActor.run {
            if isAvailable {
                backendStatus = "已连接"
                statusColor = .green
            } else {
                backendStatus = "未连接"
                statusColor = .red
            }
        }
    }

    /// 测试 Pattern 执行
    private func testPatternExecution() async {
        await MainActor.run {
            isTestingAPI = true
        }

        let _ = await appState.executePattern(
            "summarize",
            text: "Phase 2 Week 2 Backend API 集成测试。测试从 SwiftUI Frontend 调用 Python Backend 的 Pattern 执行功能。",
            parameters: ["length": "short", "language": "zh-CN"]
        )

        await MainActor.run {
            isTestingAPI = false
        }
    }
}

#Preview {
    ContentView()
        .environment(AppState())
}
