//
//  LLMModels.swift
//  MacCortex
//
//  Phase 4 - Multi-LLM Support: Swift Data Models
//  Created on 2026-01-26
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import Foundation
import SwiftUI

// MARK: - Token Usage

/// Token 使用量统计
struct TokenUsage: Codable, Equatable {
    let inputTokens: Int
    let outputTokens: Int
    let totalTokens: Int

    enum CodingKeys: String, CodingKey {
        case inputTokens = "input_tokens"
        case outputTokens = "output_tokens"
        case totalTokens = "total_tokens"
    }

    /// 空使用量
    static var zero: TokenUsage {
        TokenUsage(inputTokens: 0, outputTokens: 0, totalTokens: 0)
    }

    /// 格式化的 Token 数量（如 "1.2K"）
    var formattedTotal: String {
        formatNumber(totalTokens)
    }

    var formattedInput: String {
        formatNumber(inputTokens)
    }

    var formattedOutput: String {
        formatNumber(outputTokens)
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

// MARK: - Cost Info

/// 成本信息
struct CostInfo: Codable, Equatable {
    let inputCost: Decimal
    let outputCost: Decimal
    let totalCost: Decimal

    enum CodingKeys: String, CodingKey {
        case inputCost = "input_cost"
        case outputCost = "output_cost"
        case totalCost = "total_cost"
    }

    /// 空成本
    static var zero: CostInfo {
        CostInfo(inputCost: 0, outputCost: 0, totalCost: 0)
    }

    /// 格式化的总成本（如 "$0.0234"）
    var formattedTotal: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "USD"
        formatter.minimumFractionDigits = 2
        formatter.maximumFractionDigits = 4
        return formatter.string(from: totalCost as NSDecimalNumber) ?? "$0.00"
    }

    /// 简短格式（如 "$0.02"）
    var formattedShort: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "USD"
        formatter.minimumFractionDigits = 2
        formatter.maximumFractionDigits = 2
        return formatter.string(from: totalCost as NSDecimalNumber) ?? "$0.00"
    }
}

// MARK: - Model Pricing

/// 模型定价信息
struct ModelPricing: Codable, Equatable {
    let inputPricePer1M: Decimal
    let outputPricePer1M: Decimal

    enum CodingKeys: String, CodingKey {
        case inputPricePer1M = "input_price_per_1m"
        case outputPricePer1M = "output_price_per_1m"
    }

    /// 格式化的输入价格
    var formattedInputPrice: String {
        "$\(inputPricePer1M)/1M"
    }

    /// 格式化的输出价格
    var formattedOutputPrice: String {
        "$\(outputPricePer1M)/1M"
    }

    /// 估算成本
    func estimateCost(inputTokens: Int, outputTokens: Int) -> Decimal {
        let inputCost = Decimal(inputTokens) * inputPricePer1M / 1_000_000
        let outputCost = Decimal(outputTokens) * outputPricePer1M / 1_000_000
        return inputCost + outputCost
    }
}

// MARK: - LLM Model

/// LLM 模型信息
struct LLMModel: Identifiable, Codable, Equatable {
    let id: String
    let displayName: String
    let provider: String
    let isLocal: Bool
    let isAvailable: Bool
    let pricing: ModelPricing
    let capabilities: [String]

    enum CodingKeys: String, CodingKey {
        case id
        case displayName = "display_name"
        case provider
        case isLocal = "is_local"
        case isAvailable = "is_available"
        case pricing
        case capabilities
    }

    /// Provider 枚举（如果匹配）
    var providerType: LLMProvider? {
        LLMProvider(rawValue: provider)
    }

    /// 是否支持流式输出
    var supportsStreaming: Bool {
        capabilities.contains("streaming")
    }

    /// 是否支持工具调用
    var supportsTools: Bool {
        capabilities.contains("tools")
    }

    /// 是否为长上下文模型
    var isLongContext: Bool {
        capabilities.contains("long_context")
    }

    /// 模型图标
    var icon: String {
        if isLocal {
            return "desktopcomputer"
        } else {
            return providerType?.icon ?? "cloud"
        }
    }

    /// 能力标签颜色
    static func capabilityColor(for capability: String) -> Color {
        switch capability {
        case "streaming": return .blue
        case "tools": return .purple
        case "local": return .green
        case "long_context": return .orange
        default: return .gray
        }
    }

    /// 能力标签显示名称
    static func capabilityDisplayName(for capability: String) -> String {
        switch capability {
        case "streaming": return "流式"
        case "tools": return "工具"
        case "local": return "本地"
        case "long_context": return "长上下文"
        default: return capability
        }
    }
}

// MARK: - Models Response

/// 模型列表 API 响应
struct LLMModelsResponse: Codable {
    let models: [LLMModel]
    let defaultModel: String
    let totalCount: Int

    enum CodingKeys: String, CodingKey {
        case models
        case defaultModel = "default_model"
        case totalCount = "total_count"
    }
}

// MARK: - Usage Stats

/// Agent 使用量统计
struct AgentUsageStats: Codable, Equatable {
    let inputTokens: Int
    let outputTokens: Int
    let totalTokens: Int
    let callCount: Int
    let totalCost: String

    enum CodingKeys: String, CodingKey {
        case inputTokens = "input_tokens"
        case outputTokens = "output_tokens"
        case totalTokens = "total_tokens"
        case callCount = "call_count"
        case totalCost = "total_cost"
    }

    /// 成本 Decimal 值
    var cost: Decimal {
        Decimal(string: totalCost) ?? 0
    }
}

/// 使用量统计
struct UsageStats: Codable, Equatable {
    let totalTokens: Int
    let inputTokens: Int
    let outputTokens: Int
    let totalCost: String
    let formattedCost: String
    let callCount: Int
    let byAgent: [String: AgentUsageStats]
    let byModel: [String: AgentUsageStats]
    let byProvider: [String: AgentUsageStats]

    enum CodingKeys: String, CodingKey {
        case totalTokens = "total_tokens"
        case inputTokens = "input_tokens"
        case outputTokens = "output_tokens"
        case totalCost = "total_cost"
        case formattedCost = "formatted_cost"
        case callCount = "call_count"
        case byAgent = "by_agent"
        case byModel = "by_model"
        case byProvider = "by_provider"
    }

    /// 空统计
    static var empty: UsageStats {
        UsageStats(
            totalTokens: 0,
            inputTokens: 0,
            outputTokens: 0,
            totalCost: "0.000000",
            formattedCost: "$0.00",
            callCount: 0,
            byAgent: [:],
            byModel: [:],
            byProvider: [:]
        )
    }

    /// 成本 Decimal 值
    var cost: Decimal {
        Decimal(string: totalCost) ?? 0
    }

    /// 格式化的 Token 使用量
    var formattedTokens: String {
        if totalTokens >= 1_000_000 {
            return String(format: "%.1fM", Double(totalTokens) / 1_000_000)
        } else if totalTokens >= 1_000 {
            return String(format: "%.1fK", Double(totalTokens) / 1_000)
        } else {
            return "\(totalTokens)"
        }
    }
}

/// 使用量统计 API 响应
struct UsageStatsResponse: Codable {
    let sessionId: String?
    let stats: UsageStats

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case stats
    }
}

// MARK: - Token Update Message

/// WebSocket Token 更新消息
struct TokenUpdateMessage: Codable {
    let totalTokens: Int
    let inputTokens: Int
    let outputTokens: Int
    let totalCost: String
    let formattedCost: String
    let byAgent: [String: AgentUsageStats]?

    enum CodingKeys: String, CodingKey {
        case totalTokens = "total_tokens"
        case inputTokens = "input_tokens"
        case outputTokens = "output_tokens"
        case totalCost = "total_cost"
        case formattedCost = "formatted_cost"
        case byAgent = "by_agent"
    }
}

// MARK: - Preview Data

#if DEBUG
extension LLMModel {
    static var previewClaude: LLMModel {
        LLMModel(
            id: "claude-sonnet-4",
            displayName: "Claude Sonnet 4",
            provider: "anthropic",
            isLocal: false,
            isAvailable: true,
            pricing: ModelPricing(inputPricePer1M: 3.00, outputPricePer1M: 15.00),
            capabilities: ["streaming", "tools", "long_context"]
        )
    }

    static var previewGPT: LLMModel {
        LLMModel(
            id: "gpt-4o",
            displayName: "GPT-4o",
            provider: "openai",
            isLocal: false,
            isAvailable: false,
            pricing: ModelPricing(inputPricePer1M: 2.50, outputPricePer1M: 10.00),
            capabilities: ["streaming", "tools"]
        )
    }

    static var previewOllama: LLMModel {
        LLMModel(
            id: "qwen3:14b",
            displayName: "Qwen3 14B",
            provider: "ollama",
            isLocal: true,
            isAvailable: true,
            pricing: ModelPricing(inputPricePer1M: 0, outputPricePer1M: 0),
            capabilities: ["streaming", "local"]
        )
    }
}

extension TokenUsage {
    static var preview: TokenUsage {
        TokenUsage(inputTokens: 1234, outputTokens: 567, totalTokens: 1801)
    }
}

extension UsageStats {
    static var preview: UsageStats {
        UsageStats(
            totalTokens: 15000,
            inputTokens: 10000,
            outputTokens: 5000,
            totalCost: "0.045000",
            formattedCost: "$0.0450",
            callCount: 12,
            byAgent: [
                "planner": AgentUsageStats(
                    inputTokens: 3000,
                    outputTokens: 1500,
                    totalTokens: 4500,
                    callCount: 4,
                    totalCost: "0.013500"
                ),
                "coder": AgentUsageStats(
                    inputTokens: 5000,
                    outputTokens: 2500,
                    totalTokens: 7500,
                    callCount: 5,
                    totalCost: "0.022500"
                ),
                "reviewer": AgentUsageStats(
                    inputTokens: 2000,
                    outputTokens: 1000,
                    totalTokens: 3000,
                    callCount: 3,
                    totalCost: "0.009000"
                )
            ],
            byModel: [:],
            byProvider: [:]
        )
    }
}
#endif
