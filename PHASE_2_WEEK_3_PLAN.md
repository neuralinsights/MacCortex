# Phase 2 Week 3: 高级功能与优化 - 实施计划

> **创建时间**: 2026-01-21 14:45 +1300 (NZDT)
> **基于时间校验**: #20260121-01
> **状态**: 待开始
> **预计工期**: 5 天（Day 11-15）

---

## 📊 当前状态

### ✅ Phase 2 Week 1 完成（Day 1-5）
- ✅ SceneDetector (场景识别) - 10 种场景检测
- ✅ FloatingToolbarView (浮动工具栏) - Apple Intelligence 风格 UI
- ✅ Pattern 快捷按钮 (5 个 Pattern 一键执行)
- ✅ 场景感知自动推荐 (基于上下文自动选择 Pattern)

### ✅ Phase 2 Week 2 完成（Day 6-10）
- ✅ Backend API 集成（Network 层 530 行）
- ✅ 渐进式信任机制（TrustEngine + RiskBadge 580 行）
- ✅ 一键撤销系统（UndoManager + UndoButton 600 行）
- ✅ 风险评估与确认对话框
- ✅ 快照管理（7 天 TTL，JSON 持久化）

**累计代码**: 3,420+ 行（Swift + Python）

---

## 🎯 Week 3 目标

### 核心目标
1. **MCP 工具动态加载** - 支持第三方 MCP 服务器扩展
2. **Shortcuts 自动化集成** - macOS 原生自动化能力
3. **性能优化** - 减少内存占用，提升响应速度
4. **压力测试** - 验证并发性能与稳定性

### 非目标（Phase 3）
- ❌ Shell 执行器（Phase 3: Hands）
- ❌ 文件移动/重命名（R1 级操作，Phase 3）
- ❌ Swarm 复杂任务编排（Phase 4）

---

## Day 11-12: MCP 工具动态加载

### 背景

**MCP (Model Context Protocol)** 是 Anthropic 推出的标准化工具扩展协议：
- 当前生态：5,800+ MCP 服务器，800 万下载
- 官方规范：2025-11-25 最新版本
- 应用场景：文件系统、数据库、API 集成、第三方服务

**MacCortex 集成需求**：
- 支持加载第三方 MCP 服务器（白名单机制）
- 与 TrustEngine 集成（风险评估）
- 审计日志记录所有 MCP 工具调用

---

### 技术设计

#### 架构

```
MacCortex GUI
├─ AppState.mcpManager: MCPManager
│
└─ MCPManager (Actor)
   ├─ loadedServers: [MCPServer]
   ├─ whitelist: [String] (server URLs 白名单)
   ├─ loadServer(url:) async throws
   ├─ executeToolcall(:) async throws
   └─ unloadServer(id:)

MCPServer
├─ id: UUID
├─ name: String
├─ url: URL
├─ capabilities: [String]
├─ trustLevel: TrustLevel (R0-R3)
├─ lastPing: Date
└─ process: Process (子进程)
```

#### 文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `Sources/MacCortexApp/Services/MCPManager.swift` | ~250 | MCP 服务器管理器 |
| `Sources/MacCortexApp/Models/MCPServer.swift` | ~100 | MCP 服务器数据模型 |
| `Sources/MacCortexApp/Models/MCPToolCall.swift` | ~80 | MCP 工具调用请求/响应 |
| `Sources/MacCortexApp/Components/MCPServerList.swift` | ~200 | MCP 服务器列表 UI |
| `Resources/Config/mcp_whitelist.json` | ~50 | 白名单配置文件 |

**预计总代码**: ~680 行

---

### 核心功能

#### 1. MCPManager.swift - 服务器管理

