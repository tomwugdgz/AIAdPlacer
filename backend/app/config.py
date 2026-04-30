from pydantic_settings import BaseSettings
from typing import Optional

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
    
    # 应用配置
    APP_NAME: str = "AI智能投放系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
