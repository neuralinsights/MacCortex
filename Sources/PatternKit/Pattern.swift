// MacCortex PatternKit - Pattern 协议定义
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20
//
// Pattern 是 MacCortex 的核心抽象，代表一种可重用的 AI 处理模式

import Foundation

/// Pattern 执行结果
public struct PatternResult {
    /// 处理后的输出
    public let output: String

    /// 元数据（可选）
    public let metadata: [String: Any]?

    /// 执行耗时（秒）
    public let duration: TimeInterval

    /// 是否成功
    public let success: Bool

    /// 错误信息（失败时）
    public let error: String?

    public init(
        output: String,
        metadata: [String: Any]? = nil,
        duration: TimeInterval,
        success: Bool = true,
        error: String? = nil
    ) {
        self.output = output
        self.metadata = metadata
        self.duration = duration
        self.success = success
        self.error = error
    }
}

/// Pattern 输入
public struct PatternInput {
    /// 输入文本
    public let text: String

    /// 附加参数
    public let parameters: [String: Any]

    /// 上下文信息
    public let context: [String: Any]?

    public init(
        text: String,
        parameters: [String: Any] = [:],
        context: [String: Any]? = nil
    ) {
        self.text = text
        self.parameters = parameters
        self.context = context
    }
}

/// Pattern 协议
///
/// 所有 Pattern 必须实现此协议
public protocol Pattern {
    /// Pattern 唯一标识符
    var id: String { get }

    /// Pattern 名称
    var name: String { get }

    /// Pattern 描述
    var description: String { get }

    /// Pattern 版本
    var version: String { get }

    /// Pattern 类型（本地/远程）
    var type: PatternType { get }

    /// 执行 Pattern
    /// - Parameter input: 输入数据
    /// - Returns: 处理结果
    /// - Throws: 处理错误
    func execute(input: PatternInput) async throws -> PatternResult

    /// 验证输入是否有效
    /// - Parameter input: 输入数据
    /// - Returns: 是否有效
    func validate(input: PatternInput) -> Bool
}

/// Pattern 类型
public enum PatternType {
    /// 本地处理（Swift）
    case local

    /// Python 后端处理
    case python

    /// 远程 API 处理
    case remote
}

/// Pattern 错误
public enum PatternError: Error, LocalizedError {
    /// 输入无效
    case invalidInput(String)

    /// 执行失败
    case executionFailed(String)

    /// 超时
    case timeout

    /// 后端不可用
    case backendUnavailable

    /// 未知错误
    case unknown(String)

    public var errorDescription: String? {
        switch self {
        case .invalidInput(let message):
            return "Invalid input: \(message)"
        case .executionFailed(let message):
            return "Execution failed: \(message)"
        case .timeout:
            return "Pattern execution timed out"
        case .backendUnavailable:
            return "Backend service unavailable"
        case .unknown(let message):
            return "Unknown error: \(message)"
        }
    }
}

// MARK: - Pattern Extension

extension Pattern {
    /// 默认验证实现（检查输入文本非空）
    public func validate(input: PatternInput) -> Bool {
        return !input.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
}
