"""青柠智能助手 — 报备 / 锁点 / 导点工作流。

- 锁点（lock_point）/ 导点（export_point）：**真实事务**，调用 ``booking_service`` 占用
  PostgreSQL ``media_resources`` 档期并返回真实 ``booking_no``，``demo:False``。
- 报备（submit_report）：**保留演示态**（P0 不接 CRM），``demo:True``，仅写审计 + 占位。

注意：RBAC 已由上层拦截，本模块只在「已授权」的前提下被调用。锁点/导点一旦成功即
落地真实资源变更；失败回滚并保留审计（``demo`` 置 ``False``）。
"""

from __future__ import annotations

import json
import os
import threading
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from app.config import settings
from app.common import setup_logging
from app.core.async_db import AsyncSessionLocal
from app.core.exceptions import QinglinError
from app.qinglin_assistant.tools.base import ToolResult
from app.services.booking_service import find_media_resource

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
    return f"DEMO-{prefix}-{__import__('uuid').uuid4().hex[:8].upper()}"


# point_type（自然语言/前端） → media_type_code（ETL 归一化后的媒体类型编码）
POINT_TYPE_TO_MEDIA_TYPE: Dict[str, str] = {
    "门禁": "door_access",
    "door": "door_access",
    "door_access": "door_access",
    "梯影": "smart_screen_l9",
    "smart": "smart_screen_l9",
    "smart_screen": "smart_screen_l9",
    "单元门": "unit_door",
    "unit": "unit_door",
    "unit_door": "unit_door",
    "商场led": "mall_led",
    "mall_led": "mall_led",
    "led": "mall_led",
    "道闸": "boom_gate",
    "boom": "boom_gate",
    "boom_gate": "boom_gate",
}


def _map_media_type(point_type: Optional[str]) -> Optional[str]:
    if not point_type:
        return None
    key = point_type.strip().lower()
    if key in POINT_TYPE_TO_MEDIA_TYPE:
        return POINT_TYPE_TO_MEDIA_TYPE[key]
    # 子串匹配，兜底
    for k, v in POINT_TYPE_TO_MEDIA_TYPE.items():
        if k in key:
            return v
    return None


def _parse_date(value: Any, default: date) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        value = value.strip()
        if value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                pass
    return default


async def resolve_media_resource_id(params: Dict[str, Any]) -> Optional[str]:
    """由 ``params``（point_type / city / project / 或直接 media_resource_id）解析唯一 ``media_resource_id``。

    接入说明（设计 §9 待明确#A）：对话态下用户通常说「朝阳区XX楼盘门禁点位」，这里先按
    ``media_type_code × city × project`` 在 ``media_resources`` 中查询首个候选；若 ``params``
    已显式带 ``media_resource_id`` 则直接采用。返回 UUID 字符串或 ``None``。
    """
    explicit = params.get("media_resource_id")
    if explicit:
        return str(explicit)

    media_type_code = _map_media_type(params.get("point_type") or params.get("media_type_code"))
    city = params.get("city")
    project = params.get("project")
    if not media_type_code and not city and not project:
        return None

    async with AsyncSessionLocal() as db:
        rows = await find_media_resource(
            db, media_type_code=media_type_code, city=city, project=project, limit=1
        )
    if not rows:
        return None
    return str(rows[0].id)


