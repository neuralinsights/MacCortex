#
# MacCortex - Usage Tracker Tests
# Phase 5 - Multi-LLM Support
# Created: 2026-01-26
#

"""UsageTracker 单元测试"""

from decimal import Decimal

import pytest

from src.llm.models import CostInfo, ProviderType, TokenUsage
from src.llm.usage_tracker import UsageTracker


class TestUsageTracker:
    """UsageTracker 测试"""

    def test_create_empty(self):
        """测试创建空追踪器"""
        tracker = UsageTracker()
        assert tracker.get_total_tokens() == 0
        assert tracker.get_total_cost() == 0.0

    def test_record_single_usage(self):
        """测试记录单次使用"""
        tracker = UsageTracker()
        usage = TokenUsage(100, 200, 300)
        cost = CostInfo(
            Decimal("0.01"),
            Decimal("0.02"),
            Decimal("0.03"),
        )

        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=usage,
            cost=cost,
        )

        assert tracker.get_total_tokens() == 300
        assert tracker.get_total_cost() == pytest.approx(0.03)

    def test_record_multiple_usages(self):
        """测试记录多次使用"""
        tracker = UsageTracker()

        for i in range(3):
            usage = TokenUsage(100, 100, 200)
            cost = CostInfo(
                Decimal("0.01"),
                Decimal("0.01"),
                Decimal("0.02"),
            )
            tracker.record_usage(
                model_id="claude-sonnet-4",
                provider=ProviderType.ANTHROPIC,
                usage=usage,
                cost=cost,
            )

        assert tracker.get_total_tokens() == 600
        assert tracker.get_total_cost() == pytest.approx(0.06)

    def test_record_with_session_id(self):
        """测试按会话记录"""
        tracker = UsageTracker()

        # Session 1
        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=TokenUsage(100, 100, 200),
            cost=CostInfo(Decimal("0.01"), Decimal("0.01"), Decimal("0.02")),
            session_id="session-1",
        )

        # Session 2
        tracker.record_usage(
            model_id="gpt-4o",
            provider=ProviderType.OPENAI,
            usage=TokenUsage(50, 50, 100),
            cost=CostInfo(Decimal("0.005"), Decimal("0.005"), Decimal("0.01")),
            session_id="session-2",
        )

        # 总计
        assert tracker.get_total_tokens() == 300
        assert tracker.get_total_cost() == pytest.approx(0.03)

        # 按会话
        assert tracker.get_total_tokens(session_id="session-1") == 200
        assert tracker.get_total_cost(session_id="session-1") == pytest.approx(0.02)
        assert tracker.get_total_tokens(session_id="session-2") == 100
        assert tracker.get_total_cost(session_id="session-2") == pytest.approx(0.01)

    def test_record_with_agent_name(self):
        """测试按 Agent 记录"""
        tracker = UsageTracker()

        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=TokenUsage(100, 200, 300),
            cost=CostInfo(Decimal("0.01"), Decimal("0.02"), Decimal("0.03")),
            agent_name="planner",
        )

        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=TokenUsage(200, 400, 600),
            cost=CostInfo(Decimal("0.02"), Decimal("0.04"), Decimal("0.06")),
            agent_name="coder",
        )

        by_agent = tracker.get_usage_by_agent()
        assert "planner" in by_agent
        assert "coder" in by_agent
        assert by_agent["planner"]["total_tokens"] == 300
        assert by_agent["coder"]["total_tokens"] == 600

    def test_get_usage_by_model(self):
        """测试按模型统计"""
        tracker = UsageTracker()

        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=TokenUsage(100, 100, 200),
            cost=CostInfo(Decimal("0.01"), Decimal("0.01"), Decimal("0.02")),
        )

        tracker.record_usage(
            model_id="gpt-4o",
            provider=ProviderType.OPENAI,
            usage=TokenUsage(50, 50, 100),
            cost=CostInfo(Decimal("0.005"), Decimal("0.005"), Decimal("0.01")),
        )

        by_model = tracker.get_usage_by_model()
        assert "claude-sonnet-4" in by_model
        assert "gpt-4o" in by_model
        assert by_model["claude-sonnet-4"]["call_count"] == 1
        assert by_model["gpt-4o"]["call_count"] == 1

    def test_get_usage_by_provider(self):
        """测试按 Provider 统计"""
        tracker = UsageTracker()

        # 两次 Anthropic 调用
        for _ in range(2):
            tracker.record_usage(
                model_id="claude-sonnet-4",
                provider=ProviderType.ANTHROPIC,
                usage=TokenUsage(100, 100, 200),
                cost=CostInfo(Decimal("0.01"), Decimal("0.01"), Decimal("0.02")),
            )

        # 一次 Ollama 调用
        tracker.record_usage(
            model_id="qwen3:14b",
            provider=ProviderType.OLLAMA,
            usage=TokenUsage(500, 500, 1000),
            cost=CostInfo.zero(),
        )

        by_provider = tracker.get_usage_by_provider()
        assert by_provider["anthropic"]["call_count"] == 2
        assert by_provider["ollama"]["call_count"] == 1
        assert by_provider["ollama"]["total_cost"] == "0"

    def test_get_stats(self):
        """测试获取统计信息"""
        tracker = UsageTracker()

        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=TokenUsage(100, 200, 300),
            cost=CostInfo(Decimal("0.01"), Decimal("0.02"), Decimal("0.03")),
            session_id="test-session",
            agent_name="planner",
        )

        stats = tracker.get_stats()
        assert stats["total_tokens"] == 300
        assert stats["input_tokens"] == 100
        assert stats["output_tokens"] == 200
        assert stats["call_count"] == 1
        assert "by_model" in stats
        assert "by_provider" in stats
        assert "by_agent" in stats

    def test_get_stats_for_session(self):
        """测试获取特定会话的统计"""
        tracker = UsageTracker()

        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=TokenUsage(100, 200, 300),
            cost=CostInfo(Decimal("0.01"), Decimal("0.02"), Decimal("0.03")),
            session_id="session-1",
        )

        stats = tracker.get_stats(session_id="session-1")
        assert stats["total_tokens"] == 300
        assert stats["call_count"] == 1

        # 不存在的会话
        empty_stats = tracker.get_stats(session_id="non-existent")
        assert empty_stats["total_tokens"] == 0
        assert empty_stats["call_count"] == 0

    def test_get_recent_records(self):
        """测试获取最近记录"""
        tracker = UsageTracker()

        for i in range(10):
            tracker.record_usage(
                model_id=f"model-{i}",
                provider=ProviderType.ANTHROPIC,
                usage=TokenUsage(10, 10, 20),
                cost=CostInfo.zero(),
            )

        # 获取最近 5 条
        records = tracker.get_recent_records(limit=5)
        assert len(records) == 5
        assert records[-1]["model_id"] == "model-9"

    def test_reset_all(self):
        """测试全部重置"""
        tracker = UsageTracker()

        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=TokenUsage(100, 200, 300),
            cost=CostInfo(Decimal("0.01"), Decimal("0.02"), Decimal("0.03")),
        )

        assert tracker.get_total_tokens() == 300

        tracker.reset()

        assert tracker.get_total_tokens() == 0
        assert tracker.get_total_cost() == 0.0

    def test_reset_session(self):
        """测试重置特定会话"""
        tracker = UsageTracker()

        # Session 1
        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=TokenUsage(100, 100, 200),
            cost=CostInfo(Decimal("0.01"), Decimal("0.01"), Decimal("0.02")),
            session_id="session-1",
        )

        # Session 2
        tracker.record_usage(
            model_id="gpt-4o",
            provider=ProviderType.OPENAI,
            usage=TokenUsage(50, 50, 100),
            cost=CostInfo(Decimal("0.005"), Decimal("0.005"), Decimal("0.01")),
            session_id="session-2",
        )

        # 重置 session-1
        tracker.reset(session_id="session-1")

        # Session 1 应该被清除
        assert tracker.get_total_tokens(session_id="session-1") == 0

        # Session 2 应该保留
        assert tracker.get_total_tokens(session_id="session-2") == 100

        # 总计应该只有 session-2
        assert tracker.get_total_tokens() == 100

    def test_max_records_limit(self):
        """测试最大记录限制"""
        tracker = UsageTracker(max_records=5)

        for i in range(10):
            tracker.record_usage(
                model_id=f"model-{i}",
                provider=ProviderType.ANTHROPIC,
                usage=TokenUsage(10, 10, 20),
                cost=CostInfo.zero(),
            )

        records = tracker.get_recent_records(limit=100)
        assert len(records) == 5
        # 最早的记录应该是 model-5（前 5 个被删除）
        assert records[0]["model_id"] == "model-5"

    def test_export_to_json(self):
        """测试导出 JSON"""
        tracker = UsageTracker()

        tracker.record_usage(
            model_id="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            usage=TokenUsage(100, 200, 300),
            cost=CostInfo(Decimal("0.01"), Decimal("0.02"), Decimal("0.03")),
        )

        export = tracker.export_to_json()
        assert "summary" in export
        assert "records" in export
        assert "exported_at" in export
        assert len(export["records"]) == 1

    def test_thread_safety(self):
        """测试线程安全"""
        import threading

        tracker = UsageTracker()
        errors = []

        def record_usage():
            try:
                for _ in range(100):
                    tracker.record_usage(
                        model_id="claude-sonnet-4",
                        provider=ProviderType.ANTHROPIC,
                        usage=TokenUsage(1, 1, 2),
                        cost=CostInfo.zero(),
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_usage) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert tracker.get_total_tokens() == 1000  # 5 threads * 100 * 2 tokens
