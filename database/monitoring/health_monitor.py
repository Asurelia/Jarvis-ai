"""
Database health monitoring for JARVIS AI
Monitors database connectivity, performance, and integrity
"""

import asyncio
import asyncpg
import aioredis
import psutil
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.details is None:
            self.details = {}

class HealthMonitor:
    """Comprehensive database health monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.last_check = None
        self.check_history = []
        self.max_history = 100
        
        # Connection configurations
        self.postgres_config = config.get('postgresql', {})
        self.redis_config = config.get('redis', {})
        self.chromadb_config = config.get('chromadb', {})
    
    async def run_full_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check on all services"""
        
        logger.info("Starting full database health check")
        
        health_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": HealthStatus.HEALTHY.value,
            "services": {},
            "system": {},
            "summary": {
                "total_checks": 0,
                "healthy": 0,
                "warnings": 0,
                "critical": 0
            }
        }
        
        # Run all health checks
        checks = [
            ("postgresql", self._check_postgresql_health),
            ("redis", self._check_redis_health),
            ("chromadb", self._check_chromadb_health),
            ("system", self._check_system_health),
            ("backup_system", self._check_backup_system_health),
            ("disk_space", self._check_disk_space)
        ]
        
        for service_name, check_func in checks:
            try:
                check_result = await check_func()
                
                if service_name == "system":
                    health_report["system"] = check_result
                else:
                    health_report["services"][service_name] = check_result
                
                # Update summary
                status = check_result.get("status", HealthStatus.UNKNOWN.value)
                if status == HealthStatus.HEALTHY.value:
                    health_report["summary"]["healthy"] += 1
                elif status == HealthStatus.WARNING.value:
                    health_report["summary"]["warnings"] += 1
                elif status == HealthStatus.CRITICAL.value:
                    health_report["summary"]["critical"] += 1
                
                health_report["summary"]["total_checks"] += 1
                
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                
                error_result = {
                    "status": HealthStatus.CRITICAL.value,
                    "message": f"Health check failed: {e}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                if service_name == "system":
                    health_report["system"] = error_result
                else:
                    health_report["services"][service_name] = error_result
                
                health_report["summary"]["critical"] += 1
                health_report["summary"]["total_checks"] += 1
        
        # Determine overall status
        if health_report["summary"]["critical"] > 0:
            health_report["overall_status"] = HealthStatus.CRITICAL.value
        elif health_report["summary"]["warnings"] > 0:
            health_report["overall_status"] = HealthStatus.WARNING.value
        
        # Store in history
        self.last_check = health_report
        self.check_history.append(health_report)
        
        # Maintain history size
        if len(self.check_history) > self.max_history:
            self.check_history = self.check_history[-self.max_history:]
        
        logger.info(f"Health check completed: {health_report['overall_status']} "
                   f"({health_report['summary']['healthy']}/{health_report['summary']['total_checks']} healthy)")
        
        return health_report
    
    async def _check_postgresql_health(self) -> Dict[str, Any]:
        """Check PostgreSQL database health"""
        
        result = {
            "status": HealthStatus.HEALTHY.value,
            "message": "PostgreSQL is healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }
        
        try:
            # Build connection URL
            pg_config = self.postgres_config
            database_url = (f"postgresql://{pg_config.get('username', 'jarvis')}:"
                          f"{pg_config.get('password', 'password')}@"
                          f"{pg_config.get('host', 'localhost')}:"
                          f"{pg_config.get('port', 5432)}/"
                          f"{pg_config.get('database', 'jarvis_memory')}")
            
            # Test connection
            conn = await asyncpg.connect(database_url)
            
            try:
                # Basic connectivity test
                await conn.fetchval("SELECT 1")
                
                # Get database metrics
                metrics = await self._get_postgresql_metrics(conn)
                result["metrics"] = metrics
                
                # Check connection count
                if metrics.get("active_connections", 0) > 80:  # 80% of max connections
                    result["status"] = HealthStatus.WARNING.value
                    result["message"] = "High connection count"
                
                # Check database size
                db_size_mb = metrics.get("database_size_mb", 0)
                if db_size_mb > 10000:  # 10GB
                    result["status"] = HealthStatus.WARNING.value
                    result["message"] = "Large database size"
                
                # Check for long-running queries
                if metrics.get("long_running_queries", 0) > 5:
                    result["status"] = HealthStatus.WARNING.value
                    result["message"] = "Long-running queries detected"
                
            finally:
                await conn.close()
                
        except Exception as e:
            result.update({
                "status": HealthStatus.CRITICAL.value,
                "message": f"PostgreSQL connection failed: {e}"
            })
        
        return result
    
    async def _get_postgresql_metrics(self, conn: asyncpg.Connection) -> Dict[str, Any]:
        """Get PostgreSQL performance metrics"""
        
        metrics = {}
        
        try:
            # Database size
            size_query = "SELECT pg_database_size(current_database())"
            db_size = await conn.fetchval(size_query)
            metrics["database_size_bytes"] = db_size
            metrics["database_size_mb"] = db_size / (1024 * 1024) if db_size else 0
            
            # Connection count
            conn_query = """
            SELECT count(*) as active_connections,
                   max_conn.setting::int as max_connections
            FROM pg_stat_activity, 
                 (SELECT setting FROM pg_settings WHERE name = 'max_connections') max_conn
            WHERE state = 'active'
            GROUP BY max_conn.setting
            """
            conn_result = await conn.fetchrow(conn_query)
            if conn_result:
                metrics["active_connections"] = conn_result["active_connections"]
                metrics["max_connections"] = conn_result["max_connections"]
                metrics["connection_usage_percent"] = (
                    conn_result["active_connections"] / conn_result["max_connections"] * 100
                )
            
            # Long-running queries
            long_query = """
            SELECT count(*) as long_running_queries
            FROM pg_stat_activity
            WHERE state = 'active' 
            AND now() - query_start > interval '5 minutes'
            AND query NOT LIKE '%pg_stat_activity%'
            """
            metrics["long_running_queries"] = await conn.fetchval(long_query)
            
            # Cache hit ratio
            cache_query = """
            SELECT 
                sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as cache_hit_ratio
            FROM pg_statio_user_tables
            WHERE heap_blks_hit + heap_blks_read > 0
            """
            cache_ratio = await conn.fetchval(cache_query)
            metrics["cache_hit_ratio"] = float(cache_ratio) if cache_ratio else 0
            
            # Table statistics
            table_stats_query = """
            SELECT 
                schemaname,
                tablename,
                n_tup_ins + n_tup_upd + n_tup_del as total_operations,
                n_dead_tup,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            ORDER BY total_operations DESC
            LIMIT 5
            """
            table_stats = await conn.fetch(table_stats_query)
            metrics["top_active_tables"] = [dict(row) for row in table_stats]
            
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL metrics: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        
        result = {
            "status": HealthStatus.HEALTHY.value,
            "message": "Redis is healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }
        
        try:
            # Connect to Redis
            redis_config = self.redis_config
            connection_params = {
                'host': redis_config.get('host', 'localhost'),
                'port': redis_config.get('port', 6379),
                'db': redis_config.get('db', 0)
            }
            if redis_config.get('password'):
                connection_params['password'] = redis_config['password']
            
            redis = await aioredis.create_redis_pool(**connection_params)
            
            try:
                # Test connection
                await redis.ping()
                
                # Get Redis info
                info = await redis.info()
                
                # Extract key metrics
                metrics = {
                    "redis_version": info.get("redis_version"),
                    "used_memory": info.get("used_memory"),
                    "used_memory_human": info.get("used_memory_human"),
                    "used_memory_peak": info.get("used_memory_peak"),
                    "used_memory_peak_human": info.get("used_memory_peak_human"),
                    "connected_clients": info.get("connected_clients"),
                    "blocked_clients": info.get("blocked_clients"),
                    "total_commands_processed": info.get("total_commands_processed"),
                    "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                    "expired_keys": info.get("expired_keys"),
                    "evicted_keys": info.get("evicted_keys")
                }
                
                # Calculate hit ratio
                if metrics["keyspace_hits"] and metrics["keyspace_misses"]:
                    total_ops = metrics["keyspace_hits"] + metrics["keyspace_misses"]
                    metrics["hit_ratio"] = (metrics["keyspace_hits"] / total_ops) * 100
                
                result["metrics"] = metrics
                
                # Health checks
                memory_usage = info.get("used_memory", 0)
                max_memory = info.get("maxmemory", 0)
                
                if max_memory > 0 and memory_usage / max_memory > 0.9:
                    result["status"] = HealthStatus.WARNING.value
                    result["message"] = "High memory usage"
                
                if metrics.get("blocked_clients", 0) > 0:
                    result["status"] = HealthStatus.WARNING.value
                    result["message"] = "Blocked clients detected"
                
                if metrics.get("hit_ratio", 100) < 80:
                    result["status"] = HealthStatus.WARNING.value
                    result["message"] = "Low cache hit ratio"
                
            finally:
                await redis.wait_closed()
                
        except Exception as e:
            result.update({
                "status": HealthStatus.CRITICAL.value,
                "message": f"Redis connection failed: {e}"
            })
        
        return result
    
    async def _check_chromadb_health(self) -> Dict[str, Any]:
        """Check ChromaDB health"""
        
        result = {
            "status": HealthStatus.HEALTHY.value,
            "message": "ChromaDB is healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }
        
        try:
            # Check ChromaDB persist directory
            chroma_dir = Path(self.chromadb_config.get('persist_dir', './memory/chroma'))
            
            if not chroma_dir.exists():
                result.update({
                    "status": HealthStatus.WARNING.value,
                    "message": "ChromaDB persist directory not found"
                })
                return result
            
            # Check directory access
            if not chroma_dir.is_dir():
                result.update({
                    "status": HealthStatus.CRITICAL.value,
                    "message": "ChromaDB persist path is not a directory"
                })
                return result
            
            # Get directory statistics
            total_size = 0
            file_count = 0
            sqlite_files = []
            
            for file_path in chroma_dir.rglob("*"):
                if file_path.is_file():
                    file_count += 1
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    if file_path.suffix in ['.sqlite', '.sqlite3', '.db']:
                        sqlite_files.append({
                            "name": file_path.name,
                            "size": file_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime, timezone.utc
                            ).isoformat()
                        })
            
            metrics = {
                "persist_directory": str(chroma_dir),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "file_count": file_count,
                "sqlite_files": sqlite_files
            }
            
            result["metrics"] = metrics
            
            # Health checks
            if total_size > 5 * 1024 * 1024 * 1024:  # 5GB
                result["status"] = HealthStatus.WARNING.value
                result["message"] = "Large ChromaDB size"
            
            if file_count > 10000:
                result["status"] = HealthStatus.WARNING.value
                result["message"] = "Many ChromaDB files"
            
        except Exception as e:
            result.update({
                "status": HealthStatus.CRITICAL.value,
                "message": f"ChromaDB check failed: {e}"
            })
        
        return result
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Check system health (CPU, memory, disk)"""
        
        result = {
            "status": HealthStatus.HEALTHY.value,
            "message": "System is healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage for current directory
            disk = psutil.disk_usage('.')
            
            metrics = {
                "cpu_usage_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_used": memory.used,
                "memory_usage_percent": memory.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_free": disk.free,
                "disk_usage_percent": (disk.used / disk.total) * 100,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
            result["metrics"] = metrics
            
            # Health checks
            if cpu_percent > 90:
                result["status"] = HealthStatus.CRITICAL.value
                result["message"] = "Very high CPU usage"
            elif cpu_percent > 80:
                result["status"] = HealthStatus.WARNING.value
                result["message"] = "High CPU usage"
            
            if memory.percent > 95:
                result["status"] = HealthStatus.CRITICAL.value
                result["message"] = "Very high memory usage"
            elif memory.percent > 85:
                result["status"] = HealthStatus.WARNING.value
                result["message"] = "High memory usage"
            
            disk_usage_percent = (disk.used / disk.total) * 100
            if disk_usage_percent > 95:
                result["status"] = HealthStatus.CRITICAL.value
                result["message"] = "Very low disk space"
            elif disk_usage_percent > 85:
                result["status"] = HealthStatus.WARNING.value
                result["message"] = "Low disk space"
            
        except Exception as e:
            result.update({
                "status": HealthStatus.CRITICAL.value,
                "message": f"System check failed: {e}"
            })
        
        return result
    
    async def _check_backup_system_health(self) -> Dict[str, Any]:
        """Check backup system health"""
        
        result = {
            "status": HealthStatus.HEALTHY.value,
            "message": "Backup system is healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }
        
        try:
            backup_dir = Path(self.config.get('backup_dir', './backups'))
            
            if not backup_dir.exists():
                result.update({
                    "status": HealthStatus.WARNING.value,
                    "message": "Backup directory not found"
                })
                return result
            
            # Check recent backups
            recent_backups = {}
            cutoff_time = datetime.now() - timedelta(days=2)
            
            for service_dir in backup_dir.iterdir():
                if service_dir.is_dir():
                    service_name = service_dir.name
                    backup_files = list(service_dir.glob("*.backup*"))
                    
                    recent_backup_files = [
                        f for f in backup_files
                        if datetime.fromtimestamp(f.stat().st_mtime) > cutoff_time
                    ]
                    
                    recent_backups[service_name] = {
                        "total_backups": len(backup_files),
                        "recent_backups": len(recent_backup_files),
                        "latest_backup": None,
                        "total_size": sum(f.stat().st_size for f in backup_files)
                    }
                    
                    if backup_files:
                        latest_file = max(backup_files, key=lambda f: f.stat().st_mtime)
                        recent_backups[service_name]["latest_backup"] = {
                            "filename": latest_file.name,
                            "size": latest_file.stat().st_size,
                            "created": datetime.fromtimestamp(
                                latest_file.stat().st_mtime, timezone.utc
                            ).isoformat()
                        }
            
            result["metrics"] = {
                "backup_directory": str(backup_dir),
                "services": recent_backups
            }
            
            # Health checks
            services_without_recent_backups = [
                name for name, info in recent_backups.items()
                if info["recent_backups"] == 0
            ]
            
            if services_without_recent_backups:
                result["status"] = HealthStatus.WARNING.value
                result["message"] = f"No recent backups for: {', '.join(services_without_recent_backups)}"
            
        except Exception as e:
            result.update({
                "status": HealthStatus.CRITICAL.value,
                "message": f"Backup system check failed: {e}"
            })
        
        return result
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space for important directories"""
        
        result = {
            "status": HealthStatus.HEALTHY.value,
            "message": "Disk space is healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }
        
        try:
            important_dirs = [
                ("backup", self.config.get('backup_dir', './backups')),
                ("logs", './logs'),
                ("data", './data'),
                ("memory", './memory')
            ]
            
            disk_info = {}
            
            for dir_name, dir_path in important_dirs:
                dir_path = Path(dir_path)
                
                if dir_path.exists():
                    # Get disk usage for the directory's filesystem
                    disk = psutil.disk_usage(str(dir_path))
                    
                    # Calculate directory size
                    dir_size = sum(
                        f.stat().st_size for f in dir_path.rglob("*") if f.is_file()
                    )
                    
                    disk_info[dir_name] = {
                        "path": str(dir_path),
                        "exists": True,
                        "directory_size": dir_size,
                        "filesystem_total": disk.total,
                        "filesystem_used": disk.used,
                        "filesystem_free": disk.free,
                        "filesystem_usage_percent": (disk.used / disk.total) * 100
                    }
                else:
                    disk_info[dir_name] = {
                        "path": str(dir_path),
                        "exists": False
                    }
            
            result["metrics"] = disk_info
            
            # Health checks
            critical_dirs = []
            warning_dirs = []
            
            for dir_name, info in disk_info.items():
                if info.get("exists") and "filesystem_usage_percent" in info:
                    usage_percent = info["filesystem_usage_percent"]
                    
                    if usage_percent > 95:
                        critical_dirs.append(dir_name)
                    elif usage_percent > 85:
                        warning_dirs.append(dir_name)
            
            if critical_dirs:
                result["status"] = HealthStatus.CRITICAL.value
                result["message"] = f"Critical disk space for: {', '.join(critical_dirs)}"
            elif warning_dirs:
                result["status"] = HealthStatus.WARNING.value
                result["message"] = f"Low disk space for: {', '.join(warning_dirs)}"
            
        except Exception as e:
            result.update({
                "status": HealthStatus.CRITICAL.value,
                "message": f"Disk space check failed: {e}"
            })
        
        return result
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history for the specified number of hours"""
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        filtered_history = []
        for check in self.check_history:
            check_time = datetime.fromisoformat(check["timestamp"].replace('Z', '+00:00'))
            if check_time >= cutoff_time:
                filtered_history.append(check)
        
        return filtered_history
    
    def get_health_trends(self) -> Dict[str, Any]:
        """Analyze health trends from history"""
        
        if not self.check_history:
            return {"error": "No health check history available"}
        
        trends = {
            "total_checks": len(self.check_history),
            "time_range": {
                "start": self.check_history[0]["timestamp"],
                "end": self.check_history[-1]["timestamp"]
            },
            "status_distribution": {
                "healthy": 0,
                "warning": 0,
                "critical": 0
            },
            "service_trends": {},
            "most_common_issues": []
        }
        
        # Analyze status distribution
        for check in self.check_history:
            status = check["overall_status"]
            if status in trends["status_distribution"]:
                trends["status_distribution"][status] += 1
        
        # Analyze service trends
        service_issues = {}
        
        for check in self.check_history:
            for service_name, service_data in check.get("services", {}).items():
                if service_name not in trends["service_trends"]:
                    trends["service_trends"][service_name] = {
                        "healthy": 0,
                        "warning": 0,
                        "critical": 0
                    }
                
                status = service_data.get("status", "unknown")
                if status in trends["service_trends"][service_name]:
                    trends["service_trends"][service_name][status] += 1
                
                # Track issues
                if status in ["warning", "critical"]:
                    message = service_data.get("message", "Unknown issue")
                    issue_key = f"{service_name}: {message}"
                    service_issues[issue_key] = service_issues.get(issue_key, 0) + 1
        
        # Sort most common issues
        trends["most_common_issues"] = sorted(
            service_issues.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return trends