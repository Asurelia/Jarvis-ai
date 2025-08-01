#!/usr/bin/env python3
"""
📊 JARVIS Performance Benchmark Suite
Tests de performance pour mesurer l'impact des optimisations
"""

import asyncio
import json
import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict

import httpx
import psutil
import redis.asyncio as redis
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkConfig:
    """Configuration des benchmarks"""
    # Endpoints à tester
    endpoints: Dict[str, str] = None
    
    # Paramètres de charge
    concurrent_users: int = 10
    requests_per_user: int = 50
    ramp_up_time: int = 5
    
    # Timeouts
    request_timeout: int = 30
    total_timeout: int = 300
    
    # Base de données
    db_url: str = "postgresql://jarvis:jarvis123@localhost:5432/jarvis_memory"
    redis_url: str = "redis://localhost:6379"
    
    # Configuration des tests
    test_memory_operations: bool = True
    test_llm_cache: bool = True
    test_database_performance: bool = True
    test_connection_pooling: bool = True
    test_circuit_breakers: bool = True
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = {
                "health": "http://localhost:5000/health",
                "memory_stats": "http://localhost:5000/api/memory/stats",
                "chat": "http://localhost:5000/api/chat/message",
                "agent": "http://localhost:5000/api/agent/process",
                "ollama": "http://localhost:11434/api/tags"
            }

@dataclass
class BenchmarkResult:
    """Résultat d'un benchmark"""
    test_name: str
    success_count: int
    error_count: int
    total_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float  # requests/sec
    error_rate: float  # %
    
    # Métriques système
    avg_cpu_usage: float
    max_memory_usage: float
    
    # Détails des erreurs
    errors: Dict[str, int] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = {}

@dataclass
class ComparisonReport:
    """Rapport de comparaison avant/après optimisations"""
    baseline: Dict[str, BenchmarkResult]
    optimized: Dict[str, BenchmarkResult]
    improvements: Dict[str, Dict[str, float]]
    timestamp: datetime
    
    def calculate_improvements(self):
        """Calculer les améliorations"""
        self.improvements = {}
        
        for test_name in self.baseline:
            if test_name in self.optimized:
                baseline_result = self.baseline[test_name]
                optimized_result = self.optimized[test_name]
                
                self.improvements[test_name] = {
                    "response_time_improvement": (
                        (baseline_result.avg_response_time - optimized_result.avg_response_time) /
                        baseline_result.avg_response_time * 100
                    ),
                    "throughput_improvement": (
                        (optimized_result.throughput - baseline_result.throughput) /
                        baseline_result.throughput * 100
                    ),
                    "error_rate_improvement": (
                        baseline_result.error_rate - optimized_result.error_rate
                    ),
                    "cpu_usage_improvement": (
                        baseline_result.avg_cpu_usage - optimized_result.avg_cpu_usage
                    ),
                    "memory_usage_improvement": (
                        baseline_result.max_memory_usage - optimized_result.max_memory_usage
                    )
                }

