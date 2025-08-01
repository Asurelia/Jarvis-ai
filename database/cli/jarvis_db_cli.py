"""
JARVIS Database Management CLI
Complete command-line interface for database operations
"""

import asyncio
import click
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.backup.backup_manager import BackupManager
from database.backup.backup_scheduler import BackupScheduler
from database.backup.base_backup import BackupType
from database.retention.retention_manager import RetentionManager
from database.retention.retention_policies import DataCategory, RetentionPolicyBuilder
from database.monitoring.health_monitor import HealthMonitor
from config.settings import settings

# CLI Configuration
CONFIG_FILE = Path.home() / ".jarvis" / "db_config.json"

def load_config() -> Dict[str, Any]:
    """Load CLI configuration"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    
    # Default configuration
    return {
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
        }
    }

def save_config(config: Dict[str, Any]):
    """Save CLI configuration"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# Main CLI group
@click.group()
@click.version_option(version="1.0.0")
@click.pass_context
def cli(ctx):
    """JARVIS Database Management CLI
    
    Comprehensive tool for managing JARVIS AI database backups, 
    migrations, monitoring, and maintenance.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config()

# Backup commands
@cli.group()
def backup():
    """Database backup operations"""
    pass

@backup.command()
@click.option('--service', type=click.Choice(['postgresql', 'redis', 'chromadb', 'all']), default='all')
@click.option('--type', 'backup_type', type=click.Choice(['full', 'incremental']), default='full')
@click.option('--output', help='Output directory for backups')
@click.pass_context
def create(ctx, service, backup_type, output):
    """Create database backup"""
    config = ctx.obj['config']
    
    if output:
        config['backup_dir'] = output
    
    async def run_backup():
        backup_manager = BackupManager(
            backup_root_dir=Path(config['backup_dir']),
            config=config['services']
        )
        
        try:
            backup_type_enum = BackupType.FULL if backup_type == 'full' else BackupType.INCREMENTAL
            
            if service == 'all':
                click.echo("Creating full system backup...")
                result = await backup_manager.create_full_backup({
                    "triggered_by": "cli",
                    "backup_type": backup_type
                })
                
                click.echo(f"Backup completed:")
                click.echo(f"  - Total services: {result['total_services']}")
                click.echo(f"  - Successful: {result['successful']}")
                click.echo(f"  - Failed: {result['failed']}")
                
                if result['errors']:
                    click.echo("Errors:")
                    for error in result['errors']:
                        click.echo(f"  - {error}")
            
            else:
                click.echo(f"Creating {backup_type} backup for {service}...")
                result = await backup_manager.create_backup(
                    service, 
                    backup_type_enum,
                    {"triggered_by": "cli"}
                )
                
                if result['status'] == 'completed':
                    click.echo(f"✅ Backup completed: {result['backup_path']}")
                    click.echo(f"   Size: {result.get('file_size', 0):,} bytes")
                    if 'checksum' in result:
                        click.echo(f"   Checksum: {result['checksum']}")
                else:
                    click.echo(f"❌ Backup failed: {result.get('error', 'Unknown error')}")
                    sys.exit(1)
        
        finally:
            await backup_manager.close()
    
    asyncio.run(run_backup())

@backup.command()
@click.option('--service', type=click.Choice(['postgresql', 'redis', 'chromadb']), required=True)
@click.argument('backup_path', type=click.Path(exists=True))
@click.option('--target', help='Target location for restore')
@click.pass_context
def restore(ctx, service, backup_path, target):
    """Restore from backup"""
    config = ctx.obj['config']
    
    async def run_restore():
        backup_manager = BackupManager(
            backup_root_dir=Path(config['backup_dir']),
            config=config['services']
        )
        
        try:
            click.echo(f"Restoring {service} from {backup_path}...")
            
            # Confirm restore operation
            if not click.confirm(f"⚠️  This will restore {service} from backup. Continue?"):
                click.echo("Restore cancelled.")
                return
            
            success = await backup_manager.restore_backup(
                service,
                Path(backup_path),
                target
            )
            
            if success:
                click.echo(f"✅ Restore completed successfully")
            else:
                click.echo(f"❌ Restore failed")
                sys.exit(1)
        
        finally:
            await backup_manager.close()
    
    asyncio.run(run_restore())

@backup.command()
@click.option('--service', type=click.Choice(['postgresql', 'redis', 'chromadb']))
@click.pass_context
def list(ctx, service):
    """List available backups"""
    config = ctx.obj['config']
    
    async def run_list():
        backup_manager = BackupManager(
            backup_root_dir=Path(config['backup_dir']),
            config=config['services']
        )
        
        try:
            backups = await backup_manager.list_backups(service)
            
            if not backups:
                click.echo("No backups found.")
                return
            
            for service_name, service_backups in backups.items():
                click.echo(f"\n📁 {service_name.upper()} Backups:")
                click.echo("-" * 50)
                
                if not service_backups:
                    click.echo("  No backups found")
                    continue
                
                for backup in service_backups:
                    size_mb = backup['size'] / (1024 * 1024)
                    created_at = backup['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    click.echo(f"  📄 {backup['filename']}")
                    click.echo(f"     Type: {backup['backup_type']}")
                    click.echo(f"     Size: {size_mb:.1f} MB")
                    click.echo(f"     Created: {created_at}")
                    if backup.get('checksum'):
                        click.echo(f"     Checksum: {backup['checksum'][:16]}...")
                    click.echo()
        
        finally:
            await backup_manager.close()
    
    asyncio.run(run_list())

@backup.command()
@click.option('--service', type=click.Choice(['postgresql', 'redis', 'chromadb']), required=True)
@click.argument('backup_path', type=click.Path(exists=True))
@click.pass_context
def verify(ctx, service, backup_path):
    """Verify backup integrity"""
    config = ctx.obj['config']
    
    async def run_verify():
        backup_manager = BackupManager(
            backup_root_dir=Path(config['backup_dir']),
            config=config['services']
        )
        
        try:
            click.echo(f"Verifying {service} backup: {backup_path}")
            
            verified = await backup_manager.verify_backup(service, Path(backup_path))
            
            if verified:
                click.echo("✅ Backup verification successful")
            else:
                click.echo("❌ Backup verification failed")
                sys.exit(1)
        
        finally:
            await backup_manager.close()
    
    asyncio.run(run_verify())

# Scheduler commands
@cli.group()
def schedule():
    """Backup scheduling operations"""
    pass

@schedule.command()
@click.pass_context
def status(ctx):
    """Show backup schedule status"""
    config = ctx.obj['config']
    
    async def run_status():
        backup_manager = BackupManager(
            backup_root_dir=Path(config['backup_dir']),
            config=config['services']
        )
        
        scheduler = BackupScheduler(backup_manager)
        
        try:
            status_info = scheduler.get_schedule_status()
            
            click.echo("📅 Backup Schedule Status")
            click.echo("=" * 50)
            click.echo(f"Scheduler Running: {'✅ Yes' if status_info['scheduler_running'] else '❌ No'}")
            click.echo(f"Total Schedules: {status_info['summary']['total']}")
            click.echo(f"Enabled: {status_info['summary']['enabled']}")
            click.echo(f"Disabled: {status_info['summary']['disabled']}")
            
            click.echo("\n📋 Schedule Details:")
            click.echo("-" * 30)
            
            for service, schedule_info in status_info['schedules'].items():
                status_icon = "✅" if schedule_info['enabled'] else "❌"
                click.echo(f"{status_icon} {service.upper()}")
                click.echo(f"   Cron: {schedule_info['cron_expression']}")
                click.echo(f"   Type: {schedule_info['backup_type']}")
                click.echo(f"   Last Run: {schedule_info.get('last_run', 'Never')}")
                click.echo(f"   Next Run: {schedule_info.get('next_run', 'Not scheduled')}")
                click.echo(f"   Run Count: {schedule_info['run_count']}")
                click.echo(f"   Failures: {schedule_info['failure_count']}/{schedule_info['max_failures']}")
                click.echo()
            
            # Show next backup
            next_backup = scheduler.get_next_scheduled_backup()
            if next_backup:
                click.echo(f"⏰ Next Backup: {next_backup['service_name']} at {next_backup['scheduled_time']}")
        
        finally:
            await backup_manager.close()
    
    asyncio.run(run_status())

@schedule.command()
@click.pass_context
def start(ctx):
    """Start backup scheduler"""
    config = ctx.obj['config']
    
    async def run_scheduler():
        backup_manager = BackupManager(
            backup_root_dir=Path(config['backup_dir']),
            config=config['services']
        )
        
        scheduler = BackupScheduler(backup_manager)
        
        try:
            click.echo("🚀 Starting backup scheduler...")
            await scheduler.start()
            
            click.echo("✅ Backup scheduler started successfully")
            click.echo("Press Ctrl+C to stop...")
            
            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(60)
                    
                    # Show next backup info periodically
                    next_backup = scheduler.get_next_scheduled_backup()
                    if next_backup:
                        click.echo(f"⏰ Next: {next_backup['service_name']} at {next_backup['scheduled_time']}")
            
            except KeyboardInterrupt:
                click.echo("\n🛑 Stopping scheduler...")
                await scheduler.stop()
                click.echo("✅ Scheduler stopped")
        
        finally:
            await backup_manager.close()
    
    asyncio.run(run_scheduler())

# Health monitoring commands
@cli.group()
def health():
    """Database health monitoring"""
    pass

@health.command()
@click.option('--json-output', is_flag=True, help='Output as JSON')
@click.pass_context
def check(ctx, json_output):
    """Run health check"""
    config = ctx.obj['config']
    
    async def run_health_check():
        monitor = HealthMonitor(config)
        
        report = await monitor.run_full_health_check()
        
        if json_output:
            click.echo(json.dumps(report, indent=2, default=str))
            return
        
        # Format human-readable output
        overall_status = report['overall_status']
        status_icon = {"healthy": "✅", "warning": "⚠️", "critical": "❌"}.get(overall_status, "❓")
        
        click.echo(f"🏥 JARVIS Database Health Check")
        click.echo("=" * 50)
        click.echo(f"Overall Status: {status_icon} {overall_status.upper()}")
        click.echo(f"Timestamp: {report['timestamp']}")
        click.echo(f"Checks: {report['summary']['healthy']}/{report['summary']['total_checks']} healthy")
        
        if report['summary']['warnings'] > 0:
            click.echo(f"Warnings: {report['summary']['warnings']}")
        
        if report['summary']['critical'] > 0:
            click.echo(f"Critical Issues: {report['summary']['critical']}")
        
        # Show service details
        click.echo("\n📊 Service Status:")
        click.echo("-" * 30)
        
        for service_name, service_data in report['services'].items():
            status = service_data['status']
            status_icon = {"healthy": "✅", "warning": "⚠️", "critical": "❌"}.get(status, "❓")
            
            click.echo(f"{status_icon} {service_name.upper()}: {service_data['message']}")
            
            # Show key metrics
            metrics = service_data.get('metrics', {})
            if 'database_size_mb' in metrics:
                click.echo(f"   Database Size: {metrics['database_size_mb']:.1f} MB")
            if 'used_memory_human' in metrics:
                click.echo(f"   Memory Usage: {metrics['used_memory_human']}")
            if 'connection_usage_percent' in metrics:
                click.echo(f"   Connections: {metrics['connection_usage_percent']:.1f}%")
        
        # Show system status
        if 'system' in report:
            system_data = report['system']
            status = system_data['status']
            status_icon = {"healthy": "✅", "warning": "⚠️", "critical": "❌"}.get(status, "❓")
            
            click.echo(f"\n🖥️  System Status:")
            click.echo(f"{status_icon} {system_data['message']}")
            
            metrics = system_data.get('metrics', {})
            if 'cpu_usage_percent' in metrics:
                click.echo(f"   CPU Usage: {metrics['cpu_usage_percent']:.1f}%")
            if 'memory_usage_percent' in metrics:
                click.echo(f"   Memory Usage: {metrics['memory_usage_percent']:.1f}%")
            if 'disk_usage_percent' in metrics:
                click.echo(f"   Disk Usage: {metrics['disk_usage_percent']:.1f}%")
    
    asyncio.run(run_health_check())

# Retention commands
@cli.group()
def retention():
    """Data retention management"""
    pass

@retention.command()
@click.option('--category', type=click.Choice([c.value for c in DataCategory]), help='Specific category to clean')
@click.option('--dry-run', is_flag=True, help='Preview without executing')
@click.pass_context
def cleanup(ctx, category, dry_run):
    """Execute data retention policies"""
    config = ctx.obj['config']
    
    async def run_cleanup():
        retention_manager = RetentionManager(
            database_url=config['database_url'],
            archive_dir=Path(config['archive_dir'])
        )
        
        try:
            if category:
                category_enum = DataCategory(category)
                
                if dry_run:
                    click.echo(f"🔍 Previewing retention policy for {category}...")
                    preview = await retention_manager.preview_policy_execution(category_enum)
                    
                    click.echo(f"Policy: {preview['policy']}")
                    click.echo(f"Table: {preview['table']}")
                    click.echo("Rules:")
                    
                    for rule in preview['rules']:
                        click.echo(f"  - {rule['rule_name']}: {rule['action']} ({rule['affected_records']} records)")
                
                else:
                    click.echo(f"🧹 Executing retention policy for {category}...")
                    result = await retention_manager.execute_policy_for_category(category_enum)
                    
                    if result['success']:
                        click.echo(f"✅ Policy executed successfully")
                        click.echo(f"   Rules executed: {result['rules_executed']}")
                        click.echo(f"   Records processed: {result['total_processed']}")
                        click.echo(f"   Archived: {result['archived']}")
                        click.echo(f"   Deleted: {result['deleted']}")
                    else:
                        click.echo(f"❌ Policy execution failed")
                        for error in result.get('errors', []):
                            click.echo(f"   Error: {error}")
            
            else:
                if dry_run:
                    click.echo("🔍 Previewing all retention policies...")
                    for cat in DataCategory:
                        try:
                            preview = await retention_manager.preview_policy_execution(cat)
                            total_affected = sum(rule['affected_records'] for rule in preview['rules'])
                            
                            if total_affected > 0:
                                click.echo(f"\n{cat.value}: {total_affected} records affected")
                                for rule in preview['rules']:
                                    if rule['affected_records'] > 0:
                                        click.echo(f"  - {rule['rule_name']}: {rule['action']} ({rule['affected_records']} records)")
                        except Exception as e:
                            click.echo(f"{cat.value}: Error - {e}")
                
                else:
                    click.echo("🧹 Executing all retention policies...")
                    result = await retention_manager.execute_all_policies()
                    
                    click.echo(f"Execution completed:")
                    click.echo(f"  - Duration: {result['execution_time_seconds']:.1f} seconds")
                    click.echo(f"  - Successful policies: {result['successful_policies']}/{result['total_policies']}")
                    click.echo(f"  - Records processed: {result['total_records_processed']}")
                    click.echo(f"  - Errors: {result['total_errors']}")
                    
                    if result['total_errors'] > 0:
                        click.echo("\nErrors occurred:")
                        for policy_name, policy_result in result['policy_results'].items():
                            for error in policy_result.get('errors', []):
                                click.echo(f"  - {policy_name}: {error}")
        
        except Exception as e:
            click.echo(f"❌ Retention cleanup failed: {e}")
            sys.exit(1)
    
    asyncio.run(run_cleanup())

@retention.command()
@click.pass_context
def stats(ctx):
    """Show retention statistics"""
    config = ctx.obj['config']
    
    async def run_stats():
        retention_manager = RetentionManager(
            database_url=config['database_url'],
            archive_dir=Path(config['archive_dir'])
        )
        
        try:
            stats = await retention_manager.get_retention_stats()
            
            click.echo("📊 Data Retention Statistics")
            click.echo("=" * 50)
            click.echo(f"Generated: {stats['timestamp']}")
            
            click.echo("\n📋 Table Statistics:")
            click.echo("-" * 30)
            
            for table_name, table_stats in stats['tables'].items():
                if 'error' in table_stats:
                    click.echo(f"❌ {table_name}: {table_stats['error']}")
                    continue
                
                status_icon = "✅" if table_stats['policy_enabled'] else "❌"
                click.echo(f"{status_icon} {table_name.upper()}")
                click.echo(f"   Category: {table_stats['category']}")
                click.echo(f"   Records: {table_stats['total_records']:,}")
                click.echo(f"   Size: {table_stats['table_size']}")
                
                if table_stats['oldest_record']:
                    click.echo(f"   Oldest: {table_stats['oldest_record']}")
                if table_stats['newest_record']:
                    click.echo(f"   Newest: {table_stats['newest_record']}")
                
                click.echo(f"   Policy: {'Enabled' if table_stats['policy_enabled'] else 'Disabled'}")
                click.echo()
        
        except Exception as e:
            click.echo(f"❌ Failed to get retention stats: {e}")
            sys.exit(1)
    
    asyncio.run(run_stats())

# Configuration commands
@cli.group()
def config():
    """Configuration management"""
    pass

@config.command()
@click.pass_context
def show(ctx):
    """Show current configuration"""
    config = ctx.obj['config']
    click.echo(json.dumps(config, indent=2))

@config.command()
@click.option('--backup-dir', help='Backup directory path')
@click.option('--archive-dir', help='Archive directory path')
@click.pass_context
def set(ctx, backup_dir, archive_dir):
    """Update configuration"""
    config = ctx.obj['config']
    
    if backup_dir:
        config['backup_dir'] = backup_dir
    
    if archive_dir:
        config['archive_dir'] = archive_dir
    
    save_config(config)
    click.echo("Configuration updated successfully")

if __name__ == '__main__':
    cli()