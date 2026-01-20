// MacCortex PythonBridge - Python 桥接模块
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20
//
// Swift ↔ Python 通信桥接，用于执行需要 Python 后端的 Pattern

import Foundation

/// Python 桥接错误
public enum PythonBridgeError: Error, LocalizedError {
    case pythonNotFound
    case backendNotRunning
    case communicationFailed(String)
    case invalidResponse(String)
    case timeout

    public var errorDescription: String? {
        switch self {
        case .pythonNotFound:
            return "Python interpreter not found"
        case .backendNotRunning:
            return "Python backend is not running"
        case .communicationFailed(let message):
            return "Communication failed: \(message)"
        case .invalidResponse(let message):
            return "Invalid response: \(message)"
        case .timeout:
            return "Request timed out"
        }
    }
}

/// Python 请求
public struct PythonRequest: Codable {
    /// Pattern ID
    public let patternID: String

    /// 输入文本
    public let text: String

    /// 参数
    public let parameters: [String: AnyCodable]

    /// 请求 ID（用于追踪）
    public let requestID: String

    public init(patternID: String, text: String, parameters: [String: AnyCodable], requestID: String = UUID().uuidString) {
        self.patternID = patternID
        self.text = text
        self.parameters = parameters
        self.requestID = requestID
    }
}

/// Python 响应
public struct PythonResponse: Codable {
    /// 请求 ID
    public let requestID: String

    /// 是否成功
    public let success: Bool

    /// 输出结果
    public let output: String?

    /// 元数据
    public let metadata: [String: AnyCodable]?

    /// 错误信息
    public let error: String?

    /// 执行时间（秒）
    public let duration: Double
}

/// Python 桥接管理器
///
/// 管理与 Python 后端的通信
public class PythonBridge {

    // MARK: - Singleton

    public static let shared = PythonBridge()

    // MARK: - Properties

    /// 后端进程
    private var backendProcess: Process?

    /// 后端 URL
    private let backendURL: URL

    /// 超时时间（秒）
    private let timeout: TimeInterval = 30.0

    /// 是否正在运行
    public private(set) var isRunning: Bool = false

    /// 设置运行状态（仅用于测试）
    /// - Parameter running: 运行状态
    internal func setRunningState(_ running: Bool) {
        self.isRunning = running
    }

    // MARK: - Initialization

    private init() {
        // TODO: 从配置文件读取或自动检测
        // 默认使用本地 HTTP 服务（FastAPI）
        self.backendURL = URL(string: "http://localhost:8000")!
    }

    // MARK: - Lifecycle

    /// 启动 Python 后端
    /// - Throws: 如果启动失败
    public func start() async throws {
        guard !isRunning else {
            return
        }

        // TODO: 实现 Python 后端启动逻辑（Day 8-9）
        // 1. 检测 Python 环境
        // 2. 启动 FastAPI 服务
        // 3. 等待服务就绪
        // 4. 健康检查

        isRunning = true
    }

    /// 停止 Python 后端
    public func stop() {
        guard isRunning else {
            return
        }

        // TODO: 实现 Python 后端停止逻辑（Day 8-9）
        backendProcess?.terminate()
        backendProcess = nil
        isRunning = false
    }

