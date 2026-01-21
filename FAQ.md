# MacCortex 常见问题解答（FAQ）

> **版本**: v1.0 (Phase 2 Week 4 Day 19)
> **更新时间**: 2026-01-21
> **适用版本**: MacCortex v0.2.0+

---

## 目录

1. [安装与启动问题](#安装与启动问题)
2. [权限配置问题](#权限配置问题)
3. [Pattern 使用问题](#pattern-使用问题)
4. [性能与资源问题](#性能与资源问题)
5. [故障排查](#故障排查)
6. [技术与兼容性](#技术与兼容性)

---

## 安装与启动问题

### Q1: 为什么双击 MacCortex.app 提示"无法打开，因为它来自身份不明的开发者"？

**A**: 这是 macOS Gatekeeper 的默认安全保护。MacCortex 目前为独立分发（非 App Store），需要手动绕过：

**解决方法**:
```bash
# 方法 1: 右键点击 → "打开"（推荐）
右键点击 MacCortex.app → 选择"打开" → 在弹出对话框中点击"打开"

# 方法 2: 命令行移除隔离标记
xattr -d com.apple.quarantine /Applications/MacCortex.app
```

**注意**:
- 只需操作一次，后续可正常双击启动
- Phase 0.5 将提供代码签名和公证，届时无需此步骤

---

### Q2: MacCortex 是否支持 Apple Silicon (M1/M2/M3) 和 Intel Mac？

**A**:
- ✅ **Apple Silicon (M1/M2/M3/M4)**: 完全支持，MLX 框架针对 Apple Silicon 优化，性能最佳（40-60 tok/s）
- ⚠️ **Intel Mac (x86_64)**: 部分支持，但 MLX 框架**仅支持 Apple Silicon**，需切换到 Ollama 后端（性能约 15-28 tok/s）

**检查您的芯片类型**:
```bash
uname -m
# 输出 "arm64" = Apple Silicon
# 输出 "x86_64" = Intel Mac
```

---

### Q3: 首次启动后，Backend 提示"端口 8000 已被占用"怎么办？

**A**: 可能是之前运行的 Backend 进程未正常退出。

**解决方法**:
```bash
# 1. 查找占用端口的进程
lsof -i :8000

# 2. 终止进程（替换 <PID> 为上一步的进程号）
kill <PID>

# 3. 验证端口已释放
lsof -i :8000  # 应无输出

# 4. 重新启动 MacCortex
```

---

### Q4: 安装需要多少磁盘空间？

**A**:
- **MacCortex 应用**: ~50 MB
- **Backend 依赖**: ~500 MB（Python 环境 + 库）
- **MLX 模型**: ~800 MB（Llama-3.2-1B-Instruct-4bit）
- **Ollama 模型**（可选）: ~2-5 GB（qwen2.5:3b / aya-23）
- **推荐可用空间**: ≥5 GB

---

## 权限配置问题

### Q5: 为什么需要"Full Disk Access"（完全磁盘访问权限）？

**A**: MacCortex 的核心功能需要访问受保护的系统区域：

**必需的访问场景**:
- **Notes.app 数据库**（~/Library/Group Containers/group.com.apple.notes/）
- **Shortcuts.app 工作流**（~/Library/Shortcuts/）
- **批量文件操作**（如用户指定的文档目录）

**隐私保证**:
- MacCortex **不会**上传任何本地数据到云端
- 所有 LLM 推理均在本地执行（MLX/Ollama）
- 审计日志记录所有文件访问（见 `Backend/logs/audit.jsonl`）

---

### Q6: 如何验证 Full Disk Access 是否正确配置？

**A**: MacCortex 启动后会自动检测权限状态。

**手动验证方法**:
```bash
# 1. 检查系统设置
系统设置 → 隐私与安全性 → 完全磁盘访问权限 → 确认 MacCortex.app 已勾选

# 2. 测试 Notes 访问
# 在 MacCortex 中执行 Extract Pattern，输入："请提取我最近的 Note"
# 如果返回实际 Note 内容 = 权限正常
# 如果返回"权限被拒绝" = 权限未生效
```

**常见问题**:
- 勾选后仍无权限？→ 重启 MacCortex.app
- 仍然失败？→ 移除勾选 → 重新添加 → 重启 Mac

---

### Q7: MacCortex 会访问哪些敏感数据？如何审计？

**A**: MacCortex 遵循"最小权限原则"，仅在用户明确指令时访问数据。

**审计方法**:
```bash
# 查看实时审计日志（JSON 格式）
tail -f ~/Library/Logs/MacCortex/audit.jsonl | jq .

# 日志示例（PII 已自动脱敏）
{
  "timestamp": "2026-01-21T12:00:00.000Z",
  "event_type": "pattern_execute",
  "pattern_id": "extract",
  "user_ip_hash": "8f3b5c7a9e1d2f4b",  # IP 已哈希
  "input_length": 1024,
  "security_flags": [],
  "success": true
}
```

**隐私保护措施**:
- PII 自动脱敏（email/phone/IP 地址等）
- 日志本地存储，不上传
- 符合 GDPR/CCPA 规范

---

## Pattern 使用问题

### Q8: Translate Pattern 翻译质量不佳（翻译不完整或重复），如何解决？

**A**: 这是**已知限制**，由当前 MLX 模型（Llama-3.2-1B-Instruct，1B 参数）能力不足导致。

**当前缓解措施**（Phase 2）:
- 使用简短文本（< 200 字）
- 选择 `style=casual`（对话风格比正式风格更稳定）
- 避免使用低资源语言对（如 ko-KR → ar-AR）

**根本解决方案**（Phase 3）:
- 升级到 Ollama aya-23（23B 参数，专用翻译模型）
- 预期质量提升 **3-5 倍**
- 详见 `Backend/TRANSLATE_LIMITATION.md`

**测试示例**（当前限制）:
```
输入（153 字）: "MacCortex is a next-generation..."
目标语言: zh-CN
输出: "MacCortex 是下一代 macOS 个人 AI 基础设施，MacCortex 是..."  # ❌ 重复
```

---

### Q9: Search Pattern 提示"Rate limit exceeded"，如何解决？

**A**: DuckDuckGo 有反爬虫速率限制（< 1 秒间隔的连续请求会触发）。

**当前缓解机制**（Phase 2）:
- ✅ **5 分钟缓存**: 相同查询自动返回缓存结果
- ✅ **自动降级**: 触发速率限制时回退到 Mock 搜索
- ✅ **错误日志**: 记录到 `Backend/logs/backend.log`

**用户最佳实践**:
- 避免 10 秒内重复相同查询
- 使用缓存结果（查看日志 "🚀 使用缓存结果"）
- Phase 3 将支持 Google Custom Search API（备用）

**技术细节**: 见 `Backend/DUCKDUCKGO_INTEGRATION.md`

---

### Q10: Format Pattern 支持哪些格式转换？如何处理复杂 JSON？

**A**: 当前支持 5 种格式（Phase 2）：

| 源格式 | 目标格式 | 示例 |
|--------|----------|------|
| JSON | YAML, CSV, Markdown, XML | ✅ |
| YAML | JSON, CSV, Markdown | ✅ |
| CSV | JSON, YAML, Markdown | ✅ |
| Markdown | JSON, YAML | ⚠️ 有限支持（表格） |
| XML | JSON, YAML | ⚠️ 有限支持（简单结构） |

**复杂 JSON 处理**:
```json
// 支持嵌套对象和数组
{
  "users": [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
  ]
}

// 转换为 YAML（prettify=true）
users:
  - name: Alice
    age: 30
  - name: Bob
    age: 25
```

**限制**:
- CSV 转换仅支持扁平结构（嵌套对象会被字符串化）
- XML 转换不支持属性（仅元素）

---

### Q11: Extract Pattern 能提取哪些实体类型？准确率如何？

**A**: 当前支持 6 种实体类型（基于 MLX Llama-3.2）：

| 实体类型 | 示例 | 准确率 (Phase 2) |
|----------|------|------------------|
| `person` | "Alice Smith" | ~85% |
| `organization` | "Apple Inc." | ~80% |
| `location` | "San Francisco" | ~75% |
| `date` | "2026-01-21" | ~90% |
| `email` | "alice@example.com" | ~95% |
| `phone` | "+1-555-1234" | ~90% |

**提升准确率技巧**:
- 提供清晰上下文（如 "Contact: alice@example.com" 比 "alice@example.com" 更准确）
- 使用标准格式（ISO 8601 日期、E.164 电话号码）
- Phase 3 将集成正则表达式后处理（email/phone 准确率 → 99%+）

---

### Q12: Summarize Pattern 的长度参数（short/medium/long）有何区别？

**A**:
- **short** (简短): 1-3 句话，~50-100 字（适合快速浏览）
- **medium** (中等): 1-2 段落，~150-300 字（默认值）
- **long** (详细): 3+ 段落，~400-600 字（深度分析）

**实际对比**（Phase 2 测试结果）:
```
输入: 1,000 字技术文档

short 输出（87 字）:
"MacCortex 是基于 MLX 的 macOS AI 工具，提供 5 个 Pattern：总结、提取、翻译、格式转换、搜索。核心优势是本地化 LLM 推理（隐私保护）和 Apple Silicon 优化。"

medium 输出（243 字）:
"MacCortex 是新一代 macOS 个人 AI 基础设施，采用双 LLM 架构（MLX + Ollama）。提供 5 个核心 Pattern：1) Summarize - 文本总结，2) Extract - 实体提取... [中略] ...所有推理本地执行，无数据上传，响应时间 < 2s。"

long 输出（512 字）:
"MacCortex 项目背景：随着 Apple Intelligence 推出... [完整段落] ...Phase 1-4 路线图... [技术架构详解] ..."
```

---

## 性能与资源问题

### Q13: MacCortex 的性能指标如何？与 ChatGPT/Claude 对比？

**A**: Phase 2 Week 4 基准测试结果（2026-01-21）：

| 指标 | MacCortex (本地) | ChatGPT/Claude (云端) | 对比 |
|------|------------------|----------------------|------|
| **响应时间** (p50) | 1.638s | 0.5-2s | ≈ 相当 |
| **内存占用** | 103.89 MB | N/A（服务器端） | 轻量 |
| **CPU 占用**（空闲） | 0% | N/A | 极低 |
| **Token 生成速度** | 40-60 tok/s (MLX) | ~100 tok/s | 稍慢 |
| **隐私保护** | ✅ 100% 本地 | ❌ 数据上传 | 🏆 优势 |
| **网络依赖** | ✅ 离线可用 | ❌ 必需联网 | 🏆 优势 |

**关键优势**:
- **响应时间** < 2s（90% 请求），接近云端服务
- **零成本**: 无 API 费用（vs ChatGPT $20/月、Claude Pro $20/月）
- **隐私**: 数据不离开本地

**适用场景**:
- ✅ 处理敏感数据（医疗、法律、财务）
- ✅ 离线环境（飞机、无网络地区）
- ⚠️ 不适合超长文本（> 4096 tokens，受 MLX 模型限制）

---

### Q14: MacCortex 运行时占用多少资源？会影响其他应用吗？

**A**: 资源占用极低（Phase 2 测试数据）：

**内存占用**:
- MacCortex.app: **103.89 MB**（GUI 前端）
- Backend Python: **26.56 MB**（FastAPI 服务）
- MLX 模型加载后: **+800 MB**（仅在推理时）
- **总计**: ~1 GB（vs Chrome 单标签页 ~500 MB）

**CPU 占用**:
- 空闲状态: **0%**
- 推理时: **60-80%**（单核，持续 1-2 秒）
- 推理完成后立即降至 **0%**

**对其他应用的影响**:
- ✅ **无明显影响**: MacBook Air M1 (8GB) 上与 Safari、Xcode 同时运行无卡顿
- ⚠️ **批量处理时**: 如同时处理 100+ 文件，建议暂停大型应用

---

### Q15: 为什么 Pattern 响应时间有时会超过 5 秒？

**A**: 响应时间受多种因素影响：

**正常范围**（Phase 2 基准）:
- **p50（中位数）**: 1.638s
- **p90**: ~2.5s
- **p99**: ~4s

**超时原因排查**:

1. **首次推理慢（冷启动）**:
   - MLX 模型首次加载需 2-3 秒
   - 解决方法: 预热请求（启动后自动执行）

2. **输入文本过长**:
   - > 2000 tokens 会显著增加推理时间
   - 解决方法: 使用 Summarize Pattern 先总结

3. **DuckDuckGo 搜索超时**:
   - 网络慢或触发速率限制时，搜索可能耗时 5-10s
   - 解决方法: 查看日志是否有 "Ratelimit" 错误

4. **系统资源不足**:
   - 内存 < 4 GB 或 CPU 高负载
   - 解决方法: 关闭其他应用或升级硬件

**性能调优**（Phase 3）:
- 模型预加载（减少冷启动）
- 批处理优化
- GPU 加速（Metal Performance Shaders）

---

## 故障排查

### Q16: MacCortex 崩溃或无响应，如何调试？

**A**: 按以下步骤排查：

**步骤 1: 检查日志**
```bash
# Backend 错误日志
tail -100 ~/Library/Logs/MacCortex/backend.log

# 系统崩溃日志
open ~/Library/Logs/DiagnosticReports/
# 查找 MacCortex*.crash 文件
```

**步骤 2: 验证 Backend 状态**
```bash
# 检查 Backend 是否运行
lsof -i :8000

# 手动启动 Backend（调试模式）
cd /Applications/MacCortex.app/Contents/Resources/Backend
python3 src/main.py --debug
```

**步骤 3: 重置环境**
```bash
# 清理缓存和日志
rm -rf ~/Library/Logs/MacCortex/*
rm -rf ~/Library/Caches/com.maccortex.app

# 重新启动 MacCortex
```

**常见崩溃原因**:
- Python 依赖损坏 → 重新安装 MacCortex
- MLX 模型损坏 → 删除 `~/.cache/huggingface/` 后重新下载
- 权限问题 → 重新授予 Full Disk Access

---

### Q17: Backend 日志提示"模型未找到"或"下载失败"？

**A**: MLX 模型需首次下载（约 800 MB）。

**自动下载失败原因**:
1. **网络问题**: HuggingFace 被墙或网络不稳定
2. **磁盘空间不足**: 需 > 2 GB 可用空间
3. **代理设置**: Clash/Surge 可能拦截 Python 请求

**解决方法**:

**方法 1: 手动下载模型**
```bash
# 1. 设置 HuggingFace 镜像（中国用户）
export HF_ENDPOINT=https://hf-mirror.com

# 2. 使用 huggingface-cli 下载
pip3 install huggingface-hub
huggingface-cli download mlx-community/Llama-3.2-1B-Instruct-4bit

# 3. 验证模型文件
ls ~/.cache/huggingface/hub/models--mlx-community--Llama-3.2-1B-Instruct-4bit/
```

**方法 2: 使用 Ollama 替代**
```bash
# 安装 Ollama
brew install ollama

# 下载轻量模型
ollama pull qwen2.5:3b

# 修改 Backend 配置使用 Ollama
# （详见 Backend/src/utils/config.py）
```

---

### Q18: 如何报告 Bug 或提交功能建议？

**A**:
1. **GitHub Issues**: https://github.com/yourusername/MacCortex/issues
   - Bug 报告模板: 描述 + 复现步骤 + 日志
   - 功能建议模板: 用例 + 预期效果 + 优先级

2. **提供以下信息**:
   ```
   - macOS 版本: (如 macOS 15.2 Sequoia)
   - 芯片类型: (M1/M2/Intel)
   - MacCortex 版本: (如 v0.2.0)
   - 错误日志: (粘贴 backend.log 最后 50 行)
   - 复现步骤: (详细描述操作)
   ```

3. **紧急问题**: 邮件至 support@maccortex.com

---

## 技术与兼容性

### Q19: MacCortex 支持哪些 macOS 版本？

**A**:
- ✅ **macOS 14 Sonoma** (推荐)
- ✅ **macOS 15 Sequoia** (推荐)
- ⚠️ **macOS 13 Ventura** (有限支持，部分功能受限)
- ❌ **macOS 12 及更早** (不支持，MLX 框架要求 macOS 13+)

**验证系统版本**:
```bash
sw_vers -productVersion
```

---

### Q20: MacCortex 未来路线图？会支持 Windows/Linux 吗？

**A**:
**Phase 2 (当前)**: 核心 5 个 Pattern + CLI 接口
**Phase 3 (Q2 2026)**: SwiftUI Desktop GUI + 浮动工具栏
**Phase 4 (Q3 2026)**: MCP 工具集成 + 高级 Swarm
**Phase 5 (Q4 2026)**: Apple Intelligence 集成 + App Intents

**跨平台计划**:
- ❌ **Windows/Linux**: 无计划（依赖 Apple Silicon + MLX 框架）
- ✅ **iOS/iPadOS**: Phase 6 考虑（需重写 UI）

**替代方案**（非 macOS 用户）:
- 使用 Ollama + LangChain 自行搭建类似架构
- 参考 `Backend/` 代码（100% Python，可移植）

---

## 附录

**相关文档**:
- [用户指南 (USER_GUIDE.md)](./USER_GUIDE.md) - 完整使用手册
- [API 参考 (API_REFERENCE.md)](./API_REFERENCE.md) - Backend API 文档（即将发布）
- [变更日志 (CHANGELOG.md)](./CHANGELOG.md) - 版本更新历史
- [技术限制 (TRANSLATE_LIMITATION.md)](./Backend/TRANSLATE_LIMITATION.md) - 翻译质量问题详解
- [DuckDuckGo 集成 (DUCKDUCKGO_INTEGRATION.md)](./Backend/DUCKDUCKGO_INTEGRATION.md) - 搜索 API 技术细节

**社区资源**:
- GitHub: https://github.com/yourusername/MacCortex
- Discord: https://discord.gg/maccortex (即将开放)
- 文档站点: https://docs.maccortex.com (Phase 3)

---

**文档更新**: 本 FAQ 随 MacCortex 版本持续更新。最后更新：2026-01-21（Phase 2 Week 4 Day 19）
