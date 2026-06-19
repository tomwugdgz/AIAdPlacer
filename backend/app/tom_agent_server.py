"""
Tom Agent 独立服务入口
端口: 5003
功能: 户外广告投放专家 Agent（独立运行版本）

运行方式:
    python -m uvicorn app.tom_agent_server:app --host 0.0.0.0 --port 5003 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.tom_agent import router as tom_router
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tom_agent_server")

# 创建 FastAPI 应用
app = FastAPI(
    title="Tom Agent — 户外广告投放专家",
    version="1.0.0",
    description="Tom Agent 独立服务：提供户外广告投放方案生成、CPM 追踪等功能",
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

# 注册路由
app.include_router(tom_router)

@app.on_event("startup")
async def startup():
    """服务启动时的初始化操作"""
    logger.info("🚀 Tom Agent 独立服务已启动")
    logger.info("📍 API 文档: http://127.0.0.1:5003/docs")
    logger.info("💬 对话接口: http://127.0.0.1:5003/api/v2/tom/chat")
    logger.info("📋 投放方案: http://127.0.0.1:5003/api/v2/tom/plan/generate")
    logger.info("📊 CPM 追踪: http://127.0.0.1:5003/api/v2/tom/cpm/track")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "Tom Agent",
        "version": "1.0.0",
        "port": 5003
    }

@app.get("/")
async def root():
    """根路径：返回服务信息"""
    return {
        "service": "Tom Agent — 户外广告投放专家",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/v2/tom/chat",
            "plan_generate": "/api/v2/tom/plan/generate",
            "cpm_track": "/api/v2/tom/cpm/track",
            "cpm_compare": "/api/v2/tom/cpm/compare",
            "query_points": "/api/v2/tom/query/points",
            "docs": "/docs",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
