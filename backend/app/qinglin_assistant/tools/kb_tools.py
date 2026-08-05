"""青柠智能助手 — 知识库真实查询工具。

本模块是「真实链路」的核心：所有查询都直接打到既有 ``app.db_dao``（底层为
``qinlin_local.db`` 真实库），**绝不**编造数据。

对外提供四角色入口（与 brief 命名一致）：
- ``call_api_sale``：销售视角查询（门禁点位 / 客户线索）
- ``call_api_media``：媒介视角查询（各类点位明细）
- ``call_api_engineer``：工程视角查询（智能屏 / 道闸等设备的技术点位）
- ``call_api_developer``：商业开发视角查询（客户通讯录 / 商场 LED 等）

并以 ``KnowledgeBaseTool`` 统一封装，供编排层按角色 / 动作调度。

所有返回均标注 ``demo: False``（真实数据），并按调用角色做字段脱敏。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.db_dao import (
    get_all_tables,
    get_points_by_type,
    get_table_stats,
    query_table,
    search_clients,
)
from app.qinglin_assistant.rbac.policy import Role, mask_records
from app.qinglin_assistant.tools.base import Tool, ToolContext, ToolResult

# 点位类型 -> 中文表名（与 db_dao.type_to_table 的 value 对齐）
POINT_TYPE_TO_TABLE: Dict[str, str] = {
    "门禁点位": "门禁点位",
    "单元门点位": "单元门点位",
    "道闸点位": "道闸点位",
    "商场LED点位": "商场LED点位",
    "智能屏L9": "智能屏L9",
    "智能屏202507": "智能屏202507",
}


def _detect_city_in_stats(city_stats: Dict[str, int], text: str) -> Optional[str]:
    """在表统计的城市分布中，找出与 ``text`` 对应的城市名（取最长匹配）。

    同时支持双向子串匹配：既允许 ``city in text``（如 "广州市" 命中 "广州"），
    也允许 ``text in city``，以兼容「广州市 / 广州」这类省市级表述差异。
    """
    best: Optional[str] = None
    for city in city_stats:
        if not city:
            continue
        if city == text or city in text or text in city:
            if best is None or len(city) > len(best):
                best = city
    return best


def _point_count(point_type: str, city: Optional[str] = None) -> Dict[str, Any]:
    """统计某类型点位数量；若给出城市则在城市维度下钻。"""
    table = POINT_TYPE_TO_TABLE.get(point_type, point_type)
    stats = get_table_stats(table)
    total = stats.get("total_count", 0)
    result: Dict[str, Any] = {"point_type": point_type, "total": total, "scoped": False}
    if city:
        matched = _detect_city_in_stats(stats.get("city_stats", {}), city)
        if matched:
            result.update({"city": matched, "count": stats["city_stats"][matched], "scoped": True})
            return result
        # 城市未命中该表，回退到总量并提示
        result.update({"city": city, "count": total, "city_matched": False})
    else:
        result["count"] = total
    return result


def _list_points(point_type: str, city: Optional[str], limit: int) -> Dict[str, Any]:
    table = POINT_TYPE_TO_TABLE.get(point_type, point_type)
    filters: Dict[str, Any] = {}
    if city:
        filters["city"] = city
    page = query_table(table, filters=filters or None, page=1, page_size=limit)
    return {
        "point_type": point_type,
        "total": page.get("total", 0),
        "records": page.get("data", []),
    }


def _query_clients(keyword: Optional[str], city: Optional[str], limit: int) -> Dict[str, Any]:
    rows = search_clients(keyword=keyword, city=city, limit=limit)
    return {"keyword": keyword, "city": city, "total": len(rows), "records": rows}


# ─────────────────────────────────────────────────────────────
# 四角色入口（与 brief 命名一致，均为真实查询）
# ─────────────────────────────────────────────────────────────

async def call_api_sale(params: Dict[str, Any]) -> Dict[str, Any]:
    """销售视角：门禁点位计数 + 客户线索检索。"""
    point_type = params.get("point_type") or "门禁点位"
    city = params.get("city")
    clients = _query_clients(params.get("keyword"), city, int(params.get("limit", 10)))
    count = _point_count(point_type, city)
    return {
        "role": "sale",
        "demo": False,
        "point_count": count,
        "clients": clients,
    }


async def call_api_media(params: Dict[str, Any]) -> Dict[str, Any]:
    """媒介视角：点位明细列表。"""
    point_type = params.get("point_type") or "门禁点位"
    city = params.get("city")
    points = _list_points(point_type, city, int(params.get("limit", 10)))
    return {"role": "media", "demo": False, "points": points}


async def call_api_engineer(params: Dict[str, Any]) -> Dict[str, Any]:
    """工程视角：智能屏 / 道闸等设备的技术点位查询。"""
    point_type = params.get("point_type") or "智能屏L9"
    city = params.get("city")
    points = _list_points(point_type, city, int(params.get("limit", 10)))
    count = _point_count(point_type, city)
    return {"role": "engineer", "demo": False, "points": points, "point_count": count}


async def call_api_developer(params: Dict[str, Any]) -> Dict[str, Any]:
    """商业开发视角：客户通讯录 + 商场 LED 点位。"""
    clients = _query_clients(params.get("keyword"), params.get("city"), int(params.get("limit", 10)))
    led = _list_points("商场LED点位", params.get("city"), int(params.get("limit", 10)))
    return {"role": "developer", "demo": False, "clients": clients, "led_points": led}


# 角色 -> 查询入口
_ROLE_QUERY_DISPATCH = {
    Role.SALE: call_api_sale,
    Role.MEDIA: call_api_media,
    Role.ENGINEER: call_api_engineer,
    Role.DEVELOPER: call_api_developer,
}


def _format_count_text(count_info: Dict[str, Any]) -> str:
    pt = count_info.get("point_type", "点位")
    if count_info.get("scoped") and count_info.get("city"):
        return f"{count_info['city']}的{pt}共 {count_info['count']:,} 个（{pt}全国总量 {count_info['total']:,} 个）"
    return f"{pt}共 {count_info['count']:,} 个"


def _format_records(records: List[Dict[str, Any]], role: Any, limit: int = 5) -> List[Dict[str, Any]]:
    masked, _ = mask_records(role, records[:limit])
    return masked


class KnowledgeBaseTool(Tool):
    """知识库真实查询工具，按角色自动分派到对应入口。"""

    name = "knowledge_base"
    description = "查询青柠真实点位 / 客户数据库（qinlin_local.db）"

    async def run(self, ctx: ToolContext) -> ToolResult:
        role = Role.from_str(ctx.role) or Role.SALE
        params = ctx.params or {}
        handler = _ROLE_QUERY_DISPATCH.get(role, call_api_sale)
        raw = await handler(params)

        # 脱敏：对返回数据中的记录（points / clients / led_points）按角色脱敏，
        # 保证响应 data 负载里也不泄露 PII（销售 / 媒介等外部角色默认脱敏）。
        for key in ("points", "clients", "led_points"):
            block = raw.get(key)
            if isinstance(block, dict) and block.get("records"):
                masked, _ = mask_records(role, block["records"])
                block["records"] = masked

        # 脱敏：把各结果块里的 records 统一脱敏
        masked_fields: List[str] = []
        parts: List[str] = []

        if "point_count" in raw:
            parts.append(_format_count_text(raw["point_count"]))
        if "points" in raw:
            recs = raw["points"].get("records", [])
            masked, f1 = mask_records(role, recs[:5])
            masked_fields.extend(f1)
            parts.append(
                f"「{raw['points'].get('point_type')}」命中 {raw['points'].get('total'):,} 条，"
                f"示例：{masked[0] if masked else '（无示例数据）'}"
            )
        if "clients" in raw:
            recs = raw["clients"].get("records", [])
            masked, f2 = mask_records(role, recs[:5])
            masked_fields.extend(f2)
            parts.append(
                f"客户通讯录命中 {raw['clients'].get('total'):,} 条，"
                f"示例：{masked[0] if masked else '（无示例数据）'}"
            )
        if "led_points" in raw:
            recs = raw["led_points"].get("records", [])
            masked, f3 = mask_records(role, recs[:5])
            masked_fields.extend(f3)
            parts.append(
                f"商场 LED 点位命中 {raw['led_points'].get('total'):,} 条，"
                f"示例：{masked[0] if masked else '（无示例数据）'}"
            )

        content = "；".join(parts) if parts else "未查询到相关数据。"
        return ToolResult(
            tool_name=self.name,
            success=True,
            content=content,
            data=raw,
            demo=False,
        )
