"""
青柠智能助手 — 业务工作流（骨架，T04 实现）。

规划能力（**演示态**，一律返回 ``demo: true`` + ``demo_note``）
----------------------------------------------------------------
- ``workflow_report``       媒体报备
- ``workflow_lock_point``   点位锁定
- ``workflow_export_point`` 点位导出下单

按已拍板的产品决策：操作类（写入/下单）**一律模拟**，
禁止真实写入生产系统。所有返回必须经 ``constants.demo_response()`` 包装。

本轮只提供可 import 的签名与状态机定义，不含实现逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── 工作流状态 ────────────────────────────────────────────────────────────
STATUS_PENDING: str = "pending"
STATUS_RUNNING: str = "running"
STATUS_SUCCESS: str = "success"
STATUS_FAILED: str = "failed"

#: 全部状态码
ALL_STATUSES: List[str] = [STATUS_PENDING, STATUS_RUNNING, STATUS_SUCCESS, STATUS_FAILED]


@dataclass
class WorkflowResult:
    """工作流执行结果（演示态）。"""

    workflow: str = ""
    status: str = STATUS_PENDING
    task_id: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)


async def workflow_report(
    campaign_name: str,
    point_ids: List[str],
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """
    媒体报备工作流（演示态）。

    Notes
    -----
    TODO(T04): 生成模拟报备单号与步骤流水，
    返回值必须用 ``constants.demo_response()`` 包装。
    """
    raise NotImplementedError("workflows.workflow_report 将在 T04 实现")


async def workflow_lock_point(
    point_ids: List[str],
    lock_days: int = 7,
    operator: Optional[str] = None,
) -> Dict[str, Any]:
    """
    点位锁定工作流（演示态）。

    Notes
    -----
    TODO(T04): 模拟锁点结果，返回 ``demo: true``。
    """
    raise NotImplementedError("workflows.workflow_lock_point 将在 T04 实现")


async def workflow_export_point(
    city: Optional[str] = None,
    resource_type: Optional[str] = None,
    file_format: str = "xlsx",
) -> Dict[str, Any]:
    """
    点位导出下单工作流（演示态）。

    Notes
    -----
    TODO(T04): 查询走真实库、导出文件走 skills，
    但「下单」动作模拟，整体返回 ``demo: true``。
    """
    raise NotImplementedError("workflows.workflow_export_point 将在 T04 实现")
