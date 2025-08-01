"""
Redis backup implementation for JARVIS AI
"""

import asyncio
import aioredis
import tempfile
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from .base_backup import BaseBackup, BackupType, BackupStatus

class RedisBackup(BaseBackup):
    """Redis backup implementation using BGSAVE and AOF"""
    
    def __init__(self, backup_dir: Path, host: str = "localhost", 
                 port: int = 6379, password: Optional[str] = None,
                 db: int = 0, compress: bool = True):
        super().__init__("redis", backup_dir, compress)
        
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.redis_client = None
    
    async def _get_redis_client(self):
        """Get Redis client connection"""
        if not self.redis_client:
            connection_params = {
                'host': self.host,
                'port': self.port,
                'db': self.db
            }
            if self.password:
                connection_params['password'] = self.password
            
            self.redis_client = await aioredis.create_redis_pool(**connection_params)
        
        return self.redis_client
    
    async def create_backup(self, backup_type: BackupType = BackupType.FULL,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create Redis backup using BGSAVE or AOF"""
        
        backup_filename = self.generate_backup_filename(backup_type)
        backup_path = self.backup_dir / backup_filename
        
        result = {
            "service": self.service_name,
            "backup_type": backup_type.value,
            "status": BackupStatus.RUNNING.value,
            "started_at": datetime.now(timezone.utc),
            "backup_path": str(backup_path),
            "metadata": metadata or {}
        }
        
        try:
            redis = await self._get_redis_client()
            
            self.logger.info(f"Starting Redis backup: {backup_filename}")
            
            if backup_type == BackupType.FULL:
                # Use BGSAVE for full backup
                await self._create_rdb_backup(redis, backup_path)
            else:
                # Use AOF for incremental backup
                await self._create_aof_backup(redis, backup_path)
            
            # Calculate file stats
            file_size = self.get_file_size(backup_path)
            checksum = self.calculate_checksum(backup_path)
            
            result.update({
                "status": BackupStatus.COMPLETED.value,
                "completed_at": datetime.now(timezone.utc),
                "file_size": file_size,
                "checksum": checksum
            })
            
            self.logger.info(f"Redis backup completed: {backup_path.name} ({file_size} bytes)")
            
        except Exception as e:
            self.logger.error(f"Redis backup failed: {e}")
            
            result.update({
                "status": BackupStatus.FAILED.value,
                "completed_at": datetime.now(timezone.utc),
                "error": str(e)
            })
            
            raise
        
        return result
    
    async def _create_rdb_backup(self, redis, backup_path: Path):
        """Create RDB backup using BGSAVE"""
        
        # Get Redis data directory
        config = await redis.config_get('dir')
        redis_dir = Path(config.get('dir', '/var/lib/redis'))
        
        # Get RDB filename
        dbfilename_config = await redis.config_get('dbfilename')
        rdb_filename = dbfilename_config.get('dbfilename', 'dump.rdb')
        rdb_path = redis_dir / rdb_filename
        
        # Trigger background save
        await redis.bgsave()
        
        # Wait for BGSAVE to complete
        while True:
            last_save = await redis.info('persistence')
            if 'rdb_bgsave_in_progress' in last_save and last_save['rdb_bgsave_in_progress'] == 0:
                break
            await asyncio.sleep(0.5)
        
        # Copy RDB file to backup location
        if rdb_path.exists():
            if self.compress:
                temp_path = backup_path.with_suffix('.tmp')
                shutil.copy2(rdb_path, temp_path)
                self.compress_file(temp_path, backup_path)
                temp_path.unlink()
            else:
                shutil.copy2(rdb_path, backup_path)
        else:
            raise FileNotFoundError(f"RDB file not found: {rdb_path}")
    
    async def _create_aof_backup(self, redis, backup_path: Path):
        """Create AOF backup"""
        
        # Get Redis data directory
        config = await redis.config_get('dir')
        redis_dir = Path(config.get('dir', '/var/lib/redis'))
        
        # Check if AOF is enabled
        aof_config = await redis.config_get('appendonly')
        if aof_config.get('appendonly', 'no') == 'no':
            # Temporarily enable AOF
            await redis.config_set('appendonly', 'yes')
        
        # Get AOF filename
        aof_config = await redis.config_get('appendfilename')
        aof_filename = aof_config.get('appendfilename', 'appendonly.aof')
        aof_path = redis_dir / aof_filename
        
        # Force AOF rewrite to ensure all data is in AOF
        await redis.bgrewriteaof()
        
        # Wait for AOF rewrite to complete
        while True:
            info = await redis.info('persistence')
            if 'aof_rewrite_in_progress' in info and info['aof_rewrite_in_progress'] == 0:
                break
            await asyncio.sleep(0.5)
        
        # Copy AOF file to backup location
        if aof_path.exists():
            if self.compress:
                temp_path = backup_path.with_suffix('.tmp')
                shutil.copy2(aof_path, temp_path)
                self.compress_file(temp_path, backup_path)
                temp_path.unlink()
            else:
                shutil.copy2(aof_path, backup_path)
        else:
            raise FileNotFoundError(f"AOF file not found: {aof_path}")
    
    async def restore_backup(self, backup_path: Path, 
                           target_location: Optional[str] = None) -> bool:
        """Restore Redis backup"""
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        self.logger.info(f"Starting Redis restore from {backup_path.name}")
        
        try:
            redis = await self._get_redis_client()
            
            # Get Redis data directory
            config = await redis.config_get('dir')
            redis_dir = Path(config.get('dir', '/var/lib/redis'))
            
            # Determine if backup is RDB or AOF based on content/filename
            is_aof = backup_path.name.endswith('aof') or 'aof' in backup_path.name.lower()
            
            if is_aof:
                await self._restore_aof_backup(redis, backup_path, redis_dir)
            else:
                await self._restore_rdb_backup(redis, backup_path, redis_dir)
            
            self.logger.info("Redis restore completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Redis restore failed: {e}")
            return False
    
    async def _restore_rdb_backup(self, redis, backup_path: Path, redis_dir: Path):
        """Restore from RDB backup"""
        
        # Get RDB filename
        dbfilename_config = await redis.config_get('dbfilename')
        rdb_filename = dbfilename_config.get('dbfilename', 'dump.rdb')
        target_rdb_path = redis_dir / rdb_filename
        
        # Stop Redis writes temporarily
        await redis.config_set('save', '')  # Disable automatic saves
        
        # Clear current data
        await redis.flushall()
        
        # Decompress and copy backup file
        if backup_path.suffix == '.gz':
            self.decompress_file(backup_path, target_rdb_path)
        else:
            shutil.copy2(backup_path, target_rdb_path)
        
        # Restart Redis or reload data
        await redis.debug_restart()
    
    async def _restore_aof_backup(self, redis, backup_path: Path, redis_dir: Path):
        """Restore from AOF backup"""
        
        # Get AOF filename
        aof_config = await redis.config_get('appendfilename')
        aof_filename = aof_config.get('appendfilename', 'appendonly.aof')
        target_aof_path = redis_dir / aof_filename
        
        # Enable AOF if not already enabled
        await redis.config_set('appendonly', 'yes')
        
        # Clear current data
        await redis.flushall()
        
        # Decompress and copy backup file
        if backup_path.suffix == '.gz':
            self.decompress_file(backup_path, target_aof_path)
        else:
            shutil.copy2(backup_path, target_aof_path)
        
        # Restart Redis to load AOF
        await redis.debug_restart()
    
    async def verify_backup(self, backup_path: Path) -> bool:
        """Verify Redis backup integrity"""
        
        if not backup_path.exists():
            return False
        
        try:
            # For RDB files, we can use redis-check-rdb
            # For AOF files, we can use redis-check-aof
            
            temp_file = None
            check_file = backup_path
            
            if backup_path.suffix == '.gz':
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.rdb')
                self.decompress_file(backup_path, Path(temp_file.name))
                check_file = Path(temp_file.name)
                temp_file.close()
            
            # Determine file type and use appropriate checker
            is_aof = 'aof' in backup_path.name.lower()
            
            if is_aof:
                cmd = ['redis-check-aof', str(check_file)]
            else:
                cmd = ['redis-check-rdb', str(check_file)]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Cleanup temporary file
            if temp_file:
                Path(temp_file.name).unlink()
            
            if process.returncode == 0:
                self.logger.info(f"Backup verification successful: {backup_path.name}")
                return True
            else:
                self.logger.error(f"Backup verification failed: {backup_path.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Backup verification error: {e}")
            return False
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all Redis backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob(f"{self.service_name}_*.backup*"):
            metadata = self.get_backup_metadata(backup_file)
            
            # Parse backup type from filename
            filename_parts = backup_file.stem.split('_')
            backup_type = filename_parts[1] if len(filename_parts) > 1 else "unknown"
            
            metadata.update({
                "service": self.service_name,
                "backup_type": backup_type,
                "path": str(backup_file)
            })
            
            backups.append(metadata)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
    
    async def get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        try:
            redis = await self._get_redis_client()
            info = await redis.info()
            
            return {
                "redis_version": info.get('redis_version'),
                "used_memory": info.get('used_memory'),
                "used_memory_human": info.get('used_memory_human'),
                "connected_clients": info.get('connected_clients'),
                "total_commands_processed": info.get('total_commands_processed'),
                "keyspace": await redis.info('keyspace')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Redis info: {e}")
            return {}
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.wait_closed()
            self.redis_client = None