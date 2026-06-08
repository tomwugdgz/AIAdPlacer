"""
知识库 + 调用日志 REST API 路由

提供：
1. 知识库检索、浏览、统计
2. MCP 调用日志记录、查询、详情查看
"""

from fastapi import APIRouter, Query, Request
from typing import Optional

from app.services.knowledge_base import kb

router = APIRouter(tags=["知识库管理"])


# ═══════════════════════════════════════════════════════
# 知识库接口
# ═══════════════════════════════════════════════════════

@router.get("/knowledge/search")
def search_knowledge(
    tool_name: Optional[str] = Query(None, description="按工具名筛选"),
    date_from: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    city: Optional[str] = Query(None, description="按城市筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    limit: int = Query(50, ge=1, le=200, description="返回数量上限"),
):
    """检索知识库（按工具/日期/城市/关键词）"""
    results = kb.search(
        tool_name=tool_name, date_from=date_from, date_to=date_to,
        city=city, keyword=keyword, limit=limit,
    )
    return {"total": len(results), "records": results}


@router.get("/knowledge/record/{record_id}")
def get_record(record_id: str):
    """根据 ID 获取完整知识库记录"""
    record = kb.get_record(record_id)
    if not record:
        return {"error": "记录不存在", "record_id": record_id}
    return record


@router.get("/knowledge/dates")
def list_dates():
    """列出所有有数据的日期"""
    return {"dates": kb.list_dates()}


@router.get("/knowledge/tools")
def list_tools():
    """列出所有已使用过的工具"""
    return {"tools": kb.list_tools()}


@router.get("/knowledge/date/{date_str}")
def list_by_date(date_str: str, limit: int = Query(100, ge=1, le=500)):
    """按日期列出所有知识库记录"""
    records = kb.list_by_date(date_str)[:limit]
    return {"date": date_str, "total": len(records), "records": records}


@router.get("/knowledge/tool/{tool_name}")
def list_by_tool(tool_name: str, limit: int = Query(100, ge=1, le=500)):
    """按工具名列出所有知识库记录"""
    records = kb.list_by_tool(tool_name, limit)
    return {"tool": tool_name, "total": len(records), "records": records}


@router.get("/knowledge/stats")
def get_stats():
    """获取知识库统计信息"""
    return kb.get_stats()


# ═══════════════════════════════════════════════════════
# MCP 调用日志接口
# ═══════════════════════════════════════════════════════

@router.get("/logs")
def get_call_logs(
    tool_name: Optional[str] = Query(None, description="按工具名筛选"),
    date_from: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """
    MCP 调用日志列表

    展示每次外部 MCP 调用的：工具名、参数、结果摘要、时间、来源 IP
    """
    offset = (page - 1) * page_size
    data = kb.get_call_logs(
        tool_name=tool_name, date_from=date_from, date_to=date_to,
        limit=page_size, offset=offset,
    )
    return {
        "total": data["total"],
        "page": page,
        "page_size": page_size,
        "total_pages": (data["total"] + page_size - 1) // page_size,
        "logs": data["logs"],
    }


@router.get("/logs/{log_id}")
def get_log_detail(log_id: str):
    """
    MCP 调用日志详情

    含完整的调用参数 + 完整结果（result 字段）
    """
    detail = kb.get_call_log_detail(log_id)
    if not detail:
        return {"error": "日志不存在", "log_id": log_id}
    return detail


@router.get("/logs/stats")
def get_log_stats():
    """
    MCP 调用日志统计

    展示：总调用次数、按工具分布、按日期分布
    """
    return kb.get_stats()
