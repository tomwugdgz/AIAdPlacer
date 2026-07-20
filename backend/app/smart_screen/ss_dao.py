"""
智能屏资源子系统（Smart Screen L9）— 数据访问层（DAO）。

连接独立库 smart_screen_l9.db（row_factory=sqlite3.Row + WAL），
提供：表清单 / 小区宽表查询 / 指标查询 / 媒体查询 / 统计 / 算法查询。

响应统一风格与 db_dao 一致；本文件仅服务子系统，不复用主库 db_dao。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

import sqlite3
from typing import Any, Dict, List, Optional

from app.smart_screen.ss_config import SS_DB_PATH, ROW_FACTORY, JOURNAL_MODE
from app.smart_screen.schema_constants import (
    TABLE_MEDIA, TABLE_COMMUNITY, TABLE_DEVICE, TABLE_DELIVERY, TABLE_SALES,
    TABLE_COMMUNITY_WIDE, TABLE_ALGORITHM, TABLE_INDICATORS, INDICATOR_COLUMNS,
)


def get_ss_db_connection() -> sqlite3.Connection:
    """
    获取子系统数据库连接（行工厂 + WAL）。

    Returns:
        sqlite3.Connection: 已配置的连接

    Raises:
        FileNotFoundError: 数据库文件不存在时抛出（提示先执行构建脚本）
    """
    if not SS_DB_PATH.exists():
        raise FileNotFoundError(
            f"智能屏子系统数据库不存在：{SS_DB_PATH}\n"
            f"请先执行构建：python -m app.smart_screen.cli --xls <path>"
        )
    conn = sqlite3.connect(str(SS_DB_PATH))
    conn.row_factory = ROW_FACTORY
    conn.execute(f"PRAGMA journal_mode={JOURNAL_MODE}")
    return conn


# ── 1. 获取所有表 ──────────────────────────────────────────────────────────────

def list_tables() -> List[Dict[str, Any]]:
    """
    获取子系统所有表的信息（表名 / 行数 / 字段列表）。

    Returns:
        List[Dict]: 形如 [{"name": ..., "count": ..., "columns": [...]}]
    """
    conn = get_ss_db_connection()
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = cursor.fetchall()
        result: List[Dict[str, Any]] = []
        for row in tables:
            tname = row["name"]
            cnt = conn.execute(f'SELECT COUNT(*) AS c FROM "{tname}"').fetchone()["c"]
            cols = [c["name"] for c in conn.execute(f'PRAGMA table_info("{tname}")')]
            result.append({"name": tname, "count": cnt, "columns": cols})
        return result
    finally:
        conn.close()


# ── 2. 小区级宽表查询（关联层）──────────────────────────────────────────────────

def get_community_wide(
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    查询小区级宽表（JOIN t_community_wide 与 t_community 以补充 城市/区/省）。

    Args:
        filters: 筛选字典，支持键：
            - city: 城市（精确匹配 t_community.city）
            - district: 区/县（精确匹配 t_community.district）
            - province: 省份（精确匹配 t_community.province）
        limit: 返回上限（默认 100，最大 1000）
    Returns:
        List[Dict]: 小区宽表行（含 community_name/city/district/province）
    """
    filters = filters or {}
    limit = max(1, min(int(limit), 1000))

    where: List[str] = []
    params: List[Any] = []
    if filters.get("province"):
        where.append("c.province = ?")
        params.append(filters["province"])
    if filters.get("city"):
        where.append("c.city = ?")
        params.append(filters["city"])
    if filters.get("district"):
        where.append("c.district = ?")
        params.append(filters["district"])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT w.*, c.community_name, c.province, c.city, c.district
        FROM {TABLE_COMMUNITY_WIDE} w
        JOIN {TABLE_COMMUNITY} c ON w.community_id = c.community_id
        {where_sql}
        ORDER BY w.community_id
        LIMIT ?
    """
    conn = get_ss_db_connection()
    try:
        rows = conn.execute(sql, params + [limit]).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── 3. 指标查询（产出层，小区级）────────────────────────────────────────────────

def get_indicators(community_id: str) -> Optional[Dict[str, Any]]:
    """
    获取某小区的 39 指标（小区级，point_id IS NULL）。

    Args:
        community_id: 小区 ID（如 CM00001）
    Returns:
        Optional[Dict]: 指标行（含 community_id + 39 指标 + computed_at），不存在返回 None
    """
    conn = get_ss_db_connection()
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE_INDICATORS} WHERE community_id=? AND point_id IS NULL LIMIT 1",
            (community_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── 4. 媒体列表查询（输入层，支持筛选 + 分页）────────────────────────────────────

def query_media(
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    查询 t_media_l9（支持筛选与分页）。

    Args:
        filters: 筛选字典，支持键：
            - province / city / district(区/县) / community_id（精确）
            - keyword（模糊匹配 网点名称 / 点位名称 / MAC）
        page: 页码（≥1）
        page_size: 每页数量（1–1000）
    Returns:
        Dict: {"data": [...], "total": int, "page": int, "page_size": int,
               "total_pages": int}
    """
    if page < 1:
        raise ValueError("page 必须 >= 1")
    if page_size < 1 or page_size > 1000:
        raise ValueError("page_size 必须在 1-1000 之间")

    filters = filters or {}
    where: List[str] = []
    params: List[Any] = []

    if filters.get("province"):
        where.append("所属省份 = ?")
        params.append(filters["province"])
    if filters.get("city"):
        where.append("所属城市 = ?")
        params.append(filters["city"])
    if filters.get("district"):
        where.append('"区/县" = ?')
        params.append(filters["district"])
    if filters.get("community_id"):
        where.append("community_id = ?")
        params.append(filters["community_id"])
    if filters.get("keyword"):
        kw = f"%{filters['keyword']}%"
        where.append("(网点名称 LIKE ? OR 点位名称 LIKE ? OR MAC LIKE ?)")
        params.extend([kw, kw, kw])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = get_ss_db_connection()
    try:
        total = conn.execute(
            f'SELECT COUNT(*) AS c FROM "{TABLE_MEDIA}" {where_sql}', params
        ).fetchone()["c"]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        offset = (page - 1) * page_size

        rows = conn.execute(
            f'SELECT * FROM "{TABLE_MEDIA}" {where_sql} ORDER BY id LIMIT ? OFFSET ?',
            params + [page_size, offset],
        ).fetchall()
        data = [dict(r) for r in rows]
        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    finally:
        conn.close()


