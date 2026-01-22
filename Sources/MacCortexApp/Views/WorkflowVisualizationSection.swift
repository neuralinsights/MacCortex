//
//  WorkflowVisualizationSection.swift
//  MacCortex
//
//  Created by Claude Code on 2026-01-22.
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import SwiftUI

/// Swarm 工作流可视化视图
///
/// 显示 5 个 Agent 的执行流程：
/// - Planner → Coder → Reviewer → ToolRunner → Reflector
/// - 实时状态更新（✅ 🔵 ⚪ ❌ ⚠️）
/// - 可展开查看 Agent 详情
/// - 动画过渡效果
struct WorkflowVisualizationSection: View {

    // MARK: - Properties

    let task: SwarmTask

    @State private var expandedAgent: String?

    // MARK: - Body

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // 标题
            HStack {
                Text("Agent 执行流程")
                    .font(.headline)

                Spacer()

                // 整体进度
                Text("\(Int(task.progress * 100))%")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            // 工作流流程图
            VStack(spacing: 16) {
                ForEach(Array(SwarmTask.agentSequence.enumerated()), id: \.offset) { index, agentName in
                    AgentFlowNode(
                        agentName: agentName,
                        status: task.statusForAgent(agentName),
                        isExpanded: expandedAgent == agentName,
                        isCurrentAgent: task.currentAgent == agentName,
                        onTap: {
                            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                                if expandedAgent == agentName {
                                    expandedAgent = nil
                                } else {
                                    expandedAgent = agentName
                                }
                            }
                        }
                    )

                    // 连接箭头（除了最后一个）
                    if index < SwarmTask.agentSequence.count - 1 {
                        FlowArrow(isActive: task.statusForAgent(agentName) == .completed)
                    }
                }
            }

            // 图例
            WorkflowLegend()
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }
}

// MARK: - Agent Flow Node

/// Agent 流程节点
struct AgentFlowNode: View {
    let agentName: String
    let status: AgentStatus
    let isExpanded: Bool
    let isCurrentAgent: Bool
    let onTap: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // 节点主体
            Button(action: onTap) {
                HStack(spacing: 16) {
                    // 状态图标
                    ZStack {
                        Circle()
                            .fill(status.color.opacity(0.2))
                            .frame(width: 48, height: 48)

                        Text(status.emoji)
                            .font(.title2)
                    }
                    .overlay(
                        Circle()
                            .stroke(isCurrentAgent ? status.color : .clear, lineWidth: 3)
                            .frame(width: 56, height: 56)
                            .scaleEffect(isCurrentAgent ? 1.0 : 0.0)
                            .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: isCurrentAgent)
                    )

                    // Agent 信息
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(agentDisplayName)
                                .font(.headline)

                            if isCurrentAgent {
                                Text("执行中")
                                    .font(.caption)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(status.color.opacity(0.2))
                                    .foregroundColor(status.color)
                                    .cornerRadius(4)
                            }
                        }

                        Text(status.displayName)
                            .font(.subheadline)
                            .foregroundColor(.secondary)

                        Text(agentDescription)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(isExpanded ? nil : 1)
                    }

                    Spacer()

                    // 展开指示器
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .foregroundColor(.secondary)
                }
                .padding()
                .background(nodeBackgroundColor)
                .cornerRadius(12)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(nodeBorderColor, lineWidth: 2)
                )
            }
            .buttonStyle(.plain)

            // 展开详情
            if isExpanded {
                AgentDetailView(agentName: agentName, status: status)
                    .transition(.asymmetric(
                        insertion: .scale.combined(with: .opacity),
                        removal: .opacity
                    ))
            }
        }
    }

    // MARK: - Computed Properties

    private var agentDisplayName: String {
        switch agentName {
        case "planner": return "Planner 规划器"
        case "coder": return "Coder 编码器"
        case "reviewer": return "Reviewer 审查器"
        case "tool_runner": return "ToolRunner 执行器"
        case "reflector": return "Reflector 反思器"
        default: return agentName.capitalized
        }
    }

    private var agentDescription: String {
        switch agentName {
        case "planner": return "将用户需求拆解为可执行的子任务"
        case "coder": return "根据子任务生成高质量代码"
        case "reviewer": return "审查代码质量、安全性与规范"
        case "tool_runner": return "执行系统命令与工具操作"
        case "reflector": return "整体反思与优化建议"
        default: return "AI Agent"
        }
    }

    private var nodeBackgroundColor: Color {
        if isCurrentAgent {
            return status.color.opacity(0.05)
        }
        return Color(NSColor.controlBackgroundColor)
    }

    private var nodeBorderColor: Color {
        if isCurrentAgent {
            return status.color
        }
        return Color.clear
    }
}

// MARK: - Agent Detail View

/// Agent 详情视图
struct AgentDetailView: View {
    let agentName: String
    let status: AgentStatus

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Divider()

