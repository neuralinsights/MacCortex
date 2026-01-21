//
//  ClipboardMonitor.swift
//  MacCortex
//
//  Phase 3 Week 3 Day 3 - 剪贴板监听服务
//  Created on 2026-01-22
//

import Foundation
import AppKit
import Combine

/// 剪贴板监听服务
///
/// 自动检测剪贴板内容变化，触发翻译操作
/// 支持：
/// - 定时轮询（0.5 秒）
/// - 文本变化检测（去重）
/// - 最小长度过滤（≥3 字符）
/// - 启用/禁用开关
@MainActor
class ClipboardMonitor: ObservableObject {
    // MARK: - Published Properties

    /// 是否启用剪贴板监听
    @Published var isEnabled: Bool = false {
        didSet {
            if isEnabled {
                startMonitoring()
            } else {
                stopMonitoring()
            }
        }
    }

    /// 最小触发长度（字符数）
    @Published var minimumLength: Int = 3

    /// 最近检测到的文本
    @Published var lastDetectedText: String = ""

    // MARK: - Private Properties

    /// 定时器
    private var timer: Timer?

    /// 上次剪贴板变化计数（NSPasteboard.changeCount）
    private var lastChangeCount: Int = 0

    /// 上次处理的文本（用于去重）
    private var lastProcessedText: String = ""

    /// 剪贴板变化回调
    var onClipboardChange: ((String) -> Void)?

    // MARK: - Initialization

    init() {
        // Phase 3 Week 3 后续: 从 SettingsManager 加载配置
        let settings = SettingsManager.shared
        self.minimumLength = settings.clipboardMinimumLength

        // 初始化时不自动启动，需要用户明确启用
        lastChangeCount = NSPasteboard.general.changeCount
    }

    // MARK: - Public Methods

    /// 开始监听剪贴板
    func startMonitoring() {
        guard timer == nil else { return }

        // 记录当前状态
        lastChangeCount = NSPasteboard.general.changeCount
        lastProcessedText = NSPasteboard.general.string(forType: .string) ?? ""

        // Phase 3 Week 3 后续: 从 SettingsManager 读取轮询间隔
        let pollingInterval = SettingsManager.shared.clipboardPollingInterval

        // 创建定时器（使用设置的轮询间隔）
        timer = Timer.scheduledTimer(withTimeInterval: pollingInterval, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.checkClipboard()
            }
        }

        print("[ClipboardMonitor] 开始监听剪贴板（轮询间隔: \(pollingInterval)s）")
    }

    /// 停止监听剪贴板
    func stopMonitoring() {
        timer?.invalidate()
        timer = nil

        print("[ClipboardMonitor] 停止监听剪贴板")
    }

    // MARK: - Private Methods

    /// 检查剪贴板变化
    private func checkClipboard() {
        let pasteboard = NSPasteboard.general
        let currentChangeCount = pasteboard.changeCount

        // 1. 检查是否有变化
        guard currentChangeCount != lastChangeCount else {
            return
        }

        lastChangeCount = currentChangeCount

        // 2. 读取文本内容
        guard let text = pasteboard.string(forType: .string) else {
            return
        }

        // 3. 过滤条件
        guard shouldProcessText(text) else {
            return
        }

        // 4. 触发回调
        lastProcessedText = text
        lastDetectedText = text

        print("[ClipboardMonitor] 检测到新文本: \(text.prefix(50))...")

        onClipboardChange?(text)
    }

    /// 判断是否应该处理该文本
    private func shouldProcessText(_ text: String) -> Bool {
        // Phase 3 Week 3 后续: 使用 SettingsManager 配置
        let settings = SettingsManager.shared

        // 1. 长度检查
        let trimmedText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmedText.count >= settings.clipboardMinimumLength else {
            return false
        }

        // 2. 去重检查（与上次处理的文本相同）
        guard trimmedText != lastProcessedText else {
            return false
        }

        // 3. 排除 URL（如果启用）
        if settings.clipboardExcludeURLs {
            if trimmedText.hasPrefix("http://") || trimmedText.hasPrefix("https://") {
                return false
            }
        }

        // 4. 排除纯数字（如果启用）
        if settings.clipboardExcludeNumbers {
            if trimmedText.allSatisfy({ $0.isNumber }) {
                return false
            }
        }

        // 5. 排除代码片段（如果启用）
        if settings.clipboardExcludeCode {
            // 简单判断：如果包含大量符号（如 { } ; ( ) [ ]），认为是代码
            let symbolCount = trimmedText.filter { "{}();[]<>=+-*/&|!@#$%^".contains($0) }.count
            if Double(symbolCount) / Double(trimmedText.count) > 0.2 {
                return false
            }
        }

        // 6. 最大长度限制
        if trimmedText.count > settings.clipboardMaxLength {
            return false
        }

        return true
    }

    // MARK: - Cleanup

    deinit {
        stopMonitoring()
    }
}
