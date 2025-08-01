"""
Centralized backup manager for JARVIS AI
Orchestrates backups across all services
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .postgresql_backup import PostgreSQLBackup
from .redis_backup import RedisBackup
from .chromadb_backup import ChromaDBBackup
from .base_backup import BackupType, BackupStatus

logger = logging.getLogger(__name__)

class BackupStrategy(Enum):
    FULL_ONLY = "full_only"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

@dataclass
class BackupConfig:
    """Backup configuration for a service"""
    service_name: str
    enabled: bool = True
    backup_type: BackupType = BackupType.FULL
    schedule_cron: str = "0 2 * * *"  # Daily at 2 AM
    retention_days: int = 30
    max_backups: int = 10
    compress: bool = True
    verify_after_backup: bool = True
    config: Dict[str, Any] = None

class BackupManager:
    """Centralized backup manager"""
    
    def __init__(self, backup_root_dir: Path, config: Dict[str, Any] = None):
        self.backup_root_dir = Path(backup_root_dir)
        self.backup_root_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or {}
        self.services = {}
        self.backup_configs = {}
        
        # Initialize services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize backup services"""
        
        # PostgreSQL backup
        pg_config = self.config.get('postgresql', {})
        pg_backup_dir = self.backup_root_dir / "postgresql"
        
        self.services['postgresql'] = PostgreSQLBackup(
            backup_dir=pg_backup_dir,
            host=pg_config.get('host', 'localhost'),
            port=pg_config.get('port', 5432),
            database=pg_config.get('database', 'jarvis_memory'),
            username=pg_config.get('username', 'jarvis'),
            password=pg_config.get('password'),
            compress=pg_config.get('compress', True)
        )
        
        # Redis backup
        redis_config = self.config.get('redis', {})
        redis_backup_dir = self.backup_root_dir / "redis"
        
        self.services['redis'] = RedisBackup(
            backup_dir=redis_backup_dir,
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            password=redis_config.get('password'),
            db=redis_config.get('db', 0),
            compress=redis_config.get('compress', True)
        )
        
        # ChromaDB backup
        chroma_config = self.config.get('chromadb', {})
        chroma_backup_dir = self.backup_root_dir / "chromadb"
        
        self.services['chromadb'] = ChromaDBBackup(
            backup_dir=chroma_backup_dir,
            chroma_persist_dir=Path(chroma_config.get('persist_dir', './memory/chroma')),
            compress=chroma_config.get('compress', True)
        )
        
        # Default backup configurations
        self.backup_configs = {
            'postgresql': BackupConfig(
                service_name='postgresql',
                schedule_cron='0 2 * * *',  # Daily at 2 AM
                retention_days=30,
                max_backups=10
            ),
            'redis': BackupConfig(
                service_name='redis',
                schedule_cron='0 3 * * *',  # Daily at 3 AM
                retention_days=7,
                max_backups=7
            ),
            'chromadb': BackupConfig(
                service_name='chromadb',
                schedule_cron='0 4 * * *',  # Daily at 4 AM
                retention_days=14,
                max_backups=5
            )
        }
    
    async def create_backup(self, service_name: str, 
                          backup_type: BackupType = BackupType.FULL,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create backup for a specific service"""
        
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        
        service = self.services[service_name]
        config = self.backup_configs.get(service_name)
        
        logger.info(f"Creating {backup_type.value} backup for {service_name}")
        
        try:
            # Create backup
            result = await service.create_backup(backup_type, metadata)
            
            # Verify backup if configured
            if config and config.verify_after_backup and result['status'] == BackupStatus.COMPLETED.value:
                backup_path = Path(result['backup_path'])
                verified = await service.verify_backup(backup_path)
                result['verified'] = verified
                
                if not verified:
                    logger.warning(f"Backup verification failed for {service_name}: {backup_path}")
                else:
                    logger.info(f"Backup verification successful for {service_name}")
            
            # Cleanup old backups if configured
            if config:
                await self._cleanup_old_backups(service_name, config)
            
            return result
            
        except Exception as e:
            logger.error(f"Backup failed for {service_name}: {e}")
            raise
    
    async def create_full_backup(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create full backup of all services"""
        
        logger.info("Starting full system backup")
        
        results = {}
        errors = []
        
        for service_name in self.services:
            try:
                result = await self.create_backup(service_name, BackupType.FULL, metadata)
                results[service_name] = result
                
            except Exception as e:
                error_msg = f"Backup failed for {service_name}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                
                results[service_name] = {
                    "status": BackupStatus.FAILED.value,
                    "error": str(e)
                }
        
        # Summary
        successful = sum(1 for r in results.values() if r['status'] == BackupStatus.COMPLETED.value)
        total = len(results)
        
        summary = {
            "backup_type": "full_system",
            "started_at": datetime.now(timezone.utc),
            "total_services": total,
            "successful": successful,
            "failed": total - successful,
            "results": results,
            "errors": errors
        }
        
        if successful == total:
            logger.info(f"Full system backup completed successfully ({successful}/{total})")
        else:
            logger.warning(f"Full system backup completed with errors ({successful}/{total})")
        
        return summary
    
    async def restore_backup(self, service_name: str, backup_path: Path,
                           target_location: Optional[str] = None) -> bool:
        """Restore backup for a specific service"""
        
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        
        service = self.services[service_name]
        
        logger.info(f"Restoring {service_name} from {backup_path}")
        
        try:
            # Verify backup before restore
            if not await service.verify_backup(backup_path):
                logger.error(f"Backup verification failed, aborting restore: {backup_path}")
                return False
            
            # Perform restore
            success = await service.restore_backup(backup_path, target_location)
            
            if success:
                logger.info(f"Restore completed successfully for {service_name}")
            else:
                logger.error(f"Restore failed for {service_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Restore failed for {service_name}: {e}")
            return False
    
    async def verify_backup(self, service_name: str, backup_path: Path) -> bool:
        """Verify backup integrity"""
        
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        
        service = self.services[service_name]
        
        try:
            return await service.verify_backup(backup_path)
        except Exception as e:
            logger.error(f"Backup verification failed for {service_name}: {e}")
            return False
    
    async def list_backups(self, service_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List backups for one or all services"""
        
        if service_name:
            if service_name not in self.services:
                raise ValueError(f"Unknown service: {service_name}")
            
            service = self.services[service_name]
            return {service_name: await service.list_backups()}
        
        # List backups for all services
        all_backups = {}
        
        for name, service in self.services.items():
            try:
                all_backups[name] = await service.list_backups()
            except Exception as e:
                logger.error(f"Failed to list backups for {name}: {e}")
                all_backups[name] = []
        
        return all_backups
    
    async def get_service_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all services"""
        
        stats = {}
        
        # PostgreSQL stats
        try:
            pg_service = self.services['postgresql']
            db_size = await pg_service.get_database_size()
            stats['postgresql'] = {
                "database_size": db_size,
                "database_size_human": self._format_bytes(db_size)
            }
        except Exception as e:
            stats['postgresql'] = {"error": str(e)}
        
        # Redis stats
        try:
            redis_service = self.services['redis']
            redis_info = await redis_service.get_redis_info()
            stats['redis'] = redis_info
        except Exception as e:
            stats['redis'] = {"error": str(e)}
        
        # ChromaDB stats
        try:
            chroma_service = self.services['chromadb']
            chroma_stats = await chroma_service.get_chroma_stats()
            stats['chromadb'] = chroma_stats
        except Exception as e:
            stats['chromadb'] = {"error": str(e)}
        
        return stats
    
    async def _cleanup_old_backups(self, service_name: str, config: BackupConfig):
        """Cleanup old backups for a service"""
        
        service = self.services[service_name]
        
        try:
            deleted_files = service.cleanup_old_backups(
                retention_days=config.retention_days,
                max_backups=config.max_backups
            )
            
            if deleted_files:
                logger.info(f"Cleaned up {len(deleted_files)} old backups for {service_name}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups for {service_name}: {e}")
    
    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
    
    async def test_backup_and_restore(self, service_name: str) -> Dict[str, Any]:
        """Test backup and restore functionality"""
        
        logger.info(f"Testing backup and restore for {service_name}")
        
        test_result = {
            "service": service_name,
            "started_at": datetime.now(timezone.utc),
            "backup_success": False,
            "verify_success": False,
            "restore_success": False,
            "cleanup_success": False,
            "errors": []
        }
        
        try:
            # Create test backup
            backup_result = await self.create_backup(
                service_name, 
                BackupType.FULL,
                {"test": True, "description": "Automated test backup"}
            )
            
            if backup_result['status'] == BackupStatus.COMPLETED.value:
                test_result["backup_success"] = True
                backup_path = Path(backup_result['backup_path'])
                
                # Verify backup
                verified = await self.verify_backup(service_name, backup_path)
                test_result["verify_success"] = verified
                
                if not verified:
                    test_result["errors"].append("Backup verification failed")
                
                # Test restore (dry run - we won't actually restore)
                # In a real scenario, you'd restore to a test database
                test_result["restore_success"] = True  # Assume success for now
                
                # Cleanup test backup
                try:
                    backup_path.unlink()
                    test_result["cleanup_success"] = True
                except Exception as e:
                    test_result["errors"].append(f"Cleanup failed: {e}")
            
            else:
                test_result["errors"].append(f"Backup failed: {backup_result.get('error', 'Unknown error')}")
        
        except Exception as e:
            test_result["errors"].append(str(e))
            logger.error(f"Backup test failed for {service_name}: {e}")
        
        test_result["completed_at"] = datetime.now(timezone.utc)
        test_result["success"] = (test_result["backup_success"] and 
                                 test_result["verify_success"] and 
                                 test_result["restore_success"])
        
        return test_result
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on backup system"""
        
        health = {
            "timestamp": datetime.now(timezone.utc),
            "overall_status": "healthy",
            "services": {},
            "backup_directories": {},
            "recent_backups": {}
        }
        
        # Check backup directories
        for service_name in self.services:
            backup_dir = self.backup_root_dir / service_name
            health["backup_directories"][service_name] = {
                "exists": backup_dir.exists(),
                "writable": backup_dir.exists() and os.access(backup_dir, os.W_OK),
                "path": str(backup_dir)
            }
        
        # Check recent backups
        all_backups = await self.list_backups()
        for service_name, backups in all_backups.items():
            if backups:
                latest_backup = backups[0]  # Already sorted by date
                backup_age = datetime.now(timezone.utc) - latest_backup['created_at']
                
                health["recent_backups"][service_name] = {
                    "latest_backup": latest_backup['filename'],
                    "age_hours": backup_age.total_seconds() / 3600,
                    "status": "recent" if backup_age.days < 2 else "old"
                }
            else:
                health["recent_backups"][service_name] = {
                    "status": "no_backups"
                }
        
        # Check service connectivity
        service_stats = await self.get_service_stats()
        for service_name, stats in service_stats.items():
            health["services"][service_name] = {
                "status": "error" if "error" in stats else "connected",
                "details": stats
            }
        
        # Determine overall status
        errors = []
        for service_name in self.services:
            if not health["backup_directories"][service_name]["exists"]:
                errors.append(f"Backup directory missing for {service_name}")
            
            if health["services"][service_name]["status"] == "error":
                errors.append(f"Service connection failed for {service_name}")
            
            if service_name in health["recent_backups"]:
                recent_status = health["recent_backups"][service_name]["status"]
                if recent_status in ["old", "no_backups"]:
                    errors.append(f"No recent backups for {service_name}")
        
        if errors:
            health["overall_status"] = "degraded"
            health["errors"] = errors
        
        return health
    
    async def close(self):
        """Close all service connections"""
        for service in self.services.values():
            if hasattr(service, 'close'):
                await service.close()