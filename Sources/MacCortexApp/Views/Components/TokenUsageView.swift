//
//  TokenUsageView.swift
//  MacCortex
//
//  Phase 4 - Multi-LLM Support: Token Usage Display Component
//  Created on 2026-01-26
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import SwiftUI

// MARK: - Token Usage Badge

/// Token 使用量徽章（紧凑型显示）
///
/// 用于在界面角落显示当前任务或会话的 Token 使用量和成本。
/// 支持点击展开详情。
///
/// ## 使用示例
/// ```swift
/// TokenUsageBadge(
///     tokens: 1234,
///     cost: "$0.05",
///     style: .compact
/// )
/// ```
struct TokenUsageBadge: View {
    let tokens: Int
    let cost: String
    var style: BadgeStyle = .compact

    enum BadgeStyle {
        case compact   // 仅显示总数
        case detailed  // 显示 Token + 成本
        case minimal   // 仅图标 + 数字
    }

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "chart.bar.fill")
                .font(.caption2)
                .foregroundColor(.secondary)

            switch style {
            case .compact:
                Text(formattedTokens)
                    .font(.caption)
                    .monospacedDigit()

            case .detailed:
                Text("\(formattedTokens) · \(cost)")
                    .font(.caption)
                    .monospacedDigit()

            case .minimal:
                Text(formattedTokens)
                    .font(.caption2)
                    .monospacedDigit()
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color.secondary.opacity(0.1))
        .cornerRadius(6)
    }

    private var formattedTokens: String {
        if tokens >= 1_000_000 {
            return String(format: "%.1fM", Double(tokens) / 1_000_000)
        } else if tokens >= 1_000 {
            return String(format: "%.1fK", Double(tokens) / 1_000)
        } else {
            return "\(tokens)"
        }
    }
}

// MARK: - Token Usage Bar

/// Token 使用量进度条
///
/// 显示输入/输出 Token 的比例和总量。
struct TokenUsageBar: View {
    let inputTokens: Int
    let outputTokens: Int
    var maxTokens: Int = 100_000  // 用于计算比例的最大值

    private var totalTokens: Int {
        inputTokens + outputTokens
    }

    private var inputRatio: CGFloat {
        guard totalTokens > 0 else { return 0 }
        return CGFloat(inputTokens) / CGFloat(totalTokens)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            // 进度条
            GeometryReader { geometry in
                HStack(spacing: 1) {
                    // 输入部分
                    Rectangle()
                        .fill(Color.blue)
                        .frame(width: geometry.size.width * inputRatio)

                    // 输出部分
                    Rectangle()
                        .fill(Color.green)
                        .frame(width: geometry.size.width * (1 - inputRatio))
                }
                .cornerRadius(2)
            }
            .frame(height: 6)

            // 图例
            HStack {
                HStack(spacing: 4) {
                    Circle()
                        .fill(Color.blue)
                        .frame(width: 8, height: 8)
                    Text("输入: \(formatNumber(inputTokens))")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }

                Spacer()

                HStack(spacing: 4) {
                    Circle()
                        .fill(Color.green)
                        .frame(width: 8, height: 8)
                    Text("输出: \(formatNumber(outputTokens))")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
        }
    }

    private func formatNumber(_ n: Int) -> String {
        if n >= 1_000_000 {
            return String(format: "%.1fM", Double(n) / 1_000_000)
        } else if n >= 1_000 {
            return String(format: "%.1fK", Double(n) / 1_000)
        } else {
            return "\(n)"
        }
    }
}

// MARK: - Token Usage Card

/// Token 使用量卡片（完整显示）
///
/// 显示完整的 Token 使用统计，包括：
/// - 总 Token 数
/// - 输入/输出分解
/// - 成本估算
/// - 按 Agent 分组（可选）
struct TokenUsageCard: View {
    let usage: TokenUsage
    let cost: String
    var byAgent: [String: AgentUsageStats]?
    var showDetails: Bool = true

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 标题行
            HStack {
                Image(systemName: "chart.bar.fill")
                    .foregroundColor(.blue)
                Text("Token 使用量")
                    .font(.headline)
                Spacer()
                Text(cost)
                    .font(.headline)
                    .foregroundColor(.green)
            }

            Divider()

            // Token 统计
            HStack(spacing: 20) {
                TokenStatItem(
                    label: "总计",
                    value: usage.formattedTotal,
                    color: .primary
                )

                TokenStatItem(
                    label: "输入",
                    value: usage.formattedInput,
                    color: .blue
                )

                TokenStatItem(
                    label: "输出",
                    value: usage.formattedOutput,
                    color: .green
                )
            }

            // Token 比例条
            TokenUsageBar(
                inputTokens: usage.inputTokens,
                outputTokens: usage.outputTokens
            )

            // Agent 分组（如果有）
            if showDetails, let byAgent = byAgent, !byAgent.isEmpty {
                Divider()

                Text("按 Agent 分组")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                ForEach(Array(byAgent.keys.sorted()), id: \.self) { agent in
                    if let stats = byAgent[agent] {
                        AgentTokenRow(agentName: agent, stats: stats)
                    }
                }
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
    }
}

/// Token 统计项
struct TokenStatItem: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        VStack(alignment: .center, spacing: 2) {
            Text(value)
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(color)

            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

/// Agent Token 使用行
struct AgentTokenRow: View {
    let agentName: String
    let stats: AgentUsageStats

