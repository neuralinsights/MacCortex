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

@main
struct MacCortexApp: App {
    @State private var appState = AppState()

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

    // MARK: - Phase 2: 场景检测
    var detectedScene: DetectedScene? = nil
    var sceneConfidence: Double = 0.0

    // MARK: - Phase 2: 信任等级
    var currentTrustLevel: TrustLevel = .R0
    var pendingOperations: [PendingOperation] = []

    // MARK: - UI 状态
    var showFloatingToolbar: Bool = false
    var showSettings: Bool = false

    init() {
        checkPermissions()
    }

    func checkPermissions() {
        // Phase 0.5 Day 6-7: 集成 FullDiskAccessManager
        hasFullDiskAccess = FullDiskAccessManager.shared.hasFullDiskAccess

        // Phase 1 Week 1 Day 1-2: 集成 AccessibilityManager
        hasAccessibilityPermission = AccessibilityManager.shared.hasAccessibilityPermission

        // 检查是否首次运行
        let defaults = UserDefaults.standard
        isFirstRun = !defaults.bool(forKey: "HasLaunchedBefore")

        if isFirstRun {
            defaults.set(true, forKey: "HasLaunchedBefore")
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

    /// 执行 Pattern
    @MainActor
    func executePattern(_ patternId: String, text: String, parameters: [String: Any] = [:]) async -> PatternResult {
        isProcessingPattern = true
        currentPatternId = patternId

        // TODO: Phase 2 Week 2 - 调用 Python Backend API
        // 临时模拟结果
        try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 秒

        let result = PatternResult(
            patternId: patternId,
            output: "模拟输出（Phase 2 Week 2 将集成真实 Backend）",
            success: true,
            duration: 1.0
        )

        lastPatternResult = result
        isProcessingPattern = false
        currentPatternId = nil

        return result
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

    /// 添加待审批操作
    @MainActor
    func addPendingOperation(_ operation: PendingOperation) {
        pendingOperations.append(operation)
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
enum TrustLevel: Int, CaseIterable {
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
