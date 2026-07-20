"""
智能屏资源子系统（Smart Screen L9）— 算法注册表。

将 schema_constants.ALGORITHMS 的 19 条算法元数据写入 t_algorithm，
status 统一为 'registered'（仅注册占位，真实模型待数据科学团队补充）。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

import json
import sqlite3
from typing import List

from app.smart_screen.schema_constants import ALGORITHMS
from app.smart_screen.ss_config import TABLE_ALGORITHM


def register_algorithms(conn: sqlite3.Connection) -> int:
    """
    注册 19 个算法到 t_algorithm（幂等：先清空再写入）。

    Args:
        conn: 子系统数据库连接
    Returns:
        int: 注册成功的算法数量（恒为 19）
    """
    # 清空旧数据（与 build_db 的 DROP 双重保险，保证幂等）
    conn.execute(f"DELETE FROM {TABLE_ALGORITHM}")

    rows: List[tuple] = []
    for alg in ALGORITHMS:
        rows.append((
            alg["code"],
            alg["name"],
            alg["category"],
            alg["source"],
            alg["journal_level"],
            alg["validated_city"],
            json.dumps(alg["input_fields"], ensure_ascii=False),  # 宽表字段 JSON 数组
            alg["weight"],
            alg["formula_hint"],
            alg["description"],
            alg.get("status", "registered"),
        ))

    conn.executemany(
        f"""
        INSERT INTO {TABLE_ALGORITHM}
            (code, name, category, source, journal_level, validated_city,
             input_fields, weight, formula_hint, description, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


if __name__ == "__main__":
    # 便捷自测：连独立库注册并打印
    from app.smart_screen.ss_config import SS_DB_PATH, JOURNAL_MODE
    c = sqlite3.connect(str(SS_DB_PATH))
    c.execute(f"PRAGMA journal_mode={JOURNAL_MODE}")
    n = register_algorithms(c)
    c.close()
    print(f"已注册 {n} 个算法")
