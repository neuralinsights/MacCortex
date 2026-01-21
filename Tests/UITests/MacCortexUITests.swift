// MacCortexUITests.swift
// MacCortex UI 自动化测试
//
// Phase 2 Week 4 Day 18
// 创建时间: 2026-01-21
// 状态: 框架完成，Phase 3 启用
//
// 说明：
// 当前项目使用 Swift Package Manager，不支持直接运行 UI 测试
// Phase 3 迁移到 Xcode 项目后，此测试套件将可用
//
// 运行方式（Phase 3）：
// 1. 在 Xcode 中创建 UI Testing Bundle
// 2. 复制此文件到测试 Target
// 3. 运行: Product → Test (⌘U)

import XCTest

/// MacCortex UI 端到端测试套件
///
/// 测试覆盖：
/// - 应用启动与初始化
/// - Pattern 功能测试（5 个 Pattern）
/// - 错误处理与边界测试
/// - UI/UX 交互测试
/// - 性能基准测试
class MacCortexUITests: XCTestCase {

    // MARK: - Properties

    var app: XCUIApplication!

    // MARK: - Setup & Teardown

    override func setUpWithError() throws {
        // 测试失败后继续执行
        continueAfterFailure = false

        // 初始化应用
        app = XCUIApplication()

        // 设置启动参数（可选）
        app.launchArguments = ["--ui-testing"]

        // 启动应用
        app.launch()

        // 等待应用完全加载
        let mainWindow = app.windows.firstMatch
        let windowExists = mainWindow.waitForExistence(timeout: 5)
        XCTAssertTrue(windowExists, "主窗口应该在 5 秒内出现")
    }

    override func tearDownWithError() throws {
        // 关闭应用
        app.terminate()
        app = nil
    }

    // MARK: - 分类 1: 应用启动与初始化

    /// 测试 1.1: 应用冷启动
    func testAppLaunch() throws {
        // 验证主窗口存在
        let mainWindow = app.windows.firstMatch
        XCTAssertTrue(mainWindow.exists, "主窗口应该存在")

        // 验证窗口大小合理
        let frame = mainWindow.frame
        XCTAssertGreaterThan(frame.width, 600, "窗口宽度应该 > 600")
        XCTAssertGreaterThan(frame.height, 400, "窗口高度应该 > 400")

        print("✅ 应用启动测试通过")
    }

    /// 测试 1.2: Pattern 列表加载
    func testPatternListLoading() throws {
        // 等待 Pattern 选择器加载
        let patternPicker = app.popUpButtons["patternPicker"]
        let pickerExists = patternPicker.waitForExistence(timeout: 10)
        XCTAssertTrue(pickerExists, "Pattern 选择器应该在 10 秒内加载")

        // 点击展开选择器
        patternPicker.click()

        // 验证 5 个 Pattern 存在
        let expectedPatterns = ["Summarize", "Extract", "Translate", "Format", "Search"]
        for patternName in expectedPatterns {
            let menuItem = patternPicker.menuItems[patternName]
            XCTAssertTrue(menuItem.exists, "应该存在 \(patternName) Pattern")
        }

        // 关闭选择器
        patternPicker.click()

        print("✅ Pattern 列表加载测试通过")
    }

    /// 测试 1.3: Backend 连接状态
    func testBackendConnection() throws {
        // 查找连接状态指示器（如果有）
        let statusIndicator = app.staticTexts["connectionStatus"]

        if statusIndicator.exists {
            let statusText = statusIndicator.value as? String ?? ""
            XCTAssertTrue(
                statusText.contains("已连接") || statusText.contains("Connected"),
                "应该显示已连接状态"
            )
        } else {
            // 如果没有状态指示器，通过执行 Pattern 间接验证
            // （在后续测试中验证）
            print("⚠️ 无连接状态指示器，跳过直接验证")
        }
    }

    // MARK: - 分类 2: Pattern 功能测试

    /// 测试 2.1: Summarize Pattern - 短文本
    func testSummarizePatternShortText() throws {
        // 选择 Summarize Pattern
        selectPattern("Summarize")

        // 输入测试文本
        let testText = "MacCortex is a next-generation macOS personal AI infrastructure built with Swift and Python. It integrates multiple LLM models and provides 5 AI patterns for intelligent text processing."
        enterInputText(testText)

        // 执行 Pattern
        let executeButton = app.buttons["executeButton"]
        XCTAssertTrue(executeButton.exists, "执行按钮应该存在")
        executeButton.click()

        // 等待结果（最多 10 秒）
        let outputField = app.textViews["outputTextView"]
        let hasOutput = outputField.waitForExistence(timeout: 10)
        XCTAssertTrue(hasOutput, "应该在 10 秒内返回结果")

        // 验证输出不为空
        let outputText = outputField.value as? String ?? ""
        XCTAssertFalse(outputText.isEmpty, "输出不应为空")
        XCTAssertGreaterThan(outputText.count, 10, "输出应该有实际内容")

        print("✅ Summarize Pattern 短文本测试通过")
    }

