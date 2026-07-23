"""
智能屏资源子系统（Smart Screen L9）— 39 个启发式指标公式。

重要约定：
- 每个公式函数首行注释 `# 示意算法，待替换为真实模型`
- 当前为占位启发式（0–100 相对分值或合理量纲），真实模型由算法层 19 算法替换
- 所有函数输入为「小区级宽表一行（dict）」，输出为 float
- INDICATOR_FUNCS 为 字段名 -> 函数 的注册表，供 indicators.generate_indicators 调用

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

import hashlib
from typing import Callable, Dict

from app.smart_screen.schema_constants import INDICATOR_COLUMNS


# ── ROI 模型行业假设常量（社区梯媒）──────────────────────────────────────────────
# 说明：P0 阶段 CVR / AOV 采用社区梯媒统一常量，不按社区差异化（差异化留待 P1）。
# 取值来自社区梯媒行业经验区间中值，作为可解释 ROI 模型的固定假设。
CVR = 0.008   # 转化率：社区梯媒到店/扫码率 0.5%–2% 取中值，来源：社区梯媒行业经验区间
AOV = 80.0    # 客单价(元)：社区周边客单价 50–120 元取中值，来源：社区周边消费行业经验区间


def _num(value, default: float = 0.0) -> float:
    """安全取数值：None / 空 返回默认值。"""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _seeded(row: dict, salt: int) -> float:
    """
    基于 community_id + 盐值生成 [0.4, 1.2] 之间的确定性抖动因子。
    用于行业适配类（G）指标在占位阶段的合理差异化（待真实模型替换）。
    """
    cid = str(row.get("community_id") or "")
    h = int(hashlib.md5((cid + ":" + str(salt)).encode("utf-8")).hexdigest(), 16)
    return 0.4 + (h % 1000) / 1000 * 0.8


# ═══════════════════════════════════════════════════════════════════════════════
# A. 人口覆盖（5）
# ═══════════════════════════════════════════════════════════════════════════════

def daily_reach(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return _num(row.get("household_count")) * _num(row.get("occupancy_rate")) * 2.1


def building_depth(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, _num(row.get("building_count")) * 3.5)


def dual_touch(row: dict) -> float:
    # 示意算法，待替换为真实模型
    hh = max(_num(row.get("household_count")), 1.0)
    return min(100.0, (_num(row.get("gate_device_count")) + _num(row.get("access_device_count"))) / hh * 10000.0)


def coverage_rate(row: dict) -> float:
    # 示意算法，待替换为真实模型
    b = max(_num(row.get("building_count")), 0.0)
    return min(100.0, _num(row.get("occupancy_rate")) * 100.0 * (1.0 - 1.0 / (1.0 + b)))


def population_index(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, daily_reach(row) / 50.0)


# ═══════════════════════════════════════════════════════════════════════════════
# B. 质量评分（5）
# ═══════════════════════════════════════════════════════════════════════════════

def health_score(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return max(0.0, 100.0 - _num(row.get("monthly_failure_rate")) * 1000.0)


def timeliness_rate(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 95.0 + _num(row.get("historical_launch_count")) * 0.5)


def activity_score(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, _num(row.get("historical_launch_count")) * 10.0 + _num(row.get("access_device_count")) * 2.0)


def stability_score(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return max(0.0, 100.0 - _num(row.get("monthly_failure_rate")) * 500.0)


def quality_index(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return (health_score(row) + timeliness_rate(row) + activity_score(row) + stability_score(row)) / 4.0


# ═══════════════════════════════════════════════════════════════════════════════
# C. 效果预测（4）
# ═══════════════════════════════════════════════════════════════════════════════

def industry_heat(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, _num(row.get("covered_industry_count")) * 20.0 + 40.0)


def recommend_score(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, quality_index(row) * 0.5 + population_index(row) * 0.5)


def peak_season_index(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return 70.0  # 占位，待季节模型


def effect_predict(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, recommend_score(row) * 0.6 + industry_heat(row) * 0.4)


# ═══════════════════════════════════════════════════════════════════════════════
# D. 价值分析（5）
# ═══════════════════════════════════════════════════════════════════════════════

def cpm(row: dict) -> float:
    # 示意算法，待替换为真实模型
    reach = max(daily_reach(row), 1.0)
    return round(_num(row.get("access_lightbox_price")) / reach * 1000.0, 2)


def cost_performance(row: dict) -> float:
    # 示意算法，待替换为真实模型
    price = max(_num(row.get("ad_door_avg_price")), 1.0)
    return round(daily_reach(row) / price * 10.0, 2)


def sssc_coefficient(row: dict) -> float:
    # 示意算法，待替换为真实模型
    gate = max(_num(row.get("gate_device_count")), 1.0)
    return round((_num(row.get("occupancy_rate")) * _num(row.get("building_count"))) / gate, 2)


def roi_estimate(row: dict) -> float:
    """真实 ROI 预估（可解释模型）。

    成本 = CPM × 日触达 / 1000（等价于单屏日投放成本 access_lightbox_price）
    收益 = 日触达 × CVR × AOV
    真实 ROI = (收益 − 成本) / 成本
    返回 0–100 的 ROI 指数：盈亏平衡→50，ROI≥100%→100，ROI≤−100%→0
    """
    reach = max(daily_reach(row), 1.0)
    cost = max(cpm(row) * reach / 1000.0, 1e-6)   # = access_lightbox_price
    revenue = reach * CVR * AOV
    roi = (revenue - cost) / cost
    return round(min(100.0, max(0.0, roi * 50.0 + 50.0)), 2)


def value_index(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return round((cost_performance(row) + roi_estimate(row) + effect_predict(row)) / 3.0, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# E. 画像标签（5）
# ═══════════════════════════════════════════════════════════════════════════════

def grade_tag(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, _num(row.get("household_count")) / 300.0 * 50.0 + _num(row.get("ad_door_avg_price")) / 20.0)


def consumption_power(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, _num(row.get("ad_door_avg_price")) / 20.0 + _num(row.get("access_lightbox_price")) / 30.0)


def commute_tag(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, _num(row.get("building_count")) * 2.0)


def family_tag(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, _num(row.get("household_count")) / 200.0)


def function_tag(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, _num(row.get("access_device_count")) * 3.0)


# ═══════════════════════════════════════════════════════════════════════════════
# F. 空间价值（4）—— 因 L9 缺 GPS，空间类指标以占位公式生成，待补坐标后接真实算法
# ═══════════════════════════════════════════════════════════════════════════════

def integration(row: dict) -> float:
    # 示意算法，待替换为真实模型（GPS 缺失，暂以设备密度占位）
    if row.get("gps_lng") is None:
        return 50.0  # 占位，待真实空间算法
    return min(100.0, (_num(row.get("gate_device_count")) + _num(row.get("access_device_count"))) * 5.0)


def choice(row: dict) -> float:
    # 示意算法，待替换为真实模型（选择度，占位 50）
    return 50.0


def depth(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, _num(row.get("building_count")) * 4.0)


def sci(row: dict) -> float:
    # 示意算法，待替换为真实模型（空间整合度指数，占位 50）
    return 50.0


# ═══════════════════════════════════════════════════════════════════════════════
# G. 行业适配（11）—— 由宽表字段 + 确定性抖动生成相对适配分（占位）
# ═══════════════════════════════════════════════════════════════════════════════

def fit_takeout(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 60.0 * _seeded(row, 1))


def fit_ecommerce(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 65.0 * _seeded(row, 2))


def fit_fmcg(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 70.0 * _seeded(row, 3))


def fit_beauty(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 55.0 * _seeded(row, 4))


def fit_auto(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 45.0 * _seeded(row, 5))


def fit_education(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 60.0 * _seeded(row, 6))


def fit_realestate(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 50.0 * _seeded(row, 7))


def fit_finance(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 55.0 * _seeded(row, 8))


def fit_health(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 65.0 * _seeded(row, 9))


def fit_travel(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 50.0 * _seeded(row, 10))


def fit_local(row: dict) -> float:
    # 示意算法，待替换为真实模型
    return min(100.0, 75.0 * _seeded(row, 11))


# ═══════════════════════════════════════════════════════════════════════════════
# 指标函数注册表（字段名 -> 函数），顺序与 INDICATOR_COLUMNS 一致
# ═══════════════════════════════════════════════════════════════════════════════

INDICATOR_FUNCS: Dict[str, Callable[[dict], float]] = {
    "daily_reach": daily_reach,
    "building_depth": building_depth,
    "dual_touch": dual_touch,
    "coverage_rate": coverage_rate,
    "population_index": population_index,
    "health_score": health_score,
    "timeliness_rate": timeliness_rate,
    "activity_score": activity_score,
    "stability_score": stability_score,
    "quality_index": quality_index,
    "industry_heat": industry_heat,
    "recommend_score": recommend_score,
    "peak_season_index": peak_season_index,
    "effect_predict": effect_predict,
    "cpm": cpm,
    "cost_performance": cost_performance,
    "sssc_coefficient": sssc_coefficient,
    "roi_estimate": roi_estimate,
    "value_index": value_index,
    "grade_tag": grade_tag,
    "consumption_power": consumption_power,
    "commute_tag": commute_tag,
    "family_tag": family_tag,
    "function_tag": function_tag,
    "integration": integration,
    "choice": choice,
    "depth": depth,
    "sci": sci,
    "fit_takeout": fit_takeout,
    "fit_ecommerce": fit_ecommerce,
    "fit_fmcg": fit_fmcg,
    "fit_beauty": fit_beauty,
    "fit_auto": fit_auto,
    "fit_education": fit_education,
    "fit_realestate": fit_realestate,
    "fit_finance": fit_finance,
    "fit_health": fit_health,
    "fit_travel": fit_travel,
    "fit_local": fit_local,
}

# 自检：注册表必须恰好覆盖 39 个指标
assert set(INDICATOR_FUNCS.keys()) == set(INDICATOR_COLUMNS), "指标函数注册表与指标列定义不一致"