    var body: some View {
        HStack {
            // Agent 图标
            Image(systemName: agentIcon)
                .frame(width: 20)
                .foregroundColor(agentColor)

            Text(agentName.capitalized)
                .font(.body)

            Spacer()

            // Token 数量
            Text("\(stats.totalTokens)")
                .font(.caption)
                .monospacedDigit()
                .foregroundColor(.secondary)

            // 成本
            Text("$\(stats.totalCost)")
                .font(.caption)
                .monospacedDigit()
                .foregroundColor(.secondary)
                .frame(width: 70, alignment: .trailing)
        }
        .padding(.vertical, 4)
    }

    private var agentIcon: String {
        switch agentName.lowercased() {
        case "planner": return "list.bullet.clipboard"
        case "coder": return "chevron.left.forwardslash.chevron.right"
        case "reviewer": return "checkmark.seal"
        case "tool_runner": return "hammer"
        case "reflector": return "brain.head.profile"
        case "researcher": return "magnifyingglass"
        default: return "person.circle"
        }
    }

    private var agentColor: Color {
        switch agentName.lowercased() {
        case "planner": return .blue
        case "coder": return .purple
        case "reviewer": return .green
        case "tool_runner": return .orange
        case "reflector": return .pink
        case "researcher": return .cyan
        default: return .gray
        }
    }
}

// MARK: - Live Token Counter

/// 实时 Token 计数器
///
/// 在任务执行期间实时显示 Token 使用量变化。
/// 支持动画效果。
struct LiveTokenCounter: View {
    @Binding var tokens: Int
    @Binding var cost: String
    var isActive: Bool = true

    @State private var displayedTokens: Int = 0
    @State private var isAnimating = false

    var body: some View {
        HStack(spacing: 8) {
            // Token 计数
            HStack(spacing: 4) {
                Image(systemName: "number.circle.fill")
                    .foregroundColor(.blue)

                Text("\(displayedTokens)")
                    .font(.system(.body, design: .monospaced))
                    .contentTransition(.numericText())
            }

            // 分隔线
            Text("·")
                .foregroundColor(.secondary)

            // 成本显示
            HStack(spacing: 4) {
                Image(systemName: "dollarsign.circle.fill")
                    .foregroundColor(.green)

                Text(cost)
                    .font(.system(.body, design: .monospaced))
            }

            // 活跃指示器
            if isActive {
                Circle()
                    .fill(Color.green)
                    .frame(width: 8, height: 8)
                    .opacity(isAnimating ? 0.3 : 1.0)
                    .animation(.easeInOut(duration: 0.8).repeatForever(), value: isAnimating)
                    .onAppear { isAnimating = true }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color.secondary.opacity(0.1))
        .cornerRadius(8)
        .onChange(of: tokens) { oldValue, newValue in
            withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                displayedTokens = newValue
            }
        }
        .onAppear {
            displayedTokens = tokens
        }
    }
}

// MARK: - Token Cost Estimate

/// Token 成本估算器
///
/// 根据输入的 Token 数量估算成本。
struct TokenCostEstimate: View {
    let inputTokens: Int
    let outputTokens: Int
    let pricing: ModelPricing

    private var estimatedCost: Decimal {
        pricing.estimateCost(inputTokens: inputTokens, outputTokens: outputTokens)
    }

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("预估成本")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Text(formattedCost)
                    .font(.headline)
                    .foregroundColor(.blue)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 2) {
                Text("输入: \(inputTokens) × $\(NSDecimalNumber(decimal: pricing.inputPricePer1M).doubleValue, specifier: "%.2f")/1M")
                    .font(.caption2)
                    .foregroundColor(.secondary)

                Text("输出: \(outputTokens) × $\(NSDecimalNumber(decimal: pricing.outputPricePer1M).doubleValue, specifier: "%.2f")/1M")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color.blue.opacity(0.05))
        .cornerRadius(8)
    }

    private var formattedCost: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "USD"
        formatter.minimumFractionDigits = 4
        formatter.maximumFractionDigits = 4
        return formatter.string(from: estimatedCost as NSDecimalNumber) ?? "$0.0000"
    }
}

// MARK: - Previews

#Preview("Token Badge - Compact") {
    VStack(spacing: 20) {
        TokenUsageBadge(tokens: 1234, cost: "$0.05", style: .compact)
        TokenUsageBadge(tokens: 12345, cost: "$0.50", style: .detailed)
        TokenUsageBadge(tokens: 123456, cost: "$5.00", style: .minimal)
    }
    .padding()
}

#Preview("Token Usage Bar") {
    TokenUsageBar(inputTokens: 3000, outputTokens: 1500)
        .padding()
}

#Preview("Token Usage Card") {
    TokenUsageCard(
        usage: .preview,
        cost: "$0.0450",
        byAgent: UsageStats.preview.byAgent
    )
    .padding()
}

#Preview("Live Token Counter") {
    struct PreviewWrapper: View {
        @State var tokens = 0
        @State var cost = "$0.00"

        var body: some View {
            VStack(spacing: 20) {
                LiveTokenCounter(tokens: $tokens, cost: $cost)

                Button("增加 Token") {
                    tokens += Int.random(in: 100...500)
                    cost = String(format: "$%.4f", Double(tokens) * 0.00003)
                }
            }
            .padding()
        }
    }

    return PreviewWrapper()
}

#Preview("Token Cost Estimate") {
    TokenCostEstimate(
        inputTokens: 5000,
        outputTokens: 2000,
        pricing: ModelPricing(inputPricePer1M: 3.00, outputPricePer1M: 15.00)
    )
    .padding()
}
