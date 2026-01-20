# Bug Fix: Sparkle.framework 动态链接错误

**Bug ID**: #20260120-RPATH
**发现时间**: 2026-01-20 20:49:11 +1300
**修复时间**: 2026-01-20 20:55:00 +1300
**严重级别**: 🔴 Critical（应用无法启动）
**状态**: ✅ 已修复

---

## 一、问题描述

### 1.1 用户报告

用户执行 `open build/MacCortex.app` 时，应用立即崩溃，错误信息：

```
Termination Reason: Namespace DYLD, Code 1, Library missing
Library not loaded: @rpath/Sparkle.framework/Versions/B/Sparkle
Referenced from: <AC4AEE13-4865-383D-86AC-592F70CEDF69> /Users/USER/*/MacCortex.app/Contents/MacOS/MacCortex
Reason: tried: '/usr/lib/swift/Sparkle.framework/Versions/B/Sparkle' (no such file, not in dyld cache), '/Users/jamesg/projects/MacCortex/build/MacCortex.app/Contents/MacOS/Sparkle.framework/Versions/B/Sparkle' (no such file), ...
```

### 1.2 错误类型

- **Exception Type**: `EXC_CRASH (SIGABRT)`
- **Termination Reason**: `DYLD` - 动态链接器无法找到 Sparkle.framework
- **影响**: 应用启动时立即崩溃，100% 失败率

---

## 二、根因分析

### 2.1 诊断步骤

#### 步骤 1: 检查 Sparkle.framework 位置
```bash
ls -la build/MacCortex.app/Contents/Frameworks/
```

**结果**: ✅ Sparkle.framework 存在于正确位置
```
drwxr-xr-x@ 11 jamesg  staff  352 20 Jan 16:41 Sparkle.framework
```

#### 步骤 2: 检查应用的 @rpath 配置
```bash
otool -l build/MacCortex.app/Contents/MacOS/MacCortex | grep -A 2 "LC_RPATH"
```

**结果**: ❌ @rpath 缺失 `@loader_path/../Frameworks`
```
LC_RPATH
  path /usr/lib/swift
LC_RPATH
  path @loader_path  # ← 错误：指向 MacOS/ 目录
LC_RPATH
  path /Applications/Xcode.app/.../swift-6.2/macosx
```

#### 步骤 3: 检查 Sparkle 的链接路径
```bash
otool -L build/MacCortex.app/Contents/MacOS/MacCortex | grep Sparkle
```

**结果**: Sparkle 链接到 `@rpath/Sparkle.framework/Versions/B/Sparkle`
```
@rpath/Sparkle.framework/Versions/B/Sparkle (compatibility version 1.6.0, current version 2.8.1)
```

### 2.2 根本原因

**问题**: SPM (Swift Package Manager) 构建时没有设置正确的 `@rpath`

**技术细节**:
1. MacCortex.app 链接到 `@rpath/Sparkle.framework/Versions/B/Sparkle`
2. `@rpath` 包含：
   - `/usr/lib/swift`（系统 Swift 库，Sparkle 不在此）
   - `@loader_path`（指向 `MacCortex.app/Contents/MacOS/`）
   - Xcode toolchain 路径
3. Sparkle.framework 实际位置：`MacCortex.app/Contents/Frameworks/`
4. **缺失**: `@loader_path/../Frameworks`（从 MacOS/ 到 Frameworks/ 的相对路径）

**dyld 搜索路径逻辑**:
```
@rpath/Sparkle.framework/Versions/B/Sparkle 展开为:
1. /usr/lib/swift/Sparkle.framework/Versions/B/Sparkle（不存在）
2. @loader_path/Sparkle.framework/Versions/B/Sparkle
   → MacCortex.app/Contents/MacOS/Sparkle.framework/...（不存在）
3. Xcode toolchain 路径/Sparkle.framework/...（不存在）

❌ 所有路径尝试失败 → dyld 错误 → 应用崩溃
```

