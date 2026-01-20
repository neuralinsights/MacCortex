// MacCortex 首次启动引导界面
// Phase 0.5 - Day 8
// 创建时间：2026-01-20
// 更新时间：2026-01-20 (Day 6-7: 集成 PermissionsKit)

import SwiftUI
import PermissionsKit

struct FirstRunView: View {
    @EnvironmentObject var appState: AppState
    @State private var currentStep = 0
    @State private var isRequestingFDA = false
    @State private var isRequestingAccessibility = false

    var body: some View {
        VStack(spacing: 30) {
            // 标题
            VStack(spacing: 10) {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 60))
                    .foregroundColor(.blue)

                Text("欢迎使用 MacCortex")
                    .font(.largeTitle)
                    .fontWeight(.bold)

                Text("下一代 macOS 个人智能基础设施")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            Divider()

            // 权限说明
            VStack(alignment: .leading, spacing: 20) {
                PermissionCard(
                    icon: "folder.fill",
                    title: "Full Disk Access（完全磁盘访问）",
                    description: "MacCortex 需要此权限来读取和组织您的文件、笔记和文档。这是核心功能所必需的。",
                    isRequired: true,
                    isGranted: appState.hasFullDiskAccess,
                    isRequesting: isRequestingFDA,
                    onRequest: {
                        requestFullDiskAccess()
                    }
                )

                PermissionCard(
                    icon: "cursorarrow.rays",
                    title: "Accessibility（辅助功能）",
                    description: "允许 MacCortex 控制其他应用以自动化您的工作流程。此权限为可选，仅在需要自动化功能时才需要。",
                    isRequired: false,
                    isGranted: appState.hasAccessibilityPermission,
                    isRequesting: isRequestingAccessibility,
                    onRequest: {
                        requestAccessibilityPermission()
                    }
                )
            }

            Spacer()

            // 操作按钮
            VStack(spacing: 15) {
                if appState.hasAllRequiredPermissions {
                    Button(action: {
                        appState.isFirstRun = false
                    }) {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                            Text("开始使用 MacCortex")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                } else {
                    Text("请授予 Full Disk Access 权限以继续")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.bottom, 5)
                }

                Button("稍后授权") {
                    appState.isFirstRun = false
                }
                .foregroundColor(.secondary)
            }
            .padding(.horizontal)
        }
        .padding(40)
        .frame(maxWidth: 600)
    }

    private func requestFullDiskAccess() {
        isRequestingFDA = true

        // Phase 0.5 Day 6-7: 使用 PermissionsKit
        FullDiskAccessManager.shared.openSystemPreferences()

        // 启动轮询检测权限变化
        FullDiskAccessManager.shared.requestFullDiskAccess(timeout: 60, interval: 2) { granted in
            DispatchQueue.main.async {
                self.isRequestingFDA = false
                self.appState.hasFullDiskAccess = granted
            }
        }
    }

    private func requestAccessibilityPermission() {
        isRequestingAccessibility = true

        // Phase 1 Week 1 Day 1-2: 使用 AccessibilityManager
        AccessibilityManager.shared.openSystemPreferences()

        // 启动轮询检测权限变化
        AccessibilityManager.shared.requestAccessibilityPermission(timeout: 60, interval: 2) { granted in
            DispatchQueue.main.async {
                self.isRequestingAccessibility = false
                self.appState.hasAccessibilityPermission = granted
            }
        }
    }
}

struct PermissionCard: View {
    let icon: String
    let title: String
    let description: String
    let isRequired: Bool
    let isGranted: Bool
    let isRequesting: Bool
    let onRequest: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 15) {
                Image(systemName: icon)
                    .font(.system(size: 30))
                    .foregroundColor(isGranted ? .green : .blue)
                    .frame(width: 40)

                VStack(alignment: .leading, spacing: 5) {
                    HStack {
                        Text(title)
                            .font(.headline)

                        if isRequired {
                            Text("必需")
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(Color.red.opacity(0.2))
                                .foregroundColor(.red)
                                .cornerRadius(4)
                        }

                        Spacer()

                        // 权限状态指示器
                        if isGranted {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                        } else if isRequesting {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "exclamationmark.circle")
                                .foregroundColor(.orange)
                        }
                    }

                    Text(description)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }

            // 请求按钮
            if !isGranted {
                Button(action: onRequest) {
                    HStack {
                        if isRequesting {
                            ProgressView()
                                .scaleEffect(0.8)
                            Text("正在等待授权...")
                        } else {
                            Image(systemName: "arrow.right.circle.fill")
                            Text("授予权限")
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(isRequesting ? Color.gray.opacity(0.3) : Color.blue.opacity(0.1))
                    .foregroundColor(isRequesting ? .secondary : .blue)
                    .cornerRadius(8)
                }
                .disabled(isRequesting)
            }
        }
        .padding()
        .background(isGranted ? Color.green.opacity(0.1) : Color.secondary.opacity(0.1))
        .cornerRadius(10)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(isGranted ? Color.green.opacity(0.3) : Color.clear, lineWidth: 2)
        )
    }
}

#Preview {
    FirstRunView()
        .environmentObject(AppState())
}
