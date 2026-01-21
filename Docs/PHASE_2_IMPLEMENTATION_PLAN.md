# MacCortex Phase 2 实施计划

**版本**: v1.1（Week 1 完成更新）
**创建时间**: 2026-01-21
**最后更新**: 2026-01-21
**状态**: Week 1 已完成 ✅，Week 2 进行中
**前置条件**: Phase 1.5 已完成 ✅

---

## 执行摘要

Phase 2 是 MacCortex 的 **Desktop GUI + 高级功能开发阶段**，目标是构建一个现代化的 macOS 原生应用，提供"隐形 AI"用户体验，同时复用 Phase 1.5 的安全基础设施。

**核心目标**:
1. ✅ Desktop GUI（SwiftUI + Observation Framework）
2. ✅ 浮动工具栏（Apple Intelligence 风格）
3. ✅ 智能场景识别（自动检测用户意图）
4. ✅ 渐进式信任机制（Risk Level 0-3）
5. ✅ 一键撤销（7 天内可回滚）
6. ✅ Phase 1.5 安全集成（审计日志、速率限制等）

**工期**: 3 周（15 个工作日）
**验收标准**: 6 项 P0 阻塞性标准必须全部通过
**用户体验评分目标**: 7/10 → 9/10 (+28.6%)

---

## 背景：Phase 1.5 完成状态

### 已有基础设施

**安全模块** (Phase 1.5 ✅):
- ✅ 5 层 Prompt Injection 防护（87% 防御率）
- ✅ 审计日志系统（PII 脱敏 + GDPR 合规）
- ✅ 输入验证系统（参数白名单）
- ✅ 速率限制系统（60/min + 1000/hour）
- ✅ 输出验证系统（凭证清理）

**后端服务** (Phase 1 ✅):
- ✅ FastAPI REST API（5 个 Pattern）
- ✅ MLX/Ollama 集成（Apple Silicon 优化）
- ✅ 版权保护系统（水印 + 审计）

**签名与分发** (Phase 0.5 ✅):
- ✅ Developer ID 签名 + Notarization
- ✅ Hardened Runtime Entitlements
- ✅ Sparkle 2 自动更新

### Phase 2 的挑战

1. **UX 设计**: 从"CLI 工程师工具"到"隐形 AI 助手"
2. **SwiftUI 现代化**: 使用 Observation Framework（iOS 17+/macOS 14+）
3. **场景识别**: 智能检测用户意图（文本选择、文件拖拽等）
4. **信任机制**: 渐进式风险评估（R0 → R3）
5. **撤销系统**: 7 天内一键回滚（文件版本管理）
6. **安全集成**: 前端调用 Phase 1.5 安全 API

---

## Phase 2 核心架构

### 技术栈选择

**Frontend（macOS 应用）**:
- **GUI 框架**: SwiftUI（macOS 14+）
- **状态管理**: Observation Framework（替代 @StateObject/@ObservedObject）
- **网络**: URLSession + async/await
- **持久化**: SwiftData（替代 Core Data）
- **权限管理**: FullDiskAccess.swift + TCC（已有）

**后端集成**:
- **通信协议**: REST API（FastAPI）
- **安全调用**: 集成 Phase 1.5 审计日志 + 速率限制
- **错误处理**: 统一错误处理 + 用户友好提示

### 应用架构

```
MacCortex.app
├── App Layer（应用层）
│   ├── MacCortexApp.swift         # 应用入口（@main）
│   ├── AppState.swift              # 全局状态（Observation）
│   └── SceneDelegate.swift         # 场景管理
│
├── UI Layer（界面层）
│   ├── Views/
│   │   ├── FloatingToolbar.swift  # 浮动工具栏（主界面）
│   │   ├── PatternPicker.swift    # Pattern 选择器
│   │   ├── ResultView.swift       # 结果展示
│   │   ├── HistoryView.swift      # 历史记录
│   │   └── SettingsView.swift     # 设置界面
│   └── Components/
│       ├── RiskBadge.swift        # 风险等级标识
│       ├── ProgressIndicator.swift # 进度指示器
│       └── UndoButton.swift       # 撤销按钮
│
├── Business Logic Layer（业务逻辑层）
│   ├── Services/
│   │   ├── PatternService.swift   # Pattern 执行服务
│   │   ├── SceneDetector.swift    # 场景识别服务
│   │   ├── TrustEngine.swift      # 渐进式信任引擎
│   │   └── UndoManager.swift      # 撤销管理器
│   └── Models/
│       ├── Pattern.swift          # Pattern 模型
│       ├── Task.swift             # 任务模型
│       ├── RiskLevel.swift        # 风险等级
│       └── UndoSnapshot.swift     # 撤销快照
│
├── Data Layer（数据层）
│   ├── Repositories/
│   │   ├── TaskRepository.swift   # 任务数据仓库
│   │   └── HistoryRepository.swift # 历史记录仓库
│   └── SwiftData/
│       ├── Schema.swift           # SwiftData Schema
│       └── Migration.swift        # 数据迁移
│
├── Network Layer（网络层）
│   ├── APIClient.swift            # API 客户端
│   ├── Endpoints.swift            # API 端点定义
│   └── SecurityInterceptor.swift  # 安全拦截器（集成 Phase 1.5）
│
└── System Layer（系统层）
    ├── Permissions/
    │   ├── FullDiskAccessManager.swift
    │   └── NotificationsManager.swift
    └── Utilities/
        ├── Logger.swift           # 日志工具
        └── FileManager+Extensions.swift
```

---

## Week 1: 基础 GUI 框架（Day 1-5）✅ 已完成（2026-01-21）

### 完成总结

**总体进度**: 100% (5/5 天完成)
**新增代码**: +570 行
**新增组件**: FloatingToolbarView, SceneDetector
**编译时间**: 11.87s
**编译状态**: ✅ 零错误

---

### Day 1: Observation Framework 升级 ✅

**实际完成**:
- ✅ AppState 迁移至 @Observable 宏（Swift 5.9+）
- ✅ 所有视图更新为 @Environment（替代 @EnvironmentObject）
- ✅ 4 个核心数据模型定义（PatternResult, DetectedScene, TrustLevel, PendingOperation）
- ✅ 编译验证成功（0.08s）

**交付物**:
- `MacCortexApp.swift` 升级（+180 行）
- 数据模型完整定义

**Git**: fac38e4

---

### Day 1-2: SwiftUI 项目骨架（原计划）

**原任务**:
- [x] ~~创建 Xcode 项目（macOS App，SwiftUI + Swift 6）~~ 已有项目
- [x] 配置 Observation Framework
- [x] ~~设置 SwiftData Schema~~ 推迟到 Week 2
- [x] ~~集成 Phase 0.5 签名配置~~ 已在 Phase 0.5 完成

**交付物**: 可运行的应用 + AppState（Observation）

**核心代码**:
```swift
// MacCortexApp.swift
import SwiftUI

@main
struct MacCortexApp: App {
    @State private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(appState)
        }
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}

// AppState.swift (Observation Framework)
import Observation
import Foundation

@Observable
class AppState {
    var selectedPattern: Pattern?
    var currentTask: Task?
    var history: [Task] = []
    var isProcessing = false

    // Phase 1.5 安全集成
    var auditLogger: AuditLogger
    var rateLimiter: RateLimiter

    init() {
        self.auditLogger = AuditLogger()
        self.rateLimiter = RateLimiter()
    }
}
```

**验收**:
```bash
# 构建成功
xcodebuild -scheme MacCortex -configuration Debug build

# 签名验证
codesign -dv --verbose=4 build/Debug/MacCortex.app
```

---

### Day 2-3: 浮动工具栏 UI ✅

**实际完成**:
- ✅ FloatingToolbarView.swift（320 行）
- ✅ Apple Intelligence 风格设计（毛玻璃背景 + 圆角）
- ✅ 展开/紧凑模式切换（320px ↔ 60px，流畅动画）
- ✅ 5 个 Pattern 快捷按钮（可重用 PatternButton 组件）
- ✅ 场景指示器 + 信任等级指示器
- ✅ 拖拽功能（DragGesture）
- ✅ 3 个 Preview 配置
- ✅ ContentView 测试面板集成（+70 行）
- ✅ 编译验证成功（4.14s）

**交付物**:
- `FloatingToolbarView.swift`（320 行）
- `PatternButton` 组件（可重用）
- 测试面板（场景切换 + 信任等级切换）

**Git**: 01c74c1

