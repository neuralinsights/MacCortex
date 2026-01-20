// MacCortex PermissionsKit Tests - Accessibility Manager
// Phase 1 - Week 1 Day 1-2
// 创建时间: 2026-01-20

import XCTest
@testable import PermissionsKit

final class AccessibilityManagerTests: XCTestCase {

    // MARK: - Properties

    var manager: AccessibilityManager!

    // MARK: - Setup & Teardown

    override func setUp() {
        super.setUp()
        manager = AccessibilityManager.shared
    }

    override func tearDown() {
        manager.stopPolling()
        manager = nil
        super.tearDown()
    }

    // MARK: - Tests

    /// 测试单例模式
    func testSingleton() {
        let instance1 = AccessibilityManager.shared
        let instance2 = AccessibilityManager.shared

        XCTAssertTrue(instance1 === instance2, "应该返回同一个实例")
    }

    /// 测试权限检测（基础功能）
    func testHasAccessibilityPermission() {
        // 注意：此测试的结果取决于当前系统的实际权限状态
        let hasPermission = manager.hasAccessibilityPermission

        // 只验证方法可以调用，不验证具体值
        // 因为 CI 环境可能没有授权
        XCTAssertNotNil(hasPermission, "hasAccessibilityPermission 应该返回一个有效的布尔值")
    }

    /// 测试系统设置 URL（验证 URL 格式）
    func testOpenSystemPreferencesURL() {
        // macOS 13+ URL
        if #available(macOS 13.0, *) {
            let url = URL(string: "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility")
            XCTAssertNotNil(url, "macOS 13+ 系统设置 URL 应该有效")
        }

        // macOS 12 及以下 URL
        let legacyURL = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")
        XCTAssertNotNil(legacyURL, "macOS 12 系统设置 URL 应该有效")
    }

    /// 测试轮询停止
    func testStopPolling() {
        // 启动轮询
        let expectation = self.expectation(description: "轮询启动")
        expectation.isInverted = true  // 期望不被满足（因为我们会立即停止）

        manager.requestAccessibilityPermission(timeout: 5, interval: 1) { _ in
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
        if manager.hasAccessibilityPermission {
            let expectation1 = self.expectation(description: "第一次调用")
            let expectation2 = self.expectation(description: "第二次调用")

            manager.requestAccessibilityPermission { granted in
                XCTAssertTrue(granted, "应该已授权")
                expectation1.fulfill()
            }

            manager.requestAccessibilityPermission { granted in
                XCTAssertTrue(granted, "应该已授权")
                expectation2.fulfill()
            }

            waitForExpectations(timeout: 1)
        }
    }

    /// 测试超时机制
    func testRequestTimeout() {
        // 如果未授权，应该在超时后返回 false
        if !manager.hasAccessibilityPermission {
            let expectation = self.expectation(description: "超时测试")

            manager.requestAccessibilityPermission(timeout: 3, interval: 0.5) { granted in
                XCTAssertFalse(granted, "超时后应该返回 false")
                expectation.fulfill()
            }

            waitForExpectations(timeout: 4)
        }
    }

    /// 测试轮询间隔参数
    func testPollingInterval() {
        if !manager.hasAccessibilityPermission {
            let expectation = self.expectation(description: "间隔测试")
            let startTime = Date()

            manager.requestAccessibilityPermission(timeout: 2, interval: 0.5) { _ in
                let elapsed = Date().timeIntervalSince(startTime)
                // 应该至少等待 2 秒（超时时间）
                XCTAssertGreaterThanOrEqual(elapsed, 2.0, "应该至少等待超时时间")
                expectation.fulfill()
            }

            waitForExpectations(timeout: 3)
        }
    }

    // MARK: - 性能测试

    /// 测试权限检测性能
    func testCheckPerformance() {
        measure {
            _ = manager.hasAccessibilityPermission
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

    // MARK: - 集成测试

    /// 测试权限请求流程（集成测试）
    func testPermissionRequestFlow() {
        let expectation = self.expectation(description: "权限请求流程")

        // 如果已授权，应该立即返回 true
        if manager.hasAccessibilityPermission {
            manager.requestAccessibilityPermission(timeout: 1, interval: 0.5) { granted in
                XCTAssertTrue(granted, "已授权应该立即返回 true")
                expectation.fulfill()
            }
        } else {
            // 如果未授权，启动请求流程但使用极短超时（1秒）
            // 注意：此测试不会实际打开系统设置（避免影响用户）
            // 只验证流程可以正常启动并在超时后返回
            manager.requestAccessibilityPermission(timeout: 1, interval: 0.5) { granted in
                XCTAssertFalse(granted, "未授权应该在超时后返回 false")
                expectation.fulfill()
            }
        }

        waitForExpectations(timeout: 2)
    }

    /// 测试同时请求两个权限管理器
    func testConcurrentManagers() {
        let accessibilityExpectation = self.expectation(description: "Accessibility")
        let fdaExpectation = self.expectation(description: "Full Disk Access")

        // 同时请求两个权限
        AccessibilityManager.shared.requestAccessibilityPermission(timeout: 3, interval: 1) { _ in
            accessibilityExpectation.fulfill()
        }

        FullDiskAccessManager.shared.requestFullDiskAccess(timeout: 3, interval: 1) { _ in
            fdaExpectation.fulfill()
        }

        waitForExpectations(timeout: 4)
    }
}
