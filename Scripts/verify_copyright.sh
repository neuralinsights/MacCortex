#!/bin/bash
# MacCortex 版权验证脚本
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# 用途：验证所有源代码文件是否包含正确的版权声明

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="/Users/jamesg/projects/MacCortex"
OWNER="Yu Geng"
EMAIL="james.geng@gmail.com"

echo ""
echo "======================================================================"
echo "  MacCortex 版权验证工具"
echo "  Copyright (c) 2026 Yu Geng"
echo "======================================================================"
echo ""

# 计数器
total_files=0
valid_files=0
invalid_files=0

# 验证 Python 文件
echo "📝 检查 Python 文件..."
echo ""

for file in $(find "$PROJECT_ROOT/Backend/src" -name "*.py" -not -path "*/.*"); do
    total_files=$((total_files + 1))

    if grep -q "Copyright (c) 2026 Yu Geng" "$file"; then
        echo -e "${GREEN}✓${NC} $(basename "$file")"
        valid_files=$((valid_files + 1))
    else
        echo -e "${RED}✗${NC} $(basename "$file") - 缺少版权声明"
        invalid_files=$((invalid_files + 1))
    fi
done

echo ""
echo "📱 检查 Swift 文件..."
echo ""

for file in $(find "$PROJECT_ROOT/Sources" -name "*.swift" -not -path "*/.*"); do
    total_files=$((total_files + 1))

    if grep -q "Copyright (c) 2026 Yu Geng" "$file"; then
        echo -e "${GREEN}✓${NC} $(basename "$file")"
        valid_files=$((valid_files + 1))
    else
        echo -e "${RED}✗${NC} $(basename "$file") - 缺少版权声明"
        invalid_files=$((invalid_files + 1))
    fi
done

echo ""
echo "📄 检查关键文档..."
echo ""

# 检查 LICENSE 文件
if [ -f "$PROJECT_ROOT/LICENSE" ]; then
    if grep -q "Yu Geng" "$PROJECT_ROOT/LICENSE"; then
        echo -e "${GREEN}✓${NC} LICENSE"
        valid_files=$((valid_files + 1))
    else
        echo -e "${RED}✗${NC} LICENSE - 缺少所有者信息"
        invalid_files=$((invalid_files + 1))
    fi
    total_files=$((total_files + 1))
else
    echo -e "${RED}✗${NC} LICENSE - 文件不存在"
    invalid_files=$((invalid_files + 1))
    total_files=$((total_files + 1))
fi

# 检查 COPYRIGHT.md 文件
if [ -f "$PROJECT_ROOT/COPYRIGHT.md" ]; then
    if grep -q "Yu Geng" "$PROJECT_ROOT/COPYRIGHT.md"; then
        echo -e "${GREEN}✓${NC} COPYRIGHT.md"
        valid_files=$((valid_files + 1))
    else
        echo -e "${RED}✗${NC} COPYRIGHT.md - 缺少所有者信息"
        invalid_files=$((invalid_files + 1))
    fi
    total_files=$((total_files + 1))
else
    echo -e "${RED}✗${NC} COPYRIGHT.md - 文件不存在"
    invalid_files=$((invalid_files + 1))
    total_files=$((total_files + 1))
fi

echo ""
echo "🔍 验证水印模块..."
echo ""

# 检查 Python 水印模块
if [ -f "$PROJECT_ROOT/Backend/src/utils/watermark.py" ]; then
    if grep -q "_PROJECT_WATERMARK" "$PROJECT_ROOT/Backend/src/utils/watermark.py" && \
       grep -q "Yu Geng" "$PROJECT_ROOT/Backend/src/utils/watermark.py"; then
        echo -e "${GREEN}✓${NC} Python 水印模块完整"
        valid_files=$((valid_files + 1))
    else
        echo -e "${RED}✗${NC} Python 水印模块不完整"
        invalid_files=$((invalid_files + 1))
    fi
    total_files=$((total_files + 1))
else
    echo -e "${RED}✗${NC} Python 水印模块不存在"
    invalid_files=$((invalid_files + 1))
    total_files=$((total_files + 1))
fi

# 检查 Swift 水印模块
if [ -f "$PROJECT_ROOT/Sources/MacCortexApp/Watermark.swift" ]; then
    if grep -q "MacCortexWatermark" "$PROJECT_ROOT/Sources/MacCortexApp/Watermark.swift" && \
       grep -q "Yu Geng" "$PROJECT_ROOT/Sources/MacCortexApp/Watermark.swift"; then
        echo -e "${GREEN}✓${NC} Swift 水印模块完整"
        valid_files=$((valid_files + 1))
    else
        echo -e "${RED}✗${NC} Swift 水印模块不完整"
        invalid_files=$((invalid_files + 1))
    fi
    total_files=$((total_files + 1))
else
    echo -e "${RED}✗${NC} Swift 水印模块不存在"
    invalid_files=$((invalid_files + 1))
    total_files=$((total_files + 1))
fi

echo ""
echo "======================================================================"
echo "  验证总结"
echo "======================================================================"
echo ""
echo "总文件数:   $total_files"
echo -e "有效文件:   ${GREEN}$valid_files${NC}"
echo -e "无效文件:   ${RED}$invalid_files${NC}"
echo ""

# 计算通过率
pass_rate=$(awk "BEGIN {printf \"%.1f\", ($valid_files/$total_files)*100}")
echo "通过率:     ${pass_rate}%"
echo ""

# 最终判定
if [ $invalid_files -eq 0 ]; then
    echo -e "${GREEN}✅ 所有版权声明完整！项目已受保护。${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 发现 $invalid_files 个文件缺少版权声明！${NC}"
    echo -e "${YELLOW}⚠️  请立即修复以确保项目版权保护。${NC}"
    echo ""
    exit 1
fi
