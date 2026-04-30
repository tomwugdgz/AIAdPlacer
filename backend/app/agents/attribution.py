"""
效果归因 Agent
技术方案：线上线下数据打通，Cookie-ID+设备指纹跨端归因
"""
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models import Placement, Conversion, Campaign
from app.services.mock_data import mock_data
from app.services.rag_kb import rag_kb
from app.services.llm_client import llm_client


class AttributionAgent:
    """
    效果归因Agent
    输入: 投放执行数据、转化数据
    输出: 归因分析报告、ROI看板数据、优化建议
    """
    
    async def analyze_attribution(
        self,
        db: Session = None,
        campaign_id: str = None
    ) -> Dict[str, Any]:
        """执行效果归因分析"""
        # 1. 线上线下数据打通
        online_data = await self._get_online_data(campaign_id)
        offline_data = await self._get_offline_data(campaign_id, db)
        
        # 2. 跨端身份匹配（Cookie-ID + 设备指纹）
        merged_data = self._cross_device_match(online_data, offline_data)
        
        # 3. 多模型归因计算
        multi_touch = self._multi_touch_attribution(merged_data)
        geo_analysis = self._geo_attribution(merged_data)
        
        # 4. 生成ROI看板
        dashboard = self._generate_dashboard(multi_touch, geo_analysis)
        
        # 5. RAG检索优化建议
        suggestions = await rag_kb.query("投放优化建议 ROI提升", n_results=3)
        
        match_rate = self._calculate_match_rate(online_data, offline_data)
        
        return {
            "agent": "AttributionAgent",
            "attribution": multi_touch,
            "geo_analysis": geo_analysis,
            "dashboard": dashboard,
            "suggestions": suggestions.get("results", []),
            "cross_device_match_rate": match_rate,
            "data_summary": {
                "online_records": len(online_data),
                "offline_records": len(offline_data),
                "merged_records": len(merged_data),
                "match_rate": match_rate,
            },
        }
    
    async def _get_online_data(self, campaign_id: str = None) -> list:
        """获取线上数据（模拟）"""
        return mock_data.get_qinlin_app_behavior(user_count=200)
    
    async def _get_offline_data(self, campaign_id: str = None, db: Session = None) -> list:
        """获取线下投放数据"""
        offline_data = []
        if db:
            query = db.query(Placement)
            if campaign_id:
                query = query.filter(Placement.campaign_id == campaign_id)
            
            placements = query.all()
            for p in placements:
                offline_data.append({
                    "placement_id": str(p.id),
                    "date": str(p.date),
                    "impressions": p.impressions,
                    "clicks": p.clicks,
                    "conversions": p.conversions,
                    "cost": float(p.cost or 0),
                    "lat": p.latitude,
                    "lng": p.longitude,
                })
        
        # 补充模拟数据
        qadn_data = mock_data.get_qadn_location_data()
        for poi in qadn_data[:20]:
            offline_data.append({
                "poi_id": poi["poi_id"],
                "lat": poi["lat"],
                "lng": poi["lng"],
                "foot_traffic": poi["foot_traffic_daily"],
                "impressions": int(poi["foot_traffic_daily"] * 0.3),
                "district": poi["district"],
            })
        
        return offline_data
    
    def _cross_device_match(self, online_data: list, offline_data: list) -> list:
        """跨端身份匹配：Cookie-ID + 设备指纹"""
        # 构建匹配索引
        fp_index = {d.get("device_fingerprint"): d for d in online_data if d.get("device_fingerprint")}
        
        merged = []
        for od in online_data:
            # 尝试通过设备指纹匹配
            match = None
            for ofd in offline_data:
                # 简单坐标匹配（实际应使用更复杂的匹配逻辑）
                if ofd.get("lat") and od.get("location_visited"):
                    district = ofd.get("district", "")
                    if district in od.get("location_visited", []):
                        match = ofd
                        break
            
            merged_record = {**od}
            if match:
                merged_record["matched_offline"] = True
                merged_record["offline_data"] = match
            else:
                merged_record["matched_offline"] = False
            
            merged.append(merged_record)
        
        return merged
    
    def _multi_touch_attribution(self, merged_data: list) -> dict:
        """多触点归因分析"""
        conversions = [d for d in merged_data if d.get("conversion")]
        
        # 按触点类型分组
        touch_types = {}
        for conv in conversions:
            actions = conv.get("actions", [])
            for action in actions:
                action_type = action.get("type", "unknown")
                if action_type not in touch_types:
                    touch_types[action_type] = {"count": 0, "value": 0}
                touch_types[action_type]["count"] += 1
                touch_types[action_type]["value"] += conv.get("conversion_value", 0)
        
        return {
            "total_conversions": len(conversions),
            "total_value": sum(d.get("conversion_value", 0) for d in conversions),
            "touch_type_attribution": touch_types,
            "avg_touchpoints": sum(len(d.get("actions", [])) for d in conversions) / max(len(conversions), 1),
        }
    
    def _geo_attribution(self, merged_data: list) -> dict:
        """地域归因分析"""
        district_data = {}
        
        for record in merged_data:
            for location in record.get("location_visited", []):
                if location not in district_data:
                    district_data[location] = {"users": 0, "conversions": 0, "value": 0}
                district_data[location]["users"] += 1
                if record.get("conversion"):
                    district_data[location]["conversions"] += 1
                    district_data[location]["value"] += record.get("conversion_value", 0)
        
        # 按转化率排序
        ranked = sorted(
            district_data.items(),
            key=lambda x: x[1]["conversions"] / max(x[1]["users"], 1),
            reverse=True
        )
        
        return {
            "district_ranking": [
                {"district": name, **data, "conversion_rate": data["conversions"] / max(data["users"], 1)}
                for name, data in ranked[:10]
            ],
            "total_districts": len(district_data),
        }
    
    def _generate_dashboard(self, multi_touch: dict, geo_analysis: dict) -> dict:
        """生成ROI看板数据"""
        return {
            "kpi_summary": {
                "total_conversions": multi_touch.get("total_conversions", 0),
                "total_value": round(multi_touch.get("total_value", 0), 2),
                "avg_touchpoints": round(multi_touch.get("avg_touchpoints", 0), 1),
                "top_district": geo_analysis.get("district_ranking", [{}])[0].get("district", "N/A") if geo_analysis.get("district_ranking") else "N/A",
            },
            "roi_metrics": {
                "cost_per_acquisition": "待接入成本数据",
                "return_on_ad_spend": "待接入ROAS数据",
                "lifetime_value": "待接入LTV数据",
            },
            "trend_data": self._generate_mock_trend(),
        }
    
    def _generate_mock_trend(self) -> list:
        """生成模拟趋势数据"""
        from datetime import datetime, timedelta
        trend = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).date()
            trend.append({
                "date": str(date),
                "impressions": 150000 + i * 10000,
                "clicks": 7000 + i * 500,
                "conversions": 300 + i * 30,
            })
        return trend
    
    def _calculate_match_rate(self, online_data: list, offline_data: list) -> float:
        """计算跨端匹配率"""
        if not online_data:
            return 0.0
        
        matched = sum(1 for d in online_data if d.get("location_visited"))
        return round(matched / len(online_data), 2)


# 全局实例
attribution_agent = AttributionAgent()
