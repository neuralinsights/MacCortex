# Week 4 Day 6-7: Slow Lane UI 设计文档

> **任务**: Slow Lane (Swarm Orchestration) 前端集成
> **日期**: 2026-01-22
> **状态**: 设计阶段
> **技术栈**: SwiftUI (Frontend) + FastAPI (Backend) + WebSocket (Real-time)

---

## 1. 执行摘要

### 目标

为 MacCortex Slow Lane (LangGraph Swarm 编排系统) 创建完整的原生 macOS UI，实现：

1. **任务提交界面** - 自然语言输入 + 上下文附件
2. **工作流可视化** - 实时显示 Agent 执行状态
3. **HITL 交互界面** - 工具审批、代码审查、决策确认
4. **历史记录管理** - 查看、搜索、恢复过往任务

### 核心价值

- **零学习曲线**: 自然语言输入，无需编程知识
- **全程可控**: 每个关键操作都可人工审批
- **可追溯性**: 完整的执行历史与状态快照
- **原生体验**: SwiftUI + macOS 设计语言

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                  MacCortex (SwiftUI App)                     │
├─────────────────────────────────────────────────────────────┤
│  Slow Lane UI  (Week 4 Day 6-7)                             │
│  ├─ TaskSubmissionView                                       │
│  ├─ WorkflowVisualizationView                               │
│  ├─ HITLInteractionView                                      │
│  └─ HistoryView                                              │
├─────────────────────────────────────────────────────────────┤
│  SwarmAPIClient (Swift)                                      │
│  ├─ RESTful API (任务提交、状态查询)                         │
│  └─ WebSocket (实时状态更新)                                 │
├─────────────────────────────────────────────────────────────┤
│  Backend FastAPI Server (Python)                             │
│  ├─ POST /swarm/tasks - 创建任务                             │
│  ├─ GET /swarm/tasks/{id} - 查询状态                         │
│  ├─ POST /swarm/tasks/{id}/approve - HITL 审批               │
│  └─ WebSocket /swarm/ws/{id} - 实时推送                      │
├─────────────────────────────────────────────────────────────┤
│  LangGraph Swarm Orchestration (Python)                      │
│  └─ Planner → Coder → Reviewer → ToolRunner → Reflector     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 版本 | 用途 |
|------|----------|------|------|
| **前端** | SwiftUI | macOS 13+ | UI 框架 |
| **前端** | Combine | macOS 13+ | 响应式编程 |
| **前端** | URLSession | macOS 13+ | HTTP 客户端 |
| **前端** | Starscream | 4.0+ | WebSocket 客户端 |
| **后端** | FastAPI | 0.115+ | REST API |
| **后端** | Uvicorn | 0.32+ | ASGI 服务器 |
| **后端** | python-socketio | 5.11+ | WebSocket 服务器 |
| **后端** | LangGraph | 0.2.31+ | 工作流引擎 |

---

## 3. 前端 UI 设计

### 3.1 主视图结构

```swift
// Week 4 Day 6-7 新增视图
SwarmOrchestrationView (主视图)
├─ TaskInputSection (任务输入)
│  ├─ TextEditor (自然语言输入)
│  ├─ FileAttachmentList (附件列表)
│  └─ SubmitButton (提交按钮)
│
├─ WorkflowVisualizationSection (工作流可视化)
│  ├─ AgentStageView (Agent 阶段显示)
│  │  └─ For each: Planner, Coder, Reviewer, etc.
│  ├─ ProgressIndicator (进度条)
│  └─ CurrentStepDetail (当前步骤详情)
│
├─ HITLApprovalSheet (HITL 审批弹窗)
│  ├─ OperationDetailView (操作详情)
│  ├─ RiskLevelBadge (风险等级)
│  └─ ApprovalButtons (approve/deny/modify/abort)
│
└─ HistoryView (历史记录)
   ├─ TaskListView (任务列表)
   ├─ SearchBar (搜索栏)
   └─ TaskDetailView (详情查看)
```

