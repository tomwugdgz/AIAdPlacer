from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np
from app.models import Placement, Conversion


class AttributionEngine:
    """归因分析引擎"""
    
    @staticmethod
    def geo_attribution(db: Session, campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        地域归因分析
        1. 按地理位置聚合投放数据
        2. 计算各区域ROI
        3. 生成地域效果排名
        """
        query = db.query(
            Placement.latitude,
            Placement.longitude,
            func.sum(Placement.impressions).label('total_impressions'),
            func.sum(Placement.clicks).label('total_clicks'),
            func.sum(Placement.conversions).label('total_conversions'),
            func.sum(Placement.cost).label('total_cost')
        )
        
        if campaign_id:
            query = query.filter(Placement.campaign_id == campaign_id)
        
        query = query.group_by(Placement.latitude, Placement.longitude)
        results = query.all()
        
        geo_data = []
        for row in results:
            roi = 0
            if row.total_cost > 0:
                roi = (row.total_conversions * 100) / row.total_cost
            
            geo_data.append({
                "lat": row.latitude,
                "lng": row.longitude,
                "impressions": row.total_impressions,
                "clicks": row.total_clicks,
                "conversions": row.total_conversions,
                "cost": float(row.total_cost),
                "roi": roi,
                "ctr": row.total_clicks / row.total_impressions if row.total_impressions > 0 else 0,
                "cvr": row.total_conversions / row.total_clicks if row.total_clicks > 0 else 0,
            })
        
        # 按ROI排序
        geo_data.sort(key=lambda x: x["roi"], reverse=True)
        return geo_data
    
    @staticmethod
    def multi_touch_attribution(
        db: Session, 
        campaign_id: Optional[str] = None,
        model: str = "linear"
    ) -> Dict[str, Any]:
        """
        多触点归因模型
        - first: 首次触点获得全部权重
        - last: 最终触点获得全部权重
        - linear: 所有触点平均分配
        - time_decay: 时间衰减模型
        """
        query = db.query(Conversion).order_by(Conversion.created_at)
        
        if campaign_id:
            # 需要先关联placement获取campaign_id
            from app.models import Placement
            query = query.join(Placement).filter(Placement.campaign_id == campaign_id)
        
        conversions = query.all()
        
        if not conversions:
            return {"error": "无转化数据"}
        
        # 按触点模型分配权重
        attribution_data = {
            "first_touch": {},
            "last_touch": {},
            "linear": {},
            "time_decay": {},
        }
        
        for conv in conversions:
            placement_id = str(conv.placement_id)
            
            # 首次触点
            if conv.touchpoint_order == 1:
                attribution_data["first_touch"][placement_id] = \
                    attribution_data["first_touch"].get(placement_id, 0) + float(conv.conversion_value or 0)
            
            # 最终触点（简化处理：假设最后一个触点是最大的touchpoint_order）
            # 实际应该查询用户所有触点后确定
            attribution_data["last_touch"][placement_id] = \
                attribution_data["last_touch"].get(placement_id, 0) + float(conv.conversion_value or 0)
            
            # 线性分配
            if model == "linear":
                weight = float(conv.conversion_value or 0)
                attribution_data["linear"][placement_id] = \
                    attribution_data["linear"].get(placement_id, 0) + weight
            
            # 时间衰减（越接近转化权重越高）
            if model == "time_decay":
                decay_weight = 2 ** (conv.touchpoint_order - 1)
                weight = (float(conv.conversion_value or 0) * decay_weight) / 10
                attribution_data["time_decay"][placement_id] = \
                    attribution_data["time_decay"].get(placement_id, 0) + weight
        
        return {
            "model": model,
            "attribution": attribution_data[model],
            "all_models": attribution_data,
            "total_conversions": len(conversions),
            "total_value": sum(float(c.conversion_value or 0) for c in conversions),
        }
    
    @staticmethod
    def spatio_temporal_attribution(
        db: Session,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        时空归因矩阵
        时间×地理二维归因分析
        """
        query = db.query(
            Placement.date,
            Placement.latitude,
            Placement.longitude,
            Placement.impressions,
            Placement.clicks,
            Placement.conversions,
            Placement.cost
        )
        
        if campaign_id:
            query = query.filter(Placement.campaign_id == campaign_id)
        
        placements = query.all()
        
        if not placements:
            return {"error": "无投放数据"}
        
        # 构建时空矩阵
        df = pd.DataFrame([
            {
                "date": p.date,
                "lat": p.latitude,
                "lng": p.longitude,
                "impressions": p.impressions,
                "clicks": p.clicks,
                "conversions": p.conversions,
                "cost": float(p.cost),
                "week_day": p.date.weekday(),
            }
            for p in placements
        ])
        
        # 时间维度分析
        time_analysis = df.groupby("date").agg({
            "impressions": "sum",
            "clicks": "sum",
            "conversions": "sum",
            "cost": "sum"
        }).reset_index()
        
        # 地理维度分析
        geo_analysis = df.groupby(["lat", "lng"]).agg({
            "impressions": "sum",
            "clicks": "sum",
            "conversions": "sum",
            "cost": "sum"
        }).reset_index()
        
        # 计算ROI
        geo_analysis["roi"] = geo_analysis["conversions"] / geo_analysis["cost"]
        
        return {
            "time_analysis": time_analysis.to_dict(orient="records"),
            "geo_analysis": geo_analysis.to_dict(orient="records"),
            "summary": {
                "total_impressions": int(df["impressions"].sum()),
                "total_clicks": int(df["clicks"].sum()),
                "total_conversions": int(df["conversions"].sum()),
                "total_cost": float(df["cost"].sum()),
                "avg_ctr": float(df["clicks"].sum() / df["impressions"].sum()) if df["impressions"].sum() > 0 else 0,
                "avg_cvr": float(df["conversions"].sum() / df["clicks"].sum()) if df["clicks"].sum() > 0 else 0,
            }
        }
    
    @staticmethod
    def conversion_funnel(db: Session, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """
        转化漏斗分析
        曝光 → 点击 → 转化
        """
        query = db.query(
            func.sum(Placement.impressions).label('impressions'),
            func.sum(Placement.clicks).label('clicks'),
            func.sum(Placement.conversions).label('conversions')
        )
        
        if campaign_id:
            query = query.filter(Placement.campaign_id == campaign_id)
        
        result = query.first()
        
        impressions = result.impressions or 0
        clicks = result.clicks or 0
        conversions = result.conversions or 0
        
        return {
            "funnel": [
                {"stage": "曝光", "count": impressions, "percentage": 100},
                {"stage": "点击", "count": clicks, "percentage": (clicks / impressions * 100) if impressions > 0 else 0},
                {"stage": "转化", "count": conversions, "percentage": (conversions / impressions * 100) if impressions > 0 else 0},
            ],
            "ctr": (clicks / impressions * 100) if impressions > 0 else 0,
            "cvr": (conversions / clicks * 100) if clicks > 0 else 0,
        }


attribution_engine = AttributionEngine()
