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

// MCP 服务器列表 UI 组件
// Phase 2 Week 3 Day 11-12: MCP 工具动态加载
// 创建时间：2026-01-21

import SwiftUI

/// MCP 服务器列表视图
struct MCPServerListView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var servers: [MCPServer] = []
    @State private var isLoading = true
    @State private var showAddServer = false
    @State private var errorMessage: String? = nil

    var body: some View {
        VStack(spacing: 0) {
            // 头部
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("MCP 服务器")
                        .font(.title2)
                        .fontWeight(.bold)

                    Text("\(servers.count) 个服务器")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                // 刷新按钮
                Button(action: { loadServers() }) {
                    Label("刷新", systemImage: "arrow.clockwise")
                        .font(.system(size: 11))
                }
                .buttonStyle(.borderless)

                // 添加服务器按钮
                Button(action: { showAddServer = true }) {
                    Label("添加服务器", systemImage: "plus.circle.fill")
                }
                .buttonStyle(.borderedProminent)

                // 关闭按钮
                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
                .help("关闭")
            }
            .padding()

            Divider()

            // 服务器列表
            if isLoading {
                Spacer()
                ProgressView()
                    .scaleEffect(1.5)
                Spacer()
            } else if servers.isEmpty {
                Spacer()
                VStack(spacing: 12) {
                    Image(systemName: "server.rack")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)

                    Text("暂无 MCP 服务器")
                        .font(.headline)
                        .foregroundColor(.secondary)

                    Text("点击「添加服务器」开始")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                Spacer()
            } else {
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(servers) { server in
                            MCPServerRow(
                                server: server,
                                onUnload: {
                                    unloadServer(server.id)
                                }
                            )
                        }
                    }
                    .padding()
                }
            }

            // 错误提示
            if let errorMessage = errorMessage {
                Divider()
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundColor(.red)
                    Spacer()
                    Button("关闭") {
                        self.errorMessage = nil
                    }
                    .buttonStyle(.borderless)
                }
                .padding()
                .background(Color.red.opacity(0.1))
            }
        }
        .frame(width: 600, height: 500)
        .background(Color(NSColor.windowBackgroundColor))
        .onAppear { loadServers() }
        .sheet(isPresented: $showAddServer) {
            AddMCPServerSheet(onAdd: { url in
                loadServer(url)
                showAddServer = false
            })
        }
    }

    // MARK: - 私有方法

    /// 加载服务器列表
    private func loadServers() {
        Task {
            isLoading = true
            let allServers = await MCPManager.shared.getAllServers()
            await MainActor.run {
                servers = allServers
                isLoading = false
            }
        }
    }

    /// 加载单个服务器
    private func loadServer(_ url: URL) {
        Task {
            do {
                let _ = try await MCPManager.shared.loadServer(url: url)
                loadServers()
            } catch {
                await MainActor.run {
                    errorMessage = "加载服务器失败: \(error.localizedDescription)"
                }
            }
        }
    }

    /// 卸载服务器
    private func unloadServer(_ id: UUID) {
        Task {
            await MCPManager.shared.unloadServer(id: id)
            loadServers()
        }
    }
}

/// MCP 服务器行
struct MCPServerRow: View {
    let server: MCPServer
    let onUnload: () -> Void

    @State private var isHovering = false

    var body: some View {
        HStack(spacing: 12) {
            // 状态指示器
            Circle()
                .fill(server.isResponding ? Color.green : (server.isActive ? Color.yellow : Color.red))
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 4) {
                // 服务器名称
                Text(server.displayName)
                    .font(.system(size: 13, weight: .medium))

                // 服务器路径
                Text(server.url.path)
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)

                // 工具数量
                Text("\(server.toolCount) 个工具")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
            }

            Spacer()

            // 信任等级徽章
            RiskBadge(riskLevel: server.trustLevel, compact: false)

            // 卸载按钮
            if isHovering || !server.isActive {
                Button(action: onUnload) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.red)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(isHovering ? Color.secondary.opacity(0.05) : Color.clear)
        .cornerRadius(8)
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

/// 添加 MCP 服务器对话框
struct AddMCPServerSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var serverPath: String = "/usr/local/bin/mcp-server-filesystem"
    @State private var errorMessage: String? = nil

    let onAdd: (URL) -> Void