### 3.2 视图层级详细设计

#### 3.2.1 SwarmOrchestrationView (主视图)

**功能**:
- 统一入口，包含任务输入、工作流可视化、历史记录
- 支持标签页切换（Task、History）

**布局**:
```
┌────────────────────────────────────────────────────┐
│  🤖 Slow Lane - AI Swarm Orchestration             │
├────────────────────────────────────────────────────┤
│  [Task]  [History]                                  │
├────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐ │
│  │ 📝 What would you like me to do?             │ │
│  │                                               │ │
│  │ (Multi-line text editor)                     │ │
│  │                                               │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  📎 Attachments: [+ Add File] [workspace.txt]     │
│                                                    │
│  [Submit Task] ──────────────────────────────────│
│                                                    │
│  ╔══════════════════════════════════════════════╗ │
│  ║ 🔄 Current Workflow                          ║ │
│  ╠══════════════════════════════════════════════╣ │
│  ║ ✅ Planner      - Task decomposition        ║ │
│  ║ 🔵 Coder        - Generating code...         ║ │
│  ║ ⚪ Reviewer     - Pending                     ║ │
│  ║ ⚪ ToolRunner   - Pending                     ║ │
│  ║ ⚪ Reflector    - Pending                     ║ │
│  ╚══════════════════════════════════════════════╝ │
│                                                    │
│  Progress: ████████████░░░░░░░░ 60%               │
└────────────────────────────────────────────────────┘
```

#### 3.2.2 HITLApprovalSheet (HITL 审批弹窗)

**功能**:
- 当工作流触发 HITL 中断时弹出
- 显示操作详情、风险等级、参数
- 提供 4 种决策按钮（approve/deny/modify/abort）

**布局**:
```
┌────────────────────────────────────────────────────┐
│  ⚠️  Approval Required                              │
├────────────────────────────────────────────────────┤
│  Operation Type: Tool Execution                     │
│  Tool Name: write_file                              │
│  Risk Level: 🟡 MEDIUM                              │
│                                                     │
│  ╔═══════════════════════════════════════════════╗ │
│  ║ Parameters:                                   ║ │
│  ║ • path: /workspace/hello.txt                  ║ │
│  ║ • content: Hello, MacCortex!                  ║ │
│  ╚═══════════════════════════════════════════════╝ │
│                                                     │
│  ℹ️  This operation will write a new file to your │
│     workspace.                                      │
│                                                     │
│  [Approve] [Deny] [Modify...] [Abort Workflow]     │
└────────────────────────────────────────────────────┘
```

**决策按钮行为**:
- **Approve**: 绿色按钮，继续执行
- **Deny**: 红色按钮，跳过此操作并继续
- **Modify**: 黄色按钮，打开参数编辑器
- **Abort**: 灰色按钮，终止整个工作流

#### 3.2.3 WorkflowVisualizationSection (工作流可视化)

**功能**:
- 实时显示 Agent 执行状态
- 使用状态图标（✅ 完成、🔵 进行中、⚪ 待执行、❌ 失败）
- 展开/折叠每个 Agent 的详细日志

**状态枚举**:
```swift
enum AgentStatus {
    case pending      // 待执行
    case running      // 执行中
    case completed    // 已完成
    case failed       // 失败
    case interrupted  // 中断（等待 HITL）
}
```

**AgentStageView 组件**:
```
┌─────────────────────────────────────────────┐
│  ✅ Planner Agent                          │
│  └─ Task decomposition completed           │
│      • Subtask 1: Create hello.txt         │
│      • Subtask 2: Write content            │
│      [View Full Output ▼]                  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🔵 Coder Agent (Running...)               │
│  └─ Generating code for subtask 1          │
│      Progress: ████░░░░░ 40%                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  ⚠️  ToolRunner Agent (Awaiting Approval)  │
│  └─ Tool: write_file                        │
│      [Approve Now]                          │
└─────────────────────────────────────────────┘
```

