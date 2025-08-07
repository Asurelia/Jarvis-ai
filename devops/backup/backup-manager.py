#!/usr/bin/env python3
"""
JARVIS AI - Comprehensive Backup & Disaster Recovery Manager
Production-ready backup system with encryption, compression, and multi-destination support
"""

import os
import json
import yaml
import logging
import subprocess
import tempfile
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
import psycopg2
import redis
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Backup configuration settings"""
    name: str
    type: str  # database, redis, files, docker_volumes
    source: Dict[str, Any]
    destination: Dict[str, Any]
    schedule: str
    retention_days: int
    encryption_enabled: bool = True
    compression_enabled: bool = True
    verification_enabled: bool = True
    priority: int = 1  # 1=highest, 5=lowest

@dataclass
class BackupMetadata:
    """Backup metadata for tracking and verification"""
    backup_id: str
    config_name: str
    timestamp: datetime
    size_bytes: int
    checksum: str
    encrypted: bool
    compressed: bool
    destination: str
    status: str  # success, failed, in_progress
    verification_status: str  # verified, failed, pending
    retention_date: datetime

class BackupDestination:
    """Abstract base class for backup destinations"""
    
    def upload(self, source_path: str, destination_path: str) -> bool:
        raise NotImplementedError
    
    def download(self, source_path: str, destination_path: str) -> bool:
        raise NotImplementedError
    
    def delete(self, path: str) -> bool:
        raise NotImplementedError
    
    def list(self, prefix: str = "") -> List[str]:
        raise NotImplementedError

class LocalDestination(BackupDestination):
    """Local filesystem destination"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def upload(self, source_path: str, destination_path: str) -> bool:
        try:
            dest_full_path = self.base_path / destination_path
            dest_full_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(source_path, dest_full_path)
            return True
        except Exception as e:
            logger.error(f"Local upload failed: {e}")
            return False
    
    def download(self, source_path: str, destination_path: str) -> bool:
        try:
            source_full_path = self.base_path / source_path
            import shutil
            shutil.copy2(source_full_path, destination_path)
            return True
        except Exception as e:
            logger.error(f"Local download failed: {e}")
            return False
    
    def delete(self, path: str) -> bool:
        try:
            full_path = self.base_path / path
            full_path.unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"Local delete failed: {e}")
            return False
    
    def list(self, prefix: str = "") -> List[str]:
        try:
            prefix_path = self.base_path / prefix
            if prefix_path.is_dir():
                return [str(p.relative_to(self.base_path)) for p in prefix_path.rglob("*") if p.is_file()]
            return []
        except Exception as e:
            logger.error(f"Local list failed: {e}")
            return []

class S3Destination(BackupDestination):
    """AWS S3 destination"""
    
    def __init__(self, bucket: str, prefix: str = "", region: str = "us-east-1"):
        self.bucket = bucket
        self.prefix = prefix
        self.s3_client = boto3.client('s3', region_name=region)
    
    def upload(self, source_path: str, destination_path: str) -> bool:
        try:
            key = f"{self.prefix}/{destination_path}" if self.prefix else destination_path
            self.s3_client.upload_file(source_path, self.bucket, key)
            return True
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return False
    
    def download(self, source_path: str, destination_path: str) -> bool:
        try:
            key = f"{self.prefix}/{source_path}" if self.prefix else source_path
            self.s3_client.download_file(self.bucket, key, destination_path)
            return True
        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            return False
    
    def delete(self, path: str) -> bool:
        try:
            key = f"{self.prefix}/{path}" if self.prefix else path
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception as e:
            logger.error(f"S3 delete failed: {e}")
            return False
    
    def list(self, prefix: str = "") -> List[str]:
        try:
            full_prefix = f"{self.prefix}/{prefix}" if self.prefix else prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=full_prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            logger.error(f"S3 list failed: {e}")
            return []