**未完成（推迟到 Week 2）**:
- ⏳ 全局快捷键支持（⌘+Shift+Space）
- ⏳ 窗口置顶（需要独立窗口，当前为叠加层）

---

### Day 3-4: 浮动工具栏 UI（原计划）

**原任务**:
- [x] 设计浮动工具栏（参考 Apple Intelligence 风格）
- [x] 实现 Pattern 选择器（5 个 Pattern）
- [ ] 添加快捷键支持（⌘+Shift+Space） - 推迟
- [ ] 实现窗口置顶与透明效果 - 推迟

**交付物**: FloatingToolbarView.swift ✅

**核心 UI 设计**:
```swift
// FloatingToolbar.swift
import SwiftUI

struct FloatingToolbar: View {
    @Environment(AppState.self) private var appState
    @State private var isExpanded = false

    var body: some View {
        VStack(spacing: 0) {
            // 顶部手柄
            Handle()

            // Pattern 选择器
            if isExpanded {
                PatternPicker(selection: $appState.selectedPattern)
                    .transition(.move(edge: .top).combined(with: .opacity))
            }

            // 主操作按钮
            ActionButton(
                pattern: appState.selectedPattern,
                action: { await executePattern() }
            )
        }
        .frame(width: 320)
        .background(.ultraThinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.1), radius: 20)
        .onAppear {
            // 窗口置顶
            NSApp.windows.first?.level = .floating
        }
    }

    private func executePattern() async {
        // 调用 Phase 1.5 安全 API
        guard await appState.rateLimiter.checkLimit() else {
            showRateLimitError()
            return
        }

        // 执行 Pattern
        await appState.executePattern()
    }
}
```

**验收**:
- ✅ 工具栏显示正常（320px 宽度，半透明材质）
- ✅ 快捷键 ⌘+Shift+Space 触发
- ✅ 窗口置顶（level = .floating）
- ✅ 动画流畅（60fps）

---

### Day 4-5: 智能场景检测 ✅

**实际完成**:
- ✅ SceneDetector.swift（250 行）
- ✅ Accessibility API 集成（窗口标题实时检测）
- ✅ NSWorkspace API 集成（活动应用检测）
- ✅ 6 种场景识别（browsing, coding, writing, reading, meeting, unknown）
- ✅ 置信度计算（0.5-0.95 范围）
- ✅ 40+ 应用规则库（视频会议、代码编写、文档编写等）
- ✅ 双重分析（应用类型 + 窗口标题）
- ✅ 自动同步 AppState（每 2 秒实时更新）
- ✅ ContentView 实时检测面板（+60 行）
- ✅ 启动/停止控制 + 实时信息显示
- ✅ 编译验证成功（11.87s）

**交付物**:
- `SceneDetector.swift`（250 行）
- `AppState` 扩展（场景检测方法）
- 实时检测控制面板

**Git**: 6cb969c

---

### Day 5: 网络层 + Phase 1.5 集成（原计划）

**原任务**:
- [ ] 创建 APIClient（URLSession + async/await） - 推迟到 Week 2
- [ ] 实现 SecurityInterceptor（集成审计日志、速率限制） - 推迟到 Week 2
- [ ] 连接 FastAPI Backend - 推迟到 Week 2
- [ ] 错误处理与重试机制 - 推迟到 Week 2

**交付物**: APIClient.swift + SecurityInterceptor.swift（推迟到 Week 2 Day 6-7）

