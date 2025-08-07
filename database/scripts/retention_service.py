#!/usr/bin/env python3
"""
JARVIS AI - Database Retention Service
Automated data archiving and retention policy management
"""

import asyncio
import logging
import os
import json
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

import asyncpg
import redis.asyncio as aioredis
import structlog
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "memory-db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "jarvis_memory")
POSTGRES_USER = os.getenv("POSTGRES_USER", "jarvis")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "jarvis_secure_2024")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
RETENTION_SCHEDULE = os.getenv("RETENTION_SCHEDULE", "0 5 * * *")  # Daily at 5 AM
ARCHIVE_PATH = os.getenv("ARCHIVE_PATH", "/app/archives")

# Retention policies (in days)
RETENTION_POLICIES = {
    "conversations": 90,      # Keep conversations for 90 days
    "memory_entries": 180,    # Keep memory entries for 6 months
    "system_logs": 30,        # Keep system logs for 30 days
    "user_sessions": 7,       # Keep user sessions for 7 days
    "metrics": 60,            # Keep metrics for 60 days
    "audio_files": 14,        # Keep audio files for 14 days
    "cache_entries": 1,       # Keep cache entries for 1 day
}

# Pydantic models
class RetentionJob(BaseModel):
    job_id: str
    table_name: str
    retention_days: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    records_archived: int = 0
    records_deleted: int = 0
    status: str = "running"
    error: Optional[str] = None

class RetentionReport(BaseModel):
    timestamp: datetime
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    total_records_processed: int
    total_records_archived: int
    total_records_deleted: int
    space_freed_mb: float
    duration_seconds: float
    jobs: List[RetentionJob]

# Global state
postgres_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[aioredis.Redis] = None
scheduler: Optional[AsyncIOScheduler] = None
current_jobs: List[RetentionJob] = []

async def initialize_connections():
    """Initialize database connections"""
    global postgres_pool, redis_client
    
    try:
        # Initialize PostgreSQL connection pool
        postgres_pool = await asyncpg.create_pool(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            min_size=1,
            max_size=3
        )
        
        # Initialize Redis connection
        redis_client = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True
        )
        
        logger.info("Database connections initialized")
        
    except Exception as e:
        logger.error("Failed to initialize database connections", error=str(e))
        raise

async def setup_scheduler():
    """Setup the retention scheduler"""
    global scheduler
    
    scheduler = AsyncIOScheduler()
    
    # Add retention job
    scheduler.add_job(
        run_retention_cycle,
        CronTrigger.from_crontab(RETENTION_SCHEDULE),
        id="retention_cycle",
        name="Data Retention Cycle",
        replace_existing=True
    )
    
    # Start scheduler
    scheduler.start()
    logger.info("Retention scheduler started", schedule=RETENTION_SCHEDULE)

async def run_retention_cycle():
    """Run a complete retention cycle"""
    global current_jobs
    
    start_time = datetime.utcnow()
    current_jobs = []
    
    logger.info("Starting retention cycle")
    
    try:
        # Create archive directory if it doesn't exist
        Path(ARCHIVE_PATH).mkdir(parents=True, exist_ok=True)
        
        # Process each table with retention policy
        for table_name, retention_days in RETENTION_POLICIES.items():
            job = RetentionJob(
                job_id=f"retention_{table_name}_{int(start_time.timestamp())}",
                table_name=table_name,
                retention_days=retention_days,
                started_at=start_time
            )
            current_jobs.append(job)
            
            try:
                await process_table_retention(job)
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                
            except Exception as e:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.utcnow()
                logger.error("Retention job failed", table=table_name, error=str(e))
        
        # Generate report
        duration = (datetime.utcnow() - start_time).total_seconds()
        successful_jobs = len([j for j in current_jobs if j.status == "completed"])
        failed_jobs = len([j for j in current_jobs if j.status == "failed"])
        
        report = RetentionReport(
            timestamp=datetime.utcnow(),
            total_jobs=len(current_jobs),
            successful_jobs=successful_jobs,
            failed_jobs=failed_jobs,
            total_records_processed=sum(j.records_processed for j in current_jobs),
            total_records_archived=sum(j.records_archived for j in current_jobs),
            total_records_deleted=sum(j.records_deleted for j in current_jobs),
            space_freed_mb=await calculate_space_freed(),
            duration_seconds=duration,
            jobs=current_jobs
        )
        
        # Store report
        await store_retention_report(report)
        
        logger.info(
            "Retention cycle completed",
            duration_seconds=duration,
            successful_jobs=successful_jobs,
            failed_jobs=failed_jobs,
            records_processed=report.total_records_processed
        )
        
    except Exception as e:
        logger.error("Retention cycle failed", error=str(e))

