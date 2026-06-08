"""
pDOOH A2A MCP Server — AI-to-AI 投放接口
让外部 AI Agent 能直接调用 pDOOH 投放能力（MCP 协议）
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.services.knowledge_base import auto_store_mcp_result

router = APIRouter(prefix="/api/v2/mcp/pdooh", tags=["pDOOH A2A MCP"])

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# MCP Protocol: tools/list
# ─────────────────────────────────────────────

class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: dict[str, Any]


# pDOOH 对外暴露的 8 个 MCP Tools
PDOOH_MCP_TOOLS = [
    {
        "name": "pdooh_query_screens",
        "description": "查询符合条件的智能屏（支持地理位置/人群标签/社区属性筛选）。"
                       "返回屏ID、地址、经纬度、覆盖人群画像。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市，如'广州'"},
                "district": {"type": "string", "description": "区县，如'天河区'"},
                "lat": {"type": "number", "description": "纬度（与 radius 配合使用）"},
                "lng": {"type": "number", "description": "经度（与 radius 配合使用）"},
                "radius": {"type": "number", "description": "搜索半径（米），默认 3000"},
                "tags": {"type": "array", "items": {"type": "string"},
                           "description": "人群标签，如 ['高端白酒','母婴']"},
                "min_house_price": {"type": "number", "description": "最低房价（万），筛选高净值社区"},
                "limit": {"type": "integer", "description": "返回数量上限，默认 20"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_get_screen_audience",
        "description": "获取指定屏的人群画像（人口属性/消费偏好/社区属性），"
                       "用于评估投放匹配度。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "screen_id": {"type": "integer", "description": "屏 ID"},
            },
            "required": ["screen_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_create_campaign",
        "description": "创建 pDOOH 投放计划。AI Agent 可自主调用此工具完成投放下单。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "投放计划名称"},
                "screen_ids": {"type": "array", "items": {"type": "integer"},
                                 "description": "屏 ID 列表"},
                "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
                "budget": {"type": "number", "description": "总预算（元）"},
                "creative_text": {"type": "string", "description": "广告文案（将自动送合规审核）"},
                "ai_generated": {"type": "boolean",
                                 "description": "是否由 AI 生成创意，默认 false"},
            },
            "required": ["name", "screen_ids", "start_date", "end_date", "budget"],
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_campaigns",
        "description": "查询投放计划列表，支持按状态筛选。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string",
                           "enum": ["draft", "reviewing", "approved", "running", "finished"],
                           "description": "计划状态"},
                "limit": {"type": "integer", "default": 20},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_submit_creative",
        "description": "提交广告创意（AIGC 生成或人工上传），自动触发合规审核。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "投放计划 ID"},
                "creative_type": {"type": "string",
                                 "enum": ["image", "video", "text", "aigc"],
                                 "description": "创意类型"},
                "creative_url": {"type": "string", "description": "创意素材 URL（非 AIGC 时必填）"},
                "ai_prompt": {"type": "string",
                              "description": "AIGC 生成提示词（creative_type=aigc 时必填）"},
            },
            "required": ["campaign_id", "creative_type"],
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_report",
        "description": "查询投放报告（曝光量/开门转化率/ROI 模拟），"
                       "支持按屏/按计划维度查询。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "投放计划 ID"},
                "screen_id": {"type": "integer", "description": "单独查询某屏的数据"},
                "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_compliance_check",
        "description": "广告内容合规预审（AI 自动审核）。"
                       "检查医疗/金融/药品等受限品类，返回是否通过及原因。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "广告文案或图片描述"},
                "industry": {"type": "string",
                             "description": "行业，如'医疗'/'金融'/'白酒'"},
            },
            "required": ["content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_audience_insight",
        "description": "AI 人群洞察：输入产品或品牌描述，"
                       "自动匹配最合适的人群标签和推荐屏列表。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_desc": {"type": "string",
                                "description": "产品/品牌描述，如'高端白酒，目标高净值人群'"},
                "target_city": {"type": "string", "description": "目标城市"},
                "budget_hint": {"type": "number", "description": "预算提示（元）"},
            },
            "required": ["product_desc"],
            "additionalProperties": False,
        },
    },
]


@router.get("/tools/list")
async def mcp_tools_list():
    """MCP protocol: 列出所有可用 Tools"""
    return {"tools": PDOOH_MCP_TOOLS}


# ─────────────────────────────────────────────
# MCP Protocol: tools/call
# ─────────────────────────────────────────────

class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any]


# 模拟数据库 — 生产环境改为真实 pdooh 库连接
MOCK_SCREENS = [
    {"id": 1, "name": "天河城社区门禁屏", "city": "广州", "district": "天河区",
     "lat": 23.1291, "lng": 113.3642, "house_price": 8,
     "tags": ["高端白酒", "母婴", "美妆"], "impressions_per_day": 3200},
    {"id": 2, "name": "猎德花园广告屏", "city": "广州", "district": "天河区",
     "lat": 23.1189, "lng": 113.3258, "house_price": 12,
     "tags": ["高端白酒", "农产品", "网红爆款"], "impressions_per_day": 5100},
    {"id": 3, "name": "番禺奥园入口屏", "city": "广州", "district": "番禺区",
     "lat": 22.9317, "lng": 113.3644, "house_price": 4,
     "tags": ["母婴", "美妆"], "impressions_per_day": 1800},
]

MOCK_CAMPAIGNS: list[dict] = []


@router.post("/tools/call")
async def mcp_tools_call(body: ToolCallRequest, request: Request):
    """
    MCP protocol: 执行 Tool 调用
    AI Agent 通过此接口调用 pDOOH 能力
    每次调用结果自动归档到知识库（data/knowledge/）
    """
    tool_name = body.name
    args = body.arguments

    logger.info(f"[A2A MCP] Tool调用: {tool_name}, args={args}")

    result = None

    try:

    # ── Tool 1: 查询屏 ──
    if tool_name == "pdooh_query_screens":
        results = MOCK_SCREENS.copy()
        if args.get("city"):
            results = [s for s in results if s["city"] == args["city"]]
        if args.get("district"):
            results = [s for s in results if s["district"] == args["district"]]
        if args.get("min_house_price"):
            results = [s for s in results
                       if s.get("house_price", 0) >= args["min_house_price"]]
        if args.get("tags"):
            results = [s for s in results
                       if any(t in s.get("tags", []) for t in args["tags"])]
        limit = args.get("limit", 20)
        result = {"content": [{"type": "text",
                               "text": json.dumps(results[:limit], ensure_ascii=False)}]}

    # ── Tool 2: 获取屏人群画像 ──
    elif tool_name == "pdooh_get_screen_audience":
        screen_id = args["screen_id"]
        screen = next((s for s in MOCK_SCREENS if s["id"] == screen_id), None)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
        audience = {
            "screen_id": screen_id,
            "screen_name": screen["name"],
            "demographics": {
                "age_25_35": "45%", "age_35_45": "38%",
                "gender_female": "62%", "education_bachelor+": "71%",
            },
            "consumption": {
                "high_end_liquor": "68%", "makeup": "55%",
                "mother_baby": "42%" if "母婴" in screen.get("tags", []) else "18%",
            },
            "community": {
                "avg_house_price_wan": screen.get("house_price", 5) * 10000,
                "households": 1200, "door_open_per_day": 3200,
            },
            "recommendation": "该屏人群与高端白酒高度匹配，建议投放"
        }
        result = {"content": [{"type": "text",
                               "text": json.dumps(audience, ensure_ascii=False)}]}

    # ── Tool 3: 创建投放计划 ──
    elif tool_name == "pdooh_create_campaign":
        campaign_id = len(MOCK_CAMPAIGNS) + 1
        new_campaign = {
            "id": campaign_id, "name": args["name"],
            "screen_ids": args["screen_ids"],
            "start_date": args["start_date"], "end_date": args["end_date"],
            "budget": args["budget"], "status": "draft",
            "creative_text": args.get("creative_text", ""),
            "ai_generated": args.get("ai_generated", False),
            "created_at": "2026-05-28T00:00:00",
        }
        MOCK_CAMPAIGNS.append(new_campaign)
        logger.info(f"[A2A] 投放计划已创建: id={campaign_id}, name={args['name']}")
        result = {"content": [{"type": "text",
                               "text": json.dumps(
                                   {"campaign_id": campaign_id, "status": "draft",
                                    "message": "投放计划已创建，请提交创意素材后送审"},
                                   ensure_ascii=False)}]}

    # ── Tool 4: 查询投放计划 ──
    elif tool_name == "pdooh_query_campaigns":
        results = MOCK_CAMPAIGNS.copy()
        if args.get("status"):
            results = [c for c in results if c["status"] == args["status"]]
        result = {"content": [{"type": "text",
                               "text": json.dumps(results, ensure_ascii=False)}]}

    # ── Tool 5: 提交创意 ──
    elif tool_name == "pdooh_submit_creative":
        campaign_id = args["campaign_id"]
        campaign = next((c for c in MOCK_CAMPAIGNS
                         if c["id"] == campaign_id), None)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        review_result = {
            "campaign_id": campaign_id,
            "creative_status": "under_review",
            "estimated_review_time_hours": 2,
            "message": "创意已提交，预计 2 小时内完成合规审核"
        }
        result = {"content": [{"type": "text",
                               "text": json.dumps(review_result, ensure_ascii=False)}]}

    # ── Tool 6: 查询报告 ──
    elif tool_name == "pdooh_query_report":
        report = {
            "campaign_id": args.get("campaign_id"),
            "period": f"{args.get('start_date', 'N/A')} ~ {args.get('end_date', 'N/A')}",
            "metrics": {
                "impressions": 126800, "door_open_conversions": 3840,
                "ctr": "3.03%", "estimated_roi": "1:4.2",
                "top_screen": "猎德花园广告屏（转化率最高）",
            },
            "note": "报告数据为模拟值，真实数据需接入XX开门行动数据"
        }
        result = {"content": [{"type": "text",
                               "text": json.dumps(report, ensure_ascii=False)}]}

    # ── Tool 7: 合规预审 ──
    elif tool_name == "pdooh_compliance_check":
        content = args.get("content", "")
        industry = args.get("industry", "")
        blocked_keywords = {
            "医疗": ["治愈", "疗效", "第一"],
            "金融": ["保本", "无风险", "稳赚"],
            "白酒": [],
        }
        issues = []
        for ind, kws in blocked_keywords.items():
            if ind in industry or ind in content:
                for kw in kws:
                    if kw in content:
                        issues.append(f"[{ind}] 禁用词：「{kw}」")
        passed = len(issues) == 0
        compliance_result = {
            "passed": passed, "issues": issues,
            "suggestion": "修改后重新提交" if not passed else "可以投放",
            "reviewer": "AI-Compliance-v1.0",
        }
        result = {"content": [{"type": "text",
                               "text": json.dumps(compliance_result, ensure_ascii=False)}]}

    # ── Tool 8: AI 人群洞察 ──
    elif tool_name == "pdooh_audience_insight":
        product_desc = args.get("product_desc", "")
        target_city = args.get("target_city", "广州")
        insight = {
            "product_desc": product_desc, "target_city": target_city,
            "matched_tags": [], "recommended_screens": [], "budget_suggestion": "",
        }
        if "白酒" in product_desc:
            insight["matched_tags"] = ["高端白酒", "高净值人群"]
            insight["recommended_screens"] = [
                s for s in MOCK_SCREENS if s.get("house_price", 0) >= 8]
            insight["budget_suggestion"] = "建议预算 ≥ 5万/月，聚焦房价>8万社区"
        elif "母婴" in product_desc:
            insight["matched_tags"] = ["母婴", "美妆"]
            insight["recommended_screens"] = [
                s for s in MOCK_SCREENS if "母婴" in s.get("tags", [])]
            insight["budget_suggestion"] = "建议预算 ≥ 3万/月，聚焦年轻家庭社区"
        else:
            insight["recommended_screens"] = MOCK_SCREENS
            insight["budget_suggestion"] = "建议预算 ≥ 2万/月"
        insight["summary"] = (
            f"「{product_desc}」目标人群与 "
            f"{len(insight['recommended_screens'])} 块屏匹配，"
            f"{insight['budget_suggestion']}"
        )
        result = {"content": [{"type": "text",
                               "text": json.dumps(insight, ensure_ascii=False)}]}

    else:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    # 📚 自动归档到知识库（每次 MCP 调用结果）
    try:
        client_ip = request.client.host if request.client else ""
        user_agent = request.headers.get("user-agent", "")
        kb_info = auto_store_mcp_result(
            tool_name=tool_name,
            arguments=args,
            result=result,
            source="mcp_call",
            ip=client_ip,
            user_agent=user_agent,
        )
        logger.info(f"[Knowledge Base] 已归档: {kb_info}")
    except Exception as e:
        logger.warning(f"[Knowledge Base] 归档失败: {e}")

    return result


# ─────────────────────────────────────────────
# Skill 调用模块（WorkBuddy Skill 封装）
# ─────────────────────────────────────────────

SKILL_YAML = """
name: pdooh-agent
description: >
  pDOOH AI原生投放平台 Skill。
  让 AI Agent 能直接调用 pDOOH 投放能力（查询屏、创建计划、合规审核、效果报告）。
  参考XX科技5V数据模型，支持人群洞察和智能选点。

