# MacCortex Backend - 变更日志

所有显著变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### Phase 1.5: 安全强化（进行中）

#### [0.2.0] - 2026-01-21 - Day 1-3 完成

**新增 🆕**
- **安全模块**: 新增 `src/security/` 目录，包含完整的安全防护体系
  - `security_config.py` (270 行) - 统一安全配置管理
  - `prompt_guard.py` (480 行) - PromptGuard 核心防护类
- **5 层 Prompt Injection 防护体系**:
  - Layer 1: 输入标记 (`<user_input>` 标签)
  - Layer 2: 指令隔离（系统提示与用户内容分离）
  - Layer 3: 模式检测（26+ 恶意正则表达式）
  - Layer 4: LLM 验证（Stub，待后续实现）
  - Layer 5: 输出清理（系统提示泄露、凭证检测）
- **26+ 恶意模式检测**:
  - 指令覆盖攻击（ignore instructions, you are now, etc.）
  - 提示泄露攻击（repeat your prompt, tell me your instructions）
  - 角色劫持攻击（forget rules, disregard safety）
  - 社会工程攻击（emotional manipulation, urgency）
- **安全测试套件**:
  - `tests/security/test_prompt_guard.py` - PromptGuard 单元测试
  - `test_prompt_guard_manual.py` (170 行) - 手动测试脚本
  - `test_phase1.5_integration.py` (134 行) - 集成测试

**修改 ✏️**
- **BasePattern** (`src/patterns/base.py`):
  - 新增 `__init__(enable_security=True)` - 支持安全模块初始化
  - 新增 `_init_security()` - 延迟加载 PromptGuard
  - 新增 `_check_injection()` - Prompt Injection 检测钩子
  - 新增 `_protect_prompt()` - Layer 1+2 防护钩子
  - 新增 `_sanitize_output()` - Layer 5 输出清理钩子
- **所有 5 个 Pattern 类**:
  - `summarize.py` - 完整集成 PromptGuard（+50 行）
  - `extract.py` - 完整集成 + 系统提示分离（+100 行）
  - `translate.py` - 集成安全钩子
  - `format.py` - 集成安全钩子
  - `search.py` - 集成安全钩子
- **Pytest 配置** (`pyproject.toml`):
  - 新增 `pythonpath = ["src"]` - 修复模块导入问题
  - 新增 `tests/conftest.py` - Pytest 配置文件

**安全修复 🔒**
- 修复置信度评分过低问题（首次匹配从 25% 提升到 80%）
- 修复正则表达式转义问题（`[INST]` → `\[INST\]`）
- 扩展模式覆盖范围（新增 "directions", "commands" 关键词）
- 优化凭证检测模式（`{48}` → `{20,}` 灵活长度）
- 修复 "you are now" 模式匹配（支持无冠词情况）

**测试结果 ✅**
- **test_prompt_guard_manual.py**: 85% (17/20)
- **test_phase1.5_integration.py**: 100% (30/30) ⭐
- **test_all_patterns.py**: 100% (5/5) ⭐
- **总体通过率**: 96% (52/55)

**性能 ⚡**
- Injection 检测延迟: < 5ms（正则匹配）
- 输入标记延迟: < 1ms（字符串操作）
- 输出清理延迟: < 5ms（正则替换）
- **总体性能开销**: < 10ms p95 ✅（符合验收标准）

**文档 📚**
- 新增 `PHASE_1.5_DAY1-3_SUMMARY.md` - Day 1-3 完成总结（428 行）
- 更新 `README.md` - 添加 Phase 1.5 安全功能说明
- 新增 `CHANGELOG.md` - 本文件

**向后兼容 🔄**
- ✅ 所有现有 API 保持不变
- ✅ 安全功能默认启用，但可通过 `enable_security=False` 禁用
- ✅ 现有测试无需修改，全部通过

**Git 提交**
```bash
217acf5 [SECURITY] Phase 1.5 Day 3: 完成所有 Pattern 集成
207f2f0 [SECURITY] Phase 1.5 Day 1-3: Implement Prompt Injection Defense System
```

**验收标准进度**
| # | 验收项 | 状态 | 进度 |
|---|--------|------|------|
| 1 | OWASP LLM01 防御 | 🟡 进行中 | 85% |
| 2 | 审计日志完整性 | ⏸️ 待开始 | 0% |
| 3 | PII 脱敏 | ⏸️ 待开始 | 0% |
| 4 | 参数白名单 | ⏸️ 待开始 | 0% |
| 5 | 速率限制 | ⏸️ 待开始 | 0% |
| 6 | **性能开销** | ✅ 通过 | 100% |
| 7 | **向后兼容** | ✅ 通过 | 100% |
| 8 | 测试覆盖率 | 🟡 进行中 | 85% |

**下一步（Day 4-5）**
- [ ] 实施审计日志系统（`audit_logger.py`）
- [ ] 实施 15+ PII 脱敏模式
- [ ] 创建安全中间件（`security_middleware.py`）
- [ ] GDPR/CCPA 合规验证

---

## [0.1.0] - 2026-01-20 - Phase 1 完成

**新增 🆕**
- FastAPI 应用框架（`src/main.py`）
- Pattern 系统架构：
  - `patterns/base.py` - BasePattern 抽象类
  - `patterns/registry.py` - PatternRegistry 注册表
- 5 个核心 Pattern 实现：
  - `patterns/summarize.py` - 文本总结
  - `patterns/extract.py` - 信息提取
  - `patterns/translate.py` - 文本翻译
  - `patterns/format.py` - 格式转换
  - `patterns/search.py` - 网络搜索
- MLX/Ollama 集成（Apple Silicon 优化）
- 版权保护系统（`utils/watermark.py`）
- 配置管理（`utils/config.py`）
- API 端点：
  - `GET /health` - 健康检查
  - `GET /version` - 版本信息
  - `GET /patterns` - 列出可用 Pattern
  - `POST /execute` - 执行 Pattern

**技术栈**
- FastAPI 0.109.0
- Pydantic 2.5.0
- MLX 0.5.0
- Ollama 0.1.6
- Loguru 0.7.2

**测试**
- `test_all_patterns.py` - 所有 Pattern 功能测试

---

## 图例

- 🆕 新增功能
- ✏️ 修改功能
- 🔒 安全修复
- 🐛 Bug 修复
- ⚡ 性能优化
- 📚 文档更新
- 🔄 向后兼容
- ✅ 测试通过
- ⭐ 重要里程碑
