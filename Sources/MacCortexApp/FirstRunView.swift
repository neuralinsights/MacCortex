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
    @State private var showPermissionInfo = false

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

                Text("您的 macOS 智能助手，助力高效工作")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            // 权限说明信息框
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: "info.circle.fill")
                        .foregroundColor(.blue)
                    Text("为什么需要这些权限？")
                        .font(.headline)
                }

                Text("MacCortex 使用 AI 技术帮您组织文件、总结笔记和自动化工作流。为了提供这些功能，需要您授予以下权限：")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding()
            .background(Color.blue.opacity(0.1))
            .cornerRadius(10)

            Divider()

            // 权限说明
            VStack(alignment: .leading, spacing: 20) {
                PermissionCard(
                    icon: "folder.fill",
                    title: "Full Disk Access（完全磁盘访问）",
                    description: "读取 Notes、文件和文档，帮您智能整理信息。MacCortex 仅读取您的数据，所有处理在本地完成，绝不上传到云端。",
                    examples: ["• 读取 Apple Notes 笔记", "• 扫描 Documents 文件夹", "• 访问 Downloads 下载内容"],
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
                    description: "控制其他应用，实现工作流自动化。此权限为可选，仅在需要自动化功能（如批量文件处理、应用间数据同步）时才需要授予。",
                    examples: ["• 自动整理文件到文件夹", "• 批量重命名文档", "• 跨应用复制粘贴数据"],
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
                    // 未完成必需权限授予时的提示
                    VStack(spacing: 8) {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.orange)
                            Text("请授予 Full Disk Access 权限")
                                .font(.subheadline)
                                .fontWeight(.medium)
                        }

                        Text("此权限是 MacCortex 核心功能所必需的")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding()
                    .background(Color.orange.opacity(0.1))
                    .cornerRadius(10)
                }

                Button(action: {
                    showDegradedExperienceWarning()
                }) {
                    Text("稍后授权")
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal)
        }
        .padding(40)
        .frame(maxWidth: 600)
        .alert("功能受限提醒", isPresented: $showPermissionInfo) {
            Button("返回授权", role: .cancel) {}
            Button("仍然继续") {
                appState.isFirstRun = false
            }
        } message: {
            Text(degradedExperienceMessage)
        }
    }

    /// 降级体验警告信息
    private var degradedExperienceMessage: String {
        if !appState.hasFullDiskAccess {
            return """
            未授予 Full Disk Access 权限，MacCortex 将无法：

            • 读取和整理您的笔记（Notes）
            • 扫描和组织文档（Documents）
            • 访问下载的文件（Downloads）

            这将严重影响核心功能的使用。建议先授予权限再继续。
            """
        } else if !appState.hasAccessibilityPermission {
            return """
            未授予 Accessibility 权限，MacCortex 将无法：

            • 自动整理文件
            • 批量处理文档
            • 跨应用同步数据

            您可以稍后在设置中授予此权限。
            """
        }
        return "某些功能可能受限。"
    }

    /// 显示降级体验警告
    private func showDegradedExperienceWarning() {
        if appState.hasAllRequiredPermissions {
            // 必需权限已授予，直接进入
            appState.isFirstRun = false
        } else {
            // 显示警告
            showPermissionInfo = true
        }
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
    let examples: [String]
    let isRequired: Bool
    let isGranted: Bool
    let isRequesting: Bool
    let onRequest: () -> Void
    @State private var showExamples = false

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

                    // 使用示例（可展开）
                    if !examples.isEmpty {
                        Button(action: {
                            withAnimation {
                                showExamples.toggle()
                            }
                        }) {
                            HStack(spacing: 4) {
                                Image(systemName: showExamples ? "chevron.down" : "chevron.right")
                                    .font(.caption)
                                Text(showExamples ? "收起示例" : "查看使用示例")
                                    .font(.caption)
                            }
                            .foregroundColor(.blue)
                        }
                        .buttonStyle(.plain)
                        .padding(.top, 4)

                        if showExamples {
                            VStack(alignment: .leading, spacing: 4) {
                                ForEach(examples, id: \.self) { example in
                                    Text(example)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                            .padding(.top, 4)
                            .transition(.opacity)
                        }
                    }
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
