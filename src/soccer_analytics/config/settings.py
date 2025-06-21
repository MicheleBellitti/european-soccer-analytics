"""Application settings and configuration."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/soccer_analytics"
    )
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="password")
    postgres_db: str = Field(default="soccer_analytics")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    
    # Football Data API
    football_data_api_key: str = Field(default="demo_key")  # Default demo key, should be overridden
    football_data_base_url: str = Field(
        default="https://api.football-data.org/v4"
    )
    
    # Application
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    streamlit_port: int = Field(default=8501)
    
    # Testing
    test_database_url: Optional[str] = Field(default=None)
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)