class PerformanceBenchmark:
    """
    Suite de benchmarks pour JARVIS
    
    Tests:
    - Endpoints HTTP avec charge
    - Opérations base de données
    - Cache Redis
    - Connection pooling
    - Circuit breakers
    """
    
    def __init__(self, config: BenchmarkConfig = None):
        self.config = config or BenchmarkConfig()
        self.results: Dict[str, BenchmarkResult] = {}
        
        # Clients
        self.http_client = None
        self.redis_client = None
        self.db_engine = None
        
        logger.info(f"🔧 Benchmark initialisé - {self.config.concurrent_users} utilisateurs concurrents")
    
    async def setup(self):
        """Initialiser les clients de test"""
        # Client HTTP avec pool de connexions
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.request_timeout),
            limits=httpx.Limits(
                max_connections=self.config.concurrent_users * 2,
                max_keepalive_connections=self.config.concurrent_users
            )
        )
        
        # Client Redis
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Redis connecté")
        except Exception as e:
            logger.warning(f"⚠️ Redis non disponible: {e}")
        
        # Engine PostgreSQL
        try:
            self.db_engine = create_engine(
                self.config.db_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                echo=False
            )
            
            # Test connexion
            with self.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ PostgreSQL connecté")
            
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL non disponible: {e}")
    
    async def cleanup(self):
        """Nettoyer les ressources"""
        if self.http_client:
            await self.http_client.aclose()
        
        if self.redis_client:
            await self.redis_client.aclose()
        
        if self.db_engine:
            self.db_engine.dispose()
    
    async def run_http_endpoint_test(self, endpoint_name: str, url: str) -> BenchmarkResult:
        """Test de charge sur un endpoint HTTP"""
        logger.info(f"🚀 Test endpoint: {endpoint_name}")
        
        response_times = []
        errors = {}
        success_count = 0
        
        # Monitoring système
        cpu_usage = []
        memory_usage = []
        
        start_time = time.time()
        
        async def make_request():
            try:
                start_req_time = time.time()
                
                if endpoint_name == "chat":
                    payload = {
                        "message": "Hello JARVIS, test message",
                        "user_id": "benchmark_user",
                        "context": {"test": True}
                    }
                    response = await self.http_client.post(url, json=payload)
                elif endpoint_name == "agent":
                    payload = {
                        "task": "test task",
                        "context": {"benchmark": True}
                    }
                    response = await self.http_client.post(url, json=payload)
                else:
                    response = await self.http_client.get(url)
                
                response_time = time.time() - start_req_time
                
                if response.status_code < 400:
                    nonlocal success_count
                    success_count += 1
                    response_times.append(response_time)
                else:
                    error_key = f"HTTP_{response.status_code}"
                    errors[error_key] = errors.get(error_key, 0) + 1
                
            except Exception as e:
                error_key = type(e).__name__
                errors[error_key] = errors.get(error_key, 0) + 1
        
        # Lancer les requêtes concurrentes
        total_requests = self.config.concurrent_users * self.config.requests_per_user
        
        tasks = []
        for user_id in range(self.config.concurrent_users):
            for request_id in range(self.config.requests_per_user):
                # Étalement des requêtes sur ramp_up_time
                delay = (user_id * self.config.ramp_up_time) / self.config.concurrent_users
                
                async def delayed_request(delay_time):
                    await asyncio.sleep(delay_time)
                    return await make_request()
                
                tasks.append(delayed_request(delay))
        
        # Monitoring système pendant les tests
        async def monitor_system():
            while tasks:
                await asyncio.sleep(0.5)
                cpu_usage.append(psutil.cpu_percent())
                memory_usage.append(psutil.virtual_memory().percent)
        
        monitor_task = asyncio.create_task(monitor_system())
        
        # Exécuter tous les tests
        await asyncio.gather(*tasks)
        monitor_task.cancel()
        
        total_time = time.time() - start_time
        
        # Calculer statistiques
        error_count = sum(errors.values())
        total_requests_made = success_count + error_count
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        p95_response_time = 0
        p99_response_time = 0
        if response_times:
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        
        throughput = success_count / total_time if total_time > 0 else 0
        error_rate = (error_count / total_requests_made * 100) if total_requests_made > 0 else 0
        
        avg_cpu_usage = statistics.mean(cpu_usage) if cpu_usage else 0
        max_memory_usage = max(memory_usage) if memory_usage else 0
        
        result = BenchmarkResult(
            test_name=endpoint_name,
            success_count=success_count,
            error_count=error_count,
            total_requests=total_requests_made,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput=throughput,
            error_rate=error_rate,
            avg_cpu_usage=avg_cpu_usage,
            max_memory_usage=max_memory_usage,
            errors=errors
        )
        
        logger.info(f"✅ {endpoint_name}: {success_count}/{total_requests_made} succès, "
                   f"{avg_response_time:.3f}s moyenne, {throughput:.1f} req/s")
        
        return result
    
    async def run_database_performance_test(self) -> BenchmarkResult:
        """Test de performance de la base de données"""
        if not self.db_engine:
            logger.warning("⚠️ PostgreSQL non disponible, skip test DB")
            return None
        
        logger.info("🗄️ Test performance PostgreSQL")
        
        response_times = []
        errors = {}
        success_count = 0
        
        start_time = time.time()
        
        # Test différentes opérations
        async def db_operations():
            try:
                start_op_time = time.time()
                
                with self.db_engine.connect() as conn:
                    # Test insertion
                    conn.execute(text("""
                        INSERT INTO memory_entries (id, type, content, metadata, created_at, updated_at)
                        VALUES (:id, 'test', 'benchmark content', '{}', NOW(), NOW())
                    """), {"id": f"bench_{int(time.time() * 1000000)}"})
                    
                    # Test requête avec filtre
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM memory_entries WHERE type = 'test'
                    """))
                    
                    # Test requête avec tri
                    result = conn.execute(text("""
                        SELECT id, created_at FROM memory_entries 
                        ORDER BY created_at DESC LIMIT 10
                    """))
                    
                    conn.commit()
                
                response_time = time.time() - start_op_time
                response_times.append(response_time)
                nonlocal success_count
                success_count += 1
                
            except Exception as e:
                error_key = type(e).__name__
                errors[error_key] = errors.get(error_key, 0) + 1
        
        # Lancer opérations concurrentes
        tasks = [db_operations() for _ in range(self.config.concurrent_users * 5)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        error_count = sum(errors.values())
        total_operations = success_count + error_count
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        throughput = success_count / total_time if total_time > 0 else 0
        error_rate = (error_count / total_operations * 100) if total_operations > 0 else 0
        
        # Nettoyer les données de test
        try:
            with self.db_engine.connect() as conn:
                conn.execute(text("DELETE FROM memory_entries WHERE type = 'test'"))
                conn.commit()
        except Exception as e:
            logger.warning(f"⚠️ Erreur nettoyage: {e}")
        
        result = BenchmarkResult(
            test_name="database_performance",
            success_count=success_count,
            error_count=error_count,
            total_requests=total_operations,
            avg_response_time=avg_response_time,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=0,  # Calculer si nécessaire
            p99_response_time=0,
            throughput=throughput,
            error_rate=error_rate,
            avg_cpu_usage=0,
            max_memory_usage=0,
            errors=errors
        )
        
        logger.info(f"✅ DB Performance: {success_count}/{total_operations} succès, "
                   f"{avg_response_time:.3f}s moyenne")
        
        return result
    
    async def run_redis_performance_test(self) -> BenchmarkResult:
        """Test de performance Redis"""
        if not self.redis_client:
            logger.warning("⚠️ Redis non disponible, skip test Redis")
            return None
        
        logger.info("🗃️ Test performance Redis")
        
        response_times = []
        errors = {}
        success_count = 0
        
        start_time = time.time()
        
        async def redis_operations():
            try:
                start_op_time = time.time()
                
                key = f"benchmark:{int(time.time() * 1000000)}"
                
                # Test SET
                await self.redis_client.set(key, "benchmark value", ex=60)
                
                # Test GET
                value = await self.redis_client.get(key)
                
                # Test DELETE
                await self.redis_client.delete(key)
                
                response_time = time.time() - start_op_time
                response_times.append(response_time)
                nonlocal success_count
                success_count += 1
                
            except Exception as e:
                error_key = type(e).__name__
                errors[error_key] = errors.get(error_key, 0) + 1
        
        # Lancer opérations concurrentes
        tasks = [redis_operations() for _ in range(self.config.concurrent_users * 10)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        error_count = sum(errors.values())
        total_operations = success_count + error_count
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        throughput = success_count / total_time if total_time > 0 else 0
        error_rate = (error_count / total_operations * 100) if total_operations > 0 else 0
        
        result = BenchmarkResult(
            test_name="redis_performance",
            success_count=success_count,
            error_count=error_count,
            total_requests=total_operations,
            avg_response_time=avg_response_time,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=0,
            p99_response_time=0,
            throughput=throughput,
            error_rate=error_rate,
            avg_cpu_usage=0,
            max_memory_usage=0,
            errors=errors
        )
        
        logger.info(f"✅ Redis Performance: {success_count}/{total_operations} succès, "
                   f"{avg_response_time:.3f}s moyenne")
        
        return result
    
    async def run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """Exécuter tous les benchmarks"""
        logger.info("🏃 Démarrage de tous les benchmarks...")
        
        await self.setup()
        
        try:
            # Tests des endpoints HTTP
            for endpoint_name, url in self.config.endpoints.items():
                try:
                    result = await self.run_http_endpoint_test(endpoint_name, url)
                    self.results[endpoint_name] = result
                except Exception as e:
                    logger.error(f"❌ Erreur test {endpoint_name}: {e}")
            
            # Test base de données
            if self.config.test_database_performance:
                try:
                    db_result = await self.run_database_performance_test()
                    if db_result:
                        self.results["database"] = db_result
                except Exception as e:
                    logger.error(f"❌ Erreur test DB: {e}")
            
            # Test Redis
            if self.config.test_llm_cache:
                try:
                    redis_result = await self.run_redis_performance_test()
                    if redis_result:
                        self.results["redis"] = redis_result
                except Exception as e:
                    logger.error(f"❌ Erreur test Redis: {e}")
            
        finally:
            await self.cleanup()
        
        logger.info(f"✅ Benchmarks terminés - {len(self.results)} tests")
        return self.results
    
    def save_results(self, filename: str):
        """Sauvegarder les résultats"""
        results_data = {
            test_name: asdict(result) 
            for test_name, result in self.results.items()
        }
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "config": asdict(self.config),
                "results": results_data
            }, f, indent=2)
        
        logger.info(f"💾 Résultats sauvegardés: {filename}")
    
    @staticmethod
    def load_results(filename: str) -> Dict[str, BenchmarkResult]:
        """Charger les résultats"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        results = {}
        for test_name, result_data in data["results"].items():
            results[test_name] = BenchmarkResult(**result_data)
        
        return results
    
    @staticmethod
    def compare_results(
        baseline_file: str,
        optimized_file: str,
        output_file: str = None
    ) -> ComparisonReport:
        """Comparer deux séries de résultats"""
        baseline = PerformanceBenchmark.load_results(baseline_file)
        optimized = PerformanceBenchmark.load_results(optimized_file)
        
        report = ComparisonReport(
            baseline=baseline,
            optimized=optimized,
            improvements={},
            timestamp=datetime.now()
        )
        
        report.calculate_improvements()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
        
        return report
    
    def print_summary(self):
        """Afficher résumé des résultats"""
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DES BENCHMARKS JARVIS")
        print("="*80)
        
        for test_name, result in self.results.items():
            print(f"\n🔸 {test_name.upper()}")
            print(f"   Succès: {result.success_count}/{result.total_requests}")
            print(f"   Temps moyen: {result.avg_response_time:.3f}s")
            print(f"   Débit: {result.throughput:.1f} req/s")
            print(f"   Taux d'erreur: {result.error_rate:.1f}%")
            
            if result.errors:
                print(f"   Erreurs: {result.errors}")
        
        print("\n" + "="*80)

