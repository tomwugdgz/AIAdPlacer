"""
ROI Agent — 广告投放 ROI 计算专家 Agent
端口: 5004
功能:
  - /api/v2/roi/calculate       三场景 ROI 计算（悲观/中性/乐观）
  - /api/v2/roi/sensitivity     灵敏度分析（参数变动对 ROI 影响）
  - /api/v2/roi/compare        多方案对比
  - /api/v2/roi/formula         公式说明与参数定义
  - /health                      健康检查
"""

import os
import sys
import json
import math
import asyncio
import time
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from pydantic import BaseModel, Field, validator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

# ── 导入公共模块 ────────────────────────────────────────────────────────────────
from app.common import (
    setup_logging,
    PDOOHError,
    ValidationError,
    monitor_performance,
    monitor_performance_async,
    cached,
    retry_async,
    validate_params,
    generate_request_id,
    format_error_response,
)

# ── 日志 ────────────────────────────────────────────────────────────────────────
logger = setup_logging("roi_agent", log_file="logs/roi_agent.log")
logger.info("ROI Agent 启动中...")

router = APIRouter(prefix="/api/v2/roi", tags=["ROI Agent"])

# ── 公式常量与默认参数 ────────────────────────────────────────────────────────────
# 来源：duckwolf.cn/10.html（黑人牙膏 × 皓邻传媒 社区精准营销合作方案 v5.0）

DEFAULT_PARAMS = {
    # 基础参数
    "N": 5000,       # 广告框数（个）
    "U": 100,        # 每栋楼户数（户/栋）[MCP 数据库 711 广州楼盘中位数]
    "P": 2.51,      # 每户人数（人/户）[国家统计局《中国统计年鉴2024》]
    "beta": 0.85,    # 接触率（%）[皓邻 5 年实测]

    # 曝光参数
    "gamma": 2.0,    # 每日接触频次（次/户/日）[单面灯箱]
    "T": 14,         # 投放天数（天）

    # 记忆率（三场景）
    "r_pessimistic": 0.15,  # 悲观场景记忆率
    "r_neutral": 0.18,      # 中性场景记忆率（行业基线中位）
    "r_optimistic": 0.22,   # 乐观场景记忆率（双面+智能屏 4 周）

    # 客单价（三场景，单位：元）
    "a_pessimistic": 20,  # 悲观场景客单价
    "a_neutral": 22,        # 中性场景客单价（黑人双重薄荷 120g）
    "a_optimistic": 25,     # 乐观场景客单价（组合购买）

    # 复购系数（三场景）
    "f_pessimistic": 1.3,  # 悲观场景复购系数
    "f_neutral": 1.4,      # 中性场景复购系数
    "f_optimistic": 1.5,    # 乐观场景复购系数

    # 转化率（%）
    "c": 0.02,      # 记忆→购买转化率（2%）

    # 成本
    "cost_per_frame": 20,  # 每框成本（元/框/2周）[方案A]
    "cost_per_frame_4w": 60, # 每框成本（元/框/4周）[方案B]
}

# ── 城市参数自动调整映射 ────────────────────────────────────────────────────────────
# 根据城市等级自动调整参数（U/β/a）
CITY_PARAMS = {
    "一线城市": {
        "cities": ["北京", "上海", "广州", "深圳"],
        "U": 80,      # 每栋楼户数较少（高端楼盘）
        "beta": 0.82, # 接触率略低（选择多）
        "a": 30,      # 客单价较高
        "r_base": 0.17, # 记忆率基准
    },
    "新一线城市": {
        "cities": ["成都", "杭州", "重庆", "西安", "武汉", "苏州", "天津", "南京", "郑州", "长沙", "东莞", "沈阳", "青岛", "合肥", "佛山"],
        "U": 100,
        "beta": 0.85,
        "a": 22,
        "r_base": 0.18,
    },
    "二线城市": {
        "cities": ["昆明", "福州", "无锡", "厦门", "哈尔滨", "长春", "南昌", "济南", "宁波", "大连", "贵阳", "温州", "石家庄", "泉州", "南宁", "金华", "常州", "珠海", "惠州", "嘉兴", "南通", "中山", "保定", "兰州", "台州", "徐州", "太原", "绍兴", "烟台", "廊坊"],
        "U": 110,
        "beta": 0.87,
        "a": 18,
        "r_base": 0.19,
    },
    "三线及以下": {
        "cities": [],  # 其他城市
        "U": 120,
        "beta": 0.90,
        "a": 15,
        "r_base": 0.20,
    },
}

