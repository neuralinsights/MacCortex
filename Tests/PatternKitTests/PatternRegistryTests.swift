// MacCortex PatternKit Tests - Pattern Registry Tests
// Phase 1 - Week 2 Day 6-7
// 创建时间: 2026-01-20

import XCTest
@testable import PatternKit

final class PatternRegistryTests: XCTestCase {

    // MARK: - Lifecycle

    override func setUp() {
        super.setUp()
        // 注意：PatternRegistry 是单例，每个测试会共享状态
        // 实际使用中需要注意清理
    }

    // MARK: - Registration Tests

    func testSingletonInstance() {
        let instance1 = PatternRegistry.shared
        let instance2 = PatternRegistry.shared

        XCTAssertTrue(instance1 === instance2, "应该返回相同的单例实例")
    }

    func testDefaultPatternsRegistered() {
        let registry = PatternRegistry.shared
        let allPatterns = registry.allPatterns()

        XCTAssertGreaterThanOrEqual(allPatterns.count, 5, "应该至少注册 5 个默认 Pattern")

        // 验证核心 Pattern 存在
        XCTAssertTrue(registry.hasPattern(withID: "summarize"), "应该包含 SummarizePattern")
        XCTAssertTrue(registry.hasPattern(withID: "extract"), "应该包含 ExtractPattern")
        XCTAssertTrue(registry.hasPattern(withID: "translate"), "应该包含 TranslatePattern")
        XCTAssertTrue(registry.hasPattern(withID: "format"), "应该包含 FormatPattern")
        XCTAssertTrue(registry.hasPattern(withID: "search"), "应该包含 SearchPattern")
    }

    func testPatternLookupByID() {
        let registry = PatternRegistry.shared

        let summarizePattern = registry.pattern(withID: "summarize")
        XCTAssertNotNil(summarizePattern, "应该能找到 summarize Pattern")
        XCTAssertEqual(summarizePattern?.id, "summarize")
        XCTAssertEqual(summarizePattern?.name, "Summarize")

        let nonexistentPattern = registry.pattern(withID: "nonexistent")
        XCTAssertNil(nonexistentPattern, "不存在的 Pattern 应该返回 nil")
    }

    func testPatternsByType() {
        let registry = PatternRegistry.shared

        let localPatterns = registry.patterns(ofType: .local)
        let pythonPatterns = registry.patterns(ofType: .python)

        // FormatPattern 是 local 类型
        XCTAssertTrue(localPatterns.contains(where: { $0.id == "format" }), "应该包含 local 类型的 FormatPattern")

        // 其他 Pattern 是 python 类型
        XCTAssertTrue(pythonPatterns.contains(where: { $0.id == "summarize" }))
        XCTAssertTrue(pythonPatterns.contains(where: { $0.id == "extract" }))
        XCTAssertTrue(pythonPatterns.contains(where: { $0.id == "translate" }))
        XCTAssertTrue(pythonPatterns.contains(where: { $0.id == "search" }))
    }

    // MARK: - Execution Tests

    func testExecutePattern() async throws {
        let registry = PatternRegistry.shared

        let input = PatternInput(
            text: "This is a test document for summarization. It contains multiple sentences to test the summarize pattern.",
            parameters: [
                "length": "short",
                "style": "bullet"
            ]
        )

        let result = try await registry.execute(patternID: "summarize", input: input)

        XCTAssertTrue(result.success, "执行应该成功")
        XCTAssertFalse(result.output.isEmpty, "应该有输出")
        XCTAssertNotNil(result.metadata, "应该有元数据")
        XCTAssertGreaterThan(result.duration, 0, "执行时间应该大于 0")
    }

    func testExecuteNonexistentPattern() async {
        let registry = PatternRegistry.shared

        let input = PatternInput(text: "Test", parameters: [:])

        do {
            _ = try await registry.execute(patternID: "nonexistent", input: input)
            XCTFail("执行不存在的 Pattern 应该抛出错误")
        } catch PatternError.executionFailed(let message) {
            XCTAssertTrue(message.contains("not found"), "错误信息应该说明 Pattern 未找到")
        } catch {
            XCTFail("应该抛出 executionFailed 错误")
        }
    }

