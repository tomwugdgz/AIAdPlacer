import sys
import types
import os

# ── Windows 兼容：mock pwd 模块 ──────────────────────
# transformers 在 Windows 下调用 getpass.getuser() 会触发 import pwd（Unix-only）
# 提前将 pwd 注入 sys.modules 彻底绕过
_pwd_mock = types.ModuleType("pwd")
_pwd_mock.getpwuid = lambda uid: type("FakePw", (), {"pw_name": "user"})()
_pwd_mock.getpwnam = lambda name: type("FakePw", (), {"pw_name": name})()
sys.modules["pwd"] = _pwd_mock
# 设置 USERNAME 环境变量（双重保险）
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
# BMN 品牌智能增长系统路由
app.include_router(bmn_brand_router)
app.include_router(bmn_asset_router)
app.include_router(bmn_workflow_router)

@app.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    from app.models import init_db
    init_db()
    print(f"🚀 {settings.APP_NAME} v2.0.0 CPS 已启动")
    print(f"📍 API文档: http://127.0.0.1:5002/docs")
    print(f"🤖 Agent API: http://127.0.0.1:5002/api/v2/agents/execute")
    print(f"📚 RAG知识库: http://127.0.0.1:5002/api/v2/rag/knowledge")
