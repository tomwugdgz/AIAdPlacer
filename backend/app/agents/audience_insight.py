"""
人群洞察 Agent
技术方案：基于LBS+友盟数据，聚类算法动态划分微细分群体
"""
import json
from typing import List, Dict, Any, Optional
from sklearn.cluster import KMeans, DBSCAN
import numpy as np

from app.services.mock_data import mock_data
from app.services.rag_kb import rag_kb
from app.services.llm_client import llm_client


class AudienceInsightAgent:
    """
    人群洞察Agent
    输入: 目标城市、行业类型、预算范围
    输出: 人群画像报告、推荐投放区域、最佳触达时段
    """
    
    async def analyze(self, city: str = "广州", industry: str = "retail", date_range: dict = None) -> Dict[str, Any]:
        """执行人群洞察分析"""
        # 1. 数据融合：LBS + 友盟
        lbs_data = mock_data.get_qadn_location_data(city, date_range)
        umeng_data = mock_data.get_umeng_audience_data(city)
        fused_data = self._fuse_data(lbs_data, umeng_data)
        
        # 2. 聚类分群
        clusters = self._cluster_audience(fused_data, algorithm="kmeans")
        
        # 3. RAG检索行业案例
        rag_results = await rag_kb.query(f"{industry}人群运营案例", n_results=3)
        
        # 4. LLM生成洞察报告
        report = await llm_client.generate_report(
            clusters,
            context=f"行业: {industry}, 城市: {city}\n参考案例: {json.dumps(rag_results, ensure_ascii=False, default=str)}"
        )
        
        return {
            "agent": "AudienceInsightAgent",
            "city": city,
            "industry": industry,
            "clusters": clusters,
            "insights": report.get("insights", []),
            "recommended_areas": report.get("recommended_areas", []),
            "best_touch_times": report.get("best_times", []),
            "rag_references": rag_results.get("results", []),
        }
    
    def _fuse_data(self, lbs_data: list, umeng_data: dict) -> list:
        """融合LBS和友盟数据"""
        fused = []
        umeng_districts = umeng_data.get("districts", {})
        
        for poi in lbs_data:
            district_name = poi.get("district", "")
            umeng_info = umeng_districts.get(district_name, {})
            
            fused.append({
                "poi_id": poi["poi_id"],
                "name": poi["name"],
                "lat": poi["lat"],
                "lng": poi["lng"],
                "district_type": poi["district_type"],
                "foot_traffic": poi["foot_traffic_daily"],
                "dwell_time": poi["dwell_time_avg_min"],
                "age_group": poi["audience_profile"]["age_group"],
                "income_level": poi["audience_profile"]["income_level"],
                "top_interests": poi["audience_profile"]["top_interests"],
                "mobile_pct": poi["device_data"]["mobile_visitors_pct"],
                "unique_devices": poi["device_data"]["unique_devices_daily"],
                # 友盟补充数据
                "umeng_total_users": umeng_info.get("total_users", 0),
                "umeng_interests": umeng_info.get("interest_ranking", []),
            })
        
        return fused
    
    def _cluster_audience(self, data: list, algorithm: str = "kmeans") -> list:
        """聚类算法划分人群"""
        # 提取数值特征
        features = []
        feature_names = ["foot_traffic", "dwell_time", "mobile_pct", "unique_devices", "umeng_total_users"]
        
        for item in data:
            feature_vec = []
            for name in feature_names:
                val = item.get(name, 0)
                if isinstance(val, (int, float)):
                    feature_vec.append(val)
                else:
                    feature_vec.append(0)
            features.append(feature_vec)
        
        if not features:
            return []
        
        features = np.array(features)
        
        # 标准化
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # 聚类
        n_clusters = min(5, len(features))
        if algorithm == "kmeans" and n_clusters >= 2:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(features_scaled)
        else:
            dbscan = DBSCAN(eps=0.5, min_samples=2)
            labels = dbscan.fit_predict(features_scaled)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        # 构建聚类画像
        clusters = []
        for cluster_id in range(n_clusters):
            cluster_items = [data[i] for i in range(len(data)) if labels[i] == cluster_id]
            
            if not cluster_items:
                continue
            
            avg_traffic = np.mean([item["foot_traffic"] for item in cluster_items])
            avg_dwell = np.mean([item["dwell_time"] for item in cluster_items])
            
            # 判断人群类型
            if avg_traffic > 30000:
                cluster_type = "高流量核心商圈"
            elif avg_dwell > 8:
                cluster_type = "高停留深度体验区"
            elif avg_traffic > 15000:
                cluster_type = "中等流量潜力区"
            else:
                cluster_type = "社区生活区"
            
            clusters.append({
                "cluster_id": cluster_id,
                "cluster_type": cluster_type,
                "size": len(cluster_items),
                "avg_foot_traffic": int(avg_traffic),
                "avg_dwell_time": round(float(avg_dwell), 1),
                "locations": [{"name": item["name"], "district": item["district_type"]} for item in cluster_items[:5]],
                "dominant_interests": self._get_dominant_interests(cluster_items),
            })
        
        return clusters
    
    def _get_dominant_interests(self, cluster_items: list) -> list:
        """获取聚类群体的主导兴趣"""
        interest_counts = {}
        for item in cluster_items:
            for interest in item.get("top_interests", []):
                interest_counts[interest] = interest_counts.get(interest, 0) + 1
            for interest in item.get("umeng_interests", []):
                interest_counts[interest] = interest_counts.get(interest, 0) + 0.5
        
        sorted_interests = sorted(interest_counts.items(), key=lambda x: x[1], reverse=True)
        return [name for name, count in sorted_interests[:3]]


# 全局实例
audience_agent = AudienceInsightAgent()
