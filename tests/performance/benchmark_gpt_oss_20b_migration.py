#!/usr/bin/env python3
"""
🎯 JARVIS AI - Benchmark Performance GPT-OSS 20B Migration
Script de test performance pour valider les métriques d'analyse

Usage:
    python benchmark_gpt_oss_20b_migration.py --mode [baseline|hybrid|comparison]
    python benchmark_gpt_oss_20b_migration.py --load-test --concurrent 10 --duration 60
"""

import asyncio
import aiohttp
import json
import time
import argparse
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import psutil
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Résultat individuel de benchmark"""
    query_type: str
    model_used: str
    response_time: float
    token_count: int
    tokens_per_second: float
    gpu_memory_usage: float
    success: bool
    error: Optional[str] = None
    timestamp: float = 0

@dataclass
class BenchmarkSuite:
    """Suite complète de benchmarks"""
    config_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    avg_tokens_per_second: float
    total_tokens: int
    avg_gpu_memory: float
    max_gpu_memory: float
    results: List[BenchmarkResult]

class PerformanceBenchmark:
    """Benchmark suite pour migration GPT-OSS 20B"""
    
    def __init__(self):
        # Configuration endpoints
        self.endpoints = {
            "baseline": "http://localhost:8080",  # Brain API direct
            "hybrid": "http://localhost:5010",    # LLM Gateway
            "fallback": "http://localhost:11434"  # Ollama direct
        }
        
        # Queries de test pour différents types de complexité
        self.test_queries = {
            "simple": [
                "Hello, how are you?",
                "What's the weather like?", 
                "Tell me a joke",
                "What time is it?",
                "How do you say hello in French?"
            ],
            "medium": [
                "Explain the basics of machine learning",
                "How does Docker work internally?",
                "What are the benefits of microservices architecture?",
                "Compare React and Vue.js frameworks",
                "Describe the HTTP request lifecycle"
            ],
            "complex": [
                """Analyze this Python code for performance bottlenecks:
                def fibonacci(n):
                    if n <= 1: return n
                    return fibonacci(n-1) + fibonacci(n-2)
                """,
                """Design a scalable microservices architecture for an e-commerce platform 
                with high availability requirements and global distribution.""",
                """Explain the mathematical foundations of transformer neural networks 
                and their attention mechanism in detail.""",
                """Review this system design: 
                - API Gateway with rate limiting
                - Event-driven microservices
                - CQRS with Event Sourcing
                - Multi-tenant database sharding
                What are the potential issues and optimizations?""",
                """Implement a distributed lock manager with leader election,
                explaining the consensus algorithm and failure handling strategies."""
            ]
        }
        
    async def get_gpu_memory_usage(self) -> float:
        """Récupérer l'utilisation mémoire GPU (simulé pour Windows/AMD)"""
        try:
            # TODO: Implémenter avec rocm-smi si disponible
            # Pour l'instant, simulation basée sur l'activité système
            return psutil.virtual_memory().percent * 0.6  # Approximation
        except:
            return 0.0
            
    async def send_request(self, endpoint: str, query: str, model: str = None) -> BenchmarkResult:
        """Envoyer une requête et mesurer les performances"""
        start_time = time.time()
        gpu_before = await self.get_gpu_memory_usage()
        
        # Configuration payload selon l'endpoint
        if "5010" in endpoint:  # LLM Gateway
            payload = {
                "messages": [{"role": "user", "content": query}],
                "stream": False,
                "model": model or "auto"
            }
            endpoint_url = f"{endpoint}/api/chat"
        else:  # Direct Ollama
            payload = {
                "model": model or "llama3.2:3b",
                "prompt": query,
                "stream": False
            }
            endpoint_url = f"{endpoint}/api/generate"
            
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120)
            ) as session:
                async with session.post(endpoint_url, json=payload) as response:
                    response_data = await response.json()
                    response_time = time.time() - start_time
                    
                    # Parser réponse selon format
                    if "message" in response_data:
                        content = response_data["message"]["content"]
                        model_used = response_data.get("model", model or "unknown")
                    elif "response" in response_data:
                        content = response_data["response"]
                        model_used = response_data.get("model", model or "unknown")  
                    else:
                        content = str(response_data)
                        model_used = model or "unknown"
                    
                    # Calculer métriques tokens
                    token_count = len(content.split())
                    tokens_per_second = token_count / response_time if response_time > 0 else 0
                    
                    # Déterminer type de query
                    query_type = "simple"
                    if len(query) > 100:
                        query_type = "complex" if len(query) > 300 else "medium"
                    
                    return BenchmarkResult(
                        query_type=query_type,
                        model_used=model_used,
                        response_time=response_time,
                        token_count=token_count,
                        tokens_per_second=tokens_per_second,
                        gpu_memory_usage=gpu_before,
                        success=True,
                        timestamp=time.time()
                    )
                    
        except Exception as e:
            logger.error(f"❌ Erreur requête {endpoint}: {e}")
            return BenchmarkResult(
                query_type="error",
                model_used="error",
                response_time=time.time() - start_time,
                token_count=0,
                tokens_per_second=0,
                gpu_memory_usage=gpu_before,
                success=False,
                error=str(e),
                timestamp=time.time()
            )
    
    async def run_single_benchmark(self, config_name: str, endpoint: str, 
                                 query_types: List[str] = None) -> BenchmarkSuite:
        """Exécuter benchmark pour une configuration"""
        logger.info(f"🚀 Benchmark {config_name} - {endpoint}")
        
        query_types = query_types or ["simple", "medium", "complex"]
        all_results = []
        
        # Test chaque type de query
        for query_type in query_types:
            queries = self.test_queries[query_type]
            
            for query in queries:
                logger.info(f"   📝 Test {query_type}: {query[:50]}...")
                
                result = await self.send_request(endpoint, query)
                all_results.append(result)
                
                # Délai entre requêtes pour éviter saturation
                await asyncio.sleep(1)
        
        # Calculer statistiques
        successful_results = [r for r in all_results if r.success]
        response_times = [r.response_time for r in successful_results]
        tokens_per_second = [r.tokens_per_second for r in successful_results]
        gpu_usage = [r.gpu_memory_usage for r in all_results]
        
        suite = BenchmarkSuite(
            config_name=config_name,
            total_requests=len(all_results),
            successful_requests=len(successful_results),
            failed_requests=len(all_results) - len(successful_results),
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 5 else 0,
            p99_response_time=statistics.quantiles(response_times, n=100)[98] if len(response_times) > 10 else 0,
            avg_tokens_per_second=statistics.mean(tokens_per_second) if tokens_per_second else 0,
            total_tokens=sum(r.token_count for r in successful_results),
            avg_gpu_memory=statistics.mean(gpu_usage) if gpu_usage else 0,
            max_gpu_memory=max(gpu_usage) if gpu_usage else 0,
            results=all_results
        )
        
        return suite
    
    async def run_load_test(self, endpoint: str, concurrent: int = 10, 
                          duration: int = 60) -> BenchmarkSuite:
        """Test de charge avec requêtes concurrentes"""
        logger.info(f"🔥 Load test: {concurrent} concurrent requests for {duration}s")
        
        start_time = time.time()
        all_results = []
        tasks = []
        
        # Générateur de requêtes continues
        async def request_generator():
            query_types = list(self.test_queries.keys())
            i = 0
            while time.time() - start_time < duration:
                query_type = query_types[i % len(query_types)]
                queries = self.test_queries[query_type]
                query = queries[i % len(queries)]
                
                result = await self.send_request(endpoint, query)
                all_results.append(result)
                
                i += 1
                await asyncio.sleep(0.1)  # Petit délai
        
        # Lancer workers concurrents
        for _ in range(concurrent):
            tasks.append(asyncio.create_task(request_generator()))
        
        # Attendre fin du test
        await asyncio.sleep(duration)
        
        # Arrêter tous les workers
        for task in tasks:
            task.cancel()
        
        # Attendre arrêt propre
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"✅ Load test terminé: {len(all_results)} requêtes")
        
        # Calculer statistiques
        successful_results = [r for r in all_results if r.success]
        response_times = [r.response_time for r in successful_results]
        
        return BenchmarkSuite(
            config_name=f"load_test_c{concurrent}_d{duration}",
            total_requests=len(all_results),
            successful_requests=len(successful_results),
            failed_requests=len(all_results) - len(successful_results),
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 5 else 0,
            p99_response_time=statistics.quantiles(response_times, n=100)[98] if len(response_times) > 10 else 0,
            avg_tokens_per_second=statistics.mean([r.tokens_per_second for r in successful_results]) if successful_results else 0,
            total_tokens=sum(r.token_count for r in successful_results),
            avg_gpu_memory=statistics.mean([r.gpu_memory_usage for r in all_results]) if all_results else 0,
            max_gpu_memory=max([r.gpu_memory_usage for r in all_results]) if all_results else 0,
            results=all_results
        )
    
    def generate_report(self, suites: List[BenchmarkSuite]) -> str:
        """Générer rapport de performance"""
        report = f"""
# 📊 JARVIS AI - Rapport Performance Benchmark
Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Résumé Configurations Testées
"""
        
        for suite in suites:
            success_rate = (suite.successful_requests / suite.total_requests * 100) if suite.total_requests > 0 else 0
            
            report += f"""
### {suite.config_name}
- **Requêtes**: {suite.total_requests} ({suite.successful_requests} succès, {suite.failed_requests} échecs)
- **Taux succès**: {success_rate:.1f}%  
- **Temps réponse moyen**: {suite.avg_response_time:.2f}s
- **P95 temps réponse**: {suite.p95_response_time:.2f}s
- **P99 temps réponse**: {suite.p99_response_time:.2f}s
- **Throughput moyen**: {suite.avg_tokens_per_second:.1f} tokens/sec
- **Tokens total**: {suite.total_tokens:,}
- **GPU mémoire (moy/max)**: {suite.avg_gpu_memory:.1f}% / {suite.max_gpu_memory:.1f}%
"""
        
        # Comparaison si plusieurs suites
        if len(suites) > 1:
            report += "\n## 📈 Comparaison Performance\n"
            
            baseline = suites[0]
            for suite in suites[1:]:
                latency_ratio = (suite.avg_response_time / baseline.avg_response_time - 1) * 100
                throughput_ratio = (suite.avg_tokens_per_second / baseline.avg_tokens_per_second - 1) * 100
                
                report += f"""
### {suite.config_name} vs {baseline.config_name}
- **Latence**: {latency_ratio:+.1f}% ({suite.avg_response_time:.2f}s vs {baseline.avg_response_time:.2f}s)
- **Throughput**: {throughput_ratio:+.1f}% ({suite.avg_tokens_per_second:.1f} vs {baseline.avg_tokens_per_second:.1f} t/s)
"""
        
        # Recommendations
        report += """
## 🎯 Recommandations

### Performance Optimale Observée:
"""
        best_suite = min(suites, key=lambda s: s.avg_response_time)
        report += f"- **Configuration la plus rapide**: {best_suite.config_name} ({best_suite.avg_response_time:.2f}s)\n"
        
        best_throughput = max(suites, key=lambda s: s.avg_tokens_per_second)
        report += f"- **Meilleur throughput**: {best_throughput.config_name} ({best_throughput.avg_tokens_per_second:.1f} t/s)\n"
        
        return report
    
    def save_results(self, suites: List[BenchmarkSuite], filename: str = None):
        """Sauvegarder résultats en JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"benchmark_results_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "suites": [asdict(suite) for suite in suites]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Résultats sauvegardés: {filename}")

async def main():
    """Main benchmark execution"""
    parser = argparse.ArgumentParser(description="JARVIS AI Performance Benchmark")
    parser.add_argument("--mode", choices=["baseline", "hybrid", "comparison", "all"], 
                       default="all", help="Mode de benchmark")
    parser.add_argument("--load-test", action="store_true", help="Activer test de charge")
    parser.add_argument("--concurrent", type=int, default=10, help="Requêtes concurrentes")
    parser.add_argument("--duration", type=int, default=60, help="Durée test (secondes)")
    parser.add_argument("--output", help="Fichier de sortie")
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark()
    suites = []
    
    try:
        if args.mode == "baseline" or args.mode == "all":
            # Test configuration baseline (llama3.2:3b container)
            suite = await benchmark.run_single_benchmark(
                "Baseline_llama3.2:3b", 
                benchmark.endpoints["baseline"]
            )
            suites.append(suite)
            
        if args.mode == "hybrid" or args.mode == "all":
            # Test configuration hybride (LLM Gateway)
            suite = await benchmark.run_single_benchmark(
                "Hybrid_LLM_Gateway",
                benchmark.endpoints["hybrid"]
            )
            suites.append(suite)
            
        if args.load_test:
            # Test de charge sur configuration hybride
            load_suite = await benchmark.run_load_test(
                benchmark.endpoints["hybrid"],
                concurrent=args.concurrent,
                duration=args.duration
            )
            suites.append(load_suite)
        
        # Générer rapport
        report = benchmark.generate_report(suites)
        print(report)
        
        # Sauvegarder résultats
        benchmark.save_results(suites, args.output)
        
        # Résumé final
        logger.info("🎉 Benchmark terminé avec succès!")
        logger.info(f"📊 {len(suites)} configuration(s) testée(s)")
        
        total_requests = sum(s.total_requests for s in suites)
        total_successful = sum(s.successful_requests for s in suites)
        logger.info(f"📈 {total_requests} requêtes total ({total_successful} succès)")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Benchmark interrompu par utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur benchmark: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())