//
//  BackendClient.swift
//  MacCortex
//
//  Phase 3 Week 2 Day 1 - Backend 通信层
//  Created on 2026-01-22
//

import Foundation
import Combine

/// Backend API 客户端（单例）
@MainActor
class BackendClient: ObservableObject {
    static let shared = BackendClient()

    private let baseURL = "http://localhost:8000"
    private let session: URLSession

    @Published var isConnected = false
    @Published var backendVersion = "未知"
    @Published var lastError: String?

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300
        self.session = URLSession(configuration: config)
    }

    // MARK: - 健康检查

    /// 检查 Backend 健康状态
    func checkHealth() async throws -> Bool {
        let url = URL(string: "\(baseURL)/health")!

        do {
            let (data, response) = try await session.data(from: url)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw BackendError.invalidResponse
            }

            guard httpResponse.statusCode == 200 else {
                throw BackendError.httpError(statusCode: httpResponse.statusCode)
            }

            let healthResponse = try JSONDecoder().decode(HealthResponse.self, from: data)

            DispatchQueue.main.async {
                self.isConnected = (healthResponse.status == "healthy")
                self.backendVersion = healthResponse.version
            }

            return healthResponse.status == "healthy"
        } catch {
            DispatchQueue.main.async {
                self.isConnected = false
                self.lastError = "Backend 连接失败: \(error.localizedDescription)"
            }
            throw error
        }
    }

    // MARK: - 翻译 API

    /// 翻译单个文本
    func translate(
        text: String,
        targetLanguage: String,
        sourceLanguage: String = "auto",
        style: String = "formal"
    ) async throws -> TranslationResponse {
        let url = URL(string: "\(baseURL)/execute")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = TranslationRequest(
            pattern_id: "translate",
            text: text,
            parameters: [
                "target_language": targetLanguage,
                "source_language": sourceLanguage,
                "style": style
            ],
            request_id: UUID().uuidString
        )

        request.httpBody = try JSONEncoder().encode(body)

        do {
            let (data, response) = try await session.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw BackendError.invalidResponse
            }

            guard httpResponse.statusCode == 200 else {
                throw BackendError.httpError(statusCode: httpResponse.statusCode)
            }

            let translationResponse = try JSONDecoder().decode(TranslationResponse.self, from: data)

            if !translationResponse.success {
                throw BackendError.translationFailed(error: translationResponse.error ?? "未知错误")
            }

            return translationResponse
        } catch let error as BackendError {
            throw error
        } catch {
            throw BackendError.networkError(error)
        }
    }

    /// 批量翻译（Phase 3 Backend 优化 2）
    func translateBatch(items: [BatchTranslationItem]) async throws -> BatchTranslationResponse {
        let url = URL(string: "\(baseURL)/execute/batch")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = BatchTranslationRequest(
            pattern_id: "translate",
            items: items,
            request_id: UUID().uuidString
        )

        request.httpBody = try JSONEncoder().encode(body)

        do {
            let (data, response) = try await session.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw BackendError.invalidResponse
            }

            guard httpResponse.statusCode == 200 else {
                throw BackendError.httpError(statusCode: httpResponse.statusCode)
            }

            let batchResponse = try JSONDecoder().decode(BatchTranslationResponse.self, from: data)

            return batchResponse
        } catch let error as BackendError {
            throw error
        } catch {
            throw BackendError.networkError(error)
        }
    }
}

// MARK: - 数据模型

/// 健康检查响应
struct HealthResponse: Codable {
    let status: String
    let timestamp: String
    let version: String
    let uptime: Double
    let patterns_loaded: Int
}

/// 翻译请求
struct TranslationRequest: Codable {
    let pattern_id: String
    let text: String
    let parameters: [String: String]
    let request_id: String
}

/// 翻译响应
struct TranslationResponse: Codable {
    let request_id: String
    let success: Bool
    let output: String?
    let metadata: TranslationMetadata?
    let error: String?
    let duration: Double
}

/// 翻译元数据
struct TranslationMetadata: Codable {
    let source_language: String?
    let target_language: String?
    let style: String?
    let original_length: Int?
    let translation_length: Int?
    let mode: String?
    let cached: Bool?
    let cache_stats: CacheStats?
}

/// 缓存统计
struct CacheStats: Codable {
    let cache_size: Int
    let max_size: Int
    let hits: Int
    let misses: Int
    let evictions: Int
    let hit_rate: Double
    let ttl_seconds: Int?
}

/// 批量翻译请求
struct BatchTranslationRequest: Codable {
    let pattern_id: String
    let items: [BatchTranslationItem]
    let request_id: String
}

/// 批量翻译单个条目
struct BatchTranslationItem: Codable {
    let text: String
    let parameters: [String: String]
}

/// 批量翻译响应
struct BatchTranslationResponse: Codable {
    let request_id: String
    let success: Bool
    let total: Int
    let succeeded: Int
    let failed: Int
    let items: [BatchItemResponse]
    let aggregate_stats: AggregateStats
    let duration: Double
}

/// 批量翻译单个条目响应
struct BatchItemResponse: Codable {
    let index: Int
    let success: Bool
    let output: String?
    let metadata: TranslationMetadata?
    let error: String?
    let duration: Double
}

/// 聚合统计
struct AggregateStats: Codable {
    let total_items: Int
    let succeeded: Int
    let failed: Int
    let cache_hits: Int
    let cache_misses: Int
    let cache_hit_rate: Double
    let total_duration: Double
    let avg_item_duration: Double
    let estimated_speedup: String
}

/// Backend 错误类型
enum BackendError: LocalizedError {
    case invalidResponse
    case httpError(statusCode: Int)
    case translationFailed(error: String)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "无效的服务器响应"
        case .httpError(let statusCode):
            return "HTTP 错误: \(statusCode)"
        case .translationFailed(let error):
            return "翻译失败: \(error)"
        case .networkError(let error):
            return "网络错误: \(error.localizedDescription)"
        }
    }
}
