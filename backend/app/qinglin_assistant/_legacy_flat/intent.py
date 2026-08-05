"""
青柠智能助手 — 意图识别（骨架，T02 实现）。

规划能力
--------
- 基于 LLM 的意图分类（复用 ``llm.get_llm_provider()``）
- 规则前置匹配，命中关键词直接短路，降低 LLM 调用量
- 输出结构化 :class:`IntentResult`，供 ``tools.py`` 分发工具调用

本轮只提供可 import 的签名与数据结构，不含实现逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── 意图码 ────────────────────────────────────────────────────────────────
INTENT_CHITCHAT: str = "chitchat"            # 闲聊 / 通用问答
INTENT_QUERY_RESOURCE: str = "query_resource"  # 点位资源查询
INTENT_QUERY_KNOWLEDGE: str = "query_knowledge"  # 知识库检索
INTENT_GENERATE_DOC: str = "generate_doc"    # 文档生成
INTENT_WORKFLOW: str = "workflow"            # 报备 / 锁点 / 导点
INTENT_UNKNOWN: str = "unknown"              # 无法识别

#: 全部意图码
ALL_INTENTS: List[str] = [
    INTENT_CHITCHAT,
    INTENT_QUERY_RESOURCE,
    INTENT_QUERY_KNOWLEDGE,
    INTENT_GENERATE_DOC,
    INTENT_WORKFLOW,
    INTENT_UNKNOWN,
]


@dataclass
class IntentResult:
    """意图识别结果。"""

    intent: str = INTENT_UNKNOWN
    confidence: float = 0.0
    tool_name: Optional[str] = None
    slots: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)


async def detect_intent(
    message: str,
    role: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> IntentResult:
    """
    识别用户消息意图。

    Parameters
    ----------
    message : str
        用户消息。
    role : str
        当前角色码，用于约束候选工具范围。
    history : list[dict] | None
        最近若干轮对话历史。

    Returns
    -------
    IntentResult
        结构化意图结果。

    Notes
    -----
    TODO(T02): 规则前置匹配 + LLM 兜底分类（generate_json），
    并按 rbac 白名单过滤 tool_name。
    """
    raise NotImplementedError("intent.detect_intent 将在 T02 实现")


def match_by_rules(message: str) -> Optional[IntentResult]:
    """
    纯规则关键词匹配（无 LLM 调用）。

    Parameters
    ----------
    message : str
        用户消息。

    Returns
    -------
    IntentResult | None
        命中返回结果，未命中返回 None。

    Notes
    -----
    TODO(T02): 实现关键词表与槽位抽取（城市 / 资源类型 / 数量）。
    """
    raise NotImplementedError("intent.match_by_rules 将在 T02 实现")
