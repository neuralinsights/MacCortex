//
//  SwarmAPIClient.swift
//  MacCortex
//
//  Created by Claude Code on 2026-01-22.
//  Copyright © 2026 Yu Geng. All rights reserved.
//

import Foundation
import Combine

/// Swarm API 客户端
///
/// 负责与 Backend Swarm API 通信：
/// - RESTful API（创建任务、查询状态、审批等）
/// - WebSocket 实时状态推送
@MainActor
class SwarmAPIClient: ObservableObject {

    // MARK: - Published Properties

    /// 当前任务
    @Published var currentTask: SwarmTask?

    /// WebSocket 连接状态
    @Published var connectionStatus: ConnectionStatus = .disconnected

    /// 当前活跃的 HITL 中断
    @Published var activeInterrupt: HITLInterrupt?

    /// 错误信息
    @Published var lastError: String?

    // MARK: - Private Properties

    /// Backend API 基础 URL
    private let baseURL: URL

    /// URL Session
    private let session: URLSession

    /// WebSocket Task
    private var webSocketTask: URLSessionWebSocketTask?

    /// JSON Decoder（配置 ISO8601 日期解析，支持微秒）
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        // 创建支持微秒的 ISO8601 日期格式化器
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)

            // 尝试带微秒的格式
            if let date = formatter.date(from: dateString) {
                return date
            }

            // 尝试不带微秒的标准 ISO8601 格式
            let standardFormatter = ISO8601DateFormatter()
            standardFormatter.formatOptions = [.withInternetDateTime]
            if let date = standardFormatter.date(from: dateString) {
                return date
            }

            // 尝试不带时区的格式（后端可能返回此格式）
            let localFormatter = DateFormatter()
            localFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
            localFormatter.locale = Locale(identifier: "en_US_POSIX")
            if let date = localFormatter.date(from: dateString) {
                return date
            }

            // 不带微秒的本地格式
            localFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
            if let date = localFormatter.date(from: dateString) {
                return date
            }

            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Cannot decode date string: \(dateString)"
            )
        }
        return decoder
    }()

    /// JSON Encoder（配置 ISO8601 日期编码）
    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()

    /// Cancellables
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization

    /// 初始化 Swarm API 客户端
    /// - Parameter baseURL: Backend API 基础 URL（默认 http://localhost:8000）
    init(baseURL: URL = URL(string: "http://127.0.0.1:8000")!) {
        self.baseURL = baseURL

        // 配置 URLSession
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 300
        self.session = URLSession(configuration: configuration)
    }

    // MARK: - Task Management

    /// 创建新任务
    /// - Parameters:
    ///   - userInput: 用户输入（自然语言）
    ///   - workspacePath: 工作空间路径
    ///   - enableHITL: 是否启用 Human-in-the-Loop
    ///   - enableCodeReview: 是否启用代码审查
    /// - Returns: 任务 ID
    func createTask(
        userInput: String,
        workspacePath: String,
        enableHITL: Bool = true,
        enableCodeReview: Bool = false
    ) async throws -> String {
        let url = baseURL.appendingPathComponent("swarm/tasks")

        let requestBody = CreateTaskRequest(
            userInput: userInput,
            workspacePath: workspacePath,
            attachments: [],
            enableHITL: enableHITL,
            enableCodeReview: enableCodeReview
        )

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(requestBody)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.invalidResponse
        }

        let createResponse = try decoder.decode(CreateTaskResponse.self, from: data)

        // 连接 WebSocket 用于实时更新
        await connectWebSocket(taskId: createResponse.taskId)

        return createResponse.taskId
    }

    /// 获取任务状态
    /// - Parameter taskId: 任务 ID
    /// - Returns: 任务详情
    func fetchTaskStatus(taskId: String) async throws -> SwarmTask {
        let url = baseURL.appendingPathComponent("swarm/tasks/\(taskId)")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.invalidResponse
        }

        let task = try decoder.decode(SwarmTask.self, from: data)

        // 更新当前任务
        currentTask = task

        // 更新活跃中断
        activeInterrupt = task.activeInterrupt

        return task
    }

    /// 审批 HITL 中断
    /// - Parameters:
    ///   - taskId: 任务 ID
    ///   - interruptId: 中断 ID
    ///   - action: 审批动作
    ///   - modifiedData: 修改后的数据（仅 modify 动作需要）
    func approveInterrupt(
        taskId: String,
        interruptId: String,
        action: ApprovalAction,
        modifiedData: [String: Any]? = nil
    ) async throws {
        let url = baseURL.appendingPathComponent("swarm/tasks/\(taskId)/approve")

        let approval = HITLApprovalRequest(
            interruptId: interruptId,
            action: action,
            modifiedData: modifiedData?.mapValues { AnyCodable($0) }
        )

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(approval)

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.invalidResponse
        }

        // 清除活跃中断
        activeInterrupt = nil
    }

    /// 获取任务历史
    /// - Parameters:
    ///   - status: 状态过滤（all/created/running/completed/failed）
    ///   - limit: 每页数量
    ///   - offset: 偏移量
    /// - Returns: 任务历史响应
    func fetchTaskHistory(
        status: String = "all",
        limit: Int = 20,
        offset: Int = 0
    ) async throws -> TaskHistoryResponse {
        var components = URLComponents(url: baseURL.appendingPathComponent("swarm/tasks"), resolvingAgainstBaseURL: true)!
        components.queryItems = [
            URLQueryItem(name: "status", value: status),
            URLQueryItem(name: "limit", value: "\(limit)"),
            URLQueryItem(name: "offset", value: "\(offset)")
        ]

        guard let url = components.url else {
            throw APIError.invalidURL
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.invalidResponse
        }

        let historyResponse = try decoder.decode(TaskHistoryResponse.self, from: data)
        return historyResponse
    }

    // MARK: - WebSocket Management

    /// 连接 WebSocket
    /// - Parameter taskId: 任务 ID
    private func connectWebSocket(taskId: String) async {
        // 断开现有连接
        disconnectWebSocket()

        // 构造 WebSocket URL
        let wsURLString = "ws://127.0.0.1:8000/swarm/ws/\(taskId)"
        guard let wsURL = URL(string: wsURLString) else {
            lastError = "Invalid WebSocket URL"
            return
        }

        // 创建 WebSocket Task
        webSocketTask = session.webSocketTask(with: wsURL)
        webSocketTask?.resume()

        connectionStatus = .connecting

        // 开始接收消息
        await receiveMessages()
    }

    /// 断开 WebSocket 连接
    func disconnectWebSocket() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        connectionStatus = .disconnected
    }

    /// 接收 WebSocket 消息
    private func receiveMessages() async {
        guard let webSocketTask = webSocketTask else { return }

        do {
            let message = try await webSocketTask.receive()

            switch message {
            case .string(let text):
                await handleWebSocketMessage(text)

            case .data(let data):
                if let text = String(data: data, encoding: .utf8) {
                    await handleWebSocketMessage(text)
                }

            @unknown default:
                break
            }

            // 继续接收下一条消息
            await receiveMessages()

        } catch {
            // 忽略正常断开连接导致的错误（如用户返回主界面）
            let errorDesc = error.localizedDescription.lowercased()
            if errorDesc.contains("socket is not connected") ||
               errorDesc.contains("cancelled") ||
               errorDesc.contains("connection was closed") {
                // 正常断开，不显示错误
                connectionStatus = .disconnected
                return
            }

            // 其他错误才显示
            connectionStatus = .error(error.localizedDescription)
            lastError = error.localizedDescription
        }
    }

    /// 处理 WebSocket 消息
    /// - Parameter text: JSON 文本
    private func handleWebSocketMessage(_ text: String) async {
        guard let data = text.data(using: .utf8) else { return }

        do {
            let message = try decoder.decode(WSMessage.self, from: data)

            // 根据消息类型处理
            switch message.type {
            case .connected:
                connectionStatus = .connected

            case .statusChanged:
                // 重新获取任务状态
                if let task = currentTask {
                    try? await fetchTaskStatus(taskId: task.id)
                }

            case .agentStatus:
                // 更新 Agent 状态
                if var task = currentTask,
                   let agent = message.agent,
                   let statusString = message.status,
                   let agentStatus = AgentStatus(rawValue: statusString) {
                    var agentsStatus = task.agentsStatus
                    agentsStatus[agent] = agentStatus
                    // 创建新的 SwarmTask 实例（Swift 值类型模式）
                    currentTask = SwarmTask(
                        id: task.id,
                        userInput: task.userInput,
                        workspacePath: task.workspacePath,
                        status: task.status,
                        progress: task.progress,
                        currentAgent: task.currentAgent,
                        agentsStatus: agentsStatus,
                        createdAt: task.createdAt,
                        updatedAt: task.updatedAt,
                        interrupts: task.interrupts,
                        output: task.output
                    )
                }

            case .progress:
                // 更新进度
                if var task = currentTask,
                   let progress = message.progress {
                    // 创建新的 SwarmTask 实例（Swift 值类型模式）
                    currentTask = SwarmTask(
                        id: task.id,
                        userInput: task.userInput,
                        workspacePath: task.workspacePath,
                        status: task.status,
                        progress: progress,
                        currentAgent: task.currentAgent,
                        agentsStatus: task.agentsStatus,
                        createdAt: task.createdAt,
                        updatedAt: task.updatedAt,
                        interrupts: task.interrupts,
                        output: task.output
                    )
                }

            case .intermediateStep:
                // 中间处理步骤（如 stop_condition 检查）- 忽略，不更新主进度
                break

            case .hitlInterrupt:
                // 显示 HITL 审批 UI
                if let interruptId = message.interruptId,
                   let operation = message.operation,
                   let riskLevel = message.riskLevel {
                    let interrupt = HITLInterrupt(
                        id: interruptId,
                        operation: operation,
                        toolName: message.toolName,
                        riskLevel: riskLevel,
                        details: message.details
                    )
                    activeInterrupt = interrupt
                }

            case .approvalReceived:
                // 审批已收到，清除中断
                activeInterrupt = nil

            case .taskCompleted:
                // 任务完成
                if let task = currentTask {
                    // 使用 WebSocket 消息中的 output，如果没有则保留原有值
                    let taskOutput = message.output ?? task.output
                    // 创建新的 SwarmTask 实例（Swift 值类型模式）
                    currentTask = SwarmTask(
                        id: task.id,
                        userInput: task.userInput,
                        workspacePath: task.workspacePath,
                        status: .completed,
                        progress: 1.0,
                        currentAgent: task.currentAgent,
                        agentsStatus: task.agentsStatus,
                        createdAt: task.createdAt,
                        updatedAt: Date(),
                        interrupts: task.interrupts,
                        output: taskOutput
                    )
                }
                disconnectWebSocket()

            case .tokenUpdate:
                // Phase 4: Token 使用量更新 - 目前仅记录日志，未来可添加 UI 更新
                if let totalTokens = message.totalTokens,
                   let formattedCost = message.formattedCost {
                    print("[SwarmAPIClient] Token 更新: \(totalTokens) tokens, \(formattedCost)")
                }

            case .error:
                // 错误通知
                if let errorMessage = message.message {
                    lastError = errorMessage
                }
                if let task = currentTask {
                    // 创建新的 SwarmTask 实例（Swift 值类型模式）
                    currentTask = SwarmTask(
                        id: task.id,
                        userInput: task.userInput,
                        workspacePath: task.workspacePath,
                        status: .failed,
                        progress: task.progress,
                        currentAgent: task.currentAgent,
                        agentsStatus: task.agentsStatus,
                        createdAt: task.createdAt,
                        updatedAt: Date(),
                        interrupts: task.interrupts,
                        output: task.output
                    )
                }
            }

        } catch {
            lastError = "Failed to decode WebSocket message: \(error.localizedDescription)"
        }
    }

    /// 发送心跳
    func sendHeartbeat() async throws {
        guard let webSocketTask = webSocketTask else { return }

        try await webSocketTask.send(.string("ping"))
    }
}

// MARK: - API Error
// (APIError 已在 Endpoints.swift 中定义)
