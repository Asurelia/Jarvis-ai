#!/usr/bin/env python3
"""
🔍 JARVIS Network Monitor Service
Monitore la connectivité Host Ollama et les services Docker
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog

# Configuration logging
logger = structlog.get_logger(__name__)

@dataclass
class EndpointStatus:
    name: str
    url: str
    status: str  # healthy, unhealthy, unknown
    last_check: datetime
    response_time: float
    error_count: int
    success_count: int
    uptime_percentage: float
    last_error: Optional[str] = None

class NetworkStats(BaseModel):
    total_checks: int
    successful_checks: int
    failed_checks: int
    average_response_time: float
    uptime_percentage: float
    endpoints: Dict[str, dict]
    last_update: str

class NetworkMonitorConfig:
    """Configuration du monitor réseau"""
    
    def __init__(self):
        self.monitor_interval = int(os.getenv("MONITOR_INTERVAL", "30"))
        self.host_ollama_url = os.getenv("HOST_OLLAMA_URL", "http://host.docker.internal:11434")
        self.fallback_ollama_url = os.getenv("FALLBACK_OLLAMA_URL", "http://ollama-fallback:11434")
        self.alert_threshold_failures = int(os.getenv("ALERT_THRESHOLD_FAILURES", "3"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Services supplémentaires à monitorer
        self.additional_services = {
            "brain-api": "http://brain-api:8080/health",
            "llm-gateway": "http://llm-gateway:5010/health",
            "redis": "http://redis:6379",  # Nécessitera adaptation
            "memory-db": "http://memory-db:5432"  # Nécessitera adaptation
        }

class NetworkMonitor:
    """Moniteur de connectivité réseau pour JARVIS"""
    
    def __init__(self, config: NetworkMonitorConfig):
        self.config = config
        self.endpoints: Dict[str, EndpointStatus] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.stats_history: List[Dict] = []
        self.max_history_size = 1000
        
        # Initialiser les endpoints
        self._initialize_endpoints()
        
    def _initialize_endpoints(self):
        """Initialiser les endpoints à monitorer"""
        current_time = datetime.now()
        
        # Ollama Host
        self.endpoints["host_ollama"] = EndpointStatus(
            name="host_ollama",
            url=self.config.host_ollama_url,
            status="unknown",
            last_check=current_time,
            response_time=0.0,
            error_count=0,
            success_count=0,
            uptime_percentage=100.0
        )
        
        # Ollama Fallback
        self.endpoints["fallback_ollama"] = EndpointStatus(
            name="fallback_ollama",
            url=self.config.fallback_ollama_url,
            status="unknown",
            last_check=current_time,
            response_time=0.0,
            error_count=0,
            success_count=0,
            uptime_percentage=100.0
        )
        
        # Services additionnels
        for name, url in self.config.additional_services.items():
            self.endpoints[name] = EndpointStatus(
                name=name,
                url=url,
                status="unknown",
                last_check=current_time,
                response_time=0.0,
                error_count=0,
                success_count=0,
                uptime_percentage=100.0
            )
        
        logger.info("Network Monitor initialized", 
                   endpoints=list(self.endpoints.keys()),
                   interval=self.config.monitor_interval)

    async def check_endpoint(self, endpoint: EndpointStatus) -> bool:
        """Vérifier un endpoint spécifique"""
        start_time = time.time()
        
        try:
            # Adapter le check selon le type de service
            if "ollama" in endpoint.name:
                success = await self._check_ollama(endpoint.url)
            elif endpoint.name == "redis":
                success = await self._check_redis()
            elif endpoint.name == "memory-db":
                success = await self._check_postgres()
            else:
                success = await self._check_http_health(endpoint.url)
            
            response_time = time.time() - start_time
            
            if success:
                endpoint.status = "healthy"
                endpoint.success_count += 1
                endpoint.response_time = response_time
                endpoint.last_error = None
                logger.debug("Endpoint check successful", 
                           endpoint=endpoint.name, 
                           response_time=response_time)
            else:
                endpoint.status = "unhealthy"
                endpoint.error_count += 1
                endpoint.last_error = "Connection failed"
                logger.warning("Endpoint check failed", endpoint=endpoint.name)
                
        except Exception as e:
            endpoint.status = "unhealthy"
            endpoint.error_count += 1
            endpoint.last_error = str(e)
            logger.error("Endpoint check error", 
                        endpoint=endpoint.name, 
                        error=str(e))
            success = False
        
        endpoint.last_check = datetime.now()
        
        # Calculer l'uptime
        total_checks = endpoint.success_count + endpoint.error_count
        if total_checks > 0:
            endpoint.uptime_percentage = (endpoint.success_count / total_checks) * 100
        
        # Alertes si trop d'échecs consécutifs
        if endpoint.error_count >= self.config.alert_threshold_failures:
            await self._send_alert(endpoint)
        
        return success

    async def _check_ollama(self, url: str) -> bool:
        """Vérifier un service Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except:
            return False

    async def _check_http_health(self, url: str) -> bool:
        """Vérifier un endpoint HTTP health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False

    async def _check_redis(self) -> bool:
        """Vérifier Redis (simplifiée pour le moment)"""
        # TODO: Implémenter un check Redis proper
        return True

    async def _check_postgres(self) -> bool:
        """Vérifier PostgreSQL (simplifiée pour le moment)"""
        # TODO: Implémenter un check PostgreSQL proper
        return True

    async def _send_alert(self, endpoint: EndpointStatus):
        """Envoyer une alerte pour un endpoint défaillant"""
        # TODO: Implémenter système d'alertes (webhook, email, etc.)
        logger.critical("ALERT: Endpoint failure threshold reached",
                       endpoint=endpoint.name,
                       error_count=endpoint.error_count,
                       last_error=endpoint.last_error)

    async def monitoring_loop(self):
        """Boucle principale de monitoring"""
        while True:
            try:
                # Vérifier tous les endpoints
                tasks = [self.check_endpoint(endpoint) for endpoint in self.endpoints.values()]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Enregistrer les statistiques
                await self._record_stats()
                
                # Attendre le prochain cycle
                await asyncio.sleep(self.config.monitor_interval)
                
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error("Monitoring loop error", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying

    async def _record_stats(self):
        """Enregistrer les statistiques dans l'historique"""
        current_time = datetime.now()
        
        stats = {
            "timestamp": current_time.isoformat(),
            "endpoints": {
                name: {
                    "status": ep.status,
                    "response_time": ep.response_time,
                    "uptime_percentage": ep.uptime_percentage,
                    "error_count": ep.error_count,
                    "success_count": ep.success_count
                }
                for name, ep in self.endpoints.items()
            }
        }
        
        self.stats_history.append(stats)
        
        # Limiter la taille de l'historique
        if len(self.stats_history) > self.max_history_size:
            self.stats_history.pop(0)

    def get_network_stats(self) -> NetworkStats:
        """Obtenir les statistiques réseau actuelles"""
        total_checks = sum(ep.success_count + ep.error_count for ep in self.endpoints.values())
        successful_checks = sum(ep.success_count for ep in self.endpoints.values())
        failed_checks = sum(ep.error_count for ep in self.endpoints.values())
        
        avg_response_time = 0.0
        healthy_endpoints = [ep for ep in self.endpoints.values() if ep.status == "healthy"]
        if healthy_endpoints:
            avg_response_time = sum(ep.response_time for ep in healthy_endpoints) / len(healthy_endpoints)
        
        overall_uptime = 0.0
        if self.endpoints:
            overall_uptime = sum(ep.uptime_percentage for ep in self.endpoints.values()) / len(self.endpoints)
        
        return NetworkStats(
            total_checks=total_checks,
            successful_checks=successful_checks,
            failed_checks=failed_checks,
            average_response_time=avg_response_time,
            uptime_percentage=overall_uptime,
            endpoints={name: asdict(ep) for name, ep in self.endpoints.items()},
            last_update=datetime.now().isoformat()
        )

    async def start_monitoring(self):
        """Démarrer le monitoring"""
        if self.monitoring_task is None or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(self.monitoring_loop())
            logger.info("Network monitoring started")

    async def stop_monitoring(self):
        """Arrêter le monitoring"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Network monitoring stopped")

# Configuration et instances globales
config = NetworkMonitorConfig()
monitor = NetworkMonitor(config)

# FastAPI Application
app = FastAPI(
    title="JARVIS Network Monitor",
    description="Network connectivity monitoring for JARVIS services",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Démarrage de l'application"""
    await monitor.start_monitoring()

@app.on_event("shutdown") 
async def shutdown():
    """Arrêt de l'application"""
    await monitor.stop_monitoring()

@app.get("/health")
async def health():
    """Health check du monitor lui-même"""
    return {
        "status": "healthy",
        "monitoring_active": monitor.monitoring_task is not None and not monitor.monitoring_task.done(),
        "endpoints_monitored": len(monitor.endpoints),
        "uptime": datetime.now().isoformat()
    }

@app.get("/status", response_model=NetworkStats)
async def get_network_status():
    """Obtenir le statut réseau complet"""
    return monitor.get_network_stats()

@app.get("/endpoints/{endpoint_name}")
async def get_endpoint_status(endpoint_name: str):
    """Obtenir le statut d'un endpoint spécifique"""
    if endpoint_name not in monitor.endpoints:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    endpoint = monitor.endpoints[endpoint_name]
    return asdict(endpoint)

@app.post("/check/{endpoint_name}")
async def force_check_endpoint(endpoint_name: str):
    """Forcer la vérification d'un endpoint"""
    if endpoint_name not in monitor.endpoints:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    endpoint = monitor.endpoints[endpoint_name]
    success = await monitor.check_endpoint(endpoint)
    
    return {
        "endpoint": endpoint_name,
        "check_result": success,
        "status": endpoint.status,
        "response_time": endpoint.response_time
    }

@app.get("/history")
async def get_history(limit: int = 100):
    """Obtenir l'historique des statistiques"""
    return {
        "history": monitor.stats_history[-limit:],
        "total_records": len(monitor.stats_history)
    }

@app.get("/alerts")
async def get_alerts():
    """Obtenir les alertes actives"""
    alerts = []
    for name, endpoint in monitor.endpoints.items():
        if endpoint.error_count >= config.alert_threshold_failures:
            alerts.append({
                "endpoint": name,
                "status": endpoint.status,
                "error_count": endpoint.error_count,
                "last_error": endpoint.last_error,
                "uptime": endpoint.uptime_percentage
            })
    
    return {"active_alerts": alerts, "alert_count": len(alerts)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5011,
        log_level=config.log_level.lower(),
        reload=False
    )