"""
⚙️ Configuration Brain API
Variables d'environnement et paramètres système
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration centralisée de l'application"""
    
    # 🌐 Serveur
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    WEBSOCKET_PORT: int = 8081
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    # 🔗 URLs des services externes
    REDIS_URL: str = "redis://redis:6379"
    MEMORY_DB_URL: str = "postgresql://jarvis:jarvis123@memory-db:5432/jarvis_memory"
    
    # 🤖 LLM Configuration - Hybrid Mode Support
    OLLAMA_MODE: str = "single"  # single, hybrid, gateway_only
    OLLAMA_URL: str = "http://ollama:11434"  # Legacy single mode
    
    # Hybrid mode configuration
    OLLAMA_PRIMARY_URL: str = "http://host.docker.internal:11434"    # Host Ollama
    OLLAMA_FALLBACK_URL: str = "http://ollama-fallback:11434"        # Container Ollama
    OLLAMA_CLOUD_URL: str = ""                                       # Future OpenRouter
    
    # LLM Gateway Service
    LLM_GATEWAY_URL: str = "http://llm-gateway:5010"
    LLM_ROUTING_ENABLED: bool = True
    
    # Model configuration
    PRIMARY_MODEL: str = "llama3.2:3b"
    LARGE_MODEL: str = "gpt-oss-20b" 
    FALLBACK_MODEL: str = "llama3.2:3b"
    MODEL_SELECTION_STRATEGY: str = "complexity_based"
    
    # Timeouts and failover
    HOST_NETWORK_TIMEOUT: int = 30
    LLM_FAILOVER_TIMEOUT: int = 10
    
    TTS_SERVICE_URL: str = "http://tts-service:5002"
    STT_SERVICE_URL: str = "http://stt-service:5003"
    
    # 🧠 Métacognition
    METACOGNITION_THRESHOLD: float = 0.7
    COMPLEXITY_MIN_SCORE: float = 0.3
    HALLUCINATION_DETECTION: bool = True
    REPETITION_THRESHOLD: int = 3
    
    # 🤖 Agent React
    AGENT_MAX_ITERATIONS: int = 5
    AGENT_TIMEOUT_SECONDS: int = 30
    TOOLS_ENABLED: List[str] = [
        "web_search", "file_system", "calculator", 
        "datetime", "weather", "system_info"
    ]
    
    # 🧮 Mémoire
    STATIC_MEMORY_TTL: int = 86400 * 30  # 30 jours
    DYNAMIC_MEMORY_UPDATE_INTERVAL: int = 5  # 5 interactions
    EPISODIC_MEMORY_MAX_ENTRIES: int = 1000
    VECTOR_DIMENSION: int = 384
    
    # 🔊 Audio
    AUDIO_CHUNK_SIZE: int = 1024
    AUDIO_SAMPLE_RATE: int = 16000
    WEBSOCKET_AUDIO_BUFFER_SIZE: int = 4096
    
    # 📊 Performance
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 60
    MEMORY_LIMIT_MB: int = 2048
    
    # 🔐 Sécurité
    API_KEY_REQUIRED: bool = False
    API_KEY: str = ""
    CORS_ORIGINS: List[str] = ["*"]
    
    # 📈 Monitoring
    METRICS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    LOG_TO_FILE: bool = True
    LOG_ROTATION_SIZE: str = "100MB"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Instance globale des paramètres
settings = Settings()

# 🔧 Validation de configuration
def validate_config():
    """Valider la configuration au démarrage"""
    errors = []
    
    # Vérifier URLs de services
    required_urls = [
        settings.REDIS_URL,
        settings.MEMORY_DB_URL, 
        settings.OLLAMA_URL
    ]
    
    for url in required_urls:
        if not url or url == "":
            errors.append(f"URL de service manquante: {url}")
    
    # Vérifier paramètres numériques
    if settings.METACOGNITION_THRESHOLD < 0 or settings.METACOGNITION_THRESHOLD > 1:
        errors.append("METACOGNITION_THRESHOLD doit être entre 0 et 1")
        
    if settings.COMPLEXITY_MIN_SCORE < 0 or settings.COMPLEXITY_MIN_SCORE > 1:
        errors.append("COMPLEXITY_MIN_SCORE doit être entre 0 et 1")
    
    if settings.AGENT_MAX_ITERATIONS < 1:
        errors.append("AGENT_MAX_ITERATIONS doit être >= 1")
        
    if settings.DYNAMIC_MEMORY_UPDATE_INTERVAL < 1:
        errors.append("DYNAMIC_MEMORY_UPDATE_INTERVAL doit être >= 1")
    
    if errors:
        raise ValueError(f"Erreurs de configuration: {'; '.join(errors)}")
    
    return True

# Validation automatique
if __name__ != "__main__":
    validate_config()