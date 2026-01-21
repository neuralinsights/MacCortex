# MacCortex Xcode 项目迁移指南

> **版本**: v1.0
> **日期**: 2026-01-22
> **目标**: 从 Swift Package Manager (SPM) 迁移到 Xcode Workspace
> **适用**: Phase 3 Week 2 SwiftUI Desktop GUI 开发

---

## 执行摘要

MacCortex Phase 3 需要从 SPM 命令行工具迁移到 Xcode 完整项目，以支持 SwiftUI Desktop GUI 开发。本指南提供完整的迁移步骤，预计耗时 **30-45 分钟**。

### 迁移目标

| 项目 | Phase 2 (SPM) | Phase 3 (Xcode) |
|------|--------------|-----------------|
| **构建系统** | SwiftPM CLI | Xcode Build System |
| **界面** | 无 GUI（CLI only） | SwiftUI Desktop GUI |
| **依赖管理** | Package.swift | SPM + CocoaPods 混合 |
| **调试** | LLDB CLI | Xcode 图形化调试器 |
| **资源管理** | 无 | Assets.xcassets + Storyboards |

---

## 前置准备

### 1. 环境检查

运行以下命令验证环境：

```bash
# 检查 Xcode 版本（需要 Xcode 15.0+）
xcodebuild -version
# 预期输出: Xcode 15.x 或更高

# 检查 Swift 版本（需要 Swift 5.9+）
swift --version
# 预期输出: Swift version 5.9.x 或更高

# 检查 Git 状态（确保无未提交变更）
cd /Users/jamesg/projects/MacCortex
git status
# 预期输出: "working tree clean"

# 如有未提交变更，先提交
git add .
git commit -m "Pre-migration checkpoint"
```

### 2. 备份当前项目

```bash
# 创建备份分支
git checkout -b backup/pre-xcode-migration
git push -u origin backup/pre-xcode-migration

# 返回主分支
git checkout main

# 创建备份压缩包（可选）
cd ..
tar -czf MacCortex_backup_$(date +%Y%m%d).tar.gz MacCortex/
```

### 3. 确认现有结构

```bash
cd /Users/jamesg/projects/MacCortex
tree -L 2 -I 'Backend'
# 预期结构:
# MacCortex/
# ├── Sources/
# │   └── MacCortexApp/
# ├── Tests/
# ├── Package.swift
# ├── README.md
# └── ...
```

---

## 迁移步骤

### Step 1: 创建 Xcode Workspace（5 分钟）

#### 1.1 打开 Xcode

```bash
# 方式 1: 使用 Xcode 打开当前目录
open -a Xcode .

# 方式 2: 直接打开 Package.swift
open Package.swift
```

Xcode 会自动识别 SPM 项目并加载。

---

#### 1.2 生成 Xcode 项目

**在 Xcode 中**:

1. 菜单栏 → `File` → `New` → `Project...`
2. 选择模板：
   - **macOS** → **App**
3. 配置项目：
   - **Product Name**: `MacCortex`
   - **Team**: 选择你的 Apple Developer 账户（或 "None"）
   - **Organization Identifier**: `com.yourdomain`（与现有 Package.swift 一致）
   - **Bundle Identifier**: `com.yourdomain.MacCortex`
   - **Language**: `Swift`
   - **User Interface**: `SwiftUI`
   - **Storage**: `None`（不需要 Core Data）
   - **Include Tests**: ✅ 勾选
4. 保存位置：
   - 选择 `/Users/jamesg/projects/MacCortex-Xcode`（新目录，避免覆盖）
   - ⚠️ **不要**选择现有的 `MacCortex/` 目录

---

#### 1.3 创建 Workspace

**目的**: 将 Xcode 项目与 Backend（Python）分离，便于管理。

