"""
智能屏资源子系统（Smart Screen L9）— FastAPI 路由。

统一前缀 /api/v2/smart-screen，端点：
- GET /tables                  表清单 + 行数
- GET /communities             小区级宽表（可按 省/市/区 筛选）
- GET /indicators/{community_id}  某小区 39 指标
- GET /media                   媒体列表（筛选 + 分页）
- GET /stats                   子系统整体统计
- GET /algorithms              19 算法注册表

响应体统一 {success, data/error, code, total?}（与 db_api 风格一致）。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.common import setup_logging, format_error_response
from app.smart_screen import ss_dao

logger = setup_logging(__name__)

# 子系统路由（前缀 /api/v2/smart-screen，tag 中文）
ss_api_router = APIRouter(
    prefix="/api/v2/smart-screen",
    tags=["智能屏资源"],
)


# ── 1. 表清单 ──────────────────────────────────────────────────────────────────

@ss_api_router.get("/tables")
async def get_tables():
    """
    获取子系统所有表名与行数。

    Returns:
        {success, data:[{name,count,columns}], total, code}
    """
    try:
        tables = ss_dao.list_tables()
        return JSONResponse(
            content={
                "success": True,
                "data": tables,
                "total": len(tables),
                "code": "OK",
            },
            status_code=200,
        )
    except FileNotFoundError as e:
        return JSONResponse(
            content={"success": False, "error": str(e), "code": "DATABASE_NOT_FOUND"},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"获取表清单失败: {e}", exc_info=True)
        return JSONResponse(
            content=format_error_response(e, request_id=None),
            status_code=500,
        )


# ── 2. 小区级宽表 ──────────────────────────────────────────────────────────────

@ss_api_router.get("/communities")
async def get_communities(
    province: Optional[str] = Query(None, description="省份筛选"),
    city: Optional[str] = Query(None, description="城市筛选"),
    district: Optional[str] = Query(None, description="区/县筛选"),
    limit: int = Query(100, description="返回上限", ge=1, le=1000),
):
    """
    查询小区级宽表（关联层），支持省/市/区筛选。

    Returns:
        {success, data:[...], total, code}
    """
    try:
        filters = {}
        if province:
            filters["province"] = province
        if city:
            filters["city"] = city
        if district:
            filters["district"] = district
        rows = ss_dao.get_community_wide(filters=filters, limit=limit)
        return JSONResponse(
            content={
                "success": True,
                "data": rows,
                "total": len(rows),
                "code": "OK",
            },
            status_code=200,
        )
    except FileNotFoundError as e:
        return JSONResponse(
            content={"success": False, "error": str(e), "code": "DATABASE_NOT_FOUND"},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"查询小区宽表失败: {e}", exc_info=True)
        return JSONResponse(
            content=format_error_response(e, request_id=None),
            status_code=500,
        )


# ── 3. 指标查询 ────────────────────────────────────────────────────────────────

@ss_api_router.get("/indicators/{community_id}")
async def get_indicators(community_id: str):
    """
    获取某小区的 39 指标（小区级）。

    Returns:
        {success, data:{community_id, indicators:{...}}, code}
    """
    try:
        ind = ss_dao.get_indicators(community_id)
        if ind is None:
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"未找到小区指标: {community_id}",
                    "code": "NOT_FOUND",
                },
                status_code=404,
            )
        # 拆分元信息与 39 指标
        indicators = {k: ind[k] for k in ind.keys() if k not in ("id", "community_id", "point_id", "computed_at")}
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "community_id": ind["community_id"],
                    "point_id": ind.get("point_id"),
                    "computed_at": ind.get("computed_at"),
                    "indicators": indicators,
                },
                "code": "OK",
            },
            status_code=200,
        )
    except FileNotFoundError as e:
        return JSONResponse(
            content={"success": False, "error": str(e), "code": "DATABASE_NOT_FOUND"},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"查询指标失败: {e}", exc_info=True)
        return JSONResponse(
            content=format_error_response(e, request_id=None),
            status_code=500,
        )


# ── 4. 媒体列表 ────────────────────────────────────────────────────────────────

@ss_api_router.get("/media")
async def get_media(
    province: Optional[str] = Query(None, description="省份筛选"),
    city: Optional[str] = Query(None, description="城市筛选"),
    district: Optional[str] = Query(None, description="区/县筛选"),
    community_id: Optional[str] = Query(None, description="小区ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词（网点/点位/MAC）"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页数量", ge=1, le=1000),
):
    """
    查询媒体列表（输入层），支持筛选与分页。

    Returns:
        {success, data:[...], total, page, page_size, total_pages, code}
    """
    try:
        filters = {}
        if province:
            filters["province"] = province
        if city:
            filters["city"] = city
        if district:
            filters["district"] = district
        if community_id:
            filters["community_id"] = community_id
        if keyword:
            filters["keyword"] = keyword
        result = ss_dao.query_media(filters=filters, page=page, page_size=page_size)
        return JSONResponse(
            content={
                "success": True,
                **result,
                "code": "OK",
            },
            status_code=200,
        )
    except ValueError as e:
        return JSONResponse(
            content={"success": False, "error": str(e), "code": "VALIDATION_ERROR"},
            status_code=400,
        )
    except FileNotFoundError as e:
        return JSONResponse(
            content={"success": False, "error": str(e), "code": "DATABASE_NOT_FOUND"},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"查询媒体失败: {e}", exc_info=True)
        return JSONResponse(
            content=format_error_response(e, request_id=None),
            status_code=500,
        )


# ── 5. 统计信息 ────────────────────────────────────────────────────────────────

@ss_api_router.get("/stats")
async def get_stats():
    """
    子系统整体统计（媒体/小区/设备/指标/算法 总量 + 城市/省份分布）。

    Returns:
        {success, data:{...}, code}
    """
    try:
        stats = ss_dao.get_stats()
        return JSONResponse(
            content={"success": True, "data": stats, "code": "OK"},
            status_code=200,
        )
    except FileNotFoundError as e:
        return JSONResponse(
            content={"success": False, "error": str(e), "code": "DATABASE_NOT_FOUND"},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"查询统计失败: {e}", exc_info=True)
        return JSONResponse(
            content=format_error_response(e, request_id=None),
            status_code=500,
        )


# ── 6. 算法注册表 ──────────────────────────────────────────────────────────────

@ss_api_router.get("/algorithms")
async def get_algorithms():
    """
    获取 19 个算法注册信息。

    Returns:
        {success, data:[...], total, code}
    """
    try:
        algs = ss_dao.get_algorithms()
        return JSONResponse(
            content={
                "success": True,
                "data": algs,
                "total": len(algs),
                "code": "OK",
            },
            status_code=200,
        )
    except FileNotFoundError as e:
        return JSONResponse(
            content={"success": False, "error": str(e), "code": "DATABASE_NOT_FOUND"},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"查询算法失败: {e}", exc_info=True)
        return JSONResponse(
            content=format_error_response(e, request_id=None),
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    _app = FastAPI(title="智能屏资源子系统 API 测试")
    _app.include_router(ss_api_router)
    print("测试服务: http://127.0.0.1:9100/docs")
    uvicorn.run(_app, host="127.0.0.1", port=9100)
