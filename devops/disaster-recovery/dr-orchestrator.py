#!/usr/bin/env python3
"""
JARVIS AI - Disaster Recovery Orchestrator
Automated disaster recovery with intelligent failover and rollback capabilities
"""

import os
import json
import yaml
import time
import logging
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
import psycopg2
import redis
from slack_sdk import WebClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DRStatus(Enum):
    """Disaster Recovery Status"""
    ACTIVE = "active"
    STANDBY = "standby"
    FAILING_OVER = "failing_over"
    FAILED_OVER = "failed_over"
    RECOVERING = "recovering"
    FAILED = "failed"

class HealthStatus(Enum):
    """Health Check Status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    """Service health information"""
    service_name: str
    status: HealthStatus
    response_time_ms: int
    error_message: str = ""
    last_check: datetime = None
    consecutive_failures: int = 0

@dataclass
class DREvent:
    """Disaster Recovery Event"""
    event_id: str
    event_type: str
    timestamp: datetime
    status: str
    details: Dict[str, Any]
    duration_seconds: int = 0

class HealthChecker:
    """Health checking service"""
    
    def __init__(self):
        self.timeout = 10
        self.user_agent = "JARVIS-DR-HealthChecker/1.0"
    
    def check_http_endpoint(self, url: str) -> ServiceHealth:
        """Check HTTP endpoint health"""
        try:
            start_time = time.time()
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent}
            )
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                error_message = ""
            elif 500 <= response.status_code < 600:
                status = HealthStatus.UNHEALTHY
                error_message = f"Server error: {response.status_code}"
            else:
                status = HealthStatus.DEGRADED
                error_message = f"HTTP {response.status_code}"
            
            return ServiceHealth(
                service_name=url,
                status=status,
                response_time_ms=response_time,
                error_message=error_message,
                last_check=datetime.now()
            )
            
        except requests.exceptions.Timeout:
            return ServiceHealth(
                service_name=url,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=self.timeout * 1000,
                error_message="Request timeout",
                last_check=datetime.now()
            )
        except requests.exceptions.ConnectionError as e:
            return ServiceHealth(
                service_name=url,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=f"Connection error: {str(e)}",
                last_check=datetime.now()
            )
        except Exception as e:
            return ServiceHealth(
                service_name=url,
                status=HealthStatus.UNKNOWN,
                response_time_ms=0,
                error_message=f"Unknown error: {str(e)}",
                last_check=datetime.now()
            )
    
    def check_database_health(self, db_config: Dict[str, Any]) -> ServiceHealth:
        """Check database connectivity"""
        try:
            start_time = time.time()
            
            conn = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                database=db_config["database"],
                user=db_config["username"],
                password=db_config["password"],
                connect_timeout=self.timeout
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            conn.close()
            response_time = int((time.time() - start_time) * 1000)
            
            return ServiceHealth(
                service_name=f"postgres://{db_config['host']}:{db_config['port']}/{db_config['database']}",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now()
            )
            
        except Exception as e:
            return ServiceHealth(
                service_name=f"postgres://{db_config['host']}:{db_config['port']}/{db_config['database']}",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=str(e),
                last_check=datetime.now()
            )
    
    def check_redis_health(self, redis_config: Dict[str, Any]) -> ServiceHealth:
        """Check Redis connectivity"""
        try:
            start_time = time.time()
            
            r = redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                password=redis_config.get("password"),
                socket_timeout=self.timeout,
                socket_connect_timeout=self.timeout
            )
            
            r.ping()
            response_time = int((time.time() - start_time) * 1000)
            
            return ServiceHealth(
                service_name=f"redis://{redis_config['host']}:{redis_config['port']}",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now()
            )
            
        except Exception as e:
            return ServiceHealth(
                service_name=f"redis://{redis_config['host']}:{redis_config['port']}",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=str(e),
                last_check=datetime.now()
            )

class NotificationManager:
    """Notification management for DR events"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.slack_client = None
        
        if config.get("slack", {}).get("token"):
            self.slack_client = WebClient(token=config["slack"]["token"])
    
    def send_notification(self, event: DREvent, channels: List[str]):
        """Send notification to specified channels"""
        message = self._format_message(event)
        
        for channel in channels:
            if channel == "slack" and self.slack_client:
                self._send_slack_notification(message, event)
            elif channel == "email":
                self._send_email_notification(message, event)
            elif channel == "pagerduty":
                self._send_pagerduty_notification(message, event)
            elif channel == "webhook":
                self._send_webhook_notification(message, event)
    
    def _format_message(self, event: DREvent) -> str:
        """Format notification message"""
        severity = "🚨 CRITICAL" if event.event_type == "failover_initiated" else "ℹ️ INFO"
        
        return f"""
{severity} - JARVIS AI Disaster Recovery Event

Event: {event.event_type}
Status: {event.status}
Time: {event.timestamp.isoformat()}
Duration: {event.duration_seconds}s

Details:
{json.dumps(event.details, indent=2)}
        """.strip()
    
    def _send_slack_notification(self, message: str, event: DREvent):
        """Send Slack notification"""
        try:
            channel = self.config["slack"]["channel"]
            color = "danger" if event.event_type == "failover_initiated" else "good"
            
            self.slack_client.chat_postMessage(
                channel=channel,
                text=message,
                attachments=[{
                    "color": color,
                    "fields": [
                        {"title": "Event Type", "value": event.event_type, "short": True},
                        {"title": "Status", "value": event.status, "short": True},
                        {"title": "Duration", "value": f"{event.duration_seconds}s", "short": True}
                    ]
                }]
            )
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    def _send_email_notification(self, message: str, event: DREvent):
        """Send email notification"""
        # Implementation depends on email service (SES, SMTP, etc.)
        logger.info(f"Email notification would be sent: {message}")
    
    def _send_pagerduty_notification(self, message: str, event: DREvent):
        """Send PagerDuty notification"""
        # Implementation depends on PagerDuty integration
        logger.info(f"PagerDuty notification would be sent: {message}")
    
    def _send_webhook_notification(self, message: str, event: DREvent):
        """Send webhook notification"""
        try:
            webhook_url = self.config["webhook"]["url"]
            payload = {
                "event": asdict(event),
                "message": message,
                "timestamp": event.timestamp.isoformat()
            }
            
            requests.post(webhook_url, json=payload, timeout=10)
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")

