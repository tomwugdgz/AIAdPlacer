"""青柠智能助手 — 点位查询编排 + 文档生成编排（真实链路）。

- ``query_points_orchestration``：编排知识库真实查询（真实 DB）。
- ``generate_document_orchestration``：先真实查询，再落地为 .docx / .xlsx 文件
  （真实链路，**非**演示态）。文档内容来自真实数据，并按角色脱敏后写入。
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.qinglin_assistant.rbac.policy import Role, mask_records
from app.qinglin_assistant.skills.registry import skill_registry
from app.qinglin_assistant.tools.base import ToolContext, ToolResult
from app.qinglin_assistant.tools.kb_tools import KnowledgeBaseTool


async def query_points_orchestration(
    role: str, session_id: str, params: Dict[str, Any]
) -> ToolResult:
    """编排知识库真实查询。"""
    ctx = ToolContext(role=str(role), session_id=session_id, params=params, action="point_query")
    return await KnowledgeBaseTool().run(ctx)


def _collect_records(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从 KB 结果中汇总可落文档的记录行。"""
    records: List[Dict[str, Any]] = []
    for key in ("points", "clients", "led_points"):
        block = raw.get(key)
        if isinstance(block, dict) and block.get("records"):
            records.extend(block["records"])
    return records


async def generate_document_orchestration(
    role: str, session_id: str, params: Dict[str, Any]
) -> ToolResult:
    """先真实查询，再生成文档（真实链路）。"""
    # 1) 真实查询
    kb = await KnowledgeBaseTool().run(
        ToolContext(role=str(role), session_id=session_id, params=params, action="point_query")
    )
    raw = kb.data or {}
    records = _collect_records(raw)

    # 2) 按角色脱敏
    masked, _ = mask_records(role, records)
    if not masked:
        masked = [{"说明": "未查询到可落文档的数据"}]

    headers: List[str] = list(masked[0].keys())
    rows: List[List[Any]] = [list(r.values()) for r in masked[:50]]

    doc_type = (params.get("doc_type") or "docx").lower()
    point_type = params.get("point_type") or "点位"
    city = params.get("city") or ""
    title = params.get("title") or f"青柠{point_type}{('·' + city) if city else ''}资源清单"

    if doc_type == "xlsx":
        result = skill_registry.run(
            "xlsx",
            {"title": title, "sheet_name": "数据", "headers": headers, "rows": rows},
        )
    else:
        result = skill_registry.run(
            "docx",
            {
                "title": title,
                "sections": [{"heading": "概览", "body": kb.content}],
                "table": {"headers": headers, "rows": rows},
            },
        )

    if not result.get("success"):
        return ToolResult(
            tool_name="doc_generate",
            success=False,
            demo=False,
            content=f"文档生成失败：{result.get('error', '未知错误')}",
            data=result,
        )

    return ToolResult(
        tool_name="doc_generate",
        success=True,
        demo=False,
        content=f"已基于青柠真实数据库生成文档：{result.get('file_name')}（共 {len(rows)} 条记录）。",
        data={**result, "demo": False, "record_count": len(rows)},
    )
