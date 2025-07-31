"""
Tests d'intégration pour les services Docker JARVIS AI
Vérifie le démarrage et la communication entre services
"""

import pytest
import docker
import requests
import time
import asyncio
from typing import Dict, List

class TestDockerServices:
    """Tests d'intégration des services Docker"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Client Docker pour les tests"""
        return docker.from_env()
    
    @pytest.fixture(scope="class")
    def services_config(self) -> Dict[str, Dict]:
        """Configuration des services à tester"""
        return {
            "brain-api": {
                "container": "jarvis_brain",
                "health_url": "http://localhost:5000/health",
                "ports": [5000, 5001],
                "wait_time": 30
            },
            "tts-service": {
                "container": "jarvis_tts",
                "health_url": "http://localhost:5002/health",
                "ports": [5002],
                "wait_time": 20
            },
            "stt-service": {
                "container": "jarvis_stt",
                "health_url": "http://localhost:5003/health",
                "ports": [5003],
                "wait_time": 20
            },
            "gpu-stats-service": {
                "container": "jarvis_gpu_stats",
                "health_url": "http://localhost:5009/health",
                "ports": [5009],
                "wait_time": 15
            },
            "system-control": {
                "container": "jarvis_system_control",
                "health_url": "http://localhost:5004/health",
                "ports": [5004],
                "wait_time": 15
            },
            "terminal-service": {
                "container": "jarvis_terminal",
                "health_url": "http://localhost:5005/health",
                "ports": [5005],
                "wait_time": 15
            },
            "mcp-gateway": {
                "container": "jarvis_mcp_gateway",
                "health_url": "http://localhost:5006/health",
                "ports": [5006],
                "wait_time": 20
            },
            "autocomplete-service": {
                "container": "jarvis_autocomplete",
                "health_url": "http://localhost:5007/health",
                "ports": [5007],
                "wait_time": 15
            }
        }
    
    @pytest.mark.integration
    @pytest.mark.docker
    def test_all_services_running(self, docker_client, services_config):
        """Vérifie que tous les services sont en cours d'exécution"""
        running_containers = {c.name for c in docker_client.containers.list()}
        
        for service_name, config in services_config.items():
            container_name = config["container"]
            assert container_name in running_containers, \
                f"Service {service_name} ({container_name}) n'est pas en cours d'exécution"
    
    @pytest.mark.integration
    @pytest.mark.docker
    def test_services_health_checks(self, services_config):
        """Vérifie que tous les services répondent aux health checks"""
        failed_services = []
        
        for service_name, config in services_config.items():
            health_url = config["health_url"]
            wait_time = config["wait_time"]
            
            # Attendre que le service soit prêt
            service_ready = False
            for attempt in range(wait_time):
                try:
                    response = requests.get(health_url, timeout=5)
                    if response.status_code == 200:
                        service_ready = True
                        break
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            if not service_ready:
                failed_services.append(service_name)
        
        assert not failed_services, \
            f"Services sans réponse health check : {', '.join(failed_services)}"
    
    @pytest.mark.integration
    @pytest.mark.docker
    def test_inter_service_communication(self):
        """Teste la communication entre services"""
        # Test Brain API -> Ollama
        try:
            response = requests.post(
                "http://localhost:5000/api/chat",
                json={"message": "Test inter-service"},
                timeout=10
            )
            assert response.status_code in [200, 201]
        except Exception as e:
            pytest.fail(f"Communication Brain API échouée : {str(e)}")
        
        # Test MCP Gateway -> autres services
        try:
            response = requests.get(
                "http://localhost:5006/api/tools",
                timeout=5
            )
            assert response.status_code == 200
        except Exception as e:
            pytest.fail(f"Communication MCP Gateway échouée : {str(e)}")
    
    @pytest.mark.integration
    @pytest.mark.docker
    async def test_websocket_connectivity(self):
        """Test de connectivité WebSocket"""
        import websockets
        
        # Test WebSocket Brain API
        try:
            async with websockets.connect("ws://localhost:5001/ws") as websocket:
                await websocket.send('{"type": "ping"}')
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                assert response is not None
        except Exception as e:
            pytest.fail(f"WebSocket Brain API échoué : {str(e)}")
        
        # Test WebSocket GPU Stats
        try:
            async with websockets.connect("ws://localhost:5009/ws/gpu-stats") as websocket:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                assert "gpu" in response.lower()
        except Exception as e:
            pytest.fail(f"WebSocket GPU Stats échoué : {str(e)}")
    
    @pytest.mark.integration
    @pytest.mark.docker
    def test_database_connectivity(self, docker_client):
        """Test de connectivité aux bases de données"""
        # Test PostgreSQL
        postgres_container = docker_client.containers.get("jarvis_memory_db")
        exec_result = postgres_container.exec_run(
            "pg_isready -U jarvis -d jarvis_memory"
        )
        assert exec_result.exit_code == 0, "PostgreSQL n'est pas prêt"
        
        # Test Redis
        redis_container = docker_client.containers.get("jarvis_redis")
        exec_result = redis_container.exec_run("redis-cli ping")
        assert b"PONG" in exec_result.output, "Redis ne répond pas"
    
    @pytest.mark.integration
    @pytest.mark.docker
    def test_resource_limits(self, docker_client, services_config):
        """Vérifie que les limites de ressources sont appliquées"""
        for service_name, config in services_config.items():
            try:
                container = docker_client.containers.get(config["container"])
                stats = container.stats(stream=False)
                
                # Vérifier les limites mémoire
                memory_limit = stats.get("memory_stats", {}).get("limit", 0)
                assert memory_limit > 0, f"{service_name} n'a pas de limite mémoire"
                
                # Vérifier l'utilisation CPU
                cpu_percent = self._calculate_cpu_percent(stats)
                assert cpu_percent < 90, f"{service_name} utilise trop de CPU : {cpu_percent}%"
                
            except docker.errors.NotFound:
                pytest.skip(f"Container {config['container']} non trouvé")
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calcule le pourcentage d'utilisation CPU"""
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                   stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                      stats["precpu_stats"]["system_cpu_usage"]
        
        if system_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * 100
            return round(cpu_percent, 2)
        return 0.0
    
    @pytest.mark.integration
    @pytest.mark.docker
    def test_network_isolation(self, docker_client):
        """Vérifie l'isolation réseau des services sensibles"""
        # Vérifier que les services sensibles sont sur le réseau sécurisé
        secure_services = ["jarvis_memory_db", "jarvis_redis"]
        
        for service_name in secure_services:
            try:
                container = docker_client.containers.get(service_name)
                networks = list(container.attrs["NetworkSettings"]["Networks"].keys())
                
                assert "jarvis_secure" in networks, \
                    f"{service_name} n'est pas sur le réseau sécurisé"
                
            except docker.errors.NotFound:
                pytest.skip(f"Container {service_name} non trouvé")