# Multi-LLM Support 交割文档

**交割时间**: 2026-01-26 19:30:00 +13:00 (NZDT)
**分支**: `feature/multi-llm-support`
**最新提交**: `9cbc934`

---

## 一、功能概述

本次实现为 MacCortex 添加完整的 **多 LLM 支持架构**，包含：

1. **统一 LLM 抽象层** - 支持 6+ Provider 的统一接口
2. **Token 计数与成本追踪** - 实时追踪 API 调用成本
3. **Swift 前端集成** - API Key 管理和模型设置 UI
4. **WebSocket 实时更新** - Token 使用量实时推送

---

## 二、实现阶段

### Phase 1: Python Backend LLM 抽象层 ✅

| 文件 | 说明 |
|------|------|
| `Backend/src/llm/__init__.py` | 模块入口，导出公共接口 |
| `Backend/src/llm/models.py` | 数据模型：TokenUsage, CostInfo, LLMResponse, ModelInfo, ModelConfig |
| `Backend/src/llm/protocol.py` | LLMProviderProtocol ABC 接口定义 |
| `Backend/src/llm/router.py` | ModelRouterV2 统一路由器 |
| `Backend/src/llm/usage_tracker.py` | UsageTracker Token 使用量追踪 |
| `Backend/src/llm/providers/` | Provider 实现目录 |

### Phase 2: Agent 节点集成 ✅

| 文件 | 修改内容 |
|------|---------|
| `Backend/src/orchestration/state.py` | 添加 `total_tokens`, `total_cost`, `token_usage_by_agent` 字段 |
| `Backend/src/orchestration/nodes/planner.py` | 集成 ModelRouterV2，Token 累加 |
| `Backend/src/orchestration/nodes/coder.py` | 集成 ModelRouterV2，Token 累加 |
| `Backend/src/orchestration/nodes/reviewer.py` | 集成 ModelRouterV2，Token 累加 |

### Phase 3: REST API 扩展 ✅

| 端点 | 功能 |
|------|------|
| `GET /llm/models` | 返回可用模型列表 |
| `GET /llm/usage` | 返回会话使用统计 |
| `POST /llm/usage/reset` | 重置使用统计 |
| WebSocket `token_update` | Token 使用量实时推送 |

### Phase 4: Swift Frontend 实现 ✅

| 文件 | 说明 |
|------|------|
| `Sources/MacCortexApp/Services/APIKeyManager.swift` | Keychain API Key 安全存储 |
| `Sources/MacCortexApp/Models/LLMModels.swift` | Swift 数据模型 |
| `Sources/MacCortexApp/Views/Settings/ModelSettingsView.swift` | 模型选择 UI（完整版） |
| `Sources/MacCortexApp/Views/Components/TokenUsageView.swift` | Token 使用量组件 |
| `Sources/MacCortexApp/Views/SettingsView.swift` | 添加"模型"设置标签页 |
| `Sources/MacCortexApp/Models/SwarmModels.swift` | 添加 `tokenUpdate` 消息类型 |
| `Sources/MacCortexApp/Network/SwarmAPIClient.swift` | 处理 `token_update` 消息 |

---

## 三、测试验证

### Backend 测试

```
510 passed, 68743 warnings in 8.74s
```

| 测试模块 | 数量 | 状态 |
|---------|-----|------|
| tests/llm/test_models.py | 26 | ✅ |
| tests/llm/test_usage_tracker.py | 15 | ✅ |
| tests/llm/test_router_integration.py | 10 | ✅ |
| tests/api/test_llm_routes.py | 14 | ✅ |
| 其他 orchestration 测试 | 445 | ✅ |

### Swift 编译

```
Build complete! (0.91s)
```

---

## 四、修复的 Bug

### 1. UsageTracker 死锁 (Critical)

**问题**: `export_to_json()` 调用 `get_stats()` 时发生死锁
**原因**: 使用 `Lock()` 而不是 `RLock()`，不支持嵌套锁获取
**修复**: `Backend/src/llm/usage_tracker.py` 第 10 行和第 91 行
```python
from threading import RLock  # 改自 Lock
self._lock = RLock()  # 使用可重入锁
```

### 2. 测试导入路径

**问题**: 测试文件使用 `from src.xxx` 但 conftest.py 只添加 `src/` 到路径
**修复**: `Backend/tests/conftest.py` 同时添加 Backend 根目录和 `src/` 目录

---

## 五、提交历史