#### 3.2.4 HistoryView (历史记录)

**功能**:
- 显示所有过往任务
- 支持搜索、过滤、排序
- 点击查看详情、恢复任务

**布局**:
```
┌────────────────────────────────────────────────────┐
│  🔍 Search: [_________________________] [Filter▼]  │
├────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐ │
│  │ ✅ Create a hello world program              │ │
│  │    Status: Completed                          │ │
│  │    Time: 2026-01-22 14:30                     │ │
│  │    Duration: 2m 34s                           │ │
│  │    [View Details] [Resume]                    │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │ ❌ Analyze large codebase                     │ │
│  │    Status: Failed                             │ │
│  │    Error: Timeout exceeded                    │ │
│  │    Time: 2026-01-22 12:00                     │ │
│  │    [View Details] [Retry]                     │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

---

## 4. Backend API 设计

### 4.1 RESTful API Endpoints

#### 4.1.1 创建任务

**Endpoint**: `POST /swarm/tasks`

**Request Body**:
```json
{
  "user_input": "Create a hello world program in Python",
  "workspace_path": "/Users/jamesg/workspace",
  "attachments": [
    {
      "type": "file",
      "path": "/Users/jamesg/context.txt"
    }
  ],
  "enable_hitl": true,
  "enable_code_review": false
}
```

**Response**:
```json
{
  "task_id": "task_20260122_143000",
  "status": "created",
  "created_at": "2026-01-22T14:30:00+13:00",
  "websocket_url": "ws://localhost:8000/swarm/ws/task_20260122_143000"
}
```

#### 4.1.2 查询任务状态

**Endpoint**: `GET /swarm/tasks/{task_id}`

**Response**:
```json
{
  "task_id": "task_20260122_143000",
  "status": "running",
  "current_agent": "coder",
  "progress": 0.60,
  "created_at": "2026-01-22T14:30:00+13:00",
  "updated_at": "2026-01-22T14:32:30+13:00",
  "agents_status": {
    "planner": "completed",
    "coder": "running",
    "reviewer": "pending",
    "tool_runner": "pending",
    "reflector": "pending"
  },
  "interrupts": []
}
```

#### 4.1.3 HITL 审批

**Endpoint**: `POST /swarm/tasks/{task_id}/approve`

**Request Body**:
```json
{
  "interrupt_id": "int_001",
  "action": "approve",
  "modified_data": {}
}
```

**Response**:
```json
{
  "success": true,
  "message": "Approval processed, workflow resumed"
}
```

#### 4.1.4 获取任务历史

**Endpoint**: `GET /swarm/tasks`

**Query Parameters**:
- `status`: `all` | `completed` | `failed` | `running`
- `limit`: 默认 20
- `offset`: 默认 0

**Response**:
```json
{
  "tasks": [
    {
      "task_id": "task_20260122_143000",
      "user_input": "Create a hello world program",
      "status": "completed",
      "created_at": "2026-01-22T14:30:00+13:00",
      "duration": 154.5
    }
  ],
  "total": 10,
  "has_more": false
}
```

### 4.2 WebSocket 实时推送

**Endpoint**: `ws://localhost:8000/swarm/ws/{task_id}`

**连接后接收的消息类型**:

#### 4.2.1 Agent 状态更新

```json
{
  "type": "agent_status",
  "agent": "coder",
  "status": "running",
  "timestamp": "2026-01-22T14:32:30+13:00",
  "data": {
    "subtask": "Generate Python code for hello world"
  }
}
```

#### 4.2.2 进度更新

```json
{
  "type": "progress",
  "progress": 0.60,
  "current_step": "Code generation",
  "total_steps": 5
}
```

#### 4.2.3 HITL 中断通知

```json
{
  "type": "hitl_interrupt",
  "interrupt_id": "int_001",
  "operation": "tool_execution",
  "tool_name": "write_file",
  "risk_level": "medium",
  "details": {
    "path": "/workspace/hello.py",
    "content": "print('Hello, World!')"
  }
}
```

