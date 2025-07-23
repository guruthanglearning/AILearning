"""
Configuration settings for the fraud detection system.
Loads environment variables and provides access to configuration settings.
"""

import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Configuration settings for the application."""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    VECTOR_DIMENSION: int = int(os.getenv("VECTOR_DIMENSION", "384"))
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    
    # Local LLM Configuration
    USE_LOCAL_LLM: bool = os.getenv("USE_LOCAL_LLM", "False").lower() in ("true", "1", "t")
    FORCE_LOCAL_LLM: bool = os.getenv("FORCE_LOCAL_LLM", "False").lower() in ("true", "1", "t")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "llama3")
    
    # Online Ollama API Configuration
    USE_ONLINE_OLLAMA: bool = os.getenv("USE_ONLINE_OLLAMA", "False").lower() in ("true", "1", "t")
    ONLINE_OLLAMA_API_URL: str = os.getenv("ONLINE_OLLAMA_API_URL", "")
    # API key is marked as secret to prevent accidental logging
    ONLINE_OLLAMA_API_KEY: str = os.getenv("ONLINE_OLLAMA_API_KEY", "")
    # Mask the API key when displaying configuration
    @property
    def MASKED_ONLINE_OLLAMA_API_KEY(self) -> str:
        """Return a masked version of the API key for logging/display purposes."""
        api_key = self.ONLINE_OLLAMA_API_KEY
        if not api_key or len(api_key) < 8:
            return ""
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    LOCAL_LLM_API_URL: str = os.getenv("LOCAL_LLM_API_URL", "http://localhost:11434/api")
    
    # Database Configuration
    VECTOR_INDEX_NAME: str = os.getenv("VECTOR_INDEX_NAME", "fraud-patterns")

    # Application Configuration
    APP_ENV: str = os.getenv("APP_ENV", "development")  # development, testing, production
    VERSION: str = os.getenv("VERSION", "1.0.0")  # Application version
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_for_jwt")
    API_KEY: str = os.getenv("API_KEY", "development_api_key_for_testing")
    AUTH_REQUIRED: bool = os.getenv("AUTH_REQUIRED", "False").lower() in ("true", "1", "t")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    
    # Constants for the fraud detection system
    TRANSACTION_HISTORY_WINDOW: int = int(os.getenv("TRANSACTION_HISTORY_WINDOW", "30"))  # Days
    DEFAULT_SIMILARITY_THRESHOLD: float = float(os.getenv("DEFAULT_SIMILARITY_THRESHOLD", "0.85"))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
    
    # Monitoring settings
    ENABLE_PROMETHEUS: bool = os.getenv("ENABLE_PROMETHEUS", "True").lower() in ("true", "1", "t")
    GRAFANA_ADMIN_USER: str = os.getenv("GRAFANA_ADMIN_USER", "admin")
    GRAFANA_ADMIN_PASSWORD: str = os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")
    
    # Vector DB settings
    USE_PINECONE: bool = os.getenv("USE_PINECONE", "False").lower() in ("true", "1", "t")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

def get_settings() -> Settings:
    """Return the settings instance."""
    return settings