**核心代码**:
```swift
// APIClient.swift
import Foundation

actor APIClient {
    private let baseURL = URL(string: "http://localhost:8000")!
    private let session = URLSession.shared
    private let interceptor: SecurityInterceptor

    init(interceptor: SecurityInterceptor) {
        self.interceptor = interceptor
    }

    func executePattern(
        _ pattern: Pattern,
        text: String,
        parameters: [String: Any]
    ) async throws -> PatternResult {
        // Phase 1.5 安全拦截
        try await interceptor.preRequest(pattern: pattern, text: text)

        // 构建请求
        var request = URLRequest(url: baseURL.appendingPathComponent("/execute"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "pattern_id": pattern.id,
            "text": text,
            "parameters": parameters
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        // 发送请求
        let (data, response) = try await session.data(for: request)

        // Phase 1.5 审计日志
        await interceptor.postRequest(response: response, data: data)

        // 解析响应
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.invalidResponse
        }

        return try JSONDecoder().decode(PatternResult.self, from: data)
    }
}

// SecurityInterceptor.swift
actor SecurityInterceptor {
    private let auditLogger: AuditLogger
    private let rateLimiter: RateLimiter

    func preRequest(pattern: Pattern, text: String) async throws {
        // 速率限制检查
        guard await rateLimiter.checkLimit() else {
            throw SecurityError.rateLimitExceeded
        }

        // 审计日志（请求前）
        await auditLogger.logRequest(
            pattern: pattern.id,
            textLength: text.count
        )
    }

    func postRequest(response: URLResponse, data: Data) async {
        // 审计日志（请求后）
        await auditLogger.logResponse(
            statusCode: (response as? HTTPURLResponse)?.statusCode ?? 0,
            dataSize: data.count
        )
    }
}
```

**验收**:
```bash
# 启动 Backend
cd Backend && source .venv/bin/activate && python -m uvicorn src.main:app --reload

# 测试 API 连接
curl -X POST http://localhost:8000/execute -d '{
  "pattern_id": "summarize",
  "text": "Test text",
  "parameters": {}
}'

# 验证审计日志
cat Backend/logs/audit-$(date +%Y-%m-%d).jsonl | jq .
```

---

## Week 1 完成总结（2026-01-21）

### 实施概览

| 指标 | 计划 | 实际 | 达成率 |
|------|------|------|--------|
| **工期** | 5 天 | 5 天 | 100% |
| **核心任务** | 3 项 | 3 项 | 100% |
| **代码量** | ~500 行 | 570 行 | 114% |
| **编译状态** | 0 错误 | 0 错误 | ✅ |
| **Git 提交** | 3-5 次 | 3 次 | ✅ |

### 核心交付物

1. **Observation Framework 升级** ✅
   - AppState 迁移至 @Observable
   - 4 个数据模型定义（PatternResult, DetectedScene, TrustLevel, PendingOperation）
   - 所有视图更新为 @Environment
   - Git: fac38e4

2. **Apple Intelligence 风格浮动工具栏** ✅
   - FloatingToolbarView.swift（320 行）
   - 展开/紧凑模式切换（320px ↔ 60px）
   - 5 个 Pattern 快捷按钮
   - 毛玻璃背景 + 流畅动画
   - Git: 01c74c1

3. **智能场景检测系统** ✅
   - SceneDetector.swift（250 行）
   - Accessibility API + NSWorkspace 集成
   - 6 种场景识别（0.5-0.95 置信度）
   - 40+ 应用规则库
   - 实时检测面板
   - Git: 6cb969c

### 技术亮点

- **Swift 现代化**: 全面采用 Swift 5.9+ Observation Framework
- **Actor 并发**: 正确处理 @MainActor 隔离（Timer → Task → Main Thread）
- **组件化设计**: PatternButton 可复用组件，3 个 Preview 配置
- **Apple 设计规范**:
  - `.ultraThinMaterial` 毛玻璃
  - `.spring(response: 0.3, dampingFraction: 0.7)` 流畅动画
  - 圆角阴影（cornerRadius: 16, shadow: radius 12）
- **实时性能**: 2 秒轮询场景检测，性能开销可控

### 推迟到 Week 2 的任务

| 原计划 | 推迟原因 | 新计划 |
|--------|----------|--------|
| Day 5: APIClient + Backend 集成 | 优先完成场景检测 | Week 2 Day 6-7 |
| 全局快捷键（⌘+Shift+Space） | 需要独立窗口架构 | Week 2 Day 8 |
| 窗口置顶（level: .floating） | 当前为叠加层设计 | Week 2 Day 8 |

### Week 1 验收结果

| 验收项 | 状态 | 备注 |
|--------|------|------|
| SwiftUI 项目可运行 | ✅ | 编译时间 11.87s |
| Observation Framework 集成 | ✅ | 零编译错误 |
| 浮动工具栏 UI 完成 | ✅ | 320 行，3 个 Preview |
| 场景检测可用 | ✅ | 6 种场景，40+ 规则 |
| 代码签名正常 | ✅ | Developer ID 有效 |
| Git 历史清晰 | ✅ | 3 次有意义提交 |