# ── 产品类型参数自动调整映射 ────────────────────────────────────────────────────────
# 根据产品类型自动调整参数（r/a/f）
PRODUCT_PARAMS = {
    "日化": {
        "keywords": ["牙膏", "洗发水", "沐浴露", "洗衣液", "洗面奶", "护肤品", "化妆品", "香皂", "牙刷"],
        "r_mult": 1.0,   # 记忆率倍数
        "a_base": 25,    # 客单价基准
        "f_mult": 1.1,   # 复购系数倍数（日化复购高）
    },
    "食品": {
        "keywords": ["食品", "零食", "饮料", "牛奶", "酸奶", "面包", "饼干", "巧克力", "糖果"],
        "r_mult": 1.1,   # 食品记忆率较高
        "a_base": 15,    # 客单价较低
        "f_mult": 1.2,   # 食品复购很高
    },
    "家电": {
        "keywords": ["电视", "冰箱", "洗衣机", "空调", "微波炉", "烤箱", "家电", "数码", "手机", "电脑"],
        "r_mult": 0.9,   # 家电记忆率较低
        "a_base": 50,    # 客单价很高
        "f_mult": 0.8,   # 家电复购低
    },
    "母婴": {
        "keywords": ["母婴", "奶粉", "纸尿裤", "婴儿", "孕妇", "玩具", "童装"],
        "r_mult": 1.2,   # 母婴记忆率很高
        "a_base": 35,    # 客单价较高
        "f_mult": 1.3,   # 母婴复购高
    },
    "汽车": {
        "keywords": ["汽车", "新能源车", "电动车", "4S店", "保养", "轮胎"],
        "r_mult": 0.8,   # 汽车记忆率较低
        "a_base": 100,   # 客单价很高
        "f_mult": 0.6,   # 汽车复购很低
    },
    "其他": {
        "keywords": [],
        "r_mult": 1.0,
        "a_base": 22,
        "f_mult": 1.0,
    },
}

def detect_city_tier(city: str) -> str:
    """
    检测城市等级
    
    返回：一线城市/新一线城市/二线城市/三线及以下
    """
    for tier, params in CITY_PARAMS.items():
        if city in params["cities"]:
            return tier
    return "三线及以下"

def detect_product_type(product: str) -> str:
    """
    检测产品类型
    
    返回：日化/食品/家电/母婴/汽车/其他
    """
    for ptype, params in PRODUCT_PARAMS.items():
        if ptype != "其他":
            for keyword in params["keywords"]:
                if keyword in product:
                    return ptype
    return "其他"

def adjust_params_by_context(city: str = None, product: str = None, U: float = None, a: float = None, r: float = None, f: float = None):
    """
    根据城市和产品类型自动调整参数
    
    返回调整后的参数字典
    
    Args:
        city: 投放城市（如 "广州"、"北京"）
        product: 产品类型（如 "牙膏"、"洗发水"）
        U: 每栋楼户数（如果提供，则使用提供值）
        a: 客单价（如果提供，则使用提供值）
        r: 记忆率（如果提供，则使用提供值）
        f: 复购系数（如果提供，则使用提供值）
        
    Returns:
        Dict[str, Any]: 调整后的参数字典
        
    Example:
        >>> params = adjust_params_by_context(city="广州", product="牙膏")
        >>> print(params["U"])  # 输出: 80（一线城市）
    """
    params = DEFAULT_PARAMS.copy()
    
    # 记录调整前的参数值
    logger.debug(f"参数调整前: U={params['U']}, beta={params['beta']}, a_neutral={params['a_neutral']}")
    
    # 如果传入了具体值，使用传入值
    if U is not None:
        params["U"] = U
        logger.info(f"使用用户指定的 U 值: {U}")
    if a is not None:
        params["a_neutral"] = a
        params["a_pessimistic"] = a * 0.9
        params["a_optimistic"] = a * 1.15
        logger.info(f"使用用户指定的 a 值: {a}")
    if r is not None:
        params["r_neutral"] = r
        params["r_pessimistic"] = r * 0.85
        params["r_optimistic"] = r * 1.2
        logger.info(f"使用用户指定的 r 值: {r}")
    if f is not None:
        params["f_neutral"] = f
        params["f_pessimistic"] = f * 0.95
        params["f_optimistic"] = f * 1.05
        logger.info(f"使用用户指定的 f 值: {f}")
    
    # 根据城市调整参数
    if city:
        city_tier = detect_city_tier(city)
        city_params = CITY_PARAMS[city_tier]
        params["U"] = city_params["U"]
        params["beta"] = city_params["beta"]
        if a is None:  # 如果没有传入 a，使用城市默认值
            params["a_neutral"] = city_params["a"]
            params["a_pessimistic"] = city_params["a"] * 0.9
            params["a_optimistic"] = city_params["a"] * 1.15
        if r is None:  # 如果没有传入 r，使用城市默认值
            params["r_neutral"] = city_params["r_base"]
            params["r_pessimistic"] = city_params["r_base"] * 0.85
            params["r_optimistic"] = city_params["r_base"] * 1.2
        logger.info(f"根据城市 {city}（{city_tier}）调整参数: U={params['U']}, beta={params['beta']}")
    
    # 根据产品类型调整参数
    if product:
        product_type = detect_product_type(product)
        product_params = PRODUCT_PARAMS[product_type]
        if r is None:  # 如果没有传入 r，使用产品类型调整
            params["r_neutral"] *= product_params["r_mult"]
            params["r_pessimistic"] = params["r_neutral"] * 0.85
            params["r_optimistic"] = params["r_neutral"] * 1.2
        if a is None:  # 如果没有传入 a，使用产品类型调整
            params["a_neutral"] = product_params["a_base"]
            params["a_pessimistic"] = product_params["a_base"] * 0.9
            params["a_optimistic"] = product_params["a_base"] * 1.15
        params["f_neutral"] *= product_params["f_mult"]
        params["f_pessimistic"] = params["f_neutral"] * 0.95
        params["f_optimistic"] = params["f_neutral"] * 1.05
        logger.info(f"根据产品 {product}（{product_type}）调整参数: r_neutral={params['r_neutral']}, a_neutral={params['a_neutral']}, f_neutral={params['f_neutral']}")
    
    # 记录调整后的参数值
    logger.debug(f"参数调整后: U={params['U']}, beta={params['beta']}, a_neutral={params['a_neutral']}, r_neutral={params['r_neutral']}, f_neutral={params['f_neutral']}")
    
    return params

