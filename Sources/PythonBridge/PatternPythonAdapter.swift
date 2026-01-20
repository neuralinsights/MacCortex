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

// MacCortex PythonBridge - Pattern Python Adapter
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20
//
// PatternKit 与 PythonBridge 的适配器

import Foundation

/// Pattern Python 适配器
///
/// 将 PatternKit 的 Pattern 执行适配到 Python 后端
public class PatternPythonAdapter {

    // MARK: - Properties

    private let bridge: PythonBridge

    // MARK: - Initialization

    public init(bridge: PythonBridge = .shared) {
        self.bridge = bridge
    }

    // MARK: - Execution

    /// 执行 Python Pattern
    /// - Parameters:
    ///   - patternID: Pattern ID
    ///   - text: 输入文本
    ///   - parameters: 参数
    /// - Returns: 执行结果（output, metadata, duration）
    /// - Throws: 如果执行失败
    public func execute(
        patternID: String,
        text: String,
        parameters: [String: Any]
    ) async throws -> (output: String, metadata: [String: Any], duration: TimeInterval) {

        // 转换参数为 AnyCodable
        let codableParams = parameters.mapValues { AnyCodable($0) }

        // 创建 Python 请求
        let request = PythonRequest(
            patternID: patternID,
            text: text,
            parameters: codableParams
        )

        // 执行请求
        let response = try await bridge.execute(request: request)

        // 检查响应
        guard response.success else {
            throw PythonBridgeError.communicationFailed(response.error ?? "Unknown error")
        }

        guard let output = response.output else {
            throw PythonBridgeError.invalidResponse("Missing output")
        }

        // 转换元数据
        let metadata: [String: Any] = response.metadata?.mapValues { $0.value } ?? [:]

        return (output, metadata, response.duration)
    }

    /// 检查 Python 后端是否可用
    /// - Returns: 是否可用
    public func isAvailable() async -> Bool {
        return await bridge.healthCheck()
    }

    /// 启动 Python 后端
    public func start() async throws {
        try await bridge.start()
    }

    /// 停止 Python 后端
    public func stop() {
        bridge.stop()
    }
}
