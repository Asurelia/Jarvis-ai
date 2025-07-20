"""
⚙️ Configuration - TTS Service
Configuration centralisée avec variables d'environnement
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration TTS Service"""
    
    # Service
    SERVICE_NAME: str = "JARVIS TTS Service"
    VERSION: str = "2.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 5002
    LOG_LEVEL: str = "INFO"
    
    # TTS Engine
    TTS_MODEL: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    TTS_DEVICE: str = "cpu"  # ou "cuda" si GPU disponible
    ANTI_HALLUCINATION: bool = True
    
    # Audio
    SAMPLE_RATE: int = 22050
    CHANNELS: int = 1
    CHUNK_SIZE: int = 1024
    CHUNK_DURATION_MS: int = 20
    
    # Streaming
    STREAMING_ENABLED: bool = True
    BUFFER_SIZE: int = 5
    MAX_LATENCY_MS: int = 500
    
    # Cache
    CACHE_DIR: str = "/app/cache"
    MODEL_DIR: str = "/app/models"
    
    # Redis (optionnel pour cache distribué)
    REDIS_URL: Optional[str] = None
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9091
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instance singleton
settings = Settings()

# Créer les répertoires nécessaires
os.makedirs(settings.CACHE_DIR, exist_ok=True)
os.makedirs(settings.MODEL_DIR, exist_ok=True)