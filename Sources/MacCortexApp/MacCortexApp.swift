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

// MacCortex 主应用入口
// Phase 0.5 - 基础设施
// Phase 2 - Desktop GUI + Observation Framework
// 创建时间：2026-01-20
// 更新时间：2026-01-21 (Phase 2 Day 1: Observation Framework 升级)

import SwiftUI
import Observation
import PermissionsKit
import AppIntents

@main
struct MacCortexApp: App {
    @State private var appState = AppState()

    init() {
        // Phase 2 Week 3 Day 15: 延迟 App Intents 注册（启动优化）
        // 不阻塞主启动流程，首次显示后再注册
        if #available(macOS 13.0, *) {
            Task.detached(priority: .background) {
                // 延迟 0.5 秒，等待主窗口显示后再注册
                try? await Task.sleep(nanoseconds: 500_000_000)
                MacCortexAppShortcuts.updateAppShortcutParameters()
            }
        }

        // Phase 3 Week 3 Day 5: 注册全局快捷键
        Task { @MainActor in
            // 延迟 1 秒，等待应用完全启动后再注册
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            GlobalHotKeyManager.shared.registerHotKeys()
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(appState)
                .frame(minWidth: 800, minHeight: 600)
        }
        .commands {
            CommandGroup(replacing: .appInfo) {
                Button("关于 MacCortex") {
                    // 显示关于窗口
                }
            }
        }

        // Phase 3 Week 3 后续: 偏好设置窗口（Cmd+,）
        Settings {
            SettingsView()
                .environment(appState)
        }
    }
}

// MARK: - AppState（Observation Framework）

/// 应用全局状态管理
/// Phase 2 升级：使用 @Observable 替代 ObservableObject
@Observable
class AppState {
    // MARK: - 权限状态
    var hasFullDiskAccess: Bool = false
    var hasAccessibilityPermission: Bool = false
    var isFirstRun: Bool = true

    // MARK: - Phase 2: Pattern 执行状态
    var isProcessingPattern: Bool = false
    var currentPatternId: String? = nil
    var lastPatternResult: PatternResult? = nil
    var lastError: String? = nil  // Phase 2 Week 2: API 错误信息

    // MARK: - Phase 2: 场景检测
    var detectedScene: DetectedScene? = nil
    var sceneConfidence: Double = 0.0

    // MARK: - Phase 2: 信任等级
    var currentTrustLevel: TrustLevel = .R0
    var pendingOperations: [PendingOperation] = []

    // MARK: - UI 状态
    var showFloatingToolbar: Bool = false
    var showSettings: Bool = false

    // MARK: - Phase 2 Week 2 Day 8-9: 风险评估与确认
    var showRiskConfirmation: Bool = false
    var currentRiskAssessment: RiskAssessment? = nil
    var riskConfirmationResult: Bool? = nil

    // MARK: - Phase 2 Week 3 Day 11-12: MCP 服务器管理
    var showMCPServerList: Bool = false
    var mcpServers: [MCPServer] = []
    var isLoadingMCPServers: Bool = false

    init() {
        // Phase 2 Week 3 Day 15: 异步权限检查（启动优化）
        // 快速检查首次运行状态，权限检查异步执行
        let defaults = UserDefaults.standard
        isFirstRun = !defaults.bool(forKey: "HasLaunchedBefore")

        if isFirstRun {
            defaults.set(true, forKey: "HasLaunchedBefore")
        }

        // 异步执行权限检查，不阻塞主线程
        Task.detached(priority: .userInitiated) {
            await self.checkPermissions()
        }
    }

    func checkPermissions() async {
        // Phase 0.5 Day 6-7: 集成 FullDiskAccessManager
        let fda = FullDiskAccessManager.shared.hasFullDiskAccess

        // Phase 1 Week 1 Day 1-2: 集成 AccessibilityManager
        let accessibility = AccessibilityManager.shared.hasAccessibilityPermission

        // 更新主线程状态
        await MainActor.run {
            self.hasFullDiskAccess = fda
            self.hasAccessibilityPermission = accessibility
        }
    }

    /// 检查是否所有必需权限已授予
    var hasAllRequiredPermissions: Bool {
        return hasFullDiskAccess
        // 注意：Accessibility 不是必需权限，仅在需要自动化时才请求
    }

