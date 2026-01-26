//
//  TaskHistoryView.swift
//  MacCortex
//
//  Created by Claude Code on 2026-01-22.
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import SwiftUI

/// 任务历史详细视图
///
/// 提供完整的任务历史管理功能：
/// - 任务列表（支持筛选）
/// - 搜索功能
/// - 任务详情查看
/// - 任务重新执行
struct TaskHistoryView: View {

    // MARK: - Properties

    @ObservedObject var viewModel: SwarmViewModel

    @State private var searchText: String = ""
    @State private var selectedStatus: String = "all"
    @State private var showingTaskDetail: Bool = false

    // MARK: - Body

    var body: some View {
        VStack(spacing: 0) {
            // 搜索与筛选栏
            searchAndFilterBar

            Divider()

            // 任务列表
            taskListView

            // 底部统计
            bottomStatistics
        }
        .navigationTitle("任务历史")
        .sheet(isPresented: $showingTaskDetail) {
            if let task = viewModel.selectedTask {
                TaskDetailSheet(task: task, viewModel: viewModel)
            }
        }
    }

    // MARK: - Search and Filter Bar

    @ViewBuilder
    private var searchAndFilterBar: some View {
        VStack(spacing: 12) {
            // 搜索框
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)

                TextField("搜索任务...", text: $searchText)
                    .textFieldStyle(.plain)

                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(8)
            .background(Color(NSColor.textBackgroundColor))
            .cornerRadius(8)

            // 状态筛选
            HStack(spacing: 8) {
                Text("状态:")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                ForEach(statusOptions, id: \.value) { option in
                    Button {
                        selectedStatus = option.value
                        Task {
                            await viewModel.loadTaskHistory(status: selectedStatus)
                        }
                    } label: {
                        Text(option.label)
                            .font(.subheadline)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(selectedStatus == option.value ? option.color.opacity(0.2) : Color.clear)
                            .foregroundColor(selectedStatus == option.value ? option.color : .secondary)
                            .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                }

                Spacer()

                // 刷新按钮
                Button {
                    Task {
                        await viewModel.loadTaskHistory(status: selectedStatus)
                    }
                } label: {
                    Label("刷新", systemImage: "arrow.clockwise")
                        .font(.subheadline)
                }
                .disabled(viewModel.isLoadingHistory)
            }
        }
        .padding()
    }

    // MARK: - Task List View

    @ViewBuilder
    private var taskListView: some View {
        if viewModel.isLoadingHistory {
            ProgressView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else if filteredTasks.isEmpty {
            emptyStateView
        } else {
            List {
                ForEach(filteredTasks) { task in
                    TaskHistoryCard(task: task)
                        .onTapGesture {
                            Task {
                                await viewModel.loadTaskDetails(taskId: task.id)
                                showingTaskDetail = true
                            }
                        }
                        .contextMenu {
                            Button {
                                Task {
                                    await viewModel.loadTaskDetails(taskId: task.id)
                                    showingTaskDetail = true
                                }
                            } label: {
                                Label("查看详情", systemImage: "info.circle")
                            }

                            Button {
                                // TODO: 实现重新执行
                                viewModel.userInput = task.userInput ?? ""
                            } label: {
                                Label("使用此输入", systemImage: "arrow.clockwise")
                            }

                            Divider()

                            Button(role: .destructive) {
                                // TODO: 实现删除任务
                            } label: {
                                Label("删除", systemImage: "trash")
                            }
                        }
                }
            }
            .listStyle(.inset)
        }
    }

    @ViewBuilder
    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: searchText.isEmpty ? "tray" : "magnifyingglass")
                .font(.system(size: 48))
                .foregroundColor(.secondary)

            Text(searchText.isEmpty ? "暂无任务" : "无匹配结果")
                .font(.headline)
                .foregroundColor(.secondary)