---

## 三、解决方案

### 3.1 修复方法

**方案**: 修改 `Scripts/build-app.sh`，在 SPM 构建时添加链接器标志

#### 修改 1: 添加 linker 标志（Line 45-55）

**之前**:
```bash
if [ "$BUILD_CONFIG" = "release" ]; then
    swift build --configuration release
    echo "  ✓ Release 构建完成"
else
    swift build --configuration debug
    echo "  ✓ Debug 构建完成"
fi
```

**之后**:
```bash
# 添加 linker 标志以设置正确的 @rpath
LINKER_FLAGS="-Xlinker -rpath -Xlinker @loader_path/../Frameworks"

if [ "$BUILD_CONFIG" = "release" ]; then
    swift build --configuration release $LINKER_FLAGS
    echo "  ✓ Release 构建完成（已配置 @rpath）"
else
    swift build --configuration debug $LINKER_FLAGS
    echo "  ✓ Debug 构建完成（已配置 @rpath）"
fi
```

#### 修改 2: 添加 @rpath 验证步骤（Line 84-94）

**新增**:
```bash
# Step 6.5: 验证 @rpath 配置
echo ""
echo -e "${YELLOW}[验证]${NC} 检查 @rpath 配置..."
if otool -l "$APP_BUNDLE/Contents/MacOS/$APP_NAME" | grep -q "@loader_path/../Frameworks"; then
    echo "  ✓ @rpath 配置正确"
else
    echo -e "  ${RED}✗ @rpath 配置缺失！${NC}"
    echo "  正在添加 @rpath..."
    install_name_tool -add_rpath "@loader_path/../Frameworks" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
    echo "  ✓ @rpath 已修复"
fi
```

**作用**:
- 构建后自动验证 @rpath
- 如果缺失，使用 `install_name_tool` 修复
- 提供双重保障（构建时 + 构建后）

---

### 3.2 修复步骤

```bash
# 1. 修改构建脚本
# （已通过 Edit tool 完成）

# 2. 重新构建应用
./Scripts/build-app.sh
# 输出: ✓ @rpath 配置正确

# 3. 验证 @rpath
otool -l build/MacCortex.app/Contents/MacOS/MacCortex | grep -A 2 "LC_RPATH"
# 现在包含: @loader_path/../Frameworks

# 4. 重新签名
source Configs/developer-config.env && ./Scripts/sign.sh
# 输出: ✅ 签名验证成功

# 5. 重新公证
./Scripts/notarize.sh
# Submission ID: 8b695834-10e6-40b8-a102-8dbe605f2989
# 状态: Accepted

# 6. 测试应用启动
open build/MacCortex.app
ps aux | grep MacCortex.app
# 输出: MacCortex 进程正在运行 ✅
```

---

## 四、验证结果

### 4.1 @rpath 配置验证

**命令**:
```bash
otool -l build/MacCortex.app/Contents/MacOS/MacCortex | grep -A 2 "LC_RPATH"
```

**结果**: ✅ 包含所有必需的 @rpath
```
LC_RPATH
  path /usr/lib/swift
LC_RPATH
  path @loader_path
LC_RPATH
  path /Applications/Xcode.app/.../swift-6.2/macosx
LC_RPATH
  path @loader_path/../Frameworks  # ← 已添加！
```

### 4.2 应用启动验证

**命令**:
```bash
open build/MacCortex.app
ps aux | grep MacCortex.app | grep -v grep
```

**结果**: ✅ 应用成功启动
```
jamesg  47768  0.0  0.4 435700608 108896  ??  S  8:54PM  0:00.20 /Users/jamesg/projects/MacCortex/build/MacCortex.app/Contents/MacOS/MacCortex
```

### 4.3 Gatekeeper 验证

**命令**:
```bash
spctl --assess --type execute build/MacCortex.app
```

