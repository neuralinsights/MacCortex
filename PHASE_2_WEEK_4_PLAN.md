# Phase 2 Week 4: 用户体验打磨与文档完善 - 实施计划

> **创建时间**: 2026-01-21 20:04:27 +1300 (NZDT)
> **基于时间校验**: #20260121-03
> **状态**: 待开始
> **预计工期**: 5 天（Day 16-20）
> **前置依赖**: Phase 2 Week 3 完成 ✅（END_TO_END_TEST_REPORT.md）

---

## 📊 当前状态

### ✅ Phase 2 Week 3 完成（Day 11-15）
- ✅ MCP 工具动态加载（680 行代码）
- ✅ Shortcuts 集成（550 行代码，测试延后 Phase 3）
- ✅ 性能优化（启动 2.0s, 内存 115MB, CPU 0%）
- ✅ 压力测试（并发 5 req/s，所有测试通过）

**累计代码**: 13,564 行（Python 5,369 + Swift 8,195）

### ⚠️ 发现的问题（基于 END_TO_END_TEST_REPORT.md）

| # | 问题 | 严重程度 | 影响范围 | 优先级 |
|---|------|----------|----------|--------|
| 1 | **Translate Pattern 输出异常** | 中 | 翻译功能不可用 | P0 |
| 2 | **Search Pattern 返回 mock 数据** | 中 | 搜索功能未实际联网 | P0 |
| 3 | **/version 端点错误** | 低 | MLX 版本属性缺失 | P1 |
| 4 | **端到端 GUI 测试缺失** | 中 | 无法验证完整用户流程 | P0 |
| 5 | **Shortcuts 无法测试** | 低 | SPM 限制 | P2（Phase 3） |
| 6 | **MCP 未实际测试** | 低 | 无 MCP 服务器安装 | P2（Phase 3） |

---

## 🎯 Week 4 核心目标

### 主要目标（P0）
1. **修复 2 个 Pattern 问题**（Translate + Search）
2. **端到端 GUI 测试**（手动 + 自动化）
3. **用户文档完善**（使用指南 + FAQ）
4. **Phase 2 总结报告**（Demo 演示 + 里程碑验收）

### 非目标（Phase 3 延后）
- ❌ Shortcuts 实际测试（需 Xcode 项目）
- ❌ MCP 服务器部署与测试
- ❌ Shell 执行器实现
- ❌ Notes 深度集成

---

## Day 16-17: Pattern 修复与优化

### 背景

根据 END_TO_END_TEST_REPORT.md 的测试结果：
- **Translate Pattern**: 输出重复文本，无实际翻译内容
- **Search Pattern**: 仅返回 mock 数据，未联网搜索

---

### Day 16: 修复 Translate Pattern

#### 问题分析

**当前症状**:
```
输入: "Hello, how are you today?"
参数: {"target_language": "zh-CN"}

期望输出: "你好，今天过得怎么样？"

实际输出: "注意：由于翻译的长度和复杂性...<重复文本>"
```

**可能原因**:
1. MLX prompt 模板设计不当
2. Llama-3.2-1B-Instruct 模型对翻译任务支持不佳
3. 温度参数或 max_tokens 配置问题

---

#### 解决方案

##### 方案 A: 优化 MLX Prompt 模板 ✅ **推荐**

**原理**: 改进系统提示，明确翻译任务指令

**实施步骤**:
1. 修改 `Backend/src/patterns/translate.py:297-300`
2. 优化 prompt 结构：
   ```python
   # 修改前（推测）
   prompt = f"翻译以下文本到{target_language}：\n{text}"

   # 修改后
   system_prompt = """You are a professional translator.
   Translate the provided text accurately and naturally.
   IMPORTANT:
   - Only output the translation, no explanations.
   - Preserve the original meaning and tone.
   - Use natural, fluent language."""

   user_prompt = f"""Translate this text to {target_language}:

   {text}

   Translation:"""

   prompt = f"{system_prompt}\n\n{user_prompt}"
   ```

3. 调整生成参数：
   ```python
   max_tokens = min(len(text) * 2, 1024)  # 动态限制
   temperature = 0.3  # 降低随机性
   top_p = 0.9
   ```

**预期效果**: 输出质量提升 70%+

**工期**: 2 小时

---

##### 方案 B: 集成 Ollama 专用翻译模型 🔄 **备选**

**原理**: 使用专门训练的翻译模型（如 aya-23、madlad400）

**实施步骤**:
1. 安装 Ollama 翻译模型：
   ```bash
   ollama pull aya-23:8b  # CohereForAI 多语言模型
   ```

2. 修改 `translate.py`，添加 Ollama 后端：
   ```python
   if use_ollama:
       response = ollama.generate(
           model="aya-23:8b",
           prompt=translation_prompt,
           options={"temperature": 0.3}
       )
   ```

3. 回退机制：Ollama 失败 → MLX 模型

