//
//  SwarmOrchestrationView.swift
//  MacCortex
//
//  Created by Claude Code on 2026-01-22.
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import SwiftUI

/// Swarm 编排主视图
///
/// MacCortex Slow Lane 的核心 UI，提供：
/// - 任务输入与提交
/// - 实时工作流可视化
/// - HITL 审批交互
/// - 任务历史管理
struct SwarmOrchestrationView: View {

    // MARK: - Properties

    @StateObject private var viewModel = SwarmViewModel(apiClient: SwarmAPIClient())

    // MARK: - Body

    var body: some View {
        NavigationSplitView {
            // 侧边栏：任务历史
            sidebarView
        } detail: {
            // 主视图：任务执行与可视化
            mainContentView
        }
        .navigationTitle("Swarm 编排")
        .alert("错误", isPresented: $viewModel.showError) {
            Button("确定") {
                viewModel.clearError()
            }
        } message: {
            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
            }
        }
        .sheet(item: $viewModel.apiClient.activeInterrupt) { interrupt in
            // HITL 审批弹窗
            HITLApprovalSheet(
                interrupt: interrupt,
                viewModel: viewModel
            )
        }
        .task {
            // 启动时加载历史
            await viewModel.loadTaskHistory()
        }
        // 监听 apiClient 的变化以刷新视图
        .onReceive(viewModel.apiClient.objectWillChange) { _ in
            // 空操作，仅触发 SwiftUI 重新评估视图
        }
    }

    // MARK: - Sidebar View

    @ViewBuilder
    private var sidebarView: some View {
        VStack(spacing: 0) {
            // 历史标题
            HStack {
                Text("任务历史")
                    .font(.headline)

                Spacer()

                Button {
                    Task {
                        await viewModel.loadTaskHistory()
                    }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .disabled(viewModel.isLoadingHistory)
            }
            .padding()

            Divider()

            // 历史列表
            if viewModel.isLoadingHistory {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if viewModel.taskHistory.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "tray")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)
                    Text("暂无任务")
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List(viewModel.taskHistory) { task in
                    TaskHistoryRow(task: task)
                        .onTapGesture {
                            Task {
                                await viewModel.loadTaskDetails(taskId: task.id)
                            }
                        }
                }
                .listStyle(.sidebar)
            }
        }
        .frame(minWidth: 250, idealWidth: 300)
    }

    // MARK: - Main Content View

    @ViewBuilder
    private var mainContentView: some View {
        if let currentTask = viewModel.apiClient.currentTask {
            // 有活跃任务：显示工作流可视化
            TaskDetailView(
                task: currentTask,
                connectionStatus: viewModel.apiClient.connectionStatus,
                onBack: {
                    viewModel.clearCurrentTask()
                },
                onRefresh: {
                    Task {
                        _ = try? await viewModel.apiClient.fetchTaskStatus(taskId: currentTask.id)
                    }
                }
            )
        } else {
            // 无活跃任务：显示任务输入
            TaskInputView(viewModel: viewModel)
        }
    }
}

// MARK: - Task Input View

/// 任务输入视图
struct TaskInputView: View {

    @ObservedObject var viewModel: SwarmViewModel

