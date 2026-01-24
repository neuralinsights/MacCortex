#!/bin/bash

# MacCortex .app Bundle 构建脚本
# Phase 2 Week 3 Day 13-14: Shortcuts 集成
# 创建时间：2026-01-21
#
# 将 SPM 构建的可执行文件打包成完整的 .app bundle（App Intents 需要）

set -e  # 遇到错误立即退出

# 配置
APP_NAME="MacCortex"
BUILD_DIR=".build/arm64-apple-macosx/debug"
APP_BUNDLE="${BUILD_DIR}/${APP_NAME}.app"
EXECUTABLE="${BUILD_DIR}/${APP_NAME}"
RESOURCES_DIR="Resources"

echo "=== MacCortex .app Bundle 构建 ==="
echo ""

# 1. 先构建可执行文件
echo "📦 步骤 1: 构建可执行文件..."
swift build
echo "✅ 构建完成"
echo ""

# 2. 创建 .app 目录结构
echo "📁 步骤 2: 创建 .app bundle 结构..."
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"
echo "✅ 目录结构已创建"
echo ""

# 3. 复制可执行文件
echo "🔧 步骤 3: 复制可执行文件..."
cp "${EXECUTABLE}" "${APP_BUNDLE}/Contents/MacOS/${APP_NAME}"
chmod +x "${APP_BUNDLE}/Contents/MacOS/${APP_NAME}"
# 添加 @loader_path/../Frameworks 到 rpath（Sparkle.framework 需要）
install_name_tool -add_rpath "@loader_path/../Frameworks" "${APP_BUNDLE}/Contents/MacOS/${APP_NAME}" 2>/dev/null || true
echo "✅ 可执行文件已复制"
echo ""

# 4. 复制 Info.plist
echo "📄 步骤 4: 复制 Info.plist..."
if [ -f "${RESOURCES_DIR}/Info.plist" ]; then
    cp "${RESOURCES_DIR}/Info.plist" "${APP_BUNDLE}/Contents/Info.plist"
    echo "✅ Info.plist 已复制"
else
    echo "❌ 错误：找不到 ${RESOURCES_DIR}/Info.plist"
    exit 1
fi
echo ""

# 5. 复制资源文件
echo "🎨 步骤 5: 复制资源文件..."
if [ -d "${BUILD_DIR}/MacCortex_MacCortexApp.bundle" ]; then
    cp -R "${BUILD_DIR}/MacCortex_MacCortexApp.bundle" "${APP_BUNDLE}/Contents/Resources/"
    echo "✅ 资源 bundle 已复制"
fi

# 复制其他资源文件（如图标、配置等）
if [ -d "${RESOURCES_DIR}/Config" ]; then
    mkdir -p "${APP_BUNDLE}/Contents/Resources/Config"
    cp -R "${RESOURCES_DIR}/Config/"* "${APP_BUNDLE}/Contents/Resources/Config/" 2>/dev/null || true
    echo "✅ 配置文件已复制"
fi
echo ""

# 5.5. 复制动态库（Frameworks）
echo "📦 步骤 5.5: 复制动态库..."
mkdir -p "${APP_BUNDLE}/Contents/Frameworks"

# 查找并复制所有 .framework
find "${BUILD_DIR}" -name "*.framework" -maxdepth 1 -exec cp -R {} "${APP_BUNDLE}/Contents/Frameworks/" \;

if [ -d "${APP_BUNDLE}/Contents/Frameworks/Sparkle.framework" ]; then
    echo "✅ Sparkle.framework 已复制"
    
    # 修复 Sparkle.framework 的 install_name（解决 @rpath 加载问题）
    SPARKLE_BINARY="${APP_BUNDLE}/Contents/Frameworks/Sparkle.framework/Versions/B/Sparkle"
    if [ -f "${SPARKLE_BINARY}" ]; then
        echo "🔧 修复 Sparkle.framework install_name..."
        install_name_tool -id "@rpath/Sparkle.framework/Versions/B/Sparkle" "${SPARKLE_BINARY}" 2>/dev/null || true
        echo "✅ Sparkle.framework install_name 已修复"
    fi
else
    echo "⚠️  警告：未找到 Sparkle.framework"
