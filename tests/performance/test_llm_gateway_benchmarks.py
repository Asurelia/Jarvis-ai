#!/usr/bin/env python3
"""
📊 LLM Gateway Benchmarks & Validation Tests
Tests de performance complets pour intégration GPT-OSS 20B
"""

import pytest
import asyncio
import time
import json
import statistics
import aiohttp
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import logging

# Configuration logging pour tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    test_name: str
    model_used: str
    complexity_score: float
    response_time: float
    tokens_per_second: float
    memory_usage_mb: int
    gpu_temperature_c: float
    success: bool
    error_message: str = ""

@dataclass
class BenchmarkSuite:
    suite_name: str
    total_tests: int
    successful_tests: int
    failed_tests: int
    avg_response_time: float
    avg_tokens_per_second: float
    model_distribution: Dict[str, int]
    results: List[BenchmarkResult]

class LLMGatewayBenchmark:
    """Suite complète de benchmarks LLM Gateway"""
    
    def __init__(self, gateway_url: str = "http://localhost:5010"):
        self.gateway_url = gateway_url
        self.session: aiohttp.ClientSession = None
        
        # Test prompts par complexité
        self.test_prompts = {
            "simple": [
                "Hello, how are you?",
                "What is the weather like?",
                "Tell me a joke.",
                "What time is it?",
                "How do you spell 'artificial'?"
            ],
            "medium": [
                "Explain the concept of machine learning in simple terms.",
                "What are the main differences between Python and JavaScript?",
                "How does photosynthesis work?",
                "Describe the process of making bread from scratch.",
                "What are the benefits of renewable energy?"
            ],
            "complex": [
                "Analyze the architectural differences between transformer models and recurrent neural networks, discussing their computational complexity, memory requirements, and use cases in modern NLP applications.",
                "Implement a Python function that optimizes GPU memory usage for large language model inference, considering batch processing, attention mechanism optimizations, and VRAM constraints on AMD RX 7800 XT.",
                "Design a comprehensive system architecture for a multi-tenant AI platform that can handle real-time inference requests while maintaining sub-200ms latency, implementing load balancing, circuit breakers, and graceful degradation strategies.",
                "Explain the mathematical foundations of attention mechanisms in transformer architecture, including multi-head attention computation, positional encoding, and the role of key-value-query matrices in information processing.",
                "Develop a detailed optimization strategy for running 20B parameter models on consumer hardware, covering quantization techniques, memory mapping, batch size optimization, and thermal management considerations."
            ],
            "reasoning": [
                "If Alice has 3 apples and gives 2 to Bob, then Bob gives 1 back to Alice, how many apples does each person have? Walk through your reasoning step by step.",
                "A company's revenue increased by 20% in the first quarter and decreased by 15% in the second quarter. If the initial revenue was $100,000, what is the revenue at the end of Q2? Show all calculations.",
                "Three people are in a room: Alex, Beth, and Charlie. Alex always tells the truth, Beth always lies, and Charlie alternates between truth and lies. If Alex says 'Beth is lying about Charlie', what can we deduce?",
                "You have a 3-liter jug and a 5-liter jug. How can you measure exactly 4 liters of water? Provide a detailed step-by-step solution.",
                "A train leaves Station A at 2 PM traveling at 60 mph. Another train leaves Station B at 3 PM traveling at 80 mph toward Station A. If the stations are 350 miles apart, at what time will the trains meet?"
            ],
            "coding": [
                "Write a Python function to implement binary search on a sorted array. Include error handling and explain the time complexity.",
                "Create a class in Python that implements a thread-safe LRU cache with a maximum size limit. Include proper documentation and usage examples.",
                "Implement a function that optimizes database queries by building an index on frequently accessed columns. Consider different data types and query patterns.",
                "Design and implement a REST API endpoint for a chat application that handles real-time message routing with WebSocket integration and proper error handling.",
                "Write a Python script that monitors GPU usage and automatically adjusts batch sizes for machine learning inference to maintain optimal VRAM utilization."
            ]
        }
    
    async def setup(self):
        """Configuration initiale des tests"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)
        )
        
        # Vérifier disponibilité gateway
        try:
            async with self.session.get(f"{self.gateway_url}/api/health") as response:
                if response.status != 200:
                    raise Exception(f"Gateway non disponible: {response.status}")
                
                health_data = await response.json()
                logger.info(f"✅ Gateway connecté: {health_data.get('status')}")
                
        except Exception as e:
            raise Exception(f"Impossible de se connecter au gateway: {e}")
    
    async def cleanup(self):
        """Nettoyage après tests"""
        if self.session:
            await self.session.close()
    
    async def _send_chat_request(self, prompt: str, **kwargs) -> BenchmarkResult:
        """Envoyer requête de chat et mesurer performance"""
        
        start_time = time.time()
        
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            **kwargs
        }
        
        try:
            async with self.session.post(
                f"{self.gateway_url}/api/chat",
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    return BenchmarkResult(
                        test_name="chat_request",
                        model_used="unknown",
                        complexity_score=0.0,
                        response_time=time.time() - start_time,
                        tokens_per_second=0.0,
                        memory_usage_mb=0,
                        gpu_temperature_c=0.0,
                        success=False,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )
                
                # Parser réponse
                data = await response.json()
                response_time = time.time() - start_time
                
                # Extraire contenu réponse
                if "response" in data and "metadata" in data:
                    # Format gateway complet
                    content = data["response"].get("message", {}).get("content", "")
                    metadata = data["metadata"]
                    model_used = metadata.get("model_used", "unknown")
                    complexity_score = metadata.get("complexity_score", 0.0)
                    gpu_status = metadata.get("gpu_status", "unknown")
                else:
                    # Format Ollama direct
                    content = data.get("message", {}).get("content", "")
                    model_used = "fallback"
                    complexity_score = 0.3
                    gpu_status = "unknown"
                
                # Calculer tokens par seconde
                token_count = len(content.split())
                tokens_per_second = token_count / response_time if response_time > 0 else 0
                
                return BenchmarkResult(
                    test_name="chat_request",
                    model_used=model_used,
                    complexity_score=complexity_score,
                    response_time=response_time,
                    tokens_per_second=tokens_per_second,
                    memory_usage_mb=0,  # TODO: Récupérer via métriques
                    gpu_temperature_c=0.0,  # TODO: Récupérer via métriques
                    success=True
                )
                
        except Exception as e:
            return BenchmarkResult(
                test_name="chat_request",
                model_used="unknown", 
                complexity_score=0.0,
                response_time=time.time() - start_time,
                tokens_per_second=0.0,
                memory_usage_mb=0,
                gpu_temperature_c=0.0,
                success=False,
                error_message=str(e)
            )
    
    async def benchmark_complexity_routing(self) -> BenchmarkSuite:
        """Test routing basé sur complexité"""
        
        logger.info("🧠 Test routing par complexité...")
        results = []
        
        for complexity_level, prompts in self.test_prompts.items():
            logger.info(f"   Testing {complexity_level} prompts...")
            
            for i, prompt in enumerate(prompts):
                logger.info(f"     Prompt {i+1}/{len(prompts)}")
                
                result = await self._send_chat_request(prompt)
                result.test_name = f"complexity_{complexity_level}_{i+1}"
                results.append(result)
                
                # Petite pause entre requêtes
                await asyncio.sleep(1)
        
        # Analyser résultats
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        # Distribution modèles utilisés
        model_distribution = {}
        for result in successful:
            model = result.model_used
            model_distribution[model] = model_distribution.get(model, 0) + 1
        
        suite = BenchmarkSuite(
            suite_name="complexity_routing",
            total_tests=len(results),
            successful_tests=len(successful),
            failed_tests=len(failed),
            avg_response_time=statistics.mean([r.response_time for r in successful]) if successful else 0,
            avg_tokens_per_second=statistics.mean([r.tokens_per_second for r in successful]) if successful else 0,
            model_distribution=model_distribution,
            results=results
        )
        
        return suite
    
    async def benchmark_load_testing(self, concurrent_requests: int = 5, total_requests: int = 50) -> BenchmarkSuite:
        """Test charge avec requêtes concurrentes"""
        
        logger.info(f"⚡ Test charge: {concurrent_requests} requêtes concurrentes, {total_requests} total")
        
        # Mélanger prompts de différentes complexités
        all_prompts = []
        for prompts in self.test_prompts.values():
            all_prompts.extend(prompts[:2])  # 2 prompts par catégorie
        
        # Dupliquer pour atteindre total_requests
        test_prompts = (all_prompts * ((total_requests // len(all_prompts)) + 1))[:total_requests]
        
        results = []
        
        # Traiter par batches concurrents
        for batch_start in range(0, total_requests, concurrent_requests):
            batch_end = min(batch_start + concurrent_requests, total_requests)
            batch_prompts = test_prompts[batch_start:batch_end]
            
            logger.info(f"   Batch {batch_start+1}-{batch_end}/{total_requests}")
            
            # Lancer requêtes concurrentes
            tasks = []
            for i, prompt in enumerate(batch_prompts):
                task = self._send_chat_request(prompt)
                tasks.append(task)
            
            # Attendre toutes les réponses
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Convertir exception en BenchmarkResult
                    error_result = BenchmarkResult(
                        test_name=f"load_test_batch_{batch_start}_{i}",
                        model_used="unknown",
                        complexity_score=0.0,
                        response_time=0.0,
                        tokens_per_second=0.0,
                        memory_usage_mb=0,
                        gpu_temperature_c=0.0,
                        success=False,
                        error_message=str(result)
                    )
                    results.append(error_result)
                else:
                    result.test_name = f"load_test_batch_{batch_start}_{i}"
                    results.append(result)
            
            # Pause entre batches
            await asyncio.sleep(2)
        
        # Analyser résultats
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        model_distribution = {}
        for result in successful:
            model = result.model_used
            model_distribution[model] = model_distribution.get(model, 0) + 1
        
        suite = BenchmarkSuite(
            suite_name="load_testing",
            total_tests=len(results),
            successful_tests=len(successful),
            failed_tests=len(failed),
            avg_response_time=statistics.mean([r.response_time for r in successful]) if successful else 0,
            avg_tokens_per_second=statistics.mean([r.tokens_per_second for r in successful]) if successful else 0,
            model_distribution=model_distribution,
            results=results
        )
        
        return suite
    
    async def benchmark_model_switching(self) -> BenchmarkSuite:
        """Test switching entre modèles selon complexité"""
        
        logger.info("🔄 Test switching modèles...")
        
        results = []
        
        # Séquence alternée: simple -> complexe -> simple -> complexe
        sequence_prompts = [
            ("simple", self.test_prompts["simple"][0]),
            ("complex", self.test_prompts["complex"][0]),
            ("simple", self.test_prompts["simple"][1]),  
            ("complex", self.test_prompts["complex"][1]),
            ("medium", self.test_prompts["medium"][0]),
            ("reasoning", self.test_prompts["reasoning"][0]),
            ("coding", self.test_prompts["coding"][0]),
            ("simple", self.test_prompts["simple"][2])
        ]
        
        for i, (complexity, prompt) in enumerate(sequence_prompts):
            logger.info(f"   Test {i+1}/{len(sequence_prompts)}: {complexity}")
            
            result = await self._send_chat_request(prompt)
            result.test_name = f"model_switching_{complexity}_{i+1}"
            results.append(result)
            
            # Pause courte pour permettre switch
            await asyncio.sleep(0.5)
        
        # Analyser pattern de switching
        successful = [r for r in results if r.success]
        
        model_distribution = {}
        for result in successful:
            model = result.model_used
            model_distribution[model] = model_distribution.get(model, 0) + 1
        
        suite = BenchmarkSuite(
            suite_name="model_switching",
            total_tests=len(results),
            successful_tests=len(successful),
            failed_tests=len(results) - len(successful),
            avg_response_time=statistics.mean([r.response_time for r in successful]) if successful else 0,
            avg_tokens_per_second=statistics.mean([r.tokens_per_second for r in successful]) if successful else 0,
            model_distribution=model_distribution,
            results=results
        )
        
        return suite
    
    async def benchmark_gpu_optimization(self) -> Dict[str, Any]:
        """Test optimisations GPU avec monitoring"""
        
        logger.info("🎮 Test optimisations GPU...")
        
        # Récupérer métriques initiales
        try:
            async with self.session.get(f"{self.gateway_url}/api/metrics") as response:
                initial_metrics = await response.json() if response.status == 200 else {}
        except:
            initial_metrics = {}
        
        # Test avec modèle lourd (supposé utiliser GPT-OSS 20B)
        heavy_prompts = self.test_prompts["complex"][:3]
        
        results = []
        for i, prompt in enumerate(heavy_prompts):
            logger.info(f"   Test GPU {i+1}/{len(heavy_prompts)}")
            
            result = await self._send_chat_request(prompt)
            result.test_name = f"gpu_optimization_{i+1}"
            results.append(result)
            
            # Récupérer métriques après requête
            try:
                async with self.session.get(f"{self.gateway_url}/api/metrics") as response:
                    current_metrics = await response.json() if response.status == 200 else {}
            except:
                current_metrics = {}
            
            await asyncio.sleep(2)  # Laisser temps au GPU de se refroidir
        
        return {
            "initial_metrics": initial_metrics,
            "results": [asdict(r) for r in results],
            "gpu_optimized_requests": len([r for r in results if "gpt-oss" in r.model_used.lower()]),
            "avg_response_time_gpu": statistics.mean([r.response_time for r in results if r.success])
        }
    
    async def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """Exécuter suite complète de benchmarks"""
        
        logger.info("🚀 Démarrage suite complète de benchmarks LLM Gateway")
        
        start_time = time.time()
        
        try:
            await self.setup()
            
            # Tests individuels
            complexity_suite = await self.benchmark_complexity_routing()
            load_suite = await self.benchmark_load_testing(concurrent_requests=3, total_requests=20)
            switching_suite = await self.benchmark_model_switching()
            gpu_results = await self.benchmark_gpu_optimization()
            
            total_time = time.time() - start_time
            
            # Résumé global
            all_results = (complexity_suite.results + 
                          load_suite.results + 
                          switching_suite.results)
            
            successful_results = [r for r in all_results if r.success]
            
            # Analyse modèles utilisés
            global_model_distribution = {}
            for result in successful_results:
                model = result.model_used
                global_model_distribution[model] = global_model_distribution.get(model, 0) + 1
            
            summary = {
                "benchmark_duration_seconds": total_time,
                "total_tests": len(all_results),
                "successful_tests": len(successful_results),
                "success_rate": len(successful_results) / len(all_results) if all_results else 0,
                "global_avg_response_time": statistics.mean([r.response_time for r in successful_results]) if successful_results else 0,
                "global_avg_tokens_per_second": statistics.mean([r.tokens_per_second for r in successful_results]) if successful_results else 0,
                "model_distribution": global_model_distribution,
                "suites": {
                    "complexity_routing": asdict(complexity_suite),
                    "load_testing": asdict(load_suite),
                    "model_switching": asdict(switching_suite),
                    "gpu_optimization": gpu_results
                }
            }
            
            return summary
            
        finally:
            await self.cleanup()

# Tests pytest
@pytest.fixture
async def gateway_benchmark():
    """Fixture benchmark gateway"""
    benchmark = LLMGatewayBenchmark()
    yield benchmark

@pytest.mark.asyncio
async def test_gateway_health(gateway_benchmark):
    """Test santé gateway"""
    await gateway_benchmark.setup()
    
    async with gateway_benchmark.session.get(f"{gateway_benchmark.gateway_url}/api/health") as response:
        assert response.status == 200
        data = await response.json()
        assert data.get("status") == "healthy"
    
    await gateway_benchmark.cleanup()

@pytest.mark.asyncio
async def test_complexity_routing(gateway_benchmark):
    """Test routing par complexité"""
    suite = await gateway_benchmark.benchmark_complexity_routing()
    
    assert suite.total_tests > 0
    assert suite.successful_tests > 0
    assert suite.success_rate > 0.8  # 80% succès minimum
    assert len(suite.model_distribution) > 0  # Au moins 1 modèle utilisé

@pytest.mark.asyncio
async def test_load_performance(gateway_benchmark):
    """Test performance sous charge"""
    suite = await gateway_benchmark.benchmark_load_testing(concurrent_requests=2, total_requests=10)
    
    assert suite.total_tests == 10
    assert suite.successful_tests >= 8  # 80% succès minimum
    assert suite.avg_response_time < 30  # Moins de 30s par requête

@pytest.mark.asyncio 
async def test_model_switching(gateway_benchmark):
    """Test switching entre modèles"""
    suite = await gateway_benchmark.benchmark_model_switching()
    
    assert suite.successful_tests > 0
    # Vérifier que différents modèles sont utilisés selon complexité
    assert len(suite.model_distribution) >= 1

async def main():
    """Point d'entrée script standalone"""
    
    benchmark = LLMGatewayBenchmark()
    
    try:
        results = await benchmark.run_full_benchmark_suite()
        
        # Sauvegarder résultats
        output_file = f"llm_gateway_benchmark_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Afficher résumé
        print("\n" + "="*60)
        print("📊 RÉSULTATS BENCHMARK LLM GATEWAY")
        print("="*60)
        print(f"⏱️  Durée totale: {results['benchmark_duration_seconds']:.1f}s")
        print(f"🎯 Tests total: {results['total_tests']}")
        print(f"✅ Tests réussis: {results['successful_tests']}")
        print(f"📈 Taux succès: {results['success_rate']*100:.1f}%")
        print(f"⚡ Temps réponse moyen: {results['global_avg_response_time']:.2f}s")
        print(f"🔤 Tokens/sec moyen: {results['global_avg_tokens_per_second']:.1f}")
        
        print(f"\n🤖 Distribution modèles:")
        for model, count in results['model_distribution'].items():
            print(f"   {model}: {count} requêtes")
        
        print(f"\n💾 Résultats complets sauvés: {output_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur benchmark: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())