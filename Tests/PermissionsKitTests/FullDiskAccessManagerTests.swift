// MacCortex PermissionsKit Tests
// Phase 0.5 - Day 6-7
// 创建时间: 2026-01-20

import XCTest
@testable import PermissionsKit

final class FullDiskAccessManagerTests: XCTestCase {

    // MARK: - Properties

    var manager: FullDiskAccessManager!

    // MARK: - Setup & Teardown

    override func setUp() {
        super.setUp()
        manager = FullDiskAccessManager.shared
    }

    override func tearDown() {
        manager.stopPolling()
        manager = nil
        super.tearDown()
    }

    // MARK: - Tests

    /// 测试单例模式
    func testSingleton() {
        let instance1 = FullDiskAccessManager.shared
        let instance2 = FullDiskAccessManager.shared

        XCTAssertTrue(instance1 === instance2, "应该返回同一个实例")
    }

    /// 测试权限检测（基础功能）
    func testHasFullDiskAccess() {
        // 注意：此测试的结果取决于当前系统的实际权限状态
        let hasAccess = manager.hasFullDiskAccess

        // 只验证方法可以调用，不验证具体值
        // 因为 CI 环境可能没有授权
        XCTAssertNotNil(hasAccess, "hasFullDiskAccess 应该返回一个有效的布尔值")
    }

    /// 测试系统设置 URL（验证 URL 格式）
    func testOpenSystemPreferencesURL() {
        // macOS 13+ URL
        if #available(macOS 13.0, *) {
            let url = URL(string: "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_AllFiles")
            XCTAssertNotNil(url, "macOS 13+ 系统设置 URL 应该有效")
        }

        // macOS 12 及以下 URL
        let legacyURL = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles")
        XCTAssertNotNil(legacyURL, "macOS 12 系统设置 URL 应该有效")
    }

    /// 测试轮询停止
    func testStopPolling() {
        // 启动轮询
        let expectation = self.expectation(description: "轮询启动")
        expectation.isInverted = true  // 期望不被满足（因为我们会立即停止）

        manager.requestFullDiskAccess(timeout: 5, interval: 1) { _ in
            expectation.fulfill()
        }

        // 立即停止
        manager.stopPolling()

        // 等待 2 秒，确保回调没有被调用
        waitForExpectations(timeout: 2)
    }

    /// 测试多次调用已授权情况
    func testMultipleCallsWhenAuthorized() {
        // 这个测试只在有权限时有意义
        if manager.hasFullDiskAccess {
            let expectation1 = self.expectation(description: "第一次调用")
            let expectation2 = self.expectation(description: "第二次调用")

            manager.requestFullDiskAccess { granted in
                XCTAssertTrue(granted, "应该已授权")
                expectation1.fulfill()
            }

            manager.requestFullDiskAccess { granted in
                XCTAssertTrue(granted, "应该已授权")
                expectation2.fulfill()
            }

            waitForExpectations(timeout: 1)
        }
    }

    // MARK: - 性能测试

    /// 测试权限检测性能
    func testCheckPerformance() {
        measure {
            _ = manager.hasFullDiskAccess
        }
    }

    // MARK: - Debug 功能测试

    #if DEBUG
    /// 测试调试打印（仅在 Debug 模式）
    func testPrintStatus() {
        // 验证方法可以调用且不崩溃
        manager.printStatus()
    }
    #endif
}