async def submit_report(role: str, session_id: str, params: Dict[str, Any]) -> ToolResult:
    """报备（演示态，P0 不接 CRM）。"""
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
    """锁点（真实事务）：解析 ``media_resource_id`` → 调 ``booking_service.create_booking``。

    成功返回真实 ``booking_no``，``demo:False``；解析失败或冲突返回明确错误（仍 ``demo:False``）。
    """
    media_resource_id = params.get("media_resource_id") or await resolve_media_resource_id(params)
    if not media_resource_id:
        msg = (
            "未能解析到目标点位：请提供明确的 media_resource_id，或 point_type/city/project "
            "组合（如 point_type=门禁, city=北京）。"
        )
        write_audit({
            "role": role, "session_id": session_id, "action": "point_lock",
            "demo": False, "ok": False, "reason": "unresolved_media_resource",
        })
        return ToolResult(
            tool_name="sale_media_lock",
            success=False,
            demo=False,
            content=f"【真实锁点失败】{msg}",
            data={"demo": False, "action": "point_lock", "ok": False, "reason": "unresolved_media_resource"},
        )

    lock_start = _parse_date(params.get("lock_start"), date.today())
    lock_end = _parse_date(params.get("lock_end"), lock_start + timedelta(days=7))
    if lock_end < lock_start:
        return ToolResult(
            tool_name="sale_media_lock",
            success=False,
            demo=False,
            content="【真实锁点失败】档期结束日期不能早于开始日期。",
            data={"demo": False, "action": "point_lock", "ok": False, "reason": "invalid_date"},
        )

    try:
        async with AsyncSessionLocal() as db:
            booking = await booking_service_create(
                db,
                media_resource_id=media_resource_id,
                lock_start=lock_start,
                lock_end=lock_end,
                created_by=role,
                customer_id=params.get("customer_id"),
                campaign_id=params.get("campaign_id"),
                idempotency_key=params.get("idempotency_key"),
            )
        write_audit({
            "role": role, "session_id": session_id, "action": "point_lock",
            "demo": False, "ok": True, "booking_no": booking.booking_no,
            "media_resource_id": str(media_resource_id),
        })
        return ToolResult(
            tool_name="sale_media_lock",
            success=True,
            demo=False,
            content=(
                f"【真实锁点成功】点位已锁定，档期 {lock_start} ~ {lock_end}（{booking.lock_tier} 档）。"
                f"锁位单号：{booking.booking_no}，到期时间：{booking.expire_at}。"
            ),
            data={
                "demo": False,
                "action": "point_lock",
                "ok": True,
                "booking_no": booking.booking_no,
                "status": booking.status,
                "lock_tier": booking.lock_tier,
                "media_resource_id": str(media_resource_id),
                "lock_start": str(lock_start),
                "lock_end": str(lock_end),
                "expire_at": str(booking.expire_at),
            },
        )
    except QinglinError as e:
        write_audit({
            "role": role, "session_id": session_id, "action": "point_lock",
            "demo": False, "ok": False, "error_code": e.error_code,
            "reason": e.message,
        })
        return ToolResult(
            tool_name="sale_media_lock",
            success=False,
            demo=False,
            content=f"【真实锁点失败】{e.message}（错误码：{e.error_code}）",
            data={"demo": False, "action": "point_lock", "ok": False, "error_code": e.error_code, "message": e.message},
        )


async def export_point(role: str, session_id: str, params: Dict[str, Any]) -> ToolResult:
    """导点（真实导出）：拉取该客户/会话已锁清单（真实 booking_no / 档期），``demo:False``。"""
    customer_id = params.get("customer_id")
    try:
        async with AsyncSessionLocal() as db:
            locked = await booking_service_list(db, status="LOCKED")
            published = await booking_service_list(db, status="PUBLISHED")
        items = list(locked) + list(published)
        if customer_id:
            items = [b for b in items if (b.customer_id or "") == customer_id]
        records = [
            {
                "booking_no": b.booking_no,
                "status": b.status,
                "media_resource_id": str(b.media_resource_id),
                "lock_tier": b.lock_tier,
                "lock_start": str(b.lock_start),
                "lock_end": str(b.lock_end),
                "expire_at": str(b.expire_at),
            }
            for b in items
        ]
        write_audit({
            "role": role, "session_id": session_id, "action": "point_export",
            "demo": False, "ok": True, "count": len(records), "customer_id": customer_id,
        })
        return ToolResult(
            tool_name="sale_media_export",
            success=True,
            demo=False,
            content=(
                f"【真实导出】当前已锁定点位清单共 {len(records)} 条"
                + (f"（客户：{customer_id}）" if customer_id else "")
                + "，详见 data 字段（含真实 booking_no / 档期 / 到期时间）。"
            ),
            data={"demo": False, "action": "point_export", "ok": True, "count": len(records), "items": records},
        )
    except QinglinError as e:
        return ToolResult(
            tool_name="sale_media_export",
            success=False,
            demo=False,
            content=f"【真实导出失败】{e.message}（错误码：{e.error_code}）",
            data={"demo": False, "action": "point_export", "ok": False, "error_code": e.error_code, "message": e.message},
        )


# 延迟绑定 booking_service 函数，避免循环导入风险（booking_service 不反向依赖本模块）
from app.services import booking_service as _svc  # noqa: E402

booking_service_create = _svc.create_booking
booking_service_list = _svc.list_bookings
