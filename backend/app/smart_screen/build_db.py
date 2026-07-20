"""
智能屏资源子系统（Smart Screen L9）— 建库脚本（输入层 + 关联层）。

职责：
1. 幂等建表：先 DROP TABLE IF EXISTS 再 CREATE（重跑可重建，不影响主库）
2. 从「智能屏L9.xls」(sheet「媒体列表」, 9802×12) 导入 t_media_l9（12 列严格对应）
3. 由 t_media_l9 派生 t_community / t_device / t_delivery / t_sales（无真实值处标注占位）
4. 构建关联层 t_community_wide 小区级宽表（默认策略见 §8）
5. 调用 algorithm_catalog.register_algorithms 写入 t_algorithm（19 行）
6. 调用 indicators.generate_indicators 写入 t_poi_indicators（39 列）

所有派生处均加中文注释标明「占位 / 待真实数据」。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

import json
import math
import sqlite3
import time
import xlrd
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from app.smart_screen.ss_config import (
    SS_DB_PATH,
    ROW_FACTORY,
    JOURNAL_MODE,
    XLS_SHEET_NAME,
    XLS_COLUMNS,
    COMMUNITY_ID_PREFIX,
    PLAN_ID_PREFIX,
    DEVICE_STATUS_ONLINE,
    TABLE_MEDIA,
    TABLE_COMMUNITY,
    TABLE_DEVICE,
    TABLE_DELIVERY,
    TABLE_SALES,
    TABLE_COMMUNITY_WIDE,
    TABLE_ALGORITHM,
    TABLE_INDICATORS,
)
from app.smart_screen.algorithm_catalog import register_algorithms
from app.smart_screen.indicators import generate_indicators

# 所有建表 DDL（统一 t_ 前缀）。列名使用中文业务名，与 xls / 既有库一致。
_DDL_LIST: List[str] = [
    # ── 输入层①：原始媒体列表（12 列与 xls 严格对应）──────────────────────────────
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_MEDIA} (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        所属省份       TEXT,
        所属城市       TEXT,
        "区/县"        TEXT,
        网点名称       TEXT,
        楼盘类型       TEXT,
        住户数         TEXT,        -- 原始为 "--" 等占位，存原文，派生时再 cast
        楼盘价格       TEXT,        -- 原始为 "--"，存原文
        点位名称       TEXT,
        详细地址       TEXT,
        点位ID         TEXT,        -- xls 样例 "448"
        MAC           TEXT,
        终端型号       TEXT,
        community_id  TEXT,         -- 由 网点名称 映射
        device_id     TEXT,         -- = MAC
        media_id      TEXT,         -- 由 终端型号 映射
        point_id      TEXT,         -- = 点位ID
        plan_id       TEXT,         -- 由 community 映射占位
        imported_at   TEXT
    );
    """,
    # ── 输入层②：BD 小区（由 网点名称 聚合派生）─────────────────────────────────
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_COMMUNITY} (
        community_id    TEXT PRIMARY KEY,
        community_name  TEXT,
        province        TEXT,
        city            TEXT,
        district        TEXT,
        household_count INTEGER DEFAULT 0,
        building_count  INTEGER DEFAULT 0,
        occupancy_rate  REAL    DEFAULT 0.0,
        contract_amount REAL    DEFAULT 0.0,
        gps_lng         REAL,
        gps_lat         REAL,
        src             TEXT DEFAULT 'derived_from_l9',
        created_at      TEXT
    );
    """,
    # ── 输入层③：工程设备（由 MAC 派生）────────────────────────────────────────
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_DEVICE} (
        device_id        TEXT PRIMARY KEY,
        community_id     TEXT,
        point_id         TEXT,
        terminal_model   TEXT,
        status           TEXT DEFAULT '在线',
        install_location TEXT,
        patrol_count     INTEGER DEFAULT 0,
        repair_count     INTEGER DEFAULT 0,
        install_date     TEXT,
        created_at       TEXT
    );
    """,
    # ── 输入层④：媒介投放（每小区占位派生）────────────────────────────────────
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_DELIVERY} (
        delivery_id      TEXT PRIMARY KEY,
        community_id     TEXT,
        point_id         TEXT,
        device_id        TEXT,
        media_type       TEXT,
        plan_id          TEXT,
        schedule_start   TEXT,
        schedule_end     TEXT,
        on_shelf_count   INTEGER DEFAULT 0,
        created_at       TEXT
    );
    """,
    # ── 输入层⑤：销售选点（每小区占位派生）────────────────────────────────────
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_SALES} (
        sales_id              TEXT PRIMARY KEY,
        community_id          TEXT,
        customer_name         TEXT,
        quote                 REAL DEFAULT 0,
        selection_preference  TEXT,
        industry              TEXT,
        budget                REAL DEFAULT 0,
        created_at            TEXT
    );
    """,
    # ── 关联层：小区级宽表（13 业务字段 + PK）──────────────────────────────────
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_COMMUNITY_WIDE} (
        community_id           TEXT PRIMARY KEY,
        household_count        INTEGER DEFAULT 0,
        occupancy_rate         REAL    DEFAULT 0.0,
        building_count         INTEGER DEFAULT 0,
        gate_device_count      INTEGER DEFAULT 0,
        access_device_count    INTEGER DEFAULT 0,
        monthly_failure_rate   REAL    DEFAULT 0.0,
        historical_launch_count INTEGER DEFAULT 0,
        covered_industry_count INTEGER DEFAULT 0,
        ad_door_avg_price      REAL    DEFAULT 0.0,
        access_lightbox_price  REAL    DEFAULT 0.0,
        historical_customer_industry TEXT,
        gps_lng                REAL,
        gps_lat                REAL
    );
    """,
    # ── 算法层：19 算法注册表（由 algorithm_catalog 填充）──────────────────────
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_ALGORITHM} (
        code           TEXT PRIMARY KEY,
        name           TEXT,
        category       TEXT,
        source         TEXT,
        journal_level  TEXT,
        validated_city TEXT,
        input_fields   TEXT,
        weight         REAL DEFAULT 1.0,
        formula_hint   TEXT,
        description    TEXT,
        status         TEXT DEFAULT 'registered'
    );
    """,
    # ── 产出层：点位/小区级 39 指标宽表（由 indicators 填充）────────────────────
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_INDICATORS} (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        community_id     TEXT NOT NULL,
        point_id         TEXT,
        daily_reach       REAL,
        building_depth    REAL,
        dual_touch        REAL,
        coverage_rate     REAL,
        population_index  REAL,
        health_score      REAL,
        timeliness_rate   REAL,
        activity_score    REAL,
        stability_score   REAL,
        quality_index     REAL,
        industry_heat     REAL,
        recommend_score   REAL,
        peak_season_index REAL,
        effect_predict    REAL,
        cpm               REAL,
        cost_performance  REAL,
        sssc_coefficient  REAL,
        roi_estimate      REAL,
        value_index       REAL,
        grade_tag         REAL,
        consumption_power REAL,
        commute_tag       REAL,
        family_tag        REAL,
        function_tag      REAL,
        integration       REAL,
        choice            REAL,
        depth             REAL,
        sci               REAL,
        fit_takeout       REAL,
        fit_ecommerce     REAL,
        fit_fmcg          REAL,
        fit_beauty        REAL,
        fit_auto          REAL,
        fit_education     REAL,
        fit_realestate    REAL,
        fit_finance       REAL,
        fit_health        REAL,
        fit_travel        REAL,
        fit_local         REAL,
        computed_at       TEXT
    );
    """,
]


def _to_text(value) -> str:
    """
    将单元格值规范为字符串（处理 xlrd 的空值 / 整数型浮点）。

    直接用 xlrd 1.2.0 读取 .xls（避免 pandas 2.x 与 xlrd<2.0 的版本冲突）。
    空单元格返回 ""；整数型浮点（如 点位ID "448.0"）转整数字符串避免 ".0" 后缀。

    Args:
        value: xlrd 读出的原始单元格值
    Returns:
        str: 规范化后的文本；空值返回 ""
    """
    if value is None:
        return ""
    # xlrd 空数值单元格为 NaN（float）
    if isinstance(value, float) and math.isnan(value):
        return ""
    # 整数型浮点（如 1900003.0 / 点位ID "448.0"）转整数字符串
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _read_xls_rows(xls_path: str, sheet_name: str) -> List[Dict[str, any]]:
    """
    使用 xlrd 1.2.0 读取 .xls，返回表头为键的 dict 行列表。

    Args:
        xls_path: xls 文件路径
        sheet_name: 工作表名（如「媒体列表」）
    Returns:
        List[Dict]: 每行一个 dict（键为表头文本）
    """
    book = xlrd.open_workbook(xls_path)
    # 优先按名称取表，失败则取第一个表（兼容表名差异）
    try:
        sheet = book.sheet_by_name(sheet_name)
    except xlrd.biffh.XLRDError:
        sheet = book.sheet_by_index(0)
    headers = [str(sheet.cell_value(0, c)).strip() for c in range(sheet.ncols)]
    rows: List[Dict[str, any]] = []
    for r in range(1, sheet.nrows):
        row = {headers[c]: sheet.cell_value(r, c) for c in range(sheet.ncols)}
        rows.append(row)
    return rows


def _connect() -> sqlite3.Connection:
    """建立子系统连接（行工厂 + WAL）。"""
    conn = sqlite3.connect(str(SS_DB_PATH))
    conn.row_factory = ROW_FACTORY
    conn.execute(f"PRAGMA journal_mode={JOURNAL_MODE}")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """
    幂等建表：先 DROP 再 CREATE 全部 8 张表。重跑可安全重建。

    Args:
        conn: 子系统数据库连接
    """
    # ① 先全部 DROP（幂等），解除依赖
    for tbl in [
        TABLE_MEDIA, TABLE_COMMUNITY, TABLE_DEVICE, TABLE_DELIVERY,
        TABLE_SALES, TABLE_COMMUNITY_WIDE, TABLE_ALGORITHM, TABLE_INDICATORS,
    ]:
        conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    # ② 再统一 CREATE
    for ddl in _DDL_LIST:
        conn.execute(ddl)
    conn.commit()


def import_media_and_derive(
    conn: sqlite3.Connection, xls_path: str
) -> Dict[str, any]:
    """
    导入 xls → t_media_l9，并一次性派生 t_community / t_device / t_delivery /
    t_sales / t_community_wide。

    Args:
        conn: 子系统数据库连接
        xls_path: xls 文件路径
    Returns:
        Dict: 各表写入行数统计
    """
    # ── 1. 读取 xls（xlrd 1.2.0 直读，规避 pandas/xlrd 版本冲突）──────────────
    rows = _read_xls_rows(xls_path, XLS_SHEET_NAME)
    if not rows:
        raise ValueError(f"xls 读取为空：{xls_path}")
    # 校验列完整性（取首行表头集合）
    first_headers = set(rows[0].keys())
    missing = [c for c in XLS_COLUMNS if c not in first_headers]
    if missing:
        raise ValueError(f"xls 缺少必要列: {missing}（期望 12 列：{XLS_COLUMNS}）")

    now = time.strftime("%Y-%m-%d %H:%M:%S")

    # ── 2. 第一轮扫描：确定社区顺序、计划 ID、聚合结构 ──────────────────────────
    community_order: List[str] = []          # 社区出现顺序（用于 CM 序号）
    community_map: Dict[str, str] = {}        # 网点名称 -> community_id
    plan_map: Dict[str, str] = {}             # community_id -> plan_id
    # 每个社区的聚合信息
    comm_meta: Dict[str, dict] = defaultdict(lambda: {
        "province": "", "city": "", "district": "",
        "point_count": 0, "macs": set(),
        "terminal_counter": Counter(),
    })
    # 设备信息（按 MAC 去重，取首次出现）
    devices: Dict[str, dict] = {}

    for row in rows:
        province = _to_text(row.get("所属省份"))
        city = _to_text(row.get("所属城市"))
        district = _to_text(row.get("区/县"))
        net_name = _to_text(row.get("网点名称"))
        mac = _to_text(row.get("MAC"))
        model = _to_text(row.get("终端型号"))
        point_id = _to_text(row.get("点位ID"))
        install_loc = _to_text(row.get("详细地址"))

        # 社区映射
        if net_name not in community_map:
            community_map[net_name] = f"{COMMUNITY_ID_PREFIX}{len(community_order) + 1:05d}"
            community_order.append(net_name)
            plan_map[community_map[net_name]] = f"{PLAN_ID_PREFIX}{len(community_order):05d}"
        cid = community_map[net_name]

        meta = comm_meta[cid]
        if not meta["province"]:
            meta["province"] = province
            meta["city"] = city
            meta["district"] = district
        meta["point_count"] += 1
        if mac:
            meta["macs"].add(mac)
        if model:
            meta["terminal_counter"][model] += 1

        # 设备去重登记
        if mac and mac not in devices:
            devices[mac] = {
                "community_id": cid,
                "point_id": point_id,
                "terminal_model": model,
                "install_location": install_loc,
            }

    # ── 3. 写入 t_media_l9（12 列 + 派生关联键）────────────────────────────────
    media_rows: List[Tuple] = []
    for row in rows:
        net_name = _to_text(row.get("网点名称"))
        mac = _to_text(row.get("MAC"))
        model = _to_text(row.get("终端型号"))
        point_id = _to_text(row.get("点位ID"))
        cid = community_map[net_name]
        media_rows.append((
            _to_text(row.get("所属省份")),
            _to_text(row.get("所属城市")),
            _to_text(row.get("区/县")),
            net_name,
            _to_text(row.get("楼盘类型")),
            _to_text(row.get("住户数")),       # 原文存（可能为 "--"）
            _to_text(row.get("楼盘价格")),      # 原文存（可能为 "--"）
            _to_text(row.get("点位名称")),
            _to_text(row.get("详细地址")),
            point_id,
            mac,
            model,
            cid,                               # community_id
            mac,                               # device_id = MAC
            model,                             # media_id = 终端型号
            point_id,                          # point_id = 点位ID
            plan_map[cid],                     # plan_id（按社区占位）
            now,
        ))
    conn.executemany(
        f"""
        INSERT INTO {TABLE_MEDIA}
            (所属省份, 所属城市, "区/县", 网点名称, 楼盘类型, 住户数, 楼盘价格,
             点位名称, 详细地址, 点位ID, MAC, 终端型号,
             community_id, device_id, media_id, point_id, plan_id, imported_at)
        VALUES ({','.join(['?'] * 18)})
        """,
        media_rows,
    )

    # ── 4. 派生 t_community ───────────────────────────────────────────────────
    community_rows: List[Tuple] = []
    for net_name in community_order:
        cid = community_map[net_name]
        meta = comm_meta[cid]
        point_count = meta["point_count"]
        device_count = len(meta["macs"])
        # 占位策略：楼栋数 = max(1, round(点位数量 / 3))；户数 = 楼栋数 * 100
        building_count = max(1, round(point_count / 3))           # 占位，待真实数据
        household_count = building_count * 100                    # 占位，待真实数据
        occupancy_rate = 0.92                                     # 占位默认入住率
        community_rows.append((
            cid, net_name, meta["province"], meta["city"], meta["district"],
            household_count, building_count, occupancy_rate,
            0.0,            # contract_amount 占位
            None, None,     # gps 缺失，留 NULL（待补坐标）
            "derived_from_l9", now,
        ))
    conn.executemany(
        f"""
        INSERT INTO {TABLE_COMMUNITY}
            (community_id, community_name, province, city, district,
             household_count, building_count, occupancy_rate,
             contract_amount, gps_lng, gps_lat, src, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        community_rows,
    )

    # ── 5. 派生 t_device ──────────────────────────────────────────────────────
    device_rows: List[Tuple] = []
    for mac, d in devices.items():
        device_rows.append((
            mac,                         # device_id = MAC
            d["community_id"],
            d["point_id"],
            d["terminal_model"],
            DEVICE_STATUS_ONLINE,       # 占位默认在线
            d["install_location"],
            0, 0,                       # patrol/repair 占位 0
            None,                       # install_date 待真实数据
            now,
        ))
    conn.executemany(
        f"""
        INSERT INTO {TABLE_DEVICE}
            (device_id, community_id, point_id, terminal_model, status,
             install_location, patrol_count, repair_count, install_date, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        device_rows,
    )

    # ── 6. 派生 t_delivery（每小区一条占位）────────────────────────────────────
    delivery_rows: List[Tuple] = []
    dl_seq = 0
    for net_name in community_order:
        cid = community_map[net_name]
        meta = comm_meta[cid]
        # 媒体类型 = 该社区终端型号众数（占位，待真实投放数据）
        media_type = meta["terminal_counter"].most_common(1)[0][0] if meta["terminal_counter"] else ""
        first_mac = next(iter(meta["macs"])) if meta["macs"] else None
        dl_seq += 1
        delivery_rows.append((
            f"DL{dl_seq:06d}",
            cid,
            None,               # point_id 占位 NULL
            first_mac,          # device_id 取首设备
            media_type,
            plan_map[cid],
            None, None,         # 排期上/下刊 占位 NULL
            0,                  # on_shelf_count 占位 0
            now,
        ))
    conn.executemany(
        f"""
        INSERT INTO {TABLE_DELIVERY}
            (delivery_id, community_id, point_id, device_id, media_type,
             plan_id, schedule_start, schedule_end, on_shelf_count, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        delivery_rows,
    )

    # ── 7. 派生 t_sales（每小区一条占位）───────────────────────────────────────
    sales_rows: List[Tuple] = []
    sa_seq = 0
    for net_name in community_order:
        cid = community_map[net_name]
        sa_seq += 1
        sales_rows.append((
            f"SA{sa_seq:06d}",
            cid,
            "—",          # customer_name 无数据占位
            0.0,          # quote 占位
            None,         # selection_preference 待真实数据
            None,         # industry 待真实数据
            0.0,          # budget 占位
            now,
        ))
    conn.executemany(
        f"""
        INSERT INTO {TABLE_SALES}
            (sales_id, community_id, customer_name, quote, selection_preference,
             industry, budget, created_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        sales_rows,
    )

    # ── 8. 构建关联层 t_community_wide（默认策略见 §8）──────────────────────────
    wide_rows: List[Tuple] = []
    for net_name in community_order:
        cid = community_map[net_name]
        meta = comm_meta[cid]
        building_count = max(1, round(meta["point_count"] / 3))
        household_count = building_count * 100
        occupancy_rate = 0.92
        device_count = len(meta["macs"])
        # 设备数拆分（占位，注释标明）：大门 = round(设备数 * 0.3)，门禁 = 剩余
        gate_device_count = round(device_count * 0.3)              # 占位，待真实分布
        access_device_count = device_count - gate_device_count     # 占位，待真实分布
        # 其余业务字段默认占位（待真实数据接入）
        monthly_failure_rate = 0.0        # 占位
        historical_launch_count = 0       # 占位
        covered_industry_count = 0        # 占位
        ad_door_avg_price = 800.0         # 占位默认广告门均价
        access_lightbox_price = 1200.0    # 占位默认门禁灯箱价
        historical_customer_industry = "" # 占位
        wide_rows.append((
            cid, household_count, occupancy_rate, building_count,
            gate_device_count, access_device_count,
            monthly_failure_rate, historical_launch_count, covered_industry_count,
            ad_door_avg_price, access_lightbox_price,
            historical_customer_industry,
            None, None,   # gps 缺失留 NULL（待补坐标后接空间算法）
        ))
    conn.executemany(
        f"""
        INSERT INTO {TABLE_COMMUNITY_WIDE}
            (community_id, household_count, occupancy_rate, building_count,
             gate_device_count, access_device_count,
             monthly_failure_rate, historical_launch_count, covered_industry_count,
             ad_door_avg_price, access_lightbox_price,
             historical_customer_industry, gps_lng, gps_lat)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        wide_rows,
    )

    conn.commit()
    return {
        "t_media_l9": len(media_rows),
        "t_community": len(community_rows),
        "t_device": len(device_rows),
        "t_delivery": len(delivery_rows),
        "t_sales": len(sales_rows),
        "t_community_wide": len(wide_rows),
        "community_count": len(community_order),
        "device_count": len(devices),
    }


def build_all(xls_path: str) -> Dict[str, any]:
    """
    全量构建入口（幂等）。

    流程：建表 → 导入+派生 → 注册算法 → 计算指标。

    Args:
        xls_path: 「智能屏L9.xls」路径（含 sheet「媒体列表」）
    Returns:
        Dict: 各阶段统计
    """
    xls_path = str(xls_path)
    if not Path(xls_path).exists():
        raise FileNotFoundError(f"xls 文件不存在: {xls_path}")

    conn = _connect()
    try:
        # ① 幂等建表
        create_tables(conn)
        # ② 导入 + 派生宽表
        imp = import_media_and_derive(conn, xls_path)
        # ③ 注册 19 算法 → t_algorithm
        alg_n = register_algorithms(conn)
        # ④ 计算 39 指标 → t_poi_indicators
        ind_n = generate_indicators(conn)
        # ⑤ 收尾：WAL 检查点截断，确保主库文件自包含（便于提交 git）
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.commit()

        return {
            "xls_path": xls_path,
            "import": imp,
            "algorithms": alg_n,
            "indicators_rows": ind_n,
            "built_at": datetime.now().isoformat(timespec="seconds"),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    # 允许直接运行：python -m app.smart_screen.build_db
    import sys
    default_xls = r"D:/BaiduNetdiskDownload/Other/皓邻/智能屏L9.xls"
    arg = sys.argv[1] if len(sys.argv) > 1 else default_xls
    summary = build_all(arg)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
