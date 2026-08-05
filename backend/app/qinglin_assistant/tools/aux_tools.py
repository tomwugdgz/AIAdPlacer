"""青柠智能助手 — 地图辅助工具。

复用既有 ``app.services.tencent_map.TencentMapService``（地理编码 / POI 检索）。
这些是真实链路调用（腾讯地图 API），返回坐标与周边 POI。调用结果不属于 PII，
通常不做脱敏；失败时返回明确错误信息，绝不伪造坐标。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.tencent_map import tencent_map_service
from app.qinglin_assistant.tools.base import Tool, ToolContext, ToolResult


async def map_geocode(address: str, city: str = "") -> Dict[str, Any]:
    """地址转坐标（地理编码）。"""
    if not address:
        return {"success": False, "error": "缺少地址参数"}
    result = await tencent_map_service.geocode(address, city=city)
    if not result:
        return {"success": False, "error": "地理编码失败（请检查地址或腾讯地图 Key）"}
    return {"success": True, **result}


async def map_search_poi(
    keyword: str,
    location: str = "",
    radius: int = 5000,
    page_size: int = 10,
) -> Dict[str, Any]:
    """周边 POI 搜索。"""
    if not keyword:
        return {"success": False, "error": "缺少关键词参数"}
    pois = await tencent_map_service.search_poi(
        keyword=keyword, location=location, radius=radius, page_size=page_size
    )
    return {"success": True, "count": len(pois), "pois": pois}


class MapGeocodeTool(Tool):
    """地理编码工具。"""

    name = "map_geocode"
    description = "将地址转换为经纬度坐标"

    async def run(self, ctx: ToolContext) -> ToolResult:
        params = ctx.params or {}
        result = await map_geocode(params.get("address", ""), params.get("city", ""))
        return ToolResult(
            tool_name=self.name,
            success=result.get("success", False),
            content=(
                f"「{params.get('address')}」坐标：纬度 {result.get('lat')}，经度 {result.get('lng')}"
                if result.get("success") else f"地理编码失败：{result.get('error')}"
            ),
            data=result,
            demo=False,
        )


class MapPoiTool(Tool):
    """POI 搜索工具。"""

    name = "map_search_poi"
    description = "搜索指定位置周边的兴趣点（POI）"

    async def run(self, ctx: ToolContext) -> ToolResult:
        params = ctx.params or {}
        result = await map_search_poi(
            keyword=params.get("keyword", ""),
            location=params.get("location", ""),
            radius=int(params.get("radius", 5000)),
        )
        return ToolResult(
            tool_name=self.name,
            success=result.get("success", False),
            content=(
                f"「{params.get('keyword')}」周边找到 {result.get('count', 0)} 个 POI"
                if result.get("success") else f"POI 搜索失败：{result.get('error')}"
            ),
            data=result,
            demo=False,
        )
