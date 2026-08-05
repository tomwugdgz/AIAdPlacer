"""青柠智能助手（qinglin_assistant）增量模块 —— 回归测试。

测试策略
--------
使用 ``httpx.ASGITransport`` 直接驱动 ASGI 应用，**不启动 uvicorn、不占用端口**：
- 规避后台线程启动 uvicorn 静默失败的问题；
- 规避 signal handler 只能在主线程注册的限制；
- 仅挂载 ``qinglin_assistant`` 的 router，绕开 ``app.main`` 的重型依赖
  （transformers / langgraph 等），保证测试快速且可重复。

环境前提（测试断言依赖）
------------------------
1. Ollama（LLM 后端）处于**关闭**状态 → 纯对话请求必须返回 HTTP 503，
   且 ``detail.error == "LLM_UNAVAILABLE"``；返回 200 + 伪造中文文案即判定造假。
2. 知识库指向真实主库 ``backend/data/qinglin_local.db``，查询返回真实数字
   （广州门禁 2,174 / 全国门禁总量 66,308）。
3. LLM 关闭时意图识别走确定性规则回退，触发词见各用例注释。

兼容性说明
----------
所有用例均为**同步函数**，内部通过 ``asyncio.run()`` 驱动异步客户端，
因此不依赖 ``pytest-asyncio`` 插件及其 ``asyncio_mode`` 配置，
在任意 pytest 版本下均可直接运行。

运行方式
--------
    cd backend
    venv/Scripts/python.exe -m pytest tests/test_qinglin_assistant.py -v

或（无 pytest 时的退化入口）：

    venv/Scripts/python.exe tests/test_qinglin_assistant.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Awaitable, Callable, Dict

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

# 允许以 `python tests/test_qinglin_assistant.py` 方式直接运行（补齐 backend 根路径）
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from app.qinglin_assistant.api import router  # noqa: E402

# ─────────────────────────────────────────────────────────────
# 测试夹具 / 公共常量
# ─────────────────────────────────────────────────────────────

API_PREFIX = "/api/v2/assistant"
BASE_URL = "http://test"

EXPECTED_ROLES = {"sale", "media", "engineer", "developer"}
EXPECTED_ROLE_COUNT = 4

# 知识库真查预期出现的真实数字（全国门禁总量 / 广州门禁）
REAL_KB_NUMBERS = ("66,308", "2,174")

DEMO_MARKER = "演示态"


def _build_app() -> FastAPI:
    """构建仅挂载 qinglin_assistant router 的最小 ASGI 应用。"""
    app = FastAPI(title="qinglin-assistant-test")
    app.include_router(router, prefix=API_PREFIX)
    return app


_APP = _build_app()


def _run(coro_factory: Callable[[AsyncClient], Awaitable[Any]]) -> Any:
    """在同步测试中驱动一次异步 ASGI 调用，返回协程结果。"""

    async def _main() -> Any:
        transport = ASGITransport(app=_APP)
        async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
            return await coro_factory(client)

    return asyncio.run(_main())


def _get(path: str) -> Response:
    """同步发起 GET 请求。"""
    return _run(lambda client: client.get(f"{API_PREFIX}{path}"))


def _chat(role: str, session_id: str, message: str) -> Response:
    """同步发起一次 /chat 请求。"""
    payload = {"role": role, "session_id": session_id, "message": message}
    return _run(lambda client: client.post(f"{API_PREFIX}/chat", json=payload))


def _data_of(resp: Response) -> Dict[str, Any]:
    """提取 ChatResponse 的 data 段，便于断言。"""
    body = resp.json()
    assert isinstance(body, dict), f"响应体应为 JSON 对象，实际：{type(body)}"
    data = body.get("data")
    assert isinstance(data, dict), f"响应缺少 data 段：{body}"
    return data


def _assert_demo_workflow(resp: Response, scenario: str) -> None:
    """演示态工作流（报备 / 锁点 / 导点）的公共断言。"""
    assert resp.status_code == 200, f"{scenario} 应返回 200，实际 {resp.status_code}"

    body = resp.json()
    assert body.get("success") is True, f"{scenario} success 应为 True，实际 {body.get('success')}"

    data = _data_of(resp)
    assert data.get("demo") is True, f"{scenario} data.demo 应为 True，实际 {data.get('demo')}"
    assert data.get("demo_mode") is True, (
        f"{scenario} data.demo_mode 应为 True，实际 {data.get('demo_mode')}"
    )

    content = data.get("content") or ""
    assert DEMO_MARKER in content, (
        f"{scenario} 文案必须显式标注「{DEMO_MARKER}」，实际内容：{content[:200]}"
    )
    assert data.get("permission_denied") is False, (
        f"{scenario} 不应被 RBAC 拦截，实际 permission_denied={data.get('permission_denied')}"
    )


# ─────────────────────────────────────────────────────────────
# 1. 基础设施端点
# ─────────────────────────────────────────────────────────────

def test_health() -> None:
    """GET /health → 200，DB 可达，LLM 不可用，角色数为 4。"""
    # Arrange / Act
    resp = _get("/health")

    # Assert
    assert resp.status_code == 200, f"/health 应返回 200，实际 {resp.status_code}"

    body = resp.json()
    assert body.get("status") == "ok", f"status 应为 ok，实际 {body.get('status')}"
    assert body.get("db") is True, (
        f"数据库应可达（db=True），实际 db={body.get('db')}，database={body.get('database')}"
    )

    llm = body.get("llm") or {}
    assert llm.get("available") is False, (
        "环境前提为 Ollama 关闭，llm.available 必须为 False，"
        f"实际 {llm.get('available')}（provider={llm.get('provider')}）"
    )

    assert body.get("roles") == EXPECTED_ROLE_COUNT, (
        f"角色数应为 {EXPECTED_ROLE_COUNT}，实际 {body.get('roles')}"
    )


def test_roles() -> None:
    """GET /roles → 200，返回 4 个角色（sale/media/engineer/developer）。"""
    # Arrange / Act
    resp = _get("/roles")

    # Assert
    assert resp.status_code == 200, f"/roles 应返回 200，实际 {resp.status_code}"

    body = resp.json()
    assert body.get("count") == EXPECTED_ROLE_COUNT, (
        f"count 应为 {EXPECTED_ROLE_COUNT}，实际 {body.get('count')}"
    )

    role_list = body.get("roles") or []
    assert len(role_list) == EXPECTED_ROLE_COUNT, (
        f"roles 数组长度应为 {EXPECTED_ROLE_COUNT}，实际 {len(role_list)}"
    )

    # 角色标识位于 code 字段（name 为中文展示名，如 sale → 销售）
    codes = {item.get("code") for item in role_list if isinstance(item, dict)}
    assert codes == EXPECTED_ROLES, f"角色 code 集合应为 {EXPECTED_ROLES}，实际 {codes}"

    # 每个角色应具备可读的中文名与非空能力清单
    for item in role_list:
        assert item.get("name"), f"角色 {item.get('code')} 缺少中文展示名"
        assert item.get("capabilities"), f"角色 {item.get('code')} 的 capabilities 不应为空"


# ─────────────────────────────────────────────────────────────
# 2. 知识库真查（真实 DB，数字可核对）
# ─────────────────────────────────────────────────────────────

def test_kb_real_query() -> None:
    """知识库计数查询走真实 DB：demo=False 且返回可核对的真实数字。

    触发词：「门禁」+ 数量词「多少」→ 规则回退命中 point_count。
    """
    # Arrange / Act
    resp = _chat("sale", "qa-kb-1", "广州有多少门禁点位")

    # Assert
    assert resp.status_code == 200, f"知识库查询应返回 200，实际 {resp.status_code}"

    body = resp.json()
    assert body.get("success") is True, f"success 应为 True，实际 {body.get('success')}"

    data = _data_of(resp)
    assert data.get("demo") is False, (
        f"知识库查询为真实查询，demo 必须为 False，实际 {data.get('demo')}"
    )
    assert data.get("permission_denied") is False, "sale 角色应有权查询点位数量"

    content = data.get("content") or ""
    assert any(num in content for num in REAL_KB_NUMBERS), (
        f"应返回真实可核对数字（{' 或 '.join(REAL_KB_NUMBERS)}），实际内容：{content[:300]}"
    )

    tool_calls = data.get("tool_calls") or []
    assert tool_calls, "知识库查询应记录 tool_calls（证明真实走了 DB 工具）"


# ─────────────────────────────────────────────────────────────
# 3. LLM 不可用闸门（最关键用例：禁止静默 mock）
# ─────────────────────────────────────────────────────────────

def test_chat_llm_unavailable_503() -> None:
    """纯对话在 Ollama 关闭时必须返回 503 + LLM_UNAVAILABLE，禁止伪造回复。

    这是验收硬约束：若返回 200 或任何「看起来正常」的中文模板文案，判定为造假 → FAIL。
    """
    # Arrange / Act
    resp = _chat("sale", "qa-llm-1", "你好，介绍一下你自己")

    # Assert —— 状态码优先（200 即造假）
    if resp.status_code == 200:
        fake = (resp.json().get("data") or {}).get("content", "")
        pytest.fail(
            "【造假检测】Ollama 已关闭，纯对话却返回 HTTP 200。"
            f"疑似静默 mock 的伪造文案：{fake[:200]}"
        )

    assert resp.status_code == 503, (
        f"LLM 不可用时纯对话必须返回 503，实际 {resp.status_code}"
    )

    body = resp.json()
    detail = body.get("detail")
    assert isinstance(detail, dict), f"503 响应应携带结构化 detail，实际：{body}"
    assert detail.get("error") == "LLM_UNAVAILABLE", (
        f'detail.error 应为 "LLM_UNAVAILABLE"，实际 {detail.get("error")}'
    )
    assert detail.get("message"), "503 响应应包含可读的 message，便于排障"


# ─────────────────────────────────────────────────────────────
# 4. RBAC 越权拦截
# ─────────────────────────────────────────────────────────────

def test_rbac_denied() -> None:
    """sale 角色执行 shell 命令应被 RBAC 拦截，且不访问任何底层数据。"""
    # Arrange / Act
    resp = _chat("sale", "qa-rbac-1", "帮我执行 shell 命令 echo hi")

    # Assert
    assert resp.status_code == 200, f"RBAC 拦截应以 200 + 业务标记返回，实际 {resp.status_code}"

    data = _data_of(resp)
    assert data.get("permission_denied") is True, (
        f"sale 无沙箱执行权限，permission_denied 应为 True，实际 {data.get('permission_denied')}"
    )

    content = data.get("content") or ""
    assert "权限不足" in content, f"拦截文案应明确提示「权限不足」，实际：{content[:200]}"

    # 越权请求不得泄露执行结果
    assert "hi" not in content.replace("shell", ""), (
        f"拦截后不应出现命令执行输出，实际：{content[:200]}"
    )


# ─────────────────────────────────────────────────────────────
# 5. 演示态工作流（锁点 / 报备 / 导点）
# ─────────────────────────────────────────────────────────────

def test_lock_demo() -> None:
    """media 锁点 → demo=True，文案标注「演示态」。触发词：「锁点」。"""
    resp = _chat("media", "qa-lock-1", "帮我锁点广州天河区的门禁点位 A001")
    _assert_demo_workflow(resp, "锁点")


def test_report_demo() -> None:
    """developer 报备 → demo=True，文案标注「演示态」。触发词：「报备」。"""
    resp = _chat(
        "developer",
        "qa-report-1",
        "报备一个客户：广州智达科技有限公司，决策人张总",
    )
    _assert_demo_workflow(resp, "报备")


def test_export_demo() -> None:
    """media 导点 → demo=True，文案标注「演示态」。触发词：「导点」。"""
    resp = _chat("media", "qa-export-1", "帮我导点广州的门禁点位清单")
    _assert_demo_workflow(resp, "导点")


# ─────────────────────────────────────────────────────────────
# 无 pytest 环境下的退化入口
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _CASES = [
        test_health,
        test_roles,
        test_kb_real_query,
        test_chat_llm_unavailable_503,
        test_rbac_denied,
        test_lock_demo,
        test_report_demo,
        test_export_demo,
    ]
    _failed = 0
    for _case in _CASES:
        try:
            _case()
            print(f"PASS  {_case.__name__}")
        except Exception as exc:  # noqa: BLE001
            _failed += 1
            print(f"FAIL  {_case.__name__}: {exc}")
    print(f"\n=== {len(_CASES) - _failed}/{len(_CASES)} passed ===")
    sys.exit(1 if _failed else 0)
