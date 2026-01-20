# MacCortex 文档索引

**最后更新**: 2026-01-20 17:05:00 +1300
**Phase**: 0.5 ✅ 完成
**文档总量**: 130 KB（15 个文件）

---

## 📚 核心文档

### 1. 项目主文档
- **[README.md](../README.md)** - 项目首页、快速开始、验收结果
- **[README_ARCH.md](../README_ARCH.md)** - 完整架构设计（v1.1，修正 Sandbox 矛盾）
- **[CHANGELOG.md](../CHANGELOG.md)** - 版本变更历史（遵循 Keep a Changelog 规范）

### 2. Phase 0.5 总结
- **[Phase-0.5-Summary.md](Phase-0.5-Summary.md)** - 完整总结报告（899 行）
  - 10 天执行历程
  - 核心技术成果
  - 验收结果（技术成熟度 9.0/10）
  - 经验教训
  - Phase 1 准备

---

## 📋 验收报告（按时间顺序）

### Day 1: 项目初始化
- **[phase-0.5-day1-report.md](phase-0.5-day1-report.md)** - 项目初始化报告
  - 目录结构创建
  - Git 仓库初始化
  - 核心配置文件
  - 构建脚本
  - SwiftUI 应用骨架

### Day 2: Hardened Runtime + Entitlements
- **[Day2-Verification-Report.md](Day2-Verification-Report.md)** - 验收报告（271 行）
  - SPM 构建成功（423 KB）
  - Info.plist XML 错误修复
  - Entitlements 配置验证
  - build-app.sh 脚本创建

### Day 3: 代码签名
- **[Day3-Verification-Report.md](Day3-Verification-Report.md)** - 验收报告（272 行）
  - sign.sh Glob 语法错误修复
  - Sparkle.framework 签名
  - MacCortex.app 签名
  - 签名链验证（3 级）
  - Gatekeeper 状态检查

### Day 4: Apple 公证
- **[Day4-Verification-Report.md](Day4-Verification-Report.md)** - 验收报告（247 行）
  - notarytool 凭证配置
  - 公证提交（Submission ID: 12df3803...）
  - 公证成功（~2 分钟）
  - Staple 票据集成
  - Gatekeeper 验证通过（accepted）

### Day 5-9: 并行任务
- **[phase-0.5-day5-9-report.md](phase-0.5-day5-9-report.md)** - 并行任务报告
  - Day 5: GitHub Actions CI/CD
  - Day 6-7: Full Disk Access 集成（PermissionsKit）
  - Day 8: 首次启动 UI
  - Day 9: 用户教育资源（FAQ + 视频脚本）

### Day 10: Sparkle 2 + 最终验收
- **[Day10-Verification-Report.md](Day10-Verification-Report.md)** - 验收报告（525 行）
  - EdDSA 密钥对生成
  - Info.plist 更新（SUPublicEDKey）
  - appcast.xml 创建
  - 重新签名与公证
  - 5 项 P0 验收标准验证

---

## 🔧 开发指南

### 配置与设置
- **[setup-checklist.md](setup-checklist.md)** - 开发环境配置清单（10 分钟）
  - 切换到完整版 Xcode
  - 申请 Developer ID 证书
  - 配置 notarytool 凭证
  - 环境变量设置
  - 验证检查

- **[apple-developer-program-guide.md](apple-developer-program-guide.md)** - Apple Developer Program 申请指南
  - 注册流程
  - 支付方式
  - 证书管理
  - 团队管理

### CI/CD
- **[github-actions-setup.md](github-actions-setup.md)** - GitHub Actions 配置指南
  - 6 个必需 GitHub Secrets
  - 配置步骤
  - 安全最佳实践
  - 故障排查

---

## ❓ 用户支持

### FAQ
- **[FAQ.md](FAQ.md)** - 常见问题解答（15+ 问题）
  - 安装与设置
  - 权限管理
  - 使用方法
  - 故障排查
  - 安全与隐私
  - 技术支持

### 用户教育
- **[videos/authorization-demo-script.md](videos/authorization-demo-script.md)** - 15 秒授权演示视频脚本
  - 镜头分镜
  - 旁白文案
  - 关键帧设计

---

## 📐 架构文档

### 架构更新
- **[ARCH_UPDATE_v1.1.md](ARCH_UPDATE_v1.1.md)** - 架构文档 v1.1 更新报告（341 行）
  - 更新时间：2026-01-20 10:00:00 +1300
  - 更新原因：解决 Sandbox 策略矛盾
  - 主要变更：
    - Section 5.6.3: "沙箱策略" → "权限策略（非 Sandbox 架构）"
    - Section 5.1: 新增 Accessibility 权限
    - Section 10: 插入 Phase 0.5 里程碑
    - Appendix C: 新增 3 个 ADR
  - 对比矩阵：v1.0 vs v1.1
  - 影响评估：低风险

### Architecture Decision Records (ADR)
- **ADR-001**: 非 Sandbox 架构
  - 问题：Full Disk Access 与 App Sandbox 互斥
  - 决策：采用非 Sandbox + 三重防护机制
  - 日期：2026-01-20