            // 详细信息
            VStack(alignment: .leading, spacing: 8) {
                Text("详细信息")
                    .font(.subheadline)
                    .fontWeight(.semibold)

                DetailRow(title: "Agent 类型", value: agentType)
                DetailRow(title: "状态", value: status.displayName)
                DetailRow(title: "职责", value: agentResponsibility)
            }

            // 能力列表
            VStack(alignment: .leading, spacing: 8) {
                Text("核心能力")
                    .font(.subheadline)
                    .fontWeight(.semibold)

                ForEach(agentCapabilities, id: \.self) { capability in
                    HStack(spacing: 6) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                            .font(.caption)
                        Text(capability)
                            .font(.caption)
                    }
                }
            }

            // 状态说明
            if let statusMessage = statusMessage {
                HStack(spacing: 8) {
                    Image(systemName: "info.circle")
                        .foregroundColor(.blue)
                    Text(statusMessage)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(8)
                .background(Color.blue.opacity(0.05))
                .cornerRadius(6)
            }
        }
        .padding()
        .background(Color(NSColor.textBackgroundColor))
        .cornerRadius(8)
        .padding(.top, 8)
    }

    // MARK: - Computed Properties

    private var agentType: String {
        switch agentName {
        case "planner": return "规划型 Agent"
        case "coder": return "生成型 Agent"
        case "reviewer": return "审查型 Agent"
        case "tool_runner": return "执行型 Agent"
        case "reflector": return "反思型 Agent"
        default: return "通用 Agent"
        }
    }

    private var agentResponsibility: String {
        switch agentName {
        case "planner":
            return "分析用户需求，拆解为结构化子任务，规划执行顺序"
        case "coder":
            return "根据子任务生成代码、文档与配置文件"
        case "reviewer":
            return "检查代码质量、安全性、性能与最佳实践"
        case "tool_runner":
            return "安全执行文件操作、Shell 命令与系统工具"
        case "reflector":
            return "整体复盘，提出改进建议与优化方向"
        default:
            return "执行特定任务"
        }
    }

    private var agentCapabilities: [String] {
        switch agentName {
        case "planner":
            return [
                "需求理解与澄清",
                "任务拆解与优先级排序",
                "依赖关系分析",
                "可行性评估"
            ]
        case "coder":
            return [
                "多语言代码生成",
                "API 与文档生成",
                "测试用例编写",
                "配置文件生成"
            ]
        case "reviewer":
            return [
                "静态代码分析",
                "安全漏洞检测",
                "性能优化建议",
                "代码风格检查"
            ]
        case "tool_runner":
            return [
                "文件系统操作",
                "Shell 命令执行",
                "Git 版本控制",
                "依赖安装与构建"
            ]
        case "reflector":
            return [
                "任务执行复盘",
                "错误根因分析",
                "改进建议生成",
                "最佳实践总结"
            ]
        default:
            return []
        }
    }

    private var statusMessage: String? {
        switch status {
        case .pending:
            return "等待前序 Agent 完成后开始执行"
        case .running:
            return "正在处理中，请稍候..."
        case .completed:
            return "✅ 已成功完成所有任务"
        case .failed:
            return "❌ 执行失败，请查看错误日志"
        case .interrupted:
            return "⚠️ 执行被中断，等待用户审批"
        }
    }
}

/// 详情行视图
struct DetailRow: View {
    let title: String
    let value: String

    var body: some View {
        HStack {
            Text(title + ":")
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 80, alignment: .leading)

            Text(value)
                .font(.caption)

            Spacer()
        }
    }
}

// MARK: - Flow Arrow

/// 流程箭头
struct FlowArrow: View {
    let isActive: Bool

    var body: some View {
        HStack(spacing: 4) {
            Rectangle()
                .fill(isActive ? Color.green : Color.secondary.opacity(0.3))
                .frame(width: 2, height: 24)

            Image(systemName: "arrowtriangle.down.fill")
                .font(.caption)
                .foregroundColor(isActive ? .green : .secondary.opacity(0.3))
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Workflow Legend

/// 工作流图例
struct WorkflowLegend: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("状态说明")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(.secondary)

            HStack(spacing: 16) {
                LegendItem(emoji: "⚪", label: "待执行", color: .gray)
                LegendItem(emoji: "🔵", label: "执行中", color: .blue)
                LegendItem(emoji: "✅", label: "已完成", color: .green)
                LegendItem(emoji: "❌", label: "失败", color: .red)
                LegendItem(emoji: "⚠️", label: "已中断", color: .yellow)
            }
        }
        .padding(.top, 8)
    }
}

/// 图例项
struct LegendItem: View {
    let emoji: String
    let label: String
    let color: Color

    var body: some View {
        HStack(spacing: 4) {
            Text(emoji)
                .font(.caption)
            Text(label)
                .font(.caption)
                .foregroundColor(color)
        }
    }
}

// MARK: - Preview

#if DEBUG
struct WorkflowVisualizationSection_Previews: PreviewProvider {
    static var previews: some View {
        WorkflowVisualizationSection(task: .preview)
            .padding()
            .frame(width: 600)
    }
}
#endif
