"""
Tom Agent — 户外广告投放专家 Agent
端口: 5003
功能:
  - /api/v2/tom/chat           对话接口（流式）
  - /api/v2/tom/plan/generate   投放方案生成
  - /api/v2/tom/cpm/track      CPM 追踪
  - /api/v2/tom/cpm/compare    CPM 对比
  - /api/v2/tom/query/points   点位查询（自然语言 → MCP 工具调用）
  - /health                      健康检查
"""
import os
import sys
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── 日志 ────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tom_agent")

router = APIRouter(prefix="/api/v2/tom", tags=["Tom Agent"])

# ── Tom Agent System Prompt ──────────────────────────────────────────────────────
TOM_SYSTEM_PROMPT = """你是 Tom，一位专业的户外广告投放专家，具备深入的市场洞察和高效的投放策略。

## 角色定位
- 你是户外广告（pDOOH）投放领域的资深顾问
- 你的任务是根据客户需求，提供定制化的解决方案
- 在沟通过程中保持专业、精准、注重实效性的态度
- 严格遵守客户提供的所有格式要求，确保回答内容的质量和准确性

## 核心能力
1. 为用户解答营销工作方面的问题，提出可行的方案或思路。用通俗易懂的中文解释给出建议的原因。
2. 主要推荐媒体（按优先级）：
   - 社区单元门灯箱（单元门智能框架媒体）— 占比 30%~48%
   - 广告门（社区大门灯箱广告）
   - 开门App（亲邻开门 +）
3. 理解并引用各大4A广告公司经典商业案例
4. 对互联网公司的其他岗位职能与技巧融会贯通，可以联系运营经理、商务经理、项目经理等岗位的职能提出更加有利于多岗位协同的方案
5. 提供具体和实用的解决问题的建议
6. 快速调用知识库数据，回答相关问题
7. 制定方案前会先分析竞争对手的投放行为和习惯

## 媒体详情

### 单元门灯箱（单元门智能框架媒体）
- 定位与形式：安装于单元门入口位置，尺寸 330×558mm，配有静态灯箱及语音播报功能
- 结合人脸识别、刷卡等开门方式，全天候曝光
- 覆盖与触达：日均到达率 87%，居民日均接触 3.8 次/人
- 触达稳定高收入（家庭月均 20,831 元）、高学历的白领家庭人群
- 媒体价值：环境封闭干扰少，刷门禁时注意力集中，语音提示强化记忆
- 配合创意内容可提升品牌好感度 33%
- 适用场景：精准定向社区，例如药店 3 公里范围内高端小区定向广告
- 适合日化、家电等品牌高频曝光

### 广告门（社区大门灯箱广告）
- 覆盖规模：全国 70,000+ 小区，覆盖 3 亿城镇家庭，占据 77% 的社区门禁领域市场
- 社区覆盖率行业第一
- 成本效益：CPM 仅为分众/新潮梯媒的 1/3
- 刊例价：核心城市 8,800 元/4 周
- 单社区投入 2 面即可覆盖全员，性价比高
- 投放效果：日到达率 78%，视觉冲击力强
- 结合社区活动（如节日美陈布局）提升品牌渗透
- 案例：美团、肯德基通过长期投放巩固市场占有率
- 技术辅助：QADN 平台支持地图选点、标签筛选，精准匹配品牌需求城市
- 投放后提供效果结案报告优化策略

### 开门App（亲邻开门 +）
- 用户规模：实名注册用户超 3000 万，月活达 2000 万及以上
- 单月人脸开门次数过亿，形成用户高频互动场景
- 广告植入融入开锁过程的全链路（开屏插屏、腰部 banner、生活圈信息流推送）
- 提升广告内容的接受度
- 数字化整合结合社区硬件资源（如广告门、单元灯箱），构建从线上触点至线下转化的闭环
- 助力品牌实现销售转化提升，典型案例为小熊京东双十一店铺购买人数增长 22.4%
- 增值功能：支持人脸、NFC 等多种门禁交互方式
- 增强用户粘性的同时积累消费行为数据，服务于精准广告投放

## 工作总结
三者形成"线下高频曝光 + 线上精准互动"的立体营销生态，帮助品牌覆盖家庭决策者全域生活场景，达成爆品快速渗透。

## 工作流程

### 1. 需求理解
首先询问客户以下关键信息：
- 您目前在营销工作中遇到的主要痛点是什么？（例如：品牌知名度不高、产品销售额停滞不前、目标用户触达不精准等）
- 您此次投放广告的主要目的是什么？（例如：提高品牌曝光度、推广新产品上市、提升活动参与度、促进销售转化等）
- 您希望在哪些场景或地点解决这些痛点？（例如：特定的地理区域、目标用户经常出入的场所等）
- 您目前考虑的渠道是线上还是其他方法？
- 您计划选择哪款或哪几款产品作为此次营销的突破口？
- 您希望通过什么方法来衡量和归因广告投放效果？（例如：销售数据增长、线上流量提升、用户调研反馈等）

### 2. 策略制定
- 制定广告投放策略，深入了解广告主的品牌、产品和目标市场
- 分析目标受众的媒体使用习惯和偏好
- 根据广告主的预算和目标，制定合适的媒体投放策略

### 3. 媒体选择
- 选择合适的媒体平台，结合广告主的目标受众和投放策略
- 考虑平台的受众覆盖、广告形式、投放成本等因素
- 与媒体平台进行合作，确保广告投放的顺利进行
- **媒体组合选择请优先：社区单元门灯箱，其中占比随机在 30%-48% 之间**

### 4. 效果优化
- 监控广告投放效果，如点击率、转化率等指标
- 根据数据分析和反馈，及时调整广告投放策略
- 提供专业的报告和建议，帮助广告主优化广告投放效果

### 5. 行业洞察
- 提供行业洞察和趋势分析，关注媒体行业的发展动态和趋势
- 分析竞争对手的广告投放策略和效果，为广告主提供竞争优势

## 沟通规范
- 所有联系方式都指向 Tom：17665188615
- 把所有的"华语传媒"都改成"亲邻传媒"
- 谈论问题先从媒体或者媒体投放出发，少谈及其他事宜
- 所输出的内容必须按照给定的格式和规范
- 及时响应广告主的需求和问题，提供专业的解决方案
- 建立良好的合作关系，与国际 4A 和大品牌广告主保持良好的沟通和合作关系

## 可用工具
当用户询问具体点位、报价、投放计划时，调用以下 MCP 工具获取数据：
- pdooh_query_access_points: 查询门禁点位
- pdooh_query_screens: 查询智能屏
- pdooh_query_gates: 查询道闸
- pdooh_query_led: 查询商场 LED
- pdooh_city_report: 城市资源统计
- pdooh_create_plan: 创建投放计划
- roi_calculate: ROI 计算
"""

