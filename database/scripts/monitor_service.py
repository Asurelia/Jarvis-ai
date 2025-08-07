#!/usr/bin/env python3
"""
JARVIS AI - Database Health Monitor Service
Real-time database health monitoring and metrics collection
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import asyncpg
import redis.asyncio as aioredis
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import psutil

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
DB_CONNECTIONS = Gauge('jarvis_db_connections_active', 'Active database connections')
DB_QUERY_DURATION = Histogram('jarvis_db_query_duration_seconds', 'Database query duration')
DB_QUERY_COUNT = Counter('jarvis_db_queries_total', 'Total database queries', ['status'])
DB_SIZE_BYTES = Gauge('jarvis_db_size_bytes', 'Database size in bytes', ['database'])
REDIS_MEMORY_USAGE = Gauge('jarvis_redis_memory_bytes', 'Redis memory usage in bytes')
HEALTH_CHECKS = Counter('jarvis_health_checks_total', 'Total health checks', ['service', 'status'])

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "memory-db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "jarvis_memory")
POSTGRES_USER = os.getenv("POSTGRES_USER", "jarvis")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "jarvis_secure_2024")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))

# Pydantic models
class HealthStatus(BaseModel):
    service: str
    status: str
    timestamp: datetime
    metrics: Dict[str, Any]
    issues: List[str] = []

class DatabaseMetrics(BaseModel):
    connections_active: int
    connections_max: int
    database_size_mb: float
    query_performance: Dict[str, float]
    slow_queries: List[Dict[str, Any]]
    lock_count: int

class RedisMetrics(BaseModel):
    memory_usage_mb: float
    connected_clients: int
    keys_count: int
    hit_rate: float
    commands_per_second: float

class MonitoringReport(BaseModel):
    timestamp: datetime
    overall_status: str
    database_health: HealthStatus
    redis_health: HealthStatus
    system_health: Dict[str, Any]
    recommendations: List[str]

# FastAPI app
app = FastAPI(
    title="JARVIS Database Monitor",
    description="Real-time database health monitoring and metrics collection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
start_time = datetime.utcnow()
postgres_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[aioredis.Redis] = None
latest_report: Optional[MonitoringReport] = None

@app.on_event("startup")
async def startup_event():
    """Initialize database connections and start monitoring"""
    global postgres_pool, redis_client
    
    try:
        # Initialize PostgreSQL connection pool
        postgres_pool = await asyncpg.create_pool(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            min_size=1,
            max_size=5
        )
        
        # Initialize Redis connection
        redis_client = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )
        
        # Start monitoring task
        asyncio.create_task(monitoring_loop())
        
        logger.info("Database monitor service started")
        
    except Exception as e:
        logger.error("Failed to initialize database monitor", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections"""
    global postgres_pool, redis_client
    
    if postgres_pool:
        await postgres_pool.close()
    if redis_client:
        await redis_client.close()
    
    logger.info("Database monitor service shutting down")

async def monitoring_loop():
    """Main monitoring loop"""
    while True:
        try:
            await perform_health_check()
            await asyncio.sleep(HEALTH_CHECK_INTERVAL)
        except Exception as e:
            logger.error("Monitoring loop error", error=str(e))
            await asyncio.sleep(60)  # Wait longer on error

async def perform_health_check():
    """Perform comprehensive health check"""
    global latest_report
    
    try:
        # Check PostgreSQL health
        db_health = await check_database_health()
        
        # Check Redis health  
        redis_health = await check_redis_health()
        
        # Check system health
        system_health = await check_system_health()
        
        # Generate recommendations
        recommendations = generate_recommendations(db_health, redis_health, system_health)
        
        # Determine overall status
        overall_status = "healthy"
        if db_health.status != "healthy" or redis_health.status != "healthy":
            overall_status = "degraded"
        if len(db_health.issues) > 3 or len(redis_health.issues) > 3:
            overall_status = "critical"
        
        # Create monitoring report
        latest_report = MonitoringReport(
            timestamp=datetime.utcnow(),
            overall_status=overall_status,
            database_health=db_health,
            redis_health=redis_health,
            system_health=system_health,
            recommendations=recommendations
        )
        
        logger.info("Health check completed", status=overall_status)
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))

