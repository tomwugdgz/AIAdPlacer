"""青柠 Booking P0 — ETL 与 level 派生测试（T9 / CT 辅助）。

验证：
- 派生规则正确性（媒体类型基础档 + 城市覆盖 + 未知回退）
- ETL 幂等（两次全量小批量，distinct_ids / 写入数一致）
- media_resources 中 ETL 行数 > 0

铁律：SQLite 只读、不跨库 join；ETL 为确定性 uuid5 幂等 upsert，可安全重跑。

注：模块级 async_engine 绑定事件循环，故所有异步调用经共享持久 loop（_run），
避免反复 asyncio.run 关闭 loop 导致连接失效。
"""
from __future__ import annotations

import asyncio

import app.core.async_db as _ad
from app.services.level_rule import DEFAULT_RULES, derive_level_from_rules
from app.services.etl_media import count_etl_rows, run_etl


def _run(coro):
    loop = getattr(_ad, "_TEST_LOOP", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _ad._TEST_LOOP = loop
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def test_derive_level_media_type_base():
    """决策①：按媒体类型取基础档。"""
    cases = {
        "door_access": "A+",
        "mall_led": "A++",
        "smart_screen_l9": "A",
        "smart_screen_202507": "A",
        "unit_door": "B",
        "boom_gate": "C",
    }
    for code, expect in cases.items():
        got = derive_level_from_rules(code, "其他城市", DEFAULT_RULES)
        assert got == expect, f"{code}: 期望 {expect}，实际 {got}"


def test_derive_level_city_override():
    """核心城区覆盖 → 封顶 A++；非覆盖城市保持基础档。"""
    assert derive_level_from_rules("unit_door", "广州天河", DEFAULT_RULES) == "A++"
    assert derive_level_from_rules("boom_gate", "广州珠江新城", DEFAULT_RULES) == "A++"
    assert derive_level_from_rules("unit_door", "成都", DEFAULT_RULES) == "B"


def test_derive_level_unknown_media_fallback():
    """未知媒体类型回退 C 档。"""
    assert derive_level_from_rules("unknown_type", "未知", DEFAULT_RULES) == "C"


def test_etl_idempotent_and_rows():
    """ETL 幂等：两次 limit=600 小批量，read/written/distinct_ids 一致；库内 ETL 行数 > 0。"""
    r1 = _run(run_etl(limit=600))
    r2 = _run(run_etl(limit=600))
    assert r1["read"] == r2["read"] == 600
    assert r1["written"] == r2["written"] == 600
    # 确定性 uuid5 → 两轮去重集合完全一致
    assert r1["distinct_ids"] == r2["distinct_ids"]
    total = _run(count_etl_rows())
    assert total > 0, "media_resources 中应有 ETL 写入的行"
