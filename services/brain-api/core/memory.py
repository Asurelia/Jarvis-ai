"""
🧮 Module Mémoire Hybride - JARVIS Brain API
Système de mémoire statique + dynamique + épisodique
Optimisé avec Connection Pooling et Cache Redis
"""

import asyncio
import json
import time
import uuid
import hashlib
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque
from urllib.parse import urlparse

# Database imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import String, DateTime, Integer, Float, JSON, Text

# Redis imports
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool as RedisConnectionPool

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    id: str
    type: str  # static, dynamic, episodic
    content: str
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    relevance_score: float = 1.0
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at

@dataclass
class UserProfile:
    user_id: str
    name: str
    preferences: Dict[str, Any]
    personality_traits: Dict[str, float]
    interaction_patterns: Dict[str, Any]
    expertise_areas: List[str]
    created_at: datetime
    updated_at: datetime

# SQLAlchemy Models
class Base(DeclarativeBase):
    pass

class MemoryEntryModel(Base):
    __tablename__ = "memory_entries"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(JSON, nullable=True)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_memory_user_type', 'metadata', 'type'),
        Index('idx_memory_created', 'created_at'),
        Index('idx_memory_relevance', 'relevance_score'),
    )

class UserProfileModel(Base):
    __tablename__ = "user_profiles"
    
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    personality_traits: Mapped[Dict[str, float]] = mapped_column(JSON, nullable=False)
    interaction_patterns: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    expertise_areas: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

