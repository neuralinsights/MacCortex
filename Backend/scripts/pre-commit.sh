#!/bin/bash
# MacCortex Testing Agent - Pre-commit Hook
# 强制执行严格测试标准

set -e

echo ""
echo "🤖 Testing Agent: 开始 pre-commit 检查..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 获取项目根目录
PROJECT_ROOT="$(git rev-parse --show-toplevel)/Backend"
cd "$PROJECT_ROOT"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ 未找到虚拟环境 .venv"
    exit 1
fi

# ================================
# 1. 运行所有测试
# ================================
echo ""
echo "📝 Step 1/5: 运行测试套件..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! python -m pytest tests/ -v --tb=short 2>&1 | tee /tmp/pytest_output.txt; then
    echo ""
    echo "❌ 测试失败！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 失败的测试："
    grep -A 5 "FAILED" /tmp/pytest_output.txt || true
    echo ""
    echo "💡 建议："
    echo "   1. 修复失败的测试"
    echo "   2. 运行 'pytest tests/ -v' 查看详细信息"
    echo "   3. 确保所有测试通过后再 commit"
    exit 1
fi

# ================================
# 2. 检查测试覆盖率
# ================================
echo ""
echo "📊 Step 2/5: 检查测试覆盖率（要求 ≥ 80%）..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! python -m pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80 -q 2>&1 | tee /tmp/coverage_output.txt; then
    echo ""
    echo "❌ 测试覆盖率不足 80%！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "TOTAL" /tmp/coverage_output.txt || true
    echo ""
    echo "💡 建议："
    echo "   1. 运行 'pytest --cov=src --cov-report=html' 生成详细报告"
    echo "   2. 在浏览器中打开 htmlcov/index.html 查看未覆盖代码"
    echo "   3. 为未覆盖的代码添加测试"
    exit 1
fi

COVERAGE=$(grep "TOTAL" /tmp/coverage_output.txt | awk '{print $NF}' | sed 's/%//')
echo "✅ 测试覆盖率：$COVERAGE%（通过）"

# ================================
# 3. 检查边缘情况测试
# ================================
echo ""
echo "🔍 Step 3/5: 检查边缘情况覆盖..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

EDGE_CASE_PATTERNS=(
    "test.*invalid"
    "test.*edge"
    "test.*error"
    "test.*boundary"
    "test.*empty"
    "test.*null"
)

edge_case_count=0
for pattern in "${EDGE_CASE_PATTERNS[@]}"; do
    count=$(grep -r -i "$pattern" tests/ 2>/dev/null | wc -l)
    edge_case_count=$((edge_case_count + count))
done

if [ $edge_case_count -lt 5 ]; then
    echo "⚠️  警告：边缘情况测试不足（发现 $edge_case_count 个，建议 ≥ 5 个）"
    echo ""
    echo "💡 建议添加："
    echo "   - test_invalid_input(): 测试无效输入"
    echo "   - test_boundary_conditions(): 测试边界条件"
    echo "   - test_error_handling(): 测试错误处理"
    echo "   - test_empty_data(): 测试空数据"
    echo ""
    echo "ℹ️  这是警告，不阻止 commit，但建议改进"
else
    echo "✅ 边缘情况测试：$edge_case_count 个（充足）"
fi

# ================================
# 4. 检查新代码是否有对应测试
# ================================
echo ""
echo "📂 Step 4/5: 检查新代码的测试文件..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

missing_tests=()
git diff --cached --name-only --diff-filter=A | grep "^Backend/src/.*\.py$" | while read file; do
    # 跳过 __init__.py
    if [[ "$file" == *"__init__.py" ]]; then
        continue
    fi

    # 计算对应的测试文件路径
    relative_path=${file#Backend/src/}
    test_file="tests/$(dirname $relative_path)/test_$(basename $relative_path)"

    if [ ! -f "$test_file" ]; then
        echo "⚠️  新文件缺少测试：$file → $test_file"
        missing_tests+=("$test_file")
    fi
done

if [ ${#missing_tests[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  警告：${#missing_tests[@]} 个新文件缺少测试"
    echo ""
    echo "💡 建议："
    echo "   运行 'python scripts/generate_test_template.py' 生成测试骨架"
    echo ""
    echo "ℹ️  这是警告，不阻止 commit，但强烈建议添加测试"
else
    echo "✅ 所有新代码均有对应测试"
fi

# ================================
# 5. 测试质量评分
# ================================
echo ""
echo "⭐ Step 5/5: 测试质量评分..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "scripts/test_quality_scorer.py" ]; then
    python scripts/test_quality_scorer.py tests/ || true
else
    echo "ℹ️  测试质量评分脚本未找到（可选）"
fi

# ================================
# 总结
# ================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Testing Agent: 所有强制检查通过"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 检查摘要："
echo "   ✅ 测试通过"
echo "   ✅ 覆盖率 $COVERAGE% (≥ 80%)"
if [ $edge_case_count -ge 5 ]; then
    echo "   ✅ 边缘情况测试 $edge_case_count 个"
else
    echo "   ⚠️  边缘情况测试 $edge_case_count 个（建议改进）"
fi
if [ ${#missing_tests[@]} -eq 0 ]; then
    echo "   ✅ 新代码有测试"
else
    echo "   ⚠️  ${#missing_tests[@]} 个新文件缺少测试"
fi
echo ""
echo "🚀 准备 commit..."
echo ""

exit 0