#### 4.2.4 任务完成

```json
{
  "type": "task_completed",
  "status": "success",
  "output": {
    "files_created": ["hello.py"],
    "summary": "Successfully created a Python hello world program"
  }
}
```

#### 4.2.5 错误通知

```json
{
  "type": "error",
  "error_code": "TIMEOUT",
  "message": "Task execution exceeded maximum time limit"
}
```

---

## 5. 数据模型

### 5.1 Swift 数据模型

#### 5.1.1 SwarmTask (任务模型)

```swift
struct SwarmTask: Identifiable, Codable {
    let id: String
    let userInput: String
    let workspacePath: String
    let status: TaskStatus
    let progress: Double
    let currentAgent: String?
    let agentsStatus: [String: AgentStatus]
    let createdAt: Date
    let updatedAt: Date
    let interrupts: [HITLInterrupt]
    let output: TaskOutput?

    enum CodingKeys: String, CodingKey {
        case id = "task_id"
        case userInput = "user_input"
        case workspacePath = "workspace_path"
        case status
        case progress
        case currentAgent = "current_agent"
        case agentsStatus = "agents_status"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case interrupts
        case output
    }
}

enum TaskStatus: String, Codable {
    case created
    case running
    case completed
    case failed
    case interrupted
}

enum AgentStatus: String, Codable {
    case pending
    case running
    case completed
    case failed
    case interrupted
}
```

#### 5.1.2 HITLInterrupt (HITL 中断模型)

```swift
struct HITLInterrupt: Identifiable, Codable {
    let id: String
    let operation: String
    let toolName: String?
    let riskLevel: RiskLevel
    let details: [String: AnyCodable]

    enum CodingKeys: String, CodingKey {
        case id = "interrupt_id"
        case operation
        case toolName = "tool_name"
        case riskLevel = "risk_level"
        case details
    }
}

enum RiskLevel: String, Codable {
    case low
    case medium
    case high

    var color: Color {
        switch self {
        case .low: return .green
        case .medium: return .yellow
        case .high: return .red
        }
    }

    var emoji: String {
        switch self {
        case .low: return "🟢"
        case .medium: return "🟡"
        case .high: return "🔴"
        }
    }
}
```

#### 5.1.3 HITLApproval (审批决策模型)

```swift
struct HITLApproval: Codable {
    let interruptId: String
    let action: ApprovalAction
    let modifiedData: [String: AnyCodable]?

    enum CodingKeys: String, CodingKey {
        case interruptId = "interrupt_id"
        case action
        case modifiedData = "modified_data"
    }
}

enum ApprovalAction: String, Codable {
    case approve
    case deny
    case modify
    case abort
}
```

### 5.2 WebSocket 消息模型

```swift
struct WSMessage: Codable {
    let type: WSMessageType
    let data: AnyCodable
    let timestamp: Date
}

enum WSMessageType: String, Codable {
    case agentStatus = "agent_status"
    case progress
    case hitlInterrupt = "hitl_interrupt"
    case taskCompleted = "task_completed"
    case error
}
```

---

## 6. 核心组件实现

### 6.1 SwarmAPIClient (Swift)

**职责**:
- 封装所有与 Backend 的通信
- 管理 WebSocket 连接
- 提供 Combine Publishers 用于 UI 绑定

