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

struct ContentView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        Group {
            if appState.isFirstRun {
                // Phase 0.5 Day 8: 首次启动引导
                FirstRunView()
            } else {
                // 主界面（Phase 2 开发）
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
    @State private var selectedTab = 0  // Phase 3 Week 2: 标签选择

    var body: some View {
        TabView(selection: $selectedTab) {
            // Phase 3 Week 2 Day 1-2: 翻译界面
            TranslationView()
                .tabItem {
                    Label("翻译", systemImage: "character.bubble")
                }
                .tag(0)

            // Phase 3 Week 2 Day 3-4: 批量翻译界面
            BatchTranslationView()
                .tabItem {
                    Label("批量", systemImage: "list.bullet")
                }
                .tag(1)

            // Phase 3 Week 2 Day 5: 缓存统计界面
            CacheStatsView()
                .tabItem {
                    Label("统计", systemImage: "chart.bar")
                }
                .tag(2)

            // 原有的权限状态页面
            permissionsView
                .tabItem {
                    Label("权限", systemImage: "lock.shield")
                }
                .tag(3)
        }
    }

    // 权限状态视图（原有内容）
    private var permissionsView: some View {
        NavigationView {
            VStack(spacing: 30) {
                // 顶部标题区
                VStack(spacing: 10) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 80))
                        .foregroundColor(.blue)

                    Text("MacCortex")
                        .font(.largeTitle)
                        .fontWeight(.bold)

                    Text("Phase 3 - aya-23 翻译模型")
                        .font(.caption)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 4)
                        .background(Color.green.opacity(0.2))
                        .foregroundColor(.green)
                        .cornerRadius(4)
                }

                Spacer()

                // 权限状态卡片
                VStack(alignment: .leading, spacing: 15) {
                    HStack {
                        Image(systemName: "lock.shield")
                            .foregroundColor(.blue)
                        Text("权限状态")
                            .font(.headline)
                    }

                    PermissionStatusRow(
                        icon: "folder.fill",
                        name: "Full Disk Access",
                        isGranted: appState.hasFullDiskAccess,
                        isRequired: true
                    )

                    PermissionStatusRow(
                        icon: "cursorarrow.rays",
                        name: "Accessibility",
                        isGranted: appState.hasAccessibilityPermission,
                        isRequired: false
                    )

                    // 权限管理按钮
                    Button(action: {
                        showSettings = true
                    }) {
                        HStack {
                            Image(systemName: "gear")
                            Text("管理权限")
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(Color.blue.opacity(0.1))
                        .foregroundColor(.blue)
                        .cornerRadius(8)
                    }
                }
                .padding()
                .background(Color.secondary.opacity(0.1))
                .cornerRadius(10)

                // Phase 状态
                VStack(alignment: .leading, spacing: 15) {
                    HStack {
                        Image(systemName: "list.bullet.clipboard")
                            .foregroundColor(.blue)
                        Text("开发进度")
                            .font(.headline)
                    }

                    StatusRow(icon: "checkmark.circle.fill",
                             text: "Phase 0.5: 签名与公证",
                             status: .completed)

                    StatusRow(icon: "checkmark.circle.fill",
                             text: "Phase 1: Python Backend",
                             status: .completed)

                    StatusRow(icon: "checkmark.circle.fill",
                             text: "Phase 1.5: 安全强化",
                             status: .completed)

                    StatusRow(icon: "circle.fill",
                             text: "Phase 2 Week 1: SwiftUI 架构",
                             status: .inProgress)

                    StatusRow(icon: "circle",
                             text: "Phase 2 Week 2: 浮动工具栏",
                             status: .pending)
                }
                .padding()
                .background(Color.secondary.opacity(0.1))
                .cornerRadius(10)

                // Phase 2: 功能测试区
                VStack(alignment: .leading, spacing: 15) {
                    HStack {
                        Image(systemName: "testtube.2")
                            .foregroundColor(.blue)
                        Text("Phase 2 功能测试")
                            .font(.headline)
                    }

                    // 浮动工具栏开关
                    Toggle("显示浮动工具栏", isOn: Binding(
                        get: { appState.showFloatingToolbar },
                        set: { appState.showFloatingToolbar = $0 }
                    ))
                    .toggleStyle(.switch)

                    Divider()

                    // 场景检测控制
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("智能场景检测")
                                .font(.subheadline)
                                .fontWeight(.medium)

                            Spacer()

                            Button(action: {
                                if SceneDetector.shared.isDetecting {
                                    appState.stopSceneDetection()
                                } else {
                                    appState.startSceneDetection()
                                }
                            }) {
                                HStack(spacing: 4) {
                                    Image(systemName: SceneDetector.shared.isDetecting ? "stop.circle.fill" : "play.circle.fill")
                                    Text(SceneDetector.shared.isDetecting ? "停止" : "启动")
                                }
                                .font(.system(size: 11))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 4)
                                .background(SceneDetector.shared.isDetecting ? Color.red.opacity(0.1) : Color.green.opacity(0.1))
                                .foregroundColor(SceneDetector.shared.isDetecting ? .red : .green)
                                .cornerRadius(6)
                            }
                            .buttonStyle(.plain)
                        }

