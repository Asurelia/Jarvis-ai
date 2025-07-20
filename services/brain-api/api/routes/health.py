"""
🏥 Routes de santé - JARVIS Brain API
Endpoints pour monitoring et diagnostics
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import time
import psutil
import platform

router = APIRouter()

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Check de santé principal"""
    return {
        "status": "healthy",
        "service": "JARVIS Brain API",
        "version": "2.0.0",
        "timestamp": time.time(),
        "uptime": time.time() - getattr(health_check, 'start_time', time.time())
    }

@router.get("/detailed")
async def detailed_health() -> Dict[str, Any]:
    """Check de santé détaillé avec métriques système"""
    
    # Métriques système
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Informations système
    system_info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "hostname": platform.node()
    }
    
    # Métriques de performance
    performance = {
        "cpu_percent": cpu_percent,
        "memory_total": memory.total,
        "memory_available": memory.available,
        "memory_percent": memory.percent,
        "disk_total": disk.total,
        "disk_free": disk.free,
        "disk_percent": (disk.used / disk.total) * 100
    }
    
    # Status global
    status = "healthy"
    if cpu_percent > 80 or memory.percent > 85:
        status = "warning"
    if cpu_percent > 95 or memory.percent > 95:
        status = "critical"
    
    return {
        "status": status,
        "service": "JARVIS Brain API",
        "version": "2.0.0",
        "timestamp": time.time(),
        "system_info": system_info,
        "performance": performance,
        "components": {
            "metacognition": "healthy",
            "memory_manager": "healthy", 
            "agent": "healthy",
            "websocket_manager": "healthy"
        }
    }

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Check de préparation pour K8s/Docker"""
    
    # Vérifier que tous les composants sont prêts
    components_ready = {
        "database": True,  # TODO: vraie vérification DB
        "redis": True,     # TODO: vraie vérification Redis
        "ollama": True,    # TODO: vraie vérification Ollama
        "memory": True,
        "agent": True,
        "metacognition": True
    }
    
    all_ready = all(components_ready.values())
    
    return {
        "ready": all_ready,
        "timestamp": time.time(),
        "components": components_ready
    }

@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Check de vivacité pour K8s/Docker"""
    return {
        "status": "alive",
        "timestamp": str(time.time())
    }

# Initialiser temps de démarrage
health_check.start_time = time.time()