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

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case patternID = "pattern_id"
        case text
        case parameters
        case requestID = "request_id"
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(patternID, forKey: .patternID)
        try container.encode(text, forKey: .text)
        try container.encode(requestID, forKey: .requestID)

        // 自定义编码 parameters：展开 AnyCodable 的值
        // 将 [String: AnyCodable] 转换为原始值的字典
        let unwrappedParameters = parameters.mapValues { $0.value }

        // 使用临时结构体来编码 Any 类型的字典
        let parametersWrapper = AnyCodableDict(unwrappedParameters)
        try container.encode(parametersWrapper, forKey: .parameters)
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.patternID = try container.decode(String.self, forKey: .patternID)
        self.text = try container.decode(String.self, forKey: .text)
        self.requestID = try container.decode(String.self, forKey: .requestID)
        self.parameters = try container.decode([String: AnyCodable].self, forKey: .parameters)
    }
}

// AnyCodable 字典包装器（用于编码 [String: Any]）
private struct AnyCodableDict: Encodable {
    let dict: [String: Any]

    init(_ dict: [String: Any]) {
        self.dict = dict
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: DynamicCodingKey.self)

        for (key, value) in dict {
            guard let codingKey = DynamicCodingKey(stringValue: key) else {
                continue
            }

            // 根据值的类型进行编码
            switch value {
            case let string as String:
                try container.encode(string, forKey: codingKey)
            case let int as Int:
                try container.encode(int, forKey: codingKey)
            case let double as Double:
                try container.encode(double, forKey: codingKey)
            case let bool as Bool:
                try container.encode(bool, forKey: codingKey)
            case let array as [Any]:
                let wrapper = AnyArray(array)
                try container.encode(wrapper, forKey: codingKey)
            case let dict as [String: Any]:
                let wrapper = AnyCodableDict(dict)
                try container.encode(wrapper, forKey: codingKey)
            default:
                // 尝试使用 nil（忽略不支持的类型）
                try container.encodeNil(forKey: codingKey)
            }
        }
    }
}

// Any 数组包装器
private struct AnyArray: Encodable {
    let array: [Any]

    init(_ array: [Any]) {
        self.array = array
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.unkeyedContainer()

        for value in array {
            switch value {
            case let string as String:
                try container.encode(string)
            case let int as Int:
                try container.encode(int)
            case let double as Double:
                try container.encode(double)
            case let bool as Bool:
                try container.encode(bool)
            case let array as [Any]:
                let wrapper = AnyArray(array)
                try container.encode(wrapper)
            case let dict as [String: Any]:
                let wrapper = AnyCodableDict(dict)
                try container.encode(wrapper)
            default:
                try container.encodeNil()
            }
        }
    }
}

// 动态 CodingKey（用于编码字典）
private struct DynamicCodingKey: CodingKey {
    var stringValue: String
    var intValue: Int?

    init?(stringValue: String) {
        self.stringValue = stringValue
        self.intValue = nil
    }

    init?(intValue: Int) {
        self.stringValue = "\(intValue)"
        self.intValue = intValue
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

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case requestID = "request_id"
        case success
        case output
        case metadata
        case error
        case duration
    }
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

    /// 后端端口
    private let backendPort: Int = 8000

    /// 超时时间（秒）
    private let timeout: TimeInterval = 30.0

    /// 是否正在运行
    public private(set) var isRunning: Bool = false

    /// 标准输出管道
    private var outputPipe: Pipe?

    /// 标准错误管道
    private var errorPipe: Pipe?

    /// 设置运行状态（仅用于测试）
    /// - Parameter running: 运行状态
    internal func setRunningState(_ running: Bool) {
        self.isRunning = running
    }

    // MARK: - Initialization

    private init() {
        self.backendURL = URL(string: "http://127.0.0.1:8000")!
    }

    // MARK: - Lifecycle

