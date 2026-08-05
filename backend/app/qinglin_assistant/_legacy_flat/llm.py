"""
青柠智能助手 — LLM Provider 兼容抽象层。

设计目标
--------
默认走本地 Ollama，通过环境变量 ``QINGLIN_LLM_PROVIDER`` 可切换到任意
OpenAI 协议兼容的云端网关（OpenAI / DashScope / Claude 网关等）。

关键约束
--------
1. **复用既有能力**：``OllamaProvider`` 直接复用
   ``app.services.ollama_client.OllamaClient``，不重写任何 HTTP 调用逻辑。
2. **绝不静默造假**：所有 provider 都不可用时抛出 :class:`LLMUnavailableError`，
   由上层转成 HTTP 503，禁止 fallback 到写死的假文案。
3. **自动降级**：本地 Ollama 不可用且配置了 ``OPENAI_API_KEY`` 时，
   自动切换到 OpenAI 兼容网关。

使用示例
--------
    from app.qinglin_assistant.llm import get_llm_provider, LLMUnavailableError

    try:
        provider = await get_llm_provider()
        reply = await provider.chat([{"role": "user", "content": "你好"}])
    except LLMUnavailableError as exc:
        ...  # 返回 503
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

#: 支持的 provider 名称
PROVIDER_OLLAMA: str = "ollama"
PROVIDER_OPENAI: str = "openai"
SUPPORTED_PROVIDERS: List[str] = [PROVIDER_OLLAMA, PROVIDER_OPENAI]

#: 默认系统提示词
DEFAULT_SYSTEM_PROMPT: str = (
    "你是青柠的智能助手，服务于 pDOOH 程序化户外广告投放业务。"
    "请使用简体中文回答，回答要专业、准确、简洁。"
)


class LLMUnavailableError(RuntimeError):
    """
    所有 LLM provider 均不可用时抛出。

    上层（api.py）捕获后应返回 HTTP 503 及清晰错误信息，
    **禁止**降级为写死的模拟回复。
    """


class LLMProvider(ABC):
    """LLM 提供方统一接口。"""

    #: provider 名称标识
    name: str = "base"

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """
        发起一次对话补全。

        Parameters
        ----------
        messages : list[dict]
            OpenAI 风格消息列表，每项形如
            ``{"role": "system"|"user"|"assistant", "content": "..."}``。
        **kwargs
            provider 可选参数，当前支持 ``temperature`` (float)。

        Returns
        -------
        str
            模型回复文本。

        Raises
        ------
        LLMUnavailableError
            调用失败（网络异常 / 服务不可达 / 鉴权失败）时抛出。
        """
        raise NotImplementedError

    @abstractmethod
    async def is_available(self) -> bool:
        """
        探测该 provider 当前是否可用。

        Returns
        -------
        bool
            可用返回 True，任何异常一律返回 False（不向外抛）。
        """
        raise NotImplementedError

    def describe(self) -> Dict[str, Any]:
        """
        返回 provider 的元信息，供 /health 等接口展示。

        Returns
        -------
        dict
            含 ``provider`` 与 ``model`` 字段。
        """
        return {"provider": self.name, "model": getattr(self, "model", "")}


def split_messages(messages: List[Dict[str, str]]) -> tuple[Optional[str], str]:
    """
    将 OpenAI 风格消息列表拍平为 (system_prompt, prompt) 二元组。

    背景：既有的 :class:`OllamaClient` 只接受「单条 prompt + 可选 system_prompt」，
    为了复用它而不重写 HTTP 层，这里把多轮历史渲染成一段可读的对话转写文本，
    最后一条 user 消息作为当前提问。

    Parameters
    ----------
    messages : list[dict]
        消息列表。

    Returns
    -------
    tuple[str | None, str]
        ``(system_prompt, prompt)``。当没有 system 消息时第一项为 None。
    """
    system_parts: List[str] = []
    dialogue: List[str] = []

    for message in messages or []:
        role = str(message.get("role", "user")).strip().lower()
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            dialogue.append(f"助手：{content}")
        else:
            dialogue.append(f"用户：{content}")

    system_prompt: Optional[str] = "\n".join(system_parts) if system_parts else None

    if not dialogue:
        return system_prompt, ""
    if len(dialogue) == 1:
        # 单轮：直接把原文当 prompt，避免多余的「用户：」前缀干扰模型
        return system_prompt, dialogue[0].removeprefix("用户：")

    history = "\n".join(dialogue[:-1])
    current = dialogue[-1].removeprefix("用户：")
    prompt = f"以下是历史对话：\n{history}\n\n请回答用户当前的问题：\n{current}"
    return system_prompt, prompt


class OllamaProvider(LLMProvider):
    """
    本地 Ollama provider。

    完全复用 ``app.services.ollama_client.OllamaClient``（已实现
    chat / generate / generate_json / is_available），本类只做
    消息格式适配与异常归一化。
    """

    name = PROVIDER_OLLAMA

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        base_url : str | None
            Ollama 服务地址，默认取 ``settings.OLLAMA_BASE_URL``。
        model : str | None
            聊天模型名，默认取 ``settings.QINGLIN_CHAT_MODEL``
            （**不使用** OLLAMA_MODEL，那可能是 embedding 模型）。
        """
        self.model: str = model or settings.QINGLIN_CHAT_MODEL
        self.base_url: str = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._client: OllamaClient = OllamaClient(
            base_url=self.base_url, model=self.model
        )

    async def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """调用本地 Ollama 完成对话补全。"""
        system_prompt, prompt = split_messages(messages)
        temperature: float = float(kwargs.get("temperature", 0.7))
        try:
            return await self._client.chat(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
            )
        except Exception as exc:  # noqa: BLE001 — 统一归一化为可识别异常
            logger.warning("Ollama 调用失败: %s", exc)
            raise LLMUnavailableError(
                f"本地 Ollama 调用失败（{self.base_url}, model={self.model}）: {exc}"
            ) from exc

    async def is_available(self) -> bool:
        """探测 Ollama 服务是否可达。"""
        try:
            return await self._client.is_available()
        except Exception:  # noqa: BLE001
            return False


