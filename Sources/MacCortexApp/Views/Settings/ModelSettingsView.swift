//
//  ModelSettingsView.swift
//  MacCortex
//
//  Phase 4 - Multi-LLM Support: Model Selection & API Key Settings UI
//  Created on 2026-01-26
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import SwiftUI

/// 模型设置视图
///
/// 包含两个主要部分：
/// 1. API Key 管理 - 配置各 Provider 的 API Key
/// 2. 模型选择 - 选择默认使用的 LLM 模型
struct ModelSettingsView: View {
    @StateObject private var viewModel = ModelSettingsViewModel()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Text("LLM 模型设置")
                    .font(.headline)
                Spacer()
                Button {
                    viewModel.refreshModels()
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.borderless)
                .help("刷新模型列表")
            }
            .padding()

            Divider()

            // 内容区域
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Section 1: API Key 配置
                    APIKeySection(viewModel: viewModel)

                    Divider()

                    // Section 2: 可用模型列表
                    AvailableModelsSection(viewModel: viewModel)

                    // Section 3: 使用量统计（可选展示）
                    if viewModel.showUsageStats {
                        Divider()
                        UsageStatsSection(viewModel: viewModel)
                    }
                }
                .padding()
            }

            Divider()

            // 底部按钮
            HStack {
                Toggle("显示使用量统计", isOn: $viewModel.showUsageStats)
                    .toggleStyle(.checkbox)

                Spacer()

                Button("关闭") {
                    dismiss()
                }
                .keyboardShortcut(.escape, modifiers: [])
            }
            .padding()
        }
        .frame(width: 600, height: 550)
        .onAppear {
            viewModel.loadData()
        }
    }
}

// MARK: - API Key Section

/// API Key 配置区域
struct APIKeySection: View {
    @ObservedObject var viewModel: ModelSettingsViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("API Key 配置")
                .font(.headline)

            Text("配置各 LLM 服务提供商的 API Key。API Key 使用 macOS Keychain 安全存储。")
                .font(.caption)
                .foregroundColor(.secondary)

            // Provider 列表
            ForEach(LLMProvider.allCases) { provider in
                APIKeyRow(
                    provider: provider,
                    isConfigured: viewModel.isProviderConfigured(provider),
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

/// 单个 API Key 配置行
struct APIKeyRow: View {
    let provider: LLMProvider
    let isConfigured: Bool
    let onSave: (String) -> Void
    let onDelete: () -> Void

    @State private var isEditing = false
    @State private var keyInput = ""
    @State private var showKey = false

    var body: some View {
        HStack(spacing: 12) {
            // Provider 图标
            Image(systemName: provider.icon)
                .font(.title2)
                .frame(width: 30)
                .foregroundColor(isConfigured ? .green : .secondary)

            // Provider 名称和状态
            VStack(alignment: .leading, spacing: 2) {
                Text(provider.displayName)
                    .font(.body)

                if isConfigured {
                    Text("已配置")
                        .font(.caption)
                        .foregroundColor(.green)
                } else {
                    Text("未配置")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            // 操作按钮
            if isEditing {
                HStack(spacing: 8) {
                    SecureField("输入 API Key", text: $keyInput)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 200)

                    Button("保存") {
                        onSave(keyInput)
                        keyInput = ""
                        isEditing = false
                    }
                    .disabled(keyInput.isEmpty)

                    Button("取消") {
                        keyInput = ""
                        isEditing = false
                    }
                }
            } else {
                HStack(spacing: 8) {
                    if isConfigured {
                        Button {
                            onDelete()
                        } label: {
                            Image(systemName: "trash")
                                .foregroundColor(.red)
                        }
                        .buttonStyle(.borderless)
                        .help("删除 API Key")
                    }

                    Button(isConfigured ? "修改" : "配置") {
                        isEditing = true
                    }
                    .buttonStyle(.bordered)

                    // 帮助链接
                    if let url = provider.apiKeyHelpURL {
                        Link(destination: url) {
                            Image(systemName: "questionmark.circle")
                        }
                        .help("获取 API Key")
                    }
                }
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(8)
    }
}

// MARK: - Available Models Section

/// 可用模型列表区域
struct AvailableModelsSection: View {
    @ObservedObject var viewModel: ModelSettingsViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("可用模型")
                    .font(.headline)

                Spacer()

                if viewModel.isLoading {
                    ProgressView()
                        .scaleEffect(0.7)
                }
            }

            if let error = viewModel.errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle")
                        .foregroundColor(.orange)
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(8)
                .background(Color.orange.opacity(0.1))
                .cornerRadius(6)
            }

            if viewModel.models.isEmpty && !viewModel.isLoading {
                Text("暂无可用模型。请先配置 API Key 或启动本地模型服务。")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding()
            } else {
                // 模型列表
                LazyVStack(spacing: 8) {
                    ForEach(viewModel.models) { model in
                        ModelRow(
                            model: model,
                            isDefault: model.id == viewModel.defaultModelId,
                            onSelect: {
                                viewModel.setDefaultModel(model.id)
                            }
                        )
                    }
                }
            }
        }
    }
}

/// 单个模型行
struct ModelRow: View {
    let model: LLMModel
    let isDefault: Bool
    let onSelect: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // 模型图标
            Image(systemName: model.icon)
                .font(.title3)
                .frame(width: 28)
                .foregroundColor(model.isAvailable ? .primary : .secondary)

            // 模型信息
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(model.displayName)
                        .font(.body)
                        .foregroundColor(model.isAvailable ? .primary : .secondary)

                    if isDefault {
                        Text("默认")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(4)
                    }

                    if !model.isAvailable {
                        Text("不可用")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.gray.opacity(0.3))
                            .foregroundColor(.secondary)
                            .cornerRadius(4)
                    }
                }

