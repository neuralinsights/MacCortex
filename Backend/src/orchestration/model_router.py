"""
MacCortex Model Router - 智能模型选择

根据任务复杂度和 API 可用性，智能选择使用 Claude API 或本地 Ollama 模型。

策略：
1. 如果 ANTHROPIC_API_KEY 可用：
   - 复杂任务（代码生成、架构设计）→ Claude API
   - 简单任务（格式化、总结）→ 本地 Ollama
2. 如果 API Key 不可用：
   - 所有任务 → 本地 Ollama（降级模式）

性能对比：
- Claude API: ~5-15 秒/请求，高质量
- Ollama qwen3:14b: ~30-90 秒/请求，中等质量
"""

import os
from typing import Optional, Tuple, Literal
from enum import Enum
from langchain_core.language_models import BaseChatModel


class TaskComplexity(Enum):
    """任务复杂度级别"""
    SIMPLE = "simple"        # 格式化、摘要、简单问答
    MEDIUM = "medium"        # 代码补全、Bug 修复
    COMPLEX = "complex"      # 架构设计、复杂代码生成


class ModelRouter:
    """
    智能模型路由器

    根据任务复杂度和可用资源选择最佳模型。
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        ollama_model: str = "qwen3:14b",
        ollama_base_url: str = "http://localhost:11434",
        force_local: bool = False
    ):
        """
        初始化路由器

        Args:
            anthropic_api_key: Anthropic API Key（如果为 None，从环境变量获取）
            ollama_model: 本地 Ollama 模型名称
            ollama_base_url: Ollama API 地址
            force_local: 强制使用本地模型（即使有 API Key）
        """
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url
        self.force_local = force_local

        # 检查 Claude API 可用性
        self.claude_available = bool(self.anthropic_api_key) and not force_local

        if self.claude_available:
            print("✅ Claude API 可用，启用智能路由")
        else:
            print("⚠️  Claude API 不可用，使用本地 Ollama 模型")

    def get_model(
        self,
        complexity: TaskComplexity = TaskComplexity.MEDIUM,
        temperature: float = 0.7
    ) -> Tuple[BaseChatModel, str]:
        """
        获取适合任务复杂度的模型

        Args:
            complexity: 任务复杂度
            temperature: 模型温度

        Returns:
            (model, model_name): 模型实例和名称
        """
        # 决定使用哪个模型
        use_claude = self._should_use_claude(complexity)

        if use_claude:
            return self._get_claude_model(temperature), "claude-sonnet-4"
        else:
            return self._get_ollama_model(temperature), f"ollama/{self.ollama_model}"

    def _should_use_claude(self, complexity: TaskComplexity) -> bool:
        """
        判断是否应该使用 Claude

        策略：
        - COMPLEX → 总是用 Claude（如果可用）
        - MEDIUM → 用 Claude（如果可用）
        - SIMPLE → 用本地模型（节省成本）
        """
        if not self.claude_available:
            return False

        # 复杂和中等任务用 Claude
        if complexity in (TaskComplexity.COMPLEX, TaskComplexity.MEDIUM):
            return True

        # 简单任务用本地模型
        return False

    def _get_claude_model(self, temperature: float) -> BaseChatModel:
        """获取 Claude 模型"""
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=temperature,
            api_key=self.anthropic_api_key,
            max_tokens=4096
        )

    def _get_ollama_model(self, temperature: float) -> BaseChatModel:
        """获取 Ollama 本地模型"""
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            model=self.ollama_model,
            temperature=temperature,
            base_url=self.ollama_base_url
        )

    @staticmethod
    def estimate_complexity(task_description: str) -> TaskComplexity:
        """
        估算任务复杂度

        基于任务描述的关键词判断复杂度。

        Args:
            task_description: 任务描述

        Returns:
            TaskComplexity: 估算的复杂度
        """
        task_lower = task_description.lower()

        # 复杂任务关键词
        complex_keywords = [
            "architecture", "设计", "design", "refactor", "重构",
            "optimize", "优化", "system", "系统", "framework", "框架",
            "api", "database", "数据库", "security", "安全",
            "performance", "性能", "scalable", "可扩展"
        ]

        # 简单任务关键词
        simple_keywords = [
            "hello", "print", "simple", "简单", "basic", "基础",
            "format", "格式", "summary", "总结", "list", "列表",
            "rename", "重命名", "copy", "复制"
        ]

        # 检查复杂关键词
        for keyword in complex_keywords:
            if keyword in task_lower:
                return TaskComplexity.COMPLEX

        # 检查简单关键词
        for keyword in simple_keywords:
            if keyword in task_lower:
                return TaskComplexity.SIMPLE

        # 默认中等复杂度
        return TaskComplexity.MEDIUM


# 全局单例
_router: Optional[ModelRouter] = None


def get_model_router(
    force_reinit: bool = False,
    **kwargs
) -> ModelRouter:
    """
    获取全局模型路由器实例（单例模式）

    Args:
        force_reinit: 强制重新初始化
        **kwargs: 传递给 ModelRouter 的参数

    Returns:
        ModelRouter 实例
    """
    global _router

    if _router is None or force_reinit:
        _router = ModelRouter(**kwargs)

    return _router
