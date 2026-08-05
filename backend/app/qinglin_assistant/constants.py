"""
青柠智能助手 — 全局常量与响应约定。

本模块**不依赖任何其他 qinglin_assistant 子模块**，可被包内任意模块安全导入，
不会产生循环引用。

演示态规范（全模块统一，禁止各文件自行拼装）
----------------------------------------------
- 未接真实后端 / 模拟写操作的响应：``"demo": true`` + ``"demo_note"``
- 真实数据链路（如知识库真查、文档生成）的响应：``"demo": false``

使用示例
--------
    from app.qinglin_assistant.constants import demo_response, real_response

    return demo_response({"order_id": "MOCK-001"})
    return real_response({"total": 8114, "rows": rows})
"""

from __future__ import annotations

from typing import Any, Dict, Optional

#: 模块标识（对内代码标识符统一 qinglin）
MODULE_NAME: str = "qinglin_assistant"
#: 对外品牌名（统一「青柠」）
BRAND_NAME: str = "青柠"
#: 模块版本
MODULE_VERSION: str = "0.1.0"

#: 演示态标准提示语
DEMO_NOTE: str = "演示态，未执行真实写操作"


def demo_response(
    data: Optional[Dict[str, Any]] = None,
    note: str = DEMO_NOTE,
) -> Dict[str, Any]:
    """
    包装一个**演示态**响应（模拟返回，未触达真实后端写操作）。

    Parameters
    ----------
    data : dict | None
        业务数据载荷，会被合并到返回字典的顶层。
    note : str
        演示态说明文案，默认使用 :data:`DEMO_NOTE`。

    Returns
    -------
    dict
        含 ``demo=True`` 与 ``demo_note`` 的响应字典。
    """
    payload: Dict[str, Any] = dict(data or {})
    payload["demo"] = True
    payload["demo_note"] = note
    return payload


def real_response(data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    包装一个**真实链路**响应（数据来自真实数据库 / 真实计算）。

    Parameters
    ----------
    data : dict | None
        业务数据载荷，会被合并到返回字典的顶层。

    Returns
    -------
    dict
        含 ``demo=False`` 的响应字典。
    """
    payload: Dict[str, Any] = dict(data or {})
    payload["demo"] = False
    return payload
