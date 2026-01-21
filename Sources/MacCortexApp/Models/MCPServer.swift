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

// MCP 服务器数据模型
// Phase 2 Week 3 Day 11-12: MCP 工具动态加载
// 创建时间：2026-01-21

import Foundation

/// MCP 服务器数据模型
struct MCPServer: Identifiable, Codable {
    // MARK: - 基本属性
    let id: UUID
    let name: String
    let url: URL
    let version: String
    let capabilities: [String]
    let trustLevel: TrustLevel
    var lastPing: Date
    var isActive: Bool

    // MARK: - 进程信息（不序列化）
    var process: Process? {
        didSet {
            isActive = process != nil && process?.isRunning == true
        }
    }

    // MARK: - 计算属性

    /// 显示名称（优先使用 name，回退到 URL）
    var displayName: String {
        name.isEmpty ? url.lastPathComponent : name
    }

    /// 服务器是否响应（30 秒内有 ping）
    var isResponding: Bool {
        guard isActive else { return false }
        return Date().timeIntervalSince(lastPing) < 30.0
    }

    /// 风险等级颜色
    var trustColor: String {
        switch trustLevel {
        case .R0: return "green"
        case .R1: return "yellow"
        case .R2: return "orange"
        case .R3: return "red"
        }
    }

    /// 工具数量
    var toolCount: Int {
        capabilities.count
    }

    // MARK: - 初始化

    init(
        id: UUID = UUID(),
        name: String,
        url: URL,
        version: String = "1.0.0",
        capabilities: [String] = [],
        trustLevel: TrustLevel = .R1,
        lastPing: Date = Date(),
        isActive: Bool = false
    ) {
        self.id = id
        self.name = name
        self.url = url
        self.version = version
        self.capabilities = capabilities
        self.trustLevel = trustLevel
        self.lastPing = lastPing
        self.isActive = isActive
    }

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case id, name, url, version, capabilities, trustLevel, lastPing, isActive
    }
}

/// MCP 工具调用请求
struct MCPToolCall: Identifiable {
    let id: UUID
    let serverID: UUID
    let toolName: String
    let arguments: [String: Any]
    let timestamp: Date

    init(
        id: UUID = UUID(),
        serverID: UUID,
        toolName: String,
        arguments: [String: Any] = [:],
        timestamp: Date = Date()
    ) {
        self.id = id
        self.serverID = serverID
        self.toolName = toolName
        self.arguments = arguments
        self.timestamp = timestamp
    }

    /// 转换为 JSON 字符串（用于日志）
    var argumentsJSON: String {
        guard let data = try? JSONSerialization.data(withJSONObject: arguments),
              let json = String(data: data, encoding: .utf8) else {
            return "{}"
        }
        return json
    }
}

/// MCP 工具调用结果
struct MCPToolResult {
    let success: Bool
    let output: String
    let metadata: [String: Any]
    let duration: TimeInterval
    let timestamp: Date

    init(
        success: Bool,
        output: String,
        metadata: [String: Any] = [:],
        duration: TimeInterval,
        timestamp: Date = Date()
    ) {
        self.success = success
        self.output = output
        self.metadata = metadata
        self.duration = duration
        self.timestamp = timestamp
    }

    /// 格式化持续时间
    var durationFormatted: String {
        String(format: "%.2f s", duration)
    }
}

/// MCP 错误类型
enum MCPError: LocalizedError {
    case notWhitelisted
    case serverNotFound
    case connectionFailed
    case timeout
    case invalidResponse
    case processTerminated
    case invalidArguments

    var errorDescription: String? {
        switch self {
        case .notWhitelisted:
            return "MCP 服务器未在白名单中"
        case .serverNotFound:
            return "未找到 MCP 服务器"
        case .connectionFailed:
            return "连接 MCP 服务器失败"
        case .timeout:
            return "MCP 请求超时（30 秒）"
        case .invalidResponse:
            return "MCP 响应格式错误"
        case .processTerminated:
            return "MCP 服务器进程已终止"
        case .invalidArguments:
            return "工具调用参数无效"
        }
    }
}

/// MCP 白名单配置
struct MCPWhitelist: Codable {
    let version: String
    let allowedServers: [String]
    let description: String

    /// 检查 URL 是否在白名单中
    func contains(_ url: URL) -> Bool {
        allowedServers.contains(url.absoluteString)
    }
}

/// MCP 工具元数据
struct MCPTool: Identifiable {
    let id = UUID()
    let name: String
    let description: String
    let inputSchema: [String: Any]?

    init(name: String, description: String, inputSchema: [String: Any]? = nil) {
        self.name = name
        self.description = description
        self.inputSchema = inputSchema
    }
}