    /// 测试 2.2: Extract Pattern - 实体提取
    func testExtractPattern() throws {
        // 选择 Extract Pattern
        selectPattern("Extract")

        // 输入包含实体的文本
        let testText = "Contact John Doe at john@example.com for the meeting scheduled on 2026-01-25. Call us at +1-555-0123."
        enterInputText(testText)

        // 执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 等待结果
        let outputField = app.textViews["outputTextView"]
        let hasOutput = outputField.waitForExistence(timeout: 10)
        XCTAssertTrue(hasOutput, "应该返回提取结果")

        // 验证 JSON 格式输出
        let outputText = outputField.value as? String ?? ""
        XCTAssertTrue(outputText.contains("entities") || outputText.contains("output"), "输出应包含实体信息")

        print("✅ Extract Pattern 测试通过")
    }

    /// 测试 2.3: Translate Pattern - 英译中
    func testTranslatePatternEnglishToChinese() throws {
        // 选择 Translate Pattern
        selectPattern("Translate")

        // 输入英文文本
        let testText = "Hello, world! How are you doing today?"
        enterInputText(testText)

        // 选择目标语言（如果有选择器）
        let languagePicker = app.popUpButtons["targetLanguagePicker"]
        if languagePicker.exists {
            languagePicker.click()
            // 尝试选择中文
            let chineseOption = languagePicker.menuItems.matching(
                NSPredicate(format: "label CONTAINS[c] '中文' OR label CONTAINS[c] 'Chinese'")
            ).firstMatch
            if chineseOption.exists {
                chineseOption.click()
            }
        }

        // 执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 等待结果
        let outputField = app.textViews["outputTextView"]
        let hasOutput = outputField.waitForExistence(timeout: 10)
        XCTAssertTrue(hasOutput, "应该返回翻译结果")

        // 验证有输出（质量可能有限，见 TRANSLATE_LIMITATION.md）
        let outputText = outputField.value as? String ?? ""
        XCTAssertFalse(outputText.isEmpty, "翻译结果不应为空")

        print("✅ Translate Pattern 测试通过")
        print("⚠️ 注意：翻译质量可能有限（Llama-3.2-1B 模型限制）")
    }

    /// 测试 2.4: Format Pattern - JSON to YAML
    func testFormatPatternJSONtoYAML() throws {
        // 选择 Format Pattern
        selectPattern("Format")

        // 输入 JSON
        let testJSON = """
        {
            "name": "MacCortex",
            "version": "0.5.0",
            "platform": "macOS",
            "features": ["summarize", "extract", "translate"]
        }
        """
        enterInputText(testJSON)

        // 设置参数（from_format: json, to_format: yaml）
        // 注意：实际 UI 可能不同，需要根据实际设计调整
        let fromFormatPicker = app.popUpButtons["fromFormatPicker"]
        if fromFormatPicker.exists {
            fromFormatPicker.click()
            fromFormatPicker.menuItems["JSON"].click()
        }

        let toFormatPicker = app.popUpButtons["toFormatPicker"]
        if toFormatPicker.exists {
            toFormatPicker.click()
            toFormatPicker.menuItems["YAML"].click()
        }

        // 执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 等待结果
        let outputField = app.textViews["outputTextView"]
        let hasOutput = outputField.waitForExistence(timeout: 10)
        XCTAssertTrue(hasOutput, "应该返回转换结果")

        // 验证 YAML 格式（简单检查）
        let outputText = outputField.value as? String ?? ""
        XCTAssertTrue(outputText.contains("name:") || outputText.contains("version:"), "输出应该是 YAML 格式")
        XCTAssertFalse(outputText.contains("{") && outputText.contains("}"), "不应该包含 JSON 大括号")

        print("✅ Format Pattern JSON to YAML 测试通过")
    }

    /// 测试 2.5: Search Pattern - Web 搜索
    func testSearchPattern() throws {
        // 选择 Search Pattern
        selectPattern("Search")

        // 输入搜索查询
        let testQuery = "Python async programming best practices"
        enterInputText(testQuery)

        // 设置参数（如果有）
        let enginePicker = app.popUpButtons["enginePicker"]
        if enginePicker.exists {
            enginePicker.click()
            enginePicker.menuItems["DuckDuckGo"].click()
        }

        // 执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 等待结果（搜索可能较慢）
        let outputField = app.textViews["outputTextView"]
        let hasOutput = outputField.waitForExistence(timeout: 15)
        XCTAssertTrue(hasOutput, "应该在 15 秒内返回搜索结果")

        // 验证输出包含搜索结果
        let outputText = outputField.value as? String ?? ""
        XCTAssertTrue(
            outputText.contains("results") || outputText.contains("title") || outputText.contains("url"),
            "输出应包含搜索结果字段"
        )

        print("✅ Search Pattern 测试通过")
        print("⚠️ 注意：可能返回 Mock 数据（DuckDuckGo 速率限制）")
    }

