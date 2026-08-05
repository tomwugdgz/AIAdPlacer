from pathlib import Path

from pydantic_settings import BaseSettings
from typing import Optional

# backend/app/config.py -> backend/app -> backend
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_QINGLIN_DB = str(_BACKEND_DIR / "data" / "qinlin_local.db")
_DEFAULT_QINGLIN_MEMORY_DB = str(_BACKEND_DIR / "data" / "qinglin_memory.db")


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "postgresql://quantdinger:quantdinger123@127.0.0.1:5432/ai_adplacer"
    
    # Redis配置
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    
    # 腾讯地图API
    TENCENT_MAP_KEY: str = "7HKBZ-HQBEM-XS56X-6DBAT-ITXUZ-IDFNG"
    TENCENT_MAP_BASE_URL: str = "https://apis.map.qq.com/ws/"
    
    # AI配置
    LLM_API_KEY: Optional[str] = None
    LLM_API_URL: Optional[str] = None
    
    # LLM 配置（客户可自助配置）
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "modelscope.cn/bge-m3:latest"
    LLM_ENABLED: bool = True

    # ── 青柠智能助手（qinglin_assistant 增量模块）─────────────────
    # 业务库：真实点位/客户数据，查询类走真实链路
    QINGLIN_DB_PATH: str = _DEFAULT_QINGLIN_DB
    # 会话记忆持久化库（按 session_id 隔离）
    QINGLIN_MEMORY_DB_PATH: str = _DEFAULT_QINGLIN_MEMORY_DB

    # 聊天模型。注意：OLLAMA_MODEL 可能被配置为 bge-m3 等 embedding 模型，
    # 不能用于对话，因此青柠助手使用独立的聊天模型字段。
    QINGLIN_CHAT_MODEL: str = "qwen3.5-9b"

    # OpenAI 协议兼容网关（OpenAI / DashScope / Claude 网关等）
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # 应用配置
    APP_NAME: str = "AI智能投放系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