class DROrchestrator:
    """Main Disaster Recovery Orchestrator"""
    
    def __init__(self, config_file: str = "dr-config.yml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        self.health_checker = HealthChecker()
        self.notification_manager = NotificationManager(self.config.get("notifications", {}))
        
        self.current_status = DRStatus.ACTIVE
        self.service_health: Dict[str, ServiceHealth] = {}
        self.events: List[DREvent] = []
        
        # AWS clients for cross-region operations
        self.primary_region = self.config["primary_region"]
        self.dr_region = self.config["dr_region"]
        
        self.primary_s3 = boto3.client('s3', region_name=self.primary_region)
        self.dr_s3 = boto3.client('s3', region_name=self.dr_region)
        
        self.primary_ec2 = boto3.client('ec2', region_name=self.primary_region)
        self.dr_ec2 = boto3.client('ec2', region_name=self.dr_region)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load DR configuration"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"DR configuration file not found: {self.config_file}")
        
        with open(self.config_file) as f:
            return yaml.safe_load(f)
    
    def _log_event(self, event_type: str, status: str, details: Dict[str, Any] = None):
        """Log DR event"""
        event = DREvent(
            event_id=f"{event_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type=event_type,
            timestamp=datetime.now(),
            status=status,
            details=details or {}
        )
        
        self.events.append(event)
        logger.info(f"DR Event: {event_type} - {status}")
        
        return event
    
    def check_primary_health(self) -> bool:
        """Check health of primary environment"""
        logger.info("Checking primary environment health...")
        
        primary_config = self.config["primary_environment"]
        all_healthy = True
        
        # Check HTTP endpoints
        for endpoint in primary_config.get("health_endpoints", []):
            health = self.health_checker.check_http_endpoint(endpoint)
            self.service_health[endpoint] = health
            
            if health.status == HealthStatus.UNHEALTHY:
                all_healthy = False
                logger.warning(f"Endpoint unhealthy: {endpoint} - {health.error_message}")
        
        # Check database
        if "database" in primary_config:
            db_health = self.health_checker.check_database_health(primary_config["database"])
            self.service_health["database"] = db_health
            
            if db_health.status == HealthStatus.UNHEALTHY:
                all_healthy = False
                logger.warning(f"Database unhealthy: {db_health.error_message}")
        
        # Check Redis
        if "redis" in primary_config:
            redis_health = self.health_checker.check_redis_health(primary_config["redis"])
            self.service_health["redis"] = redis_health
            
            if redis_health.status == HealthStatus.UNHEALTHY:
                all_healthy = False
                logger.warning(f"Redis unhealthy: {redis_health.error_message}")
        
        return all_healthy
    
    def should_initiate_failover(self) -> bool:
        """Determine if failover should be initiated"""
        if self.current_status != DRStatus.ACTIVE:
            return False
        
        failure_config = self.config["failover"]["conditions"]
        consecutive_failures = 0
        critical_services_down = 0
        
        # Count consecutive failures
        for service_name, health in self.service_health.items():
            if health.status == HealthStatus.UNHEALTHY:
                health.consecutive_failures += 1
                consecutive_failures = max(consecutive_failures, health.consecutive_failures)
                
                # Check if this is a critical service
                if service_name in failure_config.get("critical_services", []):
                    critical_services_down += 1
            else:
                health.consecutive_failures = 0
        
        # Check failover conditions
        if consecutive_failures >= failure_config["failure_threshold"]:
            logger.warning(f"Failover threshold reached: {consecutive_failures} consecutive failures")
            return True
        
        if critical_services_down >= failure_config.get("critical_services_threshold", 1):
            logger.warning(f"Critical services down: {critical_services_down}")
            return True
        
        return False
    
    def initiate_failover(self) -> bool:
        """Initiate disaster recovery failover"""
        logger.critical("Initiating disaster recovery failover...")
        
        self.current_status = DRStatus.FAILING_OVER
        event = self._log_event("failover_initiated", "in_progress", {
            "primary_region": self.primary_region,
            "dr_region": self.dr_region,
            "trigger_reason": "health_check_failure"
        })
        
        # Send immediate notification
        self.notification_manager.send_notification(
            event, self.config["notifications"]["channels"]["critical"]
        )
        
        try:
            # Step 1: Stop traffic to primary
            if not self._stop_primary_traffic():
                raise Exception("Failed to stop primary traffic")
            
            # Step 2: Restore latest backups to DR environment
            if not self._restore_dr_environment():
                raise Exception("Failed to restore DR environment")
            
            # Step 3: Start DR services
            if not self._start_dr_services():
                raise Exception("Failed to start DR services")
            
            # Step 4: Update DNS/load balancer
            if not self._update_traffic_routing():
                raise Exception("Failed to update traffic routing")
            
            # Step 5: Verify DR environment
            if not self._verify_dr_environment():
                raise Exception("DR environment verification failed")
            
            self.current_status = DRStatus.FAILED_OVER
            event.status = "completed"
            event.duration_seconds = int((datetime.now() - event.timestamp).total_seconds())
            
            logger.info("Disaster recovery failover completed successfully")
            
            # Send success notification
            success_event = self._log_event("failover_completed", "success", {
                "failover_duration": event.duration_seconds,
                "dr_region": self.dr_region
            })
            
            self.notification_manager.send_notification(
                success_event, self.config["notifications"]["channels"]["info"]
            )
            
            return True
            
        except Exception as e:
            self.current_status = DRStatus.FAILED
            event.status = "failed"
            event.details["error"] = str(e)
            
            logger.error(f"Disaster recovery failover failed: {e}")
            
            # Send failure notification
            failure_event = self._log_event("failover_failed", "failed", {
                "error": str(e),
                "recovery_actions": "Manual intervention required"
            })
            
            self.notification_manager.send_notification(
                failure_event, self.config["notifications"]["channels"]["critical"]
            )
            
            return False
    
    def _stop_primary_traffic(self) -> bool:
        """Stop traffic to primary environment"""
        logger.info("Stopping traffic to primary environment...")
        
        try:
            # Update load balancer to remove primary targets
            # This would depend on your load balancer (ALB, NLB, Cloudflare, etc.)
            
            # For AWS ALB example:
            # elb_client = boto3.client('elbv2', region_name=self.primary_region)
            # elb_client.modify_target_group(...)
            
            # Simulate traffic stop
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop primary traffic: {e}")
            return False
    
    def _restore_dr_environment(self) -> bool:
        """Restore DR environment from backups"""
        logger.info("Restoring DR environment from backups...")
        
        try:
            restore_config = self.config["restore"]
            
            # Restore database
            if not self._restore_database():
                return False
            
            # Restore Redis
            if not self._restore_redis():
                return False
            
            # Restore application data
            if not self._restore_application_data():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore DR environment: {e}")
            return False
    
    def _restore_database(self) -> bool:
        """Restore database from backup"""
        logger.info("Restoring database from backup...")
        
        try:
            db_config = self.config["dr_environment"]["database"]
            backup_config = self.config["restore"]["database"]
            
            # Download latest backup from S3
            s3_key = backup_config["latest_backup_key"]
            local_backup_path = "/tmp/db_restore.sql"
            
            self.dr_s3.download_file(
                backup_config["bucket"],
                s3_key,
                local_backup_path
            )
            
            # Restore database
            restore_cmd = [
                "psql",
                "-h", db_config["host"],
                "-p", str(db_config["port"]),
                "-U", db_config["username"],
                "-d", db_config["database"],
                "-f", local_backup_path
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = db_config["password"]
            
            result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Database restore failed: {result.stderr}")
            
            # Clean up
            os.unlink(local_backup_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def _restore_redis(self) -> bool:
        """Restore Redis from backup"""
        logger.info("Restoring Redis from backup...")
        
        try:
            # Implementation would depend on Redis backup format
            # For now, simulate successful restore
            time.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"Redis restore failed: {e}")
            return False
    
    def _restore_application_data(self) -> bool:
        """Restore application data from backup"""
        logger.info("Restoring application data...")
        
        try:
            # Sync S3 buckets
            source_bucket = self.config["primary_environment"]["data_bucket"]
            target_bucket = self.config["dr_environment"]["data_bucket"]
            
            # Use AWS CLI for efficient sync
            sync_cmd = [
                "aws", "s3", "sync",
                f"s3://{source_bucket}",
                f"s3://{target_bucket}",
                "--region", self.dr_region,
                "--delete"
            ]
            
            result = subprocess.run(sync_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Data sync failed: {result.stderr}")
            
            return True
            
        except Exception as e:
            logger.error(f"Application data restore failed: {e}")
            return False
    
    def _start_dr_services(self) -> bool:
        """Start services in DR environment"""
        logger.info("Starting DR services...")
        
        try:
            dr_config = self.config["dr_environment"]
            
            # Start EC2 instances if needed
            if "ec2_instances" in dr_config:
                instance_ids = dr_config["ec2_instances"]
                self.dr_ec2.start_instances(InstanceIds=instance_ids)
                
                # Wait for instances to be running
                waiter = self.dr_ec2.get_waiter('instance_running')
                waiter.wait(InstanceIds=instance_ids)
            
            # Start Docker services
            if "docker_compose_file" in dr_config:
                compose_cmd = [
                    "docker-compose",
                    "-f", dr_config["docker_compose_file"],
                    "up", "-d"
                ]
                
                result = subprocess.run(compose_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Docker services start failed: {result.stderr}")
            
            # Wait for services to be ready
            time.sleep(30)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start DR services: {e}")
            return False
    
    def _update_traffic_routing(self) -> bool:
        """Update DNS/load balancer to route traffic to DR"""
        logger.info("Updating traffic routing to DR environment...")
        
        try:
            # Update Route 53 DNS records
            route53 = boto3.client('route53')
            
            dns_config = self.config["dns"]
            hosted_zone_id = dns_config["hosted_zone_id"]
            
            for record in dns_config["records"]:
                response = route53.change_resource_record_sets(
                    HostedZoneId=hosted_zone_id,
                    ChangeBatch={
                        'Changes': [{
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': record["name"],
                                'Type': record["type"],
                                'TTL': 60,
                                'ResourceRecords': [{'Value': record["dr_value"]}]
                            }
                        }]
                    }
                )
                
                # Wait for DNS change to propagate
                waiter = route53.get_waiter('resource_record_sets_changed')
                waiter.wait(Id=response['ChangeInfo']['Id'])
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update traffic routing: {e}")
            return False
    
    def _verify_dr_environment(self) -> bool:
        """Verify DR environment is working correctly"""
        logger.info("Verifying DR environment...")
        
        try:
            dr_config = self.config["dr_environment"]
            
            # Check all health endpoints
            for endpoint in dr_config.get("health_endpoints", []):
                health = self.health_checker.check_http_endpoint(endpoint)
                if health.status != HealthStatus.HEALTHY:
                    raise Exception(f"DR endpoint unhealthy: {endpoint}")
            
            # Verify database connectivity
            if "database" in dr_config:
                db_health = self.health_checker.check_database_health(dr_config["database"])
                if db_health.status != HealthStatus.HEALTHY:
                    raise Exception("DR database unhealthy")
            
            # Verify Redis connectivity
            if "redis" in dr_config:
                redis_health = self.health_checker.check_redis_health(dr_config["redis"])
                if redis_health.status != HealthStatus.HEALTHY:
                    raise Exception("DR Redis unhealthy")
            
            return True
            
        except Exception as e:
            logger.error(f"DR environment verification failed: {e}")
            return False
    
    def check_recovery_conditions(self) -> bool:
        """Check if primary environment has recovered"""
        if self.current_status != DRStatus.FAILED_OVER:
            return False
        
        recovery_config = self.config["recovery"]
        
        if not recovery_config.get("auto_recovery_enabled", False):
            return False
        
        # Check if primary is healthy for required duration
        primary_healthy = self.check_primary_health()
        
        if primary_healthy:
            # Check if it's been healthy for the required time
            health_duration = recovery_config.get("health_duration_minutes", 30)
            # Implementation would track health over time
            return True
        
        return False
    
    def initiate_recovery(self) -> bool:
        """Initiate recovery back to primary environment"""
        logger.info("Initiating recovery to primary environment...")
        
        self.current_status = DRStatus.RECOVERING
        event = self._log_event("recovery_initiated", "in_progress", {
            "from_region": self.dr_region,
            "to_region": self.primary_region
        })
        
        try:
            # Reverse the failover process
            # This would involve similar steps but in reverse
            
            # For now, simulate recovery
            time.sleep(10)
            
            self.current_status = DRStatus.ACTIVE
            event.status = "completed"
            event.duration_seconds = int((datetime.now() - event.timestamp).total_seconds())
            
            recovery_event = self._log_event("recovery_completed", "success", {
                "recovery_duration": event.duration_seconds
            })
            
            self.notification_manager.send_notification(
                recovery_event, self.config["notifications"]["channels"]["info"]
            )
            
            return True
            
        except Exception as e:
            self.current_status = DRStatus.FAILED
            event.status = "failed"
            event.details["error"] = str(e)
            
            logger.error(f"Recovery failed: {e}")
            return False
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Starting DR monitoring loop...")
        
        check_interval = self.config["monitoring"]["check_interval_seconds"]
        
        while True:
            try:
                # Check primary environment health
                primary_healthy = self.check_primary_health()
                
                # Check if failover should be initiated
                if not primary_healthy and self.should_initiate_failover():
                    self.initiate_failover()
                
                # Check if recovery should be initiated
                elif self.check_recovery_conditions():
                    self.initiate_recovery()
                
                # Log status
                logger.info(f"DR Status: {self.current_status.value}, Primary Healthy: {primary_healthy}")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("DR monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current DR status"""
        return {
            "current_status": self.current_status.value,
            "last_check": datetime.now().isoformat(),
            "service_health": {
                name: {
                    "status": health.status.value,
                    "response_time_ms": health.response_time_ms,
                    "consecutive_failures": health.consecutive_failures,
                    "last_check": health.last_check.isoformat() if health.last_check else None,
                    "error_message": health.error_message
                }
                for name, health in self.service_health.items()
            },
            "recent_events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "status": event.status,
                    "duration_seconds": event.duration_seconds
                }
                for event in self.events[-10:]  # Last 10 events
            ]
        }

def main():
    """CLI interface for DR orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS AI Disaster Recovery Orchestrator")
    parser.add_argument("--config", "-c", default="dr-config.yml",
                       help="DR configuration file")
    parser.add_argument("--action", "-a", required=True,
                       choices=["monitor", "status", "failover", "recover", "test"],
                       help="Action to perform")
    
    args = parser.parse_args()
    
    dr_orchestrator = DROrchestrator(config_file=args.config)
    
    if args.action == "monitor":
        dr_orchestrator.run_monitoring_loop()
    elif args.action == "status":
        status = dr_orchestrator.get_status()
        print(json.dumps(status, indent=2))
    elif args.action == "failover":
        success = dr_orchestrator.initiate_failover()
        print(f"Failover {'successful' if success else 'failed'}")
    elif args.action == "recover":
        success = dr_orchestrator.initiate_recovery()
        print(f"Recovery {'successful' if success else 'failed'}")
    elif args.action == "test":
        # Run DR tests
        primary_healthy = dr_orchestrator.check_primary_health()
        print(f"Primary environment health: {'Healthy' if primary_healthy else 'Unhealthy'}")

if __name__ == "__main__":
    main()