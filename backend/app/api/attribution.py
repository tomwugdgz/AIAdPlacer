from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.models import get_db
from app.services.attribution_engine import attribution_engine

router = APIRouter()


@router.get("/attribution/geo")
async def geo_attribution(
    campaign_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """地域归因分析"""
    results = attribution_engine.geo_attribution(db, str(campaign_id) if campaign_id else None)
    return {
        "geo_data": results,
        "total_locations": len(results),
    }


@router.get("/attribution/multi-touch")
async def multi_touch_attribution(
    campaign_id: Optional[UUID] = Query(None),
    model: str = Query("linear", regex="^(first|last|linear|time_decay)$"),
    db: Session = Depends(get_db)
):
    """多触点归因分析"""
    results = attribution_engine.multi_touch_attribution(
        db, 
        str(campaign_id) if campaign_id else None,
        model
    )
    return results


@router.get("/attribution/spatio-temporal")
async def spatio_temporal_attribution(
    campaign_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """时空归因分析"""
    results = attribution_engine.spatio_temporal_attribution(
        db,
        str(campaign_id) if campaign_id else None
    )
    return results


@router.get("/attribution/funnel")
async def conversion_funnel(
    campaign_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """转化漏斗分析"""
    results = attribution_engine.conversion_funnel(
        db,
        str(campaign_id) if campaign_id else None
    )
    return results
