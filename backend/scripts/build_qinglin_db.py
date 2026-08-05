"""
青柠助手业务库构建 / 校验脚本（一次性 + 可重复执行）。

作用
----
1. 以 ``backend/data/qinlin_local.db``（历史命名，含 db_dao 所需的全部表）为基底，
   通过 SQLite Backup API 生成命名合规的 ``backend/data/qinglin_local.db``。
   Backup API 能正确处理 WAL 模式下未落盘的数据，比直接 copy 文件更安全。
2. 从仓库根目录的真实媒体资源库（``青柠媒体资源.db``）补齐基底库中缺失的资源表
   （城市资源索引 / 梯影点位 / 电梯框架点位），使青柠库成为**超集**，
   既不丢失既有功能依赖的表，又能覆盖更多真实点位类型。
3. 打印表名清单 + 样例行，用于人工验收。

用法
----
    python backend/scripts/build_qinglin_db.py            # 构建 + 校验
    python backend/scripts/build_qinglin_db.py --verify   # 仅校验，不写入

设计说明
--------
- 全程只读源库，绝不修改/删除仓库根目录的原始 ``青柠*.db`` 文件。
- 幂等：重复执行会重新生成目标库，结果一致。
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

# backend/scripts/build_qinglin_db.py -> backend/ -> 仓库根
BACKEND_DIR: Path = Path(__file__).resolve().parent.parent
REPO_ROOT: Path = BACKEND_DIR.parent

DATA_DIR: Path = BACKEND_DIR / "data"
#: 历史命名的基底库（含 db_dao 依赖的 智能屏202507 / 智能屏L9 / 客户通讯录）
LEGACY_DB: Path = DATA_DIR / "qinlin_local.db"
#: 本次要产出的命名合规目标库
TARGET_DB: Path = DATA_DIR / "qinglin_local.db"
#: 仓库根的真实媒体资源库（只读）
MEDIA_DB: Path = REPO_ROOT / "青柠媒体资源.db"

#: 需要从媒体资源库补充进目标库的表（仅当目标库中不存在时才补）
SUPPLEMENT_TABLES: List[str] = ["城市资源索引", "梯影点位", "电梯框架点位"]


def list_tables(conn: sqlite3.Connection) -> List[str]:
    """返回连接中所有用户表名（排除 sqlite_ 系统表）。"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [row[0] for row in cursor.fetchall()]


def backup_database(src: Path, dst: Path) -> None:
    """使用 SQLite Backup API 将 ``src`` 完整复制为 ``dst``（WAL 安全）。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    # 不做 unlink：sqlite3 的 backup() 会整库覆盖目标内容，
    # 且部分沙箱环境禁止删除文件，直接覆盖更稳妥。
    src_conn = sqlite3.connect(f"file:{src.as_posix()}?mode=ro", uri=True)
    dst_conn = sqlite3.connect(str(dst))
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()


def copy_table(dst_conn: sqlite3.Connection, table: str) -> int:
    """
    从已 ATTACH 的 ``media`` 库把 ``table`` 整表复制到目标库。

    Returns
    -------
    int
        复制的行数。
    """
    create_sql_row = dst_conn.execute(
        "SELECT sql FROM media.sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    if create_sql_row is None or not create_sql_row[0]:
        return 0

    dst_conn.execute(create_sql_row[0])
    dst_conn.execute(f'INSERT INTO main."{table}" SELECT * FROM media."{table}"')
    return int(dst_conn.execute(f'SELECT COUNT(*) FROM main."{table}"').fetchone()[0])


def build() -> None:
    """构建目标库：基底备份 + 补充表合并。"""
    if not LEGACY_DB.exists():
        raise FileNotFoundError(f"基底库不存在：{LEGACY_DB}")

    print(f"[1/3] 基底备份 {LEGACY_DB.name} -> {TARGET_DB.name}")
    backup_database(LEGACY_DB, TARGET_DB)

    print(f"[2/3] 从 {MEDIA_DB.name} 补充资源表")
    if not MEDIA_DB.exists():
        print(f"      ! 媒体资源库不存在，跳过补充：{MEDIA_DB}")
        return

    # uri=True 才能让 ATTACH 识别 file:...?mode=ro 只读 URI；
    # 主库传普通路径（不以 file: 开头）在 URI 模式下仍按普通文件名处理。
    conn = sqlite3.connect(TARGET_DB.as_posix(), uri=True)
    try:
        existing = set(list_tables(conn))
        conn.execute(
            "ATTACH DATABASE ? AS media", (f"file:{MEDIA_DB.as_posix()}?mode=ro",)
        )
        media_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM media.sqlite_master WHERE type='table'"
            ).fetchall()
        }

        for table in SUPPLEMENT_TABLES:
            if table in existing:
                print(f"      - {table}: 目标库已存在，跳过")
                continue
            if table not in media_tables:
                print(f"      - {table}: 源库不存在，跳过")
                continue
            rows = copy_table(conn, table)
            print(f"      + {table}: 已补充 {rows} 行")

        conn.commit()
        conn.execute("DETACH DATABASE media")
    finally:
        conn.close()


def verify() -> Dict[str, Any]:
    """校验目标库：列出表名、行数，并抽一行真实数据。"""
    if not TARGET_DB.exists():
        raise FileNotFoundError(f"目标库不存在：{TARGET_DB}")

    print(f"[3/3] 校验 {TARGET_DB}  ({TARGET_DB.stat().st_size / 1024 / 1024:.1f} MB)")
    conn = sqlite3.connect(f"file:{TARGET_DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    summary: Dict[str, Any] = {"db": str(TARGET_DB), "tables": {}}
    try:
        tables = list_tables(conn)
        for table in tables:
            count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            summary["tables"][table] = count
            print(f"      {table:<16} {count:>8} 行")

        probe = "门禁点位" if "门禁点位" in tables else (tables[0] if tables else None)
        if probe:
            row = conn.execute(f'SELECT * FROM "{probe}" LIMIT 1').fetchone()
            if row is not None:
                sample = {k: row[k] for k in row.keys()}
                summary["sample_table"] = probe
                summary["sample_row"] = sample
                print(f"\n      样例行 @ {probe}:")
                for key, value in sample.items():
                    print(f"        {key} = {value}")
    finally:
        conn.close()
    return summary


def main() -> int:
    """脚本入口。"""
    parser = argparse.ArgumentParser(description="构建/校验青柠助手业务库")
    parser.add_argument(
        "--verify", action="store_true", help="仅校验现有目标库，不重新构建"
    )
    args = parser.parse_args()

    if not args.verify:
        build()
    verify()
    print("\n✅ 完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
