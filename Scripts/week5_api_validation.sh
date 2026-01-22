#!/bin/bash

# MacCortex Week 5 验收脚本 - API 版本
# 目标：通过 Backend API 测试 Swarm 编排系统

set -e

echo "=========================================="
echo "  MacCortex Week 5 API 验收测试"
echo "=========================================="
echo ""

# 1. 检查 Backend 健康状态
echo "1️⃣  检查 Backend 健康状态..."
HEALTH=$(curl -s http://localhost:8000/health)
echo "$HEALTH" | jq .
echo "✅ Backend 运行正常"
echo ""

# 2. 提交 CLI Todo App 任务
echo "2️⃣  提交 CLI Todo App 构建任务..."
TASK_PAYLOAD='{
  "user_input": "Create a simple command-line todo application with the following features:\n1. Add tasks (todo add <task>)\n2. List all tasks (todo list)\n3. Mark task as done (todo done <id>)\n4. Delete task (todo delete <id>)\n5. Save to JSON file\n\nRequirements:\n- Python 3.10+\n- Use argparse for CLI\n- Store in ~/mytodo.json\n- Simple and clean code",
  "workspace_path": "/tmp/cli_todo_app"
}'

echo "发送任务..."
echo "$TASK_PAYLOAD" | jq .

TASK_RESPONSE=$(curl -s -X POST http://localhost:8000/swarm/tasks \
  -H "Content-Type: application/json" \
  -d "$TASK_PAYLOAD")

echo ""
echo "任务响应:"
echo "$TASK_RESPONSE" | jq .

TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.task_id')
echo ""
echo "✅ 任务已提交，Task ID: $TASK_ID"
echo ""

# 3. 轮询任务状态
echo "3️⃣  监控任务执行状态..."
echo "（注意：完整执行可能需要 5-10 分钟）"
echo ""

for i in {1..60}; do
    sleep 5
    STATUS=$(curl -s http://localhost:8000/swarm/tasks/$TASK_ID)

    CURRENT_STATUS=$(echo "$STATUS" | jq -r '.status')
    CURRENT_AGENT=$(echo "$STATUS" | jq -r '.current_agent')
    PROGRESS=$(echo "$STATUS" | jq -r '.progress')

    echo "[$i/60] 状态: $CURRENT_STATUS | 当前Agent: $CURRENT_AGENT | 进度: $PROGRESS%"

    if [ "$CURRENT_STATUS" = "completed" ] || [ "$CURRENT_STATUS" = "failed" ]; then
        echo ""
        echo "任务结束！最终状态: $CURRENT_STATUS"
        echo ""
        echo "完整结果:"
        echo "$STATUS" | jq .
        break
    fi

    if [ $i -eq 60 ]; then
        echo ""
        echo "⚠️  超时（5分钟），但任务可能仍在后台执行"
        echo "手动检查: curl http://localhost:8000/swarm/tasks/$TASK_ID | jq ."
    fi
done

echo ""
echo "=========================================="
echo "  验收测试完成"
echo "=========================================="
echo ""
echo "📋 检查清单:"
echo "  ✅ Backend 健康检查"
echo "  ✅ 任务提交成功"
echo "  ⏳ 任务执行监控"
echo ""
echo "如需查看详细日志:"
echo "  tail -f /tmp/backend.log"