    /// 请求 Full Disk Access 权限
    func requestFullDiskAccess() {
        FullDiskAccessManager.shared.requestFullDiskAccess(timeout: 60, interval: 2) { [weak self] granted in
            guard let self = self else { return }
            Task { @MainActor in
                self.hasFullDiskAccess = granted
                if granted && self.hasAllRequiredPermissions {
                    self.isFirstRun = false
                }
            }
        }
    }

    /// 请求 Accessibility 权限
    func requestAccessibilityPermission() {
        AccessibilityManager.shared.requestAccessibilityPermission(timeout: 60, interval: 2) { [weak self] granted in
            guard let self = self else { return }
            Task { @MainActor in
                self.hasAccessibilityPermission = granted
            }
        }
    }

    // MARK: - Phase 2: Pattern 执行

    /// 执行 Pattern（调用 Backend API，集成风险评估）
    /// - Parameters:
    ///   - patternId: Pattern ID
    ///   - text: 输入文本
    ///   - parameters: 参数字典
    ///   - source: 输入来源（默认为用户输入）
    ///   - outputTarget: 输出目标（默认为显示）
    /// - Returns: Pattern 执行结果
    @MainActor
    func executePattern(
        _ patternId: String,
        text: String,
        parameters: [String: String] = [:],
        source: OperationTask.InputSource = .user,
        outputTarget: OperationTask.OutputTarget = .display
    ) async -> PatternResult {
        isProcessingPattern = true
        currentPatternId = patternId
        lastError = nil

        let startTime = Date()

        // Phase 2 Week 2 Day 8-9: 风险评估
        let task = OperationTask(
            patternId: patternId,
            text: text,
            parameters: parameters,
            source: source,
            outputTarget: outputTarget
        )

        let assessment = TrustEngine.shared.assessRisk(for: task)

        // 如果需要确认，显示确认对话框
        if assessment.requiresConfirmation {
            let confirmed = await requestRiskConfirmation(assessment)

            if !confirmed {
                // 用户取消操作
                let result = PatternResult(
                    patternId: patternId,
                    output: "操作已取消",
                    success: false,
                    duration: Date().timeIntervalSince(startTime)
                )

                lastPatternResult = result
                isProcessingPattern = false
                currentPatternId = nil

                return result
            }
        }

        // 记录操作到历史
        TrustEngine.shared.recordOperation(task)

        // 调用 Backend API
        do {
            let apiClient = APIClient.shared
            let response = try await apiClient.executePattern(
                patternId: patternId,
                text: text,
                parameters: parameters
            )

            let duration = Date().timeIntervalSince(startTime)

            let result = PatternResult(
                patternId: patternId,
                output: response.output,
                success: response.success,
                duration: duration
            )

            lastPatternResult = result
            isProcessingPattern = false
            currentPatternId = nil

            return result

        } catch {
            // 错误处理
            let duration = Date().timeIntervalSince(startTime)
            lastError = error.localizedDescription

            let result = PatternResult(
                patternId: patternId,
                output: "执行失败: \(error.localizedDescription)",
                success: false,
                duration: duration
            )

            lastPatternResult = result
            isProcessingPattern = false
            currentPatternId = nil

            return result
        }
    }

    /// 请求风险确认
    /// - Parameter assessment: 风险评估结果
    /// - Returns: 用户是否批准
    @MainActor
    private func requestRiskConfirmation(_ assessment: RiskAssessment) async -> Bool {
        // 设置当前风险评估
        currentRiskAssessment = assessment
        showRiskConfirmation = true
        riskConfirmationResult = nil

        // 等待用户响应
        while riskConfirmationResult == nil {
            try? await Task.sleep(nanoseconds: 100_000_000)  // 0.1 秒
        }

        let result = riskConfirmationResult ?? false

        // 清理状态
        showRiskConfirmation = false
        currentRiskAssessment = nil
        riskConfirmationResult = nil

        return result
    }

    /// 用户确认风险操作
    @MainActor
    func confirmRiskOperation() {
        riskConfirmationResult = true
    }

    /// 用户取消风险操作
    @MainActor
    func cancelRiskOperation() {
        riskConfirmationResult = false
    }

    // MARK: - Phase 2: 场景检测