    var body: some View {
        VStack(spacing: 24) {
            // 标题
            VStack(spacing: 8) {
                Image(systemName: "gearshape.2.fill")
                    .font(.system(size: 48))
                    .foregroundColor(.accentColor)

                Text("Swarm 编排系统")
                    .font(.title)
                    .fontWeight(.bold)

                Text("描述您的任务，让 AI Agents 协作完成")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            .padding(.top, 40)

            // 输入表单
            VStack(alignment: .leading, spacing: 16) {
                // 任务描述
                VStack(alignment: .leading, spacing: 8) {
                    Text("任务描述")
                        .font(.headline)

                    TextEditor(text: $viewModel.userInput)
                        .frame(height: 120)
                        .font(.body)
                        .padding(8)
                        .background(Color(NSColor.textBackgroundColor))
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.secondary.opacity(0.2), lineWidth: 1)
                        )

                    Text("示例：创建一个 Python Hello World 程序")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                // 工作空间路径
                VStack(alignment: .leading, spacing: 8) {
                    Text("工作空间路径")
                        .font(.headline)

                    HStack {
                        TextField("", text: $viewModel.workspacePath)
                            .textFieldStyle(.roundedBorder)

                        Button("浏览...") {
                            viewModel.selectWorkspacePath()
                        }
                    }

                    Text("选择任务执行的目录")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                // 选项
                VStack(alignment: .leading, spacing: 12) {
                    Text("执行选项")
                        .font(.headline)

                    Toggle("启用 Human-in-the-Loop (推荐)", isOn: $viewModel.enableHITL)
                        .toggleStyle(.checkbox)

                    Toggle("启用代码审查", isOn: $viewModel.enableCodeReview)
                        .toggleStyle(.checkbox)
                }
            }
            .padding(24)
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(12)

            // 提交按钮
            Button {
                Task {
                    await viewModel.submitTask()
                }
            } label: {
                HStack {
                    if viewModel.isSubmitting {
                        ProgressView()
                            .controlSize(.small)
                    }
                    Text(viewModel.submitButtonText)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(!viewModel.canSubmit)

            Spacer()
        }
        .padding()
        .frame(maxWidth: 600)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Supporting Views

/// 任务历史行视图
struct TaskHistoryRow: View {
    let task: TaskHistoryItem

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(task.userInput)
                .font(.body)
                .lineLimit(2)

            HStack {
                Text(task.status)
                    .font(.caption)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(statusColor.opacity(0.2))
                    .foregroundColor(statusColor)
                    .cornerRadius(4)

                Spacer()

                Text(task.createdAt)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }

    private var statusColor: Color {
        switch task.status {
        case "created": return .blue
        case "running": return .orange
        case "completed": return .green
        case "failed": return .red
        case "interrupted": return .yellow
        default: return .gray
        }
    }
}

/// 任务信息卡片
struct TaskInfoCard: View {
    let task: SwarmTask

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(task.userInput ?? "未知任务")
                        .font(.headline)

                    Text("任务 ID: \(task.id)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                HStack(spacing: 8) {
                    Image(systemName: task.status.icon)
                    Text(task.status.displayName)
                }
                .font(.subheadline)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(task.status.color.opacity(0.2))
                .foregroundColor(task.status.color)
                .cornerRadius(8)
            }

            // 进度条
            ProgressView(value: task.progress)
                .progressViewStyle(.linear)

            HStack {
                Text("进度: \(Int(task.progress * 100))%")
                    .font(.caption)

                Spacer()

                if let agent = task.currentAgent {
                    Text("当前: \(agent)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Text("耗时: \(task.formattedDuration)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            // 显示任务输出（仅当任务完成或失败时）
            if (task.status == .completed || task.status == .failed), let output = task.output {
                Divider()

                VStack(alignment: .leading, spacing: 8) {
                    // 结果标题
                    HStack {
                        if output.passed == true {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            Text("任务完成")
                                .font(.headline)
                        } else {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(.red)
                            Text("任务失败")
                                .font(.headline)
                        }
                    }

                    // 摘要
                    if let summary = output.summary {
                        Text(summary)
                            .font(.body)
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color(NSColor.textBackgroundColor))
                            .cornerRadius(8)
                            .textSelection(.enabled)
                    }

                    // 成就列表
                    if let achievements = output.achievements, !achievements.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("完成项:")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            ForEach(achievements, id: \.self) { item in
                                HStack(alignment: .top) {
                                    Image(systemName: "checkmark")
                                        .foregroundColor(.green)
                                        .font(.caption)
                                    Text(item)
                                        .font(.caption)
                                }
                            }
                        }
                    }

                    // 问题列表
                    if let issues = output.issues, !issues.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("问题:")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            ForEach(issues, id: \.self) { issue in
                                HStack(alignment: .top) {
                                    Image(systemName: "exclamationmark.triangle")
                                        .foregroundColor(.orange)
                                        .font(.caption)
                                    Text(issue)
                                        .font(.caption)
                                }
                            }
                        }
                    }

                    // 创建的文件
                    if let filesCreated = output.filesCreated, !filesCreated.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("创建的文件:")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            ForEach(filesCreated, id: \.self) { file in
                                HStack {
                                    Image(systemName: "doc.fill")
                                        .foregroundColor(.blue)
                                    Text(file)
                                        .font(.caption.monospaced())
                                }
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }
}

/// 连接状态横幅
struct ConnectionStatusBanner: View {
    let status: ConnectionStatus

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(status.color)

            Text(status.displayName)
                .font(.subheadline)

            Spacer()
        }
        .padding()
        .background(status.color.opacity(0.1))
        .cornerRadius(8)
    }

    private var icon: String {
        switch status {
        case .disconnected: return "wifi.slash"
        case .connecting: return "wifi.exclamationmark"
        case .connected: return "wifi"
        case .error: return "exclamationmark.triangle"
        }
    }
}

/// 任务详情视图（独立组件，确保响应状态变化）
struct TaskDetailView: View {
    let task: SwarmTask
    let connectionStatus: ConnectionStatus
    let onBack: () -> Void
    let onRefresh: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // 顶部工具栏：返回按钮和刷新按钮
            HStack {
                Button {
                    onBack()
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "chevron.left")
                        Text("新建任务")
                    }
                }
                .buttonStyle(.plain)
                .foregroundColor(.accentColor)

                Spacer()

                // 刷新按钮（当任务未完成时显示）
                if task.status != .completed && task.status != .failed {
                    Button {
                        onRefresh()
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.accentColor)
                }

                // 任务状态指示
                HStack(spacing: 6) {
                    Circle()
                        .fill(task.status.color)
                        .frame(width: 8, height: 8)
                    Text(task.status.displayName)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
            }
            .padding()
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            // 任务详情滚动区域
            ScrollView {
                VStack(spacing: 24) {
                    // 任务信息卡片
                    TaskInfoCard(task: task)

                    // 工作流可视化
                    WorkflowVisualizationSection(task: task)

                    // 连接状态
                    ConnectionStatusBanner(status: connectionStatus)
                }
                .padding()
            }
        }
    }
}

