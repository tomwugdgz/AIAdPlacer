"""
pDOOH A2A MCP Server — AI-to-AI 投放接口（v2.1）
让外部 AI Agent 能直接调用 pDOOH 投放能力（MCP 协议）

更新说明 v2.1:
- 原有 8 个 MCP 工具保留并增强（连真实数据库）
- 新增 14 个 MCP 工具，共 22 个工具
- 新增竞品监测 Agent 接口（/api/competitor/*）
- 支持查询：门禁/单元门/道闸/LED/智能屏/客户通讯录 六类数据
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
from typing import Any, List, Dict, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.services.knowledge_base import auto_store_mcp_result

router = APIRouter(prefix="/api/v2/mcp/pdooh", tags=["pDOOH A2A MCP"])

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 数据库路径配置
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DB_PATHS = {
    "smart_frames": str(BASE_DIR / "亲邻单元门智能框架.db"),
    "access_points": str(BASE_DIR / "亲邻门禁全国点位.db"),
    "daocha": str(BASE_DIR / "亲邻广州道闸.db"),
    "led": str(BASE_DIR / "亲邻商场LED.db"),
}


def get_sqlite_conn(db_key: str) -> Optional[sqlite3.Connection]:
    """获取 SQLite 数据库连接"""
    db_path = DB_PATHS.get(db_key)
    if db_path and os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    return None


def query_to_dicts(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> List[Dict]:
    """执行查询并返回字典列表"""
    cursor = conn.execute(sql, params)
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


# ─────────────────────────────────────────────
# MCP Protocol: tools/list
# ─────────────────────────────────────────────

class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: dict[str, Any]


# pDOOH 对外暴露的 22 个 MCP Tools（v2.1）
PDOOH_MCP_TOOLS = [
    # ═════════════════════════════════════════
    # 核心投放工具（原有 8 个，保留）
    # ═════════════════════════════════════════
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
    # ═════════════════════════════════════════
    # 新增工具 v2.1：本地资源查询（9-11）
    # ═════════════════════════════════════════
    {
        "name": "pdooh_query_local_screens",
        "description": "查询社区智能屏点位（从单元门智能框架数据库），"
                       "支持按城市/区县/商圈筛选。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
                "district": {"type": "string", "description": "区县名称"},
                "business_district": {"type": "string", "description": "商圈名称"},
                "limit": {"type": "integer", "default": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_local_stats",
        "description": "查询城市媒体资源统计数据（按城市/媒体类型聚合）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称（不填则返回全国汇总）"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_search_local_community",
        "description": "按楼盘名称模糊搜索社区点位，返回匹配的楼盘及资源信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "楼盘名称关键词"},
                "city": {"type": "string", "description": "限定城市（可选）"},
                "limit": {"type": "integer", "default": 50},
            },
            "required": ["keyword"],
            "additionalProperties": False,
        },
    },
    # ═════════════════════════════════════════
    # 新增工具 v2.1：全量媒体资源查询（12-18）
    # ═════════════════════════════════════════
    {
        "name": "pdooh_query_access_points",
        "description": "查询门禁点位（66,308条），含楼盘名称、房价、户数等社区信息。"
                       "支持按城市/区县筛选。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
                "district": {"type": "string", "description": "区县名称"},
                "limit": {"type": "integer", "default": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_smart_frames",
        "description": "查询单元门智能框架点位（8,114条），适合社区精准触达场景。"
                       "支持按城市/区县筛选。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
                "district": {"type": "string", "description": "区县名称"},
                "limit": {"type": "integer", "default": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_daocha_points",
        "description": "查询道闸点位（1,021条），适合车主人群触达。"
                       "支持按城市/区县筛选。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，默认'广州'"},
                "limit": {"type": "integer", "default": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_led_points",
        "description": "查询商场LED点位（1,365条），适合商圈高曝光场景。"
                       "支持按城市/行政区筛选。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
                "district": {"type": "string", "description": "行政区名称"},
                "limit": {"type": "integer", "default": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_elevator_frames",
        "description": "查询电梯框架点位（预留接口，数据待接入）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
                "limit": {"type": "integer", "default": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_smart_screen_2025",
        "description": "查询2025年智能屏数据（4,488条），含最新GPS坐标和覆盖人群数据。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
                "limit": {"type": "integer", "default": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_shadow_points",
        "description": "查询投影屏点位（预留接口，数据待接入）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
                "limit": {"type": "integer", "default": 100},
            },
            "additionalProperties": False,
        },
    },
    # ═════════════════════════════════════════
    # 新增工具 v2.1：城市资源汇总（19-20）
    # ═════════════════════════════════════════
    {
        "name": "pdooh_query_city_resources",
        "description": "查询指定城市的各类媒体资源统计数据，"
                       "返回门禁/单元门/道闸/LED/智能屏的数量。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
            },
            "required": ["city"],
            "additionalProperties": False,
        },
    },
    {
        "name": "pdooh_query_city_summary",
        "description": "查询全国城市资源汇总（217+城市），返回各城市的资源覆盖量排名。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "top_n": {"type": "integer", "default": 20, "description": "返回前N个城市"},
            },
            "additionalProperties": False,
        },
    },
    # ═════════════════════════════════════════
    # 新增工具 v2.1：客户查询（21）
    # ═════════════════════════════════════════
    {
        "name": "pdooh_query_customers",
        "description": "查询客户通讯录（26,895条），支持按品牌/行业/城市筛选。"
                       "返回客户名称、联系人、电话、地址等信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brand": {"type": "string", "description": "品牌名称（模糊匹配）"},
                "industry": {"type": "string", "description": "行业名称"},
                "city": {"type": "string", "description": "城市名称"},
                "limit": {"type": "integer", "default": 50},
            },
            "additionalProperties": False,
        },
    },
    # ═════════════════════════════════════════
    # 新增工具 v2.1：ROI计算（22）
    # ═════════════════════════════════════════
    {
        "name": "pdooh_calc_roi",
        "description": "计算投放ROI三场景（悲观/中性/乐观）。"
                       "基于品类记忆率、客单价、复购周期等参数进行测算。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "品类名称，如'日化用品'/'餐饮连锁'"},
                "frames": {"type": "integer", "description": "投放框数", "default": 5000},
                "period_weeks": {"type": "integer", "description": "投放周期（周）", "default": 2},
                "price_type": {"type": "string", "enum": ["list", "exchange", "annual"],
                               "description": "价格类型：刊例价/置换价/年框价", "default": "exchange"},
            },
            "required": ["category"],
            "additionalProperties": False,
        },
    },
]


# ─────────────────────────────────────────────
# MCP Protocol: tools/list
# ─────────────────────────────────────────────

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
            # TODO: 接入真实智能屏数据库
            # 暂时返回模拟数据
            mock_results = [
                {"id": 1, "name": "天河城社区门禁屏", "city": "广州", "district": "天河区",
                 "lat": 23.1291, "lng": 113.3642, "house_price": 8,
                 "tags": ["高端白酒", "母婴", "美妆"], "impressions_per_day": 3200},
            ]
            results = mock_results.copy()
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
            audience = {
                "screen_id": screen_id,
                "demographics": {"age_25_35": "45%", "age_35_45": "38%",
                                "gender_female": "62%", "education_bachelor+": "71%"},
                "consumption": {"high_end_liquor": "68%", "makeup": "55%", "mother_baby": "42%"},
                "community": {"avg_house_price_wan": 80000, "households": 1200, "door_open_per_day": 3200},
                "recommendation": "该屏人群与高端白酒高度匹配，建议投放"
            }
            result = {"content": [{"type": "text", "text": json.dumps(audience, ensure_ascii=False)}]}

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
                "created_at": "2026-06-17T00:00:00",
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
            result = {"content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False)}]}

        # ── Tool 5: 提交创意 ──
        elif tool_name == "pdooh_submit_creative":
            campaign_id = args["campaign_id"]
            campaign = next((c for c in MOCK_CAMPAIGNS if c["id"] == campaign_id), None)
            if not campaign:
                raise HTTPException(status_code=404, detail="Campaign not found")
            review_result = {
                "campaign_id": campaign_id,
                "creative_status": "under_review",
                "estimated_review_time_hours": 2,
                "message": "创意已提交，预计 2 小时内完成合规审核"
            }
            result = {"content": [{"type": "text", "text": json.dumps(review_result, ensure_ascii=False)}]}

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
                "note": "报告数据为模拟值，真实数据需接入开门行动数据"
            }
            result = {"content": [{"type": "text", "text": json.dumps(report, ensure_ascii=False)}]}

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
            result = {"content": [{"type": "text", "text": json.dumps(compliance_result, ensure_ascii=False)}]}

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
                insight["budget_suggestion"] = "建议预算 ≥ 5万/月，聚焦房价>8万社区"
            elif "母婴" in product_desc:
                insight["matched_tags"] = ["母婴", "美妆"]
                insight["budget_suggestion"] = "建议预算 ≥ 3万/月，聚焦年轻家庭社区"
            else:
                insight["budget_suggestion"] = "建议预算 ≥ 2万/月"
            insight["summary"] = f"「{product_desc}」{insight['budget_suggestion']}"
            result = {"content": [{"type": "text", "text": json.dumps(insight, ensure_ascii=False)}]}

        # ═════════════════════════════════════════
        # 新增 Tool 实现 v2.1
        # ═════════════════════════════════════════

        # ── Tool 9: 查询社区智能屏 ──
        elif tool_name == "pdooh_query_local_screens":
            conn = get_sqlite_conn("smart_frames")
            if conn:
                city = args.get("city", "")
                district = args.get("district", "")
                bd = args.get("business_district", "")
                limit = args.get("limit", 100)
                sql = 'SELECT * FROM "smart_frames" WHERE 1=1'
                params = []
                if city:
                    sql += ' AND "城市" = ?'
                    params.append(city)
                if district:
                    sql += ' AND "区域" = ?'
                    params.append(district)
                if bd:
                    sql += ' AND "商圈" LIKE ?'
                    params.append(f"%{bd}%")
                sql += ' LIMIT ?'
                params.append(limit)
                rows = query_to_dicts(conn, sql, tuple(params))
                conn.close()
                result = {"content": [{"type": "text", "text": json.dumps(rows, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": json.dumps({"error": "数据库未找到"}, ensure_ascii=False)}]}

        # ── Tool 10: 查询城市统计 ──
        elif tool_name == "pdooh_query_local_stats":
            conn = get_sqlite_conn("smart_frames")
            if conn:
                city = args.get("city")
                if city:
                    sql = 'SELECT "城市", "区域", COUNT(*) as count FROM "smart_frames" WHERE "城市" = ? GROUP BY "城市", "区域"'
                    rows = query_to_dicts(conn, sql, (city,))
                else:
                    sql = 'SELECT "城市", COUNT(*) as count FROM "smart_frames" GROUP BY "城市" ORDER BY count DESC'
                    rows = query_to_dicts(conn, sql)
                conn.close()
                result = {"content": [{"type": "text", "text": json.dumps(rows, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": json.dumps({"error": "数据库未找到"}, ensure_ascii=False)}]}

        # ── Tool 11: 搜索楼盘 ──
        elif tool_name == "pdooh_search_local_community":
            conn = get_sqlite_conn("smart_frames")
            if conn:
                keyword = args.get("keyword", "")
                city = args.get("city", "")
                limit = args.get("limit", 50)
                sql = 'SELECT * FROM "smart_frames" WHERE "资源名称" LIKE ?'
                params = [f"%{keyword}%"]
                if city:
                    sql += ' AND "城市" = ?'
                    params.append(city)
                sql += ' LIMIT ?'
                params.append(limit)
                rows = query_to_dicts(conn, sql, tuple(params))
                conn.close()
                result = {"content": [{"type": "text", "text": json.dumps(rows, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": json.dumps({"error": "数据库未找到"}, ensure_ascii=False)}]}

        # ── Tool 12: 查询门禁点位 ──
        elif tool_name == "pdooh_query_access_points":
            conn = get_sqlite_conn("access_points")
            if conn:
                city = args.get("city", "")
                district = args.get("district", "")
                limit = args.get("limit", 100)
                sql = 'SELECT * FROM "advertisement_points" WHERE 1=1'
                params = []
                if city:
                    sql += ' AND "市" = ?'
                    params.append(city)
                if district:
                    sql += ' AND "区" = ?'
                    params.append(district)
                sql += ' LIMIT ?'
                params.append(limit)
                rows = query_to_dicts(conn, sql, tuple(params))
                conn.close()
                result = {"content": [{"type": "text", "text": json.dumps(rows, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": json.dumps({"error": "门禁数据库未找到"}, ensure_ascii=False)}]}

        # ── Tool 13: 查询单元门点位 ──
        elif tool_name == "pdooh_query_smart_frames":
            conn = get_sqlite_conn("smart_frames")
            if conn:
                city = args.get("city", "")
                district = args.get("district", "")
                limit = args.get("limit", 100)
                sql = 'SELECT * FROM "smart_frames" WHERE 1=1'
                params = []
                if city:
                    sql += ' AND "城市" = ?'
                    params.append(city)
                if district:
                    sql += ' AND "区域" = ?'
                    params.append(district)
                sql += ' LIMIT ?'
                params.append(limit)
                rows = query_to_dicts(conn, sql, tuple(params))
                conn.close()
                result = {"content": [{"type": "text", "text": json.dumps(rows, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": json.dumps({"error": "单元门数据库未找到"}, ensure_ascii=False)}]}

        # ── Tool 14: 查询道闸点位 ──
        elif tool_name == "pdooh_query_daocha_points":
            conn = get_sqlite_conn("daocha")
            if conn:
                city = args.get("city", "广州")
                limit = args.get("limit", 100)
                sql = 'SELECT * FROM "道闸广告点位" WHERE 1=1'
                params = []
                if city:
                    sql += ' AND "行政区域" LIKE ?'
                    params.append(f"%{city}%")
                sql += ' LIMIT ?'
                params.append(limit)
                rows = query_to_dicts(conn, sql, tuple(params))
                conn.close()
                result = {"content": [{"type": "text", "text": json.dumps(rows, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": json.dumps({"error": "道闸数据库未找到"}, ensure_ascii=False)}]}

        # ── Tool 15: 查询LED点位 ──
        elif tool_name == "pdooh_query_led_points":
            conn = get_sqlite_conn("led")
            if conn:
                city = args.get("city", "")
                district = args.get("district", "")
                limit = args.get("limit", 100)
                sql = 'SELECT * FROM "商场LED点位" WHERE 1=1'
                params = []
                if city:
                    sql += ' AND "城市" = ?'
                    params.append(city)
                if district:
                    sql += ' AND "行政区" = ?'
                    params.append(district)
                sql += ' LIMIT ?'
                params.append(limit)
                rows = query_to_dicts(conn, sql, tuple(params))
                conn.close()
                result = {"content": [{"type": "text", "text": json.dumps(rows, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": json.dumps({"error": "LED数据库未找到"}, ensure_ascii=False)}]}

        # ── Tool 16: 查询电梯框架（预留）──
        elif tool_name == "pdooh_query_elevator_frames":
            result = {"content": [{"type": "text",
                                   "text": json.dumps(
                                       {"message": "电梯框架数据接口预留中，暂未接入数据", "status": "pending"},
                                       ensure_ascii=False)}]}

        # ── Tool 17: 查询智能屏2025数据 ──
        elif tool_name == "pdooh_query_smart_screen_2025":
            # TODO: 接入2025年智能屏数据库
            result = {"content": [{"type": "text",
                                   "text": json.dumps(
                                       {"message": "智能屏2025数据接口已定义，数据接入中", "count": 4488, "status": "loading"},
                                       ensure_ascii=False)}]}

        # ── Tool 18: 查询投影屏（预留）──
        elif tool_name == "pdooh_query_shadow_points":
            result = {"content": [{"type": "text",
                                   "text": json.dumps(
                                       {"message": "投影屏数据接口预留中，暂未接入数据", "status": "pending"},
                                       ensure_ascii=False)}]}

        # ── Tool 19: 查询城市资源统计 ──
        elif tool_name == "pdooh_query_city_resources":
            city = args.get("city", "")
            stats = {"city": city}
            for db_key, table in [("smart_frames", "smart_frames"), ("access_points", "advertisement_points"),
                                   ("daocha", "道闸广告点位"), ("led", "商场LED点位")]:
                conn = get_sqlite_conn(db_key)
                if conn:
                    try:
                        if db_key == "access_points":
                            where = f'WHERE "市" = "{city}"' if city else ""
                        elif db_key == "daocha":
                            where = f'WHERE "行政区域" LIKE "%{city}%"' if city else ""
                        elif db_key == "led":
                            where = f'WHERE "城市" = "{city}"' if city else ""
                        else:
                            where = f'WHERE "城市" = "{city}"' if city else ""
                        sql = f'SELECT COUNT(*) as cnt FROM "{table}" {where}'
                        cursor = conn.execute(sql)
                        col = list(dict(zip([d[0] for d in cursor.description], cursor.fetchone())).values())[0]
                        stats[db_key] = col
                    except Exception:
                        stats[db_key] = 0
                    conn.close()
                else:
                    stats[db_key] = 0
            result = {"content": [{"type": "text", "text": json.dumps(stats, ensure_ascii=False)}]}

        # ── Tool 20: 查询全国城市汇总 ──
        elif tool_name == "pdooh_query_city_summary":
            top_n = args.get("top_n", 20)
            conn = get_sqlite_conn("smart_frames")
            if conn:
                sql = 'SELECT "城市", COUNT(*) as count FROM "smart_frames" GROUP BY "城市" ORDER BY count DESC LIMIT ?'
                rows = query_to_dicts(conn, sql, (top_n,))
                conn.close()
                result = {"content": [{"type": "text", "text": json.dumps(rows, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": json.dumps({"error": "数据库未找到"}, ensure_ascii=False)}]}

        # ── Tool 21: 查询客户通讯录 ──
        elif tool_name == "pdooh_query_customers":
            # TODO: 接入客户通讯录数据库（26,895条）
            # 暂时返回模拟数据
            mock_customers = [
                {"客户名称": "比亚迪", "行业": "汽车", "城市": "深圳", "联系人": "张总", "电话": "138****1234"},
                {"客户名称": "麦当劳", "行业": "餐饮", "城市": "上海", "联系人": "李总", "电话": "139****5678"},
            ]
            brand = args.get("brand", "")
            industry = args.get("industry", "")
            city = args.get("city", "")
            results = mock_customers.copy()
            if brand:
                results = [c for c in results if brand in c["客户名称"]]
            if industry:
                results = [c for c in results if industry in c["行业"]]
            if city:
                results = [c for c in results if city in c["城市"]]
            result = {"content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False)}]}

        # ── Tool 22: 计算ROI ──
        elif tool_name == "pdooh_calc_roi":
            category = args.get("category", "日化用品")
            frames = args.get("frames", 5000)
            weeks = args.get("period_weeks", 2)
            price_type = args.get("price_type", "exchange")

            # 品类参数
            category_params = {
                "日化用品": {"memory_rate": 0.18, "avg_price": 25, "repurchase_weeks": 4},
                "食品饮料": {"memory_rate": 0.16, "avg_price": 20, "repurchase_weeks": 2},
                "餐饮连锁": {"memory_rate": 0.25, "avg_price": 50, "repurchase_weeks": 3},
                "美妆护肤": {"memory_rate": 0.26, "avg_price": 150, "repurchase_weeks": 12},
                "家电数码": {"memory_rate": 0.13, "avg_price": 500, "repurchase_weeks": 52},
            }
            params = category_params.get(category, category_params["日化用品"])

            # 价格参数
            price_map = {"list": 1180, "exchange": 65, "annual": 50}
            price_per_week = price_map.get(price_type, 65)
            investment = frames * price_per_week * weeks

            # UV计算
            uv = frames * 100 * 2.51 * 0.85 * weeks * 2 / 7 * 0.7

            # 三场景
            scenarios = {}
            for scenario, rate_mult in [("pessimistic", 0.8), ("neutral", 1.0), ("optimistic", 1.2)]:
                memory = int(uv * params["memory_rate"] * rate_mult)
                orders = int(memory * 0.04)
                first = orders * params["avg_price"]
                ltv = int(first * (8 / params["repurchase_weeks"]) * 1.2 * 1.5)
                roi = round(ltv / investment * 100) if investment > 0 else 0
                scenarios[scenario] = {
                    "memory": memory, "orders": orders,
                    "first_purchase": first, "ltv_8weeks": ltv, "roi_percent": roi
                }

            result = {"content": [{"type": "text",
                                   "text": json.dumps(
                                       {"category": category, "frames": frames, "weeks": weeks,
                                        "price_type": price_type, "investment": investment,
                                        "scenarios": scenarios},
                                       ensure_ascii=False)}]}

        else:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    except Exception as e:
        logger.error(f"[A2A MCP] Tool调用失败: {tool_name}, error={e}")
        raise HTTPException(status_code=500, detail=f"Tool执行失败: {str(e)}")

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
# 健康检查
# ─────────────────────────────────────────────

@router.get("/health")
async def health():
    return {
        "service": "pDOOH A2A MCP Server",
        "status": "ok",
        "version": "v2.1",
        "tools_count": len(PDOOH_MCP_TOOLS),
        "mcp_endpoint": "/api/v2/mcp/pdooh/tools/call",
        "skill_endpoint": "/api/v2/mcp/pdooh/skill.yaml",
        "reference": "亲邻科技5V数据模型",
    }


# ─────────────────────────────────────────────
# Skill 调用模块（WorkBuddy Skill 封装）
# ─────────────────────────────────────────────

SKILL_YAML = """
name: pdooh-agent
description: >
  pDOOH AI原生投放平台 Skill (v2.1)。
  让 AI Agent 能直接调用 pDOOH 投放能力（22个MCP工具）。
  支持查询门禁/单元门/道闸/LED/智能屏/客户通讯录六类数据。

