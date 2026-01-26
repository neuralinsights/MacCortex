//
//  SwarmViewModel.swift
//  MacCortex
//
//  Created by Claude Code on 2026-01-22.
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import Foundation
import SwiftUI
import Combine

/// Swarm 编排视图模型
///
/// 连接 SwarmAPIClient 和 SwiftUI 视图层，负责：
/// - 管理用户输入状态
/// - 处理任务提交
/// - 协调 UI 更新
/// - 处理错误与加载状态
@MainActor
class SwarmViewModel: ObservableObject {

    // MARK: - Published Properties

    /// API 客户端
    @Published var apiClient: SwarmAPIClient

    /// 用户输入文本
    @Published var userInput: String = ""

    /// 工作空间路径
    @Published var workspacePath: String = ""

    /// 启用 Human-in-the-Loop
    @Published var enableHITL: Bool = true

    /// 启用代码审查
    @Published var enableCodeReview: Bool = false

    /// 是否正在提交任务
    @Published var isSubmitting: Bool = false

    /// 错误消息
    @Published var errorMessage: String?

    /// 是否显示错误弹窗
    @Published var showError: Bool = false

    /// 任务历史
    @Published var taskHistory: [TaskHistoryItem] = []

    /// 是否正在加载历史
    @Published var isLoadingHistory: Bool = false

    /// 当前选中的任务（用于详情查看）
    @Published var selectedTask: SwarmTask?

    // MARK: - Private Properties

    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization

    /// 初始化视图模型
    /// - Parameter apiClient: API 客户端（默认使用 localhost:8000）
    init(apiClient: SwarmAPIClient) {
        self.apiClient = apiClient

        // 设置默认工作空间路径
        if let homeDirectory = FileManager.default.homeDirectoryForCurrentUser.path as String? {
            self.workspacePath = homeDirectory + "/workspace"
        }

        // 监听 API 客户端的错误
        apiClient.$lastError
            .compactMap { $0 }
            .sink { [weak self] error in
                Task { @MainActor in
                    self?.handleError(error)
                }
            }
            .store(in: &cancellables)
    }

    // MARK: - Task Submission

    /// 提交新任务
    func submitTask() async {
        // 验证输入
        guard !userInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            handleError("请输入任务描述")
            return
        }

        guard !workspacePath.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            handleError("请输入工作空间路径")
            return
        }

        isSubmitting = true
        errorMessage = nil

        do {
            let taskId = try await apiClient.createTask(
                userInput: userInput,
                workspacePath: workspacePath,
                enableHITL: enableHITL,
                enableCodeReview: enableCodeReview
            )

            // 任务创建成功
            print("✅ 任务创建成功: \(taskId)")

            // 清空输入
            userInput = ""

            // 刷新历史记录
            await loadTaskHistory()

        } catch {
            handleError("任务创建失败: \(error.localizedDescription)")
        }

        isSubmitting = false
    }

    // MARK: - Task History Management

    /// 加载任务历史
    /// - Parameters:
    ///   - status: 状态过滤（all/created/running/completed/failed）
    ///   - limit: 每页数量
    ///   - offset: 偏移量
    func loadTaskHistory(
        status: String = "all",
        limit: Int = 20,
        offset: Int = 0
    ) async {
        isLoadingHistory = true

        do {
            let historyResponse = try await apiClient.fetchTaskHistory(
                status: status,
                limit: limit,
                offset: offset
            )

            taskHistory = historyResponse.tasks

        } catch {
            handleError("加载历史失败: \(error.localizedDescription)")
        }

        isLoadingHistory = false
    }

    /// 查询任务详情
    /// - Parameter taskId: 任务 ID
    func loadTaskDetails(taskId: String) async {
        do {
            let task = try await apiClient.fetchTaskStatus(taskId: taskId)
            selectedTask = task
        } catch {
            handleError("加载任务详情失败: \(error.localizedDescription)")
        }
    }

    // MARK: - HITL Approval

    /// 审批 HITL 中断
    /// - Parameters:
    ///   - action: 审批动作
    ///   - modifiedData: 修改后的数据（仅 modify 动作需要）
    func approveInterrupt(
        action: ApprovalAction,
        modifiedData: [String: Any]? = nil
    ) async {
        guard let currentTask = apiClient.currentTask,
              let interrupt = apiClient.activeInterrupt else {
            handleError("无活跃的中断")
            return
        }

        do {
            try await apiClient.approveInterrupt(
                taskId: currentTask.id,
                interruptId: interrupt.id,
                action: action,
                modifiedData: modifiedData
            )

            print("✅ 审批成功: \(action.displayName)")

        } catch {
            handleError("审批失败: \(error.localizedDescription)")
        }
    }

    // MARK: - File Selection

    /// 选择工作空间路径
    func selectWorkspacePath() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.prompt = "选择工作空间"

        if panel.runModal() == .OK {
            if let url = panel.url {
                workspacePath = url.path
            }
        }
    }

    // MARK: - Error Handling

    /// 处理错误
    /// - Parameter message: 错误消息
    private func handleError(_ message: String) {
        errorMessage = message
        showError = true
    }

    /// 清除错误
    func clearError() {
        errorMessage = nil
        showError = false
    }

    /// 清除当前任务（返回任务输入界面）
    func clearCurrentTask() {
        apiClient.currentTask = nil
        apiClient.activeInterrupt = nil
        apiClient.disconnectWebSocket()
    }

    // MARK: - Computed Properties

    /// 是否可以提交任务
    var canSubmit: Bool {
        !userInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        !workspacePath.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        !isSubmitting
    }

    /// 提交按钮文本
    var submitButtonText: String {
        isSubmitting ? "提交中..." : "开始执行"
    }
}
