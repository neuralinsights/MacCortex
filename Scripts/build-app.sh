#!/bin/bash
# MacCortex 应用构建脚本
# Phase 0.5 Day 2
# 创建时间: 2026-01-20
#
# 功能：
# 1. 使用 Swift Package Manager 构建可执行文件
# 2. 创建 .app bundle 结构
# 3. 复制资源、框架和 Info.plist
# 4. 准备签名（Day 3 执行）

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="MacCortex"
BUILD_CONFIG="${BUILD_CONFIG:-debug}"
BUILD_DIR="${PROJECT_ROOT}/.build/${BUILD_CONFIG}"
OUTPUT_DIR="${PROJECT_ROOT}/build"
APP_BUNDLE="${OUTPUT_DIR}/${APP_NAME}.app"

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}MacCortex 应用构建脚本（Phase 0.5 Day 2）${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Step 1: 清理旧的构建产物
echo -e "${YELLOW}[1/6]${NC} 清理旧的构建产物..."
if [ -d "$APP_BUNDLE" ]; then
    rm -rf "$APP_BUNDLE"
    echo "  ✓ 已删除旧的 .app bundle"
fi
mkdir -p "$OUTPUT_DIR"

# Step 2: Swift Package Manager 构建
echo -e "${YELLOW}[2/6]${NC} 使用 SPM 构建可执行文件..."
cd "$PROJECT_ROOT"

# 添加 linker 标志以设置正确的 @rpath
LINKER_FLAGS="-Xlinker -rpath -Xlinker @loader_path/../Frameworks"

if [ "$BUILD_CONFIG" = "release" ]; then
    swift build --configuration release $LINKER_FLAGS
    echo "  ✓ Release 构建完成（已配置 @rpath）"
else
    swift build --configuration debug $LINKER_FLAGS
    echo "  ✓ Debug 构建完成（已配置 @rpath）"
fi

# Step 3: 创建 .app bundle 结构
echo -e "${YELLOW}[3/6]${NC} 创建 .app bundle 结构..."
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"
mkdir -p "$APP_BUNDLE/Contents/Frameworks"
echo "  ✓ .app 目录结构已创建"

# Step 4: 复制可执行文件
echo -e "${YELLOW}[4/6]${NC} 复制可执行文件..."
cp "$BUILD_DIR/$APP_NAME" "$APP_BUNDLE/Contents/MacOS/"
chmod +x "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
echo "  ✓ 可执行文件已复制: $(ls -lh "$APP_BUNDLE/Contents/MacOS/$APP_NAME" | awk '{print $5}')"

# Step 5: 复制 Info.plist
echo -e "${YELLOW}[5/6]${NC} 复制 Info.plist..."
if [ -f "$PROJECT_ROOT/Resources/Info.plist" ]; then
    cp "$PROJECT_ROOT/Resources/Info.plist" "$APP_BUNDLE/Contents/"
    echo "  ✓ Info.plist 已复制"
else
    echo -e "  ${RED}✗ Info.plist 未找到: $PROJECT_ROOT/Resources/Info.plist${NC}"
    exit 1
fi

# Step 6: 复制 Sparkle 框架
echo -e "${YELLOW}[6/6]${NC} 复制 Sparkle.framework..."
if [ -d "$BUILD_DIR/Sparkle.framework" ]; then
    cp -R "$BUILD_DIR/Sparkle.framework" "$APP_BUNDLE/Contents/Frameworks/"
    echo "  ✓ Sparkle.framework 已复制: $(du -sh "$APP_BUNDLE/Contents/Frameworks/Sparkle.framework" | awk '{print $1}')"
else
    echo -e "  ${YELLOW}⚠ Sparkle.framework 未找到（正常，将在 Day 10 集成）${NC}"
fi

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

# 验证 .app bundle 结构
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✅ .app bundle 构建成功！${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "输出路径: $APP_BUNDLE"
echo ""
echo "结构预览:"
tree -L 3 "$APP_BUNDLE" 2>/dev/null || find "$APP_BUNDLE" -maxdepth 3 -print | sed 's|[^/]*/| |g'
echo ""

# 显示构建信息
echo "构建信息："
echo "  - 配置: $BUILD_CONFIG"
echo "  - 可执行文件大小: $(ls -lh "$APP_BUNDLE/Contents/MacOS/$APP_NAME" | awk '{print $5}')"
echo "  - Bundle 总大小: $(du -sh "$APP_BUNDLE" | awk '{print $1}')"
echo ""

# 检查当前签名状态（未签名）
echo "当前签名状态:"
codesign -dvvv "$APP_BUNDLE" 2>&1 | grep -E "Authority|Identifier|TeamIdentifier" || echo "  ⚠️  未签名（将在 Day 3 签名）"
echo ""

# 下一步提示
echo -e "${BLUE}下一步：${NC}"
echo "  1. 检查 .app 结构是否正确"
echo "  2. 验证 Info.plist 内容"
echo "  3. Day 3: 运行 ./Scripts/sign.sh 进行签名"
echo ""
echo -e "${GREEN}Day 2 任务 1/2 完成 ✅${NC}"
echo ""
