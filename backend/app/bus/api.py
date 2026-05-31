"""
bus-pDOOH 子系统 — REST API 路由

前缀: /api/v2/bus/
覆盖: 线路管理 / Excel导入 / 竞价计算 / 方案管理 / AI审核 / 效果归因 / 智能推荐
"""
import uuid
import math
from typing import Optional, List
from datetime import datetime, date as date_type
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from decimal import Decimal
import pandas as pd

from app.models import get_db
from app.bus.models import (
    BusRoute, BusCampaign, BusCampaignRoute,
    BusHeatTask, BusAttribution,
    RouteLevel, RouteStatus, CampaignStatus, AiReviewStatus,
)
from app.bus.schemas import (
    BusRouteCreate, BusRouteUpdate, BusRouteOut, BusRouteListOut,
    BusRouteStatusUpdate, ExcelImportResult,
    BiddingCalculateRequest, MultiBiddingRequest,
    CampaignCreate, CampaignRouteItem, CampaignOut, CampaignListOut,
    HeatTaskOut, AttributionOut, AiReviewResult,
    RecommendRequest, RecommendOut,
)
from app.bus.services.bidding_engine import calculate_bidding, calculate_multi_bidding
from app.bus.services.heat_scoring import HeatScoringService
from app.bus.services.ai_review import AiReviewService
from app.bus.services.attribution import AttributionService
from app.services.tencent_map import TencentMapService

router = APIRouter(prefix="/api/v2/bus")

# ── 工具函数 ────────────────────────────────────────────────

def route_to_dict(route: BusRoute) -> dict:
    """ORM 对象 → 字典"""
    return {
        "id": str(route.id),
        "city": route.city,
        "route_name": route.route_name,
        "route_code": route.route_code,
        "level": route.level.value if route.level else "A",
        "vehicle_count": route.vehicle_count,
        "monthly_price": float(route.monthly_price),
        "heat_score": route.heat_score or 0.0,
        "daily_traffic": route.daily_traffic,
        "hotspot_traffic": route.hotspot_traffic,
        "display_formula": route.display_formula,
        "pois": route.pois or [],
        "status": route.status.value if route.status else "available",
        "created_at": route.created_at.isoformat() if route.created_at else None,
        "updated_at": route.updated_at.isoformat() if route.updated_at else None,
    }


def campaign_to_dict(campaign: BusCampaign) -> dict:
    """投放方案 ORM → 字典"""
    routes_data = []
    for cr in campaign.campaign_routes:
        route_dict = route_to_dict(cr.route) if cr.route else {}
        routes_data.append({
            "id": str(cr.id),
            "route_id": str(cr.route_id),
            "vehicle_count": cr.vehicle_count,
            "route_budget": float(cr.route_budget),
            "actual_days": cr.actual_days,
            "estimated_impressions": cr.estimated_impressions,
            "route_info": route_dict,
        })
    return {
        "id": str(campaign.id),
        "advertiser_id": campaign.advertiser_id,
        "campaign_name": campaign.campaign_name,
        "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
        "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
        "total_budget": float(campaign.total_budget),
        "ai_review_status": campaign.ai_review_status.value if campaign.ai_review_status else "pending",
        "ai_review_comment": campaign.ai_review_comment,
        "attribution_report": campaign.attribution_report,
        "status": campaign.status.value if campaign.status else "draft",
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
        "routes": routes_data,
    }


