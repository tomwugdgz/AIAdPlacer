"""青柠智能助手 — 提示词加载。

加载 ``system.jinja`` 系统提示词（青柠口吻），按角色渲染后用于 LLM 合成。
"""

from __future__ import annotations

import os

from jinja2 import Template

_PROMPT_DIR = os.path.dirname(__file__)
_TEMPLATE_PATH = os.path.join(_PROMPT_DIR, "system.jinja")
_cache: str = ""

_ROLE_LABELS = {
    "sale": "销售",
    "media": "媒介",
    "engineer": "工程",
    "developer": "商业开发",
}


def _read_template() -> str:
    global _cache
    if not _cache:
        with open(_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            _cache = f.read()
    return _cache


def load_system_prompt(role: str = "sale") -> str:
    """读取并渲染系统提示词。"""
    text = _read_template()
    role_label = _ROLE_LABELS.get(role, role)
    return Template(text).render(role=role, role_label=role_label)
