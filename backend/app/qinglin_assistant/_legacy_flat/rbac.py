"""
青柠智能助手 — 角色权限控制（RBAC）。

四个业务角色
------------
- ``sale``      销售：客户沟通、方案报价、点位查询
- ``media``     媒介：资源盘点、排期锁点、报备执行
- ``engineer``  工程：点位运维、设备巡检、施工派单
- ``developer`` 开发：接口调试、数据校验、沙箱命令

每个角色持有一份**工具白名单**，未在白名单中的工具一律拒绝调用。
白名单在 T02 接入真实工具时继续沿用，工具名需与 ``tools.py`` 中注册名一致。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ── 角色码 ────────────────────────────────────────────────────────────────
ROLE_SALE: str = "sale"
ROLE_MEDIA: str = "media"
ROLE_ENGINEER: str = "engineer"
ROLE_DEVELOPER: str = "developer"

#: 全部合法角色码
ALL_ROLES: List[str] = [ROLE_SALE, ROLE_MEDIA, ROLE_ENGINEER, ROLE_DEVELOPER]

# ── 工具名常量（与 tools.py / skills.py / workflows.py 注册名保持一致）──────
TOOL_QUERY_RESOURCE: str = "query_resource"          # 点位资源查询（真实库）
TOOL_QUERY_KNOWLEDGE: str = "query_knowledge"        # 知识库检索（真实库）
TOOL_QUERY_CUSTOMER: str = "query_customer"          # 客户通讯录查询（真实库）
TOOL_QUERY_STATS: str = "query_stats"                # 资源统计（真实库）
TOOL_GEN_DOCX: str = "generate_docx"                 # 生成 Word
TOOL_GEN_XLSX: str = "generate_xlsx"                 # 生成 Excel
TOOL_GEN_PPTX: str = "generate_pptx"                 # 生成 PPT
TOOL_GEN_PDF: str = "generate_pdf"                   # 生成 PDF
TOOL_WORKFLOW_REPORT: str = "workflow_report"        # 报备（演示态）
TOOL_WORKFLOW_LOCK: str = "workflow_lock_point"      # 锁点（演示态）
TOOL_WORKFLOW_EXPORT: str = "workflow_export_point"  # 导点（演示态）
TOOL_SANDBOX_EXEC: str = "sandbox_exec"              # 沙箱命令执行

#: 角色 -> 可用工具白名单
ROLE_TOOL_WHITELIST: Dict[str, List[str]] = {
    ROLE_SALE: [
        TOOL_QUERY_RESOURCE,
        TOOL_QUERY_KNOWLEDGE,
        TOOL_QUERY_CUSTOMER,
        TOOL_QUERY_STATS,
        TOOL_GEN_DOCX,
        TOOL_GEN_XLSX,
        TOOL_GEN_PPTX,
        TOOL_GEN_PDF,
    ],
    ROLE_MEDIA: [
        TOOL_QUERY_RESOURCE,
        TOOL_QUERY_KNOWLEDGE,
        TOOL_QUERY_STATS,
        TOOL_GEN_XLSX,
        TOOL_GEN_PPTX,
        TOOL_WORKFLOW_REPORT,
        TOOL_WORKFLOW_LOCK,
        TOOL_WORKFLOW_EXPORT,
    ],
    ROLE_ENGINEER: [
        TOOL_QUERY_RESOURCE,
        TOOL_QUERY_KNOWLEDGE,
        TOOL_QUERY_STATS,
        TOOL_GEN_DOCX,
        TOOL_GEN_XLSX,
        TOOL_WORKFLOW_EXPORT,
    ],
    ROLE_DEVELOPER: [
        TOOL_QUERY_RESOURCE,
        TOOL_QUERY_KNOWLEDGE,
        TOOL_QUERY_CUSTOMER,
        TOOL_QUERY_STATS,
        TOOL_GEN_DOCX,
        TOOL_GEN_XLSX,
        TOOL_GEN_PPTX,
        TOOL_GEN_PDF,
        TOOL_WORKFLOW_REPORT,
        TOOL_WORKFLOW_LOCK,
        TOOL_WORKFLOW_EXPORT,
        TOOL_SANDBOX_EXEC,
    ],
}

#: 角色元信息（供前端渲染角色选择器）
ROLE_METADATA: Dict[str, Dict[str, Any]] = {
    ROLE_SALE: {
        "name": "销售",
        "description": "面向客户的方案沟通与报价支持，可查询点位资源、客户信息并生成方案文档。",
        "capabilities": ["点位查询", "客户查询", "知识库检索", "方案文档生成"],
        "system_prompt": (
            "你现在是青柠的销售顾问，擅长向广告主解释 pDOOH 户外广告的价值、"
            "点位覆盖与报价逻辑。回答要有说服力且数据可查证。"
        ),
    },
    ROLE_MEDIA: {
        "name": "媒介",
        "description": "负责媒体资源盘点、排期与投放执行，可发起报备、锁点、导点等流程。",
        "capabilities": ["资源盘点", "统计分析", "报备/锁点/导点（演示态）", "排期表生成"],
        "system_prompt": (
            "你现在是青柠的媒介执行专员，熟悉全国点位资源库存、排期规则与"
            "报备锁点流程。回答要精确到资源类型与数量。"
        ),
    },
    ROLE_ENGINEER: {
        "name": "工程",
        "description": "负责点位运维与设备巡检，可查询点位明细并导出施工清单。",
        "capabilities": ["点位明细查询", "施工清单导出", "巡检报告生成"],
        "system_prompt": (
            "你现在是青柠的工程运维工程师，关注点位设备状态、安装位置与"
            "施工可行性。回答要具体到楼盘、地址与媒体面数。"
        ),
    },
    ROLE_DEVELOPER: {
        "name": "开发",
        "description": "平台开发与集成调试角色，拥有全部工具权限，包括受限沙箱命令。",
        "capabilities": ["全部查询工具", "全部文档生成", "全部工作流", "沙箱命令执行"],
        "system_prompt": (
            "你现在是青柠平台的研发工程师助手，熟悉 A2A / MCP 协议与本平台"
            "数据结构。回答可以包含接口字段、SQL 与调试建议。"
        ),
    },
}


class PermissionDeniedError(PermissionError):
    """角色无权调用目标工具时抛出。"""


def is_valid_role(role: str) -> bool:
    """
    判断角色码是否合法。

    Parameters
    ----------
    role : str
        角色码。

    Returns
    -------
    bool
        合法返回 True。
    """
    return (role or "").strip().lower() in ROLE_TOOL_WHITELIST


def normalize_role(role: str) -> str:
    """
    归一化角色码（去空格 + 转小写）。

    Parameters
    ----------
    role : str
        原始角色码。

    Returns
    -------
    str
        归一化后的角色码。
    """
    return (role or "").strip().lower()


def check_permission(role: str, tool_name: str) -> bool:
    """
    校验某角色是否有权调用指定工具。

    Parameters
    ----------
    role : str
        角色码，如 ``"sale"``。
    tool_name : str
        工具名，如 ``"query_resource"``。

    Returns
    -------
    bool
        有权返回 True；角色非法或工具不在白名单返回 False。
    """
    normalized = normalize_role(role)
    whitelist = ROLE_TOOL_WHITELIST.get(normalized)
    if whitelist is None:
        return False
    return (tool_name or "").strip() in whitelist


def assert_permission(role: str, tool_name: str) -> None:
    """
    断言权限，无权时抛出 :class:`PermissionDeniedError`。

    Parameters
    ----------
    role : str
        角色码。
    tool_name : str
        工具名。

    Raises
    ------
    PermissionDeniedError
        角色非法或无该工具权限。
    """
    if not is_valid_role(role):
        raise PermissionDeniedError(
            f"未知角色 {role!r}，合法角色：{ALL_ROLES}"
        )
    if not check_permission(role, tool_name):
        raise PermissionDeniedError(
            f"角色 {normalize_role(role)!r} 无权调用工具 {tool_name!r}"
        )


def get_role_tools(role: str) -> List[str]:
    """
    获取角色的工具白名单副本。

    Parameters
    ----------
    role : str
        角色码。

    Returns
    -------
    list[str]
        工具名列表；角色非法返回空列表。
    """
    return list(ROLE_TOOL_WHITELIST.get(normalize_role(role), []))


def get_system_prompt(role: str) -> Optional[str]:
    """
    获取角色对应的系统提示词。

    Parameters
    ----------
    role : str
        角色码。

    Returns
    -------
    str | None
        系统提示词；角色非法返回 None。
    """
    meta = ROLE_METADATA.get(normalize_role(role))
    return meta.get("system_prompt") if meta else None


def list_roles() -> List[Dict[str, Any]]:
    """
    列出全部角色元信息，供前端渲染角色选择器。

    Returns
    -------
    list[dict]
        每项含 ``code`` / ``name`` / ``description`` / ``capabilities`` / ``tools``。
    """
    roles: List[Dict[str, Any]] = []
    for code in ALL_ROLES:
        meta = ROLE_METADATA[code]
        roles.append(
            {
                "code": code,
                "name": meta["name"],
                "description": meta["description"],
                "capabilities": list(meta["capabilities"]),
                "tools": list(ROLE_TOOL_WHITELIST[code]),
            }
        )
    return roles
