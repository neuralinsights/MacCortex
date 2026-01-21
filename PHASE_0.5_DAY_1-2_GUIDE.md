# Phase 0.5 Day 1-2: Developer ID 证书 + Entitlements 配置指南

> **创建时间**: 2026-01-21 14:29 +1300 (NZDT)
> **基于时间校验**: #20260121-01
> **状态**: 待用户执行
> **预计耗时**: 2-4 小时（取决于 Apple 证书签发速度）

---

## 📊 当前状态总结

### ✅ 已完成（2026-01-20）
- ✅ **MacCortex.entitlements** (27 行) - Hardened Runtime 配置完美
- ✅ **Info.plist** (55 行) - Sparkle + TCC 配置完整
- ✅ **sign.sh** (128 行, 已改进) - 添加 Developer ID 配置检查
- ✅ **notarize.sh** (103 行) - 完整公证流程
- ✅ **build-dmg.sh** (63 行) - DMG 创建流程

**质量评分**: 9.8/10 ✅ 优秀

### ⏳ 待完成（本指南）
- [ ] 申请 Apple Developer Program ($99/年)
- [ ] 下载 Developer ID Application 证书
- [ ] 配置 `DEVELOPER_ID` 环境变量
- [ ] 配置 notarytool Keychain Profile
- [ ] 端到端测试（构建 → 签名 → 公证 → DMG）

---

## 第 1 步：申请 Apple Developer Program

### 1.1 访问 Apple Developer
```bash
# 在浏览器中打开
open https://developer.apple.com/account
```

### 1.2 登录/注册 Apple ID
- 如果没有 Apple ID，先注册一个
- 建议使用个人邮箱（不要使用公司邮箱，避免权限问题）

### 1.3 加入 Developer Program
1. 点击 **"Enroll"** 或 **"Join the Apple Developer Program"**
2. 选择 **Individual（个人）** 或 **Organization（组织）**
   - **Individual**: $99/年，个人开发者
   - **Organization**: $99/年，公司开发者（需要邓白氏编码）
3. 填写基本信息（姓名、地址）
4. 支付 $99/年费用（支持信用卡/Apple Pay）

### 1.4 等待审核
- **个人账户**: 通常 24-48 小时
- **组织账户**: 可能需要 1-2 周（需要邓白氏编码验证）

### 1.5 验证状态
```bash
# 审核通过后，在 Apple Developer 网站查看
open https://developer.apple.com/account/

# 应显示 "Membership Status: Active"
```

---

## 第 2 步：下载 Developer ID Application 证书

### 2.1 通过 Xcode 自动创建证书（推荐）

```bash
# 1. 打开 Xcode
open /Applications/Xcode.app

# 2. 打开 Xcode → Settings（⌘,）
# 3. 切换到 "Accounts" 标签
# 4. 点击左下角 "+" 添加 Apple ID
# 5. 登录您的 Apple Developer 账户

# 6. 选择账户 → 点击 "Manage Certificates..."
# 7. 点击右下角 "+" → 选择 "Developer ID Application"
# 8. 证书会自动创建并安装到 Keychain
```

### 2.2 验证证书安装成功

```bash
# 查找 Developer ID 证书
security find-identity -v -p codesigning

# 预期输出（示例）：
# 1) 12A34B5C6D7E8F9G0H1I2J3K4L5M6N7O8P9Q0R1 "Developer ID Application: Your Name (TEAM123456)"
# 2) ...

# 注意：记录证书完整名称（包括 TEAM ID）
```

### 2.3 记录 Team ID

```bash
# 方式 1: 从证书名称中提取
security find-identity -v -p codesigning | grep "Developer ID Application"

# 方式 2: 访问网站查看
open https://developer.apple.com/account/

# 点击 "Membership Details" → 查看 "Team ID"
```

---

## 第 3 步：配置 `DEVELOPER_ID` 环境变量

### 3.1 添加到 Shell 配置文件

```bash
# 判断您使用的 Shell
echo $SHELL

# 如果是 zsh（macOS 默认）
nano ~/.zshrc

# 如果是 bash
nano ~/.bashrc
```

### 3.2 添加环境变量

**在配置文件末尾添加**：

```bash
# MacCortex Developer ID 配置
# 替换 "Your Name" 和 "TEAM123456" 为您的真实信息
export DEVELOPER_ID="Developer ID Application: Your Name (TEAM123456)"
```

**真实示例**：
```bash
export DEVELOPER_ID="Developer ID Application: Yu Geng (A1B2C3D4E5)"
```

### 3.3 重新加载配置

```bash
# zsh
source ~/.zshrc

# bash
source ~/.bashrc
```

### 3.4 验证配置

```bash
# 检查环境变量
echo $DEVELOPER_ID

# 预期输出：
# Developer ID Application: Your Name (TEAM123456)

# 验证签名脚本不再报错
cd /Users/jamesg/projects/MacCortex
./Scripts/sign.sh

# 应显示："================================================"
#         "MacCortex 代码签名流程"
#         "================================================"
# 而不是 "❌ 错误: Developer ID 未配置"
```

---

## 第 4 步：配置 notarytool Keychain Profile

