# GitHub Actions CI/CD 配置指南

**文档版本**: v1.0
**创建时间**: 2026-01-20
**Phase**: 0.5 Day 5
**状态**: ✅ 已完成配置文件

---

## 📋 概述

MacCortex 使用 GitHub Actions 实现自动化构建、签名、公证和发布流程。本指南将帮助您配置必要的 GitHub Secrets。

---

## ✅ 已完成工作

- ✅ GitHub Actions 工作流配置: `.github/workflows/release.yml`
- ✅ 支持功能:
  - 自动构建 macOS 应用
  - 代码签名（Developer ID）
  - 公证（notarytool）
  - 创建 DMG 安装包
  - 发布到 GitHub Release
  - 生成自动化 Release Notes

---

## 🔑 必需的 GitHub Secrets

在完成 Apple Developer Program 申请后，您需要配置以下 6 个 GitHub Secrets。

### 配置位置

1. 访问您的 GitHub 仓库
2. 点击「Settings」→「Secrets and variables」→「Actions」
3. 点击「New repository secret」

---

## 📝 Secrets 配置清单

### 1. DEVELOPER_ID_CERT_BASE64

**用途**: Developer ID Application 证书（用于代码签名）

**获取方法**:

```bash
# 步骤 1: 从 Keychain 导出证书
# 打开「钥匙串访问」(Keychain Access)
# 找到「Developer ID Application: Your Name (TEAM_ID)」
# 右键 → 导出 → 选择 .p12 格式
# 设置密码（记住这个密码，后面需要用）
# 保存为 certificate.p12

# 步骤 2: base64 编码
base64 -i certificate.p12 | pbcopy

# 步骤 3: 粘贴到 GitHub Secret
# 名称: DEVELOPER_ID_CERT_BASE64
# 值: 粘贴剪贴板内容

# 步骤 4: 清理临时文件
rm certificate.p12
```

**格式**: base64 编码的字符串（很长，约 3000+ 字符）

---

### 2. DEVELOPER_ID_CERT_PASSWORD

**用途**: .p12 证书文件的密码

**获取方法**: 使用您在导出证书时设置的密码

**格式**: 纯文本密码

**示例**: `MySecureP@ssw0rd`

---

### 3. DEVELOPER_ID_NAME

**用途**: 签名身份的完整名称（用于 codesign 命令）

**获取方法**:

```bash
security find-identity -v -p codesigning
```

**输出示例**:
```
1) ABCDEF1234567890 "Developer ID Application: John Doe (ABC123XYZ)"
```

**配置值**: 复制引号内的完整字符串

**格式**: `Developer ID Application: Your Name (TEAM_ID)`

**示例**: `Developer ID Application: John Doe (ABC123XYZ)`

---

### 4. APPLE_ID

**用途**: Apple ID 邮箱地址（用于公证）

**获取方法**: 您用于注册 Apple Developer Program 的邮箱

**格式**: 邮箱地址

**示例**: `john.doe@example.com`

---

### 5. APPLE_TEAM_ID

**用途**: Apple Developer Team ID（10 个字符）

**获取方法**:

1. 访问: https://developer.apple.com/account/
2. 点击「Membership」
3. 查看「Team ID」字段

**格式**: 10 个大写字母和数字

**示例**: `ABC123XYZ`

---

### 6. APPLE_APP_PASSWORD

**用途**: App-Specific Password（用于公证服务）

**获取方法**:

1. 访问: https://appleid.apple.com/account/manage
2. 登录您的 Apple ID
3. 在「登录和安全性」部分，找到「App 专用密码」
4. 点击「生成密码」
5. 输入标签: `MacCortex GitHub Actions`
6. 复制生成的密码（格式: `xxxx-xxxx-xxxx-xxxx`）

**格式**: 4 组 4 位字符，用短横线分隔

**示例**: `abcd-efgh-ijkl-mnop`

**重要提示**: ⚠️ 这个密码只显示一次，请立即保存到 GitHub Secrets！

---

## 🚀 配置步骤总结

### 完整配置流程

**前置条件** (需要先完成):
- ✅ 加入 Apple Developer Program
- ✅ 申请并安装 Developer ID Application 证书
- ✅ 配置 notarytool 凭证

**配置步骤**:

```bash
# 1. 导出并编码证书
# (按照上面 DEVELOPER_ID_CERT_BASE64 的步骤操作)

# 2. 查询签名身份
security find-identity -v -p codesigning

# 3. 查询 Team ID
# 访问 https://developer.apple.com/account/ → Membership

# 4. 生成 App-Specific Password
# 访问 https://appleid.apple.com/account/manage

# 5. 在 GitHub 配置所有 6 个 Secrets
# GitHub → Settings → Secrets and variables → Actions → New repository secret
```

---

## ✅ 配置验证清单

完成配置后，使用此清单验证：

- [ ] **DEVELOPER_ID_CERT_BASE64**: 已配置（~3000+ 字符）
- [ ] **DEVELOPER_ID_CERT_PASSWORD**: 已配置
- [ ] **DEVELOPER_ID_NAME**: 已配置（格式: Developer ID Application: ...）
- [ ] **APPLE_ID**: 已配置（邮箱地址）
- [ ] **APPLE_TEAM_ID**: 已配置（10 个字符）
- [ ] **APPLE_APP_PASSWORD**: 已配置（格式: xxxx-xxxx-xxxx-xxxx）

