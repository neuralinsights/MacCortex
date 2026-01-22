"""
MacCortex Swarm State Definition

Defines the state structure for the LangGraph workflow.
All nodes in the graph will operate on and modify this state.
"""

from typing import TypedDict, List, Dict, Any, Literal, Optional
import time


class SubtaskResult(TypedDict):
    """单个子任务的执行结果"""
    subtask_id: str                     # 子任务 ID
    type: Literal["code", "research", "tool"]  # 任务类型
    passed: bool                        # 是否通过验收
    code: Optional[str]                 # 生成的代码（如果是代码任务）
    output: Optional[str]               # 执行输出
    research_result: Optional[str]      # 调研结果（如果是调研任务）
    tool_result: Optional[str]          # 工具执行结果
    error: Optional[str]                # 错误信息（如果失败）


class Subtask(TypedDict):
    """单个子任务定义"""
    id: str                             # 子任务 ID（如 "task-1"）
    type: Literal["code", "research", "tool"]  # 任务类型
    description: str                    # 任务描述
    dependencies: List[str]             # 依赖的子任务 ID 列表
    acceptance_criteria: List[str]      # 验收标准列表
    # 工具任务专用字段
    tool_name: Optional[str]            # 工具名称（如 "write_file"）
    tool_args: Optional[Dict[str, Any]] # 工具参数


class Plan(TypedDict):
    """任务计划"""
    subtasks: List[Subtask]             # 子任务列表
    overall_acceptance: List[str]       # 整体验收标准


class SwarmState(TypedDict):
    """
    Swarm 工作流状态

    这是 LangGraph 状态图的核心数据结构。所有节点（Planner、Coder、Reviewer 等）
    都会读取和修改这个状态。

    状态流转：
    1. 用户输入 → Planner 生成计划
    2. 计划 → Executor 执行子任务
    3. 子任务结果 → Reviewer 审查
    4. 所有子任务完成 → Reflector 整体反思
    5. 反思通过 → 输出最终结果
    """

    # ===== 输入 =====
    user_input: str                     # 用户原始输入（复杂任务描述）
    context: Optional[Dict[str, Any]]   # 上下文信息（文件路径、屏幕 OCR 等）

    # ===== 计划 =====
    plan: Optional[Plan]                # Planner 生成的任务计划
    current_subtask_index: int          # 当前执行到第几个子任务（从 0 开始）

    # ===== 执行 =====
    subtask_results: List[SubtaskResult]  # 每个子任务的执行结果
    current_code: Optional[str]         # Coder 当前生成的代码
    current_code_file: Optional[str]    # 代码文件路径
    review_feedback: Optional[str]      # Reviewer 的反馈（用于 Coder 修复）

    # ===== 控制 =====
    iteration_count: int                # 当前 Coder ↔ Reviewer 循环次数
    total_tokens: int                   # 累计 Token 消耗
    start_time: float                   # 任务开始时间（Unix 时间戳）
    status: Literal["planning", "executing", "reviewing", "reflecting", "completed", "failed"]
    user_interrupted: bool              # 用户是否请求中断

    # ===== 输出 =====
    final_output: Optional[Dict[str, Any]]  # 最终输出结果
    error_message: Optional[str]        # 错误信息（如果失败）


def create_initial_state(user_input: str, context: Optional[Dict[str, Any]] = None) -> SwarmState:
    """
    创建初始状态

    Args:
        user_input: 用户输入的复杂任务描述
        context: 可选的上下文信息

    Returns:
        SwarmState: 初始化的状态对象
    """
    return SwarmState(
        # 输入
        user_input=user_input,
        context=context or {},

        # 计划
        plan=None,
        current_subtask_index=0,

        # 执行
        subtask_results=[],
        current_code=None,
        current_code_file=None,
        review_feedback=None,

        # 控制
        iteration_count=0,
        total_tokens=0,
        start_time=time.time(),
        status="planning",
        user_interrupted=False,

        # 输出
        final_output=None,
        error_message=None
    )
