"""青柠智能助手 — 报备 / 锁点 / 导点工作流（演示态）。

这三个动作属于「框架 + 模拟」：返回体**必须**带 ``demo: true``，并在文案中明确标注
「演示态」，同时把所有调用写入审计日志 ``backend/data/audit/qinglin_assistant.log``。

注意：RBAC 已由上层拦截，本模块只在「已授权」的前提下被调用；即便被调用，也只产生
模拟结果，绝不落地任何真实资源变更。
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime
from typing import Any, Dict

from app.config import settings
from app.common import setup_logging
from app.qinglin_assistant.tools.base import ToolResult

logger = setup_logging("qinglin_sale_media")

# 审计日志目录与文件（轻量留痕）
_AUDIT_DIR = os.path.join(os.path.dirname(settings.QINGLIN_MEMORY_DB_PATH), "audit")
_AUDIT_FILE = os.path.join(_AUDIT_DIR, "qinglin_assistant.log")
os.makedirs(_AUDIT_DIR, exist_ok=True)
_audit_lock = threading.Lock()


def write_audit(entry: Dict[str, Any]) -> None:
    """追加一条审计日志（JSON 行）。"""
    entry.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
    entry.setdefault("demo", True)
    try:
        with _audit_lock:
            with open(_AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        logger.error("审计日志写入失败: %s", e)


def _demo_id(prefix: str) -> str:
    return f"DEMO-{prefix}-{uuid.uuid4().hex[:8].upper()}"


async def submit_report(role: str, session_id: str, params: Dict[str, Any]) -> ToolResult:
    """报备（演示态）。"""
    rid = _demo_id("RPT")
    subject = params.get("keyword") or params.get("client") or "客户/项目"
    write_audit({
        "role": role, "session_id": session_id, "action": "report_submit",
        "demo": True, "subject": subject, "report_id": rid,
    })
    return ToolResult(
        tool_name="sale_media_report",
        success=True,
        demo=True,
        content=(
            f"【演示态】已收到您的报备请求（对象：{subject}）。当前为演示环境，"
            f"真实报备将进入 CRM 工单流转并由商务跟进。报备编号：{rid}。"
        ),
        data={"demo": True, "action": "report_submit", "report_id": rid, "subject": subject},
    )


async def lock_point(role: str, session_id: str, params: Dict[str, Any]) -> ToolResult:
    """锁点（演示态）。"""
    lid = _demo_id("LOCK")
    point_type = params.get("point_type") or "点位"
    city = params.get("city") or "指定城市"
    write_audit({
        "role": role, "session_id": session_id, "action": "point_lock",
        "demo": True, "point_type": point_type, "city": city, "lock_id": lid,
    })
    return ToolResult(
        tool_name="sale_media_lock",
        success=True,
        demo=True,
        content=(
            f"【演示态】点位锁定申请已受理（{city} · {point_type}）。演示环境下不实际锁定资源，"
            f"真实锁点需商务在排期中台操作。锁定申请编号：{lid}。"
        ),
        data={"demo": True, "action": "point_lock", "lock_id": lid, "point_type": point_type, "city": city},
    )


async def export_point(role: str, session_id: str, params: Dict[str, Any]) -> ToolResult:
    """导点（演示态）。"""
    eid = _demo_id("EXP")
    point_type = params.get("point_type") or "点位"
    city = params.get("city") or "指定城市"
    write_audit({
        "role": role, "session_id": session_id, "action": "point_export",
        "demo": True, "point_type": point_type, "city": city, "export_id": eid,
    })
    return ToolResult(
        tool_name="sale_media_export",
        success=True,
        demo=True,
        content=(
            f"【演示态】已生成点位导出任务（{city} · {point_type}，格式：Excel）。"
            f"演示环境下返回样例数据清单，真实导出将推送完整资源包。导出任务编号：{eid}。"
        ),
        data={"demo": True, "action": "point_export", "export_id": eid, "point_type": point_type, "city": city},
    )
