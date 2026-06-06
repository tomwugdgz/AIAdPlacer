"""
bus-pDOOH 子系统 — 公交车身广告 programmatic 竞价投放

ORM 数据模型，基于主 models 模块的 Base，
确保 init_db() 自动创建 bus_* 系列表。
"""
from sqlalchemy import (
    Column, String, Text, Integer, Float, DECIMAL, DateTime,
    Enum as SQLEnum, ForeignKey, JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

# 共用主模型的 Base，确保 init_db() 能扫描创建所有表
from app.models import Base


# ── 枚举定义 ──────────────────────────────────────────────

class RouteLevel(str, enum.Enum):
    S = "S"
    A_PLUS_PLUS = "A++"
    A_PLUS = "A+"
    A = "A"


class RouteStatus(str, enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    OFFLINE = "offline"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AiReviewStatus(str, enum.Enum):
    PENDING = "pending"
    PASS_ = "pass"
    REJECTED = "rejected"


class HeatTaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ── L1 公交线路资源表 ──────────────────────────────────────

class BusRoute(Base):
    __tablename__ = "bus_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city = Column(String(50), nullable=False, index=True)
    route_name = Column(String(100), nullable=False)
    route_code = Column(String(50), nullable=False, unique=True)
    level = Column(SQLEnum(RouteLevel), nullable=False, default=RouteLevel.A)
    vehicle_count = Column(Integer, nullable=False, default=1)
    monthly_price = Column(DECIMAL(12, 2), nullable=False)
    heat_score = Column(Float, default=0.0)
    daily_traffic = Column(Integer, nullable=False, default=0)
    hotspot_traffic = Column(Float, nullable=False, default=1.0)
    display_formula = Column(Text)
    pois = Column(JSON, default=list)

    # ── 行业标准曝光测量字段 (T/CCSA 738-2025) ──
    exposure_duration = Column(Float, default=15.0, comment="平均曝光时长 T_exposure（秒）")
    ad_duration = Column(Float, default=15.0, comment="单广告片时长 T_ad（秒）")
    sot = Column(Float, default=0.25, comment="时间占比 Share of Time (0-1)")
    ad_slots_per_cycle = Column(Integer, default=4, comment="轮播周期内广告数量")
    flow_otc = Column(Float, default=0.5, comment="流动曝光概率 flow_OTC (标准公式2)")
    dwell_otc = Column(Float, default=0.05, comment="驻留曝光概率 dwell_OTC (标准公式4)")

    status = Column(SQLEnum(RouteStatus), nullable=False, default=RouteStatus.AVAILABLE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign_routes = relationship("BusCampaignRoute", back_populates="route")
    heat_tasks = relationship("BusHeatTask", back_populates="route")


# ── L2 投放方案表 ──────────────────────────────────────────

class BusCampaign(Base):
    __tablename__ = "bus_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    advertiser_id = Column(String(100), nullable=False)
    campaign_name = Column(String(200), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_budget = Column(DECIMAL(14, 2), nullable=False)
    ai_review_status = Column(SQLEnum(AiReviewStatus), nullable=False, default=AiReviewStatus.PENDING)
    ai_review_comment = Column(Text)
    attribution_report = Column(JSON)
    status = Column(SQLEnum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign_routes = relationship("BusCampaignRoute", back_populates="campaign")
    attribution = relationship("BusAttribution", back_populates="campaign", uselist=False)


# ── L3 方案-线路关联表 ─────────────────────────────────────

class BusCampaignRoute(Base):
    __tablename__ = "bus_campaign_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("bus_campaigns.id"), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey("bus_routes.id"), nullable=False)
    vehicle_count = Column(Integer, nullable=False, default=1)
    route_budget = Column(DECIMAL(14, 2), nullable=False)
    actual_days = Column(Integer, nullable=False, default=1)
    estimated_impressions = Column(Integer, default=0)

    # ── 行业标准曝光测量字段 ──
    flow_impressions = Column(Integer, default=0, comment="流动曝光量 (标准公式1)")
    dwell_impressions = Column(Integer, default=0, comment="驻留曝光量 (标准公式3)")

    # Relationships
    campaign = relationship("BusCampaign", back_populates="campaign_routes")
    route = relationship("BusRoute", back_populates="campaign_routes")


# ── L4 热力评分任务表 ──────────────────────────────────────

class BusHeatTask(Base):
    __tablename__ = "bus_heat_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("bus_routes.id"), nullable=False)
    task_status = Column(SQLEnum(HeatTaskStatus), nullable=False, default=HeatTaskStatus.PENDING)
    heat_score = Column(Float)
    poi_data = Column(JSON)
    error_message = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    route = relationship("BusRoute", back_populates="heat_tasks")


# ── L5 效果归因表 ─────────────────────────────────────────

class BusAttribution(Base):
    __tablename__ = "bus_attribution"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("bus_campaigns.id"), nullable=False)
    total_impressions = Column(Integer, default=0)
    total_reach = Column(Integer, default=0)
    cost_per_impression = Column(DECIMAL(10, 4))
    cost_per_reach = Column(DECIMAL(10, 4))
    detailed_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ── 行业标准曝光测量字段 (T/CCSA 738-2025) ──
    flow_impressions = Column(Integer, default=0, comment="流动曝光量 IMP_flow")
    dwell_impressions = Column(Integer, default=0, comment="驻留曝光量 IMP_dwell")
    effective_impressions = Column(Integer, default=0, comment="有效曝光量")
    impression_multiplier = Column(Float, default=1.0, comment="曝光乘数 (标准公式6)")
    frequency = Column(Float, default=0.0, comment="接触频次 = 有效展示/独立受众")
    independent_audience = Column(Integer, default=0, comment="独立受众数量")

    # Relationships
    campaign = relationship("BusCampaign", back_populates="attribution")
