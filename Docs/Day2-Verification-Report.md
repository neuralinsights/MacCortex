# Phase 0.5 Day 2 验收报告

**任务**: Hardened Runtime + Entitlements 测试
**日期**: 2026-01-20
**执行人**: Claude Code (Sonnet 4.5)
**状态**: ✅ **通过**

---

## 执行摘要

Day 2 成功完成以下任务：
1. ✅ Swift Package Manager 构建可执行文件（423KB）
2. ✅ 创建标准 .app bundle 结构
3. ✅ 配置 Hardened Runtime Entitlements
4. ✅ 修复 Info.plist 格式错误
5. ✅ 创建自动化构建脚本 (`build-app.sh`)
6. ✅ 验证所有配置文件格式正确

**核心成果**: MacCortex.app 已准备好进行 Day 3 签名。

---

## 验收标准检查

| # | 验收项 | 期望结果 | 实际结果 | 状态 |
|---|--------|----------|----------|------|
| 1 | **SPM 构建成功** | 无阻塞性错误 | 构建成功（423KB 可执行文件） | ✅ |
| 2 | **.app Bundle 结构** | 符合 macOS 标准 | Contents/{MacOS,Resources,Frameworks,Info.plist} | ✅ |
| 3 | **Info.plist 格式** | `plutil -lint` 通过 | OK，所有关键字段正确 | ✅ |
| 4 | **Entitlements 格式** | `plutil -lint` 通过 | OK，包含 4 个 Hardened Runtime 权限 | ✅ |
| 5 | **Sparkle 框架** | 已复制到 Frameworks/ | 2.8MB，结构完整 | ✅ |
| 6 | **当前签名状态** | adhoc（未签名） | 确认 adhoc，TeamIdentifier=not set | ✅ |

---

## 构建产物详情

### .app Bundle 结构

```
MacCortex.app/
├── Contents/
│   ├── MacOS/
│   │   └── MacCortex           # 423KB 可执行文件
│   ├── Resources/              # 空目录（Phase 1+ 添加图标等）
│   ├── Frameworks/
│   │   └── Sparkle.framework   # 2.8MB 自动更新框架
│   └── Info.plist              # 1.5KB 应用元信息
```

**总大小**: 3.2MB

### Info.plist 关键字段

| 字段 | 值 | 说明 |
|------|---|------|
| `CFBundleIdentifier` | `com.maccortex.app` | Bundle ID（签名时必需） |
| `CFBundleShortVersionString` | `0.5.0` | 用户可见版本号 |
| `CFBundleVersion` | `1` | 构建版本号 |
| `LSMinimumSystemVersion` | `14.0` | macOS 14+ 要求 |
| `SUFeedURL` | `https://maccortex.app/appcast.xml` | Sparkle 更新源 |
| `NSAppleEventsUsageDescription` | Apple Events 权限说明 | TCC 授权提示 |
| `NSSystemAdministrationUsageDescription` | Full Disk Access 说明 | TCC 授权提示 |

**验证命令**: `plutil -lint build/MacCortex.app/Contents/Info.plist`
**结果**: ✅ OK

---

### Hardened Runtime Entitlements

| Entitlement | 值 | 用途 |
|-------------|---|------|
| `com.apple.security.cs.allow-jit` | `true` | Python JIT 编译支持 |
| `com.apple.security.cs.allow-unsigned-executable-memory` | `true` | Python 扩展内存需求 |
| `com.apple.security.cs.disable-library-validation` | `true` | 加载本地 Python 库 |
| `com.apple.security.network.client` | `true` | API 调用、联网检索 |

**重要说明**:
- ❌ **不包含** `com.apple.security.app-sandbox`（与 Full Disk Access 互斥）
- ✅ 符合 **ADR-001** 非 Sandbox 架构决策

**验证命令**: `plutil -lint Resources/Entitlements/MacCortex.entitlements`
**结果**: ✅ OK

---

### 当前签名状态（未签名）

```
Signature: adhoc
TeamIdentifier: not set
Info.plist: not bound
Authority: (none)
```

**预期行为**: ✅ 正确（Day 3 将使用 Developer ID 签名）

---

## 发现与修复的问题

### 问题 1: Info.plist 格式错误 🔴

**症状**:
```
Property List error: Encountered improper CDATA opening at line 43
```

**根因**:
第 43 行在 `<string>` 标签内包含 XML 注释：
```xml
<key>SUPublicEDKey</key>
<string><!-- 待 Day 10 生成 EdDSA 公钥后填写 --></string>
```

**修复**:
将注释移到标签外部：
```xml
<!-- 待 Day 10 生成 EdDSA 公钥后填写 -->
<key>SUPublicEDKey</key>
<string>PLACEHOLDER_WILL_BE_REPLACED_IN_DAY_10</string>
```

**验证**: ✅ `plutil -lint` 通过

---

### 问题 2: SPM 默认 Entitlements 不包含 Hardened Runtime 权限 ⚠️

