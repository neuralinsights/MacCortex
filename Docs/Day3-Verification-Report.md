# Phase 0.5 Day 3 验收报告

**任务**: 签名脚本测试
**日期**: 2026-01-20
**执行人**: Claude Code (Sonnet 4.5)
**状态**: ✅ **通过**

---

## 执行摘要

Day 3 成功完成 Developer ID 代码签名，所有验收标准 100% 通过：

| 验收项 | 期望结果 | 实际结果 | 状态 |
|--------|----------|----------|------|
| **签名验证** | `codesign --verify` 通过 | ✅ 深度验证成功 | ✅ |
| **签名链完整** | 3 级认证链 | Developer ID → Developer ID CA → Apple Root CA | ✅ |
| **Team ID** | CSRKUK3CQV | CSRKUK3CQV | ✅ |
| **Entitlements** | 4 个 Hardened Runtime 权限 | 全部正确应用 | ✅ |
| **Gatekeeper** | rejected（公证前） | rejected（预期行为） | ✅ |

**核心成果**: MacCortex.app 已使用 Developer ID 正确签名，准备好进行 Day 4 公证。

---

## 签名流程执行记录

### 签名顺序（符合最佳实践）

```
1. XPC Services  ⚠️  无（跳过）
   └─ 路径: Contents/XPCServices/*.xpc
   └─ 结果: 无需签名

2. Frameworks    ✅ 已签名
   └─ Sparkle.framework
   └─ 签名身份: Developer ID Application (CSRKUK3CQV)
   └─ 选项: runtime + timestamp

3. Main App      ✅ 已签名
   └─ MacCortex.app
   └─ 签名身份: Developer ID Application (CSRKUK3CQV)
   └─ 选项: runtime + timestamp + deep
   └─ Entitlements: 4 个权限已应用
```

---

## 签名详细信息

### 主应用 (MacCortex.app)

```
Executable: /Users/jamesg/projects/MacCortex/build/MacCortex.app/Contents/MacOS/MacCortex
Identifier: com.maccortex.app
Format: app bundle with Mach-O thin (arm64)

=== 签名证书链 ===
Authority: Developer ID Application: INNORA INFORMATION TECHNOLOGY PTE. LTD. (CSRKUK3CQV)
Authority: Developer ID Certification Authority
Authority: Apple Root CA

=== 关键属性 ===
TeamIdentifier: CSRKUK3CQV
Runtime Version: 26.2.0 ✅ (Hardened Runtime 已启用)
Timestamp: 20 Jan 2026 at 4:20:00 PM ✅
Signature size: 9029 bytes
Sealed Resources: version=2 rules=13 files=1
Info.plist entries: 15 ✅
```

**验证命令**:
```bash
codesign --verify --deep --strict build/MacCortex.app
```

**结果**: ✅ **通过**

---

### Sparkle.framework

```
Identifier: org.sparkle-project.Sparkle
Authority: Developer ID Application: INNORA INFORMATION TECHNOLOGY PTE. LTD. (CSRKUK3CQV)
Authority: Developer ID Certification Authority
Authority: Apple Root CA
TeamIdentifier: CSRKUK3CQV
Runtime Version: 15.5.0 ✅
```

**验证**: ✅ 框架已正确签名，与主应用使用相同 Team ID

---

### Entitlements 验证

已应用的 4 个 Hardened Runtime 权限：

| Entitlement Key | 值 | 用途 | 状态 |
|-----------------|---|------|------|
| `com.apple.security.cs.allow-jit` | `true` | Python JIT 编译支持 | ✅ |
| `com.apple.security.cs.allow-unsigned-executable-memory` | `true` | Python 扩展内存需求 | ✅ |
| `com.apple.security.cs.disable-library-validation` | `true` | 加载本地 Python 库 | ✅ |
| `com.apple.security.network.client` | `true` | API 调用、联网检索 | ✅ |

**验证命令**:
```bash
codesign -d --entitlements :- build/MacCortex.app
```

**结果**: ✅ **所有权限正确应用**

**重要说明**:
- ❌ **不包含** `com.apple.security.app-sandbox`（与 Full Disk Access 互斥）
- ✅ 符合 **ADR-001** 非 Sandbox 架构决策

