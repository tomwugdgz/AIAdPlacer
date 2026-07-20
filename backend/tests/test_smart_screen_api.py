"""
智能屏资源子系统（Smart Screen L9）— API 层测试。

使用 FastAPI TestClient 对 ss_api_router 做端到端验证。
为避免拉起整个 main.py（含 langchain / chromadb 等重依赖），此处仅挂载
ss_api_router 到最小化 FastAPI 应用。

前置条件：已构建 backend/data/smart_screen_l9.db。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.smart_screen.ss_api import ss_api_router
from app.smart_screen.schema_constants import INDICATOR_COLUMNS

# 最小化测试应用（仅挂载智能屏子系统路由）
_app = FastAPI(title="智能屏子系统 API 测试")
_app.include_router(ss_api_router)
client = TestClient(_app)

PREFIX = "/api/v2/smart-screen"


# ── 用例 1：/tables 返回 success=true ───────────────────────────────────────────
def test_tables():
    r = client.get(f"{PREFIX}/tables")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["code"] == "OK"
    assert body["total"] >= 8
    assert any(t["name"] == "t_media_l9" for t in body["data"])


# ── 用例 2：/stats 返回 success=true 且总量正确 ────────────────────────────────
def test_stats():
    r = client.get(f"{PREFIX}/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_media"] == 9801   # xls 9802 行含表头，数据 9801 行
    assert data["total_algorithms"] == 19


# ── 用例 3：/communities 返回小区宽表 ───────────────────────────────────────────
def test_communities():
    r = client.get(f"{PREFIX}/communities")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["total"] > 0
    assert "community_id" in body["data"][0]
    assert "city" in body["data"][0]


# ── 用例 4：/indicators/{community_id} 返回 39 指标 ────────────────────────────
def test_indicators_by_community():
    # 取第一个小区的 community_id
    comm = client.get(f"{PREFIX}/communities").json()["data"][0]
    cid = comm["community_id"]
    r = client.get(f"{PREFIX}/indicators/{cid}")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    indicators = body["data"]["indicators"]
    for col in INDICATOR_COLUMNS:
        assert col in indicators, f"指标缺失：{col}"


# ── 用例 5：/indicators/{未知ID} 返回 404 ─────────────────────────────────────
def test_indicators_not_found():
    r = client.get(f"{PREFIX}/indicators/CM99999")
    assert r.status_code == 404
    assert r.json()["success"] is False
    assert r.json()["code"] == "NOT_FOUND"


# ── 用例 6：/media 分页返回 ────────────────────────────────────────────────────
def test_media():
    r = client.get(f"{PREFIX}/media", params={"page": 1, "page_size": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["total"] == 9801  # xls 9802 行含表头，数据 9801 行
    assert len(body["data"]) == 5


# ── 用例 7：/algorithms 返回 19 条 ─────────────────────────────────────────────
def test_algorithms():
    r = client.get(f"{PREFIX}/algorithms")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["total"] == 19
    assert isinstance(body["data"][0]["input_fields"], list)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
