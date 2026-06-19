"""
ROI Agent 独立服务入口
端口: 5004
功能: 广告投放 ROI 计算专家 Agent（独立运行版本）

运行方式:
    python -m uvicorn app.roi_agent_server:app --host 0.0.0.0 --port 5004 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.roi_agent import router as roi_router
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("roi_agent_server")

# 创建 FastAPI 应用
app = FastAPI(
    title="ROI Agent — 广告投放 ROI 计算专家",
    version="1.0.0",
    description="ROI Agent 独立服务：提供三场景 ROI 计算、灵敏度分析、多方案对比等功能",
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
app.include_router(roi_router)

@app.on_event("startup")
async def startup():
    """服务启动时的初始化操作"""
    logger.info("🚀 ROI Agent 独立服务已启动")
    logger.info("📍 API 文档: http://127.0.0.1:5004/docs")
    logger.info("📈 ROI 计算: http://127.0.0.1:5004/api/v2/roi/calculate")
    logger.info("📊 三场景快查: http://127.0.0.1:5004/api/v2/roi/three-scenarios")
    logger.info("🔬 灵敏度分析: http://127.0.0.1:5004/api/v2/roi/sensitivity")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "ROI Agent",
        "version": "1.0.0",
        "port": 5004
    }

@app.get("/")
async def root():
    """根路径：返回服务信息"""
    return {
        "service": "ROI Agent — 广告投放 ROI 计算专家",
        "version": "1.0.0",
        "endpoints": {
            "calculate": "/api/v2/roi/calculate",
            "three_scenarios": "/api/v2/roi/three-scenarios",
            "sensitivity": "/api/v2/roi/sensitivity",
            "compare": "/api/v2/roi/compare",
            "formula": "/api/v2/roi/formula",
            "docs": "/docs",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
