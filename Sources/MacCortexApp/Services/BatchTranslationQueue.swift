//
//  BatchTranslationQueue.swift
//  MacCortex
//
//  Phase 3 Week 4 Day 1-2 - 批量翻译队列
//  Created on 2026-01-22
//

import Foundation
import SwiftUI
import Combine

/// 批量翻译项
struct BatchItem: Identifiable, Hashable {
    let id: UUID
    let url: URL
    var status: BatchStatus
    var progress: Double
    var sourceText: String?
    var translatedText: String?
    var error: String?
    let timestamp: Date

    init(url: URL) {
        self.id = UUID()
        self.url = url
        self.status = .pending
        self.progress = 0.0
        self.timestamp = Date()
    }

    var fileName: String {
        url.lastPathComponent
    }

    var fileSize: String {
        guard let attributes = try? FileManager.default.attributesOfItem(atPath: url.path),
              let size = attributes[.size] as? Int64 else {
            return "未知"
        }

        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: size)
    }
}

/// 批量翻译状态
enum BatchStatus: Equatable {
    case pending      // 等待中
    case processing   // 翻译中
    case completed    // 已完成
    case failed       // 失败
    case cancelled    // 已取消
}

/// 批量翻译队列管理器
@MainActor
class BatchTranslationQueue: ObservableObject {
    // MARK: - Published Properties

    /// 队列中的所有项
    @Published var items: [BatchItem] = []

    /// 是否正在处理
    @Published var isProcessing: Bool = false

    /// 整体进度（0.0 - 1.0）
    @Published var overallProgress: Double = 0.0

    /// 统计信息
    @Published var completedCount: Int = 0
    @Published var failedCount: Int = 0
    @Published var pendingCount: Int = 0

    // MARK: - Private Properties

    /// 最大并发数
    private let maxConcurrency = 5

    /// 活跃任务 ID 集合
    private var activeTasks: Set<UUID> = []

    /// Backend 客户端
    private let client = BackendClient.shared

    /// 取消标记
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Public Methods

    /// 添加文件到队列
    func addFiles(_ urls: [URL]) {
        for url in urls {
            // 检查文件是否已存在
            guard !items.contains(where: { $0.url == url }) else {
                continue
            }

            // 检查文件格式
            let ext = url.pathExtension.lowercased()
            guard ["txt", "md"].contains(ext) else {
                print("[BatchQueue] 不支持的文件格式: \(ext)")
                continue
            }

            // 添加到队列
            let item = BatchItem(url: url)
            items.append(item)
        }

        updateStatistics()
    }

    /// 开始批量翻译
    func start() {
        guard !isProcessing else { return }
        guard items.contains(where: { $0.status == .pending }) else { return }

        isProcessing = true
        print("[BatchQueue] 开始批量翻译，队列大小: \(items.count)")

        // 启动多个并发任务
        for _ in 0..<min(maxConcurrency, pendingCount) {
            processNext()
        }
    }

    /// 暂停批量翻译
    func pause() {
        isProcessing = false
        print("[BatchQueue] 暂停批量翻译")
    }

    /// 恢复批量翻译
    func resume() {
        start()
    }

    /// 取消所有任务
    func cancel() {
        isProcessing = false
        activeTasks.removeAll()

        // 将所有 pending 和 processing 状态的项标记为 cancelled
        for index in items.indices {
            if items[index].status == .pending || items[index].status == .processing {
                items[index].status = .cancelled
            }
        }

        updateStatistics()
        print("[BatchQueue] 取消所有任务")
    }

    /// 移除单个项
    func remove(_ id: UUID) {
        items.removeAll { $0.id == id }
        updateStatistics()
    }

    /// 清空队列
    func clearCompleted() {
        items.removeAll { $0.status == .completed || $0.status == .failed || $0.status == .cancelled }
        updateStatistics()
    }

    /// 重试失败的项
    func retryFailed() {
        for index in items.indices {
            if items[index].status == .failed {
                items[index].status = .pending
                items[index].progress = 0.0
                items[index].error = nil
            }
        }

        updateStatistics()
        start()
    }

    // MARK: - Private Methods

    /// 处理下一个待翻译项
    private func processNext() {
        // 1. 检查是否暂停
        guard isProcessing else { return }

        // 2. 检查并发数
        guard activeTasks.count < maxConcurrency else { return }

        // 3. 获取下一个待处理项
        guard let index = items.firstIndex(where: { $0.status == .pending }) else {
            // 所有任务完成
            if activeTasks.isEmpty {
                isProcessing = false
                print("[BatchQueue] 批量翻译完成")

                // 发送完成通知
                Task { @MainActor in
                    await NotificationManager.shared.sendBatchTranslationCompletedNotification(
                        completedCount: completedCount,
                        totalCount: items.count,
                        failedCount: failedCount
                    )
                }
            }
            return
        }

        let item = items[index]

        // 4. 标记为处理中
        activeTasks.insert(item.id)
        items[index].status = .processing
        updateStatistics()

        print("[BatchQueue] 开始翻译: \(item.fileName)")

        // 5. 异步翻译
        Task {
            await translateFile(index)
            activeTasks.remove(item.id)
            updateStatistics()
            processNext()  // 递归处理下一个
        }
    }

    /// 翻译单个文件
    private func translateFile(_ index: Int) async {
        let item = items[index]

        do {
            // 1. 读取文件内容
            let sourceText = try FileReader.shared.readFile(item.url)
            items[index].sourceText = sourceText
            items[index].progress = 0.2

            // 2. 调用翻译 API
            let settings = SettingsManager.shared
            let response = try await client.translate(
                text: sourceText,
                targetLanguage: settings.defaultTargetLanguage.code,
                sourceLanguage: settings.defaultSourceLanguage.code,
                style: settings.defaultStyle.rawValue
            )

            items[index].progress = 0.8

            // 3. 保存翻译结果
            guard let translatedText = response.output else {
                throw BatchError.emptyResponse
            }

            items[index].translatedText = translatedText
            items[index].progress = 1.0
            items[index].status = .completed

            print("[BatchQueue] 翻译完成: \(item.fileName)")

        } catch {
            // 翻译失败
            items[index].status = .failed
            items[index].error = error.localizedDescription
            items[index].progress = 0.0

            print("[BatchQueue] 翻译失败: \(item.fileName), 错误: \(error)")
        }

        updateStatistics()
    }

    /// 更新统计信息
    private func updateStatistics() {
        completedCount = items.filter { $0.status == .completed }.count
        failedCount = items.filter { $0.status == .failed }.count
        pendingCount = items.filter { $0.status == .pending }.count

        // 计算整体进度
        let totalItems = items.count
        guard totalItems > 0 else {
            overallProgress = 0.0
            return
        }

        let totalProgress = items.reduce(0.0) { sum, item in
            switch item.status {
            case .completed:
                return sum + 1.0
            case .processing:
                return sum + item.progress
            default:
                return sum
            }
        }

        overallProgress = totalProgress / Double(totalItems)
    }
}

/// 批量翻译错误
enum BatchError: LocalizedError {
    case emptyResponse
    case fileReadError(String)
    case translationError(String)

    var errorDescription: String? {
        switch self {
        case .emptyResponse:
            return "翻译结果为空"
        case .fileReadError(let detail):
            return "文件读取失败: \(detail)"
        case .translationError(let detail):
            return "翻译失败: \(detail)"
        }
    }
}
