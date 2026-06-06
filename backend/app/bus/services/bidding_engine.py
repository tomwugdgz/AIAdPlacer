"""
bus-pDOOH 子系统 — 公交线路广告竞价引擎

核心竞价逻辑：
- 基础价格 = 月单价 / 30 × 投放天数 × 等级系数 × 时段溢价
- 展示量 = 行业标准曝光计算（T/CCSA 738-2025）
  · 流动曝光（公式1）+ 驻留曝光（公式3）= 总曝光（公式5）
  · 曝光乘数（公式6）+ 接触频次

兼容旧版简单公式：impressions = vehicles × daily_traffic × hotspot_traffic × days
"""
from decimal import Decimal
from typing import Dict, Any, List, Optional
from app.bus.models import RouteLevel
from app.bus.services.standard_impression import calc_standard_impression


# ── 竞价参数常量 ───────────────────────────────────────────

LEVEL_MULTIPLIERS: Dict[str, float] = {
    "S": 1.5,
    "A++": 1.3,
    "A+": 1.1,
    "A": 1.0,
}

TIME_PREMIUMS: Dict[str, float] = {
    "morning_rush": 1.3,
    "evening_rush": 1.2,
    "normal": 1.0,
}


def calculate_bidding(
    monthly_price: Decimal,
    level: str,
    days: int,
    vehicles: int,
    daily_traffic: int,
    hotspot_traffic: float,
    time_period: str = "normal",
) -> Dict[str, Any]:
    """
    单条线路竞价计算。

    Parameters
    ----------
    monthly_price : Decimal
        月单价（元）
    level : str
        线路等级 S / A++ / A+ / A
    days : int
        投放天数
    vehicles : int
        车辆数
    daily_traffic : int
        日均客流
    hotspot_traffic : float
        热点系数（1.0-3.0）
    time_period : str
        时段类型：morning_rush / evening_rush / normal

    Returns
    -------
    dict
        包含 base_price、impressions、coverage_30d、
        cost_per_impression、cost_per_reach 的竞价结果
    """
    level_key = level.replace("+", "+")
    level_mult = LEVEL_MULTIPLIERS.get(level, 1.0)
    time_premium = TIME_PREMIUMS.get(time_period, 1.0)

    # 基础价格 = 月单价 / 30 × 投放天数 × 等级系数 × 时段溢价
    base_price = (monthly_price / Decimal("30")) * Decimal(str(days)) * Decimal(str(level_mult)) * Decimal(str(time_premium))

    # 展示量 = 车辆数 × 日均客流 × 热点系数 × 投放天数
    impressions = int(vehicles * daily_traffic * hotspot_traffic * days)

    # 覆盖人群（30天）= 车辆数 × 日均客流 × 热点系数 × 30
    coverage_30d = int(vehicles * daily_traffic * hotspot_traffic * 30)

    # ── 行业标准曝光测量 (T/CCSA 738-2025) ──
    # 使用标准引擎计算流动/驻留曝光、曝光乘数、接触频次
    standard_result = calc_standard_impression(
        vehicles=vehicles,
        daily_traffic=daily_traffic,
        hotspot_traffic=hotspot_traffic,
        days=days,
        exposure_duration=15.0,  # 默认 15 秒曝光时长
        ad_duration=15.0,        # 默认 15 秒广告时长
        sot=0.25,                # 默认时间占比 25%（4 个广告轮播）
        ad_slots=4,              # 默认 4 个广告轮播
    )

    # 单次展示成本
    cost_per_impression = round(Decimal(str(base_price)) / Decimal(str(impressions)), 4) if impressions > 0 else Decimal("0")

    # 单次覆盖成本
    cost_per_reach = round(Decimal(str(base_price)) / Decimal(str(coverage_30d)), 4) if coverage_30d > 0 else Decimal("0")

    return {
        "base_price": float(base_price.quantize(Decimal("0.01"))),
        "impressions": impressions,
        "coverage_30d": coverage_30d,
        "cost_per_impression": float(cost_per_impression),
        "cost_per_reach": float(cost_per_reach),
        "level_multiplier": level_mult,
        "time_premium": time_premium,

        # ── 行业标准指标 ──
        "standard_impression": {
            "flow_impressions": standard_result.flow_impressions,
            "dwell_impressions": standard_result.dwell_impressions,
            "total_impressions": standard_result.total_impressions,
            "effective_impressions": standard_result.effective_impressions,
            "flow_otc": standard_result.flow_otc,
            "dwell_otc": standard_result.dwell_otc,
            "impression_multiplier": standard_result.impression_multiplier,
            "frequency": standard_result.frequency,
            "independent_audience": standard_result.independent_audience,
            "reach": standard_result.reach,
        },

        "details": {
            "monthly_price": float(monthly_price),
            "level": level,
            "days": days,
            "vehicles": vehicles,
            "daily_traffic": daily_traffic,
            "hotspot_traffic": hotspot_traffic,
            "time_period": time_period,
        },
    }


def calculate_multi_bidding(
    routes: List[Dict[str, Any]],
    days: int,
    vehicle_per_route: Optional[int] = None,
    time_period: str = "normal",
) -> Dict[str, Any]:
    """
    多线路竞价计算（批量）。

    Parameters
    ----------
    routes : list[dict]
        每条线路包含 monthly_price, level, vehicle_count,
        daily_traffic, hotspot_traffic
    days : int
        投放天数
    vehicle_per_route : int | None
        统一车辆数（覆盖每条线路的 vehicle_count）
    time_period : str
        时段类型

    Returns
    -------
    dict
        包含 each_result（逐条结果）与 summary（汇总）
    """
    results: List[Dict[str, Any]] = []
    total_budget = Decimal("0")
    total_impressions = 0
    total_coverage = 0

    for route in routes:
        v_count = vehicle_per_route if vehicle_per_route else route.get("vehicle_count", 1)
        res = calculate_bidding(
            monthly_price=Decimal(str(route["monthly_price"])),
            level=route["level"],
            days=days,
            vehicles=v_count,
            daily_traffic=route["daily_traffic"],
            hotspot_traffic=route["hotspot_traffic"],
            time_period=time_period,
        )
        res["route_code"] = route.get("route_code", "")
        res["route_name"] = route.get("route_name", "")
        results.append(res)
        total_budget += Decimal(str(res["base_price"]))
        total_impressions += res["impressions"]
        total_coverage += res["coverage_30d"]

    # 汇总 CPM/CPR
    summary_cpm = round(total_budget / Decimal(str(total_impressions)), 4) if total_impressions > 0 else Decimal("0")
    summary_cpr = round(total_budget / Decimal(str(total_coverage)), 4) if total_coverage > 0 else Decimal("0")

    return {
        "each_result": results,
        "summary": {
            "total_budget": float(total_budget.quantize(Decimal("0.01"))),
            "total_impressions": total_impressions,
            "total_coverage_30d": total_coverage,
            "cpm": float(summary_cpm),
            "cpr": float(summary_cpr),
            "route_count": len(results),
        },
    }
