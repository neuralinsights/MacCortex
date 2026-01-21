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

// MacCortex 场景检测服务
// Phase 2 Day 4-5: 智能场景识别
// 创建时间：2026-01-21

import SwiftUI
import AppKit
import ApplicationServices

/// 场景检测服务（单例）
@Observable
class SceneDetector {
    // MARK: - 单例
    static let shared = SceneDetector()

    // MARK: - 状态
    var currentScene: DetectedScene = .unknown
    var sceneConfidence: Double = 0.0
    var activeApplicationName: String = ""
    var activeWindowTitle: String = ""
    var isDetecting: Bool = false

    // MARK: - 私有属性
    private var detectionTimer: Timer?
    private let detectionInterval: TimeInterval = 2.0  // 每 2 秒检测一次

    private init() {}

    // MARK: - 公共方法

    /// 开始场景检测
    func startDetection() {
        guard !isDetecting else { return }

        isDetecting = true
        detectScene()  // 立即执行一次

        // 启动定时检测
        detectionTimer = Timer.scheduledTimer(withTimeInterval: detectionInterval, repeats: true) { [weak self] _ in
            self?.detectScene()
        }
    }

    /// 停止场景检测
    func stopDetection() {
        isDetecting = false
        detectionTimer?.invalidate()
        detectionTimer = nil
    }

    /// 手动触发场景检测
    func detectScene() {
        // 1. 获取活动应用程序
        guard let activeApp = NSWorkspace.shared.frontmostApplication else {
            Task { @MainActor in
                updateScene(.unknown, confidence: 0.0)
            }
            return
        }

        let appName = activeApp.localizedName ?? ""
        let windowTitle = getActiveWindowTitle() ?? ""

        // 2. 分析场景（后台线程）
        let (scene, confidence) = analyzeScene(
            appName: appName,
            windowTitle: windowTitle
        )

        // 3. 更新场景（主线程）
        Task { @MainActor in
            self.activeApplicationName = appName
            self.activeWindowTitle = windowTitle
            self.updateScene(scene, confidence: confidence)
        }
    }

    // MARK: - 私有方法

    /// 获取活动窗口标题（Accessibility API）
    private func getActiveWindowTitle() -> String? {
        // 检查 Accessibility 权限
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: false]
        guard AXIsProcessTrustedWithOptions(options as CFDictionary) else {
            return nil
        }

        // 获取系统级 Accessibility Element
        let systemWide = AXUIElementCreateSystemWide()

        // 获取聚焦应用
        var focusedApp: AnyObject?
        let appResult = AXUIElementCopyAttributeValue(
            systemWide,
            kAXFocusedApplicationAttribute as CFString,
            &focusedApp
        )

        guard appResult == .success, let app = focusedApp else {
            return nil
        }

        // 获取聚焦窗口
        var focusedWindow: AnyObject?
        let windowResult = AXUIElementCopyAttributeValue(
            app as! AXUIElement,
            kAXFocusedWindowAttribute as CFString,
            &focusedWindow
        )

        guard windowResult == .success, let window = focusedWindow else {
            return nil
        }

        // 获取窗口标题
        var title: AnyObject?
        let titleResult = AXUIElementCopyAttributeValue(
            window as! AXUIElement,
            kAXTitleAttribute as CFString,
            &title
        )

        guard titleResult == .success, let windowTitle = title as? String else {
            return nil
        }