def heat_task_to_dict(task: BusHeatTask) -> dict:
    return {
        "id": str(task.id),
        "route_id": str(task.route_id),
        "task_status": task.task_status.value if task.task_status else "pending",
        "heat_score": task.heat_score,
        "poi_data": task.poi_data,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


# ════════════════════════════════════════════════════════════════
# 1. 线路资源管理 API
# ════════════════════════════════════════════════════════════════

@router.post("/routes/import", response_model=ExcelImportResult, summary="Excel批量导入线路")
async def import_routes(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """通过 Excel 批量导入公交线路数据（.xlsx）"""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx / .xls 文件")

    contents = await file.read()
    df = pd.read_excel(pd.io.common.BytesIO(contents))

    success_count = 0
    failed_count = 0
    failed_reasons: List[str] = []

    # 适配常见列名
    col_map = {}
    for col in df.columns:
        col_lower = str(col).strip().lower()
        if any(k in col_lower for k in ["城市", "city"]):
            col_map["city"] = col
        elif any(k in col_lower for k in ["线路", "route"]):
            col_map["route_name"] = col
        elif any(k in col_lower for k in ["编号", "code"]):
            col_map["route_code"] = col
        elif any(k in col_lower for k in ["等级", "level"]):
            col_map["level"] = col
        elif any(k in col_lower for k in ["车辆", "车数", "vehicle"]):
            col_map["vehicle_count"] = col
        elif any(k in col_lower for k in ["单价", "price", "月单"]):
            col_map["monthly_price"] = col
        elif any(k in col_lower for k in ["客流", "traffic"]):
            col_map["daily_traffic"] = col
        elif any(k in col_lower for k in ["热力", "hot"]):
            col_map["heat_score"] = col

    for idx, row in df.iterrows():
        try:
            city = str(row.get(col_map.get("city", "城市"), "")).strip()
            route_name = str(row.get(col_map.get("route_name", "线路名称"), "")).strip()
            route_code = str(row.get(col_map.get("route_code", "线路编号"), "")).strip()

            if not city or not route_code:
                failed_reasons.append(f"行{idx+1}: 缺少城市或线路编号")
                failed_count += 1
                continue

            level_str = str(row.get(col_map.get("level", "等级"), "A")).strip()
            level_map = {"S": RouteLevel.S, "A++": RouteLevel.A_PLUS_PLUS, "A+": RouteLevel.A_PLUS, "A": RouteLevel.A}
            level = level_map.get(level_str, RouteLevel.A)

            # 检查是否重复
            existing = db.query(BusRoute).filter(BusRoute.route_code == route_code).first()
            if existing:
                # 更新已有线路
                existing.city = city
                existing.route_name = route_name
                existing.level = level
                existing.vehicle_count = int(row.get(col_map.get("vehicle_count", "车辆数"), 1) or 1)
                existing.monthly_price = Decimal(str(row.get(col_map.get("monthly_price", "月单价"), 0) or 0))
                existing.daily_traffic = int(row.get(col_map.get("daily_traffic", "日均客流"), 0) or 0)
                if "heat_score" in col_map:
                    existing.heat_score = float(row.get(col_map["heat_score"], 0) or 0)
            else:
                route = BusRoute(
                    city=city,
                    route_name=route_name,
                    route_code=route_code,
                    level=level,
                    vehicle_count=int(row.get(col_map.get("vehicle_count", "车辆数"), 1) or 1),
                    monthly_price=Decimal(str(row.get(col_map.get("monthly_price", "月单价"), 0) or 0)),
                    daily_traffic=int(row.get(col_map.get("daily_traffic", "日均客流"), 0) or 0),
                    heat_score=float(row.get(col_map.get("heat_score", "热力评分"), 0) or 0),
                )
                db.add(route)

            success_count += 1
        except Exception as e:
            failed_reasons.append(f"行{idx+1}: {str(e)}")
            failed_count += 1

    db.commit()
    return ExcelImportResult(
        total_rows=len(df),
        success_count=success_count,
        failed_count=failed_count,
        failed_reasons=failed_reasons[:20],
    )


@router.get("/routes", response_model=BusRouteListOut, summary="线路列表（筛选）")
def list_routes(
    city: Optional[str] = Query(None, description="城市筛选"),
    level: Optional[str] = Query(None, description="等级筛选 S/A++/A+/A"),
    min_price: Optional[float] = Query(None, description="最低月单价"),
    max_price: Optional[float] = Query(None, description="最高月单价"),
    min_heat: Optional[float] = Query(None, description="最低热力评分"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（线路名/编号）"),
    sort_by: str = Query("heat_score", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向 asc/desc"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """支持多条件筛选的线路列表"""
    q = db.query(BusRoute)

    if city:
        q = q.filter(BusRoute.city == city)
    if level:
        level_map = {"S": RouteLevel.S, "A++": RouteLevel.A_PLUS_PLUS, "A+": RouteLevel.A_PLUS, "A": RouteLevel.A}
        if level in level_map:
            q = q.filter(BusRoute.level == level_map[level])
    if min_price is not None:
        q = q.filter(BusRoute.monthly_price >= min_price)
    if max_price is not None:
        q = q.filter(BusRoute.monthly_price <= max_price)
    if min_heat is not None:
        q = q.filter(BusRoute.heat_score >= min_heat)
    if status:
        q = q.filter(BusRoute.status == status)
    if keyword:
        q = q.filter(
            or_(
                BusRoute.route_name.ilike(f"%{keyword}%"),
                BusRoute.route_code.ilike(f"%{keyword}%"),
            )
        )

    # 排序
    sort_col = getattr(BusRoute, sort_by, BusRoute.heat_score)
    if sort_order.lower() == "desc":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())

    total = q.count()
    routes = q.offset(offset).limit(limit).all()

    return BusRouteListOut(
        total=total,
        data=[BusRouteOut(**route_to_dict(r)) for r in routes],
    )


@router.get("/routes/{route_id}", response_model=BusRouteOut, summary="线路详情")
def get_route(route_id: str, db: Session = Depends(get_db)):
    route = db.query(BusRoute).filter(BusRoute.id == uuid.UUID(route_id)).first()
    if not route:
        raise HTTPException(status_code=404, detail="线路不存在")
    return BusRouteOut(**route_to_dict(route))


@router.put("/routes/{route_id}", response_model=BusRouteOut, summary="更新线路")
def update_route(route_id: str, data: BusRouteUpdate, db: Session = Depends(get_db)):
    route = db.query(BusRoute).filter(BusRoute.id == uuid.UUID(route_id)).first()
    if not route:
        raise HTTPException(status_code=404, detail="线路不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(route, key, value)
    db.commit()
    db.refresh(route)
    return BusRouteOut(**route_to_dict(route))


@router.put("/routes/{route_id}/status", response_model=BusRouteOut, summary="变更线路状态")
def update_route_status(route_id: str, data: BusRouteStatusUpdate, db: Session = Depends(get_db)):
    route = db.query(BusRoute).filter(BusRoute.id == uuid.UUID(route_id)).first()
    if not route:
        raise HTTPException(status_code=404, detail="线路不存在")

    status_map = {"available": RouteStatus.AVAILABLE, "booked": RouteStatus.BOOKED, "offline": RouteStatus.OFFLINE}
    if data.status not in status_map:
        raise HTTPException(status_code=400, detail=f"无效的状态值: {data.status}")

    route.status = status_map[data.status]
    db.commit()
    db.refresh(route)
    return BusRouteOut(**route_to_dict(route))


@router.post("/routes/{route_id}/heat-score", response_model=dict, summary="触发热力评分")
async def trigger_heat_score(route_id: str, db: Session = Depends(get_db)):
    """手动触发单条线路热力评分计算"""
    route = db.query(BusRoute).filter(BusRoute.id == uuid.UUID(route_id)).first()
    if not route:
        raise HTTPException(status_code=404, detail="线路不存在")

    # 创建热力任务
    task = BusHeatTask(
        route_id=route.id,
        task_status=HeatTaskStatus.RUNNING,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 同步计算热力评分（V0.1）
    try:
        scorer = HeatScoringService()
        result = await scorer.calculate(route.city, route.route_name)

        route.heat_score = result.get("heat_score", 0.0)
        task.heat_score = result.get("heat_score", 0.0)
        task.poi_data = result.get("poi_data", {})
        task.task_status = HeatTaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
    except Exception as e:
        task.task_status = HeatTaskStatus.FAILED
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(route)

    return {
        "code": 0,
        "data": {
            "route": route_to_dict(route),
            "task": heat_task_to_dict(task),
        },
    }


@router.get("/heat-tasks/{task_id}", response_model=HeatTaskOut, summary="查询热力任务状态")
def get_heat_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(BusHeatTask).filter(BusHeatTask.id == uuid.UUID(task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="热力任务不存在")
    return HeatTaskOut(**heat_task_to_dict(task))


# ════════════════════════════════════════════════════════════════
# 2. 竞价引擎 API
# ════════════════════════════════════════════════════════════════

@router.post("/bidding/calculate", summary="竞价计算")
async def calculate_bid(data: BiddingCalculateRequest, db: Session = Depends(get_db)):
    """单条线路竞价计算"""
    route = db.query(BusRoute).filter(BusRoute.id == data.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="线路不存在")

    vehicles = data.vehicles or route.vehicle_count
    result = calculate_bidding(
        monthly_price=route.monthly_price,
        level=route.level.value if route.level else "A",
        days=data.days,
        vehicles=vehicles,
        daily_traffic=route.daily_traffic,
        hotspot_traffic=route.hotspot_traffic,
        time_period=data.time_period,
    )
    result["route_id"] = str(route.id)
    result["route_code"] = route.route_code
    result["route_name"] = route.route_name

    return {"code": 0, "data": result}


@router.post("/bidding/multi", summary="多线路竞价")
async def calculate_multi_bid(data: MultiBiddingRequest, db: Session = Depends(get_db)):
    """多线路组合竞价"""
    routes = db.query(BusRoute).filter(BusRoute.id.in_(data.route_ids)).all()
    if len(routes) != len(data.route_ids):
        raise HTTPException(status_code=404, detail="部分线路不存在")

    route_data = [
        {
            "route_code": r.route_code,
            "route_name": r.route_name,
            "monthly_price": float(r.monthly_price),
            "level": r.level.value if r.level else "A",
            "vehicle_count": r.vehicle_count,
            "daily_traffic": r.daily_traffic,
            "hotspot_traffic": r.hotspot_traffic,
        }
        for r in routes
    ]

    result = calculate_multi_bidding(
        routes=route_data,
        days=data.days,
        vehicle_per_route=data.vehicle_per_route,
        time_period=data.time_period,
    )

    return {"code": 0, "data": result}


# ════════════════════════════════════════════════════════════════
# 3. 投放方案 API
# ════════════════════════════════════════════════════════════════

@router.post("/campaigns", response_model=dict, summary="创建投放方案")
async def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)):
    campaign = BusCampaign(
        advertiser_id=data.advertiser_id,
        campaign_name=data.campaign_name,
        start_date=data.start_date,
        end_date=data.end_date,
        total_budget=data.total_budget,
        ai_review_status=AiReviewStatus.PENDING,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    db.flush()  # 获取 campaign.id

    for item in data.routes:
        route = db.query(BusRoute).filter(BusRoute.id == item.route_id).first()
        if not route:
            raise HTTPException(status_code=404, detail=f"线路 {item.route_id} 不存在")

        # 计算预估展示量
        vehicles = item.vehicle_count
        days = (data.end_date - data.start_date).days if hasattr(data.end_date, '__sub__') else 30
        if isinstance(days, float):
            days = int(days)
        estimated_impressions = int(vehicles * route.daily_traffic * route.hotspot_traffic * max(days, 1))

        cr = BusCampaignRoute(
            campaign_id=campaign.id,
            route_id=item.route_id,
            vehicle_count=vehicles,
            route_budget=item.route_budget,
            actual_days=max(days, 1),
            estimated_impressions=estimated_impressions,
        )
        db.add(cr)

    db.commit()
    db.refresh(campaign)

    return {"code": 0, "data": campaign_to_dict(campaign)}


@router.get("/campaigns", response_model=dict, summary="投放方案列表")
def list_campaigns(
    advertiser_id: Optional[str] = Query(None, description="广告主筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    q = db.query(BusCampaign)
    if advertiser_id:
        q = q.filter(BusCampaign.advertiser_id == advertiser_id)
    if status:
        status_map = {"draft": CampaignStatus.DRAFT, "active": CampaignStatus.ACTIVE,
                       "completed": CampaignStatus.COMPLETED, "cancelled": CampaignStatus.CANCELLED}
        if status in status_map:
            q = q.filter(BusCampaign.status == status_map[status])

    total = q.count()
    campaigns = q.order_by(BusCampaign.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "code": 0,
        "data": {
            "total": total,
            "data": [campaign_to_dict(c) for c in campaigns],
        },
    }


@router.get("/campaigns/{campaign_id}", response_model=dict, summary="方案详情")
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(BusCampaign).filter(BusCampaign.id == uuid.UUID(campaign_id)).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="投放方案不存在")
    return {"code": 0, "data": campaign_to_dict(campaign)}


# ════════════════════════════════════════════════════════════════
# 4. AI审核 API
# ════════════════════════════════════════════════════════════════

@router.post("/campaigns/{campaign_id}/submit-review", summary="提交AI审核")
async def submit_review(campaign_id: str, db: Session = Depends(get_db)):
    """提交投放方案进行 AI审核"""
    campaign = db.query(BusCampaign).filter(BusCampaign.id == uuid.UUID(campaign_id)).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="投放方案不存在")

    if not campaign.campaign_routes:
        raise HTTPException(status_code=400, detail="方案没有选定线路，无法审核")

    review_service = AiReviewService()
    result = await review_service.review_campaign(campaign)

    # 更新方案审核状态
    campaign.ai_review_status = AiReviewStatus.PASS_ if result.get("status") == "pass" else AiReviewStatus.REJECTED
    campaign.ai_review_comment = result.get("comment", "")
    db.commit()

    return {
        "code": 0,
        "data": {
            "status": result.get("status"),
            "score": result.get("score"),
            "comment": result.get("comment"),
            "suggestions": result.get("suggestions", []),
            "reviewed_at": datetime.utcnow().isoformat(),
        },
    }


@router.get("/campaigns/{campaign_id}/review", summary="获取审核结果")
def get_review_result(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(BusCampaign).filter(BusCampaign.id == uuid.UUID(campaign_id)).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="投放方案不存在")

    return {
        "code": 0,
        "data": {
            "ai_review_status": campaign.ai_review_status.value if campaign.ai_review_status else "pending",
            "ai_review_comment": campaign.ai_review_comment,
        },
    }


# ════════════════════════════════════════════════════════════════
# 5. 效果归因API
# ════════════════════════════════════════════════════════════════

@router.post("/campaigns/{campaign_id}/attribution", summary="生成效果归因报告")
async def generate_attribution(campaign_id: str, db: Session = Depends(get_db)):
    """为已完成方案生成效果归因报告"""
    campaign = db.query(BusCampaign).filter(BusCampaign.id == uuid.UUID(campaign_id)).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="投放方案不存在")

    if not campaign.campaign_routes:
        raise HTTPException(status_code=400, detail="方案没有线路数据，无法归因")

    attr_service = AttributionService()
    result = await attr_service.calculate(campaign)

    # 保存归因结果
    campaign.attribution_report = result.get("detailed_data", {})
    campaign.status = CampaignStatus.COMPLETED

    existing_attr = db.query(BusAttribution).filter(BusAttribution.campaign_id == campaign.id).first()
    if existing_attr:
        existing_attr.total_impressions = result.get("total_impressions", 0)
        existing_attr.total_reach = result.get("total_reach", 0)
        existing_attr.cost_per_impression = Decimal(str(result.get("cost_per_impression", 0)))
        existing_attr.cost_per_reach = Decimal(str(result.get("cost_per_reach", 0)))
        existing_attr.detailed_data = result.get("detailed_data", {})
    else:
        attr = BusAttribution(
            campaign_id=campaign.id,
            total_impressions=result.get("total_impressions", 0),
            total_reach=result.get("total_reach", 0),
            cost_per_impression=Decimal(str(result.get("cost_per_impression", 0))),
            cost_per_reach=Decimal(str(result.get("cost_per_reach", 0))),
            detailed_data=result.get("detailed_data", {}),
        )
        db.add(attr)

    db.commit()

    return {
        "code": 0,
        "data": {
            "total_impressions": result.get("total_impressions"),
            "total_reach": result.get("total_reach"),
            "cost_per_impression": result.get("cost_per_impression"),
            "cost_per_reach": result.get("cost_per_reach"),
            "detailed_data": result.get("detailed_data"),
        },
    }


# ════════════════════════════════════════════════════════════════
# 6. 智能推荐 API
# ════════════════════════════════════════════════════════════════

@router.get("/recommend", summary="智能线路推荐")
async def recommend_routes(
    city: str = Query(..., description="城市"),
    budget: float = Query(..., gt=0, description="预算"),
    days: int = Query(30, ge=1, le=365, description="投放天数"),
    target_level: Optional[str] = Query(None, description="目标等级"),
    db: Session = Depends(get_db),
):
    """根据城市和预算智能推荐线路"""
    q = db.query(BusRoute).filter(
        BusRoute.city == city,
        BusRoute.status == RouteStatus.AVAILABLE,
    )
    if target_level:
        level_map = {"S": RouteLevel.S, "A++": RouteLevel.A_PLUS_PLUS, "A+": RouteLevel.A_PLUS, "A": RouteLevel.A}
        if target_level in level_map:
            q = q.filter(BusRoute.level == level_map[target_level])

    routes = q.order_by(BusRoute.heat_score.desc()).all()

    recommendations = []
    for route in routes:
        bidding = calculate_bidding(
            monthly_price=route.monthly_price,
            level=route.level.value if route.level else "A",
            days=days,
            vehicles=route.vehicle_count,
            daily_traffic=route.daily_traffic,
            hotspot_traffic=route.hotspot_traffic,
        )

        # 推荐评分：热力评分 × 预算匹配度
        price_ratio = bidding["base_price"] / budget if budget > 0 else 999
        budget_score = max(0, 1.0 - abs(price_ratio - 0.3))  # 预算的30%单条线路为最优
        rec_score = (route.heat_score / 100.0) * 0.6 + budget_score * 0.4

        if bidding["base_price"] <= budget:
            recommendations.append({
                "route": route_to_dict(route),
                "bidding_result": bidding,
                "recommendation_score": round(rec_score, 3),
                "reason": f"热力评分{route.heat_score}，预算占比{price_ratio*100:.1f}%",
            })

    recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)

    return {
        "code": 0,
        "data": {
            "city": city,
            "budget": budget,
            "days": days,
            "recommendations": recommendations[:10],
        },
    }


# ════════════════════════════════════════════════════════════════
# 7. 运营后台 API（批量热力评分）
# ════════════════════════════════════════════════════════════════

@router.post("/admin/batch-heat-score", summary="批量触发热力评分（运营）")
async def batch_heat_score(
    city: Optional[str] = Query(None, description="城市筛选"),
    db: Session = Depends(get_db),
):
    """为指定城市的所有线路批量计算热力评分"""
    q = db.query(BusRoute)
    if city:
        q = q.filter(BusRoute.city == city)

    routes = q.all()
    scorer = HeatScoringService()

    results = []
    for route in routes:
        try:
            result = await scorer.calculate(route.city, route.route_name)
            route.heat_score = result.get("heat_score", 0.0)
            results.append({"route_code": route.route_code, "status": "success", "score": result.get("heat_score")})
        except Exception as e:
            results.append({"route_code": route.route_code, "status": "failed", "error": str(e)})

    db.commit()
    return {"code": 0, "data": {"total": len(results), "results": results}}
