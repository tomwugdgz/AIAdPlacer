"""
青柠智能助手 — 业务工具（骨架，T02 实现）。

规划能力
--------
查询类工具走**真实链路**（复用 ``app.db_dao``，返回 ``demo: false``）：

- ``query_resource``   点位资源查询
- ``query_knowledge``  知识库检索
- ``query_customer``   客户通讯录查询
- ``query_stats``      资源统计

工具调用前必须经 ``rbac.assert_permission(role, tool_name)`` 校验。

本轮只提供可 import 的签名与注册表，不含实现逻辑。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from app.qinglin_assistant import rbac

#: 工具注册表：工具名 -> 可调用对象。T02 填充。
TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {}


async def query_resource(
    city: Optional[str] = None,
    resource_type: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    查询点位资源（真实库）。

    Parameters
    ----------
    city : str | None
        城市名筛选。
    resource_type : str | None
        资源类型，对应 ``db_dao.type_to_table`` 的键。
    keyword : str | None
        楼盘名 / 地址关键词。
    limit : int
        返回条数上限。

    Returns
    -------
    dict
        ``real_response`` 包装的查询结果。

    Notes
    -----
    TODO(T02): 调用 ``app.db_dao`` 真实查询 qinglin_local.db。
    """
    raise NotImplementedError("tools.query_resource 将在 T02 实现")


async def query_knowledge(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    知识库检索（真实库）。

    Parameters
    ----------
    query : str
        检索关键词。
    top_k : int
        返回条数。

    Returns
    -------
    dict
        ``real_response`` 包装的检索结果。

    Notes
    -----
    TODO(T02): 复用 ``app.services.knowledge_base`` / ``rag_kb``，禁止重造检索层。
    """
    raise NotImplementedError("tools.query_knowledge 将在 T02 实现")


async def query_customer(keyword: str, limit: int = 20) -> Dict[str, Any]:
    """
    客户通讯录查询（真实库 客户通讯录 表）。

    Notes
    -----
    TODO(T02): 接 db_dao，注意敏感字段脱敏。
    """
    raise NotImplementedError("tools.query_customer 将在 T02 实现")


async def query_stats(group_by: str = "城市", resource_type: Optional[str] = None) -> Dict[str, Any]:
    """
    资源统计（真实库）。

    Notes
    -----
    TODO(T02): 接 db_dao 的分组统计接口。
    """
    raise NotImplementedError("tools.query_stats 将在 T02 实现")


def list_tools(role: Optional[str] = None) -> List[str]:
    """
    列出工具名。

    Parameters
    ----------
    role : str | None
        指定角色时，仅返回该角色白名单内的工具。

    Returns
    -------
    list[str]
        工具名列表。
    """
    names = sorted(TOOL_REGISTRY.keys())
    if role is None:
        return names
    return [name for name in names if rbac.check_permission(role, name)]


async def dispatch(role: str, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
    """
    按角色权限分发工具调用。

    Parameters
    ----------
    role : str
        角色码。
    tool_name : str
        工具名。
    **kwargs
        透传给目标工具的参数。

    Returns
    -------
    dict
        工具执行结果。

    Raises
    ------
    rbac.PermissionDeniedError
        角色无权调用该工具。

    Notes
    -----
    TODO(T02): 校验通过后从 TOOL_REGISTRY 取出并 await 执行。
    """
    raise NotImplementedError("tools.dispatch 将在 T02 实现")
