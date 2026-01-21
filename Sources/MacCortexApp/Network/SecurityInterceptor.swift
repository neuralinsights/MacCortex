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

// MacCortex 安全拦截器
// Phase 2 Week 2 Day 6-7: Backend API 集成
// 集成 Phase 1.5 安全机制（审计日志、速率限制）
// 创建时间：2026-01-21

import Foundation
import os.log

/// 安全拦截器（Actor 保证线程安全）
actor SecurityInterceptor {
    // MARK: - 属性

    /// 日志记录器
    private let logger = Logger(subsystem: "com.yugeng.MacCortex", category: "SecurityInterceptor")

    /// 请求计数器（用于本地速率限制）
    private var requestCounts: [Date] = []

    /// 速率限制窗口（秒）
    private let rateLimitWindow: TimeInterval = 60.0

    /// 最大请求数（每分钟）
    private let maxRequestsPerMinute: Int = 60

    // MARK: - 公共方法

    /// 请求前拦截
    /// - Parameters:
    ///   - endpoint: API 端点
    ///   - request: URL 请求
    /// - Throws: APIError 如果速率限制超限
    func preRequest(endpoint: Endpoint, request: URLRequest) async throws {
        // 1. 检查本地速率限制
        try checkRateLimit()

        // 2. 记录请求日志
        logRequest(endpoint: endpoint, request: request)

        // 3. 更新请求计数
        requestCounts.append(Date())
    }

    /// 请求后拦截
    /// - Parameters:
    ///   - endpoint: API 端点
    ///   - response: HTTP 响应
    ///   - data: 响应数据
    ///   - duration: 请求耗时（秒）
    func postRequest(
        endpoint: Endpoint,
        response: HTTPURLResponse?,
        data: Data?,
        duration: TimeInterval
    ) async {
        // 记录响应日志
        logResponse(
            endpoint: endpoint,
            response: response,
            dataSize: data?.count ?? 0,
            duration: duration
        )
    }

    /// 错误拦截
    /// - Parameters:
    ///   - endpoint: API 端点
    ///   - error: 错误信息
    func onError(endpoint: Endpoint, error: Error) async {
        logger.error("[\(endpoint.path)] 请求失败: \(error.localizedDescription)")
    }

    // MARK: - 私有方法

    /// 检查速率限制
    private func checkRateLimit() throws {
        // 清理过期的请求记录（超过 1 分钟）
        let now = Date()
        requestCounts = requestCounts.filter { request in
            now.timeIntervalSince(request) < rateLimitWindow
        }

        // 检查是否超限
        if requestCounts.count >= maxRequestsPerMinute {
            logger.warning("本地速率限制触发: \(self.requestCounts.count)/\(self.maxRequestsPerMinute) 请求/分钟")
            throw APIError.rateLimitExceeded
        }
    }

    /// 记录请求日志
    private func logRequest(endpoint: Endpoint, request: URLRequest) {
        let method = endpoint.method
        let path = endpoint.path
        let url = request.url?.absoluteString ?? "unknown"

        logger.info("[\(method) \(path)] 请求 URL: \(url)")

        // 记录请求体大小（如果有）
        if let bodySize = request.httpBody?.count {
            logger.debug("[\(path)] 请求体大小: \(bodySize) 字节")
        }
    }

    /// 记录响应日志
    private func logResponse(
        endpoint: Endpoint,
        response: HTTPURLResponse?,
        dataSize: Int,
        duration: TimeInterval
    ) {
        let path = endpoint.path
        let statusCode = response?.statusCode ?? 0
        let durationMs = Int(duration * 1000)

        logger.info("[\(path)] 响应状态: \(statusCode), 耗时: \(durationMs)ms, 大小: \(dataSize) 字节")

        // 警告慢请求（超过 5 秒）
        if duration > 5.0 {
            logger.warning("[\(path)] 慢请求警告: \(durationMs)ms")
        }

        // 警告大响应（超过 1MB）
        if dataSize > 1_000_000 {
            logger.warning("[\(path)] 大响应警告: \(dataSize) 字节")
        }
    }

    /// 重置速率限制计数器（用于测试）
    func resetRateLimit() {
        requestCounts.removeAll()
        logger.debug("速率限制计数器已重置")
    }

    /// 获取当前速率限制状态
    func getRateLimitStatus() -> (current: Int, max: Int, windowSeconds: TimeInterval) {
        // 清理过期记录
        let now = Date()
        requestCounts = requestCounts.filter { request in
            now.timeIntervalSince(request) < rateLimitWindow
        }

        return (
            current: requestCounts.count,
            max: maxRequestsPerMinute,
            windowSeconds: rateLimitWindow
        )
    }
}

// MARK: - 扩展：格式化输出

extension SecurityInterceptor {
    /// 格式化速率限制状态
    func formatRateLimitStatus() -> String {
        let status = getRateLimitStatus()
        return "\(status.current)/\(status.max) 请求 (\(Int(status.windowSeconds))秒窗口)"
    }
}