                // 能力标签
                HStack(spacing: 4) {
                    ForEach(model.capabilities, id: \.self) { capability in
                        Text(LLMModel.capabilityDisplayName(for: capability))
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(LLMModel.capabilityColor(for: capability).opacity(0.2))
                            .foregroundColor(LLMModel.capabilityColor(for: capability))
                            .cornerRadius(4)
                    }
                }
            }

            Spacer()

            // 定价信息
            VStack(alignment: .trailing, spacing: 2) {
                if model.isLocal {
                    Text("免费")
                        .font(.caption)
                        .foregroundColor(.green)
                } else {
                    Text("$\(NSDecimalNumber(decimal: model.pricing.inputPricePer1M).doubleValue, specifier: "%.2f") / $\(NSDecimalNumber(decimal: model.pricing.outputPricePer1M).doubleValue, specifier: "%.2f")")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("输入 / 输出 ($/1M)")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }

            // 选择按钮
            Button {
                onSelect()
            } label: {
                Image(systemName: isDefault ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(isDefault ? .blue : .secondary)
            }
            .buttonStyle(.borderless)
            .disabled(!model.isAvailable)
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(isDefault ? Color.blue.opacity(0.05) : Color.secondary.opacity(0.05))
        .cornerRadius(8)
        .opacity(model.isAvailable ? 1.0 : 0.6)
    }
}

// MARK: - Usage Stats Section

/// 使用量统计区域
struct UsageStatsSection: View {
    @ObservedObject var viewModel: ModelSettingsViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("使用量统计")
                    .font(.headline)

                Spacer()

                Button("重置") {
                    viewModel.resetUsageStats()
                }
                .buttonStyle(.borderless)
                .foregroundColor(.red)
            }

            if let stats = viewModel.usageStats {
                // 总体统计
                HStack(spacing: 20) {
                    UsageStatCard(
                        title: "总 Tokens",
                        value: stats.formattedTokens,
                        icon: "number.circle"
                    )

                    UsageStatCard(
                        title: "总成本",
                        value: stats.formattedCost,
                        icon: "dollarsign.circle"
                    )

                    UsageStatCard(
                        title: "调用次数",
                        value: "\(stats.callCount)",
                        icon: "arrow.up.circle"
                    )
                }

                // 按 Agent 分组
                if !stats.byAgent.isEmpty {
                    Text("按 Agent 分组")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .padding(.top, 8)

                    ForEach(Array(stats.byAgent.keys.sorted()), id: \.self) { agent in
                        if let agentStats = stats.byAgent[agent] {
                            AgentUsageRow(agentName: agent, stats: agentStats)
                        }
                    }
                }
            } else {
                Text("暂无使用量数据")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
}

/// 使用量统计卡片
struct UsageStatCard: View {
    let title: String
    let value: String
    let icon: String

    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.blue)

            Text(value)
                .font(.headline)

            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(8)
    }
}

/// Agent 使用量行
struct AgentUsageRow: View {
    let agentName: String
    let stats: AgentUsageStats

    var body: some View {
        HStack {
            Text(agentName.capitalized)
                .font(.body)
                .frame(width: 80, alignment: .leading)

            Spacer()

            Text("\(stats.totalTokens) tokens")
                .font(.caption)
                .foregroundColor(.secondary)

            Text("$\(stats.totalCost)")
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 80, alignment: .trailing)

            Text("\(stats.callCount) 次")
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 50, alignment: .trailing)
        }
        .padding(.vertical, 4)
    }
}

// MARK: - View Model

/// 模型设置 ViewModel
@MainActor
class ModelSettingsViewModel: ObservableObject {
    @Published var models: [LLMModel] = []
    @Published var defaultModelId: String = ""
    @Published var usageStats: UsageStats?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var showUsageStats = false

    private let apiKeyManager = APIKeyManager.shared

    func loadData() {
        refreshModels()
        loadUsageStats()
    }

    func refreshModels() {
        isLoading = true
        errorMessage = nil

        // TODO: 调用 Backend API /llm/models
        // 暂时使用模拟数据
        Task {
            try? await Task.sleep(nanoseconds: 500_000_000)

            await MainActor.run {
                // 模拟数据
                #if DEBUG
                self.models = [
                    .previewClaude,
                    .previewGPT,
                    .previewOllama
                ]
                self.defaultModelId = "claude-sonnet-4"
                #endif

                self.isLoading = false
            }
        }
    }

    func loadUsageStats() {
        // TODO: 调用 Backend API /llm/usage
        #if DEBUG
        usageStats = .preview
        #endif
    }

    func isProviderConfigured(_ provider: LLMProvider) -> Bool {
        apiKeyManager.hasKey(for: provider)
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

    func setDefaultModel(_ modelId: String) {
        defaultModelId = modelId
        // TODO: 调用 Backend API 更新默认模型
    }

    func resetUsageStats() {
        // TODO: 调用 Backend API /llm/usage/reset
        usageStats = .empty
    }
}

// MARK: - Preview

#Preview {
    ModelSettingsView()
}
