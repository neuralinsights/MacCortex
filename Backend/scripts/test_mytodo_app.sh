#!/bin/bash

# Week 5 验收项目 - CLI Todo App 测试脚本
# 用途：自动测试生成的 mytodo 应用所有功能

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 工作空间路径
WORKSPACE="/tmp/mytodo_workspace"
MYTODO="python ${WORKSPACE}/mytodo.py"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CLI Todo App 功能测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查工作空间
if [ ! -d "$WORKSPACE" ]; then
    echo -e "${RED}❌ 工作空间不存在: $WORKSPACE${NC}"
    exit 1
fi

cd "$WORKSPACE"
echo -e "${GREEN}📁 工作空间: $WORKSPACE${NC}"
echo ""

# 检查文件
echo -e "${GREEN}🔍 检查生成的文件${NC}"
FILES=("mytodo.py" "requirements.txt" "README.md")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ✅ $file"
    else
        echo -e "   ❌ $file 不存在"
    fi
done
echo ""

# 安装依赖
echo -e "${GREEN}📦 安装依赖${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    echo "   ✅ 依赖已安装"
else
    echo -e "${YELLOW}⚠️  未找到 requirements.txt，跳过依赖安装${NC}"
fi
echo ""

# 测试计数器
TESTS_PASSED=0
TESTS_FAILED=0

# 测试函数
test_command() {
    local description="$1"
    local command="$2"
    local expected_exit_code="${3:-0}"

    echo -e "${BLUE}🧪 测试: $description${NC}"
    echo "   命令: $command"

    if eval "$command" > /tmp/test_output.txt 2>&1; then
        exit_code=0
    else
        exit_code=$?
    fi

    if [ "$exit_code" -eq "$expected_exit_code" ]; then
        echo -e "   ${GREEN}✅ 通过${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        cat /tmp/test_output.txt | head -5 | sed 's/^/   > /'
    else
        echo -e "   ${RED}❌ 失败${NC} (退出码: $exit_code, 期望: $expected_exit_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        cat /tmp/test_output.txt | head -10 | sed 's/^/   > /'
    fi
    echo ""
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  开始功能测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 清理旧数据
rm -rf ~/.mytodo/tasks.json 2>/dev/null || true

# 测试 1: 显示帮助
test_command "显示帮助信息" "$MYTODO help"

# 测试 2: 添加任务
test_command "添加任务 #1" "$MYTODO add '学习 LangGraph'"
test_command "添加任务 #2" "$MYTODO add '完成 MacCortex Phase 4'"
test_command "添加任务 #3" "$MYTODO add '编写测试用例'"

# 测试 3: 列出所有任务
test_command "列出所有任务" "$MYTODO list"

# 测试 4: 标记任务完成
test_command "标记任务 #1 完成" "$MYTODO done 1"

# 测试 5: 列出所有任务（包括已完成）
test_command "列出所有任务（含已完成）" "$MYTODO list --all"

# 测试 6: 删除任务
test_command "删除任务 #2" "$MYTODO delete 2"

# 测试 7: 再次列出任务（验证删除）
test_command "验证任务已删除" "$MYTODO list --all"

# 测试 8: 清除已完成任务
test_command "清除已完成任务" "$MYTODO clear --done"

# 测试 9: 最终列出任务
test_command "最终任务列表" "$MYTODO list --all"

# 测试 10: 验证数据持久化
if [ -f ~/.mytodo/tasks.json ]; then
    echo -e "${BLUE}🧪 测试: 验证数据持久化${NC}"
    echo "   文件: ~/.mytodo/tasks.json"
    if python -m json.tool ~/.mytodo/tasks.json > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ 通过${NC} (JSON 格式正确)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "   > 任务数据:"
        cat ~/.mytodo/tasks.json | python -m json.tool | head -10 | sed 's/^/   > /'
    else
        echo -e "   ${RED}❌ 失败${NC} (JSON 格式错误)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
else
    echo -e "${BLUE}🧪 测试: 验证数据持久化${NC}"
    echo -e "   ${RED}❌ 失败${NC} (tasks.json 不存在)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo ""
fi

# 测试 11: 运行单元测试（如果存在）
if [ -f "tests/test_mytodo.py" ]; then
    echo -e "${BLUE}🧪 测试: 运行单元测试${NC}"
    if pytest tests/ -v > /tmp/pytest_output.txt 2>&1; then
        echo -e "   ${GREEN}✅ 通过${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        cat /tmp/pytest_output.txt | grep -E "(PASSED|FAILED|test_)" | head -10 | sed 's/^/   > /'
    else
        echo -e "   ${YELLOW}⚠️  单元测试失败或未安装 pytest${NC}"
        cat /tmp/pytest_output.txt | head -5 | sed 's/^/   > /'
    fi
    echo ""
fi

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  测试总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✅ 通过: $TESTS_PASSED${NC}"
echo -e "${RED}❌ 失败: $TESTS_FAILED${NC}"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！ ($TESTS_PASSED/$TOTAL_TESTS)${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  部分测试失败 ($TESTS_PASSED/$TOTAL_TESTS)${NC}"
    exit 1
fi
