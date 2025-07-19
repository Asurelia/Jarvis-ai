"""
🔧 Configuration centralisée pour JARVIS
Gestion des variables d'environnement et paramètres par défaut
"""

import os
from pathlib import Path
from typing import Any, Optional, Union
from loguru import logger

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.warning("python-dotenv non disponible, utilisation des variables d'environnement système uniquement")

class JarvisSettings:
    """Configuration globale de JARVIS"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self._load_environment()
    
    def _load_environment(self):
        """Charge les variables d'environnement"""
        env_file = self.root_dir / ".env"
        
        if DOTENV_AVAILABLE and env_file.exists():
            load_dotenv(env_file)
            logger.info(f"📄 Configuration chargée depuis {env_file}")
        elif env_file.exists():
            logger.warning("⚠️ Fichier .env trouvé mais python-dotenv non installé")
    
    def get(self, key: str, default: Any = None, cast_type: type = str) -> Any:
        """Récupère une variable d'environnement avec cast de type"""
        value = os.getenv(key, default)
        
        if value is None:
            return default
        
        if cast_type == bool:
            return str(value).lower() in ('true', '1', 'yes', 'on')
        elif cast_type == int:
            try:
                return int(value)
            except ValueError:
                logger.warning(f"⚠️ Impossible de convertir {key}='{value}' en int, utilisation de la valeur par défaut")
                return default
        elif cast_type == float:
            try:
                return float(value)
            except ValueError:
                logger.warning(f"⚠️ Impossible de convertir {key}='{value}' en float, utilisation de la valeur par défaut")
                return default
        elif cast_type == Path:
            return Path(value)
        else:
            return value
    
    def get_list(self, key: str, default: list = None, separator: str = ",") -> list:
        """Récupère une liste depuis une variable d'environnement"""
        value = self.get(key, "")
        if not value:
            return default or []
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    # === API Configuration ===
    @property
    def api_host(self) -> str:
        return self.get("API_HOST", "127.0.0.1")
    
    @property
    def api_port(self) -> int:
        return self.get("API_PORT", 8000, int)
    
    @property
    def api_reload(self) -> bool:
        return self.get("API_RELOAD", False, bool)
    
    @property
    def api_workers(self) -> int:
        return self.get("API_WORKERS", 1, int)
    
    # === WebSocket Configuration ===
    @property
    def ws_ping_interval(self) -> int:
        return self.get("WS_PING_INTERVAL", 30, int)
    
    @property
    def ws_ping_timeout(self) -> int:
        return self.get("WS_PING_TIMEOUT", 10, int)
    
    @property
    def ws_max_connections(self) -> int:
        return self.get("WS_MAX_CONNECTIONS", 100, int)
    
    # === UI Configuration ===
    @property
    def react_app_api_url(self) -> str:
        return self.get("REACT_APP_API_URL", f"http://{self.api_host}:{self.api_port}")
    
    @property
    def react_app_ws_url(self) -> str:
        return self.get("REACT_APP_WS_URL", f"ws://{self.api_host}:{self.api_port}/ws")
    
    @property
    def ui_dev_port(self) -> int:
        return self.get("UI_DEV_PORT", 3000, int)
    
    # === Logging Configuration ===
    @property
    def log_level(self) -> str:
        return self.get("LOG_LEVEL", "INFO").upper()
    
    @property
    def log_file_enabled(self) -> bool:
        return self.get("LOG_FILE_ENABLED", True, bool)
    
    @property
    def log_file_path(self) -> Path:
        return self.get("LOG_FILE_PATH", "logs/jarvis.log", Path)
    
    @property
    def log_rotation(self) -> str:
        return self.get("LOG_ROTATION", "10 MB")
    
    @property
    def log_retention(self) -> str:
        return self.get("LOG_RETENTION", "30 days")
    
    @property
    def log_format(self) -> str:
        return self.get("LOG_FORMAT", 
                       "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}")
    
    # === Memory System ===
    @property
    def memory_persist_dir(self) -> Path:
        return self.get("MEMORY_PERSIST_DIR", "memory", Path)
    
    @property
    def memory_auto_cleanup(self) -> bool:
        return self.get("MEMORY_AUTO_CLEANUP", True, bool)
    
    @property
    def memory_cleanup_interval_hours(self) -> int:
        return self.get("MEMORY_CLEANUP_INTERVAL_HOURS", 24, int)
    
    @property
    def memory_max_age_days(self) -> int:
        return self.get("MEMORY_MAX_AGE_DAYS", 30, int)
    
    @property
    def memory_importance_threshold(self) -> float:
        return self.get("MEMORY_IMPORTANCE_THRESHOLD", 0.2, float)
    
    @property
    def memory_max_entries_per_category(self) -> int:
        return self.get("MEMORY_MAX_ENTRIES_PER_CATEGORY", 10000, int)
    
    # === Voice Interface ===
    @property
    def voice_enabled(self) -> bool:
        return self.get("VOICE_ENABLED", True, bool)
    
    @property
    def voice_default_language(self) -> str:
        return self.get("VOICE_DEFAULT_LANGUAGE", "fr-FR")
    
    @property
    def voice_default_voice(self) -> str:
        return self.get("VOICE_DEFAULT_VOICE", "fr-FR-DeniseNeural")
    
    @property
    def voice_speech_rate(self) -> float:
        return self.get("VOICE_SPEECH_RATE", 1.0, float)
    
    @property
    def voice_speech_volume(self) -> float:
        return self.get("VOICE_SPEECH_VOLUME", 1.0, float)
    
    # === Autocomplete System ===
    @property
    def autocomplete_enabled(self) -> bool:
        return self.get("AUTOCOMPLETE_ENABLED", True, bool)
    
    @property
    def autocomplete_max_suggestions(self) -> int:
        return self.get("AUTOCOMPLETE_MAX_SUGGESTIONS", 5, int)
    
    @property
    def autocomplete_cache_size(self) -> int:
        return self.get("AUTOCOMPLETE_CACHE_SIZE", 1000, int)
    
    @property
    def autocomplete_min_word_length(self) -> int:
        return self.get("AUTOCOMPLETE_MIN_WORD_LENGTH", 2, int)
    
    # === AI Models ===
    @property
    def ollama_base_url(self) -> str:
        return self.get("OLLAMA_BASE_URL", "http://localhost:11434")
    
    @property
    def ollama_default_model(self) -> str:
        return self.get("OLLAMA_DEFAULT_MODEL", "llama3.2:3b")
    
    @property
    def ollama_vision_model(self) -> str:
        return self.get("OLLAMA_VISION_MODEL", "llava:7b")
    
    @property
    def ollama_coding_model(self) -> str:
        return self.get("OLLAMA_CODING_MODEL", "deepseek-coder:6.7b")
    
    @property
    def ollama_timeout(self) -> int:
        return self.get("OLLAMA_TIMEOUT", 30, int)
    
    # === Security ===
    @property
    def sandbox_mode(self) -> bool:
        return self.get("SANDBOX_MODE", True, bool)
    
    @property
    def safe_mode(self) -> bool:
        return self.get("SAFE_MODE", True, bool)
    
    @property
    def allowed_hosts(self) -> list:
        return self.get_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
    
    @property
    def cors_origins(self) -> list:
        return self.get_list("CORS_ORIGINS", ["http://localhost:3000", "http://localhost:3001"])
    
    # === Performance ===
    @property
    def max_concurrent_requests(self) -> int:
        return self.get("MAX_CONCURRENT_REQUESTS", 50, int)
    
    @property
    def request_timeout(self) -> int:
        return self.get("REQUEST_TIMEOUT", 30, int)
    
    @property
    def cache_ttl(self) -> int:
        return self.get("CACHE_TTL", 300, int)
    
    @property
    def async_workers(self) -> int:
        return self.get("ASYNC_WORKERS", 4, int)
    
    # === Development ===
    @property
    def debug_mode(self) -> bool:
        return self.get("DEBUG_MODE", False, bool)
    
    @property
    def dev_mode(self) -> bool:
        return self.get("DEV_MODE", False, bool)
    
    @property
    def hot_reload(self) -> bool:
        return self.get("HOT_RELOAD", False, bool)
    
    @property
    def profiling_enabled(self) -> bool:
        return self.get("PROFILING_ENABLED", False, bool)
    
    # === System Integration ===
    @property
    def auto_start_browser(self) -> bool:
        return self.get("AUTO_START_BROWSER", True, bool)
    
    @property
    def electron_enabled(self) -> bool:
        return self.get("ELECTRON_ENABLED", True, bool)
    
    @property
    def system_tray(self) -> bool:
        return self.get("SYSTEM_TRAY", True, bool)
    
    @property
    def auto_update_check(self) -> bool:
        return self.get("AUTO_UPDATE_CHECK", True, bool)
    
    # === Monitoring ===
    @property
    def health_check_interval(self) -> int:
        return self.get("HEALTH_CHECK_INTERVAL", 60, int)
    
    @property
    def metrics_enabled(self) -> bool:
        return self.get("METRICS_ENABLED", True, bool)
    
    @property
    def telemetry_enabled(self) -> bool:
        return self.get("TELEMETRY_ENABLED", False, bool)
    
    @property
    def error_reporting(self) -> bool:
        return self.get("ERROR_REPORTING", True, bool)
    
    # === Database ===
    @property
    def chroma_persist_directory(self) -> Path:
        return self.get("CHROMA_PERSIST_DIRECTORY", "./memory/chroma", Path)
    
    @property
    def embedding_model(self) -> str:
        return self.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    @property
    def embedding_cache_size(self) -> int:
        return self.get("EMBEDDING_CACHE_SIZE", 1000, int)
    
    # === UI Theming ===
    @property
    def ui_theme(self) -> str:
        return self.get("UI_THEME", "dark")
    
    @property
    def ui_accent_color(self) -> str:
        return self.get("UI_ACCENT_COLOR", "blue")
    
    @property
    def ui_animations(self) -> bool:
        return self.get("UI_ANIMATIONS", True, bool)
    
    @property
    def ui_notifications(self) -> bool:
        return self.get("UI_NOTIFICATIONS", True, bool)
    
    def to_dict(self) -> dict:
        """Retourne toute la configuration sous forme de dictionnaire"""
        config = {}
        
        # Utiliser la réflexion pour obtenir toutes les propriétés
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                try:
                    value = getattr(self, attr_name)
                    if not callable(value):
                        config[attr_name] = value
                except:
                    continue
        
        return config
    
    def print_config(self):
        """Affiche la configuration actuelle"""
        logger.info("🔧 Configuration JARVIS:")
        config = self.to_dict()
        
        categories = {
            "API": ["api_", "ws_"],
            "UI": ["ui_", "react_"],
            "Logging": ["log_"],
            "Memory": ["memory_", "chroma_", "embedding_"],
            "Voice": ["voice_"],
            "Autocomplete": ["autocomplete_"],
            "AI": ["ollama_"],
            "Security": ["sandbox_", "safe_", "allowed_", "cors_"],
            "Performance": ["max_", "request_", "cache_", "async_"],
            "Development": ["debug_", "dev_", "hot_", "profiling_"],
            "System": ["auto_", "electron_", "system_"],
            "Monitoring": ["health_", "metrics_", "telemetry_", "error_"]
        }
        
        for category, prefixes in categories.items():
            category_items = {}
            for key, value in config.items():
                if any(key.startswith(prefix) for prefix in prefixes):
                    category_items[key] = value
            
            if category_items:
                logger.info(f"  📂 {category}:")
                for key, value in category_items.items():
                    # Masquer les valeurs sensibles
                    if "password" in key.lower() or "secret" in key.lower() or "token" in key.lower():
                        display_value = "***"
                    else:
                        display_value = str(value)
                    logger.info(f"    {key}: {display_value}")

# Instance globale
settings = JarvisSettings()

# Export des principales configurations pour rétrocompatibilité
API_HOST = settings.api_host
API_PORT = settings.api_port
LOG_LEVEL = settings.log_level
MEMORY_PERSIST_DIR = settings.memory_persist_dir

if __name__ == "__main__":
    # Test de la configuration
    settings.print_config()