async def process_table_retention(job: RetentionJob):
    """Process retention for a specific table"""
    table_name = job.table_name
    retention_days = job.retention_days
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    logger.info("Processing table retention", table=table_name, retention_days=retention_days)
    
    async with postgres_pool.acquire() as conn:
        # Check if table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = $1
            )
        """, table_name)
        
        if not table_exists:
            logger.warning("Table does not exist", table=table_name)
            return
        
        # Get table schema for archiving
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        
        # Determine date column to use for retention
        date_column = await determine_date_column(conn, table_name)
        if not date_column:
            logger.warning("No date column found for retention", table=table_name)
            return
        
        # Count records to be archived
        records_query = f"""
            SELECT COUNT(*) FROM {table_name} 
            WHERE {date_column} < $1
        """
        records_count = await conn.fetchval(records_query, cutoff_date)
        
        if records_count == 0:
            logger.info("No records to archive", table=table_name)
            return
        
        job.records_processed = records_count
        
        # Archive records
        if records_count > 0:
            archived_count = await archive_records(conn, job, cutoff_date, date_column)
            job.records_archived = archived_count
            
            # Delete archived records
            deleted_count = await delete_archived_records(conn, job, cutoff_date, date_column)
            job.records_deleted = deleted_count
        
        logger.info(
            "Table retention completed",
            table=table_name,
            processed=job.records_processed,
            archived=job.records_archived,
            deleted=job.records_deleted
        )

async def determine_date_column(conn: asyncpg.Connection, table_name: str) -> Optional[str]:
    """Determine which date column to use for retention"""
    # Common date column names to look for
    date_columns = ['created_at', 'updated_at', 'timestamp', 'date', 'created', 'modified']
    
    for col_name in date_columns:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = $1 
                AND column_name = $2
                AND data_type IN ('timestamp', 'timestamp with time zone', 'date')
            )
        """, table_name, col_name)
        
        if exists:
            return col_name
    
    return None

async def archive_records(conn: asyncpg.Connection, job: RetentionJob, cutoff_date: datetime, date_column: str) -> int:
    """Archive records to compressed JSON files"""
    table_name = job.table_name
    
    # Fetch records to archive
    records_query = f"""
        SELECT * FROM {table_name} 
        WHERE {date_column} < $1
        ORDER BY {date_column}
    """
    
    records = await conn.fetch(records_query, cutoff_date)
    
    if not records:
        return 0
    
    # Create archive file
    archive_date = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    archive_filename = f"{table_name}_{archive_date}.json.gz"
    archive_path = Path(ARCHIVE_PATH) / archive_filename
    
    # Convert records to JSON format
    json_records = []
    for record in records:
        record_dict = dict(record)
        
        # Convert datetime objects to ISO strings
        for key, value in record_dict.items():
            if isinstance(value, datetime):
                record_dict[key] = value.isoformat()
        
        json_records.append(record_dict)
    
    # Write compressed archive
    with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
        json.dump({
            'table': table_name,
            'archived_at': datetime.utcnow().isoformat(),
            'cutoff_date': cutoff_date.isoformat(),
            'record_count': len(json_records),
            'records': json_records
        }, f, indent=2)
    
    logger.info("Records archived", table=table_name, count=len(records), file=archive_filename)
    
    return len(records)

async def delete_archived_records(conn: asyncpg.Connection, job: RetentionJob, cutoff_date: datetime, date_column: str) -> int:
    """Delete records that have been archived"""
    table_name = job.table_name
    
    delete_query = f"""
        DELETE FROM {table_name} 
        WHERE {date_column} < $1
    """
    
    result = await conn.execute(delete_query, cutoff_date)
    
    # Extract count from result string (e.g., "DELETE 123")
    deleted_count = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
    
    logger.info("Records deleted", table=table_name, count=deleted_count)
    
    return deleted_count

async def calculate_space_freed() -> float:
    """Calculate space freed by retention process (approximate)"""
    try:
        # This is a rough estimate based on record counts
        # In production, you might want to measure actual disk space
        total_deleted = sum(j.records_deleted for j in current_jobs)
        
        # Estimate ~1KB per record on average
        estimated_bytes = total_deleted * 1024
        estimated_mb = estimated_bytes / (1024 * 1024)
        
        return estimated_mb
        
    except Exception:
        return 0.0

async def store_retention_report(report: RetentionReport):
    """Store retention report for monitoring"""
    try:
        # Store in Redis for quick access
        report_key = f"retention_report:{report.timestamp.strftime('%Y%m%d_%H%M%S')}"
        await redis_client.setex(
            report_key,
            timedelta(days=30).total_seconds(),
            json.dumps(report.dict(), default=str)
        )
        
        # Keep only last 10 reports
        await redis_client.ltrim("retention_reports", 0, 9)
        await redis_client.lpush("retention_reports", report_key)
        
        # Also save to file
        report_file = Path(ARCHIVE_PATH) / f"retention_report_{report.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report.dict(), f, indent=2, default=str)
        
        logger.info("Retention report stored", report_key=report_key)
        
    except Exception as e:
        logger.error("Failed to store retention report", error=str(e))

async def cleanup_old_archives():
    """Clean up old archive files"""
    try:
        archive_path = Path(ARCHIVE_PATH)
        if not archive_path.exists():
            return
        
        # Remove archives older than 1 year
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        
        for archive_file in archive_path.glob("*.json.gz"):
            if archive_file.stat().st_mtime < cutoff_date.timestamp():
                archive_file.unlink()
                logger.info("Old archive deleted", file=archive_file.name)
        
    except Exception as e:
        logger.error("Archive cleanup failed", error=str(e))

async def main_service():
    """Main service loop"""
    try:
        await initialize_connections()
        await setup_scheduler()
        
        logger.info("Retention service started", policies=RETENTION_POLICIES)
        
        # Keep the service running
        while True:
            await asyncio.sleep(60)
            
            # Periodic cleanup of old archives
            if datetime.utcnow().hour == 6 and datetime.utcnow().minute == 0:
                await cleanup_old_archives()
    
    except KeyboardInterrupt:
        logger.info("Retention service stopping")
    except Exception as e:
        logger.error("Retention service error", error=str(e))
        raise
    finally:
        # Cleanup
        if scheduler:
            scheduler.shutdown()
        if postgres_pool:
            await postgres_pool.close()
        if redis_client:
            await redis_client.close()

def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(main_service())
    except KeyboardInterrupt:
        logger.info("Retention service stopped by user")
    except Exception as e:
        logger.error("Retention service failed", error=str(e))
        raise

if __name__ == "__main__":
    main()