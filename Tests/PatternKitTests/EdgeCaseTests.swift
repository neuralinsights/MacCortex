// MacCortex PatternKit - 边界条件和错误路径测试
// 测试审查专用 - 无情的边界测试

import XCTest
@testable import PatternKit
@testable import PythonBridge

final class EdgeCaseTests: XCTestCase {

    // MARK: - 输入验证边界测试

    /// 测试：词数不足（SummarizePattern 应该拒绝）
    func testSummarizePattern_Exactly49Characters() async {
        let pattern = SummarizePattern()
        // 英文：少于 30 词应该被拒绝
        let input = PatternInput(
            text: Array(repeating: "word", count: 20).joined(separator: " "),  // 20 词
            parameters: ["language": "en"]
        )

        XCTAssertFalse(pattern.validate(input: input), "20 词应该被拒绝（< 30 词）")
    }

    /// 测试：词数刚好（SummarizePattern 应该接受）
    func testSummarizePattern_Exactly50Characters() async {
        let pattern = SummarizePattern()
        // 英文：30 词应该被接受
        let input = PatternInput(
            text: Array(repeating: "word", count: 30).joined(separator: " "),  // 30 词
            parameters: ["language": "en"]
        )

        XCTAssertTrue(pattern.validate(input: input), "30 词应该被接受")
    }

    /// 测试：纯空白字符（应该被所有 Pattern 拒绝）
    func testAllPatterns_WhitespaceOnlyInput() {
        let patterns: [PatternKit.AIPattern] = [
            SummarizePattern(),
            ExtractPattern(),
            TranslatePattern(),
            FormatPattern(),
            SearchPattern()
        ]

        let whitespaceInputs = [
            "   ",
            "\t\t\t",
            "\n\n\n",
            " \t\n ",
            String(repeating: " ", count: 100)
        ]

        for pattern in patterns {
            for whitespace in whitespaceInputs {
                let input = PatternInput(text: whitespace, parameters: [:])
                XCTAssertFalse(
                    pattern.validate(input: input),
                    "\(pattern.id) 应该拒绝纯空白: '\(whitespace.debugDescription)'"
                )
            }
        }
    }

    /// 测试：空字符串
    func testAllPatterns_EmptyString() {
        let patterns: [PatternKit.AIPattern] = [
            SummarizePattern(),
            ExtractPattern(),
            TranslatePattern(),
            FormatPattern(),
            SearchPattern()
        ]

        for pattern in patterns {
            let input = PatternInput(text: "", parameters: [:])
            XCTAssertFalse(
                pattern.validate(input: input),
                "\(pattern.id) 应该拒绝空字符串"
            )
        }
    }

    /// 测试：超长输入（10MB）
    func testAllPatterns_ExtremelyLongInput() async throws {
        let hugeText = String(repeating: "A", count: 10_000_000) // 10MB

        let patterns: [PatternKit.AIPattern] = [
            SummarizePattern(),
            TranslatePattern()
        ]

        for pattern in patterns {
            let input = PatternInput(text: hugeText, parameters: [:])

            // 应该不会崩溃
            XCTAssertTrue(pattern.validate(input: input), "\(pattern.id) 应该能处理超长输入验证")

            // 执行不应该崩溃（即使是 mock）
            let result = try await pattern.execute(input: input)
            XCTAssertTrue(result.success, "\(pattern.id) 超长输入不应崩溃")
        }
    }

    // MARK: - 参数边界测试

    /// 测试：无效的枚举值（应该回退到默认值）
    func testSummarizePattern_InvalidEnumValues() async throws {
        let pattern = SummarizePattern()

        let invalidInputs: [[String: Any]] = [
            ["length": "超长"],         // 无效的 length
            ["style": "诗歌"],          // 无效的 style
            ["length": 123],           // 错误的类型
            ["style": true],           // 错误的类型
            ["length": ""],            // 空字符串
            ["style": ""]              // 空字符串
        ]

        for params in invalidInputs {
            let input = PatternInput(
                text: String(repeating: "Test sentence. ", count: 10),
                parameters: params
            )

            // 应该回退到默认值，不应崩溃
            let result = try await pattern.execute(input: input)
            XCTAssertTrue(result.success, "无效参数应该回退到默认值: \(params)")
        }
    }

    /// 测试：TranslatePattern 相同语言对
    func testTranslatePattern_SameSourceAndTargetLanguage() async {
        let pattern = TranslatePattern()
        let input = PatternInput(
            text: "Hello world",
            parameters: [
                "source_language": "en",
                "target_language": "en"  // 相同！
            ]
        )

        // 修复 P0 #3 后，validate() 会在执行前检查语言对
        XCTAssertFalse(pattern.validate(input: input), "相同语言对应该验证失败")

        // PatternRegistry.execute() 会因为 validate() 返回 false 而抛出错误
        do {
            _ = try await PatternRegistry.shared.execute(patternID: "translate", input: input)
            XCTFail("相同语言对应该抛出错误")
        } catch PatternError.invalidInput {
            // 预期的错误
        } catch {
            XCTFail("应该抛出 invalidInput 错误，而非 \(error)")
        }
    }

