"""
Data archiver for JARVIS AI
Handles archiving of old data to compressed storage
"""

import json
import gzip
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

class DataArchiver:
    """Handles data archiving operations"""
    
    def __init__(self, archive_dir: Path):
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    async def archive_records(self, table_name: str, records: List[Dict[str, Any]],
                            metadata: Optional[Dict[str, Any]] = None) -> Path:
        """Archive records to compressed JSON file"""
        
        if not records:
            raise ValueError("No records to archive")
        
        # Generate archive filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_id = str(uuid.uuid4())[:8]
        filename = f"{table_name}_{timestamp}_{archive_id}.json.gz"
        
        archive_path = self.archive_dir / table_name
        archive_path.mkdir(exist_ok=True)
        
        full_path = archive_path / filename
        
        # Prepare archive data
        archive_data = {
            "metadata": {
                "table_name": table_name,
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "record_count": len(records),
                "archive_id": archive_id,
                **(metadata or {})
            },
            "records": records
        }
        
        # Write compressed JSON
        with gzip.open(full_path, 'wt', encoding='utf-8') as f:
            json.dump(archive_data, f, indent=2, default=str)
        
        logger.info(f"Archived {len(records)} records from {table_name} to {filename}")
        
        return full_path
    
    async def restore_from_archive(self, archive_path: Path) -> Dict[str, Any]:
        """Restore records from archive file"""
        
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_path}")
        
        try:
            with gzip.open(archive_path, 'rt', encoding='utf-8') as f:
                archive_data = json.load(f)
            
            logger.info(f"Restored {archive_data['metadata']['record_count']} records from {archive_path.name}")
            
            return archive_data
            
        except Exception as e:
            logger.error(f"Failed to restore from archive {archive_path}: {e}")
            raise
    
    def list_archives(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available archive files"""
        
        archives = []
        
        if table_name:
            search_dirs = [self.archive_dir / table_name]
        else:
            search_dirs = [d for d in self.archive_dir.iterdir() if d.is_dir()]
        
        for archive_dir in search_dirs:
            if not archive_dir.exists():
                continue
            
            for archive_file in archive_dir.glob("*.json.gz"):
                stat = archive_file.stat()
                
                # Try to extract metadata without fully loading the file
                try:
                    with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                        # Read just the beginning to get metadata
                        content = f.read(1024)
                        if '"metadata"' in content:
                            f.seek(0)
                            data = json.load(f)
                            metadata = data.get('metadata', {})
                        else:
                            metadata = {}
                except:
                    metadata = {}
                
                archives.append({
                    "filename": archive_file.name,
                    "path": str(archive_file),
                    "table_name": archive_dir.name,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime, timezone.utc),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc),
                    "record_count": metadata.get('record_count', 0),
                    "archived_at": metadata.get('archived_at'),
                    "archive_id": metadata.get('archive_id')
                })
        
        # Sort by creation time (newest first)
        archives.sort(key=lambda x: x['created_at'], reverse=True)
        
        return archives
    
    def get_archive_stats(self) -> Dict[str, Any]:
        """Get statistics about archived data"""
        
        stats = {
            "total_archives": 0,
            "total_size_bytes": 0,
            "total_records": 0,
            "tables": {},
            "oldest_archive": None,
            "newest_archive": None
        }
        
        archives = self.list_archives()
        
        if not archives:
            return stats
        
        stats["total_archives"] = len(archives)
        stats["oldest_archive"] = archives[-1]["created_at"].isoformat()
        stats["newest_archive"] = archives[0]["created_at"].isoformat()
        
        # Aggregate by table
        for archive in archives:
            table_name = archive["table_name"]
            
            if table_name not in stats["tables"]:
                stats["tables"][table_name] = {
                    "archive_count": 0,
                    "total_size_bytes": 0,
                    "total_records": 0,
                    "oldest_archive": None,
                    "newest_archive": None
                }
            
            table_stats = stats["tables"][table_name]
            table_stats["archive_count"] += 1
            table_stats["total_size_bytes"] += archive["size_bytes"]
            table_stats["total_records"] += archive["record_count"]
            
            if not table_stats["oldest_archive"] or archive["created_at"] < datetime.fromisoformat(table_stats["oldest_archive"].replace('Z', '+00:00')):
                table_stats["oldest_archive"] = archive["created_at"].isoformat()
            
            if not table_stats["newest_archive"] or archive["created_at"] > datetime.fromisoformat(table_stats["newest_archive"].replace('Z', '+00:00')):
                table_stats["newest_archive"] = archive["created_at"].isoformat()
            
            stats["total_size_bytes"] += archive["size_bytes"]
            stats["total_records"] += archive["record_count"]
        
        return stats
    
    def cleanup_old_archives(self, retention_days: int = 365) -> List[Path]:
        """Clean up old archive files"""
        
        deleted_files = []
        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
        
        archives = self.list_archives()
        
        for archive in archives:
            archive_path = Path(archive["path"])
            
            if archive["created_at"].timestamp() < cutoff_time:
                try:
                    archive_path.unlink()
                    deleted_files.append(archive_path)
                    logger.info(f"Deleted old archive: {archive_path.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to delete archive {archive_path}: {e}")
        
        return deleted_files
    
    def verify_archive(self, archive_path: Path) -> bool:
        """Verify archive file integrity"""
        
        try:
            with gzip.open(archive_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            # Basic validation
            if 'metadata' not in data or 'records' not in data:
                return False
            
            metadata = data['metadata']
            records = data['records']
            
            # Check record count matches metadata
            if metadata.get('record_count') != len(records):
                return False
            
            # Check required metadata fields
            required_fields = ['table_name', 'archived_at', 'record_count']
            for field in required_fields:
                if field not in metadata:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Archive verification failed for {archive_path}: {e}")
            return False
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information for archive directory"""
        
        try:
            import shutil
            
            total, used, free = shutil.disk_usage(self.archive_dir)
            
            return {
                "archive_directory": str(self.archive_dir),
                "total_space_bytes": total,
                "used_space_bytes": used,
                "free_space_bytes": free,
                "archive_size_bytes": sum(
                    f.stat().st_size
                    for f in self.archive_dir.rglob("*")
                    if f.is_file()
                ),
                "usage_percentage": (used / total) * 100
            }
            
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {"error": str(e)}