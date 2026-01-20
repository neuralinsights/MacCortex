// MacCortex 主应用入口
// Phase 0.5
// 创建时间：2026-01-20
// 更新时间：2026-01-20 (Day 6-7: 集成 PermissionsKit)

import SwiftUI
import PermissionsKit

@main
struct MacCortexApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .frame(minWidth: 800, minHeight: 600)
        }
        .commands {
            CommandGroup(replacing: .appInfo) {
                Button("关于 MacCortex") {
                    // 显示关于窗口
                }
            }
        }
    }
}

// 应用状态管理
class AppState: ObservableObject {
    @Published var hasFullDiskAccess: Bool = false
    @Published var isFirstRun: Bool = true

    init() {
        checkPermissions()
    }

    func checkPermissions() {
        // Phase 0.5 Day 6-7: 集成 FullDiskAccessManager
        hasFullDiskAccess = FullDiskAccessManager.shared.hasFullDiskAccess

        // 检查是否首次运行
        let defaults = UserDefaults.standard
        isFirstRun = !defaults.bool(forKey: "HasLaunchedBefore")

        if isFirstRun {
            defaults.set(true, forKey: "HasLaunchedBefore")
        }
    }

    /// 请求 Full Disk Access 权限
    func requestFullDiskAccess() {
        FullDiskAccessManager.shared.requestFullDiskAccess(timeout: 60, interval: 2) { [weak self] granted in
            DispatchQueue.main.async {
                self?.hasFullDiskAccess = granted
                if granted {
                    self?.isFirstRun = false
                }
            }
        }
    }
}