class OpenAICompatProvider(LLMProvider):
    """
    OpenAI 协议兼容云端 provider。

    适用于 OpenAI 官方、DashScope 兼容模式、Claude 网关等所有暴露
    ``POST {base_url}/chat/completions`` 的服务。
    与仓库其他 HTTP 客户端保持一致，使用 ``httpx.AsyncClient``。
    """

    name = PROVIDER_OPENAI

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        """
        Parameters
        ----------
        base_url : str | None
            兼容网关地址，默认 ``settings.OPENAI_BASE_URL``。
        api_key : str | None
            API Key，默认 ``settings.OPENAI_API_KEY``。
        model : str | None
            模型名，默认 ``settings.OPENAI_MODEL``。
        timeout : float
            请求超时秒数。
        """
        self.base_url: str = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.api_key: str = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.model: str = model or settings.OPENAI_MODEL
        self.timeout: float = timeout

    def _headers(self) -> Dict[str, str]:
        """构造请求头。"""
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """调用 OpenAI 兼容接口完成对话补全。"""
        if not self.api_key:
            raise LLMUnavailableError(
                "未配置 OPENAI_API_KEY，无法使用 OpenAI 兼容云端 provider"
            )

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": str(m.get("role", "user")),
                    "content": str(m.get("content", "")),
                }
                for m in (messages or [])
                if str(m.get("content", "")).strip()
            ],
            "temperature": float(kwargs.get("temperature", 0.7)),
            "stream": False,
        }
        if "max_tokens" in kwargs:
            payload["max_tokens"] = int(kwargs["max_tokens"])

        url = f"{self.base_url}/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()
                data: Dict[str, Any] = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenAI 兼容网关调用失败: %s", exc)
            raise LLMUnavailableError(
                f"OpenAI 兼容网关调用失败（{url}, model={self.model}）: {exc}"
            ) from exc

        choices: List[Dict[str, Any]] = data.get("choices") or []
        if not choices:
            raise LLMUnavailableError(f"OpenAI 兼容网关返回空 choices: {data}")
        return str(choices[0].get("message", {}).get("content", ""))

    async def is_available(self) -> bool:
        """探测云端网关是否可用（未配置 Key 直接判定不可用）。"""
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/models", headers=self._headers()
                )
                return response.status_code < 500
        except Exception:  # noqa: BLE001
            return False


