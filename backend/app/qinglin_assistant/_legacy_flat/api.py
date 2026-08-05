"""
青柠智能助手 — FastAPI 路由。

本轮（T01 基础设施）实现三个端点：

- ``GET  /health``  模块状态 + 当前 LLM provider + 业务库可达性
- ``GET  /roles``   四角色元信息（供前端渲染）
- ``POST /chat``    最小对话闭环：RBAC 校验 -> LLM 调用 -> 返回

挂载位置见 ``app/main.py``：``prefix="/api/v2/assistant"``。

注意
----
LLM 不可用时返回 **HTTP 503** 并携带清晰错误信息，
**绝不** fallback 到写死的假文案。
"""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.qinglin_assistant import rbac
from app.qinglin_assistant.constants import (
    BRAND_NAME,
    MODULE_NAME,
    MODULE_VERSION,
    real_response,
)
from app.qinglin_assistant.llm import (
    DEFAULT_SYSTEM_PROMPT,
    LLMUnavailableError,
    get_llm_provider,
    probe_providers,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["青柠助手"])


# ── 请求 / 响应模型 ───────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    """对话请求体。"""

    role: str = Field(..., description="角色码：sale / media / engineer / developer")
    session_id: str = Field(..., description="会话 ID，用于按会话隔离上下文")
    message: str = Field(..., description="用户消息内容")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="采样温度")


# ── 内部工具函数 ─────────────────────────────────────────────────────────
def check_database() -> Dict[str, Any]:
    """
    检查青柠业务库是否可达。

    Returns
    -------
    dict
        含 ``reachable`` / ``path`` / ``tables`` / ``total_rows``；
        不可达时含 ``error``。
    """
    db_path = Path(settings.QINGLIN_DB_PATH)
    result: Dict[str, Any] = {"reachable": False, "path": str(db_path)}

    if not db_path.exists():
        result["error"] = f"数据库文件不存在：{db_path}"
        return result

    try:
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            tables: List[str] = [row[0] for row in rows]
            total = 0
            for table in tables:
                total += int(
                    conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                )
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("青柠业务库连接失败: %s", exc)
        result["error"] = f"数据库连接失败：{exc}"
        return result

    result["reachable"] = True
    result["tables"] = tables
    result["table_count"] = len(tables)
    result["total_rows"] = total
    return result


# ── 端点 ─────────────────────────────────────────────────────────────────
@router.get("/health")
async def health() -> Dict[str, Any]:
    """
    模块健康检查。

    Returns
    -------
    dict
        模块状态、LLM provider 探测结果、业务库可达性。
    """
    db_info = check_database()
    llm_info = await probe_providers()

    return real_response(
        {
            "status": "ok",
            "module": MODULE_NAME,
            "brand": BRAND_NAME,
            "version": MODULE_VERSION,
            "db": db_info["reachable"],
            "database": db_info,
            "llm": llm_info,
            "roles": rbac.ALL_ROLES,
            "timestamp": int(time.time()),
        }
    )


@router.get("/roles")
async def get_roles() -> Dict[str, Any]:
    """
    获取全部角色元信息。

    Returns
    -------
    dict
        含 ``total`` 与 ``roles`` 列表。
    """
    roles = rbac.list_roles()
    return real_response({"total": len(roles), "roles": roles})


@router.post("/chat")
async def chat(payload: ChatRequest) -> Dict[str, Any]:
    """
    最小对话闭环：RBAC 校验 -> LLM 调用 -> 返回。

    工具调用与意图识别在 T02 接入（见 ``intent.py`` / ``tools.py``），
    会话记忆持久化在 T02 接入（见 ``memory.py``）。

    Raises
    ------
    HTTPException
        - 400：角色非法 / 消息为空
        - 503：所有 LLM provider 均不可用
        - 500：LLM 调用出现未预期异常
    """
    role = rbac.normalize_role(payload.role)
    if not rbac.is_valid_role(role):
        raise HTTPException(
            status_code=400,
            detail=f"未知角色 {payload.role!r}，合法角色：{rbac.ALL_ROLES}",
        )

    message = (payload.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    # 角色专属系统提示词 + 全局人设
    role_prompt: Optional[str] = rbac.get_system_prompt(role)
    system_prompt = DEFAULT_SYSTEM_PROMPT
    if role_prompt:
        system_prompt = f"{DEFAULT_SYSTEM_PROMPT}\n{role_prompt}"

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    started = time.time()
    try:
        provider = await get_llm_provider()
        reply = await provider.chat(messages, temperature=payload.temperature)
    except LLMUnavailableError as exc:
        # 明确 503，不做任何静默 mock
        raise HTTPException(
            status_code=503,
            detail={
                "error": "LLM_UNAVAILABLE",
                "message": str(exc),
                "hint": (
                    "请启动本地 Ollama 并拉取聊天模型 "
                    f"（{settings.QINGLIN_CHAT_MODEL}），"
                    "或在环境变量中配置 OPENAI_API_KEY 使用云端兜底。"
                ),
            },
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("青柠助手对话失败")
        raise HTTPException(status_code=500, detail=f"对话处理失败：{exc}") from exc

    return real_response(
        {
            "role": role,
            "role_name": rbac.ROLE_METADATA[role]["name"],
            "session_id": payload.session_id,
            "message": message,
            "reply": reply,
            "llm": provider.describe(),
            "elapsed_ms": int((time.time() - started) * 1000),
            "tools_used": [],
        }
    )
