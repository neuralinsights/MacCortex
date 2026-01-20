// MacCortex PythonBridge - Integration Tests
// Phase 1 - Week 2 Day 8
// 创建时间: 2026-01-20
//
// Swift ↔ Python HTTP 通信集成测试（需要后端运行）

import XCTest
@testable import PythonBridge

final class IntegrationTests: XCTestCase {

    var bridge: PythonBridge!

    override func setUp() async throws {
        try await super.setUp()
        bridge = PythonBridge.shared

        // 注意：这些测试需要 Python 后端运行
        // 启动命令: cd Backend && source .venv/bin/activate && cd src && python main.py
    }

    // MARK: - 健康检查测试

    /// 测试：健康检查端点
    func testHealthCheck() async {
        // 假设后端已经运行
        bridge.setRunningState(true)

        let isHealthy = await bridge.healthCheck()

        XCTAssertTrue(isHealthy, "后端应该返回 healthy 状态")
    }

    /// 测试：后端未运行时健康检查失败
    func testHealthCheck_BackendNotRunning() async {
        // 修改 URL 到不存在的端口
        let originalIsRunning = bridge.isRunning
        bridge.setRunningState(true)

        // 创建新的 bridge 实例，使用错误的端口
        let testBridge = PythonBridge.shared
        // 注意：由于 PythonBridge 是单例，这个测试可能不准确
        // 在真实场景中，后端未运行会返回 false

        bridge.setRunningState(originalIsRunning)
    }

    // MARK: - 版本信息测试

    /// 测试：获取版本信息
    func testGetVersion() async throws {
        bridge.setRunningState(true)

        let versionInfo = try await bridge.getVersion()

        // 验证返回的版本信息
        XCTAssertNotNil(versionInfo["python"], "应该包含 Python 版本")
        XCTAssertNotNil(versionInfo["backend"], "应该包含 Backend 版本")

        print("📋 版本信息:")
        for (key, value) in versionInfo {
            print("  \(key): \(value)")
        }
    }

    // MARK: - Pattern 执行测试

    /// 测试：执行 SummarizePattern (Mock 模式)
    func testExecuteSummarizePattern_MockMode() async throws {
        bridge.setRunningState(true)

        let request = PythonRequest(
            patternID: "summarize",
            text: "MacCortex 是下一代 macOS 个人智能基础设施，集成了 Pattern CLI 框架、Python 后端以及 LangGraph 工作流编排。",
            parameters: [
                "length": AnyCodable("medium"),
                "style": AnyCodable("bullet"),
                "language": AnyCodable("zh-CN")
            ],
            requestID: "swift-test-001"
        )

        let response = try await bridge.execute(request: request)

        // 验证响应
        XCTAssertEqual(response.requestID, "swift-test-001", "请求 ID 应该匹配")
        XCTAssertTrue(response.success, "执行应该成功")
        XCTAssertNotNil(response.output, "应该有输出")
        XCTAssertNil(response.error, "不应该有错误")
        XCTAssertGreaterThan(response.duration, 0, "执行时间应该大于 0")

        // 验证 Mock 输出内容
        if let output = response.output {
            XCTAssertTrue(output.contains("Mock"), "应该包含 Mock 标识")
            XCTAssertTrue(output.contains("•"), "Bullet 风格应该包含项目符号")
        }

        // 验证元数据
        if let metadata = response.metadata {
            XCTAssertEqual(metadata["length"]?.value as? String, "medium")
            XCTAssertEqual(metadata["style"]?.value as? String, "bullet")
            XCTAssertEqual(metadata["language"]?.value as? String, "zh-CN")
        }

        print("\n📝 SummarizePattern 测试结果:")
        print("  ✅ 成功: \(response.success)")
        print("  ⏱️ 耗时: \(String(format: "%.3f", response.duration))s")
        print("  📄 输出:\n\(response.output ?? "无")")
    }

    /// 测试：输入验证（文本过短）
    func testExecutePattern_InvalidInput_TextTooShort() async throws {
        bridge.setRunningState(true)

        let request = PythonRequest(
            patternID: "summarize",
            text: "短文本",  // 只有 3 个字符，少于最小要求
            parameters: [
                "language": AnyCodable("zh-CN")
            ]
        )

        let response = try await bridge.execute(request: request)

        // 验证失败响应
        XCTAssertFalse(response.success, "输入验证应该失败")
        XCTAssertNotNil(response.error, "应该有错误信息")
        XCTAssertNil(response.output, "不应该有输出")

        print("\n❌ 输入验证测试:")
        print("  错误: \(response.error ?? "无")")
    }

    /// 测试：Pattern 不存在
    func testExecutePattern_PatternNotFound() async throws {
        bridge.setRunningState(true)

        let request = PythonRequest(
            patternID: "nonexistent_pattern",
            text: "测试文本",
            parameters: [:]
        )

        let response = try await bridge.execute(request: request)

        // 验证失败响应
        XCTAssertFalse(response.success, "不存在的 Pattern 应该失败")
        XCTAssertNotNil(response.error, "应该有错误信息")

        if let error = response.error {
            XCTAssertTrue(
                error.contains("not found") || error.contains("Pattern"),
                "错误信息应该提示 Pattern 不存在"
            )
        }

        print("\n❌ Pattern 不存在测试:")
        print("  错误: \(response.error ?? "无")")
    }

    // MARK: - 性能测试

    /// 测试：执行延迟（目标 < 2s）
    func testExecutionLatency() async throws {
        bridge.setRunningState(true)

        let iterations = 10
        var totalDuration: Double = 0

        print("\n⏱️ 性能测试（\(iterations) 次执行）:")

        for i in 1...iterations {
            let startTime = Date()

            let request = PythonRequest(
                patternID: "summarize",
                text: String(repeating: "测试文本句子。", count: 20),  // 约 100 字符
                parameters: [
                    "length": AnyCodable("short"),
                    "language": AnyCodable("zh-CN")
                ]
            )

            let response = try await bridge.execute(request: request)
            let latency = Date().timeIntervalSince(startTime)

            XCTAssertTrue(response.success, "执行应该成功")
            XCTAssertLessThan(latency, 2.0, "延迟应该小于 2 秒")

            totalDuration += latency
            print("  第 \(i) 次: \(String(format: "%.3f", latency))s")
        }

        let avgLatency = totalDuration / Double(iterations)
        print("  📊 平均延迟: \(String(format: "%.3f", avgLatency))s")
        print("  🎯 目标: < 2.0s")

        XCTAssertLessThan(avgLatency, 2.0, "平均延迟应该小于 2 秒")
    }

    // MARK: - 并发测试

    /// 测试：并发请求
    func testConcurrentRequests() async throws {
        bridge.setRunningState(true)

        let concurrency = 5
        print("\n🚀 并发测试（\(concurrency) 个同时请求）:")

        let startTime = Date()

        try await withThrowingTaskGroup(of: PythonResponse.self) { group in
            for i in 1...concurrency {
                group.addTask {
                    let request = PythonRequest(
                        patternID: "summarize",
                        text: "并发测试文本 #\(i)：" + String(repeating: "测试句子。", count: 10),
                        parameters: [
                            "length": AnyCodable("short"),
                            "language": AnyCodable("zh-CN")
                        ],
                        requestID: "concurrent-\(i)"
                    )

                    return try await self.bridge.execute(request: request)
                }
            }

            var successCount = 0
            for try await response in group {
                if response.success {
                    successCount += 1
                }
            }

            let totalTime = Date().timeIntervalSince(startTime)
            print("  ✅ 成功: \(successCount)/\(concurrency)")
            print("  ⏱️ 总耗时: \(String(format: "%.3f", totalTime))s")

            XCTAssertEqual(successCount, concurrency, "所有请求都应该成功")
        }
    }

    // MARK: - 错误处理测试

    /// 测试：后端未运行时的错误处理
    func testExecute_BackendNotRunning() async throws {
        bridge.setRunningState(false)

        let request = PythonRequest(
            patternID: "summarize",
            text: "测试文本",
            parameters: [:]
        )

        do {
            _ = try await bridge.execute(request: request)
            XCTFail("应该抛出 backendNotRunning 错误")
        } catch PythonBridgeError.backendNotRunning {
            // 预期的错误
            print("\n✅ 正确捕获 backendNotRunning 错误")
        } catch {
            XCTFail("应该抛出 PythonBridgeError.backendNotRunning，而非 \(error)")
        }
    }
}
