"""
🧠 LLM Response Cache Manager
Cache intelligent pour les réponses LLM avec déduplication et optimisations
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from .redis_manager import RedisManager
from .circuit_breaker import call_redis_with_circuit_breaker

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Stratégies de cache pour différents types de requêtes"""
    EXACT_MATCH = "exact_match"          # Cache exact (même prompt)
    SEMANTIC_MATCH = "semantic_match"    # Cache sémantique (similarité)
    PREFIX_MATCH = "prefix_match"        # Cache par préfixe
    CONTEXT_AWARE = "context_aware"      # Cache conscient du contexte
    BYPASS = "bypass"                    # Pas de cache

@dataclass
class CacheEntry:
    """Entrée de cache LLM"""
    key: str
    prompt_hash: str
    prompt: str
    response: str
    model: str
    temperature: float
    max_tokens: int
    context_hash: Optional[str] = None
    created_at: datetime = None
    last_accessed: datetime = None
    access_count: int = 0
    response_time: float = 0.0
    token_count: int = 0
    cost_saved: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = self.created_at

@dataclass
class CacheConfig:
    """Configuration du cache LLM"""
    # TTL par type de requête (en secondes)
    exact_match_ttl: int = 86400 * 7      # 7 jours
    semantic_match_ttl: int = 86400 * 3   # 3 jours
    context_aware_ttl: int = 3600         # 1 heure
    default_ttl: int = 86400              # 1 jour
    
    # Seuils de similarité
    semantic_threshold: float = 0.85
    context_threshold: float = 0.75
    
    # Limites de cache
    max_prompt_length: int = 4000
    max_response_length: int = 16000
    max_cache_size: int = 10000
    
    # Optimisations
    enable_compression: bool = True
    enable_deduplication: bool = True
    enable_prefetch: bool = True
    
    # Coûts (pour calcul d'économies)
    cost_per_1k_tokens: float = 0.002  # $0.002 per 1K tokens

