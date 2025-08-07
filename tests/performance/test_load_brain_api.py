"""
Tests de performance et charge pour Brain API JARVIS
"""

import pytest
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

class TestBrainAPIPerformance:
    """Tests de performance pour Brain API"""
    
    BASE_URL = "http://localhost:8080"
    
    @pytest.fixture
    def performance_thresholds(self) -> Dict[str, float]:
        """Seuils de performance acceptables"""
        return {
            "chat_latency_p95": 500,      # 95e percentile < 500ms
            "chat_latency_p99": 1000,     # 99e percentile < 1s
            "health_latency_avg": 50,      # Health check < 50ms moyenne
            "websocket_latency": 100,      # WebSocket < 100ms
            "throughput_min": 100,         # Minimum 100 req/s
            "error_rate_max": 0.01,        # Maximum 1% d'erreurs
            "memory_increase_max": 100     # Maximum 100MB d'augmentation mémoire
        }
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_chat_endpoint_latency(self, performance_thresholds):
        """Test de latence de l'endpoint /api/chat"""
        latencies = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(100):
                start_time = time.time()
                
                try:
                    async with session.post(
                        f"{self.BASE_URL}/api/chat",
                        json={"message": f"Test message {i}"},
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        await response.json()
                        latency = (time.time() - start_time) * 1000  # en ms
                        latencies.append(latency)
                        
                except Exception as e:
                    pytest.fail(f"Erreur requête chat : {str(e)}")
                
                await asyncio.sleep(0.05)  # 50ms entre requêtes
        
        # Analyser les résultats
        p95 = statistics.quantiles(latencies, n=20)[18]  # 95e percentile
        p99 = statistics.quantiles(latencies, n=100)[98]  # 99e percentile
        avg = statistics.mean(latencies)
        
        print(f"\nLatence Chat API - Avg: {avg:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms")
        
        assert p95 < performance_thresholds["chat_latency_p95"], \
            f"P95 latency {p95:.2f}ms dépasse le seuil {performance_thresholds['chat_latency_p95']}ms"
        assert p99 < performance_thresholds["chat_latency_p99"], \
            f"P99 latency {p99:.2f}ms dépasse le seuil {performance_thresholds['chat_latency_p99']}ms"
    
    @pytest.mark.performance
    def test_concurrent_load(self, performance_thresholds):
        """Test de charge avec requêtes concurrentes"""
        concurrent_users = 50
        requests_per_user = 10
        total_requests = concurrent_users * requests_per_user
        
        successful_requests = 0
        failed_requests = 0
        latencies = []
        
        def make_request(user_id: int, request_id: int):
            """Effectue une requête pour un utilisateur"""
            import requests
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.BASE_URL}/api/chat",
                    json={"message": f"User {user_id} request {request_id}"},
                    timeout=5
                )
                latency = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    return True, latency
                else:
                    return False, latency
                    
            except Exception:
                return False, 5000  # Timeout = 5s
        
        # Lancer les requêtes concurrentes
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            for user_id in range(concurrent_users):
                for request_id in range(requests_per_user):
                    future = executor.submit(make_request, user_id, request_id)
                    futures.append(future)
            
            for future in as_completed(futures):
                success, latency = future.result()
                if success:
                    successful_requests += 1
                    latencies.append(latency)
                else:
                    failed_requests += 1
        
        total_time = time.time() - start_time
        throughput = total_requests / total_time
        error_rate = failed_requests / total_requests
        
        print(f"\nCharge concurrente - Throughput: {throughput:.2f} req/s, "
              f"Erreurs: {error_rate*100:.2f}%, Latence moy: {statistics.mean(latencies):.2f}ms")
        
        assert throughput >= performance_thresholds["throughput_min"], \
            f"Throughput {throughput:.2f} req/s inférieur au minimum {performance_thresholds['throughput_min']} req/s"
        assert error_rate <= performance_thresholds["error_rate_max"], \
            f"Taux d'erreur {error_rate*100:.2f}% supérieur au maximum {performance_thresholds['error_rate_max']*100}%"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_websocket_performance(self, performance_thresholds):
        """Test de performance WebSocket"""
        import websockets
        
        latencies = []
        messages_sent = 100
        
        try:
            async with websockets.connect("ws://localhost:5001/ws") as websocket:
                for i in range(messages_sent):
                    start_time = time.time()
                    
                    # Envoyer message
                    await websocket.send(f'{{"type": "chat", "message": "Test {i}"}}')
                    
                    # Attendre réponse
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    
                    latency = (time.time() - start_time) * 1000
                    latencies.append(latency)
                    
                    await asyncio.sleep(0.01)  # 10ms entre messages
                    
        except Exception as e:
            pytest.fail(f"Erreur WebSocket : {str(e)}")
        
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        
        print(f"\nWebSocket Performance - Latence moy: {avg_latency:.2f}ms, Max: {max_latency:.2f}ms")
        
        assert avg_latency < performance_thresholds["websocket_latency"], \
            f"Latence WebSocket moyenne {avg_latency:.2f}ms dépasse le seuil {performance_thresholds['websocket_latency']}ms"
    
    @pytest.mark.performance
    def test_memory_leak(self, performance_thresholds):
        """Test de fuite mémoire sous charge"""
        import psutil
        import gc
        
        # Mesure initiale
        gc.collect()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Effectuer beaucoup de requêtes
        import requests
        for i in range(500):
            try:
                requests.post(
                    f"{self.BASE_URL}/api/chat",
                    json={"message": f"Memory test {i}"},
                    timeout=5
                )
            except:
                pass
            
            if i % 100 == 0:
                gc.collect()
        
        # Mesure finale
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\nMémoire - Initial: {initial_memory:.2f}MB, "
              f"Final: {final_memory:.2f}MB, Augmentation: {memory_increase:.2f}MB")
        
        assert memory_increase < performance_thresholds["memory_increase_max"], \
            f"Augmentation mémoire {memory_increase:.2f}MB dépasse le seuil {performance_thresholds['memory_increase_max']}MB"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_endpoint_performance_comparison(self):
        """Compare les performances des différents endpoints"""
        endpoints = [
            ("/health", "GET", None),
            ("/api/chat", "POST", {"message": "Test"}),
            ("/api/memory/search", "GET", None),
            ("/api/agent/status", "GET", None),
            ("/api/metacognition/reflect", "POST", {"thought": "Test"}),
            ("/api/persona/current", "GET", None)
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method, data in endpoints:
                latencies = []
                
                for _ in range(50):
                    start_time = time.time()
                    
                    try:
                        if method == "GET":
                            async with session.get(
                                f"{self.BASE_URL}{endpoint}",
                                timeout=aiohttp.ClientTimeout(total=5)
                            ) as response:
                                await response.text()
                        else:
                            async with session.post(
                                f"{self.BASE_URL}{endpoint}",
                                json=data,
                                timeout=aiohttp.ClientTimeout(total=5)
                            ) as response:
                                await response.text()
                        
                        latency = (time.time() - start_time) * 1000
                        latencies.append(latency)
                        
                    except:
                        latencies.append(5000)  # Timeout
                    
                    await asyncio.sleep(0.02)
                
                results[endpoint] = {
                    "avg": statistics.mean(latencies),
                    "min": min(latencies),
                    "max": max(latencies),
                    "p95": statistics.quantiles(latencies, n=20)[18]
                }
        
        # Afficher les résultats
        print("\n=== Performance par Endpoint ===")
        for endpoint, metrics in sorted(results.items(), key=lambda x: x[1]["avg"]):
            print(f"{endpoint:30} - Avg: {metrics['avg']:6.2f}ms, "
                  f"P95: {metrics['p95']:6.2f}ms, "
                  f"Min: {metrics['min']:6.2f}ms, "
                  f"Max: {metrics['max']:6.2f}ms")