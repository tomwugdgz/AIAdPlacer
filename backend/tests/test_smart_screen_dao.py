"""
智能屏资源子系统（Smart Screen L9）— DAO 层测试。

前置条件：已执行 `python -m app.smart_screen.cli --xls ...` 生成 backend/data/smart_screen_l9.db。
本测试只读不写，验证 DAO 查询正确性。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

import sqlite3

import pytest

from app.smart_screen import ss_dao
from app.smart_screen.ss_config import SS_DB_PATH, TABLE_MEDIA, TABLE_INDICATORS
from app.smart_screen.schema_constants import INDICATOR_COLUMNS

# xls「媒体列表」共 9802 行（含表头 1 行），真实数据行为 9801 行。
# 表头（row0）非数据，不应作为媒体点导入，故 t_media_l9 = 9801。
EXPECTED_MEDIA_ROWS = 9801


def _count(tbl: str) -> int:
    conn = sqlite3.connect(str(SS_DB_PATH))
    try:
        return conn.execute(f'SELECT COUNT(*) AS c FROM "{tbl}"').fetchone()[0]
    finally:
        conn.close()


# ── 用例 1：数据库文件存在 ──────────────────────────────────────────────────────
def test_db_file_exists():
    assert SS_DB_PATH.exists(), f"子系统库不存在：{SS_DB_PATH}，请先执行构建脚本"


# ── 用例 2：表清单包含 8 张预期表 ───────────────────────────────────────────────
def test_list_tables():
    tables = ss_dao.list_tables()
    names = {t["name"] for t in tables}
    expected = {
        "t_media_l9", "t_community", "t_device", "t_delivery",
        "t_sales", "t_community_wide", "t_algorithm", "t_poi_indicators",
    }
    assert expected.issubset(names), f"缺失表：{expected - names}"


# ── 用例 3：t_media_l9 行数 = 9802 ──────────────────────────────────────────────
def test_media_row_count():
    assert _count(TABLE_MEDIA) == EXPECTED_MEDIA_ROWS


# ── 用例 4：小区宽表查询可返回数据 ───────────────────────────────────────────────
def test_get_community_wide():
    rows = ss_dao.get_community_wide({})
    assert len(rows) > 0, "小区宽表查询为空"
    first = rows[0]
    assert "community_id" in first
    assert "household_count" in first
    assert "city" in first  # 关联层补充字段


# ── 用例 5：指标查询返回 39 个指标 ──────────────────────────────────────────────
def test_get_indicators():
    # 取第一个小区的 community_id
    conn = sqlite3.connect(str(SS_DB_PATH))
    cid = conn.execute(
        "SELECT community_id FROM t_community_wide ORDER BY community_id LIMIT 1"
    ).fetchone()[0]
    conn.close()

    ind = ss_dao.get_indicators(cid)
    assert ind is not None, f"未找到小区 {cid} 的指标"
    for col in INDICATOR_COLUMNS:
        assert col in ind, f"指标列缺失：{col}"
        assert ind[col] is not None


# ── 用例 6：统计信息总量正确 ────────────────────────────────────────────────────
def test_get_stats():
    stats = ss_dao.get_stats()
    assert stats["total_media"] == EXPECTED_MEDIA_ROWS
    assert stats["total_algorithms"] == 19
    assert stats["total_indicators"] == _count(TABLE_INDICATORS)
    assert "by_city" in stats and "by_province" in stats


# ── 用例 7：算法注册表返回 19 条 ────────────────────────────────────────────────
def test_get_algorithms():
    algs = ss_dao.get_algorithms()
    assert len(algs) == 19
    assert all(a["status"] == "registered" for a in algs)
    # input_fields 应被解析为 list
    assert isinstance(algs[0]["input_fields"], list)


# ── 用例 8：媒体筛选 + 分页 ─────────────────────────────────────────────────────
def test_query_media_pagination():
    res = ss_dao.query_media(filters={}, page=1, page_size=10)
    assert res["total"] == EXPECTED_MEDIA_ROWS
    assert len(res["data"]) == 10
    assert res["total_pages"] == (EXPECTED_MEDIA_ROWS + 9) // 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
