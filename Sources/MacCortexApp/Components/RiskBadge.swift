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

// MacCortex 风险标识组件
// Phase 2 Week 2 Day 8-9: 渐进式信任机制
// 创建时间：2026-01-21

import SwiftUI

/// 风险标识徽章
struct RiskBadge: View {
    let riskLevel: TrustLevel
    let compact: Bool

    init(riskLevel: TrustLevel, compact: Bool = false) {
        self.riskLevel = riskLevel
        self.compact = compact
    }

    var body: some View {
        if compact {
            compactBadge
        } else {
            fullBadge
        }
    }

    // MARK: - 紧凑徽章（仅图标）

    private var compactBadge: some View {
        Image(systemName: riskLevel.icon)
            .font(.system(size: 12))
            .foregroundColor(riskLevel.color)
            .frame(width: 20, height: 20)
            .background(riskLevel.color.opacity(0.15))
            .clipShape(Circle())
    }

    // MARK: - 完整徽章（图标 + 文本）

    private var fullBadge: some View {
        HStack(spacing: 4) {
            Image(systemName: riskLevel.icon)
                .font(.system(size: 10))

            Text(riskLevel.displayName)
                .font(.system(size: 10, weight: .medium))
        }
        .foregroundColor(riskLevel.color)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(riskLevel.color.opacity(0.15))
        .clipShape(Capsule())
    }
}

/// 风险评估详情卡片
struct RiskAssessmentCard: View {
    let assessment: RiskAssessment

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 头部：风险等级徽章
            HStack {
                RiskBadge(riskLevel: assessment.riskLevel)

                Spacer()

                if assessment.requiresConfirmation {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 14))
                        .foregroundColor(.orange)
                }
            }

            // 风险描述
            Text(assessment.riskDescription)
                .font(.system(size: 12))
                .foregroundColor(.primary)

            // 风险原因列表
            if !assessment.reasons.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("风险因素:")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(.secondary)

                    ForEach(assessment.reasons, id: \.self) { reason in
                        HStack(spacing: 4) {
                            Circle()
                                .fill(Color.secondary)
                                .frame(width: 4, height: 4)

                            Text(reason)
                                .font(.system(size: 10))
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }

            Divider()

            // 操作详情
            VStack(alignment: .leading, spacing: 6) {
                DetailRow(label: "Pattern", value: assessment.task.patternId)
                DetailRow(label: "输入来源", value: assessment.task.source.displayName)
                DetailRow(label: "输出目标", value: assessment.task.outputTarget.displayName)

                if let duration = assessment.estimatedDuration {
                    DetailRow(
                        label: "预计耗时",
                        value: String(format: "%.1f 秒", duration)
                    )
                }
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(assessment.riskLevel.color.opacity(0.3), lineWidth: 1)
        )
    }
}

/// 详情行
private struct DetailRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label + ":")
                .font(.system(size: 10))
                .foregroundColor(.secondary)

            Text(value)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(.primary)

            Spacer()
        }
    }
}

/// 确认对话框内容
struct RiskConfirmationDialog: View {
    let assessment: RiskAssessment
    let onConfirm: () -> Void
    let onCancel: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            // 警告图标
            Image(systemName: "exclamationmark.shield.fill")
                .font(.system(size: 48))
                .foregroundColor(assessment.riskLevel.color)

            // 标题
            Text("需要您的确认")
                .font(.title2)
                .fontWeight(.bold)

            // 风险评估卡片
            RiskAssessmentCard(assessment: assessment)

            // 文本预览
            if !assessment.task.text.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("输入内容:")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(.secondary)

                    Text(assessment.task.text)
                        .font(.system(size: 10))
                        .foregroundColor(.primary)
                        .lineLimit(3)
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(6)
                }
            }

            // 按钮
            HStack(spacing: 12) {
                Button(action: onCancel) {
                    Text("取消")
                        .font(.system(size: 13))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color.secondary.opacity(0.1))
                        .foregroundColor(.primary)
                        .cornerRadius(8)
                }
                .buttonStyle(.plain)

                Button(action: onConfirm) {
                    Text("继续执行")
                        .font(.system(size: 13, weight: .medium))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(assessment.riskLevel.color)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(24)
        .frame(width: 450)
    }
}

// MARK: - TrustLevel 扩展（UI 属性）

extension TrustLevel {
    /// 图标
    var icon: String {
        switch self {
        case .R0:
            return "checkmark.shield.fill"
        case .R1:
            return "info.circle.fill"
        case .R2:
            return "exclamationmark.triangle.fill"
        case .R3:
            return "xmark.shield.fill"
        }
    }
}

// MARK: - 预览

#Preview("Risk Badge - R0") {
    VStack(spacing: 20) {
        RiskBadge(riskLevel: .R0)
        RiskBadge(riskLevel: .R0, compact: true)
    }
    .padding()
}

#Preview("Risk Badge - All Levels") {
    VStack(spacing: 12) {
        ForEach(TrustLevel.allCases, id: \.self) { level in
            HStack(spacing: 20) {
                RiskBadge(riskLevel: level)
                RiskBadge(riskLevel: level, compact: true)
            }
        }
    }
    .padding()
}

#Preview("Risk Assessment Card") {
    let task = OperationTask(
        patternId: "search",
        text: "搜索关于 API key 和 password 的信息",
        parameters: [:],
        source: .web,
        outputTarget: .network
    )

    let assessment = TrustEngine.shared.assessRisk(for: task)

    return RiskAssessmentCard(assessment: assessment)
        .padding()
}

#Preview("Risk Confirmation Dialog") {
    let task = OperationTask(
        patternId: "search",
        text: "这是一个测试文本，包含 password 和 API key 等敏感关键词。",
        parameters: [:],
        source: .file,
        outputTarget: .network
    )

    let assessment = TrustEngine.shared.assessRisk(for: task)

    return RiskConfirmationDialog(
        assessment: assessment,
        onConfirm: {},
        onCancel: {}
    )
}
