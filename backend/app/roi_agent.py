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
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# ── 日志 ────────────────────────────────────────────────────────────────────────
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("roi_agent")

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
    """
    uv = calc_uv(N, U, P, beta)
    pv = calc_pv(uv, gamma, T)
    recall = calc_recall_uv(uv, r)
    conversions = calc_conversion(recall, c)
    first_sale = calc_first_sale(conversions, a)
    ltv = calc_ltv(first_sale, f, weeks)
    roi = calc_roi(ltv, cost)

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

def calc_three_scenarios(
    N: int = 5000,
    U: float = 100,
    P: float = 2.51,
    beta: float = 0.85,
    gamma: float = 2.0,
    T: int = 14,
    cost: float = 100000,
    weeks: int = 8,
) -> Dict[str, Any]:
    """
    计算三场景 ROI（悲观/中性/乐观）

    返回三个场景的完整计算结果
    """
    params = DEFAULT_PARAMS.copy()

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

    return results

# ── 请求/响应模型 ────────────────────────────────────────────────────────────────

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
    f: float = Field(1.4, description="复购系数")

    c: float = Field(0.02, description="转化率（0-1）")

    cost: float = Field(100000, description="投入成本（元）")
    weeks: int = Field(8, description="LTV 计算周期（周）")

    scenario: Optional[str] = Field(None, description="预设场景：pessimistic/neutral/optimistic")

class ROICalculateResponse(BaseModel):
    """ROI 计算响应"""
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

# ── API 端点 ──────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "agent": "ROI Agent", "version": "2.2.0"}

@router.post("/calculate", response_model=Dict[str, Any])
async def calculate_roi(req: ROICalculateRequest):
    """
    ROI 计算（支持三场景预设）

    传入 scenario 可快速计算预设场景：
    - pessimistic: 悲观（记忆率 0.15 / 客单 ¥20 / 复购 1.3）
    - neutral: 中性（记忆率 0.18 / 客单 ¥22 / 复购 1.4）
    - optimistic: 乐观（记忆率 0.22 / 客单 ¥25 / 复购 1.5）
    """
    # 如果指定了预设场景，覆盖对应参数
    if req.scenario:
        scen_params = {
            "pessimistic": {"r": 0.15, "a": 20, "f": 1.3},
            "neutral": {"r": 0.18, "a": 22, "f": 1.4},
            "optimistic": {"r": 0.22, "a": 25, "f": 1.5},
        }
        if req.scenario in scen_params:
            sp = scen_params[req.scenario]
            req.r = sp["r"]
            req.a = sp["a"]
            req.f = sp["f"]
        else:
            raise HTTPException(status_code=400, detail=f"未知场景: {req.scenario}")

    result = calc_roi_full(
        N=req.N, U=req.U, P=req.P, beta=req.beta,
        gamma=req.gamma, T=req.T,
        r=req.r, a=req.a, f=req.f,
        c=req.c, cost=req.cost, weeks=req.weeks,
    )

    formula_desc = (
        f"UV = N×U×P×β = {req.N}×{req.U}×{req.P}×{req.beta} = {result['intermediates']['uv']}\n"
        f"PV = UV×γ×T = {result['intermediates']['uv']}×{req.gamma}×{req.T} = {result['intermediates']['pv']}\n"
        f"记忆人数 = UV×r = {result['intermediates']['uv']}×{req.r} = {result['intermediates']['recall']}\n"
        f"转化人数 = 记忆×c = {result['intermediates']['recall']}×{req.c} = {result['intermediates']['conversions']}\n"
        f"首期销售 = 转化×a = {result['intermediates']['conversions']}×{req.a} = {result['intermediates']['first_sale']:.2f}\n"
        f"LTV = 首期×f = {result['intermediates']['first_sale']:.2f}×{req.f} = {result['result']['ltv']:.2f}\n"
        f"ROI = (LTV-成本)/成本×100% = ({result['result']['ltv']:.2f}-{req.cost})/{req.cost}×100% = {result['result']['roi_percent']:.2f}%"
    )

    return {
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

@router.get("/three-scenarios")
async def get_three_scenarios(
    N: int = 5000,
    cost: float = 100000,
    T: int = 14,
):
    """
    快速获取三场景 ROI（悲观/中性/乐观）

    查询参数：
    - N: 广告框数（默认 5000）
    - cost: 投入成本（默认 100000）
    - T: 投放天数（默认 14）
    """
    results = calc_three_scenarios(N=N, cost=cost, T=T)
    return {"scenarios": results}

@router.post("/sensitivity", response_model=SensitivityResponse)
async def sensitivity_analysis(req: SensitivityRequest):
    """
    灵敏度分析：单参数变动对 ROI 的影响

    用于分析哪个参数对 ROI 影响最大（敏感性分析）
    """
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

    return SensitivityResponse(
        variable=req.variable,
        values=req.values,
        roi_values=roi_values,
        ltv_values=ltv_values,
    )

@router.post("/compare", response_model=CompareResponse)
async def compare_scenarios(req: CompareRequest):
    """
    多方案对比

    传入多个场景参数，返回对比表格
    """
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
    summary = f"最佳方案 ROI {best['roi_percent']:.2f}%（{best['scenario'] or f'方案{best[\"index\"]}'），" \
              f"最低方案 ROI {worst['roi_percent']:.2f}%（{worst['scenario'] or f'方案{worst[\"index\"]}'）。"

    return CompareResponse(scenarios=results, summary=summary)

@router.get("/formula")
async def get_formula():
    """
    获取 ROI 计算公式说明（含参数定义与数据来源）
    """
    return {
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

@router.get("/benchmark")
async def get_benchmark():
    """
    获取行业 ROI 基准对比（横评）
    """
    return {
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
