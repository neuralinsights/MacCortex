// MacCortex 首次启动引导界面
// Phase 0.5 - Day 8
// 创建时间：2026-01-20

import SwiftUI

struct FirstRunView: View {
    @EnvironmentObject var appState: AppState
    @State private var currentStep = 0

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
                    isRequired: true
                )

                PermissionCard(
                    icon: "app.badge",
                    title: "AppleScript/Automation（自动化）",
                    description: "允许 MacCortex 控制其他应用以自动化您的工作流程。",
                    isRequired: false
                )
            }

            Spacer()

            // 操作按钮
            VStack(spacing: 15) {
                Button(action: {
                    openSystemPreferences()
                }) {
                    HStack {
                        Image(systemName: "lock.shield")
                        Text("打开系统设置授权")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
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

    private func openSystemPreferences() {
        // 打开系统设置的 Full Disk Access 页面
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles") {
            NSWorkspace.shared.open(url)
        }

        // 启动轮询检测（Phase 0.5 Day 6-7 实现）
        // FullDiskAccessManager.shared.requestFullDiskAccess { granted in
        //     if granted {
        //         appState.hasFullDiskAccess = true
        //         appState.isFirstRun = false
        //     }
        // }
    }
}

struct PermissionCard: View {
    let icon: String
    let title: String
    let description: String
    let isRequired: Bool

    var body: some View {
        HStack(alignment: .top, spacing: 15) {
            Image(systemName: icon)
                .font(.system(size: 30))
                .foregroundColor(.blue)
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
                }

                Text(description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.1))
        .cornerRadius(10)
    }
}

#Preview {
    FirstRunView()
        .environmentObject(AppState())
}
