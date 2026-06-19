"""
pDOOH Python 客户端库 - 工具函数模块

提供响应解析、参数验证等通用工具函数。
"""

from typing import Any, Dict, Optional
import json


def parse_response(response: Any) -> Dict[str, Any]:
    """解析 HTTP 响应为字典格式。

    Args:
        response: HTTP 响应对象（支持 httpx 或 requests 响应）。

    Returns:
        解析后的字典数据。

    Raises:
        ValueError: 当响应内容不是有效的 JSON 时抛出。
    """
    if hasattr(response, "json"):
        return response.json()
    elif isinstance(response, dict):
        return response
    else:
        raise ValueError("无法解析的响应类型")


def validate_required_params(params: Dict[str, Any], required: list[str]) -> None:
    """验证必需参数是否存在。

    Args:
        params: 参数字典。
        required: 必需参数名列表。

    Raises:
        ValueError: 当缺少必需参数时抛出。
    """
    missing = [key for key in required if key not in params or params[key] is None]
    if missing:
        raise ValueError(f"缺少必需参数: {', '.join(missing)}")


def build_query_params(**kwargs: Any) -> Dict[str, Any]:
    """构建查询参数字典，过滤掉 None 值。

    Args:
        **kwargs: 键值对参数。

    Returns:
        过滤后的参数字典，不包含值为 None 的键。
    """
    return {k: v for k, v in kwargs.items() if v is not None}


def format_json(data: Any, indent: int = 2) -> str:
    """将数据格式化为格式化的 JSON 字符串。

    Args:
        data: 要格式化的数据。
        indent: 缩进空格数，默认 2。

    Returns:
        格式化的 JSON 字符串。
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """安全获取字典中的值。

    Args:
        data: 数据源字典。
        key: 键名。
        default: 默认值，当键不存在时返回。

    Returns:
        键对应的值，或默认值。
    """
    return data.get(key, default)


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """合并多个字典。

    Args:
        *dicts: 要合并的字典列表。

    Returns:
        合并后的新字典。
    """
    result: Dict[str, Any] = {}
    for d in dicts:
        if d:
            result.update(d)
    return result