async def check_database_health() -> HealthStatus:
    """Check PostgreSQL database health"""
    issues = []
    metrics = {}
    
    try:
        async with postgres_pool.acquire() as conn:
            # Check connection count
            result = await conn.fetchrow("""
                SELECT count(*) as active_connections,
                       setting::int as max_connections
                FROM pg_stat_activity, pg_settings 
                WHERE pg_settings.name = 'max_connections'
            """)
            
            active_connections = result['active_connections']
            max_connections = result['max_connections']
            connection_usage = (active_connections / max_connections) * 100
            
            DB_CONNECTIONS.set(active_connections)
            metrics['connections_active'] = active_connections
            metrics['connections_max'] = max_connections
            metrics['connection_usage_percent'] = connection_usage
            
            if connection_usage > 80:
                issues.append(f"High connection usage: {connection_usage:.1f}%")
            
            # Check database size
            size_result = await conn.fetchrow("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                       pg_database_size(current_database()) as size_bytes
            """)
            
            size_bytes = size_result['size_bytes']
            size_mb = size_bytes / (1024 * 1024)
            DB_SIZE_BYTES.labels(database=POSTGRES_DB).set(size_bytes)
            metrics['database_size_mb'] = size_mb
            
            # Check for slow queries
            slow_queries = await conn.fetch("""
                SELECT query, mean_exec_time, calls, total_exec_time
                FROM pg_stat_statements 
                WHERE mean_exec_time > 1000 
                ORDER BY mean_exec_time DESC 
                LIMIT 5
            """)
            
            if slow_queries:
                metrics['slow_query_count'] = len(slow_queries)
                for query in slow_queries:
                    issues.append(f"Slow query detected: {query['mean_exec_time']:.2f}ms avg")
            
            # Check locks
            lock_result = await conn.fetchrow("""
                SELECT count(*) as lock_count
                FROM pg_locks 
                WHERE NOT granted
            """)
            
            lock_count = lock_result['lock_count']
            metrics['active_locks'] = lock_count
            
            if lock_count > 0:
                issues.append(f"Active locks detected: {lock_count}")
            
            # Check table sizes
            table_sizes = await conn.fetch("""
                SELECT schemaname, tablename, 
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
                LIMIT 5
            """)
            
            metrics['largest_tables'] = [
                {"table": f"{row['schemaname']}.{row['tablename']}", "size": row['size']}
                for row in table_sizes
            ]
            
        HEALTH_CHECKS.labels(service='postgresql', status='success').inc()
        
        return HealthStatus(
            service="postgresql",
            status="healthy" if not issues else ("degraded" if len(issues) < 3 else "critical"),
            timestamp=datetime.utcnow(),
            metrics=metrics,
            issues=issues
        )
        
    except Exception as e:
        HEALTH_CHECKS.labels(service='postgresql', status='error').inc()
        logger.error("PostgreSQL health check failed", error=str(e))
        
        return HealthStatus(
            service="postgresql",
            status="critical",
            timestamp=datetime.utcnow(),
            metrics={},
            issues=[f"Connection failed: {str(e)}"]
        )

async def check_redis_health() -> HealthStatus:
    """Check Redis health"""
    issues = []
    metrics = {}
    
    try:
        # Get Redis info
        info = await redis_client.info()
        
        # Memory usage
        memory_used = info.get('used_memory', 0)
        memory_mb = memory_used / (1024 * 1024)
        REDIS_MEMORY_USAGE.set(memory_used)
        metrics['memory_usage_mb'] = memory_mb
        
        # Connected clients
        connected_clients = info.get('connected_clients', 0)
        metrics['connected_clients'] = connected_clients
        
        # Key count
        db_info = await redis_client.info('keyspace')
        total_keys = 0
        for db_key, db_stats in db_info.items():
            if db_key.startswith('db'):
                keys = int(db_stats.split(',')[0].split('=')[1])
                total_keys += keys
        
        metrics['total_keys'] = total_keys
        
        # Hit rate
        keyspace_hits = info.get('keyspace_hits', 0)
        keyspace_misses = info.get('keyspace_misses', 0)
        total_requests = keyspace_hits + keyspace_misses
        hit_rate = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0
        metrics['hit_rate_percent'] = hit_rate
        
        if hit_rate < 80 and total_requests > 100:
            issues.append(f"Low cache hit rate: {hit_rate:.1f}%")
        
        # Commands per second
        commands_processed = info.get('total_commands_processed', 0)
        uptime = info.get('uptime_in_seconds', 1)
        commands_per_second = commands_processed / uptime
        metrics['commands_per_second'] = commands_per_second
        
        # Memory usage warnings
        max_memory = info.get('maxmemory', 0)
        if max_memory > 0:
            memory_usage_percent = (memory_used / max_memory) * 100
            metrics['memory_usage_percent'] = memory_usage_percent
            
            if memory_usage_percent > 80:
                issues.append(f"High memory usage: {memory_usage_percent:.1f}%")
        
        HEALTH_CHECKS.labels(service='redis', status='success').inc()
        
        return HealthStatus(
            service="redis",
            status="healthy" if not issues else ("degraded" if len(issues) < 3 else "critical"),
            timestamp=datetime.utcnow(),
            metrics=metrics,
            issues=issues
        )
        
    except Exception as e:
        HEALTH_CHECKS.labels(service='redis', status='error').inc()
        logger.error("Redis health check failed", error=str(e))
        
        return HealthStatus(
            service="redis",
            status="critical",
            timestamp=datetime.utcnow(),
            metrics={},
            issues=[f"Connection failed: {str(e)}"]
        )

async def check_system_health() -> Dict[str, Any]:
    """Check system resource health"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_percent": (disk.used / disk.total) * 100,
            "disk_free_gb": disk.free / (1024 * 1024 * 1024)
        }
        
    except Exception as e:
        logger.error("System health check failed", error=str(e))
        return {"error": str(e)}

