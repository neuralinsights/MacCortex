// MacCortex PatternKit Tests - 共享测试工具
// 测试审查专用

import Foundation
@testable import PatternKit

/// Mock Pattern - 用于测试
class MockAIPattern: PatternKit.AIPattern {
    let id: String
    let name = "Mock"
    let description = "Mock Pattern for testing"
    let version = "1.0.0"
    let type: PatternType = .local

    init(id: String) {
        self.id = id
    }

    func execute(input: PatternInput) async throws -> PatternResult {
        // 模拟一些处理时间
        try await Task.sleep(nanoseconds: 1_000_000) // 1ms
        return PatternResult(
            output: "mock output",
            metadata: nil,
            duration: 0.001,
            success: true
        )
    }

    func validate(input: PatternInput) -> Bool {
        return !input.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
}
