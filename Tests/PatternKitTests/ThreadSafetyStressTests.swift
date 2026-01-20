// MacCortex PatternKit - 线程安全压力测试
// 测试审查专用

import XCTest
@testable import PatternKit

final class ThreadSafetyStressTests: XCTestCase {

    /// 高并发注册测试 - 验证 NSLock 是否真正有效
    func testConcurrentRegistration() async throws {
        let registry = PatternRegistry.shared

        // 100 个并发任务同时注册 Pattern
        try await withThrowingTaskGroup(of: Void.self) { group in
            for i in 0..<100 {
                group.addTask {
                    // 创建临时 Pattern
                    let pattern = MockAIPattern(id: "concurrent_\(i)")
                    try? registry.register(pattern)
                }
            }

            try await group.waitForAll()
        }

        // 验证：不应该有数据竞争导致的崩溃或数据损坏
        let allPatterns = registry.allPatterns()
        XCTAssertGreaterThan(allPatterns.count, 5, "应该至少保留默认的 5 个 Pattern")
    }

    /// 读写混合压力测试
    func testConcurrentReadWrite() async throws {
        let registry = PatternRegistry.shared

        try await withThrowingTaskGroup(of: Void.self) { group in
            // 50 个读任务
            for _ in 0..<50 {
                group.addTask {
                    _ = registry.allPatterns()
                    _ = registry.pattern(withID: "summarize")
                    _ = registry.statistics()
                }
            }

            // 10 个写任务
            for i in 0..<10 {
                group.addTask {
                    let pattern = MockAIPattern(id: "stress_\(i)")
                    try? registry.register(pattern)
                    registry.unregister("stress_\(i)")
                }
            }

            try await group.waitForAll()
        }

        // 验证注册表仍然完整
        XCTAssertTrue(registry.hasPattern(withID: "summarize"))
    }

    /// 极限并发执行测试
    func testExtremeConcurrentExecution() async throws {
        let registry = PatternRegistry.shared

        let input = PatternInput(
            text: String(repeating: "Test sentence for summarization. ", count: 10),
            parameters: ["length": "short"]
        )

        // 200 个并发执行请求
        let results = try await withThrowingTaskGroup(of: PatternResult.self, returning: [PatternResult].self) { group in
            for _ in 0..<200 {
                group.addTask {
                    try await registry.execute(patternID: "summarize", input: input)
                }
            }

            var allResults: [PatternResult] = []
            for try await result in group {
                allResults.append(result)
            }
            return allResults
        }

        XCTAssertEqual(results.count, 200, "所有请求应该成功返回")
        XCTAssertTrue(results.allSatisfy { $0.success }, "所有执行应该成功")
    }

    /// 内存泄漏检测 - 大量 Pattern 注册后取消注册
    func testMemoryLeakOnMassiveRegistration() {
        let registry = PatternRegistry.shared

        measure(metrics: [XCTMemoryMetric()]) {
            // 注册 1000 个 Pattern
            for i in 0..<1000 {
                let pattern = MockAIPattern(id: "leak_test_\(i)")
                try? registry.register(pattern)
            }

            // 取消注册所有
            for i in 0..<1000 {
                registry.unregister("leak_test_\(i)")
            }
        }
    }
}

// MockAIPattern 定义在 TestHelpers.swift