```swift
/// MCP 服务器管理器（Actor 线程安全）
actor MCPManager {
    static let shared = MCPManager()

    private var loadedServers: [MCPServer] = []
    private var whitelist: Set<String> = []
    private let logger = Logger(subsystem: "com.yugeng.MacCortex", category: "MCPManager")

    /// 加载 MCP 服务器
    /// - Parameter url: 服务器 URL（必须在白名单中）
    /// - Returns: 服务器 ID
    func loadServer(url: URL) async throws -> UUID {
        // 1. 白名单检查
        guard whitelist.contains(url.absoluteString) else {
            throw MCPError.notWhitelisted
        }

        // 2. 启动子进程（stdio 通信）
        let process = Process()
        process.executableURL = url
        // ... 配置 stdin/stdout pipes

        // 3. 握手（发送 initialize 请求）
        let capabilities = try await sendInitialize(process)

        // 4. 创建 MCPServer 实例
        let server = MCPServer(
            url: url,
            capabilities: capabilities,
            process: process
        )

        loadedServers.append(server)
        logger.info("已加载 MCP 服务器: \\(server.name)")

        return server.id
    }

    /// 执行 MCP 工具调用
    /// - Parameter toolCall: 工具调用请求
    /// - Returns: 执行结果
    func executeToolCall(_ toolCall: MCPToolCall) async throws -> MCPToolResult {
        // 1. 查找服务器
        guard let server = loadedServers.first(where: { $0.id == toolCall.serverID }) else {
            throw MCPError.serverNotFound
        }

        // 2. 风险评估（集成 TrustEngine）
        let task = OperationTask(
            patternId: "mcp_\(toolCall.toolName)",
            text: toolCall.arguments.description,
            parameters: [:],
            source: .user,
            outputTarget: .display
        )
        let assessment = TrustEngine.shared.assessRisk(for: task)

        // 3. 如果需要确认，请求用户授权
        if assessment.requiresConfirmation {
            // 显示确认对话框（通过 AppState）
            // ...
        }

        // 4. 发送 tools/call 请求到 MCP 服务器
        let result = try await sendToolCall(server.process, toolCall)

        // 5. 审计日志
        AuditLogger.shared.log(event: "mcp_tool_call", metadata: [
            "server_id": server.id.uuidString,
            "tool_name": toolCall.toolName,
            "trust_level": assessment.riskLevel.rawValue
        ])

        // 6. 记录到 UndoManager（如果是修改操作）
        if server.trustLevel.rawValue >= TrustLevel.R1.rawValue {
            // 创建撤销快照
        }

        return result
    }

    /// 卸载 MCP 服务器
    func unloadServer(id: UUID) async {
        guard let index = loadedServers.firstIndex(where: { $0.id == id }) else {
            return
        }

        let server = loadedServers[index]
        server.process.terminate()
        loadedServers.remove(at: index)

        logger.info("已卸载 MCP 服务器: \\(server.name)")
    }

    /// 加载白名单配置
    private func loadWhitelist() {
        guard let url = Bundle.main.url(forResource: "mcp_whitelist", withExtension: "json") else {
            return
        }

        do {
            let data = try Data(contentsOf: url)
            let config = try JSONDecoder().decode(MCPWhitelist.self, from: data)
            whitelist = Set(config.allowedServers)
            logger.info("已加载 MCP 白名单: \\(whitelist.count) 个服务器")
        } catch {
            logger.error("加载 MCP 白名单失败: \\(error.localizedDescription)")
        }
    }
}
```

#### 2. MCPServer.swift - 服务器模型

```swift
/// MCP 服务器数据模型
struct MCPServer: Identifiable, Codable {
    let id: UUID
    let name: String
    let url: URL
    let capabilities: [String]
    let trustLevel: TrustLevel
    let lastPing: Date

    var displayName: String {
        name.isEmpty ? url.lastPathComponent : name
    }

    var isResponding: Bool {
        Date().timeIntervalSince(lastPing) < 30.0
    }
}

/// MCP 工具调用请求
struct MCPToolCall {
    let serverID: UUID
    let toolName: String
    let arguments: [String: Any]
    let requestID: UUID = UUID()
}

/// MCP 工具调用结果
struct MCPToolResult {
    let success: Bool
    let output: String
    let metadata: [String: Any]
    let duration: TimeInterval
}

enum MCPError: LocalizedError {
    case notWhitelisted
    case serverNotFound
    case connectionFailed
    case timeout
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .notWhitelisted:
            return "MCP 服务器未在白名单中"
        case .serverNotFound:
            return "未找到 MCP 服务器"
        case .connectionFailed:
            return "连接 MCP 服务器失败"
        case .timeout:
            return "MCP 请求超时"
        case .invalidResponse:
            return "MCP 响应格式错误"
        }
    }
}
```

#### 3. mcp_whitelist.json - 白名单配置

```json
{
  "version": "1.0",
  "allowedServers": [
    "file:///usr/local/bin/mcp-server-filesystem",
    "file:///usr/local/bin/mcp-server-sqlite",
    "file:///usr/local/bin/mcp-server-brave-search"
  ],
  "description": "MCP 服务器白名单（仅信任的服务器可加载）"
}
```

#### 4. MCPServerList.swift - UI 组件

```swift
/// MCP 服务器列表视图
struct MCPServerListView: View {
    @State private var servers: [MCPServer] = []
    @State private var isLoading = true
    @State private var showAddServer = false

    var body: some View {
        VStack(spacing: 0) {
            // 头部
            HStack {
                Text("MCP 服务器")
                    .font(.title2)
                    .fontWeight(.bold)

                Spacer()

                Button(action: { showAddServer = true }) {
                    Label("添加服务器", systemImage: "plus.circle.fill")
                }
            }
            .padding()

            Divider()

            // 服务器列表
            if servers.isEmpty {
                VStack {
                    Image(systemName: "server.rack")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)
                    Text("暂无 MCP 服务器")
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List(servers) { server in
                    MCPServerRow(server: server, onUnload: {
                        unloadServer(server.id)
                    })
                }
            }
        }
        .frame(width: 600, height: 500)
        .onAppear { loadServers() }
        .sheet(isPresented: $showAddServer) {
            AddMCPServerSheet()
        }
    }

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

    var body: some View {
        HStack(spacing: 12) {
            // 状态指示器
            Circle()
                .fill(server.isResponding ? Color.green : Color.red)
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 4) {
                Text(server.displayName)
                    .font(.system(size: 13, weight: .medium))

                Text(server.url.path)
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            }

            Spacer()

            // 信任等级徽章
            RiskBadge(riskLevel: server.trustLevel, compact: true)

            // 卸载按钮
            Button(action: onUnload) {
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.red)
            }
            .buttonStyle(.plain)
        }
        .padding(.vertical, 4)
    }
}
```

---

### 安全策略

#### 白名单机制
- ✅ **仅加载白名单服务器**：`mcp_whitelist.json` 强制检查
- ✅ **版本锁定**：白名单记录服务器版本哈希
- ✅ **签名验证**：验证 MCP 服务器二进制签名（Phase 3）

#### 风险评估
- **R0（只读工具）**：自动执行（如 `list-files`）
- **R1（写入工具）**：需要确认（如 `write-file`）
- **R2/R3（删除/网络）**：默认禁止（如 `delete-file`, `http-request`）

#### 进程隔离
- **子进程执行**：所有 MCP 服务器在独立进程运行
- **资源限制**：CPU/内存限制（通过 `Process` 配置）
- **超时控制**：30 秒超时（防止死锁）

---

### 验收标准

| # | 验收项 | 测试方法 | 期望结果 |
|---|--------|----------|----------|
| 1 | 加载白名单服务器 | 添加 `mcp-server-filesystem` | 成功加载，显示在服务器列表 |
| 2 | 拒绝非白名单服务器 | 尝试添加 `/tmp/malicious-server` | 报错：`notWhitelisted` |
| 3 | 风险评估集成 | 调用 `write-file` 工具 | 显示确认对话框（R1 级） |
| 4 | 审计日志记录 | 执行任意 MCP 工具 | `audit.jsonl` 记录 `mcp_tool_call` 事件 |
| 5 | 进程隔离 | MCP 服务器崩溃 | MacCortex 主进程不受影响 |
| 6 | 超时控制 | 模拟慢响应服务器 | 30 秒后自动超时 |

---

## Day 13-14: Shortcuts 自动化集成

### 背景

**macOS Shortcuts** 是 Apple 官方自动化工具：
- macOS 12+ 内置
- 可调用 App Intents、AppleScript、Shell 脚本
- 支持触发器（时间、位置、App 启动等）

**MacCortex 集成目标**：
- 通过 Shortcuts 调用 MacCortex Pattern
- 支持从 Shortcuts 传递参数
- 返回结果到 Shortcuts（用于后续自动化）

---

### 技术设计

#### 架构

