from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os, dotenv


class Config(BaseSettings):
    
    # DeepSeek
    DEEPSEEK_CHAT: str = "deepseek-chat"
    DEEPSEEK_API_KEY:Optional[str]=None
    
    # LangSmith
    LANGCHAIN_TRACING_V2:Optional[bool]=True               # 支持环境变量 LANGSMITH_TRACING=true/false
    LANGSMITH_ENDPOINT:Optional[str]=None
    LANGSMITH_API_KEY:Optional[str]=None
    LANGSMITH_PROJECT:Optional[str]=None
    
    # 数据库
    DATABASE_URL:Optional[str]=None
    
    # 多环境标识（容器内运行时，docker-compose.yml已经为web和worker服务显式设置了环境变量为container）
    ENVIRONMENT: str = "development"   # development 或 container
    
    
    model_config=SettingsConfigDict(
        case_sensitive=False,
        env_file_encoding="utf-8",
        env_file=Path(__file__).resolve().parent.joinpath(".env"),
        extra="ignore"
    )
    
    def get_database_url(self) -> str:
        """根据环境返回正确的数据库连接字符串"""
        if self.ENVIRONMENT == "container":
            # 容器内使用服务名 postgres
            return "postgresql://postgres:postgres@postgres:5432/analysis"
        else:
            # 开发环境使用 .env 中配置的地址（通常是 localhost）
            return self.DATABASE_URL or "postgresql://postgres:postgres@localhost:5432/analysis"
    
    
config = Config()

# 手动加载 .env 中的 LangSmith 变量
_env_path = Path(__file__).resolve().parent / ".env"
dotenv.load_dotenv(dotenv_path=_env_path)

# 为了兼容现有代码，把动态数据库 URL 赋值给 config.DATABASE_URL
if config.ENVIRONMENT == "container":
    config.DATABASE_URL = config.get_database_url()