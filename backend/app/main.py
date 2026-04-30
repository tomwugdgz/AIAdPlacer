from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as main_router
from app.api.attribution import router as attribution_router
from app.api.agents import router as agents_router
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
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

@app.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    from app.models import init_db
    init_db()
    print(f"🚀 {settings.APP_NAME} v2.0.0 CPS 已启动")
    print(f"📍 API文档: http://127.0.0.1:5002/docs")
    print(f"🤖 Agent API: http://127.0.0.1:5002/api/v2/agents/execute")
    print(f"📚 RAG知识库: http://127.0.0.1:5002/api/v2/rag/knowledge")
