# MacCortex 常见问题解答 (FAQ)

**文档版本**: v1.0
**创建时间**: 2026-01-20
**Phase**: 0.5 Day 9
**状态**: ✅ 已完成

---

## 📚 目录

- [安装与设置](#安装与设置)
- [权限管理](#权限管理)
- [使用方法](#使用方法)
- [故障排查](#故障排查)
- [安全与隐私](#安全与隐私)
- [技术支持](#技术支持)

---

## 安装与设置

### Q: MacCortex 的系统要求是什么？

**A**: MacCortex 需要：
- **操作系统**: macOS 14.0 (Sonoma) 或更高版本
- **处理器**: Apple Silicon (M1/M2/M3) 或 Intel
- **内存**: 至少 8GB RAM（推荐 16GB+）
- **存储**: 至少 500MB 可用空间
- **网络**: 联网访问（用于 API 调用和更新）

---

### Q: 如何安装 MacCortex？

**A**: 安装步骤：
1. 从 [GitHub Releases](https://github.com/YOUR_USERNAME/MacCortex/releases) 下载最新版本的 DMG 文件
2. 双击 DMG 文件打开
3. 将 MacCortex.app 拖到 Applications 文件夹
4. 双击打开 MacCortex
5. 按照首次启动引导完成权限设置

---

### Q: 首次启动时出现"无法打开"或"来自未验证的开发者"提示怎么办？

**A**: 这是 macOS Gatekeeper 的安全保护。解决方法：

**方法 1（推荐）**：
1. 右键点击 MacCortex.app
2. 选择「打开」
3. 在弹出的对话框中点击「打开」

**方法 2**：
1. 打开「系统设置」→「隐私与安全性」
2. 在「安全性」部分，找到被阻止的 MacCortex
3. 点击「仍要打开」

**注意**: MacCortex 使用 Apple Developer ID 签名和公证，确保安全可靠。

---

## 权限管理

### Q: 什么是 Full Disk Access（完全磁盘访问）？

**A**: Full Disk Access 是 macOS 的安全功能，允许应用访问：
- 系统文件和文件夹
- 其他应用的数据（如 Notes、Mail）
- 受保护的用户文件

MacCortex 需要此权限来：
- ✅ 读取和组织您的文件和笔记
- ✅ 搜索整个文件系统
- ✅ 备份和同步数据
- ✅ 与其他应用（如 Notes）集成

---

### Q: 如何授予 Full Disk Access 权限？

**A**: 详细步骤：

1. **打开系统设置**：
   - 方法 A: 在 MacCortex 首次启动引导中点击「打开系统设置授权」
   - 方法 B: 手动打开「系统设置」→「隐私与安全性」→「Full Disk Access」

2. **添加 MacCortex**：
   - 如果列表中已有 MacCortex（未勾选），勾选它
   - 如果列表中没有，点击「+」按钮 → 选择 Applications/MacCortex.app

3. **确认授权**：
   - 输入管理员密码
   - 勾选 MacCortex 旁边的复选框

4. **重启应用**（如果需要）：
   - 关闭 MacCortex
   - 重新打开，权限生效

**视频演示**: 查看 `Docs/videos/fda-authorization-guide.mp4`（60 秒演示）

---

### Q: MacCortex 能自动获取 Full Disk Access 吗？

**A**: **不能**。出于安全原因，macOS 不允许任何应用自动授予自己 Full Disk Access 权限。

这是 Apple 的设计：
- ✅ 保护用户数据安全
- ✅ 防止恶意软件自动获取权限
- ✅ 确保用户明确知情并同意

您必须手动在系统设置中授权。

---

### Q: 如果不授予 Full Disk Access 会怎样？

**A**: MacCortex 会进入**降级模式**：

**可用功能** ✅：
- 访问您主动选择的文件和文件夹
- 使用 Open/Save 对话框操作文件
- 访问应用自己的沙盒目录

**不可用功能** ❌：
- 自动读取 Notes 笔记
- 搜索整个文件系统
- 访问其他应用的数据
- 批量文件组织功能

**推荐**: 为了获得完整体验，请授予权限。

---

### Q: MacCortex 会访问哪些文件？

**A**: MacCortex 只访问必要的文件：

**会访问** ✅：
- 您的文档文件夹（~/Documents）
- Notes 应用数据（~/Library/Group Containers/.../NoteStore.sqlite）
- 您在 MacCortex 中主动添加的路径

**不会访问** ❌：
- 系统敏感文件（如密码、证书）
- 其他用户的数据
- 无关的应用数据

**透明度**: 所有文件访问都会记录日志（可在应用内查看）。

---

## 使用方法

### Q: MacCortex 的核心功能是什么？

**A**: MacCortex Phase 0.5 提供基础设施能力：

**当前功能** (Phase 0.5):
- ✅ Full Disk Access 权限管理
- ✅ 自动更新（Sparkle 2）
- ✅ 代码签名和公证（安全保障）

**即将推出** (Phase 1+):
- 🔜 Pattern 快速处理（总结、提取、翻译、格式化、搜索）
- 🔜 Swarm 多代理编排（复杂任务自动化）
- 🔜 本地 AI 模型（MLX + Ollama）
- 🔜 Raycast 扩展（快速访问）
- 🔜 Notes 集成（自动组织笔记）

---

### Q: 如何更新 MacCortex？

**A**: MacCortex 支持自动更新（基于 Sparkle 2）：

**自动更新**（推荐）：
1. MacCortex 会定期检查更新（后台进行）
2. 有新版本时，会弹出通知
3. 点击「立即更新」自动下载和安装

**手动检查**：
1. 打开 MacCortex
2. 菜单栏：MacCortex → Check for Updates
3. 如果有更新，按提示操作

**手动下载**：
- 访问 [GitHub Releases](https://github.com/YOUR_USERNAME/MacCortex/releases)
- 下载最新版本 DMG
- 替换 Applications 文件夹中的旧版本

---

## 故障排查

### Q: MacCortex 无法启动或崩溃

**A**: 故障排查步骤：

1. **检查系统要求**: 确保运行 macOS 14.0+
2. **完全重启应用**:
   ```bash
   # 强制退出
   killall MacCortex
   # 重新启动
   open -a MacCortex
   ```
3. **检查权限**: 确认 Full Disk Access 已授予
4. **查看日志**:
   ```bash
   # 查看应用日志
   log show --predicate 'process == "MacCortex"' --last 1h
   ```
5. **重置设置**（如果需要）:
   ```bash
   # 删除偏好设置文件
   rm ~/Library/Preferences/com.maccortex.app.plist
   ```

如果问题持续，请提交 [GitHub Issue](https://github.com/YOUR_USERNAME/MacCortex/issues)。

---

### Q: Full Disk Access 授权后仍然无法访问文件

**A**: 可能的原因和解决方法：

1. **应用未重启**:
   - 完全退出 MacCortex（Cmd+Q）
   - 重新启动

2. **权限未勾选**:
   - 打开「系统设置」→「隐私与安全性」→「Full Disk Access」
   - 确认 MacCortex 旁边的复选框**已勾选**（不是只是在列表中）

3. **macOS 缓存问题**:
   ```bash
   # 重置 TCC 数据库（需要管理员权限）
   tccutil reset All com.maccortex.app
   ```
   - 然后重新授权

4. **文件权限问题**:
   - 检查目标文件的权限设置
   - 确保您的用户账户有读取权限

---

### Q: 更新失败或卡住

**A**: 解决方法：

1. **取消当前更新**: 关闭更新窗口
2. **手动下载**: 从 GitHub Releases 下载最新 DMG
3. **清理旧版本**:
   ```bash
   # 删除旧的 MacCortex.app
   rm -rf /Applications/MacCortex.app
   ```
4. **重新安装**: 安装新下载的版本

---

## 安全与隐私

### Q: MacCortex 是否收集用户数据？

**A**: **不收集个人数据**。

MacCortex 的隐私承诺：
- ✅ **本地优先**: 所有数据处理在您的 Mac 上完成
- ✅ **零遥测**: 不发送使用统计或分析数据
- ✅ **无账户**: 无需注册或登录
- ✅ **开源透明**: 代码在 GitHub 公开，可审计

**唯一的网络连接**：
- 检查更新（Sparkle）
- API 调用（如果您配置了云端 AI 服务）

---

### Q: MacCortex 如何保护我的数据安全？

**A**: 多层安全保障：

**代码安全**：
- ✅ Apple Developer ID 签名
- ✅ Apple 公证服务验证
- ✅ Hardened Runtime 启用
- ✅ 代码审计和测试

**数据安全**：
- ✅ 本地存储加密（系统级 FileVault）
- ✅ 不上传用户文件到云端
- ✅ API 密钥安全存储（macOS Keychain）

**权限最小化**：
- ✅ 只请求必要权限
- ✅ 用户完全控制授权
- ✅ 可随时撤销权限

---

### Q: 我可以在企业环境中使用 MacCortex 吗？

**A**: **可以**，Mac Cortex 支持企业部署。

**企业功能**（规划中）：
- 🔜 MDM 配置文件（Jamf Pro 兼容）
- 🔜 PPPC 预授权（无需用户手动授权）
- 🔜 集中式配置管理
- 🔜 审计日志导出
- 🔜 私有化部署选项

联系我们获取企业版信息。

---

## 技术支持

### Q: 如何报告 Bug 或请求新功能？

**A**: 我们欢迎您的反馈！

**报告 Bug**：
1. 访问 [GitHub Issues](https://github.com/YOUR_USERNAME/MacCortex/issues)
2. 点击「New issue」
3. 选择「Bug report」模板
4. 填写详细信息：
   - macOS 版本
   - MacCortex 版本
   - 复现步骤
   - 错误截图或日志

**请求功能**：
1. 访问 [GitHub Issues](https://github.com/YOUR_USERNAME/MacCortex/issues)
2. 点击「New issue」
3. 选择「Feature request」模板
4. 描述您的需求和使用场景

---

### Q: MacCortex 是开源的吗？

**A**: **是的！** MacCortex 在 GitHub 上开源。

**仓库**: https://github.com/YOUR_USERNAME/MacCortex
**许可证**: MIT License

您可以：
- ✅ 查看完整源代码
- ✅ 贡献代码和文档
- ✅ Fork 和自定义
- ✅ 提交 Pull Request

欢迎参与贡献！

---

### Q: 如何获取更多帮助？

**A**: 多种支持渠道：

1. **文档**:
   - [架构设计](README_ARCH.md)
   - [Phase 0.5 实施计划](Docs/phase-0.5-plan.md)
   - [Apple Developer Program 申请指南](Docs/apple-developer-program-guide.md)
   - [GitHub Actions 配置指南](Docs/github-actions-setup.md)

2. **社区**:
   - [GitHub Discussions](https://github.com/YOUR_USERNAME/MacCortex/discussions)
   - [GitHub Issues](https://github.com/YOUR_USERNAME/MacCortex/issues)

3. **联系方式**:
   - 邮箱: support@maccortex.app（规划中）
   - Twitter: @MacCortex（规划中）

---

## 版本历史

### v0.5.0 (Phase 0.5) - 2026-01-20

**新功能**:
- ✅ Full Disk Access 权限管理
- ✅ 首次启动引导界面
- ✅ 自动更新支持（Sparkle 2）
- ✅ 代码签名和公证
- ✅ GitHub Actions CI/CD

**已知问题**:
- Pattern 和 Swarm 功能尚未实现（Phase 1）
- 暂不支持 Raycast 扩展（Phase 1）

---

## 附录：快速参考

### 系统设置路径

```
macOS 13+ (Ventura):
系统设置 → 隐私与安全性 → Full Disk Access

macOS 12 及以下:
系统偏好设置 → 安全性与隐私 → 隐私 → Full Disk Access
```

### 命令行工具

```bash
# 检查权限状态
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT * FROM access WHERE service='kTCCServiceSystemPolicyAllFiles'"

# 查看应用日志
log show --predicate 'process == "MacCortex"' --last 1h

# 验证代码签名
codesign -dv --verbose=4 /Applications/MacCortex.app

# 验证公证
spctl --assess --type execute /Applications/MacCortex.app
```

---

**文档状态**: ✅ 已完成
**创建时间**: 2026-01-20 12:30:54 +1300 (NZDT)
**维护者**: MacCortex 项目团队

**需要更多帮助？** 访问 [GitHub Issues](https://github.com/YOUR_USERNAME/MacCortex/issues)

**Sources:**
- [GitHub - inket/FullDiskAccess](https://github.com/inket/FullDiskAccess)
- [GitHub - MacPaw/PermissionsKit](https://github.com/MacPaw/PermissionsKit)
- [Apple Developer - Full Disk Access](https://developer.apple.com/forums/thread/107546)
- [Huntress - Full Transparency: Controlling Apple's TCC](https://www.huntress.com/blog/full-transparency-controlling-apples-tcc)
