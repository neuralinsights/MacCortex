//
//  NotificationManager.swift
//  MacCortex
//
//  Phase 3 Week 4 Day 5 - 通知管理器
//  Created on 2026-01-22
//

import Foundation
import UserNotifications

/// 通知管理器（单例）
@MainActor
class NotificationManager {
    static let shared = NotificationManager()

    private init() {}

    /// 请求通知权限
    func requestAuthorization() async throws {
        let center = UNUserNotificationCenter.current()

        let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])

        if granted {
            print("[Notification] ✅ 通知权限已授予")
        } else {
            print("[Notification] ⚠️  用户拒绝了通知权限")
        }
    }

    /// 检查通知权限状态
    func checkAuthorizationStatus() async -> UNAuthorizationStatus {
        let center = UNUserNotificationCenter.current()
        let settings = await center.notificationSettings()
        return settings.authorizationStatus
    }

    /// 发送翻译完成通知
    ///
    /// - Parameters:
    ///   - sourceText: 原文（显示前 50 字符）
    ///   - targetLanguage: 目标语言
    ///   - translationMode: 翻译模式（批量/剪贴板/手动）
    func sendTranslationCompletedNotification(
        sourceText: String,
        targetLanguage: Language,
        translationMode: TranslationMode = .manual
    ) async {
        // 检查设置是否启用通知
        let settings = SettingsManager.shared

        // 根据模式检查是否启用通知
        let shouldNotify: Bool
        switch translationMode {
        case .clipboard:
            shouldNotify = settings.clipboardShowNotification
        case .batch, .manual:
            shouldNotify = true  // 批量和手动翻译总是显示通知
        }

        guard shouldNotify else {
            print("[Notification] 通知已禁用")
            return
        }

        // 检查权限
        let status = await checkAuthorizationStatus()
        guard status == .authorized else {
            print("[Notification] 通知权限未授予: \(status)")
            return
        }

        // 创建通知内容
        let content = UNMutableNotificationContent()
        content.title = "翻译完成"
        content.body = formatNotificationBody(sourceText: sourceText, targetLanguage: targetLanguage)
        content.sound = .default

        // 添加自定义数据
        content.userInfo = [
            "translationMode": translationMode.rawValue,
            "targetLanguage": targetLanguage.code
        ]

        // 设置类别（用于交互式通知）
        content.categoryIdentifier = "TRANSLATION_COMPLETED"

        // 立即触发通知
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 0.1, repeats: false)

        // 创建请求
        let identifier = UUID().uuidString
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)

        // 发送通知
        do {
            try await UNUserNotificationCenter.current().add(request)
            print("[Notification] ✅ 通知已发送: \(identifier)")
        } catch {
            print("[Notification] ❌ 通知发送失败: \(error)")
        }
    }

    /// 发送批量翻译完成通知
    ///
    /// - Parameters:
    ///   - completedCount: 已完成数量
    ///   - totalCount: 总数量
    ///   - failedCount: 失败数量
    func sendBatchTranslationCompletedNotification(
        completedCount: Int,
        totalCount: Int,
        failedCount: Int = 0
    ) async {
        // 检查权限
        let status = await checkAuthorizationStatus()
        guard status == .authorized else {
            print("[Notification] 通知权限未授予: \(status)")
            return
        }

        // 创建通知内容
        let content = UNMutableNotificationContent()
        content.title = "批量翻译完成"

        if failedCount > 0 {
            content.body = "已完成 \(completedCount) 个文件，\(failedCount) 个失败"
        } else {
            content.body = "已完成 \(completedCount) 个文件的翻译"
        }

        content.sound = .default

        // 添加自定义数据
        content.userInfo = [
            "translationMode": "batch",
            "completedCount": completedCount,
            "totalCount": totalCount,
            "failedCount": failedCount
        ]

        // 设置类别
        content.categoryIdentifier = "BATCH_TRANSLATION_COMPLETED"

        // 立即触发通知
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 0.1, repeats: false)

        // 创建请求
        let identifier = UUID().uuidString
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)

        // 发送通知
        do {
            try await UNUserNotificationCenter.current().add(request)
            print("[Notification] ✅ 批量翻译通知已发送: \(identifier)")
        } catch {
            print("[Notification] ❌ 通知发送失败: \(error)")
        }
    }

    /// 发送导出完成通知
    ///
    /// - Parameters:
    ///   - format: 导出格式
    ///   - itemCount: 导出项数量
    ///   - filePath: 文件路径
    func sendExportCompletedNotification(
        format: ExportFormat,
        itemCount: Int,
        filePath: String
    ) async {
        // 检查权限
        let status = await checkAuthorizationStatus()
        guard status == .authorized else {
            print("[Notification] 通知权限未授予: \(status)")
            return
        }

        // 创建通知内容
        let content = UNMutableNotificationContent()
        content.title = "导出完成"
        content.body = "已将 \(itemCount) 个翻译导出为 \(format.displayName)"
        content.sound = .default

        // 添加自定义数据
        content.userInfo = [
            "action": "export",
            "format": format.rawValue,
            "itemCount": itemCount,
            "filePath": filePath
        ]

        // 设置类别
        content.categoryIdentifier = "EXPORT_COMPLETED"

        // 立即触发通知
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 0.1, repeats: false)

        // 创建请求
        let identifier = UUID().uuidString
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)

        // 发送通知
        do {
            try await UNUserNotificationCenter.current().add(request)
            print("[Notification] ✅ 导出通知已发送: \(identifier)")
        } catch {
            print("[Notification] ❌ 通知发送失败: \(error)")
        }
    }

    /// 设置通知类别（支持交互式操作）
    func setupNotificationCategories() {
        let center = UNUserNotificationCenter.current()

        // 翻译完成类别
        let copyAction = UNNotificationAction(
            identifier: "COPY_ACTION",
            title: "复制结果",
            options: []
        )

        let viewAction = UNNotificationAction(
            identifier: "VIEW_ACTION",
            title: "查看详情",
            options: .foreground
        )

        let translationCategory = UNNotificationCategory(
            identifier: "TRANSLATION_COMPLETED",
            actions: [copyAction, viewAction],
            intentIdentifiers: [],
            options: []
        )

        // 批量翻译完成类别
        let openAction = UNNotificationAction(
            identifier: "OPEN_ACTION",
            title: "打开结果",
            options: .foreground
        )

        let batchCategory = UNNotificationCategory(
            identifier: "BATCH_TRANSLATION_COMPLETED",
            actions: [openAction],
            intentIdentifiers: [],
            options: []
        )

        // 导出完成类别
        let revealAction = UNNotificationAction(
            identifier: "REVEAL_ACTION",
            title: "在 Finder 中显示",
            options: .foreground
        )

        let exportCategory = UNNotificationCategory(
            identifier: "EXPORT_COMPLETED",
            actions: [revealAction],
            intentIdentifiers: [],
            options: []
        )

        // 注册类别
        center.setNotificationCategories([translationCategory, batchCategory, exportCategory])

        print("[Notification] ✅ 通知类别已设置")
    }

    /// 清除所有已发送的通知
    func clearAllNotifications() {
        UNUserNotificationCenter.current().removeAllDeliveredNotifications()
        print("[Notification] 已清除所有通知")
    }

    /// 清除指定通知
    func clearNotifications(withIdentifiers identifiers: [String]) {
        UNUserNotificationCenter.current().removeDeliveredNotifications(withIdentifiers: identifiers)
        print("[Notification] 已清除 \(identifiers.count) 个通知")
    }

    // MARK: - Private Methods

    /// 格式化通知正文
    private func formatNotificationBody(sourceText: String, targetLanguage: Language) -> String {
        // 截断原文（最多显示 50 字符）
        let truncatedText: String
        if sourceText.count > 50 {
            truncatedText = String(sourceText.prefix(50)) + "..."
        } else {
            truncatedText = sourceText
        }

        return "\"\(truncatedText)\" → \(targetLanguage.displayName)"
    }
}

/// 翻译模式
enum TranslationMode: String {
    case manual = "manual"        // 手动翻译
    case clipboard = "clipboard"  // 剪贴板翻译
    case batch = "batch"          // 批量翻译
}
