"""
MacCortex Backend - Base Pattern
Phase 1 - Week 2 Day 8-9
创建时间: 2026-01-20

Python Pattern 基类定义
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePattern(ABC):
    """AI Pattern 基类"""

    def __init__(self):
        """初始化 Pattern"""
        pass

    @property
    @abstractmethod
    def pattern_id(self) -> str:
        """Pattern ID（唯一标识符）"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Pattern 名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Pattern 描述"""
        pass

    @property
    def version(self) -> str:
        """Pattern 版本"""
        return "1.0.0"

    @abstractmethod
    async def execute(
        self, text: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行 Pattern

        Args:
            text: 输入文本
            parameters: 参数字典

        Returns:
            Dict[str, Any]: 执行结果
                {
                    "output": str,           # 输出文本
                    "metadata": Dict[str, Any] | None,  # 元数据
                }

        Raises:
            ValueError: 参数无效
            RuntimeError: 执行失败
        """
        pass

    def validate(self, text: str, parameters: Dict[str, Any]) -> bool:
        """
        验证输入

        Args:
            text: 输入文本
            parameters: 参数字典

        Returns:
            bool: 是否有效
        """
        # 基本验证
        if not text or not text.strip():
            return False

        return True

    async def initialize(self):
        """初始化资源（如加载模型）"""
        pass

    async def cleanup(self):
        """清理资源"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }
