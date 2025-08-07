"""
🖥️ System Control Service - JARVIS 2025 (Simplified)
Service de contrôle système sécurisé sans GUI automation
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
import uvicorn
import psutil
import platform
import time
import json
import hashlib
import hmac
import secrets
import logging
import asyncio
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os
import threading
from dataclasses import dataclass
from enum import Enum

# Prometheus monitoring
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import structlog

# Configuration
SYSTEM_OS = platform.system()
SERVICE_PORT = 5004
API_VERSION = "2.0.0"

# Configuration sécurité
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "true").lower() == "true"
MAX_ACTIONS_PER_MINUTE = int(os.getenv("MAX_ACTIONS_PER_MINUTE", "60"))

# Logging sécurisé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/system-control.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Security models
class SystemAction(BaseModel):
    action_type: str = Field(..., description="Type d'action système")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = Field(default=True)
    
class SystemStatus(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    network_io: Dict[str, int]
    running_processes: int
    system_uptime: float
    os_info: Dict[str, str]

class ActionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    action_id: str
    timestamp: datetime

# FastAPI app
app = FastAPI(
    title="JARVIS System Control Service (Simple)",
    description="Service de contrôle système sécurisé - Mode simplifié",
    version=API_VERSION,
    docs_url="/docs" if not SANDBOX_MODE else None,
    redoc_url="/redoc" if not SANDBOX_MODE else None
)

# Security
security = HTTPBearer()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Prometheus metrics
REGISTRY = CollectorRegistry()
REQUEST_COUNT = Counter('system_control_requests_total', 'Total requests', ['method', 'endpoint'], registry=REGISTRY)
REQUEST_DURATION = Histogram('system_control_request_duration_seconds', 'Request duration', registry=REGISTRY)
SYSTEM_ACTIONS = Counter('system_actions_total', 'System actions executed', ['action_type'], registry=REGISTRY)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Vérification basique du token"""
    if SANDBOX_MODE and credentials.credentials != "dev-token":
        raise HTTPException(status_code=403, detail="Invalid token")
    return credentials.credentials

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "system-control",
        "version": API_VERSION,
        "mode": "simple",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

@app.get("/system/status", response_model=SystemStatus)
async def get_system_status(token: str = Depends(verify_token)):
    """Obtenir le statut système détaillé"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk_usage = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100
                }
            except PermissionError:
                continue
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Running processes
        running_processes = len(psutil.pids())
        
        # System uptime
        boot_time = psutil.boot_time()
        system_uptime = time.time() - boot_time
        
        # OS info
        os_info = {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        
        return SystemStatus(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage=disk_usage,
            network_io=network_io,
            running_processes=running_processes,
            system_uptime=system_uptime,
            os_info=os_info
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@app.get("/system/processes")
async def get_running_processes(token: str = Depends(verify_token), limit: int = 50):
    """Obtenir la liste des processus en cours"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Trier par utilisation CPU
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        
        return {
            "processes": processes[:limit],
            "total_count": len(processes),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processes: {str(e)}")

@app.post("/system/action/simple", response_model=ActionResponse)
async def execute_simple_action(
    action: SystemAction,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Exécuter une action système simple (non-GUI)"""
    
    action_id = secrets.token_hex(8)
    
    try:
        logger.info(f"Executing simple action: {action.action_type} (ID: {action_id})")
        
        if action.action_type == "get_disk_usage":
            result = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    result[partition.mountpoint] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": round((usage.used / usage.total) * 100, 2)
                    }
                except PermissionError:
                    continue
            
            SYSTEM_ACTIONS.labels(action_type=action.action_type).inc()
            
            return ActionResponse(
                success=True,
                message="Disk usage retrieved successfully",
                data=result,
                action_id=action_id,
                timestamp=datetime.now()
            )
        
        elif action.action_type == "get_memory_info":
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            result = {
                "virtual_memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "swap_memory": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent
                }
            }
            
            SYSTEM_ACTIONS.labels(action_type=action.action_type).inc()
            
            return ActionResponse(
                success=True,
                message="Memory info retrieved successfully",
                data=result,
                action_id=action_id,
                timestamp=datetime.now()
            )
        
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Action type '{action.action_type}' not supported in simple mode"
            )
            
    except Exception as e:
        logger.error(f"Error executing action {action.action_type}: {e}")
        return ActionResponse(
            success=False,
            message=f"Failed to execute action: {str(e)}",
            action_id=action_id,
            timestamp=datetime.now()
        )

@app.get("/")
async def root():
    return {
        "service": "JARVIS System Control Service",
        "version": API_VERSION,
        "mode": "simple",
        "status": "operational",
        "features": [
            "System monitoring",
            "Process information",
            "Resource usage tracking"
        ],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    logger.info(f"Starting JARVIS System Control Service (Simple) on port {SERVICE_PORT}")
    logger.info(f"Sandbox mode: {SANDBOX_MODE}")
    logger.info(f"OS: {SYSTEM_OS}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVICE_PORT,
        log_level="info"
    )