fi
echo ""

# 5.7. 构建并打包 Python 后端
echo "🐍 步骤 5.7: 构建 Python 后端..."
BACKEND_DIR="Backend"
PYTHON_BUILD_DIR="${APP_BUNDLE}/Contents/Resources/python_backend"

PYINSTALLER_CMD=""
if [ -f "${BACKEND_DIR}/.venv/bin/pyinstaller" ]; then
    PYINSTALLER_CMD="$(cd "${BACKEND_DIR}" && pwd)/.venv/bin/pyinstaller"
elif command -v pyinstaller &> /dev/null; then
    PYINSTALLER_CMD="pyinstaller"
fi

if [ -n "${PYINSTALLER_CMD}" ]; then
    CURRENT_DIR=$(pwd)
    cd "${BACKEND_DIR}"
    # 激活 venv 确保所有依赖可用
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi
    "${PYINSTALLER_CMD}" maccortex_backend.spec \
        --noconfirm \
        --clean \
        --distpath "../${BUILD_DIR}/python_dist" \
        2>&1 | tail -5
    cd "${CURRENT_DIR}"

    # 复制到 App Bundle
    if [ -d "${BUILD_DIR}/python_dist/maccortex_backend" ]; then
        mkdir -p "${PYTHON_BUILD_DIR}"
        cp -R "${BUILD_DIR}/python_dist/maccortex_backend/"* "${PYTHON_BUILD_DIR}/"
        chmod +x "${PYTHON_BUILD_DIR}/maccortex_backend"
        echo "✅ Python 后端已打包 ($(du -sh "${PYTHON_BUILD_DIR}" | cut -f1))"
    else
        echo "❌ 错误：PyInstaller 构建产物不存在"
        exit 1
    fi
else
    echo "⚠️  PyInstaller 未安装，跳过 Python 后端打包"
    echo "   安装方法: pip install pyinstaller"
    echo "   开发模式可设置 MACCORTEX_DEV_BACKEND 环境变量"
fi
echo ""

# 6. 代码签名（开发签名）
echo "🔐 步骤 6: 代码签名..."
if security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
    # 如果有 Developer ID，使用它
    IDENTITY=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | awk '{print $2}')
    codesign --force --deep --sign "${IDENTITY}" "${APP_BUNDLE}"
    echo "✅ 已使用 Developer ID 签名"
elif security find-identity -v -p codesigning | grep -q "Apple Development"; then
    # 否则使用开发签名
    IDENTITY=$(security find-identity -v -p codesigning | grep "Apple Development" | head -1 | awk '{print $2}')
    codesign --force --deep --sign "${IDENTITY}" "${APP_BUNDLE}"
    echo "✅ 已使用开发签名"
else
    # 使用 ad-hoc 签名（最低要求）
    codesign --force --deep --sign - "${APP_BUNDLE}"
    echo "⚠️  使用 ad-hoc 签名（App Intents 可能无法正常工作）"
    echo "   建议：配置 Apple Developer 证书以获得完整功能"
fi
echo ""

# 7. 验证签名
echo "✅ 步骤 7: 验证签名..."
codesign --verify --deep --strict --verbose=2 "${APP_BUNDLE}" 2>&1 | head -5
echo ""

# 8. 重新注册 App Intents（清除缓存）
echo "🔄 步骤 8: 重新注册 App Intents..."
pluginkit -a "${APP_BUNDLE}" 2>/dev/null || true
pluginkit -r "${APP_BUNDLE}" 2>/dev/null || true
echo "✅ 已触发 App Intents 重新注册"
echo ""

# 9. 显示结果
echo "════════════════════════════════════════"
echo "✅ .app Bundle 构建完成！"
echo ""
echo "📍 位置: ${APP_BUNDLE}"
echo "🚀 启动: open ${APP_BUNDLE}"
echo ""
echo "📱 测试 Shortcuts 集成："
echo "   1. 运行应用：open ${APP_BUNDLE}"
echo "   2. 重启 Shortcuts.app：killall Shortcuts && open /System/Applications/Shortcuts.app"
echo "   3. 搜索 'MacCortex'"
echo "════════════════════════════════════════"