---

## 🎯 测试 CI/CD 流程

配置完成后，测试发布流程：

### 方法 1: 创建测试版本标签

```bash
# 1. 确保本地代码已提交
git add -A
git commit -m "准备测试发布"

# 2. 创建版本标签
git tag v0.5.0-alpha

# 3. 推送标签到 GitHub（触发 CI/CD）
git push origin v0.5.0-alpha
```

### 方法 2: 手动触发

1. 访问: GitHub 仓库 → Actions
2. 选择「MacCortex Release CI/CD」工作流
3. 点击「Run workflow」→「Run workflow」

---

## 📊 监控构建状态

### 查看构建日志

1. 访问: GitHub 仓库 → Actions
2. 点击最新的工作流运行
3. 查看每个步骤的详细日志

### 常见构建错误

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| `Certificate not found` | 证书配置错误 | 检查 DEVELOPER_ID_CERT_BASE64 和密码 |
| `Notarization failed` | 公证凭证错误 | 检查 APPLE_ID、TEAM_ID、APP_PASSWORD |
| `Signing identity not found` | 签名身份名称错误 | 检查 DEVELOPER_ID_NAME 格式 |
| `Build failed` | Xcode 项目配置错误 | 检查 Xcode 项目设置 |

---

## 🔒 安全最佳实践

### Secrets 管理

1. **永远不要**:
   - ❌ 在代码中硬编码证书或密码
   - ❌ 提交 .p12 文件到 Git
   - ❌ 在公开渠道分享 Secrets
   - ❌ 将 Secrets 写入日志

2. **应该**:
   - ✅ 只在 GitHub Secrets 中存储敏感信息
   - ✅ 定期更新 App-Specific Password
   - ✅ 使用强密码保护 .p12 文件
   - ✅ 限制团队成员的 Secrets 访问权限

### 证书过期处理

Developer ID 证书有效期为 **5 年**:

1. 过期前 1 个月收到 Apple 通知
2. 在 Apple Developer 网站续订证书
3. 导出新证书并更新 GitHub Secrets
4. 测试 CI/CD 流程确保正常工作

---

## 🎉 发布流程

配置完成后，正式发布版本：

```bash
# 1. 更新版本号 (Info.plist)
# CFBundleShortVersionString: 0.5.0

# 2. 提交所有变更
git add -A
git commit -m "[RELEASE] v0.5.0"

# 3. 创建版本标签
git tag v0.5.0

# 4. 推送到 GitHub
git push origin main
git push origin v0.5.0

# 5. 等待 GitHub Actions 完成（约 10-15 分钟）

# 6. 访问 Releases 页面，审核并发布
# GitHub → Releases → Edit draft → Publish release
```

---

## 📱 GitHub Actions 工作流说明

### 触发条件

工作流在以下情况自动触发：
- 推送版本标签: `v*.*.*` (例如: v0.5.0, v1.0.0)
- 手动触发: Actions 页面手动运行

### 执行步骤

1. **代码检出**: 克隆仓库代码
2. **设置环境**: 配置 Xcode 和 Swift
3. **恢复依赖**: 缓存和恢复 SPM 依赖
4. **导入证书**: 从 Secrets 导入 Developer ID 证书
5. **构建应用**: 使用 Xcodebuild 编译
6. **代码签名**: 使用 Developer ID 签名
7. **公证应用**: 提交到 Apple 公证服务
8. **创建 DMG**: 打包为安装程序
9. **生成 Notes**: 自动生成 Release Notes
10. **创建 Release**: 发布到 GitHub Releases
11. **上传产物**: 保存构建产物 30 天
12. **清理环境**: 删除临时文件和 Keychain

### 构建时间

- 首次构建: ~15-20 分钟（包括公证等待）
- 后续构建: ~10-15 分钟（利用缓存）

---

## 🆘 故障排查

### 问题: 证书导入失败

**症状**: `security: SecKeychainItemImport: The specified item already exists in the keychain.`

**解决方法**:
```bash
# 检查 base64 编码是否正确
echo "$CERT_BASE64" | base64 --decode > test.p12
file test.p12  # 应该显示: "data"
rm test.p12
```

### 问题: 公证超时

**症状**: `Notarization timed out`

**解决方法**:
- Apple 公证服务高峰期可能较慢（2-10 分钟）
- 检查 App-Specific Password 是否正确
- 使用 `xcrun notarytool log` 查看详细日志

### 问题: DMG 创建失败

**症状**: `hdiutil: create failed`

**解决方法**:
- 检查 build 目录是否存在
- 确保应用已正确签名
- 检查磁盘空间是否充足

---

## 📚 相关文档

- [Apple: Notarizing macOS Software](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- [GitHub Actions: macOS runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners#supported-runners-and-hardware-resources)
- [GitHub Actions: Encrypted secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

## ⏭️ 下一步

完成 GitHub Actions 配置后：

1. ✅ 继续 Phase 0.5 Day 6-7（PermissionsKit 开发）
2. ✅ 完成 Day 8-9（UI 和用户教育）
3. ⏳ 等待用户完成 Apple Developer Program 申请
4. ⏳ 测试完整 CI/CD 流程

---

**文档状态**: ✅ 已完成
**创建时间**: 2026-01-20 12:30:54 +1300 (NZDT)
**维护者**: MacCortex 项目团队