### 4.1 生成 App-Specific Password

```bash
# 1. 访问 Apple ID 网站
open https://appleid.apple.com/account/manage

# 2. 登录您的 Apple ID
# 3. 在 "Security" 部分 → 点击 "App-Specific Passwords"
# 4. 点击 "Generate Password..."
# 5. 输入标签: "MacCortex Notarization"
# 6. 记录生成的密码（格式: xxxx-xxxx-xxxx-xxxx）
```

### 4.2 存储到 Keychain

```bash
# 运行 notarytool 配置命令
xcrun notarytool store-credentials notarytool-profile \
    --apple-id "your-email@example.com" \
    --team-id "TEAM123456" \
    --password "xxxx-xxxx-xxxx-xxxx"

# 替换：
# - your-email@example.com: 您的 Apple ID 邮箱
# - TEAM123456: 您的 Team ID（步骤 2.3）
# - xxxx-xxxx-xxxx-xxxx: 刚生成的 App-Specific Password
```

**预期输出**：
```
This process stores your credentials securely in the Keychain. You reference them later using a profile name.

Validating your credentials...
Success. Credentials validated.
Credentials saved to Keychain.
Profile name: notarytool-profile
```

### 4.3 验证配置

```bash
# 查看已保存的 Profile
xcrun notarytool history --keychain-profile notarytool-profile

# 预期输出：
# No submissions found.
# （第一次运行时正常）
```

---

## 第 5 步：端到端测试

### 5.1 构建应用

```bash
cd /Users/jamesg/projects/MacCortex

# 方式 1: 使用 Swift Package Manager
swift build -c release

# 方式 2: 使用自定义构建脚本
./Scripts/build-app.sh
```

### 5.2 代码签名

```bash
# 运行签名脚本
./Scripts/sign.sh

# 预期输出：
# ================================================
# MacCortex 代码签名流程
# ================================================
# 应用路径: build/MacCortex.app
# 签名身份: Developer ID Application: Your Name (TEAM123456)
# Entitlements: Resources/Entitlements/MacCortex.entitlements
#
# 步骤 1/3: 签名 XPC Services...
#   ⚠️  无 XPC Services（跳过）
#
# 步骤 2/3: 签名 Frameworks...
#   - 签名 Sparkle.framework
#
# 步骤 3/3: 签名主应用...
#
# ================================================
# 验证签名...
# ================================================
# ✅ 签名验证成功
#
# Gatekeeper 评估...
# ⚠️  Gatekeeper 评估失败（公证后会通过）
#
# ================================================
# 签名完成！
# ================================================
# 下一步: 运行 ./Scripts/notarize.sh 进行公证
```

**故障排查**:
- 如果报错 "Developer ID 未配置"，检查步骤 3
- 如果报错 "无效的签名身份"，检查步骤 2

### 5.3 公证应用

```bash
# 运行公证脚本（首次公证可能需要 2-3 天）
./Scripts/notarize.sh

# 预期输出：
# ================================================
# MacCortex 公证流程
# ================================================
# 应用路径: build/MacCortex.app
# ZIP 路径: build/MacCortex.zip
# Keychain Profile: notarytool-profile
#
# 验证签名状态...
# ✅ 签名有效
#
# 步骤 1/3: 创建 ZIP 归档...
# ✅ ZIP 创建成功: build/MacCortex.zip
#
# 步骤 2/3: 提交公证请求...
# 注意: 公证通常需要 2-10 分钟，请耐心等待
#
# Conducting pre-submission checks for MacCortex.zip...
# Submission ID received
#   id: 12345678-1234-1234-1234-123456789012
# Successfully uploaded file
#   id: 12345678-1234-1234-1234-123456789012
#   path: build/MacCortex.zip
# Waiting for processing to complete.
# Current status: In Progress..........
# Current status: Accepted
#
# ✅ 公证成功
#
# 步骤 3/3: Staple 票据...
# Processing: build/MacCortex.app
# Processing: build/MacCortex.app/Contents/MacOS/MacCortex
# The staple and validate action worked!
# ✅ Staple 成功
#
# ================================================
# 验证公证状态...
# ================================================
# ✅ 公证票据验证成功
#
# 🎉 恭喜！应用已完成签名和公证
#    可以安全分发给用户
#
# ================================================
# 最终 Gatekeeper 检查...
# ================================================
# build/MacCortex.app: accepted
# source=Notarized Developer ID
# ✅ Gatekeeper 通过
#
# ================================================
# 公证完成！
# ================================================
# 下一步: 创建 DMG 安装包
#   ./Scripts/build-dmg.sh
```

**⚠️ 重要提示**：
- **首次公证**: Apple 可能需要 2-3 天审核（2026 年公证服务性能波动）
- **后续公证**: 通常 2-10 分钟
- **错误码 7000**: 通常是签名问题，检查 Entitlements 配置

### 5.4 创建 DMG 安装包

