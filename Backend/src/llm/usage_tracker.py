#
# MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
# Copyright (c) 2026 Yu Geng. All rights reserved.
#
# Usage Tracker
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""
UsageTracker - Token 使用量与成本追踪器

核心功能：
- 实时 Token 计数
- 成本累计计算
- 按会话/Agent/模型分组统计
- 使用量导出与报告
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from threading import RLock
from typing import Optional

from .models import CostInfo, ProviderType, TokenUsage

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """单次使用记录"""

    model_id: str
    provider: ProviderType
    usage: TokenUsage
    cost: CostInfo
    session_id: Optional[str]
    agent_name: Optional[str]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "model_id": self.model_id,
            "provider": self.provider.value,
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
                "total_tokens": self.usage.total_tokens,
            },
            "cost": {
                "input_cost": str(self.cost.input_cost),
                "output_cost": str(self.cost.output_cost),
                "total_cost": str(self.cost.total_cost),
            },
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
        }


class UsageTracker:
    """
    使用量追踪器

    线程安全的 Token 使用量与成本追踪

    Example:
        >>> tracker = UsageTracker()
        >>> tracker.record_usage(
        ...     model_id="claude-sonnet-4",
        ...     provider=ProviderType.ANTHROPIC,
        ...     usage=TokenUsage(100, 200, 300),
        ...     cost=CostInfo(...),
        ...     session_id="session-123"
        ... )
        >>> print(tracker.get_total_cost())
    """

    def __init__(self, max_records: int = 10000):
        """
        初始化追踪器

        Args:
            max_records: 最大记录数量（超出时删除旧记录）
        """
        self._records: list[UsageRecord] = []
        self._lock = RLock()  # 使用可重入锁，支持嵌套调用（如 export_to_json -> get_stats）
        self._max_records = max_records

        # 累计统计（避免遍历所有记录）
        self._total_usage = TokenUsage.zero()
        self._total_cost = CostInfo.zero()

        # 按维度分组的累计值
        self._by_session: dict[str, dict] = {}
        self._by_model: dict[str, dict] = {}
        self._by_agent: dict[str, dict] = {}
        self._by_provider: dict[ProviderType, dict] = {}

    def record_usage(
        self,
        model_id: str,
        provider: ProviderType,
        usage: TokenUsage,
        cost: CostInfo,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> None:
        """
        记录使用量

        Args:
            model_id: 模型 ID
            provider: Provider 类型
            usage: Token 使用量
            cost: 成本信息
            session_id: 会话 ID
            agent_name: Agent 名称
        """
        record = UsageRecord(
            model_id=model_id,
            provider=provider,
            usage=usage,
            cost=cost,
            session_id=session_id,
            agent_name=agent_name,
        )

        with self._lock:
            # 添加记录
            self._records.append(record)

            # 限制记录数量
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records:]

            # 更新累计值
            self._total_usage = self._total_usage + usage
            self._total_cost = self._total_cost + cost

            # 更新分组统计
            self._update_group_stats(
                self._by_model, model_id, usage, cost
            )
            self._update_group_stats(
                self._by_provider, provider, usage, cost
            )

            if session_id:
                self._update_group_stats(
                    self._by_session, session_id, usage, cost
                )

            if agent_name:
                self._update_group_stats(
                    self._by_agent, agent_name, usage, cost
                )

        logger.debug(
            f"Recorded usage: model={model_id}, "
            f"tokens={usage.total_tokens}, "
            f"cost={cost.formatted_total}"
        )

    def _update_group_stats(
        self,
        group_dict: dict,
        key,
        usage: TokenUsage,
        cost: CostInfo,
    ) -> None:
        """更新分组统计"""
        if key not in group_dict:
            group_dict[key] = {
                "usage": TokenUsage.zero(),
                "cost": CostInfo.zero(),
                "count": 0,
            }

        stats = group_dict[key]
        stats["usage"] = stats["usage"] + usage
        stats["cost"] = stats["cost"] + cost
        stats["count"] += 1

    def get_total_usage(self) -> TokenUsage:
        """获取总 Token 使用量"""
        with self._lock:
            return self._total_usage

    def get_total_cost(self, session_id: Optional[str] = None) -> float:
        """获取总成本（USD）"""
        with self._lock:
            if session_id:
                if session_id in self._by_session:
                    return float(self._by_session[session_id]["cost"].total_cost)
                return 0.0  # 会话不存在时返回 0
            return float(self._total_cost.total_cost)

    def get_total_tokens(self, session_id: Optional[str] = None) -> int:
        """获取总 Token 数"""
        with self._lock:
            if session_id:
                if session_id in self._by_session:
                    return self._by_session[session_id]["usage"].total_tokens
                return 0  # 会话不存在时返回 0
            return self._total_usage.total_tokens

    def get_stats(self, session_id: Optional[str] = None) -> dict:
        """
        获取统计信息

        Args:
            session_id: 会话 ID（可选，获取特定会话的统计）

        Returns:
            dict: 统计信息字典
        """
        with self._lock:
            if session_id:
                session_stats = self._by_session.get(session_id)
                if not session_stats:
                    return {
                        "total_tokens": 0,
                        "total_cost": "0.000000",
                        "call_count": 0,
                    }
                return {
                    "total_tokens": session_stats["usage"].total_tokens,
                    "input_tokens": session_stats["usage"].input_tokens,
                    "output_tokens": session_stats["usage"].output_tokens,
                    "total_cost": str(session_stats["cost"].total_cost),
                    "formatted_cost": session_stats["cost"].formatted_total,
                    "call_count": session_stats["count"],
                }

            return {
                "total_tokens": self._total_usage.total_tokens,
                "input_tokens": self._total_usage.input_tokens,
                "output_tokens": self._total_usage.output_tokens,
                "total_cost": str(self._total_cost.total_cost),
                "formatted_cost": self._total_cost.formatted_total,
                "call_count": len(self._records),
                "by_model": self._format_group_stats(self._by_model),
                "by_provider": self._format_group_stats(self._by_provider),
                "by_agent": self._format_group_stats(self._by_agent),
            }

    def _format_group_stats(self, group_dict: dict) -> dict:
        """格式化分组统计"""
        result = {}
        for key, stats in group_dict.items():
            key_str = key.value if isinstance(key, ProviderType) else str(key)
            result[key_str] = {
                "total_tokens": stats["usage"].total_tokens,
                "input_tokens": stats["usage"].input_tokens,
                "output_tokens": stats["usage"].output_tokens,
                "total_cost": str(stats["cost"].total_cost),
                "call_count": stats["count"],
            }
        return result

    def get_usage_by_agent(self) -> dict[str, dict]:
        """获取按 Agent 分组的使用统计"""
        with self._lock:
            return self._format_group_stats(self._by_agent)

    def get_usage_by_model(self) -> dict[str, dict]:
        """获取按模型分组的使用统计"""
        with self._lock:
            return self._format_group_stats(self._by_model)

    def get_usage_by_provider(self) -> dict[str, dict]:
        """获取按 Provider 分组的使用统计"""
        with self._lock:
            return self._format_group_stats(self._by_provider)

    def get_recent_records(
        self,
        limit: int = 100,
        session_id: Optional[str] = None,
    ) -> list[dict]:
        """
        获取最近的使用记录

        Args:
            limit: 返回数量限制
            session_id: 会话 ID 过滤

        Returns:
            list[dict]: 使用记录列表
        """
        with self._lock:
            records = self._records[-limit:]
            if session_id:
                records = [r for r in records if r.session_id == session_id]
            return [r.to_dict() for r in records]

    def reset(self, session_id: Optional[str] = None) -> None:
        """
        重置统计

        Args:
            session_id: 会话 ID（可选，仅重置特定会话）
        """
        with self._lock:
            if session_id:
                # 仅重置特定会话
                if session_id in self._by_session:
                    del self._by_session[session_id]
                # 从记录中移除该会话的记录
                self._records = [
                    r for r in self._records if r.session_id != session_id
                ]
                # 重新计算总计
                self._recalculate_totals()
            else:
                # 全部重置
                self._records.clear()
                self._total_usage = TokenUsage.zero()
                self._total_cost = CostInfo.zero()
                self._by_session.clear()
                self._by_model.clear()
                self._by_agent.clear()
                self._by_provider.clear()

        logger.info(f"Reset usage stats (session_id={session_id})")

    def _recalculate_totals(self) -> None:
        """重新计算总计（移除会话后调用）"""
        self._total_usage = TokenUsage.zero()
        self._total_cost = CostInfo.zero()
        self._by_model.clear()
        self._by_agent.clear()
        self._by_provider.clear()
        self._by_session.clear()  # 也需要重建 session 统计

        for record in self._records:
            self._total_usage = self._total_usage + record.usage
            self._total_cost = self._total_cost + record.cost
            self._update_group_stats(
                self._by_model, record.model_id, record.usage, record.cost
            )
            self._update_group_stats(
                self._by_provider, record.provider, record.usage, record.cost
            )
            if record.agent_name:
                self._update_group_stats(
                    self._by_agent, record.agent_name, record.usage, record.cost
                )
            if record.session_id:
                self._update_group_stats(
                    self._by_session, record.session_id, record.usage, record.cost
                )

    def export_to_json(self) -> dict:
        """导出完整统计数据为 JSON"""
        with self._lock:
            return {
                "summary": self.get_stats(),
                "records": [r.to_dict() for r in self._records],
                "exported_at": datetime.now().isoformat(),
            }

    def __repr__(self) -> str:
        return (
            f"<UsageTracker "
            f"tokens={self._total_usage.total_tokens} "
            f"cost={self._total_cost.formatted_total}>"
        )