def generate_recommendations(db_health: HealthStatus, redis_health: HealthStatus, system_health: Dict[str, Any]) -> List[str]:
    """Generate optimization recommendations"""
    recommendations = []
    
    # Database recommendations
    if db_health.metrics.get('connection_usage_percent', 0) > 70:
        recommendations.append("Consider increasing PostgreSQL max_connections or optimizing connection pooling")
    
    if db_health.metrics.get('slow_query_count', 0) > 0:
        recommendations.append("Review and optimize slow queries, consider adding indexes")
    
    if db_health.metrics.get('database_size_mb', 0) > 1000:
        recommendations.append("Database size is large, consider archiving old data or implementing partitioning")
    
    # Redis recommendations
    if redis_health.metrics.get('hit_rate_percent', 100) < 80:
        recommendations.append("Redis cache hit rate is low, review caching strategy")
    
    if redis_health.metrics.get('memory_usage_percent', 0) > 70:
        recommendations.append("Redis memory usage is high, consider increasing memory or implementing eviction policies")
    
    # System recommendations
    if system_health.get('cpu_percent', 0) > 80:
        recommendations.append("High CPU usage detected, consider scaling resources")
    
    if system_health.get('memory_percent', 0) > 80:
        recommendations.append("High memory usage detected, consider adding more RAM")
    
    if system_health.get('disk_percent', 0) > 80:
        recommendations.append("Disk space is running low, consider cleanup or expansion")
    
    return recommendations

@app.get("/health")
async def health_endpoint():
    """Health check endpoint"""
    if latest_report:
        return {
            "status": latest_report.overall_status,
            "timestamp": latest_report.timestamp,
            "uptime_seconds": (datetime.utcnow() - start_time).total_seconds()
        }
    else:
        return {
            "status": "initializing",
            "timestamp": datetime.utcnow(),
            "uptime_seconds": (datetime.utcnow() - start_time).total_seconds()
        }

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/report")
async def get_monitoring_report():
    """Get latest monitoring report"""
    if latest_report:
        return latest_report
    else:
        raise HTTPException(status_code=503, detail="Monitoring report not yet available")

@app.get("/database/status")
async def get_database_status():
    """Get detailed database status"""
    if latest_report:
        return latest_report.database_health
    else:
        raise HTTPException(status_code=503, detail="Database status not yet available")

@app.get("/redis/status")
async def get_redis_status():
    """Get detailed Redis status"""
    if latest_report:
        return latest_report.redis_health
    else:
        raise HTTPException(status_code=503, detail="Redis status not yet available")

def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    
    uvicorn.run(
        "database.scripts.monitor_service:app",
        host="0.0.0.0",
        port=8090,
        log_level="info",
        access_log=True,
        reload=False
    )

if __name__ == "__main__":
    main()