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

// MacCortex 主视图
// Phase 0.5 - 基础设施
// Phase 2 Day 1 - Observation Framework 升级
// 创建时间：2026-01-20
// 更新时间：2026-01-21

import SwiftUI

struct ContentView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        Group {
            if appState.isFirstRun {
                // Phase 0.5 Day 8: 首次启动引导
                FirstRunView()
            } else {
                // 主界面（Phase 2 开发）
                MainView()
            }
        }
    }
}

struct MainView: View {
    @Environment(AppState.self) private var appState
    @State private var showSettings = false

    var body: some View {
        NavigationView {
            VStack(spacing: 30) {
                // 顶部标题区
                VStack(spacing: 10) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 80))
                        .foregroundColor(.blue)

                    Text("MacCortex")
                        .font(.largeTitle)
                        .fontWeight(.bold)

                    Text("Phase 2 - 开发中")
                        .font(.caption)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 4)
                        .background(Color.blue.opacity(0.2))
                        .foregroundColor(.blue)
                        .cornerRadius(4)
                }

                Spacer()

                // 权限状态卡片
                VStack(alignment: .leading, spacing: 15) {
                    HStack {
                        Image(systemName: "lock.shield")
                            .foregroundColor(.blue)
                        Text("权限状态")
                            .font(.headline)
                    }

                    PermissionStatusRow(
                        icon: "folder.fill",
                        name: "Full Disk Access",
                        isGranted: appState.hasFullDiskAccess,
                        isRequired: true
                    )

                    PermissionStatusRow(
                        icon: "cursorarrow.rays",
                        name: "Accessibility",
                        isGranted: appState.hasAccessibilityPermission,
                        isRequired: false
                    )

                    // 权限管理按钮
                    Button(action: {
                        showSettings = true
                    }) {
                        HStack {
                            Image(systemName: "gear")
                            Text("管理权限")
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(Color.blue.opacity(0.1))
                        .foregroundColor(.blue)
                        .cornerRadius(8)
                    }
                }
                .padding()
                .background(Color.secondary.opacity(0.1))
                .cornerRadius(10)

                // Phase 状态
                VStack(alignment: .leading, spacing: 15) {
                    HStack {
                        Image(systemName: "list.bullet.clipboard")
                            .foregroundColor(.blue)
                        Text("开发进度")
                            .font(.headline)
                    }

                    StatusRow(icon: "checkmark.circle.fill",
                             text: "Phase 0.5: 签名与公证",
                             status: .completed)

                    StatusRow(icon: "checkmark.circle.fill",
                             text: "Phase 1: Python Backend",
                             status: .completed)

                    StatusRow(icon: "checkmark.circle.fill",
                             text: "Phase 1.5: 安全强化",
                             status: .completed)

                    StatusRow(icon: "circle.fill",
                             text: "Phase 2 Week 1: SwiftUI 架构",
                             status: .inProgress)

                    StatusRow(icon: "circle",
                             text: "Phase 2 Week 2: 浮动工具栏",
                             status: .pending)
                }
                .padding()
                .background(Color.secondary.opacity(0.1))
                .cornerRadius(10)

                // Phase 2: 功能测试区
                VStack(alignment: .leading, spacing: 15) {
                    HStack {
                        Image(systemName: "testtube.2")
                            .foregroundColor(.blue)
                        Text("Phase 2 功能测试")
                            .font(.headline)
                    }

                    // 浮动工具栏开关
                    Toggle("显示浮动工具栏", isOn: Binding(
                        get: { appState.showFloatingToolbar },
                        set: { appState.showFloatingToolbar = $0 }
                    ))
                    .toggleStyle(.switch)

                    // 场景检测测试
                    VStack(alignment: .leading, spacing: 8) {
                        Text("场景检测测试")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)

                        HStack(spacing: 8) {
                            ForEach(DetectedScene.allCases.prefix(4), id: \.self) { scene in
                                Button(action: {
                                    appState.updateDetectedScene(scene, confidence: Double.random(in: 0.75...0.95))
                                }) {
                                    VStack(spacing: 4) {
                                        Image(systemName: scene.icon)
                                            .font(.system(size: 16))
                                        Text(scene.rawValue)
                                            .font(.system(size: 9))
                                    }
                                    .frame(width: 60, height: 50)
                                    .background(appState.detectedScene == scene ? Color.blue.opacity(0.2) : Color.secondary.opacity(0.1))
                                    .cornerRadius(8)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // 信任等级测试
                    VStack(alignment: .leading, spacing: 8) {
                        Text("信任等级切换")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)

                        HStack(spacing: 8) {
                            ForEach(TrustLevel.allCases, id: \.self) { level in
                                Button(action: {
                                    appState.setTrustLevel(level)
                                }) {
                                    Text(level.displayName)
                                        .font(.system(size: 10))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(appState.currentTrustLevel == level ? level.color.opacity(0.3) : Color.secondary.opacity(0.1))
                                        .foregroundColor(appState.currentTrustLevel == level ? level.color : .secondary)
                                        .cornerRadius(6)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                }
                .padding()
                .background(Color.blue.opacity(0.05))
                .cornerRadius(10)

                Spacer()
            }
            .padding()
            .navigationTitle("MacCortex")
            .overlay(
                // 浮动工具栏叠加层
                Group {
                    if appState.showFloatingToolbar {
                        FloatingToolbarView()
                            .position(x: 200, y: 100)
                            .transition(.scale.combined(with: .opacity))
                    }
                }
            )
            .toolbar {
                ToolbarItem(placement: .navigation) {
                    Button(action: {
                        showSettings = true
                    }) {
                        Image(systemName: "gear")
                    }
                }
            }
        }
        .sheet(isPresented: $showSettings) {
            SettingsView()
                .environment(appState)
        }
    }
}

struct PermissionStatusRow: View {
    let icon: String
    let name: String
    let isGranted: Bool
    let isRequired: Bool

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(isGranted ? .green : .orange)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(name)
                        .font(.subheadline)

                    if isRequired {
                        Text("必需")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 1)
                            .background(Color.red.opacity(0.2))
                            .foregroundColor(.red)
                            .cornerRadius(3)
                    }
                }

                Text(isGranted ? "已授予" : "未授予")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Image(systemName: isGranted ? "checkmark.circle.fill" : "xmark.circle")
                .foregroundColor(isGranted ? .green : .orange)
        }
    }
}

struct StatusRow: View {
    let icon: String
    let text: String
    let status: Status

    enum Status {
        case completed, pending, inProgress

        var color: Color {
            switch self {
            case .completed: return .green
            case .pending: return .gray
            case .inProgress: return .blue
            }
        }
    }

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(status.color)
            Text(text)
            Spacer()
        }
    }
}

#Preview {
    ContentView()
        .environment(AppState())
}
