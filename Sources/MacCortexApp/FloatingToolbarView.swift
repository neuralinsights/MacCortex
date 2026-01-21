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

// MacCortex 浮动工具栏
// Phase 2 Day 2-3: Apple Intelligence 风格浮动工具栏
// 创建时间：2026-01-21

import SwiftUI

/// 浮动工具栏视图（Apple Intelligence 风格）
struct FloatingToolbarView: View {
    @Environment(AppState.self) private var appState

    // MARK: - UI 状态
    @State private var isExpanded: Bool = true
    @State private var isHovering: Bool = false
    @State private var dragOffset: CGSize = .zero
    @State private var savedPosition: CGPoint? = nil

    // MARK: - 常量
    private let compactWidth: CGFloat = 60
    private let expandedWidth: CGFloat = 320
    private let toolbarHeight: CGFloat = 60

    var body: some View {
        VStack(spacing: 0) {
            if isExpanded {
                expandedToolbar
            } else {
                compactToolbar
            }
        }
        .frame(width: isExpanded ? expandedWidth : compactWidth, height: toolbarHeight)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.15), radius: 12, x: 0, y: 4)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .strokeBorder(Color.primary.opacity(0.1), lineWidth: 1)
        )
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.2)) {
                isHovering = hovering
            }
        }
        .gesture(
            DragGesture()
                .onChanged { value in
                    dragOffset = value.translation
                }
                .onEnded { value in
                    // 保存位置（未来实现）
                    dragOffset = .zero
                }
        )
        .offset(dragOffset)
    }

    // MARK: - 展开工具栏

    private var expandedToolbar: some View {
        HStack(spacing: 12) {
            // 左侧：场景检测
            sceneIndicator

            Divider()
                .frame(height: 36)

            // 中间：Pattern 快捷按钮
            patternButtons

            Spacer()

            // 右侧：信任等级 + 最小化按钮
            HStack(spacing: 8) {
                trustLevelIndicator

                Button(action: {
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                        isExpanded.toggle()
                    }
                }) {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundStyle(.secondary)
                        .frame(width: 24, height: 24)
                        .background(Color.secondary.opacity(0.1))
                        .clipShape(Circle())
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 12)
        .frame(height: toolbarHeight)
    }

    // MARK: - 紧凑工具栏

    private var compactToolbar: some View {
        Button(action: {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                isExpanded.toggle()
            }
        }) {
            VStack(spacing: 4) {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 20))
                    .foregroundStyle(.blue)

                if let scene = appState.detectedScene {
                    Image(systemName: scene.icon)
                        .font(.system(size: 10))
                        .foregroundStyle(.secondary)
                }
            }
            .frame(width: compactWidth, height: toolbarHeight)
        }
        .buttonStyle(.plain)
    }

    // MARK: - 场景指示器

    private var sceneIndicator: some View {
        HStack(spacing: 6) {
            // 场景图标
            Image(systemName: appState.detectedScene?.icon ?? DetectedScene.unknown.icon)
                .font(.system(size: 16))
                .foregroundStyle(sceneColor)
                .frame(width: 28, height: 28)
                .background(sceneColor.opacity(0.15))
                .clipShape(Circle())

            // 场景文本（悬停时显示）
            if isHovering {
                VStack(alignment: .leading, spacing: 2) {
                    Text(appState.detectedScene?.rawValue ?? "未知")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(.primary)

                    Text("\(Int(appState.sceneConfidence * 100))% 置信度")
                        .font(.system(size: 9))
                        .foregroundStyle(.secondary)
                }
                .transition(.opacity.combined(with: .scale(scale: 0.95)))
            }
        }
    }

    // MARK: - Pattern 快捷按钮

    private var patternButtons: some View {
        HStack(spacing: 4) {
            PatternButton(
                icon: "doc.text.fill",
                patternId: "summarize",
                tooltip: "总结",
                isProcessing: appState.isProcessingPattern && appState.currentPatternId == "summarize"
            )

            PatternButton(
                icon: "textformat.123",
                patternId: "extract",
                tooltip: "提取",
                isProcessing: appState.isProcessingPattern && appState.currentPatternId == "extract"
            )

            PatternButton(
                icon: "globe",
                patternId: "translate",
                tooltip: "翻译",
                isProcessing: appState.isProcessingPattern && appState.currentPatternId == "translate"
            )

            PatternButton(
                icon: "arrow.left.arrow.right",
                patternId: "format",
                tooltip: "格式",
                isProcessing: appState.isProcessingPattern && appState.currentPatternId == "format"
            )

            PatternButton(
                icon: "magnifyingglass",
                patternId: "search",
                tooltip: "搜索",
                isProcessing: appState.isProcessingPattern && appState.currentPatternId == "search"
            )
        }
    }

    // MARK: - 信任等级指示器

    private var trustLevelIndicator: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(appState.currentTrustLevel.color)
                .frame(width: 8, height: 8)

            if isHovering {
                Text(appState.currentTrustLevel.displayName)
                    .font(.system(size: 10, weight: .medium))
                    .foregroundStyle(.secondary)
                    .transition(.opacity.combined(with: .scale(scale: 0.95)))
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 6)
        .background(appState.currentTrustLevel.color.opacity(0.1))
        .clipShape(Capsule())
    }

    // MARK: - 辅助计算属性

    private var sceneColor: Color {
        guard let scene = appState.detectedScene else { return .gray }

        switch scene {
        case .browsing: return .blue
        case .coding: return .purple
        case .writing: return .green
        case .reading: return .orange
        case .meeting: return .red
        case .unknown: return .gray
        }
    }
}

// MARK: - Pattern 按钮组件

struct PatternButton: View {
    @Environment(AppState.self) private var appState

    let icon: String
    let patternId: String
    let tooltip: String
    let isProcessing: Bool

    @State private var isHovering = false

    var body: some View {
        Button(action: {
            Task {
                _ = await appState.executePattern(patternId, text: "示例文本")
            }
        }) {
            ZStack {
                if isProcessing {
                    ProgressView()
                        .scaleEffect(0.6)
                } else {
                    Image(systemName: icon)
                        .font(.system(size: 14))
                }
            }
            .frame(width: 32, height: 32)
            .background(isHovering ? Color.blue.opacity(0.1) : Color.clear)
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(.plain)
        .disabled(isProcessing || appState.isProcessingPattern)
        .help(tooltip)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

// MARK: - 预览

#Preview("展开状态") {
    FloatingToolbarView()
        .environment(AppState())
        .frame(width: 400, height: 200)
}

#Preview("紧凑状态") {
    let appState = AppState()

    return FloatingToolbarView()
        .environment(appState)
        .frame(width: 200, height: 200)
        .onAppear {
            appState.detectedScene = .coding
            appState.sceneConfidence = 0.89
        }
}

#Preview("处理中状态") {
    let appState = AppState()

    return FloatingToolbarView()
        .environment(appState)
        .frame(width: 400, height: 200)
        .onAppear {
            appState.detectedScene = .writing
            appState.sceneConfidence = 0.95
            appState.currentTrustLevel = .R1
            appState.isProcessingPattern = true
            appState.currentPatternId = "summarize"
        }
}