                        // 实时检测信息
                        if SceneDetector.shared.isDetecting {
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Text("活动应用:")
                                        .font(.system(size: 10))
                                        .foregroundStyle(.secondary)
                                    Text(SceneDetector.shared.activeApplicationName.isEmpty ? "未检测" : SceneDetector.shared.activeApplicationName)
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundStyle(.primary)
                                }

                                HStack {
                                    Text("窗口标题:")
                                        .font(.system(size: 10))
                                        .foregroundStyle(.secondary)
                                    Text(SceneDetector.shared.activeWindowTitle.isEmpty ? "未授权" : SceneDetector.shared.activeWindowTitle)
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundStyle(.primary)
                                        .lineLimit(1)
                                }

                                HStack {
                                    Text("检测场景:")
                                        .font(.system(size: 10))
                                        .foregroundStyle(.secondary)
                                    HStack(spacing: 4) {
                                        Image(systemName: SceneDetector.shared.currentScene.icon)
                                            .font(.system(size: 10))
                                        Text(SceneDetector.shared.currentScene.rawValue)
                                            .font(.system(size: 10, weight: .medium))
                                        Text("(\(Int(SceneDetector.shared.sceneConfidence * 100))%)")
                                            .font(.system(size: 9))
                                            .foregroundStyle(.secondary)
                                    }
                                    .foregroundStyle(.primary)
                                }
                            }
                            .padding(.vertical, 6)
                            .padding(.horizontal, 8)
                            .background(Color.secondary.opacity(0.05))
                            .cornerRadius(6)
                        }
                    }

                    // 场景检测测试
                    VStack(alignment: .leading, spacing: 8) {
                        Text("场景检测测试")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)

                        HStack(spacing: 8) {
                            ForEach(DetectedScene.allCases.prefix(4), id: \.self) { scene in
                                Button(action: {
                                    appState.updateDetectedScene(scene, confidence: Double.random(in: 0.75...0.95))
                                }) {
                                    VStack(spacing: 4) {
                                        Image(systemName: scene.icon)
                                            .font(.system(size: 16))
                                        Text(scene.rawValue)
                                            .font(.system(size: 9))
                                    }
                                    .frame(width: 60, height: 50)
                                    .background(appState.detectedScene == scene ? Color.blue.opacity(0.2) : Color.secondary.opacity(0.1))
                                    .cornerRadius(8)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // 信任等级测试
                    VStack(alignment: .leading, spacing: 8) {
                        Text("信任等级切换")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)

                        HStack(spacing: 8) {
                            ForEach(TrustLevel.allCases, id: \.self) { level in
                                Button(action: {
                                    appState.setTrustLevel(level)
                                }) {
                                    Text(level.displayName)
                                        .font(.system(size: 10))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(appState.currentTrustLevel == level ? level.color.opacity(0.3) : Color.secondary.opacity(0.1))
                                        .foregroundColor(appState.currentTrustLevel == level ? level.color : .secondary)
                                        .cornerRadius(6)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    Divider()

                    // Backend API 测试（Phase 2 Week 2 Day 6-7）
                    BackendAPITestPanel()
                }
                .padding()
                .background(Color.blue.opacity(0.05))
                .cornerRadius(10)

                Spacer()
            }
            .padding()
            .navigationTitle("MacCortex")
            .overlay(
                // 浮动工具栏叠加层
                Group {
                    if appState.showFloatingToolbar {
                        FloatingToolbarView()
                            .position(x: 200, y: 100)
                            .transition(.scale.combined(with: .opacity))
                    }
                }
            )
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