async def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS Performance Benchmark")
    parser.add_argument("--mode", choices=["baseline", "optimized", "compare"], 
                       default="optimized", help="Mode de benchmark")
    parser.add_argument("--output", help="Fichier de sortie pour les résultats")
    parser.add_argument("--baseline", help="Fichier baseline pour comparaison")
    parser.add_argument("--concurrent-users", type=int, default=10, 
                       help="Nombre d'utilisateurs concurrents")
    parser.add_argument("--requests-per-user", type=int, default=50,
                       help="Requêtes par utilisateur")
    
    args = parser.parse_args()
    
    if args.mode == "compare":
        if not args.baseline or not args.output:
            print("❌ Mode compare nécessite --baseline et --output")
            return
        
        # Comparer les résultats
        report = PerformanceBenchmark.compare_results(
            args.baseline,
            args.output,
            args.output.replace('.json', '_comparison.json')
        )
        
        print("\n📈 COMPARAISON DES PERFORMANCES")
        print("="*50)
        
        for test_name, improvements in report.improvements.items():
            print(f"\n🔸 {test_name.upper()}")
            for metric, improvement in improvements.items():
                if "improvement" in metric:
                    if improvement > 0:
                        print(f"   ✅ {metric}: +{improvement:.1f}%")
                    else:
                        print(f"   ❌ {metric}: {improvement:.1f}%")
        
        return
    
    # Configuration
    config = BenchmarkConfig(
        concurrent_users=args.concurrent_users,
        requests_per_user=args.requests_per_user
    )
    
    # Exécuter benchmarks
    benchmark = PerformanceBenchmark(config)
    
    logger.info(f"🚀 Lancement benchmark mode: {args.mode}")
    
    results = await benchmark.run_all_benchmarks()
    
    # Sauvegarder
    output_file = args.output or f"benchmark_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    benchmark.save_results(output_file)
    
    # Afficher résumé
    benchmark.print_summary()

if __name__ == "__main__":
    asyncio.run(main())