- **ADR-002**: LangGraph for Swarm（推荐）
  - 问题：如何实现 Swarm Intelligence
  - 决策：使用 LangGraph Human-in-the-Loop 模式
  - 日期：2026-01-20

- **ADR-003**: 统一授权流程
  - 问题：Full Disk Access + Accessibility 两阶段授权
  - 决策：合并为单一授权向导（FirstRunView）
  - 日期：2026-01-20

---

## 📊 文档统计

### 按类型分类
- **总结报告**: 2 个（Phase 0.5 Summary, Day 5-9 Report）
- **验收报告**: 4 个（Day 2/3/4/10）
- **配置指南**: 3 个（Setup Checklist, GitHub Actions, Apple Developer）
- **用户文档**: 2 个（FAQ, 视频脚本）
- **架构文档**: 2 个（README_ARCH v1.1, ARCH_UPDATE v1.1）
- **索引文档**: 1 个（本文档）

### 按状态分类
- ✅ **已完成**: 14 个
- ⏳ **计划中**: 0 个
- 📝 **持续更新**: 2 个（CHANGELOG, FAQ）

### 文档质量
- **总行数**: ~5,000 行
- **总大小**: ~130 KB
- **平均文档长度**: ~350 行
- **代码示例**: 100+ 个
- **命令示例**: 50+ 个
- **截图/图表**: 0 个（待 Phase 1 添加）

---

## 🔍 文档查找快速链接

### 我想了解...
- **如何开始使用 MacCortex** → [README.md](../README.md)
- **Phase 0.5 完成了什么** → [Phase-0.5-Summary.md](Phase-0.5-Summary.md)
- **架构设计原理** → [README_ARCH.md](../README_ARCH.md)
- **如何配置开发环境** → [setup-checklist.md](setup-checklist.md)
- **版本变更历史** → [CHANGELOG.md](../CHANGELOG.md)
- **常见问题解答** → [FAQ.md](FAQ.md)

### 我遇到问题...
- **启动失败** → [FAQ.md#故障排查](FAQ.md)
- **权限授权问题** → [FAQ.md#权限管理](FAQ.md)
- **签名/公证错误** → [setup-checklist.md#遇到问题](setup-checklist.md)
- **GitHub Actions 失败** → [github-actions-setup.md#故障排查](github-actions-setup.md)

### 我想了解技术细节...
- **代码签名流程** → [Day3-Verification-Report.md](Day3-Verification-Report.md)
- **Apple 公证流程** → [Day4-Verification-Report.md](Day4-Verification-Report.md)
- **Sparkle 2 集成** → [Day10-Verification-Report.md](Day10-Verification-Report.md)
- **权限管理实现** → [phase-0.5-day5-9-report.md](phase-0.5-day5-9-report.md)
- **架构决策记录** → [README_ARCH.md#appendix-c](../README_ARCH.md)

---

## 📅 文档维护

### 更新频率
- **README.md**: 每个 Phase 完成后更新
- **CHANGELOG.md**: 每次版本发布后更新
- **FAQ.md**: 根据用户反馈持续更新
- **验收报告**: 每个 Day 完成后创建，不再修改
- **架构文档**: 重大架构变更时更新（标注版本号）

### 文档所有者
- **核心文档**: Claude Code + 用户
- **验收报告**: Claude Code（自动生成）
- **用户文档**: 用户 + 社区贡献
- **架构文档**: 技术团队

### 文档审核
- **审核频率**: 每个 Phase 完成后
- **审核内容**: 准确性、一致性、完整性
- **审核记录**: 记录在 Git 提交信息中

---

## 🔗 相关链接

### 外部资源
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [Sparkle Project](https://sparkle-project.org/)
- [LangGraph Documentation](https://docs.langchain.com/langgraph)

### 项目资源
- [GitHub 仓库](https://github.com/YOUR_USERNAME/MacCortex)（待创建）
- [官方网站](https://maccortex.app)（待创建）
- [Issue Tracker](https://github.com/YOUR_USERNAME/MacCortex/issues)（待创建）

---

## 📝 文档贡献指南

### 如何贡献
1. Fork 项目仓库
2. 创建文档分支（`git checkout -b docs/your-topic`）
3. 编写或更新文档
4. 提交 Pull Request
5. 等待审核

### 文档规范
- **格式**: Markdown（GitHub Flavored）
- **命名**: kebab-case（例如：setup-checklist.md）
- **语言**: 中文（技术术语可保留英文）
- **示例**: 提供可执行的代码/命令示例
- **链接**: 使用相对路径

### 文档模板
- 验收报告模板：参考 [Day10-Verification-Report.md](Day10-Verification-Report.md)
- 配置指南模板：参考 [setup-checklist.md](setup-checklist.md)
- FAQ 模板：参考 [FAQ.md](FAQ.md)

---

**文档索引创建时间**: 2026-01-20 17:05:00 +1300
**维护者**: Claude Code (Sonnet 4.5)
**状态**: ✅ 最新（Phase 0.5 完成）