# ── 公式函数 ──────────────────────────────────────────────────────────────────────

def calc_uv(N: int, U: float, P: float, beta: float) -> int:
    """
    UV（独立触达人数）= N × U × P × β
    
    参数来源：
    - N: 本方案设定
    - U: MCP 数据库 711 广州楼盘中位数
    - P: 国家统计局《中国统计年鉴2024》
    - β: 皓邻 5 年实测
    """
    return int(N * U * P * beta)

def calc_pv(uv: int, gamma: float, T: int) -> int:
    """
    PV（总曝光次数）= UV × γ × T
    
    - γ: 单面灯箱 2.0 次/户/日（双面 3.8）
    - T: 投放天数
    """
    return int(uv * gamma * T)

def calc_recall_uv(uv: int, r: float) -> int:
    """
    记忆人数 = UV × 记忆率(r)
    """
    return int(uv * r)

def calc_conversion(recall_uv: int, c: float = 0.02) -> int:
    """
    转化人数 = 记忆人数 × 转化率(c)
    
    - c: 记忆→购买转化率（默认 2%）
    """
    return int(recall_uv * c)

def calc_first_sale(conversions: int, a: float) -> float:
    """
    首期销售 = 转化人数 × 客单价(a)
    """
    return conversions * a

def calc_ltv(first_sale: float, f: float, weeks: int = 8) -> float:
    """
    LTV（生命周期价值）= 首期销售 × (1 + 复购系数(f))
    
    注：本方案采用 8 周 LTV（牙膏使用周期 1-3 月）
    - f: 复购系数（悲观 1.3 / 中性 1.4 / 乐观 1.5）
    """
    return first_sale * f

def calc_roi(ltv: float, cost: float) -> float:
    """
    ROI（投资回报率）= (LTV - 投入成本) / 投入成本 × 100%
    
    返回百分比（如 181.6 表示 181.6%）
    """
    if cost == 0:
        return float('inf')
    return (ltv - cost) / cost * 100

@monitor_performance
def calc_roi_full(
    N: int = 5000,
    U: float = 100,
    P: float = 2.51,
    beta: float = 0.85,
    gamma: float = 2.0,
    T: int = 14,
    r: float = 0.18,
    a: float = 22,
    f: float = 1.4,
    c: float = 0.02,
    cost: float = 100000,
    weeks: int = 8,
) -> Dict[str, Any]:
    """
    完整 ROI 计算（调用所有子公式）
    
    返回包含所有中间结果的字典
    
    Args:
        N: 广告框数（个）
        U: 每栋楼户数（户/栋）
        P: 每户人数（人/户）
        beta: 接触率（%）
        gamma: 每日接触频次（次/户/日）
        T: 投放天数（天）
        r: 记忆率（0-1）
        a: 客单价（元）
        f: 复购系数
        c: 转化率（0-1）
        cost: 投入成本（元）
        weeks: LTV 计算周期（周）
        
    Returns:
        Dict[str, Any]: 包含参数、中间结果和最终结果的字典
        
    Example:
        >>> result = calc_roi_full(N=5000, cost=100000)
        >>> print(result["result"]["roi_percent"])
    """
    logger.info(f"开始计算 ROI: N={N}, U={U}, cost={cost}")
    
    uv = calc_uv(N, U, P, beta)
    pv = calc_pv(uv, gamma, T)
    recall = calc_recall_uv(uv, r)
    conversions = calc_conversion(recall, c)
    first_sale = calc_first_sale(conversions, a)
    ltv = calc_ltv(first_sale, f, weeks)
    roi = calc_roi(ltv, cost)
    
    logger.info(f"ROI 计算完成: ROI={roi:.2f}%, LTV={ltv:.2f}")
    
    return {
        "params": {
            "N": N, "U": U, "P": P, "beta": beta,
            "gamma": gamma, "T": T,
            "r": r, "a": a, "f": f, "c": c,
            "cost": cost, "weeks": weeks,
        },
        "intermediates": {
            "uv": uv,
            "pv": pv,
            "recall": recall,
            "conversions": conversions,
            "first_sale": first_sale,
            "ltv": ltv,
        },
        "result": {
            "roi_percent": round(roi, 2),
            "ltv": round(ltv, 2),
            "cost": cost,
            "net_profit": round(ltv - cost, 2),
        }
    }

@cached(ttl=300, maxsize=100)  # 缓存 5 分钟，最多 100 条
def calc_three_scenarios(
    N: int = 5000,
    U: float = 100,
    P: float = 2.51,
    beta: float = 0.85,
    gamma: float = 2.0,
    T: int = 14,
    cost: float = 100000,
    weeks: int = 8,
    r_neutral: float = None,
    a_neutral: float = None,
    f_neutral: float = None,
) -> Dict[str, Any]:
    """
    计算三场景 ROI（悲观/中性/乐观）
    
    返回三个场景的完整计算结果
    
    新增参数：
    - r_neutral: 中性场景记忆率（如果提供，使用该值；否则使用 DEFAULT_PARAMS）
    - a_neutral: 中性场景客单价（如果提供，使用该值；否则使用 DEFAULT_PARAMS）
    - f_neutral: 中性场景复购系数（如果提供，使用该值；否则使用 DEFAULT_PARAMS）
    
    Args:
        N: 广告框数（个）
        U: 每栋楼户数（户/栋）
        P: 每户人数（人/户）
        beta: 接触率（%）
        gamma: 每日接触频次（次/户/日）
        T: 投放天数（天）
        cost: 投入成本（元）
        weeks: LTV 计算周期（周）
        r_neutral: 中性场景记忆率
        a_neutral: 中性场景客单价
        f_neutral: 中性场景复购系数
        
    Returns:
        Dict[str, Any]: 三个场景的计算结果
        
    Example:
        >>> results = calc_three_scenarios(N=5000, cost=100000, city="广州")
        >>> print(results["neutral"]["roi_percent"])
    """
    logger.info(f"开始计算三场景 ROI: N={N}, cost={cost}, T={T}")
    if r_neutral is not None:
        logger.info(f"使用指定的 r_neutral: {r_neutral}")
    if a_neutral is not None:
        logger.info(f"使用指定的 a_neutral: {a_neutral}")
    if f_neutral is not None:
        logger.info(f"使用指定的 f_neutral: {f_neutral}")
    
    params = DEFAULT_PARAMS.copy()
    
    # 使用传入的参数（如果提供）
    if r_neutral is not None:
        params["r_neutral"] = r_neutral
        params["r_pessimistic"] = r_neutral * 0.85
        params["r_optimistic"] = r_neutral * 1.2
    if a_neutral is not None:
        params["a_neutral"] = a_neutral
        params["a_pessimistic"] = a_neutral * 0.9
        params["a_optimistic"] = a_neutral * 1.15
    if f_neutral is not None:
        params["f_neutral"] = f_neutral
        params["f_pessimistic"] = f_neutral * 0.95
        params["f_optimistic"] = f_neutral * 1.05
    
    scenarios = {
        "pessimistic": {
            "r": params["r_pessimistic"],
            "a": params["a_pessimistic"],
            "f": params["f_pessimistic"],
            "label": "悲观场景",
            "desc": "单元门单面+2周短投",
        },
        "neutral": {
            "r": params["r_neutral"],
            "a": params["a_neutral"],
            "f": params["f_neutral"],
            "label": "中性场景",
            "desc": "行业基线中位",
        },
        "optimistic": {
            "r": params["r_optimistic"],
            "a": params["a_optimistic"],
            "f": params["f_optimistic"],
            "label": "乐观场景",
            "desc": "双面+智能屏 4周",
        },
    }
    
    results = {}
    for key, scen in scenarios.items():
        result = calc_roi_full(
            N=N, U=U, P=P, beta=beta,
            gamma=gamma, T=T,
            r=scen["r"], a=scen["a"], f=scen["f"],
            cost=cost, weeks=weeks,
        )
        results[key] = {
            "label": scen["label"],
            "desc": scen["desc"],
            "r": scen["r"],
            "a": scen["a"],
            "f": scen["f"],
            "uv": result["intermediates"]["uv"],
            "pv": result["intermediates"]["pv"],
            "recall": result["intermediates"]["recall"],
            "conversions": result["intermediates"]["conversions"],
            "first_sale": result["intermediates"]["first_sale"],
            "ltv": result["result"]["ltv"],
            "roi_percent": result["result"]["roi_percent"],
            "net_profit": result["result"]["net_profit"],
        }
    
    logger.info(f"三场景 ROI 计算完成: 悲观={results['pessimistic']['roi_percent']:.2f}%, 中性={results['neutral']['roi_percent']:.2f}%, 乐观={results['optimistic']['roi_percent']:.2f}%")
    
    return results

# ── 请求/响应模型 ─────────────────────────────────────────────────────────────

class ROICalculateRequest(BaseModel):
    """ROI 计算请求"""
    N: int = Field(5000, description="广告框数（个）")
    U: float = Field(100, description="每栋楼户数（户/栋）")
    P: float = Field(2.51, description="每户人数（人/户）")
    beta: float = Field(0.85, description="接触率（%）")

    gamma: float = Field(2.0, description="每日接触频次（次/户/日）")
    T: int = Field(14, description="投放天数（天）")

    r: float = Field(0.18, description="记忆率（0-1）")
    a: float = Field(22, description="客单价（元）")
    f: float = Field(1.4, description="复购系数（倍）")

    c: float = Field(0.02, description="转化率（0-1）")

    cost: float = Field(100000, description="投入成本（元）")
    weeks: int = Field(8, description="LTV 计算周期（周）")

    scenario: Optional[str] = Field(None, description="预设场景：pessimistic/neutral/optimistic")
    
    # 新增：参数自动调整
    city: Optional[str] = Field(None, description="投放城市（用于自动调整参数）")
    product: Optional[str] = Field(None, description="产品类型（用于自动调整参数）")
    auto_adjust: bool = Field(True, description="是否自动调整参数（根据城市/产品）")

