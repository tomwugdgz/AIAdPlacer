"""青柠智能助手 — 会话记忆持久化（sqlite）。

按 ``session_id`` 严格隔离的多轮对话历史。落库路径来自 ``settings.QINGLIN_MEMORY_DB_PATH``，
默认 ``backend/data/qinglin_assistant_memory.db``。

设计要点：
- 每次对话调用 ``save_turn`` 记录一问一答。
- 编排层通过 ``get_history`` 取回最近 N 轮作为 LLM 上下文。
- 所有查询均带 ``session_id`` 过滤，天然实现会话隔离。
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import settings
from app.common import setup_logging

logger = setup_logging("qinglin_memory")


class MemoryStore:
    """基于 sqlite 的会话记忆存储，按 session_id 隔离。"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.QINGLIN_MEMORY_DB_PATH
        parent = os.path.dirname(self.db_path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_reply TEXT NOT NULL,
                    tool_calls TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id, id)"
            )
            conn.commit()
        finally:
            conn.close()

    def save_turn(
        self,
        session_id: str,
        role: str,
        user_message: str,
        assistant_reply: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """持久化一轮对话（一问一答）。"""
        import json

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO turns
                    (session_id, role, user_message, assistant_reply, tool_calls, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    user_message,
                    assistant_reply,
                    json.dumps(tool_calls or [], ensure_ascii=False),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conn.commit()
            logger.debug("已保存会话轮次 session_id=%s role=%s", session_id, role)
        finally:
            conn.close()

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """取回某会话最近 ``limit`` 轮（按时间升序，即先旧后新）。"""
        import json

        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT role, user_message, assistant_reply, tool_calls, created_at
                FROM turns
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
            history: List[Dict[str, Any]] = []
            for row in reversed(rows):
                history.append(
                    {
                        "role": row["role"],
                        "user_message": row["user_message"],
                        "assistant_reply": row["assistant_reply"],
                        "tool_calls": json.loads(row["tool_calls"] or "[]"),
                        "created_at": row["created_at"],
                    }
                )
            return history
        finally:
            conn.close()

    def clear(self, session_id: str) -> int:
        """清空某会话的全部历史，返回删除条数。"""
        conn = self._connect()
        try:
            cur = conn.execute("DELETE FROM turns WHERE session_id = ?", (session_id,))
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()


# 模块级单例，供路由层直接复用
memory_store = MemoryStore()
