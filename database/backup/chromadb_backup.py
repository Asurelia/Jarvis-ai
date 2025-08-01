"""
ChromaDB backup implementation for JARVIS AI
"""

import asyncio
import sqlite3
import shutil
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from .base_backup import BaseBackup, BackupType, BackupStatus

class ChromaDBBackup(BaseBackup):
    """ChromaDB backup implementation"""
    
    def __init__(self, backup_dir: Path, chroma_persist_dir: Path,
                 compress: bool = True):
        super().__init__("chromadb", backup_dir, compress)
        
        self.chroma_persist_dir = Path(chroma_persist_dir)
        if not self.chroma_persist_dir.exists():
            self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, backup_type: BackupType = BackupType.FULL,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create ChromaDB backup"""
        
        backup_filename = self.generate_backup_filename(backup_type)
        backup_path = self.backup_dir / backup_filename
        temp_backup_dir = self.backup_dir / f"temp_{backup_filename}"
        
        result = {
            "service": self.service_name,
            "backup_type": backup_type.value,
            "status": BackupStatus.RUNNING.value,
            "started_at": datetime.now(timezone.utc),
            "backup_path": str(backup_path),
            "metadata": metadata or {}
        }
        
        try:
            self.logger.info(f"Starting ChromaDB backup: {backup_filename}")
            
            # Create temporary backup directory
            temp_backup_dir.mkdir(exist_ok=True)
            
            # Backup ChromaDB data
            await self._backup_chroma_data(temp_backup_dir)
            
            # Create archive
            if self.compress:
                await self._create_compressed_archive(temp_backup_dir, backup_path)
            else:
                shutil.make_archive(str(backup_path.with_suffix('')), 'tar', temp_backup_dir)
                backup_path = backup_path.with_suffix('.tar')
            
            # Calculate file stats
            file_size = self.get_file_size(backup_path)
            checksum = self.calculate_checksum(backup_path)
            
            result.update({
                "status": BackupStatus.COMPLETED.value,
                "completed_at": datetime.now(timezone.utc),
                "file_size": file_size,
                "checksum": checksum,
                "backup_path": str(backup_path)
            })
            
            self.logger.info(f"ChromaDB backup completed: {backup_path.name} ({file_size} bytes)")
            
        except Exception as e:
            self.logger.error(f"ChromaDB backup failed: {e}")
            
            result.update({
                "status": BackupStatus.FAILED.value,
                "completed_at": datetime.now(timezone.utc),
                "error": str(e)
            })
            
            raise
        
        finally:
            # Cleanup temporary directory
            if temp_backup_dir.exists():
                shutil.rmtree(temp_backup_dir)
        
        return result
    
    async def _backup_chroma_data(self, backup_dir: Path):
        """Backup ChromaDB data files"""
        
        # Copy the entire ChromaDB persist directory
        if self.chroma_persist_dir.exists():
            chroma_backup_dir = backup_dir / "chroma_data"
            shutil.copytree(self.chroma_persist_dir, chroma_backup_dir)
        
        # Backup SQLite databases if they exist
        sqlite_files = list(self.chroma_persist_dir.glob("*.sqlite*"))
        for sqlite_file in sqlite_files:
            await self._backup_sqlite_file(sqlite_file, backup_dir / sqlite_file.name)
        
        # Create metadata file
        metadata = {
            "backup_timestamp": datetime.now(timezone.utc).isoformat(),
            "chroma_persist_dir": str(self.chroma_persist_dir),
            "files_backed_up": [
                str(f.relative_to(self.chroma_persist_dir))
                for f in self.chroma_persist_dir.rglob("*")
                if f.is_file()
            ]
        }
        
        with open(backup_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    async def _backup_sqlite_file(self, source_path: Path, target_path: Path):
        """Backup SQLite file with proper locking"""
        
        try:
            # Use SQLite backup API for consistent backup
            source_conn = sqlite3.connect(str(source_path))
            target_conn = sqlite3.connect(str(target_path))
            
            # Perform backup
            source_conn.backup(target_conn)
            
            source_conn.close()
            target_conn.close()
            
        except Exception as e:
            self.logger.warning(f"SQLite backup failed for {source_path}, using file copy: {e}")
            # Fallback to file copy
            shutil.copy2(source_path, target_path)
    
    async def _create_compressed_archive(self, source_dir: Path, target_path: Path):
        """Create compressed tar.gz archive"""
        
        import tarfile
        
        with tarfile.open(target_path, "w:gz") as tar:
            tar.add(source_dir, arcname=".")
    
    async def restore_backup(self, backup_path: Path, 
                           target_location: Optional[str] = None) -> bool:
        """Restore ChromaDB backup"""
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        restore_dir = Path(target_location) if target_location else self.chroma_persist_dir
        
        self.logger.info(f"Starting ChromaDB restore from {backup_path.name} to {restore_dir}")
        
        try:
            # Create temporary extraction directory
            temp_extract_dir = self.backup_dir / f"temp_extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_extract_dir.mkdir(exist_ok=True)
            
            # Extract backup archive
            if backup_path.name.endswith('.tar.gz') or backup_path.name.endswith('.gz'):
                await self._extract_compressed_archive(backup_path, temp_extract_dir)
            else:
                await self._extract_archive(backup_path, temp_extract_dir)
            
            # Restore ChromaDB data
            chroma_data_dir = temp_extract_dir / "chroma_data"
            if chroma_data_dir.exists():
                # Backup existing data
                if restore_dir.exists():
                    backup_existing_dir = restore_dir.parent / f"{restore_dir.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.move(restore_dir, backup_existing_dir)
                    self.logger.info(f"Existing data backed up to: {backup_existing_dir}")
                
                # Restore new data
                shutil.copytree(chroma_data_dir, restore_dir)
            
            # Verify metadata
            metadata_file = temp_extract_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    self.logger.info(f"Restored ChromaDB backup from: {metadata.get('backup_timestamp')}")
            
            self.logger.info("ChromaDB restore completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"ChromaDB restore failed: {e}")
            return False
        
        finally:
            # Cleanup temporary directory
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
    
    async def _extract_compressed_archive(self, archive_path: Path, extract_dir: Path):
        """Extract compressed tar.gz archive"""
        
        import tarfile
        
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(extract_dir)
    
    async def _extract_archive(self, archive_path: Path, extract_dir: Path):
        """Extract regular tar archive"""
        
        import tarfile
        
        with tarfile.open(archive_path, "r") as tar:
            tar.extractall(extract_dir)
    
    async def verify_backup(self, backup_path: Path) -> bool:
        """Verify ChromaDB backup integrity"""
        
        if not backup_path.exists():
            return False
        
        try:
            # Create temporary extraction directory
            temp_verify_dir = self.backup_dir / f"temp_verify_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_verify_dir.mkdir(exist_ok=True)
            
            # Extract and verify backup
            if backup_path.name.endswith('.tar.gz') or backup_path.name.endswith('.gz'):
                await self._extract_compressed_archive(backup_path, temp_verify_dir)
            else:
                await self._extract_archive(backup_path, temp_verify_dir)
            
            # Verify metadata file exists
            metadata_file = temp_verify_dir / "metadata.json"
            if not metadata_file.exists():
                self.logger.error("Backup verification failed: metadata.json not found")
                return False
            
            # Verify metadata content
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check for required ChromaDB data
            chroma_data_dir = temp_verify_dir / "chroma_data"
            if not chroma_data_dir.exists():
                self.logger.error("Backup verification failed: chroma_data directory not found")
                return False
            
            # Verify SQLite files if they exist
            for sqlite_file in chroma_data_dir.glob("*.sqlite*"):
                if not await self._verify_sqlite_file(sqlite_file):
                    self.logger.error(f"Backup verification failed: corrupted SQLite file {sqlite_file.name}")
                    return False
            
            self.logger.info(f"Backup verification successful: {backup_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup verification error: {e}")
            return False
        
        finally:
            # Cleanup temporary directory
            if temp_verify_dir.exists():
                shutil.rmtree(temp_verify_dir)
    
    async def _verify_sqlite_file(self, sqlite_path: Path) -> bool:
        """Verify SQLite file integrity"""
        
        try:
            conn = sqlite3.connect(str(sqlite_path))
            cursor = conn.cursor()
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            
            return result and result[0] == "ok"
            
        except Exception as e:
            self.logger.error(f"SQLite verification failed for {sqlite_path}: {e}")
            return False
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all ChromaDB backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob(f"{self.service_name}_*.backup*"):
            if backup_file.is_file():
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
    
    async def get_chroma_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics"""
        
        try:
            stats = {
                "persist_directory": str(self.chroma_persist_dir),
                "exists": self.chroma_persist_dir.exists(),
                "total_size": 0,
                "file_count": 0,
                "sqlite_files": []
            }
            
            if self.chroma_persist_dir.exists():
                # Count files and calculate total size
                for file_path in self.chroma_persist_dir.rglob("*"):
                    if file_path.is_file():
                        stats["file_count"] += 1
                        stats["total_size"] += file_path.stat().st_size
                        
                        if file_path.suffix in ['.sqlite', '.sqlite3', '.db']:
                            stats["sqlite_files"].append({
                                "name": file_path.name,
                                "size": file_path.stat().st_size,
                                "modified": datetime.fromtimestamp(
                                    file_path.stat().st_mtime, timezone.utc
                                ).isoformat()
                            })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get ChromaDB stats: {e}")
            return {"error": str(e)}