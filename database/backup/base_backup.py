"""
Base backup class for JARVIS AI database backup system
"""

import os
import hashlib
import gzip
import shutil
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BaseBackup(ABC):
    """Base class for all backup implementations"""
    
    def __init__(self, service_name: str, backup_dir: Path, compress: bool = True):
        self.service_name = service_name
        self.backup_dir = Path(backup_dir)
        self.compress = compress
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
    
    @abstractmethod
    async def create_backup(self, backup_type: BackupType = BackupType.FULL, 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a backup of the service"""
        pass
    
    @abstractmethod
    async def restore_backup(self, backup_path: Path, 
                           target_location: Optional[str] = None) -> bool:
        """Restore from a backup file"""
        pass
    
    @abstractmethod
    async def verify_backup(self, backup_path: Path) -> bool:
        """Verify backup integrity"""
        pass
    
    @abstractmethod
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        pass
    
    def generate_backup_filename(self, backup_type: BackupType, 
                                timestamp: Optional[datetime] = None) -> str:
        """Generate standardized backup filename"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        date_str = timestamp.strftime("%Y%m%d_%H%M%S")
        extension = ".gz" if self.compress else ""
        
        return f"{self.service_name}_{backup_type.value}_{date_str}.backup{extension}"
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def compress_file(self, source_path: Path, target_path: Path) -> None:
        """Compress a file using gzip"""
        with open(source_path, 'rb') as f_in:
            with gzip.open(target_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def decompress_file(self, source_path: Path, target_path: Path) -> None:
        """Decompress a gzip file"""
        with gzip.open(source_path, 'rb') as f_in:
            with open(target_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        return file_path.stat().st_size if file_path.exists() else 0
    
    def cleanup_old_backups(self, retention_days: int = 30, 
                          max_backups: Optional[int] = None) -> List[Path]:
        """Clean up old backup files"""
        deleted_files = []
        backup_files = []
        
        # Get all backup files for this service
        for file_path in self.backup_dir.glob(f"{self.service_name}_*.backup*"):
            stat = file_path.stat()
            backup_files.append((file_path, stat.st_mtime))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Delete files older than retention period
        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
        
        for file_path, mtime in backup_files:
            should_delete = False
            
            # Check age
            if mtime < cutoff_time:
                should_delete = True
                self.logger.info(f"Deleting old backup: {file_path.name} (age)")
            
            # Check count limit
            elif max_backups and len(backup_files) - len(deleted_files) > max_backups:
                should_delete = True
                self.logger.info(f"Deleting old backup: {file_path.name} (count)")
            
            if should_delete:
                try:
                    file_path.unlink()
                    deleted_files.append(file_path)
                except Exception as e:
                    self.logger.error(f"Failed to delete {file_path}: {e}")
        
        return deleted_files
    
    def get_backup_metadata(self, backup_path: Path) -> Dict[str, Any]:
        """Extract metadata from backup file"""
        if not backup_path.exists():
            return {}
        
        stat = backup_path.stat()
        
        return {
            "filename": backup_path.name,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime, timezone.utc),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc),
            "checksum": self.calculate_checksum(backup_path),
            "compressed": backup_path.suffix == ".gz"
        }