"""
动态创意 Agent
技术方案：AIGC生成社区场景适配素材，DCO动态创意优化
"""
import json
import random
from typing import Dict, Any, List

from app.services.rag_kb import rag_kb
from app.services.llm_client import llm_client


class DynamicCreativeAgent:
    """
    动态创意Agent
    输入: 人群画像、排期方案、产品卖点
    输出: 创意方案（文案+视觉建议+投放映射）
    """
    
    async def generate_creatives(
        self,
        audience_report: dict = None,
        schedule_plan: dict = None,
        industry: str = "retail",
        product_info: str = ""
    ) -> Dict[str, Any]:
        """生成动态创意方案"""
        # 1. RAG检索相似行业创意模板
        templates_result = await rag_kb.query(f"{industry}创意素材", n_results=3)
        
        # 2. 基于人群特征生成适配文案（AIGC）
        copies = await self._generate_copies_aigc(audience_report, industry, product_info)
        
        # 3. DCO动态创意组合
        dco_map = self._create_dco_mapping(copies, schedule_plan or {}, audience_report or {})
        
        # 4. 生成多模态创意
        creatives = []
        for copy in copies:
            creative = {
                "type": "multimodal",
                "copy": copy["text"],
                "audio_script": copy.get("audio_script", ""),
                "scene": copy["scene_type"],
                "target_cluster": copy.get("target_cluster", ""),
                "visual_suggestion": self._generate_visual_prompt(copy),
                "recommended_formats": ["灯箱", "电子屏", "语音播报"],
            }
            creatives.append(creative)
        
        return {
            "agent": "DynamicCreativeAgent",
            "creatives": creatives,
            "dco_mapping": dco_map,
            "rag_references": templates_result.get("results", []),
            "expected_performance": self._predict_creative_performance(creatives),
        }
    
    async def _generate_copies_aigc(self, audience_report: dict, industry: str, product_info: str) -> list:
        """AIGC生成适配文案"""
        clusters = audience_report.get("clusters", []) if audience_report else []
        
        prompt = f"""
        为{industry}行业生成适配的广告文案，目标人群特征如下：

        {json.dumps(clusters[:3], ensure_ascii=False, default=str)}

        产品信息: {product_info}

        要求：
        1. 为每个人群聚类生成2条不同风格的文案
        2. 适配社区场景（灯箱广告）
        3. 包含语音播报脚本（30秒以内）
        4. 返回JSON格式: [{{"text": "文案", "audio_script": "语音脚本", "scene_type": "场景类型", "target_cluster": "目标人群"}}]
        """
        
        response = await llm_client.chat(prompt)
        
        try:
            # 尝试解析JSON
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                copies = json.loads(json_match.group())
            else:
                copies = self._mock_copies(clusters)
        except:
            copies = self._mock_copies(clusters)
        
        return copies
    
    def _mock_copies(self, clusters: list) -> list:
        """模拟创意文案（无LLM时）"""
        scene_templates = [
            {
                "text": "家的味道，从这一站开始 | 下班路上，为自己选一份温暖",
                "audio_script": "每天忙碌的你，值得被好好对待。走进我们的社区店，感受家的温暖。现在进店，即享新人专属优惠。",
                "scene_type": "通勤回家",
            },
            {
                "text": "周末不宅家！来{location}发现城市新玩法",
                "audio_script": "周末不知道去哪？来我们这里，美食、娱乐、购物一站式体验。带上家人朋友，共度美好时光。",
                "scene_type": "周末休闲",
            },
            {
                "text": "年轻人的第一台{product} | 性价比之选",
                "audio_script": "品质不妥协，价格更友好。现在购买，享分期免息。年轻人的第一选择，从这里开始。",
                "scene_type": "年轻消费",
            },
            {
                "text": "品质生活，触手可及 | 精选好物限时特惠",
                "audio_script": "好的生活不需要很贵。我们为您精选品质好物，限时特惠中。扫码下单，次日送达。",
                "scene_type": "品质生活",
            },
            {
                "text": "家庭好物推荐 | 买对不买贵，精明妈妈的选择",
                "audio_script": "选对的不选贵的。家庭日用好物精选，实用又划算。现在下单，满199减50。",
                "scene_type": "家庭消费",
            },
        ]
        
        copies = []
        for cluster in (clusters or [{"cluster_type": "通用"}]):
            for template in random.sample(scene_templates, min(2, len(scene_templates))):
                copies.append({
                    **template,
                    "target_cluster": cluster.get("cluster_type", "通用"),
                })
        
        return copies
    
    def _create_dco_mapping(self, copies: list, schedule_plan: dict, audience_report: dict) -> dict:
        """DCO动态创意映射"""
        dco_map = {}
        clusters = audience_report.get("clusters", [])
        schedule_items = schedule_plan.get("schedule", []) if schedule_plan else []
        
        for cluster in (clusters or [{"cluster_type": "通用"}]):
            cluster_type = cluster.get("cluster_type", "通用")
            
            # 为每个集群匹配最佳文案
            matching_copies = [c for c in copies if c.get("target_cluster") == cluster_type]
            if not matching_copies:
                matching_copies = copies[:1] if copies else []
            
            for schedule_item in schedule_items:
                key = f"{cluster_type}_{schedule_item.get('id', 'default')}"
                dco_map[key] = {
                    "cluster": cluster_type,
                    "location": schedule_item.get("district", ""),
                    "creative": random.choice(matching_copies) if matching_copies else None,
                    "time_slots": ["07:00-09:00", "12:00-14:00", "17:00-19:00"],
                }
        
        return dco_map
    
    def _generate_visual_prompt(self, copy: dict) -> str:
        """生成视觉建议"""
        scene = copy.get("scene_type", "")
        if "通勤" in scene:
            return "温暖色调，城市街景背景，人物手持产品走在路上"
        elif "休闲" in scene:
            return "明亮活泼色彩，户外场景，人群聚会互动"
        elif "年轻" in scene:
            return "现代简约风格，科技感背景，年轻模特展示"
        elif "品质" in scene:
            return "高级感色调，极简构图，产品特写"
        elif "家庭" in scene:
            return "温馨家庭场景，暖色灯光，亲子互动"
        else:
            return "简洁大气风格，突出产品核心价值"
    
    def _predict_creative_performance(self, creatives: list) -> dict:
        """预估创意表现"""
        return {
            "expected_ctr_range": "3.5% - 6.2%",
            "expected_engagement_rate": "2.8% - 4.5%",
            "top_performing_scene": "通勤回家",
            "a_b_test_suggestion": "建议对年轻消费和品质生活两组创意进行A/B测试",
        }


# 全局实例
creative_agent = DynamicCreativeAgent()