class LLMCacheManager:
    """
    Gestionnaire de cache LLM avec:
    - Cache multi-niveaux (local + Redis)
    - Stratégies de cache adaptatives
    - Déduplication intelligente
    - Monitoring des performances et économies
    - Préchargement prédictif
    """
    
    def __init__(
        self,
        redis_manager: RedisManager,
        config: CacheConfig = None
    ):
        self.redis = redis_manager
        self.config = config or CacheConfig()
        
        # Cache local (L1)
        self.local_cache: Dict[str, CacheEntry] = {}
        self.local_cache_max_size = 100
        
        # Index de similarité pour recherche sémantique
        self.similarity_index: Dict[str, List[str]] = {}
        
        # Statistiques détaillées
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "exact_matches": 0,
            "semantic_matches": 0,
            "context_matches": 0,
            "total_tokens_saved": 0,
            "total_cost_saved": 0.0,
            "avg_response_time": 0.0,
            "cache_size": 0,
            "evictions": 0
        }
        
        # Patterns de requêtes fréquentes
        self.frequent_patterns: Dict[str, int] = {}
        self.pattern_threshold = 3
        
        self._lock = asyncio.Lock()
        
        logger.info("🧠 LLM Cache Manager initialisé")
    
    def _generate_prompt_hash(self, prompt: str, model: str = "", temperature: float = 0.7) -> str:
        """Générer hash du prompt pour cache exact"""
        content = f"{prompt}|{model}|{temperature}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_context_hash(self, context: Dict[str, Any]) -> str:
        """Générer hash du contexte"""
        if not context:
            return ""
        
        # Normaliser et trier le contexte
        normalized = {
            k: v for k, v in sorted(context.items())
            if k not in ['timestamp', 'request_id', 'user_session']
        }
        
        content = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _generate_cache_key(
        self, 
        prompt_hash: str, 
        strategy: CacheStrategy,
        context_hash: Optional[str] = None
    ) -> str:
        """Générer clé de cache Redis"""
        parts = ["llm_cache", strategy.value, prompt_hash]
        if context_hash:
            parts.append(context_hash)
        return ":".join(parts)
    
    def _should_cache(self, prompt: str, response: str) -> bool:
        """Déterminer si la requête/réponse doit être cachée"""
        if len(prompt) > self.config.max_prompt_length:
            return False
        if len(response) > self.config.max_response_length:
            return False
        if not response or response.strip() == "":
            return False
        
        # Ne pas cacher les réponses d'erreur
        error_indicators = ["error", "sorry", "cannot", "unable", "failed"]
        response_lower = response.lower()
        if any(indicator in response_lower for indicator in error_indicators):
            return False
        
        return True
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimer le nombre de tokens approximativement"""
        # Approximation: ~4 caractères par token pour l'anglais
        return max(len(text) // 4, 1)
    
    def _calculate_cost_saved(self, prompt: str, response: str) -> float:
        """Calculer le coût économisé"""
        total_tokens = self._estimate_tokens(prompt + response)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens
    
    async def _get_from_local_cache(self, cache_key: str) -> Optional[CacheEntry]:
        """Récupérer depuis cache local"""
        if cache_key in self.local_cache:
            entry = self.local_cache[cache_key]
            # Vérifier TTL (simple pour cache local)
            age = (datetime.now() - entry.created_at).total_seconds()
            if age < self.config.default_ttl:
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                return entry
            else:
                # Supprimer entrée expirée
                del self.local_cache[cache_key]
        
        return None
    
    def _update_local_cache(self, cache_key: str, entry: CacheEntry):
        """Mettre à jour cache local avec éviction LRU"""
        if len(self.local_cache) >= self.local_cache_max_size:
            # Éviction LRU
            oldest_key = min(
                self.local_cache.keys(),
                key=lambda k: self.local_cache[k].last_accessed
            )
            del self.local_cache[oldest_key]
            self.stats["evictions"] += 1
        
        self.local_cache[cache_key] = entry
    
    async def _find_semantic_match(
        self, 
        prompt: str, 
        model: str,
        threshold: float = None
    ) -> Optional[CacheEntry]:
        """Chercher correspondance sémantique"""
        if threshold is None:
            threshold = self.config.semantic_threshold
        
        # Pour une implémentation simple, on utilise la correspondance de mots-clés
        # Dans un système complet, on utiliserait des embeddings
        
        prompt_words = set(prompt.lower().split())
        if len(prompt_words) < 3:  # Trop court pour match sémantique
            return None
        
        # Chercher dans l'index de similarité
        try:
            pattern = f"semantic:{model}:*"
            keys = await self.redis.client.keys(pattern)
            
            best_match = None
            best_score = 0.0
            
            for key in keys[:50]:  # Limiter la recherche
                cached_data = await self.redis.get(key)
                if not cached_data:
                    continue
                
                try:
                    entry_data = json.loads(cached_data)
                    cached_prompt = entry_data.get("prompt", "")
                    cached_words = set(cached_prompt.lower().split())
                    
                    # Calcul similarité Jaccard simple
                    intersection = len(prompt_words & cached_words)
                    union = len(prompt_words | cached_words)
                    
                    if union > 0:
                        similarity = intersection / union
                        
                        if similarity >= threshold and similarity > best_score:
                            best_score = similarity
                            # Reconstruire CacheEntry
                            best_match = CacheEntry(**entry_data)
                
                except (json.JSONDecodeError, TypeError):
                    continue
            
            if best_match and best_score >= threshold:
                logger.info(f"🎯 Match sémantique trouvé (score: {best_score:.2f})")
                return best_match
        
        except Exception as e:
            logger.error(f"❌ Erreur recherche sémantique: {e}")
        
        return None
    
    async def get_cached_response(
        self,
        prompt: str,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        context: Optional[Dict[str, Any]] = None,
        strategy: CacheStrategy = CacheStrategy.EXACT_MATCH
    ) -> Optional[str]:
        """
        Récupérer réponse depuis cache
        
        Returns:
            Réponse cachée ou None si pas trouvée
        """
        if strategy == CacheStrategy.BYPASS:
            return None
        
        self.stats["total_requests"] += 1
        start_time = time.time()
        
        # Générer identifiants
        prompt_hash = self._generate_prompt_hash(prompt, model, temperature)
        context_hash = self._generate_context_hash(context) if context else None
        
        try:
            # Étape 1: Recherche exacte
            if strategy in [CacheStrategy.EXACT_MATCH, CacheStrategy.CONTEXT_AWARE]:
                cache_key = self._generate_cache_key(prompt_hash, strategy, context_hash)
                
                # Cache local
                entry = await self._get_from_local_cache(cache_key)
                if entry:
                    self.stats["cache_hits"] += 1
                    self.stats["exact_matches"] += 1
                    logger.info("⚡ Cache hit (local exact)")\n                    return entry.response
                
                # Cache Redis
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    try:
                        entry_data = json.loads(cached_data)
                        entry = CacheEntry(**entry_data)
                        
                        # Mettre à jour stats d'accès
                        entry.last_accessed = datetime.now()
                        entry.access_count += 1
                        
                        # Sauvegarder back dans Redis avec nouvelles stats
                        await self.redis.setex(
                            cache_key,
                            self._get_ttl_for_strategy(strategy),
                            json.dumps(asdict(entry), default=str)
                        )
                        
                        # Mettre en cache local
                        self._update_local_cache(cache_key, entry)
                        
                        self.stats["cache_hits"] += 1
                        self.stats["exact_matches"] += 1
                        
                        cost_saved = self._calculate_cost_saved(prompt, entry.response)
                        self.stats["total_cost_saved"] += cost_saved
                        self.stats["total_tokens_saved"] += self._estimate_tokens(entry.response)
                        
                        logger.info(f"⚡ Cache hit (Redis exact) - Économie: ${cost_saved:.4f}")
                        return entry.response
                        
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"❌ Erreur décodage cache: {e}")
            
            # Étape 2: Recherche sémantique si activée
            if strategy == CacheStrategy.SEMANTIC_MATCH:
                semantic_entry = await self._find_semantic_match(prompt, model)
                if semantic_entry:
                    self.stats["cache_hits"] += 1
                    self.stats["semantic_matches"] += 1
                    
                    cost_saved = self._calculate_cost_saved(prompt, semantic_entry.response)
                    self.stats["total_cost_saved"] += cost_saved
                    
                    logger.info(f"🎯 Cache hit (sémantique) - Économie: ${cost_saved:.4f}")
                    return semantic_entry.response
            
            # Étape 3: Recherche par préfixe pour requêtes similaires
            if strategy == CacheStrategy.PREFIX_MATCH:
                prefix = prompt[:100].lower()
                pattern_key = f"prefix:{hashlib.md5(prefix.encode()).hexdigest()[:8]}"
                
                cached_keys = await self.redis.client.keys(f"llm_cache:prefix_match:{pattern_key}*")
                if cached_keys:
                    # Prendre le plus récent
                    for key in cached_keys[:5]:
                        cached_data = await self.redis.get(key)
                        if cached_data:
                            try:
                                entry_data = json.loads(cached_data)
                                entry = CacheEntry(**entry_data)
                                
                                self.stats["cache_hits"] += 1
                                cost_saved = self._calculate_cost_saved(prompt, entry.response)
                                self.stats["total_cost_saved"] += cost_saved
                                
                                logger.info(f"📄 Cache hit (préfixe) - Économie: ${cost_saved:.4f}")
                                return entry.response
                                
                            except (json.JSONDecodeError, TypeError):
                                continue
            
            # Pas de match trouvé
            self.stats["cache_misses"] += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération cache: {e}")
            self.stats["cache_misses"] += 1
        
        finally:
            # Mettre à jour temps de réponse
            response_time = time.time() - start_time
            if self.stats["avg_response_time"] == 0:
                self.stats["avg_response_time"] = response_time
            else:
                self.stats["avg_response_time"] = (
                    self.stats["avg_response_time"] + response_time
                ) / 2
        
        return None
    
    async def cache_response(
        self,
        prompt: str,
        response: str,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_time: float = 0.0,
        context: Optional[Dict[str, Any]] = None,
        strategy: CacheStrategy = CacheStrategy.EXACT_MATCH
    ) -> bool:
        """
        Mettre en cache une réponse LLM
        
        Returns:
            True si mis en cache avec succès
        """
        if strategy == CacheStrategy.BYPASS or not self._should_cache(prompt, response):
            return False
        
        try:
            # Générer identifiants
            prompt_hash = self._generate_prompt_hash(prompt, model, temperature)
            context_hash = self._generate_context_hash(context) if context else None
            cache_key = self._generate_cache_key(prompt_hash, strategy, context_hash)
            
            # Créer entrée de cache
            entry = CacheEntry(
                key=cache_key,
                prompt_hash=prompt_hash,
                prompt=prompt,
                response=response,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                context_hash=context_hash,
                response_time=response_time,
                token_count=self._estimate_tokens(prompt + response),
                cost_saved=self._calculate_cost_saved(prompt, response)
            )
            
            # TTL basé sur la stratégie
            ttl = self._get_ttl_for_strategy(strategy)
            
            # Sauvegarder dans Redis
            success = await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(asdict(entry), default=str)
            )
            
            if success:
                # Mettre en cache local
                self._update_local_cache(cache_key, entry)
                
                # Mettre à jour patterns fréquents
                pattern = prompt[:50].lower()
                self.frequent_patterns[pattern] = self.frequent_patterns.get(pattern, 0) + 1
                
                # Mettre à jour stats
                self.stats["cache_size"] += 1
                
                logger.info(f"💾 Réponse cachée - Stratégie: {strategy.value}, TTL: {ttl}s")
                return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise en cache: {e}")
        
        return False
    
    def _get_ttl_for_strategy(self, strategy: CacheStrategy) -> int:
        """Obtenir TTL selon la stratégie"""
        ttl_map = {
            CacheStrategy.EXACT_MATCH: self.config.exact_match_ttl,
            CacheStrategy.SEMANTIC_MATCH: self.config.semantic_match_ttl,
            CacheStrategy.CONTEXT_AWARE: self.config.context_aware_ttl,
            CacheStrategy.PREFIX_MATCH: self.config.default_ttl,
        }
        return ttl_map.get(strategy, self.config.default_ttl)
    
    async def invalidate_cache(self, pattern: str = None) -> int:
        """Invalider cache par pattern"""
        try:
            if pattern:
                keys = await self.redis.client.keys(f"llm_cache:*{pattern}*")
            else:
                keys = await self.redis.client.keys("llm_cache:*")
            
            if keys:
                deleted = await self.redis.delete(*keys)
                self.stats["cache_size"] = max(0, self.stats["cache_size"] - deleted)
                logger.info(f"🗑️ Cache invalidé - {deleted} entrées supprimées")
                return deleted
            
        except Exception as e:
            logger.error(f"❌ Erreur invalidation cache: {e}")
        
        return 0
    
    async def cleanup_expired(self):
        """Nettoyer les entrées expirées (tâche périodique)"""
        try:
            # Redis s'occupe automatiquement des TTL
            # Nettoyer seulement le cache local
            now = datetime.now()
            expired_keys = []
            
            for key, entry in self.local_cache.items():
                age = (now - entry.created_at).total_seconds()
                if age > self.config.default_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.local_cache[key]
            
            if expired_keys:
                logger.info(f"🧹 Cache local nettoyé - {len(expired_keys)} entrées expirées")
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage cache: {e}")
    
    async def preload_frequent_patterns(self):
        """Précharger les patterns fréquents"""
        if not self.config.enable_prefetch:
            return
        
        try:
            frequent = sorted(
                self.frequent_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            preloaded = 0
            for pattern, count in frequent:
                if count >= self.pattern_threshold:
                    # Chercher et précharger dans cache local
                    keys = await self.redis.client.keys(f"llm_cache:*{pattern}*")
                    for key in keys[:3]:  # Limiter
                        cached_data = await self.redis.get(key)
                        if cached_data:
                            try:
                                entry_data = json.loads(cached_data)
                                entry = CacheEntry(**entry_data)
                                self._update_local_cache(key, entry)
                                preloaded += 1
                            except (json.JSONDecodeError, TypeError):
                                continue
            
            if preloaded > 0:
                logger.info(f"🚀 Préchargement terminé - {preloaded} entrées")
                
        except Exception as e:
            logger.error(f"❌ Erreur préchargement: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir statistiques détaillées"""
        hit_rate = 0.0
        if self.stats["total_requests"] > 0:
            hit_rate = (self.stats["cache_hits"] / self.stats["total_requests"]) * 100
        
        return {
            **self.stats,
            "hit_rate_percent": hit_rate,
            "local_cache_size": len(self.local_cache),
            "frequent_patterns_count": len(self.frequent_patterns),
            "config": asdict(self.config)
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Vérification santé du cache"""
        try:
            # Test Redis
            await self.redis.client.ping()
            
            stats = self.get_stats()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "cache_stats": stats,
                "performance": {
                    "hit_rate": stats["hit_rate_percent"],
                    "avg_response_time": stats["avg_response_time"],
                    "total_cost_saved": stats["total_cost_saved"]
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e),
                "cache_stats": self.get_stats()
            }

# Factory function
def create_llm_cache_manager(
    redis_manager: RedisManager,
    config: CacheConfig = None
) -> LLMCacheManager:
    """Créer gestionnaire de cache LLM"""
    return LLMCacheManager(redis_manager, config)

# Décorateur pour cache automatique
def cache_llm_response(
    cache_manager: LLMCacheManager,
    strategy: CacheStrategy = CacheStrategy.EXACT_MATCH,
    ttl: Optional[int] = None
):
    """
    Décorateur pour cacher automatiquement les réponses LLM
    
    Usage:
        @cache_llm_response(cache_manager)
        async def call_llm(prompt, model="gpt-4"):
            # appel LLM
            return response
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extraire prompt et paramètres
            prompt = args[0] if args else kwargs.get('prompt', '')
            model = kwargs.get('model', 'default')
            temperature = kwargs.get('temperature', 0.7)
            
            # Chercher en cache
            cached_response = await cache_manager.get_cached_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                strategy=strategy
            )
            
            if cached_response:
                return cached_response
            
            # Appeler fonction originale
            start_time = time.time()
            response = await func(*args, **kwargs)
            response_time = time.time() - start_time
            
            # Mettre en cache
            await cache_manager.cache_response(
                prompt=prompt,
                response=response,
                model=model,
                temperature=temperature,
                response_time=response_time,
                strategy=strategy
            )
            
            return response
        
        return wrapper
    return decorator