**结果**: ✅ 已通过
```
build/MacCortex.app: accepted
source=Notarized Developer ID
origin=Developer ID Application: INNORA INFORMATION TECHNOLOGY PTE. LTD. (CSRKUK3CQV)
```

### 4.4 公证记录

**Submission ID**: `8b695834-10e6-40b8-a102-8dbe605f2989`
**状态**: **Accepted**
**处理时间**: ~2 分钟

---

## 五、影响评估

### 5.1 受影响范围

- **组件**: MacCortex.app（主应用）
- **依赖**: Sparkle.framework
- **影响用户**: 所有使用 Phase 0.5 构建的用户（100%）
- **发生时间**: Day 10 Sparkle 集成后

### 5.2 临时方案（已废弃）

**尝试 1**: 使用 `install_name_tool` 直接修改已签名的应用
- **结果**: 失败（权限错误，签名失效）

**最终方案**: 修改构建脚本 + 重新构建 + 重新签名 + 重新公证
- **结果**: ✅ 成功

---

## 六、经验教训

### 6.1 问题根源

1. **构建脚本不完整**: `build-app.sh` 未设置 `@rpath`
2. **验证不足**: 构建后未检查动态链接配置
3. **集成测试缺失**: Day 10 完成后未测试应用启动

### 6.2 改进措施

#### 改进 1: 构建脚本增强 ✅
- 添加 linker 标志设置 `@rpath`
- 添加构建后 `@rpath` 验证
- 自动修复机制（使用 `install_name_tool`）

#### 改进 2: 验收标准增强（建议）
- P0-5（Sparkle 检测更新）应包含：**应用能够正常启动**
- 添加启动测试：`open build/MacCortex.app && sleep 3 && ps aux | grep MacCortex`

#### 改进 3: 文档更新
- ✅ 创建 BUGFIX-rpath.md（本文档）
- ⏳ 更新 Day10-Verification-Report.md（添加此 bug 记录）
- ⏳ 更新 Phase-0.5-Summary.md（Known Issues 章节）

---

## 七、相关资料

### 7.1 技术文档

- [Apple: Dynamic Library Programming Topics - Runtime Search Paths](https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/DynamicLibraries/100-Articles/RunpathDependentLibraries.html)
- [otool man page](https://www.manpagez.com/man/1/otool/)
- [install_name_tool man page](https://www.manpagez.com/man/1/install_name_tool/)

### 7.2 类似问题

- [Stack Overflow: dyld: Library not loaded @rpath](https://stackoverflow.com/questions/33281233)
- [Sparkle Documentation: Embedding the Framework](https://sparkle-project.org/documentation/cocoapods/)

---

## 八、附录

### 8.1 完整 @rpath 配置

**正确的 @rpath 结构**（从 MacOS/ 目录视角）:
```
@loader_path/../Frameworks → MacCortex.app/Contents/Frameworks/
```

**dyld 搜索逻辑**（修复后）:
```
@rpath/Sparkle.framework/Versions/B/Sparkle 展开为:
1. /usr/lib/swift/Sparkle.framework/...（尝试）
2. @loader_path/Sparkle.framework/...（尝试）
3. Xcode toolchain/Sparkle.framework/...（尝试）
4. @loader_path/../Frameworks/Sparkle.framework/Versions/B/Sparkle
   → MacCortex.app/Contents/Frameworks/Sparkle.framework/...（✅ 找到！）
```

### 8.2 相关文件

- **修改**: `Scripts/build-app.sh`（Line 45-55, 84-94）
- **验证**: `build/MacCortex.app/Contents/MacOS/MacCortex`（@rpath）
- **依赖**: `build/MacCortex.app/Contents/Frameworks/Sparkle.framework`

---

**Bug Fix 完成时间**: 2026-01-20 20:55:00 +1300
**修复者**: Claude Code (Sonnet 4.5)
**验证者**: 用户（顶尖开发人员）
**状态**: ✅ **已修复并验证**
