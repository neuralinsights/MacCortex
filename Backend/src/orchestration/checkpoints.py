"""
MacCortex Checkpoints - LangGraph Checkpoint Wrappers

This module provides checkpoint implementations for LangGraph state persistence.
Updated for LangGraph 1.0+ API compatibility.
"""

from langgraph.checkpoint.memory import MemorySaver

# 为了保持向后兼容，提供 InMemorySaver 别名
InMemorySaver = MemorySaver

__all__ = ["InMemorySaver", "MemorySaver"]