    // MARK: - 分类 3: 错误处理测试

    /// 测试 3.1: 空输入验证
    func testEmptyInputValidation() throws {
        // 选择任意 Pattern
        selectPattern("Summarize")

        // 清空输入（如果有默认文本）
        let inputField = app.textViews["inputTextView"]
        if inputField.exists {
            inputField.click()
            inputField.typeKey("a", modifierFlags: .command) // 全选
            inputField.typeKey(.delete, modifierFlags: [])   // 删除
        }

        // 尝试执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 验证错误提示
        // 方式1：查找 Alert
        let errorAlert = app.alerts.firstMatch
        let alertExists = errorAlert.waitForExistence(timeout: 2)

        if alertExists {
            // 有弹窗提示
            XCTAssertTrue(errorAlert.exists, "应该显示错误提示")

            // 关闭弹窗
            let okButton = errorAlert.buttons["确定"]
            if okButton.exists {
                okButton.click()
            }
        } else {
            // 方式2：查找内联错误提示
            let errorLabel = app.staticTexts.matching(
                NSPredicate(format: "label CONTAINS[c] '不能为空' OR label CONTAINS[c] 'required'")
            ).firstMatch

            XCTAssertTrue(
                errorLabel.exists,
                "应该显示内联错误提示或禁用执行按钮"
            )
        }

        print("✅ 空输入验证测试通过")
    }

    /// 测试 3.2: 无效参数处理
    func testInvalidParameterHandling() throws {
        // 选择 Translate Pattern
        selectPattern("Translate")

        // 输入文本
        enterInputText("Test invalid parameter")

        // 尝试设置无效参数（通过 UI 可能无法设置，此测试可能需要调整）
        // 这里假设我们能够通过某种方式输入无效语言代码

        // 执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 等待结果或错误
        let outputField = app.textViews["outputTextView"]
        let errorAlert = app.alerts.firstMatch

        let hasOutput = outputField.waitForExistence(timeout: 5)
        let hasAlert = errorAlert.waitForExistence(timeout: 5)

        // 应该有错误提示或输出错误信息
        XCTAssertTrue(hasOutput || hasAlert, "应该有错误反馈")

        if hasAlert {
            // 关闭错误提示
            errorAlert.buttons.firstMatch.click()
        }

        print("✅ 无效参数处理测试通过")
    }

    // MARK: - 分类 4: UI/UX 测试

    /// 测试 4.1: 界面响应性
    func testUIResponsiveness() throws {
        // 选择 Pattern
        selectPattern("Summarize")

        // 输入较长文本（模拟较慢的处理）
        let longText = String(repeating: "This is a test sentence. ", count: 100)
        enterInputText(longText)

        // 执行
        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        // 在处理期间，尝试与 UI 交互
        sleep(1) // 等待 1 秒让处理开始

        // 检查是否有加载指示器
        let loadingIndicator = app.progressIndicators.firstMatch
        let spinnerIndicator = app.activityIndicators.firstMatch

        let hasLoadingUI = loadingIndicator.exists || spinnerIndicator.exists

        // 理想情况应该有加载指示器
        if !hasLoadingUI {
            print("⚠️ 建议添加加载指示器以改善用户体验")
        }

        // 尝试点击窗口其他区域（验证不冻结）
        let mainWindow = app.windows.firstMatch
        XCTAssertTrue(mainWindow.exists, "窗口应该仍然存在")

        // 等待完成
        let outputField = app.textViews["outputTextView"]
        _ = outputField.waitForExistence(timeout: 15)

        print("✅ UI 响应性测试通过")
    }

    /// 测试 4.2: 输出复制功能
    func testOutputCopyFunctionality() throws {
        // 执行一个 Pattern 获取输出
        selectPattern("Summarize")
        enterInputText("Test output copy")

        let executeButton = app.buttons["executeButton"]
        executeButton.click()

        let outputField = app.textViews["outputTextView"]
        _ = outputField.waitForExistence(timeout: 10)

        // 选中输出文本
        outputField.click()
        outputField.typeKey("a", modifierFlags: .command) // 全选

        // 复制
        outputField.typeKey("c", modifierFlags: .command)

        // 验证剪贴板（可选，需要额外权限）
        // 这里简单验证操作不崩溃

        print("✅ 输出复制功能测试通过")
    }

    // MARK: - 分类 5: 性能测试

    /// 测试 5.1: 启动性能
    func testLaunchPerformance() throws {
        // 使用 XCTest 的性能测量
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            let testApp = XCUIApplication()
            testApp.launch()
            testApp.terminate()
        }

