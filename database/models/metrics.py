"""
Performance metrics and backup logging models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Enum, Boolean
from sqlalchemy.sql import func
from .base import BaseModel
import enum

class MetricType(enum.Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    QUERY_TIME = "query_time"
    API_RESPONSE_TIME = "api_response_time"
    EMBEDDING_TIME = "embedding_time"
    BACKUP_SIZE = "backup_size"
    RESTORE_TIME = "restore_time"

class BackupStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BackupType(enum.Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class PerformanceMetric(BaseModel):
    """Performance metrics tracking"""
    __tablename__ = 'performance_metrics'
    
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(Enum(MetricType), nullable=False)
    metric_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)  # seconds, bytes, percentage, etc.
    
    # Context information
    service_name = Column(String(50), nullable=True)  # brain-api, redis, postgresql, etc.
    operation = Column(String(100), nullable=True)  # specific operation being measured
    metadata = Column(JSON, default=dict)
    
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class BackupLog(BaseModel):
    """Backup operation logging"""
    __tablename__ = 'backup_logs'
    
    backup_type = Column(Enum(BackupType), nullable=False)
    service_name = Column(String(50), nullable=False)  # postgresql, redis, chromadb
    status = Column(Enum(BackupStatus), default=BackupStatus.PENDING, nullable=False)
    
    # Backup details
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    compression_ratio = Column(Float, nullable=True)
    
    # Timing information
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # seconds
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Verification
    checksum = Column(String(64), nullable=True)  # SHA-256 checksum
    verified = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    def mark_completed(self, file_path: str, file_size: int, checksum: str = None):
        """Mark backup as completed"""
        self.status = BackupStatus.COMPLETED
        self.completed_at = func.now()
        self.file_path = file_path
        self.file_size = file_size
        self.checksum = checksum
    
    def mark_failed(self, error_message: str):
        """Mark backup as failed"""
        self.status = BackupStatus.FAILED
        self.completed_at = func.now()
        self.error_message = error_message
        self.retry_count += 1