class ROICalculateResponse(BaseModel):
    """ROI 计算响应"""
    request_id: Optional[str] = None
    scenario: Optional[str] = None
    uv: int
    pv: int
    recall: int
    conversions: int
    first_sale: float
    ltv: float
    roi_percent: float
    net_profit: float
    params: Dict[str, Any]
    formula: str
    auto_adjusted: Optional[bool] = None
    adjust_info: Optional[Dict[str, Any]] = None

class SensitivityRequest(BaseModel):
    """灵敏度分析请求"""
    base_params: ROICalculateRequest
    variable: str = Field(..., description="变动参数：r/a/f/N/cost")
    values: List[float] = Field(..., description="参数取值列表")

class SensitivityResponse(BaseModel):
    """灵敏度分析响应"""
    variable: str
    values: List[float]
    roi_values: List[float]
    ltv_values: List[float]

class CompareRequest(BaseModel):
    """多方案对比请求"""
    scenarios: List[ROICalculateRequest]

class CompareResponse(BaseModel):
    """多方案对比响应"""
    scenarios: List[Dict[str, Any]]
    summary: str

# ── API 端点 ─────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """健康检查"""
    logger.info("收到健康检查请求")
    return {"status": "ok", "agent": "ROI Agent", "version": "2.3.0"}

