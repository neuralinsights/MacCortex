# MacCortex GUI 端到端测试计划

**创建时间**: 2026-01-21
**Phase**: Phase 2 Week 4 Day 18
**测试类型**: 手动 + 自动化（XCTest）
**状态**: 📋 测试计划完成

---

## 测试环境

**系统配置**:
- macOS: Tahoe 26.2 (Darwin 25.2.0)
- 设备: Apple Silicon (arm64)
- Backend: Python 3.11 + FastAPI (http://localhost:8000)
- Frontend: SwiftUI + SPM 构建

**前置条件**:
- ✅ Backend API 正在运行（PID 13833）
- ✅ MacCortex.app 正在运行（PID 11489）
- ✅ 5 个 Pattern 已加载（summarize, extract, translate, format, search）
- ✅ MLX 模型已加载（Llama-3.2-1B-Instruct-4bit）

---

## 测试清单（20+ 测试用例）

### 分类 1: 应用启动与初始化（5 个测试）

#### 1.1 应用冷启动
- **步骤**:
  1. 完全退出 MacCortex.app
  2. 启动 MacCortex.app
  3. 观察启动时间和界面加载
- **预期结果**:
  - 启动时间 < 3 秒
  - 主界面正确显示
  - 无崩溃或错误提示
- **验证点**:
  - 启动时间
  - 界面元素完整性
  - 日志无错误
- **状态**: ⏳ 待测试

#### 1.2 后台通信验证
- **步骤**:
  1. 打开 MacCortex.app
  2. 观察状态栏或日志
  3. 确认与 Backend 的连接状态
- **预期结果**:
  - 显示"已连接"或类似状态
  - 可以获取 Pattern 列表
- **验证点**:
  - Backend 连接状态
  - 网络请求成功
- **状态**: ⏳ 待测试

#### 1.3 Pattern 列表加载
- **步骤**:
  1. 查看 Pattern 选择器/列表
  2. 确认所有 Pattern 显示
- **预期结果**:
  - 显示 5 个 Pattern（summarize, extract, translate, format, search）
  - 每个 Pattern 有名称和描述
- **验证点**:
  - Pattern 数量
  - 名称和描述正确
- **状态**: ⏳ 待测试

#### 1.4 内存占用检查
- **步骤**:
  1. 启动应用后等待 10 秒
  2. 使用 Activity Monitor 检查内存占用
- **预期结果**:
  - 内存占用 < 200 MB（空闲状态）
- **验证点**:
  - 内存占用量
  - 无内存泄漏
- **状态**: ⏳ 待测试

#### 1.5 权限状态检查
- **步骤**:
  1. 检查 Full Disk Access 权限状态
  2. 检查 Accessibility 权限状态（如需要）
- **预期结果**:
  - 显示当前权限状态
  - 提供授权引导（如未授权）
- **验证点**:
  - 权限检测准确
  - 引导流程清晰
- **状态**: ⏳ 待测试

---

### 分类 2: Pattern 功能测试（10 个测试）

#### 2.1 Summarize Pattern - 短文本
- **步骤**:
  1. 选择 Summarize Pattern
  2. 输入短文本（50-100 字）
  3. 点击执行
- **输入示例**: "MacCortex is a next-generation macOS personal AI infrastructure built with Swift and Python. It integrates multiple LLM models and provides 5 AI patterns."
- **预期结果**:
  - 响应时间 < 3 秒
  - 生成合理的总结
  - 无错误提示
- **验证点**:
  - 响应速度
  - 总结质量
  - 错误处理
- **状态**: ⏳ 待测试

#### 2.2 Summarize Pattern - 长文本
- **步骤**:
  1. 输入长文本（500+ 字）
  2. 执行 Summarize
- **预期结果**:
  - 响应时间 < 5 秒
  - 总结长度合理（10-20% 原文）
- **验证点**:
  - 长文本处理能力
  - 响应时间
- **状态**: ⏳ 待测试

#### 2.3 Extract Pattern - 实体提取
- **步骤**:
  1. 选择 Extract Pattern
  2. 输入包含实体的文本
  3. 选择实体类型（person, email, date 等）
- **输入示例**: "Contact John Doe at john@example.com for meeting on 2026-01-25."
- **预期结果**:
  - 成功提取人名、邮箱、日期
  - 返回结构化 JSON
- **验证点**:
  - 实体识别准确率
  - JSON 格式正确
- **状态**: ⏳ 待测试

#### 2.4 Translate Pattern - 英译中
- **步骤**:
  1. 选择 Translate Pattern
  2. 输入英文文本
  3. 目标语言：zh-CN
- **输入示例**: "Hello, how are you?"
- **预期结果**:
  - 返回中文翻译
  - 响应时间 < 3 秒
- **验证点**:
  - 翻译结果存在（质量可能有限，见 TRANSLATE_LIMITATION.md）
  - 无错误
- **状态**: ⏳ 待测试

#### 2.5 Translate Pattern - 中译英
- **步骤**:
  1. 输入中文文本
  2. 目标语言：en
- **输入示例**: "你好，最近怎么样？"
- **预期结果**:
  - 返回英文翻译
- **验证点**:
  - 翻译结果存在
- **状态**: ⏳ 待测试

#### 2.6 Format Pattern - JSON to YAML
- **步骤**:
  1. 选择 Format Pattern
  2. 输入 JSON 文本
  3. from_format: json, to_format: yaml
- **输入示例**: `{"name": "MacCortex", "version": "0.5.0"}`
- **预期结果**:
  - 正确转换为 YAML 格式
  - 格式化美观
- **验证点**:
  - 转换准确性
  - 格式正确
- **状态**: ⏳ 待测试

#### 2.7 Format Pattern - YAML to JSON
- **步骤**:
  1. 输入 YAML 文本
  2. from_format: yaml, to_format: json
- **输入示例**:
  ```yaml
  name: MacCortex
  version: 0.5.0
  ```
- **预期结果**:
  - 正确转换为 JSON
- **验证点**:
  - 转换准确性
- **状态**: ⏳ 待测试

#### 2.8 Search Pattern - Web 搜索
- **步骤**:
  1. 选择 Search Pattern
  2. 输入搜索查询
  3. engine: duckduckgo, num_results: 5
- **输入示例**: "Python async programming"
- **预期结果**:
  - 返回搜索结果（可能是 Mock，见 DUCKDUCKGO_INTEGRATION.md）
  - JSON 格式包含 results 数组
- **验证点**:
  - 返回结果数量
  - JSON 格式正确
- **状态**: ⏳ 待测试

#### 2.9 参数验证 - 无效参数
- **步骤**:
  1. 任意 Pattern
  2. 输入无效参数（如 translate 的 target_language: "invalid"）
  3. 执行
- **预期结果**:
  - 显示友好错误提示
  - 不崩溃
- **验证点**:
  - 错误提示清晰
  - 应用稳定性
- **状态**: ⏳ 待测试

#### 2.10 空输入处理
- **步骤**:
  1. 任意 Pattern
  2. 不输入文本或输入空字符串
  3. 执行
- **预期结果**:
  - 显示"输入不能为空"或类似提示
  - 不发送请求
- **验证点**:
  - 前端验证
  - 错误提示
- **状态**: ⏳ 待测试

---

### 分类 3: 错误处理与边界测试（5 个测试）

#### 3.1 Backend 断开处理
- **步骤**:
  1. 停止 Backend（kill Backend 进程）
  2. 在 MacCortex.app 中执行任意 Pattern
  3. 观察错误提示
- **预期结果**:
  - 显示"无法连接到后端服务"错误
  - 提供重试或检查说明
- **验证点**:
  - 网络错误处理
  - 用户提示友好
- **状态**: ⏳ 待测试

#### 3.2 超长输入处理
- **步骤**:
  1. 输入超长文本（> 50,000 字符）
  2. 执行 Summarize Pattern
- **预期结果**:
  - 前端限制输入长度，或
  - Backend 返回"输入过长"错误
- **验证点**:
  - 输入长度限制
  - 错误处理
- **状态**: ⏳ 待测试

#### 3.3 并发请求测试
- **步骤**:
  1. 快速连续执行 3-5 个 Pattern 请求
  2. 观察处理情况
- **预期结果**:
  - 请求排队或并发处理
  - 无崩溃
  - 所有请求最终完成
- **验证点**:
  - 并发处理能力
  - UI 响应性
- **状态**: ⏳ 待测试

#### 3.4 速率限制测试
- **步骤**:
  1. 在 1 分钟内发送 > 60 个请求
  2. 观察是否触发速率限制
- **预期结果**:
  - 显示"请求过于频繁"提示，或
  - Backend 返回 429 错误
- **验证点**:
  - 速率限制机制
  - 错误提示
- **状态**: ⏳ 待测试

#### 3.5 特殊字符输入
- **步骤**:
  1. 输入包含特殊字符的文本（emoji, Unicode, 控制字符）
  2. 执行 Pattern
- **输入示例**: "Hello 👋 世界 \n\t Test"
- **预期结果**:
  - 正常处理或清理特殊字符
  - 不崩溃
- **验证点**:
  - 特殊字符处理
  - 应用稳定性
- **状态**: ⏳ 待测试

---

### 分类 4: UI/UX 测试（3 个测试）

#### 4.1 界面响应性
- **步骤**:
  1. 在 Pattern 执行期间
  2. 尝试点击其他界面元素
- **预期结果**:
  - UI 不冻结
  - 显示加载指示器
  - 可以取消操作（如有）
- **验证点**:
  - 异步处理
  - 用户体验
- **状态**: ⏳ 待测试

#### 4.2 输出显示
- **步骤**:
  1. 执行任意 Pattern
  2. 观察输出结果显示
- **预期结果**:
  - 结果清晰可读
  - 支持复制输出
  - 格式化美观（JSON/代码高亮）
- **验证点**:
  - 输出格式
  - 复制功能
- **状态**: ⏳ 待测试

#### 4.3 历史记录（如有）
- **步骤**:
  1. 执行多个 Pattern
  2. 查看历史记录或操作历史
- **预期结果**:
  - 显示最近操作
  - 可以重新执行
- **验证点**:
  - 历史记录功能
- **状态**: ⏳ 待测试

---

### 分类 5: 性能与资源测试（2 个测试）

#### 5.1 内存泄漏测试
- **步骤**:
  1. 连续执行 50 个 Pattern 请求
  2. 使用 Activity Monitor 监控内存
- **预期结果**:
  - 内存占用稳定
  - 无持续增长
- **验证点**:
  - 内存管理
  - 资源释放
- **状态**: ⏳ 待测试

#### 5.2 CPU 占用
- **步骤**:
  1. 执行多个 Pattern（特别是 Summarize）
  2. 监控 CPU 占用
- **预期结果**:
  - 空闲时 CPU < 5%
  - 执行时 CPU < 50%（单核）
- **验证点**:
  - CPU 效率
- **状态**: ⏳ 待测试

---

## 自动化测试（XCTest UI）

### 框架设置

**文件位置**: `Tests/UITests/MacCortexUITests.swift`

**测试框架**: XCTest + XCTestUI
**执行条件**: Phase 3（迁移到 Xcode 项目后）

### UI 测试脚本（框架）

```swift
import XCTest

class MacCortexUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    override func tearDownWithError() throws {
        app.terminate()
    }

    // MARK: - 启动测试

    func testAppLaunch() throws {
        // 验证应用启动成功
        XCTAssertTrue(app.windows.firstMatch.exists)

        // 验证主界面元素存在
        let mainWindow = app.windows.firstMatch
        XCTAssertTrue(mainWindow.exists, "主窗口应该存在")

        // 等待 Pattern 列表加载
        let patternPicker = app.popUpButtons["patternPicker"]
        let exists = patternPicker.waitForExistence(timeout: 5)
        XCTAssertTrue(exists, "Pattern 选择器应该在 5 秒内加载")
    }

    // MARK: - Pattern 功能测试

    func testSummarizePattern() throws {
        // 选择 Summarize Pattern
        let patternPicker = app.popUpButtons["patternPicker"]
        patternPicker.click()
        patternPicker.menuItems["Summarize"].click()

        // 输入测试文本
        let inputField = app.textViews["inputTextView"]
        inputField.click()
        inputField.typeText("MacCortex is a next-generation macOS personal AI infrastructure.")

        // 点击执行按钮
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 等待结果
        let outputField = app.textViews["outputTextView"]
        let hasOutput = outputField.waitForExistence(timeout: 10)
        XCTAssertTrue(hasOutput, "应该在 10 秒内返回结果")

        // 验证输出不为空
        let outputText = outputField.value as? String ?? ""
        XCTAssertFalse(outputText.isEmpty, "输出不应为空")
    }

    func testExtractPattern() throws {
        // 选择 Extract Pattern
        let patternPicker = app.popUpButtons["patternPicker"]
        patternPicker.click()
        patternPicker.menuItems["Extract"].click()

        // 输入包含实体的文本
        let inputField = app.textViews["inputTextView"]
        inputField.click()
        inputField.typeText("Contact John Doe at john@example.com for meeting.")

        // 执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 验证结果
        let outputField = app.textViews["outputTextView"]
        let hasOutput = outputField.waitForExistence(timeout: 10)
        XCTAssertTrue(hasOutput)

        // 验证 JSON 格式
        let outputText = outputField.value as? String ?? ""
        XCTAssertTrue(outputText.contains("entities"), "输出应包含 entities 字段")
    }

    func testTranslatePattern() throws {
        // 测试翻译功能
        let patternPicker = app.popUpButtons["patternPicker"]
        patternPicker.click()
        patternPicker.menuItems["Translate"].click()

        // 输入文本
        let inputField = app.textViews["inputTextView"]
        inputField.click()
        inputField.typeText("Hello, world!")

        // 选择目标语言
        let languagePicker = app.popUpButtons["targetLanguagePicker"]
        languagePicker.click()
        languagePicker.menuItems["中文 (zh-CN)"].click()

        // 执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 验证结果
        let outputField = app.textViews["outputTextView"]
        let hasOutput = outputField.waitForExistence(timeout: 10)
        XCTAssertTrue(hasOutput)
    }

    // MARK: - 错误处理测试

    func testEmptyInputValidation() throws {
        // 不输入文本直接执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 验证错误提示
        let errorAlert = app.alerts.firstMatch
        let alertExists = errorAlert.waitForExistence(timeout: 2)
        XCTAssertTrue(alertExists, "应该显示错误提示")

        // 关闭提示
        errorAlert.buttons["确定"].click()
    }

    func testInvalidParameterHandling() throws {
        // 输入无效参数并验证错误处理
        // (具体实现取决于 UI 设计)
    }

    // MARK: - 性能测试

    func testLaunchPerformance() throws {
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            XCUIApplication().launch()
        }
    }

    func testPatternExecutionPerformance() throws {
        let app = XCUIApplication()
        app.launch()

        // 选择 Pattern
        let patternPicker = app.popUpButtons["patternPicker"]
        patternPicker.click()
        patternPicker.menuItems["Summarize"].click()

        // 输入文本
        let inputField = app.textViews["inputTextView"]
        inputField.click()
        inputField.typeText("Test performance measurement.")

        // 测量执行时间
        measure {
            let executeButton = app.buttons["executeButton"]
            executeButton.click()

            let outputField = app.textViews["outputTextView"]
            _ = outputField.waitForExistence(timeout: 10)
        }
    }
}
```

---

## 测试执行指南

### 手动测试执行

1. **环境准备**:
   ```bash
   # 启动 Backend
   cd /Users/jamesg/projects/MacCortex/Backend
   .venv/bin/python src/main.py

   # 启动 MacCortex.app
   open .build/arm64-apple-macosx/debug/MacCortex.app
   ```

2. **测试执行**:
   - 按照上述测试清单逐项执行
   - 记录每个测试的结果（通过/失败）
   - 截图记录关键步骤

3. **结果记录**:
   - 在本文档中更新每个测试的状态
   - 记录任何 Bug 或异常
   - 创建 Bug 报告（如需要）

### 自动化测试执行（Phase 3）

1. **迁移到 Xcode 项目**（Phase 3 前置条件）
2. **创建 UI Test Target**:
   ```bash
   # 在 Xcode 中
   File → New → Target → macOS UI Testing Bundle
   ```

3. **添加测试代码**:
   - 复制上述 XCTest 脚本
   - 调整元素标识符（Accessibility Identifier）

4. **运行测试**:
   ```bash
   # 命令行
   xcodebuild test -scheme MacCortex -destination 'platform=macOS'

   # 或在 Xcode 中
   Product → Test (⌘U)
   ```

---

## 性能基准测试

### 测试脚本

**文件**: `/tmp/performance_benchmark.sh`

```bash
#!/bin/bash

echo "=== MacCortex 性能基准测试 ==="
echo ""

# 1. 启动时间测试
echo "1. 启动时间测试"
start_time=$(date +%s.%N)
open -a MacCortex
sleep 3  # 等待完全启动
end_time=$(date +%s.%N)
startup_duration=$(echo "$end_time - $start_time" | bc)
echo "   启动时间: ${startup_duration}s"
echo ""

# 2. Pattern 响应时间测试（10 次平均）
echo "2. Pattern 响应时间测试（Summarize, 10 次）"
total_duration=0
for i in {1..10}; do
    response=$(curl -s -w "\n%{time_total}" -X POST http://localhost:8000/execute \
        -H "Content-Type: application/json" \
        -d '{"pattern_id":"summarize","text":"Test performance","parameters":{"length":"short"}}')
    duration=$(echo "$response" | tail -1)
    total_duration=$(echo "$total_duration + $duration" | bc)
done
avg_duration=$(echo "scale=3; $total_duration / 10" | bc)
echo "   平均响应时间: ${avg_duration}s"
echo ""

# 3. 内存占用测试
echo "3. 内存占用测试"
app_pid=$(ps aux | grep "MacCortex.app" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$app_pid" ]; then
    memory=$(ps -o rss= -p "$app_pid")
    memory_mb=$(echo "scale=2; $memory / 1024" | bc)
    echo "   内存占用: ${memory_mb} MB"
else
    echo "   ⚠️  应用未运行"
fi
echo ""

# 4. CPU 占用测试
echo "4. CPU 占用测试（空闲 5 秒）"
if [ -n "$app_pid" ]; then
    cpu_usage=$(ps -p "$app_pid" -o %cpu= | awk '{print $1}')
    echo "   CPU 占用: ${cpu_usage}%"
else
    echo "   ⚠️  应用未运行"
fi
echo ""

echo "=== 基准测试完成 ==="
```

### 预期性能指标

| 指标 | 目标值 | Phase 2 Week 3 实测 | 验收标准 |
|------|--------|---------------------|----------|
| 启动时间 | < 3s | 2.0s ✅ | < 3s |
| Pattern 响应（p50） | < 2s | 1.8s ✅ | < 2s |
| Pattern 响应（p95） | < 5s | 2.5s ✅ | < 5s |
| 内存占用（空闲） | < 200 MB | 115 MB ✅ | < 200 MB |
| CPU 占用（空闲） | < 5% | 0% ✅ | < 5% |

---

## 测试报告模板

### 测试执行摘要

**执行日期**: 2026-01-21
**执行人**: [测试人员姓名]
**环境**: macOS Tahoe 26.2, Apple Silicon

**测试结果**:
- 总测试用例: 25
- 通过: [X]
- 失败: [X]
- 阻塞: [X]
- 跳过: [X]

**通过率**: [X]%

### 发现的问题

#### 问题 1: [问题标题]
- **严重性**: Critical / High / Medium / Low
- **复现步骤**: [详细步骤]
- **预期结果**: [预期行为]
- **实际结果**: [实际行为]
- **截图/日志**: [附件]
- **状态**: Open / In Progress / Fixed

---

## 下一步行动

### Day 18 执行计划

1. **手动测试执行**（2-3 小时）
   - 执行所有 25 个测试用例
   - 记录结果和截图
   - 发现并记录 Bug

2. **XCTest 脚本完善**（1-2 小时）
   - 完成基础测试脚本
   - 添加断言和验证
   - 准备 Phase 3 使用

3. **性能基准测试**（1 小时）
   - 运行基准测试脚本
   - 对比 Phase 2 Week 3 数据
   - 验证无回归

4. **测试报告生成**（1 小时）
   - 汇总测试结果
   - 生成详细报告
   - 提交到 Git

### Day 19-20 预览

- **Day 19**: 用户文档完善（USER_GUIDE, FAQ, API_REFERENCE）
- **Day 20**: Phase 2 总结与 Demo 准备

---

**文档状态**: ✅ 完成
**测试状态**: ⏳ 待执行
**自动化脚本**: ✅ 框架完成
**所有者**: MacCortex 测试团队
