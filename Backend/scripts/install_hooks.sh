#!/bin/bash
# MacCortex - Testing Agent 安装脚本
# 安装 pre-commit hook 到 Git 仓库

set -e

echo "🤖 Testing Agent: 开始安装 pre-commit hook..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 获取项目根目录
PROJECT_ROOT="$(git rev-parse --show-toplevel)/Backend"
cd "$PROJECT_ROOT"

# 检查 pre-commit hook 源文件
if [ ! -f "scripts/pre-commit.sh" ]; then
    echo "❌ 错误：未找到 scripts/pre-commit.sh"
    exit 1
fi

# 创建 .git/hooks 目录（如果不存在）
mkdir -p .git/hooks

# 复制 pre-commit hook
cp scripts/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hook 已安装到 .git/hooks/pre-commit"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Testing Agent 安装成功！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 功能说明："
echo "   • 每次 commit 前自动运行所有测试"
echo "   • 强制测试覆盖率 ≥ 80%"
echo "   • 检查边缘情况测试覆盖"
echo "   • 验证新代码有对应测试"
echo "   • 评估测试质量评分（≥ 80/100）"
echo ""
echo "🔍 测试命令："
echo "   • 运行测试质量评分: python scripts/test_quality_scorer.py tests/"
echo "   • 手动运行所有检查: .git/hooks/pre-commit"
echo ""
