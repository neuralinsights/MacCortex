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

// MacCortex API 端点定义
// Phase 2 Week 2 Day 6-7: Backend API 集成
// 创建时间：2026-01-21

import Foundation

/// API 端点定义
enum Endpoint {
    case executePattern
    case health

    /// 端点路径
    var path: String {
        switch self {
        case .executePattern:
            return "/execute"
        case .health:
            return "/health"
        }
    }

    /// HTTP 方法
    var method: String {
        switch self {
        case .executePattern:
            return "POST"
        case .health:
            return "GET"
        }
    }
}

/// API 配置
struct APIConfig {
    /// Backend 基础 URL（默认本地开发）
    static var baseURL: URL {
        // 优先从环境变量读取
        if let urlString = ProcessInfo.processInfo.environment["MACCORTEX_API_URL"],
           let url = URL(string: urlString) {
            return url
        }

        // 默认本地开发
        return URL(string: "http://localhost:8000")!
    }

    /// 请求超时时间（秒）
    static let timeout: TimeInterval = 30.0

    /// 最大重试次数
    static let maxRetries: Int = 3

    /// 重试延迟（秒）
    static let retryDelay: TimeInterval = 1.0
}

/// API 错误定义
enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int, message: String)
    case networkError(Error)
    case decodingError(Error)
    case rateLimitExceeded
    case unauthorized
    case serverError
    case timeout

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "无效的 URL"
        case .invalidResponse:
            return "无效的服务器响应"
        case .httpError(let statusCode, let message):
            return "HTTP 错误 \(statusCode): \(message)"
        case .networkError(let error):
            return "网络错误: \(error.localizedDescription)"
        case .decodingError(let error):
            return "数据解析错误: \(error.localizedDescription)"
        case .rateLimitExceeded:
            return "请求频率超限，请稍后再试"
        case .unauthorized:
            return "未授权访问"
        case .serverError:
            return "服务器内部错误"
        case .timeout:
            return "请求超时"
        }
    }

    /// 是否可重试
    var isRetryable: Bool {
        switch self {
        case .networkError, .timeout, .serverError:
            return true
        default:
            return false
        }
    }
}

/// Pattern 执行请求
struct PatternExecuteRequest: Encodable {
    let pattern_id: String
    let text: String
    let parameters: [String: String]
}

/// Pattern 执行响应
struct PatternExecuteResponse: Decodable {
    let pattern_id: String
    let output: String
    let success: Bool
    let duration: Double?
    let error: String?

    /// 元数据（可选）
    struct Metadata: Decodable {
        let input_length: Int?
        let output_length: Int?
        let model_name: String?
    }

    let metadata: Metadata?
}

/// 健康检查响应
struct HealthCheckResponse: Decodable {
    let status: String
    let version: String
    let timestamp: String
}
