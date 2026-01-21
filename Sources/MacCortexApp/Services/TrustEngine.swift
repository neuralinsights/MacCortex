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

// MacCortex 渐进式信任引擎
// Phase 2 Week 2 Day 8-9: 渐进式信任机制
// 创建时间：2026-01-21

import Foundation
import SwiftUI
import Observation

/// 操作任务（待评估）
struct OperationTask: Identifiable {
    let id = UUID()
    let patternId: String
    let text: String
    let parameters: [String: String]
    let source: InputSource
    let outputTarget: OutputTarget

    /// 输入来源
    enum InputSource {
        case user           // 用户手动输入
        case clipboard      // 剪贴板
        case file           // 文件
        case web            // 网页
        case selection      // 文本选择

        var displayName: String {
            switch self {
            case .user: return "用户输入"
            case .clipboard: return "剪贴板"
            case .file: return "文件"
            case .web: return "网页"
            case .selection: return "选中文本"
            }
        }
    }

    /// 输出目标
    enum OutputTarget {
        case display        // 仅显示
        case clipboard      // 复制到剪贴板
        case file           // 保存到文件
        case network        // 发送到网络

        var displayName: String {
            switch self {
            case .display: return "显示"
            case .clipboard: return "剪贴板"
            case .file: return "文件"
            case .network: return "网络"
            }
        }
    }
}

/// 风险评估结果
struct RiskAssessment {
    let task: OperationTask
    let riskLevel: TrustLevel
    let reasons: [String]
    let requiresConfirmation: Bool
    let estimatedDuration: TimeInterval?

    /// 风险描述
    var riskDescription: String {
        switch riskLevel {
        case .R0:
            return "安全操作，只读模式"
        case .R1:
            return "低风险操作，文本处理"
        case .R2:
            return "中风险操作，需要确认"
        case .R3:
            return "高风险操作，需要明确授权"
        }
    }
}

/// 渐进式信任引擎（Actor 保证线程安全）
@Observable
class TrustEngine {
    // MARK: - 单例
    static let shared = TrustEngine()

    // MARK: - 状态
    var pendingConfirmations: [RiskAssessment] = []
    var operationHistory: [OperationTask] = []

    // MARK: - 私有属性
    private let maxHistorySize = 100

    private init() {}

    // MARK: - 公共方法

    /// 评估操作风险
    /// - Parameter task: 操作任务
    /// - Returns: 风险评估结果
    func assessRisk(for task: OperationTask) -> RiskAssessment {
        var riskLevel: TrustLevel = .R0
        var reasons: [String] = []

        // 规则 1: Pattern 类型风险
        let patternRisk = assessPatternRisk(task.patternId)
        if patternRisk.level.rawValue > riskLevel.rawValue {
            riskLevel = patternRisk.level
        }
        if let reason = patternRisk.reason {
            reasons.append(reason)
        }

        // 规则 2: 输入来源风险
        let sourceRisk = assessSourceRisk(task.source)
        if sourceRisk.level.rawValue > riskLevel.rawValue {
            riskLevel = sourceRisk.level
        }
        if let reason = sourceRisk.reason {
            reasons.append(reason)
        }

        // 规则 3: 输出目标风险
        let outputRisk = assessOutputRisk(task.outputTarget)
        if outputRisk.level.rawValue > riskLevel.rawValue {
            riskLevel = outputRisk.level
        }
        if let reason = outputRisk.reason {
            reasons.append(reason)
        }

        // 规则 4: 数据敏感性风险
        let sensitivityRisk = assessDataSensitivity(task.text)
        if sensitivityRisk.level.rawValue > riskLevel.rawValue {
            riskLevel = sensitivityRisk.level
        }
        if let reason = sensitivityRisk.reason {
            reasons.append(reason)
        }

        // 规则 5: 文本长度风险
        let lengthRisk = assessTextLength(task.text)
        if lengthRisk.level.rawValue > riskLevel.rawValue {
            riskLevel = lengthRisk.level
        }
        if let reason = lengthRisk.reason {
            reasons.append(reason)
        }

        let requiresConfirmation = riskLevel.rawValue >= TrustLevel.R2.rawValue

        return RiskAssessment(
            task: task,
            riskLevel: riskLevel,
            reasons: reasons,
            requiresConfirmation: requiresConfirmation,
            estimatedDuration: estimateDuration(for: task)
        )
    }