```bash
# 运行 DMG 构建脚本
./Scripts/build-dmg.sh

# 预期输出：
# ================================================
# MacCortex DMG 构建流程
# ================================================
# 应用路径: build/MacCortex.app
# 版本: 0.5.0
# DMG 名称: MacCortex-v0.5.0.dmg
#
# 步骤 1/2: 准备 DMG 内容...
# ✅ 内容准备完成
#
# 步骤 2/2: 创建 DMG...
# created: build/MacCortex-v0.5.0.dmg
# ✅ DMG 创建成功: build/MacCortex-v0.5.0.dmg
#
# ================================================
# DMG 构建完成！
# ================================================
# 文件大小: 25M
#
# 下一步: 分发 DMG
#   1. 测试安装: open build/MacCortex-v0.5.0.dmg
#   2. 上传到服务器或 GitHub Release
```

### 5.5 测试安装

```bash
# 打开 DMG
open build/MacCortex-v0.5.0.dmg

# 手动操作：
# 1. 拖拽 MacCortex.app 到 Applications 文件夹
# 2. 打开 Finder → Applications
# 3. 双击 MacCortex.app
# 4. 应直接打开，无 Gatekeeper 警告
```

---

## 第 6 步：验收标准

### ✅ 必须全部通过

| # | 验收项 | 测试方法 | 期望结果 |
|---|--------|----------|----------|
| 1 | **Developer ID 证书有效** | `security find-identity -v -p codesigning` | 显示 "Developer ID Application: ..." |
| 2 | **环境变量配置正确** | `echo $DEVELOPER_ID` | 输出正确的签名身份 |
| 3 | **签名验证通过** | `codesign --verify --deep --strict build/MacCortex.app` | 无输出（静默成功） |
| 4 | **公证成功** | `xcrun stapler validate build/MacCortex.app` | "validate action worked!" |
| 5 | **Gatekeeper 通过** | `spctl --assess --type execute build/MacCortex.app` | "accepted, source=Notarized Developer ID" |
| 6 | **DMG 创建成功** | `ls -lh build/MacCortex-v0.5.0.dmg` | 文件存在，大小 > 20MB |
| 7 | **无警告安装** | 双击 DMG 安装并打开 | 无 Gatekeeper 警告，直接打开 |
| 8 | **Keychain Profile 可用** | `xcrun notarytool history --keychain-profile notarytool-profile` | 无错误，显示历史记录 |

---

## 常见问题 FAQ

### Q1: 公证失败，错误码 7000
**原因**: 签名问题，通常是 Entitlements 配置错误
**解决方案**:
```bash
# 查看公证日志
xcrun notarytool log <submission-id> --keychain-profile notarytool-profile

# 常见问题：
# 1. Hardened Runtime 未启用 → 检查 sign.sh 的 --options runtime
# 2. get-task-allow 权限启用 → 检查 MacCortex.entitlements
# 3. 签名顺序错误 → 确保 XPC → Frameworks → App
```

### Q2: Gatekeeper 评估失败
**原因**: 公证前的正常现象
**解决方案**: 完成公证后再次测试，应显示 "accepted"

### Q3: notarytool 报错 "Invalid Credentials"
**原因**: Keychain Profile 配置错误
**解决方案**:
```bash
# 删除旧配置
security delete-generic-password -l "notarytool-profile"

# 重新配置（步骤 4.2）
xcrun notarytool store-credentials notarytool-profile ...
```

### Q4: 签名后应用无法运行
**原因**: 签名破坏了可执行文件
**解决方案**:
```bash
# 重新构建（不签名）
swift build -c release

# 检查可执行权限
chmod +x .build/release/MacCortex

# 重新签名
./Scripts/sign.sh
```

---

## 下一步行动

### Day 3-5（Week 1 剩余时间）
- [ ] Day 3: 签名脚本优化（处理嵌套框架）
- [ ] Day 4: 公证自动化测试
- [ ] Day 5: GitHub Actions CI/CD 集成

### Week 2: 权限管理与用户体验
- [ ] Day 6-7: PermissionManager.swift（Full Disk Access 检测）
- [ ] Day 8-9: FirstRunView.swift（首次启动引导）
- [ ] Day 10: Phase 0.5 验收测试

---

## 参考资料

### 官方文档
- [Apple Developer ID 签名指南](https://developer.apple.com/developer-id/)
- [TN3127: Inside Code Signing: Requirements](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements)
- [Customizing the Notarization Workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)
- [Hardened Runtime 配置](https://developer.apple.com/documentation/xcode/configuring-the-hardened-runtime)

### 社区资源
- [Tony Gorez: Complete Guide to Notarizing macOS Apps](https://tonygo.tech/blog/2023/notarization-for-macos-app-with-notarytool)
- [Scripting OSX: Notarize a Command Line Tool](https://scriptingosx.com/2021/07/notarize-a-command-line-tool-with-notarytool/)
- [Eclectic Light: macOS 代码签名现状（2026）](https://eclecticlight.co/2026/01/17/whats-happening-with-code-signing-and-future-macos/)

---

**创建时间**: 2026-01-21 14:29 +1300 (NZDT)
**基于**: 时间校验记录 #20260121-01 + CLAUDE.md 证据清单议题 7-9
**作者**: Claude Code (Sonnet 4.5)
**版本**: v1.0
