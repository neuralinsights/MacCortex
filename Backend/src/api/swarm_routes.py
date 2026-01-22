"""
MacCortex Swarm API Routes

提供 Slow Lane (Swarm Orchestration) 的 RESTful API 和 WebSocket 接口。

Routes:
- POST /swarm/tasks - 创建新任务
- GET /swarm/tasks/{task_id} - 查询任务状态
- POST /swarm/tasks/{task_id}/approve - HITL 审批
- GET /swarm/tasks - 获取任务历史
- WebSocket /swarm/ws/{task_id} - 实时状态推送
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from orchestration.swarm_graph import create_full_swarm_graph
from orchestration.state import SwarmState
from orchestration.checkpoints import InMemorySaver

# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/swarm", tags=["swarm"])

# ============================================================================
# Data Models
# ============================================================================

class FileAttachment(BaseModel):
    """文件附件"""
    type: Literal["file"] = "file"
    path: str


class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    user_input: str = Field(..., min_length=1, max_length=10000)
    workspace_path: str
    attachments: List[FileAttachment] = Field(default_factory=list)
    enable_hitl: bool = True
    enable_code_review: bool = False


class CreateTaskResponse(BaseModel):
    """创建任务响应"""
    task_id: str
    status: str
    created_at: str
    websocket_url: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    current_agent: Optional[str]
    progress: float
    created_at: str
    updated_at: str
    agents_status: Dict[str, str]
    interrupts: List[Dict[str, Any]]
    output: Optional[Dict[str, Any]] = None


class HITLApprovalRequest(BaseModel):
    """HITL 审批请求"""
    interrupt_id: str
    action: Literal["approve", "deny", "modify", "abort"]
    modified_data: Optional[Dict[str, Any]] = None


class HITLApprovalResponse(BaseModel):
    """HITL 审批响应"""
    success: bool
    message: str


class TaskHistoryItem(BaseModel):
    """任务历史项"""
    task_id: str
    user_input: str
    status: str
    created_at: str
    duration: Optional[float] = None


class TaskHistoryResponse(BaseModel):
    """任务历史响应"""
    tasks: List[TaskHistoryItem]
    total: int
    has_more: bool


# ============================================================================
# Task Management (In-Memory Storage)
# ============================================================================

class TaskManager:
    """任务管理器（内存存储，Week 5 将迁移到数据库）"""

    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.websockets: Dict[str, List[WebSocket]] = {}

    def create_task(
        self,
        user_input: str,
        workspace_path: str,
        enable_hitl: bool = True,
        enable_code_review: bool = False
    ) -> str:
        """创建新任务"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        task = {
            "task_id": task_id,
            "user_input": user_input,
            "workspace_path": workspace_path,
            "status": "created",
            "current_agent": None,
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "agents_status": {
                "planner": "pending",
                "coder": "pending",
                "reviewer": "pending",
                "tool_runner": "pending",
                "reflector": "pending"
            },
            "interrupts": [],
            "output": None,
            "enable_hitl": enable_hitl,
            "enable_code_review": enable_code_review
        }

        self.tasks[task_id] = task
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """更新任务"""
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

    def get_all_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取所有任务"""
        tasks = list(self.tasks.values())

        if status and status != "all":
            tasks = [t for t in tasks if t["status"] == status]

        # 按创建时间倒序排序
        tasks.sort(key=lambda x: x["created_at"], reverse=True)

        return tasks[offset:offset+limit]

    async def broadcast_to_websockets(self, task_id: str, message: Dict[str, Any]):
        """向所有连接的 WebSocket 广播消息"""
        if task_id in self.websockets:
            dead_sockets = []

            for ws in self.websockets[task_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_sockets.append(ws)

            # 清理断开的连接
            for ws in dead_sockets:
                self.websockets[task_id].remove(ws)

    def add_websocket(self, task_id: str, websocket: WebSocket):
        """添加 WebSocket 连接"""
        if task_id not in self.websockets:
            self.websockets[task_id] = []
        self.websockets[task_id].append(websocket)

    def remove_websocket(self, task_id: str, websocket: WebSocket):
        """移除 WebSocket 连接"""
        if task_id in self.websockets and websocket in self.websockets[task_id]:
            self.websockets[task_id].remove(websocket)


# 全局任务管理器
task_manager = TaskManager()


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/tasks", response_model=CreateTaskResponse)
async def create_task(request: CreateTaskRequest):
    """
    创建新任务并启动 Swarm 编排

    **请求示例**:
    ```json
    {
      "user_input": "Create a hello world program in Python",
      "workspace_path": "/Users/jamesg/workspace",
      "enable_hitl": true
    }
    ```

    **响应示例**:
    ```json
    {
      "task_id": "task_20260122_143000_a1b2c3d4",
      "status": "created",
      "created_at": "2026-01-22T14:30:00+13:00",
      "websocket_url": "ws://localhost:8000/swarm/ws/task_20260122_143000_a1b2c3d4"
    }
    ```
    """
    # 创建任务
    task_id = task_manager.create_task(
        user_input=request.user_input,
        workspace_path=request.workspace_path,
        enable_hitl=request.enable_hitl,
        enable_code_review=request.enable_code_review
    )

    # 异步启动任务执行
    asyncio.create_task(_execute_task(task_id))

    return CreateTaskResponse(
        task_id=task_id,
        status="created",
        created_at=datetime.now().isoformat(),
        websocket_url=f"ws://localhost:8000/swarm/ws/{task_id}"
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态

    **响应示例**:
    ```json
    {
      "task_id": "task_20260122_143000_a1b2c3d4",
      "status": "running",
      "current_agent": "coder",
      "progress": 0.60,
      "agents_status": {
        "planner": "completed",
        "coder": "running",
        "reviewer": "pending"
      }
    }
    ```
    """
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        current_agent=task.get("current_agent"),
        progress=task["progress"],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        agents_status=task["agents_status"],
        interrupts=task.get("interrupts", []),
        output=task.get("output")
    )