triggers:
  - "pDOOH"
  - "户外广告投放"
  - "社区屏"
  - "XX科技"
  - "程序化户外"
  - "audience insight"
  - "投放计划"

tools:
  - pdooh_query_screens
  - pdooh_get_screen_audience
  - pdooh_create_campaign
  - pdooh_query_campaigns
  - pdooh_submit_creative
  - pdooh_query_report
  - pdooh_compliance_check
  - pdooh_audience_insight

examples:
  - query: "帮我在广州天河区找房价>8万的社区屏，投放高端白酒广告"
    tool: pdooh_audience_insight
    args:
      product_desc: "高端白酒，目标高净值人群"
      target_city: "广州"
      budget_hint: 50000

  - query: "创建一个投放计划，在天河城社区屏投放，预算3万，时间下周一至周五"
    tool: pdooh_create_campaign
    args:
      name: "高端白酒-天河城-周投"
      screen_ids: [1]
      start_date: "2026-06-02"
      end_date: "2026-06-06"
      budget: 30000
      creative_text: "品味传世，高端白酒限时品鉴"

  - query: "检查这个广告文案是否能过审：治愈你的失眠"
    tool: pdooh_compliance_check
    args:
      content: "治愈你的失眠"
      industry: "医疗"

mcp_endpoint: "/api/v2/mcp/pdooh/tools/call"
""".strip()


@router.get("/skill.yaml")
async def get_skill_yaml():
    """返回 WorkBuddy Skill 定义文件"""
    return Response(content=SKILL_YAML, media_type="text/yaml")


# ─────────────────────────────────────────────
# 健康检查
# ─────────────────────────────────────────────

@router.get("/health")
async def health():
    return {
        "service": "pDOOH A2A MCP Server",
        "status": "ok",
        "tools_count": len(PDOOH_MCP_TOOLS),
        "mcp_endpoint": "/api/v2/mcp/pdooh/tools/call",
        "skill_endpoint": "/api/v2/mcp/pdooh/skill.yaml",
        "reference": "XX科技5V数据模型",
    }


"""
路由注册说明：
在 main.py 中添加：
    from app.pdooh_mcp import router as pdooh_mcp_router
    app.include_router(pdooh_mcp_router)

MCP 调用示例（AI Agent）：
    POST /api/v2/mcp/pdooh/tools/call
    {
      "name": "pdooh_audience_insight",
      "arguments": {
        "product_desc": "高端白酒，目标高净值人群",
        "target_city": "广州"
      }
    }
"""
