//
//  SwarmModels.swift
//  MacCortex
//
//  Created by Claude Code on 2026-01-22.
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import Foundation
import SwiftUI

// MARK: - Task Status

/// 任务状态枚举
enum TaskStatus: String, Codable, CaseIterable {
    case created = "created"
    case running = "running"
    case completed = "completed"
    case failed = "failed"
    case interrupted = "interrupted"

    var displayName: String {
        switch self {
        case .created: return "已创建"
        case .running: return "执行中"
        case .completed: return "已完成"
        case .failed: return "失败"
        case .interrupted: return "已中断"
        }
    }

    var color: Color {
        switch self {
        case .created: return .blue
        case .running: return .orange
        case .completed: return .green
        case .failed: return .red
        case .interrupted: return .yellow
        }
    }

    var icon: String {
        switch self {
        case .created: return "doc.badge.plus"
        case .running: return "gearshape.2.fill"
        case .completed: return "checkmark.circle.fill"
        case .failed: return "xmark.circle.fill"
        case .interrupted: return "pause.circle.fill"
        }
    }
}

// MARK: - Agent Status

/// Agent 执行状态枚举
enum AgentStatus: String, Codable, CaseIterable {
    case pending = "pending"
    case running = "running"
    case completed = "completed"
    case failed = "failed"
    case interrupted = "interrupted"

    var displayName: String {
        switch self {
        case .pending: return "待执行"
        case .running: return "执行中"
        case .completed: return "已完成"
        case .failed: return "失败"
        case .interrupted: return "已中断"
        }
    }

    var emoji: String {
        switch self {
        case .pending: return "⚪"
        case .running: return "🔵"
        case .completed: return "✅"
        case .failed: return "❌"
        case .interrupted: return "⚠️"
        }
    }

    var color: Color {
        switch self {
        case .pending: return .gray
        case .running: return .blue
        case .completed: return .green
        case .failed: return .red
        case .interrupted: return .yellow
        }
    }
}

// MARK: - Risk Level

/// 操作风险等级枚举
enum RiskLevel: String, Codable, CaseIterable {
    case low = "low"
    case medium = "medium"
    case high = "high"

    var displayName: String {
        switch self {
        case .low: return "低风险"
        case .medium: return "中风险"
        case .high: return "高风险"
        }
    }

    var emoji: String {
        switch self {
        case .low: return "🟢"
        case .medium: return "🟡"
        case .high: return "🔴"
        }
    }

    var color: Color {
        switch self {
        case .low: return .green
        case .medium: return .yellow
        case .high: return .red
        }
    }
}

// MARK: - Approval Action

/// HITL 审批动作枚举
enum ApprovalAction: String, Codable, CaseIterable {
    case approve = "approve"
    case deny = "deny"
    case modify = "modify"
    case abort = "abort"

    var displayName: String {
        switch self {
        case .approve: return "批准"
        case .deny: return "拒绝"
        case .modify: return "修改"
        case .abort: return "终止"
        }
    }

    var icon: String {
        switch self {
        case .approve: return "checkmark.circle.fill"
        case .deny: return "xmark.circle.fill"
        case .modify: return "pencil.circle.fill"
        case .abort: return "stop.circle.fill"
        }
    }

    var color: Color {
        switch self {
        case .approve: return .green
        case .deny: return .red
        case .modify: return .orange
        case .abort: return .gray
        }
    }
}

// MARK: - AnyCodable

