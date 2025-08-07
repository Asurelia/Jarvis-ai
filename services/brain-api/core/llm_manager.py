"""
🧠 LLM Manager - Intelligent Model Routing Integration
Intégration avec LLM Gateway pour sélection automatique de modèles
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModelSelectionStrategy(Enum):
    COMPLEXITY_BASED = "complexity_based"
    GPU_OPTIMIZED = "gpu_optimized" 
    COST_OPTIMIZED = "cost_optimized"
    SPEED_OPTIMIZED = "speed_optimized"

@dataclass
class LLMResponse:
    content: str
    model_used: str
    complexity_score: float
    response_time: float
    gpu_status: str
    token_count: int
    cached: bool = False

@dataclass
class LLMStreamChunk:
    content: str
    is_final: bool
    metadata: Optional[Dict] = None

class LLMManager:
    """Manager intelligent pour routing LLM avec fallback"""
    
    def __init__(self, 
                 gateway_url: str = "http://llm-gateway:5010",
                 fallback_url: str = "http://ollama:11434",
                 strategy: ModelSelectionStrategy = ModelSelectionStrategy.COMPLEXITY_BASED):
        
        self.gateway_url = gateway_url
        self.fallback_url = fallback_url
        self.strategy = strategy
        
        # État du système
        self.gateway_available = True
        self.gateway_last_check = 0
        self.health_check_interval = 60  # 1 minute
        
        # Cache réponses
        self.response_cache: Dict[str, LLMResponse] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Statistiques
        self.stats = {
            "total_requests": 0,
            "gateway_requests": 0,
            "fallback_requests": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0,
            "model_usage": {},
            "errors": 0
        }
        
        # Configuration circuit breaker
        self.circuit_breaker = {
            "failures": 0,
            "threshold": 5,
            "timeout": 30,
            "last_failure": 0,
            "state": "closed"  # closed, open, half-open
        }
        
    async def initialize(self):
        """Initialisation du LLM Manager"""
        logger.info("🚀 Initialisation LLM Manager...")
        
        # Tester connectivité gateway
        await self._check_gateway_health()
        
        # Démarrer monitoring périodique
        asyncio.create_task(self._health_monitor_loop())
        
        logger.info(f"✅ LLM Manager initialisé (Gateway: {'✓' if self.gateway_available else '✗'})")
    
    async def _health_monitor_loop(self):
        """Monitoring périodique santé services"""
        while True:
            try:
                await self._check_gateway_health()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"❌ Erreur monitoring santé: {e}")
                await asyncio.sleep(30)
    
    async def _check_gateway_health(self):
        """Vérification santé LLM Gateway"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.gateway_url}/api/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.gateway_available = data.get("status") == "healthy"
                        self.gateway_last_check = time.time()
                        
                        if self.gateway_available:
                            self._reset_circuit_breaker()
                            
                        logger.debug(f"Gateway santé: {'✓' if self.gateway_available else '✗'}")
                    else:
                        self.gateway_available = False
                        self._record_failure()
                        
        except Exception as e:
            self.gateway_available = False
            self._record_failure()
            logger.warning(f"⚠️ Gateway indisponible: {e}")
    
    def _record_failure(self):
        """Enregistrer échec pour circuit breaker"""
        self.circuit_breaker["failures"] += 1
        self.circuit_breaker["last_failure"] = time.time()
        
        if self.circuit_breaker["failures"] >= self.circuit_breaker["threshold"]:
            self.circuit_breaker["state"] = "open"
            logger.warning("🚨 Circuit breaker OUVERT - Gateway désactivé temporairement")
    
    def _reset_circuit_breaker(self):
        """Réinitialiser circuit breaker"""
        if self.circuit_breaker["failures"] > 0:
            self.circuit_breaker["failures"] = 0
            self.circuit_breaker["state"] = "closed"
            logger.info("✅ Circuit breaker FERMÉ - Gateway rétabli")
    
    def _should_use_gateway(self) -> bool:
        """Décider si utiliser le gateway ou fallback"""
        
        # Vérifier circuit breaker
        if self.circuit_breaker["state"] == "open":
            # Vérifier si timeout écoulé pour réessayer
            time_since_failure = time.time() - self.circuit_breaker["last_failure"]
            if time_since_failure > self.circuit_breaker["timeout"]:
                self.circuit_breaker["state"] = "half-open"
                logger.info("🔄 Circuit breaker SEMI-OUVERT - Test gateway...")
                return True
            return False
        
        return self.gateway_available
    
    def _generate_cache_key(self, messages: List[Dict], **kwargs) -> str:
        """Générer clé cache pour requête"""
        # Utiliser hash du contenu + paramètres pour la clé
        content = json.dumps(messages, sort_keys=True)
        params = json.dumps(kwargs, sort_keys=True)
        return f"{hash(content)}_{hash(params)}"
    
    def _is_cache_valid(self, cached_response: LLMResponse) -> bool:
        """Vérifier validité cache"""
        return (time.time() - getattr(cached_response, 'cached_at', 0)) < self.cache_ttl
    
    async def chat_completion(self, 
                            messages: List[Dict], 
                            stream: bool = False,
                            **kwargs) -> LLMResponse:
        """
        Completion de chat avec sélection intelligente de modèle
        
        Args:
            messages: Messages de conversation
            stream: Streaming activé
            **kwargs: Paramètres additionnels (temperature, max_tokens, etc.)
        
        Returns:
            LLMResponse avec métadonnées complètes
        """
        
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        # Vérifier cache
        cache_key = self._generate_cache_key(messages, **kwargs)
        if cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            if self._is_cache_valid(cached):
                self.stats["cache_hits"] += 1
                logger.info("📦 Réponse depuis cache")
                return cached
        
        try:
            # Décider service à utiliser
            use_gateway = self._should_use_gateway()
            
            if use_gateway:
                response = await self._request_gateway(messages, stream, **kwargs)
                self.stats["gateway_requests"] += 1
            else:
                response = await self._request_fallback(messages, stream, **kwargs)
                self.stats["fallback_requests"] += 1
            
            # Mettre en cache si pertinent
            if not stream and len(response.content) > 10:
                response.cached_at = time.time()
                self.response_cache[cache_key] = response
            
            # Mise à jour statistiques
            response_time = time.time() - start_time
            self.stats["avg_response_time"] = (
                (self.stats["avg_response_time"] * (self.stats["total_requests"] - 1) + response_time) 
                / self.stats["total_requests"]
            )
            
            # Statistiques par modèle
            if response.model_used in self.stats["model_usage"]:
                self.stats["model_usage"][response.model_used] += 1
            else:
                self.stats["model_usage"][response.model_used] = 1
            
            return response
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Erreur LLM completion: {e}")
            raise
    
    async def _request_gateway(self, messages: List[Dict], stream: bool, **kwargs) -> LLMResponse:
        """Requête via LLM Gateway"""
        
        payload = {
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.gateway_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Gateway error {response.status}: {error_text}")
                    
                    if stream:
                        # TODO: Implémenter streaming
                        raise NotImplementedError("Streaming via gateway pas encore implémenté")
                    else:
                        data = await response.json()
                        
                        # Parser réponse gateway
                        if "response" in data and "metadata" in data:
                            return LLMResponse(
                                content=data["response"].get("message", {}).get("content", ""),
                                model_used=data["metadata"]["model_used"],
                                complexity_score=data["metadata"]["complexity_score"],
                                response_time=data["metadata"]["response_time"],
                                gpu_status=data["metadata"]["gpu_status"],
                                token_count=len(data["response"].get("message", {}).get("content", "").split())
                            )
                        else:
                            # Format direct Ollama
                            return LLMResponse(
                                content=data.get("message", {}).get("content", ""),
                                model_used="unknown",
                                complexity_score=0.5,
                                response_time=0.0,
                                gpu_status="unknown",
                                token_count=len(data.get("message", {}).get("content", "").split())
                            )
                            
        except Exception as e:
            self._record_failure()
            logger.error(f"❌ Erreur requête gateway: {e}")
            # Fallback automatique
            return await self._request_fallback(messages, stream, **kwargs)
    
    async def _request_fallback(self, messages: List[Dict], stream: bool, **kwargs) -> LLMResponse:
        """Requête via service fallback (Ollama direct)"""
        
        payload = {
            "model": kwargs.get("model", "llama3.2:3b"),  # Modèle par défaut
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 2048)
            }
        }
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.fallback_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Fallback error {response.status}: {error_text}")
                    
                    data = await response.json()
                    response_time = time.time() - start_time
                    
                    return LLMResponse(
                        content=data.get("message", {}).get("content", ""),
                        model_used=payload["model"],
                        complexity_score=0.3,  # Score par défaut pour fallback
                        response_time=response_time,
                        gpu_status="fallback",
                        token_count=len(data.get("message", {}).get("content", "").split())
                    )
                    
        except Exception as e:
            logger.error(f"❌ Erreur fallback: {e}")
            raise
    
    async def stream_completion(self, messages: List[Dict], **kwargs) -> AsyncGenerator[LLMStreamChunk, None]:
        """
        Streaming completion avec sélection intelligente
        """
        # TODO: Implémenter streaming complet
        # Pour l'instant, simuler streaming depuis réponse normale
        
        response = await self.chat_completion(messages, stream=False, **kwargs)
        
        # Diviser réponse en chunks pour simuler streaming
        words = response.content.split()
        chunk_size = max(1, len(words) // 10)  # ~10 chunks
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_content = " ".join(chunk_words)
            
            is_final = i + chunk_size >= len(words)
            
            yield LLMStreamChunk(
                content=chunk_content + (" " if not is_final else ""),
                is_final=is_final,
                metadata={"model": response.model_used} if is_final else None
            )
            
            # Petit délai pour simuler streaming réaliste
            await asyncio.sleep(0.1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupérer statistiques détaillées"""
        return {
            **self.stats,
            "gateway_available": self.gateway_available,
            "circuit_breaker": self.circuit_breaker,
            "cache_size": len(self.response_cache),
            "strategy": self.strategy.value
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Récupérer état santé du manager"""
        return {
            "status": "healthy" if self.gateway_available or self.fallback_url else "degraded",
            "gateway_available": self.gateway_available,
            "circuit_breaker_state": self.circuit_breaker["state"],
            "last_health_check": self.gateway_last_check,
            "cache_entries": len(self.response_cache),
            "total_requests": self.stats["total_requests"],
            "error_rate": self.stats["errors"] / max(self.stats["total_requests"], 1)
        }
    
    async def shutdown(self):
        """Arrêt propre du manager"""
        logger.info("🛑 Arrêt LLM Manager...")
        
        # Nettoyer cache
        self.response_cache.clear()
        
        # Log statistiques finales
        logger.info("📊 Statistiques finales LLM Manager:")
        for key, value in self.stats.items():
            logger.info(f"   {key}: {value}")
        
        logger.info("✅ LLM Manager arrêté")