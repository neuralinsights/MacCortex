#!/bin/bash
# MacCortex 环境配置验证脚本
# Phase 0.5
# 创建时间: 2026-01-20

set -e

echo "=========================================="
echo "MacCortex 环境配置验证"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
FAILURES=0

# 检查函数
check() {
    local name="$1"
    local command="$2"
    local expected="$3"

    echo -n "检查 $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((SUCCESS++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        if [ -n "$expected" ]; then
            echo "   期望: $expected"
        fi
        ((FAILURES++))
        return 1
    fi
}

check_warning() {
    local name="$1"
    local command="$2"
    local message="$3"

    echo -n "检查 $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((SUCCESS++))
        return 0
    else
        echo -e "${YELLOW}⚠️  警告${NC}"
        if [ -n "$message" ]; then
            echo "   提示: $message"
        fi
        ((WARNINGS++))
        return 1
    fi
}

echo "1. 检查基础环境"
echo "----------------------------------------"

# 检查 macOS 版本
check "macOS 版本" "sw_vers -productVersion | grep -E '1[4-9]\.|[2-9][0-9]\.'" "macOS 14.0+"

# 检查 Xcode
if [ -d "/Applications/Xcode.app" ]; then
    check "Xcode 安装" "test -d /Applications/Xcode.app"
    check "Xcode 版本" "xcodebuild -version | head -1" "Xcode 15.x+"
    check "Xcode 路径" "xcode-select -p | grep -q '/Applications/Xcode.app'" "/Applications/Xcode.app/Contents/Developer"
else
    echo -e "${RED}❌ Xcode 未安装${NC}"
    ((FAILURES++))
fi

echo ""
echo "2. 检查代码签名配置"
echo "----------------------------------------"

# 检查 Developer ID 证书
if security find-identity -v -p codesigning 2>&1 | grep -q "Developer ID Application"; then
    CERT_NAME=$(security find-identity -v -p codesigning 2>&1 | grep "Developer ID Application" | head -1 | sed 's/.*"\(.*\)"/\1/')
    echo -e "${GREEN}✅ Developer ID 证书已安装${NC}"
    echo "   证书: $CERT_NAME"
    ((SUCCESS++))

    # 提取 Team ID
    if echo "$CERT_NAME" | grep -q "CSRKUK3CQV"; then
        echo -e "${GREEN}✅ Team ID 匹配${NC}"
        echo "   Team ID: CSRKUK3CQV"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}⚠️  Team ID 不匹配${NC}"
        echo "   期望: CSRKUK3CQV"
        echo "   实际: $(echo "$CERT_NAME" | grep -o '([^)]*)' | tr -d '()')"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}❌ Developer ID 证书未找到${NC}"
    echo "   请申请 Developer ID Application 证书"
    echo "   指南: Docs/setup-checklist.md"
    ((FAILURES++))
fi

echo ""
echo "3. 检查公证配置"
echo "----------------------------------------"

# 检查 notarytool
check "notarytool 可用性" "which xcrun && xcrun notarytool --version"

# 检查 notarytool 凭证
check_warning "notarytool 凭证" "xcrun notarytool history --keychain-profile notarytool-profile 2>&1 | grep -qE 'No submissions|Date'" "运行: Docs/setup-checklist.md 步骤 3"

echo ""
echo "4. 检查项目文件"
echo "----------------------------------------"

check "Git 仓库" "test -d .git"
check "Package.swift" "test -f Package.swift"
check "Entitlements" "test -f Resources/Entitlements/MacCortex.entitlements"
check "Info.plist" "test -f Resources/Info.plist"
check "签名脚本" "test -x Scripts/sign.sh"
check "公证脚本" "test -x Scripts/notarize.sh"

echo ""
echo "5. 检查环境变量"
echo "----------------------------------------"

check_warning "DEVELOPER_ID" "test -n \"\$DEVELOPER_ID\"" "运行: source Configs/developer-config.env"
check_warning "APPLE_TEAM_ID" "test -n \"\$APPLE_TEAM_ID\" && [ \"\$APPLE_TEAM_ID\" = 'CSRKUK3CQV' ]" "运行: source Configs/developer-config.env"

echo ""
echo "=========================================="
echo "验证结果"
echo "=========================================="
echo -e "${GREEN}✅ 通过: $SUCCESS${NC}"
echo -e "${YELLOW}⚠️  警告: $WARNINGS${NC}"
echo -e "${RED}❌ 失败: $FAILURES${NC}"
echo ""

if [ $FAILURES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查通过！可以开始 Phase 0.5 Day 2-4 任务${NC}"
    exit 0
elif [ $FAILURES -eq 0 ]; then
    echo -e "${YELLOW}⚠️  有警告项，但可以继续${NC}"
    echo "建议完成所有配置以获得最佳体验"
    exit 0
else
    echo -e "${RED}❌ 有必需项未完成，请先完成配置${NC}"
    echo ""
    echo "下一步："
    echo "1. 查看 Docs/setup-checklist.md"
    echo "2. 完成缺失的配置项"
    echo "3. 重新运行此脚本: ./Scripts/verify-setup.sh"
    exit 1
fi
