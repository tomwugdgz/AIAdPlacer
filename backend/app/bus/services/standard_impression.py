"""
标准曝光计算引擎 — 基于 T/CCSA 738-2025 / T/CAAAD 040-2025

《程序化户外广告投放曝光测量技术要求》

公式清单：
- 公式(1): flow_IMP = flow_OTC × SOT × Traffic        流动曝光量
- 公式(2): flow_OTC = (max(T_exp, T_ad) - T_ad) / max(T_exp, 2)  流动曝光概率
- 公式(3): dwell_IMP = dwell_OTC × Traffic             驻留曝光量
- 公式(4): dwell_OTC = T_exp / 300                      驻留曝光概率 (5min=300s)
- 公式(5): IMP = flow_IMP + dwell_IMP                   总曝光量
- 公式(6): ImpressionMultiplier = (flow_Traffic × IMP) / ad_slots  曝光乘数

作者: AIAdPlacer Team
日期: 2026-06-06
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


# ── 常量 ─────────────────────────────────────────────────

DWELL_THRESHOLD_SECONDS = 300  # 驻留判定阈值：5 分钟 = 300 秒（标准商业实践）
MINIMUM_EXPOSURE_SECONDS = 1.0  # 广告观看不足 1 秒不计为有效曝光（标准 7.3）


# ── 数据类 ────────────────────────────────────────────────

@dataclass
class ExposureParams:
    """曝光计算参数"""
    traffic: int                    # 人群流量 Traffic
    exposure_duration: float        # 曝光时长 T_exposure（秒）
    ad_duration: float              # 广告时长 T_ad（秒）
    sot: float                      # 时间占比 Share of Time (0-1)
    ad_slots_per_cycle: int         # 轮播周期内广告数量
    dwell_traffic: int | None = None  # 驻留人群流量（可选，默认 = traffic）


@dataclass
class ExposureResult:
    """曝光计算结果"""
    # 核心指标
    flow_otc: float                 # 流动曝光概率
    dwell_otc: float                # 驻留曝光概率
    flow_impressions: int           # 流动曝光量
    dwell_impressions: int          # 驻留曝光量
    total_impressions: int          # 总曝光量 (flow + dwell)
    effective_impressions: int      # 有效曝光量（≥1s 观看）
    impression_multiplier: float    # 曝光乘数

    # 派生指标
    frequency: float = 0.0          # 接触频次
    independent_audience: int = 0   # 独立受众数量
    reach: int = 0                  # 触达人数（去重）

    # 原始参数
    traffic: int = 0
    ad_slots: int = 0


# ── 核心计算类 ────────────────────────────────────────────

class StandardImpressionEngine:
    """
    基于 T/CCSA 738-2025 标准的曝光量计算引擎。

    实现标准第 7 节「曝光量计算方法要求」的全部公式。
    """

    @staticmethod
    def calc_flow_otc(exposure_t: float, ad_t: float) -> float:
        """
        公式(2): 流动曝光概率

        flow_OTC = (max(T_exposure, T_ad) - T_ad) / max(T_exposure, 2)

        约束：
        - OTC 理论值满足受众观看至少两次广告
        - 广告观看时间不足 1 秒不计为有效曝光

        Args:
            exposure_t: 曝光时长 T_exposure（秒）
            ad_t: 广告时长 T_ad（秒）

        Returns:
            流动曝光概率 (0-1)
        """
        if exposure_t <= 0 or ad_t <= 0:
            return 0.0

        max_t = max(exposure_t, ad_t)
        denominator = max(exposure_t, 2.0)
        otc = (max_t - ad_t) / denominator

        # 约束到 [0, 1]
        return max(0.0, min(1.0, otc))

    @staticmethod
    def calc_flow_imp(flow_otc: float, sot: float, traffic: int) -> float:
        """
        公式(1): 流动曝光量

        flow_IMP = flow_OTC × SOT × Traffic

        Args:
            flow_otc: 流动曝光概率
            sot: 时间占比 (0-1)
            traffic: 人群流量

        Returns:
            流动曝光量（浮点，外部取整）
        """
        if traffic <= 0:
            return 0.0
        return flow_otc * sot * traffic

    @staticmethod
    def calc_dwell_otc(exposure_t: float) -> float:
        """
        公式(4): 驻留曝光概率

        dwell_OTC = T_exposure / 300

        约束：
        - 基于全球户外广告行业商业实践，5 分钟 = 300 秒为通用规则
        - 每额外停留 5 分钟增加一次观看

        Args:
            exposure_t: 曝光时长 T_exposure（秒）

        Returns:
            驻留曝光概率（可 > 1，表示多次观看）
        """
        if exposure_t <= 0:
            return 0.0
        return exposure_t / DWELL_THRESHOLD_SECONDS

    @staticmethod
    def calc_dwell_imp(dwell_otc: float, traffic: int) -> float:
        """
        公式(3): 驻留曝光量

        dwell_IMP = dwell_OTC × Traffic

        Args:
            dwell_otc: 驻留曝光概率
            traffic: 驻留人群流量

        Returns:
            驻留曝光量（浮点，外部取整）
        """
        if traffic <= 0:
            return 0.0
        return dwell_otc * traffic

    @staticmethod
    def calc_total_imp(flow_imp: float, dwell_imp: float) -> int:
        """
        公式(5): 总曝光量

        IMP = IMP_flow + IMP_dwell

        Args:
            flow_imp: 流动曝光量
            dwell_imp: 驻留曝光量

        Returns:
            总曝光量（整数）
        """
        return math.floor(flow_imp + dwell_imp)

    @staticmethod
    def calc_impression_multiplier(flow_traffic: int, imp: float, ad_slots: int) -> float:
        """
        公式(6): 曝光乘数

        ImpressionMultiplier = (flow_Traffic × IMP) / ad_slots

        含义：所在时段每播放一次广告片所产生的曝光量

        Args:
            flow_traffic: 流动人群流量
            imp: 总曝光量
            ad_slots: 轮播广告数量

        Returns:
            曝光乘数
        """
        if ad_slots <= 0:
            return 1.0
        return (flow_traffic * imp) / ad_slots

    @staticmethod
    def calc_frequency(effective_impressions: int, independent_audience: int) -> float:
        """
        接触频次 = 广告有效展示次数 / 独立受众数量

        标准 3.8 定义：平均每个个体看到 DOOH&OOH 广告的次数（≥1 次）

        Args:
            effective_impressions: 有效展示次数
            independent_audience: 独立受众数量

        Returns:
            接触频次
        """
        if independent_audience <= 0:
            return 0.0
        return effective_impressions / independent_audience

    # ── 一站式计算 ─────────────────────────────────────

    def calculate(self, params: ExposureParams) -> ExposureResult:
        """
        一站式曝光计算，执行完整标准公式链。

        计算顺序：
        1. flow_OTC（公式2）→ flow_IMP（公式1）
        2. dwell_OTC（公式4）→ dwell_IMP（公式3）
        3. IMP（公式5）= flow + dwell
        4. Effective IMP（过滤 < 1s 的无效曝光）
        5. ImpressionMultiplier（公式6）

        Args:
            params: 曝光计算参数

        Returns:
            ExposureResult 包含全部曝光指标
        """
        traffic = params.traffic
        dwell_traffic = params.dwell_traffic or traffic

        # Step 1: 流动曝光（公式 2 → 1）
        flow_otc = self.calc_flow_otc(params.exposure_duration, params.ad_duration)
        flow_imp = self.calc_flow_imp(flow_otc, params.sot, traffic)

        # Step 2: 驻留曝光（公式 4 → 3）
        dwell_otc = self.calc_dwell_otc(params.exposure_duration)
        dwell_imp = self.calc_dwell_imp(dwell_otc, dwell_traffic)

        # Step 3: 总曝光（公式 5）
        total_imp = self.calc_total_imp(flow_imp, dwell_imp)

        # Step 4: 有效曝光（过滤 < 1s 观看）
        effective_ratio = 1.0 if params.exposure_duration >= MINIMUM_EXPOSURE_SECONDS else 0.0
        effective_imp = math.floor(total_imp * effective_ratio)

        # Step 5: 曝光乘数（公式 6）
        multiplier = self.calc_impression_multiplier(traffic, total_imp, params.ad_slots_per_cycle)

        # 派生指标：触达和频次（基于 35% 去重系数）
        reach = math.floor(total_imp * 0.35)

        return ExposureResult(
            flow_otc=round(flow_otc, 4),
            dwell_otc=round(dwell_otc, 4),
            flow_impressions=math.floor(flow_imp),
            dwell_impressions=math.floor(dwell_imp),
            total_impressions=total_imp,
            effective_impressions=effective_imp,
            impression_multiplier=round(multiplier, 4),
            reach=reach,
            independent_audience=reach,
            frequency=0.0,  # 待有有效展示数后计算
            traffic=traffic,
            ad_slots=params.ad_slots_per_cycle,
        )

    def calculate_for_campaign(
        self,
        vehicles: int,
        daily_traffic: int,
        hotspot_traffic: float,
        days: int,
        exposure_duration: float = 15.0,
        ad_duration: float = 15.0,
        sot: float = 0.25,
        ad_slots: int = 4,
    ) -> ExposureResult:
        """
        为投放方案计算曝光（考虑车辆数和投放天数）。

        总流量 = 车辆数 × 日均客流 × 热点系数 × 天数

        Args:
            vehicles: 投放车辆数
            daily_traffic: 日均客流
            hotspot_traffic: 热点系数 (1.0-3.0)
            days: 投放天数
            exposure_duration: 平均曝光时长（秒）
            ad_duration: 广告时长（秒）
            sot: 时间占比
            ad_slots: 轮播广告数量

        Returns:
            ExposureResult
        """
        total_traffic = int(vehicles * daily_traffic * hotspot_traffic * days)

        params = ExposureParams(
            traffic=total_traffic,
            exposure_duration=exposure_duration,
            ad_duration=ad_duration,
            sot=sot,
            ad_slots_per_cycle=ad_slots,
        )

        result = self.calculate(params)

        # 计算接触频次
        if result.independent_audience > 0:
            result.frequency = self.calc_frequency(result.effective_impressions, result.independent_audience)
            result.frequency = round(result.frequency, 2)

        return result


# ── 便捷函数 ──────────────────────────────────────────────

_engine = StandardImpressionEngine()


def calc_standard_impression(**kwargs) -> ExposureResult:
    """便捷函数：调用标准曝光计算引擎"""
    return _engine.calculate_for_campaign(**kwargs)
