"""
🗃️ Redis Manager avec Connection Pooling Optimisé
Gestionnaire centralisé pour toutes les connexions Redis avec cache intelligent
"""

import asyncio
import json
import logging
import time
import hashlib
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool as RedisConnectionPool
from redis.asyncio.sentinel import Sentinel
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from .circuit_breaker import call_redis_with_circuit_breaker, CircuitOpenException

logger = logging.getLogger(__name__)

class RedisManager:
    """
    Gestionnaire Redis optimisé avec:
    - Connection pooling configurable
    - Cache multi-niveaux avec TTL
    - Retry automatique avec circuit breaker
    - Monitoring des performances
    - Support Redis Sentinel (HA)
    """
    
    def __init__(
        self,
        redis_url: str,
        pool_size: int = 50,
        max_connections: int = 100,
        socket_timeout: int = 10,
        socket_connect_timeout: int = 10,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
        enable_sentinel: bool = False,
        sentinel_hosts: Optional[List[str]] = None,
        master_name: str = "mymaster"
    ):
        self.redis_url = redis_url
        self.pool_size = pool_size
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval
        
        # Sentinel configuration for HA
        self.enable_sentinel = enable_sentinel
        self.sentinel_hosts = sentinel_hosts or []
        self.master_name = master_name
        
        # Connection management
        self.pool: Optional[RedisConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self.sentinel: Optional[Sentinel] = None
        
        # Cache local pour réduire les appels Redis
        self.local_cache: Dict[str, Dict] = {}
        self.local_cache_ttl = 60  # 1 minute
        self.max_local_cache_size = 1000
        
        # Statistiques de performance
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "local_cache_hits": 0,
            "errors": 0,
            "avg_response_time": 0.0,
            "pool_stats": {}
        }
        
        self._initialized = False
        self._lock = asyncio.Lock()
        
        logger.info(f"🗃️ Redis Manager configuré - Pool: {pool_size}, Max: {max_connections}")
    
    async def initialize(self):
        """Initialiser les connexions Redis"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            try:
                if self.enable_sentinel:
                    await self._initialize_sentinel()
                else:
                    await self._initialize_direct()
                
                # Test la connexion
                await self._test_connection()
                
                self._initialized = True
                logger.info("✅ Redis Manager initialisé avec succès")
                
            except Exception as e:
                logger.error(f"❌ Erreur initialisation Redis: {e}")
                raise
    
    async def _initialize_direct(self):
        """Initialiser connexion directe Redis"""
        # Créer le pool de connexions
        self.pool = RedisConnectionPool.from_url(
            self.redis_url,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=self.retry_on_timeout,
            health_check_interval=self.health_check_interval,
            decode_responses=True
        )
        
        # Créer le client Redis
        self.client = redis.Redis(
            connection_pool=self.pool,
            decode_responses=True
        )
        
        logger.info(f"🔗 Connexion directe Redis configurée - {self.redis_url}")
    
    async def _initialize_sentinel(self):
        """Initialiser connexion avec Redis Sentinel pour HA"""
        if not self.sentinel_hosts:
            raise ValueError("Sentinel hosts requis pour mode HA")
        
        # Parser les hosts sentinel
        sentinel_list = []
        for host in self.sentinel_hosts:
            if ':' in host:
                hostname, port = host.split(':')
                sentinel_list.append((hostname, int(port)))
            else:
                sentinel_list.append((host, 26379))
        
        # Créer Sentinel
        self.sentinel = Sentinel(
            sentinel_list,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout
        )
        
        # Obtenir le client master
        self.client = self.sentinel.master_for(
            self.master_name,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            decode_responses=True
        )
        
        logger.info(f"🏰 Redis Sentinel configuré - Master: {self.master_name}")
    
    async def _test_connection(self):
        """Tester la connexion Redis"""
        await call_redis_with_circuit_breaker(self.client.ping)
        logger.info("✅ Test connexion Redis réussi")
    
    async def shutdown(self):
        """Arrêt propre du gestionnaire Redis"""
        logger.info("🛑 Arrêt Redis Manager...")
        
        try:
            if self.client:
                await self.client.aclose()
                logger.info("🔴 Client Redis fermé")
            
            if self.pool:
                await self.pool.disconnect()
                logger.info("🔴 Pool Redis fermé")
            
            # Nettoyer le cache local
            self.local_cache.clear()
            
            self._initialized = False
            
        except Exception as e:
            logger.error(f"❌ Erreur arrêt Redis: {e}")
    
    def _get_local_cache_key(self, key: str) -> str:
        """Générer clé cache local"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _is_local_cache_valid(self, cache_entry: Dict) -> bool:
        """Vérifier validité cache local"""
        return time.time() - cache_entry["timestamp"] < self.local_cache_ttl
    
    def _update_local_cache(self, key: str, value: Any):
        """Mettre à jour cache local"""
        if len(self.local_cache) >= self.max_local_cache_size:
            # Supprimer les entrées les plus anciennes
            oldest_key = min(
                self.local_cache.keys(),
                key=lambda k: self.local_cache[k]["timestamp"]
            )
            del self.local_cache[oldest_key]
        
        cache_key = self._get_local_cache_key(key)
        self.local_cache[cache_key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def _get_from_local_cache(self, key: str) -> Optional[Any]:
        """Récupérer depuis cache local"""
        cache_key = self._get_local_cache_key(key)
        if cache_key in self.local_cache:
            entry = self.local_cache[cache_key]
            if self._is_local_cache_valid(entry):
                self.stats["local_cache_hits"] += 1
                return entry["value"]
            else:
                # Supprimer entrée expirée
                del self.local_cache[cache_key]
        return None
    
    async def _execute_with_stats(self, operation: str, func, *args, **kwargs):
        """Exécuter opération avec statistiques"""
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            result = await call_redis_with_circuit_breaker(func, *args, **kwargs)
            
            # Mettre à jour temps de réponse moyen
            response_time = time.time() - start_time
            if self.stats["avg_response_time"] == 0:
                self.stats["avg_response_time"] = response_time
            else:
                self.stats["avg_response_time"] = (
                    self.stats["avg_response_time"] + response_time
                ) / 2
            
            return result
            
        except (RedisError, CircuitOpenException) as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Erreur Redis {operation}: {e}")
            raise
    
    # Opérations GET/SET optimisées
    async def get(self, key: str, use_local_cache: bool = True) -> Optional[str]:
        """Récupérer valeur avec cache multi-niveaux"""
        if not self._initialized:
            await self.initialize()
        
        # Vérifier cache local
        if use_local_cache:
            cached_value = self._get_from_local_cache(key)
            if cached_value is not None:
                return cached_value
        
        # Récupérer depuis Redis
        try:
            value = await self._execute_with_stats("GET", self.client.get, key)
            
            if value is not None:
                self.stats["cache_hits"] += 1
                if use_local_cache:
                    self._update_local_cache(key, value)
            else:
                self.stats["cache_misses"] += 1
            
            return value
            
        except Exception as e:
            logger.error(f"❌ Erreur GET {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Définir valeur avec options"""
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self._execute_with_stats(
                "SET", 
                self.client.set, 
                key, value, ex=ex, px=px, nx=nx, xx=xx
            )
            
            # Mettre à jour cache local si succès
            if result and ex and ex < self.local_cache_ttl:
                self._update_local_cache(key, value)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur SET {key}: {e}")
            return False
    
    async def setex(self, key: str, time: int, value: str) -> bool:
        """Définir valeur avec expiration"""
        return await self.set(key, value, ex=time)
    
    async def delete(self, *keys: str) -> int:
        """Supprimer clés"""
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self._execute_with_stats("DEL", self.client.delete, *keys)
            
            # Supprimer du cache local
            for key in keys:
                cache_key = self._get_local_cache_key(key)
                self.local_cache.pop(cache_key, None)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur DELETE {keys}: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """Vérifier existence clés"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._execute_with_stats("EXISTS", self.client.exists, *keys)
        except Exception as e:
            logger.error(f"❌ Erreur EXISTS {keys}: {e}")
            return 0
    
    async def expire(self, key: str, time: int) -> bool:
        """Définir expiration"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._execute_with_stats("EXPIRE", self.client.expire, key, time)
        except Exception as e:
            logger.error(f"❌ Erreur EXPIRE {key}: {e}")
            return False
    
    # Opérations JSON optimisées
    async def get_json(self, key: str, default: Any = None, use_local_cache: bool = True) -> Any:
        """Récupérer objet JSON"""
        try:
            value = await self.get(key, use_local_cache)
            if value is None:
                return default
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur décodage JSON {key}: {e}")
            return default
    
    async def set_json(
        self, 
        key: str, 
        value: Any, 
        ex: Optional[int] = None,
        px: Optional[int] = None
    ) -> bool:
        """Définir objet JSON"""
        try:
            json_value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            return await self.set(key, json_value, ex=ex, px=px)
        except (TypeError, ValueError) as e:
            logger.error(f"❌ Erreur encodage JSON {key}: {e}")
            return False
    
    # Opérations de liste
    async def lpush(self, key: str, *values: str) -> int:
        """Ajouter au début de liste"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._execute_with_stats("LPUSH", self.client.lpush, key, *values)
        except Exception as e:
            logger.error(f"❌ Erreur LPUSH {key}: {e}")
            return 0
    
    async def rpush(self, key: str, *values: str) -> int:
        """Ajouter à la fin de liste"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._execute_with_stats("RPUSH", self.client.rpush, key, *values)
        except Exception as e:
            logger.error(f"❌ Erreur RPUSH {key}: {e}")
            return 0
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Récupérer range de liste"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._execute_with_stats("LRANGE", self.client.lrange, key, start, end)
        except Exception as e:
            logger.error(f"❌ Erreur LRANGE {key}: {e}")
            return []
    
    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim liste"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._execute_with_stats("LTRIM", self.client.ltrim, key, start, end)
        except Exception as e:
            logger.error(f"❌ Erreur LTRIM {key}: {e}")
            return False
    
    # Opérations de set ordonné
    async def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Ajouter à set ordonné"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._execute_with_stats("ZADD", self.client.zadd, key, mapping)
        except Exception as e:
            logger.error(f"❌ Erreur ZADD {key}: {e}")
            return 0
    
    async def zrevrange(self, key: str, start: int = 0, end: int = -1, withscores: bool = False) -> List:
        """Récupérer range de set ordonné (desc)"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._execute_with_stats(
                "ZREVRANGE", 
                self.client.zrevrange, 
                key, start, end, withscores=withscores
            )
        except Exception as e:
            logger.error(f"❌ Erreur ZREVRANGE {key}: {e}")
            return []
    
    # Opérations batch pour performance
    async def mget(self, *keys: str, use_local_cache: bool = True) -> List[Optional[str]]:
        """Récupérer multiple valeurs"""
        if not self._initialized:
            await self.initialize()
        
        # Vérifier cache local pour certaines clés
        cached_results = {}
        missing_keys = []
        
        if use_local_cache:
            for i, key in enumerate(keys):
                cached_value = self._get_from_local_cache(key)
                if cached_value is not None:
                    cached_results[i] = cached_value
                else:
                    missing_keys.append((i, key))
        else:
            missing_keys = [(i, key) for i, key in enumerate(keys)]
        
        # Récupérer clés manquantes depuis Redis
        results = [None] * len(keys)
        
        if missing_keys:
            try:
                redis_keys = [key for _, key in missing_keys]
                redis_values = await self._execute_with_stats("MGET", self.client.mget, *redis_keys)
                
                for (i, key), value in zip(missing_keys, redis_values):
                    results[i] = value
                    if value is not None and use_local_cache:
                        self._update_local_cache(key, value)
                
            except Exception as e:
                logger.error(f"❌ Erreur MGET: {e}")
        
        # Intégrer résultats cache local
        for i, value in cached_results.items():
            results[i] = value
        
        return results
    
    async def mset(self, mapping: Dict[str, str]) -> bool:
        """Définir multiple valeurs"""
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self._execute_with_stats("MSET", self.client.mset, mapping)
            
            # Mettre à jour cache local
            for key, value in mapping.items():
                self._update_local_cache(key, value)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur MSET: {e}")
            return False
    
    # Pipeline pour opérations batch
    @asynccontextmanager
    async def pipeline(self):
        """Context manager pour pipeline Redis"""
        if not self._initialized:
            await self.initialize()
        
        pipe = self.client.pipeline()
        try:
            yield pipe
            await pipe.execute()
        except Exception as e:
            logger.error(f"❌ Erreur pipeline: {e}")
            raise
        finally:
            await pipe.reset()
    
    # Monitoring et stats
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Obtenir statistiques du pool"""
        if not self.pool:
            return {}
        
        try:
            pool_stats = {
                "created_connections": getattr(self.pool, 'created_connections', 0),
                "available_connections": getattr(self.pool, 'available_connections', 0),
                "in_use_connections": getattr(self.pool, 'in_use_connections', 0),
                "max_connections": self.pool.max_connections
            }
            
            self.stats["pool_stats"] = pool_stats
            return pool_stats
            
        except Exception as e:
            logger.error(f"❌ Erreur stats pool: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir toutes les statistiques"""
        return {
            **self.stats,
            "initialized": self._initialized,
            "local_cache_size": len(self.local_cache),
            "local_cache_hit_ratio": (
                self.stats["local_cache_hits"] / max(1, self.stats["total_requests"])
            ) * 100,
            "redis_cache_hit_ratio": (
                self.stats["cache_hits"] / max(1, self.stats["cache_hits"] + self.stats["cache_misses"])
            ) * 100,
            "error_rate": (
                self.stats["errors"] / max(1, self.stats["total_requests"])
            ) * 100
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérification santé Redis"""
        if not self._initialized:
            return {"status": "not_initialized", "healthy": False}
        
        try:
            start_time = time.time()
            await self.client.ping()
            response_time = time.time() - start_time
            
            pool_stats = await self.get_pool_stats()
            
            return {
                "status": "healthy",
                "healthy": True,
                "response_time": response_time,
                "pool_stats": pool_stats,
                "stats": self.get_stats()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e),
                "stats": self.get_stats()
            }

# Factory function pour créer RedisManager
def create_redis_manager(
    redis_url: str,
    **kwargs
) -> RedisManager:
    """Créer instance RedisManager avec configuration optimisée"""
    return RedisManager(redis_url, **kwargs)

# Instance globale partagée (à utiliser avec précaution)
_global_redis_manager: Optional[RedisManager] = None

async def get_redis_manager(redis_url: str = None, **kwargs) -> RedisManager:
    """Obtenir instance globale RedisManager (singleton)"""
    global _global_redis_manager
    
    if _global_redis_manager is None:
        if redis_url is None:
            raise ValueError("redis_url requis pour première initialisation")
        _global_redis_manager = create_redis_manager(redis_url, **kwargs)
        await _global_redis_manager.initialize()
    
    return _global_redis_manager