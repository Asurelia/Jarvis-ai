"""
JARVIS Database Backup Service
Automated backup service that runs as a daemon
"""

import asyncio
import signal
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.backup.backup_manager import BackupManager
from database.backup.backup_scheduler import BackupScheduler
from database.retention.retention_manager import RetentionManager
from database.monitoring.health_monitor import HealthMonitor
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BackupService:
    """Main backup service class"""
    
    def __init__(self, config_file: Path = None):
        self.config = self._load_config(config_file)
        self.running = False
        self.backup_manager = None
        self.scheduler = None
        self.retention_manager = None
        self.health_monitor = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_file: Path = None) -> dict:
        """Load service configuration"""
        
        if config_file and config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            # Default configuration
            config = {
                "backup_dir": "./backups",
                "archive_dir": "./archives",
                "database_url": f"postgresql://{settings.get('POSTGRES_USER', 'jarvis')}:{settings.get('POSTGRES_PASSWORD', 'password')}@{settings.get('POSTGRES_HOST', 'localhost')}:{settings.get('POSTGRES_PORT', '5432')}/{settings.get('POSTGRES_DB', 'jarvis_memory')}",
                "services": {
                    "postgresql": {
                        "host": settings.get('POSTGRES_HOST', 'localhost'),
                        "port": int(settings.get('POSTGRES_PORT', '5432')),
                        "database": settings.get('POSTGRES_DB', 'jarvis_memory'),
                        "username": settings.get('POSTGRES_USER', 'jarvis'),
                        "password": settings.get('POSTGRES_PASSWORD', 'password')
                    },
                    "redis": {
                        "host": settings.get('REDIS_HOST', 'localhost'),
                        "port": int(settings.get('REDIS_PORT', '6379')),
                        "password": settings.get('REDIS_PASSWORD'),
                        "db": 0
                    },
                    "chromadb": {
                        "persist_dir": settings.get('CHROMA_PERSIST_DIRECTORY', './memory/chroma')
                    }
                },
                "schedule": {
                    "postgresql": {
                        "cron": "0 2 * * *",  # Daily at 2 AM
                        "backup_type": "full",
                        "enabled": True
                    },
                    "redis": {
                        "cron": "0 3 * * *",  # Daily at 3 AM
                        "backup_type": "full",
                        "enabled": True
                    },
                    "chromadb": {
                        "cron": "0 4 * * *",  # Daily at 4 AM
                        "backup_type": "full",
                        "enabled": True
                    }
                },
                "retention": {
                    "enabled": True,
                    "cleanup_cron": "0 5 * * *"  # Daily at 5 AM
                },
                "health_check": {
                    "enabled": True,
                    "interval_minutes": 30
                }
            }
        
        return config
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def start(self):
        """Start the backup service"""
        
        logger.info("🚀 Starting JARVIS Database Backup Service")
        
        try:
            # Initialize components
            await self._initialize_components()
            
            # Start scheduler
            if self.scheduler:
                await self.scheduler.start()
                logger.info("✅ Backup scheduler started")
            
            self.running = True
            logger.info("✅ Backup service started successfully")
            
            # Main service loop
            await self._run_service_loop()
            
        except Exception as e:
            logger.error(f"❌ Failed to start backup service: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _initialize_components(self):
        """Initialize service components"""
        
        # Create directories
        Path(self.config['backup_dir']).mkdir(parents=True, exist_ok=True)
        Path(self.config['archive_dir']).mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        
        # Initialize backup manager
        self.backup_manager = BackupManager(
            backup_root_dir=Path(self.config['backup_dir']),
            config=self.config['services']
        )
        
        # Initialize scheduler
        self.scheduler = BackupScheduler(
            backup_manager=self.backup_manager,
            schedule_config=self.config['schedule']
        )
        
        # Initialize retention manager
        if self.config['retention']['enabled']:
            self.retention_manager = RetentionManager(
                database_url=self.config['database_url'],
                archive_dir=Path(self.config['archive_dir'])
            )
        
        # Initialize health monitor
        if self.config['health_check']['enabled']:
            self.health_monitor = HealthMonitor(self.config)
        
        logger.info("✅ Service components initialized")
    
    async def _run_service_loop(self):
        """Main service loop"""
        
        health_check_interval = self.config['health_check'].get('interval_minutes', 30) * 60
        last_health_check = 0
        last_retention_cleanup = 0
        retention_interval = 24 * 3600  # Daily
        
        while self.running:
            try:
                current_time = asyncio.get_event_loop().time()
                
                # Health check
                if (self.health_monitor and 
                    current_time - last_health_check >= health_check_interval):
                    
                    await self._run_health_check()
                    last_health_check = current_time
                
                # Retention cleanup
                if (self.retention_manager and 
                    current_time - last_retention_cleanup >= retention_interval):
                    
                    await self._run_retention_cleanup()
                    last_retention_cleanup = current_time
                
                # Sleep for 60 seconds before next check
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in service loop: {e}")
                await asyncio.sleep(60)
    
    async def _run_health_check(self):
        """Run health check"""
        
        try:
            logger.info("🏥 Running health check...")
            
            health_report = await self.health_monitor.run_full_health_check()
            
            overall_status = health_report['overall_status']
            
            if overall_status == 'healthy':
                logger.info("✅ Health check: All systems healthy")
            elif overall_status == 'warning':
                logger.warning(f"⚠️ Health check: {health_report['summary']['warnings']} warnings detected")
            elif overall_status == 'critical':
                logger.error(f"❌ Health check: {health_report['summary']['critical']} critical issues detected")
            
            # Log detailed issues
            for service_name, service_data in health_report.get('services', {}).items():
                if service_data['status'] != 'healthy':
                    logger.warning(f"Service {service_name}: {service_data['message']}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def _run_retention_cleanup(self):
        """Run retention cleanup"""
        
        try:
            logger.info("🧹 Running retention cleanup...")
            
            result = await self.retention_manager.execute_all_policies()
            
            logger.info(f"Retention cleanup completed:")
            logger.info(f"  - Policies executed: {result['successful_policies']}/{result['total_policies']}")
            logger.info(f"  - Records processed: {result['total_records_processed']}")
            logger.info(f"  - Execution time: {result['execution_time_seconds']:.1f}s")
            
            if result['total_errors'] > 0:
                logger.warning(f"  - Errors: {result['total_errors']}")
            
        except Exception as e:
            logger.error(f"Retention cleanup failed: {e}")
    
    async def _cleanup(self):
        """Cleanup service resources"""
        
        logger.info("🧹 Cleaning up service resources...")
        
        if self.scheduler:
            await self.scheduler.stop()
        
        if self.backup_manager:
            await self.backup_manager.close()
        
        logger.info("✅ Service cleanup completed")
    
    async def status(self):
        """Get service status"""
        
        if not self.backup_manager:
            return {"error": "Service not initialized"}
        
        status = {
            "service_running": self.running,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backup_manager": "initialized" if self.backup_manager else "not_initialized",
            "scheduler": "initialized" if self.scheduler else "not_initialized",
            "retention_manager": "initialized" if self.retention_manager else "not_initialized",
            "health_monitor": "initialized" if self.health_monitor else "not_initialized"
        }
        
        # Get scheduler status
        if self.scheduler:
            scheduler_status = self.scheduler.get_schedule_status()
            status["scheduler_details"] = scheduler_status
        
        # Get health status
        if self.health_monitor:
            health_report = await self.health_monitor.run_full_health_check()
            status["health"] = {
                "overall_status": health_report["overall_status"],
                "summary": health_report["summary"]
            }
        
        return status

async def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS Database Backup Service")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--status", action="store_true", help="Show service status")
    parser.add_argument("--test-backup", action="store_true", help="Run test backup")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    
    args = parser.parse_args()
    
    service = BackupService(args.config)
    
    if args.status:
        # Show status and exit
        await service._initialize_components()
        status = await service.status()
        print(json.dumps(status, indent=2, default=str))
        await service._cleanup()
        return
    
    if args.test_backup:
        # Run test backup and exit
        await service._initialize_components()
        logger.info("🧪 Running test backup...")
        
        result = await service.backup_manager.create_full_backup({
            "test": True,
            "triggered_by": "test_command"
        })
        
        logger.info(f"Test backup completed: {result['successful']}/{result['total_services']} successful")
        await service._cleanup()
        return
    
    if args.health_check:
        # Run health check and exit
        await service._initialize_components()
        await service._run_health_check()
        await service._cleanup()
        return
    
    # Start service
    await service.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)