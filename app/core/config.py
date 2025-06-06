"""
Configuration settings for AgriTech Assistant
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "AgriTech Assistant"
    VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./agritech.db",
        env="DATABASE_URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    WEATHER_API_KEY: Optional[str] = Field(default=None, env="WEATHER_API_KEY")
    SOIL_API_KEY: Optional[str] = Field(default=None, env="SOIL_API_KEY")
    
    # ML Models
    DISEASE_MODEL_PATH: str = Field(
        default="models/disease_detection_model.pt",
        env="DISEASE_MODEL_PATH"
    )
    MODEL_CONFIDENCE_THRESHOLD: float = 0.7
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/jpg"]
    
    # Weather Service
    WEATHER_API_BASE_URL: str = "http://api.openweathermap.org/data/2.5"
    WEATHER_CACHE_DURATION: int = 300  # 5 minutes
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("logs", exist_ok=True)