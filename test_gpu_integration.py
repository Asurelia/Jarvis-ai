#!/usr/bin/env python3
"""
🧪 Test d'intégration GPU Stats Service - JARVIS AI
Script pour valider le fonctionnement du service GPU et son intégration
"""

import asyncio
import aiohttp
import json
import time
import websockets
from typing import Dict, Any
import sys
import os

# Ajouter le répertoire racine au PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class GPUStatsIntegrationTest:
    def __init__(self):
        self.base_url = "http://localhost:5009"
        self.ws_url = "ws://localhost:5009/ws/gpu-stats"
        self.test_results = []
        
    async def test_health_endpoint(self) -> bool:
        """Test du health check"""
        print("🔍 Test health endpoint...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Health check OK: {data}")
                        return True
                    else:
                        print(f"❌ Health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_gpu_info_endpoint(self) -> bool:
        """Test de l'endpoint info GPU"""
        print("🔍 Test GPU info endpoint...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/gpu/info") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ GPU Info OK:")
                        print(f"   - Nom: {data.get('gpu_info', {}).get('name', 'Unknown')}")
                        print(f"   - VRAM: {data.get('gpu_info', {}).get('memory_total', 0)} MB")
                        print(f"   - Driver: {data.get('gpu_info', {}).get('driver_version', 'Unknown')}")
                        return True
                    else:
                        print(f"❌ GPU Info failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ GPU Info error: {e}")
            return False
    
    async def test_gpu_stats_endpoint(self) -> bool:
        """Test de l'endpoint stats GPU"""
        print("🔍 Test GPU stats endpoint...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/gpu/stats") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ GPU Stats OK:")
                        print(f"   - Température: {data.get('temperature', 0):.1f}°C")
                        print(f"   - Utilisation: {data.get('utilization', 0):.1f}%")
                        print(f"   - VRAM: {data.get('memory_utilization', 0):.1f}%")
                        print(f"   - Power: {data.get('power_usage', 0):.1f}W")
                        print(f"   - Statut: {data.get('status', 'unknown')}")
                        return True
                    else:
                        print(f"❌ GPU Stats failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ GPU Stats error: {e}")
            return False
    
    async def test_gpu_history_endpoint(self) -> bool:
        """Test de l'endpoint historique"""
        print("🔍 Test GPU history endpoint...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/gpu/history?minutes=1") as response:
                    if response.status == 200:
                        data = await response.json()
                        history = data.get('history', [])
                        print(f"✅ GPU History OK: {len(history)} entrées")
                        if history:
                            latest = history[-1]
                            print(f"   - Dernière mesure: {latest.get('utilization', 0):.1f}% GPU")
                        return True
                    else:
                        print(f"❌ GPU History failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ GPU History error: {e}")
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test de la connexion WebSocket"""
        print("🔍 Test WebSocket connection...")
        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("✅ WebSocket connecté")
                
                # Envoyer un ping pour maintenir la connexion
                await websocket.send("ping")
                
                # Attendre quelques messages
                messages_received = 0
                start_time = time.time()
                
                while messages_received < 3 and (time.time() - start_time) < 10:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        
                        if data.get('type') == 'gpu_stats':
                            messages_received += 1
                            stats = data.get('data', {})
                            print(f"✅ Message WebSocket #{messages_received}:")
                            print(f"   - GPU: {stats.get('utilization', 0):.1f}%")
                            print(f"   - Temp: {stats.get('temperature', 0):.1f}°C")
                    
                    except asyncio.TimeoutError:
                        print("⏱️ Timeout en attente de message WebSocket")
                        break
                
                if messages_received >= 3:
                    print(f"✅ WebSocket OK: {messages_received} messages reçus")
                    return True
                else:
                    print(f"⚠️ WebSocket partiel: seulement {messages_received} messages")
                    return messages_received > 0
                    
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            return False
    
    async def test_docker_service_health(self) -> bool:
        """Test de l'état du service Docker"""
        print("🔍 Test Docker service health...")
        try:
            import subprocess
            
            # Vérifier si le container est running
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=jarvis_gpu_stats", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "Up" in result.stdout:
                print("✅ Container Docker running")
                
                # Vérifier les logs récents
                log_result = subprocess.run(
                    ["docker", "logs", "--tail", "5", "jarvis_gpu_stats"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if log_result.returncode == 0:
                    print("✅ Logs Docker accessibles")
                    print("📋 Logs récents:")
                    for line in log_result.stdout.split('\n')[-3:]:
                        if line.strip():
                            print(f"   {line}")
                    return True
                else:
                    print("⚠️ Logs Docker non accessibles")
                    return True  # Container fonctionne même si logs inaccessibles
            else:
                print("❌ Container Docker non running")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏱️ Timeout lors de la vérification Docker")
            return False
        except Exception as e:
            print(f"❌ Docker health error: {e}")
            return False
    
    async def test_frontend_integration(self) -> bool:
        """Test d'intégration avec le frontend"""
        print("🔍 Test intégration frontend...")
        try:
            # Vérifier si le port frontend est accessible
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get("http://localhost:3000", timeout=5) as response:
                        if response.status == 200:
                            print("✅ Frontend accessible sur port 3000")
                            return True
                        else:
                            print(f"⚠️ Frontend répond avec status {response.status}")
                            return False
                except aiohttp.ClientConnectorError:
                    print("⚠️ Frontend non accessible (service probablement arrêté)")
                    return False
                    
        except Exception as e:
            print(f"❌ Frontend integration error: {e}")
            return False
    
    async def run_performance_test(self) -> bool:
        """Test de performance du service"""
        print("🔍 Test performance du service...")
        try:
            start_time = time.time()
            requests_count = 10
            success_count = 0
            
            async with aiohttp.ClientSession() as session:
                for i in range(requests_count):
                    try:
                        async with session.get(f"{self.base_url}/gpu/stats") as response:
                            if response.status == 200:
                                success_count += 1
                    except Exception:
                        pass
            
            total_time = time.time() - start_time
            avg_response_time = (total_time / requests_count) * 1000  # en ms
            success_rate = (success_count / requests_count) * 100
            
            print(f"✅ Performance test:")
            print(f"   - {requests_count} requêtes en {total_time:.2f}s")
            print(f"   - Temps moyen: {avg_response_time:.1f}ms")
            print(f"   - Taux de succès: {success_rate:.1f}%")
            
            return success_rate >= 90 and avg_response_time < 1000
            
        except Exception as e:
            print(f"❌ Performance test error: {e}")
            return False
    
    async def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 Démarrage des tests d'intégration GPU Stats Service\n")
        
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("GPU Info", self.test_gpu_info_endpoint),
            ("GPU Stats", self.test_gpu_stats_endpoint),
            ("GPU History", self.test_gpu_history_endpoint),
            ("WebSocket", self.test_websocket_connection),
            ("Docker Health", self.test_docker_service_health),
            ("Frontend Integration", self.test_frontend_integration),
            ("Performance", self.run_performance_test),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            print(f"🧪 Test: {test_name}")
            print('='*50)
            
            try:
                result = await test_func()
                if result:
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"💥 {test_name}: ERROR - {e}")
            
            # Pause entre les tests
            await asyncio.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"📊 RÉSULTATS FINAUX")
        print('='*60)
        print(f"✅ Tests réussis: {passed}/{total} ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 TOUS LES TESTS SONT PASSÉS!")
            print("🚀 L'intégration GPU Stats est opérationnelle")
        elif passed >= total * 0.8:
            print("⚠️ La plupart des tests sont passés")
            print("🔧 Quelques ajustements peuvent être nécessaires")
        else:
            print("❌ Plusieurs tests ont échoué")
            print("🛠️ Une révision de l'implémentation est nécessaire")
        
        print(f"\n💡 Pour démarrer le service:")
        print(f"   docker-compose up gpu-stats-service")
        print(f"\n🌐 URLs importantes:")
        print(f"   - API: http://localhost:5009")
        print(f"   - Health: http://localhost:5009/health")
        print(f"   - Stats: http://localhost:5009/gpu/stats")
        print(f"   - WebSocket: ws://localhost:5009/ws/gpu-stats")
        
        return passed >= total * 0.8

async def main():
    """Point d'entrée principal"""
    tester = GPUStatsIntegrationTest()
    
    # Attendre un peu pour laisser le temps aux services de démarrer
    print("⏳ Attente de 5 secondes pour le démarrage des services...")
    await asyncio.sleep(5)
    
    success = await tester.run_all_tests()
    
    # Code de sortie pour CI/CD
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())