@router.post("/tasks/{task_id}/approve", response_model=HITLApprovalResponse)
async def approve_interrupt(task_id: str, request: HITLApprovalRequest):
    """
    HITL 审批

    **请求示例**:
    ```json
    {
      "interrupt_id": "int_001",
      "action": "approve",
      "modified_data": {}
    }
    ```

    **响应示例**:
    ```json
    {
      "success": true,
      "message": "Approval processed, workflow resumed"
    }
    ```
    """
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # TODO: 实现 HITL 审批逻辑（通过 Graph resume）
    # 这需要保存 Graph 实例的引用，或使用 checkpoint 恢复

    # 目前仅记录审批决策
    task_manager.update_task(task_id, {
        "last_approval": {
            "interrupt_id": request.interrupt_id,
            "action": request.action,
            "timestamp": datetime.now().isoformat()
        }
    })

    # 广播审批事件
    await task_manager.broadcast_to_websockets(task_id, {
        "type": "approval_received",
        "interrupt_id": request.interrupt_id,
        "action": request.action,
        "timestamp": datetime.now().isoformat()
    })

    return HITLApprovalResponse(
        success=True,
        message=f"Approval ({request.action}) processed"
    )


@router.get("/tasks", response_model=TaskHistoryResponse)
async def get_task_history(
    status: Optional[str] = "all",
    limit: int = 20,
    offset: int = 0
):
    """
    获取任务历史

    **查询参数**:
    - status: all | created | running | completed | failed
    - limit: 每页数量（默认 20）
    - offset: 偏移量（默认 0）

    **响应示例**:
    ```json
    {
      "tasks": [
        {
          "task_id": "task_20260122_143000_a1b2c3d4",
          "user_input": "Create a hello world program",
          "status": "completed",
          "created_at": "2026-01-22T14:30:00+13:00",
          "duration": 154.5
        }
      ],
      "total": 10,
      "has_more": false
    }
    ```
    """
    tasks = task_manager.get_all_tasks(status=status, limit=limit, offset=offset)

    history_items = []
    for task in tasks:
        # 计算持续时间
        duration = None
        if task["status"] in ["completed", "failed"]:
            created = datetime.fromisoformat(task["created_at"])
            updated = datetime.fromisoformat(task["updated_at"])
            duration = (updated - created).total_seconds()

        history_items.append(TaskHistoryItem(
            task_id=task["task_id"],
            user_input=task["user_input"],
            status=task["status"],
            created_at=task["created_at"],
            duration=duration
        ))

    total = len(task_manager.get_all_tasks(status=status, limit=999999))
    has_more = (offset + limit) < total

    return TaskHistoryResponse(
        tasks=history_items,
        total=total,
        has_more=has_more
    )


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket 实时状态推送

    **连接后接收的消息类型**:
    - agent_status: Agent 状态更新
    - progress: 进度更新
    - hitl_interrupt: HITL 中断通知
    - task_completed: 任务完成
    - error: 错误通知
    """
    await websocket.accept()

    # 添加到连接池
    task_manager.add_websocket(task_id, websocket)

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        })

        # 保持连接
        while True:
            # 接收客户端消息（心跳检测）
            data = await websocket.receive_text()

            # 心跳响应
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        task_manager.remove_websocket(task_id, websocket)


# ============================================================================
# Task Execution
# ============================================================================

async def _execute_task(task_id: str):
    """
    异步执行任务（后台任务）

    此函数在后台线程中执行 LangGraph Swarm 编排，并通过 WebSocket 推送状态更新。
    """
    task = task_manager.get_task(task_id)
    if not task:
        return

    try:
        # 更新状态为 running
        task_manager.update_task(task_id, {"status": "running"})
        await task_manager.broadcast_to_websockets(task_id, {
            "type": "status_changed",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        })

        # 创建 Swarm Graph
        workspace_path = Path(task["workspace_path"])
        checkpointer = InMemorySaver()  # 使用内存 checkpointer

        graph = create_full_swarm_graph(
            workspace_path=workspace_path,
            checkpointer=checkpointer,
            tool_runner={"require_approval": task["enable_hitl"]}
        )

        # 初始化状态
        initial_state: SwarmState = {
            "user_input": task["user_input"],
            "subtasks": [],
            "current_subtask_index": 0,
            "subtask_results": [],
            "code_artifacts": [],
            "current_iteration": 0,
            "max_iterations": 3,
            "status": "executing",
            "error_message": None,
            "reflection": None
        }

        thread_config = {"configurable": {"thread_id": task_id}}

        # 执行 Graph（处理 interrupts）
        async for event in graph.astream(initial_state, thread_config):
            # 解析事件
            if isinstance(event, dict):
                for node_name, node_output in event.items():
                    # 更新当前 Agent
                    task_manager.update_task(task_id, {
                        "current_agent": node_name
                    })

                    # 更新 Agent 状态
                    agents_status = task.get("agents_status", {})
                    if node_name in agents_status:
                        agents_status[node_name] = "running"
                        task_manager.update_task(task_id, {"agents_status": agents_status})

                    # 广播 Agent 状态更新
                    await task_manager.broadcast_to_websockets(task_id, {
                        "type": "agent_status",
                        "agent": node_name,
                        "status": "running",
                        "timestamp": datetime.now().isoformat()
                    })

                    # 模拟进度更新（简化版）
                    agent_sequence = ["planner", "coder", "reviewer", "tool_runner", "reflector"]
                    if node_name in agent_sequence:
                        progress = (agent_sequence.index(node_name) + 1) / len(agent_sequence)
                        task_manager.update_task(task_id, {"progress": progress})

                        await task_manager.broadcast_to_websockets(task_id, {
                            "type": "progress",
                            "progress": progress,
                            "current_step": node_name,
                            "total_steps": len(agent_sequence)
                        })

                    # 标记 Agent 完成
                    if node_name in agents_status:
                        agents_status[node_name] = "completed"
                        task_manager.update_task(task_id, {"agents_status": agents_status})

        # 任务完成
        task_manager.update_task(task_id, {
            "status": "completed",
            "progress": 1.0
        })

        await task_manager.broadcast_to_websockets(task_id, {
            "type": "task_completed",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        # 任务失败
        task_manager.update_task(task_id, {
            "status": "failed",
            "error_message": str(e)
        })

        await task_manager.broadcast_to_websockets(task_id, {
            "type": "error",
            "error_code": "EXECUTION_ERROR",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        })
