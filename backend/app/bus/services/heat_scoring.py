"""
bus-pDOOH 子系统 — 热力评分服务

基于腾讯地图 API 计算公交线路热力评分。
V0.1 同步实现（数据量小）；V0.2 升级为 Celery 异步。
"""
import math
from typing import Dict, Any, Optional
from app.services.tencent_map import TencentMapService


class HeatScoringService:
    """公交线路热力评分服务"""

    def __init__(self):
        self.map_service = TencentMapService()

    async def calculate(
        self,
        city: str,
        route_name: str,
    ) -> Dict[str, Any]:
        """
        计算单条线路的热力评分（0-100）。

        Parameters
        ----------
        city : str
            城市名称
        route_name : str
            线路名称

        Returns
        -------
        dict
            {heat_score, poi_data, breakdown}
        """
        # 1. 地理编码：获取线路坐标
        geo = await self.map_service.geocode(route_name, city)
        if not geo:
            return {
                "heat_score": 50.0,  # 默认中位评分
                "poi_data": {"error": "geocode_failed"},
                "breakdown": {"poi_density": 0, "crowd_factor": 0, "time_factor": 0},
            }

        lat, lng = geo["lat"], geo["lng"]

        # 2. 搜索周边 POI（500m 半径）
        pois = await self.map_service.search_nearby(lat, lng, radius=500)

        # 3. POI 密度评分（40%）
        poi_density_score = self._calculate_poi_density(pois)

        # 4. 周边人流系数（40%）
        crowd_factor_score = self._calculate_crowd_factor(pois)

        # 5. 时段评分（20%）
        time_score = self._calculate_time_score()

        # 6. 加权总分
        total = poi_density_score * 0.4 + crowd_factor_score * 0.4 + time_score * 0.2
        heat_score = min(100.0, max(0.0, total))

        return {
            "heat_score": round(heat_score, 1),
            "poi_data": {
                "lat": lat,
                "lng": lng,
                "poi_count": len(pois),
                "pois": pois[:20],
            },
            "breakdown": {
                "poi_density": round(poi_density_score, 1),
                "crowd_factor": round(crowd_factor_score, 1),
                "time_factor": round(time_score, 1),
            },
        }

    def _calculate_poi_density(self, pois: list) -> float:
        """
        POI 密度评分（40%）。
        基准：500m 内 20+ POI = 满分 100。
        """
        if not pois:
            return 0.0
        count = len(pois)
        # 线性映射，20个POI以上满分
        score = min(100.0, (count / 20.0) * 100.0)
        return score

    def _calculate_crowd_factor(self, pois: list) -> float:
        """
        周边人流系数（40%）。
        基于 POI 类型加权：商业区 > 住宅区 > 工业区。
        """
        if not pois:
            return 30.0  # 默认低分

        crowd_keywords = {
            "high": ["商场", "商业", "广场", "购物中心", "步行街", "地铁", "bus", "枢纽", "写字楼"],
            "medium": ["住宅", "小区", "学校", "医院", "超市", "餐饮"],
            "low": ["工业", "园区", "仓库", "物流"],
        }

        high_count = 0
        medium_count = 0
        low_count = 0

        for poi in pois:
            name = poi.get("name", "") + poi.get("category", "")
            if any(k in name for k in crowd_keywords["high"]):
                high_count += 1
            elif any(k in name for k in crowd_keywords["medium"]):
                medium_count += 1
            elif any(k in name for k in crowd_keywords["low"]):
                low_count += 1

        total = len(pois)
        if total == 0:
            return 30.0

        # 加权：high=1.0, medium=0.6, low=0.3
        weighted = (high_count * 1.0 + medium_count * 0.6 + low_count * 0.3) / total
        score = weighted * 100.0
        return score

    def _calculate_time_score(self) -> float:
        """
        时段评分（20%）。
        工作日 > 周末，早晚高峰 > 平峰。
        V0.1 使用固定默认值。
        """
        from datetime import datetime
        now = datetime.utcnow()
        hour = now.hour + 8  # UTC+8
        if hour > 24:
            hour -= 24
        weekday = now.isoweekday()  # 1=Mon, 7=Sun

        # 工作日
        if weekday <= 5:
            if 7 <= hour <= 9 or 17 <= hour <= 19:
                return 90.0  # 早晚高峰
            elif 9 < hour < 17:
                return 70.0  # 工作时间
            else:
                return 40.0  # 夜间
        else:
            # 周末
            if 10 <= hour <= 20:
                return 75.0
            else:
                return 40.0


# 全局实例
heat_scoring_service = HeatScoringService()