```
9cbc934 [FIX] 修复测试死锁和导入路径问题
50cf6bc [FEATURE] Phase 4: Swift Frontend Multi-LLM Support
a7d7f20 [Phase 5] Phase 3 完成: REST API 扩展 + Token 追踪
d3ad3b0 [Phase 5] 添加 WebSocket token_update 消息和集成测试
9c3fc69 [FEAT] 集成 ModelRouterV2 实现 Token 追踪 (Phase 2)
6661547 [FEAT] 实现多 LLM 支持抽象层 (Phase 1)
```

---

## 六、下一步工作

### 待完成

1. **创建 PR 合并到 main**
   ```
   https://github.com/neuralinsights/MacCortex/compare/main...feature/multi-llm-support
   ```

2. **Phase 5: 扩展 Provider（可选）**
   - DeepSeek Provider
   - Google Gemini Provider
   - MLX Provider (Apple Silicon)

3. **端到端验证**
   - 启动应用测试模型设置 UI
   - 验证 Token 计数实时更新
   - 验证 API Key Keychain 存储

### 已知限制

1. Swift 前端的 `ModelSettingsViewModel.refreshModels()` 目前使用 mock 数据（`#if DEBUG`）
2. `LLMSettingsViewModel` 尚未连接真实的 Backend API
3. Provider 实现目前只有骨架代码，需要实际 API 调用

---

## 七、关键代码位置

### Backend

```
Backend/
├── src/
│   ├── llm/                    # LLM 抽象层核心
│   │   ├── __init__.py         # 公共导出
│   │   ├── models.py           # 数据模型
│   │   ├── protocol.py         # Provider 接口
│   │   ├── router.py           # ModelRouterV2
│   │   └── usage_tracker.py    # Token 追踪
│   ├── api/
│   │   ├── llm_routes.py       # LLM API 端点
│   │   └── swarm_routes.py     # 添加 token_usage 字段
│   └── orchestration/
│       ├── state.py            # SwarmState Token 字段
│       └── nodes/              # Agent 节点集成
└── tests/
    └── llm/                    # LLM 测试
```

### Swift

```
Sources/MacCortexApp/
├── Services/
│   └── APIKeyManager.swift     # Keychain 管理
├── Models/
│   ├── LLMModels.swift         # Swift 数据模型
│   └── SwarmModels.swift       # WebSocket 消息
├── Views/
│   ├── Settings/
│   │   └── ModelSettingsView.swift  # 模型设置 UI
│   ├── Components/
│   │   └── TokenUsageView.swift     # Token 显示组件
│   └── SettingsView.swift      # 设置主视图
└── Network/
    └── SwarmAPIClient.swift    # WebSocket 处理
```

---

## 八、使用示例

### Python - 使用 ModelRouterV2

```python
from llm import create_default_router, ModelConfig

router = create_default_router()

# 调用模型
response = await router.invoke(
    model_id="claude-sonnet-4",
    messages=[{"role": "user", "content": "Hello"}],
    config=ModelConfig.default()
)

# 获取使用统计
print(f"Tokens: {response.usage.total_tokens}")
print(f"Cost: {response.cost.formatted_total}")
```

### Swift - 使用 APIKeyManager

```swift
let manager = APIKeyManager.shared

// 保存 API Key
manager.setKey("sk-xxx", for: .anthropic)

// 检查是否已配置
if manager.hasKey(for: .anthropic) {
    // 使用 API
}

// 删除 API Key
manager.deleteKey(for: .anthropic)
```

---

## 九、定价表（2026-01）

| Provider | Model | Input ($/1M) | Output ($/1M) |
|----------|-------|--------------|---------------|
| Anthropic | claude-opus-4 | $15.00 | $75.00 |
| Anthropic | claude-sonnet-4 | $3.00 | $15.00 |
| Anthropic | claude-haiku-3.5 | $0.80 | $4.00 |
| OpenAI | gpt-4o | $2.50 | $10.00 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| DeepSeek | deepseek-chat | $0.27 | $1.10 |
| Ollama/MLX | 本地模型 | $0.00 | $0.00 |

---

## 十、联系方式

如有问题，请参考：
- Plan 文件: `/Users/jamesg/.claude/plans/pure-noodling-sunrise.md`
- 项目 CLAUDE.md: `/Users/jamesg/.claude-worktrees/MacCortex/nervous-rubin/CLAUDE.md`
- GitHub: https://github.com/neuralinsights/MacCortex

**交割人**: Claude Opus 4.5
**交割时间**: 2026-01-26 19:30:00 +13:00
