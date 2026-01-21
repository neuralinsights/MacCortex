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

// MacCortex 设置界面
// Phase 1 - Week 1 Day 4
// Phase 2 Day 1 - Observation Framework 升级
// 创建时间：2026-01-20
// 更新时间：2026-01-21

import SwiftUI
import PermissionsKit

struct SettingsView: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) var dismiss
    @State private var isRequestingFDA = false
    @State private var isRequestingAccessibility = false

    var body: some View {
        NavigationView {
            Form {
                // 权限管理区
                Section(header: Text("权限管理")) {
                    // Full Disk Access
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text("Full Disk Access")
                                    .font(.headline)

                                if appState.hasFullDiskAccess {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundColor(.green)
                                } else {
                                    Image(systemName: "exclamationmark.circle")
                                        .foregroundColor(.orange)
                                }
                            }

                            Text(appState.hasFullDiskAccess ? "已授予" : "未授予 - 核心功能受限")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        Spacer()

                        if !appState.hasFullDiskAccess {
                            Button(action: {
                                requestFullDiskAccess()
                            }) {
                                if isRequestingFDA {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                } else {
                                    Text("授权")
                                }
                            }
                            .disabled(isRequestingFDA)
                        }
                    }

                    // Accessibility
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text("Accessibility")
                                    .font(.headline)

                                if appState.hasAccessibilityPermission {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundColor(.green)
                                } else {
                                    Image(systemName: "minus.circle")
                                        .foregroundColor(.gray)
                                }
                            }

                            Text(appState.hasAccessibilityPermission ? "已授予" : "未授予 - 自动化功能不可用")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        Spacer()

                        if !appState.hasAccessibilityPermission {
                            Button(action: {
                                requestAccessibilityPermission()
                            }) {
                                if isRequestingAccessibility {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                } else {
                                    Text("授权")
                                }
                            }
                            .disabled(isRequestingAccessibility)
                        }
                    }
                }

                // 应用信息区
                Section(header: Text("应用信息")) {
                    HStack {
                        Text("版本")
                        Spacer()
                        Text("0.5.0 (Phase 1)")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("构建")
                        Spacer()
                        Text("Phase 1 Week 1 Day 4")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("开发状态")
                        Spacer()
                        Text("开发中")
                            .foregroundColor(.orange)
                    }
                }

                // 关于区
                Section(header: Text("关于")) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("MacCortex")
                            .font(.headline)

                        Text("下一代 macOS 个人智能基础设施")
                            .font(.subheadline)
                            .foregroundColor(.secondary)

                        Text("使用 AI 技术帮您组织文件、总结笔记和自动化工作流。所有处理在本地完成，保护您的隐私。")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .padding(.vertical, 4)
                }

                // 重置区
                Section(header: Text("高级")) {
                    Button(action: {
                        resetFirstRunFlag()
                    }) {
                        HStack {
                            Image(systemName: "arrow.clockwise")
                            Text("重新显示首次启动引导")
                        }
                        .foregroundColor(.blue)
                    }

                    Button(action: {
                        openSystemSettings()
                    }) {
                        HStack {
                            Image(systemName: "gear")
                            Text("打开系统设置")
                        }
                        .foregroundColor(.blue)
                    }
                }
            }
            .formStyle(.grouped)
            .navigationTitle("设置")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("关闭") {
                        dismiss()
                    }
                }
            }
        }
    }

    // MARK: - Private Methods

    private func requestFullDiskAccess() {
        isRequestingFDA = true
        FullDiskAccessManager.shared.openSystemPreferences()

        FullDiskAccessManager.shared.requestFullDiskAccess(timeout: 60, interval: 2) { granted in
            DispatchQueue.main.async {
                self.isRequestingFDA = false
                self.appState.hasFullDiskAccess = granted
            }
        }
    }

    private func requestAccessibilityPermission() {
        isRequestingAccessibility = true
        AccessibilityManager.shared.openSystemPreferences()

        AccessibilityManager.shared.requestAccessibilityPermission(timeout: 60, interval: 2) { granted in
            DispatchQueue.main.async {
                self.isRequestingAccessibility = false
                self.appState.hasAccessibilityPermission = granted
            }
        }
    }

    private func resetFirstRunFlag() {
        UserDefaults.standard.set(false, forKey: "HasLaunchedBefore")
        appState.isFirstRun = true
        dismiss()
    }

    private func openSystemSettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension") {
            NSWorkspace.shared.open(url)
        }
    }
}

#Preview {
    SettingsView()
        .environment(AppState())
}
