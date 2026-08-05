"""青柠智能助手 — 意图识别。

策略：优先用 LLM（``generate_json``）做结构化意图识别；若 LLM 不可用或解析失败，
自动回退到**确定性关键词分类**，保证端点永远可用、且知识库查询能拿到真实数字。

识别结果 ``dict`` 结构：
- ``intent``：人类可读意图
- ``action``：与 RBAC 对应的动作常量
- ``params``：抽取的参数（point_type / city / keyword / address / command 等）
- ``confidence``：置信度（LLM 0.9，规则 0.7）
- ``source``：``"llm"`` 或 ``"rule"``

LLM 调用使用 ``asyncio.wait_for`` 设短超时（8s），避免 Ollama 未启动时长阻塞。
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from app.qinglin_assistant.llm.provider import get_llm_client
from app.qinglin_assistant.rbac.policy import (
    ACTION_CLIENT_QUERY,
    ACTION_DOC_GENERATE,
    ACTION_GENERAL,
    ACTION_MAP_QUERY,
    ACTION_POINT_COUNT,
    ACTION_POINT_EXPORT,
    ACTION_POINT_LOCK,
    ACTION_POINT_QUERY,
    ACTION_REPORT_SUBMIT,
    ACTION_SANDBOX_EXEC,
)
from app.qinglin_assistant.tools.kb_tools import POINT_TYPE_TO_TABLE

ALL_ACTIONS: List[str] = [
    ACTION_POINT_QUERY,
    ACTION_POINT_COUNT,
    ACTION_CLIENT_QUERY,
    ACTION_REPORT_SUBMIT,
    ACTION_POINT_LOCK,
    ACTION_POINT_EXPORT,
    ACTION_DOC_GENERATE,
    ACTION_MAP_QUERY,
    ACTION_SANDBOX_EXEC,
    ACTION_GENERAL,
]

# 常见城市（用于从消息中抽取城市 token；最终是否命中真实库由 KB 层用真实统计校验）
_CITIES = [
    "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "重庆",
    "天津", "苏州", "长沙", "郑州", "青岛", "宁波", "东莞", "佛山", "无锡", "合肥",
    "昆明", "厦门", "济南", "福州", "温州", "石家庄", "哈尔滨", "沈阳", "大连", "南宁",
    "贵阳", "海口", "常州", "珠海", "中山", "惠州", "南昌", "兰州", "太原", "嘉兴",
]

# 点位类型关键词 -> 中文表名（特定项放前面，避免被泛化关键词抢先匹配）
_POINT_TYPE_KEYWORDS = [
    ("智能屏L9", ["智能屏l9", "l9智能屏", "l9"]),
    ("智能屏202507", ["智能屏202507", "202507智能屏", "202507"]),
    ("商场LED点位", ["商场led", "商场 led", "led", "商场屏", "商场led点位"]),
    ("道闸点位", ["道闸"]),
    ("单元门点位", ["单元门", "单元"]),
    ("门禁点位", ["门禁"]),
    ("智能屏202507", ["智能屏"]),  # 泛化兜底
]


def _detect_city(text: str) -> Optional[str]:
    for c in _CITIES:
        if c in text or (c + "市") in text:
            return c
    return None


def _detect_point_type(text: str) -> Optional[str]:
    low = text.lower()
    for table, kws in _POINT_TYPE_KEYWORDS:
        for kw in kws:
            if kw in low:
                return table
    return None


def _rule_based(message: str) -> Dict[str, Any]:
    """确定性关键词分类（LLM 不可用时的回退）。"""
    text = message.strip()
    low = text.lower()

    if any(k in text for k in ["报备", "报备单", "线索报备", "客户报备"]):
        return _pack(ACTION_REPORT_SUBMIT, "报备客户/项目", {"keyword": _extract_keyword(text)})
    if any(k in text for k in ["锁点", "锁定点位", "点位锁定"]):
        pt = _detect_point_type(text)
        return _pack(ACTION_POINT_LOCK, "锁定点位", {"point_type": pt, "city": _detect_city(text)})
    if any(k in text for k in ["导点", "导出点位", "导出资源", "点位导出"]):
        pt = _detect_point_type(text)
        return _pack(ACTION_POINT_EXPORT, "导出点位", {"point_type": pt, "city": _detect_city(text)})
    if any(k in low for k in ["生成文档", "生成报告", "导出文档", "生成方案", "docx", "pptx", "excel", "导出excel", "文档生成"]):
        return _pack(ACTION_DOC_GENERATE, "文档生成", {"doc_type": _detect_doc_type(text)})
    if any(k in text for k in ["坐标", "地理编码", "geocode", "经纬度", "定位地址"]):
        return _pack(ACTION_MAP_QUERY, "地图地理编码", {"address": _extract_address(text), "city": _detect_city(text)})
    if any(k in low for k in ["执行命令", "运行命令", "bash", "shell", "command", "执行脚本", "运行脚本"]):
        return _pack(ACTION_SANDBOX_EXEC, "沙箱命令执行", {"command": _extract_command(text)})
    if any(k in text for k in ["客户", "通讯录", "品牌", "决策城市"]):
        return _pack(ACTION_CLIENT_QUERY, "客户通讯录查询", {"keyword": _extract_keyword(text), "city": _detect_city(text)})

    pt = _detect_point_type(text)
    if pt:
        if any(k in text for k in ["多少", "数量", "总数", "几个", "一共", "共有", "几台", "几块"]):
            return _pack(ACTION_POINT_COUNT, "点位计数", {"point_type": pt, "city": _detect_city(text)})
        return _pack(ACTION_POINT_QUERY, "点位查询", {"point_type": pt, "city": _detect_city(text)})
    if "点位" in text or "资源" in text:
        return _pack(ACTION_POINT_QUERY, "点位查询", {"point_type": None, "city": _detect_city(text)})

    return _pack(ACTION_GENERAL, "通用对话", {})


def _pack(action: str, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "intent": intent,
        "action": action,
        "params": params,
        "confidence": 0.7,
        "source": "rule",
    }


def _detect_doc_type(text: str) -> str:
    low = text.lower()
    if "ppt" in low:
        return "pptx"
    if "excel" in low or "xlsx" in low:
        return "xlsx"
    return "docx"


def _extract_keyword(text: str) -> Optional[str]:
    # 提取「查/找/关于 X」中的 X（简单启发式）
    for sep in ["客户", "品牌", "关于", "查", "找", "搜"]:
        if sep in text:
            idx = text.index(sep) + len(sep)
            rest = text[idx:].strip(" ：:，。、")
            if rest:
                return rest[:20]
    return None


def _extract_address(text: str) -> Optional[str]:
    # 提取「地址/坐标 X」
    for sep in ["地址", "坐标", "位置", "geocode"]:
        if sep in text:
            idx = text.index(sep) + len(sep)
            rest = text[idx:].strip(" ：:，。、")
            if rest:
                return rest[:40]
    return None


def _clean_command(rest: str) -> str:
    """去除命令前后的引导词与标点，得到纯净的 shell 命令。"""
    cmd = rest.strip(" \t：:，。、；;\"'")
    # 依次去除常见引导词（shell / bash / 命令 / command / 脚本 / 以下 / 如下）
    changed = True
    while changed:
        changed = False
        for filler in ("shell", "bash", "命令", "command", "脚本", "以下", "如下"):
            low = cmd.lower()
            if low.startswith(filler):
                cmd = cmd[len(filler):].strip(" \t：:，。、；;\"'")
                changed = True
                break
    return cmd


def _extract_command(text: str) -> Optional[str]:
    for sep in ["执行命令", "运行命令", "执行脚本", "运行脚本", "执行", "运行"]:
        if sep in text:
            idx = text.index(sep) + len(sep)
            cmd = _clean_command(text[idx:])
            if cmd:
                return cmd[:200]
    # 未命中触发词：整条消息若像命令则直接采用
    return _clean_command(text)[:200]


async def _llm_recognize(client, message: str, role: str) -> Optional[Dict[str, Any]]:
    prompt = (
        "你是青柠智能对话助手的意图识别器。\n"
        f"当前用户角色：{role}\n"
        f"用户消息：{message}\n\n"
        "请从下列动作中选择最匹配的一个，并抽取参数，只返回 JSON（不要多余文字）：\n"
        "{\"intent\":\"<意图>\", \"action\":\"<动作>\", "
        "\"params\":{\"point_type\":\"<门禁点位|单元门点位|道闸点位|商场LED点位|智能屏L9|智能屏202507|null>\", "
        "\"city\":\"<城市|null>\", \"keyword\":\"<关键词|null>\", \"address\":\"<地址|null>\", "
        "\"command\":\"<命令|null>\"}}\n"
        "可选 action：\n" + "、".join(ALL_ACTIONS)
    )
    system = "你是意图识别器，只输出 JSON，不要解释。"
    try:
        raw = await asyncio.wait_for(
            client.generate_json(prompt, system_prompt=system, temperature=0.2),
            timeout=8.0,
        )
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    action = raw.get("action")
    if action not in ALL_ACTIONS:
        return None
    params = raw.get("params") or {}
    # 把 LLM 可能返回的 "null" 字符串归一化
    for k, v in list(params.items()):
        if v in (None, "null", "None"):
            params[k] = None
    return {
        "intent": raw.get("intent", action),
        "action": action,
        "params": params,
        "confidence": 0.9,
        "source": "llm",
    }


class IntentRecognizer:
    """意图识别器：LLM 优先，规则回退。"""

    def __init__(self, llm_client=None):
        self._llm = llm_client or get_llm_client()

    async def recognize(self, message: str, role: str = "sale") -> Dict[str, Any]:
        # 先尝试 LLM
        try:
            llm_result = await _llm_recognize(self._llm, message, role)
            if llm_result:
                return llm_result
        except Exception:
            pass
        # 回退到确定性规则
        return _rule_based(message)


# 便捷单例
intent_recognizer = IntentRecognizer()