---

## 验收测试结果

### 测试 1: 深度签名验证 ✅

**命令**:
```bash
codesign --verify --deep --strict build/MacCortex.app
```

**结果**: ✅ **通过**
- 主应用签名有效
- Sparkle.framework 签名有效
- 所有嵌套组件签名一致
- 无篡改检测

---

### 测试 2: Gatekeeper 评估 ⚠️

**命令**:
```bash
spctl --assess --type execute build/MacCortex.app
```

**结果**: ⚠️ **rejected**

**预期行为**: ✅ 正确
- Developer ID 签名的应用必须经过 **公证（Notarization）** 才能通过 Gatekeeper
- 此状态是公证前的正常表现
- Day 4 公证完成后，此测试将变为 `accepted`

---

### 测试 3: 签名链验证 ✅

**命令**:
```bash
codesign -dvvv build/MacCortex.app 2>&1 | grep "Authority="
```

**结果**: ✅ **3 级认证链完整**

```
Authority=Developer ID Application: INNORA INFORMATION TECHNOLOGY PTE. LTD. (CSRKUK3CQV)
Authority=Developer ID Certification Authority
Authority=Apple Root CA
```

**认证路径**:
```
[MacCortex.app]
    └─ 签名者: INNORA INFORMATION TECHNOLOGY (CSRKUK3CQV)
        └─ 中间 CA: Developer ID Certification Authority
            └─ 根 CA: Apple Root CA ✅
```

---

### 测试 4: Team ID 验证 ✅

**命令**:
```bash
codesign -dvvv build/MacCortex.app 2>&1 | grep "TeamIdentifier="
```

**结果**: ✅ **Team ID 正确**

```
TeamIdentifier=CSRKUK3CQV
```

**验证**: 匹配 `Configs/developer-config.env` 中的 `APPLE_TEAM_ID`

---

## 修复的脚本问题

### 问题: Glob 模式语法错误 🔴