/// HITL 审批弹窗（增强版，支持参数修改）
struct HITLApprovalSheet: View {
    let interrupt: HITLInterrupt
    @ObservedObject var viewModel: SwarmViewModel

    @Environment(\.dismiss) private var dismiss

    // 编辑模式状态
    @State private var isEditMode: Bool = false
    @State private var editedParameters: [String: String] = [:]

    var body: some View {
        VStack(spacing: 24) {
            // 标题
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(isEditMode ? "修改参数" : "需要您的审批")
                        .font(.title2)
                        .fontWeight(.bold)

                    Text(isEditMode ? "请修改下方参数后提交" : "AI Agent 请求执行以下操作")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()

                Text(interrupt.riskLevel.emoji)
                    .font(.system(size: 32))
            }

            // 操作详情
            VStack(alignment: .leading, spacing: 12) {
                InfoRow(title: "操作类型", value: interrupt.operation)

                if let toolName = interrupt.toolName {
                    InfoRow(title: "工具名称", value: toolName)
                }

                InfoRow(title: "风险等级", value: interrupt.riskLevel.displayName)

                // 详细参数（可编辑或只读）
                if let details = interrupt.details {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("参数详情")
                                .font(.headline)

                            if isEditMode {
                                Spacer()
                                Text("✏️ 编辑模式")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                            }
                        }

                        if isEditMode {
                            // 编辑模式：显示可编辑文本框
                            editableParametersView(details: details)
                        } else {
                            // 只读模式：显示参数
                            readOnlyParametersView(details: details)
                        }
                    }
                    .padding()
                    .background(Color(NSColor.textBackgroundColor))
                    .cornerRadius(8)
                }
            }

            Divider()

            if isEditMode {
                // 编辑模式：显示提交和取消按钮
                editModeButtons
            } else {
                // 普通模式：显示审批按钮
                approvalButtons
            }
        }
        .padding(24)
        .frame(width: 550)
        .onAppear {
            initializeEditedParameters()
        }
    }

    // MARK: - Parameter Views

    @ViewBuilder
    private func readOnlyParametersView(details: [String: AnyCodable]) -> some View {
        ForEach(Array(details.keys.sorted()), id: \.self) { key in
            if let value = details[key] {
                HStack(alignment: .top, spacing: 8) {
                    Text(key + ":")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .frame(width: 80, alignment: .leading)

                    Text("\(value.value)")
                        .font(.caption.monospaced())
                        .textSelection(.enabled)

                    Spacer()
                }
            }
        }
    }

    @ViewBuilder
    private func editableParametersView(details: [String: AnyCodable]) -> some View {
        ForEach(Array(details.keys.sorted()), id: \.self) { key in
            HStack(alignment: .top, spacing: 8) {
                Text(key + ":")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(width: 80, alignment: .leading)

                TextField("", text: binding(for: key))
                    .textFieldStyle(.roundedBorder)
                    .font(.caption.monospaced())

                Spacer()
            }
        }
    }

    // MARK: - Button Groups

    @ViewBuilder
    private var approvalButtons: some View {
        VStack(spacing: 12) {
            // 主要操作：批准和拒绝
            HStack(spacing: 12) {
                Button {
                    Task {
                        await viewModel.approveInterrupt(action: .deny)
                        dismiss()
                    }
                } label: {
                    Label("拒绝", systemImage: ApprovalAction.deny.icon)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .tint(.red)

                Button {
                    Task {
                        await viewModel.approveInterrupt(action: .approve)
                        dismiss()
                    }
                } label: {
                    Label("批准", systemImage: ApprovalAction.approve.icon)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(.green)
            }

            // 次要操作：修改和终止
            HStack(spacing: 12) {
                Button {
                    withAnimation(.spring(response: 0.3)) {
                        isEditMode = true
                    }
                } label: {
                    Label("修改参数", systemImage: ApprovalAction.modify.icon)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .tint(.orange)
                .disabled(interrupt.details == nil || interrupt.details!.isEmpty)

                Button {
                    Task {
                        await viewModel.approveInterrupt(action: .abort)
                        dismiss()
                    }
                } label: {
                    Label("终止任务", systemImage: ApprovalAction.abort.icon)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .tint(.gray)
            }
        }
    }

    @ViewBuilder
    private var editModeButtons: some View {
        HStack(spacing: 12) {
            Button {
                withAnimation(.spring(response: 0.3)) {
                    isEditMode = false
                    initializeEditedParameters()
                }
            } label: {
                Label("取消", systemImage: "xmark")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)

            Button {
                Task {
                    await submitModifiedParameters()
                    dismiss()
                }
            } label: {
                Label("提交修改", systemImage: "checkmark")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(.orange)
        }
    }

    // MARK: - Helper Methods

    private func initializeEditedParameters() {
        guard let details = interrupt.details else { return }
        editedParameters = details.mapValues { "\($0.value)" }
    }

    private func binding(for key: String) -> Binding<String> {
        Binding(
            get: { editedParameters[key] ?? "" },
            set: { editedParameters[key] = $0 }
        )
    }

    private func submitModifiedParameters() async {
        // 将编辑后的参数转换为 [String: Any]
        let modifiedData: [String: Any] = editedParameters.mapValues { value in
            // 尝试转换为数字或布尔值
            if let intValue = Int(value) {
                return intValue
            } else if let doubleValue = Double(value) {
                return doubleValue
            } else if let boolValue = Bool(value.lowercased()) {
                return boolValue
            } else {
                return value
            }
        }

        await viewModel.approveInterrupt(action: .modify, modifiedData: modifiedData)
    }
}

/// 信息行视图
struct InfoRow: View {
    let title: String
    let value: String

    var body: some View {
        HStack {
            Text(title + ":")
                .font(.subheadline)
                .foregroundColor(.secondary)

            Text(value)
                .font(.subheadline)
                .fontWeight(.medium)

            Spacer()
        }
    }
}

// MARK: - Preview

#if DEBUG
struct SwarmOrchestrationView_Previews: PreviewProvider {
    static var previews: some View {
        SwarmOrchestrationView()
            .frame(width: 1200, height: 800)
    }
}
#endif
