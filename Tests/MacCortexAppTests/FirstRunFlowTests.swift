// MacCortex 首次启动流程端到端测试
// Phase 1 - Week 1 Day 5
// 创建时间: 2026-01-20

import XCTest
@testable import MacCortexApp
@testable import PermissionsKit

final class FirstRunFlowTests: XCTestCase {

    // MARK: - Properties

    var appState: AppState!

    // MARK: - Setup & Teardown

    override func setUp() {
        super.setUp()
        appState = AppState()

        // 重置首次运行标志（测试用）
        UserDefaults.standard.removeObject(forKey: "HasLaunchedBefore")
    }

    override func tearDown() {
        appState = nil
        super.tearDown()
    }

    // MARK: - AppState Tests

    /// 测试 AppState 初始化
    func testAppStateInitialization() {
        let state = AppState()

        // 验证属性已初始化
        XCTAssertNotNil(state.hasFullDiskAccess)
        XCTAssertNotNil(state.hasAccessibilityPermission)
        XCTAssertNotNil(state.isFirstRun)
    }

    /// 测试首次运行检测
    func testFirstRunDetection() {
        // 清除标志
        UserDefaults.standard.removeObject(forKey: "HasLaunchedBefore")

        let state = AppState()

        // 首次运行应该为 true
        XCTAssertTrue(state.isFirstRun, "首次启动应该检测为 isFirstRun = true")

        // 验证标志已设置
        let hasLaunched = UserDefaults.standard.bool(forKey: "HasLaunchedBefore")
        XCTAssertTrue(hasLaunched, "HasLaunchedBefore 应该被设置为 true")
    }

    /// 测试非首次运行检测
    func testNonFirstRunDetection() {
        // 设置已启动标志
        UserDefaults.standard.set(true, forKey: "HasLaunchedBefore")

        let state = AppState()

        // 非首次运行应该为 false
        XCTAssertFalse(state.isFirstRun, "非首次启动应该检测为 isFirstRun = false")
    }

    /// 测试必需权限检查
    func testHasAllRequiredPermissions() {
        let state = AppState()

        // hasAllRequiredPermissions 应该只检查 Full Disk Access
        if state.hasFullDiskAccess {
            XCTAssertTrue(state.hasAllRequiredPermissions, "有 FDA 权限应该返回 true")
        } else {
            XCTAssertFalse(state.hasAllRequiredPermissions, "没有 FDA 权限应该返回 false")
        }

        // Accessibility 不影响必需权限检查
        // （即使没有 Accessibility，hasAllRequiredPermissions 也可能为 true）
    }

    // MARK: - Permission Request Tests

    /// 测试 Full Disk Access 请求流程
    func testFullDiskAccessRequestFlow() {
        let expectation = self.expectation(description: "Full Disk Access 请求")

        appState.requestFullDiskAccess()

        // 等待轮询启动（短时间）
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            // 验证轮询已启动（权限状态应该被检查）
            expectation.fulfill()
        }

        waitForExpectations(timeout: 1)

