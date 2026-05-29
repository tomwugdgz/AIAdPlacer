"""
BMN 品牌智能增长系统 — 独立启动文件
只加载 BMN 路由，完全不触碰 agents/transformers 导入链
"""
import sys
import types
import os

# ── Windows 兼容：mock pwd 模块（双重保险）─────────
_pwd = types.ModuleType("pwd")
class _FakePwRec:
    pw_name = "user"
_pwd.getpwuid = lambda uid: _FakePwRec()
_pwd.getpwnam = lambda name: _FakePwRec()
sys.modules["pwd"] = _pwd

os.environ.setdefault("USERNAME", "user")
os.environ.setdefault("USER", "user")

# ── 加入 backend/ 到 Python 路径 ────────────────────────
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BMN 品牌智能增长操作系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 只加载 BMN 路由 ──────────────────────────────────
from app.bmn.api.brand_routes import router as br
from app.bmn.api.asset_routes import router as ar
from app.bmn.api.workflow_routes import router as wr
app.include_router(br)
app.include_router(ar)
app.include_router(wr)


@app.on_event("startup")
async def startup():
    from app.models import init_db
    init_db()
    print("BMN 启动成功")
    print("  API文档: http://127.0.0.1:5003/docs")
    bmn_paths = [r.path for r in app.routes if hasattr(r, "path") and ("bmn" in r.path or "workflow" in r.path)]
    print(f"  BMN 路由数: {len(bmn_paths)}")
    for p in bmn_paths:
        print(f"    {p}")


@app.get("/")
async def root():
    return {"msg": "BMN 品牌智能增长操作系统运行中", "docs": "/docs"}
