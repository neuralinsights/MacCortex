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

// MacCortex 撤销快照数据模型
// Phase 2 Week 2 Day 10: 一键撤销系统
// 创建时间：2026-01-21

import Foundation

/// 撤销快照（文件版本记录）
struct UndoSnapshot: Codable, Identifiable {
    // MARK: - 基本属性
    let id: UUID
    let timestamp: Date

    // MARK: - 任务关联
    let taskID: UUID
    let patternId: String

    // MARK: - 文件信息
    let filePath: URL?
    let originalContent: Data
    let modifiedContent: Data

    // MARK: - 元数据
    let description: String
    let fileSize: Int
    let contentHash: String

    // MARK: - TTL（生存时间）
    static let expirationDays = 7

    /// 是否已过期（7 天）
    var isExpired: Bool {
        let expirationDate = Calendar.current.date(
            byAdding: .day,
            value: Self.expirationDays,
            to: timestamp
        ) ?? timestamp

        return Date() > expirationDate
    }

    /// 剩余天数
    var remainingDays: Int {
        let expirationDate = Calendar.current.date(
            byAdding: .day,
            value: Self.expirationDays,
            to: timestamp
        ) ?? timestamp

        let components = Calendar.current.dateComponents(
            [.day],
            from: Date(),
            to: expirationDate
        )

        return max(0, components.day ?? 0)
    }

    /// 快照大小（人类可读）
    var fileSizeFormatted: String {
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(fileSize))
    }

    /// 创建时间（人类可读）
    var timestampFormatted: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .full
        return formatter.localizedString(for: timestamp, relativeTo: Date())
    }

    // MARK: - 初始化

    init(
        id: UUID = UUID(),
        timestamp: Date = Date(),
        taskID: UUID,
        patternId: String,
        filePath: URL?,
        originalContent: Data,
        modifiedContent: Data,
        description: String
    ) {
        self.id = id
        self.timestamp = timestamp
        self.taskID = taskID
        self.patternId = patternId
        self.filePath = filePath
        self.originalContent = originalContent
        self.modifiedContent = modifiedContent
        self.description = description
        self.fileSize = originalContent.count + modifiedContent.count
        self.contentHash = Self.calculateHash(originalContent, modifiedContent)
    }

    // MARK: - 哈希计算

    /// 计算内容哈希（用于去重）
    private static func calculateHash(_ original: Data, _ modified: Data) -> String {
        var combined = Data()
        combined.append(original)
        combined.append(modified)

        // 使用 SHA256 的前 16 个字符作为哈希
        let hash = combined.base64EncodedString()
            .prefix(16)

        return String(hash)
    }
}

/// 撤销操作结果
enum UndoResult {
    case success(message: String)
    case failure(error: Error)
    case expired
    case notFound
}

/// 撤销错误
enum UndoError: LocalizedError {
    case snapshotNotFound
    case snapshotExpired
    case fileNotFound
    case writeFailed(Error)
    case readFailed(Error)

    var errorDescription: String? {
        switch self {
        case .snapshotNotFound:
            return "未找到快照记录"
        case .snapshotExpired:
            return "快照已过期（超过 7 天）"
        case .fileNotFound:
            return "未找到文件"
        case .writeFailed(let error):
            return "写入文件失败: \(error.localizedDescription)"
        case .readFailed(let error):
            return "读取文件失败: \(error.localizedDescription)"
        }
    }
}
