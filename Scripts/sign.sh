#!/bin/bash
# MacCortex 代码签名脚本
# Phase 0.5 - Day 3
# 创建时间：2026-01-20 (基于时间校验记录 #20260120-01)

set -euo pipefail

# 配置变量
APP_PATH="${1:-build/MacCortex.app}"
DEVELOPER_ID="${DEVELOPER_ID:-Developer ID Application: Your Name (TEAM_ID)}"
ENTITLEMENTS="Resources/Entitlements/MacCortex.entitlements"

# 检查 Developer ID 配置
if [[ "$DEVELOPER_ID" == *"Your Name"* ]] || [[ "$DEVELOPER_ID" == *"TEAM_ID"* ]]; then
    echo "❌ 错误: Developer ID 未配置"
    echo ""
    echo "请按以下步骤配置："
    echo ""
    echo "1. 申请 Apple Developer Program ($99/年)"
    echo "   https://developer.apple.com/account"
    echo ""
    echo "2. 下载 Developer ID Application 证书"
    echo "   Xcode → Settings → Accounts → Manage Certificates"
    echo ""
    echo "3. 查找您的 Team ID:"
    echo "   https://developer.apple.com/account → Membership Details"
    echo ""
    echo "4. 设置环境变量（添加到 ~/.zshrc 或 ~/.bashrc）:"
    echo "   export DEVELOPER_ID=\"Developer ID Application: Your Name (YOUR_TEAM_ID)\""
    echo ""
    echo "5. 验证证书可用:"
    echo "   security find-identity -v -p codesigning | grep 'Developer ID Application'"
    echo ""
    exit 1
fi

echo "================================================"
echo "MacCortex 代码签名流程"
echo "================================================"
echo "应用路径: $APP_PATH"
echo "签名身份: $DEVELOPER_ID"
echo "Entitlements: $ENTITLEMENTS"
echo ""

# 检查应用是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "错误: 应用不存在于 $APP_PATH"
    exit 1
fi

# 检查 Entitlements 文件
if [ ! -f "$ENTITLEMENTS" ]; then
    echo "错误: Entitlements 文件不存在于 $ENTITLEMENTS"
    exit 1
fi

# 签名顺序：XPC Services → Frameworks → App
echo "步骤 1/3: 签名 XPC Services..."
if [ -d "${APP_PATH}/Contents/XPCServices" ]; then
    shopt -s nullglob  # 如果没有匹配项，glob 返回空
    for xpc in "${APP_PATH}"/Contents/XPCServices/*.xpc; do
        echo "  - 签名 $(basename "$xpc")"
        codesign --force --sign "$DEVELOPER_ID" \
                 --options runtime \
                 --timestamp \
                 "$xpc"
    done
    shopt -u nullglob
fi
if [ ! -d "${APP_PATH}/Contents/XPCServices" ] || [ -z "$(ls -A "${APP_PATH}/Contents/XPCServices" 2>/dev/null)" ]; then
    echo "  ⚠️  无 XPC Services（跳过）"
fi

echo ""
echo "步骤 2/3: 签名 Frameworks..."
if [ -d "${APP_PATH}/Contents/Frameworks" ]; then
    shopt -s nullglob
    for framework in "${APP_PATH}"/Contents/Frameworks/*.framework; do
        echo "  - 签名 $(basename "$framework")"
        codesign --force --sign "$DEVELOPER_ID" \
                 --options runtime \
                 --timestamp \
                 "$framework"
    done
    shopt -u nullglob
fi

echo ""
echo "步骤 3/3: 签名主应用..."
codesign --force --sign "$DEVELOPER_ID" \
         --entitlements "$ENTITLEMENTS" \
         --options runtime \
         --timestamp \
         --deep \
         "$APP_PATH"

echo ""
echo "================================================"
echo "验证签名..."
echo "================================================"

# 验证签名
if codesign --verify --deep --strict "$APP_PATH"; then
    echo "✅ 签名验证成功"
else
    echo "❌ 签名验证失败"
    exit 1
fi

# Gatekeeper 检查
echo ""
echo "Gatekeeper 评估..."
if spctl --assess --type execute "$APP_PATH" 2>&1; then
    echo "✅ Gatekeeper 通过"
else
    echo "⚠️  Gatekeeper 评估失败（公证后会通过）"
fi

echo ""
echo "================================================"
echo "签名完成！"
echo "================================================"
echo "下一步: 运行 ./Scripts/notarize.sh 进行公证"
