"""
Backup scheduler for JARVIS AI
Automated backup scheduling with cron-like functionality
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from croniter import croniter
from pathlib import Path

from .backup_manager import BackupManager, BackupConfig
from .base_backup import BackupType

logger = logging.getLogger(__name__)

@dataclass
class ScheduledBackup:
    """Scheduled backup configuration"""
    service_name: str
    cron_expression: str
    backup_type: BackupType
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0
    max_failures: int = 3

class BackupScheduler:
    """Automated backup scheduler"""
    
    def __init__(self, backup_manager: BackupManager, 
                 schedule_config: Dict[str, Any] = None):
        self.backup_manager = backup_manager
        self.schedules: Dict[str, ScheduledBackup] = {}
        self.running = False
        self.scheduler_task = None
        
        # Load schedule configuration
        self._load_schedule_config(schedule_config or {})
    
    def _load_schedule_config(self, config: Dict[str, Any]):
        """Load backup schedules from configuration"""
        
        # Default schedules
        default_schedules = {
            'postgresql': {
                'cron': '0 2 * * *',  # Daily at 2 AM
                'backup_type': 'full',
                'enabled': True
            },
            'redis': {
                'cron': '0 3 * * *',  # Daily at 3 AM
                'backup_type': 'full',
                'enabled': True
            },
            'chromadb': {
                'cron': '0 4 * * *',  # Daily at 4 AM
                'backup_type': 'full',
                'enabled': True
            }
        }
        
        # Merge with provided config
        for service_name, default_config in default_schedules.items():
            service_config = config.get(service_name, {})
            final_config = {**default_config, **service_config}
            
            backup_type = BackupType.FULL
            if final_config['backup_type'].lower() == 'incremental':
                backup_type = BackupType.INCREMENTAL
            elif final_config['backup_type'].lower() == 'differential':
                backup_type = BackupType.DIFFERENTIAL
            
            schedule = ScheduledBackup(
                service_name=service_name,
                cron_expression=final_config['cron'],
                backup_type=backup_type,
                enabled=final_config['enabled']
            )
            
            # Calculate next run time
            self._update_next_run_time(schedule)
            
            self.schedules[service_name] = schedule
    
    def _update_next_run_time(self, schedule: ScheduledBackup):
        """Update next run time for a schedule"""
        
        try:
            cron = croniter(schedule.cron_expression, datetime.now(timezone.utc))
            schedule.next_run = cron.get_next(datetime)
            
        except Exception as e:
            logger.error(f"Invalid cron expression for {schedule.service_name}: {e}")
            schedule.enabled = False
    
    async def start(self):
        """Start the backup scheduler"""
        
        if self.running:
            logger.warning("Backup scheduler is already running")
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("Backup scheduler started")
        
        # Log scheduled backups
        for service_name, schedule in self.schedules.items():
            if schedule.enabled:
                logger.info(f"Scheduled {schedule.backup_type.value} backup for {service_name}: "
                           f"{schedule.cron_expression} (next: {schedule.next_run})")
    
    async def stop(self):
        """Stop the backup scheduler"""
        
        if not self.running:
            return
        
        self.running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Backup scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        
        while self.running:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Check each schedule
                for service_name, schedule in self.schedules.items():
                    if not schedule.enabled:
                        continue
                    
                    if schedule.next_run and current_time >= schedule.next_run:
                        # Time to run backup
                        asyncio.create_task(self._run_scheduled_backup(schedule))
                
                # Sleep for 60 seconds before next check
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    async def _run_scheduled_backup(self, schedule: ScheduledBackup):
        """Run a scheduled backup"""
        
        logger.info(f"Running scheduled {schedule.backup_type.value} backup for {schedule.service_name}")
        
        try:
            # Create backup
            result = await self.backup_manager.create_backup(
                schedule.service_name,
                schedule.backup_type,
                {
                    "scheduled": True,
                    "cron_expression": schedule.cron_expression,
                    "run_count": schedule.run_count + 1
                }
            )
            
            # Update schedule statistics
            schedule.last_run = datetime.now(timezone.utc)
            schedule.run_count += 1
            
            if result['status'] == 'completed':
                schedule.failure_count = 0  # Reset failure count on success
                logger.info(f"Scheduled backup completed for {schedule.service_name}")
            else:
                schedule.failure_count += 1
                logger.error(f"Scheduled backup failed for {schedule.service_name}: {result.get('error')}")
            
        except Exception as e:
            schedule.failure_count += 1
            logger.error(f"Scheduled backup error for {schedule.service_name}: {e}")
        
        # Disable schedule if too many failures
        if schedule.failure_count >= schedule.max_failures:
            schedule.enabled = False
            logger.error(f"Disabling schedule for {schedule.service_name} due to repeated failures")
        
        # Update next run time
        self._update_next_run_time(schedule)
    
    def add_schedule(self, service_name: str, cron_expression: str, 
                    backup_type: BackupType = BackupType.FULL,
                    enabled: bool = True) -> bool:
        """Add a new backup schedule"""
        
        try:
            # Validate cron expression
            croniter(cron_expression)
            
            schedule = ScheduledBackup(
                service_name=service_name,
                cron_expression=cron_expression,
                backup_type=backup_type,
                enabled=enabled
            )
            
            self._update_next_run_time(schedule)
            self.schedules[service_name] = schedule
            
            logger.info(f"Added backup schedule for {service_name}: {cron_expression}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add schedule for {service_name}: {e}")
            return False
    
    def remove_schedule(self, service_name: str) -> bool:
        """Remove a backup schedule"""
        
        if service_name in self.schedules:
            del self.schedules[service_name]
            logger.info(f"Removed backup schedule for {service_name}")
            return True
        
        return False
    
    def enable_schedule(self, service_name: str) -> bool:
        """Enable a backup schedule"""
        
        if service_name in self.schedules:
            schedule = self.schedules[service_name]
            schedule.enabled = True
            schedule.failure_count = 0  # Reset failure count
            self._update_next_run_time(schedule)
            
            logger.info(f"Enabled backup schedule for {service_name}")
            return True
        
        return False
    
    def disable_schedule(self, service_name: str) -> bool:
        """Disable a backup schedule"""
        
        if service_name in self.schedules:
            self.schedules[service_name].enabled = False
            logger.info(f"Disabled backup schedule for {service_name}")
            return True
        
        return False
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """Get status of all schedules"""
        
        status = {
            "scheduler_running": self.running,
            "schedules": {},
            "summary": {
                "total": len(self.schedules),
                "enabled": sum(1 for s in self.schedules.values() if s.enabled),
                "disabled": sum(1 for s in self.schedules.values() if not s.enabled)
            }
        }
        
        for service_name, schedule in self.schedules.items():
            status["schedules"][service_name] = {
                "enabled": schedule.enabled,
                "cron_expression": schedule.cron_expression,
                "backup_type": schedule.backup_type.value,
                "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "run_count": schedule.run_count,
                "failure_count": schedule.failure_count,
                "max_failures": schedule.max_failures
            }
        
        return status
    
    async def run_manual_backup(self, service_name: str, 
                              backup_type: BackupType = BackupType.FULL) -> Dict[str, Any]:
        """Run a manual backup outside of schedule"""
        
        logger.info(f"Running manual {backup_type.value} backup for {service_name}")
        
        try:
            result = await self.backup_manager.create_backup(
                service_name,
                backup_type,
                {
                    "manual": True,
                    "triggered_by": "admin"
                }
            )
            
            logger.info(f"Manual backup completed for {service_name}")
            return result
            
        except Exception as e:
            logger.error(f"Manual backup failed for {service_name}: {e}")
            raise
    
    async def run_emergency_backup(self) -> Dict[str, Any]:
        """Run emergency backup of all services"""
        
        logger.warning("Running emergency backup of all services")
        
        return await self.backup_manager.create_full_backup({
            "emergency": True,
            "triggered_by": "system",
            "description": "Emergency backup triggered"
        })
    
    def get_next_scheduled_backup(self) -> Optional[Dict[str, Any]]:
        """Get information about the next scheduled backup"""
        
        next_backup = None
        next_time = None
        
        for service_name, schedule in self.schedules.items():
            if schedule.enabled and schedule.next_run:
                if next_time is None or schedule.next_run < next_time:
                    next_time = schedule.next_run
                    next_backup = {
                        "service_name": service_name,
                        "backup_type": schedule.backup_type.value,
                        "scheduled_time": schedule.next_run.isoformat(),
                        "cron_expression": schedule.cron_expression
                    }
        
        return next_backup
    
    async def test_all_schedules(self) -> Dict[str, Any]:
        """Test all backup schedules"""
        
        logger.info("Testing all backup schedules")
        
        test_results = {}
        
        for service_name in self.schedules:
            try:
                result = await self.backup_manager.test_backup_and_restore(service_name)
                test_results[service_name] = result
                
            except Exception as e:
                test_results[service_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Summary
        successful = sum(1 for r in test_results.values() if r.get('success', False))
        total = len(test_results)
        
        summary = {
            "total_tested": total,
            "successful": successful,
            "failed": total - successful,
            "results": test_results,
            "overall_success": successful == total
        }
        
        logger.info(f"Schedule testing completed: {successful}/{total} successful")
        
        return summary