# ── 5. 统计信息 ────────────────────────────────────────────────────────────────

def get_stats() -> Dict[str, Any]:
    """
    子系统整体统计（媒体 / 小区 / 设备 / 指标 / 算法 总量 + 城市/省份分布）。

    Returns:
        Dict: 统计结果
    """
    conn = get_ss_db_connection()
    try:
        def _count(tbl: str) -> int:
            return conn.execute(f'SELECT COUNT(*) AS c FROM "{tbl}"').fetchone()["c"]

        total_media = _count(TABLE_MEDIA)
        total_communities = _count(TABLE_COMMUNITY)
        total_devices = _count(TABLE_DEVICE)
        total_indicators = _count(TABLE_INDICATORS)
        total_algorithms = _count(TABLE_ALGORITHM)

        by_city = {
            r["所属城市"]: r["c"]
            for r in conn.execute(
                f'SELECT 所属城市, COUNT(*) AS c FROM "{TABLE_MEDIA}" '
                f"GROUP BY 所属城市 ORDER BY c DESC"
            )
        }
        by_province = {
            r["所属省份"]: r["c"]
            for r in conn.execute(
                f'SELECT 所属省份, COUNT(*) AS c FROM "{TABLE_MEDIA}" '
                f"GROUP BY 所属省份 ORDER BY c DESC"
            )
        }

        return {
            "total_media": total_media,
            "total_communities": total_communities,
            "total_devices": total_devices,
            "total_indicators": total_indicators,
            "total_algorithms": total_algorithms,
            "by_city": by_city,
            "by_province": by_province,
        }
    finally:
        conn.close()


# ── 6. 算法注册表查询 ───────────────────────────────────────────────────────────

def get_algorithms() -> List[Dict[str, Any]]:
    """
    查询 19 个算法注册信息。

    Returns:
        List[Dict]: 算法列表
    """
    conn = get_ss_db_connection()
    try:
        rows = conn.execute(
            f"SELECT * FROM {TABLE_ALGORITHM} ORDER BY code"
        ).fetchall()
        result: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            # input_fields 为 JSON 字符串，转回 list 便于前端使用
            if isinstance(d.get("input_fields"), str):
                try:
                    d["input_fields"] = __import__("json").loads(d["input_fields"])
                except (ValueError, TypeError):
                    d["input_fields"] = []
            result.append(d)
        return result
    finally:
        conn.close()