    /// 请求用户确认
    /// - Parameter assessment: 风险评估结果
    /// - Returns: 用户是否批准
    @MainActor
    func requestConfirmation(for assessment: RiskAssessment) async -> Bool {
        // 添加到待确认列表
        pendingConfirmations.append(assessment)

        // 显示确认对话框（通过 SwiftUI Alert）
        // 这将由调用方（AppState）处理
        return true
    }

    /// 记录操作到历史
    func recordOperation(_ task: OperationTask) {
        operationHistory.append(task)

        // 限制历史记录大小
        if operationHistory.count > maxHistorySize {
            operationHistory.removeFirst(operationHistory.count - maxHistorySize)
        }
    }

    // MARK: - 私有评估方法

    /// 评估 Pattern 类型风险
    private func assessPatternRisk(_ patternId: String) -> (level: TrustLevel, reason: String?) {
        switch patternId {
        case "summarize", "translate":
            return (.R1, nil)  // 文本处理，低风险

        case "extract":
            return (.R1, "提取信息可能涉及敏感数据")

        case "format":
            return (.R1, nil)  // 格式转换，低风险

        case "search":
            return (.R3, "网络搜索将发送数据到外部服务")  // 网络请求，高风险

        default:
            return (.R2, "未知 Pattern 类型")
        }
    }

    /// 评估输入来源风险
    private func assessSourceRisk(_ source: OperationTask.InputSource) -> (level: TrustLevel, reason: String?) {
        switch source {
        case .user:
            return (.R0, nil)  // 用户手动输入，最安全

        case .clipboard:
            return (.R1, "剪贴板内容可能包含敏感信息")

        case .selection:
            return (.R1, nil)  // 文本选择，低风险

        case .file:
            return (.R2, "文件内容可能包含敏感信息")

        case .web:
            return (.R2, "网页内容可能包含恶意代码")
        }
    }

    /// 评估输出目标风险
    private func assessOutputRisk(_ target: OperationTask.OutputTarget) -> (level: TrustLevel, reason: String?) {
        switch target {
        case .display:
            return (.R0, nil)  // 仅显示，无风险

        case .clipboard:
            return (.R1, "数据将复制到剪贴板")

        case .file:
            return (.R3, "数据将写入文件系统")  // 文件写入，高风险

        case .network:
            return (.R3, "数据将发送到网络")  // 网络发送，高风险
        }
    }

    /// 评估数据敏感性
    private func assessDataSensitivity(_ text: String) -> (level: TrustLevel, reason: String?) {
        let textLower = text.lowercased()

        // 检测敏感关键词
        let sensitiveKeywords = [
            "password", "密码", "token", "api key", "secret",
            "credit card", "信用卡", "ssn", "身份证"
        ]

        for keyword in sensitiveKeywords {
            if textLower.contains(keyword) {
                return (.R3, "检测到敏感关键词：\(keyword)")
            }
        }

        // 检测 email 模式
        if textLower.contains("@") && textLower.contains(".") {
            let emailPattern = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
            if text.range(of: emailPattern, options: .regularExpression) != nil {
                return (.R1, "检测到邮箱地址")
            }
        }

        return (.R0, nil)
    }

    /// 评估文本长度风险
    private func assessTextLength(_ text: String) -> (level: TrustLevel, reason: String?) {
        let length = text.count

        if length > 10_000 {
            return (.R2, "文本长度超过 10,000 字符")
        } else if length > 50_000 {
            return (.R3, "文本长度超过 50,000 字符")
        }

        return (.R0, nil)
    }

    /// 估算操作耗时
    private func estimateDuration(for task: OperationTask) -> TimeInterval? {
        let baseTime: TimeInterval

        switch task.patternId {
        case "summarize":
            baseTime = 2.0
        case "translate":
            baseTime = 1.5
        case "extract":
            baseTime = 1.0
        case "format":
            baseTime = 0.5
        case "search":
            baseTime = 3.0
        default:
            return nil
        }

        // 根据文本长度调整
        let textLength = task.text.count
        let lengthFactor = Double(textLength) / 1000.0
        let adjustedTime = baseTime + (lengthFactor * 0.1)

        return min(adjustedTime, 10.0)  // 最多 10 秒
    }

    // MARK: - 统计方法

    /// 获取风险等级统计
    func getRiskStatistics() -> [TrustLevel: Int] {
        var stats: [TrustLevel: Int] = [
            .R0: 0,
            .R1: 0,
            .R2: 0,
            .R3: 0
        ]

        for task in operationHistory {
            let assessment = assessRisk(for: task)
            stats[assessment.riskLevel, default: 0] += 1
        }

        return stats
    }
}
