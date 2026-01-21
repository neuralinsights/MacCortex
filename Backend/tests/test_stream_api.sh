#!/bin/bash
# Phase 3 Week 3 Day 1 - 流式翻译 API 测试脚本
# 测试 /execute/stream 端点（Server-Sent Events）

set -e

BASE_URL="http://localhost:8000"

echo "=== Phase 3 Week 3 Day 1: 流式翻译 API 测试 ==="
echo

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试 1: 流式翻译（英文→中文）
echo -e "${BLUE}[测试 1]${NC} 流式翻译：Hello, how are you? (英文→中文)"
echo -e "${YELLOW}请求...${NC}"

curl -N "$BASE_URL/execute/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "translate",
    "text": "Hello, how are you?",
    "parameters": {
      "target_language": "zh-CN",
      "source_language": "en",
      "style": "formal"
    }
  }'

echo
echo -e "${GREEN}✅ 测试 1 完成${NC}"
echo
echo "-------------------------------------------"
echo

# 测试 2: 流式翻译（缓存命中测试 - 重复请求）
echo -e "${BLUE}[测试 2]${NC} 缓存命中测试（重复相同请求）"
echo -e "${YELLOW}请求...${NC}"

curl -N "$BASE_URL/execute/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "translate",
    "text": "Hello, how are you?",
    "parameters": {
      "target_language": "zh-CN",
      "source_language": "en",
      "style": "formal"
    }
  }'

echo
echo -e "${GREEN}✅ 测试 2 完成（应显示 event: cached）${NC}"
echo
echo "-------------------------------------------"
echo

# 测试 3: 流式翻译（长文本）
echo -e "${BLUE}[测试 3]${NC} 长文本流式翻译"
echo -e "${YELLOW}请求...${NC}"

curl -N "$BASE_URL/execute/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "translate",
    "text": "MacCortex is a next-generation macOS AI assistant that combines the power of MLX and Ollama. It features advanced translation capabilities using the aya-23 model, which supports over 100 languages and provides superior quality compared to smaller models. The system includes intelligent caching to dramatically improve response times for repeated translations.",
    "parameters": {
      "target_language": "zh-CN",
      "style": "formal"
    }
  }'

echo
echo -e "${GREEN}✅ 测试 3 完成${NC}"
echo
echo "-------------------------------------------"
echo

# 测试 4: 错误处理（不支持的 pattern）
echo -e "${BLUE}[测试 4]${NC} 错误处理：不支持的 pattern"
echo -e "${YELLOW}请求...${NC}"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/execute/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "summarize",
    "text": "Test text"
  }')

if [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✅ 测试 4 完成（正确返回 400 错误）${NC}"
else
    echo -e "${RED}❌ 测试 4 失败（预期 400，实际 $HTTP_CODE）${NC}"
fi

echo
echo "-------------------------------------------"
echo

# 测试 5: 流式翻译（中文→英文）
echo -e "${BLUE}[测试 5]${NC} 流式翻译：你好，最近怎么样？(中文→英文)"
echo -e "${YELLOW}请求...${NC}"

curl -N "$BASE_URL/execute/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "translate",
    "text": "你好，最近怎么样？",
    "parameters": {
      "target_language": "en-US",
      "source_language": "zh-CN",
      "style": "casual"
    }
  }'

echo
echo -e "${GREEN}✅ 测试 5 完成${NC}"
echo
echo "-------------------------------------------"
echo

# 总结
echo -e "${GREEN}=== 测试总结 ===${NC}"
echo "✅ 5 个测试用例已完成"
echo "📋 验收标准："
echo "   1. 流式响应逐行输出（event: start, chunk, done）"
echo "   2. 缓存命中显示 event: cached"
echo "   3. 长文本正确流式传输"
echo "   4. 错误处理正确（400 for non-translate pattern）"
echo "   5. 多语言支持正常"
echo
echo -e "${YELLOW}注意${NC}: 确保 Backend 服务正在运行（python Backend/src/main.py）"
echo -e "${YELLOW}注意${NC}: aya 模型必须已安装（ollama pull aya:8b）"
echo
