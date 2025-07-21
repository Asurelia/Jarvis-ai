#!/usr/bin/env python3
"""
🧪 Tests d'intégration complets pour JARVIS AI 2025
Tests end-to-end de tous les services et composants
"""

import asyncio
import pytest
import aiohttp
import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import docker
import subprocess
from datetime import datetime

# Ajouter le projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration des tests
TEST_CONFIG = {
    "services": {
        "brain_api": {"url": "http://localhost:5000", "health": "/health"},
        "stt_service": {"url": "http://localhost:5001", "health": "/health"},
        "tts_service": {"url": "http://localhost:5002", "health": "/health"},
        "system_control": {"url": "http://localhost:5004", "health": "/health"},
        "terminal_service": {"url": "http://localhost:5005", "health": "/health"},
        "mcp_gateway": {"url": "http://localhost:5006", "health": "/health"},
        "autocomplete_service": {"url": "http://localhost:5007", "health": "/health"},
    },
    "external_services": {
        "postgresql": {"url": "http://localhost:5432"},
        "redis": {"url": "http://localhost:6379"},
        "ollama": {"url": "http://localhost:11434", "endpoint": "/api/tags"},
    },
    "timeouts": {
        "service_startup": 30,
        "test_execution": 10,
        "docker_compose": 60
    }
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JarvisIntegrationTester:
    """Testeur d'intégration complet pour JARVIS AI"""
    
    def __init__(self):
        self.docker_client = None
        self.test_results = {
            "started_at": datetime.now().isoformat(),
            "services": {},
            "integration_tests": {},
            "performance_tests": {},
            "security_tests": {},
            "summary": {}
        }
        self.auth_token = None
        
    async def setup(self):
        """Configuration initiale des tests"""
        logger.info("🔧 Configuration des tests d'intégration...")
        
        try:
            # Initialiser le client Docker
            self.docker_client = docker.from_env()
            logger.info("✓ Client Docker initialisé")
        except Exception as e:
            logger.error(f"✗ Erreur Docker: {e}")
            
        # Vérifier que docker-compose.yml existe
        compose_file = project_root / "docker-compose.yml"
        if not compose_file.exists():
            raise FileNotFoundError("docker-compose.yml non trouvé")
            
    async def test_docker_services_health(self) -> Dict[str, bool]:
        """Test de santé de tous les services Docker"""
        logger.info("🏥 Test de santé des services Docker...")
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for service_name, config in TEST_CONFIG["services"].items():
                try:
                    url = f"{config['url']}{config['health']}"
                    timeout = aiohttp.ClientTimeout(total=TEST_CONFIG["timeouts"]["test_execution"])
                    
                    async with session.get(url, timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            results[service_name] = {
                                "status": "healthy",
                                "response_time": response.headers.get("X-Response-Time", "N/A"),
                                "data": data
                            }
                            logger.info(f"✓ {service_name}: Opérationnel")
                        else:
                            results[service_name] = {
                                "status": "unhealthy",
                                "http_status": response.status,
                                "error": f"HTTP {response.status}"
                            }
                            logger.warning(f"⚠ {service_name}: HTTP {response.status}")
                            
                except asyncio.TimeoutError:
                    results[service_name] = {
                        "status": "timeout",
                        "error": "Timeout de connexion"
                    }
                    logger.error(f"✗ {service_name}: Timeout")
                    
                except Exception as e:
                    results[service_name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    logger.error(f"✗ {service_name}: {e}")
        
        self.test_results["services"] = results
        return results
    
    async def test_external_services(self) -> Dict[str, bool]:
        """Test de connectivité aux services externes"""
        logger.info("🔗 Test des services externes...")
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for service_name, config in TEST_CONFIG["external_services"].items():
                try:
                    if service_name == "ollama":
                        url = f"{config['url']}{config['endpoint']}"
                    else:
                        url = config['url']
                    
                    timeout = aiohttp.ClientTimeout(total=5)
                    async with session.get(url, timeout=timeout) as response:
                        results[service_name] = {
                            "status": "available",
                            "http_status": response.status
                        }
                        logger.info(f"✓ {service_name}: Disponible")
                        
                except Exception as e:
                    results[service_name] = {
                        "status": "unavailable",
                        "error": str(e)
                    }
                    logger.warning(f"⚠ {service_name}: {e}")
        
        return results
    
    async def test_authentication_flow(self) -> bool:
        """Test du flux d'authentification JWT"""
        logger.info("🔐 Test d'authentification JWT...")
        
        async with aiohttp.ClientSession() as session:
            # Test de login
            login_data = {
                "username": "jarvis",
                "password": "jarvis2025!",
                "permissions": ["system_control"]
            }
            
            try:
                async with session.post(
                    "http://localhost:5004/auth/login",
                    json=login_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        auth_data = await response.json()
                        self.auth_token = auth_data["access_token"]
                        logger.info("✓ Authentification réussie")
                        
                        # Test de vérification du token
                        headers = {"Authorization": f"Bearer {self.auth_token}"}
                        async with session.get(
                            "http://localhost:5004/auth/verify",
                            headers=headers
                        ) as verify_response:
                            if verify_response.status == 200:
                                logger.info("✓ Vérification token réussie")
                                return True
                            else:
                                logger.error("✗ Échec vérification token")
                                return False
                    else:
                        logger.error(f"✗ Échec authentification: HTTP {response.status}")
                        return False
                        
            except Exception as e:
                logger.error(f"✗ Erreur authentification: {e}")
                return False
    
    async def test_brain_api_integration(self) -> Dict[str, Any]:
        """Test d'intégration de l'API Brain"""
        logger.info("🧠 Test d'intégration Brain API...")
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test de chat simple
            try:
                chat_data = {
                    "message": "Bonjour JARVIS, comment allez-vous?",
                    "user_id": "test_user",
                    "context": {}
                }
                
                async with session.post(
                    "http://localhost:5000/chat/message",
                    json=chat_data,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        chat_response = await response.json()
                        results["chat"] = {
                            "status": "success",
                            "response_time": time.time(),
                            "message_length": len(chat_response.get("response", ""))
                        }
                        logger.info("✓ Chat Brain API fonctionnel")
                    else:
                        results["chat"] = {
                            "status": "failed",
                            "http_status": response.status
                        }
                        
            except Exception as e:
                results["chat"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Test de mémoire
            try:
                memory_data = {
                    "content": "Test de mémorisation d'information",
                    "type": "user_preference",
                    "user_id": "test_user"
                }
                
                async with session.post(
                    "http://localhost:5000/memory/store",
                    json=memory_data
                ) as response:
                    if response.status == 200:
                        results["memory"] = {
                            "status": "success"
                        }
                        logger.info("✓ Système de mémoire fonctionnel")
                    else:
                        results["memory"] = {
                            "status": "failed",
                            "http_status": response.status
                        }
                        
            except Exception as e:
                results["memory"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    async def test_voice_pipeline(self) -> Dict[str, Any]:
        """Test du pipeline vocal complet (STT + TTS)"""
        logger.info("🎤 Test du pipeline vocal...")
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test STT Health
            try:
                async with session.get("http://localhost:5001/health") as response:
                    if response.status == 200:
                        results["stt"] = {"status": "healthy"}
                        logger.info("✓ Service STT disponible")
                    else:
                        results["stt"] = {"status": "unhealthy"}
                        
            except Exception as e:
                results["stt"] = {"status": "error", "error": str(e)}
            
            # Test TTS Health  
            try:
                async with session.get("http://localhost:5002/health") as response:
                    if response.status == 200:
                        results["tts"] = {"status": "healthy"}
                        logger.info("✓ Service TTS disponible")
                    else:
                        results["tts"] = {"status": "unhealthy"}
                        
            except Exception as e:
                results["tts"] = {"status": "error", "error": str(e)}
        
        return results
    
    async def test_system_control_security(self) -> Dict[str, Any]:
        """Test de sécurité du contrôle système"""
        logger.info("🛡️ Test de sécurité du contrôle système...")
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test sans authentification (doit échouer)
            try:
                mouse_data = {"x": 100, "y": 100}
                async with session.post(
                    "http://localhost:5004/mouse/move",
                    json=mouse_data
                ) as response:
                    if response.status == 401:
                        results["auth_required"] = {"status": "pass", "message": "Authentification requise"}
                        logger.info("✓ Sécurité: Authentification obligatoire")
                    else:
                        results["auth_required"] = {"status": "fail", "http_status": response.status}
                        
            except Exception as e:
                results["auth_required"] = {"status": "error", "error": str(e)}
            
            # Test avec authentification valide
            if self.auth_token:
                try:
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    async with session.post(
                        "http://localhost:5004/mouse/move",
                        json=mouse_data,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            results["authenticated_access"] = {"status": "pass"}
                            logger.info("✓ Sécurité: Accès authentifié autorisé")
                        else:
                            results["authenticated_access"] = {"status": "fail", "http_status": response.status}
                            
                except Exception as e:
                    results["authenticated_access"] = {"status": "error", "error": str(e)}
        
        return results
    
    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Tests de performance et benchmarks"""
        logger.info("⚡ Tests de performance...")
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test de latence API Brain
            start_time = time.time()
            try:
                async with session.get("http://localhost:5000/health") as response:
                    if response.status == 200:
                        latency = (time.time() - start_time) * 1000  # en ms
                        results["brain_api_latency"] = {
                            "value": latency,
                            "unit": "ms",
                            "status": "pass" if latency < 100 else "warning"
                        }
                        logger.info(f"⚡ Latence Brain API: {latency:.2f}ms")
                        
            except Exception as e:
                results["brain_api_latency"] = {"status": "error", "error": str(e)}
            
            # Test de charge simple (10 requêtes parallèles)
            start_time = time.time()
            try:
                tasks = []
                for i in range(10):
                    task = session.get("http://localhost:5000/health")
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                successful_responses = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
                
                results["load_test"] = {
                    "total_requests": 10,
                    "successful_requests": successful_responses,
                    "total_time": total_time,
                    "requests_per_second": 10 / total_time,
                    "status": "pass" if successful_responses >= 8 else "fail"
                }
                logger.info(f"⚡ Test de charge: {successful_responses}/10 succès en {total_time:.2f}s")
                
            except Exception as e:
                results["load_test"] = {"status": "error", "error": str(e)}
        
        return results
    
    async def test_docker_containers_status(self) -> Dict[str, Any]:
        """Vérification du statut des conteneurs Docker"""
        logger.info("🐳 Vérification des conteneurs Docker...")
        
        results = {}
        
        try:
            if self.docker_client:
                containers = self.docker_client.containers.list()
                
                for container in containers:
                    if "jarvis" in container.name.lower():
                        results[container.name] = {
                            "status": container.status,
                            "image": container.image.tags[0] if container.image.tags else "unknown",
                            "created": container.attrs["Created"],
                            "ports": container.ports
                        }
                        logger.info(f"🐳 {container.name}: {container.status}")
                        
            else:
                results["docker_client"] = {"status": "unavailable"}
                
        except Exception as e:
            results["docker_error"] = {"error": str(e)}
            
        return results
    
    async def run_complete_integration_tests(self) -> Dict[str, Any]:
        """Exécuter tous les tests d'intégration"""
        logger.info("🚀 Lancement des tests d'intégration complets...")
        
        await self.setup()
        
        # Tests de santé des services
        self.test_results["services"] = await self.test_docker_services_health()
        
        # Tests des services externes
        self.test_results["external_services"] = await self.test_external_services()
        
        # Tests d'authentification
        auth_success = await self.test_authentication_flow()
        self.test_results["authentication"] = {"success": auth_success}
        
        # Tests d'intégration
        self.test_results["brain_integration"] = await self.test_brain_api_integration()
        self.test_results["voice_pipeline"] = await self.test_voice_pipeline()
        
        # Tests de sécurité
        self.test_results["security"] = await self.test_system_control_security()
        
        # Tests de performance
        self.test_results["performance"] = await self.test_performance_benchmarks()
        
        # Status des conteneurs Docker
        self.test_results["docker_containers"] = await self.test_docker_containers_status()
        
        # Générer le résumé
        self.generate_summary()
        
        return self.test_results
    
    def generate_summary(self):
        """Générer le résumé des tests"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for category, tests in self.test_results.items():
            if category in ["started_at", "summary"]:
                continue
                
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    total_tests += 1
                    if isinstance(result, dict):
                        status = result.get("status", "unknown")
                        if status in ["healthy", "success", "pass", "available"]:
                            passed_tests += 1
                        elif status in ["unhealthy", "failed", "fail", "error", "timeout"]:
                            failed_tests += 1
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "completed_at": datetime.now().isoformat()
        }
        
        logger.info(f"📊 Résumé: {passed_tests}/{total_tests} tests réussis ({self.test_results['summary']['success_rate']:.1f}%)")
    
    def save_results(self, filename: str = "jarvis_integration_test_results.json"):
        """Sauvegarder les résultats des tests"""
        results_file = project_root / "tests" / filename
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Résultats sauvegardés: {results_file}")

async def main():
    """Point d'entrée principal des tests"""
    tester = JarvisIntegrationTester()
    
    try:
        results = await tester.run_complete_integration_tests()
        tester.save_results()
        
        # Afficher le résumé final
        summary = results["summary"]
        print(f"\n{'='*60}")
        print(f"🧪 TESTS D'INTÉGRATION JARVIS AI - RÉSULTATS FINAUX")
        print(f"{'='*60}")
        print(f"Total des tests: {summary['total_tests']}")
        print(f"Réussis: {summary['passed']} ✓")
        print(f"Échoués: {summary['failed']} ✗")
        print(f"Taux de réussite: {summary['success_rate']:.1f}%")
        print(f"{'='*60}")
        
        if summary['success_rate'] >= 80:
            print("🎉 JARVIS AI est prêt pour la production!")
            return 0
        else:
            print("⚠️ Des améliorations sont nécessaires avant la production")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Erreur fatale lors des tests: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)