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

// MacCortex 撤销管理器
// Phase 2 Week 2 Day 10: 一键撤销系统
// 创建时间：2026-01-21

import Foundation
import os.log

/// 撤销管理器（Actor 保证线程安全）
actor UndoManager {
    // MARK: - 单例
    static let shared = UndoManager()

    // MARK: - 属性
    private var snapshots: [UndoSnapshot] = []
    private let snapshotDirectory: URL
    private let logger = Logger(subsystem: "com.yugeng.MacCortex", category: "UndoManager")

    // MARK: - 初始化

    private init() {
        // 快照存储目录：~/Library/Application Support/MacCortex/Snapshots/
        let appSupport = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        )[0]

        self.snapshotDirectory = appSupport
            .appendingPathComponent("MacCortex")
            .appendingPathComponent("Snapshots")

        // 创建目录
        try? FileManager.default.createDirectory(
            at: snapshotDirectory,
            withIntermediateDirectories: true
        )

        // 加载现有快照
        Task {
            await loadSnapshots()
        }
    }

    // MARK: - 公共方法

    /// 创建快照
    /// - Parameters:
    ///   - taskID: 任务 ID
    ///   - patternId: Pattern ID
    ///   - filePath: 文件路径（可选）
    ///   - originalContent: 原始内容
    ///   - modifiedContent: 修改后内容
    ///   - description: 描述
    /// - Returns: 快照 ID
    func createSnapshot(
        taskID: UUID,
        patternId: String,
        filePath: URL? = nil,
        originalContent: Data,
        modifiedContent: Data,
        description: String
    ) async throws -> UUID {
        let snapshot = UndoSnapshot(
            taskID: taskID,
            patternId: patternId,
            filePath: filePath,
            originalContent: originalContent,
            modifiedContent: modifiedContent,
            description: description
        )

        // 保存到磁盘
        try await saveSnapshot(snapshot)

        // 添加到内存列表
        snapshots.append(snapshot)

        logger.info("已创建快照: \(snapshot.id), 大小: \(snapshot.fileSizeFormatted)")

        return snapshot.id
    }

    /// 撤销快照
    /// - Parameter snapshotID: 快照 ID
    /// - Returns: 撤销结果
    func undo(snapshotID: UUID) async -> UndoResult {
        // 查找快照
        guard let snapshot = snapshots.first(where: { $0.id == snapshotID }) else {
            logger.error("快照未找到: \(snapshotID)")
            return .notFound
        }

        // 检查是否过期
        if snapshot.isExpired {
            logger.warning("快照已过期: \(snapshotID)")
            return .expired
        }

        // 恢复文件（如果有）
        if let filePath = snapshot.filePath {
            do {
                try snapshot.originalContent.write(to: filePath)
                logger.info("已恢复文件: \(filePath.path)")
            } catch {
                logger.error("恢复文件失败: \(error.localizedDescription)")
                return .failure(error: UndoError.writeFailed(error))
            }
        }

        // 删除快照
        do {
            try await deleteSnapshot(snapshot)
            snapshots.removeAll { $0.id == snapshotID }

            let message = "已成功撤销: \(snapshot.description)"
            logger.info("\(message)")

            return .success(message: message)
        } catch {
            logger.error("删除快照失败: \(error.localizedDescription)")
            return .failure(error: error)
        }
    }

    /// 获取所有快照
    func getAllSnapshots() -> [UndoSnapshot] {
        return snapshots.sorted { $0.timestamp > $1.timestamp }
    }

    /// 获取快照详情
    /// - Parameter snapshotID: 快照 ID
    /// - Returns: 快照（如果存在）
    func getSnapshot(id snapshotID: UUID) -> UndoSnapshot? {
        return snapshots.first { $0.id == snapshotID }
    }

    /// 清理过期快照
    func cleanupExpiredSnapshots() async {
        let expired = snapshots.filter { $0.isExpired }

        logger.info("开始清理 \(expired.count) 个过期快照")

        for snapshot in expired {
            do {
                try await deleteSnapshot(snapshot)
                snapshots.removeAll { $0.id == snapshot.id }
                logger.info("已删除过期快照: \(snapshot.id)")
            } catch {
                logger.error("删除快照失败: \(error.localizedDescription)")
            }
        }

        logger.info("清理完成，剩余 \(self.snapshots.count) 个快照")
    }

    /// 获取存储统计
    func getStorageStats() -> (count: Int, totalSize: Int, expiredCount: Int) {
        let count = snapshots.count
        let totalSize = snapshots.reduce(0) { $0 + $1.fileSize }
        let expiredCount = snapshots.filter { $0.isExpired }.count

        return (count, totalSize, expiredCount)
    }

    // MARK: - 私有方法

    /// 保存快照到磁盘
    private func saveSnapshot(_ snapshot: UndoSnapshot) async throws {
        let fileURL = snapshotDirectory.appendingPathComponent("\(snapshot.id.uuidString).json")

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(snapshot)

        try data.write(to: fileURL)
    }

    /// 删除快照
    private func deleteSnapshot(_ snapshot: UndoSnapshot) async throws {
        let fileURL = snapshotDirectory.appendingPathComponent("\(snapshot.id.uuidString).json")

        if FileManager.default.fileExists(atPath: fileURL.path) {
            try FileManager.default.removeItem(at: fileURL)
        }
    }

    /// 加载快照
    private func loadSnapshots() async {
        do {
            let files = try FileManager.default.contentsOfDirectory(
                at: snapshotDirectory,
                includingPropertiesForKeys: nil
            )

            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601

            for fileURL in files where fileURL.pathExtension == "json" {
                do {
                    let data = try Data(contentsOf: fileURL)
                    let snapshot = try decoder.decode(UndoSnapshot.self, from: data)
                    snapshots.append(snapshot)
                } catch {
                    logger.error("加载快照失败: \(fileURL.lastPathComponent), 错误: \(error.localizedDescription)")
                }
            }

            logger.info("已加载 \(self.snapshots.count) 个快照")
        } catch {
            logger.error("读取快照目录失败: \(error.localizedDescription)")
        }
    }
}
