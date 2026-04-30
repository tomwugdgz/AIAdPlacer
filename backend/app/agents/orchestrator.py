"""
统一编排Agent（规划+反思）
基于LangGraph实现状态机工作流
"""
import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.agents.audience_insight import audience_agent
from app.agents.smart_schedule import schedule_agent
from app.agents.dynamic_creative import creative_agent
from app.agents.attribution import attribution_agent
from app.services.llm_client import llm_client


class CampaignState(TypedDict):
    """工作流状态"""
    query: dict
    audience_report: dict
    schedule_plan: dict
    creative_plan: dict
    attribution_report: dict
    iteration: int
    feedback: str
    plan: str


class OrchestratorAgent:
    """统一编排Agent（规划+反思）"""
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建LangGraph工作流"""
        workflow = StateGraph(CampaignState)
        
        # 添加节点
        workflow.add_node("plan", self._plan)
        workflow.add_node("audience_insight", self._run_audience)
        workflow.add_node("smart_schedule", self._run_schedule)
        workflow.add_node("dynamic_creative", self._run_creative)
        workflow.add_node("attribution", self._run_attribution)
        workflow.add_node("reflect", self._reflect)
        
        # 添加边
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "audience_insight")
        workflow.add_edge("audience_insight", "smart_schedule")
        workflow.add_edge("smart_schedule", "dynamic_creative")
        workflow.add_edge("dynamic_creative", "attribution")
        workflow.add_conditional_edges(
            "attribution",
            self._should_iterate,
            {"reflect": "reflect", "end": END}
        )
        workflow.add_edge("reflect", "smart_schedule")
        
        return workflow.compile()
    
    async def execute(self, query: dict) -> dict:
        """执行完整工作流"""
        import asyncio
        initial_state = {
            "query": query,
            "audience_report": {},
            "schedule_plan": {},
            "creative_plan": {},
            "attribution_report": {},
            "iteration": 0,
            "feedback": "",
            "plan": "",
        }
        
        try:
            result = await self.graph.ainvoke(initial_state)
            return self._format_result(result)
        except Exception as e:
            return {
                "error": str(e),
                "message": "工作流执行失败，请检查配置",
                "state": initial_state,
            }
    
    async def _plan(self, state: CampaignState) -> CampaignState:
        """规划阶段"""
        query = state["query"]
        state["plan"] = f"""
        投放方案规划:
        - 城市: {query.get('city', '广州')}
        - 行业: {query.get('industry', 'retail')}
        - 预算: {query.get('budget', 50000)}
        - 目标: {query.get('objective', '提升品牌认知度')}
        """
        return state
    
    async def _run_audience(self, state: CampaignState) -> CampaignState:
        """人群洞察"""
        query = state["query"]
        state["audience_report"] = await audience_agent.analyze(
            city=query.get("city", "广州"),
            industry=query.get("industry", "retail"),
        )
        return state
    
    async def _run_schedule(self, state: CampaignState) -> CampaignState:
        """智能排期"""
        state["schedule_plan"] = await schedule_agent.generate_schedule(
            audience_report=state["audience_report"],
            budget=state["query"].get("budget", 50000),
            target_audience=state["query"].get("target_audience", {}),
        )
        return state
    
    async def _run_creative(self, state: CampaignState) -> CampaignState:
        """动态创意"""
        state["creative_plan"] = await creative_agent.generate_creatives(
            audience_report=state["audience_report"],
            schedule_plan=state["schedule_plan"],
            industry=state["query"].get("industry", "retail"),
            product_info=state["query"].get("product_info", ""),
        )
        return state
    
    async def _run_attribution(self, state: CampaignState) -> CampaignState:
        """效果归因"""
        # 使用模拟数据进行归因演示
        state["attribution_report"] = await attribution_agent.analyze_attribution(
            db=None,
            campaign_id=None,
        )
        return state
    
    async def _reflect(self, state: CampaignState) -> CampaignState:
        """反思阶段"""
        report = state.get("attribution_report", {})
        
        feedback = await llm_client.chat(
            f"""
            分析以下投放方案的效果数据，提出优化建议：
            跨端匹配率: {report.get('cross_device_match_rate', 0)}
            总转化: {report.get('attribution', {}).get('total_conversions', 0)}
            
            请给出：
            1. 需要调整的投放区域
            2. 预算重新分配建议
            3. 创意优化方向
            4. 排期调整建议
            """,
            system_prompt="你是专业的广告投放优化师"
        )
        
        state["feedback"] = feedback
        state["iteration"] += 1
        return state
    
    def _should_iterate(self, state: CampaignState) -> str:
        """判断是否需要迭代优化"""
        if state.get("iteration", 0) >= 2:
            return "end"
        return "reflect"
    
    def _format_result(self, state: CampaignState) -> dict:
        """格式化输出结果"""
        return {
            "workflow": "CPS 2.0 Agent Orchestration",
            "iterations": state.get("iteration", 0),
            "plan": state.get("plan", ""),
            "audience_insight": {
                "clusters": state.get("audience_report", {}).get("clusters", []),
                "insights": state.get("audience_report", {}).get("insights", []),
                "recommended_areas": state.get("audience_report", {}).get("recommended_areas", []),
            },
            "smart_schedule": {
                "schedule_count": len(state.get("schedule_plan", {}).get("schedule", [])),
                "budget_allocation": state.get("schedule_plan", {}).get("budget_allocation", {}),
                "expected_ctr": state.get("schedule_plan", {}).get("expected_ctr", 0),
            },
            "dynamic_creative": {
                "creative_count": len(state.get("creative_plan", {}).get("creatives", [])),
                "dco_mappings": len(state.get("creative_plan", {}).get("dco_mapping", {})),
            },
            "attribution": {
                "data_summary": state.get("attribution_report", {}).get("data_summary", {}),
                "cross_device_match_rate": state.get("attribution_report", {}).get("cross_device_match_rate", 0),
                "suggestions_count": len(state.get("attribution_report", {}).get("suggestions", [])),
            },
            "feedback": state.get("feedback", ""),
        }


# 全局实例
orchestrator = OrchestratorAgent()
