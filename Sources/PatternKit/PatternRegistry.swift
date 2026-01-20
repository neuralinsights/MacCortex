// MacCortex PatternKit - Pattern Registry
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20
//
// Pattern 注册表，用于管理和发现所有可用的 AIPattern

import Foundation

/// Pattern 注册表
///
/// 管理所有可用的 AIPattern 实例，提供查询、执行和元数据访问
public class PatternRegistry {

    // MARK: - Singleton

    /// 共享实例
    public static let shared = PatternRegistry()

    // MARK: - Properties

    /// 已注册的 AIPattern（key: pattern ID）
    private var patterns: [String: AIPattern] = [:]

    /// 注册表锁（线程安全）
    private let lock = NSLock()

    // MARK: - Initialization

    private init() {
        registerDefaultPatterns()
    }

    // MARK: - Registration

    /// 注册 AIPattern
    /// - Parameter pattern: 要注册的 AIPattern
    /// - Throws: 如果 ID 已存在则抛出错误
    public func register(_ pattern: AIPattern) throws {
        lock.lock()
        defer { lock.unlock() }

        guard patterns[pattern.id] == nil else {
            throw PatternError.executionFailed("AIPattern with ID '\(pattern.id)' already registered")
        }

        patterns[pattern.id] = pattern
    }

    /// 批量注册 AIPattern
    /// - Parameter patterns: 要注册的 AIPattern 数组
    public func registerAll(_ patterns: [AIPattern]) {
        for pattern in patterns {
            try? register(pattern)
        }
    }

    /// 取消注册 AIPattern
    /// - Parameter id: AIPattern ID
    public func unregister(_ id: String) {
        lock.lock()
        defer { lock.unlock() }

        patterns.removeValue(forKey: id)
    }

    /// 注册默认 Pattern
    private func registerDefaultPatterns() {
        let defaultPatterns: [AIPattern] = [
            SummarizePattern(),
            ExtractPattern(),
            TranslatePattern(),
            FormatPattern(),
            SearchPattern()
        ]

        registerAll(defaultPatterns)
    }

    // MARK: - Query

    /// 获取所有已注册的 Pattern
    /// - Returns: AIPattern 数组
    public func allPatterns() -> [AIPattern] {
        lock.lock()
        defer { lock.unlock() }

        return Array(patterns.values)
    }

    /// 根据 ID 查找 AIPattern
    /// - Parameter id: AIPattern ID
    /// - Returns: AIPattern 实例（如果存在）
    public func pattern(withID id: String) -> AIPattern? {
        lock.lock()
        defer { lock.unlock() }

        return patterns[id]
    }

    /// 根据类型查找 AIPattern
    /// - Parameter type: AIPattern 类型
    /// - Returns: 匹配的 AIPattern 数组
    public func patterns(ofType type: PatternType) -> [AIPattern] {
        lock.lock()
        defer { lock.unlock() }

        return patterns.values.filter { $0.type == type }
    }

    /// 检查 Pattern 是否存在
    /// - Parameter id: Pattern ID
    /// - Returns: 是否存在
    public func hasPattern(withID id: String) -> Bool {
        lock.lock()
        defer { lock.unlock() }

        return patterns[id] != nil
    }

    // MARK: - Execution

    /// 执行 AIPattern
    /// - Parameters:
    ///   - id: AIPattern ID
    ///   - input: 输入数据
    /// - Returns: 执行结果
    /// - Throws: 如果 AIPattern 不存在或执行失败
    public func execute(patternID id: String, input: PatternInput) async throws -> PatternResult {
        guard let pattern = pattern(withID: id) else {
            throw PatternError.executionFailed("AIPattern '\(id)' not found")
        }

        // 验证输入
        guard pattern.validate(input: input) else {
            throw PatternError.invalidInput("Invalid input for pattern '\(id)'")
        }

        // 执行 AIPattern
        return try await pattern.execute(input: input)
    }

    /// 批量执行 AIPattern（并行）
    /// - Parameter requests: 执行请求数组（AIPattern ID + Input）
    /// - Returns: 执行结果数组
    public func executeAll(_ requests: [(patternID: String, input: PatternInput)]) async throws -> [PatternResult] {
        return try await withThrowingTaskGroup(of: PatternResult.self) { group in
            for request in requests {
                group.addTask {
                    try await self.execute(patternID: request.patternID, input: request.input)
                }
            }

            var results: [PatternResult] = []
            for try await result in group {
                results.append(result)
            }
            return results
        }
    }

    // MARK: - Metadata

    /// 获取所有 AIPattern 的元数据
    /// - Returns: 元数据字典数组
    public func allMetadata() -> [[String: Any]] {
        lock.lock()
        defer { lock.unlock() }

        return patterns.values.map { pattern in
            [
                "id": pattern.id,
                "name": pattern.name,
                "description": pattern.description,
                "version": pattern.version,
                "type": String(describing: pattern.type)
            ]
        }
    }

    /// 获取单个 Pattern 的元数据
    /// - Parameter id: Pattern ID
    /// - Returns: 元数据字典（如果 Pattern 存在）
    public func metadata(forPatternID id: String) -> [String: Any]? {
        guard let pattern = pattern(withID: id) else {
            return nil
        }

        return [
            "id": pattern.id,
            "name": pattern.name,
            "description": pattern.description,
            "version": pattern.version,
            "type": String(describing: pattern.type)
        ]
    }

    // MARK: - Statistics

    /// 获取统计信息
    /// - Returns: 统计信息字典
    public func statistics() -> [String: Any] {
        lock.lock()
        defer { lock.unlock() }

        let totalCount = patterns.count
        let localCount = patterns.values.filter { $0.type == .local }.count
        let pythonCount = patterns.values.filter { $0.type == .python }.count
        let remoteCount = patterns.values.filter { $0.type == .remote }.count

        return [
            "total": totalCount,
            "local": localCount,
            "python": pythonCount,
            "remote": remoteCount
        ]
    }

    // MARK: - Debugging

    /// 打印所有已注册的 Pattern
    public func printAllPatterns() {
        lock.lock()
        defer { lock.unlock() }

        print("=== PatternRegistry: Registered AIPatterns ===")
        print("Total: \(patterns.count)\n")

        for pattern in patterns.values.sorted(by: { $0.id < $1.id }) {
            print("[\(pattern.id)]")
            print("  Name: \(pattern.name)")
            print("  Description: \(pattern.description)")
            print("  Version: \(pattern.version)")
            print("  Type: \(pattern.type)")
            print("")
        }
    }
}
