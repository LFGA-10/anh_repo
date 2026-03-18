from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # OpenRouter
    OPEN_ROUTER_API_KEY: str
    OPEN_ROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    
    # Neo4j
    NEO4J_URI: Optional[str] = None
    NEO4J_USERNAME: Optional[str] = None
    NEO4J_PASSWORD: Optional[str] = None
    
    # Qdrant
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    
    # App Settings
    LOG_LEVEL: str = "INFO"
    USE_LOCAL_STORAGE: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