    func testExecuteWithInvalidInput() async {
        let registry = PatternRegistry.shared

        // 空文本对于大多数 Pattern 是无效的
        let input = PatternInput(text: "", parameters: [:])

        do {
            _ = try await registry.execute(patternID: "summarize", input: input)
            XCTFail("无效输入应该抛出错误")
        } catch PatternError.invalidInput {
            // 预期的错误
        } catch {
            XCTFail("应该抛出 invalidInput 错误")
        }
    }

    func testExecuteAllPatterns() async throws {
        let registry = PatternRegistry.shared

        let requests: [(patternID: String, input: PatternInput)] = [
            ("summarize", PatternInput(text: "This is a long text document that needs to be summarized. It contains multiple sentences and paragraphs with various information that should be condensed into key points.", parameters: [:])),
            ("extract", PatternInput(text: "John Smith, john@example.com, 2026-01-20", parameters: ["type": "names"])),
            ("search", PatternInput(text: "AI technology", parameters: ["mode": "semantic"]))
        ]

        let results = try await registry.executeAll(requests)

        XCTAssertEqual(results.count, 3, "应该返回 3 个结果")
        XCTAssertTrue(results.allSatisfy { $0.success }, "所有执行应该成功")
    }

    // MARK: - Metadata Tests

    func testAllMetadata() {
        let registry = PatternRegistry.shared
        let metadata = registry.allMetadata()

        XCTAssertGreaterThanOrEqual(metadata.count, 5, "应该至少有 5 个 Pattern 的元数据")

        // 验证元数据结构
        for meta in metadata {
            XCTAssertNotNil(meta["id"])
            XCTAssertNotNil(meta["name"])
            XCTAssertNotNil(meta["description"])
            XCTAssertNotNil(meta["version"])
            XCTAssertNotNil(meta["type"])
        }
    }

    func testPatternMetadata() {
        let registry = PatternRegistry.shared

        let summarizeMeta = registry.metadata(forPatternID: "summarize")
        XCTAssertNotNil(summarizeMeta)
        XCTAssertEqual(summarizeMeta?["id"] as? String, "summarize")
        XCTAssertEqual(summarizeMeta?["name"] as? String, "Summarize")

        let nonexistentMeta = registry.metadata(forPatternID: "nonexistent")
        XCTAssertNil(nonexistentMeta, "不存在的 Pattern 应该返回 nil")
    }

    func testStatistics() {
        let registry = PatternRegistry.shared
        let stats = registry.statistics()

        XCTAssertNotNil(stats["total"])
        XCTAssertNotNil(stats["local"])
        XCTAssertNotNil(stats["python"])
        XCTAssertNotNil(stats["remote"])

        let total = stats["total"] as? Int ?? 0
        let local = stats["local"] as? Int ?? 0
        let python = stats["python"] as? Int ?? 0
        let remote = stats["remote"] as? Int ?? 0

        XCTAssertGreaterThanOrEqual(total, 5)
        XCTAssertEqual(total, local + python + remote, "总数应该等于各类型之和")
    }

    // MARK: - Performance Tests

    func testPatternLookupPerformance() {
        let registry = PatternRegistry.shared

        measure {
            for _ in 0..<1000 {
                _ = registry.pattern(withID: "summarize")
            }
        }
    }

    func testConcurrentAccess() async throws {
        let registry = PatternRegistry.shared

        // 并发查询 Pattern
        try await withThrowingTaskGroup(of: Void.self) { group in
            for _ in 0..<10 {
                group.addTask {
                    _ = registry.allPatterns()
                    _ = registry.pattern(withID: "summarize")
                    _ = registry.patterns(ofType: .python)
                }
            }

            try await group.waitForAll()
        }

        // 验证注册表仍然正常
        XCTAssertGreaterThanOrEqual(registry.allPatterns().count, 5)
    }

    // MARK: - Debug Output Test

    func testPrintAllPatterns() {
        let registry = PatternRegistry.shared

        // 这个测试只是确保 printAllPatterns 不会崩溃
        registry.printAllPatterns()

        // 无断言，只要不崩溃就通过
    }
}
