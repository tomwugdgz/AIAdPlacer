"""青柠智能助手 — API 路由。

挂载位置：``app/main.py`` 中以 ``prefix=\"/api/v2/assistant\"`` 注册。
对外端点：``POST /api/v2/assistant/chat``。

调用时序（与架构设计一致）：
消息 → check_permission(RBAC) → get_history(memory) → IntentRecognizer(generate_json/规则)
→ 工具编排(kb_tools 真查 / skills 文档生成 / workflows 演示态) → LLMClient.chat 合成
→ save_turn(memory) → 返回。

关键约束：
- RBAC 越权直接拦截，绝不访问底层 DB。
- 知识库查询走真实 DB，数字可核对（即使 LLM 不可用也返回 200 + 真实数字）。
- 报备 / 锁点 / 导点返回体带 ``demo: true`` 且文案标注「演示态」。
- 纯对话（general）依赖 LLM：若 LLM 后端（Ollama）不可用，**明确返回 503 + 清晰错误**，
  绝不静默 mock（team-lead 验收硬约束）。
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.common import format_error_response, generate_request_id, setup_logging
from app.config import settings
from app.qinglin_assistant.constants import BRAND_NAME, MODULE_NAME
from app.qinglin_assistant.rbac.policy import (
    ACTION_CLIENT_QUERY,
    ACTION_DOC_GENERATE,
    ACTION_GENERAL,
    ACTION_MAP_QUERY,
    ACTION_POINT_COUNT,
    ACTION_POINT_EXPORT,
    ACTION_POINT_LOCK,
    ACTION_POINT_QUERY,
    ACTION_REPORT_SUBMIT,
    ACTION_SANDBOX_EXEC,
    Role,
    check_permission,
    is_demo_action,
    list_roles,
    mask_records,
)
from app.qinglin_assistant.intent.recognizer import IntentRecognizer
from app.qinglin_assistant.llm.provider import get_llm_client
from app.qinglin_assistant.memory.store import memory_store
from app.qinglin_assistant.prompts import load_system_prompt
from app.qinglin_assistant.sandbox.bash_tool import bash_sandbox
from app.qinglin_assistant.tools.aux_tools import MapGeocodeTool, MapPoiTool
from app.qinglin_assistant.tools.base import ToolContext
from app.qinglin_assistant.tools.kb_tools import KnowledgeBaseTool
from app.qinglin_assistant.workflows.point_doc import generate_document_orchestration
from app.qinglin_assistant.workflows.sale_media import export_point, lock_point, submit_report

logger = setup_logging("qinglin_api")

router = APIRouter()


# ─────────────────────────────────────────────────────────────
# 请求 / 响应模型（匹配契约）
# ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    role: str = Field(..., description="角色：sale/media/engineer/developer")
    session_id: str = Field(..., description="会话 ID，按会话隔离记忆")
    message: str = Field(..., description="用户消息")


class ChatResponseData(BaseModel):
    session_id: str
    role: str
    content: str
    tool_calls: List[Dict[str, Any]] = []
    demo_mode: bool = False
    demo: bool = False
    masked_fields: List[str] = []
    permission_denied: bool = False


class ChatResponse(BaseModel):
    success: bool = True
    request_id: str
    data: ChatResponseData


# ─────────────────────────────────────────────────────────────
# 基础设施端点（健康检查 / 角色清单）
# ─────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    """基础设施健康检查。

    返回数据库可达性与 LLM 后端可用性。该端点**永远返回 200**（即便底层依赖异常，
    也会在响应体中如实标记）；503 仅用于需要 LLM 的 ``/chat`` 纯对话请求。
    """
    db_path = getattr(settings, "QINGLIN_DB_PATH", "")
    db_ok = False
    table_count = 0
    row_count = 0
    try:
        if db_path and os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            try:
                cur = conn.cursor()
                tables = [
                    r[0]
                    for r in cur.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                ]
                table_count = len(tables)
                for t in tables:
                    try:
                        row_count += cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                    except sqlite3.Error:
                        pass
                db_ok = table_count > 0
            finally:
                conn.close()
    except Exception as e:  # noqa: BLE001
        logger.warning("health DB 检查失败: %s", e)
        db_ok = False

    llm_available = False
    try:
        client = get_llm_client()
        llm_available = await asyncio.wait_for(client.is_available(), timeout=5.0)
    except Exception:  # noqa: BLE001
        llm_available = False

    return {
        "status": "ok",
        "module": MODULE_NAME,
        "brand": BRAND_NAME,
        "db": db_ok,
        "database": db_path,
        "db_tables": table_count,
        "db_rows": row_count,
        "llm": {
            "provider": settings.LLM_PROVIDER,
            "model": settings.QINGLIN_CHAT_MODEL,
            "available": llm_available,
        },
        "roles": len(list_roles()),
    }


@router.get("/roles")
async def roles():
    """返回四角色（sale / media / engineer / developer）及其能力清单。"""
    role_list = list_roles()
    return {"count": len(role_list), "roles": role_list}


# ─────────────────────────────────────────────────────────────
# 内部辅助
# ─────────────────────────────────────────────────────────────

_RECOGNIZER = IntentRecognizer()


def _collect_raw_records(kb_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for key in ("points", "clients", "led_points"):
        block = kb_data.get(key)
        if isinstance(block, dict):
            records.extend(block.get("records", []))
    return records


async def _general_answer(message: str, role: str, session_id: str) -> str:
    """通用问答的 LLM 合成。

    调用方（``/chat`` 的 GENERAL 分支）需先通过 ``is_available`` 闸门确认 LLM 可用；
    本函数仅负责发起对话合成，LLM 异常时直接抛出，由端点统一返回错误，**不**静默降级模板。
    """
    client = get_llm_client()
    history = memory_store.get_history(session_id, limit=6)
    convo: List[Dict[str, str]] = [{"role": "system", "content": load_system_prompt(role)}]
    for h in history:
        convo.append({"role": "user", "content": h["user_message"]})
        convo.append({"role": "assistant", "content": h["assistant_reply"]})
    convo.append({"role": "user", "content": message})
    text = await asyncio.wait_for(client.chat(convo, temperature=0.7), timeout=25.0)
    if not text or not text.strip():
        raise RuntimeError("LLM 返回空响应")
    return text.strip()


# ─────────────────────────────────────────────────────────────
# 端点
# ─────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    """青柠智能助手对话端点。"""
    request_id = generate_request_id("qinglin")
    role = (req.role or "").strip().lower()

    # 1) 角色合法性校验
    role_obj = Role.from_str(role)
    if role_obj is None:
        return ChatResponse(
            success=False,
            request_id=request_id,
            data=ChatResponseData(
                session_id=req.session_id,
                role=role,
                content=(
                    "角色非法。可选角色：sale（销售）/ media（媒介）/ "
                    "engineer（工程）/ developer（商业开发）。"
                ),
                permission_denied=True,
            ),
        )

    try:
        # 2) 意图识别（LLM 优先，规则降级）
        intent = await _RECOGNIZER.recognize(req.message, role)
        action = intent.get("action", ACTION_GENERAL)
        params = intent.get("params") or {}

        # 3) RBAC 越权闸门 —— 返回 False 时直接拦截，绝不访问底层 DB
        if not check_permission(role_obj, action):
            logger.info("RBAC 拦截 role=%s action=%s", role, action)
            return ChatResponse(
                success=True,
                request_id=request_id,
                data=ChatResponseData(
                    session_id=req.session_id,
                    role=role,
                    content=(
                        f"⛔ 权限不足：角色「{role_obj.value}」无权执行动作「{action}」。"
                        "该操作已被拦截，未访问任何底层数据。"
                    ),
                    tool_calls=[{"tool": "rbac", "action": action, "allowed": False}],
                    permission_denied=True,
                ),
            )

        # 4) 编排
        tool_calls: List[Dict[str, Any]] = []
        masked_fields: List[str] = []
        demo_mode = is_demo_action(action)
        content = ""
        ctx = ToolContext(role=role, session_id=req.session_id, params=params, action=action)

        if action in (ACTION_POINT_QUERY, ACTION_POINT_COUNT, ACTION_CLIENT_QUERY):
            res = await KnowledgeBaseTool().run(ctx)
            content = res.content
            tool_calls.append(res.to_dict())
            _, masked_fields = mask_records(role, _collect_raw_records(res.data))

        elif action == ACTION_MAP_QUERY:
            if params.get("address"):
                res = await MapGeocodeTool().run(ctx)
            else:
                res = await MapPoiTool().run(ctx)
            content = res.content
            tool_calls.append(res.to_dict())

        elif action == ACTION_REPORT_SUBMIT:
            res = await submit_report(role, req.session_id, params)
            content = res.content
            tool_calls.append(res.to_dict())

        elif action == ACTION_POINT_LOCK:
            res = await lock_point(role, req.session_id, params)
            content = res.content
            tool_calls.append(res.to_dict())

        elif action == ACTION_POINT_EXPORT:
            res = await export_point(role, req.session_id, params)
            content = res.content
            tool_calls.append(res.to_dict())

        elif action == ACTION_DOC_GENERATE:
            res = await generate_document_orchestration(role, req.session_id, params)
            content = res.content
            tool_calls.append(res.to_dict())

        elif action == ACTION_SANDBOX_EXEC:
            cmd = params.get("command") or ""
            res = await bash_sandbox.run(cmd)
            out = (res.get("stdout") or res.get("reason") or "").strip()
            content = f"沙箱执行{'成功' if res.get('success') else '失败'}（exit={res.get('exit_code')}）：{out[:1500]}"
            tool_calls.append({"tool": "sandbox", "demo": False, "result": res})

        else:  # ACTION_GENERAL —— 纯对话，必须依赖 LLM
            client = get_llm_client()
            llm_available = False
            try:
                llm_available = await asyncio.wait_for(client.is_available(), timeout=5.0)
            except Exception:  # noqa: BLE001
                llm_available = False
            if not llm_available:
                # 验收硬约束：LLM 不可用不得静默 mock，必须明确 503
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "LLM_UNAVAILABLE",
                        "message": (
                            "LLM 后端（Ollama）当前不可用，无法处理纯对话请求。"
                            "请确认 Ollama 已启动且模型已加载，或在 .env 配置 OPENAI_API_KEY "
                            "切换 OpenAI 兼容云端。"
                        ),
                        "provider": settings.LLM_PROVIDER,
                        "model": settings.QINGLIN_CHAT_MODEL,
                        "request_id": request_id,
                    },
                )
            content = await _general_answer(req.message, role, req.session_id)
            tool_calls.append({"tool": "llm_general", "demo": False})

        # 5) 记忆持久化（按 session_id 隔离）
        try:
            memory_store.save_turn(req.session_id, role, req.message, content, tool_calls=tool_calls)
        except Exception as e:  # noqa: BLE001
            logger.warning("会话记忆保存失败（不影响本次响应）: %s", e)

        return ChatResponse(
            success=True,
            request_id=request_id,
            data=ChatResponseData(
                session_id=req.session_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
                demo_mode=demo_mode,
                demo=demo_mode,
                masked_fields=masked_fields,
            ),
        )

    except HTTPException:
        # 验收硬约束：LLM 不可用的 503 等由 FastAPI 直接对外，绝不吞掉改成 200
        raise
    except Exception as e:  # noqa: BLE001
        logger.exception("青柠助手 /chat 处理异常")
        return _error_response(req, request_id, e)


def _error_response(req: ChatRequest, request_id: str, error: Exception):
    err = format_error_response(error, request_id=request_id)
    return ChatResponse(
        success=False,
        request_id=request_id,
        data=ChatResponseData(
            session_id=req.session_id,
            role=req.role,
            content=f"服务异常：{err.get('error', {}).get('message', str(error))}",
        ),
    )