/// 支持任意类型的 Codable 包装器
struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let intValue = try? container.decode(Int.self) {
            value = intValue
        } else if let doubleValue = try? container.decode(Double.self) {
            value = doubleValue
        } else if let stringValue = try? container.decode(String.self) {
            value = stringValue
        } else if let boolValue = try? container.decode(Bool.self) {
            value = boolValue
        } else if let arrayValue = try? container.decode([AnyCodable].self) {
            value = arrayValue.map { $0.value }
        } else if let dictValue = try? container.decode([String: AnyCodable].self) {
            value = dictValue.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case let intValue as Int:
            try container.encode(intValue)
        case let doubleValue as Double:
            try container.encode(doubleValue)
        case let stringValue as String:
            try container.encode(stringValue)
        case let boolValue as Bool:
            try container.encode(boolValue)
        case let arrayValue as [Any]:
            try container.encode(arrayValue.map { AnyCodable($0) })
        case let dictValue as [String: Any]:
            try container.encode(dictValue.mapValues { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}

// MARK: - Task Output

/// 任务输出结果
struct TaskOutput: Codable, Equatable {
    let filesCreated: [String]?
    let summary: String?
    let details: [String: AnyCodable]?

    enum CodingKeys: String, CodingKey {
        case filesCreated = "files_created"
        case summary
        case details
    }

    static func == (lhs: TaskOutput, rhs: TaskOutput) -> Bool {
        lhs.filesCreated == rhs.filesCreated &&
        lhs.summary == rhs.summary
    }
}

// MARK: - HITL Interrupt

/// HITL 中断信息
struct HITLInterrupt: Identifiable, Codable, Equatable {
    let id: String
    let operation: String
    let toolName: String?
    let riskLevel: RiskLevel
    let details: [String: AnyCodable]?

    enum CodingKeys: String, CodingKey {
        case id = "interrupt_id"
        case operation
        case toolName = "tool_name"
        case riskLevel = "risk_level"
        case details
    }

    static func == (lhs: HITLInterrupt, rhs: HITLInterrupt) -> Bool {
        lhs.id == rhs.id &&
        lhs.operation == rhs.operation &&
        lhs.toolName == rhs.toolName &&
        lhs.riskLevel == rhs.riskLevel
    }
}

// MARK: - Swarm Task

/// Swarm 编排任务模型
struct SwarmTask: Identifiable, Codable, Equatable {
    let id: String
    let userInput: String
    let workspacePath: String
    let status: TaskStatus
    let progress: Double
    let currentAgent: String?
    let agentsStatus: [String: AgentStatus]
    let createdAt: Date
    let updatedAt: Date
    let interrupts: [HITLInterrupt]
    let output: TaskOutput?

    enum CodingKeys: String, CodingKey {
        case id = "task_id"
        case userInput = "user_input"
        case workspacePath = "workspace_path"
        case status
        case progress
        case currentAgent = "current_agent"
        case agentsStatus = "agents_status"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case interrupts
        case output
    }

    /// 任务持续时间（秒）
    var duration: TimeInterval {
        updatedAt.timeIntervalSince(createdAt)
    }

    /// 格式化的持续时间字符串
    var formattedDuration: String {
        let seconds = Int(duration)
        let minutes = seconds / 60
        let remainingSeconds = seconds % 60

        if minutes > 0 {
            return "\(minutes)m \(remainingSeconds)s"
        } else {
            return "\(seconds)s"
        }
    }

    /// Agent 列表（按顺序）
    static let agentSequence = ["planner", "coder", "reviewer", "tool_runner", "reflector"]

    /// 获取 Agent 状态
    func statusForAgent(_ agentName: String) -> AgentStatus {
        agentsStatus[agentName] ?? .pending
    }

    /// 是否有活跃的 HITL 中断
    var hasActiveInterrupt: Bool {
        !interrupts.isEmpty
    }

    /// 当前活跃的中断（如果有）
    var activeInterrupt: HITLInterrupt? {
        interrupts.first
    }

    static func == (lhs: SwarmTask, rhs: SwarmTask) -> Bool {
        lhs.id == rhs.id &&
        lhs.status == rhs.status &&
        lhs.progress == rhs.progress &&
        lhs.currentAgent == rhs.currentAgent
    }
}

// MARK: - Create Task Request

/// 创建任务请求
struct CreateTaskRequest: Codable {
    let userInput: String
    let workspacePath: String
    let attachments: [FileAttachment]
    let enableHITL: Bool
    let enableCodeReview: Bool

    enum CodingKeys: String, CodingKey {
        case userInput = "user_input"
        case workspacePath = "workspace_path"
        case attachments
        case enableHITL = "enable_hitl"
        case enableCodeReview = "enable_code_review"
    }
}

/// 文件附件
struct FileAttachment: Codable {
    let type: String
    let path: String
}

// MARK: - Create Task Response

/// 创建任务响应
struct CreateTaskResponse: Codable {
    let taskId: String
    let status: String
    let createdAt: String
    let websocketUrl: String

    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case status
        case createdAt = "created_at"
        case websocketUrl = "websocket_url"
    }
}

// MARK: - HITL Approval Request

/// HITL 审批请求
struct HITLApprovalRequest: Codable {
    let interruptId: String
    let action: ApprovalAction
    let modifiedData: [String: AnyCodable]?

    enum CodingKeys: String, CodingKey {
        case interruptId = "interrupt_id"
        case action
        case modifiedData = "modified_data"
    }
}

// MARK: - HITL Approval Response

/// HITL 审批响应
struct HITLApprovalResponse: Codable {
    let success: Bool
    let message: String
}

// MARK: - Task History Item

/// 任务历史条目
struct TaskHistoryItem: Identifiable, Codable {
    let id: String
    let userInput: String
    let status: String
    let createdAt: String
    let duration: Double?

    enum CodingKeys: String, CodingKey {
        case id = "task_id"
        case userInput = "user_input"
        case status
        case createdAt = "created_at"
        case duration
    }
}

// MARK: - Task History Response

/// 任务历史响应
struct TaskHistoryResponse: Codable {
    let tasks: [TaskHistoryItem]
    let total: Int
    let hasMore: Bool

    enum CodingKeys: String, CodingKey {
        case tasks
        case total
        case hasMore = "has_more"
    }
}

// MARK: - WebSocket Message

/// WebSocket 消息类型枚举
enum WSMessageType: String, Codable {
    case connected = "connected"
    case statusChanged = "status_changed"
    case agentStatus = "agent_status"
    case progress = "progress"
    case hitlInterrupt = "hitl_interrupt"
    case approvalReceived = "approval_received"
    case taskCompleted = "task_completed"
    case error = "error"
}

/// WebSocket 消息
struct WSMessage: Codable {
    let type: WSMessageType
    let timestamp: String?
    let data: [String: AnyCodable]?

    // Agent status specific fields
    let agent: String?
    let status: String?

    // Progress specific fields
    let progress: Double?
    let currentStep: String?
    let totalSteps: Int?

    // HITL interrupt specific fields
    let interruptId: String?
    let operation: String?
    let toolName: String?
    let riskLevel: RiskLevel?
    let details: [String: AnyCodable]?

    // Error specific fields
    let errorCode: String?
    let message: String?

    enum CodingKeys: String, CodingKey {
        case type
        case timestamp
        case data
        case agent
        case status
        case progress
        case currentStep = "current_step"
        case totalSteps = "total_steps"
        case interruptId = "interrupt_id"
        case operation
        case toolName = "tool_name"
        case riskLevel = "risk_level"
        case details
        case errorCode = "error_code"
        case message
    }
}

// MARK: - Connection Status

/// 连接状态枚举
enum ConnectionStatus {
    case disconnected
    case connecting
    case connected
    case error(String)

    var displayName: String {
        switch self {
        case .disconnected: return "未连接"
        case .connecting: return "连接中"
        case .connected: return "已连接"
        case .error(let message): return "错误: \(message)"
        }
    }

    var color: Color {
        switch self {
        case .disconnected: return .gray
        case .connecting: return .orange
        case .connected: return .green
        case .error: return .red
        }
    }
}

// MARK: - Mock Data (for Preview)

#if DEBUG
extension SwarmTask {
    static var preview: SwarmTask {
        SwarmTask(
            id: "task_20260122_143000_preview",
            userInput: "Create a hello world program in Python",
            workspacePath: "/Users/demo/workspace",
            status: .running,
            progress: 0.60,
            currentAgent: "coder",
            agentsStatus: [
                "planner": .completed,
                "coder": .running,
                "reviewer": .pending,
                "tool_runner": .pending,
                "reflector": .pending
            ],
            createdAt: Date().addingTimeInterval(-120),
            updatedAt: Date(),
            interrupts: [],
            output: nil
        )
    }

    static var previewWithInterrupt: SwarmTask {
        SwarmTask(
            id: "task_20260122_143001_preview",
            userInput: "Write a file to disk",
            workspacePath: "/Users/demo/workspace",
            status: .interrupted,
            progress: 0.80,
            currentAgent: "tool_runner",
            agentsStatus: [
                "planner": .completed,
                "coder": .completed,
                "reviewer": .completed,
                "tool_runner": .interrupted,
                "reflector": .pending
            ],
            createdAt: Date().addingTimeInterval(-300),
            updatedAt: Date(),
            interrupts: [
                HITLInterrupt(
                    id: "int_001",
                    operation: "tool_execution",
                    toolName: "write_file",
                    riskLevel: .medium,
                    details: [
                        "path": AnyCodable("/workspace/hello.txt"),
                        "content": AnyCodable("Hello, World!")
                    ]
                )
            ],
            output: nil
        )
    }
}

extension HITLInterrupt {
    static var preview: HITLInterrupt {
        HITLInterrupt(
            id: "int_001",
            operation: "tool_execution",
            toolName: "write_file",
            riskLevel: .medium,
            details: [
                "path": AnyCodable("/workspace/hello.txt"),
                "content": AnyCodable("Hello, World!")
            ]
        )
    }
}
#endif
