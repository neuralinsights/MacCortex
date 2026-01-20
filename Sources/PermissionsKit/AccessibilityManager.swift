// MacCortex PermissionsKit - Accessibility 权限管理
// Phase 1 - Week 1 Day 1-2
// 创建时间: 2026-01-20
//
// 基于 macOS Accessibility API
// 参考: https://developer.apple.com/documentation/applicationservices/1459186-axisprocesstrusted

import Foundation
import AppKit
import ApplicationServices

/// Accessibility 权限管理器
///
/// 提供简单的 API 来检测和请求 Accessibility 权限。
/// 支持轮询检测、系统设置跳转和用户引导。
public class AccessibilityManager {

    // MARK: - Singleton

    /// 共享实例
    public static let shared = AccessibilityManager()

    private init() {}

    // MARK: - Public Properties

    /// 是否已授予 Accessibility 权限
    ///
    /// 注意：在 macOS 10.9+ 上，首次调用会自动将应用添加到
    /// 系统设置的 Accessibility 列表（未勾选状态）
    public var hasAccessibilityPermission: Bool {
        return checkAccessibilityPermission()
    }

    // MARK: - Private Properties

    /// 轮询计时器
    private var pollingTimer: Timer?

    /// 轮询回调
    private var pollingCompletion: ((Bool) -> Void)?

    // MARK: - Public Methods

    /// 请求 Accessibility 权限
    ///
    /// 此方法会：
    /// 1. 检查当前权限状态
    /// 2. 如果未授权，触发系统权限请求对话框（首次）
    /// 3. 打开系统设置（非首次）
    /// 4. 启动轮询检测权限变化
    /// 5. 授权成功或超时后调用回调
    ///
    /// - Parameters:
    ///   - timeout: 轮询超时时间（秒），默认 60 秒
    ///   - interval: 轮询间隔（秒），默认 2 秒
    ///   - completion: 完成回调，参数为是否授权成功
    public func requestAccessibilityPermission(
        timeout: TimeInterval = 60.0,
        interval: TimeInterval = 2.0,
        completion: @escaping (Bool) -> Void
    ) {
        // 检查是否已经授权
        if hasAccessibilityPermission {
            completion(true)
            return
        }

        // 触发权限请求对话框（首次调用时会显示系统对话框）
        triggerPermissionRequest()

        // 打开系统设置（对于非首次或用户拒绝后的情况）
        openSystemPreferences()

        // 启动轮询
        startPolling(timeout: timeout, interval: interval, completion: completion)
    }

    /// 触发系统权限请求对话框
    ///
    /// 首次调用 AXIsProcessTrustedWithOptions 会显示系统对话框，
    /// 询问用户是否允许该应用控制电脑
    public func triggerPermissionRequest() {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true] as CFDictionary
        AXIsProcessTrustedWithOptions(options)
    }

    /// 打开系统设置的 Accessibility 页面
    ///
    /// 支持 macOS 13+ (Ventura) 和更早版本的不同 URL scheme
    public func openSystemPreferences() {
        // macOS 13+ (Ventura) 使用新的 URL scheme
        if #available(macOS 13.0, *) {
            if let url = URL(string: "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility") {
                NSWorkspace.shared.open(url)
                return
            }
        }

        // macOS 12 及以下
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility") {
            NSWorkspace.shared.open(url)
        }
    }

    /// 停止权限轮询
    public func stopPolling() {
        pollingTimer?.invalidate()
        pollingTimer = nil
        pollingCompletion = nil
    }

    // MARK: - Private Methods

    /// 检查 Accessibility 权限
    ///
    /// 使用 AXIsProcessTrusted() 检测权限状态
    ///
    /// - Returns: 是否已授予权限
    private func checkAccessibilityPermission() -> Bool {
        // 使用不带提示的版本，避免重复弹窗
        return AXIsProcessTrusted()
    }

    /// 启动权限轮询
    ///
    /// 定期检查权限状态，直到授权成功或超时
    ///
    /// - Parameters:
    ///   - timeout: 超时时间（秒）
    ///   - interval: 检查间隔（秒）
    ///   - completion: 完成回调
    private func startPolling(
        timeout: TimeInterval,
        interval: TimeInterval,
        completion: @escaping (Bool) -> Void
    ) {
        // 保存回调
        pollingCompletion = completion

        // 记录开始时间
        let startTime = Date()

        // 创建计时器
        pollingTimer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] timer in
            guard let self = self else {
                timer.invalidate()
                return
            }

            // 检查是否已授权
            if self.hasAccessibilityPermission {
                timer.invalidate()
                self.pollingTimer = nil

                DispatchQueue.main.async {
                    completion(true)
                }
                return
            }

            // 检查是否超时
            if Date().timeIntervalSince(startTime) >= timeout {
                timer.invalidate()
                self.pollingTimer = nil

                DispatchQueue.main.async {
                    completion(false)
                }
                return
            }
        }

        // 立即执行一次检查
        pollingTimer?.fire()
    }
}

// MARK: - Extension: 用户通知

extension AccessibilityManager {

    /// 显示权限请求通知
    ///
    /// 在主线程显示一个原生提示，引导用户授权
    ///
    /// - Parameters:
    ///   - title: 通知标题
    ///   - message: 通知内容
    ///   - completion: 用户点击回调
    public func showPermissionAlert(
        title: String = "需要 Accessibility 权限",
        message: String = "MacCortex 需要 Accessibility 权限来自动化您的工作流程，控制其他应用完成任务。\n\n请在系统设置中授予权限。",
        completion: @escaping () -> Void
    ) {
        DispatchQueue.main.async {
            let alert = NSAlert()
            alert.messageText = title
            alert.informativeText = message
            alert.alertStyle = .informational
            alert.addButton(withTitle: "打开系统设置")
            alert.addButton(withTitle: "稍后")

            let response = alert.runModal()
            if response == .alertFirstButtonReturn {
                completion()
            }
        }
    }
}

// MARK: - Extension: 调试工具

#if DEBUG
extension AccessibilityManager {

    /// 打印权限状态（调试用）
    public func printStatus() {
        print("=== Accessibility Permission Status ===")
        print("Granted: \(hasAccessibilityPermission)")
        print("Process Trusted: \(AXIsProcessTrusted())")
        print("========================================")
    }
}
#endif
