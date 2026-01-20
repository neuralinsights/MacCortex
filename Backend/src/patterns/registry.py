"""
MacCortex Backend - Pattern Registry
Phase 1 - Week 2 Day 8-9
创建时间: 2026-01-20

Pattern 注册表，管理所有 Python Pattern 实例
"""

from typing import Any, Dict, List

from loguru import logger

from patterns.base import BasePattern
from patterns.summarize import SummarizePattern


class PatternRegistry:
    """Pattern 注册表"""

    def __init__(self):
        """初始化注册表"""
        self._patterns: Dict[str, BasePattern] = {}
        self._initialized = False

    async def initialize(self):
        """初始化所有 Pattern"""
        if self._initialized:
            return

        logger.info("🔧 初始化 Pattern Registry...")

        # 注册默认 Pattern
        patterns = [
            SummarizePattern(),
            # 其他 Pattern 将在后续添加
        ]

        for pattern in patterns:
            await self._register(pattern)

        self._initialized = True
        logger.info(f"✅ 已注册 {len(self._patterns)} 个 Pattern")

    async def _register(self, pattern: BasePattern):
        """
        注册 Pattern

        Args:
            pattern: Pattern 实例

        Raises:
            ValueError: 如果 ID 已存在
        """
        if pattern.pattern_id in self._patterns:
            raise ValueError(f"Pattern '{pattern.pattern_id}' already registered")

        # 初始化 Pattern
        await pattern.initialize()

        self._patterns[pattern.pattern_id] = pattern
        logger.debug(f"  ✓ 已注册: {pattern.pattern_id} - {pattern.name}")

    async def execute(
        self, pattern_id: str, text: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行 Pattern

        Args:
            pattern_id: Pattern ID
            text: 输入文本
            parameters: 参数字典

        Returns:
            Dict[str, Any]: 执行结果

        Raises:
            ValueError: Pattern 不存在或参数无效
            RuntimeError: 执行失败
        """
        # 检查 Pattern 是否存在
        if pattern_id not in self._patterns:
            available = ", ".join(self._patterns.keys())
            raise ValueError(
                f"Pattern '{pattern_id}' not found. Available: {available}"
            )

        pattern = self._patterns[pattern_id]

        # 验证输入
        if not pattern.validate(text, parameters):
            raise ValueError(f"Invalid input for pattern '{pattern_id}'")

        # 执行
        try:
            result = await pattern.execute(text, parameters)
            return result
        except Exception as e:
            logger.error(f"Pattern '{pattern_id}' execution failed: {e}")
            raise RuntimeError(f"Pattern execution failed: {e}") from e

    def list_patterns(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的 Pattern

        Returns:
            List[Dict[str, Any]]: Pattern 信息列表
        """
        return [pattern.to_dict() for pattern in self._patterns.values()]

    def get_pattern(self, pattern_id: str) -> BasePattern | None:
        """
        获取 Pattern 实例

        Args:
            pattern_id: Pattern ID

        Returns:
            BasePattern | None: Pattern 实例（如果存在）
        """
        return self._patterns.get(pattern_id)

    async def cleanup(self):
        """清理所有 Pattern 资源"""
        logger.info("🧹 清理 Pattern 资源...")
        for pattern in self._patterns.values():
            try:
                await pattern.cleanup()
            except Exception as e:
                logger.warning(f"清理 {pattern.pattern_id} 失败: {e}")

        self._patterns.clear()
        self._initialized = False