class HybridMemoryManager:
    """
    Gestionnaire de mémoire hybride optimisé implémentant:
    - Mémoire statique: profil utilisateur, préférences
    - Mémoire dynamique: évolution tous les 5 interactions
    - Mémoire épisodique: historique des expériences
    - Connection Pooling PostgreSQL et Redis
    - Cache multi-niveaux avec TTL
    """
    
    def __init__(self, db_url: str, redis_url: str):
        self.db_url = db_url
        self.redis_url = redis_url
        
        # Connection Pools
        self.db_engine = None
        self.db_session_factory = None
        self.redis_pool = None
        self.redis_client = None
        
        # Cache en mémoire local (L1 cache)
        self.static_memory: Dict[str, MemoryEntry] = {}
        self.dynamic_memory: Dict[str, MemoryEntry] = {}
        self.episodic_memory: deque = deque(maxlen=1000)
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # Configuration
        self.dynamic_update_interval = 5  # interactions
        self.max_episodic_entries = 1000
        self.vector_dimension = 384
        
        # Cache TTL (seconds)
        self.static_cache_ttl = 86400 * 30  # 30 days
        self.dynamic_cache_ttl = 3600  # 1 hour
        self.episodic_cache_ttl = 86400  # 1 day
        self.query_cache_ttl = 300  # 5 minutes
        
        # Connection Pool Configuration
        self.db_pool_size = 20
        self.db_max_overflow = 30
        self.db_pool_timeout = 30
        self.db_pool_recycle = 3600
        
        self.redis_pool_size = 50
        self.redis_pool_timeout = 10
        
        # Compteurs et état
        self.interaction_count = 0
        self.last_dynamic_update = time.time()
        
        # Statistiques
        self.stats = {
            "total_memories": 0,
            "static_memories": 0,
            "dynamic_memories": 0,
            "episodic_memories": 0,
            "memory_retrievals": 0,
            "memory_updates": 0,
            "avg_retrieval_time": 0.0
        }
        
        logger.info("🧮 Memory Manager initialisé")
    
    async def initialize(self):
        """Initialisation asynchrone du gestionnaire de mémoire avec connection pooling"""
        logger.info("🚀 Initialisation Memory Manager avec Connection Pooling...")
        
        try:
            # 1. Initialiser PostgreSQL Connection Pool
            await self._initialize_postgres_pool()
            
            # 2. Initialiser Redis Connection Pool
            await self._initialize_redis_pool()
            
            # 3. Créer les tables si nécessaire
            await self._create_tables()
            
            # 4. Charger les données depuis les DB avec cache
            await self._load_user_profiles()
            await self._load_static_memory()
            await self._load_recent_episodic_memory()
            
            # 5. Précharger le cache Redis
            await self._preload_redis_cache()
            
            logger.info(f"✅ Memory Manager prêt avec pools - PostgreSQL: {self.db_pool_size}, Redis: {self.redis_pool_size}")
            logger.info(f"📊 {self.stats['total_memories']} entrées chargées")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Memory Manager: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Arrêt propre du gestionnaire avec fermeture des pools"""
        logger.info("🛑 Arrêt Memory Manager...")
        
        try:
            # Sauvegarder l'état avant fermeture
            await self._save_all_memories()
            
            # Vider le cache Redis
            if self.redis_client:
                await self.redis_client.flushdb()
            
            # Fermer les connexions Redis
            if self.redis_client:
                await self.redis_client.aclose()
                logger.info("🔴 Redis connection pool fermé")
            
            # Fermer les connexions PostgreSQL
            if self.db_engine:
                await self.db_engine.dispose()
                logger.info("🔴 PostgreSQL connection pool fermé")
            
            self._log_final_stats()
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'arrêt: {e}")
    
    async def _initialize_postgres_pool(self):
        """Initialiser le pool de connexions PostgreSQL"""
        try:
            # Convertir l'URL PostgreSQL pour asyncpg
            parsed = urlparse(self.db_url)
            async_url = (
                f"postgresql+asyncpg://{parsed.username}:{parsed.password}"
                f"@{parsed.hostname}:{parsed.port}{parsed.path}"
            )
            
            # Créer le moteur avec pool optimisé
            self.db_engine = create_async_engine(
                async_url,
                poolclass=QueuePool,
                pool_size=self.db_pool_size,
                max_overflow=self.db_max_overflow,
                pool_timeout=self.db_pool_timeout,
                pool_recycle=self.db_pool_recycle,
                pool_pre_ping=True,  # Valider les connexions
                echo=False  # Pas de logs SQL en production
            )
            
            # Créer la factory de sessions
            self.db_session_factory = async_sessionmaker(
                self.db_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info(f"✅ PostgreSQL Connection Pool créé - Size: {self.db_pool_size}, Max: {self.db_pool_size + self.db_max_overflow}")
            
        except Exception as e:
            logger.error(f"❌ Erreur création PostgreSQL pool: {e}")
            raise
    
    async def _initialize_redis_pool(self):
        """Initialiser le pool de connexions Redis"""
        try:
            # Créer le pool Redis
            self.redis_pool = RedisConnectionPool.from_url(
                self.redis_url,
                max_connections=self.redis_pool_size,
                socket_timeout=self.redis_pool_timeout,
                socket_connect_timeout=self.redis_pool_timeout,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Créer le client Redis
            self.redis_client = redis.Redis(
                connection_pool=self.redis_pool,
                decode_responses=True
            )
            
            # Tester la connexion
            await self.redis_client.ping()
            
            logger.info(f"✅ Redis Connection Pool créé - Size: {self.redis_pool_size}")
            
        except Exception as e:
            logger.error(f"❌ Erreur création Redis pool: {e}")
            raise
    
    async def _create_tables(self):
        """Créer les tables PostgreSQL si nécessaire"""
        try:
            async with self.db_engine.begin() as conn:
                # Créer l'extension pgvector si nécessaire
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                
                # Créer toutes les tables
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("✅ Tables PostgreSQL créées/vérifiées")
            
        except Exception as e:
            logger.error(f"❌ Erreur création tables: {e}")
            raise
    
    async def _preload_redis_cache(self):
        """Précharger le cache Redis avec les données fréquemment utilisées"""
        try:
            # Précharger les profils utilisateur actifs
            active_users = await self._get_active_users()
            for user_id in active_users:
                cache_key = f"user_profile:{user_id}"
                if user_id in self.user_profiles:
                    await self.redis_client.setex(
                        cache_key,
                        self.static_cache_ttl,
                        json.dumps(asdict(self.user_profiles[user_id]), default=str)
                    )
            
            logger.info(f"✅ Cache Redis préchargé - {len(active_users)} profils utilisateur")
            
        except Exception as e:
            logger.error(f"❌ Erreur préchargement cache: {e}")
    
    async def _get_active_users(self, days: int = 7) -> List[str]:
        """Obtenir la liste des utilisateurs actifs des N derniers jours"""
        try:
            async with self.db_session_factory() as session:
                query = text("""
                    SELECT DISTINCT metadata->>'user_id' as user_id
                    FROM memory_entries 
                    WHERE created_at >= NOW() - INTERVAL ':days days'
                    AND metadata->>'user_id' IS NOT NULL
                    LIMIT 100
                """)
                result = await session.execute(query, {"days": days})
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"❌ Erreur récupération utilisateurs actifs: {e}")
            return []
    
    async def store_static_memory(self, user_id: str, key: str, content: str, metadata: Optional[Dict] = None) -> str:
        """
        Stocker une information en mémoire statique (profil, préférences)
        
        Args:
            user_id: ID de l'utilisateur
            key: Clé d'identification de l'information
            content: Contenu à stocker
            metadata: Métadonnées additionnelles
        
        Returns:
            str: ID de l'entrée mémoire créée
        """
        memory_id = f"static_{user_id}_{key}_{uuid.uuid4().hex[:8]}"
        
        entry = MemoryEntry(
            id=memory_id,
            type="static",
            content=content,
            embedding=await self._generate_embedding(content),
            metadata={
                "user_id": user_id,
                "key": key,
                **(metadata or {})
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Stocker en base de données
        try:
            async with self.db_session_factory() as session:
                db_entry = MemoryEntryModel(
                    id=memory_id,
                    type="static",
                    content=content,
                    embedding=entry.embedding,
                    metadata=entry.metadata,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at,
                    access_count=entry.access_count,
                    last_accessed=entry.last_accessed,
                    relevance_score=entry.relevance_score
                )
                session.add(db_entry)
                await session.commit()
        except Exception as e:
            logger.error(f"❌ Erreur stockage PostgreSQL: {e}")
        
        # Stocker dans le cache local (L1)
        self.static_memory[memory_id] = entry
        
        # Stocker dans Redis (L2)
        try:
            cache_key = f"static_memory:{memory_id}"
            await self.redis_client.setex(
                cache_key,
                self.static_cache_ttl,
                json.dumps(asdict(entry), default=str)
            )
        except Exception as e:
            logger.error(f"❌ Erreur cache Redis: {e}")
        
        self.stats["static_memories"] += 1
        self.stats["total_memories"] += 1
        self.stats["memory_updates"] += 1
        
        logger.info(f"💾 Mémoire statique stockée (3 niveaux): {key} pour {user_id}")
        return memory_id
    
    async def store_dynamic_memory(self, user_id: str, content: str, context: Optional[Dict] = None) -> str:
        """
        Stocker une information en mémoire dynamique (évolution des intérêts)
        
        Args:
            user_id: ID de l'utilisateur
            content: Contenu reflétant l'évolution
            context: Contexte de l'interaction
        
        Returns:
            str: ID de l'entrée mémoire créée
        """
        memory_id = f"dynamic_{user_id}_{uuid.uuid4().hex[:8]}"
        
        entry = MemoryEntry(
            id=memory_id,
            type="dynamic",
            content=content,
            embedding=await self._generate_embedding(content),
            metadata={
                "user_id": user_id,
                "interaction_count": self.interaction_count,
                "context": context or {},
                "evolution_point": True
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.dynamic_memory[memory_id] = entry
        self.stats["dynamic_memories"] += 1
        self.stats["total_memories"] += 1
        self.stats["memory_updates"] += 1
        
        # Nettoyer l'ancienne mémoire dynamique si trop pleine
        await self._cleanup_dynamic_memory(user_id)
        
        logger.info(f"🔄 Mémoire dynamique stockée pour {user_id} (évolution #{self.interaction_count})")
        return memory_id
    
    async def store_episodic_memory(self, user_id: str, event: str, result: str, context: Optional[Dict] = None) -> str:
        """
        Stocker un épisode/expérience en mémoire épisodique
        
        Args:
            user_id: ID de l'utilisateur
            event: Description de l'événement
            result: Résultat/conséquence
            context: Contexte de l'épisode
        
        Returns:
            str: ID de l'entrée mémoire créée
        """
        memory_id = f"episodic_{user_id}_{uuid.uuid4().hex[:8]}"
        
        episode_content = f"Événement: {event}\nRésultat: {result}"
        
        entry = MemoryEntry(
            id=memory_id,
            type="episodic",
            content=episode_content,
            embedding=await self._generate_embedding(episode_content),
            metadata={
                "user_id": user_id,
                "event": event,
                "result": result,
                "context": context or {},
                "timestamp": time.time()
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.episodic_memory.append(entry)
        self.stats["episodic_memories"] += 1
        self.stats["total_memories"] += 1
        self.stats["memory_updates"] += 1
        
        logger.info(f"📝 Épisode mémorisé: {event[:50]}... → {result[:50]}...")
        return memory_id
    
    async def retrieve_memories(self, query: str, user_id: str, memory_types: Optional[List[str]] = None, limit: int = 5) -> List[MemoryEntry]:
        """
        Récupérer des mémoires pertinentes pour une requête
        
        Args:
            query: Requête de recherche
            user_id: ID de l'utilisateur
            memory_types: Types de mémoire à rechercher (static, dynamic, episodic)
            limit: Nombre maximum de résultats
        
        Returns:
            List[MemoryEntry]: Mémoires pertinentes triées par relevance
        """
        start_time = time.time()
        self.stats["memory_retrievals"] += 1
        
        if memory_types is None:
            memory_types = ["static", "dynamic", "episodic"]
        
        # Générer embedding de la requête
        query_embedding = await self._generate_embedding(query)
        
        # Collecter toutes les mémoires candidates
        candidates = []
        
        if "static" in memory_types:
            candidates.extend([entry for entry in self.static_memory.values() 
                             if entry.metadata.get("user_id") == user_id])
        
        if "dynamic" in memory_types:
            candidates.extend([entry for entry in self.dynamic_memory.values() 
                             if entry.metadata.get("user_id") == user_id])
        
        if "episodic" in memory_types:
            candidates.extend([entry for entry in self.episodic_memory 
                             if entry.metadata.get("user_id") == user_id])
        
        # Calculer la similarité et trier
        scored_memories = []
        for memory in candidates:
            if memory.embedding:
                similarity = self._calculate_similarity(query_embedding, memory.embedding)
                # Ajouter bonus pour accès récent et fréquence
                recency_bonus = self._calculate_recency_bonus(memory)
                frequency_bonus = self._calculate_frequency_bonus(memory)
                
                total_score = similarity + recency_bonus + frequency_bonus
                scored_memories.append((total_score, memory))
        
        # Trier par score décroissant et limiter
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        results = [memory for score, memory in scored_memories[:limit]]
        
        # Mettre à jour les statistiques d'accès
        for memory in results:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
        
        # Mettre à jour le temps de récupération moyen
        retrieval_time = time.time() - start_time
        if self.stats["avg_retrieval_time"] == 0:
            self.stats["avg_retrieval_time"] = retrieval_time
        else:
            self.stats["avg_retrieval_time"] = (self.stats["avg_retrieval_time"] + retrieval_time) / 2
        
        logger.info(f"🔍 {len(results)} mémoires récupérées en {retrieval_time:.3f}s")
        return results
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]):
        """Mettre à jour le profil utilisateur"""
        if user_id not in self.user_profiles:
            # Créer nouveau profil
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                name=updates.get("name", f"User_{user_id[:8]}"),
                preferences={},
                personality_traits={},
                interaction_patterns={},
                expertise_areas=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        profile = self.user_profiles[user_id]
        
        # Appliquer les mises à jour
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now()
        
        logger.info(f"👤 Profil mis à jour pour {user_id}")
    
    async def record_interaction(self, user_id: str, query: str, response: str, context: Optional[Dict] = None):
        """
        Enregistrer une interaction et déclencher mises à jour si nécessaire
        
        Args:
            user_id: ID de l'utilisateur
            query: Requête de l'utilisateur
            response: Réponse fournie
            context: Contexte de l'interaction
        """
        self.interaction_count += 1
        
        # Stocker l'épisode
        await self.store_episodic_memory(
            user_id=user_id,
            event=f"Requête: {query}",
            result=f"Réponse: {response}",
            context=context
        )
        
        # Analyser l'interaction pour patterns
        await self._analyze_interaction_patterns(user_id, query, response, context)
        
        # Vérifier si mise à jour dynamique nécessaire
        if self.interaction_count % self.dynamic_update_interval == 0:
            await self._update_dynamic_memory(user_id)
        
        logger.info(f"📊 Interaction #{self.interaction_count} enregistrée pour {user_id}")
    
    async def get_context_for_user(self, user_id: str, current_query: str) -> Dict[str, Any]:
        """
        Obtenir le contexte complet pour un utilisateur
        
        Returns:
            Dict contenant profil, mémoires pertinentes, patterns, etc.
        """
        # Récupérer le profil
        profile = self.user_profiles.get(user_id)
        
        # Récupérer mémoires pertinentes
        relevant_memories = await self.retrieve_memories(current_query, user_id, limit=3)
        
        # Analyser les patterns récents
        recent_patterns = await self._analyze_recent_patterns(user_id)
        
        context = {
            "user_profile": asdict(profile) if profile else None,
            "relevant_memories": [asdict(memory) for memory in relevant_memories],
            "recent_patterns": recent_patterns,
            "interaction_count": self.interaction_count,
            "last_update": self.last_dynamic_update
        }
        
        return context
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Générer un embedding vectoriel pour le texte"""
        try:
            # Tentative d'utiliser sentence-transformers si disponible
            try:
                from sentence_transformers import SentenceTransformer
                if not hasattr(self, '_encoder'):
                    self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
                
                embedding = self._encoder.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except ImportError:
                # Fallback vers un embedding simple si sentence-transformers n'est pas disponible
                pass
        except Exception as e:
            logger.warning(f"Erreur lors de la génération d'embedding: {e}")
        
        # Vérifier d'abord le cache des embeddings
        try:
            embedding_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
            cached_embedding = await self.redis_client.get(embedding_key)
            if cached_embedding:
                return json.loads(cached_embedding)
        except Exception as e:
            logger.warning(f"⚠️ Erreur lecture cache embedding: {e}")
        
        # Fallback: embedding basé sur TF-IDF simplifié
        import math
        
        # Tokenization simple
        words = text.lower().split()
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Créer un vecteur basé sur les mots les plus fréquents
        embedding = [0.0] * min(self.vector_dimension, 384)
        
        for i, word in enumerate(list(word_freq.keys())[:len(embedding)]):
            # Utiliser le hash pour générer une valeur reproductible
            hash_val = hashlib.md5(word.encode()).hexdigest()
            # Convertir en float normalisé
            val = int(hash_val[:8], 16) / (16**8)
            # Appliquer la fréquence du mot
            embedding[i] = val * math.log(1 + word_freq[word])
        
        # Normaliser le vecteur
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        # Mise en cache de l'embedding
        try:
            embedding_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
            await self.redis_client.setex(
                embedding_key,
                3600,  # 1 heure
                json.dumps(embedding)
            )
        except Exception as e:
            logger.warning(f"⚠️ Erreur cache embedding: {e}")
        
        return embedding
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculer la similarité cosinus entre deux embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        # Similarity cosinus
        np1 = np.array(embedding1)
        np2 = np.array(embedding2)
        
        dot_product = np.dot(np1, np2)
        norm1 = np.linalg.norm(np1)
        norm2 = np.linalg.norm(np2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _calculate_recency_bonus(self, memory: MemoryEntry) -> float:
        """Calculer bonus de récence pour une mémoire"""
        if not memory.last_accessed:
            return 0.0
        
        hours_since_access = (datetime.now() - memory.last_accessed).total_seconds() / 3600
        
        # Décroissance exponentielle
        recency_bonus = 0.1 * np.exp(-hours_since_access / 24)  # Décroit sur 24h
        return recency_bonus
    
    def _calculate_frequency_bonus(self, memory: MemoryEntry) -> float:
        """Calculer bonus de fréquence pour une mémoire"""
        # Bonus logarithmique basé sur le nombre d'accès
        frequency_bonus = 0.05 * np.log(1 + memory.access_count)
        return min(frequency_bonus, 0.2)  # Cap à 0.2
    
    async def _analyze_interaction_patterns(self, user_id: str, query: str, response: str, context: Optional[Dict]):
        """Analyser les patterns d'interaction pour mise à jour du profil"""
        
        # Extraire les sujets/domaines d'intérêt
        interests = self._extract_interests_from_query(query)
        
        # Mettre à jour le profil avec nouveaux intérêts
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            
            # Ajouter nouveaux domaines d'expertise
            for interest in interests:
                if interest not in profile.expertise_areas:
                    profile.expertise_areas.append(interest)
            
            # Limiter à 10 domaines max
            profile.expertise_areas = profile.expertise_areas[-10:]
            profile.updated_at = datetime.now()
    
    def _extract_interests_from_query(self, query: str) -> List[str]:
        """Extraire les domaines d'intérêt d'une requête"""
        interest_keywords = {
            "programmation": ["code", "programme", "fonction", "algorithme", "python", "javascript"],
            "science": ["physique", "chimie", "biologie", "mathématiques", "recherche"],
            "technologie": ["ia", "intelligence artificielle", "machine learning", "docker", "cloud"],
            "business": ["entreprise", "management", "marketing", "finance", "stratégie"],
            "créativité": ["design", "art", "musique", "écriture", "créatif"]
        }
        
        query_lower = query.lower()
        detected_interests = []
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_interests.append(interest)
        
        return detected_interests
    
    async def _update_dynamic_memory(self, user_id: str):
        """Mettre à jour la mémoire dynamique basée sur les interactions récentes"""
        
        # Analyser les 5 dernières interactions
        recent_episodes = [entry for entry in list(self.episodic_memory)[-5:] 
                          if entry.metadata.get("user_id") == user_id]
        
        if len(recent_episodes) >= 3:  # Minimum pour détecter une évolution
            # Extraire les thèmes dominants
            themes = []
            for episode in recent_episodes:
                event = episode.metadata.get("event", "")
                themes.extend(self._extract_interests_from_query(event))
            
            if themes:
                # Créer synthèse d'évolution
                theme_counts = defaultdict(int)
                for theme in themes:
                    theme_counts[theme] += 1
                
                dominant_theme = max(theme_counts, key=theme_counts.get)
                evolution_summary = f"Intérêt croissant pour {dominant_theme} (dernières interactions)"
                
                await self.store_dynamic_memory(
                    user_id=user_id,
                    content=evolution_summary,
                    context={"dominant_theme": dominant_theme, "occurrence_count": theme_counts[dominant_theme]}
                )
        
        self.last_dynamic_update = time.time()
    
    async def _cleanup_dynamic_memory(self, user_id: str, max_entries: int = 10):
        """Nettoyer la mémoire dynamique pour éviter surcharge"""
        user_dynamic_memories = [entry for entry in self.dynamic_memory.values() 
                                if entry.metadata.get("user_id") == user_id]
        
        if len(user_dynamic_memories) > max_entries:
            # Trier par date et garder les plus récentes
            user_dynamic_memories.sort(key=lambda x: x.created_at, reverse=True)
            
            # Supprimer les plus anciennes
            to_remove = user_dynamic_memories[max_entries:]
            for memory in to_remove:
                del self.dynamic_memory[memory.id]
                self.stats["dynamic_memories"] -= 1
                self.stats["total_memories"] -= 1
    
    async def _analyze_recent_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyser les patterns des interactions récentes"""
        
        recent_episodes = [entry for entry in list(self.episodic_memory)[-10:] 
                          if entry.metadata.get("user_id") == user_id]
        
        patterns = {
            "interaction_frequency": len(recent_episodes),
            "common_themes": [],
            "time_patterns": {},
            "complexity_trend": "stable"
        }
        
        if recent_episodes:
            # Analyser les thèmes communs
            all_themes = []
            for episode in recent_episodes:
                event = episode.metadata.get("event", "")
                all_themes.extend(self._extract_interests_from_query(event))
            
            theme_counts = defaultdict(int)
            for theme in all_themes:
                theme_counts[theme] += 1
            
            patterns["common_themes"] = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return patterns
    
    async def _load_user_profiles(self):
        """Charger les profils utilisateur depuis la DB"""
        try:
            # Pour l'instant, charger depuis un fichier JSON simple
            import os
            profiles_file = "data/user_profiles.json"
            
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                
                for user_id, profile_data in profiles_data.items():
                    profile_data['created_at'] = datetime.fromisoformat(profile_data['created_at'])
                    profile_data['updated_at'] = datetime.fromisoformat(profile_data['updated_at'])
                    self.user_profiles[user_id] = UserProfile(**profile_data)
                
                logger.info(f"👤 {len(self.user_profiles)} profils utilisateur chargés")
            else:
                logger.info("👤 Aucun profil utilisateur existant trouvé")
        
        except Exception as e:
            logger.warning(f"Erreur lors du chargement des profils: {e}")
            logger.info("👤 Démarrage avec profils vides")
    
    async def _load_static_memory(self):
        """Charger la mémoire statique depuis la DB"""
        try:
            import os
            memory_file = "data/static_memory.json"
            
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                for memory_id, entry_data in memory_data.items():
                    entry_data['created_at'] = datetime.fromisoformat(entry_data['created_at'])
                    entry_data['updated_at'] = datetime.fromisoformat(entry_data['updated_at'])
                    if entry_data.get('last_accessed'):
                        entry_data['last_accessed'] = datetime.fromisoformat(entry_data['last_accessed'])
                    
                    self.static_memory[memory_id] = MemoryEntry(**entry_data)
                
                logger.info(f"💾 {len(self.static_memory)} mémoires statiques chargées")
            else:
                logger.info("💾 Aucune mémoire statique existante trouvée")
        
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de la mémoire statique: {e}")
            logger.info("💾 Démarrage avec mémoire statique vide")
    
    async def _load_recent_episodic_memory(self):
        """Charger l'historique épisodique récent"""
        try:
            import os
            memory_file = "data/episodic_memory.json"
            
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    episodes_data = json.load(f)
                
                for episode_data in episodes_data[-self.max_episodic_entries:]:
                    episode_data['created_at'] = datetime.fromisoformat(episode_data['created_at'])
                    episode_data['updated_at'] = datetime.fromisoformat(episode_data['updated_at'])
                    if episode_data.get('last_accessed'):
                        episode_data['last_accessed'] = datetime.fromisoformat(episode_data['last_accessed'])
                    
                    self.episodic_memory.append(MemoryEntry(**episode_data))
                
                logger.info(f"📝 {len(self.episodic_memory)} épisodes récents chargés")
            else:
                logger.info("📝 Aucune mémoire épisodique existante trouvée")
        
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de la mémoire épisodique: {e}")
            logger.info("📝 Démarrage avec mémoire épisodique vide")
    
    async def _save_all_memories(self):
        """Sauvegarder toutes les mémoires"""
        try:
            import os
            os.makedirs("data", exist_ok=True)
            
            # Sauvegarder les profils utilisateur
            profiles_data = {}
            for user_id, profile in self.user_profiles.items():
                profile_dict = asdict(profile)
                profile_dict['created_at'] = profile.created_at.isoformat()
                profile_dict['updated_at'] = profile.updated_at.isoformat()
                profiles_data[user_id] = profile_dict
            
            with open("data/user_profiles.json", 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, ensure_ascii=False, indent=2)
            
            # Sauvegarder la mémoire statique
            static_data = {}
            for memory_id, entry in self.static_memory.items():
                entry_dict = asdict(entry)
                entry_dict['created_at'] = entry.created_at.isoformat()
                entry_dict['updated_at'] = entry.updated_at.isoformat()
                if entry.last_accessed:
                    entry_dict['last_accessed'] = entry.last_accessed.isoformat()
                static_data[memory_id] = entry_dict
            
            with open("data/static_memory.json", 'w', encoding='utf-8') as f:
                json.dump(static_data, f, ensure_ascii=False, indent=2)
            
            # Sauvegarder la mémoire épisodique
            episodic_data = []
            for entry in self.episodic_memory:
                entry_dict = asdict(entry)
                entry_dict['created_at'] = entry.created_at.isoformat()
                entry_dict['updated_at'] = entry.updated_at.isoformat()
                if entry.last_accessed:
                    entry_dict['last_accessed'] = entry.last_accessed.isoformat()
                episodic_data.append(entry_dict)
            
            with open("data/episodic_memory.json", 'w', encoding='utf-8') as f:
                json.dump(episodic_data, f, ensure_ascii=False, indent=2)
            
            logger.info("💾 Toutes les mémoires sauvegardées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du gestionnaire de mémoire"""
        return {
            **self.stats,
            "users_count": len(self.user_profiles),
            "interaction_count": self.interaction_count,
            "last_dynamic_update": self.last_dynamic_update
        }
    
    async def _get_candidates_from_db(self, user_id: str, memory_types: List[str], query_embedding: List[float]) -> List[MemoryEntry]:
        """Récupérer les candidats depuis PostgreSQL avec requête optimisée"""
        try:
            async with self.db_session_factory() as session:
                # Requête optimisée avec similarité vectorielle si disponible
                placeholders = ','.join([f"'{t}'" for t in memory_types])
                query = text(f"""
                    SELECT id, type, content, embedding, metadata, created_at, updated_at, 
                           access_count, last_accessed, relevance_score
                    FROM memory_entries 
                    WHERE metadata->>'user_id' = :user_id 
                    AND type IN ({placeholders})
                    AND embedding IS NOT NULL
                    ORDER BY 
                        relevance_score DESC,
                        last_accessed DESC NULLS LAST,
                        created_at DESC
                    LIMIT 50
                """)
                
                result = await session.execute(query, {"user_id": user_id})
                rows = result.fetchall()
                
                candidates = []
                for row in rows:
                    entry = MemoryEntry(
                        id=row[0],
                        type=row[1],
                        content=row[2],
                        embedding=row[3],
                        metadata=row[4],
                        created_at=row[5],
                        updated_at=row[6],
                        access_count=row[7],
                        last_accessed=row[8],
                        relevance_score=row[9]
                    )
                    candidates.append(entry)
                
                return candidates
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération DB: {e}")
            return []
    
    async def _update_access_stats_batch(self, memory_ids: List[str]):
        """Mettre à jour les statistiques d'accès en lot"""
        try:
            async with self.db_session_factory() as session:
                query = text("""
                    UPDATE memory_entries 
                    SET access_count = access_count + 1,
                        last_accessed = NOW()
                    WHERE id = ANY(:memory_ids)
                """)
                await session.execute(query, {"memory_ids": memory_ids})
                await session.commit()
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour stats: {e}")
    
    def _log_final_stats(self):
        """Logger les statistiques finales"""
        stats = self.get_stats()
        logger.info(f"📊 Memory Stats - Total: {stats['total_memories']}, "
                   f"Retrievals: {stats['memory_retrievals']}, "
                   f"Avg time: {stats['avg_retrieval_time']:.3f}s")