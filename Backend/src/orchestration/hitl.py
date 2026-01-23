"""
MacCortex Human-in-the-Loop (HITL) 辅助模块

提供用户交互辅助功能，支持工作流中断、用户决策收集与恢复。
"""

from typing import Dict, Any, Literal, Optional
from langgraph.types import Command
import json


class HITLHelper:
    """HITL 交互辅助类"""

    @staticmethod
    def create_approval_prompt(
        operation: str,
        details: Dict[str, Any],
        risk_level: Literal["low", "medium", "high"] = "medium"
    ) -> Dict[str, Any]:
        """
        创建审批提示信息

        Args:
            operation: 操作类型（tool_execution/code_generation/review_intervention）
            details: 操作详情（工具名称、参数、代码等）
            risk_level: 风险等级

        Returns:
            Dict: 格式化的审批提示信息
        """
        prompt_data = {
            "operation": operation,
            "risk_level": risk_level,
            "details": details,
            "timestamp": HITLHelper._get_timestamp(),
            "available_actions": HITLHelper._get_available_actions(operation)
        }

        return prompt_data

    @staticmethod
    def parse_user_decision(
        user_input: str,
        operation: str
    ) -> Dict[str, Any]:
        """
        解析用户决策

        Args:
            user_input: 用户输入（approve/deny/modify/abort）
            operation: 操作类型

        Returns:
            Dict: 解析后的决策信息

        Raises:
            ValueError: 如果输入无效
        """
        user_input = user_input.strip().lower()

        # 基础决策映射
        valid_actions = {
            "approve": "approve",
            "yes": "approve",
            "y": "approve",
            "ok": "approve",
            "deny": "deny",
            "no": "deny",
            "n": "deny",
            "skip": "deny",
            "modify": "modify",
            "edit": "modify",
            "m": "modify",
            "abort": "abort",
            "cancel": "abort",
            "stop": "abort"
        }

        action = valid_actions.get(user_input)
        if not action:
            raise ValueError(
                f"无效的决策：'{user_input}'。"
                f"有效选项：{', '.join(set(valid_actions.values()))}"
            )

        decision = {
            "action": action,
            "operation": operation,
            "timestamp": HITLHelper._get_timestamp()
        }

        # 如果是 modify，需要额外信息（由调用方添加）
        if action == "modify":
            decision["modified_data"] = {}

        return decision

    @staticmethod
    def create_resume_command(
        decision: Dict[str, Any]
    ) -> Command:
        """
        创建恢复命令

        Args:
            decision: 用户决策信息

        Returns:
            Command: LangGraph Command 对象
        """
        return Command(resume=decision)

    @staticmethod
    def format_interrupt_message(
        prompt_data: Dict[str, Any]
    ) -> str:
        """
        格式化中断消息（用于 CLI 显示）

        Args:
            prompt_data: 审批提示信息

        Returns:
            str: 格式化的消息文本
        """
        operation = prompt_data["operation"]
        risk_level = prompt_data["risk_level"]
        details = prompt_data["details"]

        # 风险等级标记
        risk_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴"
        }

        message_parts = [
            f"\n{'=' * 60}",
            f"{risk_emoji.get(risk_level, '⚪')} Human-in-the-Loop 确认请求",
            f"{'=' * 60}",
            f"操作类型: {operation}",
            f"风险等级: {risk_level.upper()}",
            f"时间戳: {prompt_data['timestamp']}",
            "\n详细信息:"
        ]

        # 根据操作类型格式化详情
        if operation == "tool_execution":
            message_parts.extend([
                f"  工具名称: {details.get('tool_name', 'N/A')}",
                f"  子任务: {details.get('subtask_description', 'N/A')}",
                f"  参数:",
                f"    {json.dumps(details.get('tool_args', {}), indent=4, ensure_ascii=False)}"
            ])
        elif operation == "code_generation":
            code = details.get("code", "")
            code_preview = code[:200] + "..." if len(code) > 200 else code
            message_parts.extend([
                f"  语言: {details.get('language', 'N/A')}",
                f"  子任务: {details.get('subtask_description', 'N/A')}",
                f"  文件路径: {details.get('file_path', 'N/A')}",
                f"  代码预览:",
                f"    {code_preview}"
            ])
        elif operation == "review_intervention":
            message_parts.extend([
                f"  子任务: {details.get('subtask_description', 'N/A')}",
                f"  迭代次数: {details.get('iteration_count', 0)}/{details.get('max_iterations', 0)}",
                f"  审查反馈: {details.get('reviewer_feedback', 'N/A')}"
            ])

        message_parts.extend([
            f"\n可用操作: {', '.join(prompt_data['available_actions'])}",
            f"{'=' * 60}\n"
        ])

        return "\n".join(message_parts)

    @staticmethod
    def _get_available_actions(operation: str) -> list:
        """获取操作类型对应的可用决策"""
        actions_map = {
            "tool_execution": ["approve", "deny", "modify", "abort"],
            "code_generation": ["approve", "regenerate", "modify", "abort"],
            "review_intervention": ["continue", "fix_manually", "skip", "abort"]
        }
        return actions_map.get(operation, ["approve", "deny", "abort"])

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳（UTC ISO 8601）"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat() + "Z"


