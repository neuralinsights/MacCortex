#!/bin/bash
# MacCortex DMG 构建脚本
# Phase 0.5
# 创建时间：2026-01-20 (基于时间校验记录 #20260120-01)

set -euo pipefail

# 配置变量
APP_PATH="${1:-build/MacCortex.app}"
VERSION="${VERSION:-0.5.0}"
DMG_NAME="MacCortex-v${VERSION}.dmg"
VOLUME_NAME="MacCortex"

echo "================================================"
echo "MacCortex DMG 构建流程"
echo "================================================"
echo "应用路径: $APP_PATH"
echo "版本: $VERSION"
echo "DMG 名称: $DMG_NAME"
echo ""

# 检查应用是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "错误: 应用不存在于 $APP_PATH"
    exit 1
fi

# 创建临时目录
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

echo "步骤 1/2: 准备 DMG 内容..."
cp -R "$APP_PATH" "$TMP_DIR/"

# 创建 Applications 链接（方便拖拽安装）
ln -s /Applications "$TMP_DIR/Applications"

echo "✅ 内容准备完成"
echo ""

# 创建 DMG
echo "步骤 2/2: 创建 DMG..."
rm -f "build/$DMG_NAME"

hdiutil create \
    -volname "$VOLUME_NAME" \
    -srcfolder "$TMP_DIR" \
    -ov \
    -format UDZO \
    "build/$DMG_NAME"

echo "✅ DMG 创建成功: build/$DMG_NAME"
echo ""

echo "================================================"
echo "DMG 构建完成！"
echo "================================================"
echo "文件大小: $(du -h "build/$DMG_NAME" | cut -f1)"
echo ""
echo "下一步: 分发 DMG"
echo "  1. 测试安装: open build/$DMG_NAME"
echo "  2. 上传到服务器或 GitHub Release"