**总体评价**: Week 1 核心目标全部达成，代码质量优秀，为 Week 2 Backend 集成奠定了坚实基础。✅

---

## Week 2: Backend 集成 + 信任机制（Day 6-10）

### Day 6-7: APIClient + Backend 集成（从 Week 1 Day 5 推迟）

**任务**:
- [ ] 创建 APIClient（URLSession + async/await）
- [ ] 实现 SecurityInterceptor（集成审计日志、速率限制）
- [ ] 连接 FastAPI Backend（http://localhost:8000）
- [ ] 错误处理与重试机制
- [ ] 集成测试（Frontend ↔ Backend）

**交付物**: APIClient.swift + SecurityInterceptor.swift

**优先级**: P0（Week 1 Day 5 推迟任务）

**说明**:
- **原计划的"智能场景识别"已在 Week 1 Day 4-5 提前完成** ✅
- 实际实现：SceneDetector.swift（250 行）
- 完成内容：
  - Accessibility API 集成（窗口标题检测）
  - NSWorkspace API 集成（活动应用检测）
  - 6 种场景识别（browsing, coding, writing, reading, meeting, unknown）
  - 置信度计算（0.5-0.95）
  - 40+ 应用规则库
- 参考：Week 1 Day 4-5 实际完成部分（行 318-340）

**后续增强方向**（可选，非 P0）:
- [ ] 文本选择监听（NSEvent.addGlobalMonitorForEvents）
- [ ] 剪贴板变化监听（NSPasteboard.changeCount）
- [ ] 自动推荐 Pattern（基于选中文本内容）
- [ ] 文件拖拽场景识别

---

### Day 8-9: 渐进式信任机制

**任务**:
- [ ] 实现 TrustEngine（Risk Level 0-3）
- [ ] 设计风险评估规则
- [ ] 集成 Policy Engine（复用 Phase 1.5）
- [ ] UI 风险提示（RiskBadge）

**交付物**: TrustEngine.swift + RiskBadge.swift

**风险等级定义**:
```swift
// RiskLevel.swift
enum RiskLevel: Int, Comparable {
    case r0_safe = 0        // 安全：只读操作
    case r1_low = 1         // 低风险：文本处理
    case r2_medium = 2      // 中风险：文件读取
    case r3_high = 3        // 高风险：文件写入/网络请求

    var color: Color {
        switch self {
        case .r0_safe: return .green
        case .r1_low: return .blue
        case .r2_medium: return .orange
        case .r3_high: return .red
        }
    }

    var requiresConfirmation: Bool {
        self >= .r2_medium
    }
}

// TrustEngine.swift
@Observable
class TrustEngine {
    private let policyEngine: PolicyEngine  // Phase 1.5

    func assessRisk(for task: Task) -> RiskLevel {
        var risk: RiskLevel = .r0_safe

        // 规则 1: 操作类型
        if task.pattern == .format || task.pattern == .translate {
            risk = .r1_low  // 文本处理
        } else if task.pattern == .search {
            risk = .r3_high  // 网络请求
        }

        // 规则 2: 输入来源
        if task.source == .file {
            risk = max(risk, .r2_medium)  // 文件读取
        }

        // 规则 3: 输出目标
        if task.outputTarget == .file {
            risk = .r3_high  // 文件写入
        }

        // Phase 1.5 Policy Engine 验证
        if !policyEngine.isAllowed(task) {
            risk = .r3_high
        }

        return risk
    }

    func requestConfirmation(for task: Task) async -> Bool {
        let risk = assessRisk(for: task)
        guard risk.requiresConfirmation else { return true }

        // 显示确认对话框
        return await showConfirmationDialog(task: task, risk: risk)
    }
}
```

**验收**:
- ✅ R0-R3 风险评估准确
- ✅ R2+ 操作需要用户确认
- ✅ UI 风险标识清晰
- ✅ 集成 Phase 1.5 Policy Engine

---

### Day 10: 一键撤销系统

**任务**:
- [ ] 实现 UndoManager（7 天内可回滚）
- [ ] 文件版本管理（快照存储）
- [ ] UI 撤销按钮与历史记录
- [ ] 自动清理过期快照

**交付物**: UndoManager.swift + UndoSnapshot.swift

