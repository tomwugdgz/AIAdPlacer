"""
智能屏资源子系统（Smart Screen L9）— 全局配置常量。

本模块是子系统唯一的路径 / 表名 / 层名事实来源（Single Source of Truth）：
- 统一数据库路径常量 SS_DB_PATH，禁止业务代码硬编码路径
- 行工厂 ROW_FACTORY = sqlite3.Row（与 db_dao 保持一致）
- 各层表名、层名常量

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

import sqlite3
from pathlib import Path

# ── 路径常量 ────────────────────────────────────────────────────────────────────
# 当前文件: backend/app/smart_screen/ss_config.py
#   parent            -> smart_screen
#   parent.parent     -> app
#   parent.parent.parent -> backend  (项目后端根目录)
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
# 子系统独立库路径（与 qinlin_local.db 物理隔离）
SS_DB_PATH: Path = BASE_DIR / "data" / "smart_screen_l9.db"

# ── 行工厂（统一返回 sqlite3.Row，业务层用 dict(row) 转字典）──────────────────────
ROW_FACTORY = sqlite3.Row

# 建库后统一开启 WAL（写前日志），提升并发读性能
JOURNAL_MODE = "WAL"

# ── 层名常量（四层架构）─────────────────────────────────────────────────────────
LAYER_INPUT = "input"            # 输入层：4 孤岛（媒体/小区/设备/投放/销售）
LAYER_ASSOCIATION = "association"  # 关联层：5 纽带宽表
LAYER_ALGORITHM = "algorithm"    # 算法层：19 算法注册表
LAYER_OUTPUT = "output"          # 产出层：39 指标 7 大类

# ── 表名常量（统一 t_ 前缀 + 英文）──────────────────────────────────────────────
TABLE_MEDIA = "t_media_l9"            # 输入层①：原始媒体列表（12 列）
TABLE_COMMUNITY = "t_community"       # 输入层②：BD 小区（派生）
TABLE_DEVICE = "t_device"             # 输入层③：工程设备（派生）
TABLE_DELIVERY = "t_delivery"         # 输入层④：媒介投放（派生占位）
TABLE_SALES = "t_sales"               # 输入层⑤：销售选点（派生占位）
TABLE_COMMUNITY_WIDE = "t_community_wide"  # 关联层：小区级宽表
TABLE_ALGORITHM = "t_algorithm"       # 算法层：19 算法注册表
TABLE_INDICATORS = "t_poi_indicators" # 产出层：39 指标宽表

# xls 原始列顺序（严格对应「智能屏L9.xls」sheet「媒体列表」）
XLS_SHEET_NAME = "媒体列表"
XLS_COLUMNS = [
    "所属省份",
    "所属城市",
    "区/县",
    "网点名称",
    "楼盘类型",
    "住户数",
    "楼盘价格",
    "点位名称",
    "详细地址",
    "点位ID",
    "MAC",
    "终端型号",
]

# 派生关联键生成规则（供 build_db 使用）
COMMUNITY_ID_PREFIX = "CM"   # 小区 ID 前缀，如 CM00001
PLAN_ID_PREFIX = "PL"        # 计划 ID 前缀，如 PL00001
DEVICE_STATUS_ONLINE = "在线"  # 设备默认状态


def get_connection() -> sqlite3.Connection:
    """
    获取子系统数据库连接（行工厂 + WAL）。

    注意：业务代码应优先使用 ss_dao.get_ss_db_connection()，
    此处仅作为无需 DAO 时的便捷入口。

    Returns:
        sqlite3.Connection: 已配置 row_factory / WAL 的连接
    """
    conn = sqlite3.connect(str(SS_DB_PATH))
    conn.row_factory = ROW_FACTORY
    conn.execute(f"PRAGMA journal_mode={JOURNAL_MODE}")
    return conn
