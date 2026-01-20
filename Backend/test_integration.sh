#!/bin/bash
# MacCortex 集成测试脚本
# Phase 1 - Week 2 Day 8
# 创建时间: 2026-01-20

set -e

echo "🧪 MacCortex 集成测试"
echo "===================="
echo ""

# 1. 检查 Python 后端状态
echo "1️⃣ 检查 Python 后端..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ Python 后端运行中"
else
    echo "   ❌ Python 后端未运行"
    echo "   启动命令: cd Backend && source .venv/bin/activate && cd src && python main.py"
    exit 1
fi

# 2. 测试 /health 端点
echo ""
echo "2️⃣ 测试 /health 端点..."
HEALTH=$(curl -s http://localhost:8000/health | python3 -m json.tool)
if echo "$HEALTH" | grep -q '"status": "healthy"'; then
    echo "   ✅ 健康检查通过"
    echo "$HEALTH" | head -5
else
    echo "   ❌ 健康检查失败"
    exit 1
fi

# 3. 测试 /version 端点
echo ""
echo "3️⃣ 测试 /version 端点..."
VERSION=$(curl -s http://localhost:8000/version | python3 -m json.tool)
if echo "$VERSION" | grep -q '"python":'; then
    echo "   ✅ 版本信息获取成功"
    echo "$VERSION"
else
    echo "   ❌ 版本信息获取失败"
    exit 1
fi

# 4. 测试 /patterns 端点
echo ""
echo "4️⃣ 测试 /patterns 端点..."
PATTERNS=$(curl -s http://localhost:8000/patterns | python3 -m json.tool)
if echo "$PATTERNS" | grep -q '"summarize"'; then
    echo "   ✅ Pattern 列表获取成功"
    echo "$PATTERNS" | head -10
else
    echo "   ❌ Pattern 列表获取失败"
    exit 1
fi

# 5. 测试 /execute 端点
echo ""
echo "5️⃣ 测试 /execute 端点（SummarizePattern）..."
cd "$(dirname "$0")"
RESULT=$(curl -s -X POST http://localhost:8000/execute \
    -H "Content-Type: application/json" \
    -d @test_request.json | python3 -m json.tool)

if echo "$RESULT" | grep -q '"success": true'; then
    echo "   ✅ Pattern 执行成功"
    echo "$RESULT" | grep -A 3 '"output"' | head -5

    # 检查延迟
    DURATION=$(echo "$RESULT" | grep '"duration"' | awk '{print $2}' | tr -d ',')
    echo "   ⏱️  执行延迟: ${DURATION}s"

    if python3 -c "exit(0 if float($DURATION) < 2.0 else 1)"; then
        echo "   ✅ 延迟 < 2.0s (目标达成)"
    else
        echo "   ⚠️  延迟 >= 2.0s (需要优化)"
    fi
else
    echo "   ❌ Pattern 执行失败"
    echo "$RESULT"
    exit 1
fi

# 6. 性能测试（10 次请求）
echo ""
echo "6️⃣ 性能测试（10 次请求）..."
TOTAL=0
for i in {1..10}; do
    START=$(python3 -c 'import time; print(time.time())')
    curl -s -X POST http://localhost:8000/execute \
        -H "Content-Type: application/json" \
        -d @test_request.json > /dev/null
    END=$(python3 -c 'import time; print(time.time())')
    DURATION=$(python3 -c "print($END - $START)")
    TOTAL=$(python3 -c "print($TOTAL + $DURATION)")
    printf "   第 %2d 次: %.3fs\n" $i $DURATION
done

AVG=$(python3 -c "print($TOTAL / 10)")
echo "   📊 平均延迟: ${AVG}s"

if python3 -c "exit(0 if float($AVG) < 2.0 else 1)"; then
    echo "   ✅ 平均延迟 < 2.0s"
else
    echo "   ⚠️  平均延迟 >= 2.0s"
fi

echo ""
echo "🎉 所有集成测试通过！"
echo ""
echo "下一步:"
echo "  - 运行 Swift 测试: swift test"
echo "  - 安装 MLX/Ollama 以启用真实 LLM"
echo "  - 实现其他 4 个 Pattern"
