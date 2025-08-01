"""
Data retention manager for JARVIS AI
Executes retention policies and manages data lifecycle
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncpg
import json

from .retention_policies import RetentionPolicy, RetentionRule, RetentionAction, DataCategory, RetentionPolicyBuilder
from .data_archiver import DataArchiver

logger = logging.getLogger(__name__)

class RetentionManager:
    """Manages data retention policies and execution"""
    
    def __init__(self, database_url: str, archive_dir: Path,
                 policies: Optional[Dict[DataCategory, RetentionPolicy]] = None):
        self.database_url = database_url
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Load policies
        self.policies = policies or RetentionPolicyBuilder.get_default_policies()
        
        # Initialize archiver
        self.archiver = DataArchiver(self.archive_dir)
        
        # Statistics
        self.last_run = None
        self.execution_stats = {}
    
    async def execute_all_policies(self) -> Dict[str, Any]:
        """Execute all enabled retention policies"""
        
        logger.info("Starting retention policy execution")
        
        execution_start = datetime.now(timezone.utc)
        results = {}
        total_processed = 0
        total_errors = 0
        
        # Connect to database
        conn = await asyncpg.connect(self.database_url)
        
        try:
            for category, policy in self.policies.items():
                if not policy.enabled:
                    logger.info(f"Skipping disabled policy for {category.value}")
                    continue
                
                try:
                    logger.info(f"Executing retention policy for {category.value}")
                    result = await self._execute_policy(conn, policy)
                    results[category.value] = result
                    
                    total_processed += result.get('total_processed', 0)
                    if result.get('errors'):
                        total_errors += len(result['errors'])
                    
                except Exception as e:
                    logger.error(f"Failed to execute policy for {category.value}: {e}")
                    results[category.value] = {
                        'success': False,
                        'error': str(e),
                        'total_processed': 0
                    }
                    total_errors += 1
        
        finally:
            await conn.close()
        
        execution_end = datetime.now(timezone.utc)
        execution_time = (execution_end - execution_start).total_seconds()
        
        # Summary
        summary = {
            'started_at': execution_start.isoformat(),
            'completed_at': execution_end.isoformat(),
            'execution_time_seconds': execution_time,
            'total_policies': len(self.policies),
            'successful_policies': sum(1 for r in results.values() if r.get('success', False)),
            'total_records_processed': total_processed,
            'total_errors': total_errors,
            'policy_results': results
        }
        
        self.last_run = execution_end
        self.execution_stats = summary
        
        logger.info(f"Retention policy execution completed: "
                   f"{summary['successful_policies']}/{summary['total_policies']} policies, "
                   f"{total_processed} records processed, "
                   f"{total_errors} errors")
        
        return summary
    
    async def _execute_policy(self, conn: asyncpg.Connection, 
                            policy: RetentionPolicy) -> Dict[str, Any]:
        """Execute a single retention policy"""
        
        result = {
            'policy': policy.category.value,
            'table': policy.table_name,
            'success': True,
            'rules_executed': 0,
            'total_processed': 0,
            'archived': 0,
            'deleted': 0,
            'compressed': 0,
            'anonymized': 0,
            'errors': []
        }
        
        # Sort rules by priority (higher priority first)
        sorted_rules = sorted(policy.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if not rule.enabled:
                logger.debug(f"Skipping disabled rule: {rule.name}")
                continue
            
            try:
                logger.debug(f"Executing rule: {rule.name}")
                rule_result = await self._execute_rule(conn, policy, rule)
                
                result['rules_executed'] += 1
                result['total_processed'] += rule_result['processed']
                
                # Update action counters
                if rule.action == RetentionAction.ARCHIVE:
                    result['archived'] += rule_result['processed']
                elif rule.action == RetentionAction.DELETE:
                    result['deleted'] += rule_result['processed']
                elif rule.action == RetentionAction.COMPRESS:
                    result['compressed'] += rule_result['processed']
                elif rule.action == RetentionAction.ANONYMIZE:
                    result['anonymized'] += rule_result['processed']
                
                if rule_result.get('error'):
                    result['errors'].append(f"{rule.name}: {rule_result['error']}")
                
            except Exception as e:
                error_msg = f"Rule '{rule.name}' failed: {e}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                result['success'] = False
        
        return result
    
    async def _execute_rule(self, conn: asyncpg.Connection, 
                          policy: RetentionPolicy, rule: RetentionRule) -> Dict[str, Any]:
        """Execute a single retention rule"""
        
        result = {'processed': 0, 'error': None}
        
        try:
            if rule.action == RetentionAction.DELETE:
                result['processed'] = await self._execute_delete_rule(conn, policy, rule)
            
            elif rule.action == RetentionAction.ARCHIVE:
                result['processed'] = await self._execute_archive_rule(conn, policy, rule)
            
            elif rule.action == RetentionAction.COMPRESS:
                result['processed'] = await self._execute_compress_rule(conn, policy, rule)
            
            elif rule.action == RetentionAction.ANONYMIZE:
                result['processed'] = await self._execute_anonymize_rule(conn, policy, rule)
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Rule execution failed: {e}")
        
        return result
    
    async def _execute_delete_rule(self, conn: asyncpg.Connection,
                                 policy: RetentionPolicy, rule: RetentionRule) -> int:
        """Execute a delete rule"""
        
        # Handle max records limit
        if rule.params and 'keep_latest' in rule.params:
            keep_latest = rule.params['keep_latest']
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM {policy.table_name}"
            total_count = await conn.fetchval(count_query)
            
            if total_count > keep_latest:
                # Delete oldest records beyond the limit
                delete_query = f"""
                DELETE FROM {policy.table_name} 
                WHERE id IN (
                    SELECT id FROM {policy.table_name}
                    ORDER BY created_at DESC
                    OFFSET {keep_latest}
                )
                """
                result = await conn.execute(delete_query)
                return int(result.split()[-1]) if result else 0
            
            return 0
        
        # Regular condition-based delete
        delete_query = f"DELETE FROM {policy.table_name} WHERE {rule.condition}"
        result = await conn.execute(delete_query)
        
        return int(result.split()[-1]) if result else 0
    
    async def _execute_archive_rule(self, conn: asyncpg.Connection,
                                  policy: RetentionPolicy, rule: RetentionRule) -> int:
        """Execute an archive rule"""
        
        # Select records to archive
        select_query = f"SELECT * FROM {policy.table_name} WHERE {rule.condition}"
        records = await conn.fetch(select_query)
        
        if not records:
            return 0
        
        # Archive records
        archive_file = await self.archiver.archive_records(
            table_name=policy.table_name,
            records=[dict(record) for record in records],
            metadata={
                'policy': policy.category.value,
                'rule': rule.name,
                'archived_at': datetime.now(timezone.utc).isoformat()
            }
        )
        
        logger.info(f"Archived {len(records)} records to {archive_file}")
        
        # Delete archived records from main table
        delete_query = f"DELETE FROM {policy.table_name} WHERE {rule.condition}"
        await conn.execute(delete_query)
        
        return len(records)
    
    async def _execute_compress_rule(self, conn: asyncpg.Connection,
                                   policy: RetentionPolicy, rule: RetentionRule) -> int:
        """Execute a compress rule (placeholder for future implementation)"""
        
        # For now, just log that compression would happen
        # In a real implementation, this could compress large text fields
        # or move data to a compressed storage format
        
        count_query = f"SELECT COUNT(*) FROM {policy.table_name} WHERE {rule.condition}"
        count = await conn.fetchval(count_query)
        
        logger.info(f"Would compress {count} records from {policy.table_name}")
        
        return count or 0
    
    async def _execute_anonymize_rule(self, conn: asyncpg.Connection,
                                    policy: RetentionPolicy, rule: RetentionRule) -> int:
        """Execute an anonymize rule"""
        
        # Example anonymization for different data types
        anonymize_updates = []
        
        if policy.category == DataCategory.MESSAGES:
            anonymize_updates.append("content = '[ANONYMIZED]'")
        
        if policy.category == DataCategory.CONVERSATIONS:
            anonymize_updates.append("title = '[ANONYMIZED CONVERSATION]'")
        
        if policy.category == DataCategory.SESSIONS:
            anonymize_updates.extend([
                "ip_address = '0.0.0.0'",
                "user_agent = '[ANONYMIZED]'"
            ])
        
        if not anonymize_updates:
            return 0
        
        update_query = f"""
        UPDATE {policy.table_name} 
        SET {', '.join(anonymize_updates)}, updated_at = NOW()
        WHERE {rule.condition}
        """
        
        result = await conn.execute(update_query)
        return int(result.split()[-1]) if result else 0
    
    async def execute_policy_for_category(self, category: DataCategory) -> Dict[str, Any]:
        """Execute retention policy for a specific category"""
        
        if category not in self.policies:
            raise ValueError(f"No policy defined for category: {category.value}")
        
        policy = self.policies[category]
        if not policy.enabled:
            return {'success': False, 'error': 'Policy is disabled'}
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            return await self._execute_policy(conn, policy)
        finally:
            await conn.close()
    
    def add_policy(self, policy: RetentionPolicy) -> bool:
        """Add or update a retention policy"""
        
        # Validate policy
        errors = RetentionPolicyBuilder.validate_policy(policy)
        if errors:
            logger.error(f"Invalid policy for {policy.category.value}: {errors}")
            return False
        
        self.policies[policy.category] = policy
        logger.info(f"Added/updated retention policy for {policy.category.value}")
        
        return True
    
    def remove_policy(self, category: DataCategory) -> bool:
        """Remove a retention policy"""
        
        if category in self.policies:
            del self.policies[category]
            logger.info(f"Removed retention policy for {category.value}")
            return True
        
        return False
    
    def enable_policy(self, category: DataCategory) -> bool:
        """Enable a retention policy"""
        
        if category in self.policies:
            self.policies[category].enabled = True
            logger.info(f"Enabled retention policy for {category.value}")
            return True
        
        return False
    
    def disable_policy(self, category: DataCategory) -> bool:
        """Disable a retention policy"""
        
        if category in self.policies:
            self.policies[category].enabled = False
            logger.info(f"Disabled retention policy for {category.value}")
            return True
        
        return False
    
    def get_policy_status(self) -> Dict[str, Any]:
        """Get status of all retention policies"""
        
        status = {
            'total_policies': len(self.policies),
            'enabled_policies': sum(1 for p in self.policies.values() if p.enabled),
            'last_execution': self.last_run.isoformat() if self.last_run else None,
            'policies': {}
        }
        
        for category, policy in self.policies.items():
            status['policies'][category.value] = {
                'enabled': policy.enabled,
                'table_name': policy.table_name,
                'rules_count': len(policy.rules),
                'archive_after_days': policy.archive_after_days,
                'delete_after_days': policy.delete_after_days,
                'max_records': policy.max_records
            }
        
        return status
    
    async def preview_policy_execution(self, category: DataCategory) -> Dict[str, Any]:
        """Preview what a policy execution would do without actually executing"""
        
        if category not in self.policies:
            raise ValueError(f"No policy defined for category: {category.value}")
        
        policy = self.policies[category]
        conn = await asyncpg.connect(self.database_url)
        
        try:
            preview = {
                'policy': category.value,
                'table': policy.table_name,
                'rules': []
            }
            
            for rule in policy.rules:
                if not rule.enabled:
                    continue
                
                # Count records that would be affected
                if rule.params and 'keep_latest' in rule.params:
                    count_query = f"SELECT COUNT(*) FROM {policy.table_name}"
                    total_count = await conn.fetchval(count_query)
                    keep_latest = rule.params['keep_latest']
                    affected_count = max(0, total_count - keep_latest)
                else:
                    count_query = f"SELECT COUNT(*) FROM {policy.table_name} WHERE {rule.condition}"
                    affected_count = await conn.fetchval(count_query)
                
                preview['rules'].append({
                    'rule_name': rule.name,
                    'action': rule.action.value,
                    'condition': rule.condition,
                    'affected_records': affected_count or 0
                })
            
            return preview
            
        finally:
            await conn.close()
    
    async def get_retention_stats(self) -> Dict[str, Any]:
        """Get retention statistics"""
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            stats = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'tables': {}
            }
            
            for category, policy in self.policies.items():
                try:
                    # Get table stats
                    table_stats_query = f"""
                    SELECT 
                        COUNT(*) as total_records,
                        MIN(created_at) as oldest_record,
                        MAX(created_at) as newest_record,
                        pg_size_pretty(pg_total_relation_size('{policy.table_name}')) as table_size
                    FROM {policy.table_name}
                    """
                    
                    result = await conn.fetchrow(table_stats_query)
                    
                    stats['tables'][policy.table_name] = {
                        'category': category.value,
                        'total_records': result['total_records'],
                        'oldest_record': result['oldest_record'].isoformat() if result['oldest_record'] else None,
                        'newest_record': result['newest_record'].isoformat() if result['newest_record'] else None,
                        'table_size': result['table_size'],
                        'policy_enabled': policy.enabled
                    }
                    
                except Exception as e:
                    stats['tables'][policy.table_name] = {
                        'error': str(e)
                    }
            
            return stats
            
        finally:
            await conn.close()