```swift
import Foundation
import Combine
import Starscream

@MainActor
class SwarmAPIClient: ObservableObject {
    // MARK: - Published Properties
    @Published var currentTask: SwarmTask?
    @Published var connectionStatus: ConnectionStatus = .disconnected
    @Published var activeInterrupt: HITLInterrupt?

    // MARK: - Private Properties
    private let baseURL: URL
    private var webSocket: WebSocket?
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization
    init(baseURL: URL = URL(string: "http://localhost:8000")!) {
        self.baseURL = baseURL
    }

    // MARK: - Task Management
    func createTask(
        userInput: String,
        workspacePath: String,
        enableHITL: Bool = true
    ) async throws -> String {
        let url = baseURL.appendingPathComponent("/swarm/tasks")

        let requestBody: [String: Any] = [
            "user_input": userInput,
            "workspace_path": workspacePath,
            "enable_hitl": enableHITL
        ]

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.invalidResponse
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let createResponse = try decoder.decode(CreateTaskResponse.self, from: data)

        // Connect to WebSocket for real-time updates
        connectWebSocket(taskId: createResponse.taskId)

        return createResponse.taskId
    }

    func fetchTaskStatus(taskId: String) async throws -> SwarmTask {
        let url = baseURL.appendingPathComponent("/swarm/tasks/\(taskId)")

        let (data, _) = try await URLSession.shared.data(from: url)

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let task = try decoder.decode(SwarmTask.self, from: data)

        await MainActor.run {
            self.currentTask = task
        }

        return task
    }

    func approveInterrupt(
        taskId: String,
        interruptId: String,
        action: ApprovalAction,
        modifiedData: [String: Any]? = nil
    ) async throws {
        let url = baseURL.appendingPathComponent("/swarm/tasks/\(taskId)/approve")

        let approval = HITLApproval(
            interruptId: interruptId,
            action: action,
            modifiedData: modifiedData?.mapValues { AnyCodable($0) }
        )

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let encoder = JSONEncoder()
        request.httpBody = try encoder.encode(approval)

        let (_, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.invalidResponse
        }

        await MainActor.run {
            self.activeInterrupt = nil
        }
    }

    // MARK: - WebSocket Management
    private func connectWebSocket(taskId: String) {
        let wsURL = URL(string: "ws://localhost:8000/swarm/ws/\(taskId)")!

        var request = URLRequest(url: wsURL)
        request.timeoutInterval = 5

        webSocket = WebSocket(request: request)
        webSocket?.delegate = self
        webSocket?.connect()

        connectionStatus = .connecting
    }

    func disconnectWebSocket() {
        webSocket?.disconnect()
        webSocket = nil
        connectionStatus = .disconnected
    }
}

// MARK: - WebSocketDelegate
extension SwarmAPIClient: WebSocketDelegate {
    nonisolated func didReceive(
        event: Starscream.WebSocketEvent,
        client: Starscream.WebSocketClient
    ) {
        Task { @MainActor in
            switch event {
            case .connected:
                connectionStatus = .connected

            case .disconnected(let reason, let code):
                connectionStatus = .disconnected
                print("WebSocket disconnected: \(reason) code: \(code)")

            case .text(let string):
                handleWebSocketMessage(string)

            case .error(let error):
                print("WebSocket error: \(error?.localizedDescription ?? "unknown")")

            default:
                break
            }
        }
    }

    @MainActor
    private func handleWebSocketMessage(_ text: String) {
        guard let data = text.data(using: .utf8) else { return }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        do {
            let message = try decoder.decode(WSMessage.self, from: data)

            switch message.type {
            case .agentStatus:
                // Update agent status
                if var task = currentTask {
                    // Update logic...
                    currentTask = task
                }

            case .progress:
                // Update progress
                if var task = currentTask,
                   let progressData = message.data.value as? [String: Any],
                   let progress = progressData["progress"] as? Double {
                    task.progress = progress
                    currentTask = task
                }

            case .hitlInterrupt:
                // Show HITL approval UI
                let interrupt = try decoder.decode(HITLInterrupt.self, from: data)
                activeInterrupt = interrupt

            case .taskCompleted:
                // Mark task as completed
                if var task = currentTask {
                    task.status = .completed
                    currentTask = task
                }
                disconnectWebSocket()

            case .error:
                // Handle error
                print("Task error received")
            }

        } catch {
            print("Failed to decode WebSocket message: \(error)")
        }
    }
}

// MARK: - Supporting Types
enum ConnectionStatus {
    case disconnected
    case connecting
    case connected
}

enum APIError: Error {
    case invalidResponse
    case decodingError
}

struct CreateTaskResponse: Codable {
    let taskId: String
    let status: String
    let websocketUrl: String

    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case status
        case websocketUrl = "websocket_url"
    }
}
```

