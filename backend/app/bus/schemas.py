"""
bus-pDOOH 子系统 — 公交线路广告 Pydantic Schema 定义
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


# ── BusRoute Schemas ──────────────────────────────────────

class BusRouteCreate(BaseModel):
    """线路创建"""
    city: str = Field(..., description="城市")
    route_name: str = Field(..., max_length=100, description="线路名称")
    route_code: str = Field(..., max_length=50, description="线路编号")
    level: str = Field(default="A", description="线路等级 S/A++/A+/A")
    vehicle_count: int = Field(default=1, ge=1, description="车辆数")
    monthly_price: float = Field(..., gt=0, description="月单价（元）")
    daily_traffic: int = Field(default=0, ge=0, description="日均客流")
    hotspot_traffic: float = Field(default=1.0, ge=1.0, le=3.0, description="热点系数")
    display_formula: Optional[str] = Field(None, description="展示公式")
    pois: Optional[List[Dict[str, Any]]] = Field(default=None, description="POI数据")


class BusRouteUpdate(BaseModel):
    """线路更新（全部可选）"""
    city: Optional[str] = None
    route_name: Optional[str] = None
    route_code: Optional[str] = None
    level: Optional[str] = None
    vehicle_count: Optional[int] = None
    monthly_price: Optional[float] = None
    daily_traffic: Optional[int] = None
    hotspot_traffic: Optional[float] = None
    display_formula: Optional[str] = None
    pois: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class BusRouteOut(BaseModel):
    """线路输出"""
    id: UUID
    city: str
    route_name: str
    route_code: str
    level: str
    vehicle_count: int
    monthly_price: float
    heat_score: float
    daily_traffic: int
    hotspot_traffic: float
    display_formula: Optional[str] = None
    pois: Optional[List[Dict[str, Any]]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BusRouteListOut(BaseModel):
    """线路列表输出"""
    total: int
    data: List[BusRouteOut]


class BusRouteStatusUpdate(BaseModel):
    """状态变更"""
    status: str = Field(..., description="available / booked / offline")


# ── Excel Import ──────────────────────────────────────────

class ExcelImportResult(BaseModel):
    """Excel 导入结果"""
    total_rows: int
    success_count: int
    failed_count: int
    failed_reasons: List[str] = Field(default_factory=list)


# ── Bidding Schemas ───────────────────────────────────────

class BiddingCalculateRequest(BaseModel):
    """竞价计算请求"""
    route_id: UUID
    days: int = Field(..., ge=1, le=365, description="投放天数")
    vehicles: Optional[int] = Field(None, ge=1, description="车辆数（覆盖线路默认值）")
    time_period: str = Field(default="normal", description="morning_rush / evening_rush / normal")


class MultiBiddingRequest(BaseModel):
    """多线路竞价请求"""
    route_ids: List[UUID] = Field(..., min_length=1, description="线路ID列表")
    days: int = Field(..., ge=1, le=365, description="投放天数")
    vehicle_per_route: Optional[int] = Field(None, ge=1, description="统一车辆数")
    time_period: str = Field(default="normal", description="时段类型")


# ── Campaign Schemas ──────────────────────────────────────

class CampaignRouteItem(BaseModel):
    """方案-线路关联项"""
    route_id: UUID
    vehicle_count: int = Field(default=1, ge=1, description="车辆数")
    route_budget: float = Field(..., gt=0, description="线路预算")


class CampaignCreate(BaseModel):
    """投放方案创建"""
    advertiser_id: str = Field(..., max_length=100, description="广告主ID")
    campaign_name: str = Field(..., max_length=200, description="方案名称")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    total_budget: float = Field(..., gt=0, description="总预算")
    routes: List[CampaignRouteItem] = Field(..., min_length=1, description="线路列表")


class CampaignRouteOut(BaseModel):
    """方案-线路关联输出"""
    id: UUID
    route_id: UUID
    vehicle_count: int
    route_budget: float
    actual_days: int
    estimated_impressions: int
    route_info: Optional[BusRouteOut] = None

    class Config:
        from_attributes = True


class CampaignOut(BaseModel):
    """投放方案输出"""
    id: UUID
    advertiser_id: str
    campaign_name: str
    start_date: datetime
    end_date: datetime
    total_budget: float
    ai_review_status: str
    ai_review_comment: Optional[str] = None
    attribution_report: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    routes: List[CampaignRouteOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CampaignListOut(BaseModel):
    """投放方案列表输出"""
    total: int
    data: List[CampaignOut]


# ── Heat Task Schemas ─────────────────────────────────────

class HeatTaskOut(BaseModel):
    """热力评分任务输出"""
    id: UUID
    route_id: UUID
    task_status: str
    heat_score: Optional[float] = None
    poi_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Attribution Schemas ───────────────────────────────────

class AttributionOut(BaseModel):
    """效果归因输出"""
    id: UUID
    campaign_id: UUID
    total_impressions: int
    total_reach: int
    cost_per_impression: float
    cost_per_reach: float
    detailed_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ── AI Review Schemas ─────────────────────────────────────

class AiReviewResult(BaseModel):
    """AI 审核结果"""
    status: str  # pass / rejected
    score: int  # 0-100
    comment: str
    suggestions: List[str] = Field(default_factory=list)
    reviewed_at: datetime


# ── Recommend Schemas ─────────────────────────────────────

class RecommendRequest(BaseModel):
    """智能推荐请求"""
    city: str = Field(..., description="城市")
    budget: float = Field(..., gt=0, description="预算")
    days: int = Field(default=30, ge=1, le=365, description="投放天数")
    target_level: Optional[str] = Field(None, description="目标等级")


class RecommendItem(BaseModel):
    """推荐线路"""
    route: BusRouteOut
    bidding_result: Dict[str, Any]
    recommendation_score: float
    reason: str


class RecommendOut(BaseModel):
    """智能推荐输出"""
    city: str
    budget: float
    days: int
    recommendations: List[RecommendItem]