def build_provider(name: str) -> LLMProvider:
    """
    按名称同步构造 provider 实例（**不做**任何网络探测）。

    Parameters
    ----------
    name : str
        provider 名称，见 :data:`SUPPORTED_PROVIDERS`。

    Returns
    -------
    LLMProvider
        provider 实例。

    Raises
    ------
    LLMUnavailableError
        名称不受支持时抛出。
    """
    normalized = (name or "").strip().lower()
    if normalized == PROVIDER_OLLAMA:
        return OllamaProvider()
    if normalized in (PROVIDER_OPENAI, "openai_compat", "compat"):
        return OpenAICompatProvider()
    raise LLMUnavailableError(
        f"不支持的 LLM provider: {name!r}，可选值：{SUPPORTED_PROVIDERS}"
    )


async def get_llm_provider(prefer: Optional[str] = None) -> LLMProvider:
    """
    获取一个**当前可用**的 LLM provider（工厂 + 自动降级）。

    选择顺序
    --------
    1. ``prefer`` 或 ``settings.QINGLIN_LLM_PROVIDER`` 指定的首选 provider
    2. 首选不可用时，降级到另一个已配置的 provider
       （ollama 挂了且配了 OPENAI_API_KEY → 切云端）
    3. 全部不可用 → 抛 :class:`LLMUnavailableError`（**绝不返回假数据**）

    Parameters
    ----------
    prefer : str | None
        强制指定首选 provider，None 时读取配置。

    Returns
    -------
    LLMProvider
        探测通过的 provider 实例。

    Raises
    ------
    LLMUnavailableError
        所有候选 provider 均不可用。
    """
    primary_name = (prefer or settings.QINGLIN_LLM_PROVIDER or PROVIDER_OLLAMA).strip().lower()

    # 构造候选顺序：首选在前，其余作为降级备选
    candidates: List[str] = [primary_name]
    for fallback in SUPPORTED_PROVIDERS:
        if fallback not in candidates:
            candidates.append(fallback)

    failures: List[str] = []
    for candidate in candidates:
        try:
            provider = build_provider(candidate)
        except LLMUnavailableError as exc:
            failures.append(str(exc))
            continue

        if await provider.is_available():
            if candidate != primary_name:
                logger.warning(
                    "首选 LLM provider %s 不可用，已自动降级到 %s",
                    primary_name,
                    candidate,
                )
            return provider

        failures.append(f"{candidate} 不可用（{provider.describe()}）")

    raise LLMUnavailableError(
        "所有 LLM provider 均不可用，请检查本地 Ollama 是否启动"
        f"（{settings.OLLAMA_BASE_URL}）或配置 OPENAI_API_KEY。明细：" + "；".join(failures)
    )


async def probe_providers() -> Dict[str, Any]:
    """
    探测全部 provider 的健康状态，供 ``/health`` 接口使用。

    Returns
    -------
    dict
        含 ``configured``（配置的首选 provider）与 ``providers``
        （每个 provider 的 name / model / available）。
    """
    results: List[Dict[str, Any]] = []
    for name in SUPPORTED_PROVIDERS:
        try:
            provider = build_provider(name)
        except LLMUnavailableError:
            continue
        info = provider.describe()
        info["available"] = await provider.is_available()
        results.append(info)

    return {
        "configured": settings.QINGLIN_LLM_PROVIDER,
        "chat_model": settings.QINGLIN_CHAT_MODEL,
        "providers": results,
    }