```
macOS Shortcuts
    ↓ (通过 App Intents 调用)
MacCortex App Intents
    ├─ ExecutePatternIntent
    ├─ GetContextIntent
    └─ CheckStatusIntent
    ↓
AppState.executePattern()
```

#### 文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `Sources/MacCortexApp/Intents/AppIntents.swift` | ~200 | App Intents 定义 |
| `Sources/MacCortexApp/Intents/ExecutePatternIntent.swift` | ~150 | Pattern 执行 Intent |
| `Sources/MacCortexApp/Intents/GetContextIntent.swift` | ~100 | 获取上下文 Intent |
| `Examples/Shortcuts/SummarizeClipboard.shortcut` | - | 示例 Shortcut |
| `Examples/Shortcuts/README.md` | ~100 | Shortcuts 使用指南 |

**预计总代码**: ~550 行

---

### 核心功能

#### 1. ExecutePatternIntent.swift

```swift
import AppIntents

/// 执行 Pattern Intent（供 Shortcuts 调用）
struct ExecutePatternIntent: AppIntent {
    static var title: LocalizedStringResource = "执行 Pattern"
    static var description = IntentDescription("执行 MacCortex Pattern 处理文本")

    @Parameter(title: "Pattern ID")
    var patternId: String

    @Parameter(title: "输入文本")
    var text: String

    @Parameter(title: "参数（JSON）", default: "{}")
    var parametersJSON: String

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        // 解析参数
        let parameters = try parseParameters(parametersJSON)

        // 调用 AppState 执行 Pattern
        let appState = AppState.shared
        let result = await appState.executePattern(
            patternId,
            text: text,
            parameters: parameters
        )

        guard result.success else {
            throw ExecutePatternError.executionFailed(result.output)
        }

        return .result(value: result.output)
    }

    private func parseParameters(_ json: String) throws -> [String: String] {
        guard let data = json.data(using: .utf8),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return [:]
        }
        return dict.compactMapValues { "\($0)" }
    }
}

enum ExecutePatternError: LocalizedError {
    case executionFailed(String)

    var errorDescription: String? {
        switch self {
        case .executionFailed(let message):
            return "Pattern 执行失败: \(message)"
        }
    }
}
```

#### 2. AppIntents.swift - 注册 Intents

```swift
import AppIntents

/// MacCortex App Intents（供 Shortcuts 调用）
struct MacCortexAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: ExecutePatternIntent(),
            phrases: [
                "总结剪贴板",
                "Summarize clipboard with \(.applicationName)",
                "翻译文本 with \(.applicationName)"
            ],
            shortTitle: "执行 Pattern",
            systemImageName: "sparkles"
        )
    }
}
```

#### 3. Info.plist 更新

```xml
<!-- Shortcuts 支持（App Intents） -->
<key>NSSupportsAppIntents</key>
<true/>
```

---

### 示例 Shortcuts

#### SummarizeClipboard.shortcut

```
Shortcut 流程：
1. Get Clipboard
2. Run MacCortex Pattern
   - Pattern ID: "summarize"
   - Text: [Clipboard]
   - Parameters: {"length": "short"}
3. Show Result
```

#### TranslateSelection.shortcut

```
Shortcut 流程：
1. Get Selected Text (通过 AppleScript)
2. Run MacCortex Pattern
   - Pattern ID: "translate"
   - Text: [Selected Text]
   - Parameters: {"target_language": "en-US"}
3. Show Result
4. Copy to Clipboard
```

---

### 用户手册

创建 `Examples/Shortcuts/README.md`：

```markdown
# MacCortex Shortcuts 使用指南

## 安装示例 Shortcuts

1. 打开 Finder → `Examples/Shortcuts/`
2. 双击 `.shortcut` 文件
3. 点击「添加快捷指令」

## 创建自定义 Shortcut

### 步骤 1: 打开 Shortcuts.app

```bash
open /System/Applications/Shortcuts.app
```

### 步骤 2: 新建快捷指令

1. 点击右上角「+」
2. 搜索「MacCortex」
3. 选择「执行 Pattern」

### 步骤 3: 配置参数

- **Pattern ID**: `summarize` / `translate` / `extract` / `format` / `search`
- **输入文本**: 可选择剪贴板、选中文本、文件内容等
- **参数**: JSON 格式（可选）

### 示例参数

**总结**:
```json
{"length": "short", "style": "bullet"}
```

**翻译**:
```json
{"target_language": "en-US", "style": "formal"}
```

**提取**:
```json
{"entity_types": ["person", "email"]}
```

### 步骤 4: 添加触发器（可选）

- 时间触发：每天 9:00 总结邮件
- App 触发：打开 Safari 时提取网页信息
- 位置触发：到达办公室时整理待办事项
```

