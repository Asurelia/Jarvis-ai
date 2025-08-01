"""
PostgreSQL backup implementation for JARVIS AI
"""

import asyncio
import subprocess
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from .base_backup import BaseBackup, BackupType, BackupStatus

class PostgreSQLBackup(BaseBackup):
    """PostgreSQL backup implementation using pg_dump and pg_restore"""
    
    def __init__(self, backup_dir: Path, host: str = "localhost", 
                 port: int = 5432, database: str = "jarvis_memory",
                 username: str = "jarvis", password: str = None,
                 compress: bool = True):
        super().__init__("postgresql", backup_dir, compress)
        
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        
        # Environment for pg_dump/pg_restore
        self.env = os.environ.copy()
        if password:
            self.env['PGPASSWORD'] = password
    
    async def create_backup(self, backup_type: BackupType = BackupType.FULL,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create PostgreSQL backup using pg_dump"""
        
        backup_filename = self.generate_backup_filename(backup_type)
        backup_path = self.backup_dir / backup_filename
        temp_backup_path = backup_path.with_suffix('.tmp')
        
        result = {
            "service": self.service_name,
            "backup_type": backup_type.value,
            "status": BackupStatus.RUNNING.value,
            "started_at": datetime.now(timezone.utc),
            "backup_path": str(backup_path),
            "metadata": metadata or {}
        }
        
        try:
            self.logger.info(f"Starting PostgreSQL backup: {backup_filename}")
            
            # Build pg_dump command
            cmd = [
                "pg_dump",
                f"--host={self.host}",
                f"--port={self.port}",
                f"--username={self.username}",
                "--verbose",
                "--format=custom",  # Use custom format for compression and parallel restore
                "--no-owner",
                "--no-acl",
                f"--file={temp_backup_path}",
            ]
            
            # Add backup type specific options
            if backup_type == BackupType.FULL:
                cmd.append("--create")  # Include CREATE DATABASE statement
            elif backup_type == BackupType.INCREMENTAL:
                # For incremental, we'll use a different approach with WAL files
                # For now, treat as full backup (proper incremental needs WAL archiving)
                cmd.append("--create")
            
            cmd.append(self.database)
            
            # Execute pg_dump
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=self.env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                raise Exception(f"pg_dump failed: {error_msg}")
            
            # Compress if requested
            if self.compress:
                self.logger.info("Compressing backup file...")
                compressed_path = backup_path
                self.compress_file(temp_backup_path, compressed_path)
                temp_backup_path.unlink()  # Remove uncompressed file
                final_backup_path = compressed_path
            else:
                final_backup_path = backup_path
                temp_backup_path.rename(final_backup_path)
            
            # Calculate file stats
            file_size = self.get_file_size(final_backup_path)
            checksum = self.calculate_checksum(final_backup_path)
            
            result.update({
                "status": BackupStatus.COMPLETED.value,
                "completed_at": datetime.now(timezone.utc),
                "file_size": file_size,
                "checksum": checksum,
                "backup_path": str(final_backup_path)
            })
            
            self.logger.info(f"PostgreSQL backup completed: {final_backup_path.name} ({file_size} bytes)")
            
        except Exception as e:
            self.logger.error(f"PostgreSQL backup failed: {e}")
            
            # Cleanup temporary file
            if temp_backup_path.exists():
                temp_backup_path.unlink()
            
            result.update({
                "status": BackupStatus.FAILED.value,
                "completed_at": datetime.now(timezone.utc),
                "error": str(e)
            })
            
            raise
        
        return result
    
    async def restore_backup(self, backup_path: Path, 
                           target_location: Optional[str] = None) -> bool:
        """Restore PostgreSQL backup using pg_restore"""
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        target_db = target_location or self.database
        
        self.logger.info(f"Starting PostgreSQL restore from {backup_path.name} to {target_db}")
        
        try:
            # Decompress if needed
            restore_file = backup_path
            temp_file = None
            
            if backup_path.suffix == '.gz':
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.backup')
                self.decompress_file(backup_path, Path(temp_file.name))
                restore_file = Path(temp_file.name)
                temp_file.close()
            
            # Build pg_restore command
            cmd = [
                "pg_restore",
                f"--host={self.host}",
                f"--port={self.port}",
                f"--username={self.username}",
                "--verbose",
                "--clean",  # Clean (drop) database objects before recreating
                "--if-exists",  # Use IF EXISTS when dropping objects
                f"--dbname={target_db}",
                str(restore_file)
            ]
            
            # Execute pg_restore
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=self.env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Cleanup temporary file
            if temp_file:
                Path(temp_file.name).unlink()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                self.logger.error(f"pg_restore failed: {error_msg}")
                return False
            
            self.logger.info(f"PostgreSQL restore completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"PostgreSQL restore failed: {e}")
            return False
    
    async def verify_backup(self, backup_path: Path) -> bool:
        """Verify PostgreSQL backup integrity"""
        
        if not backup_path.exists():
            return False
        
        try:
            # For custom format backups, use pg_restore --list to verify
            restore_file = backup_path
            temp_file = None
            
            if backup_path.suffix == '.gz':
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.backup')
                self.decompress_file(backup_path, Path(temp_file.name))
                restore_file = Path(temp_file.name)
                temp_file.close()
            
            cmd = [
                "pg_restore",
                "--list",
                str(restore_file)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Cleanup temporary file
            if temp_file:
                Path(temp_file.name).unlink()
            
            if process.returncode == 0 and stdout:
                self.logger.info(f"Backup verification successful: {backup_path.name}")
                return True
            else:
                self.logger.error(f"Backup verification failed: {backup_path.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Backup verification error: {e}")
            return False
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all PostgreSQL backups"""
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
    
    async def get_database_size(self) -> int:
        """Get current database size in bytes"""
        try:
            cmd = [
                "psql",
                f"--host={self.host}",
                f"--port={self.port}",
                f"--username={self.username}",
                f"--dbname={self.database}",
                "--tuples-only",
                "--no-align",
                "--command=SELECT pg_database_size(current_database());"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=self.env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return int(stdout.decode().strip())
            
        except Exception as e:
            self.logger.error(f"Failed to get database size: {e}")
        
        return 0