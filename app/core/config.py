from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    OPENAI_API_KEY: str
    
    # Telegram monitoring settings
    TELEGRAM_MONITOR_INTERVAL: int = 60  # seconds
    TELEGRAM_SESSION_CHECK_INTERVAL: int = 300  # seconds
    
    # API settings
    API_PAGINATION_DEFAULT_SKIP: int = 0
    API_PAGINATION_DEFAULT_LIMIT: int = 100
    API_PAGINATION_MAX_LIMIT: int = 1000
    
    # Logging settings
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached settings instance.
    Used to prevent reloading the .env file.
    """
    return Settings() 