    /// 更新检测到的场景
    @MainActor
    func updateDetectedScene(_ scene: DetectedScene, confidence: Double) {
        detectedScene = scene
        sceneConfidence = confidence
    }

    // MARK: - Phase 2: 信任等级管理

    /// 设置信任等级
    @MainActor
    func setTrustLevel(_ level: TrustLevel) {
        currentTrustLevel = level
    }

    /// 添加待审批操作（Phase 2 Week 3 Day 15: 限制队列大小）
    @MainActor
    func addPendingOperation(_ operation: PendingOperation) {
        pendingOperations.append(operation)

        // 限制队列大小为 100，避免内存无限增长
        if pendingOperations.count > 100 {
            // 移除最旧的已完成/已拒绝操作
            pendingOperations.removeAll { op in
                op.status != .pending && op.timestamp.timeIntervalSinceNow < -3600  // 1 小时前
            }
        }
    }

    /// 批准操作
    @MainActor
    func approveOperation(_ operationId: UUID) {
        if let index = pendingOperations.firstIndex(where: { $0.id == operationId }) {
            pendingOperations[index].status = .approved
        }
    }

    /// 拒绝操作
    @MainActor
    func rejectOperation(_ operationId: UUID) {
        if let index = pendingOperations.firstIndex(where: { $0.id == operationId }) {
            pendingOperations[index].status = .rejected
            pendingOperations.remove(at: index)
        }
    }

    // MARK: - Phase 2 Week 3 Day 11-12: MCP 服务器管理

    /// 加载 MCP 服务器列表
    @MainActor
    func loadMCPServers() async {
        isLoadingMCPServers = true
        let servers = await MCPManager.shared.getAllServers()
        mcpServers = servers
        isLoadingMCPServers = false
    }

    /// 加载单个 MCP 服务器
    @MainActor
    func loadMCPServer(url: URL) async throws {
        let _ = try await MCPManager.shared.loadServer(url: url)
        await loadMCPServers()
    }

    /// 卸载 MCP 服务器
    @MainActor
    func unloadMCPServer(id: UUID) async {
        await MCPManager.shared.unloadServer(id: id)
        await loadMCPServers()
    }
}

// MARK: - 数据模型（Phase 2）

/// Pattern 执行结果
struct PatternResult: Identifiable {
    let id = UUID()
    let patternId: String
    let output: String
    let success: Bool
    let duration: TimeInterval
    let timestamp = Date()
}

/// 检测到的场景
enum DetectedScene: String, CaseIterable {
    case browsing = "网页浏览"
    case coding = "代码编写"
    case writing = "文档编写"
    case reading = "阅读文档"
    case meeting = "视频会议"
    case unknown = "未知场景"

    var icon: String {
        switch self {
        case .browsing: return "safari"
        case .coding: return "chevron.left.forwardslash.chevron.right"
        case .writing: return "doc.text"
        case .reading: return "book"
        case .meeting: return "video"
        case .unknown: return "questionmark.circle"
        }
    }
}

/// 信任等级（渐进式信任机制）
enum TrustLevel: Int, CaseIterable, Codable {
    case R0 = 0 // 只读（Read-only）
    case R1 = 1 // 低风险写入（文本编辑）
    case R2 = 2 // 中风险操作（文件移动）
    case R3 = 3 // 高风险操作（删除文件）

    var displayName: String {
        switch self {
        case .R0: return "R0 - 只读"
        case .R1: return "R1 - 文本编辑"
        case .R2: return "R2 - 文件操作"
        case .R3: return "R3 - 高风险"
        }
    }

    var color: Color {
        switch self {
        case .R0: return .green
        case .R1: return .blue
        case .R2: return .orange
        case .R3: return .red
        }
    }
}

/// 待审批操作
struct PendingOperation: Identifiable {
    let id = UUID()
    let type: OperationType
    let description: String
    let requiredTrustLevel: TrustLevel
    var status: OperationStatus = .pending
    let timestamp = Date()

    enum OperationType: String {
        case fileRead = "文件读取"
        case fileWrite = "文件写入"
        case fileMove = "文件移动"
        case fileDelete = "文件删除"
        case executeScript = "执行脚本"
    }

    enum OperationStatus {
        case pending
        case approved
        case rejected
    }
}