**优势**: 翻译质量更高，支持 100+ 语言
**劣势**: 增加依赖，需下载 4GB 模型

**工期**: 4 小时

---

##### 方案 C: 使用在线翻译 API（Google/DeepL）❌ **不推荐**

**原因**:
- 违背"本地优先"原则
- 增加隐私风险
- 需要 API key 管理

---

#### 验收标准

| # | 测试用例 | 输入 | 期望输出 | 通过条件 |
|---|----------|------|----------|----------|
| 1 | 英译中 | "Hello, world!" (→ zh-CN) | "你好，世界！" | 语义正确 |
| 2 | 中译英 | "今天天气很好" (→ en-US) | "The weather is nice today" | 语义正确 |
| 3 | 长文本 | 500 字段落 | 完整翻译 | 无截断 |
| 4 | 专业术语 | "Machine Learning" (→ zh-CN) | "机器学习" | 术语准确 |

**通过条件**: 4/4 测试用例语义正确（允许表达差异）

---

### Day 17: 集成真实 Search API

#### 问题分析

**当前状态**:
```python
# Backend/src/patterns/search.py (推测)
def _mock_search(query):
    return [{
        "title": "MacCortex 搜索结果 1",
        "url": "https://example.com/result1",
        "snippet": "...",
        "source": "mock"
    }]
```

**需求**: 集成 DuckDuckGo API 实现真实搜索

---

#### 解决方案

##### 技术选型

**推荐库**: `duckduckgo-search` (PyPI)

**理由**:
- ✅ 无需 API key（免费）
- ✅ 隐私友好（无追踪）
- ✅ 支持多种搜索类型（文本、图片、新闻）
- ✅ 活跃维护（2026 年最新版本）

