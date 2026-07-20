"""
智能屏资源子系统（Smart Screen L9）— Pydantic 响应模型。

定义统一的 API 响应数据结构（与 db_api 风格一致）：
- 表信息 / 小区宽表 / 指标 / 媒体项 / 统计 / 算法
- 统一响应信封 UnifiedResponse（success/data/error/code/total?）

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── 统一响应信封 ────────────────────────────────────────────────────────────────

class UnifiedResponse(BaseModel):
    """子系统统一响应体：{success, data|error, code, total?}。"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    code: str = "OK"
    total: Optional[int] = None


# ── 各实体模型 ──────────────────────────────────────────────────────────────────

class TableInfo(BaseModel):
    """表信息。"""
    name: str
    count: int
    columns: List[str] = Field(default_factory=list)


class CommunityWideOut(BaseModel):
    """小区级宽表（含关联层补充的 名称/省/市/区）。"""
    community_id: str
    community_name: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    household_count: Optional[int] = None
    occupancy_rate: Optional[float] = None
    building_count: Optional[int] = None
    gate_device_count: Optional[int] = None
    access_device_count: Optional[int] = None
    monthly_failure_rate: Optional[float] = None
    historical_launch_count: Optional[int] = None
    covered_industry_count: Optional[int] = None
    ad_door_avg_price: Optional[float] = None
    access_lightbox_price: Optional[float] = None


class IndicatorOut(BaseModel):
    """小区/点位级 39 指标（indicators 为 字段名->分值 映射）。"""
    community_id: str
    point_id: Optional[str] = None
    computed_at: Optional[str] = None
    indicators: Dict[str, float] = Field(default_factory=dict)


class MediaItemOut(BaseModel):
    """媒体列表项（12 原始列 + 派生关联键）。"""
    id: Optional[int] = None
    所属省份: Optional[str] = None
    所属城市: Optional[str] = None
    区或县: Optional[str] = Field(None, alias="区/县")
    网点名称: Optional[str] = None
    楼盘类型: Optional[str] = None
    住户数: Optional[str] = None
    楼盘价格: Optional[str] = None
    点位名称: Optional[str] = None
    详细地址: Optional[str] = None
    点位ID: Optional[str] = None
    MAC: Optional[str] = None
    终端型号: Optional[str] = None
    community_id: Optional[str] = None
    device_id: Optional[str] = None
    media_id: Optional[str] = None
    point_id: Optional[str] = None
    plan_id: Optional[str] = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class AlgorithmOut(BaseModel):
    """算法注册信息。"""
    code: str
    name: str
    category: Optional[str] = None
    source: Optional[str] = None
    journal_level: Optional[str] = None
    validated_city: Optional[str] = None
    input_fields: List[str] = Field(default_factory=list)
    weight: Optional[float] = None
    formula_hint: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class StatsOut(BaseModel):
    """子系统整体统计。"""
    total_media: int = 0
    total_communities: int = 0
    total_devices: int = 0
    total_indicators: int = 0
    total_algorithms: int = 0
    by_city: Dict[str, int] = Field(default_factory=dict)
    by_province: Dict[str, int] = Field(default_factory=dict)


class PagedMediaOut(BaseModel):
    """媒体分页结果。"""
    data: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
