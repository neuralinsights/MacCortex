# MacCortex 项目记忆文件 (CLAUDE.md)

## 时间真实性校验记录

### 校验时间：2026-01-23 17:47:59 +13:00

- **本机系统时间与时区**：Asia/Auckland (NZDT, +13:00)
- **时间源 1**：
  - 来源/URL：本地系统 `date` 命令
  - 协议：系统调用
  - 返回示例：Fri Jan 23 17:47:59 NZDT 2026
  - 时间戳：2026-01-23 17:47:59 +13:00
- **时间源 2**：
  - 来源/URL：https://www.timeanddate.com
  - 协议：HTTPS-Header
  - 返回示例：date: Fri, 23 Jan 2026 04:47:59 GMT
  - 时间戳：2026-01-23 04:47:59 GMT (等价于 2026-01-23 17:47:59 +13:00)
- **最大偏差**：0 秒（阈值：100 秒）
- **判定**：✅ 通过
- **备注**：用于后续所有检索记录与日志的"基准时间锚点"

---

## 项目基础信息

- **项目名称**：MacCortex
- **当前版本**：v1.0.0-multi-llm
- **状态**：Multi-LLM Support Complete 🚀
- **Bundle ID**：com.maccortex.app
- **Team ID**：CSRKUK3CQV
- **主要语言**：Swift (Frontend) + Python (Backend)
- **平台**：macOS 14.0+ (ARM64)
- **项目路径**：/Users/jamesg/projects/MacCortex
- **当前分支**：`frosty-kalam`

---

## 最近成就 (2026-01-26)

### 🏆 Multi-LLM Support 完整实现

**Phase 1-4 全部完成**，包含：

1. **LLM 抽象层** (`Backend/src/llm/`)
   - LLMProviderProtocol ABC 接口
   - ModelRouterV2 统一路由器
   - UsageTracker Token 追踪
   - 支持 6+ Provider (Anthropic, OpenAI, Ollama, DeepSeek, Gemini, MLX)

2. **Agent 节点集成**
   - Planner, Coder, Reviewer 集成 ModelRouterV2
   - SwarmState 添加 Token 追踪字段
   - WebSocket `token_update` 实时推送

3. **REST API 扩展**
   - `GET /llm/models` - 可用模型列表
   - `GET /llm/usage` - 使用统计
   - `POST /llm/usage/reset` - 重置统计

4. **Swift Frontend**
   - APIKeyManager (Keychain 安全存储)
   - ModelSettingsView (模型选择 UI)
   - TokenUsageView (Token 显示组件)
   - SettingsView 新增"模型"标签页

### 测试覆盖
- **Backend**: 535 tests passed ✅ (原 510 + 新增 25 Provider 测试)
- **Swift**: Build complete ✅

### 关键修复
- UsageTracker 死锁 (Lock → RLock)
- 测试导入路径配置
- planner.py 缺少 Path 导入 (2026-01-26)

---

## 最新更新 (2026-01-26 20:10 +13:00)

### 🚀 Phase 5 P1/P2: 扩展 Provider 完成

新增三个 LLM Provider 实现：

| Provider | 模型 | 定价 (USD/1M tokens) | 特点 |
|----------|------|---------------------|------|
| **DeepSeek** | deepseek-chat, deepseek-reasoner | $0.27/$1.10 | 极高性价比 |
| **Google Gemini** | gemini-2.0-flash, gemini-1.5-pro | $0.10/$0.40 | 2M 上下文窗口 |
| **MLX** | Qwen2.5, Llama-3.2 (本地) | $0/$0 | Apple Silicon 加速 |

**新增文件**:
- `Backend/src/llm/providers/deepseek.py` (~270 行)
- `Backend/src/llm/providers/gemini.py` (~300 行)
- `Backend/src/llm/providers/mlx.py` (~350 行)
- `Backend/tests/llm/test_providers.py` (25 测试)

**提交记录**:
- `34f3d39` - [FEATURE] 扩展 Provider：DeepSeek + Gemini + MLX
- `d84e9e0` - [FIX] 修复 planner.py 缺少 Path 导入的 Bug

## 下一步计划

### 🔀 待合并
- [x] 推送分支到 origin ✅
- [ ] 创建 PR: `frosty-kalam` → `main`