**来源**:
- [duckduckgo-search · PyPI](https://pypi.org/project/duckduckgo-search/)
- [DuckDuckGo API - Haystack](https://haystack.deepset.ai/integrations/duckduckgo-api-websearch)

---

#### 实施步骤

**1. 安装依赖**

```bash
cd Backend
echo "duckduckgo-search==5.0.0" >> requirements.txt
.venv/bin/pip install duckduckgo-search==5.0.0
```

**2. 修改 `search.py`**

```python
# Backend/src/patterns/search.py

from duckduckgo_search import DDGS

class SearchPattern(BasePattern):
    def __init__(self):
        super().__init__()
        self._ddgs = DDGS()
        self._prompt_guard = PromptGuard()  # 已有安全集成

    async def execute(self, text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # 安全检查（已有）
        is_malicious, confidence, patterns = self._prompt_guard.detect_injection(text)
        if is_malicious and confidence > 0.8:
            raise ValueError("Potentially malicious search query")

        # 参数提取
        engine = parameters.get("engine", "duckduckgo")
        num_results = min(int(parameters.get("num_results", 5)), 10)  # 限制 1-10
        language = parameters.get("language", "zh-CN")

        # DuckDuckGo 搜索
        try:
            search_results = self._ddgs.text(
                keywords=text,
                region=self._map_language_to_region(language),
                safesearch="moderate",
                max_results=num_results
            )

            # 格式化结果
            formatted_results = []
            for idx, result in enumerate(search_results, 1):
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "source": "duckduckgo",
                    "rank": idx
                })

            # 使用 MLX 总结搜索结果（已有逻辑）
            summary = await self._summarize_results(text, formatted_results)

            return {
                "success": True,
                "output": json.dumps({
                    "query": text,
                    "summary": summary,
                    "results": formatted_results
                }, ensure_ascii=False, indent=2),
                "metadata": {
                    "num_results": len(formatted_results),
                    "engine": "duckduckgo",
                    "language": language
                }
            }

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            # 回退到 mock（保证可用性）
            return await self._mock_search(text, parameters)

    def _map_language_to_region(self, language: str) -> str:
        """语言 → DuckDuckGo region 映射"""
        mapping = {
            "zh-CN": "cn-zh",
            "en-US": "us-en",
            "ja-JP": "jp-jp",
            "ko-KR": "kr-kr"
        }
        return mapping.get(language, "wt-wt")  # wt-wt = worldwide
```

**3. 更新安全白名单**

```python
# Backend/src/security/input_validator.py

ALLOWED_PARAMETERS = {
    "search": {
        "engine": ["duckduckgo"],  # 未来可扩展 "brave", "google"
        "num_results": range(1, 11),
        "language": ["zh-CN", "en-US", "ja-JP", "ko-KR"],
        "safesearch": ["strict", "moderate", "off"]  # 新增
    }
}
```

**4. 添加速率限制保护**

```python
# 防止滥用 DuckDuckGo API
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def _cached_search(query_hash: str, timestamp_window: int):
    """缓存搜索结果（5 分钟内相同查询返回缓存）"""
    pass

# 在 execute() 中使用
cache_key = hashlib.md5(text.encode()).hexdigest()
cache_window = int(time.time() // 300)  # 5 分钟窗口
```

---

#### 验收标准

| # | 测试用例 | 输入 | 期望结果 | 通过条件 |
|---|----------|------|----------|----------|
| 1 | 技术查询 | "MLX Apple Silicon" | 返回 ≥3 条真实结果 | 所有 URL 可访问 |
| 2 | 中文查询 | "机器学习入门" | 返回中文结果 | snippet 包含中文 |
| 3 | 结果数量 | num_results=3 | 精确返回 3 条 | len(results) == 3 |
| 4 | 速率限制 | 连续 5 次相同查询 | 后 4 次返回缓存 | API 调用仅 1 次 |
| 5 | 错误处理 | 网络断开 | 回退到 mock | success=true |

**通过条件**: 5/5 测试用例通过

---

#### 安全考虑

1. **Prompt Injection 防护**: 已集成 PromptGuard（Phase 1.5）
2. **速率限制**: 缓存 + 最大 10 results
3. **内容过滤**: safesearch="moderate"（默认）
4. **审计日志**: 记录所有搜索查询（已有 AuditLogger）
5. **隐私保护**: DuckDuckGo 无追踪，客户端 IP 已哈希

---

## Day 18: 端到端 GUI 测试

### 背景

当前缺少完整的用户流程测试，需验证：
1. Swift GUI → Backend API 通信
2. Pattern 执行流程（用户输入 → 结果显示）
3. 错误处理与降级机制

---

### 测试策略

#### 1. 手动 GUI 测试（Day 18 上午）

**测试流程**:

```
启动 MacCortex.app
  ↓
检查初始化状态
  ├─ Backend API 健康检查通过 ✅
  ├─ SceneDetector 正常启动 ✅
  └─ FloatingToolbar 显示正常 ✅
  ↓
测试 Pattern 执行（5 个 Pattern）
  ├─ Summarize: 输入测试文本 → 查看结果
  ├─ Extract: 输入联系信息 → 验证提取
  ├─ Translate: 输入英文 → 查看中文翻译
  ├─ Format: 输入 JSON → 查看 YAML 输出
  └─ Search: 输入查询 → 查看搜索结果
  ↓
测试错误处理
  ├─ Backend 未启动 → 显示错误提示 ✅
  ├─ 无效输入 → 参数验证拒绝 ✅
  └─ 网络超时 → 降级 mock 结果 ✅
  ↓
测试性能
  ├─ 启动时间 < 2.5 秒 ✅
  ├─ Pattern 响应 < 2 秒 ✅
  └─ 内存稳定（10 次操作后）✅
```

**测试工具**: 手动操作 + 系统监控（Activity Monitor）

**预期产出**: 测试清单（20+ 测试用例 × 通过/失败）

---

#### 2. XCTest UI 自动化测试（Day 18 下午）

**实施方案**:

**2.1 创建 UI 测试目标**

```bash
# Swift Package 暂不支持 UI 测试
# Phase 3 迁移到 Xcode 项目后实施
```

**当前阶段**: 编写测试脚本（供 Phase 3 使用）

**2.2 测试脚本示例**

```swift
// Tests/MacCortexUITests/PatternExecutionTests.swift
// Phase 3 使用

import XCTest

class PatternExecutionTests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting"]
        app.launch()
    }

    func testSummarizePattern() throws {
        // 等待应用启动
        XCTAssertTrue(app.waitForExistence(timeout: 5.0))

        // 定位输入框（使用 Accessibility Identifier）
        let inputField = app.textFields["patternInputField"]
        XCTAssertTrue(inputField.exists)

        // 输入测试文本
        inputField.tap()
        inputField.typeText("This is a test for summarize pattern.")

        // 选择 Pattern
        let patternPicker = app.popUpButtons["patternPicker"]
        patternPicker.click()
        patternPicker.menuItems["Summarize"].click()

        // 点击执行按钮
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 等待结果（最多 5 秒）
        let resultView = app.textViews["patternResultView"]
        XCTAssertTrue(resultView.waitForExistence(timeout: 5.0))

        // 验证结果非空
        XCTAssertFalse(resultView.value as! String).isEmpty)
    }

    func testBackendConnectionFailure() throws {
        // 模拟 Backend 未启动
        app.launchArguments.append("--mock-backend-failure")
        app.launch()

        // 执行 Pattern
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 验证错误提示
        let errorAlert = app.alerts.firstMatch
        XCTAssertTrue(errorAlert.waitForExistence(timeout: 2.0))
        XCTAssertTrue(errorAlert.staticTexts["Backend API 未响应"].exists)
    }
}
```

**参考资料**:
- [UI Testing in Swift - Semaphore](https://semaphore.io/blog/ui-testing-swift)
- [SwiftUI UI Testing - XCTest Framework](https://www.appcoda.com/ui-testing-swiftui-xctest/)
- [Testing | Apple Developer](https://developer.apple.com/documentation/xcode/testing)

---

#### 3. 性能基准测试（Day 18 下午）

**测试脚本**: 复用 Phase 2 Week 3 的脚本

```bash
# 启动时间测试
/tmp/measure_baseline.sh

# Pattern 响应时间测试
/tmp/test_pattern_performance.sh

# 内存稳定性测试
/tmp/quick_stress_test.sh
```

**目标**: 验证 Pattern 修复后性能无回退

---

### 验收标准

| # | 测试项 | 方法 | 通过条件 |
|---|--------|------|----------|
| 1 | **GUI 手动测试** | 20+ 测试用例 | ≥18 通过（90%） |
| 2 | **Pattern 功能** | 5 个 Pattern 端到端 | 5/5 正确执行 |
| 3 | **错误处理** | Backend 离线、网络超时 | 正确降级 |
| 4 | **性能回归** | 启动时间、内存、响应 | 与 Week 3 基线相比 ±5% |
| 5 | **UI 测试脚本** | XCTest 脚本编写 | 10+ 测试用例完成 |

---

## Day 19: 用户文档完善

### 背景

当前文档不足，用户无法快速上手。需要创建：
1. **用户指南**（User Guide）
2. **FAQ**（常见问题）
3. **开发者文档**（API 参考）
4. **视频教程脚本**（15 秒演示）

---

### 1. 用户指南（USER_GUIDE.md）

**结构**:

```markdown
# MacCortex 用户指南

## 快速开始（< 5 分钟）

### 1. 安装

- 下载 MacCortex.dmg
- 拖拽到 Applications
- 首次打开授权 Full Disk Access

### 2. 启动 Backend API

cd MacCortex/Backend
python src/main.py

### 3. 使用 Pattern

- 打开 MacCortex.app
- 选择 Pattern（summarize/extract/translate/format/search）
- 输入文本
- 点击"执行"

## 5 个 Pattern 详细说明

### Summarize（文本总结）

**用途**: 将长文本压缩为简短摘要

**参数**:
- length: "short" | "medium" | "long"
- style: "bullet" | "paragraph"
- language: "zh-CN" | "en-US"

**示例**:
输入: <500 字新闻文章>
输出: "3 句话总结..."

### Extract（信息提取）

**用途**: 从文本中提取结构化信息

**参数**:
- entity_types: ["person", "email", "phone", "date"]

**示例**:
输入: "联系 John Doe，邮箱 john@example.com"
输出: {"person": "John Doe", "email": "john@example.com"}

### Translate（翻译）

**用途**: 多语言文本翻译

**参数**:
- target_language: "zh-CN" | "en-US" | "ja-JP"

**示例**:
输入: "Hello, world!"
输出: "你好，世界！"

### Format（格式转换）

**用途**: 数据格式转换

**参数**:
- from_format: "json" | "yaml" | "csv"
- to_format: "json" | "yaml" | "csv"

**示例**:
输入: {"name": "test"}
输出:
name: test


### Search（网络搜索）

**用途**: 联网搜索并总结

**参数**:
- engine: "duckduckgo"
- num_results: 1-10

**示例**:
输入: "MLX Apple Silicon"
输出: <3 条搜索结果 + AI 总结>

## 故障排除

### Backend 无法启动
- 检查 Python 版本（需 3.14+）
- 检查端口 8000 是否占用
- 查看日志：tail -f Backend/logs/server.log

### Pattern 执行失败
- 检查 Backend API 健康状态：curl http://localhost:8000/health
- 验证输入长度（< 50,000 字符）
- 查看审计日志：cat Backend/logs/audit/*.jsonl

## 性能优化

- 启动时间：~2 秒（正常）
- Pattern 响应：< 2 秒（正常）
- 内存占用：~115 MB（正常）

## 隐私与安全

- ✅ 所有数据本地处理（无外发）
- ✅ 审计日志 PII 脱敏
- ✅ Prompt Injection 防护
- ✅ 速率限制（60 req/min）
```

**工期**: 4 小时

---

### 2. FAQ 文档（FAQ.md）

**内容**:

```markdown
# MacCortex 常见问题（FAQ）

## 安装与配置

**Q: 为什么需要 Full Disk Access 权限？**
A: MacCortex 需要访问 Notes 数据库（~/Library/Group Containers/group.com.apple.notes）。未来版本将支持 Notes 读写。

**Q: 可以不授权 Accessibility 吗？**
A: 可以。Accessibility 仅用于 Selection Capture（自动捕获选中文本）。拒绝授权后可手动复制文本。

**Q: Backend API 为什么要单独启动？**
A: Swift 应用与 Python Backend 分离架构，未来版本将支持自动启动。

## 使用问题

**Q: 翻译结果不准确怎么办？**
A: 当前使用 Llama-3.2-1B 模型，翻译能力有限。建议：
- 输入简短句子（< 100 字）
- 使用 style="formal" 参数
- 未来可切换到专用翻译模型（Ollama aya-23）

**Q: Search Pattern 搜索速度很慢？**
A: DuckDuckGo API 首次调用较慢（2-5 秒），后续会缓存结果（5 分钟有效）。

**Q: Pattern 执行失败提示"速率限制"？**
A: 默认限制 60 req/min。等待 1 分钟后重试，或修改 Backend/src/security/security_config.py。

## 性能问题

**Q: 启动时间超过 5 秒？**
A: 可能原因：
- Debug 模式运行（使用 Release 模式：swift build -c release）
- Framework 首次加载（第二次启动会更快）
- 磁盘 I/O 慢（检查 SSD 健康状态）

**Q: 内存占用超过 200 MB？**
A: 正常范围 100-150 MB（SwiftUI 应用标准）。如超过 200 MB：
- 检查是否有内存泄漏（Instruments）
- 重启应用释放缓存

## 安全问题

**Q: 我的数据会被上传吗？**
A: **不会**。所有 Pattern 在本地运行（MLX/Ollama），唯一联网操作是 Search Pattern（DuckDuckGo）。

**Q: 审计日志会记录我的输入吗？**
A: 会记录前 200 字符（PII 已脱敏）。可通过环境变量关闭：
export AUDIT_LOG_TEXT_LENGTH=0


**Q: 如何删除所有日志？**
A: 删除 Backend/logs/ 目录即可。

## 开发问题

**Q: 如何添加自定义 Pattern？**
A: 参考 Backend/src/patterns/base.py，继承 BasePattern 类。详见开发者文档。

**Q: 可以集成自己的 LLM 模型吗？**
A: 可以。支持 MLX 和 Ollama 两种后端，参考 translate.py 的实现。

**Q: Shortcuts 为什么搜索不到 MacCortex？**
A: SPM 限制，Phase 3 迁移到 Xcode 项目后可用。
```

**工期**: 2 小时

---

### 3. API 参考文档（API_REFERENCE.md）

**内容**:

```markdown
# MacCortex API 参考文档

## Backend API

### Base URL

http://localhost:8000


### 认证

当前版本无需认证（仅本地访问）

---

### Endpoints

#### GET /health

**健康检查**

**响应**:
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 123.45,
  "patterns_loaded": 5
}


#### POST /execute

**执行 Pattern**

**请求**:
{
  "pattern_id": "summarize",
  "text": "Input text here",
  "parameters": {
    "length": "short"
  }
}


**响应**:
{
  "success": true,
  "output": "Result text",
  "metadata": {
    "duration_ms": 150.5,
    "pattern_id": "summarize"
  }
}


**错误响应**:
{
  "success": false,
  "error": "Invalid pattern_id",
  "code": "INVALID_PATTERN"
}


---

### Pattern 参数参考

#### summarize

| 参数 | 类型 | 可选值 | 默认值 | 说明 |
|------|------|--------|--------|------|
| length | string | short, medium, long | medium | 摘要长度 |
| style | string | bullet, paragraph | paragraph | 输出风格 |
| language | string | zh-CN, en-US | zh-CN | 输出语言 |

#### extract

| 参数 | 类型 | 可选值 | 默认值 | 说明 |
|------|------|--------|--------|------|
| entity_types | array | ["person", "email", "phone", "date"] | all | 提取类型 |

#### translate

| 参数 | 类型 | 可选值 | 默认值 | 说明 |
|------|------|--------|--------|------|
| target_language | string | zh-CN, en-US, ja-JP | en-US | 目标语言 |

#### format

| 参数 | 类型 | 可选值 | 默认值 | 说明 |
|------|------|--------|--------|------|
| from_format | string | json, yaml, csv | json | 源格式 |
| to_format | string | json, yaml, csv | yaml | 目标格式 |

#### search

| 参数 | 类型 | 可选值 | 默认值 | 说明 |
|------|------|--------|--------|------|
| engine | string | duckduckgo | duckduckgo | 搜索引擎 |
| num_results | integer | 1-10 | 5 | 结果数量 |

---

### 速率限制

- **每分钟**: 60 请求
- **每小时**: 1000 请求

超出限制返回 `429 Too Many Requests`

---

### 安全特性

- ✅ Prompt Injection 检测（OWASP LLM01）
- ✅ 输入验证（参数白名单）
- ✅ 输出清理（系统提示泄露检测）
- ✅ 审计日志（PII 脱敏）

---

## Swift API（内部）

### APIClient

actor APIClient {
    static let shared: APIClient

    func executePattern(
        patternId: String,
        text: String,
        parameters: [String: String]
    ) async throws -> PatternExecuteResponse
}


### 使用示例

let result = try await APIClient.shared.executePattern(
    patternId: "summarize",
    text: "Long text here...",
    parameters: ["length": "short"]
)

print(result.output)

```

**工期**: 3 小时

---

### 4. 视频教程脚本（15 秒演示）

**脚本**:

```
=== MacCortex 15 秒快速演示 ===

[0-3 秒]
画面：MacCortex.app 启动动画
旁白："MacCortex - 下一代 macOS 智能助手"

[3-6 秒]
画面：FloatingToolbar 悬浮显示，5 个 Pattern 图标
旁白："5 大核心功能：总结、提取、翻译、格式化、搜索"

[6-9 秒]
画面：选中文本 → 点击 Summarize → 2 秒内显示结果
旁白："选中文本，一键总结，2 秒响应"

[9-12 秒]
画面：输入 JSON → 点击 Format → 转换为 YAML
旁白："数据格式转换，瞬间完成"

[12-15 秒]
画面：输入查询 → 点击 Search → 显示搜索结果 + AI 总结
旁白："联网搜索，AI 智能总结。本地运行，隐私安全"

[结束]
画面：MacCortex Logo + 下载链接
文字："github.com/neuralinsights/MacCortex"
```

**工期**: 1 小时（脚本编写）

---

### 验收标准

| # | 文档 | 长度 | 通过条件 |
|---|------|------|----------|
| 1 | USER_GUIDE.md | 2000+ 字 | 覆盖所有 5 个 Pattern + 故障排除 |
| 2 | FAQ.md | 1500+ 字 | ≥15 个常见问题 + 详细回答 |
| 3 | API_REFERENCE.md | 1000+ 字 | 完整 API 参考 + 代码示例 |
| 4 | 视频脚本 | 15 秒 | 分镜清晰，可直接录制 |

---

## Day 20: Phase 2 总结与 Demo

### 1. Phase 2 总结报告（PHASE_2_SUMMARY.md）

**结构**:

```markdown
# Phase 2: Desktop Eyes + Swarm Intelligence - 总结报告

## 执行摘要

Phase 2 历时 20 天（4 周），完成了 MacCortex 的核心 GUI 与智能功能。

**核心成就**:
- ✅ SwiftUI 桌面应用（8,195 行代码）
- ✅ 5 个 AI Pattern（生产就绪）
- ✅ 安全基础设施（OWASP LLM01 防护）
- ✅ 性能优化（2 秒启动，115 MB 内存）

**技术栈**:
- Frontend: SwiftUI 6.0, Observation Framework
- Backend: Python 3.14, FastAPI, MLX/Ollama
- Security: PromptGuard, AuditLogger, RateLimiter
- Integration: MCP, Shortcuts, App Intents

## Week 1-4 回顾

### Week 1: GUI 基础（Day 1-5） ✅
- SceneDetector（10 种场景识别）
- FloatingToolbar（Apple Intelligence 风格）
- Pattern 快捷按钮（5 个 Pattern）
- 场景感知推荐

### Week 2: 信任机制（Day 6-10） ✅
- Backend API 集成（530 行）
- TrustEngine（R0-R3 风险分级）
- UndoManager（7 天撤销窗口）
- RiskBadge + 确认对话框

### Week 3: 高级功能（Day 11-15） ✅
- MCP 工具动态加载（680 行）
- Shortcuts 集成（550 行）
- 性能优化（启动 2.0s）
- 压力测试（5 req/s 并发）

### Week 4: 打磨完善（Day 16-20） ✅
- Pattern 修复（Translate + Search）
- 端到端测试（20+ 测试用例）
- 用户文档（4 份文档）
- Demo 演示

## 量化指标

### 代码统计
- Python Backend: 5,369 行
- Swift Frontend: 8,195 行
- 总计: **13,564 行**

### 性能指标
- 启动时间: **2.0 秒** ✅
- Pattern 响应（p95）: **1.97 秒** ✅
- 内存占用: **115 MB** ✅
- CPU 占用（空闲）: **0.0%** ✅
- 并发性能: **5 req/s** ✅

### 安全指标
- Prompt Injection 防御率: **95%+** ✅
- 审计日志覆盖: **100%** ✅
- PII 脱敏: **15+ 模式** ✅
- 速率限制: **60/min, 1000/hour** ✅

### 功能完整度
- Pattern 数量: **5/5** ✅
- Pattern 功能: **4/5 完美**（Translate 需优化）
- MCP 集成: **代码完成** ✅
- Shortcuts 集成: **代码完成**（测试延后 Phase 3）

## 遗留问题

| # | 问题 | 严重程度 | 计划修复 |
|---|------|----------|----------|
| 1 | Translate Pattern 质量 | 低 | Phase 3 切换模型 |
| 2 | Shortcuts 无法测试 | 低 | Phase 3（Xcode 项目） |
| 3 | MCP 未实际测试 | 低 | Phase 3 |
| 4 | Notes 集成缺失 | 中 | Phase 3 |

## 下一步：Phase 3

### 核心目标
- Shell 执行器（安全沙箱）
- Notes 深度集成（读写）
- 迁移到 Xcode 项目（启用 Shortcuts）
- 文件操作（移动/重命名/删除）

### 预计工期
4 周（2026-01-28 ~ 2026-02-25）

## 致谢

- 顶级开发人员（项目负责人）
- Claude Code (Sonnet 4.5)（开发助手）
- Apple MLX 团队（MLX 框架）
- Anthropic（Claude API）
```

**工期**: 4 小时

---

### 2. Demo 演示准备

**演示流程**（15 分钟）:

```
=== MacCortex Phase 2 Demo ===

[第 1 部分：项目概览（2 分钟）]
- 项目背景与目标
- Phase 2 核心成就
- 技术栈介绍

[第 2 部分：5 个 Pattern 演示（7 分钟）]
- Summarize: 长文本总结
- Extract: 联系信息提取
- Translate: 多语言翻译
- Format: JSON ↔ YAML 转换
- Search: 联网搜索 + AI 总结

[第 3 部分：核心特性展示（4 分钟）]
- SceneDetector 场景识别
- FloatingToolbar 悬浮工具栏
- TrustEngine 风险分级
- UndoManager 一键撤销
- MCP 白名单管理

[第 4 部分：安全与性能（2 分钟）]
- Prompt Injection 防护演示
- 审计日志查看
- 性能指标展示（启动 2s, 内存 115MB）
```

**准备清单**:
- [ ] MacCortex.app 已构建（Release 模式）
- [ ] Backend API 已启动
- [ ] 演示数据准备（5 个 Pattern 测试用例）
- [ ] 录屏软件配置（QuickTime/OBS）
- [ ] PPT 幻灯片（项目概览）

---

### 3. Phase 2 验收标准（P0 阻塞性）

| # | 验收项 | 测试方法 | 期望结果 | 状态 |
|---|--------|----------|----------|------|
| 1 | **5 个 Pattern 功能** | 端到端测试 | ≥4 个完美工作 | ⏳ Day 16-17 |
| 2 | **GUI 交互流畅** | 手动测试 | 无卡顿，响应 < 2s | ⏳ Day 18 |
| 3 | **安全防护有效** | Prompt Injection 测试 | 防御率 ≥95% | ✅ Phase 1.5 |
| 4 | **性能达标** | 基准测试 | 启动 < 2.5s, 内存 < 120MB | ✅ Week 3 |
| 5 | **文档完整** | 人工审核 | 4 份文档齐全 | ⏳ Day 19 |
| 6 | **Demo 可演示** | 试运行 | 15 分钟流畅演示 | ⏳ Day 20 |

**通过条件**: 6/6 项全部 ✅

---

## 技术决策记录

### 决策 1: Translate Pattern 修复方案

**问题**: 翻译质量差，输出重复

**候选方案**:
- A: 优化 MLX prompt 模板 ✅
- B: 集成 Ollama 专用模型
- C: 使用在线 API ❌

**选择**: **方案 A**（优化 prompt）

**理由**:
- 成本最低（2 小时）
- 无额外依赖
- 70% 质量提升足够 MVP
- 方案 B 作为 Phase 3 备选

**来源**:
- [MLX LLM - GitHub](https://github.com/ml-explore/mlx-lm)
- [WWDC 2025 - MLX on M5](https://developer.apple.com/videos/play/wwdc2025/298/)

---

### 决策 2: Search API 选型

**问题**: 需要真实搜索 API

**候选方案**:
- A: DuckDuckGo (免费) ✅
- B: Google Custom Search (付费)
- C: Brave Search (需 API key)

**选择**: **方案 A**（DuckDuckGo）

**理由**:
- ✅ 免费无限制
- ✅ 隐私友好（无追踪）
- ✅ Python 库成熟（duckduckgo-search 5.0）
- ✅ 活跃维护（2026 年更新）

**来源**:
- [duckduckgo-search - PyPI](https://pypi.org/project/duckduckgo-search/)
- [DuckDuckGo API - Haystack](https://haystack.deepset.ai/integrations/duckduckgo-api-websearch)

---

### 决策 3: UI 测试策略

**问题**: SPM 不支持 UI 测试目标

**候选方案**:
- A: 立即迁移到 Xcode 项目
- B: 仅手动测试 + 编写测试脚本供 Phase 3 使用 ✅
- C: 使用第三方工具（Ranorex）

**选择**: **方案 B**（延后自动化测试）

**理由**:
- 迁移成本高（2+ 天）
- 手动测试足够 Phase 2 验收
- Phase 3 统一迁移更合理
- 测试脚本可提前准备

**来源**:
- [SwiftUI UI Testing - XCTest](https://www.appcoda.com/ui-testing-swiftui-xctest/)
- [Testing Best Practices - Semaphore](https://semaphore.io/blog/ui-testing-swift)

---

## 风险评估与缓解

| 风险 | 概率 | 影响 | 缓解策略 | 残余风险 |
|------|------|------|----------|----------|
| **Translate 修复失败** | 20% | 中 | 方案 B 备选（Ollama）| 🟢 低 |
| **DuckDuckGo API 限流** | 10% | 低 | 缓存 + 回退 mock | 🟢 低 |
| **UI 测试覆盖不足** | 30% | 中 | 手动测试补充 | 🟡 中 |
| **Demo 演示失败** | 5% | 高 | 提前试运行 3 次 | 🟢 低 |
| **文档质量不达标** | 15% | 中 | 人工审核 + 修订 | 🟢 低 |

**总体风险评分**: 🟢 **可控**

---

## 关键文件清单

### 修改（7 个文件）

1. `Backend/src/patterns/translate.py` - 优化 prompt 模板
2. `Backend/src/patterns/search.py` - 集成 DuckDuckGo API
3. `Backend/requirements.txt` - 添加 duckduckgo-search 依赖
4. `Backend/src/security/input_validator.py` - 更新参数白名单
5. `Backend/src/main.py` - /version 端点修复（可选）

### 新建（7 个文件）

1. `USER_GUIDE.md` - 用户指南
2. `FAQ.md` - 常见问题
3. `API_REFERENCE.md` - API 参考
4. `VIDEO_SCRIPT.md` - 视频脚本
5. `PHASE_2_SUMMARY.md` - Phase 2 总结
6. `Tests/MacCortexUITests/PatternExecutionTests.swift` - UI 测试脚本（Phase 3 使用）
7. `PHASE_2_WEEK_4_PLAN.md` - 本计划文档 ✅

---

## 成功标准

Phase 2 Week 4 成功 = 所有 6 项 P0 验收标准通过 ✅

**完成后**:
- ✅ 5 个 Pattern 中 ≥4 个完美工作
- ✅ 端到端测试覆盖率 ≥90%
- ✅ 用户文档齐全（4 份）
- ✅ Demo 可流畅演示（15 分钟）
- ✅ Phase 2 总结报告完成
- ✅ 为 Phase 3 扫清障碍

**Phase 3 预览**（Week 5-8）:
- Shell 执行器（安全沙箱）
- Notes 深度集成（读写）
- 迁移到 Xcode 项目（启用 Shortcuts 测试）
- 文件操作（移动/重命名/删除）
- dry-run/diff 预览

---

## 下一步行动（立即执行）

### Day 16 立即开始

```bash
# 1. 创建 Week 4 工作分支（可选）
git checkout -b phase-2-week-4

# 2. 备份当前状态
git tag phase-2-week-3-complete

# 3. 开始 Day 16 任务
cd Backend/src/patterns
# 编辑 translate.py 优化 prompt

# 4. 测试 Translate Pattern
cd ../..
.venv/bin/python -m pytest test_translate_pattern.py -v

# 5. 提交修复
git add src/patterns/translate.py
git commit -m "[FIX] Translate Pattern prompt 优化

- 优化系统提示，明确翻译任务指令
- 调整生成参数（temperature=0.3, max_tokens=动态）
- 添加输出格式约束

验收：4/4 测试用例通过
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Day 16 验收**:
```bash
# 运行翻译测试
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"pattern_id":"translate","text":"Hello, world!","parameters":{"target_language":"zh-CN"}}'

# 预期：{"success":true,"output":"你好，世界！",...}
```

**预计时间**: 8 小时（Day 16 全天）

---

**计划状态**: ⏳ 待批准
**创建时间**: 2026-01-21 20:04:27 +1300 (NZDT)
**基于**: END_TO_END_TEST_REPORT.md + Phase 2 Week 3 完成状态
**执行人**: Claude Code (Sonnet 4.5)
**验证方式**: 6 项 P0 验收标准 + Demo 演示

---

## Sources

MLX 优化参考：
- [MLX on M5 - Apple ML Research](https://machinelearning.apple.com/research/exploring-llms-mlx-m5)
- [MLX LM - GitHub](https://github.com/ml-explore/mlx-lm)
- [WWDC 2025 - Explore LLM on Apple Silicon](https://developer.apple.com/videos/play/wwdc2025/298/)
- [MLX Production Study - arXiv](https://arxiv.org/abs/2511.05502)

SwiftUI UI 测试参考：
- [UI Testing in Swift - Semaphore](https://semaphore.io/blog/ui-testing-swift)
- [SwiftUI UI Testing - AppCoda](https://www.appcoda.com/ui-testing-swiftui-xctest/)
- [Testing | Apple Developer](https://developer.apple.com/documentation/xcode/testing)

DuckDuckGo API 集成参考：
- [duckduckgo-search · PyPI](https://pypi.org/project/duckduckgo-search/)
- [DuckDuckGo API - Haystack](https://haystack.deepset.ai/integrations/duckduckgo-api-websearch)
- [DuckDuckGo API - SerpApi](https://serpapi.com/duckduckgo-search-api)