        return windowTitle
    }

    /// 分析场景（基于应用和窗口标题）
    private func analyzeScene(appName: String, windowTitle: String) -> (DetectedScene, Double) {
        let appLower = appName.lowercased()
        let titleLower = windowTitle.lowercased()

        // 场景匹配规则（按优先级）

        // 1. 视频会议（高置信度）
        if isVideoConferencingApp(appLower) {
            return (.meeting, 0.95)
        }

        // 2. 代码编写（高置信度）
        if isCodingApp(appLower) || isCodingTitle(titleLower) {
            let confidence = isCodingApp(appLower) ? 0.90 : 0.80
            return (.coding, confidence)
        }

        // 3. 文档编写（中等置信度）
        if isWritingApp(appLower) || isWritingTitle(titleLower) {
            let confidence = isWritingApp(appLower) ? 0.85 : 0.75
            return (.writing, confidence)
        }

        // 4. 网页浏览（中等置信度）
        if isBrowsingApp(appLower) {
            return (.browsing, 0.80)
        }

        // 5. 阅读文档（中等置信度）
        if isReadingApp(appLower) || isReadingTitle(titleLower) {
            let confidence = isReadingApp(appLower) ? 0.80 : 0.70
            return (.reading, confidence)
        }

        // 默认：未知场景
        return (.unknown, 0.5)
    }

    /// 更新场景（主线程）
    @MainActor
    private func updateScene(_ scene: DetectedScene, confidence: Double) {
        self.currentScene = scene
        self.sceneConfidence = confidence
    }

    // MARK: - 应用类型判断

    /// 视频会议应用
    private func isVideoConferencingApp(_ appName: String) -> Bool {
        let conferenceApps = [
            "zoom", "teams", "microsoft teams", "skype", "webex",
            "google meet", "facetime", "slack", "discord"
        ]
        return conferenceApps.contains { appName.contains($0) }
    }

    /// 代码编写应用
    private func isCodingApp(_ appName: String) -> Bool {
        let codingApps = [
            "xcode", "visual studio code", "vscode", "sublime",
            "atom", "intellij", "pycharm", "webstorm", "vim",
            "terminal", "iterm", "warp", "cursor", "zed"
        ]
        return codingApps.contains { appName.contains($0) }
    }

    /// 代码相关窗口标题
    private func isCodingTitle(_ title: String) -> Bool {
        let codingKeywords = [
            ".swift", ".py", ".js", ".ts", ".go", ".rs", ".java",
            ".cpp", ".c", ".h", ".m", ".mm", ".kt", ".rb",
            "github", "gitlab", "bitbucket", "stack overflow"
        ]
        return codingKeywords.contains { title.contains($0) }
    }

    /// 文档编写应用
    private func isWritingApp(_ appName: String) -> Bool {
        let writingApps = [
            "pages", "word", "microsoft word", "google docs",
            "notion", "bear", "ulysses", "ia writer", "typora",
            "obsidian", "roam", "logseq", "notes", "drafts"
        ]
        return writingApps.contains { appName.contains($0) }
    }

    /// 写作相关窗口标题
    private func isWritingTitle(_ title: String) -> Bool {
        let writingKeywords = [
            "document", "文档", "draft", "草稿", "writing", "写作",
            "article", "文章", "blog", "博客", "note", "笔记"
        ]
        return writingKeywords.contains { title.contains($0) }
    }

    /// 网页浏览应用
    private func isBrowsingApp(_ appName: String) -> Bool {
        let browsers = [
            "safari", "chrome", "firefox", "edge", "opera",
            "brave", "arc", "vivaldi"
        ]
        return browsers.contains { appName.contains($0) }
    }

    /// 阅读应用
    private func isReadingApp(_ appName: String) -> Bool {
        let readingApps = [
            "preview", "adobe acrobat", "pdf expert", "books",
            "kindle", "reeder", "readkit", "pocket"
        ]
        return readingApps.contains { appName.contains($0) }
    }

    /// 阅读相关窗口标题
    private func isReadingTitle(_ title: String) -> Bool {
        let readingKeywords = [
            ".pdf", "documentation", "文档", "manual", "guide",
            "readme", "tutorial", "教程", "article", "文章"
        ]
        return readingKeywords.contains { title.contains($0) }
    }
}

// MARK: - AppState 扩展（场景检测集成）

extension AppState {
    /// 启动场景检测并自动同步
    func startSceneDetection() {
        SceneDetector.shared.startDetection()

        // 每 2 秒同步一次场景
        Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            guard let self = self else { return }

            Task { @MainActor in
                let detector = SceneDetector.shared
                self.updateDetectedScene(detector.currentScene, confidence: detector.sceneConfidence)
            }
        }
    }

    /// 停止场景检测
    func stopSceneDetection() {
        SceneDetector.shared.stopDetection()
    }
}
