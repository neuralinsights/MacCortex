# MacCortex Phase 0.5 配置清单

**创建时间**: 2026-01-20
**用户**: Apple Developer Program 会员
**状态**: 需要完成 3 个配置步骤

---

## ✅ 已完成

- ✅ Apple Developer Program 会员资格
- ✅ Xcode 已安装（/Applications/Xcode.app）
- ✅ MacCortex 项目代码（Git 仓库已初始化）

---

## 📋 待完成配置（3 步，约 10 分钟）

### 步骤 1: 切换到完整版 Xcode（1 分钟）

**目的**: 确保使用完整版 Xcode 而不是 Command Line Tools

**命令**:
```bash
# 切换到 Xcode
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer

# 验证
xcode-select -p
# 应该输出: /Applications/Xcode.app/Contents/Developer

# 检查版本
xcodebuild -version
# 应该输出: Xcode 15.x
```

**检查点**: ✅ `xcodebuild -version` 能正常显示版本号

---

### 步骤 2: 申请 Developer ID 证书（5 分钟）

**目的**: 获取代码签名证书

#### 2.1 生成证书签名请求（CSR）

1. 打开「钥匙串访问」（Keychain Access）应用
2. 菜单栏: **钥匙串访问 → 证书助理 → 从证书颁发机构请求证书**
3. 填写信息:
   - **电子邮件地址**: 您的 Apple ID 邮箱
   - **常用名称**: 您的姓名
   - **CA 电子邮件地址**: 留空
   - 选择「**存储到磁盘**」
4. 保存为 `CertificateSigningRequest.certSigningRequest`

#### 2.2 在 Apple Developer 网站申请证书

1. 访问: https://developer.apple.com/account/resources/certificates/add
2. 选择「**Developer ID Application**」
3. 点击「Continue」
4. 上传刚才生成的 CSR 文件
5. 点击「Continue」
6. 下载证书（.cer 文件）

#### 2.3 安装证书

1. 双击下载的 .cer 文件
2. 证书会自动导入「钥匙串访问」

#### 2.4 验证证书

在终端执行：
```bash
security find-identity -v -p codesigning
```

**应该看到**:
```
1) XXXXXXXX "Developer ID Application: Your Name (TEAM_ID)"
```

**记录以下信息**（后续需要）:
- **完整签名身份**: `Developer ID Application: Your Name (TEAM_ID)`
- **Team ID**: 括号中的 10 个字符（例如: ABC123XYZ）

**检查点**: ✅ `security find-identity` 显示 Developer ID 证书

---

### 步骤 3: 配置 notarytool 凭证（4 分钟）

**目的**: 配置 Apple 公证服务凭证

#### 3.1 生成 App-Specific Password

1. 访问: https://appleid.apple.com/account/manage
2. 登录您的 Apple ID
3. 在「登录和安全性」部分，找到「**App 专用密码**」
4. 点击「生成密码」
5. 输入标签: `MacCortex Notarization`
6. **复制生成的密码**（格式: xxxx-xxxx-xxxx-xxxx）

⚠️ **重要**: 这个密码只显示一次，请立即保存！

#### 3.2 获取 Team ID

访问: https://developer.apple.com/account/
点击「Membership」
找到「**Team ID**」字段（10 个字符）

#### 3.3 存储 notarytool 凭证

在终端执行：
```bash
xcrun notarytool store-credentials notarytool-profile \
  --apple-id "your@email.com" \
  --team-id "YOUR_TEAM_ID" \
  --password "xxxx-xxxx-xxxx-xxxx"
```

替换：
- `your@email.com`: 您的 Apple ID 邮箱
- `YOUR_TEAM_ID`: 您的 Team ID（10 个字符）
- `xxxx-xxxx-xxxx-xxxx`: 刚才生成的 App-Specific Password

#### 3.4 验证配置

```bash
xcrun notarytool history --keychain-profile notarytool-profile
```

**应该输出**: "No submissions found"（因为还没提交过公证）

**检查点**: ✅ notarytool 凭证配置成功，无报错

---

## 📝 配置信息记录表

完成后，请记录以下信息（保存到安全位置）:

```
MacCortex 开发者配置
==================

✅ Xcode 版本: _____________
✅ Developer ID 签名身份: Developer ID Application: _____________ (__________)
✅ Team ID: __________
✅ Apple ID: _____________@_______
✅ App-Specific Password: xxxx-xxxx-xxxx-xxxx
✅ notarytool Profile: notarytool-profile

配置完成时间: 2026-01-__
```

---

## 🔐 设置环境变量（可选但推荐）

将以下内容添加到 `~/.zshrc` 或 `~/.bashrc`:

```bash
# MacCortex 开发者配置
export DEVELOPER_ID="Developer ID Application: Your Name (TEAM_ID)"
export APPLE_TEAM_ID="YOUR_TEAM_ID"
export KEYCHAIN_PROFILE="notarytool-profile"
```

重新加载配置：
```bash
source ~/.zshrc
```

---

## ✅ 完成验证

完成所有步骤后，执行以下命令验证：

```bash
echo "=== MacCortex 配置验证 ===" && \
echo "" && \
echo "1. Xcode:" && xcodebuild -version && \
echo "" && \
echo "2. Developer ID:" && security find-identity -v -p codesigning | grep "Developer ID" && \
echo "" && \
echo "3. notarytool:" && xcrun notarytool history --keychain-profile notarytool-profile 2>&1 | head -1
```

**预期输出**:
```
=== MacCortex 配置验证 ===

1. Xcode:
Xcode 15.x
Build version xxxxx

2. Developer ID:
1) XXXXXXXX "Developer ID Application: Your Name (TEAM_ID)"

3. notarytool:
No submissions found
```

---

## 🎉 完成后下一步

配置完成后，请告诉我：

1. ✅ 您的 **Team ID**（10 个字符）
2. ✅ 您的 **Developer ID 签名身份**（完整字符串）

我会立即继续执行 Phase 0.5 的剩余任务：
- Day 2: Hardened Runtime 测试
- Day 3: 签名脚本测试
- Day 4: 公证自动化测试
- Day 10: Sparkle 2 + 最终验收

---

## 📞 遇到问题？

### 问题 1: Xcode 切换失败

**错误**: `xcode-select: error: invalid developer directory`

**解决**:
```bash
# 重新安装 Command Line Tools
xcode-select --install
# 然后再切换
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

---

### 问题 2: 证书申请被拒绝

**原因**: Apple ID 信息不完整或需要验证

**解决**:
- 确认 Apple Developer Program 会员资格已激活
- 检查 Apple ID 邮箱已验证
- 联系 Apple 支持: https://developer.apple.com/contact/

---

### 问题 3: notarytool 凭证存储失败

**错误**: `The username or password is incorrect`

**解决**:
- 确认 Apple ID 邮箱拼写正确
- 确认 Team ID 是 10 个字符
- 重新生成 App-Specific Password
- 确保没有多余空格

---

## 📚 参考文档

- [Apple: Code Signing Guide](https://developer.apple.com/documentation/security/code-signing-guide)
- [Apple: Notarizing macOS Software](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- [MacCortex: Apple Developer Program 申请指南](apple-developer-program-guide.md)

---

**文档状态**: ✅ 已完成
**创建时间**: 2026-01-20 12:30:54 +1300 (NZDT)
**预计完成时间**: 10 分钟
