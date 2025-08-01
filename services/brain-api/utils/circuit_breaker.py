"""
🔌 Circuit Breaker Pattern avec Retry Logic et Exponential Backoff
Implémentation pour prévenir les pannes en cascade entre microservices
"""

import asyncio
import logging
import time
import random
from typing import Any, Callable, Dict, Optional
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps

import httpx
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_log,
    after_log
)

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"        # Opérationnel
    OPEN = "open"            # Circuit ouvert, échec
    HALF_OPEN = "half_open"  # Test de récupération

@dataclass
class CircuitConfig:
    """Configuration du circuit breaker"""
    failure_threshold: int = 5           # Nombre d'échecs avant ouverture
    recovery_timeout: int = 60           # Temps avant test de récupération (s)
    expected_exception: type = Exception # Type d'exception à surveiller
    success_threshold: int = 3           # Succès requis pour fermer
    timeout: int = 30                    # Timeout des requêtes (s)
    
    # Retry configuration
    max_retries: int = 3
    min_wait: float = 1.0               # Attente minimale (s)
    max_wait: float = 60.0              # Attente maximale (s)
    exponential_base: float = 2.0       # Base pour backoff exponentiel
    jitter: bool = True                 # Ajouter du jitter

class CircuitBreaker:
    """
    Circuit Breaker avec retry logic et exponential backoff
    
    Pattern:
    - CLOSED: Requêtes passent normalement
    - OPEN: Requêtes échouent immédiatement après timeout
    - HALF_OPEN: Test une requête, ferme si succès ou rouvre si échec
    """
    
    def __init__(self, name: str, config: CircuitConfig = None):
        self.name = name
        self.config = config or CircuitConfig()
        
        # État du circuit
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = 0
        
        # Statistiques
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_opens": 0,
            "circuit_half_opens": 0,
            "circuit_closes": 0,
            "avg_response_time": 0.0
        }
        
        self._lock = asyncio.Lock()
        
        logger.info(f"🔌 Circuit Breaker '{name}' initialisé - Seuil: {self.config.failure_threshold}")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Exécuter une fonction à travers le circuit breaker
        
        Args:
            func: Fonction à exécuter
            *args, **kwargs: Arguments pour la fonction
        
        Returns:
            Résultat de la fonction
        
        Raises:
            CircuitOpenException: Si le circuit est ouvert
            Exception: Exceptions de la fonction appelée
        """
        async with self._lock:
            self.stats["total_requests"] += 1
            
            # Vérifier l'état du circuit
            if self.state == CircuitState.OPEN:
                if time.time() < self.next_attempt_time:
                    raise CircuitOpenException(
                        f"Circuit '{self.name}' ouvert jusqu'à {self.next_attempt_time}"
                    )
                else:
                    # Passer en half-open pour tester
                    self.state = CircuitState.HALF_OPEN
                    self.stats["circuit_half_opens"] += 1
                    logger.info(f"🟡 Circuit '{self.name}' -> HALF_OPEN (test de récupération)")
        
        # Exécuter avec retry et timing
        start_time = time.time()
        
        try:
            # Utiliser tenacity pour retry avec backoff exponentiel
            @retry(
                stop=stop_after_attempt(self.config.max_retries),
                wait=wait_exponential(
                    multiplier=self.config.min_wait,
                    max=self.config.max_wait,
                    exp_base=self.config.exponential_base
                ) if not self.config.jitter else wait_exponential(
                    multiplier=self.config.min_wait,
                    max=self.config.max_wait,
                    exp_base=self.config.exponential_base,
                    jitter=lambda x: x * (0.5 + random.random() * 0.5)
                ),
                retry=retry_if_exception_type(self.config.expected_exception),
                before=before_log(logger, logging.DEBUG),
                after=after_log(logger, logging.DEBUG)
            )
            async def execute_with_retry():
                if asyncio.iscoroutinefunction(func):
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
                else:
                    return func(*args, **kwargs)
            
            result = await execute_with_retry()
            
            # Succès - mettre à jour les statistiques
            response_time = time.time() - start_time
            await self._on_success(response_time)
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            await self._on_failure(e, response_time)
            raise
    
    async def _on_success(self, response_time: float):
        """Gérer un succès"""
        async with self._lock:
            self.stats["successful_requests"] += 1
            
            # Mettre à jour le temps de réponse moyen
            if self.stats["avg_response_time"] == 0:
                self.stats["avg_response_time"] = response_time
            else:
                self.stats["avg_response_time"] = (
                    self.stats["avg_response_time"] + response_time
                ) / 2
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    # Fermer le circuit
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.stats["circuit_closes"] += 1
                    logger.info(f"✅ Circuit '{self.name}' -> CLOSED (récupération réussie)")
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    async def _on_failure(self, exception: Exception, response_time: float):
        """Gérer un échec"""
        async with self._lock:
            self.stats["failed_requests"] += 1
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Mettre à jour le temps de réponse moyen même pour les échecs
            if self.stats["avg_response_time"] == 0:
                self.stats["avg_response_time"] = response_time
            else:
                self.stats["avg_response_time"] = (
                    self.stats["avg_response_time"] + response_time
                ) / 2
            
            if self.state == CircuitState.HALF_OPEN:
                # Retour à OPEN
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.next_attempt_time = time.time() + self.config.recovery_timeout
                self.stats["circuit_opens"] += 1
                logger.warning(f"🔴 Circuit '{self.name}' -> OPEN (échec en half-open)")
                
            elif self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
                # Ouvrir le circuit
                self.state = CircuitState.OPEN
                self.next_attempt_time = time.time() + self.config.recovery_timeout
                self.stats["circuit_opens"] += 1
                logger.error(
                    f"🔴 Circuit '{self.name}' -> OPEN "
                    f"({self.failure_count} échecs consécutifs) "
                    f"Exception: {type(exception).__name__}: {exception}"
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du circuit breaker"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "next_attempt_time": self.next_attempt_time,
            "last_failure_time": self.last_failure_time,
            **self.stats
        }
    
    def reset(self):
        """Reset manuel du circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.next_attempt_time = 0
        logger.info(f"🔄 Circuit '{self.name}' reseté manuellement")

