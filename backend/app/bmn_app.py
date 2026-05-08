"""
BMN 品牌智能增长系统 — 独立启动文件
只加载 BMN 路由，不触碰 agents/transformers 导入链
"""
import sys, types, os

# ── Windows 兼容：mock pwd 模块 ─────────────────────
_pwd_mod = types.ModuleType("pwd")
class _FakePwRec:
    pw_name = "user"
_pwd_mod.getpwuid = lambda uid: _FakePwRec()
_pwd_mod.getpwnam = lambda name: _FakePwRec()
sys.modules["pwd"] = _pwd_mod
os.environ.setdefault("USERNAME", "user")
os.environ.setdefault("USER", "user")

# ── 手动拼出 backend/ 路径 ──────────────────────────
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import sys as _s, os as _o   # 重新确认 PATH

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

# ── 注册 MCP 接口路由 ────────────────────────────────
try:
    from app.bmn.mcp_interface import mcp_router
    app.include_router(mcp_router, prefix="/api/v2/bmn")
    print("  ✅ MCP 接口已注册")
except Exception as e:
    print(f"  ⚠️  MCP 接口注册失败：{e}")


@app.on_event("startup")
async def startup():
    from app.models import init_db
    init_db()
    print("BMN 启动成功")
    print("  API文档: http://127.0.0.1:5003/docs")
    # 验证路由
    bmn = [r.path for r in app.routes if hasattr(r, "path") and ("bmn" in r.path or "workflow" in r.path)]
    print(f"  BMN 路由数: {len(bmn)}")
    for p in bmn:
        print(f"    {p}")


@app.get("/")
async def root():
    return {"msg": "BMN 品牌智能增长操作系统运行中", "docs": "/docs"}
