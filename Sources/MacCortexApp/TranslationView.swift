//
//  TranslationView.swift
//  MacCortex
//
//  Phase 3 Week 2 Day 1-2 - 翻译界面 UI
//  Created on 2026-01-22
//

import SwiftUI

struct TranslationView: View {
    @StateObject private var viewModel = TranslationViewModel()
    @State private var showHistory = false

    var body: some View {
        VStack(spacing: 0) {
            // 顶部工具栏
            toolbarView
                .padding()
                .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 主内容区域
            HStack(spacing: 0) {
                // 左侧：翻译界面
                mainContentView
                    .frame(minWidth: 500, maxWidth: .infinity)

                // 右侧：历史记录（可选）
                if showHistory {
                    Divider()
                    historyView
                        .frame(width: 300)
                }
            }
        }
        .frame(minWidth: 600, minHeight: 500)
    }

    // MARK: - 工具栏

    private var toolbarView: some View {
        HStack(spacing: 16) {
            // 语言选择器
            HStack(spacing: 8) {
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
                .frame(width: 180)
                .labelsHidden()

                // 交换按钮
                Button(action: {
                    viewModel.swapLanguages()
                }) {
                    Image(systemName: "arrow.left.arrow.right")
                        .font(.system(size: 14))
                }
                .buttonStyle(.plain)
                .disabled(viewModel.sourceLanguage == .auto)
                .help("交换语言 (Cmd+E)")
                .keyboardShortcut("e", modifiers: .command)

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
                .frame(width: 180)
                .labelsHidden()
            }

            Divider()
                .frame(height: 20)

            // 风格选择器
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
            .frame(width: 200)

            Spacer()

            // Phase 3 Week 3 Day 2: 流式模式开关
            Toggle("流式", isOn: $viewModel.useStreamingMode)
                .toggleStyle(.switch)
                .controlSize(.small)
                .help("启用逐字显示效果")

            Divider()
                .frame(height: 20)

            // 历史记录按钮
            Button(action: {
                withAnimation {
                    showHistory.toggle()
                }
            }) {
                Image(systemName: showHistory ? "clock.fill" : "clock")
                    .font(.system(size: 14))
            }
            .buttonStyle(.plain)
            .help("历史记录 (Cmd+H)")
            .keyboardShortcut("h", modifiers: .command)

            // Backend 连接状态
            if viewModel.client.isConnected {
                Image(systemName: "circle.fill")
                    .foregroundColor(.green)
                    .font(.system(size: 8))
                    .help("Backend 已连接")
            } else {
                Image(systemName: "circle.fill")
                    .foregroundColor(.red)
                    .font(.system(size: 8))
                    .help("Backend 未连接")
            }
        }
    }

    // MARK: - 主内容区域

    private var mainContentView: some View {
        VStack(spacing: 16) {
            // 输入区域
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("输入文本")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Spacer()

                    Button(action: {
                        viewModel.pasteFromClipboard()
                    }) {
                        Label("粘贴", systemImage: "doc.on.clipboard")
                            .font(.caption)
                    }
                    .buttonStyle(.plain)
                    .help("粘贴剪贴板内容 (Cmd+V)")

                    Button(action: {
                        viewModel.copyInput()
                    }) {
                        Label("复制", systemImage: "doc.on.doc")
                            .font(.caption)
                    }
                    .buttonStyle(.plain)
                    .disabled(viewModel.inputText.isEmpty)
                    .help("复制输入文本")
                }

                TextEditor(text: $viewModel.inputText)
                    .frame(height: 150)
                    .font(.system(size: 13))
                    .border(Color.gray.opacity(0.3), width: 1)
                    .cornerRadius(4)
            }

            // 操作按钮
            HStack(spacing: 12) {
                // Phase 3 Week 3 Day 2: 根据模式选择翻译方法
                Button(action: {
                    Task {
                        if viewModel.useStreamingMode {
                            await viewModel.translateStream()
                        } else {
                            await viewModel.translate()
                        }
                    }
                }) {
                    HStack {
                        if viewModel.isTranslating {
                            ProgressView()
                                .scaleEffect(0.7)
                                .frame(width: 12, height: 12)
                        } else {
                            Image(systemName: viewModel.useStreamingMode ? "play.circle.fill" : "arrow.triangle.2.circlepath")
                        }
                        Text(viewModel.useStreamingMode ? "流式翻译" : "翻译")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.inputText.isEmpty || viewModel.isTranslating)
                .keyboardShortcut(.return, modifiers: .command)
                .help(viewModel.useStreamingMode ? "流式翻译（逐字显示） (Cmd+Enter)" : "翻译文本 (Cmd+Enter)")

                // Phase 3 Week 3 Day 2: 流式模式下显示停止按钮
                if viewModel.isStreaming {
                    Button(action: {
                        viewModel.stopStreaming()
                    }) {
                        Label("停止", systemImage: "stop.circle.fill")
                    }
                    .buttonStyle(.bordered)
                }

                Button(action: {
                    viewModel.clear()
                }) {
                    Label("清空", systemImage: "trash")
                }
                .disabled(viewModel.inputText.isEmpty && viewModel.outputText.isEmpty)
                .help("清空所有内容 (Cmd+K)")
                .keyboardShortcut("k", modifiers: .command)

                Spacer()

                // 统计信息
                if let stats = viewModel.stats {
                    HStack(spacing: 16) {
                        HStack(spacing: 4) {
                            Image(systemName: "clock")
                                .font(.caption)
                            Text("\(stats.duration, specifier: "%.3f")s")
                                .font(.caption)
                        }
                        .foregroundColor(.secondary)

                        if stats.hitRate > 0 {
                            HStack(spacing: 4) {
                                Image(systemName: "bolt.fill")
                                    .font(.caption)
                                    .foregroundColor(.green)
                                Text("\(stats.hitRate, specifier: "%.0f")%")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }

                        HStack(spacing: 4) {
                            Image(systemName: "tray.fill")
                                .font(.caption)
                            Text("\(stats.cacheSize)/1000")
                                .font(.caption)
                        }
                        .foregroundColor(.secondary)
                    }
                }
            }

            Divider()

            // 输出区域
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("翻译结果")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    // Phase 3 Week 3 Day 2: 流式进度显示
                    if viewModel.isStreaming {
                        ProgressView()
                            .scaleEffect(0.5)
                        Text(viewModel.streamProgress)
                            .font(.caption)
                            .foregroundColor(.blue)
                    }

                    if viewModel.isCached {
                        HStack(spacing: 4) {
                            Image(systemName: "bolt.fill")
                                .font(.system(size: 10))
                            Text("缓存命中")
                                .font(.caption)
                        }
                        .foregroundColor(.green)
                    }

                    Spacer()

                    Button(action: {
                        viewModel.copyResult()
                    }) {
                        Label("复制", systemImage: "doc.on.doc")
                            .font(.caption)
                    }
                    .buttonStyle(.plain)
                    .disabled(viewModel.outputText.isEmpty)
                    .help("复制翻译结果 (Cmd+C)")
                }

                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .font(.system(size: 13))
                        .foregroundColor(.red)
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(4)
                } else {
                    TextEditor(text: .constant(viewModel.outputText))
                        .frame(height: 150)
                        .font(.system(size: 13))
                        .border(Color.gray.opacity(0.3), width: 1)
                        .cornerRadius(4)
                        .disabled(true)
                }
            }
        }
        .padding()
    }

    // MARK: - 历史记录

    private var historyView: some View {
        VStack(spacing: 0) {
            // 历史记录标题
            HStack {
                Text("历史记录")
                    .font(.headline)

                Spacer()

                Button(action: {
                    viewModel.clearHistory()
                }) {
                    Image(systemName: "trash")
                        .font(.caption)
                }
                .buttonStyle(.plain)
                .disabled(viewModel.history.isEmpty)
                .help("清空历史记录")
            }
            .padding()

            Divider()

            // 历史记录列表
            if viewModel.history.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "clock.badge.xmark")
                        .font(.system(size: 40))
                        .foregroundColor(.secondary)
                    Text("暂无历史记录")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(viewModel.history) { item in
                            HistoryItemView(item: item) {
                                viewModel.loadFromHistory(item)
                                withAnimation {
                                    showHistory = false
                                }
                            }
                        }
                    }
                    .padding()
                }
            }
        }
        .background(Color(NSColor.controlBackgroundColor))
    }
}

// MARK: - 历史记录项视图

struct HistoryItemView: View {
    let item: TranslationHistory
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 6) {
                // 时间和缓存状态
                HStack {
                    Text(item.formattedTime)
                        .font(.caption2)
                        .foregroundColor(.secondary)

                    Spacer()

                    if item.cached {
                        HStack(spacing: 2) {
                            Image(systemName: "bolt.fill")
                                .font(.system(size: 8))
                            Text("缓存")
                                .font(.caption2)
                        }
                        .foregroundColor(.green)
                    }
                }

                // 语言对
                HStack(spacing: 4) {
                    Text(item.sourceLanguage.flag)
                        .font(.caption)
                    Image(systemName: "arrow.right")
                        .font(.system(size: 8))
                        .foregroundColor(.secondary)
                    Text(item.targetLanguage.flag)
                        .font(.caption)
                    Text("•")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(item.style.displayName)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                // 文本预览
                VStack(alignment: .leading, spacing: 2) {
                    Text(item.sourcePreview)
                        .font(.caption)
                        .lineLimit(1)

                    Text(item.translatedPreview)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
            }
            .padding(8)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.gray.opacity(0.2), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - 预览

#Preview {
    TranslationView()
        .frame(width: 800, height: 600)
}