class CircuitOpenException(Exception):
    """Exception levée quand le circuit est ouvert"""
    pass

class CircuitBreakerManager:
    """Gestionnaire central des circuit breakers"""
    
    def __init__(self):
        self.circuits: Dict[str, CircuitBreaker] = {}
        logger.info("🔌 Circuit Breaker Manager initialisé")
    
    def get_or_create(self, name: str, config: CircuitConfig = None) -> CircuitBreaker:
        """Obtenir ou créer un circuit breaker"""
        if name not in self.circuits:
            self.circuits[name] = CircuitBreaker(name, config)
        return self.circuits[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Obtenir les statistiques de tous les circuits"""
        return {
            name: circuit.get_stats() 
            for name, circuit in self.circuits.items()
        }
    
    def reset_all(self):
        """Reset tous les circuit breakers"""
        for circuit in self.circuits.values():
            circuit.reset()
        logger.info("🔄 Tous les circuits resetés")

# Instance globale
circuit_manager = CircuitBreakerManager()

def circuit_breaker(name: str, config: CircuitConfig = None):
    """
    Décorateur pour circuit breaker
    
    Usage:
        @circuit_breaker("my_service")
        async def call_service():
            # code qui peut échouer
            pass
    """
    def decorator(func):
        circuit = circuit_manager.get_or_create(name, config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await circuit.call(func, *args, **kwargs)
        
        return wrapper
    return decorator

# Configuration prédéfinie pour les services JARVIS
JARVIS_CIRCUITS = {
    "ollama": CircuitConfig(
        failure_threshold=3,
        recovery_timeout=30,
        timeout=120,  # LLM peut être lent
        max_retries=2
    ),
    "redis": CircuitConfig(
        failure_threshold=5,
        recovery_timeout=15,
        timeout=5,
        max_retries=3
    ),
    "postgres": CircuitConfig(
        failure_threshold=5,
        recovery_timeout=30,
        timeout=30,
        max_retries=2
    ),
    "tts_service": CircuitConfig(
        failure_threshold=3,
        recovery_timeout=20,
        timeout=60,
        max_retries=2
    ),
    "stt_service": CircuitConfig(
        failure_threshold=3,
        recovery_timeout=20,
        timeout=30,
        max_retries=2
    )
}

# Fonctions utilitaires pour les services JARVIS
async def call_ollama_with_circuit_breaker(func: Callable, *args, **kwargs):
    """Appeler Ollama avec circuit breaker"""
    circuit = circuit_manager.get_or_create("ollama", JARVIS_CIRCUITS["ollama"])
    return await circuit.call(func, *args, **kwargs)

async def call_redis_with_circuit_breaker(func: Callable, *args, **kwargs):
    """Appeler Redis avec circuit breaker"""
    circuit = circuit_manager.get_or_create("redis", JARVIS_CIRCUITS["redis"])
    return await circuit.call(func, *args, **kwargs)

async def call_postgres_with_circuit_breaker(func: Callable, *args, **kwargs):
    """Appeler PostgreSQL avec circuit breaker"""
    circuit = circuit_manager.get_or_create("postgres", JARVIS_CIRCUITS["postgres"])
    return await circuit.call(func, *args, **kwargs)

# HTTP Client avec circuit breaker intégré
class CircuitBreakerHTTPClient:
    """Client HTTP avec circuit breaker intégré pour les appels inter-services"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5)
        )
        logger.info("🌐 Circuit Breaker HTTP Client initialisé")
    
    async def get(self, service_name: str, url: str, **kwargs):
        """GET avec circuit breaker"""
        circuit = circuit_manager.get_or_create(
            f"http_{service_name}", 
            JARVIS_CIRCUITS.get(service_name, CircuitConfig())
        )
        
        async def make_request():
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()
            return response
        
        return await circuit.call(make_request)
    
    async def post(self, service_name: str, url: str, **kwargs):
        """POST avec circuit breaker"""
        circuit = circuit_manager.get_or_create(
            f"http_{service_name}",
            JARVIS_CIRCUITS.get(service_name, CircuitConfig())
        )
        
        async def make_request():
            response = await self.client.post(url, **kwargs)
            response.raise_for_status()
            return response
        
        return await circuit.call(make_request)
    
    async def close(self):
        """Fermer le client HTTP"""
        await self.client.aclose()

# Instance globale du client HTTP avec circuit breaker
http_client = CircuitBreakerHTTPClient()