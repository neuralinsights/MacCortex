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

// MacCortex API 客户端
// Phase 2 Week 2 Day 6-7: Backend API 集成
// 创建时间：2026-01-21

import Foundation
import os.log

/// API 客户端（Actor 保证线程安全）
actor APIClient {
    // MARK: - 属性

    /// 单例
    static let shared = APIClient()

    /// URLSession
    private let session: URLSession

    /// 安全拦截器
    private let interceptor = SecurityInterceptor()

    /// 日志记录器
    private let logger = Logger(subsystem: "com.yugeng.MacCortex", category: "APIClient")

    /// JSON 编码器
    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return encoder
    }()

    /// JSON 解码器
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    // MARK: - 初始化

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = APIConfig.timeout
        config.timeoutIntervalForResource = APIConfig.timeout * 2
        config.httpAdditionalHeaders = [
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MacCortex/1.0"
        ]

        self.session = URLSession(configuration: config)
    }

    // MARK: - 公共方法

    /// 执行 Pattern
    /// - Parameters:
    ///   - patternId: Pattern ID
    ///   - text: 输入文本
    ///   - parameters: 参数字典
    /// - Returns: Pattern 执行结果
    /// - Throws: APIError 如果请求失败
    func executePattern(
        patternId: String,
        text: String,
        parameters: [String: String] = [:]
    ) async throws -> PatternExecuteResponse {
        // 构建请求体
        let requestBody = PatternExecuteRequest(
            pattern_id: patternId,
            text: text,
            parameters: parameters
        )

        // 发送请求
        let response: PatternExecuteResponse = try await request(
            endpoint: .executePattern,
            body: requestBody
        )

        return response
    }

    /// 健康检查
    /// - Returns: 健康检查响应
    /// - Throws: APIError 如果请求失败
    func healthCheck() async throws -> HealthCheckResponse {
        let response: HealthCheckResponse = try await request(
            endpoint: .health,
            body: Optional<String>.none
        )

        return response
    }

    // MARK: - 核心请求方法

    /// 通用请求方法
    /// - Parameters:
    ///   - endpoint: API 端点
    ///   - body: 请求体（可选）
    /// - Returns: 解码后的响应
    /// - Throws: APIError 如果请求失败
    private func request<T: Decodable, B: Encodable>(
        endpoint: Endpoint,
        body: B?
    ) async throws -> T {
        // 带重试的请求
        return try await requestWithRetry(
            endpoint: endpoint,
            body: body,
            retryCount: 0
        )
    }

    /// 带重试的请求方法
    private func requestWithRetry<T: Decodable, B: Encodable>(
        endpoint: Endpoint,
        body: B?,
        retryCount: Int
    ) async throws -> T {
        do {
            return try await performRequest(endpoint: endpoint, body: body)
        } catch let error as APIError {
            // 检查是否可重试
            if error.isRetryable && retryCount < APIConfig.maxRetries {
                logger.warning("[\(endpoint.path)] 请求失败，重试 \(retryCount + 1)/\(APIConfig.maxRetries)")

                // 等待后重试
                try await Task.sleep(nanoseconds: UInt64(APIConfig.retryDelay * 1_000_000_000))

                return try await requestWithRetry(
                    endpoint: endpoint,
                    body: body,
                    retryCount: retryCount + 1
                )
            } else {
                // 不可重试或超过最大重试次数
                throw error
            }
        }
    }

    /// 执行单次请求
    private func performRequest<T: Decodable, B: Encodable>(
        endpoint: Endpoint,
        body: B?
    ) async throws -> T {
        // 1. 构建 URL
        guard let url = buildURL(endpoint: endpoint) else {
            throw APIError.invalidURL
        }

        // 2. 构建请求
        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method

        // 3. 添加请求体（如果有）
        if let body = body {
            do {
                request.httpBody = try encoder.encode(body)
            } catch {
                throw APIError.networkError(error)
            }
        }

        // 4. 请求前拦截
        try await interceptor.preRequest(endpoint: endpoint, request: request)

        // 5. 发送请求
        let startTime = Date()
        let (data, response): (Data, URLResponse)

        do {
            (data, response) = try await session.data(for: request)
        } catch let error as NSError {
            // 处理网络错误
            await interceptor.onError(endpoint: endpoint, error: error)

            if error.code == NSURLErrorTimedOut {
                throw APIError.timeout
            } else {
                throw APIError.networkError(error)
            }
        }

        let duration = Date().timeIntervalSince(startTime)

        // 6. 验证 HTTP 响应
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        // 7. 请求后拦截
        await interceptor.postRequest(
            endpoint: endpoint,
            response: httpResponse,
            data: data,
            duration: duration
        )

        // 8. 处理 HTTP 状态码
        switch httpResponse.statusCode {
        case 200...299:
            // 成功
            break
        case 401:
            throw APIError.unauthorized
        case 429:
            throw APIError.rateLimitExceeded
        case 500...599:
            throw APIError.serverError
        default:
            let message = String(data: data, encoding: .utf8) ?? "未知错误"
            throw APIError.httpError(statusCode: httpResponse.statusCode, message: message)
        }

        // 9. 解码响应
        do {
            let decodedResponse = try decoder.decode(T.self, from: data)
            return decodedResponse
        } catch {
            logger.error("[\(endpoint.path)] 解码失败: \(error)")
            throw APIError.decodingError(error)
        }
    }

    /// 构建 URL
    private func buildURL(endpoint: Endpoint) -> URL? {
        return APIConfig.baseURL.appendingPathComponent(endpoint.path)
    }

    // MARK: - 辅助方法

    /// 获取速率限制状态
    func getRateLimitStatus() async -> String {
        return await interceptor.formatRateLimitStatus()
    }

    /// 重置速率限制（用于测试）
    func resetRateLimit() async {
        await interceptor.resetRateLimit()
    }
}

// MARK: - 便捷扩展

extension APIClient {
    /// 检查 Backend 连接状态
    /// - Returns: true 如果 Backend 可用
    func isBackendAvailable() async -> Bool {
        do {
            let response = try await healthCheck()
            return response.status == "ok"
        } catch {
            logger.error("Backend 连接失败: \(error.localizedDescription)")
            return false
        }
    }
}
