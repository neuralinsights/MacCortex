// MacCortex 主视图
// Phase 0.5
// 创建时间：2026-01-20

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        Group {
            if appState.isFirstRun {
                // Phase 0.5 Day 8: 首次启动引导
                FirstRunView()
            } else {
                // 主界面（Phase 1+ 开发）
                MainView()
            }
        }
    }
}

struct MainView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 80))
                .foregroundColor(.blue)

            Text("MacCortex")
                .font(.largeTitle)
                .fontWeight(.bold)

            Text("下一代 macOS 个人智能基础设施")
                .font(.headline)
                .foregroundColor(.secondary)

            Text("Phase 0.5 - 基础设施建设中")
                .font(.caption)
                .foregroundColor(.orange)

            Spacer()

            VStack(alignment: .leading, spacing: 10) {
                StatusRow(icon: "checkmark.circle.fill",
                         text: "项目目录结构",
                         status: .completed)

                StatusRow(icon: "checkmark.circle.fill",
                         text: "Git 仓库初始化",
                         status: .completed)

                StatusRow(icon: "circle",
                         text: "Developer ID 证书",
                         status: .pending)

                StatusRow(icon: "circle",
                         text: "代码签名配置",
                         status: .pending)

                StatusRow(icon: "circle",
                         text: "公证自动化",
                         status: .pending)
            }
            .padding()
            .background(Color.secondary.opacity(0.1))
            .cornerRadius(10)

            Spacer()
        }
        .padding()
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
        .environmentObject(AppState())
}
