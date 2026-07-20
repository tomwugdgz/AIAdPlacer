"""
智能屏资源子系统（Smart Screen L9）— 产出层指标计算。

读取 t_community_wide（小区级宽表），逐小区调用 indicator_formulas 的 39 个
启发式函数，写入 t_poi_indicators（community_id + point_id=NULL 表示小区级聚合）。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

import sqlite3
import time
from typing import Dict, List

from app.smart_screen.schema_constants import INDICATOR_COLUMNS
from app.smart_screen.indicator_formulas import INDICATOR_FUNCS
from app.smart_screen.ss_config import TABLE_COMMUNITY_WIDE, TABLE_INDICATORS


def generate_indicators(conn: sqlite3.Connection) -> int:
    """
    计算并写入 39 指标（小区级，point_id=NULL）。

    Args:
        conn: 子系统数据库连接
    Returns:
        int: 写入的 t_poi_indicators 行数（= 小区数）
    """
    # 读取全部小区级宽表
    rows = conn.execute(f"SELECT * FROM {TABLE_COMMUNITY_WIDE}").fetchall()

    # 清空旧指标（与 build_db DROP 双保险，幂等）
    conn.execute(f"DELETE FROM {TABLE_INDICATORS}")

    placeholders = ",".join(["?"] * (2 + len(INDICATOR_COLUMNS) + 1))  # community_id, point_id, 39, computed_at
    sql = (
        f"INSERT INTO {TABLE_INDICATORS} "
        f"(community_id, point_id, {','.join(INDICATOR_COLUMNS)}, computed_at) "
        f"VALUES ({placeholders})"
    )

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    count = 0
    for row in rows:
        wide: Dict = dict(row)
        # 逐指标调用启发式公式（占位示意）
        values = [INDICATOR_FUNCS[col](wide) for col in INDICATOR_COLUMNS]
        conn.execute(sql, [wide.get("community_id"), None, *values, now])
        count += 1

    conn.commit()
    return count


if __name__ == "__main__":
    from app.smart_screen.ss_config import SS_DB_PATH, JOURNAL_MODE
    c = sqlite3.connect(str(SS_DB_PATH))
    c.execute(f"PRAGMA journal_mode={JOURNAL_MODE}")
    print(f"已生成 {generate_indicators(c)} 行小区级指标")
    c.close()
