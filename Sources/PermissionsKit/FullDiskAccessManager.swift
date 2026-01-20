//
// MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
// Copyright (c) 2026 Yu Geng. All rights reserved.
//
// This source code is proprietary and confidential.
// Unauthorized copying, distribution, or use is strictly prohibited.
//
// Author: Yu Geng <james.geng@gmail.com>
// License: Proprietary
//

// MacCortex PermissionsKit - Full Disk Access 管理
// Phase 0.5 - Day 6-7
// 创建时间: 2026-01-20
//
// 基于 inket/FullDiskAccess 设计理念
// 参考: https://github.com/inket/FullDiskAccess

import Foundation
import AppKit

/// Full Disk Access 权限管理器
///
/// 提供简单的 API 来检测和请求 Full Disk Access 权限。
/// 支持轮询检测、系统设置跳转和用户引导。
public class FullDiskAccessManager {

    // MARK: - Singleton

    /// 共享实例
    public static let shared = FullDiskAccessManager()

    private init() {}

    // MARK: - Public Properties

    /// 是否已授予 Full Disk Access 权限
    ///
    /// 注意：在 macOS 10.15+ 上，首次调用会自动将应用添加到
    /// 系统设置的 Full Disk Access 列表（未勾选状态）
    public var hasFullDiskAccess: Bool {
        return checkFullDiskAccess()
    }

    // MARK: - Private Properties

    /// 轮询计时器
    private var pollingTimer: Timer?

    /// 轮询回调
    private var pollingCompletion: ((Bool) -> Void)?

    // MARK: - Public Methods

    /// 请求 Full Disk Access 权限
    ///
    /// 此方法会：
    /// 1. 检查当前权限状态
    /// 2. 如果未授权，打开系统设置
    /// 3. 启动轮询检测权限变化
    /// 4. 授权成功或超时后调用回调
    ///
    /// - Parameters:
    ///   - timeout: 轮询超时时间（秒），默认 60 秒
    ///   - interval: 轮询间隔（秒），默认 2 秒
    ///   - completion: 完成回调，参数为是否授权成功
    public func requestFullDiskAccess(
        timeout: TimeInterval = 60.0,
        interval: TimeInterval = 2.0,
        completion: @escaping (Bool) -> Void
    ) {
        // 检查是否已经授权
        if hasFullDiskAccess {
            completion(true)
            return
        }

        // 打开系统设置
        openSystemPreferences()

        // 启动轮询
        startPolling(timeout: timeout, interval: interval, completion: completion)
    }

    /// 打开系统设置的 Full Disk Access 页面
    ///
    /// 支持 macOS 13+ (Ventura) 和更早版本的不同 URL scheme
    public func openSystemPreferences() {
        // macOS 13+ (Ventura) 使用新的 URL scheme
        if #available(macOS 13.0, *) {
            if let url = URL(string: "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_AllFiles") {
                NSWorkspace.shared.open(url)
                return
            }
        }

        // macOS 12 及以下
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles") {
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

    /// 检查 Full Disk Access 权限
    ///
    /// 使用多种方法检测权限状态：
    /// 1. 尝试访问用户的 TCC.db 文件
    /// 2. 备用方法：检查 TimeMachine plist
    ///
    /// - Returns: 是否已授予权限
    private func checkFullDiskAccess() -> Bool {
        // 方法 1: 尝试访问 TCC.db
        // 这是最可靠的方法，因为 TCC.db 需要 Full Disk Access
        let tccPath = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/com.apple.TCC/TCC.db")

        // 检查文件是否可读
        if FileManager.default.isReadableFile(atPath: tccPath.path) {
            // 尝试实际读取文件来确认
            if let _ = try? Data(contentsOf: tccPath) {
                return true
            }
        }

        // 方法 2: 备用检测 - TimeMachine plist
        // 某些系统配置下，TCC.db 检测可能不准确
        let tmPath = "/Library/Preferences/com.apple.TimeMachine.plist"
        if FileManager.default.fileExists(atPath: tmPath) {
            if let _ = NSDictionary(contentsOfFile: tmPath) {
                return true
            }
        }

        return false
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
            if self.hasFullDiskAccess {
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

extension FullDiskAccessManager {

    /// 显示权限请求通知
    ///
    /// 在主线程显示一个原生提示，引导用户授权
    ///
    /// - Parameters:
    ///   - title: 通知标题
    ///   - message: 通知内容
    ///   - completion: 用户点击回调
    public func showPermissionAlert(
        title: String = "需要 Full Disk Access 权限",
        message: String = "MacCortex 需要 Full Disk Access 权限来读取和组织您的文件、笔记和文档。\n\n请在系统设置中授予权限。",
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
extension FullDiskAccessManager {

    /// 打印权限状态（调试用）
    public func printStatus() {
        print("=== Full Disk Access Status ===")
        print("Granted: \(hasFullDiskAccess)")

        // 检查 TCC.db 路径
        let tccPath = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/com.apple.TCC/TCC.db")
        print("TCC.db Path: \(tccPath.path)")
        print("TCC.db Exists: \(FileManager.default.fileExists(atPath: tccPath.path))")
        print("TCC.db Readable: \(FileManager.default.isReadableFile(atPath: tccPath.path))")

        // 检查 TimeMachine plist
        let tmPath = "/Library/Preferences/com.apple.TimeMachine.plist"
        print("TimeMachine plist Exists: \(FileManager.default.fileExists(atPath: tmPath))")
        print("===============================")
    }
}
#endif
