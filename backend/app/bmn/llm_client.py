"""
BMN LLM 客户端 — 统一接口
支持：Ollama（本地）/ OpenAI / Anthropic / 自定义
配置通过 .env 文件管理，客户可自行配置

使用方法：
    from app.bmn.llm_client import call_llm
    
    response = call_llm("请用一句话介绍亲邻传媒")
    print(response)
"""

import os
import json
import subprocess
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

# ── 配置读取 ─────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() == "true"


# ── Ollama 调用器 ─────────────────────────────────────────
def _call_ollama(prompt: str, model: str = None, timeout: int = 60) -> str:
    """
    调用 Ollama 本地模型（优先使用命令行，更可靠）
    :param prompt: 提示词
    :param model: 模型名称（默认使用配置项 OLLAMA_MODEL）
    :param timeout: 超时时间（秒）
    :return: 模型输出文本
    """
    model = model or OLLAMA_MODEL
    
    # 优先使用命令行（避免 HTTP API 的模型名称解析问题）
    return _call_ollama_cli(prompt, model, timeout)


def _call_ollama_cli(prompt: str, model: str = None, timeout: int = 60) -> str:
    """降级方案：使用 ollama 命令行"""
    model = model or OLLAMA_MODEL
    
    try:
        # 使用 UTF-8 编码避免解码错误
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            encoding="utf-8",  # 明确指定编码
            timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError(f"Ollama CLI 错误：{result.stderr}")
    except FileNotFoundError:
        raise RuntimeError("Ollama 未安装或不在 PATH 中")
    except UnicodeDecodeError as e:
        raise RuntimeError(f"Ollama 输出解码失败：{e}")


# ── OpenAI 调用器 ────────────────────────────────────────
def _call_openai(prompt: str, model: str = None, timeout: int = 60) -> str:
    """
    调用 OpenAI API
    （可选，客户需自行配置 OPENAI_API_KEY）
    """
    model = model or OPENAI_MODEL
    
    if not OPENAI_API_KEY:
        raise ValueError("未配置 OPENAI_API_KEY")
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
            timeout=timeout
        )
        
        return response.choices[0].message.content.strip()
        
    except ImportError:
        # 手动调用 HTTP API
        import requests
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        resp.raise_for_status()
        
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


# ── 统一调用接口 ─────────────────────────────────────────
def call_llm(prompt: str, provider: str = None, model: str = None, timeout: int = 60) -> str:
    """
    统一 LLM 调用接口
    :param prompt: 提示词
    :param provider: 提供商（可选，默认使用 .env 配置）
    :param model: 模型名称（可选，使用提供商默认模型）
    :param timeout: 超时时间（秒）
    :return: 模型输出文本
    
    配置优先级：函数参数 > .env 配置 > 默认值
    """
    if not LLM_ENABLED:
        raise RuntimeError("LLM 已禁用（LLM_ENABLED=false）")
    
    # 确定提供商
    provider = (provider or LLM_PROVIDER).lower()
    
    # 根据提供商调用对应接口
    if provider == "ollama":
        return _call_ollama(prompt, model, timeout)
    elif provider == "openai":
        return _call_openai(prompt, model, timeout)
    else:
        raise ValueError(f"不支持的 LLM 提供商：{provider}")


def is_llm_available(provider: str = None) -> bool:
    """
    检查 LLM 是否可用
    :param provider: 提供商（可选，默认使用配置）
    :return: 是否可用
    """
    if not LLM_ENABLED:
        return False
    
    provider = (provider or LLM_PROVIDER).lower()
    
    try:
        if provider == "ollama":
            import requests
            url = f"{OLLAMA_BASE_URL}/api/tags"
            resp = requests.get(url, timeout=3)
            return resp.status_code == 200
        elif provider == "openai":
            return bool(OPENAI_API_KEY)
        else:
            return False
    except Exception:
        return False


def get_llm_config() -> Dict[str, Any]:
    """
    获取当前 LLM 配置（供前端展示）
    :return: 配置字典（不含敏感信息）
    """
    return {
        "provider": LLM_PROVIDER,
        "model": OLLAMA_MODEL if LLM_PROVIDER == "ollama" else OPENAI_MODEL,
        "enabled": LLM_ENABLED,
        "available": is_llm_available(),
        "base_url": OLLAMA_BASE_URL if LLM_PROVIDER == "ollama" else "https://api.openai.com/v1"
    }


# ── 测试代码 ────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("BMN LLM 客户端测试")
    print("=" * 60)
    
    # 显示配置
    config = get_llm_config()
    print(f"\n当前配置：")
    print(f"  提供商：{config['provider']}")
    print(f"  模型：{config['model']}")
    print(f"  启用状态：{config['enabled']}")
    print(f"  可用性：{config['available']}")
    
    if not config['available']:
        print("\n⚠️  LLM 不可用，请检查配置或启动 Ollama")
        print("   Ollama 启动命令：ollama serve")
        print("   拉取模型命令：ollama pull llama3")
    else:
        # 测试调用
        print("\n测试调用...")
        try:
            response = call_llm("请用一句话介绍亲邻传媒", timeout=30)
            print(f"响应：{response[:200]}...")
        except Exception as e:
            print(f"调用失败：{e}")
    
    print("\n" + "=" * 60)