1. 关闭当前 Xcode 窗口
2. 菜单栏 → `File` → `New` → `Workspace...`
3. 命名: `MacCortex.xcworkspace`
4. 保存位置: `/Users/jamesg/projects/MacCortex/`（项目根目录）
5. 添加项目到 Workspace:
   - 在左侧导航栏右键 → `Add Files to "MacCortex"...`
   - 选择 `/Users/jamesg/projects/MacCortex-Xcode/MacCortex.xcodeproj`
   - 点击 `Add`

**结构验证**:
```
MacCortex/
├── MacCortex.xcworkspace/        # ← 新增
│   └── contents.xcworkspacedata
├── MacCortex-Xcode/              # ← 新增（Xcode 项目）
│   ├── MacCortex.xcodeproj/
│   ├── MacCortex/
│   │   ├── MacCortexApp.swift
│   │   ├── ContentView.swift
│   │   └── Assets.xcassets
│   └── MacCortexTests/
├── Backend/                      # ← 现有（Python 后端）
├── Sources/                      # ← 现有（SPM 源码，保留作参考）
└── Package.swift                 # ← 现有（SPM 配置，保留）
```

---

### Step 2: 迁移代码与资源（10 分钟）

#### 2.1 复制现有 Swift 代码

```bash
# 复制 Sources/ 中的代码到 Xcode 项目
cp -r Sources/MacCortexApp/* MacCortex-Xcode/MacCortex/

# 如果有共享代码（如 Models/）
cp -r Sources/Shared/* MacCortex-Xcode/MacCortex/Shared/
```

**在 Xcode 中验证**:
1. 打开 `MacCortex.xcworkspace`
2. 检查 `MacCortex` 项目 → `MacCortex` 文件夹
3. 确认所有 `.swift` 文件已导入
4. 如有缺失，右键 `MacCortex` 文件夹 → `Add Files to "MacCortex"...`

---

#### 2.2 配置 Info.plist

**编辑 `MacCortex-Xcode/MacCortex/Info.plist`**（如果不存在则创建）:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>MacCortex</string>
    <key>CFBundleDisplayName</key>
    <string>MacCortex</string>
    <key>CFBundleIdentifier</key>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026. All rights reserved.</string>

    <!-- Full Disk Access 权限 -->
    <key>NSAppleEventsUsageDescription</key>
    <string>MacCortex 需要访问 Notes.app 以读取笔记内容。</string>

    <!-- 网络权限（DuckDuckGo Search） -->
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
</dict>
</plist>
```

---

#### 2.3 配置 Entitlements

**创建 `MacCortex-Xcode/MacCortex/MacCortex.entitlements`**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Hardened Runtime -->
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>

    <!-- 网络访问 -->
    <key>com.apple.security.network.client</key>
    <true/>

    <!-- Apple Events（AppleScript/JXA） -->
    <key>com.apple.security.automation.apple-events</key>
    <true/>
</dict>
</plist>
```

**在 Xcode 中关联 Entitlements**:
1. 选择项目 `MacCortex` → Target `MacCortex`
2. `Signing & Capabilities` 标签
3. `+ Capability` → 搜索 `Hardened Runtime`
4. 在 `Code Signing Entitlements` 中选择 `MacCortex.entitlements`

---

#### 2.4 添加 Assets

**创建图标**（可选，Phase 3 Week 2 完成）:

1. 在 Xcode 中打开 `Assets.xcassets`
2. 右键 → `New Image Set`
3. 命名: `AppIcon`
4. 拖拽图标文件（1024x1024 PNG）

**当前可使用占位符图标**:
- Xcode 会生成默认图标
- Phase 3 Week 3 再设计正式图标

---

### Step 3: 配置 Build Settings（10 分钟）

#### 3.1 基础配置

**在 Xcode 中**:

1. 选择项目 `MacCortex` → Target `MacCortex`
2. `Build Settings` 标签
3. 搜索并设置以下项（All + Combined）:

| 设置项 | 值 | 说明 |
|--------|---|------|
| `Deployment Target` | `14.0` | macOS 14.0+ |
| `Swift Language Version` | `Swift 5` | Swift 5.9+ |
| `Code Signing Identity` | `Apple Development` | 本地开发 |
| `Product Bundle Identifier` | `com.yourdomain.MacCortex` | 与 Info.plist 一致 |
| `Enable Hardened Runtime` | `YES` | 安全加固 |
| `Other Swift Flags` | `-D DEBUG` (Debug only) | 调试标志 |

---

#### 3.2 代码签名配置

**自动签名（推荐）**:
1. `Signing & Capabilities` 标签
2. 勾选 `Automatically manage signing`
3. 选择 `Team`（你的 Apple Developer 账户）
4. Xcode 会自动生成 Provisioning Profile

**手动签名**（高级用户）:
1. 取消勾选 `Automatically manage signing`
2. 手动选择 `Provisioning Profile`
3. 确保证书与 Entitlements 匹配

---

#### 3.3 配置 Scheme

**编辑 Scheme**:
1. 菜单栏 → `Product` → `Scheme` → `Edit Scheme...`
2. `Run` → `Arguments` 标签
3. 添加环境变量（与 Backend 通信）:
   - `BACKEND_URL`: `http://localhost:8000`
   - `LOG_LEVEL`: `DEBUG`（Debug 模式）
4. 点击 `Close`

---

### Step 4: 集成 Backend 通信（10 分钟）

#### 4.1 创建网络层

**创建 `MacCortex-Xcode/MacCortex/Services/BackendClient.swift`**:

```swift
import Foundation

@MainActor
class BackendClient: ObservableObject {
    static let shared = BackendClient()

    let baseURL = URL(string: "http://localhost:8000")!

    @Published var isConnected = false

    func healthCheck() async -> Bool {
        guard let url = URL(string: "/health", relativeTo: baseURL) else {
            return false
        }

        do {
            let (data, response) = try await URLSession.shared.data(from: url)

            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                return false
            }

            let health = try JSONDecoder().decode(HealthResponse.self, from: data)
            isConnected = health.status == "healthy"
            return isConnected
        } catch {
            print("Health check failed: \(error)")
            isConnected = false
            return false
        }
    }

    func executePattern(
        patternId: String,
        text: String,
        parameters: [String: Any] = [:]
    ) async throws -> PatternResult {
        guard let url = URL(string: "/execute", relativeTo: baseURL) else {
            throw BackendError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "pattern_id": patternId,
            "text": text,
            "parameters": parameters
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw BackendError.requestFailed
        }

        return try JSONDecoder().decode(PatternResult.self, from: data)
    }
}

// MARK: - Models

struct HealthResponse: Codable {
    let status: String
    let timestamp: String
    let version: String
    let uptime: Double
    let patterns_loaded: Int
}

struct PatternResult: Codable {
    let request_id: String
    let success: Bool
    let output: String
    let metadata: [String: AnyCodable]
    let error: String?
    let duration: Double
}

struct AnyCodable: Codable {
    let value: Any

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let intValue = try? container.decode(Int.self) {
            value = intValue
        } else if let doubleValue = try? container.decode(Double.self) {
            value = doubleValue
        } else if let stringValue = try? container.decode(String.self) {
            value = stringValue
        } else if let boolValue = try? container.decode(Bool.self) {
            value = boolValue
        } else {
            value = ""
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(String(describing: value))
    }
}

enum BackendError: LocalizedError {
    case invalidURL
    case requestFailed

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid backend URL"
        case .requestFailed:
            return "Backend request failed"
        }
    }
}
```

---

#### 4.2 更新主界面集成

**编辑 `MacCortex-Xcode/MacCortex/ContentView.swift`**:

```swift
import SwiftUI

struct ContentView: View {
    @StateObject private var backendClient = BackendClient.shared
    @State private var inputText = ""
    @State private var outputText = ""
    @State private var selectedPattern = "summarize"
    @State private var isProcessing = false

    let patterns = ["summarize", "extract", "translate", "format", "search"]

    var body: some View {
        VStack(spacing: 0) {
            // 顶部工具栏
            HStack {
                Picker("Pattern", selection: $selectedPattern) {
                    ForEach(patterns, id: \.self) { pattern in
                        Text(pattern.capitalized).tag(pattern)
                    }
                }
                .frame(width: 200)

                Spacer()

                Button(action: executePattern) {
                    Label("执行", systemImage: "play.fill")
                }
                .disabled(inputText.isEmpty || isProcessing)
                .keyboardShortcut(.return, modifiers: .command)

                // 连接状态指示器
                Circle()
                    .fill(backendClient.isConnected ? Color.green : Color.red)
                    .frame(width: 10, height: 10)
            }
            .padding()

            Divider()

            // 输入区域
            VStack(alignment: .leading, spacing: 8) {
                Text("输入文本")
                    .font(.headline)
                TextEditor(text: $inputText)
                    .font(.system(.body, design: .monospaced))
                    .frame(minHeight: 150)
                    .border(Color.gray.opacity(0.3))
            }
            .padding()

            Divider()

            // 输出区域
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("输出结果")
                        .font(.headline)
                    Spacer()
                    if isProcessing {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                }

                TextEditor(text: .constant(outputText))
                    .font(.system(.body, design: .monospaced))
                    .frame(minHeight: 150)
                    .border(Color.gray.opacity(0.3))
            }
            .padding()
        }
        .frame(minWidth: 600, minHeight: 500)
        .task {
            await checkBackendConnection()
        }
    }

    func checkBackendConnection() async {
        _ = await backendClient.healthCheck()
    }

    func executePattern() {
        isProcessing = true
        outputText = "处理中..."

        Task {
            do {
                let result = try await backendClient.executePattern(
                    patternId: selectedPattern,
                    text: inputText
                )

                outputText = result.output
            } catch {
                outputText = "错误: \(error.localizedDescription)"
            }

            isProcessing = false
        }
    }
}

#Preview {
    ContentView()
}
```

---

### Step 5: 构建与测试（5 分钟）

#### 5.1 首次构建

