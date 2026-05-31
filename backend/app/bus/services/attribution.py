"""
bus-pDOOH 子系统 — 效果归因服务

计算投放效果指标：
- 展示量 = 车辆数 × 日均客流 × 热点系数 × 实际天数
- 触达人数 = 展示量 × 去重系数（0.35）
- CPI = 总预算 / 总展示量
- CPR = 总预算 / 总触达人数
"""
from typing import Dict, Any
from decimal import Decimal


class AttributionService:
    """效果归因服务"""

    # 去重系数（假设 35% 的去重触达率）
    DEDUP_FACTOR = 0.35

    async def calculate(self, campaign) -> Dict[str, Any]:
        """
        计算投放方案的效果归因。

        Parameters
        ----------
        campaign : BusCampaign
            投放方案 ORM 对象

        Returns
        -------
        dict
            {total_impressions, total_reach, cost_per_impression,
             cost_per_reach, detailed_data}
        """
        total_impressions = 0
        route_breakdown = []

        for cr in campaign.campaign_routes:
            route = cr.route
            if not route:
                continue

            # 展示量 = 车辆数 × 日均客流 × 热点系数 × 实际天数
            impressions = cr.vehicle_count * route.daily_traffic * route.hotspot_traffic * cr.actual_days

            route_breakdown.append({
                "route_id": str(route.id),
                "route_code": route.route_code,
                "route_name": route.route_name,
                "vehicle_count": cr.vehicle_count,
                "actual_days": cr.actual_days,
                "daily_traffic": route.daily_traffic,
                "hotspot_traffic": route.hotspot_traffic,
                "impressions": impressions,
                "budget": float(cr.route_budget),
            })

            total_impressions += impressions

        # 触达人数（去重）
        total_reach = int(total_impressions * self.DEDUP_FACTOR)

        # 成本指标
        total_budget = float(campaign.total_budget)
        cpi = round(total_budget / total_impressions, 4) if total_impressions > 0 else 0.0
        cpr = round(total_budget / total_reach, 4) if total_reach > 0 else 0.0

        return {
            "total_impressions": total_impressions,
            "total_reach": total_reach,
            "cost_per_impression": cpi,
            "cost_per_reach": cpr,
            "detailed_data": {
                "budget": total_budget,
                "route_count": len(route_breakdown),
                "route_breakdown": route_breakdown,
                "dedup_factor": self.DEDUP_FACTOR,
            },
        }


# 全局实例
attribution_service = AttributionService()
