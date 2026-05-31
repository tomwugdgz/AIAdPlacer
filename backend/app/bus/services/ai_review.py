"""
bus-pDOOH 子系统 — AI 方案审核服务

基于 Ollama 本地 LLM（Qwen3.5-9B）对投放方案进行多维度审核：
- 品牌与线路匹配度
- 预算合理性
- 时段配置建议
"""
import json
from typing import Dict, Any, List
from decimal import Decimal
from app.bus.services.bidding_engine import calculate_bidding
from app.services.ollama_client import ollama_client


class AiReviewService:
    """AI 方案审核服务"""

    def __init__(self):
        self.ollama = ollama_client

    async def review_campaign(self, campaign) -> Dict[str, Any]:
        """
        审核投放方案。

        Parameters
        ----------
        campaign : BusCampaign
            投放方案 ORM 对象

        Returns
        -------
        dict
            {status, score, comment, suggestions}
        """
        if not campaign.campaign_routes:
            return {
                "status": "rejected",
                "score": 0,
                "comment": "方案没有选定线路",
                "suggestions": ["请至少添加一条线路"],
            }

        # 1. 收集方案数据
        route_data = []
        total_bidding = Decimal("0")
        total_impressions = 0

        for cr in campaign.campaign_routes:
            route = cr.route
            if not route:
                continue

            bidding = calculate_bidding(
                monthly_price=route.monthly_price,
                level=route.level.value if route.level else "A",
                days=cr.actual_days,
                vehicles=cr.vehicle_count,
                daily_traffic=route.daily_traffic,
                hotspot_traffic=route.hotspot_traffic,
            )

            total_bidding += Decimal(str(bidding["base_price"]))
            total_impressions += bidding["impressions"]

            route_data.append({
                "route_name": route.route_name,
                "route_code": route.route_code,
                "level": route.level.value if route.level else "A",
                "heat_score": route.heat_score,
                "vehicle_count": cr.vehicle_count,
                "budget": float(cr.route_budget),
                "base_price": bidding["base_price"],
                "impressions": bidding["impressions"],
                "daily_traffic": route.daily_traffic,
                "hotspot_traffic": route.hotspot_traffic,
            })

        # 2. 基础规则检查
        suggestions: List[str] = []
        issues: List[str] = []

        # 预算合理性检查
        budget_ratio = float(total_bidding) / float(campaign.total_budget) if campaign.total_budget > 0 else 999
        if budget_ratio > 1.0:
            issues.append(f"线路总价 ¥{total_bidding:.0f} 超出预算 ¥{campaign.total_budget:.0f}（{budget_ratio*100:.1f}%）")
            suggestions.append("建议减少线路或降低车辆数")
        elif budget_ratio < 0.3:
            suggestions.append("预算使用率较低（{:.1f}%），可考虑增加线路提升覆盖".format(budget_ratio * 100))

        # 线路等级检查
        levels = [r["level"] for r in route_data]
        if all(l in ["A", "A+"] for l in levels):
            suggestions.append("所有线路均为 A+/A 等级，可考虑加入 S/A++ 线路提升品牌曝光")

        # 热力评分检查
        avg_heat = sum(r["heat_score"] for r in route_data) / len(route_data) if route_data else 0
        if avg_heat < 40:
            issues.append(f"平均热力评分偏低（{avg_heat:.1f}），建议优先选择高热力线路")
            suggestions.append("推荐热力评分 > 60 的线路")

        # 展示量评估
        cpi = float(total_bidding) / total_impressions if total_impressions > 0 else 0
        if cpi > 0.5:
            suggestions.append(f"单次展示成本 ¥{cpi:.2f} 偏高，可考虑增加车辆数摊薄成本")

        # 3. 生成审核结果
        if issues:
            score = max(0, int(100 - len(issues) * 15 - (budget_ratio - 1.0) * 20 if budget_ratio > 1 else 0))
            status = "rejected"
            comment = "审核不通过：" + "；".join(issues)
        else:
            score = int(60 + avg_heat * 0.3 + (1 - abs(budget_ratio - 0.7)) * 20)
            score = min(100, max(0, score))
            status = "pass"
            comment = f"方案审核通过，综合评分 {score}/100。平均热力 {avg_heat:.1f}，预算使用率 {budget_ratio*100:.1f}%。"

        # 4. LLM 增强建议（异步，超时不阻塞）
        try:
            llm_suggestion = await self._get_llm_suggestions(
                campaign.campaign_name,
                route_data,
                float(campaign.total_budget),
                suggestions,
            )
            if llm_suggestion:
                suggestions.append(f"AI建议：{llm_suggestion}")
        except Exception:
            pass  # LLM 调用失败不影响审核结果

        return {
            "status": status,
            "score": score,
            "comment": comment,
            "suggestions": suggestions,
        }

    async def _get_llm_suggestions(
        self,
        campaign_name: str,
        route_data: List[Dict[str, Any]],
        budget: float,
        existing_suggestions: List[str],
    ) -> str:
        """调用 LLM 生成额外的优化建议"""
        prompt = f"""你是一个户外广告投放优化专家。请基于以下投放方案，给出1-2条简短的优化建议（不超过100字）。

方案名称：{campaign_name}
总预算：¥{budget:,.0f}
线路数量：{len(route_data)}

线路详情：
{json.dumps(route_data, ensure_ascii=False, indent=2)}

已有建议：{', '.join(existing_suggestions) if existing_suggestions else '无'}

请直接给出优化建议，不要解释。"""

        result = await self.ollama.generate(
            prompt=prompt,
            system_prompt="你是户外广告（公交车身）投放优化专家，擅长给出简洁实用的优化建议。",
            temperature=0.5,
        )
        return result.strip()[:500]


# 全局实例
ai_review_service = AiReviewService()