    /// 健康检查
    /// - Returns: 后端是否健康
    public func healthCheck() async -> Bool {
        let healthURL = backendURL.appendingPathComponent("/health")

        do {
            let (data, response) = try await URLSession.shared.data(from: healthURL)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                return false
            }

            // 尝试解码响应以验证格式
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let status = json["status"] as? String,
               status == "healthy" {
                return true
            }

            return false
        } catch {
            return false
        }
    }

    // MARK: - Execution

    /// 执行 Python Pattern
    /// - Parameter request: Python 请求
    /// - Returns: Python 响应
    /// - Throws: 如果执行失败
    public func execute(request: PythonRequest) async throws -> PythonResponse {
        guard isRunning else {
            throw PythonBridgeError.backendNotRunning
        }

        // 构建请求 URL
        let executeURL = backendURL.appendingPathComponent("/execute")

        // 创建 HTTP 请求
        var urlRequest = URLRequest(url: executeURL)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.timeoutInterval = timeout

        // 编码请求体
        let encoder = JSONEncoder()
        urlRequest.httpBody = try encoder.encode(request)

        // 发送请求
        do {
            let (data, response) = try await URLSession.shared.data(for: urlRequest)

            // 检查 HTTP 状态码
            guard let httpResponse = response as? HTTPURLResponse else {
                throw PythonBridgeError.invalidResponse("Invalid HTTP response")
            }

            guard (200...299).contains(httpResponse.statusCode) else {
                throw PythonBridgeError.communicationFailed("HTTP \(httpResponse.statusCode)")
            }

            // 解码响应
            let decoder = JSONDecoder()
            let pythonResponse = try decoder.decode(PythonResponse.self, from: data)

            return pythonResponse

        } catch let error as PythonBridgeError {
            throw error
        } catch {
            throw PythonBridgeError.communicationFailed(error.localizedDescription)
        }
    }

    /// 批量执行 Python Pattern
    /// - Parameter requests: 请求数组
    /// - Returns: 响应数组
    public func executeBatch(requests: [PythonRequest]) async throws -> [PythonResponse] {
        // TODO: 实现批量请求优化（Day 8-9）
        // 当前使用并发单个请求
        return try await withThrowingTaskGroup(of: PythonResponse.self) { group in
            for request in requests {
                group.addTask {
                    try await self.execute(request: request)
                }
            }

            var responses: [PythonResponse] = []
            for try await response in group {
                responses.append(response)
            }
            return responses
        }
    }

    // MARK: - Helper Methods

    /// 检测 Python 环境
    /// - Returns: Python 路径（如果找到）
    public static func detectPython() -> String? {
        // TODO: 实现 Python 检测（Day 8-9）
        // 1. 检查 PATH 中的 python3
        // 2. 检查常见位置 (/usr/local/bin, /opt/homebrew/bin, etc.)
        // 3. 验证版本（需要 Python 3.10+）
        return nil
    }

    /// 获取后端版本信息
    /// - Returns: 版本信息字典
    public func getVersion() async throws -> [String: String] {
        let versionURL = backendURL.appendingPathComponent("/version")

        do {
            let (data, response) = try await URLSession.shared.data(from: versionURL)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                throw PythonBridgeError.communicationFailed("HTTP request failed")
            }

            // 解码 JSON 响应
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                var versionInfo: [String: String] = [:]

                if let python = json["python"] as? String {
                    versionInfo["python"] = python
                }
                if let backend = json["backend"] as? String {
                    versionInfo["backend"] = backend
                }
                if let mlx = json["mlx"] as? String {
                    versionInfo["mlx"] = mlx
                }
                if let ollama = json["ollama"] as? String {
                    versionInfo["ollama"] = ollama
                }

                return versionInfo
            }

            throw PythonBridgeError.invalidResponse("Failed to parse version response")

        } catch let error as PythonBridgeError {
            throw error
        } catch {
            throw PythonBridgeError.communicationFailed(error.localizedDescription)
        }
    }
}

// MARK: - AnyCodable Helper

/// 用于编码/解码任意类型的包装器
public struct AnyCodable: Codable {
    public let value: Any

    public init(_ value: Any) {
        self.value = value
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            // 修复 P1 #7: 解码特殊 Double 值
            switch string {
            case "Infinity":
                value = Double.infinity
            case "-Infinity":
                value = -Double.infinity
            case "NaN":
                value = Double.nan
            default:
                value = string
            }
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            // 修复 P1 #7: 处理特殊 Double 值（Infinity, NaN）
            if double.isInfinite {
                try container.encode(double > 0 ? "Infinity" : "-Infinity")
            } else if double.isNaN {
                try container.encode("NaN")
            } else {
                try container.encode(double)
            }
        case let string as String:
            try container.encode(string)
        case let bool as Bool:
            try container.encode(bool)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dict as [String: Any]:
            try container.encode(dict.mapValues { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}
