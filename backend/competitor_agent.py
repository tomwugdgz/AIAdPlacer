"""
竞品监测 Agent (Competitor Intelligence Agent)

独立服务，端口 5005。
提供竞品数据库查询、竞品定价查询、市场情报查询等功能。

启动方式:
    python competitor_agent.py
    或
    uvicorn competitor_agent:app --host 0.0.0.0 --port 5005 --reload
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import uvicorn

# ── 导入公共模块 ────────────────────────────────────────────────────────────────
from app.common import (
    setup_logging,
    PDOOHError,
    ValidationError,
    cached,
    validate_params,
    generate_request_id,
    format_error_response,
)

# ─────────────────────────────────────────────
# 日志配置
# ─────────────────────────────────────────────

logger = setup_logging("competitor_agent", log_file="logs/competitor_agent.log")
logger.info("竞品监测 Agent 启动中...")

# ─────────────────────────────────────────────
# FastAPI 应用
# ─────────────────────────────────────────────

app = FastAPI(
    title="竞品监测 Agent",
    description="pDOOH 竞品情报监测系统",
    version="v2.1",
)

# ─────────────────────────────────────────────
# 数据库路径
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
# 竞品数据库（如有）
COMPETITOR_DB = BASE_DIR / "data" / "competitors.db"
# 市场情报数据库（如有）
INTEL_DB = BASE_DIR / "data" / "market_intelligence.db"

# ─────────────────────────────────────────────
# 模拟数据（生产环境应接入真实数据源）
# ─────────────────────────────────────────────

MOCK_COMPETITORS = {
    "汽车": [
        {"name": "比亚迪", "category": "新能源汽车", "market_share": "32%", "recent_campaign": "宋PLUS DM-i社区投放"},
        {"name": "特斯拉", "category": "新能源汽车", "market_share": "18%", "recent_campaign": "Model Y城市商圈投放"},
        {"name": "小鹏汽车", "category": "新能源汽车", "market_share": "8%", "recent_campaign": "智能驾驶社区体验"},
    ],
    "餐饮": [
        {"name": "麦当劳", "category": "快餐", "market_share": "28%", "recent_campaign": "早餐套餐社区推广"},
        {"name": "肯德基", "category": "快餐", "market_share": "25%", "recent_campaign": "新品汉堡社区试吃"},
        {"name": "瑞幸咖啡", "category": "咖啡", "market_share": "35%", "recent_campaign": "9.9元咖啡社区渗透"},
    ],
    "日化": [
        {"name": "宝洁", "category": "日化", "market_share": "22%", "recent_campaign": "海飞丝社区洗发体验"},
        {"name": "联合利华", "category": "日化", "market_share": "18%", "recent_campaign": "奥妙洗衣液社区派样"},
    ],
}

MOCK_PRICING = [
    {"media": "单元门智能框架", "our_price": "65元/周", "competitor_avg": "80-120元/周", "advantage": "置换价优势明显"},
    {"media": "广告门", "our_price": "500元/周", "competitor_avg": "600-900元/周", "advantage": "有优势"},
    {"media": "智能屏", "our_price": "2元/周", "competitor_avg": "5-10元/周", "advantage": "显著优势"},
]

MOCK_INTELLIGENCE = [
    {
        "id": 1, "industry": "汽车", "brand": "比亚迪",
        "event": "启动社区电梯广告投放", "date": "2026-06-10",
        "details": "比亚迪在广州天河区200个社区投放宋PLUS DM-i广告，聚焦新能源车主社区",
        "source": "广告门", "impact": "high"
    },
    {
        "id": 2, "industry": "餐饮", "brand": "麦当劳",
        "event": "推出社区早餐配送服务", "date": "2026-06-08",
        "details": "麦当劳在北京、上海试点社区早餐配送，覆盖500个社区",
        "source": "公司内部情报", "impact": "medium"
    },
    {
        "id": 3, "industry": "日化", "brand": "宝洁",
        "event": "海飞丝社区派样活动", "date": "2026-06-05",
        "details": "宝洁在广州100个高端社区开展海飞丝免费派样，收集用户反馈",
        "source": "社区观察", "impact": "medium"
    },
    {
        "id": 4, "industry": "汽车", "brand": "小鹏汽车",
        "event": "智能驾驶社区体验活动", "date": "2026-06-03",
        "details": "小鹏在广州南沙社区开展智能驾驶体验，目标社区住户",
        "source": "活动观察", "impact": "low"
    },
]


# ─────────────────────────────────────────────
# 缓存装饰器（用于模拟数据）
# ─────────────────────────────────────────────

def get_cache_key(prefix: str, **kwargs) -> str:
    """
    生成缓存 key
    
    Args:
        prefix: 缓存前缀
        **kwargs: 参数字典
        
    Returns:
        str: 缓存 key
    """
    key_str = f"{prefix}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_str.encode()).hexdigest()


# 内存缓存（简单实现，生产环境应使用 Redis）
_cache: Dict[str, Any] = {}
_cache_times: Dict[str, float] = {}


def get_from_cache(key: str, ttl: int = 300) -> Optional[Any]:
    """
    从缓存获取数据
    
    Args:
        key: 缓存 key
        ttl: 缓存过期时间（秒），默认 300 秒（5 分钟）
        
    Returns:
        Optional[Any]: 缓存数据（如果未过期），否则 None
    """
    if key not in _cache:
        return None
    
    # 检查是否过期
    if time.time() - _cache_times[key] > ttl:
        del _cache[key]
        del _cache_times[key]
        return None
    
    return _cache[key]


def set_to_cache(key: str, data: Any):
    """
    设置缓存数据
    
    Args:
        key: 缓存 key
        data: 缓存数据
    """
    _cache[key] = data
    _cache_times[key] = time.time()


# ─────────────────────────────────────────────
# API 端点
# ─────────────────────────────────────────────

@app.get("/health")
async def health():
    """健康检查"""
    logger.info("收到健康检查请求")
    return {
        "service": "竞品监测 Agent",
        "status": "ok",
        "version": "v2.1",
        "endpoints": [
            "/api/competitors",
            "/api/pricing",
            "/api/intelligence",
            "/api/intelligence/stats",
            "/api/industries",
            "/api/brands",
        ]
    }


@app.get("/api/competitors")
async def get_competitors(industry: Optional[str] = Query(None, description="行业筛选")):
    """
    查询竞品数据库
    
    - `industry`: 可选，按行业筛选（如 '汽车'、'餐饮'）
    """
    request_id = generate_request_id("competitor")
    logger.info(f"收到竞品查询请求 [{request_id}]: industry={industry}")
    
    try:
        # 参数验证
        if industry and not isinstance(industry, str):
            raise ValidationError(message="industry 参数必须为字符串", details={"industry": industry})
        
        # 检查缓存
        cache_key = get_cache_key("competitors", industry=industry)
        cached_data = get_from_cache(cache_key)
        if cached_data:
            logger.info(f"从缓存返回竞品数据 [{request_id}]")
            return cached_data
        
        # 查询数据
        if industry:
            result = MOCK_COMPETITORS.get(industry, [])
        else:
            result = []
            for industry_competitors in MOCK_COMPETITORS.values():
                result.extend(industry_competitors)
        
        response = {
            "request_id": request_id,
            "industry": industry,
            "count": len(result),
            "competitors": result,
            "note": "数据为模拟数据，生产环境需接入竞品数据库",
        }
        
        # 设置缓存（缓存 5 分钟）
        set_to_cache(cache_key, response, ttl=300)
        
        logger.info(f"竞品查询请求处理完成 [{request_id}]: count={len(result)}")
        return response
        
    except ValidationError as e:
        logger.warning(f"参数验证失败 [{request_id}]: {e.message}")
        return JSONResponse(status_code=400, content=format_error_response(e, request_id=request_id))
    except Exception as e:
        logger.error(f"竞品查询失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))


@app.get("/api/pricing")
async def get_pricing():
    """查询竞品定价对比"""
    request_id = generate_request_id("pricing")
    logger.info(f"收到定价查询请求 [{request_id}]")
    
    try:
        response = {
            "request_id": request_id,
            "our_pricing": MOCK_PRICING,
            "summary": "亲邻传媒置换价在同行业中具有显著优势",
            "note": "数据为参考数据，实际价格以合同为准",
        }
        
        logger.info(f"定价查询请求处理完成 [{request_id}]")
        return response
        
    except Exception as e:
        logger.error(f"定价查询失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))


@app.get("/api/intelligence")
async def get_intelligence(
    industry: Optional[str] = Query(None, description="行业筛选"),
    brand: Optional[str] = Query(None, description="品牌筛选"),
    limit: int = Query(50, description="返回数量上限"),
):
    """
    查询市场情报
    
    - `industry`: 可选，按行业筛选（URL编码，如 %E6%B1%BD%E8%BD%A6 表示 '汽车'）
    - `brand`: 可选，按品牌筛选
    - `limit`: 返回数量上限，默认 50
    """
    request_id = generate_request_id("intelligence")
    logger.info(f"收到市场情报查询请求 [{request_id}]: industry={industry}, brand={brand}, limit={limit}")
    
    try:
        # 参数验证
        if limit <= 0:
            raise ValidationError(message="limit 必须大于 0", details={"limit": limit})
        
        # 检查缓存
        cache_key = get_cache_key("intelligence", industry=industry, brand=brand, limit=limit)
        cached_data = get_from_cache(cache_key)
        if cached_data:
            logger.info(f"从缓存返回市场情报数据 [{request_id}]")
            return cached_data
        
        # 查询数据
        results = MOCK_INTELLIGENCE.copy()
        
        if industry:
            results = [r for r in results if r["industry"] == industry]
        if brand:
            results = [r for r in results if brand in r["brand"]]
        
        results = results[:limit]
        
        response = {
            "request_id": request_id,
            "filters": {"industry": industry, "brand": brand},
            "count": len(results),
            "intelligence": results,
            "note": "数据为模拟数据，生产环境需接入市场情报数据库",
        }
        
        # 设置缓存（缓存 5 分钟）
        set_to_cache(cache_key, response, ttl=300)
        
        logger.info(f"市场情报查询请求处理完成 [{request_id}]: count={len(results)}")
        return response
        
    except ValidationError as e:
        logger.warning(f"参数验证失败 [{request_id}]: {e.message}")
        return JSONResponse(status_code=400, content=format_error_response(e, request_id=request_id))
    except Exception as e:
        logger.error(f"市场情报查询失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))


@app.get("/api/intelligence/stats")
async def get_intelligence_stats():
    """查询市场情报统计"""
    request_id = generate_request_id("intelligence_stats")
    logger.info(f"收到市场情报统计请求 [{request_id}]")
    
    try:
        stats = {
            "total_events": len(MOCK_INTELLIGENCE),
            "by_industry": {},
            "by_impact": {"high": 0, "medium": 0, "low": 0},
            "recent_7_days": 0,
            "recent_30_days": 0,
        }
        
        for item in MOCK_INTELLIGENCE:
            ind = item["industry"]
            stats["by_industry"][ind] = stats["by_industry"].get(ind, 0) + 1
            impact = item["impact"]
            stats["by_impact"][impact] = stats["by_impact"].get(impact, 0) + 1
            
            # 计算最近N天的情报
            try:
                event_date = datetime.strptime(item["date"], "%Y-%m-%d")
                days_ago = (datetime.now() - event_date).days
                if days_ago <= 7:
                    stats["recent_7_days"] += 1
                if days_ago <= 30:
                    stats["recent_30_days"] += 1
            except Exception:
                pass
        
        response = {
            "request_id": request_id,
            "stats": stats,
        }
        
        logger.info(f"市场情报统计请求处理完成 [{request_id}]")
        return response
        
    except Exception as e:
        logger.error(f"市场情报统计失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))


@app.get("/api/industries")
async def get_industries():
    """查询行业分类列表"""
    request_id = generate_request_id("industries")
    logger.info(f"收到行业分类查询请求 [{request_id}]")
    
    try:
        response = {
            "request_id": request_id,
            "industries": list(MOCK_COMPETITORS.keys()),
            "count": len(MOCK_COMPETITORS),
        }
        
        logger.info(f"行业分类查询请求处理完成 [{request_id}]")
        return response
        
    except Exception as e:
        logger.error(f"行业分类查询失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))


@app.get("/api/brands")
async def get_brands(industry: Optional[str] = Query(None, description="行业筛选")):
    """
    查询重点品牌列表
    
    - `industry`: 可选，按行业筛选
    """
    request_id = generate_request_id("brands")
    logger.info(f"收到品牌查询请求 [{request_id}]: industry={industry}")
    
    try:
        # 参数验证
        if industry and not isinstance(industry, str):
            raise ValidationError(message="industry 参数必须为字符串", details={"industry": industry})
        
        brands = []
        if industry and industry in MOCK_COMPETITORS:
            brands = [c["name"] for c in MOCK_COMPETITORS[industry]]
        else:
            for industry_competitors in MOCK_COMPETITORS.values():
                brands.extend([c["name"] for c in industry_competitors])
        
        response = {
            "request_id": request_id,
            "industry": industry,
            "count": len(brands),
            "brands": brands,
        }
        
        logger.info(f"品牌查询请求处理完成 [{request_id}]: count={len(brands)}")
        return response
        
    except ValidationError as e:
        logger.warning(f"参数验证失败 [{request_id}]: {e.message}")
        return JSONResponse(status_code=400, content=format_error_response(e, request_id=request_id))
    except Exception as e:
        logger.error(f"品牌查询失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))


@app.get("/api/intelligence/search")
async def search_intelligence(q: str = Query(..., description="搜索关键词")):
    """
    搜索市场情报
    
    - `q`: 搜索关键词（URL编码，如 %E6%AF%94%E4%BA%9A%E8%BF%A1 表示 '比亚迪'）
    """
    request_id = generate_request_id("search")
    logger.info(f"收到市场情报搜索请求 [{request_id}]: q={q}")
    
    try:
        # 参数验证
        if not q or not isinstance(q, str):
            raise ValidationError(message="q 参数必须为非空字符串", details={"q": q})
        
        # 检查缓存
        cache_key = get_cache_key("search", q=q)
        cached_data = get_from_cache(cache_key)
        if cached_data:
            logger.info(f"从缓存返回搜索结果 [{request_id}]")
            return cached_data
        
        # 搜索数据
        results = []
        for item in MOCK_INTELLIGENCE:
            if q in item["brand"] or q in item["event"] or q in item["details"]:
                results.append(item)
        
        response = {
            "request_id": request_id,
            "query": q,
            "count": len(results),
            "results": results,
        }
        
        # 设置缓存（缓存 5 分钟）
        set_to_cache(cache_key, response, ttl=300)
        
        logger.info(f"市场情报搜索请求处理完成 [{request_id}]: count={len(results)}")
        return response
        
    except ValidationError as e:
        logger.warning(f"参数验证失败 [{request_id}]: {e.message}")
        return JSONResponse(status_code=400, content=format_error_response(e, request_id=request_id))
    except Exception as e:
        logger.error(f"市场情报搜索失败 [{request_id}]: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content=format_error_response(e, request_id=request_id))


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("启动竞品监测 Agent，端口 5005...")
    uvicorn.run(app, host="0.0.0.0", port=5005)
