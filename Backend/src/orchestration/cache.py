"""
MacCortex Token Cache - LLM 响应缓存

通过缓存 LLM 响应减少重复调用，节省成本和时间。

适用场景：
1. 相同的 Planner 任务拆解（相似用户输入）
2. 常见代码模板生成（Hello World、CRUD 操作等）
3. 重复的 Reviewer 审查模式

缓存策略：
- 基于 (system_prompt_hash + user_prompt_hash) 的键值缓存
- LRU 淘汰策略（最多保留 100 条）
- 可选的持久化（JSON 文件）
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from collections import OrderedDict
from dataclasses import dataclass, asdict


@dataclass
class CacheEntry:
    """缓存条目"""
    response: str
    timestamp: float
    hit_count: int
    model_name: str


class LLMCache:
    """LLM 响应缓存"""

    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: int = 3600 * 24 * 7,  # 默认7天过期
        cache_file: Optional[Path] = None
    ):
        """
        初始化缓存

        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存过期时间（秒）
            cache_file: 持久化文件路径（None 则不持久化）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache_file = cache_file

        # LRU 缓存（OrderedDict 保证插入顺序）
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # 统计信息
        self.hits = 0
        self.misses = 0

        # 从文件加载缓存
        if cache_file and cache_file.exists():
            self._load_from_file()

    def get(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Optional[str]:
        """
        获取缓存的响应

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            缓存的响应（如果存在且未过期），否则 None
        """
        key = self._generate_key(system_prompt, user_prompt)

        if key not in self._cache:
            self.misses += 1
            return None

        entry = self._cache[key]

        # 检查是否过期
        if time.time() - entry.timestamp > self.ttl_seconds:
            del self._cache[key]
            self.misses += 1
            return None

        # 命中，更新统计和 LRU 顺序
        entry.hit_count += 1
        self.hits += 1
        self._cache.move_to_end(key)  # LRU：移到最后

        return entry.response

    def set(
        self,
        system_prompt: str,
        user_prompt: str,
        response: str,
        model_name: str = "unknown"
    ):
        """
        保存响应到缓存

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            response: LLM 响应
            model_name: 模型名称
        """
        key = self._generate_key(system_prompt, user_prompt)

        # 如果已存在，更新
        if key in self._cache:
            self._cache[key].response = response
            self._cache[key].timestamp = time.time()
            self._cache.move_to_end(key)
        else:
            # 新增条目
            entry = CacheEntry(
                response=response,
                timestamp=time.time(),
                hit_count=0,
                model_name=model_name
            )
            self._cache[key] = entry

            # LRU 淘汰
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)  # 移除最早的

        # 持久化
        if self.cache_file:
            self._save_to_file()

    def _generate_key(self, system_prompt: str, user_prompt: str) -> str:
        """生成缓存键（SHA256 哈希）"""
        combined = f"{system_prompt}||{user_prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _save_to_file(self):
        """保存缓存到文件"""
        if not self.cache_file:
            return

        data = {
            "version": "1.0",
            "timestamp": time.time(),
            "stats": {
                "hits": self.hits,
                "misses": self.misses,
                "size": len(self._cache)
            },
            "entries": {
                key: asdict(entry) for key, entry in self._cache.items()
            }
        }

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def _load_from_file(self):
        """从文件加载缓存"""
        if not self.cache_file or not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)

            # 恢复统计信息
            stats = data.get("stats", {})
            self.hits = stats.get("hits", 0)
            self.misses = stats.get("misses", 0)

            # 恢复条目
            entries = data.get("entries", {})
            for key, entry_dict in entries.items():
                entry = CacheEntry(**entry_dict)

                # 检查是否过期
                if time.time() - entry.timestamp <= self.ttl_seconds:
                    self._cache[key] = entry

            print(f"✅ 从缓存文件加载 {len(self._cache)} 条记录")

        except Exception as e:
            print(f"⚠️  缓存文件加载失败：{e}")

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

        if self.cache_file and self.cache_file.exists():
            self.cache_file.unlink()

    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1%}",
            "total_requests": total_requests
        }


# 全局单例缓存（可选）
_global_cache: Optional[LLMCache] = None


def get_global_cache() -> LLMCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        cache_dir = Path.home() / ".maccortex" / "cache"
        _global_cache = LLMCache(
            max_size=100,
            ttl_seconds=3600 * 24 * 7,  # 7 天
            cache_file=cache_dir / "llm_cache.json"
        )
    return _global_cache


def clear_global_cache():
    """清空全局缓存"""
    global _global_cache
    if _global_cache:
        _global_cache.clear()
    _global_cache = None
