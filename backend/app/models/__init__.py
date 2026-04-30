from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, Date, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class MediaResource(Base):
    __tablename__ = "media_resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # offline/online
    category = Column(String(50), nullable=False)  # billboard/elevator/bus_stop/web/app/social
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(Text)
    coverage_radius = Column(Integer, default=1000)  # 覆盖半径（米）
    daily_price = Column(DECIMAL(10, 2))
    daily_impressions = Column(Integer, default=0)  # 日均曝光量
    status = Column(String(20), default="available")  # available/booked/maintenance
    custom_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    budget = Column(DECIMAL(12, 2))
    start_date = Column(Date)
    end_date = Column(Date)
    target_audience = Column(JSON, default=dict)  # 目标人群标签
    status = Column(String(20), default="draft")  # draft/active/paused/completed
    ai_recommendations = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CampaignMedia(Base):
    """投放计划与媒体资源的关联表"""
    __tablename__ = "campaign_media"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    media_id = Column(UUID(as_uuid=True), ForeignKey("media_resources.id"))
    budget_allocation = Column(DECIMAL(10, 2))  # 分配预算
    scheduled_dates = Column(JSON, default=list)


class Placement(Base):
    __tablename__ = "placements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    media_id = Column(UUID(as_uuid=True), ForeignKey("media_resources.id"))
    date = Column(Date, nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    cost = Column(DECIMAL(10, 2))
    latitude = Column(Float)
    longitude = Column(Float)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversion(Base):
    __tablename__ = "conversions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placement_id = Column(UUID(as_uuid=True), ForeignKey("placements.id"))
    user_id = Column(String(100))
    conversion_type = Column(String(50))  # purchase/signup/download/etc
    conversion_value = Column(DECIMAL(10, 2))
    touchpoint_order = Column(Integer, default=1)  # 触点顺序
    attribution_model = Column(String(20))  # first/last/linear/time_decay
    location_lat = Column(Float)
    location_lng = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")


if __name__ == "__main__":
    init_db()