**核心功能**:
```swift
// UndoSnapshot.swift
struct UndoSnapshot: Codable, Identifiable {
    let id: UUID
    let taskID: UUID
    let timestamp: Date
    let originalContent: Data
    let modifiedContent: Data
    let filePath: URL?

    var isExpired: Bool {
        Date().timeIntervalSince(timestamp) > 7 * 24 * 3600  // 7 天
    }
}

// UndoManager.swift
actor UndoManager {
    private let snapshotDirectory: URL
    private var snapshots: [UndoSnapshot] = []

    init() {
        self.snapshotDirectory = FileManager.default
            .urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("MacCortex/Snapshots")

        try? FileManager.default.createDirectory(
            at: snapshotDirectory,
            withIntermediateDirectories: true
        )

        // 加载现有快照
        loadSnapshots()
    }

    func createSnapshot(for task: Task, originalContent: Data) async throws {
        let snapshot = UndoSnapshot(
            id: UUID(),
            taskID: task.id,
            timestamp: Date(),
            originalContent: originalContent,
            modifiedContent: task.result?.data ?? Data(),
            filePath: task.outputTarget == .file ? task.outputURL : nil
        )

        // 保存快照到磁盘
        try await saveSnapshot(snapshot)
        snapshots.append(snapshot)
    }

    func undo(snapshotID: UUID) async throws {
        guard let snapshot = snapshots.first(where: { $0.id == snapshotID }) else {
            throw UndoError.snapshotNotFound
        }

        // 恢复原始内容
        if let filePath = snapshot.filePath {
            try snapshot.originalContent.write(to: filePath)
        }

        // 删除快照
        try await deleteSnapshot(snapshot)
        snapshots.removeAll { $0.id == snapshotID }
    }

    func cleanupExpiredSnapshots() async {
        let expired = snapshots.filter { $0.isExpired }
        for snapshot in expired {
            try? await deleteSnapshot(snapshot)
        }
        snapshots.removeAll { $0.isExpired }
    }
}
```

**验收**:
- ✅ 文件操作前自动创建快照
- ✅ 7 天内可一键回滚
- ✅ 过期快照自动清理
- ✅ 存储开销 < 100MB（正常使用）

---

## Week 3: UI 完善 + 集成测试（Day 11-15）

### Day 11-12: 历史记录与设置

**任务**:
- [ ] 实现 HistoryView（任务历史）
- [ ] 实现 SettingsView（应用设置）
- [ ] SwiftData 持久化
- [ ] 搜索与过滤功能

**交付物**: HistoryView.swift + SettingsView.swift

---

### Day 13-14: 集成测试

**任务**:
- [ ] 端到端测试（UI → Backend → 安全模块）
- [ ] 性能测试（UI 响应时间 < 100ms）
- [ ] 权限测试（Full Disk Access）
- [ ] 撤销系统测试

**验收标准**:
- ✅ 所有 5 个 Pattern 正常工作
- ✅ Phase 1.5 安全模块集成无误
- ✅ UI 响应时间 < 100ms p95
- ✅ 撤销成功率 100%

---

### Day 15: 文档与发布准备

**任务**:
- [ ] 更新 README.md（Phase 2 完成）
- [ ] 创建用户手册
- [ ] 生成签名 DMG
- [ ] 公证测试

**交付物**: MacCortex-v1.0.dmg

---

## Phase 2 验收标准（P0 阻塞性）

| # | 验收项 | 测试方法 | 期望结果 | 优先级 |
|---|--------|----------|----------|--------|
| 1 | **Desktop GUI 可用性** | 手动测试 | 所有 5 个 Pattern 正常工作 | P0 |
| 2 | **场景识别准确率** | 100 个场景测试 | ≥ 85% 准确率 | P0 |
| 3 | **信任机制有效性** | 风险评估测试 | R2+ 操作需确认 | P0 |
| 4 | **撤销成功率** | 50 次撤销测试 | 100% 成功率 | P0 |
| 5 | **UI 响应时间** | 性能基准测试 | < 100ms p95 | P0 |
| 6 | **Phase 1.5 安全集成** | 集成测试 | 审计日志、速率限制正常 | P0 |

**通过条件**: 所有 6 项必须 ✅

---

## 关键技术决策

### 决策 1: Observation Framework vs Combine

