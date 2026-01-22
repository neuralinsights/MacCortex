#!/bin/bash

# Week 5 验收项目 - Backend 启动脚本
# 用途：快速启动 MacCortex Backend API

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MacCortex Backend 启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 进入 Backend 目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}📁 进入 Backend 目录${NC}"
cd "$BACKEND_DIR"
echo "   路径: $BACKEND_DIR"
echo ""

# 检查虚拟环境
if [ -d "venv" ]; then
    echo -e "${GREEN}🐍 激活 Python 虚拟环境${NC}"
    source venv/bin/activate
    echo "   ✅ 虚拟环境已激活"
else
    echo -e "${YELLOW}⚠️  未找到虚拟环境，正在创建...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo "   ✅ 虚拟环境已创建并激活"
fi
echo ""

# 检查依赖
echo -e "${GREEN}📦 检查依赖${NC}"
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "   ❌ FastAPI 未安装"
    echo "   正在安装依赖..."
    python3 -m pip install -r requirements.txt
else
    echo "   ✅ 依赖已安装"
fi
echo ""

# 检查关键文件
echo -e "${GREEN}🔍 检查关键文件${NC}"
if [ ! -f "src/main.py" ]; then
    echo "   ❌ src/main.py 不存在"
    exit 1
fi

if [ ! -f "src/api/swarm_routes.py" ]; then
    echo "   ❌ src/api/swarm_routes.py 不存在"
    exit 1
fi
echo "   ✅ 所有关键文件存在"
echo ""

# 启动服务器
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  启动 FastAPI 服务器${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}🚀 服务地址: http://localhost:8000${NC}"
echo -e "${GREEN}📚 API 文档: http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo ""

# 启动服务器
python3 src/main.py
