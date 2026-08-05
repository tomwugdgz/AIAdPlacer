"""青柠智能助手 — LLM 抽象层。

提供与具体后端无关的 ``LLMClient`` 接口，并内置两个实现：

1. ``OllamaProvider``：复用既有 ``app.services.ollama_client.OllamaClient``，
   默认聊天模型为 ``qwen3.5-9b``（**绝不**使用 ``OLLAMA_MODEL`` 中可能被配置成
   embedding 模型的 ``bge-m3``）。
2. ``OpenAICompatibleProvider``：走 OpenAI 兼容协议（OpenAI / DashScope / Claude 网关等），
   通过 ``settings.OPENAI_BASE_URL`` + ``settings.OPENAI_API_KEY`` 接入。

工厂 ``get_llm_client()`` 依据 ``settings.LLM_PROVIDER`` 选择实现，
默认走 Ollama。

设计约束（来自实测事实）：
- ``config.OLLAMA_MODEL`` 可能是 embedding 模型，**严禁**用于对话。
- 所有方法均异步；``generate_json`` 用于意图识别，复用 ``OllamaClient.generate_json``。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.services.ollama_client import OllamaClient


# ─────────────────────────────────────────────────────────────
# 抽象基类
# ─────────────────────────────────────────────────────────────

class LLMClient(ABC):
    """LLM 客户端统一抽象。

    所有 Provider 必须实现：
    - ``chat``：多轮对话合成。
    - ``generate_json``：结构化 JSON 输出（意图识别用）。
    - ``is_available``：后端可达性探测。
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        """多轮对话合成，返回模型文本。``messages`` 元素形如 {"role":..., "content":...}。"""
        raise NotImplementedError

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """要求模型返回 JSON，解析为 dict；解析失败兜底返回 {"raw_response": text}。"""
        raise NotImplementedError

    @abstractmethod
    async def is_available(self) -> bool:
        """探测 LLM 后端是否可用。"""
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────
# Ollama Provider（本地，默认）
# ─────────────────────────────────────────────────────────────

class OllamaProvider(LLMClient):
    """基于本地 Ollama 的 Provider，复用既有 ``OllamaClient``。"""

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        # 聊天模型固定使用 QINGLIN_CHAT_MODEL（qwen3.5-9b），不碰 OLLAMA_MODEL（可能是 embedding）。
        self._client = OllamaClient(
            base_url=base_url or settings.OLLAMA_BASE_URL,
            model=model or settings.QINGLIN_CHAT_MODEL,
        )

    @staticmethod
    def _split_messages(messages: List[Dict[str, str]]):
        """从 messages 中抽取 system 提示与合并后的用户对话文本。"""
        system_parts: List[str] = []
        user_parts: List[str] = []
        for msg in messages:
            role = (msg.get("role") or "user").lower()
            content = msg.get("content") or ""
            if role == "system":
                system_parts.append(content)
            else:
                prefix = "用户" if role == "user" else "助手"
                user_parts.append(f"{prefix}：{content}")
        return "\n".join(system_parts) or None, "\n".join(user_parts)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        system_prompt, user_text = self._split_messages(messages)
        prompt = user_text or (messages[-1].get("content") if messages else "")
        return await self._client.chat(prompt, system_prompt=system_prompt, temperature=temperature)

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        return await self._client.generate_json(prompt, system_prompt=system_prompt, temperature=temperature)

    async def is_available(self) -> bool:
        return await self._client.is_available()


# ─────────────────────────────────────────────────────────────
# OpenAI 兼容 Provider（云端）
# ─────────────────────────────────────────────────────────────

class OpenAICompatibleProvider(LLMClient):
    """OpenAI 兼容协议 Provider（OpenAI / DashScope / Claude 网关等）。"""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.model = model or settings.OPENAI_MODEL or settings.QINGLIN_CHAT_MODEL
        self.base_url = (base_url or settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        text = await self.chat(messages, temperature=temperature)
        text = (text or "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass
        return {"raw_response": text, "parse_error": True}

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                return resp.status_code == 200
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────
# 工厂
# ─────────────────────────────────────────────────────────────

def get_llm_client() -> LLMClient:
    """依据 ``settings.LLM_PROVIDER`` 返回对应 Provider 实例。

    默认（``ollama``）走本地 Ollama；``openai`` 走 OpenAI 兼容网关。
    其它未知值一律回退到 Ollama，保证本地优先、永远可用。
    """
    provider = (settings.LLM_PROVIDER or "ollama").lower()
    if provider == "openai":
        return OpenAICompatibleProvider()
    return OllamaProvider()
