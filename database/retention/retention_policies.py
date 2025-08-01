"""
Data retention policies for JARVIS AI
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class DataCategory(Enum):
    CONVERSATIONS = "conversations"
    MESSAGES = "messages"
    MEMORY_ENTRIES = "memory_entries"
    PERFORMANCE_METRICS = "performance_metrics"
    BACKUP_LOGS = "backup_logs"
    SESSIONS = "sessions"
    CACHE_DATA = "cache_data"
    LOGS = "logs"
    TEMPORARY_FILES = "temporary_files"

class RetentionAction(Enum):
    DELETE = "delete"
    ARCHIVE = "archive"
    COMPRESS = "compress"
    ANONYMIZE = "anonymize"

@dataclass
class RetentionRule:
    """Individual retention rule"""
    name: str
    condition: str  # SQL-like condition
    action: RetentionAction
    params: Dict[str, Any] = None
    enabled: bool = True
    priority: int = 0  # Higher priority rules run first

@dataclass
class RetentionPolicy:
    """Complete retention policy for a data category"""
    category: DataCategory
    table_name: str
    enabled: bool = True
    rules: List[RetentionRule] = None
    default_retention_days: int = 365
    archive_after_days: int = 90
    delete_after_days: int = 730
    max_records: Optional[int] = None
    
    def __post_init__(self):
        if self.rules is None:
            self.rules = []

class RetentionPolicyBuilder:
    """Builder for creating retention policies"""
    
    @staticmethod
    def get_default_policies() -> Dict[DataCategory, RetentionPolicy]:
        """Get default retention policies for all data categories"""
        
        policies = {}
        
        # Conversations retention
        conversation_rules = [
            RetentionRule(
                name="archive_old_conversations",
                condition="created_at < NOW() - INTERVAL '90 days' AND status = 'active'",
                action=RetentionAction.ARCHIVE,
                priority=1
            ),
            RetentionRule(
                name="delete_archived_conversations",
                condition="created_at < NOW() - INTERVAL '2 years' AND status = 'archived'",
                action=RetentionAction.DELETE,
                priority=2
            ),
            RetentionRule(
                name="delete_deleted_conversations",
                condition="created_at < NOW() - INTERVAL '30 days' AND status = 'deleted'",
                action=RetentionAction.DELETE,
                priority=3
            )
        ]
        
        policies[DataCategory.CONVERSATIONS] = RetentionPolicy(
            category=DataCategory.CONVERSATIONS,
            table_name="conversations",
            rules=conversation_rules,
            archive_after_days=90,
            delete_after_days=730
        )
        
        # Messages retention
        message_rules = [
            RetentionRule(
                name="archive_old_messages",
                condition="created_at < NOW() - INTERVAL '90 days'",
                action=RetentionAction.ARCHIVE,
                priority=1
            ),
            RetentionRule(
                name="delete_very_old_messages",
                condition="created_at < NOW() - INTERVAL '2 years'",
                action=RetentionAction.DELETE,
                priority=2
            )
        ]
        
        policies[DataCategory.MESSAGES] = RetentionPolicy(
            category=DataCategory.MESSAGES,
            table_name="messages",
            rules=message_rules,
            archive_after_days=90,
            delete_after_days=730
        )
        
        # Memory entries retention
        memory_rules = [
            RetentionRule(
                name="delete_low_importance_old_memories",
                condition="created_at < NOW() - INTERVAL '30 days' AND importance_score < 0.2 AND access_count = 0",
                action=RetentionAction.DELETE,
                priority=1
            ),
            RetentionRule(
                name="archive_unused_memories",
                condition="last_accessed < NOW() - INTERVAL '180 days' AND importance_score < 0.5",
                action=RetentionAction.ARCHIVE,
                priority=2
            ),
            RetentionRule(
                name="compress_old_memories",
                condition="created_at < NOW() - INTERVAL '1 year' AND importance_score >= 0.5",
                action=RetentionAction.COMPRESS,
                priority=3
            )
        ]
        
        policies[DataCategory.MEMORY_ENTRIES] = RetentionPolicy(
            category=DataCategory.MEMORY_ENTRIES,
            table_name="memory_entries",
            rules=memory_rules,
            archive_after_days=180,
            delete_after_days=365,
            max_records=100000
        )
        
        # Performance metrics retention
        metrics_rules = [
            RetentionRule(
                name="delete_old_metrics",
                condition="recorded_at < NOW() - INTERVAL '30 days'",
                action=RetentionAction.DELETE,
                priority=1
            )
        ]
        
        policies[DataCategory.PERFORMANCE_METRICS] = RetentionPolicy(
            category=DataCategory.PERFORMANCE_METRICS,
            table_name="performance_metrics",
            rules=metrics_rules,
            delete_after_days=30
        )
        
        # Backup logs retention
        backup_rules = [
            RetentionRule(
                name="delete_old_backup_logs",
                condition="created_at < NOW() - INTERVAL '90 days'",
                action=RetentionAction.DELETE,
                priority=1
            )
        ]
        
        policies[DataCategory.BACKUP_LOGS] = RetentionPolicy(
            category=DataCategory.BACKUP_LOGS,
            table_name="backup_logs",
            rules=backup_rules,
            delete_after_days=90
        )
        
        # Sessions retention
        session_rules = [
            RetentionRule(
                name="delete_expired_sessions",
                condition="expires_at < NOW() OR (is_valid = false AND revoked_at < NOW() - INTERVAL '7 days')",
                action=RetentionAction.DELETE,
                priority=1
            ),
            RetentionRule(
                name="delete_old_sessions",
                condition="created_at < NOW() - INTERVAL '30 days'",
                action=RetentionAction.DELETE,
                priority=2
            )
        ]
        
        policies[DataCategory.SESSIONS] = RetentionPolicy(
            category=DataCategory.SESSIONS,
            table_name="sessions",
            rules=session_rules,
            delete_after_days=30
        )
        
        # Cache data retention (Redis/embedding cache)
        cache_rules = [
            RetentionRule(
                name="delete_unused_cache",
                condition="last_accessed < NOW() - INTERVAL '7 days' AND access_count < 3",
                action=RetentionAction.DELETE,
                priority=1
            ),
            RetentionRule(
                name="limit_cache_size",
                condition="access_count > 0",
                action=RetentionAction.DELETE,
                params={"keep_latest": 10000},
                priority=2
            )
        ]
        
        policies[DataCategory.CACHE_DATA] = RetentionPolicy(
            category=DataCategory.CACHE_DATA,
            table_name="embedding_cache",
            rules=cache_rules,
            delete_after_days=7,
            max_records=10000
        )
        
        return policies
    
    @staticmethod
    def create_custom_policy(category: DataCategory, table_name: str,
                           retention_days: int, archive_days: Optional[int] = None,
                           max_records: Optional[int] = None) -> RetentionPolicy:
        """Create a custom retention policy"""
        
        rules = []
        
        # Archive rule if specified
        if archive_days and archive_days < retention_days:
            rules.append(RetentionRule(
                name=f"archive_old_{table_name}",
                condition=f"created_at < NOW() - INTERVAL '{archive_days} days'",
                action=RetentionAction.ARCHIVE,
                priority=1
            ))
        
        # Delete rule
        rules.append(RetentionRule(
            name=f"delete_old_{table_name}",
            condition=f"created_at < NOW() - INTERVAL '{retention_days} days'",
            action=RetentionAction.DELETE,
            priority=2
        ))
        
        # Max records rule if specified
        if max_records:
            rules.append(RetentionRule(
                name=f"limit_{table_name}_records",
                condition="id IS NOT NULL",
                action=RetentionAction.DELETE,
                params={"keep_latest": max_records},
                priority=3
            ))
        
        return RetentionPolicy(
            category=category,
            table_name=table_name,
            rules=rules,
            default_retention_days=retention_days,
            archive_after_days=archive_days,
            delete_after_days=retention_days,
            max_records=max_records
        )
    
    @staticmethod
    def validate_policy(policy: RetentionPolicy) -> List[str]:
        """Validate a retention policy"""
        
        errors = []
        
        if not policy.table_name:
            errors.append("Table name is required")
        
        if policy.delete_after_days <= 0:
            errors.append("Delete after days must be positive")
        
        if policy.archive_after_days and policy.archive_after_days >= policy.delete_after_days:
            errors.append("Archive days must be less than delete days")
        
        if policy.max_records and policy.max_records <= 0:
            errors.append("Max records must be positive")
        
        # Validate rules
        for rule in policy.rules:
            if not rule.name:
                errors.append("Rule name is required")
            
            if not rule.condition:
                errors.append(f"Rule '{rule.name}' condition is required")
        
        return errors