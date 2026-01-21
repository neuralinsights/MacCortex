#!/bin/bash

# MacCortex Phase 4 设置脚本
# 安装 LangGraph 依赖并验证基础设施

set -e

echo "=== MacCortex Phase 4 设置 ==="
echo ""

# 1. 检查 Python 版本
echo "[1/5] 检查 Python 版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $PYTHON_VERSION"

if [[ ! "$PYTHON_VERSION" =~ ^3\.(10|11|12) ]]; then
    echo "❌ 需要 Python 3.10+，当前版本: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python 版本满足要求"
echo ""

# 2. 激活虚拟环境（使用现有的 .venv）
echo "[2/5] 激活虚拟环境..."
if [ ! -d ".venv" ]; then
    echo "创建新虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "✅ 虚拟环境已激活"
echo ""

# 3. 安装 Phase 4 依赖
echo "[3/5] 安装 Phase 4 依赖..."
pip install --upgrade pip
pip install -r requirements-phase4.txt

echo "✅ 依赖安装完成"
echo ""

# 4. 验证关键依赖
echo "[4/5] 验证关键依赖..."

python3 -c "import langgraph; print('✅ LangGraph:', langgraph.__version__)" || {
    echo "❌ LangGraph 安装失败"
    exit 1
}

python3 -c "from langchain_anthropic import ChatAnthropic; print('✅ LangChain Anthropic')" || {
    echo "❌ LangChain Anthropic 安装失败"
    exit 1
}

python3 -c "from langgraph.checkpoint.sqlite import SqliteSaver; print('✅ LangGraph SQLite Checkpointer')" || {
    echo "❌ LangGraph Checkpointer 安装失败"
    exit 1
}

echo ""

# 5. 运行基础测试
echo "[5/5] 运行基础测试..."
cd ..
python -m pytest tests/orchestration/test_graph_basic.py -v

echo ""
echo "=== Phase 4 设置完成 ==="
echo ""
echo "下一步："
echo "  1. 激活环境: source .venv/bin/activate"
echo "  2. 运行测试: pytest tests/orchestration/ -v"
echo "  3. 测试图: python src/orchestration/graph.py"
