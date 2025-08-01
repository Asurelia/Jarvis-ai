#!/usr/bin/env python3
"""
🛡️ Monitoring de sécurité JARVIS AI
Surveillance continue des métriques de sécurité et détection d'anomalies
"""

import asyncio
import aiohttp
import json
import logging
import os
import time
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import docker
import subprocess

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/jarvis/logs/security-monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityAlert:
    """Classe pour représenter une alerte de sécurité"""
    timestamp: datetime
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    category: str  # AUTHENTICATION, NETWORK, SYSTEM, APPLICATION
    title: str
    description: str
    source: str
    details: Dict[str, Any]

@dataclass
class SecurityMetrics:
    """Métriques de sécurité collectées"""
    timestamp: datetime
    failed_auth_attempts: int
    active_connections: int
    suspicious_requests: int
    system_load: float
    memory_usage: float
    disk_usage: float
    docker_containers_running: int
    ssl_cert_expiry_days: Optional[int]
    firewall_status: bool

class SecurityMonitor:
    """Moniteur de sécurité principal"""
    
    def __init__(self, config_file: str = "/etc/jarvis/security-monitor.json"):
        self.config = self.load_config(config_file)
        self.alerts: List[SecurityAlert] = []
        self.metrics_history: List[SecurityMetrics] = []
        self.docker_client = docker.from_env()
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Charge la configuration du monitoring"""
        default_config = {
            "monitoring": {
                "interval_seconds": 60,
                "max_failed_auth": 10,
                "max_suspicious_requests": 50,
                "max_system_load": 80.0,
                "max_memory_usage": 85.0,
                "max_disk_usage": 90.0,
                "ssl_expiry_warning_days": 30
            },
            "alerts": {
                "email_enabled": False,
                "email_smtp_server": "smtp.gmail.com",
                "email_smtp_port": 587,
                "email_username": "",
                "email_password": "",
                "email_recipients": [],
                "webhook_url": ""
            },
            "services": {
                "brain_api_url": "http://localhost:5000",
                "nginx_logs": "/var/jarvis/logs/nginx/access.log",
                "auth_logs": "/var/jarvis/logs/brain/auth.log"
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                return {**default_config, **config}
            else:
                # Créer le fichier de config par défaut
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Configuration par défaut créée: {config_file}")
                return default_config
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            return default_config
    
    async def collect_metrics(self) -> SecurityMetrics:
        """Collecte les métriques de sécurité"""
        timestamp = datetime.now()
        
        # Métriques système
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Métriques réseau
        network_connections = len(psutil.net_connections())
        
        # Métriques Docker
        containers = self.docker_client.containers.list()
        running_containers = len([c for c in containers if c.status == 'running'])
        
        # Métriques d'authentification
        failed_auth = await self.count_failed_auth()
        suspicious_requests = await self.count_suspicious_requests()
        
        # Statut SSL
        ssl_expiry_days = await self.check_ssl_expiry()
        
        # Statut firewall
        firewall_status = self.check_firewall_status()
        
        metrics = SecurityMetrics(
            timestamp=timestamp,
            failed_auth_attempts=failed_auth,
            active_connections=network_connections,
            suspicious_requests=suspicious_requests,
            system_load=cpu_percent,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            docker_containers_running=running_containers,
            ssl_cert_expiry_days=ssl_expiry_days,
            firewall_status=firewall_status
        )
        
        self.metrics_history.append(metrics)
        
        # Garder seulement les 1000 dernières métriques
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    async def count_failed_auth(self) -> int:
        """Compte les tentatives d'authentification échouées"""
        try:
            auth_log = self.config["services"]["auth_logs"]
            if not os.path.exists(auth_log):
                return 0
            
            # Compter les échecs dans la dernière heure
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            with open(auth_log, 'r') as f:
                lines = f.readlines()
            
            failed_count = 0
            for line in lines:
                if 'Tentative de connexion échouée' in line:
                    # Extraire timestamp et vérifier si dans la dernière heure
                    # Format attendu: 2024-01-01 12:00:00 - ...
                    try:
                        timestamp_str = line.split(' - ')[0]
                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        if log_time > one_hour_ago:
                            failed_count += 1
                    except ValueError:
                        continue
            
            return failed_count
        except Exception as e:
            logger.error(f"Erreur comptage auth: {e}")
            return 0
    
    async def count_suspicious_requests(self) -> int:
        """Compte les requêtes suspectes"""
        try:
            nginx_log = self.config["services"]["nginx_logs"]
            if not os.path.exists(nginx_log):
                return 0
            
            suspicious_patterns = [
                'sql injection', 'script', 'eval', 'union select',
                '../', '..\\', '/etc/passwd', 'cmd.exe'
            ]
            
            # Analyser la dernière heure
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            with open(nginx_log, 'r') as f:
                lines = f.readlines()
            
            suspicious_count = 0
            for line in lines:
                line_lower = line.lower()
                if any(pattern in line_lower for pattern in suspicious_patterns):
                    suspicious_count += 1
            
            return suspicious_count
        except Exception as e:
            logger.error(f"Erreur comptage requêtes suspectes: {e}")
            return 0
    
    async def check_ssl_expiry(self) -> Optional[int]:
        """Vérifie l'expiration des certificats SSL"""
        try:
            domain = os.getenv('CERTBOT_DOMAIN', 'localhost')
            cert_path = f"/var/jarvis/ssl/live/{domain}/fullchain.pem"
            
            if not os.path.exists(cert_path):
                return None
            
            # Utiliser openssl pour vérifier l'expiration
            result = subprocess.run([
                'openssl', 'x509', '-in', cert_path, '-noout', '-dates'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
            
            # Extraire la date d'expiration
            for line in result.stdout.split('\n'):
                if 'notAfter=' in line:
                    date_str = line.split('notAfter=')[1]
                    expiry_date = datetime.strptime(date_str, '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (expiry_date - datetime.now()).days
                    return days_until_expiry
            
            return None
        except Exception as e:
            logger.error(f"Erreur vérification SSL: {e}")
            return None
    
    def check_firewall_status(self) -> bool:
        """Vérifie le statut du firewall"""
        try:
            # Vérifier ufw sur Linux
            result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
            return 'Status: active' in result.stdout
        except Exception:
            # Fallback pour Windows ou si ufw n'est pas disponible
            return True
    
    def analyze_metrics(self, metrics: SecurityMetrics) -> List[SecurityAlert]:
        """Analyse les métriques et génère des alertes"""
        alerts = []
        config = self.config["monitoring"]
        
        # Vérifier les tentatives d'authentification
        if metrics.failed_auth_attempts > config["max_failed_auth"]:
            alerts.append(SecurityAlert(
                timestamp=metrics.timestamp,
                severity="HIGH",
                category="AUTHENTICATION",
                title="Nombreuses tentatives d'authentification échouées",
                description=f"{metrics.failed_auth_attempts} tentatives échouées détectées",
                source="auth_logs",
                details={"count": metrics.failed_auth_attempts}
            ))
        
        # Vérifier les requêtes suspectes
        if metrics.suspicious_requests > config["max_suspicious_requests"]:
            alerts.append(SecurityAlert(
                timestamp=metrics.timestamp,
                severity="MEDIUM",
                category="NETWORK",
                title="Requêtes suspectes détectées",
                description=f"{metrics.suspicious_requests} requêtes suspectes détectées",
                source="nginx_logs",
                details={"count": metrics.suspicious_requests}
            ))
        
        # Vérifier la charge système
        if metrics.system_load > config["max_system_load"]:
            alerts.append(SecurityAlert(
                timestamp=metrics.timestamp,
                severity="MEDIUM",
                category="SYSTEM",
                title="Charge système élevée",
                description=f"Charge CPU à {metrics.system_load}%",
                source="system_metrics",
                details={"cpu_percent": metrics.system_load}
            ))
        
        # Vérifier l'utilisation mémoire
        if metrics.memory_usage > config["max_memory_usage"]:
            alerts.append(SecurityAlert(
                timestamp=metrics.timestamp,
                severity="MEDIUM",
                category="SYSTEM",
                title="Utilisation mémoire élevée",
                description=f"Mémoire utilisée à {metrics.memory_usage}%",
                source="system_metrics",
                details={"memory_percent": metrics.memory_usage}
            ))
        
        # Vérifier l'utilisation disque
        if metrics.disk_usage > config["max_disk_usage"]:
            alerts.append(SecurityAlert(
                timestamp=metrics.timestamp,
                severity="HIGH",
                category="SYSTEM",
                title="Espace disque faible",
                description=f"Disque utilisé à {metrics.disk_usage}%",
                source="system_metrics",
                details={"disk_percent": metrics.disk_usage}
            ))
        
        # Vérifier l'expiration SSL
        if (metrics.ssl_cert_expiry_days is not None and 
            metrics.ssl_cert_expiry_days < config["ssl_expiry_warning_days"]):
            severity = "CRITICAL" if metrics.ssl_cert_expiry_days < 7 else "HIGH"
            alerts.append(SecurityAlert(
                timestamp=metrics.timestamp,
                severity=severity,
                category="NETWORK",
                title="Certificat SSL proche de l'expiration",
                description=f"Certificat expire dans {metrics.ssl_cert_expiry_days} jours",
                source="ssl_check",
                details={"days_until_expiry": metrics.ssl_cert_expiry_days}
            ))
        
        # Vérifier le firewall
        if not metrics.firewall_status:
            alerts.append(SecurityAlert(
                timestamp=metrics.timestamp,
                severity="CRITICAL",
                category="NETWORK",
                title="Firewall désactivé",
                description="Le firewall n'est pas actif",
                source="firewall_check",
                details={}
            ))
        
        return alerts
    
    async def send_alert(self, alert: SecurityAlert):
        """Envoie une alerte"""
        logger.warning(f"🚨 ALERTE [{alert.severity}] {alert.title}: {alert.description}")
        
        # Envoyer par email si configuré
        if self.config["alerts"]["email_enabled"]:
            await self.send_email_alert(alert)
        
        # Envoyer par webhook si configuré
        webhook_url = self.config["alerts"].get("webhook_url")
        if webhook_url:
            await self.send_webhook_alert(alert, webhook_url)
    
    async def send_email_alert(self, alert: SecurityAlert):
        """Envoie une alerte par email"""
        try:
            smtp_server = self.config["alerts"]["email_smtp_server"]
            smtp_port = self.config["alerts"]["email_smtp_port"]
            username = self.config["alerts"]["email_username"]
            password = self.config["alerts"]["email_password"]
            recipients = self.config["alerts"]["email_recipients"]
            
            if not all([smtp_server, username, password, recipients]):
                logger.warning("Configuration email incomplete")
                return
            
            msg = MimeMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"🚨 JARVIS Security Alert - {alert.title}"
            
            body = f"""
            ALERTE DE SÉCURITÉ JARVIS
            
            Timestamp: {alert.timestamp}
            Sévérité: {alert.severity}
            Catégorie: {alert.category}
            Source: {alert.source}
            
            Description: {alert.description}
            
            Détails: {json.dumps(alert.details, indent=2)}
            
            ---
            Monitoring automatique JARVIS AI
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Envoyer l'email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(username, password)
                server.send_message(msg)
            
            logger.info("Alerte email envoyée")
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
    
    async def send_webhook_alert(self, alert: SecurityAlert, webhook_url: str):
        """Envoie une alerte par webhook"""
        try:
            payload = {
                "timestamp": alert.timestamp.isoformat(),
                "severity": alert.severity,
                "category": alert.category,
                "title": alert.title,
                "description": alert.description,
                "source": alert.source,
                "details": alert.details
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Alerte webhook envoyée")
                    else:
                        logger.error(f"Erreur webhook: {response.status}")
        except Exception as e:
            logger.error(f"Erreur envoi webhook: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Génère un rapport de sécurité"""
        if not self.metrics_history:
            return {"error": "Aucune métrique disponible"}
        
        latest = self.metrics_history[-1]
        last_24h = [m for m in self.metrics_history 
                   if m.timestamp > datetime.now() - timedelta(days=1)]
        
        alerts_24h = [a for a in self.alerts 
                     if a.timestamp > datetime.now() - timedelta(days=1)]
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": "24 heures",
            "current_metrics": asdict(latest),
            "summary": {
                "total_alerts": len(alerts_24h),
                "critical_alerts": len([a for a in alerts_24h if a.severity == "CRITICAL"]),
                "high_alerts": len([a for a in alerts_24h if a.severity == "HIGH"]),
                "avg_system_load": sum(m.system_load for m in last_24h) / len(last_24h),
                "avg_memory_usage": sum(m.memory_usage for m in last_24h) / len(last_24h),
                "total_failed_auth": sum(m.failed_auth_attempts for m in last_24h),
                "total_suspicious_requests": sum(m.suspicious_requests for m in last_24h)
            },
            "alerts": [asdict(a) for a in alerts_24h]
        }
        
        return report
    
    async def run_monitoring_cycle(self):
        """Exécute un cycle de monitoring"""
        try:
            # Collecter les métriques
            metrics = await self.collect_metrics()
            
            # Analyser et générer des alertes
            new_alerts = self.analyze_metrics(metrics)
            
            # Envoyer les alertes
            for alert in new_alerts:
                self.alerts.append(alert)
                await self.send_alert(alert)
            
            # Log des métriques
            logger.info(f"Métriques collectées - CPU: {metrics.system_load}%, "
                       f"Mémoire: {metrics.memory_usage}%, "
                       f"Auth échouées: {metrics.failed_auth_attempts}, "
                       f"Alertes: {len(new_alerts)}")
        
        except Exception as e:
            logger.error(f"Erreur cycle monitoring: {e}")
    
    async def start_monitoring(self):
        """Démarre le monitoring en continu"""
        logger.info("🛡️ Démarrage du monitoring de sécurité JARVIS")
        interval = self.config["monitoring"]["interval_seconds"]
        
        while True:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Arrêt du monitoring")
                break
            except Exception as e:
                logger.error(f"Erreur monitoring: {e}")
                await asyncio.sleep(10)  # Attendre avant de réessayer

async def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitoring de sécurité JARVIS")
    parser.add_argument('--config', default='/etc/jarvis/security-monitor.json',
                       help='Fichier de configuration')
    parser.add_argument('--report', action='store_true',
                       help='Générer un rapport et quitter')
    parser.add_argument('--test', action='store_true',
                       help='Test des alertes et quitter')
    
    args = parser.parse_args()
    
    monitor = SecurityMonitor(args.config)
    
    if args.report:
        # Générer et afficher un rapport
        report = monitor.generate_report()
        print(json.dumps(report, indent=2, default=str))
    elif args.test:
        # Test des alertes
        test_alert = SecurityAlert(
            timestamp=datetime.now(),
            severity="HIGH",
            category="TEST",
            title="Test d'alerte",
            description="Ceci est un test du système d'alertes",
            source="test",
            details={"test": True}
        )
        await monitor.send_alert(test_alert)
        print("Test d'alerte envoyé")
    else:
        # Démarrer le monitoring
        await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())