---

### 验收标准

| # | 验收项 | 测试方法 | 期望结果 |
|---|--------|----------|----------|
| 1 | Shortcuts 可调用 | 打开 Shortcuts.app 搜索「MacCortex」 | 显示「执行 Pattern」Intent |
| 2 | Pattern 执行成功 | 运行 `SummarizeClipboard.shortcut` | 返回总结结果 |
| 3 | 参数传递正确 | 运行翻译 Shortcut（`target_language: en-US`） | 英文翻译结果 |
| 4 | 错误处理 | 传递无效 Pattern ID | 显示错误提示 |
| 5 | 触发器可用 | 设置时间触发器（每天 9:00） | 自动执行 Pattern |

---

## Day 15: 性能优化与压力测试

### 背景

Phase 2 Week 2 累计代码 3,420+ 行，需要：
1. **内存优化**：减少 Actor 内存占用
2. **响应速度**：Pattern 执行 < 2 秒（p95）
3. **并发性能**：支持 10+ 并发请求
4. **稳定性**：24 小时运行无崩溃

---

### 优化目标

| 指标 | 当前值 | 目标值 | 优化策略 |
|------|--------|--------|----------|
| **启动时间** | ~3 秒 | < 2 秒 | 懒加载模块 |
| **Pattern 响应** | ~2.5 秒 | < 2 秒 | 缓存 + 并发优化 |
| **内存占用** | ~150 MB | < 100 MB | Actor 池复用 |
| **CPU 占用（空闲）** | ~5% | < 2% | 减少轮询 |
| **并发处理** | 5 req/s | 10 req/s | API 客户端连接池 |

---

### 优化清单

#### 1. 启动时间优化

**问题**：
- `SceneDetector` 初始化慢（监听 NSWorkspace）
- `UndoManager` 加载历史快照阻塞启动

**解决方案**：
```swift
// AppState.swift
init() {
    // 懒加载：不在 init 时初始化
    Task {
        await sceneDetector.start() // 异步启动
    }

    Task {
        await UndoManager.shared.loadSnapshots() // 异步加载
    }
}
```

#### 2. Pattern 响应优化

**问题**：
- Backend API 调用延迟（网络 RTT）
- TrustEngine 重复计算风险

**解决方案**：
```swift
// APIClient.swift - 连接池复用
private let session: URLSession = {
    let config = URLSessionConfiguration.default
    config.httpMaximumConnectionsPerHost = 10 // 增加连接池
    config.requestCachePolicy = .returnCacheDataElseLoad
    return URLSession(configuration: config)
}()

// TrustEngine.swift - 缓存风险评估
private var riskCache: [String: RiskAssessment] = [:]

func assessRisk(for task: OperationTask) -> RiskAssessment {
    let cacheKey = "\(task.patternId)_\(task.source)_\(task.outputTarget)"
    if let cached = riskCache[cacheKey] {
        return cached
    }

    let assessment = ... // 计算风险
    riskCache[cacheKey] = assessment
    return assessment
}
```

#### 3. 内存优化

**问题**：
- `UndoManager.snapshots` 数组无限增长
- `TrustEngine.operationHistory` 内存泄漏

**解决方案**：
```swift
// UndoManager.swift
private let maxSnapshotsInMemory = 50 // 限制内存中快照数量

func trimSnapshots() {
    if snapshots.count > maxSnapshotsInMemory {
        snapshots.removeFirst(snapshots.count - maxSnapshotsInMemory)
    }
}

// TrustEngine.swift
private let maxHistorySize = 100 // 已存在，确保生效

func recordOperation(_ task: OperationTask) {
    operationHistory.append(task)
    if operationHistory.count > maxHistorySize {
        operationHistory.removeFirst(operationHistory.count - maxHistorySize)
    }
}
```