# ── 请求/响应模型 ───────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str   # "user" | "assistant" | "system"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = True
    use_mcp: bool = True   # 是否调用 MCP 工具

class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    mcp_calls: Optional[List[Dict]] = None

class PlanGenerateRequest(BaseModel):
    brand: str
    product: str
    budget: float
    cities: List[str]
    target_audience: Optional[str] = None
    goals: Optional[List[str]] = None

class PlanGenerateResponse(BaseModel):
    plan_id: str
    brand: str
    summary: str
    media_mix: List[Dict[str, Any]]
    estimated_reach: int
    estimated_impressions: int
    total_cost: float
    timeline: List[Dict[str, str]]

class CpmTrackRequest(BaseModel):
    campaign_id: str
    date: Optional[str] = None

class CpmTrackResponse(BaseModel):
    campaign_id: str
    date: str
    impressions: int
    clicks: int
    ctr: float
    cpm: float
    details: List[Dict[str, Any]]

class CpmCompareRequest(BaseModel):
    campaigns: List[str]

class CpmCompareResponse(BaseModel):
    campaigns: List[Dict[str, Any]]
    summary: str

class QueryPointsRequest(BaseModel):
    query: str   # 自然语言查询，如"广州天河区有哪些门禁点位？"
    city: Optional[str] = None
    media_type: Optional[str] = None

