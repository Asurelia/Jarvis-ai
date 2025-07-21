"""
🏥 Routes de santé - JARVIS Brain API
Endpoints pour monitoring et diagnostics
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import time
import psutil
import platform
import asyncio
import aiohttp
import asyncpg
import redis.asyncio as redis
import subprocess
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration des services externes
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/jarvis")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

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
        "database": await check_database(),
        "redis": await check_redis(),
        "ollama": await check_ollama(),
        "memory": await check_memory_system(),
        "agent": await check_agent_system(),
        "metacognition": await check_metacognition_system()
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

async def check_database() -> bool:
    """Vérification de la connexion à la base de données"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("SELECT 1")
        await conn.close()
        return True
    except Exception as e:
        logger.warning(f"Database check failed: {e}")
        return False

async def check_redis() -> bool:
    """Vérification de la connexion Redis"""
    try:
        r = redis.from_url(REDIS_URL)
        await r.ping()
        await r.close()
        return True
    except Exception as e:
        logger.warning(f"Redis check failed: {e}")
        return False

async def check_ollama() -> bool:
    """Vérification du service Ollama"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_URL}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
    except Exception as e:
        logger.warning(f"Ollama check failed: {e}")
        return False

async def check_memory_system() -> bool:
    """Vérification du système de mémoire"""
    try:
        # Vérifier si le répertoire de mémoire existe et est accessible
        memory_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "memory")
        if os.path.exists(memory_dir) and os.access(memory_dir, os.R_OK | os.W_OK):
            return True
        return False
    except Exception as e:
        logger.warning(f"Memory system check failed: {e}")
        return False

async def check_agent_system() -> bool:
    """Vérification du système d'agent"""
    try:
        # Vérifier si les composants agent sont importables
        from core.agent import ReactAgent
        return True
    except Exception as e:
        logger.warning(f"Agent system check failed: {e}")
        return False

async def check_metacognition_system() -> bool:
    """Vérification du système de métacognition"""
    try:
        # Vérifier si les composants métacognition sont importables
        from core.metacognition import MetacognitionEngine
        return True
    except Exception as e:
        logger.warning(f"Metacognition system check failed: {e}")
        return False

@router.get("/services")
async def services_status() -> Dict[str, Any]:
    """Status détaillé de tous les services externes"""
    services = {}
    
    # Test PostgreSQL
    db_start = time.time()
    services["postgresql"] = {
        "status": "checking...",
        "response_time": None,
        "details": {}
    }
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        result = await conn.fetchval("SELECT version()")
        await conn.close()
        services["postgresql"] = {
            "status": "healthy",
            "response_time": time.time() - db_start,
            "details": {"version": result}
        }
    except Exception as e:
        services["postgresql"] = {
            "status": "unhealthy",
            "response_time": time.time() - db_start,
            "details": {"error": str(e)}
        }
    
    # Test Redis
    redis_start = time.time()
    try:
        r = redis.from_url(REDIS_URL)
        info = await r.info()
        await r.close()
        services["redis"] = {
            "status": "healthy",
            "response_time": time.time() - redis_start,
            "details": {
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human")
            }
        }
    except Exception as e:
        services["redis"] = {
            "status": "unhealthy", 
            "response_time": time.time() - redis_start,
            "details": {"error": str(e)}
        }
    
    # Test Ollama
    ollama_start = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_URL}/api/tags", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    services["ollama"] = {
                        "status": "healthy",
                        "response_time": time.time() - ollama_start,
                        "details": {
                            "models": [model["name"] for model in data.get("models", [])],
                            "model_count": len(data.get("models", []))
                        }
                    }
                else:
                    services["ollama"] = {
                        "status": "unhealthy",
                        "response_time": time.time() - ollama_start,
                        "details": {"http_status": response.status}
                    }
    except Exception as e:
        services["ollama"] = {
            "status": "unhealthy",
            "response_time": time.time() - ollama_start,
            "details": {"error": str(e)}
        }
    
    return {
        "timestamp": time.time(),
        "services": services,
        "summary": {
            "total": len(services),
            "healthy": len([s for s in services.values() if s["status"] == "healthy"]),
            "unhealthy": len([s for s in services.values() if s["status"] == "unhealthy"])
        }
    }

# Initialiser temps de démarrage
health_check.start_time = time.time()