@router.post("/calculate", response_model=Dict[str, Any])
@monitor_performance_async(logger=logger)
async def calculate_roi(req: ROICalculateRequest):
    """
    ROI 计算（支持三场景预设 + 参数自动调整）
    
    传入 scenario 可快速计算预设场景：
    - pessimistic: 悲观（记忆率 0.15 / 客单 ¥20 / 复购 1.3）
    - neutral: 中性（记忆率 0.18 / 客单 ¥22 / 复购 1.4）
    - optimistic: 乐观（记忆率 0.22 / 客单 ¥25 / 复购 1.5）
    
    传入 city 和 product 可自动调整参数：
    - city: 投放城市（一线城市/新一线城市/二线城市/三线及以下）
    - product: 产品类型（日化/食品/家电/母婴/汽车/其他）
    - auto_adjust: 是否自动调整参数（默认 True）
    
    Args:
        req: ROI 计算请求对象
        
    Returns:
        Dict[str, Any]: ROI 计算结果
        
    Raises:
        HTTPException: 参数验证失败或计算错误
    """
    request_id = generate_request_id("roi")
    logger.info(f"收到 ROI 计算请求 [{request_id}]: N={req.N}, cost={req.cost}, city={req.city}, product={req.product}")
    
    try:
        # 参数验证
        if req.N <= 0:
            raise ValidationError(message="广告框数 N 必须大于 0", details={"N": req.N})
        if req.cost <= 0:
            raise ValidationError(message="投入成本 cost 必须大于 0", details={"cost": req.cost})
        if not (0 < req.r <= 1):
            raise ValidationError(message="记忆率 r 必须在 (0, 1] 范围内", details={"r": req.r})
        if req.a <= 0:
            raise ValidationError(message="客单价 a 必须大于 0", details={"a": req.a})
        if req.f < 1:
            raise ValidationError(message="复购系数 f 必须 ≥ 1", details={"f": req.f})
        
        logger.debug(f"参数验证通过 [{request_id}]")
        
        # 参数自动调整
        adjusted = False
        adjust_info = {}
        if req.auto_adjust and (req.city or req.product):
            logger.info(f"开始自动调整参数 [{request_id}]: city={req.city}, product={req.product}")
            adjusted_params = adjust_params_by_context(
                city=req.city, 
                product=req.product,
                U=req.U if req.U != 100 else None,  # 如果用户没改默认值，允许自动调整
                a=req.a if req.a != 22 else None,
                r=req.r if req.r != 0.18 else None,
                f=req.f if req.f != 1.4 else None,
            )
            # 更新 req 的参数
            req.U = adjusted_params["U"]
            req.beta = adjusted_params["beta"]
            req.r = adjusted_params["r_neutral"]
            req.a = adjusted_params["a_neutral"]
            req.f = adjusted_params["f_neutral"]
            adjusted = True
            adjust_info = {
                "city_tier": detect_city_tier(req.city) if req.city else None,
                "product_type": detect_product_type(req.product) if req.product else None,
                "adjusted_params": {
                    "U": adjusted_params["U"],
                    "beta": adjusted_params["beta"],
                    "r": adjusted_params["r_neutral"],
                    "a": adjusted_params["a_neutral"],
                    "f": adjusted_params["f_neutral"],
                }
            }
            logger.info(f"参数自动调整完成 [{request_id}]: U={req.U}, beta={req.beta}, r={req.r}, a={req.a}, f={req.f}")
        
        # 如果指定了预设场景，覆盖对应参数
        if req.scenario:
            logger.info(f"使用预设场景 [{request_id}]: {req.scenario}")
            scen_params = {
                "pessimistic": {"r": req.r * 0.85, "a": req.a * 0.9, "f": req.f * 0.95},
                "neutral": {"r": req.r, "a": req.a, "f": req.f},
                "optimistic": {"r": req.r * 1.2, "a": req.a * 1.15, "f": req.f * 1.05},
            }
            if req.scenario in scen_params:
                sp = scen_params[req.scenario]
                req.r = sp["r"]
                req.a = sp["a"]
                req.f = sp["f"]
                logger.info(f"场景参数覆盖 [{request_id}]: r={req.r}, a={req.a}, f={req.f}")
            else:
                raise HTTPException(status_code=400, detail=f"未知场景: {req.scenario}")
        
        # 执行计算
        logger.info(f"开始计算 ROI [{request_id}]...")
        result = calc_roi_full(
            N=req.N, U=req.U, P=req.P, beta=req.beta,
            gamma=req.gamma, T=req.T,
            r=req.r, a=req.a, f=req.f,
            c=req.c, cost=req.cost, weeks=req.weeks,
        )
        logger.info(f"ROI 计算完成 [{request_id}]: ROI={result['result']['roi_percent']:.2f}%")
        
        # 构建公式描述
        formula_desc = (
            f"UV = N×U×P×β = {req.N}×{req.U}×{req.P}×{req.beta} = {result['intermediates']['uv']}\n"
            f"PV = UV×γ×T = {result['intermediates']['uv']}×{req.gamma}×{req.T} = {result['intermediates']['pv']}\n"
            f"记忆人数 = UV×r = {result['intermediates']['uv']}×{req.r} = {result['intermediates']['recall']}\n"
            f"转化人数 = 记忆×c = {result['intermediates']['recall']}×{req.c} = {result['intermediates']['conversions']}\n"
            f"首期销售 = 转化×a = {result['intermediates']['conversions']}×{req.a} = {result['intermediates']['first_sale']:.2f}\n"
            f"LTV = 首期×f = {result['intermediates']['first_sale']:.2f}×{req.f} = {result['result']['ltv']:.2f}\n"
            f"ROI = (LTV-成本)/成本×100% = ({result['result']['ltv']:.2f}-{req.cost})/{req.cost}×100% = {result['result']['roi_percent']:.2f}%"
        )
        
        response = {
            "request_id": request_id,
            "scenario": req.scenario,
            "uv": result["intermediates"]["uv"],
            "pv": result["intermediates"]["pv"],
            "recall": result["intermediates"]["recall"],
            "conversions": result["intermediates"]["conversions"],
            "first_sale": result["intermediates"]["first_sale"],
            "ltv": result["result"]["ltv"],
            "roi_percent": result["result"]["roi_percent"],
            "net_profit": result["result"]["net_profit"],
            "params": result["params"],
            "formula": formula_desc,
        }
        
        # 增加参数调整说明
        if adjusted:
            response["auto_adjusted"] = True
            response["adjust_info"] = adjust_info
        
        logger.info(f"ROI 计算请求处理完成 [{request_id}]")
        return response
        
    except ValidationError as e:
        logger.warning(f"参数验证失败 [{request_id}]: {e.message}, details={e.details}")
        return JSONResponse(status_code=400, content=format_error_response(e, request_id=request_id))
    except Exception as e:
        logger.error(f"ROI 计算失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))

@router.get("/three-scenarios")
async def get_three_scenarios(
    N: int = 5000,
    cost: float = 100000,
    T: int = 14,
    city: Optional[str] = None,
    product: Optional[str] = None,
    auto_adjust: bool = True,
):
    """
    快速获取三场景 ROI（悲观/中性/乐观）
    
    查询参数：
    - N: 广告框数（默认 5000）
    - cost: 投入成本（默认 100000）
    - T: 投放天数（默认 14）
    - city: 投放城市（用于自动调整参数）
    - product: 产品类型（用于自动调整参数）
    - auto_adjust: 是否自动调整参数（默认 True）
    """
    request_id = generate_request_id("three_scenarios")
    logger.info(f"收到三场景 ROI 请求 [{request_id}]: N={N}, cost={cost}, T={T}, city={city}, product={product}")
    
    try:
        # 参数验证
        if N <= 0:
            raise ValidationError(message="广告框数 N 必须大于 0", details={"N": N})
        if cost <= 0:
            raise ValidationError(message="投入成本 cost 必须大于 0", details={"cost": cost})
        if T <= 0:
            raise ValidationError(message="投放天数 T 必须大于 0", details={"T": T})
        
        logger.debug(f"参数验证通过 [{request_id}]")
        
        # 参数自动调整
        if auto_adjust and (city or product):
            logger.info(f"开始自动调整参数 [{request_id}]: city={city}, product={product}")
            adjusted_params = adjust_params_by_context(city=city, product=product)
            U = adjusted_params["U"]
            beta = adjusted_params["beta"]
            r_neutral = adjusted_params["r_neutral"]
            a_neutral = adjusted_params["a_neutral"]
            f_neutral = adjusted_params["f_neutral"]
            results = calc_three_scenarios(
                N=N, U=U, P=2.51, beta=beta,
                gamma=2.0, T=T,
                cost=cost,
                r_neutral=r_neutral, a_neutral=a_neutral, f_neutral=f_neutral
            )
            response = {
                "request_id": request_id,
                "scenarios": results,
                "auto_adjusted": True,
                "city_tier": detect_city_tier(city) if city else None,
                "product_type": detect_product_type(product) if product else None,
            }
            logger.info(f"三场景 ROI 请求处理完成（含参数调整） [{request_id}]")
            return response
        
        results = calc_three_scenarios(N=N, cost=cost, T=T)
        response = {
            "request_id": request_id,
            "scenarios": results,
        }
        logger.info(f"三场景 ROI 请求处理完成 [{request_id}]")
        return response
        
    except ValidationError as e:
        logger.warning(f"参数验证失败 [{request_id}]: {e.message}, details={e.details}")
        return JSONResponse(status_code=400, content=format_error_response(e, request_id=request_id))
    except Exception as e:
        logger.error(f"三场景 ROI 计算失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))

@router.post("/sensitivity", response_model=SensitivityResponse)
@monitor_performance_async(logger=logger)
async def sensitivity_analysis(req: SensitivityRequest):
    """
    灵敏度分析：单参数变动对 ROI 的影响
    
    用于分析哪个参数对 ROI 影响最大（敏感性分析）
    """
    request_id = generate_request_id("sensitivity")
    logger.info(f"收到灵敏度分析请求 [{request_id}]: variable={req.variable}, values={req.values}")
    
    try:
        # 参数验证
        if not req.variable:
            raise ValidationError(message="variable 参数不能为空", details={"variable": req.variable})
        if not req.values or len(req.values) == 0:
            raise ValidationError(message="values 参数必须非空", details={"values": req.values})
        
        logger.debug(f"参数验证通过 [{request_id}]")
        
        base = req.base_params
        roi_values = []
        ltv_values = []

        for val in req.values:
            # 复制基础参数，修改目标变量
            params = base.model_dump()
            params[req.variable] = val

            result = calc_roi_full(**params)
            roi_values.append(result["result"]["roi_percent"])
            ltv_values.append(result["result"]["ltv"])

        logger.info(f"灵敏度分析请求处理完成 [{request_id}]")
        return SensitivityResponse(
            variable=req.variable,
            values=req.values,
            roi_values=roi_values,
            ltv_values=ltv_values,
        )
        
    except ValidationError as e:
        logger.warning(f"参数验证失败 [{request_id}]: {e.message}, details={e.details}")
        return JSONResponse(status_code=400, content=format_error_response(e, request_id=request_id))
    except Exception as e:
        logger.error(f"灵敏度分析失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))

@router.post("/compare", response_model=CompareResponse)
@monitor_performance_async(logger=logger)
async def compare_scenarios(req: CompareRequest):
    """
    多方案对比
    
    传入多个场景参数，返回对比表格
    """
    request_id = generate_request_id("compare")
    logger.info(f"收到多方案对比请求 [{request_id}]: scenarios_count={len(req.scenarios)}")
    
    try:
        # 参数验证
        if not req.scenarios or len(req.scenarios) == 0:
            raise ValidationError(message="scenarios 参数必须非空", details={"scenarios": req.scenarios})
        
        logger.debug(f"参数验证通过 [{request_id}]")
        
        results = []
        for i, scen in enumerate(req.scenarios):
            result = calc_roi_full(**scen.model_dump(exclude={"scenario"}))
            results.append({
                "index": i,
                "scenario": scen.scenario,
                "roi_percent": result["result"]["roi_percent"],
                "ltv": result["result"]["ltv"],
                "uv": result["intermediates"]["uv"],
                "conversions": result["intermediates"]["conversions"],
            })

        # 生成对比总结
        best = max(results, key=lambda x: x["roi_percent"])
        worst = min(results, key=lambda x: x["roi_percent"])
        best_label = best['scenario'] if best['scenario'] else f"方案{best['index']}"
        worst_label = worst['scenario'] if worst['scenario'] else f"方案{worst['index']}"
        summary = f"最佳方案 ROI {best['roi_percent']:.2f}%（{best_label}），最低方案 ROI {worst['roi_percent']:.2f}%（{worst_label}）。"

        logger.info(f"多方案对比请求处理完成 [{request_id}]")
        return CompareResponse(scenarios=results, summary=summary)
        
    except ValidationError as e:
        logger.warning(f"参数验证失败 [{request_id}]: {e.message}, details={e.details}")
        return JSONResponse(status_code=400, content=format_error_response(e, request_id=request_id))
    except Exception as e:
        logger.error(f"多方案对比失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))

@router.get("/formula")
async def get_formula():
    """
    获取 ROI 计算公式说明（含参数定义与数据来源）
    """
    request_id = generate_request_id("formula")
    logger.info(f"收到公式说明请求 [{request_id}]")
    
    try:
        response = {
            "request_id": request_id,
            "formulas": [
                {
                    "name": "UV（独立触达人数）",
                    "formula": "UV = N × U × P × β",
                    "params": {
                        "N": "广告框数（个）[本方案设定]",
                        "U": "每栋楼户数（户/栋）[MCP 数据库 711 广州楼盘中位数]",
                        "P": "每户人数（人/户）[国家统计局《中国统计年鉴2024》]",
                        "β": "接触率（%）[皓邻 5 年实测]",
                    },
                    "example": "UV = 5000 × 100 × 2.51 × 0.85 = 1,067,000 人",
                },
                {
                    "name": "PV（总曝光次数）",
                    "formula": "PV = UV × γ × T",
                    "params": {
                        "γ": "每日接触频次（次/户/日）[单面 2.0 / 双面 3.8]",
                        "T": "投放天数（天）",
                    },
                    "example": "PV = 1,067,000 × 2.0 × 14 = 20,900,000 次",
                },
                {
                    "name": "记忆人数",
                    "formula": "记忆人数 = UV × r",
                    "params": {
                        "r": "记忆率（0-1）[悲观 0.15 / 中性 0.18 / 乐观 0.22]",
                    },
                    "example": "记忆人数 = 1,067,000 × 0.18 = 192,060 人",
                },
                {
                    "name": "转化人数",
                    "formula": "转化人数 = 记忆人数 × c",
                    "params": {
                        "c": "转化率（0-1）[默认 0.02 = 2%]",
                    },
                    "example": "转化人数 = 192,060 × 0.02 = 3,841 人",
                },
                {
                    "name": "首期销售",
                    "formula": "首期销售 = 转化人数 × a",
                    "params": {
                        "a": "客单价（元）[悲观 ¥20 / 中性 ¥22 / 乐观 ¥25]",
                    },
                    "example": "首期销售 = 3,841 × 22 = ¥845,020",
                },
                {
                    "name": "LTV（生命周期价值）",
                    "formula": "LTV = 首期销售 × (1 + f)",
                    "params": {
                        "f": "复购系数 [悲观 1.3 / 中性 1.4 / 乐观 1.5]",
                    },
                    "example": "LTV = 845,020 × 1.4 = ¥1,183,028",
                },
                {
                    "name": "ROI（投资回报率）",
                    "formula": "ROI = (LTV - 成本) / 成本 × 100%",
                    "params": {
                        "成本": "投入成本（元）",
                    },
                    "example": "ROI = (1,183,028 - 100,000) / 100,000 × 100% = 1,083.0%",
                },
            ],
            "sources": [
                "[MCP 数据库] 711 广州楼盘中位数",
                "[国家统计局] 《中国统计年鉴2024》",
                "[皓邻实测] 5 年接触率数据",
                "[CTR 报告] 户外广告记忆率行业区间",
                "[凯度 Kantar 2024] 家庭场景口碑传播",
            ],
            "three_scenarios": {
                "pessimistic": {"r": 0.15, "a": 20, "f": 1.3, "desc": "单元门单面+2周短投"},
                "neutral": {"r": 0.18, "a": 22, "f": 1.4, "desc": "行业基线中位"},
                "optimistic": {"r": 0.22, "a": 25, "f": 1.5, "desc": "双面+智能屏 4周"},
            },
        }
        
        logger.info(f"公式说明请求处理完成 [{request_id}]")
        return response
        
    except Exception as e:
        logger.error(f"公式说明请求失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))

@router.get("/benchmark")
async def get_benchmark():
    """
    获取行业 ROI 基准对比（横评）
    """
    request_id = generate_request_id("benchmark")
    logger.info(f"收到行业基准对比请求 [{request_id}]")
    
    try:
        response = {
            "request_id": request_id,
            "benchmark": [
                {"media": "社区单元门（本方案·中性）", "first_roi": "181.6%", "ltv_roi_60d": "1,367%", "source": "本方案测算"},
                {"media": "梯媒（分众）", "first_roi": "180-250%", "ltv_roi_60d": "400-600%", "source": "行业经验"},
                {"media": "地铁广告", "first_roi": "100-180%", "ltv_roi_60d": "200-400%", "source": "行业经验"},
                {"media": "楼宇 LCD", "first_roi": "60-100%", "ltv_roi_60d": "120-200%", "source": "行业经验"},
                {"media": "电视硬广", "first_roi": "40-80%", "ltv_roi_60d": "100-180%", "source": "行业经验"},
                {"media": "线上效果广告（巨量）", "first_roi": "300-500%", "ltv_roi_60d": "800-1,200%", "source": "行业经验"},
            ],
            "insights": [
                "社区单元门 LTV ROI 1,367% 与线上效果广告（巨量）800-1,200% 同属第一梯队",
                "远高于电视/地铁/楼宇 LCD（100-600% 区间）",
                "关键差异：社区是「高频强制触达 + 家庭决策」，转化效率天然高",
                "CPM 仅 3-8 元，是线上广告的 1/10 到 1/30",
            ]
        }
        
        logger.info(f"行业基准对比请求处理完成 [{request_id}]")
        return response
        
    except Exception as e:
        logger.error(f"行业基准对比请求失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))