class DatabaseBackup:
    """Database backup handler"""
    
    @staticmethod
    def backup_postgresql(config: Dict[str, Any]) -> str:
        """Backup PostgreSQL database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"postgresql_backup_{timestamp}.sql"
            temp_path = Path(tempfile.gettempdir()) / backup_file
            
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "--host", config["host"],
                "--port", str(config["port"]),
                "--username", config["username"],
                "--dbname", config["database"],
                "--verbose",
                "--clean",
                "--no-owner",
                "--no-privileges",
                "--file", str(temp_path)
            ]
            
            # Set password via environment
            env = os.environ.copy()
            env["PGPASSWORD"] = config["password"]
            
            # Execute backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            logger.info(f"PostgreSQL backup created: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {e}")
            raise

    @staticmethod
    def backup_redis(config: Dict[str, Any]) -> str:
        """Backup Redis database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"redis_backup_{timestamp}.rdb"
            temp_path = Path(tempfile.gettempdir()) / backup_file
            
            # Connect to Redis
            redis_client = redis.Redis(
                host=config["host"],
                port=config["port"],
                password=config.get("password"),
                decode_responses=False
            )
            
            # Trigger background save
            redis_client.bgsave()
            
            # Wait for save to complete
            import time
            while redis_client.lastsave() == redis_client.lastsave():
                time.sleep(1)
            
            # Copy RDB file
            rdb_path = config.get("rdb_path", "/var/lib/redis/dump.rdb")
            if Path(rdb_path).exists():
                import shutil
                shutil.copy2(rdb_path, temp_path)
            else:
                # Use Redis DUMP command for keys
                keys = redis_client.keys("*")
                with open(temp_path, "wb") as f:
                    for key in keys:
                        dump_data = redis_client.dump(key)
                        ttl = redis_client.ttl(key)
                        f.write(f"{key.decode()}:{ttl}:{dump_data.hex()}\n".encode())
            
            logger.info(f"Redis backup created: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            logger.error(f"Redis backup failed: {e}")
            raise

class FileBackup:
    """File and directory backup handler"""
    
    @staticmethod
    def backup_directory(source_path: str, exclude_patterns: List[str] = None) -> str:
        """Backup directory using tar with compression"""
        try:
            source = Path(source_path)
            if not source.exists():
                raise Exception(f"Source path does not exist: {source_path}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{source.name}_backup_{timestamp}.tar.gz"
            temp_path = Path(tempfile.gettempdir()) / backup_file
            
            # Build tar command
            cmd = ["tar", "-czf", str(temp_path), "-C", str(source.parent), source.name]
            
            # Add exclusions
            if exclude_patterns:
                for pattern in exclude_patterns:
                    cmd.extend(["--exclude", pattern])
            
            # Execute backup
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"tar failed: {result.stderr}")
            
            logger.info(f"Directory backup created: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            logger.error(f"Directory backup failed: {e}")
            raise

class BackupManager:
    """Main backup manager class"""
    
    def __init__(self, config_file: str = "backup-config.yml", 
                 metadata_file: str = "backup-metadata.json",
                 encryption_key: Optional[str] = None):
        self.config_file = Path(config_file)
        self.metadata_file = Path(metadata_file)
        self.encryption_key = encryption_key or os.getenv("BACKUP_ENCRYPTION_KEY", "default-key")
        self.cipher = self._initialize_cipher()
        
        self.configs: Dict[str, BackupConfig] = {}
        self.metadata: List[BackupMetadata] = []
        self.destinations: Dict[str, BackupDestination] = {}
        
        self._load_configs()
        self._load_metadata()
        self._initialize_destinations()
    
    def _initialize_cipher(self) -> Fernet:
        """Initialize encryption cipher"""
        key_bytes = self.encryption_key.encode()
        digest = hashes.Hash(hashes.SHA256())
        digest.update(key_bytes)
        derived_key = base64.urlsafe_b64encode(digest.finalize()[:32])
        return Fernet(derived_key)
    
    def _load_configs(self):
        """Load backup configurations"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                config_data = yaml.safe_load(f)
                for name, config in config_data.get("backups", {}).items():
                    self.configs[name] = BackupConfig(name=name, **config)
        
        logger.info(f"Loaded {len(self.configs)} backup configurations")
    
    def _load_metadata(self):
        """Load backup metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                metadata_data = json.load(f)
                for item in metadata_data:
                    item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                    item["retention_date"] = datetime.fromisoformat(item["retention_date"])
                    self.metadata.append(BackupMetadata(**item))
        
        logger.info(f"Loaded {len(self.metadata)} backup metadata records")
    
    def _save_metadata(self):
        """Save backup metadata"""
        metadata_data = []
        for metadata in self.metadata:
            item = asdict(metadata)
            item["timestamp"] = metadata.timestamp.isoformat()
            item["retention_date"] = metadata.retention_date.isoformat()
            metadata_data.append(item)
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata_data, f, indent=2)
    
    def _initialize_destinations(self):
        """Initialize backup destinations"""
        # Initialize destinations based on configs
        for config in self.configs.values():
            dest_config = config.destination
            dest_type = dest_config.get("type")
            dest_name = f"{config.name}_destination"
            
            if dest_type == "local":
                self.destinations[dest_name] = LocalDestination(dest_config["path"])
            elif dest_type == "s3":
                self.destinations[dest_name] = S3Destination(
                    bucket=dest_config["bucket"],
                    prefix=dest_config.get("prefix", ""),
                    region=dest_config.get("region", "us-east-1")
                )
    
    def _encrypt_file(self, file_path: str) -> str:
        """Encrypt a file"""
        try:
            encrypted_path = f"{file_path}.encrypted"
            
            with open(file_path, 'rb') as infile:
                with open(encrypted_path, 'wb') as outfile:
                    data = infile.read()
                    encrypted_data = self.cipher.encrypt(data)
                    outfile.write(encrypted_data)
            
            # Remove original file
            os.unlink(file_path)
            return encrypted_path
            
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            raise
    
    def _decrypt_file(self, encrypted_path: str, output_path: str) -> bool:
        """Decrypt a file"""
        try:
            with open(encrypted_path, 'rb') as infile:
                with open(output_path, 'wb') as outfile:
                    encrypted_data = infile.read()
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    outfile.write(decrypted_data)
            return True
            
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            return False
    
    def _compress_file(self, file_path: str) -> str:
        """Compress a file using gzip"""
        try:
            import gzip
            compressed_path = f"{file_path}.gz"
            
            with open(file_path, 'rb') as infile:
                with gzip.open(compressed_path, 'wb') as outfile:
                    outfile.write(infile.read())
            
            # Remove original file
            os.unlink(file_path)
            return compressed_path
            
        except Exception as e:
            logger.error(f"File compression failed: {e}")
            raise
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def execute_backup(self, config_name: str) -> BackupMetadata:
        """Execute a single backup"""
        config = self.configs.get(config_name)
        if not config:
            raise Exception(f"Backup configuration '{config_name}' not found")
        
        logger.info(f"Starting backup: {config_name}")
        
        # Generate backup ID
        backup_id = f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Create backup based on type
            if config.type == "postgresql":
                backup_path = DatabaseBackup.backup_postgresql(config.source)
            elif config.type == "redis":
                backup_path = DatabaseBackup.backup_redis(config.source)
            elif config.type == "files":
                backup_path = FileBackup.backup_directory(
                    config.source["path"],
                    config.source.get("exclude_patterns", [])
                )
            else:
                raise Exception(f"Unsupported backup type: {config.type}")
            
            # Calculate initial checksum
            checksum = self._calculate_checksum(backup_path)
            initial_size = os.path.getsize(backup_path)
            
            # Compress if enabled
            if config.compression_enabled:
                backup_path = self._compress_file(backup_path)
                logger.info("Backup compressed")
            
            # Encrypt if enabled
            encrypted = False
            if config.encryption_enabled:
                backup_path = self._encrypt_file(backup_path)
                encrypted = True
                logger.info("Backup encrypted")
            
            final_size = os.path.getsize(backup_path)
            
            # Upload to destination
            destination = self.destinations[f"{config_name}_destination"]
            remote_path = f"{backup_id}/{Path(backup_path).name}"
            
            if not destination.upload(backup_path, remote_path):
                raise Exception("Failed to upload backup to destination")
            
            logger.info(f"Backup uploaded to: {remote_path}")
            
            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                config_name=config_name,
                timestamp=datetime.now(),
                size_bytes=final_size,
                checksum=checksum,
                encrypted=encrypted,
                compressed=config.compression_enabled,
                destination=remote_path,
                status="success",
                verification_status="pending",
                retention_date=datetime.now() + timedelta(days=config.retention_days)
            )
            
            # Verify backup if enabled
            if config.verification_enabled:
                if self._verify_backup(metadata):
                    metadata.verification_status = "verified"
                    logger.info("Backup verification successful")
                else:
                    metadata.verification_status = "failed"
                    logger.error("Backup verification failed")
            
            # Clean up local file
            os.unlink(backup_path)
            
            # Save metadata
            self.metadata.append(metadata)
            self._save_metadata()
            
            logger.info(f"Backup completed successfully: {backup_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Backup failed for {config_name}: {e}")
            
            # Create failed metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                config_name=config_name,
                timestamp=datetime.now(),
                size_bytes=0,
                checksum="",
                encrypted=False,
                compressed=False,
                destination="",
                status="failed",
                verification_status="failed",
                retention_date=datetime.now() + timedelta(days=1)
            )
            
            self.metadata.append(metadata)
            self._save_metadata()
            
            raise
    
    def _verify_backup(self, metadata: BackupMetadata) -> bool:
        """Verify backup integrity"""
        try:
            destination = self.destinations[f"{metadata.config_name}_destination"]
            
            # Download backup to temp location
            temp_path = Path(tempfile.gettempdir()) / f"verify_{metadata.backup_id}"
            
            if not destination.download(metadata.destination, str(temp_path)):
                return False
            
            # Verify file size
            if os.path.getsize(temp_path) != metadata.size_bytes:
                logger.error("Backup verification failed: size mismatch")
                return False
            
            # For encrypted backups, try to decrypt
            if metadata.encrypted:
                decrypted_path = f"{temp_path}.decrypted"
                if not self._decrypt_file(str(temp_path), decrypted_path):
                    return False
                temp_path = Path(decrypted_path)
            
            # Clean up
            temp_path.unlink(missing_ok=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Backup verification error: {e}")
            return False
    
    def restore_backup(self, backup_id: str, restore_path: str) -> bool:
        """Restore a backup"""
        try:
            # Find backup metadata
            metadata = None
            for meta in self.metadata:
                if meta.backup_id == backup_id:
                    metadata = meta
                    break
            
            if not metadata:
                raise Exception(f"Backup not found: {backup_id}")
            
            if metadata.status != "success":
                raise Exception(f"Cannot restore failed backup: {backup_id}")
            
            logger.info(f"Starting restore for backup: {backup_id}")
            
            # Download backup
            destination = self.destinations[f"{metadata.config_name}_destination"]
            temp_path = Path(tempfile.gettempdir()) / f"restore_{backup_id}"
            
            if not destination.download(metadata.destination, str(temp_path)):
                raise Exception("Failed to download backup for restore")
            
            # Decrypt if needed
            if metadata.encrypted:
                decrypted_path = f"{temp_path}.decrypted"
                if not self._decrypt_file(str(temp_path), decrypted_path):
                    raise Exception("Failed to decrypt backup")
                temp_path = Path(decrypted_path)
            
            # Decompress if needed
            if metadata.compressed:
                import gzip
                decompressed_path = f"{temp_path}.decompressed"
                with gzip.open(temp_path, 'rb') as infile:
                    with open(decompressed_path, 'wb') as outfile:
                        outfile.write(infile.read())
                temp_path = Path(decompressed_path)
            
            # Move to final location
            import shutil
            shutil.move(str(temp_path), restore_path)
            
            logger.info(f"Backup restored to: {restore_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def cleanup_expired_backups(self):
        """Clean up expired backups"""
        logger.info("Starting backup cleanup process")
        
        current_time = datetime.now()
        expired_backups = [
            metadata for metadata in self.metadata 
            if metadata.retention_date < current_time
        ]
        
        for metadata in expired_backups:
            try:
                # Delete from destination
                destination = self.destinations[f"{metadata.config_name}_destination"]
                if destination.delete(metadata.destination):
                    logger.info(f"Deleted expired backup: {metadata.backup_id}")
                    
                    # Remove from metadata
                    self.metadata.remove(metadata)
                else:
                    logger.error(f"Failed to delete backup: {metadata.backup_id}")
                    
            except Exception as e:
                logger.error(f"Error cleaning up backup {metadata.backup_id}: {e}")
        
        # Save updated metadata
        self._save_metadata()
        logger.info(f"Cleanup completed. Removed {len(expired_backups)} expired backups")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get overall backup status"""
        total_backups = len(self.metadata)
        successful_backups = len([m for m in self.metadata if m.status == "success"])
        failed_backups = len([m for m in self.metadata if m.status == "failed"])
        verified_backups = len([m for m in self.metadata if m.verification_status == "verified"])
        
        total_size = sum(m.size_bytes for m in self.metadata if m.status == "success")
        
        recent_backups = [
            m for m in self.metadata 
            if m.timestamp > datetime.now() - timedelta(days=7)
        ]
        
        return {
            "total_backups": total_backups,
            "successful_backups": successful_backups,
            "failed_backups": failed_backups,
            "verified_backups": verified_backups,
            "total_size_gb": total_size / (1024**3),
            "recent_backups_count": len(recent_backups),
            "configurations": list(self.configs.keys())
        }

def main():
    """CLI interface for backup manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS AI Backup Manager")
    parser.add_argument("--config", "-c", default="backup-config.yml",
                       help="Backup configuration file")
    parser.add_argument("--action", "-a", required=True,
                       choices=["backup", "restore", "cleanup", "status", "verify"],
                       help="Action to perform")
    parser.add_argument("--name", "-n", help="Backup configuration name")
    parser.add_argument("--backup-id", help="Backup ID for restore/verify")
    parser.add_argument("--restore-path", help="Path for restore operation")
    
    args = parser.parse_args()
    
    backup_manager = BackupManager(config_file=args.config)
    
    if args.action == "backup":
        if not args.name:
            # Backup all configurations
            for config_name in backup_manager.configs:
                try:
                    backup_manager.execute_backup(config_name)
                except Exception as e:
                    logger.error(f"Backup failed for {config_name}: {e}")
        else:
            backup_manager.execute_backup(args.name)
    
    elif args.action == "restore":
        if not args.backup_id or not args.restore_path:
            parser.error("--backup-id and --restore-path are required for restore")
        backup_manager.restore_backup(args.backup_id, args.restore_path)
    
    elif args.action == "cleanup":
        backup_manager.cleanup_expired_backups()
    
    elif args.action == "status":
        status = backup_manager.get_backup_status()
        print(json.dumps(status, indent=2))
    
    elif args.action == "verify":
        if args.backup_id:
            # Verify specific backup
            for metadata in backup_manager.metadata:
                if metadata.backup_id == args.backup_id:
                    result = backup_manager._verify_backup(metadata)
                    print(f"Backup {args.backup_id} verification: {'PASSED' if result else 'FAILED'}")
                    break
            else:
                print(f"Backup {args.backup_id} not found")
        else:
            # Verify all backups
            for metadata in backup_manager.metadata:
                if metadata.status == "success" and metadata.verification_status != "verified":
                    result = backup_manager._verify_backup(metadata)
                    metadata.verification_status = "verified" if result else "failed"
            backup_manager._save_metadata()

if __name__ == "__main__":
    main()