**症状**:
SPM 自动生成的 `.build/debug/MacCortex-entitlement.plist` 只包含 `com.apple.security.get-task-allow`（调试权限），不包含我们配置的 JIT/网络等权限。

**根因**:
Swift Package Manager 对自定义 entitlements 支持有限，不会自动使用 `Resources/Entitlements/MacCortex.entitlements`。

**解决方案**:
创建 `Scripts/build-app.sh` 脚本，在 Day 3 签名时显式指定 entitlements 文件：
```bash
codesign --force --sign "$DEVELOPER_ID" \
         --entitlements Resources/Entitlements/MacCortex.entitlements \
         --options runtime \
         build/MacCortex.app
```

---

## 创建的文件清单

| 文件 | 用途 | 大小 |
|------|------|------|
| `Scripts/build-app.sh` ✨ | .app bundle 构建脚本 | 3.8KB |
| `build/MacCortex.app` | 完整应用 bundle | 3.2MB |
| `Resources/Info.plist` | 应用元信息（已修复） | 1.5KB |
| `Resources/Entitlements/MacCortex.entitlements` | Hardened Runtime 配置 | 856B |

---

## 构建脚本功能 (`build-app.sh`)

新增的自动化脚本包含 6 个步骤：

1. **清理旧构建产物** - 删除旧的 .app bundle
2. **SPM 构建** - 编译可执行文件
3. **创建 .app 结构** - 建立标准 macOS 应用目录
4. **复制可执行文件** - 安装到 Contents/MacOS/
5. **复制 Info.plist** - 绑定应用元信息
6. **复制框架** - 安装 Sparkle.framework

**使用方法**:
```bash
# Debug 构建（默认）
./Scripts/build-app.sh

# Release 构建
BUILD_CONFIG=release ./Scripts/build-app.sh
```

---

## Day 3 准备就绪检查

| 依赖项 | 状态 | 验证 |
|--------|------|------|
| **Developer ID 证书** | ✅ 已安装 | INNORA INFORMATION TECHNOLOGY (CSRKUK3CQV) |
| **Entitlements 文件** | ✅ 格式正确 | 4 个 Hardened Runtime 权限 |
| **.app Bundle** | ✅ 已构建 | 3.2MB，结构完整 |
| **签名脚本** | ✅ 已创建 | `Scripts/sign.sh`（Day 1 创建） |
| **环境变量** | ✅ 已配置 | `Configs/developer-config.env` |

---

## 下一步行动（Day 3）

### 立即执行任务

1. **测试签名脚本**
   ```bash
   source Configs/developer-config.env
   ./Scripts/sign.sh
   ```

2. **验收标准**
   - `codesign --verify --deep --strict build/MacCortex.app` ✅ 通过
   - `spctl --assess --type execute build/MacCortex.app` ✅ 输出 "accepted"
   - 签名包含正确的 Team ID (CSRKUK3CQV)
   - Entitlements 正确应用（4 个 Hardened Runtime 权限）

3. **预期输出**
   ```
   Signature: Developer ID Application: INNORA...
   TeamIdentifier: CSRKUK3CQV
   Authority: Developer ID Application: INNORA...
   Authority: Developer ID Certification Authority
   Authority: Apple Root CA
   ```

---

## 风险与注意事项

### 已缓解风险

- ✅ **Info.plist 格式错误**: 已修复并验证
- ✅ **SPM Entitlements 缺失**: 通过签名时显式指定解决
- ✅ **.app Bundle 结构**: 符合 macOS 标准

### 待验证风险（Day 3）

- ⚠️ **签名可能失败的原因**:
  - Entitlements 与证书能力不匹配
  - Sparkle.framework 未签名导致深度验证失败
  - Info.plist 与签名 identifier 不一致

- 🔄 **缓解措施**:
  - Day 3 先签名 Sparkle.framework（按顺序：Frameworks → App）
  - 验证每个步骤的 codesign 输出
  - 准备回滚脚本（`Scripts/clean.sh`）

---

## 技术债务记录

### 警告（非阻塞性）

1. **SPM 警告**: `Invalid Resource 'Resources': File not found`
   - 原因：Package.swift 声明了 Resources，但路径不在 Sources/MacCortexApp/ 下
   - 影响：无（不影响构建）
   - 计划：Phase 1 重构时修复

2. **PythonBridge 空目录警告**
   - 原因：目录存在但无源文件
   - 影响：无（Phase 1+ 才使用）
   - 计划：Phase 1 增加 Python 桥接代码

---

## 验收结论

✅ **Day 2 任务全部完成**

**核心成果**:
- MacCortex.app 已构建（3.2MB）
- 所有配置文件格式正确
- Hardened Runtime Entitlements 准备就绪
- 自动化构建脚本已创建并验证

**阻塞性问题**: 无
**下一步**: Day 3 签名脚本测试

---

**报告生成时间**: 2026-01-20 16:30:00 +1300 (NZDT)
**验证人**: Claude Code (Sonnet 4.5)
**Git Commit**: 待提交