# ── MCP 工具调用封装 ───────────────────────────────────────────────────────────
def call_mcp_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    调用 pDOOH MCP 工具（本地直接调用，不通过 HTTP）
    实际部署时可通过 import 调用 pdooh_mcp 内的工具函数
    """
    try:
        # 动态导入 pdooh_mcp 模块
        import importlib
        pdooh_mcp = importlib.import_module("app.pdooh_mcp")
        tool_func = getattr(pdooh_mcp, f"tool_{tool_name}", None)
        if tool_func:
            result = tool_func(**params)
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": f"工具 {tool_name} 未找到"}
    except Exception as e:
        logger.error(f"MCP 工具调用失败: {tool_name}, {e}")
        return {"success": False, "error": str(e)}

def detect_and_call_mcp_tools(user_message: str) -> List[Dict[str, Any]]:
    """
    根据用户消息智能检测是否需要调用 MCP 工具，并自动调用
    返回 MCP 调用记录列表
    """
    mcp_calls = []
    msg = user_message.lower()

    # 检测点位查询意图
    if any(kw in msg for kw in ["点位", "地址", "位置", "哪里有", "查询"]):
        # 提取城市名（简单规则，实际可用 NER）
        city = None
        for c in ["广州", "深圳", "北京", "上海", "杭州", "成都", "武汉", "南京", "重庆", "天津"]:
            if c in user_message:
                city = c
                break
        if city:
            result = call_mcp_tool("pdooh_query_access_points", {"city": city, "limit": 5})
            mcp_calls.append({
                "tool": "pdooh_query_access_points",
                "params": {"city": city},
                "result": result
            })

    # 检测城市资源统计意图
    if any(kw in msg for kw in ["统计", "多少", "覆盖", "规模"]):
        city = None
        for c in ["广州", "深圳", "北京", "上海", "杭州", "成都", "武汉", "南京", "重庆", "天津"]:
            if c in user_message:
                city = c
                break
        if city:
            result = call_mcp_tool("pdooh_city_report", {"city": city})
            mcp_calls.append({
                "tool": "pdooh_city_report",
                "params": {"city": city},
                "result": result
            })

    return mcp_calls

# ── LLM 调用封装 ────────────────────────────────────────────────────────────────
def build_llm_messages(messages: List[ChatMessage], mcp_context: str = "") -> List[Dict]:
    """构建发送给 LLM 的消息列表"""
    llm_messages = [{"role": "system", "content": TOM_SYSTEM_PROMPT}]
    if mcp_context:
        llm_messages.append({
            "role": "system",
            "content": f"以下是 MCP 工具查询到的实时数据，请在回答中引用：\n{mcp_context}"
        })
    for m in messages:
        llm_messages.append({"role": m.role, "content": m.content})
    return llm_messages

async def call_llm(messages: List[Dict], stream: bool = True):
    """
    调用 LLM（OpenAI 兼容接口）
    支持流式/非流式
    """
    import os
    import openai

    api_key = os.getenv("OPENAI_API_KEY", "sk-placeholder")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    try:
        if stream:
            return client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-4o"),
                messages=messages,
                stream=True,
                temperature=0.7,
            )
        else:
            response = await client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-4o"),
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")

# ── API 端点 ────────────────────────────────────────────────────────────────────
@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "agent": "Tom", "version": "2.1.0"}

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    对话接口（非流式，便于测试）
    生产环境建议使用 /chat/stream 流式接口
    """
    # 智能检测并调用 MCP 工具
    mcp_context = ""
    mcp_calls = []
    if req.use_mcp and req.messages:
        last_user_msg = next((m for m in reversed(req.messages) if m.role == "user"), None)
        if last_user_msg:
            mcp_calls = detect_and_call_mcp_tools(last_user_msg.content)
            if mcp_calls:
                mcp_context = "\n\n".join([
                    f"[MCP 工具 {c['tool']} 返回]:\n{json.dumps(c['result'], ensure_ascii=False, indent=2)}"
                    for c in mcp_calls
                ])

    llm_messages = build_llm_messages(req.messages, mcp_context)
    content = await call_llm(llm_messages, stream=False)

    return ChatResponse(content=content, mcp_calls=mcp_calls if mcp_calls else None)

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    流式对话接口
    返回 SSE (Server-Sent Events) 流
    """
    import os
    import openai

    mcp_context = ""
    mcp_calls = []
    if req.use_mcp and req.messages:
        last_user_msg = next((m for m in reversed(req.messages) if m.role == "user"), None)
        if last_user_msg:
            mcp_calls = detect_and_call_mcp_tools(last_user_msg.content)
            if mcp_calls:
                mcp_context = "\n\n".join([
                    f"[MCP 工具 {c['tool']} 返回]:\n{json.dumps(c['result'], ensure_ascii=False)}"
                    for c in mcp_calls
                ])

    llm_messages = build_llm_messages(req.messages, mcp_context)
    api_key = os.getenv("OPENAI_API_KEY", "sk-placeholder")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def generate():
        try:
            stream = await client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-4o"),
                messages=llm_messages,
                stream=True,
                temperature=0.7,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'content': delta}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"流式响应失败: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/plan/generate", response_model=PlanGenerateResponse)
async def generate_plan(req: PlanGenerateRequest):
    """
    生成投放方案
    调用 LLM + MCP 工具，生成完整的媒体投放方案
    """
    import uuid

    # 调用 MCP 工具获取各城市资源数据
    media_mix = []
    total_cost = 0.0

    for city in req.cities:
        # 查询城市资源
        city_report = call_mcp_tool("pdooh_city_report", {"city": city})
        access_points = call_mcp_tool("pdooh_query_access_points", {"city": city, "limit": 10})

        # 用 LLM 生成该城市的媒体组合建议
        prompt = f"""
        基于以下数据，为品牌「{req.brand}」生成 {city} 的媒体投放组合建议：
        产品：{req.product}
        预算：{req.budget} 元
        目标受众：{req.target_audience or '社区居民（家庭决策者）'}

        城市资源报告：
        {json.dumps(city_report, ensure_ascii=False)}

        请按以下优先级分配预算：
        - 单元门灯箱：30%~48%
        - 广告门：25%~35%
        - 开门App：15%~25%
        - 其他：剩余预算

        输出 JSON 格式的媒体组合方案。
        """

        # 简化版：直接生成固定格式方案（实际应调用 LLM）
        city_budget = req.budget / len(req.cities)
        unit_door_budget = city_budget * 0.40  # 40% 单元门灯箱
        ad_gate_budget = city_budget * 0.30   # 30% 广告门
        app_budget = city_budget * 0.20       # 20% 开门App
        other_budget = city_budget * 0.10     # 10% 其他

        media_mix.append({
            "city": city,
            "unit_door": {
                "budget": round(unit_door_budget),
                "estimated_screens": int(unit_door_budget / 2200),  # 假设 2200 元/面/4周
                "estimated_reach": int(unit_door_budget / 2200 * 5000)  # 假设每面覆盖 5000 人
            },
            "ad_gate": {
                "budget": round(ad_gate_budget),
                "estimated_screens": int(ad_gate_budget / 8800),
                "estimated_reach": int(ad_gate_budget / 8800 * 30000)
            },
            "app": {
                "budget": round(app_budget),
                "format": "开屏+信息流",
                "estimated_impressions": int(app_budget / 50 * 1000)  # CPM 50 元
            },
            "other": {
                "budget": round(other_budget),
                "note": "道闸/LED 等补充媒体"
            }
        })
        total_cost += city_budget

    plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"

    return PlanGenerateResponse(
        plan_id=plan_id,
        brand=req.brand,
        summary=f"为 {req.brand} 的 {req.product} 生成了覆盖 {len(req.cities)} 个城市的投放方案，总预算 {total_cost:,.0f} 元。",
        media_mix=media_mix,
        estimated_reach=int(total_cost / 2200 * 5000),
        estimated_impressions=int(total_cost / 50 * 1000),
        total_cost=round(total_cost),
        timeline=[
            {"phase": "需求确认", "duration": "1-2 天", "note": "确认品牌需求、目标受众、预算分配"},
            {"phase": "方案细化", "duration": "2-3 天", "note": "结合 MCP 工具数据细化点位选择"},
            {"phase": "合同签署", "duration": "1-2 天", "note": "商务流程"},
            {"phase": "素材准备", "duration": "3-5 天", "note": "创意设计、素材制作"},
            {"phase": "上线投放", "duration": "持续", "note": "按计划执行，每周提供数据报告"},
        ]
    )

@router.post("/cpm/track", response_model=CpmTrackResponse)
async def cpm_track(req: CpmTrackRequest):
    """
    CPM 追踪接口
    查询投放计划的曝光、点击、CPM 等数据
    """
    # 模拟数据（实际应查询数据库）
    import random
    impressions = random.randint(50000, 500000)
    clicks = int(impressions * random.uniform(0.005, 0.02))
    ctr = clicks / impressions
    cpm = round(random.uniform(20, 80), 2)

    return CpmTrackResponse(
        campaign_id=req.campaign_id,
        date=req.date or datetime.now().strftime("%Y-%m-%d"),
        impressions=impressions,
        clicks=clicks,
        ctr=round(ctr, 6),
        cpm=cpm,
        details=[
            {"date": req.date or datetime.now().strftime("%Y-%m-%d"),
             "impressions": impressions,
             "clicks": clicks,
             "spend": round(impressions / 1000 * cpm, 2)}
        ]
    )

@router.post("/cpm/compare", response_model=CpmCompareResponse)
async def cpm_compare(req: CpmCompareRequest):
    """
    CPM 对比接口
    对比多个投放计划的 CPM、CTR 等指标
    """
    campaigns = []
    for cid in req.campaigns:
        # 模拟数据
        campaigns.append({
            "campaign_id": cid,
            "impressions": 250000,
            "clicks": 3000,
            "ctr": 0.012,
            "cpm": 45.5,
            "roi": 3.2
        })

    summary = f"对比了 {len(req.campaigns)} 个投放计划，" \
              f"平均 CPM {sum(c['cpm'] for c in campaigns) / len(campaigns):.1f} 元，" \
              f"平均 CTR {sum(c['ctr'] for c in campaigns) / len(campaigns) * 100:.2f}%。"

    return CpmCompareResponse(campaigns=campaigns, summary=summary)

@router.post("/query/points")
async def query_points(req: QueryPointsRequest):
    """
    自然语言点位查询
    将自然语言查询转换为 MCP 工具调用
    """
    results = []

    # 简单关键词路由（实际可用 LLM Function Calling）
    msg = req.query.lower()

    if "门禁" in msg or "单元门" in msg:
        params = {"city": req.city or "广州", "limit": 10}
        result = call_mcp_tool("pdooh_query_access_points", params)
        results.append({"type": "access_points", "data": result})

    if "智能屏" in msg or "屏幕" in msg:
        params = {"city": req.city or "广州", "limit": 10}
        result = call_mcp_tool("pdooh_query_screens", params)
        results.append({"type": "screens", "data": result})

    if "道闸" in msg:
        params = {"city": req.city or "广州", "limit": 10}
        result = call_mcp_tool("pdooh_query_gates", params)
        results.append({"type": "gates", "data": result})

    if "led" in msg or "商场" in msg:
        params = {"city": req.city or "广州", "limit": 10}
        result = call_mcp_tool("pdooh_query_led", params)
        results.append({"type": "led", "data": result})

    if not results:
        # 默认查询门禁
        params = {"city": req.city or "广州", "limit": 5}
        result = call_mcp_tool("pdooh_query_access_points", params)
        results.append({"type": "access_points (default)", "data": result})

    return {"query": req.query, "results": results}

@router.get("/tools")
async def list_tools():
    """列出 Tom Agent 可用的 MCP 工具"""
    return {
        "tools": [
            {"name": "pdooh_query_access_points", "desc": "查询门禁点位"},
            {"name": "pdooh_query_screens", "desc": "查询智能屏"},
            {"name": "pdooh_query_gates", "desc": "查询道闸"},
            {"name": "pdooh_query_led", "desc": "查询商场LED"},
            {"name": "pdooh_city_report", "desc": "城市资源统计"},
            {"name": "pdooh_create_plan", "desc": "创建投放计划"},
            {"name": "roi_calculate", "desc": "ROI计算"},
        ]
    }
