"""青柠智能助手 — 角色权限控制（RBAC）与字段脱敏。

设计要点：
- ``Role`` 枚举是全模块唯一的角色真相来源，任何地方都不得硬编码 ``"sale"`` 等字符串。
- ``check_permission(role, action)`` 是越权拦截的唯一闸门：返回 ``False`` 时调用方
  **不得**继续访问底层 DB / 工具，必须直接拦截。
- 字段脱敏 ``mask_record`` 针对 PII（手机号 / 电话 / 身份证 / 邮箱 / 详细地址等），
  对销售、媒介等外部角色默认脱敏；工程、商业开发为内部可信角色，可见原始值。

动作（action）常量集中定义于此，意图识别与编排层均引用同一套常量，避免漂移。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set

# ─────────────────────────────────────────────────────────────
# 角色枚举（全模块唯一的角色真相来源）
# ─────────────────────────────────────────────────────────────

class Role(str, Enum):
    """青柠智能助手四角色。

    value 即 API 透传的字符串，便于直接序列化与比对。
    """

    SALE = "sale"          # 销售
    MEDIA = "media"        # 媒介
    ENGINEER = "engineer"  # 工程
    DEVELOPER = "developer"  # 商业开发

    @classmethod
    def from_str(cls, value: str) -> Optional["Role"]:
        """将任意字符串安全转换为 Role；非法值返回 ``None``（而非抛错）。"""
        if isinstance(value, Role):
            return value
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            return None


# ─────────────────────────────────────────────────────────────
# 动作常量（意图识别 / 编排层共享）
# ─────────────────────────────────────────────────────────────

ACTION_POINT_QUERY = "point_query"      # 点位列表查询
ACTION_POINT_COUNT = "point_count"      # 点位计数（含城市过滤）
ACTION_CLIENT_QUERY = "client_query"    # 客户通讯录查询
ACTION_REPORT_SUBMIT = "report_submit"  # 报备（演示态）
ACTION_POINT_LOCK = "point_lock"        # 锁点（演示态）
ACTION_POINT_EXPORT = "point_export"    # 导点（演示态）
ACTION_DOC_GENERATE = "doc_generate"    # 文档生成（真实链路）
ACTION_MAP_QUERY = "map_query"          # 地图地理编码 / POI
ACTION_SANDBOX_EXEC = "sandbox_exec"    # 沙箱命令执行（内部角色）
ACTION_GENERAL = "general"              # 通用对话

# 演示态动作集合：这些动作走「框架 + 模拟」，返回必须带 demo:true
DEMO_ACTIONS: Set[str] = {
    ACTION_REPORT_SUBMIT,
    ACTION_POINT_LOCK,
    ACTION_POINT_EXPORT,
}

# 内部可信角色：可见脱敏字段原始值、可执行沙箱
_TRUSTED_ROLES: Set[Role] = {Role.ENGINEER, Role.DEVELOPER}

# ─────────────────────────────────────────────────────────────
# 权限矩阵
# ─────────────────────────────────────────────────────────────

# 通用对话（general）是所有角色的基础能力：助手必须能聊天，
# 但聊天依赖 LLM，LLM 不可用时由 /chat 显式返回 503（绝不静默 mock）。
_GENERAL_FOR_ALL = {ACTION_GENERAL}

ROLE_PERMISSIONS: Dict[Role, Set[str]] = {
    Role.SALE: {
        ACTION_POINT_QUERY,
        ACTION_POINT_COUNT,
        ACTION_CLIENT_QUERY,
        ACTION_REPORT_SUBMIT,
        ACTION_DOC_GENERATE,
        ACTION_MAP_QUERY,
    } | _GENERAL_FOR_ALL,
    Role.MEDIA: {
        ACTION_POINT_QUERY,
        ACTION_POINT_COUNT,
        ACTION_CLIENT_QUERY,
        ACTION_REPORT_SUBMIT,
        ACTION_POINT_LOCK,
        ACTION_POINT_EXPORT,
        ACTION_DOC_GENERATE,
        ACTION_MAP_QUERY,
    } | _GENERAL_FOR_ALL,
    Role.ENGINEER: {
        ACTION_POINT_QUERY,
        ACTION_POINT_COUNT,
        ACTION_CLIENT_QUERY,
        ACTION_POINT_LOCK,
        ACTION_POINT_EXPORT,
        ACTION_DOC_GENERATE,
        ACTION_MAP_QUERY,
        ACTION_SANDBOX_EXEC,
    } | _GENERAL_FOR_ALL,
    Role.DEVELOPER: {
        ACTION_POINT_QUERY,
        ACTION_POINT_COUNT,
        ACTION_CLIENT_QUERY,
        ACTION_REPORT_SUBMIT,
        ACTION_DOC_GENERATE,
        ACTION_MAP_QUERY,
        ACTION_SANDBOX_EXEC,
    } | _GENERAL_FOR_ALL,
}


def check_permission(role: Any, action: str) -> bool:
    """RBAC 越权闸门。

    返回 ``False`` 的情形：
    - 角色非法（不在 ``Role`` 枚举内）
    - 动作不在该角色权限集合内

    调用方在拿到 ``False`` 后**必须**直接拦截，不得访问底层 DB / 工具。
    """
    resolved = Role.from_str(role) if not isinstance(role, Role) else role
    if resolved is None:
        return False
    return action in ROLE_PERMISSIONS.get(resolved, set())


def is_demo_action(action: str) -> bool:
    """判断某个动作是否为演示态（模拟）动作。"""
    return action in DEMO_ACTIONS


def role_is_trusted(role: Any) -> bool:
    """角色是否为内部可信角色（可见脱敏字段原始值）。"""
    resolved = Role.from_str(role) if not isinstance(role, Role) else role
    return resolved in _TRUSTED_ROLES


# ─────────────────────────────────────────────────────────────
# 字段脱敏
# ─────────────────────────────────────────────────────────────

# 命中即脱敏的字段名关键字（不区分大小写）
_SENSITIVE_KEYWORDS: List[str] = [
    "手机",
    "电话",
    "联系",
    "身份证",
    "证件",
    "邮箱",
    "mail",
    "email",
    "详细地址",
    "住址",
    "微信",
    "qq",
    "薪资",
    "收入",
]

_MASKED_PLACEHOLDER = "***已脱敏***"


def _is_sensitive_field(field_name: str) -> bool:
    name = field_name.lower()
    return any(kw in name for kw in _SENSITIVE_KEYWORDS)


def mask_record(role: Any, record: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    """对单条记录做字段脱敏。

    Args:
        role: 调用角色（任意可解析为 ``Role`` 的值）。
        record: 原始记录字典。

    Returns:
        (脱敏后的记录, 被脱敏的字段名列表)

    内部可信角色（工程 / 商业开发）直接返回原始记录，不做脱敏。
    """
    if role_is_trusted(role):
        return dict(record), []

    masked_fields: List[str] = []
    out: Dict[str, Any] = {}
    for key, value in record.items():
        if _is_sensitive_field(key):
            out[key] = _MASKED_PLACEHOLDER
            masked_fields.append(key)
        else:
            out[key] = value
    return out, masked_fields


def mask_records(role: Any, records: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
    """批量脱敏，并汇总所有出现过的脱敏字段名（去重）。"""
    out: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for rec in records:
        masked, fields = mask_record(role, rec)
        out.append(masked)
        seen.update(fields)
    return out, sorted(seen)


def list_roles() -> List[Dict[str, Any]]:
    """返回四角色（sale / media / engineer / developer）的结构化描述。

    供 ``GET /roles`` 端点使用；单一事实来源即 ``Role`` 枚举与 ``ROLE_PERMISSIONS``。
    """
    _ROLE_META: Dict[Role, tuple[str, str]] = {
        Role.SALE: (
            "销售",
            "面向客户的销售角色：可查点位 / 客户、报备、生成文档、地图查询。",
        ),
        Role.MEDIA: (
            "媒介",
            "媒介策划角色：在销售能力基础上额外可锁点、导点。",
        ),
        Role.ENGINEER: (
            "工程",
            "内部工程角色：可锁点、导点、执行沙箱命令。",
        ),
        Role.DEVELOPER: (
            "商业开发",
            "内部商业开发角色：可报备、生成文档、执行沙箱命令。",
        ),
    }
    out: List[Dict[str, Any]] = []
    for role in Role:
        name, desc = _ROLE_META.get(role, (role.value, ""))
        actions = sorted(ROLE_PERMISSIONS.get(role, set()))
        out.append(
            {
                "code": role.value,
                "name": name,
                "description": desc,
                "capabilities": actions,
                "tools": actions,
            }
        )
    return out
