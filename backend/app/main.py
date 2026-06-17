import sys
import types
import os

# ── Windows 兼容：mock pwd 模块 ─────────────────────
sys.modules["pwd"] = types.ModuleType("pwd")
os.environ.setdefault("USERNAME", "user")
os.environ.setdefault("USER", "user")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as main_router
from app.api.attribution import router as attribution_router
from app.api.agents import router as agents_router
from app.bmn.api.brand_routes import router as bmn_brand_router
from app.bmn.api.asset_routes import router as bmn_asset_router
from app.bmn.api.workflow_routes import router as bmn_workflow_router
from app.pdooh_api import router as pdooh_router
from app.pdooh_mcp import router as pdooh_mcp_router
from app.bus.api import router as bus_router
from app.api.optimization_routes import router as optimization_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.knowledge_routes import router as knowledge_router
from app.tom_agent import router as tom_agent_router   # ← Tom Agent
from app.roi_agent import router as roi_agent_router   # ← ROI Agent
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(main_router, prefix="/api/v1")
app.include_router(attribution_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v2")
# BMN 品牌智能增长系统路由
app.include_router(bmn_brand_router)
app.include_router(bmn_asset_router)
app.include_router(bmn_workflow_router)
# pDOOH 数据库 API（连接真实 pdooh 库）
app.include_router(pdooh_router)
# pDOOH A2A MCP Server（AI-to-AI 投放接口）
app.include_router(pdooh_mcp_router)
# AI 排期优化 + 竞品监控
app.include_router(optimization_router, prefix="/api/v2/optimization")
# 效果归因看板
app.include_router(dashboard_router, prefix="/api/v2/dashboard")
# MCP 知识库管理
app.include_router(knowledge_router, prefix="/api/v2/knowledge")
# Tom Agent — 户外广告投放专家（端口 5003 独立服务；此处为内嵌路由）
app.include_router(tom_agent_router)
# ROI Agent — 广告投放 ROI 计算专家（端口 5004 独立服务；此处为内嵌路由）
app.include_router(roi_agent_router)

@app.on_event("startup")
async def startup():
    from app.models import init_db
    init_db()
    print(f"🚀 {settings.APP_NAME} v2.0.0 CPS 已启动")
    print(f"📍 API文档: http://127.0.0.1:5002/docs")
    print(f"🤖 Agent API: http://127.0.0.1:5002/api/v2/agents/execute")
    print(f"📚 RAG知识库: http://127.0.0.1:5002/api/v2/rag/knowledge")
    print(f"📊 pDOOH API: http://127.0.0.1:5002/api/v2/pdooh/screens")
    print(f"📅 AI排期优化: http://127.0.0.1:5002/api/v2/optimization/scheduling/generate")
    print(f"🔍 竞品监控: http://127.0.0.1:5002/api/v2/optimization/competitor/report")
    print(f"📈 效果看板: http://127.0.0.1:5002/api/v2/dashboard/overview")
    print(f"📚 MCP知识库: http://127.0.0.1:5002/api/v2/knowledge/logs")
    print(f"🗃️  知识库调用日志: http://127.0.0.1:5002/api/v2/knowledge/stats")
    print(f"🤝 Tom Agent (投放专家): http://127.0.0.1:5002/api/v2/tom/chat")
    print(f"📋 投放方案生成: http://127.0.0.1:5002/api/v2/tom/plan/generate")
    print(f"📊 CPM 追踪/对比: http://127.0.0.1:5002/api/v2/tom/cpm/track")
    print(f"📈 ROI Agent (投资回报): http://127.0.0.1:5002/api/v2/roi/calculate")
    print(f"📊 ROI 三场景快查: http://127.0.0.1:5002/api/v2/roi/three-scenarios")