### 6.2 SwarmViewModel (SwiftUI ViewModel)

```swift
import Foundation
import Combine

@MainActor
class SwarmViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var userInput: String = ""
    @Published var isSubmitting: Bool = false
    @Published var currentTask: SwarmTask?
    @Published var showHITLSheet: Bool = false
    @Published var taskHistory: [SwarmTask] = []

    // MARK: - Private Properties
    private let apiClient: SwarmAPIClient
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization
    init(apiClient: SwarmAPIClient = SwarmAPIClient()) {
        self.apiClient = apiClient

        // Bind API client to ViewModel
        apiClient.$currentTask
            .assign(to: &$currentTask)

        apiClient.$activeInterrupt
            .map { $0 != nil }
            .assign(to: &$showHITLSheet)
    }

    // MARK: - Task Actions
    func submitTask(workspacePath: String) {
        guard !userInput.isEmpty else { return }

        isSubmitting = true

        Task {
            do {
                let taskId = try await apiClient.createTask(
                    userInput: userInput,
                    workspacePath: workspacePath,
                    enableHITL: true
                )

                print("Task created: \(taskId)")

                // Clear input
                userInput = ""

            } catch {
                print("Failed to submit task: \(error)")
            }

            isSubmitting = false
        }
    }

    func approveInterrupt(action: ApprovalAction) {
        guard let task = currentTask,
              let interrupt = apiClient.activeInterrupt else {
            return
        }

        Task {
            do {
                try await apiClient.approveInterrupt(
                    taskId: task.id,
                    interruptId: interrupt.id,
                    action: action
                )

            } catch {
                print("Failed to approve interrupt: \(error)")
            }
        }
    }

    func loadHistory() {
        // TODO: Load task history from API
        Task {
            // Implement in Week 5
        }
    }
}
```

---

## 7. 实施计划

### Day 6（2026-01-22）

#### 上午（3-4 小时）

1. **Backend API 实现** ✅
   - [ ] 创建 `backend/api/swarm_routes.py`
   - [ ] 实现 POST /swarm/tasks
   - [ ] 实现 GET /swarm/tasks/{id}
   - [ ] 实现 POST /swarm/tasks/{id}/approve
   - [ ] 集成 LangGraph Swarm

2. **WebSocket 实现** ✅
   - [ ] 安装 python-socketio
   - [ ] 实现 WebSocket /swarm/ws/{id}
   - [ ] 实现实时状态推送

#### 下午（3-4 小时）

3. **SwiftUI 基础组件** ✅
   - [ ] 创建 `SwarmOrchestrationView.swift`
   - [ ] 创建 `TaskInputSection.swift`
   - [ ] 创建 `SwarmAPIClient.swift`
   - [ ] 创建 `SwarmViewModel.swift`

### Day 7（2026-01-23）

#### 上午（3-4 小时）

4. **工作流可视化** ✅
   - [ ] 创建 `WorkflowVisualizationSection.swift`
   - [ ] 创建 `AgentStageView.swift`
   - [ ] 实现 WebSocket 数据绑定

5. **HITL 交互界面** ✅
   - [ ] 创建 `HITLApprovalSheet.swift`
   - [ ] 实现 4 种决策按钮
   - [ ] 集成审批 API

#### 下午（3-4 小时）

6. **历史记录与测试** ✅
   - [ ] 创建 `HistoryView.swift`
   - [ ] 实现搜索、过滤功能
   - [ ] 端到端测试

---

## 8. 验收标准

