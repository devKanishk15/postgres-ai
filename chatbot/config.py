"""
Configuration settings for the Postgres Debugging Chatbot.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o"
    
    # Prometheus Configuration
    prometheus_url: str = "http://prometheus:9090"
    
    # PostgreSQL Configuration
    postgres_dsn: str = "postgresql://postgres:postgres@postgres:5432/testdb"
    
    # Application Settings
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