**症状**:
```bash
./Scripts/sign.sh: line 35: syntax error near unexpected token `2'
```

**根因**:
原脚本在 `for` 循环中直接使用了 `2>/dev/null`：
```bash
for xpc in "${APP_PATH}"/Contents/XPCServices/*.xpc 2>/dev/null; do
```

这在 bash 中是不合法的语法（重定向必须在循环外部）。

**修复**:
使用 `nullglob` shell 选项 + 目录存在检查：
```bash
if [ -d "${APP_PATH}/Contents/XPCServices" ]; then
    shopt -s nullglob  # 如果没有匹配项，glob 返回空
    for xpc in "${APP_PATH}"/Contents/XPCServices/*.xpc; do
        codesign ...
    done
    shopt -u nullglob
fi
```

**验证**: ✅ 脚本执行成功，无语法错误

---

## 对比：签名前后状态

| 属性 | 签名前（Day 2） | 签名后（Day 3） | 变化 |
|------|----------------|----------------|------|
| **Signature** | `adhoc` | `Developer ID Application` | ✅ 已签名 |
| **Authority** | `(none)` | INNORA... → Apple Root CA | ✅ 完整链 |
| **TeamIdentifier** | `not set` | `CSRKUK3CQV` | ✅ 已设置 |
| **Info.plist** | `not bound` | `entries=15` | ✅ 已绑定 |
| **Runtime** | `(none)` | `26.2.0` | ✅ 已启用 |
| **Timestamp** | `(none)` | `20 Jan 2026 4:20 PM` | ✅ 已加戳 |
| **Entitlements** | `(none)` | 4 个权限 | ✅ 已应用 |
| **Gatekeeper** | ❌ rejected | ❌ rejected | ⚠️ 需公证 |

---

## 技术细节

### 签名选项说明

| 选项 | 作用 | Day 3 使用 |
|------|------|-----------|
| `--force` | 强制覆盖现有签名 | ✅ 是 |
| `--sign` | 指定签名身份 | ✅ Developer ID |
| `--options runtime` | 启用 Hardened Runtime | ✅ 是 |
| `--timestamp` | 添加可信时间戳 | ✅ 是 |
| `--entitlements` | 指定权限文件 | ✅ 主应用使用 |
| `--deep` | 深度签名（递归） | ✅ 主应用使用 |

**签名顺序重要性**:
- ❌ **错误顺序**: App → Frameworks → XPC（会导致验证失败）
- ✅ **正确顺序**: XPC → Frameworks → App（从内到外）

---

## Day 4 准备就绪检查

| 依赖项 | 状态 | 验证 |
|--------|------|------|
| **签名完成** | ✅ 已完成 | Developer ID 签名，3 级认证链 |
| **Timestamp** | ✅ 已添加 | 2026-01-20 16:20:00 |
| **App-Specific Password** | ⏳ 待生成 | 用户需在 appleid.apple.com 生成 |
| **notarytool 凭证** | ⏳ 待配置 | Day 4 执行 `xcrun notarytool store-credentials` |
| **公证脚本** | ✅ 已创建 | `Scripts/notarize.sh`（Day 1 创建） |

---

## 下一步行动（Day 4）

### 任务 1: 生成 App-Specific Password（用户操作）

1. 访问 https://appleid.apple.com/account/manage
2. 在「安全性」部分找到「应用专用密码」
3. 点击「生成密码」，标签填写「MacCortex Notarization」
4. 复制生成的 16 位密码（格式：xxxx-xxxx-xxxx-xxxx）

### 任务 2: 配置 notarytool 凭证

```bash
xcrun notarytool store-credentials notarytool-profile \
  --apple-id "your@email.com" \
  --team-id "CSRKUK3CQV" \
  --password "xxxx-xxxx-xxxx-xxxx"
```

### 任务 3: 执行公证

```bash
./Scripts/notarize.sh
```

### 任务 4: 验收标准

- ✅ `xcrun notarytool submit` 提交成功
- ✅ 公证状态: `Accepted`（等待时间：5-15 分钟）
- ✅ `xcrun stapler staple` 票据粘附成功
- ✅ `spctl --assess` 输出 `accepted`（Gatekeeper 通过）

---

## 风险与缓解

### 已缓解风险

- ✅ **脚本语法错误**: 已修复 glob 模式问题
- ✅ **签名顺序错误**: 按正确顺序（XPC → Frameworks → App）
- ✅ **Entitlements 缺失**: 已显式指定并验证应用成功

### 待验证风险（Day 4）

- ⚠️ **公证可能失败的原因**:
  - App-Specific Password 错误
  - 签名不符合公证要求（已签名应可通过）
  - Hardened Runtime 配置问题（已验证应无问题）
  - 网络连接问题（公证服务器不可达）

- 🔄 **缓解措施**:
  - 提前验证 Apple ID 账号状态
  - 准备 notarytool 错误日志查看命令
  - 保留未签名的 .app 副本（回滚用）

---

## 性能数据

| 指标 | 数值 |
|------|------|
| **签名执行时间** | ~5 秒 |
| **签名大小** | 9,029 bytes |
| **.app Bundle 大小** | 3.2 MB（签名前后无明显变化） |
| **签名验证时间** | < 1 秒 |
| **Sparkle 框架签名** | 成功（< 2 秒） |

---

## 文件变更记录

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `Scripts/sign.sh` | 修复 | 修复 glob 模式语法错误（Line 35, 47） |
| `build/MacCortex.app` | 签名 | 添加 Developer ID 签名 + Entitlements |
| `build/MacCortex.app/Contents/Frameworks/Sparkle.framework` | 签名 | 重新签名框架 |

---

## 验收结论

✅ **Day 3 任务全部完成**

**核心成果**:
- MacCortex.app 已使用 Developer ID 正确签名
- 签名链完整（3 级认证）
- 所有 Entitlements 正确应用（4 个权限）
- Team ID 匹配（CSRKUK3CQV）
- 深度验证通过（`codesign --verify --deep --strict`）

**阻塞性问题**: 无
**警告**: Gatekeeper 拒绝（预期，需公证）
**下一步**: Day 4 公证自动化配置

---

**报告生成时间**: 2026-01-20 16:30:00 +1300 (NZDT)
**验证人**: Claude Code (Sonnet 4.5)
**Git Commit**: 待提交