1. 确保 Backend 服务运行：
   ```bash
   cd /Users/jamesg/projects/MacCortex/Backend/src
   source ../.venv/bin/activate
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. 在 Xcode 中：
   - 菜单栏 → `Product` → `Clean Build Folder` (⇧⌘K)
   - 菜单栏 → `Product` → `Build` (⌘B)
   - 等待构建完成（预计 30-60 秒）

3. 检查构建日志：
   - 如有错误，查看 `Report Navigator`（⌘9）
   - 常见错误见下方"故障排除"章节

---

#### 5.2 运行应用

1. 菜单栏 → `Product` → `Run` (⌘R)
2. 应用启动后验证：
   - ✅ 窗口正常显示
   - ✅ 顶部状态指示器为绿色（Backend 已连接）
   - ✅ 输入文本 → 选择 Pattern → 点击"执行" → 输出结果显示

**测试用例**:
```
输入: "MacCortex 是一个专为 macOS 设计的智能助手，集成了多个 AI Pattern。"
Pattern: summarize
预期输出: "MacCortex：macOS 智能助手，集成多个 AI Pattern。"（简洁摘要）
```

---

#### 5.3 调试配置

**设置断点**:
1. 在 `BackendClient.swift` 的 `executePattern()` 方法第一行点击行号设置断点
2. 重新运行应用 (⌘R)
3. 执行 Pattern 时程序会暂停
4. 使用 `Debug Area`（⌘⇧Y）查看变量

**日志查看**:
- `Debug Area` → `Console` 标签
- 查看 `print()` 输出
- 查看网络请求日志

---

## 故障排除

### 问题 1: 构建失败 - "Module 'XXX' not found"

**原因**: SPM 依赖未正确导入

**解决方案**:
1. 菜单栏 → `File` → `Swift Packages` → `Update to Latest Package Versions`
2. 如果使用 CocoaPods，运行：
   ```bash
   cd MacCortex-Xcode
   pod install
   ```
3. 重新打开 `MacCortex.xcworkspace`（而非 `.xcodeproj`）

---

### 问题 2: 运行时错误 - "Connection refused"

**原因**: Backend 服务未启动

**解决方案**:
```bash
cd /Users/jamesg/projects/MacCortex/Backend/src
source ../.venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 验证服务运行
curl http://localhost:8000/health
```

---

### 问题 3: 代码签名失败

**原因**: 证书或 Entitlements 配置错误

**解决方案**:
1. `Signing & Capabilities` → 勾选 `Automatically manage signing`
2. 选择正确的 `Team`
3. 如果提示"无可用证书"，运行：
   ```bash
   security find-identity -v -p codesigning
   ```
4. 如无证书，在 Xcode → `Preferences` → `Accounts` → 登录 Apple ID

---

### 问题 4: SwiftUI Preview 不工作

**原因**: Preview 需要运行 Backend 服务

**解决方案**:
1. 在 Preview 中使用 Mock 数据（Phase 3 Week 2 实现）
2. 或临时启动 Backend 服务

---

## 验证清单

迁移完成后，请验证以下项：

### 功能验证

- [ ] Xcode 项目成功创建（`MacCortex.xcworkspace`）
- [ ] 代码从 `Sources/` 成功复制到 `MacCortex-Xcode/MacCortex/`
- [ ] Info.plist 和 Entitlements 正确配置
- [ ] Build Settings 配置完成（Deployment Target, Swift Version）
- [ ] 代码签名成功（自动或手动）
- [ ] Backend 通信成功（绿色状态指示器）
- [ ] 至少一个 Pattern 成功执行（summarize 测试）

### 构建验证

- [ ] `Product` → `Clean Build Folder` 成功
- [ ] `Product` → `Build` 无错误
- [ ] `Product` → `Run` 应用正常启动
- [ ] 无运行时崩溃
- [ ] Debug 日志正常输出

### 文件验证

```bash
# 验证目录结构
tree -L 3 MacCortex-Xcode/

# 预期输出:
# MacCortex-Xcode/
# ├── MacCortex.xcodeproj/
# ├── MacCortex/
# │   ├── MacCortexApp.swift
# │   ├── ContentView.swift
# │   ├── Info.plist
# │   ├── MacCortex.entitlements
# │   ├── Assets.xcassets/
# │   └── Services/
# │       └── BackendClient.swift
# └── MacCortexTests/
```

---

## Git 提交

迁移完成后，提交到版本控制：

```bash
cd /Users/jamesg/projects/MacCortex

# 添加新文件
git add MacCortex.xcworkspace/
git add MacCortex-Xcode/
git add XCODE_MIGRATION_GUIDE.md

# 提交
git commit -m "[Phase 3] Week 1: Xcode 项目迁移完成

✅ **迁移完成**
- 创建 Xcode Workspace (MacCortex.xcworkspace)
- 创建 SwiftUI 项目 (MacCortex-Xcode/)
- 配置 Info.plist + Entitlements
- 集成 Backend 通信层 (BackendClient.swift)
- 实现基础 GUI (ContentView.swift)

📂 **新增文件**
- MacCortex.xcworkspace/
- MacCortex-Xcode/ (完整 Xcode 项目)
- XCODE_MIGRATION_GUIDE.md (本指南)

🧪 **验证通过**
- ✅ 构建成功（无错误）
- ✅ Backend 连接成功
- ✅ Summarize Pattern 测试通过

