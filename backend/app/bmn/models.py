"""
BMN 数据库模型 — 品牌逻辑引擎 + 资产金库 + 工作流 + 指标
"""
from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, Float, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

# 共用主模型的 Base，确保 init_db() 能扫描创建所有表
from app.models import Base


# ── 枚举定义 ──────────────────────────────────────

class AssetType(str, enum.Enum):
    BRAND_APPEAL = "brand_appeal"           # 品牌诉求库
    PRODUCT_SELLING = "product_selling"      # 产品卖点库
    USER_SCENARIO = "user_scenario"          # 用户场景库
    CUSTOMER_CASE = "customer_case"           # 客户案例库
    INDUSTRY_KNOWLEDGE = "industry_knowledge" # 行业知识库
    VISUAL_ASSET = "visual_asset"           # 视觉资产库
    QA_SCRIPT = "qa_script"                  # 问答口径库
    RISK_BOUNDARY = "risk_boundary"          # 风险边界库


# ── L1 品牌配置表 ─────────────────────────────────────────

class BmnBrandConfig(Base):
    __tablename__ = "bmn_brand_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_name = Column(String(100), nullable=False, unique=True)
    identity = Column(Text)                  # 身份定位
    value_proposition = Column(Text)          # 价值定位
    trust_proof = Column(JSON, default=list)  # 信任背书（数组）
    differentiation = Column(Text)             # 差异化定位
    master_prompt = Column(Text)             # 生成的母指令
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── L2 资产金库表 ─────────────────────────────────────────

class BmnAsset(Base):
    __tablename__ = "bmn_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)         # 标签数组
    chroma_doc_id = Column(String(200))       # ChromaDB 文档 ID
    usage_count = Column(Integer, default=0)
    source = Column(String(100))              # 来源（客户名/项目名称）
    extra_data = Column(JSON, default=dict)   # 扩展字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __mapper_args__ = {
        "polymorphic_identity": "bmn_asset",
    }


# ── L3 工作流运行记录表 ──────────────────────────────────

class BmnWorkflowRun(Base):
    __tablename__ = "bmn_workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_name = Column(String(50), nullable=False)  # case_study / new_product_launch
    status = Column(String(20), default="running")      # running / success / failed
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error_msg = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)


# ── L5 增长指标表 ───────────────────────────────────────

class BmnMetric(Base):
    __tablename__ = "bmn_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(String(30), nullable=False)
    # 类型枚举: awareness / trust / engagement / conversion / asset
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    period = Column(String(20))          # daily / weekly / monthly
    related_asset_id = Column(UUID(as_uuid=True), ForeignKey("bmn_assets.id"))
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
