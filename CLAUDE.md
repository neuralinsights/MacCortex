# MacCortex 项目记忆文件 (CLAUDE.md)

## 时间真实性校验记录

### 校验时间：2026-01-23 17:47:59 +13:00

- **本机系统时间与时区**：Asia/Auckland (NZDT, +13:00)
- **时间源 1**：
  - 来源/URL：本地系统 `date` 命令
  - 协议：系统调用
  - 返回示例：Fri Jan 23 17:47:59 NZDT 2026
  - 时间戳：2026-01-23 17:47:59 +13:00
- **时间源 2**：
  - 来源/URL：https://www.timeanddate.com
  - 协议：HTTPS-Header
  - 返回示例：date: Fri, 23 Jan 2026 04:47:59 GMT
  - 时间戳：2026-01-23 04:47:59 GMT (等价于 2026-01-23 17:47:59 +13:00)
- **最大偏差**：0 秒（阈值：100 秒）
- **判定**：✅ 通过
- **备注**：用于后续所有检索记录与日志的"基准时间锚点"

---

## 项目基础信息

- **项目名称**：MacCortex
- **当前版本**：0.5.0 (Build 1)
- **Bundle ID**：com.maccortex.app
- **Team ID**：CSRKUK3CQV
- **主要语言**：Swift
- **平台**：macOS 26.2+ (ARM64)
- **项目路径**：/Users/jamesg/projects/MacCortex

---

## 当前紧急问题

### ✅ 已解决：Sparkle.framework 加载失败（2026-01-23 20:29 +13:00）

#### 问题描述
应用启动时崩溃，错误信息：
```
Library not loaded: @rpath/Sparkle.framework/Versions/B/Sparkle
Termination Reason: Namespace DYLD, Code 1, Library missing
```

#### 根因分析
1. **直接原因**：Sparkle.framework 的 install_name 未正确设置为 `@rpath` 格式
2. **技术细节**：虽然 framework 已复制到 `Contents/Frameworks/`，且 rpath 包含 `@loader_path/../Frameworks`，但 framework 内部的 dylib ID 不匹配
3. **影响范围**：应用完全无法启动

#### 解决方案
1. **临时修复**：使用 `install_name_tool -id "@rpath/Sparkle.framework/Versions/B/Sparkle"` 修复现有构建
2. **永久修复**：更新 `Scripts/build-app-bundle.sh`，在复制 framework 后自动修复 install_name
3. **验证**：应用成功启动（PID 86806），无崩溃

#### 修改文件
- `Scripts/build-app-bundle.sh`: 添加 install_name_tool 修复步骤（+8 行）

---

## 证据清单

（待补充）

---

## 特例登记

（待补充）

---

## 冗余治理报告

（待补充）
