"""青柠智能助手 — API 子包。

对外暴露 ``router``（FastAPI APIRouter），由 ``app/main.py`` 以
``prefix=\"/api/v2/assistant\"`` 挂载，提供 ``GET /health``、``GET /roles``、
``POST /chat`` 端点。

验收契约（team-lead 硬性要求）：

- ``GET /health`` 永远返回 200，并在响应体如实标记 DB 可达性与 LLM 可用性。
- ``GET /roles`` 返回四角色（sale / media / engineer / developer）。
- ``POST /chat`` 纯对话依赖 LLM：若 Ollama 不可用，**明确返回 503 + 清晰错误**，
  绝不静默 mock。
"""

from app.qinglin_assistant.api.routes import router

__all__ = ["router"]