### 🔧 待完成
- [ ] 连接 Swift 前端到真实 Backend API

### 📚 文档
- [ ] 完善用户指南与 API 文档
- [ ] 录制 Demo 视频

---

## 当前紧急问题

### ✅ 已解决：Sparkle.framework 加载失败（2026-01-23 20:29 +13:00）

#### 问题描述
应用启动时崩溃，错误信息：
```
Library not loaded: @rpath/Sparkle.framework/Versions/B/Sparkle
Termination Reason: Namespace DYLD, Code 1, Library missing
```

#### 根因分析
1. **直接原因**：Sparkle.framework 的 install_name 未正确设置为 `@rpath` 格式
2. **技术细节**：虽然 framework 已复制到 `Contents/Frameworks/`，且 rpath 包含 `@loader_path/../Frameworks`，但 framework 内部的 dylib ID 不匹配
3. **影响范围**：应用完全无法启动

#### 解决方案
1. **临时修复**：使用 `install_name_tool -id "@rpath/Sparkle.framework/Versions/B/Sparkle"` 修复现有构建
2. **永久修复**：更新 `Scripts/build-app-bundle.sh`，在复制 framework 后自动修复 install_name
3. **验证**：应用成功启动（PID 86806），无崩溃

#### 修改文件
- `Scripts/build-app-bundle.sh`: 添加 install_name_tool 修复步骤（+8 行）

---

## 证据清单

### 议题: Multi-LLM Support 架构设计 (2026-01-26)

| 来源 | URL | 版本 | 检索时间 | 摘要 | 采用性 |
|------|-----|------|---------|------|--------|
| Anthropic API 文档 | https://docs.anthropic.com/claude/reference | 2026 | 2026-01-26 | Claude API 定价与 Token 计数 | ✅ 采用 |
| OpenAI API 文档 | https://platform.openai.com/docs | 2026 | 2026-01-26 | GPT-4o 定价与能力 | ✅ 采用 |
| LangChain 官方文档 | https://python.langchain.com/docs | 0.2.x | 2026-01-26 | LLM 抽象模式参考 | ✅ 采用 |
| Apple Keychain Services | https://developer.apple.com/documentation/security/keychain_services | 2025 | 2026-01-26 | API Key 安全存储 | ✅ 采用 |

---

## 特例登记

### 特例审批单 #20260126-01 (Multi-LLM Support)

- **触发原因**：实现多 LLM 支持需要创建新的模块目录和文件
- **无法修改现有文件的论证**：
  - LLM 抽象层是全新功能，不存在可复用的现有实现
  - 需要独立的模块结构以支持未来扩展
- **证据清单**：见上方议题
- **新文件信息**：
  - 路径：`Backend/src/llm/` (8 文件)
  - 路径：`Sources/MacCortexApp/Services/APIKeyManager.swift`
  - 路径：`Sources/MacCortexApp/Models/LLMModels.swift`
  - 路径：`Sources/MacCortexApp/Views/Settings/ModelSettingsView.swift`
  - 路径：`Sources/MacCortexApp/Views/Components/TokenUsageView.swift`
- **影响范围**：新增模块，不影响现有功能
- **回滚方案**：删除 `feature/multi-llm-support` 分支
- **Commit 标签**：`[FEATURE]`, `[FEAT]`, `[FIX]`
- **审批时间**：2026-01-26 19:30:00 +13:00
- **状态**：✅ 已批准并完成

---

## 冗余治理报告

### 冗余检查 #20260126-01

**检查范围**：Multi-LLM Support 相关文件

**检查结果**：
- ✅ 无冗余：`ModelSettingsView.swift` vs `SettingsView.swift` - 职责明确分离
- ✅ 无冗余：`LLMModels.swift` vs `SwarmModels.swift` - 不同数据域
- ✅ 无冗余：`APIKeyManager.swift` - 唯一的 Keychain 管理实现

**结论**：无需合并或删除

---

## 交割文档索引

| 日期 | 文档 | 说明 |
|------|------|------|
| 2026-01-26 | `Backend/docs/MULTI_LLM_HANDOFF_20260126.md` | Multi-LLM Support 完整交割文档 |