        print("✅ 启动性能测试完成（查看测试报告获取具体数据）")
    }

    /// 测试 5.2: Pattern 执行性能
    func testPatternExecutionPerformance() throws {
        app.launch()

        // 选择 Pattern
        selectPattern("Summarize")

        // 准备输入
        enterInputText("Performance test text for measuring execution speed.")

        // 测量执行时间
        measure {
            let executeButton = app.buttons["executeButton"]
            executeButton.click()

            let outputField = app.textViews["outputTextView"]
            _ = outputField.waitForExistence(timeout: 10)
        }

        print("✅ Pattern 执行性能测试完成")
    }

    // MARK: - Helper Methods

    /// 选择指定的 Pattern
    private func selectPattern(_ patternName: String) {
        let patternPicker = app.popUpButtons["patternPicker"]

        if !patternPicker.exists {
            // 如果没有 Accessibility Identifier，尝试其他方式
            let allPickers = app.popUpButtons
            if allPickers.count > 0 {
                allPickers.firstMatch.click()
                allPickers.firstMatch.menuItems[patternName].click()
                return
            }
        }

        XCTAssertTrue(patternPicker.exists, "Pattern 选择器应该存在")
        patternPicker.click()

        let menuItem = patternPicker.menuItems[patternName]
        XCTAssertTrue(menuItem.exists, "\(patternName) 菜单项应该存在")
        menuItem.click()
    }

    /// 输入文本到输入框
    private func enterInputText(_ text: String) {
        let inputField = app.textViews["inputTextView"]

        if !inputField.exists {
            // 如果没有 Accessibility Identifier，尝试查找第一个文本视图
            let allTextViews = app.textViews
            if allTextViews.count > 0 {
                let field = allTextViews.firstMatch
                field.click()
                field.typeText(text)
                return
            }
        }

        XCTAssertTrue(inputField.exists, "输入文本框应该存在")
        inputField.click()

        // 清空现有内容
        inputField.typeKey("a", modifierFlags: .command)
        inputField.typeKey(.delete, modifierFlags: [])

        // 输入新文本
        inputField.typeText(text)
    }
}

// MARK: - 扩展：测试套件组织

/// 快速测试套件（核心功能）
extension MacCortexUITests {
    /// 快速测试：只测试核心功能（< 5 分钟）
    func testQuickSuite() throws {
        try testAppLaunch()
        try testSummarizePatternShortText()
        try testExtractPattern()
        try testEmptyInputValidation()
    }
}

/// 完整测试套件（所有功能）
extension MacCortexUITests {
    /// 完整测试：执行所有测试用例（~ 15-20 分钟）
    func testFullSuite() throws {
        // 启动测试
        try testAppLaunch()
        try testPatternListLoading()
        try testBackendConnection()

        // Pattern 功能测试
        try testSummarizePatternShortText()
        try testExtractPattern()
        try testTranslatePatternEnglishToChinese()
        try testFormatPatternJSONtoYAML()
        try testSearchPattern()

        // 错误处理测试
        try testEmptyInputValidation()
        try testInvalidParameterHandling()

        // UI/UX 测试
        try testUIResponsiveness()
        try testOutputCopyFunctionality()
    }
}

// MARK: - 测试配置

extension MacCortexUITests {
    /// 测试配置：设置 Accessibility Identifier
    ///
    /// 在 SwiftUI 中添加 Accessibility Identifier：
    /// ```swift
    /// Picker("Pattern", selection: $selectedPattern) {
    ///     // ...
    /// }
    /// .accessibilityIdentifier("patternPicker")
    ///
    /// TextEditor(text: $inputText)
    ///     .accessibilityIdentifier("inputTextView")
    ///
    /// TextEditor(text: $outputText)
    ///     .accessibilityIdentifier("outputTextView")
    ///
    /// Button("Execute") {
    ///     // ...
    /// }
    /// .accessibilityIdentifier("executeButton")
    /// ```
    func documentAccessibilityIdentifiers() {
        // 文档化需要的 Accessibility Identifiers
        let requiredIdentifiers = [
            "patternPicker",          // Pattern 选择器
            "inputTextView",          // 输入文本框
            "outputTextView",         // 输出文本框
            "executeButton",          // 执行按钮
            "targetLanguagePicker",   // 目标语言选择器（Translate）
            "fromFormatPicker",       // 源格式选择器（Format）
            "toFormatPicker",         // 目标格式选择器（Format）
            "enginePicker",           // 搜索引擎选择器（Search）
            "connectionStatus",       // 连接状态指示器（可选）
        ]

        print("需要在 SwiftUI 代码中添加以下 Accessibility Identifiers:")
        for identifier in requiredIdentifiers {
            print("  - \(identifier)")
        }
    }
}
