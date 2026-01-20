# MacCortex 版权保护使用指南

**Copyright (c) 2026 Yu Geng**
**最后更新**: 2026-01-21

---

## 🎯 概述

MacCortex 已集成完整的版权保护机制，包括：

1. ✅ **版权声明**：所有源代码文件包含版权头
2. ✅ **专有许可证**：Proprietary License 限制未授权使用
3. ✅ **隐藏水印**：代码中嵌入所有者标识
4. ✅ **完整性验证**：自动检测篡改和调试
5. ✅ **验证工具**：一键检查所有版权标识

---

## 📋 已实施的保护措施

### 1. 版权声明（32 个文件）

所有源代码文件已添加版权头：

**Python 文件** (12 个):
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential
```

**Swift 文件** (16 个):
```swift
//
// MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
// Copyright (c) 2026 Yu Geng. All rights reserved.
//
// This source code is proprietary and confidential.
// Unauthorized copying, distribution, or use is strictly prohibited.
//
// Author: Yu Geng <james.geng@gmail.com>
// License: Proprietary
//
```

### 2. 项目元数据

在 `Backend/src/main.py` 中：

```python
__author__ = "Yu Geng"
__copyright__ = "Copyright 2026, Yu Geng"
__license__ = "Proprietary"
__version__ = "1.0.0"
__maintainer__ = "Yu Geng"
__email__ = "james.geng@gmail.com"
__status__ = "Production"

# Project watermark (DO NOT REMOVE)
_PROJECT_ID = "MacCortex-YG-2026-0121-PROD"
_OWNER_HASH = "8f3b5c7a9e1d2f4b6a8c0e3f5d7b9a1c3e5f7d9b"
```

### 3. 隐藏水印系统

#### Python 水印模块
**文件**: `Backend/src/utils/watermark.py`

**功能**:
- 所有权验证 (`verify_ownership()`)
- 完整性检查 (`check_integrity()`)
- 环境验证 (`verify_environment()`)
- 隐藏标识符（SHA-256 哈希）

**使用示例**:
```python
from utils.watermark import verify_ownership, get_project_info

# 验证所有权
if verify_ownership():
    print("✅ 项目所有权验证通过")

# 获取项目信息
info = get_project_info()
print(f"项目ID: {info['watermark']}")
```

#### Swift 水印模块
**文件**: `Sources/MacCortexApp/Watermark.swift`

**功能**:
- 所有权验证 (`MacCortexWatermark.verifyOwnership()`)
- 应用完整性检查 (`checkIntegrity()`)
- 反调试检测 (`verifyEnvironment()`)
- 启动时自动验证 (`performStartupVerification()`)

**使用示例**:
```swift
import Foundation

// 应用启动时调用
MacCortexWatermark.performStartupVerification()

// 调试信息（Debug 模式）
#if DEBUG
MacCortexWatermark.debugInfo()
#endif

// 获取项目信息
let info = MacCortexWatermark.getProjectInfo()
print("项目ID: \(info["watermark"] ?? "Unknown")")
```

### 4. API 版权端点

**URL**: `http://127.0.0.1:8000/copyright`

**响应示例**:
```json
{
  "copyright": "Copyright (c) 2026 Yu Geng. All rights reserved.",
  "project": "MacCortex - Next-Generation macOS Personal Intelligence Infrastructure",
  "owner": "Yu Geng",
  "email": "james.geng@gmail.com",
  "license": "Proprietary",
  "watermark": "MacCortex-YG-2026-0121-PROD",
  "verified": true,
  "warning": "This software is proprietary and confidential. Unauthorized use is prohibited."
}
```

### 5. 法律文档

- **LICENSE**: 专有许可证，禁止未授权使用
- **COPYRIGHT.md**: 完整版权声明与侵权责任

---

## 🔧 使用工具

### 版权验证脚本

**位置**: `Scripts/verify_copyright.sh`

**功能**:
- 检查所有 Python 和 Swift 文件的版权声明
- 验证 LICENSE 和 COPYRIGHT.md 文件
- 检查水印模块完整性
- 生成验证报告

**使用方法**:
```bash
cd /Users/jamesg/projects/MacCortex
./Scripts/verify_copyright.sh
```

**输出示例**:
```
======================================================================
  MacCortex 版权验证工具
  Copyright (c) 2026 Yu Geng
======================================================================

📝 检查 Python 文件...
✓ main.py
✓ watermark.py
...

📱 检查 Swift 文件...
✓ Watermark.swift
...

======================================================================
  验证总结
======================================================================

总文件数:   32
有效文件:   32
无效文件:   0

通过率:     100.0%

✅ 所有版权声明完整！项目已受保护。
```

---

## 🛡️ 安全特性

### 1. 反调试检测

**Python**:
```python
# 自动执行（模块导入时）
from utils.watermark import verify_environment

if not verify_environment():
    # 检测到调试器，可以采取措施
    pass
```

**Swift**:
```swift
// 检测调试器
if !MacCortexWatermark.verifyEnvironment() {
    // 检测到调试器
    #if DEBUG
    print("⚠️ 调试器已检测到")
    #endif
}
```

