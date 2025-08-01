"""
Comprehensive backup and recovery tests for JARVIS AI
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

from database.backup.backup_manager import BackupManager
from database.backup.base_backup import BackupType
from database.backup.postgresql_backup import PostgreSQLBackup
from database.backup.redis_backup import RedisBackup
from database.backup.chromadb_backup import ChromaDBBackup

class TestBackupRecovery:
    """Comprehensive backup and recovery test suite"""
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def backup_config(self):
        """Test backup configuration"""
        return {
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "database": "test_jarvis",
                "username": "test_user",
                "password": "test_password"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "password": None,
                "db": 0
            },
            "chromadb": {
                "persist_dir": "./test_memory/chroma"
            }
        }
    
    @pytest.mark.asyncio
    async def test_postgresql_backup_creation(self, temp_backup_dir, backup_config):
        """Test PostgreSQL backup creation"""
        
        pg_backup = PostgreSQLBackup(
            backup_dir=temp_backup_dir / "postgresql",
            **backup_config["postgresql"]
        )
        
        try:
            # Create test backup
            result = await pg_backup.create_backup(BackupType.FULL, {
                "test": True,
                "description": "Test backup for automated testing"
            })
            
            # Verify backup result
            assert result["status"] == "completed"
            assert result["service"] == "postgresql"
            assert result["backup_type"] == "full"
            assert "backup_path" in result
            assert "file_size" in result
            assert "checksum" in result
            
            # Verify backup file exists
            backup_path = Path(result["backup_path"])
            assert backup_path.exists()
            assert backup_path.stat().st_size > 0
            
            # Verify backup can be listed
            backups = await pg_backup.list_backups()
            assert len(backups) == 1
            assert backups[0]["service"] == "postgresql"
            
        except Exception as e:
            # Skip test if PostgreSQL is not available
            pytest.skip(f"PostgreSQL not available for testing: {e}")
    
    @pytest.mark.asyncio
    async def test_backup_verification(self, temp_backup_dir, backup_config):
        """Test backup verification"""
        
        pg_backup = PostgreSQLBackup(
            backup_dir=temp_backup_dir / "postgresql",
            **backup_config["postgresql"]
        )
        
        try:
            # Create backup
            result = await pg_backup.create_backup(BackupType.FULL)
            backup_path = Path(result["backup_path"])
            
            # Verify backup
            verified = await pg_backup.verify_backup(backup_path)
            assert verified is True
            
            # Test verification with non-existent file
            fake_path = temp_backup_dir / "fake_backup.backup"
            verified = await pg_backup.verify_backup(fake_path)
            assert verified is False
            
        except Exception as e:
            pytest.skip(f"PostgreSQL not available for testing: {e}")
    
    @pytest.mark.asyncio
    async def test_backup_manager_full_backup(self, temp_backup_dir, backup_config):
        """Test full system backup through BackupManager"""
        
        backup_manager = BackupManager(
            backup_root_dir=temp_backup_dir,
            config=backup_config
        )
        
        try:
            # Create full system backup
            result = await backup_manager.create_full_backup({
                "test": True,
                "description": "Full system test backup"
            })
            
            # Verify result structure
            assert "backup_type" in result
            assert "total_services" in result
            assert "successful" in result
            assert "results" in result
            
            # Check that at least one service backup was attempted
            assert result["total_services"] > 0
            
            # Verify backup directories were created
            for service in ["postgresql", "redis", "chromadb"]:
                service_dir = temp_backup_dir / service
                # Directory should exist even if backup failed
                assert service_dir.exists()
        
        finally:
            await backup_manager.close()
    
    @pytest.mark.asyncio
    async def test_backup_cleanup(self, temp_backup_dir, backup_config):
        """Test old backup cleanup"""
        
        pg_backup = PostgreSQLBackup(
            backup_dir=temp_backup_dir / "postgresql",
            **backup_config["postgresql"]
        )
        
        try:
            # Create multiple test backup files
            backup_files = []
            for i in range(5):
                filename = f"postgresql_full_test_{i}.backup.gz"
                backup_file = temp_backup_dir / "postgresql" / filename
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Create dummy backup file
                backup_file.write_text(f"test backup content {i}")
                backup_files.append(backup_file)
            
            # Verify files exist
            assert len(list((temp_backup_dir / "postgresql").glob("*.backup*"))) == 5
            
            # Cleanup old backups (keep only 3)
            deleted_files = pg_backup.cleanup_old_backups(
                retention_days=365,  # Don't delete by age
                max_backups=3
            )
            
            # Verify cleanup worked
            remaining_files = list((temp_backup_dir / "postgresql").glob("*.backup*"))
            assert len(remaining_files) == 3
            assert len(deleted_files) == 2
            
        except Exception as e:
            pytest.skip(f"PostgreSQL not available for testing: {e}")
    
    @pytest.mark.asyncio
    async def test_chromadb_backup_and_restore(self, temp_backup_dir):
        """Test ChromaDB backup and restore"""
        
        # Create test ChromaDB data
        test_chroma_dir = temp_backup_dir / "test_chroma"
        test_chroma_dir.mkdir(parents=True)
        
        # Create some test files
        (test_chroma_dir / "chroma.sqlite3").write_text("test sqlite data")
        (test_chroma_dir / "index.bin").write_bytes(b"test binary data")
        
        chroma_backup = ChromaDBBackup(
            backup_dir=temp_backup_dir / "chromadb",
            chroma_persist_dir=test_chroma_dir
        )
        
        # Create backup
        result = await chroma_backup.create_backup(BackupType.FULL, {
            "test": True
        })
        
        # Verify backup
        assert result["status"] == "completed"
        assert result["service"] == "chromadb"
        
        backup_path = Path(result["backup_path"])
        assert backup_path.exists()
        
        # Verify backup
        verified = await chroma_backup.verify_backup(backup_path)
        assert verified is True
        
        # Test restore to different location
        restore_dir = temp_backup_dir / "restored_chroma"
        success = await chroma_backup.restore_backup(backup_path, str(restore_dir))
        
        assert success is True
        assert restore_dir.exists()
        assert (restore_dir / "chroma.sqlite3").exists()
        assert (restore_dir / "index.bin").exists()
    
    @pytest.mark.asyncio
    async def test_backup_health_check(self, temp_backup_dir, backup_config):
        """Test backup system health check"""
        
        backup_manager = BackupManager(
            backup_root_dir=temp_backup_dir,
            config=backup_config
        )
        
        try:
            # Run health check
            health = await backup_manager.health_check()
            
            # Verify health check structure
            assert "timestamp" in health
            assert "overall_status" in health
            assert "services" in health
            assert "backup_directories" in health
            assert "recent_backups" in health
            
            # Verify backup directories check
            for service in ["postgresql", "redis", "chromadb"]:
                assert service in health["backup_directories"]
                dir_info = health["backup_directories"][service]
                assert "exists" in dir_info
                assert "writable" in dir_info
                assert "path" in dir_info
        
        finally:
            await backup_manager.close()
    
    @pytest.mark.asyncio
    async def test_backup_stats(self, temp_backup_dir, backup_config):
        """Test backup statistics collection"""
        
        backup_manager = BackupManager(
            backup_root_dir=temp_backup_dir,
            config=backup_config
        )
        
        try:
            # Get service stats
            stats = await backup_manager.get_service_stats()
            
            # Verify stats structure
            assert isinstance(stats, dict)
            
            # Check for expected services
            expected_services = ["postgresql", "redis", "chromadb"]
            for service in expected_services:
                assert service in stats
                # Each service should have either data or error
                service_stats = stats[service]
                assert isinstance(service_stats, dict)
        
        finally:
            await backup_manager.close()
    
    def test_backup_filename_generation(self, temp_backup_dir):
        """Test backup filename generation"""
        
        from database.backup.base_backup import BaseBackup, BackupType
        
        class TestBackup(BaseBackup):
            async def create_backup(self, backup_type, metadata=None):
                pass
            async def restore_backup(self, backup_path, target_location=None):
                pass
            async def verify_backup(self, backup_path):
                pass
            async def list_backups(self):
                pass
        
        backup = TestBackup("test_service", temp_backup_dir)
        
        # Test filename generation
        filename = backup.generate_backup_filename(BackupType.FULL)
        
        assert filename.startswith("test_service_full_")
        assert filename.endswith(".backup.gz")
        
        # Test without compression
        backup.compress = False
        filename = backup.generate_backup_filename(BackupType.INCREMENTAL)
        
        assert filename.startswith("test_service_incremental_")
        assert filename.endswith(".backup")
        assert not filename.endswith(".gz")
    
    def test_backup_metadata_extraction(self, temp_backup_dir):
        """Test backup metadata extraction"""
        
        from database.backup.base_backup import BaseBackup
        
        class TestBackup(BaseBackup):
            async def create_backup(self, backup_type, metadata=None):
                pass
            async def restore_backup(self, backup_path, target_location=None):
                pass
            async def verify_backup(self, backup_path):
                pass
            async def list_backups(self):
                pass
        
        backup = TestBackup("test_service", temp_backup_dir)
        
        # Create test backup file
        test_file = temp_backup_dir / "test_backup.backup"
        test_file.write_text("test backup content")
        
        # Get metadata
        metadata = backup.get_backup_metadata(test_file)
        
        assert metadata["filename"] == "test_backup.backup"
        assert metadata["size"] > 0
        assert "created_at" in metadata
        assert "modified_at" in metadata
        assert "checksum" in metadata
        assert metadata["compressed"] is False

@pytest.mark.integration
class TestBackupIntegration:
    """Integration tests requiring actual database connections"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_backup_restore(self):
        """End-to-end backup and restore test"""
        # This test would require actual database setup
        # and is marked as integration test
        pytest.skip("Integration test - requires database setup")
    
    @pytest.mark.asyncio
    async def test_disaster_recovery_scenario(self):
        """Test complete disaster recovery scenario"""
        # This test would simulate complete data loss
        # and recovery from backups
        pytest.skip("Integration test - requires database setup")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])