class RiskAssessor:
    """风险评估器（用于自动判定操作风险等级）"""

    # 高风险工具列表
    HIGH_RISK_TOOLS = {
        "delete_file",
        "remove_directory",
        "execute_shell",
        "write_database",
        "send_email",
        "make_api_call"
    }

    # 中风险工具列表
    MEDIUM_RISK_TOOLS = {
        "write_file",
        "create_directory",
        "move_file",
        "copy_file"
    }

    @staticmethod
    def assess_tool_risk(tool_name: str, tool_args: Dict[str, Any]) -> Literal["low", "medium", "high"]:
        """
        评估工具执行风险

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            风险等级
        """
        if tool_name in RiskAssessor.HIGH_RISK_TOOLS:
            return "high"

        if tool_name in RiskAssessor.MEDIUM_RISK_TOOLS:
            # 检查参数中的敏感路径
            if RiskAssessor._contains_sensitive_path(tool_args):
                return "high"
            return "medium"

        return "low"

    @staticmethod
    def assess_code_risk(code: str, language: str) -> Literal["low", "medium", "high"]:
        """
        评估代码风险

        Args:
            code: 代码内容
            language: 编程语言

        Returns:
            风险等级
        """
        # 简单的静态分析（关键词检测）
        high_risk_keywords = [
            "exec", "eval", "system", "popen", "subprocess",
            "delete", "remove", "unlink", "rmtree",
            "drop table", "truncate", "delete from"
        ]

        code_lower = code.lower()
        for keyword in high_risk_keywords:
            if keyword in code_lower:
                return "high"

        # 检查代码长度（超长代码可能风险更高）
        if len(code) > 1000:
            return "medium"

        return "low"

    @staticmethod
    def _contains_sensitive_path(tool_args: Dict[str, Any]) -> bool:
        """检查参数中是否包含敏感路径"""
        sensitive_paths = [
            "/etc/",
            "/usr/",
            "/System/",
            "/Library/",
            "~/.ssh/",
            "~/.aws/",
            "/var/",
            "C:\\Windows\\",
            "C:\\Program Files\\"
        ]

        # 检查所有字符串参数
        for value in tool_args.values():
            if isinstance(value, str):
                for sensitive in sensitive_paths:
                    if sensitive in value:
                        return True

        return False


# 便捷函数
def create_tool_approval_prompt(
    tool_name: str,
    tool_args: Dict[str, Any],
    subtask_description: str
) -> Dict[str, Any]:
    """
    创建工具执行审批提示（便捷函数）

    Args:
        tool_name: 工具名称
        tool_args: 工具参数
        subtask_description: 子任务描述

    Returns:
        Dict: 审批提示信息
    """
    risk_level = RiskAssessor.assess_tool_risk(tool_name, tool_args)

    details = {
        "tool_name": tool_name,
        "tool_args": tool_args,
        "subtask_description": subtask_description
    }

    return HITLHelper.create_approval_prompt(
        operation="tool_execution",
        details=details,
        risk_level=risk_level
    )


def create_code_approval_prompt(
    code: str,
    language: str,
    subtask_description: str,
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建代码生成审批提示（便捷函数）

    Args:
        code: 生成的代码
        language: 编程语言
        subtask_description: 子任务描述
        file_path: 文件路径

    Returns:
        Dict: 审批提示信息
    """
    risk_level = RiskAssessor.assess_code_risk(code, language)

    details = {
        "code": code,
        "language": language,
        "subtask_description": subtask_description,
        "file_path": file_path or "N/A"
    }

    return HITLHelper.create_approval_prompt(
        operation="code_generation",
        details=details,
        risk_level=risk_level
    )


def create_review_intervention_prompt(
    subtask_description: str,
    failed_code: str,
    reviewer_feedback: str,
    iteration_count: int,
    max_iterations: int
) -> Dict[str, Any]:
    """
    创建审查介入提示（便捷函数）

    Args:
        subtask_description: 子任务描述
        failed_code: 失败的代码
        reviewer_feedback: 审查反馈
        iteration_count: 当前迭代次数
        max_iterations: 最大迭代次数

    Returns:
        Dict: 审批提示信息
    """
    details = {
        "subtask_description": subtask_description,
        "failed_code": failed_code,
        "reviewer_feedback": reviewer_feedback,
        "iteration_count": iteration_count,
        "max_iterations": max_iterations
    }

    return HITLHelper.create_approval_prompt(
        operation="review_intervention",
        details=details,
        risk_level="medium"  # 审查介入默认中风险
    )