### 2. 完整性验证

**自动验证**:
- Python 后端启动时自动验证
- Swift 应用启动时调用 `performStartupVerification()`

**手动验证**:
```bash
# Python 验证
cd Backend/src
python -c "from utils.watermark import verify_ownership, check_integrity; \
           print('所有权:', verify_ownership()); \
           print('完整性:', check_integrity())"

# Swift 验证（在 Xcode 中运行）
MacCortexWatermark.debugInfo()
```

### 3. 隐藏标识符

每个关键模块包含隐藏的所有者哈希：

```python
# Python
_OWNER_HASH = "8f3b5c7a9e1d2f4b6a8c0e3f5d7b9a1c3e5f7d9b"

# 十六进制编码的水印
_obfuscated_data = bytes.fromhex(
    "4d6163436f7274657820436f7079726967687420323032362059752047656e67"
)  # "MacCortex Copyright 2026 Yu Geng"
```

---

## 📝 维护指南

### 添加新文件时

**Python 文件**:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yu Geng. All rights reserved.
# MacCortex - Proprietary and Confidential

"""
文件描述
"""

__author__ = "Yu Geng"
__copyright__ = "Copyright 2026, Yu Geng"
__license__ = "Proprietary"
```

**Swift 文件**:
```swift
//
// MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
// Copyright (c) 2026 Yu Geng. All rights reserved.
//
// This source code is proprietary and confidential.
// Unauthorized copying, distribution, or use is strictly prohibited.
//
// Author: Yu Geng <james.geng@gmail.com>
// License: Proprietary
//

import Foundation

// 你的代码...
```

### 定期验证

**建议**：每次 Git 提交前运行验证脚本

```bash
# 添加到 Git pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
./Scripts/verify_copyright.sh
if [ $? -ne 0 ]; then
    echo "❌ 版权验证失败，提交被阻止"
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

---

## ⚖️ 法律保护

### 已实施的法律措施

1. ✅ **版权声明**: 所有文件包含 "Copyright (c) 2026 Yu Geng"
2. ✅ **专有许可证**: LICENSE 文件明确禁止未授权使用
3. ✅ **版权文档**: COPYRIGHT.md 详细说明权利与责任

### 待申请的法律保护

- [ ] **软件著作权登记**（中国版权保护中心）
  - 预计费用: ¥300
  - 预计时间: 30-60 个工作日
  - 材料: 源代码前后各 30 页 + 说明书

- [ ] **商标注册**（"MacCortex"）
  - 预计费用: ¥900（3 个类别）
  - 预计时间: 9-12 个月

- [ ] **专利申请**（可选）
  - 发明专利: Swarm Intelligence 融合架构
  - 预计费用: ¥8,000
  - 预计时间: 12-18 个月

---

## 🚨 侵权应对

### 如果发现代码被盗用

1. **收集证据**
   - 截图保存侵权页面
   - 使用 Web Archive 存档：`curl -X POST https://web.archive.org/save/[URL]`
   - 下载侵权代码：`git clone [侵权仓库]`
   - 运行验证脚本，证明你的代码包含水印

2. **对比水印**
   ```bash
   # 你的代码
   grep -r "_PROJECT_ID.*MacCortex-YG-2026" Backend/src/

   # 侵权代码（如果有）
   grep -r "_PROJECT_ID.*MacCortex-YG-2026" [侵权代码路径]/
   ```

3. **发送 DMCA 下架请求**（GitHub/GitLab）
   - 模板：https://github.com/github/dmca

4. **法律行动**
   - 联系知识产权律师
   - 民事索赔：停止侵权 + 赔偿损失
   - 刑事报案：侵犯著作权罪（价值 > 5 万元）

---

## 📞 联系信息

**项目所有者**: Yu Geng
**邮箱**: james.geng@gmail.com
**项目**: MacCortex - Next-Generation macOS Personal Intelligence Infrastructure

**商业授权咨询**:
如需商业使用 MacCortex 或获取技术支持，请通过上述邮箱联系。

---

## 📊 保护状态

| 保护措施 | 状态 | 完成日期 |
|----------|------|----------|
| 版权声明（所有文件） | ✅ 完成 | 2026-01-21 |
| 专有许可证 (LICENSE) | ✅ 完成 | 2026-01-21 |
| 版权文档 (COPYRIGHT.md) | ✅ 完成 | 2026-01-21 |
| Python 水印系统 | ✅ 完成 | 2026-01-21 |
| Swift 水印系统 | ✅ 完成 | 2026-01-21 |
| API 版权端点 | ✅ 完成 | 2026-01-21 |
| 验证脚本 | ✅ 完成 | 2026-01-21 |
| 软件著作权登记 | ⏰ 待办 | - |
| 商标注册 | ⏰ 待办 | - |
| 专利申请 | ⏰ 待办 | - |

---

**最后更新**: 2026-01-21
**验证状态**: ✅ 100% 完整（32/32 文件通过验证）
**保护等级**: 🔒 高（代码级 + 法律级）
