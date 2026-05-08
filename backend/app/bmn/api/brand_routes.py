"""
BMN L1 品牌配置 API
GET  /api/v2/bmn/brand/config?brand_name=亲邻传媒
PUT  /api/v2/bmn/brand/config
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.bmn.brand_engine import brand_engine

router = APIRouter()


@router.get("/api/v2/bmn/health")
async def health_check():
 return {"status": "ok", "service": "BMN", "version": "1.0.0"}


class BrandConfigUpdate(BaseModel):
    brand_name: str
    identity: Optional[str] = None
    value_proposition: Optional[str] = None
    trust_proof: Optional[list] = None
    differentiation: Optional[str] = None


@router.get("/api/v2/bmn/brand/config")
async def get_brand_config(brand_name: str = "亲邻传媒"):
    result = brand_engine.get_brand_config(brand_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.put("/api/v2/bmn/brand/config")
async def upsert_brand_config(data: BrandConfigUpdate):
    result = brand_engine.upsert_brand_config(data.dict(exclude_none=True))
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/api/v2/bmn/brand/master_prompt")
async def get_master_prompt(brand_name: str = "亲邻传媒"):
    """直接获取母指令文本，供其他服务注入 LLM"""
    prompt = brand_engine.get_master_prompt(brand_name)
    if not prompt:
        raise HTTPException(status_code=404, detail="未找到品牌配置，请先创建")
    return {"master_prompt": prompt}