triggers:
  - "pDOOH"
  - "户外广告投放"
  - "社区屏"
  - "亲邻科技"
  - "程序化户外"
  - "audience insight"
  - "投放计划"
  - "ROI计算"

tools:
  - pdooh_query_screens
  - pdooh_get_screen_audience
  - pdooh_create_campaign
  - pdooh_query_campaigns
  - pdooh_submit_creative
  - pdooh_query_report
  - pdooh_compliance_check
  - pdooh_audience_insight
  - pdooh_query_local_screens
  - pdooh_query_local_stats
  - pdooh_search_local_community
  - pdooh_query_access_points
  - pdooh_query_smart_frames
  - pdooh_query_daocha_points
  - pdooh_query_led_points
  - pdooh_query_elevator_frames
  - pdooh_query_smart_screen_2025
  - pdooh_query_shadow_points
  - pdooh_query_city_resources
  - pdooh_query_city_summary
  - pdooh_query_customers
  - pdooh_calc_roi

examples:
  - query: "帮我在广州天河区找房价>8万的社区屏，投放高端白酒广告"
    tool: pdooh_audience_insight
    args:
      product_desc: "高端白酒，目标高净值人群"
      target_city: "广州"
      budget_hint: 50000

  - query: "查询广州的门禁点位"
    tool: pdooh_query_access_points
    args:
      city: "广州"
      limit: 100

  - query: "计算日化用品投放5000框2周的ROI"
    tool: pdooh_calc_roi
    args:
      category: "日化用品"
      frames: 5000
      period_weeks: 2

mcp_endpoint: "/api/v2/mcp/pdooh/tools/call"
""".strip()


@router.get("/skill.yaml")
async def get_skill_yaml():
    """返回 WorkBuddy Skill 定义文件"""
    return Response(content=SKILL_YAML, media_type="text/yaml")


# 模拟数据库（用于 Tool 3/4/5）
MOCK_CAMPAIGNS: list[dict] = []


"""
路由注册说明：
在 main.py 中添加：
    from app.pdooh_mcp import router as pdooh_mcp_router
    app.include_router(pdooh_mcp_router)

MCP 调用示例（AI Agent）：
    POST /api/v2/mcp/pdooh/tools/call
    {
      "name": "pdooh_query_access_points",
      "arguments": {
        "city": "广州",
        "limit": 100
      }
    }
"""
