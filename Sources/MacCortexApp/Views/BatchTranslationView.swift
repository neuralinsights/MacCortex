//
//  BatchTranslationView.swift
//  MacCortex
//
//  Phase 3 Week 4 Day 1-2 - 批量翻译界面
//  Created on 2026-01-22
//

import SwiftUI
import UniformTypeIdentifiers
import AppKit

/// 批量翻译视图
struct BatchTranslationView: View {
    @StateObject private var queue = BatchTranslationQueue()
    @State private var showingFileImporter = false
    @State private var isDragging = false
    @State private var showingExportOptions = false
    @State private var exportOptions = ExportOptions.default

    var body: some View {
        VStack(spacing: 0) {
            // 顶部工具栏
            toolbarView
                .padding()
                .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 主内容区域
            if queue.items.isEmpty {
                emptyStateView
            } else {
                contentView
            }
        }
        .fileImporter(
            isPresented: $showingFileImporter,
            allowedContentTypes: [.plainText, .text],
            allowsMultipleSelection: true
        ) { result in
            handleFileSelection(result)
        }
        .sheet(isPresented: $showingExportOptions) {
            ExportOptionsView(
                options: $exportOptions,
                isPresented: $showingExportOptions,
                onExport: { options in
                    exportOptions = options
                    performExport(with: options)
                }
            )
        }
    }

    // MARK: - 工具栏

    private var toolbarView: some View {
        HStack(spacing: 16) {
            // 标题
            HStack(spacing: 8) {
                Image(systemName: "doc.on.doc")
                    .foregroundColor(.blue)
                Text("批量翻译")
                    .font(.headline)
            }

            Spacer()

            // 统计信息
            if !queue.items.isEmpty {
                statisticsView
            }

            Divider()
                .frame(height: 20)

            // 控制按钮
            controlButtons
        }
    }

    private var statisticsView: some View {
        HStack(spacing: 16) {
            StatLabel(icon: "checkmark.circle", text: "\(queue.completedCount)", color: .green)
            StatLabel(icon: "exclamationmark.triangle", text: "\(queue.failedCount)", color: .red)
            StatLabel(icon: "clock", text: "\(queue.pendingCount)", color: .orange)
        }
        .font(.caption)
    }

    private var controlButtons: some View {
        HStack(spacing: 8) {
            // 添加文件按钮
            Button(action: {
                showingFileImporter = true
            }) {
                Label("添加文件", systemImage: "plus.circle")
            }
            .help("添加 .txt、.md 文件")

            // 开始/暂停按钮
            if !queue.items.isEmpty {
                if queue.isProcessing {
                    Button(action: {
                        queue.pause()
                    }) {
                        Label("暂停", systemImage: "pause.circle")
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.orange)
                } else if queue.pendingCount > 0 || queue.items.contains(where: { $0.status == .processing }) {
                    Button(action: {
                        queue.start()
                    }) {
                        Label(queue.completedCount > 0 ? "继续" : "开始翻译", systemImage: "play.circle")
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.green)
                }

                // 导出按钮
                Button(action: {
                    showingExportOptions = true
                }) {
                    Label("导出", systemImage: "square.and.arrow.up")
                }
                .disabled(queue.completedCount == 0)
                .help("导出翻译结果")

                // 清空按钮
                Menu {
                    Button("清空已完成") {
                        queue.clearCompleted()
                    }
                    Button("重试失败项") {
                        queue.retryFailed()
                    }
                    .disabled(queue.failedCount == 0)
                    Divider()
                    Button("取消所有", role: .destructive) {
                        queue.cancel()
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
                .help("更多操作")
            }
        }
    }

    // MARK: - 空状态视图

    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Spacer()

            // 拖放区域
            VStack(spacing: 16) {
                Image(systemName: "doc.badge.plus")
                    .font(.system(size: 60))
                    .foregroundColor(isDragging ? .blue : .secondary)

                Text("拖放文件到此处")
                    .font(.title3)
                    .fontWeight(.medium)

                Text("支持 .txt、.md 格式\n最多 100 个文件")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)

                Button(action: {
                    showingFileImporter = true
                }) {
                    Label("选择文件", systemImage: "folder")
                }
                .buttonStyle(.borderedProminent)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isDragging ? Color.blue : Color.gray.opacity(0.3), lineWidth: 2)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(isDragging ? Color.blue.opacity(0.05) : Color.clear)
                    )
            )
            .padding(40)
            .onDrop(of: [.fileURL], isTargeted: $isDragging) { providers in
                handleDrop(providers)
            }

            Spacer()
        }
    }

    // MARK: - 内容视图

    private var contentView: some View {
        VStack(spacing: 0) {
            // 整体进度
            if queue.isProcessing || queue.completedCount > 0 {
                overallProgressView
                    .padding()
                    .background(Color(NSColor.controlBackgroundColor))

                Divider()
            }

            // 文件列表
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(queue.items) { item in
                        BatchItemRow(item: item, onRemove: {
                            queue.remove(item.id)
                        })
                    }
                }
                .padding()
            }
            .onDrop(of: [.fileURL], isTargeted: $isDragging) { providers in
                handleDrop(providers)
            }
        }
    }

    private var overallProgressView: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("整体进度")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Spacer()

                Text("\(Int(queue.overallProgress * 100))%")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Text("(\(queue.completedCount + queue.failedCount)/\(queue.items.count))")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            ProgressView(value: queue.overallProgress)
                .progressViewStyle(.linear)
        }
    }

    // MARK: - Helper Methods

    private func handleFileSelection(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            queue.addFiles(urls)
        case .failure(let error):
            print("[BatchTranslation] 文件选择失败: \(error)")
        }
    }

    private func handleDrop(_ providers: [NSItemProvider]) -> Bool {
        var urls: [URL] = []

        for provider in providers {
            _ = provider.loadObject(ofClass: URL.self) { url, error in
                if let url = url {
                    urls.append(url)
                }
            }
        }

        // 延迟添加，等待异步加载完成
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            queue.addFiles(urls)
        }

        return true
    }

    // MARK: - Export Methods

    /// 执行导出
    private func performExport(with options: ExportOptions) {
        let savePanel = NSSavePanel()
        savePanel.allowedContentTypes = [contentTypeForFormat(options.format)]
        savePanel.nameFieldStringValue = defaultFilename(for: options.format)
        savePanel.title = "导出翻译结果"
        savePanel.message = "选择导出位置"
        savePanel.canCreateDirectories = true

        savePanel.begin { response in
            guard response == .OK, let url = savePanel.url else {
                print("[BatchTranslation] 导出已取消")
                return
            }

            do {
                try ExportManager.shared.export(
                    items: queue.items,
                    options: options,
                    to: url
                )
                print("[BatchTranslation] 导出成功: \(url.path)")

                // 显示成功通知（可选）
                showExportSuccessNotification(url: url)
            } catch {
                print("[BatchTranslation] 导出失败: \(error)")
                showExportErrorAlert(error: error)
            }
        }
    }

    /// 获取导出格式对应的 UTType
    private func contentTypeForFormat(_ format: ExportFormat) -> UTType {
        switch format {
        case .txt:
            return .plainText
        case .pdf:
            return .pdf
        case .docx:
            return UTType(filenameExtension: "docx") ?? .data
        }
    }

    /// 生成默认文件名
    private func defaultFilename(for format: ExportFormat) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd_HHmmss"
        let timestamp = formatter.string(from: Date())
        return "MacCortex_Export_\(timestamp).\(format.rawValue)"
    }

    /// 显示导出成功通知
    private func showExportSuccessNotification(url: URL) {
        // 可以使用 NSUserNotification 或 UNUserNotificationCenter
        // 这里使用简单的控制台日志
        print("[BatchTranslation] ✅ 导出成功！文件已保存至: \(url.path)")
    }

    /// 显示导出错误警告
    private func showExportErrorAlert(error: Error) {
        let alert = NSAlert()
        alert.messageText = "导出失败"
        alert.informativeText = error.localizedDescription
        alert.alertStyle = .warning
        alert.addButton(withTitle: "确定")
        alert.runModal()
    }
}

