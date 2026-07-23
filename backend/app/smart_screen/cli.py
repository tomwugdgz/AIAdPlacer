"""
智能屏资源子系统（Smart Screen L9）— 构建命令行入口。

用法：
    python -m app.smart_screen.cli --xls "D:/BaiduNetdiskDownload/Other/皓邻/智能屏L9.xls"
    python -m app.smart_screen.cli            # 使用默认 xls 路径

功能：调用 build_db.build_all 完成建库，并打印结果（表清单 + 行数）。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

import argparse
import sqlite3
import sys
from pathlib import Path

from app.smart_screen.ss_config import SS_DB_PATH, JOURNAL_MODE, ROW_FACTORY
from app.smart_screen.build_db import build_all
from app.smart_screen.schema_constants import (
    TABLE_MEDIA, TABLE_COMMUNITY, TABLE_DEVICE, TABLE_DELIVERY,
    TABLE_SALES, TABLE_COMMUNITY_WIDE, TABLE_ALGORITHM, TABLE_INDICATORS,
)

# 默认 xls 路径（团队提供的真实数据位置）
DEFAULT_XLS = r"D:/BaiduNetdiskDownload/Other/皓邻/智能屏L9.xls"

# 建库后需要汇报行数的表（含派生表）
_RESULT_TABLES = [
    TABLE_MEDIA, TABLE_COMMUNITY, TABLE_DEVICE, TABLE_DELIVERY,
    TABLE_SALES, TABLE_COMMUNITY_WIDE, TABLE_ALGORITHM, TABLE_INDICATORS,
]


def _print_summary() -> None:
    """构建完成后，打印各表行数清单。"""
    conn = sqlite3.connect(str(SS_DB_PATH))
    conn.execute(f"PRAGMA journal_mode={JOURNAL_MODE}")
    try:
        print("\n" + "=" * 64)
        print("智能屏资源子系统（Smart Screen L9）— 构建结果")
        print("=" * 64)
        print(f"数据库: {SS_DB_PATH}")
        print("-" * 64)
        print(f"{'表名':<22}{'行数':>10}")
        print("-" * 64)
        total = 0
        for tbl in _RESULT_TABLES:
            cur = conn.execute(f'SELECT COUNT(*) AS c FROM "{tbl}"')
            cnt = cur.fetchone()[0]
            total += cnt
            print(f"{tbl:<22}{cnt:>10}")
        print("-" * 64)
        print(f"{'合计':<22}{total:>10}")
        print("=" * 64)
    finally:
        conn.close()


def _recompute_indicators() -> int:
    """重算并刷新 39 指标（幂等，一次刷新 roi_estimate + value_index 两列）。

    Returns:
        int: 刷新的 t_poi_indicators 行数（= 小区数）
    """
    from app.smart_screen.indicators import generate_indicators

    conn = sqlite3.connect(str(SS_DB_PATH))
    conn.row_factory = ROW_FACTORY
    conn.execute(f"PRAGMA journal_mode={JOURNAL_MODE}")
    try:
        rows = generate_indicators(conn)
        print(f"[cli] 已重算并刷新 {rows} 行小区级指标（roi_estimate + value_index）")
        return rows
    finally:
        conn.close()


def main(argv: list = None) -> int:
    """
    命令行主函数。

    Args:
        argv: 参数列表（默认取 sys.argv[1:]）
    Returns:
        int: 进程退出码（0 成功 / 1 失败）
    """
    parser = argparse.ArgumentParser(
        description="智能屏资源子系统（Smart Screen L9）建库工具",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        choices=["recompute-indicators"],
        help="子命令：recompute-indicators 幂等重算并刷新 39 指标（含 roi_estimate/value_index）",
    )
    parser.add_argument(
        "--xls",
        dest="xls_path",
        default=DEFAULT_XLS,
        help="「智能屏L9.xls」路径（含 sheet「媒体列表」）",
    )
    args = parser.parse_args(argv)

    # 子命令：幂等重算指标（不重建库，仅刷新 t_poi_indicators）
    if args.command == "recompute-indicators":
        try:
            _recompute_indicators()
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"[cli] 重算失败: {exc}", file=sys.stderr)
            return 1

    print(f"[cli] 开始构建，xls = {args.xls_path}")
    try:
        summary = build_all(args.xls_path)
        print("[cli] 构建完成:", summary.get("built_at"))
        _print_summary()
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[cli] 构建失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
