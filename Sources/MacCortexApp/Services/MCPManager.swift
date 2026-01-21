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

// MCP 服务器管理器
// Phase 2 Week 3 Day 11-12: MCP 工具动态加载
// 创建时间：2026-01-21

import Foundation
import os.log

/// MCP 服务器管理器（Actor 线程安全）
actor MCPManager {
    // MARK: - 单例
    static let shared = MCPManager()

    // MARK: - 属性
    private var loadedServers: [MCPServer] = []
    private var whitelist: MCPWhitelist?
    private let whitelistURL: URL
    private let logger = Logger(subsystem: "com.yugeng.MacCortex", category: "MCPManager")
    private let timeout: TimeInterval = 30.0

    // MARK: - 初始化

    private init() {
        // 白名单配置文件路径
        // 尝试多个可能的位置
        if let url = Bundle.main.url(forResource: "mcp_whitelist", withExtension: "json", subdirectory: "Config") {
            self.whitelistURL = url
        } else if let url = Bundle.main.url(forResource: "mcp_whitelist", withExtension: "json") {
            self.whitelistURL = url
        } else {
            // 回退到项目根目录（开发时）
            self.whitelistURL = URL(fileURLWithPath: "Resources/Config/mcp_whitelist.json")
        }

        // 同步加载白名单（阻塞初始化，确保白名单可用）
        Task {
            await loadWhitelist()
        }
    }

    /// 确保白名单已加载
    private func ensureWhitelistLoaded() async {
        // 如果白名单未加载，等待加载完成
        if self.whitelist == nil {
            await loadWhitelist()
        }
    }

    // MARK: - 公共方法

    /// 加载 MCP 服务器
    /// - Parameter url: 服务器可执行文件 URL
    /// - Returns: 服务器 ID
    /// - Throws: MCPError
    func loadServer(url: URL) async throws -> UUID {
        // 0. 确保白名单已加载
        await ensureWhitelistLoaded()

        // 1. 白名单检查
        logger.info("🔍 [DEBUG] 检查白名单：")
        logger.info("   URL: \(url.absoluteString)")
        logger.info("   白名单已加载: \(self.whitelist != nil)")

        if let whitelist = self.whitelist {
            logger.info("   白名单服务器数: \(whitelist.allowedServers.count)")
            logger.info("   白名单内容: \(whitelist.allowedServers)")
            logger.info("   包含此服务器: \(whitelist.contains(url))")
        }

        guard let whitelist = self.whitelist,
              whitelist.contains(url) else {
            logger.error("❌ MCP 服务器未在白名单中: \(url.absoluteString)")
            throw MCPError.notWhitelisted
        }

        logger.info("✅ 白名单检查通过")

        // 2. 检查是否已加载
        if let existing = loadedServers.first(where: { $0.url == url }) {
            logger.warning("MCP 服务器已加载: \(existing.name)")
            return existing.id
        }

        // 3. 启动子进程
        logger.info("启动 MCP 服务器: \(url.path)")

        let process = Process()
        process.executableURL = url

        // 配置 stdio pipes（JSON-RPC over stdio）
        let inputPipe = Pipe()
        let outputPipe = Pipe()
        let errorPipe = Pipe()

        process.standardInput = inputPipe
        process.standardOutput = outputPipe
        process.standardError = errorPipe

        do {
            try process.run()
        } catch {
            logger.error("启动 MCP 服务器失败: \(error.localizedDescription)")
            throw MCPError.connectionFailed
        }

        // 4. 发送 initialize 请求（MCP 握手）
        let capabilities: [String]
        do {
            capabilities = try await sendInitialize(process, outputPipe: outputPipe, inputPipe: inputPipe)
        } catch {
            process.terminate()
            logger.error("MCP 握手失败: \(error.localizedDescription)")
            throw MCPError.invalidResponse
        }

        // 5. 创建 MCPServer 实例
        var server = MCPServer(
            name: url.deletingPathExtension().lastPathComponent,
            url: url,
            capabilities: capabilities,
            trustLevel: .R1, // 默认需要确认
            isActive: true
        )
        server.process = process

        loadedServers.append(server)
        logger.info("已加载 MCP 服务器: \(server.name), 工具数: \(capabilities.count)")

        return server.id
    }

    /// 执行 MCP 工具调用
    /// - Parameter toolCall: 工具调用请求
    /// - Returns: 执行结果
    /// - Throws: MCPError
    func executeToolCall(_ toolCall: MCPToolCall) async throws -> MCPToolResult {
        let startTime = Date()

        // 1. 查找服务器
        guard let serverIndex = loadedServers.firstIndex(where: { $0.id == toolCall.serverID }) else {
            logger.error("未找到 MCP 服务器: \(toolCall.serverID)")
            throw MCPError.serverNotFound
        }

        let server = loadedServers[serverIndex]

        // 2. 检查进程状态
        guard server.isActive,
              let process = server.process,
              process.isRunning else {
            logger.error("MCP 服务器进程已终止: \(server.name)")
            throw MCPError.processTerminated
        }

        // 3. 风险评估（集成 TrustEngine）
        let task = OperationTask(
            patternId: "mcp_\(toolCall.toolName)",
            text: toolCall.argumentsJSON,
            parameters: [:],
            source: .user,
            outputTarget: .display
        )
        let assessment = TrustEngine.shared.assessRisk(for: task)

        logger.info("MCP 工具调用风险评估: \(toolCall.toolName) - \(assessment.riskLevel.displayName)")

        // 4. 如果需要确认，由调用方处理（返回特殊标记）
        // 注意：这里不直接弹窗，而是让 AppState 处理确认逻辑
        if assessment.requiresConfirmation {
            logger.warning("MCP 工具调用需要用户确认: \(toolCall.toolName)")
            // AppState 会检查 riskLevel 并显示确认对话框
        }

        // 5. 发送 tools/call 请求到 MCP 服务器
        let result: MCPToolResult
        do {
            result = try await sendToolCall(
                process,
                toolName: toolCall.toolName,
                arguments: toolCall.arguments
            )
        } catch {
            logger.error("MCP 工具调用失败: \(error.localizedDescription)")
            throw error
        }

        // 6. 更新服务器 lastPing
        loadedServers[serverIndex].lastPing = Date()

        // 7. 审计日志（集成现有 AuditLogger）
        // 注意：这里使用简化的日志格式，实际应该集成 Phase 2 Week 2 的 AuditLogger
        logger.info("""
        MCP 工具调用完成:
          - 服务器: \(server.name)
          - 工具: \(toolCall.toolName)
          - 风险等级: \(assessment.riskLevel.rawValue)
          - 耗时: \(String(format: "%.2f", result.duration))s
          - 成功: \(result.success)
        """)

        // 8. 记录到 UndoManager（如果是修改操作，R1+）
        if server.trustLevel.rawValue >= TrustLevel.R1.rawValue && result.success {
            // TODO: 集成 UndoManager（Phase 2 Week 2）
            // let snapshotID = try await UndoManager.shared.createSnapshot(...)
        }

        let duration = Date().timeIntervalSince(startTime)
        return MCPToolResult(
            success: result.success,
            output: result.output,
            metadata: result.metadata,
            duration: duration
        )
    }

    /// 卸载 MCP 服务器
    /// - Parameter id: 服务器 ID
    func unloadServer(id: UUID) async {
        guard let index = loadedServers.firstIndex(where: { $0.id == id }) else {
            logger.warning("未找到要卸载的 MCP 服务器: \(id)")
            return
        }

        var server = loadedServers[index]
        logger.info("卸载 MCP 服务器: \(server.name)")

        // 终止进程
        if let process = server.process, process.isRunning {
            process.terminate()
        }

        server.isActive = false
        server.process = nil

        loadedServers.remove(at: index)
        logger.info("已卸载 MCP 服务器: \(server.name)")
    }

    /// 获取所有已加载的服务器
    func getAllServers() -> [MCPServer] {
        return loadedServers
    }

    /// 获取服务器详情
    /// - Parameter id: 服务器 ID
    /// - Returns: 服务器（如果存在）
    func getServer(id: UUID) -> MCPServer? {
        return loadedServers.first { $0.id == id }
    }

    /// 重新加载白名单
    func reloadWhitelist() async {
        await loadWhitelist()
    }

    // MARK: - 私有方法

    /// 加载白名单配置
    private func loadWhitelist() async {
        guard FileManager.default.fileExists(atPath: whitelistURL.path) else {
            logger.error("MCP 白名单文件不存在: \(self.whitelistURL.path)")
            return
        }

        do {
            let data = try Data(contentsOf: whitelistURL)
            let config = try JSONDecoder().decode(MCPWhitelist.self, from: data)
            whitelist = config
            logger.info("已加载 MCP 白名单: \(config.allowedServers.count) 个服务器")
        } catch {
            logger.error("加载 MCP 白名单失败: \(error.localizedDescription)")
        }
    }

    /// 发送 initialize 请求（MCP 握手）
    private func sendInitialize(
        _ process: Process,
        outputPipe: Pipe,
        inputPipe: Pipe
    ) async throws -> [String] {
        // MCP 协议：initialize 请求
        let request: [String: Any] = [
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": [
                "protocolVersion": "2025-11-25",
                "capabilities": [:]
            ]
        ]

        // 发送请求
        try sendJSONRPC(request, to: inputPipe)

        // 等待响应（带超时）
        let response = try await receiveJSONRPC(from: outputPipe, timeout: timeout)

        // 解析 capabilities
        guard let result = response["result"] as? [String: Any],
              let _ = result["serverInfo"] as? [String: Any],
              let capabilities = result["capabilities"] as? [String: Any],
              let tools = capabilities["tools"] as? [[String: Any]] else {
            throw MCPError.invalidResponse
        }

        // 提取工具名称列表
        let toolNames = tools.compactMap { $0["name"] as? String }

        logger.info("MCP 服务器握手成功, 工具数: \(toolNames.count)")

        return toolNames
    }

    /// 发送 tools/call 请求
    private func sendToolCall(
        _ process: Process,
        toolName: String,
        arguments: [String: Any]
    ) async throws -> MCPToolResult {
        let startTime = Date()

        // MCP 协议：tools/call 请求
        let request: [String: Any] = [
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": [
                "name": toolName,
                "arguments": arguments
            ]
        ]

        // 发送请求
        guard let inputPipe = process.standardInput as? Pipe else {
            throw MCPError.processTerminated
        }
        try sendJSONRPC(request, to: inputPipe)

        // 等待响应
        guard let outputPipe = process.standardOutput as? Pipe else {
            throw MCPError.processTerminated
        }
        let response = try await receiveJSONRPC(from: outputPipe, timeout: timeout)

        // 解析结果
        if let error = response["error"] as? [String: Any],
           let message = error["message"] as? String {
            throw NSError(domain: "MCPError", code: -1, userInfo: [
                NSLocalizedDescriptionKey: message
            ])
        }

        guard let result = response["result"] as? [String: Any] else {
            throw MCPError.invalidResponse
        }

        let content = result["content"] as? [[String: Any]] ?? []
        let output = content.compactMap { $0["text"] as? String }.joined(separator: "\n")

        let duration = Date().timeIntervalSince(startTime)

        return MCPToolResult(
            success: true,
            output: output,
            metadata: result,
            duration: duration
        )
    }

    /// 发送 JSON-RPC 请求
    private func sendJSONRPC(_ request: [String: Any], to pipe: Pipe) throws {
        let data = try JSONSerialization.data(withJSONObject: request)
        let jsonString = String(data: data, encoding: .utf8)!
        let message = jsonString + "\n"

        guard let messageData = message.data(using: .utf8) else {
            throw MCPError.invalidArguments
        }

        pipe.fileHandleForWriting.write(messageData)
    }

    /// 接收 JSON-RPC 响应（带超时）
    private func receiveJSONRPC(from pipe: Pipe, timeout: TimeInterval) async throws -> [String: Any] {
        return try await withThrowingTaskGroup(of: [String: Any].self) { group in
            // Task 1: 读取响应
            group.addTask {
                let data = pipe.fileHandleForReading.availableData
                guard !data.isEmpty else {
                    throw MCPError.invalidResponse
                }

                let response = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                guard let response = response else {
                    throw MCPError.invalidResponse
                }

                return response
            }

            // Task 2: 超时控制
            group.addTask {
                try await Task.sleep(nanoseconds: UInt64(timeout * 1_000_000_000))
                throw MCPError.timeout
            }

            // 返回第一个完成的任务结果
            let result = try await group.next()!
            group.cancelAll()
            return result
        }
    }
}
