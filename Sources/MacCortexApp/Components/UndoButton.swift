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

// MacCortex 撤销 UI 组件
// Phase 2 Week 2 Day 10: 一键撤销系统
// 创建时间：2026-01-21

import SwiftUI

/// 撤销按钮
struct UndoButton: View {
    let snapshot: UndoSnapshot
    let onUndo: () -> Void

    @State private var isHovering = false

    var body: some View {
        Button(action: onUndo) {
            HStack(spacing: 8) {
                Image(systemName: "arrow.uturn.backward.circle.fill")
                    .font(.system(size: 16))

                Text("撤销")
                    .font(.system(size: 12, weight: .medium))
            }
            .foregroundColor(.white)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                isHovering ? Color.blue.opacity(0.8) : Color.blue
            )
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

/// 快照卡片
struct SnapshotCard: View {
    let snapshot: UndoSnapshot
    let onUndo: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 头部：时间戳 + 撤销按钮
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(snapshot.description)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.primary)

                    Text(snapshot.timestampFormatted)
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }

                Spacer()

                if snapshot.isExpired {
                    Text("已过期")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.red)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.red.opacity(0.15))
                        .cornerRadius(6)
                } else {
                    UndoButton(snapshot: snapshot, onUndo: onUndo)
                }
            }

            Divider()

            // 详情
            VStack(alignment: .leading, spacing: 6) {
                DetailRow(
                    icon: "doc.text.fill",
                    label: "Pattern",
                    value: snapshot.patternId
                )

                DetailRow(
                    icon: "internaldrive.fill",
                    label: "大小",
                    value: snapshot.fileSizeFormatted
                )

                if let filePath = snapshot.filePath {
                    DetailRow(
                        icon: "folder.fill",
                        label: "文件",
                        value: filePath.lastPathComponent
                    )
                }

                DetailRow(
                    icon: "clock.fill",
                    label: "剩余",
                    value: "\(snapshot.remainingDays) 天"
                )
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(
                    snapshot.isExpired ? Color.red.opacity(0.3) : Color.secondary.opacity(0.2),
                    lineWidth: 1
                )
        )
    }
}

/// 详情行（带图标）
private struct DetailRow: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 10))
                .foregroundColor(.secondary)
                .frame(width: 16)

            Text(label + ":")
                .font(.system(size: 10))
                .foregroundColor(.secondary)

            Text(value)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(.primary)

            Spacer()
        }
    }
}

/// 撤销历史视图
struct UndoHistoryView: View {
    @State private var snapshots: [UndoSnapshot] = []
    @State private var isLoading = true
    @State private var showCleanupConfirmation = false
    @State private var undoingSnapshotID: UUID? = nil

    var body: some View {
        VStack(spacing: 0) {
            // 头部
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("撤销历史")
                        .font(.title2)
                        .fontWeight(.bold)

                    Text("\(snapshots.count) 个快照")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                // 清理按钮
                Button(action: {
                    showCleanupConfirmation = true
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: "trash.fill")
                            .font(.system(size: 11))
                        Text("清理过期")
                            .font(.system(size: 11))
                    }
                    .foregroundColor(.red)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }
            .padding()

            Divider()

            // 快照列表
            if isLoading {
                Spacer()
                ProgressView()
                    .scaleEffect(1.5)
                Spacer()
            } else if snapshots.isEmpty {
                Spacer()
                VStack(spacing: 12) {
                    Image(systemName: "tray.fill")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)

                    Text("暂无撤销记录")
                        .font(.headline)
                        .foregroundColor(.secondary)
                }
                Spacer()
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(snapshots) { snapshot in
                            SnapshotCard(
                                snapshot: snapshot,
                                onUndo: {
                                    undoSnapshot(snapshot)
                                }
                            )
                            .disabled(undoingSnapshotID == snapshot.id)
                            .opacity(undoingSnapshotID == snapshot.id ? 0.5 : 1.0)
                        }
                    }
                    .padding()
                }
            }
        }
        .frame(width: 500, height: 600)
        .onAppear {
            loadSnapshots()
        }
        .alert("确认清理", isPresented: $showCleanupConfirmation) {
            Button("取消", role: .cancel) {}
            Button("清理", role: .destructive) {
                cleanupExpiredSnapshots()
            }
        } message: {
            Text("确定要清理所有过期快照吗？此操作不可撤销。")
        }
    }

    // MARK: - 私有方法

    /// 加载快照列表
    private func loadSnapshots() {
        Task {
            isLoading = true
            let allSnapshots = await UndoManager.shared.getAllSnapshots()
            await MainActor.run {
                snapshots = allSnapshots
                isLoading = false
            }
        }
    }

    /// 撤销快照
    private func undoSnapshot(_ snapshot: UndoSnapshot) {
        Task {
            await MainActor.run {
                undoingSnapshotID = snapshot.id
            }

            let result = await UndoManager.shared.undo(snapshotID: snapshot.id)

            await MainActor.run {
                undoingSnapshotID = nil

                switch result {
                case .success(let message):
                    print("✅ \(message)")
                    // 重新加载列表
                    loadSnapshots()

                case .failure(let error):
                    print("❌ 撤销失败: \(error.localizedDescription)")

                case .expired:
                    print("⚠️ 快照已过期")

                case .notFound:
                    print("❌ 快照未找到")
                }
            }
        }
    }

    /// 清理过期快照
    private func cleanupExpiredSnapshots() {
        Task {
            await UndoManager.shared.cleanupExpiredSnapshots()
            loadSnapshots()
        }
    }
}

// MARK: - 预览

#Preview("Undo Button") {
    let snapshot = UndoSnapshot(
        taskID: UUID(),
        patternId: "summarize",
        filePath: URL(fileURLWithPath: "/tmp/test.txt"),
        originalContent: Data(),
        modifiedContent: Data(),
        description: "总结文档"
    )

    return UndoButton(snapshot: snapshot) {
        print("撤销")
    }
    .padding()
}

#Preview("Snapshot Card") {
    let snapshot = UndoSnapshot(
        taskID: UUID(),
        patternId: "summarize",
        filePath: URL(fileURLWithPath: "/Users/test/Documents/report.txt"),
        originalContent: Data(count: 1024),
        modifiedContent: Data(count: 2048),
        description: "总结技术报告"
    )

    return SnapshotCard(snapshot: snapshot) {
        print("撤销")
    }
    .padding()
}

#Preview("Undo History View") {
    UndoHistoryView()
}