🎯 **下一步**
- Phase 3 Week 2: SwiftUI Desktop GUI 开发

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 推送到远程
git push origin main
```

---

## 下一步：Week 2 GUI 开发

迁移完成后，可以开始 Phase 3 Week 2 的 SwiftUI GUI 开发：

1. **主界面增强**:
   - Pattern 参数配置面板（动态生成）
   - 输出格式化显示（Markdown 渲染）
   - 历史记录侧边栏

2. **进度指示器**:
   - 针对 aya-23 的 2-8 秒响应时间
   - 流式输出（分块显示）
   - 取消按钮

3. **设置面板**:
   - 模式切换（aya / MLX）
   - 性能偏好（质量优先 / 速度优先）
   - 日志级别

4. **菜单栏集成**:
   - 文件菜单（导出、打印）
   - 编辑菜单（复制、粘贴、全选）
   - 帮助菜单（用户指南、关于）

---

## 常见问题 (FAQ)

### Q1: 为什么要迁移到 Xcode？

**A**: SwiftUI Desktop GUI 开发需要 Xcode 的完整功能：
- 图形化界面构建器
- Assets 管理（图标、颜色）
- 调试器（断点、变量查看）
- Instruments（性能分析）
- 代码签名与分发（Notarization）

---

### Q2: SPM 项目还能用吗？

**A**: 可以！保留 `Sources/` 和 `Package.swift` 作为参考。Xcode 项目独立运行，不影响 SPM。

---

### Q3: 迁移会破坏现有代码吗？

**A**: 不会。迁移是创建新的 Xcode 项目并复制代码，原 `Sources/` 目录保持不变。

---

### Q4: 如何回滚到 SPM？

**A**: 使用备份分支：
```bash
git checkout backup/pre-xcode-migration
```

---

### Q5: Xcode 和 Backend 如何通信？

**A**: 通过 HTTP REST API：
- Xcode (SwiftUI) → `http://localhost:8000/execute` → Backend (Python)
- Backend 响应 JSON → Xcode 解析并显示

---

## 参考资料

### 官方文档

1. **Xcode**:
   - [Xcode Help](https://developer.apple.com/documentation/xcode)
   - [SwiftUI Tutorials](https://developer.apple.com/tutorials/swiftui)

2. **Swift Package Manager**:
   - [Swift.org - Package Manager](https://swift.org/package-manager/)

3. **Code Signing**:
   - [Code Signing Guide](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/)
   - [Hardened Runtime](https://developer.apple.com/documentation/security/hardened_runtime)

### MacCortex 内部文档

- `PHASE_3_PLAN.md` - Phase 3 完整计划
- `PHASE_3_WEEK_1_SUMMARY.md` - Week 1 完成总结
- `USER_GUIDE.md` - 用户使用指南
- `API_REFERENCE.md` - Backend API 文档

---

## 附录

### A. Xcode 键盘快捷键

| 功能 | 快捷键 |
|------|--------|
| **构建** | ⌘B |
| **运行** | ⌘R |
| **停止** | ⌘. |
| **清理** | ⇧⌘K |
| **打开快速导航** | ⌘⇧O |
| **显示/隐藏 Debug Area** | ⌘⇧Y |
| **显示/隐藏 Navigator** | ⌘0 |
| **显示/隐藏 Inspector** | ⌥⌘0 |

---

### B. 目录结构对比

**Phase 2 (SPM)**:
```
MacCortex/
├── Sources/
│   └── MacCortexApp/
│       ├── MacCortexApp.swift
│       └── ContentView.swift
├── Tests/
├── Package.swift
└── Backend/
```

**Phase 3 (Xcode)**:
```
MacCortex/
├── MacCortex.xcworkspace/         # ← 新增
├── MacCortex-Xcode/               # ← 新增
│   ├── MacCortex.xcodeproj/
│   ├── MacCortex/
│   │   ├── MacCortexApp.swift
│   │   ├── ContentView.swift
│   │   ├── Services/
│   │   │   └── BackendClient.swift
│   │   ├── Info.plist
│   │   └── MacCortex.entitlements
│   └── MacCortexTests/
├── Sources/                       # ← 保留（参考）
├── Package.swift                  # ← 保留（参考）
└── Backend/                       # ← 不变
```

---

**文档结束** | Phase 3 Week 1 Xcode 迁移指南 ✅
