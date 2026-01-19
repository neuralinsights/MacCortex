# MacCortex

**下一代 macOS 个人智能基础设施（Personal AI Infrastructure）**

## 项目状态

🚧 **Phase 0.5: 签名与公证基础设施建设中**（2026-01-20 启动）

- ✅ 项目目录结构已创建
- ✅ Git 仓库已初始化
- ⏳ Developer ID 证书待申请
- ⏳ Xcode 项目待配置

## 快速开始

### 前置要求

- macOS 14.0+
- Xcode 15.2+
- Apple Developer Program 账号（$99/年）
- Git

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/MacCortex.git
cd MacCortex

# 2. 申请 Developer ID 证书
# 访问: https://developer.apple.com/account/resources/certificates/add
# 选择: Developer ID Application

# 3. 构建项目（待 Phase 0.5 完成后可用）
swift build

# 4. 运行应用
swift run MacCortex
```

## Phase 0.5 验收标准

| # | 验收项 | 状态 |
|---|--------|------|
| 1 | 签名验证通过 | ⏳ |
| 2 | 公证成功 | ⏳ |
| 3 | Gatekeeper 放行 | ⏳ |
| 4 | 授权流程完成 | ⏳ |
| 5 | Sparkle 检测更新 | ⏳ |

## 项目结构

```
MacCortex/
├── Sources/              # Swift 源代码
│   ├── MacCortexApp/    # 主应用（SwiftUI）
│   ├── PermissionsKit/  # 权限管理
│   └── PythonBridge/    # Swift ↔ Python 桥接
├── Scripts/             # 构建脚本
│   ├── sign.sh          # 代码签名
│   ├── notarize.sh      # 公证
│   └── build-dmg.sh     # DMG 打包
├── Resources/           # 资源文件
│   ├── Entitlements/    # Hardened Runtime 配置
│   └── Info.plist       # 应用元信息
├── Backend/             # Python 后端（Phase 1+）
└── RaycastExtension/    # Raycast 扩展（Phase 1 快速验证）
```

## 技术栈

- **GUI**: SwiftUI (macOS 14+)
- **权限管理**: FullDiskAccess.swift + TCC
- **签名与公证**: Developer ID + xcrun notarytool
- **自动更新**: Sparkle 2 (EdDSA)
- **后端**: Python + LangGraph + MLX/Ollama (Phase 1+)

## 文档

- [架构设计](README_ARCH.md) - 完整的系统架构与设计决策
- [Phase 0.5 实施计划](Docs/phase-0.5-plan.md) - 当前阶段详细计划

## 许可证

MIT License

## 参与贡献

MacCortex 正在积极开发中。欢迎贡献代码、报告问题或提出建议。

---

**创建时间**: 2026-01-20  
**当前版本**: v0.5.0-alpha  
**Phase**: 0.5 (基础设施建设)