    var body: some View {
        VStack(spacing: 20) {
            // 头部
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("添加 MCP 服务器")
                        .font(.title2)
                        .fontWeight(.bold)

                    Text("请输入服务器可执行文件路径")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }

            Divider()

            // 表单
            VStack(alignment: .leading, spacing: 12) {
                Text("服务器路径")
                    .font(.headline)

                HStack(spacing: 8) {
                    TextField("例如: /usr/local/bin/mcp-server-filesystem", text: $serverPath)
                        .textFieldStyle(.plain)
                        .font(.system(size: 13, design: .monospaced))
                        .padding(8)
                        .background(Color(NSColor.textBackgroundColor))
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                        )

                    Button(action: {
                        let panel = NSOpenPanel()
                        panel.canChooseFiles = true
                        panel.canChooseDirectories = false
                        panel.allowsMultipleSelection = false
                        panel.directoryURL = URL(fileURLWithPath: "/usr/local/bin")
                        panel.prompt = "选择 MCP 服务器"

                        if panel.runModal() == .OK, let url = panel.url {
                            serverPath = url.path
                        }
                    }) {
                        Image(systemName: "folder")
                            .font(.system(size: 14))
                    }
                    .buttonStyle(.bordered)
                    .help("浏览文件")
                }

                // 白名单提示
                HStack(spacing: 8) {
                    Image(systemName: "info.circle.fill")
                        .foregroundColor(.blue)
                    Text("服务器必须在白名单中（Resources/Config/mcp_whitelist.json）")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            // 常用服务器快捷按钮
            VStack(alignment: .leading, spacing: 8) {
                Text("常用服务器")
                    .font(.headline)

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                    QuickServerButton(
                        name: "🧪 测试服务器",
                        icon: "testtube.2",
                        path: "/tmp/mcp-test-server",
                        onSelect: { serverPath = $0 }
                    )

                    QuickServerButton(
                        name: "文件系统",
                        icon: "folder.fill",
                        path: "/usr/local/bin/mcp-server-filesystem",
                        onSelect: { serverPath = $0 }
                    )

                    QuickServerButton(
                        name: "SQLite",
                        icon: "cylinder.fill",
                        path: "/usr/local/bin/mcp-server-sqlite",
                        onSelect: { serverPath = $0 }
                    )

                    QuickServerButton(
                        name: "搜索",
                        icon: "magnifyingglass",
                        path: "/usr/local/bin/mcp-server-brave-search",
                        onSelect: { serverPath = $0 }
                    )
                }
            }

            // 错误提示
            if let errorMessage = errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundColor(.red)
                    Spacer()
                }
                .padding()
                .background(Color.red.opacity(0.1))
                .cornerRadius(8)
            }

            Spacer()

            // 底部按钮
            HStack {
                Button("取消") {
                    dismiss()
                }
                .keyboardShortcut(.cancelAction)

                Spacer()

                Button("添加") {
                    addServer()
                }
                .keyboardShortcut(.defaultAction)
                .disabled(serverPath.isEmpty)
            }
        }
        .padding(24)
        .frame(width: 500, height: 450)
        .background(Color(NSColor.windowBackgroundColor))
    }

    // MARK: - 私有方法

    private func addServer() {
        // 使用 fileURLWithPath 确保正确的 file:/// URL 格式
        let url = URL(fileURLWithPath: serverPath)

        print("🔍 [DEBUG] 尝试添加服务器：")
        print("   路径: \(serverPath)")
        print("   URL: \(url.absoluteString)")

        // 检查文件是否存在
        guard FileManager.default.fileExists(atPath: serverPath) else {
            errorMessage = "服务器文件不存在"
            print("   ❌ 文件不存在")
            return
        }

        // 检查文件是否可执行
        guard FileManager.default.isExecutableFile(atPath: serverPath) else {
            errorMessage = "服务器文件不可执行"
            print("   ❌ 文件不可执行")
            return
        }

        print("   ✅ 文件检查通过，调用 onAdd")
        onAdd(url)
    }
}

/// 快捷服务器按钮
private struct QuickServerButton: View {
    let name: String
    let icon: String
    let path: String
    let onSelect: (String) -> Void

    var body: some View {
        Button(action: { onSelect(path) }) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                Text(name)
                    .font(.system(size: 12))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
        }
        .buttonStyle(.bordered)
    }
}

// MARK: - 预览

#Preview("MCP Server List") {
    MCPServerListView()
}

#Preview("Add MCP Server Sheet") {
    AddMCPServerSheet(onAdd: { _ in })
}
