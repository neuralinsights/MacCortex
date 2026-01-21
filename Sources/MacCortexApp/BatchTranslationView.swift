//
//  BatchTranslationView.swift
//  MacCortex
//
//  Phase 3 Week 2 Day 3-4 - 批量翻译界面 UI
//  Created on 2026-01-22
//

import SwiftUI
import UniformTypeIdentifiers

struct BatchTranslationView: View {
    @StateObject private var viewModel = BatchTranslationViewModel()
    @State private var showAddTextDialog = false
    @State private var newText = ""

    var body: some View {
        VStack(spacing: 0) {
            // 顶部配置栏
            configurationBar
                .padding()
                .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 主内容区域
            HStack(spacing: 0) {
                // 左侧：队列列表
                queueSection
                    .frame(minWidth: 300, maxWidth: 400)

                Divider()

                // 右侧：结果列表
                resultsSection
                    .frame(minWidth: 300)
            }

            Divider()

            // 底部操作栏
            bottomActionBar
                .padding()
                .background(Color(NSColor.controlBackgroundColor))
        }
        .frame(minWidth: 700, minHeight: 500)
        .sheet(isPresented: $showAddTextDialog) {
            addTextDialog
        }
    }

    // MARK: - 配置栏

    private var configurationBar: some View {
        HStack(spacing: 16) {
            // 源语言
            Picker("", selection: $viewModel.sourceLanguage) {
                ForEach(Language.allCases) { language in
                    HStack {
                        Text(language.flag)
                        Text(language.displayName)
                    }
                    .tag(language)
                }
            }
            .frame(width: 160)
            .labelsHidden()

            Image(systemName: "arrow.right")
                .foregroundColor(.secondary)
                .font(.system(size: 12))

            // 目标语言
            Picker("", selection: $viewModel.targetLanguage) {
                ForEach(Language.allCases.filter { $0 != .auto }) { language in
                    HStack {
                        Text(language.flag)
                        Text(language.displayName)
                    }
                    .tag(language)
                }
            }
            .frame(width: 160)
            .labelsHidden()

            Divider()
                .frame(height: 20)

            // 风格选择
            Picker("", selection: $viewModel.style) {
                ForEach(TranslationStyle.allCases) { style in
                    HStack {
                        Image(systemName: style.icon)
                        Text(style.displayName)
                    }
                    .tag(style)
                }
            }
            .pickerStyle(.segmented)
            .frame(width: 180)

            Spacer()

            // 统计信息
            if viewModel.totalItems > 0 {
                HStack(spacing: 12) {
                    HStack(spacing: 4) {
                        Image(systemName: "list.bullet")
                            .font(.caption)
                        Text("\(viewModel.totalItems)")
                            .font(.caption)
                    }
                    .foregroundColor(.secondary)

                    if viewModel.cacheHitRate > 0 {
                        HStack(spacing: 4) {
                            Image(systemName: "bolt.fill")
                                .font(.caption)
                                .foregroundColor(.green)
                            Text("\(viewModel.cacheHitRate, specifier: "%.0f")%")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
        }
    }

    // MARK: - 队列区域

    private var queueSection: some View {
        VStack(spacing: 0) {
            // 队列标题
            HStack {
                Text("待翻译列表")
                    .font(.headline)

                Spacer()

                Text("\(viewModel.queueItems.count) 项")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()

            Divider()

            // 队列列表
            if viewModel.queueItems.isEmpty {
                emptyQueueView
            } else {
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(viewModel.queueItems) { item in
                            QueueItemRow(item: item) {
                                viewModel.toggleItemSelection(item)
                            } onDelete: {
                                viewModel.removeItem(item)
                            }
                        }
                    }
                    .padding()
                }
            }

            Divider()

            // 队列操作按钮
            HStack(spacing: 12) {
                Button(action: {
                    showAddTextDialog = true
                }) {
                    Label("添加文本", systemImage: "plus")
                        .font(.caption)
                }

                Button(action: {
                    selectFile()
                }) {
                    Label("导入文件", systemImage: "folder")
                        .font(.caption)
                }

                Spacer()

                Button(action: {
                    viewModel.clearQueue()
                }) {
                    Label("清空", systemImage: "trash")
                        .font(.caption)
                }
                .disabled(viewModel.queueItems.isEmpty)
            }
            .padding()
        }
        .background(Color(NSColor.controlBackgroundColor))
        .onDrop(of: [.fileURL], isTargeted: nil) { providers in
            viewModel.handleDrop(providers: providers)
        }
    }

    // 空队列视图
    private var emptyQueueView: some View {
        VStack(spacing: 16) {
            Image(systemName: "tray")
                .font(.system(size: 60))
                .foregroundColor(.secondary)

            Text("拖放文件到此处")
                .font(.headline)
                .foregroundColor(.secondary)

            Text("支持 .txt / .md / .csv 文件")
                .font(.caption)
                .foregroundColor(.secondary)

            Button(action: {
                showAddTextDialog = true
            }) {
                Label("或点击添加文本", systemImage: "plus.circle")
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 结果区域

    private var resultsSection: some View {
        VStack(spacing: 0) {
            // 结果标题
            HStack {
                Text("翻译结果")
                    .font(.headline)

                Spacer()

                if viewModel.isTranslating {
                    ProgressView()
                        .scaleEffect(0.7)
                } else if !viewModel.results.isEmpty {
                    HStack(spacing: 8) {
                        Text("✅ \(viewModel.completedItems)")
                            .font(.caption)
                            .foregroundColor(.green)
                        Text("❌ \(viewModel.failedItems)")
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                }
            }
            .padding()

            Divider()

            // 进度条
            if viewModel.isTranslating || viewModel.progress > 0 {
                progressSection
            }

            // 结果列表
            if viewModel.results.isEmpty && !viewModel.isTranslating {
                emptyResultsView
            } else {
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(viewModel.results) { result in
                            ResultItemRow(result: result) {
                                viewModel.copyResult(result)
                            }
                        }
                    }
                    .padding()
                }
            }

            Divider()

            // 结果操作按钮
            if !viewModel.results.isEmpty {
                HStack(spacing: 12) {
                    Button(action: {
                        viewModel.exportCSV()
                    }) {
                        Label("导出 CSV", systemImage: "doc.text")
                            .font(.caption)
                    }

                    Button(action: {
                        viewModel.exportJSON()
                    }) {
                        Label("导出 JSON", systemImage: "doc.badge.gearshape")
                            .font(.caption)
                    }

                    Spacer()

                    Button(action: {
                        viewModel.copyAllResults()
                    }) {
                        Label("复制全部", systemImage: "doc.on.clipboard")
                            .font(.caption)
                    }
                }
                .padding()
            }
        }
        .background(Color(NSColor.windowBackgroundColor))
    }

    // 进度区域
    private var progressSection: some View {
        VStack(spacing: 8) {
            HStack {
                Text("翻译进度")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Spacer()

                Text("\(viewModel.completedItems)/\(viewModel.totalItems) (\(Int(viewModel.progress * 100))%)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            ProgressView(value: viewModel.progress, total: 1.0)

            if viewModel.cacheHitRate > 0 {
                HStack(spacing: 16) {
                    HStack(spacing: 4) {
                        Image(systemName: "bolt.fill")
                            .font(.system(size: 10))
                            .foregroundColor(.green)
                        Text("缓存命中率: \(viewModel.cacheHitRate, specifier: "%.0f")%")
                            .font(.caption)
                    }

                    HStack(spacing: 4) {
                        Image(systemName: "clock")
                            .font(.system(size: 10))
                        Text("总耗时: \(viewModel.totalDuration, specifier: "%.2f")s")
                            .font(.caption)
                    }
                }
                .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }

    // 空结果视图
    private var emptyResultsView: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 60))
                .foregroundColor(.secondary)

            Text("还没有翻译结果")
                .font(.headline)
                .foregroundColor(.secondary)

            Text("添加文本并点击"开始翻译"")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 底部操作栏

    private var bottomActionBar: some View {
        HStack(spacing: 16) {
            Button(action: {
                Task {
                    await viewModel.startBatchTranslation()
                }
            }) {
                HStack {
                    if viewModel.isTranslating {
                        ProgressView()
                            .scaleEffect(0.7)
                            .frame(width: 12, height: 12)
                    } else {
                        Image(systemName: "play.fill")
                    }
                    Text(viewModel.isTranslating ? "翻译中..." : "开始批量翻译")
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.queueItems.isEmpty || viewModel.isTranslating)
            .keyboardShortcut(.return, modifiers: .command)

            if viewModel.isTranslating {
                Button(action: {
                    viewModel.cancelTranslation()
                }) {
                    Label("取消", systemImage: "stop.fill")
                }
                .buttonStyle(.bordered)
            }

            Spacer()

            // 错误信息
            if let errorMessage = viewModel.errorMessage {
                HStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundColor(.red)
                        .lineLimit(1)

                    Button(action: {
                        viewModel.errorMessage = nil
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - 添加文本对话框

    private var addTextDialog: some View {
        VStack(spacing: 16) {
            Text("添加文本")
                .font(.headline)

            TextEditor(text: $newText)
                .frame(height: 150)
                .border(Color.gray.opacity(0.3), width: 1)
                .cornerRadius(4)

            HStack {
                Button("取消") {
                    showAddTextDialog = false
                    newText = ""
                }
                .keyboardShortcut(.cancelAction)

                Spacer()

                Button("添加") {
                    if !newText.isEmpty {
                        viewModel.addText(newText)
                        showAddTextDialog = false
                        newText = ""
                    }
                }
                .buttonStyle(.borderedProminent)
                .keyboardShortcut(.defaultAction)
                .disabled(newText.isEmpty)
            }
        }
        .padding()
        .frame(width: 400)
    }

    // MARK: - Helper Methods

    private func selectFile() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.text, .plainText, .commaSeparatedText]
        panel.allowsMultipleSelection = false

        panel.begin { response in
            if response == .OK, let url = panel.url {
                Task {
                    await viewModel.importFromFile(url: url)
                }
            }
        }
    }
}

// MARK: - 队列项行视图

struct QueueItemRow: View {
    let item: BatchQueueItem
    let onToggle: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Button(action: onToggle) {
                Image(systemName: item.isSelected ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(item.isSelected ? .blue : .secondary)
            }
            .buttonStyle(.plain)

            Text(item.text)
                .font(.system(size: 12))
                .lineLimit(2)
                .frame(maxWidth: .infinity, alignment: .leading)

            Button(action: onDelete) {
                Image(systemName: "trash")
                    .font(.caption)
                    .foregroundColor(.red)
            }
            .buttonStyle(.plain)
        }
        .padding(8)
        .background(item.isSelected ? Color.blue.opacity(0.1) : Color.clear)
        .cornerRadius(6)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(Color.gray.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 结果项行视图

struct ResultItemRow: View {
    let result: BatchResult
    let onCopy: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // 状态和操作
            HStack {
                // 状态图标
                if result.success {
                    HStack(spacing: 4) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                            .font(.caption)

                        if result.cached {
                            HStack(spacing: 2) {
                                Image(systemName: "bolt.fill")
                                    .font(.system(size: 8))
                                Text("缓存")
                                    .font(.caption2)
                            }
                            .foregroundColor(.green)
                        }
                    }
                } else {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.red)
                        .font(.caption)
                }

                Spacer()

                if result.success {
                    Button(action: onCopy) {
                        Image(systemName: "doc.on.doc")
                            .font(.caption)
                    }
                    .buttonStyle(.plain)
                }
            }

            // 原文
            VStack(alignment: .leading, spacing: 4) {
                Text("原文:")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                Text(result.originalText)
                    .font(.caption)
                    .lineLimit(2)
            }

            Divider()

            // 译文或错误
            if result.success, let translated = result.translatedText {
                VStack(alignment: .leading, spacing: 4) {
                    Text("译文:")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text(translated)
                        .font(.caption)
                        .lineLimit(2)
                }
            } else if let error = result.error {
                VStack(alignment: .leading, spacing: 4) {
                    Text("错误:")
                        .font(.caption2)
                        .foregroundColor(.red)
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.red)
                        .lineLimit(2)
                }
            }
        }
        .padding(10)
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(result.success ? Color.green.opacity(0.3) : Color.red.opacity(0.3), lineWidth: 1)
        )
    }
}

// MARK: - 预览

#Preview {
    BatchTranslationView()
        .frame(width: 900, height: 600)
}