// MARK: - 批量翻译项行视图

struct BatchItemRow: View {
    let item: BatchItem
    let onRemove: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // 状态图标
            statusIcon
                .frame(width: 24)

            // 文件信息
            VStack(alignment: .leading, spacing: 4) {
                Text(item.fileName)
                    .font(.system(size: 13))
                    .lineLimit(1)

                HStack(spacing: 8) {
                    Text(item.fileSize)
                        .font(.caption2)
                        .foregroundColor(.secondary)

                    if let error = item.error {
                        Text("• \(error)")
                            .font(.caption2)
                            .foregroundColor(.red)
                            .lineLimit(1)
                    } else if item.status == .completed {
                        Text("• 翻译完成")
                            .font(.caption2)
                            .foregroundColor(.green)
                    }
                }
            }

            Spacer()

            // 进度或操作按钮
            if item.status == .processing {
                HStack(spacing: 8) {
                    ProgressView()
                        .scaleEffect(0.7)

                    Text("\(Int(item.progress * 100))%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .frame(width: 40, alignment: .trailing)
                }
            } else {
                Button(action: onRemove) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
                .help("移除")
            }
        }
        .padding(10)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(backgroundColor)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(borderColor, lineWidth: 1)
        )
    }

    private var statusIcon: some View {
        Group {
            switch item.status {
            case .pending:
                Image(systemName: "clock")
                    .foregroundColor(.orange)
            case .processing:
                Image(systemName: "arrow.triangle.2.circlepath")
                    .foregroundColor(.blue)
            case .completed:
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
            case .failed:
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.red)
            case .cancelled:
                Image(systemName: "xmark.circle")
                    .foregroundColor(.secondary)
            }
        }
        .font(.system(size: 16))
    }

    private var backgroundColor: Color {
        switch item.status {
        case .completed:
            return Color.green.opacity(0.05)
        case .failed:
            return Color.red.opacity(0.05)
        case .processing:
            return Color.blue.opacity(0.05)
        default:
            return Color(NSColor.controlBackgroundColor)
        }
    }

    private var borderColor: Color {
        switch item.status {
        case .completed:
            return Color.green.opacity(0.3)
        case .failed:
            return Color.red.opacity(0.3)
        case .processing:
            return Color.blue.opacity(0.3)
        default:
            return Color.gray.opacity(0.2)
        }
    }
}

// MARK: - 统计标签

struct StatLabel: View {
    let icon: String
    let text: String
    let color: Color

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .foregroundColor(color)
            Text(text)
                .foregroundColor(.primary)
        }
    }
}

// MARK: - 预览

#Preview {
    BatchTranslationView()
        .frame(width: 800, height: 600)
}