    /// 启动 Python 后端
    /// - Throws: 如果启动失败
    public func start() async throws {
        guard !isRunning else {
            return
        }

        // 1. 定位后端可执行文件
        guard let backendPath = locateBackendExecutable() else {
            throw PythonBridgeError.pythonNotFound
        }

        // 2. 配置并启动子进程
        let process = Process()
        process.executableURL = backendPath
        process.currentDirectoryURL = backendPath.deletingLastPathComponent()

        // 配置环境变量
        var environment = ProcessInfo.processInfo.environment
        environment["HOST"] = "127.0.0.1"
        environment["PORT"] = String(backendPort)
        environment["RELOAD"] = "false"
        environment["LOG_LEVEL"] = "INFO"
        environment["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
        process.environment = environment

        // 配置输出管道
        let outPipe = Pipe()
        let errPipe = Pipe()
        process.standardOutput = outPipe
        process.standardError = errPipe
        self.outputPipe = outPipe
        self.errorPipe = errPipe

        // 处理异常终止
        process.terminationHandler = { [weak self] proc in
            DispatchQueue.main.async {
                self?.handleProcessTermination(exitCode: proc.terminationStatus)
            }
        }

        // 3. 启动进程
        do {
            try process.run()
        } catch {
            throw PythonBridgeError.communicationFailed(
                "Failed to launch backend: \(error.localizedDescription)"
            )
        }

        self.backendProcess = process

        // 4. 等待健康检查通过
        let healthy = await waitForHealthy(
            maxAttempts: 30,
            initialDelay: 0.2,
            maxDelay: 2.0,
            totalTimeout: 30.0
        )

        guard healthy else {
            process.terminate()
            self.backendProcess = nil
            throw PythonBridgeError.backendNotRunning
        }

        isRunning = true
    }

    /// 停止 Python 后端
    public func stop() {
        guard isRunning else {
            return
        }

        if let process = backendProcess, process.isRunning {
            // 先发送 SIGINT 允许 uvicorn 优雅关闭
            process.interrupt()

            // 5 秒后强制终止
            DispatchQueue.global().asyncAfter(deadline: .now() + 5) { [weak self] in
                if let process = self?.backendProcess, process.isRunning {
                    process.terminate()
                }
            }
        }

        backendProcess = nil
        outputPipe = nil
        errorPipe = nil
        isRunning = false
    }

    // MARK: - Backend Location

    /// 定位后端可执行文件
    /// - Returns: 可执行文件 URL（如果找到）
    private func locateBackendExecutable() -> URL? {
        // 生产环境：App Bundle 内 Resources/python_backend/
        if let resourceURL = Bundle.main.resourceURL {
            let bundledPath = resourceURL
                .appendingPathComponent("python_backend")
                .appendingPathComponent("maccortex_backend")
            if FileManager.default.isExecutableFile(atPath: bundledPath.path) {
                return bundledPath
            }
        }

        // 开发环境：通过环境变量指定
        if let devPath = ProcessInfo.processInfo.environment["MACCORTEX_DEV_BACKEND"] {
            let url = URL(fileURLWithPath: devPath)
            if FileManager.default.isExecutableFile(atPath: url.path) {
                return url
            }
        }

        return nil
    }

    // MARK: - Health Check Waiting

    /// 等待后端健康检查通过（指数退避）
    private func waitForHealthy(
        maxAttempts: Int,
        initialDelay: TimeInterval,
        maxDelay: TimeInterval,
        totalTimeout: TimeInterval
    ) async -> Bool {
        let startTime = Date()
        var delay = initialDelay

        for _ in 1...maxAttempts {
            // 检查总超时
            if Date().timeIntervalSince(startTime) > totalTimeout {
                return false
            }

            // 检查进程是否已退出
            if let process = backendProcess, !process.isRunning {
                return false
            }

            // 尝试健康检查
            if await healthCheck() {
                return true
            }

            // 指数退避等待
            try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
            delay = min(delay * 1.5, maxDelay)
        }

        return false
    }

    // MARK: - Process Termination

    /// 处理进程异常终止
    private func handleProcessTermination(exitCode: Int32) {
        isRunning = false
        backendProcess = nil
        outputPipe = nil
        errorPipe = nil
    }

    /// 健康检查
    /// - Returns: 后端是否健康
    public func healthCheck() async -> Bool {
        let healthURL = backendURL.appendingPathComponent("health")

        do {
            let (data, response) = try await URLSession.shared.data(from: healthURL)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                return false
            }

            // 尝试解码响应以验证格式
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let status = json["status"] as? String,
               status == "healthy" || status == "ok" {
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
        let executeURL = backendURL.appendingPathComponent("execute")

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
        let versionURL = backendURL.appendingPathComponent("version")

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
