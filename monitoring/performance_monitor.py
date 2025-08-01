#!/usr/bin/env python3
"""
📊 JARVIS Performance Monitor
Monitoring en temps réel des métriques de performance avec alertes
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import psutil
import redis.asyncio as redis
import httpx
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlertConfig:
    """Configuration des alertes"""
    # Seuils de latence (ms)
    response_time_warning: float = 1000
    response_time_critical: float = 5000
    
    # Seuils d'utilisation système
    cpu_warning: float = 80.0
    cpu_critical: float = 95.0
    memory_warning: float = 85.0
    memory_critical: float = 95.0
    
    # Seuils de taux d'erreur (%)
    error_rate_warning: float = 5.0
    error_rate_critical: float = 15.0
    
    # Seuils de débit
    throughput_warning: float = 10.0  # req/s minimum
    
    # Configuration des pools
    db_connections_warning: float = 0.8  # 80% du pool
    redis_connections_warning: float = 0.8

@dataclass
class MetricSnapshot:
    """Snapshot des métriques à un instant donné"""
    timestamp: datetime
    
    # Métriques HTTP
    http_requests_total: int = 0
    http_request_duration: float = 0.0
    http_error_rate: float = 0.0
    
    # Métriques système
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    
    # Métriques base de données
    db_connections_active: int = 0
    db_connections_idle: int = 0
    db_query_duration: float = 0.0
    
    # Métriques Redis
    redis_connections: int = 0
    redis_memory_usage: int = 0
    redis_hit_rate: float = 0.0
    
    # Métriques custom JARVIS
    llm_cache_hit_rate: float = 0.0
    circuit_breaker_state: Dict[str, str] = None
    active_websockets: int = 0
    
    def __post_init__(self):
        if self.circuit_breaker_state is None:
            self.circuit_breaker_state = {}

class PerformanceMonitor:
    """
    Moniteur de performance JARVIS avec:
    - Collecte de métriques en temps réel
    - Alertes automatiques
    - Export Prometheus
    - Dashboards dynamiques
    - Analyse des tendances
    """
    
    def __init__(
        self,
        config: AlertConfig = None,
        endpoints: Dict[str, str] = None,
        db_url: str = "postgresql://jarvis:jarvis123@localhost:5432/jarvis_memory",
        redis_url: str = "redis://localhost:6379"
    ):
        self.config = config or AlertConfig()
        self.endpoints = endpoints or {
            "brain-api": "http://localhost:5000/health",
            "tts-service": "http://localhost:5002/health",
            "stt-service": "http://localhost:5003/health",
            "ollama": "http://localhost:11434/api/tags"
        }
        self.db_url = db_url
        self.redis_url = redis_url
        
        # Collecteurs Prometheus
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()
        
        # Clients
        self.http_client = None
        self.redis_client = None
        self.db_engine = None
        
        # Stockage des métriques
        self.metrics_history: List[MetricSnapshot] = []
        self.max_history_size = 1000
        
        # État des alertes
        self.active_alerts: Dict[str, datetime] = {}
        self.alert_cooldown = 300  # 5 minutes
        
        # Statistiques
        self.stats = {
            "monitoring_start": datetime.now(),
            "total_snapshots": 0,
            "alerts_triggered": 0,
            "services_monitored": len(self.endpoints)
        }
        
        self.running = False
        
        logger.info(f"📊 Performance Monitor initialisé - {len(self.endpoints)} services")
    
    def _setup_prometheus_metrics(self):
        """Configurer les métriques Prometheus"""
        # Métriques HTTP
        self.http_requests = Counter(
            'jarvis_http_requests_total',
            'Total HTTP requests',
            ['service', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_duration = Histogram(
            'jarvis_http_request_duration_seconds',
            'HTTP request duration',
            ['service', 'endpoint'],
            registry=self.registry
        )
        
        # Métriques système
        self.system_cpu = Gauge(
            'jarvis_system_cpu_usage_percent',
            'System CPU usage',
            registry=self.registry
        )
        
        self.system_memory = Gauge(
            'jarvis_system_memory_usage_percent',
            'System memory usage',
            registry=self.registry
        )
        
        # Métriques base de données
        self.db_connections = Gauge(
            'jarvis_db_connections',
            'Database connections',
            ['state'],
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'jarvis_db_query_duration_seconds',
            'Database query duration',
            registry=self.registry
        )
        
        # Métriques Redis
        self.redis_memory = Gauge(
            'jarvis_redis_memory_bytes',
            'Redis memory usage',
            registry=self.registry
        )
        
        self.redis_hit_rate = Gauge(
            'jarvis_redis_hit_rate_percent',
            'Redis cache hit rate',
            registry=self.registry
        )
        
        # Métriques custom JARVIS
        self.llm_cache_hits = Gauge(
            'jarvis_llm_cache_hit_rate_percent',
            'LLM cache hit rate',
            registry=self.registry
        )
        
        self.circuit_breaker_state = Gauge(
            'jarvis_circuit_breaker_open',
            'Circuit breaker state (1=open, 0=closed)',
            ['service'],
            registry=self.registry
        )
        
        self.websocket_connections = Gauge(
            'jarvis_websocket_connections_active',
            'Active WebSocket connections',
            registry=self.registry
        )
    
    async def setup(self):
        """Initialiser les connexions"""
        # Client HTTP
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=20)
        )
        
        # Client Redis
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Redis connecté pour monitoring")
        except Exception as e:
            logger.warning(f"⚠️ Redis non disponible: {e}")
        
        # Engine PostgreSQL
        try:
            self.db_engine = create_engine(
                self.db_url,
                pool_size=5,
                max_overflow=10,
                echo=False
            )
            
            with self.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ PostgreSQL connecté pour monitoring")
            
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL non disponible: {e}")
    
    async def cleanup(self):
        """Nettoyer les ressources"""
        self.running = False
        
        if self.http_client:
            await self.http_client.aclose()
        
        if self.redis_client:
            await self.redis_client.aclose()
        
        if self.db_engine:
            self.db_engine.dispose()
    
    async def collect_system_metrics(self) -> Dict[str, float]:
        """Collecter métriques système"""
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Mettre à jour Prometheus
        self.system_cpu.set(cpu_usage)
        self.system_memory.set(memory.percent)
        
        return {
            "cpu_usage": cpu_usage,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "memory_available_mb": memory.available / (1024 * 1024)
        }
    
    async def collect_http_metrics(self) -> Dict[str, Any]:
        """Collecter métriques HTTP des services"""
        metrics = {}
        
        for service_name, url in self.endpoints.items():
            try:
                start_time = time.time()
                response = await self.http_client.get(url)
                duration = time.time() - start_time
                
                # Métriques Prometheus
                self.http_requests.labels(
                    service=service_name,
                    endpoint="health",
                    status=str(response.status_code)
                ).inc()
                
                self.http_duration.labels(
                    service=service_name,
                    endpoint="health"
                ).observe(duration)
                
                metrics[service_name] = {
                    "status_code": response.status_code,
                    "response_time": duration,
                    "available": response.status_code < 400
                }
                
            except Exception as e:
                metrics[service_name] = {
                    "status_code": 0,
                    "response_time": 0,
                    "available": False,
                    "error": str(e)
                }
                
                self.http_requests.labels(
                    service=service_name,
                    endpoint="health",
                    status="error"
                ).inc()
        
        return metrics
    
    async def collect_database_metrics(self) -> Dict[str, Any]:
        """Collecter métriques base de données"""
        if not self.db_engine:
            return {}
        
        try:
            with self.db_engine.connect() as conn:
                # Statistiques des connexions
                result = conn.execute(text("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """))
                
                conn_stats = result.fetchone()
                
                # Statistiques des requêtes lentes
                result = conn.execute(text("""
                    SELECT 
                        COALESCE(AVG(mean_time), 0) as avg_query_time,
                        COALESCE(MAX(max_time), 0) as max_query_time
                    FROM pg_stat_statements 
                    WHERE calls > 0
                """))
                
                query_stats = result.fetchone()
                
                # Taille de la base
                result = conn.execute(text("""
                    SELECT pg_database_size(current_database()) as db_size
                """))
                
                size_stats = result.fetchone()
                
                # Mettre à jour Prometheus
                if conn_stats:
                    self.db_connections.labels(state="active").set(conn_stats[1] or 0)
                    self.db_connections.labels(state="idle").set(conn_stats[2] or 0)
                
                if query_stats and query_stats[0]:
                    self.db_query_duration.observe(query_stats[0] / 1000)  # Convertir en secondes
                
                return {
                    "total_connections": conn_stats[0] if conn_stats else 0,
                    "active_connections": conn_stats[1] if conn_stats else 0,
                    "idle_connections": conn_stats[2] if conn_stats else 0,
                    "avg_query_time": query_stats[0] if query_stats else 0,
                    "max_query_time": query_stats[1] if query_stats else 0,
                    "database_size_mb": (size_stats[0] / (1024 * 1024)) if size_stats else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur métriques DB: {e}")
            return {}
    
    async def collect_redis_metrics(self) -> Dict[str, Any]:
        """Collecter métriques Redis"""
        if not self.redis_client:
            return {}
        
        try:
            # Informations Redis
            info = await self.redis_client.info()
            
            # Statistiques keyspace
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)
            
            hit_rate = 0
            if keyspace_hits + keyspace_misses > 0:
                hit_rate = (keyspace_hits / (keyspace_hits + keyspace_misses)) * 100
            
            memory_usage = info.get('used_memory', 0)
            
            # Mettre à jour Prometheus
            self.redis_memory.set(memory_usage)
            self.redis_hit_rate.set(hit_rate)
            
            return {
                "memory_usage_bytes": memory_usage,
                "memory_usage_mb": memory_usage / (1024 * 1024),
                "hit_rate_percent": hit_rate,
                "connected_clients": info.get('connected_clients', 0),
                "total_commands_processed": info.get('total_commands_processed', 0),
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur métriques Redis: {e}")
            return {}
    
    async def collect_jarvis_metrics(self) -> Dict[str, Any]:
        """Collecter métriques spécifiques à JARVIS"""
        metrics = {}
        
        try:
            # Métriques du cache LLM
            if self.redis_client:
                llm_cache_keys = await self.redis_client.keys("llm_cache:*")
                query_cache_keys = await self.redis_client.keys("query_result:*")
                
                metrics["llm_cache_entries"] = len(llm_cache_keys)
                metrics["query_cache_entries"] = len(query_cache_keys)
            
            # État des circuit breakers via API
            try:
                response = await self.http_client.get("http://localhost:5000/api/circuit-breakers/stats")
                if response.status_code == 200:
                    cb_stats = response.json()
                    
                    for cb_name, cb_state in cb_stats.items():
                        state_value = 1 if cb_state.get("state") == "open" else 0
                        self.circuit_breaker_state.labels(service=cb_name).set(state_value)
                    
                    metrics["circuit_breakers"] = cb_stats
                
            except Exception:
                pass  # Circuit breaker stats optionnels
            
            # Connexions WebSocket actives
            try:
                response = await self.http_client.get("http://localhost:5000/api/websocket/stats")
                if response.status_code == 200:
                    ws_stats = response.json()
                    active_connections = ws_stats.get("active_connections", 0)
                    
                    self.websocket_connections.set(active_connections)
                    metrics["websocket_connections"] = active_connections
                
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"❌ Erreur métriques JARVIS: {e}")
        
        return metrics
    
    async def create_snapshot(self) -> MetricSnapshot:
        """Créer un snapshot complet des métriques"""
        timestamp = datetime.now()
        
        # Collecter toutes les métriques en parallèle
        system_metrics, http_metrics, db_metrics, redis_metrics, jarvis_metrics = await asyncio.gather(
            self.collect_system_metrics(),
            self.collect_http_metrics(),
            self.collect_database_metrics(),
            self.collect_redis_metrics(),
            self.collect_jarvis_metrics(),
            return_exceptions=True
        )
        
        # Gérer les exceptions
        if isinstance(system_metrics, Exception):
            logger.error(f"❌ Erreur métriques système: {system_metrics}")
            system_metrics = {}
        
        if isinstance(http_metrics, Exception):
            logger.error(f"❌ Erreur métriques HTTP: {http_metrics}")
            http_metrics = {}
        
        if isinstance(db_metrics, Exception):
            logger.error(f"❌ Erreur métriques DB: {db_metrics}")
            db_metrics = {}
        
        if isinstance(redis_metrics, Exception):
            logger.error(f"❌ Erreur métriques Redis: {redis_metrics}")
            redis_metrics = {}
        
        if isinstance(jarvis_metrics, Exception):
            logger.error(f"❌ Erreur métriques JARVIS: {jarvis_metrics}")
            jarvis_metrics = {}
        
        # Calculer métriques dérivées
        total_http_requests = sum(1 for service in http_metrics.values() if service.get("available"))
        avg_response_time = statistics.mean([
            service["response_time"] for service in http_metrics.values() 
            if service.get("response_time", 0) > 0
        ]) if http_metrics else 0
        
        error_count = sum(1 for service in http_metrics.values() if not service.get("available"))
        error_rate = (error_count / len(http_metrics) * 100) if http_metrics else 0
        
        snapshot = MetricSnapshot(
            timestamp=timestamp,
            http_requests_total=total_http_requests,
            http_request_duration=avg_response_time,
            http_error_rate=error_rate,
            cpu_usage=system_metrics.get("cpu_usage", 0),
            memory_usage=system_metrics.get("memory_usage", 0),
            disk_usage=system_metrics.get("disk_usage", 0),
            db_connections_active=db_metrics.get("active_connections", 0),
            db_connections_idle=db_metrics.get("idle_connections", 0),
            db_query_duration=db_metrics.get("avg_query_time", 0),
            redis_connections=redis_metrics.get("connected_clients", 0),
            redis_memory_usage=redis_metrics.get("memory_usage_bytes", 0),
            redis_hit_rate=redis_metrics.get("hit_rate_percent", 0),
            llm_cache_hit_rate=jarvis_metrics.get("llm_cache_hit_rate", 0),
            circuit_breaker_state=jarvis_metrics.get("circuit_breakers", {}),
            active_websockets=jarvis_metrics.get("websocket_connections", 0)
        )
        
        return snapshot
    
    def check_alerts(self, snapshot: MetricSnapshot):
        """Vérifier et déclencher les alertes"""
        alerts = []
        now = datetime.now()
        
        # Vérifier CPU
        if snapshot.cpu_usage > self.config.cpu_critical:
            alerts.append(("cpu_critical", f"CPU critique: {snapshot.cpu_usage:.1f}%"))
        elif snapshot.cpu_usage > self.config.cpu_warning:
            alerts.append(("cpu_warning", f"CPU élevé: {snapshot.cpu_usage:.1f}%"))
        
        # Vérifier mémoire
        if snapshot.memory_usage > self.config.memory_critical:
            alerts.append(("memory_critical", f"Mémoire critique: {snapshot.memory_usage:.1f}%"))
        elif snapshot.memory_usage > self.config.memory_warning:
            alerts.append(("memory_warning", f"Mémoire élevée: {snapshot.memory_usage:.1f}%"))
        
        # Vérifier temps de réponse
        if snapshot.http_request_duration > self.config.response_time_critical / 1000:
            alerts.append(("response_critical", f"Latence critique: {snapshot.http_request_duration*1000:.0f}ms"))
        elif snapshot.http_request_duration > self.config.response_time_warning / 1000:
            alerts.append(("response_warning", f"Latence élevée: {snapshot.http_request_duration*1000:.0f}ms"))
        
        # Vérifier taux d'erreur
        if snapshot.http_error_rate > self.config.error_rate_critical:
            alerts.append(("error_critical", f"Taux d'erreur critique: {snapshot.http_error_rate:.1f}%"))
        elif snapshot.http_error_rate > self.config.error_rate_warning:
            alerts.append(("error_warning", f"Taux d'erreur élevé: {snapshot.http_error_rate:.1f}%"))
        
        # Déclencher alertes (avec cooldown)
        for alert_type, message in alerts:
            if alert_type not in self.active_alerts or \
               (now - self.active_alerts[alert_type]).total_seconds() > self.alert_cooldown:
                
                logger.warning(f"🚨 ALERTE {alert_type.upper()}: {message}")
                self.active_alerts[alert_type] = now
                self.stats["alerts_triggered"] += 1
    
    def get_prometheus_metrics(self) -> str:
        """Obtenir métriques au format Prometheus"""
        return generate_latest(self.registry).decode('utf-8')
    
    async def run_monitoring_loop(self, interval: int = 30):
        """Boucle principale de monitoring"""
        logger.info(f"🚀 Démarrage monitoring - Intervalle: {interval}s")
        self.running = True
        
        await self.setup()
        
        try:
            while self.running:
                try:
                    # Créer snapshot
                    snapshot = await self.create_snapshot()
                    
                    # Ajouter à l'historique
                    self.metrics_history.append(snapshot)
                    if len(self.metrics_history) > self.max_history_size:
                        self.metrics_history.pop(0)
                    
                    # Vérifier alertes
                    self.check_alerts(snapshot)
                    
                    # Statistiques
                    self.stats["total_snapshots"] += 1
                    
                    # Log périodique
                    if self.stats["total_snapshots"] % 10 == 0:
                        logger.info(
                            f"📊 Snapshot #{self.stats['total_snapshots']} - "
                            f"CPU: {snapshot.cpu_usage:.1f}%, "
                            f"RAM: {snapshot.memory_usage:.1f}%, "
                            f"Latence: {snapshot.http_request_duration*1000:.0f}ms"
                        )
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur monitoring: {e}")
                    await asyncio.sleep(interval)
        
        finally:
            await self.cleanup()
    
    def get_dashboard_data(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Obtenir données pour dashboard"""
        since = datetime.now() - timedelta(minutes=duration_minutes)
        recent_snapshots = [
            s for s in self.metrics_history
            if s.timestamp >= since
        ]
        
        if not recent_snapshots:
            return {"error": "Pas de données récentes"}
        
        # Calculer statistiques
        cpu_values = [s.cpu_usage for s in recent_snapshots]
        memory_values = [s.memory_usage for s in recent_snapshots]
        response_times = [s.http_request_duration * 1000 for s in recent_snapshots]
        
        import statistics
        
        return {
            "period_minutes": duration_minutes,
            "samples_count": len(recent_snapshots),
            "timestamp": datetime.now().isoformat(),
            
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": statistics.mean(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "values": cpu_values[-60:]  # Dernières 60 valeurs
            },
            
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "average": statistics.mean(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0,
                "values": memory_values[-60:]
            },
            
            "response_time": {
                "current": response_times[-1] if response_times else 0,
                "average": statistics.mean(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "p95": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times) if response_times else 0,
                "values": response_times[-60:]
            },
            
            "alerts": {
                "active": len(self.active_alerts),
                "total": self.stats["alerts_triggered"]
            },
            
            "services": {
                "monitored": self.stats["services_monitored"],
                "uptime_hours": (datetime.now() - self.stats["monitoring_start"]).total_seconds() / 3600
            }
        }

async def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS Performance Monitor")
    parser.add_argument("--interval", type=int, default=30, help="Intervalle de monitoring (secondes)")
    parser.add_argument("--prometheus-port", type=int, default=9090, help="Port pour métriques Prometheus")
    
    args = parser.parse_args()
    
    # Créer monitor
    monitor = PerformanceMonitor()
    
    # Serveur HTTP simple pour métriques Prometheus
    from aiohttp import web
    
    async def prometheus_handler(request):
        metrics = monitor.get_prometheus_metrics()
        return web.Response(text=metrics, content_type='text/plain')
    
    async def dashboard_handler(request):
        duration = int(request.query.get('duration', 60))
        data = monitor.get_dashboard_data(duration)
        return web.json_response(data)
    
    app = web.Application()
    app.router.add_get('/metrics', prometheus_handler)
    app.router.add_get('/dashboard', dashboard_handler)
    
    # Démarrer serveur et monitoring
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', args.prometheus_port)
    await site.start()
    
    logger.info(f"🌐 Serveur métriques démarré: http://localhost:{args.prometheus_port}")
    logger.info(f"📊 Dashboard: http://localhost:{args.prometheus_port}/dashboard")
    logger.info(f"📈 Prometheus: http://localhost:{args.prometheus_port}/metrics")
    
    # Lancer monitoring
    try:
        await monitor.run_monitoring_loop(args.interval)
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt monitoring")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    import statistics
    asyncio.run(main())