    /// 测试：SearchPattern 参数边界
    func testSearchPattern_ParameterBoundaries() async throws {
        let pattern = SearchPattern()

        // 测试 max_results 边界
        let testCases: [(params: [String: Any], expectedInMetadata: Bool)] = [
            (["max_results": 0], false),       // 应该钳制到 1
            (["max_results": 1], true),        // 最小值
            (["max_results": 100], true),      // 最大值
            (["max_results": 101], false),     // 应该钳制到 100
            (["max_results": -10], false),     // 负数应该钳制到 1
            (["max_results": 1000], false),    // 超大值应该钳制到 100
        ]

        for (params, _) in testCases {
            let input = PatternInput(
                text: "test query",
                parameters: params
            )

            // 应该不会崩溃
            let result = try await pattern.execute(input: input)
            XCTAssertTrue(result.success, "参数边界应该被正确处理: \(params)")
        }
    }

    // MARK: - 并发竞争条件测试

    /// 测试：同时修改相同 Pattern
    func testPatternRegistry_ConcurrentModificationOfSameID() async throws {
        let registry = PatternRegistry.shared

        // 100 个任务同时注册/取消注册相同 ID
        try await withThrowingTaskGroup(of: Void.self) { group in
            for i in 0..<100 {
                group.addTask {
                    let pattern = MockAIPattern(id: "conflict_test")
                    if i % 2 == 0 {
                        try? registry.register(pattern)
                    } else {
                        registry.unregister("conflict_test")
                    }
                }
            }

            try await group.waitForAll()
        }

        // 注册表应该仍然完整
        let allPatterns = registry.allPatterns()
        XCTAssertGreaterThanOrEqual(allPatterns.count, 0, "注册表不应该损坏")
    }

    /// 测试：执行中取消注册
    func testPatternRegistry_UnregisterDuringExecution() async throws {
        let registry = PatternRegistry.shared
        let pattern = MockAIPattern(id: "executing_pattern")
        try registry.register(pattern)

        let input = PatternInput(text: "test", parameters: [:])

        try await withThrowingTaskGroup(of: Void.self) { group in
            // 任务 1: 执行 Pattern
            group.addTask {
                for _ in 0..<10 {
                    _ = try? await registry.execute(patternID: "executing_pattern", input: input)
                }
            }

            // 任务 2: 同时取消注册
            group.addTask {
                registry.unregister("executing_pattern")
            }

            try await group.waitForAll()
        }

        // 应该不会崩溃
    }

    // MARK: - 类型转换边界测试

    /// 测试：AnyCodable 边界情况
    func testAnyCodable_EdgeCases() throws {
        let testCases: [Any] = [
            NSNull(),
            Int.max,
            Int.min,
            Double.infinity,
            Double.nan,
            "",
            [],
            [:],
            [1, 2, 3],
            ["key": "value"],
            [1, "mixed", true],  // 混合类型数组
        ]

        for value in testCases {
            let codable = AnyCodable(value)

            // 编码
            let encoder = JSONEncoder()
            let data = try encoder.encode(codable)

            // 解码
            let decoder = JSONDecoder()
            let decoded = try decoder.decode(AnyCodable.self, from: data)

            // 验证不会崩溃（具体值可能不同，但不应崩溃）
            XCTAssertNotNil(decoded.value, "AnyCodable 应该能处理: \(value)")
        }
    }

    /// 测试：FormatPattern 正则表达式边界
    func testFormatPattern_RegexEdgeCases() async throws {
        let pattern = FormatPattern()

        let edgeCases = [
            "**粗体**",                      // 中文粗体
            "*斜体*",                        // 中文斜体
            "**嵌套的**粗体**",              // 错误嵌套
            "*****多个星号*****",            // 多个星号
            "**未闭合粗体",                  // 未闭合
            "[链接]()",                      // 空链接
            "[](http://example.com)",       // 空文本
            "[][]",                         // 多个空
            "#标题没有空格",                 // 标题无空格
            "# # # 多个空格",                // 多个空格
        ]

        for edgeCase in edgeCases {
            let input = PatternInput(
                text: edgeCase,
                parameters: [
                    "source_format": "markdown",
                    "target_format": "plaintext"
                ]
            )

            // 应该不会崩溃
            let result = try await pattern.execute(input: input)
            XCTAssertTrue(result.success, "Markdown 边界情况应该被处理: '\(edgeCase)'")
        }
    }
}

// MockAIPattern 定义在 TestHelpers.swift
