"""
青柠智能助手 — 会话记忆（骨架，T02 实现）。

规划能力
--------
- session 级短期记忆（进程内 LRU）
- SQLite 持久化（``settings.QINGLIN_MEMORY_DB_PATH``）
- 严格按 ``session_id`` 隔离，跨会话不可见

本轮只提供可 import 的签名与数据结构，不含实现逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config import settings


@dataclass
class ChatTurn:
    """单轮对话记录。"""

    role: str = ""
    content: str = ""
    timestamp: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionMemory:
    """
    会话记忆管理器（骨架）。

    T02 将实现：进程内缓存 + SQLite 落盘双写，读取时优先命中缓存。
    """

    def __init__(self, db_path: Optional[str] = None, max_turns: int = 20) -> None:
        """
        Parameters
        ----------
        db_path : str | None
            持久化库路径，默认 ``settings.QINGLIN_MEMORY_DB_PATH``。
        max_turns : int
            单会话保留的最大轮数。
        """
        self.db_path: str = db_path or settings.QINGLIN_MEMORY_DB_PATH
        self.max_turns: int = max_turns
        self._cache: Dict[str, List[ChatTurn]] = {}

    def init_schema(self) -> None:
        """初始化持久化表结构。TODO(T02): 建 sessions / turns 表。"""
        raise NotImplementedError("memory.init_schema 将在 T02 实现")

    def append(self, session_id: str, turn: ChatTurn) -> None:
        """追加一轮对话。TODO(T02): 写缓存 + 落盘。"""
        raise NotImplementedError("memory.append 将在 T02 实现")

    def history(self, session_id: str, limit: int = 10) -> List[ChatTurn]:
        """读取最近 N 轮历史。TODO(T02): 缓存命中 + 回源 SQLite。"""
        raise NotImplementedError("memory.history 将在 T02 实现")

    def clear(self, session_id: str) -> None:
        """清空指定会话。TODO(T02): 删缓存 + 删库中记录。"""
        raise NotImplementedError("memory.clear 将在 T02 实现")


#: 全局单例（与仓库既有 ollama_client 风格一致）
session_memory = SessionMemory()
