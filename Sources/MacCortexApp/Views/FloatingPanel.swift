//
//  FloatingPanel.swift
//  MacCortex
//
//  Phase 3 Week 3 Day 4 - 悬浮窗口（Apple Intelligence 风格）
//  Created on 2026-01-22
//

import SwiftUI
import AppKit

/// 悬浮翻译面板
///
/// Apple Intelligence 风格的浮动窗口：
/// - 半透明毛玻璃背景
/// - 始终置顶（NSWindow.Level.floating）
/// - 快速翻译界面（输入 + 输出）
/// - 支持全局快捷键唤起（Cmd+Shift+T）
struct FloatingPanelView: View {
    @ObservedObject var viewModel: TranslationViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 16) {
            // 标题栏
            HStack {
                Image(systemName: "globe")
                    .foregroundColor(.blue)
                    .font(.system(size: 16))

                Text("快速翻译")
                    .font(.headline)

                Spacer()

                Button(action: {
                    FloatingPanelManager.shared.hidePanel()
                }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                        .font(.system(size: 14))
                }
                .buttonStyle(.plain)
                .help("关闭 (Esc)")
            }
            .padding(.horizontal)
            .padding(.top, 12)

            Divider()

            // 输入区域
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("输入")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Spacer()

                    // 语言选择
                    Picker("", selection: $viewModel.targetLanguage) {
                        ForEach(Language.allCases.filter { $0 != .auto }) { language in
                            Text("\(language.flag) \(language.displayName)")
                                .tag(language)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 120)
                    .labelsHidden()
                }

                TextEditor(text: $viewModel.inputText)
                    .frame(height: 80)
                    .font(.system(size: 12))
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                    )
            }
            .padding(.horizontal)

            // 翻译按钮
            HStack(spacing: 12) {
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
                            Image(systemName: "arrow.triangle.2.circlepath")
                        }
                        Text("翻译")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.inputText.isEmpty || viewModel.isTranslating)
                .keyboardShortcut(.return, modifiers: .command)

                Button(action: {
                    viewModel.clear()
                }) {
                    Label("清空", systemImage: "trash")
                }
                .disabled(viewModel.inputText.isEmpty && viewModel.outputText.isEmpty)

                Spacer()

                if viewModel.useStreamingMode {
                    Toggle("流式", isOn: $viewModel.useStreamingMode)
                        .toggleStyle(.switch)
                        .controlSize(.mini)
                }
            }
            .padding(.horizontal)

            Divider()

            // 输出区域
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("翻译结果")
                        .font(.caption)
                        .foregroundColor(.secondary)

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
                            Text("缓存")
                                .font(.caption)
                        }
                        .foregroundColor(.green)
                    }

                    Spacer()

                    Button(action: {
                        viewModel.copyResult()
                    }) {
                        Image(systemName: "doc.on.doc")
                            .font(.caption)
                    }
                    .buttonStyle(.plain)
                    .disabled(viewModel.outputText.isEmpty)
                    .help("复制")
                }

                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundColor(.red)
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(6)
                } else {
                    ScrollView {
                        Text(viewModel.outputText.isEmpty ? "翻译结果将在此显示..." : viewModel.outputText)
                            .font(.system(size: 12))
                            .foregroundColor(viewModel.outputText.isEmpty ? .secondary : .primary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                    }
                    .frame(height: 100)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                    )
                }
            }
            .padding(.horizontal)
            .padding(.bottom, 12)
        }
        .frame(width: 400, height: 380)
        .background(
            VisualEffectView(material: .hudWindow, blendingMode: .behindWindow)
        )
    }
}

/// NSVisualEffectView 包装器（毛玻璃效果）
struct VisualEffectView: NSViewRepresentable {
    let material: NSVisualEffectView.Material
    let blendingMode: NSVisualEffectView.BlendingMode

    func makeNSView(context: Context) -> NSVisualEffectView {
        let view = NSVisualEffectView()
        view.material = material
        view.blendingMode = blendingMode
        view.state = .active
        return view
    }

    func updateNSView(_ nsView: NSVisualEffectView, context: Context) {
        nsView.material = material
        nsView.blendingMode = blendingMode
    }
}

/// 悬浮面板管理器
///
/// 管理悬浮窗口的创建、显示、隐藏
@MainActor
class FloatingPanelManager: ObservableObject {
    static let shared = FloatingPanelManager()

    private var panelWindow: NSPanel?
    private var viewModel = TranslationViewModel()

    private init() {}

    /// 显示悬浮面板
    func showPanel() {
        // 如果已存在，直接显示
        if let window = panelWindow {
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }

        // 创建悬浮窗口
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 400, height: 380),
            styleMask: [.titled, .closable, .fullSizeContentView, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )

        // 窗口配置
        panel.title = "MacCortex - 快速翻译"
        panel.titlebarAppearsTransparent = true
        panel.titleVisibility = .hidden
        panel.level = .floating  // 始终置顶
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.isMovableByWindowBackground = true
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]

        // 居中显示
        panel.center()

        // 设置内容视图
        let contentView = FloatingPanelView(viewModel: viewModel)
        panel.contentView = NSHostingView(rootView: contentView)

        // 显示窗口
        panel.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        panelWindow = panel
    }

    /// 隐藏悬浮面板
    func hidePanel() {
        panelWindow?.orderOut(nil)
    }

    /// 切换悬浮面板显示状态
    func togglePanel() {
        if panelWindow?.isVisible == true {
            hidePanel()
        } else {
            showPanel()
        }
    }
}

// MARK: - 预览

#Preview {
    FloatingPanelView(viewModel: TranslationViewModel())
        .frame(width: 400, height: 380)
}
