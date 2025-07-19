"""
📝 Configuration centralisée des logs pour JARVIS
Système de logging avancé avec rotation, filtrage et formatage
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import json
from datetime import datetime

from .settings import settings

class JarvisLogger:
    """Gestionnaire de logs centralisé pour JARVIS"""
    
    def __init__(self):
        self.handlers = {}
        self.initialized = False
        
    def setup_logging(self, 
                     console_level: str = None,
                     file_level: str = None,
                     log_file: str = None,
                     rotation: str = None,
                     retention: str = None,
                     format_string: str = None,
                     json_logs: bool = False,
                     enable_file_logging: bool = None) -> bool:
        """Configure le système de logging complet"""
        
        if self.initialized:
            return True
        
        try:
            # Paramètres par défaut depuis la configuration
            console_level = console_level or settings.log_level
            file_level = file_level or settings.log_level
            log_file = log_file or str(settings.log_file_path)
            rotation = rotation or settings.log_rotation
            retention = retention or settings.log_retention
            format_string = format_string or settings.log_format
            enable_file_logging = enable_file_logging if enable_file_logging is not None else settings.log_file_enabled
            
            # Supprimer tous les handlers existants
            logger.remove()
            
            # === CONSOLE HANDLER ===
            console_format = self._get_console_format(format_string)
            
            console_handler = logger.add(
                sys.stderr,
                level=console_level.upper(),
                format=console_format,
                colorize=True,
                backtrace=True,
                diagnose=True,
                filter=self._console_filter
            )
            self.handlers['console'] = console_handler
            
            # === FILE HANDLERS ===
            if enable_file_logging:
                self._setup_file_logging(
                    log_file, file_level, rotation, retention, 
                    format_string, json_logs
                )
            
            # === HANDLER SPÉCIALISÉS ===
            self._setup_specialized_handlers()
            
            self.initialized = True
            logger.info("📝 Système de logging JARVIS initialisé")
            logger.info(f"📊 Console: {console_level} | Fichiers: {'activés' if enable_file_logging else 'désactivés'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur configuration logging: {e}")
            return False
    
    def _setup_file_logging(self, log_file: str, level: str, rotation: str, 
                           retention: str, format_string: str, json_logs: bool):
        """Configure les handlers de fichiers"""
        
        # Créer le répertoire de logs
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # === LOG PRINCIPAL ===
        if json_logs:
            main_format = self._json_formatter
        else:
            main_format = format_string
        
        main_handler = logger.add(
            log_file,
            level=level.upper(),
            format=main_format,
            rotation=rotation,
            retention=retention,
            compression="gz",
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
        self.handlers['main_file'] = main_handler
        
        # === LOG D'ERREURS ===
        error_file = log_path.parent / f"{log_path.stem}_errors{log_path.suffix}"
        error_handler = logger.add(
            str(error_file),
            level="ERROR",
            format=format_string,
            rotation=rotation,
            retention=retention,
            compression="gz",
            filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"],
            backtrace=True,
            diagnose=True,
            encoding="utf-8"
        )
        self.handlers['error_file'] = error_handler
        
        # === LOG DEBUG (si activé) ===
        if level.upper() == "DEBUG":
            debug_file = log_path.parent / f"{log_path.stem}_debug{log_path.suffix}"
            debug_handler = logger.add(
                str(debug_file),
                level="DEBUG",
                format=format_string,
                rotation="50 MB",  # Plus petit pour debug
                retention="7 days",  # Moins long pour debug
                compression="gz",
                filter=lambda record: record["level"].name == "DEBUG",
                encoding="utf-8"
            )
            self.handlers['debug_file'] = debug_handler
    
    def _setup_specialized_handlers(self):
        """Configure des handlers spécialisés par module"""
        
        log_dir = Path(settings.log_file_path).parent
        
        # === LOG API ===
        api_handler = logger.add(
            str(log_dir / "api.log"),
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | API | {message}",
            rotation="10 MB",
            retention="14 days",
            filter=lambda record: "api" in record.get("extra", {}).get("module", "").lower() or 
                                 "fastapi" in record.get("name", "").lower() or
                                 "uvicorn" in record.get("name", "").lower(),
            encoding="utf-8"
        )
        self.handlers['api'] = api_handler
        
        # === LOG MÉMOIRE ===
        memory_handler = logger.add(
            str(log_dir / "memory.log"),
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | MEMORY | {message}",
            rotation="5 MB",
            retention="30 days",
            filter=lambda record: "memory" in record.get("extra", {}).get("module", "").lower(),
            encoding="utf-8"
        )
        self.handlers['memory'] = memory_handler
        
        # === LOG VOICE ===
        voice_handler = logger.add(
            str(log_dir / "voice.log"),
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | VOICE | {message}",
            rotation="5 MB",
            retention="7 days",
            filter=lambda record: "voice" in record.get("extra", {}).get("module", "").lower(),
            encoding="utf-8"
        )
        self.handlers['voice'] = voice_handler
        
        # === LOG PERFORMANCE ===
        perf_handler = logger.add(
            str(log_dir / "performance.log"),
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {extra[duration]:>8.3f}s | {extra[operation]:<20} | {message}",
            rotation="20 MB",
            retention="14 days",
            filter=lambda record: "performance" in record.get("extra", {}),
            encoding="utf-8"
        )
        self.handlers['performance'] = perf_handler
    
    def _get_console_format(self, base_format: str) -> str:
        """Génère le format pour la console avec couleurs"""
        return (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    
    def _console_filter(self, record):
        """Filtre les logs pour la console"""
        # Réduire la verbosité de certains modules
        name = record.get("name", "")
        level = record.get("level", {}).get("name", "")
        
        # Filtrer les logs trop verbeux
        if "httpx" in name and level == "DEBUG":
            return False
        if "urllib3" in name and level in ["DEBUG", "INFO"]:
            return False
        if "chromadb" in name and level == "DEBUG":
            return False
            
        return True
    
    def _json_formatter(self, record):
        """Formateur JSON pour les logs structurés"""
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
            "process": record["process"].id,
            "thread": record["thread"].id
        }
        
        # Ajouter les données extra
        if "extra" in record:
            log_entry.update(record["extra"])
        
        # Ajouter l'exception si présente
        if record.get("exception"):
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des logs"""
        log_dir = Path(settings.log_file_path).parent
        
        if not log_dir.exists():
            return {"error": "Répertoire de logs non trouvé"}
        
        stats = {
            "log_directory": str(log_dir),
            "handlers_active": len(self.handlers),
            "files": {},
            "total_size_mb": 0,
            "oldest_log": None,
            "newest_log": None
        }
        
        # Analyser les fichiers de logs
        for log_file in log_dir.glob("*.log*"):
            try:
                file_stats = log_file.stat()
                size_mb = file_stats.st_size / 1024 / 1024
                
                stats["files"][log_file.name] = {
                    "size_mb": round(size_mb, 2),
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "lines": self._count_log_lines(log_file) if log_file.suffix == ".log" else None
                }
                
                stats["total_size_mb"] += size_mb
                
                # Mettre à jour oldest/newest
                if not stats["oldest_log"] or file_stats.st_mtime < Path(log_dir / stats["oldest_log"]).stat().st_mtime:
                    stats["oldest_log"] = log_file.name
                
                if not stats["newest_log"] or file_stats.st_mtime > Path(log_dir / stats["newest_log"]).stat().st_mtime:
                    stats["newest_log"] = log_file.name
                    
            except Exception as e:
                stats["files"][log_file.name] = {"error": str(e)}
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats
    
    def _count_log_lines(self, log_file: Path, max_lines: int = 10000) -> Optional[int]:
        """Compte approximativement le nombre de lignes dans un fichier de log"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = 0
                for _ in f:
                    lines += 1
                    if lines >= max_lines:
                        return f"{max_lines}+"
                return lines
        except:
            return None
    
    def cleanup_old_logs(self, days_old: int = 30) -> Dict[str, Any]:
        """Nettoie les anciens fichiers de logs"""
        log_dir = Path(settings.log_file_path).parent
        
        if not log_dir.exists():
            return {"error": "Répertoire de logs non trouvé"}
        
        import time
        cutoff_time = time.time() - (days_old * 24 * 3600)
        
        cleanup_stats = {
            "files_checked": 0,
            "files_deleted": 0,
            "space_freed_mb": 0,
            "errors": []
        }
        
        for log_file in log_dir.glob("*.log.*"):  # Fichiers compressés ou rotatés
            try:
                file_stats = log_file.stat()
                cleanup_stats["files_checked"] += 1
                
                if file_stats.st_mtime < cutoff_time:
                    size_mb = file_stats.st_size / 1024 / 1024
                    log_file.unlink()
                    
                    cleanup_stats["files_deleted"] += 1
                    cleanup_stats["space_freed_mb"] += size_mb
                    
            except Exception as e:
                cleanup_stats["errors"].append(f"{log_file.name}: {str(e)}")
        
        cleanup_stats["space_freed_mb"] = round(cleanup_stats["space_freed_mb"], 2)
        return cleanup_stats
    
    def get_recent_logs(self, level: str = "INFO", lines: int = 100) -> List[str]:
        """Récupère les logs récents"""
        log_file = Path(settings.log_file_path)
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # Filtrer par niveau si spécifié
            if level and level != "ALL":
                filtered_lines = []
                for line in all_lines:
                    if f"| {level.upper():<8} |" in line:
                        filtered_lines.append(line.strip())
                return filtered_lines[-lines:]
            
            return [line.strip() for line in all_lines[-lines:]]
            
        except Exception as e:
            return [f"Erreur lecture logs: {str(e)}"]

# Instance globale
jarvis_logger = JarvisLogger()

# Fonctions de convenance
def setup_logging(**kwargs):
    """Configure le système de logging"""
    return jarvis_logger.setup_logging(**kwargs)

def log_performance(operation: str, duration: float, details: str = ""):
    """Log une opération de performance"""
    logger.bind(performance=True, operation=operation, duration=duration).info(
        f"{operation} - {details}" if details else operation
    )

def log_api_request(method: str, path: str, status_code: int, duration: float):
    """Log une requête API"""
    logger.bind(module="api").info(
        f"{method} {path} - {status_code} ({duration:.3f}s)"
    )

def log_memory_operation(operation: str, details: Dict[str, Any]):
    """Log une opération mémoire"""
    logger.bind(module="memory", **details).info(operation)

def log_voice_activity(activity: str, details: str = ""):
    """Log une activité vocale"""
    logger.bind(module="voice").info(f"{activity} - {details}" if details else activity)

def get_logger(name: str):
    """Obtient un logger nommé"""
    return logger.bind(name=name)

# Configuration automatique au démarrage
if not jarvis_logger.initialized:
    setup_logging()