#!/bin/bash
# MacCortex 公证脚本
# Phase 0.5 - Day 4
# 创建时间：2026-01-20 (基于时间校验记录 #20260120-01)

set -euo pipefail

# 配置变量
APP_PATH="${1:-build/MacCortex.app}"
ZIP_PATH="build/MacCortex.zip"
KEYCHAIN_PROFILE="${KEYCHAIN_PROFILE:-notarytool-profile}"

echo "================================================"
echo "MacCortex 公证流程"
echo "================================================"
echo "应用路径: $APP_PATH"
echo "ZIP 路径: $ZIP_PATH"
echo "Keychain Profile: $KEYCHAIN_PROFILE"
echo ""

# 检查应用是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "错误: 应用不存在于 $APP_PATH"
    echo "提示: 请先运行 ./Scripts/sign.sh"
    exit 1
fi

# 检查应用是否已签名
echo "验证签名状态..."
if ! codesign --verify --deep --strict "$APP_PATH" 2>/dev/null; then
    echo "错误: 应用未签名或签名无效"
    echo "提示: 请先运行 ./Scripts/sign.sh"
    exit 1
fi
echo "✅ 签名有效"
echo ""

# 创建 ZIP 归档（公证需要）
echo "步骤 1/3: 创建 ZIP 归档..."
rm -f "$ZIP_PATH"
ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"
echo "✅ ZIP 创建成功: $ZIP_PATH"
echo ""

# 提交公证
echo "步骤 2/3: 提交公证请求..."
echo "注意: 公证通常需要 2-10 分钟，请耐心等待"
echo ""

if xcrun notarytool submit "$ZIP_PATH" \
    --keychain-profile "$KEYCHAIN_PROFILE" \
    --wait; then
    echo "✅ 公证成功"
else
    echo "❌ 公证失败"
    echo ""
    echo "故障排查建议："
    echo "1. 检查 Keychain Profile 配置："
    echo "   xcrun notarytool store-credentials $KEYCHAIN_PROFILE"
    echo "2. 查看公证日志："
    echo "   xcrun notarytool log <submission-id> --keychain-profile $KEYCHAIN_PROFILE"
    echo "3. 常见失败原因："
    echo "   - Hardened Runtime 未启用"
    echo "   - Entitlements 配置错误"
    echo "   - 签名身份不正确"
    exit 1
fi

echo ""
echo "步骤 3/3: Staple 票据..."
if xcrun stapler staple "$APP_PATH"; then
    echo "✅ Staple 成功"
else
    echo "⚠️  Staple 失败（应用仍可用，但需联网验证）"
fi

echo ""
echo "================================================"
echo "验证公证状态..."
echo "================================================"

if xcrun stapler validate "$APP_PATH"; then
    echo "✅ 公证票据验证成功"
    echo ""
    echo "🎉 恭喜！应用已完成签名和公证"
    echo "   可以安全分发给用户"
else
    echo "⚠️  未检测到离线票据（在线验证仍可用）"
fi

echo ""
echo "================================================"
echo "最终 Gatekeeper 检查..."
echo "================================================"
spctl --assess --type execute -vv "$APP_PATH" || true

echo ""
echo "================================================"
echo "公证完成！"
echo "================================================"
echo "下一步: 创建 DMG 安装包"
echo "  ./Scripts/build-dmg.sh"