| # | 验收项 | 测试方法 | 期望结果 |
|---|--------|----------|----------|
| 1 | Backend API 可用 | curl 测试所有 endpoint | 200 OK |
| 2 | WebSocket 实时推送 | 提交任务并观察状态更新 | 实时更新 UI |
| 3 | 任务提交成功 | UI 提交任务 | 任务创建并开始执行 |
| 4 | 工作流可视化 | 观察 Agent 状态变化 | 实时显示每个 Agent 状态 |
| 5 | HITL 审批流程 | 触发 HITL 并审批 | 弹窗显示，审批后继续 |
| 6 | 任务完成通知 | 等待任务完成 | UI 显示完成状态 |
| 7 | 历史记录查看 | 查看过往任务 | 显示所有历史任务 |
| 8 | 错误处理 | 故意触发错误 | 显示清晰错误信息 |

---

## 9. 技术难点与解决方案

### 9.1 WebSocket 连接稳定性

**难点**: WebSocket 可能因网络波动断开连接

**解决方案**:
- 实现自动重连机制（指数退避）
- 在连接断开时显示提示
- 断开期间缓存状态，重连后同步

### 9.2 并发任务管理

**难点**: 用户可能同时提交多个任务

**解决方案**:
- 使用任务队列（Backend）
- UI 显示队列状态
- 支持取消排队任务

### 9.3 HITL 超时处理

**难点**: 用户长时间不响应 HITL 审批

**解决方案**:
- 设置审批超时（默认 5 分钟）
- 超时后自动 deny 或 abort
- 显示倒计时提醒

### 9.4 大文件附件上传

**难点**: 用户可能附加大文件作为上下文

**解决方案**:
- 限制单个文件大小（< 10MB）
- 使用流式上传
- 显示上传进度

---

## 10. 未来增强（Week 5+）

### 10.1 高级功能

- **模板化任务**: 保存常用任务作为模板
- **批量操作**: 同时处理多个文件
- **智能建议**: 根据历史记录推荐常用操作
- **导出报告**: 生成 PDF/Markdown 格式的任务报告

### 10.2 性能优化

- **本地缓存**: 缓存任务状态，减少 API 调用
- **懒加载**: 历史记录分页加载
- **后台执行**: 支持后台运行长时间任务

### 10.3 用户体验

- **键盘快捷键**: 快速提交、审批等操作
- **暗黑模式**: 支持 macOS 系统主题
- **通知中心**: macOS 原生通知提醒

---

## 11. 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 | 残余风险 |
|------|------|------|----------|----------|
| WebSocket 兼容性问题 | 20% | 中 | 充分测试，提供 polling 降级 | 🟢 低 |
| UI 性能问题（大量日志） | 30% | 中 | 限制日志显示条数，虚拟滚动 | 🟡 中 |
| HITL 超时导致任务阻塞 | 10% | 高 | 实现超时自动处理 | 🟢 低 |
| Backend API 不稳定 | 5% | 高 | 集成测试 + 错误重试 | 🟢 低 |

**总体风险评分**: 🟢 **可控**

---

## 12. 参考资料

### 官方文档

1. [SwiftUI Documentation](https://developer.apple.com/documentation/swiftui) (Apple)
2. [Combine Framework](https://developer.apple.com/documentation/combine) (Apple)
3. [FastAPI Documentation](https://fastapi.tiangolo.com/) (Tiangolo)
4. [Starscream WebSocket Library](https://github.com/daltoniam/Starscream) (GitHub)

### 最佳实践

5. [Building Real-time Apps with SwiftUI and WebSocket](https://www.swiftbysundell.com/articles/websockets-in-swiftui/) (Swift by Sundell, 2024)
6. [FastAPI WebSocket Tutorial](https://fastapi.tiangolo.com/advanced/websockets/) (FastAPI Docs)

---

**文档状态**: ✅ **已批准，准备实施**

**创建时间**: 2026-01-22 22:00:00 +1300 (NZDT)
**作者**: Claude Code (Sonnet 4.5)
**版本**: v1.0
