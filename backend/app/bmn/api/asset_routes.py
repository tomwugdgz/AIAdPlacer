"""
BMN L2 资产金库 API
GET    /api/v2/bmn/assets             列表（分页）
GET    /api/v2/bmn/assets/{id}        详情
POST   /api/v2/bmn/assets             新增
DELETE /api/v2/bmn/assets/{id}        删除
POST   /api/v2/bmn/assets/search      语义检索
POST   /api/v2/bmn/assets/batch      批量新增（内部用）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from app.bmn.asset_vault import asset_vault

router = APIRouter()


class AssetCreate(BaseModel):
    asset_type: str   # brand_appeal / product_selling / ...
    title: str
    content: str
    tags: Optional[List[str]] = []
    source: Optional[str] = None


class AssetSearchReq(BaseModel):
    query: str
    asset_type: Optional[str] = None
    top_k: int = 5


@router.get("/api/v2/bmn/assets")
async def list_assets(
    asset_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    result = asset_vault.list_assets(asset_type, keyword, page, page_size)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/api/v2/bmn/assets/{asset_id}")
async def get_asset(asset_id: str):
    result = asset_vault.get_asset(asset_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/api/v2/bmn/assets")
async def add_asset(data: AssetCreate):
    result = asset_vault.add_asset(
        asset_type=data.asset_type,
        title=data.title,
        content=data.content,
        tags=data.tags,
        source=data.source,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {"ok": True, "data": result}


@router.delete("/api/v2/bmn/assets/{asset_id}")
async def delete_asset(asset_id: str):
    result = asset_vault.delete_asset(asset_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"ok": True}


@router.post("/api/v2/bmn/assets/search")
async def search_assets(req: AssetSearchReq):
    """
    语义检索资产金库
    返回按相关度排序的资产列表
    """
    result = asset_vault.search(
        query=req.query,
        asset_type=req.asset_type,
        top_k=req.top_k,
    )
    return result