            if !searchText.isEmpty {
                Text("尝试修改搜索关键词或筛选条件")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Bottom Statistics

    @ViewBuilder
    private var bottomStatistics: some View {
        HStack {
            Label("\(filteredTasks.count) 个任务", systemImage: "list.bullet")
                .font(.caption)
                .foregroundColor(.secondary)

            Spacer()

            if !viewModel.taskHistory.isEmpty {
                let stats = calculateStatistics()
                HStack(spacing: 16) {
                    StatBadge(label: "已完成", count: stats.completed, color: .green)
                    StatBadge(label: "失败", count: stats.failed, color: .red)
                    StatBadge(label: "执行中", count: stats.running, color: .orange)
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }

    // MARK: - Computed Properties

    private var filteredTasks: [TaskHistoryItem] {
        viewModel.taskHistory.filter { task in
            if searchText.isEmpty {
                return true
            }
            return task.userInput.localizedCaseInsensitiveContains(searchText) ||
                   task.id.localizedCaseInsensitiveContains(searchText)
        }
    }

    private var statusOptions: [(label: String, value: String, color: Color)] {
        [
            ("全部", "all", .gray),
            ("已创建", "created", .blue),
            ("执行中", "running", .orange),
            ("已完成", "completed", .green),
            ("失败", "failed", .red)
        ]
    }

    private func calculateStatistics() -> (completed: Int, failed: Int, running: Int) {
        let completed = viewModel.taskHistory.filter { $0.status == "completed" }.count
        let failed = viewModel.taskHistory.filter { $0.status == "failed" }.count
        let running = viewModel.taskHistory.filter { $0.status == "running" }.count
        return (completed, failed, running)
    }
}

// MARK: - Task History Card

/// 任务历史卡片
struct TaskHistoryCard: View {
    let task: TaskHistoryItem

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 任务信息
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(task.userInput)
                        .font(.headline)
                        .lineLimit(2)

                    Text(task.id)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                // 状态徽章
                HStack(spacing: 6) {
                    Circle()
                        .fill(statusColor)
                        .frame(width: 8, height: 8)

                    Text(statusDisplayName)
                        .font(.caption)
                        .foregroundColor(statusColor)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(statusColor.opacity(0.1))
                .cornerRadius(6)
            }

            // 元信息
            HStack {
                Label(formattedCreatedAt, systemImage: "clock")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Spacer()

                if let duration = task.duration {
                    Label(formattedDuration(duration), systemImage: "timer")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }

    // MARK: - Computed Properties

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

    private var statusDisplayName: String {
        switch task.status {
        case "created": return "已创建"
        case "running": return "执行中"
        case "completed": return "已完成"
        case "failed": return "失败"
        case "interrupted": return "已中断"
        default: return task.status
        }
    }

    private var formattedCreatedAt: String {
        // 简化显示（假设后端返回 ISO 8601 格式）
        let dateFormatter = ISO8601DateFormatter()
        if let date = dateFormatter.date(from: task.createdAt) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .short
            displayFormatter.timeStyle = .short
            displayFormatter.locale = Locale(identifier: "zh_CN")
            return displayFormatter.string(from: date)
        }
        return task.createdAt
    }

    private func formattedDuration(_ duration: Double) -> String {
        let seconds = Int(duration)
        let minutes = seconds / 60
        let remainingSeconds = seconds % 60

        if minutes > 0 {
            return "\(minutes)m \(remainingSeconds)s"
        } else {
            return "\(seconds)s"
        }
    }
}

// MARK: - Stat Badge

/// 统计徽章
struct StatBadge: View {
    let label: String
    let count: Int
    let color: Color

    var body: some View {
        HStack(spacing: 4) {
            Text("\(count)")
                .font(.caption.bold())
                .foregroundColor(color)

            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(color.opacity(0.1))
        .cornerRadius(4)
    }
}

// MARK: - Task Detail Sheet

/// 任务详情弹窗
struct TaskDetailSheet: View {
    let task: SwarmTask
    @ObservedObject var viewModel: SwarmViewModel

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 24) {
            // 标题
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("任务详情")
                        .font(.title2)
                        .fontWeight(.bold)

                    Text(task.id)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                Button {
                    dismiss()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title2)
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // 任务信息
                    DetailSection(title: "任务信息") {
                        DetailItem(label: "用户输入", value: task.userInput ?? "未知")
                        DetailItem(label: "工作空间", value: task.workspacePath ?? "未知")
                        DetailItem(label: "状态", value: task.status.displayName, color: task.status.color)
                        DetailItem(label: "进度", value: "\(Int(task.progress * 100))%")
                        DetailItem(label: "当前 Agent", value: task.currentAgent ?? "无")
                    }

                    // 时间信息
                    DetailSection(title: "时间信息") {
                        DetailItem(label: "创建时间", value: formattedDate(task.createdAt))
                        DetailItem(label: "更新时间", value: formattedDate(task.updatedAt))
                        DetailItem(label: "耗时", value: task.formattedDuration)
                    }

                    // Agent 状态
                    DetailSection(title: "Agent 执行状态") {
                        ForEach(SwarmTask.agentSequence, id: \.self) { agentName in
                            HStack {
                                Text(agentName)
                                    .font(.caption)
                                Spacer()
                                Text(task.statusForAgent(agentName).displayName)
                                    .font(.caption)
                                    .foregroundColor(task.statusForAgent(agentName).color)
                            }
                        }
                    }

                    // HITL 中断记录
                    if !task.interrupts.isEmpty {
                        DetailSection(title: "HITL 中断记录") {
                            ForEach(task.interrupts) { interrupt in
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text(interrupt.operation)
                                            .font(.caption.bold())
                                        Spacer()
                                        Text(interrupt.riskLevel.emoji)
                                    }
                                    if let toolName = interrupt.toolName {
                                        Text("工具: \(toolName)")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .padding(8)
                                .background(Color(NSColor.textBackgroundColor))
                                .cornerRadius(6)
                            }
                        }
                    }

                    // 输出结果
                    if let output = task.output {
                        DetailSection(title: "输出结果") {
                            if let summary = output.summary {
                                DetailItem(label: "摘要", value: summary)
                            }
                            if let filesCreated = output.filesCreated, !filesCreated.isEmpty {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("创建的文件:")
                                        .font(.caption.bold())
                                    ForEach(filesCreated, id: \.self) { file in
                                        Text("• \(file)")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // 操作按钮
            HStack(spacing: 12) {
                Button {
                    // 使用此输入重新创建任务
                    viewModel.userInput = task.userInput ?? ""
                    viewModel.workspacePath = task.workspacePath ?? ""
                    dismiss()
                } label: {
                    Label("使用此输入", systemImage: "arrow.clockwise")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)

                Button {
                    dismiss()
                } label: {
                    Text("关闭")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(24)
        .frame(width: 600, height: 700)
    }

    private func formattedDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        formatter.locale = Locale(identifier: "zh_CN")
        return formatter.string(from: date)
    }
}

// MARK: - Detail Section

struct DetailSection<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)

            VStack(alignment: .leading, spacing: 8) {
                content
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)
        }
    }
}

struct DetailItem: View {
    let label: String
    let value: String
    var color: Color = .primary

    var body: some View {
        HStack(alignment: .top) {
            Text(label + ":")
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 80, alignment: .leading)

            Text(value)
                .font(.caption)
                .foregroundColor(color)

            Spacer()
        }
    }
}

// MARK: - Preview

#if DEBUG
struct TaskHistoryView_Previews: PreviewProvider {
    static var previews: some View {
        TaskHistoryView(viewModel: SwarmViewModel(apiClient: SwarmAPIClient()))
            .frame(width: 800, height: 600)
    }
}
#endif