**问题**: SwiftUI 状态管理选择哪种方案？

**选项**:
- **方案 A**: Observation Framework（Swift 5.9+）
- **方案 B**: Combine（传统方案）
- **方案 C**: 混合使用

**建议**: **方案 A** - Observation Framework

**理由**:
- macOS 14+ 原生支持，更简洁的 API
- 更好的性能（编译器优化）
- 自动依赖追踪（无需手动 @Published）
- 符合 Apple 最新技术方向

---

### 决策 2: 浮动工具栏 vs 菜单栏应用

**问题**: 主界面形态选择？

**选项**:
- **方案 A**: 浮动工具栏（Apple Intelligence 风格）
- **方案 B**: 菜单栏应用（Raycast 风格）
- **方案 C**: 传统窗口应用

**建议**: **方案 A** - 浮动工具栏

**理由**:
- 符合"隐形 AI"设计理念
- 快捷键触发，即用即走
- 视觉上更现代化
- 支持拖拽定位

---

### 决策 3: SwiftData vs Core Data

**问题**: 持久化方案选择？

**选项**:
- **方案 A**: SwiftData（Swift 原生）
- **方案 B**: Core Data（Objective-C）

**建议**: **方案 A** - SwiftData

**理由**:
- macOS 14+ 原生支持
- Swift 原生 API，类型安全
- 自动生成 Schema
- 与 Observation Framework 无缝集成

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 | 残余风险 |
|------|------|------|----------|----------|
| **Accessibility API 权限被拒** | 20% | 高 | 优雅降级（手动触发） | 🟡 中 |
| **性能不达标** | 15% | 中 | 异步处理 + 缓存 | 🟢 低 |
| **撤销失败** | 10% | 高 | 完整测试 + 事务机制 | 🟢 低 |
| **场景识别误报** | 30% | 低 | 手动选择 Pattern | 🟢 低 |
| **Backend 连接失败** | 5% | 高 | 离线模式 + 错误提示 | 🟢 低 |

**总体风险评分**: 🟢 **可控**

---

## 下一步行动（Week 2 立即开始）

### Week 2 Day 6-7: APIClient + Backend 集成

**准备工作**:
```bash
# 1. 验证 Week 1 完成状态
cd /Users/jamesg/projects/MacCortex
git log --oneline --since="2026-01-21" --until="2026-01-22"
# 预期: 3 个提交（fac38e4, 01c74c1, 6cb969c）

# 2. 启动 Phase 1.5 Backend
cd Backend && source .venv/bin/activate
python -m uvicorn src.main:app --reload &

# 3. 测试 Backend API 可用性
curl -X POST http://localhost:8000/execute -d '{
  "pattern_id": "summarize",
  "text": "Week 2 Backend 集成测试",
  "parameters": {"length": "short"}
}'
# 预期: 200 OK + JSON 响应

# 4. 验证 Phase 1.5 安全模块
cat Backend/logs/audit-$(date +%Y-%m-%d).jsonl | tail -1 | jq .
# 预期: 审计日志记录正常
```

**实施步骤**:
1. 创建 `Sources/MacCortexApp/Network/APIClient.swift`
2. 创建 `Sources/MacCortexApp/Network/SecurityInterceptor.swift`
3. 创建 `Sources/MacCortexApp/Network/Endpoints.swift`
4. 更新 `AppState.swift` 集成 APIClient
5. 更新 `FloatingToolbarView.swift` 调用真实 API
6. 集成测试（Frontend → Backend → 审计日志）
7. 错误处理与用户提示
8. Git 提交（Week 2 Day 6-7）

**验收标准**:
- ✅ APIClient 可正常调用 5 个 Pattern
- ✅ SecurityInterceptor 集成审计日志 + 速率限制
- ✅ 错误处理友好（网络错误、速率限制、Backend 异常）
- ✅ UI 显示实际 Pattern 执行结果
- ✅ 编译无错误，运行无崩溃

---

**计划状态**: ✅ Week 1 已完成，⏳ Week 2 待启动
**创建时间**: 2026-01-21
**最后更新**: 2026-01-21（Week 1 完成）
**基于**: Phase 1.5 完成状态 + README_ARCH.md v1.1
**执行人**: Claude Code (Sonnet 4.5)
**验证方式**: 6 项 P0 验收标准