#### 4. CPU 优化

**问题**：
- `FloatingToolbarView` 场景检测轮询（每 2 秒）

**解决方案**：
```swift
// FloatingToolbarView.swift
// 方案 1: 增加轮询间隔（2 秒 → 5 秒）
Timer.publish(every: 5.0, on: .main, in: .common)

// 方案 2: 仅在窗口活跃时检测（更优）
.onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) {
    startSceneDetection()
}
.onReceive(NotificationCenter.default.publisher(for: NSApplication.didResignActiveNotification)) {
    stopSceneDetection()
}
```

---

### 压力测试

#### 测试 1: 并发 Pattern 执行

```swift
// Tests/PerformanceTests/ConcurrencyTest.swift
func testConcurrentPatternExecution() async throws {
    let iterations = 100
    await withTaskGroup(of: Void.self) { group in
        for i in 0..<iterations {
            group.addTask {
                let result = await appState.executePattern(
                    "summarize",
                    text: "Test text \\(i)",
                    parameters: [:]
                )
                XCTAssertTrue(result.success)
            }
        }
    }
}
```

**目标**: 100 个并发请求全部成功，< 10 秒完成

#### 测试 2: 内存泄漏检测

```bash
# Instruments Memory Leaks 检测
xcodebuild test -scheme MacCortex -destination 'platform=macOS' \
    -enableAddressSanitizer YES \
    -enableThreadSanitizer YES
```

**目标**: 0 内存泄漏，0 数据竞争

#### 测试 3: 24 小时稳定性测试

```swift
// Tests/StabilityTests/LongRunningTest.swift
func testLongRunning() async throws {
    let duration: TimeInterval = 24 * 60 * 60 // 24 小时
    let startTime = Date()

    while Date().timeIntervalSince(startTime) < duration {
        // 每 60 秒执行一次 Pattern
        let result = await appState.executePattern("summarize", text: "Stability test", parameters: [:])
        XCTAssertTrue(result.success)

        try await Task.sleep(nanoseconds: 60_000_000_000)
    }
}
```

**目标**: 24 小时无崩溃，内存稳定

---

### 验收标准

| # | 验收项 | 测试方法 | 目标值 | 状态 |
|---|--------|----------|--------|------|
| 1 | **启动时间** | 应用启动 → 主窗口显示 | < 2 秒 | ⏳ |
| 2 | **Pattern 响应** | 执行 summarize（p95） | < 2 秒 | ⏳ |
| 3 | **内存占用** | Activity Monitor | < 100 MB | ⏳ |
| 4 | **CPU 占用（空闲）** | Activity Monitor | < 2% | ⏳ |
| 5 | **并发性能** | 100 并发请求 | 全部成功 | ⏳ |
| 6 | **内存泄漏** | Instruments | 0 泄漏 | ⏳ |
| 7 | **24h 稳定性** | 长时间运行测试 | 无崩溃 | ⏳ |

---

## Week 3 验收总结

### 必须全部通过（P0 阻塞性）

| # | 功能模块 | 交付物 | 状态 |
|---|----------|--------|------|
| 1 | **MCP 工具加载** | MCPManager + 白名单机制 | ⏳ |
| 2 | **Shortcuts 集成** | App Intents + 示例 Shortcuts | ⏳ |
| 3 | **性能优化** | 启动 < 2s, Pattern < 2s, 内存 < 100MB | ⏳ |
| 4 | **压力测试** | 100 并发 + 24h 稳定性 | ⏳ |

---

## 下一步（Phase 3）

### Phase 3: Hands（系统执行能力）
- Shell 执行器（安全沙箱）
- 文件移动/重命名（R1 级操作）
- Notes 写入（macOS 原生集成）
- dry-run/diff 预览

### Phase 4: Swarm（复杂任务编排）
- Slow Lane 工作流（Plan/Execute/Reflect）
- Coder ↔ Reviewer 回路
- LangGraph 状态机集成

---

**创建时间**: 2026-01-21 14:45 +1300 (NZDT)
**预计完成**: 2026-01-26（5 个工作日）
**累计代码预估**: +1,230 行（MCP 680 + Shortcuts 550）
**总代码量**: 4,650+ 行（Phase 2 全部完成）