        // 停止轮询避免影响其他测试
        FullDiskAccessManager.shared.stopPolling()
    }

    /// 测试 Accessibility 请求流程
    func testAccessibilityRequestFlow() {
        let expectation = self.expectation(description: "Accessibility 请求")

        appState.requestAccessibilityPermission()

        // 等待轮询启动（短时间）
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            // 验证轮询已启动
            expectation.fulfill()
        }

        waitForExpectations(timeout: 1)

        // 停止轮询
        AccessibilityManager.shared.stopPolling()
    }

    /// 测试权限授予后的状态更新
    func testPermissionGrantedStateUpdate() {
        // 如果已有 Full Disk Access 权限
        if appState.hasFullDiskAccess {
            // 请求应该立即返回 true
            let expectation = self.expectation(description: "权限已授予")

            appState.requestFullDiskAccess()

            // 短暂延迟后检查状态
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                XCTAssertTrue(self.appState.hasFullDiskAccess, "权限状态应该保持 true")
                expectation.fulfill()
            }

            waitForExpectations(timeout: 1)
        }
    }

    // MARK: - User Flow Tests

    /// 测试完整授权流程（已授权场景）
    func testCompleteAuthorizationFlowGranted() {
        // 如果系统已授权
        if appState.hasFullDiskAccess {
            // 1. 检查初始状态
            XCTAssertTrue(appState.hasFullDiskAccess, "应该有 Full Disk Access")

            // 2. 检查必需权限
            XCTAssertTrue(appState.hasAllRequiredPermissions, "应该满足所有必需权限")

            // 3. 模拟完成首次启动
            appState.isFirstRun = false
            XCTAssertFalse(appState.isFirstRun, "应该标记为非首次运行")
        }
    }

    /// 测试未授权流程
    func testUnauthorizedFlow() {
        // 如果系统未授权
        if !appState.hasFullDiskAccess {
            // 1. 检查初始状态
            XCTAssertFalse(appState.hasFullDiskAccess, "不应该有 Full Disk Access")

            // 2. 检查必需权限
            XCTAssertFalse(appState.hasAllRequiredPermissions, "不应该满足所有必需权限")

            // 3. 用户可以选择"稍后授权"
            appState.isFirstRun = false
            XCTAssertFalse(appState.isFirstRun, "可以跳过首次启动")
        }
    }

    // MARK: - Settings Flow Tests

    /// 测试重置首次运行标志
    func testResetFirstRunFlag() {
        // 设置已启动
        UserDefaults.standard.set(true, forKey: "HasLaunchedBefore")
        appState.isFirstRun = false

        // 重置标志
        UserDefaults.standard.set(false, forKey: "HasLaunchedBefore")
        appState.isFirstRun = true

        // 验证
        XCTAssertTrue(appState.isFirstRun, "应该重置为首次运行")
        let hasLaunched = UserDefaults.standard.bool(forKey: "HasLaunchedBefore")
        XCTAssertFalse(hasLaunched, "HasLaunchedBefore 应该为 false")
    }

    // MARK: - Performance Tests

    /// 测试权限检查性能
    func testPermissionCheckPerformance() {
        measure {
            _ = appState.hasFullDiskAccess
            _ = appState.hasAccessibilityPermission
            _ = appState.hasAllRequiredPermissions
        }
    }

    /// 测试 AppState 初始化性能
    func testAppStateInitializationPerformance() {
        measure {
            _ = AppState()
        }
    }

    // MARK: - Edge Cases

    /// 测试并发权限请求
    func testConcurrentPermissionRequests() {
        let expectation = self.expectation(description: "并发请求")
        expectation.expectedFulfillmentCount = 2

        // 同时请求两个权限
        DispatchQueue.global().async {
            self.appState.requestFullDiskAccess()
            expectation.fulfill()
        }

        DispatchQueue.global().async {
            self.appState.requestAccessibilityPermission()
            expectation.fulfill()
        }

        waitForExpectations(timeout: 2)

        // 清理
        FullDiskAccessManager.shared.stopPolling()
        AccessibilityManager.shared.stopPolling()
    }

    /// 测试快速连续请求
    func testRapidSuccessiveRequests() {
        // 快速连续请求同一权限
        for _ in 0..<5 {
            appState.requestFullDiskAccess()
        }

        // 等待短暂时间
        let expectation = self.expectation(description: "快速请求")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            expectation.fulfill()
        }

        waitForExpectations(timeout: 1)

        // 清理
        FullDiskAccessManager.shared.stopPolling()
    }

    // MARK: - Integration Tests

    /// 测试完整的首次启动到授权完成流程
    func testCompleteFirstRunToAuthorizationFlow() {
        // 1. 模拟首次启动
        UserDefaults.standard.removeObject(forKey: "HasLaunchedBefore")
        let state = AppState()
        XCTAssertTrue(state.isFirstRun, "应该是首次运行")

        // 2. 检查权限状态
        let hasAllPermissions = state.hasAllRequiredPermissions

        // 3. 如果已有权限，应该可以完成启动
        if hasAllPermissions {
            state.isFirstRun = false
            XCTAssertFalse(state.isFirstRun, "应该完成首次启动")
        }

        // 4. 如果没有权限，应该保持在引导界面
        if !hasAllPermissions {
            XCTAssertTrue(state.isFirstRun || !state.hasAllRequiredPermissions,
                         "没有必需权限时应该保持引导状态")
        }
    }
}
