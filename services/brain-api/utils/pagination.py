"""
📄 Pagination Optimisée pour APIs JARVIS
Système de pagination avec cursor, offset et optimisations de performance
"""

import asyncio
import logging
import math
import time
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from sqlalchemy import text, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

T = TypeVar('T')

class PaginationType(Enum):
    """Types de pagination supportés"""
    OFFSET = "offset"          # Pagination classique avec offset/limit
    CURSOR = "cursor"          # Pagination avec curseur (plus efficace)
    KEYSET = "keyset"         # Pagination avec keyset (plus rapide)
    HYBRID = "hybrid"         # Hybride selon le contexte

@dataclass
class PaginationConfig:
    """Configuration de pagination"""
    default_page_size: int = 20
    max_page_size: int = 100
    enable_count: bool = True           # Compter le total (coûteux)
    enable_cursor: bool = True          # Support curseur
    cursor_field: str = "id"            # Champ pour curseur
    cache_ttl: int = 300               # Cache TTL en secondes
    
    # Optimisations
    use_approximate_count: bool = True  # Compte approximatif pour gros datasets
    count_threshold: int = 10000        # Seuil pour compte approximatif
    index_hints: Dict[str, str] = None  # Hints d'index SQL

class PaginationRequest(BaseModel):
    """Requête de pagination"""
    page: Optional[int] = Field(1, ge=1, description="Numéro de page (offset)")
    page_size: Optional[int] = Field(20, ge=1, le=100, description="Taille de page")
    cursor: Optional[str] = Field(None, description="Curseur pour pagination")
    direction: Optional[str] = Field("next", regex="^(next|prev)$", description="Direction")
    sort_by: Optional[str] = Field("created_at", description="Champ de tri")
    sort_order: Optional[str] = Field("desc", regex="^(asc|desc)$", description="Ordre de tri")
    include_count: Optional[bool] = Field(True, description="Inclure le compte total")
    
    @validator('page_size')
    def validate_page_size(cls, v):
        return min(v, 100)  # Limiter à 100 max

@dataclass
class PaginationMeta:
    """Métadonnées de pagination"""
    page: int
    page_size: int
    total_items: Optional[int] = None
    total_pages: Optional[int] = None
    has_next: bool = False
    has_prev: bool = False
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    
    # Métriques de performance
    query_time: float = 0.0
    cache_hit: bool = False
    pagination_type: str = "offset"

@dataclass
class PaginatedResponse(Generic[T]):
    """Réponse paginée générique"""
    items: List[T]
    meta: PaginationMeta
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "meta": asdict(self.meta)
        }

class PaginationOptimizer:
    """
    Optimiseur de pagination avec:
    - Détection automatique du meilleur type de pagination
    - Cache des comptes pour gros datasets
    - Optimisations SQL contextuelles
    - Métriques de performance
    """
    
    def __init__(
        self,
        session: AsyncSession,
        config: PaginationConfig = None,
        redis_client=None
    ):
        self.session = session
        self.config = config or PaginationConfig()
        self.redis = redis_client
        
        # Statistiques
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "avg_query_time": 0.0,
            "pagination_types": {
                "offset": 0,
                "cursor": 0,
                "keyset": 0,
                "hybrid": 0
            }
        }
        
        logger.info("📄 Pagination Optimizer initialisé")
    
    def _generate_cache_key(self, table: str, filters: Dict, sort: str) -> str:
        """Générer clé de cache pour compte"""
        import hashlib
        
        filter_str = str(sorted(filters.items())) if filters else ""
        content = f"{table}:{filter_str}:{sort}"
        return f"pagination_count:{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _encode_cursor(self, value: Any, field: str) -> str:
        """Encoder curseur"""
        import base64
        import json
        
        cursor_data = {"value": str(value), "field": field}
        cursor_json = json.dumps(cursor_data, separators=(',', ':'))
        return base64.b64encode(cursor_json.encode()).decode()
    
    def _decode_cursor(self, cursor: str) -> Dict[str, Any]:
        """Décoder curseur"""
        import base64
        import json
        
        try:
            cursor_json = base64.b64decode(cursor.encode()).decode()
            return json.loads(cursor_json)
        except Exception as e:
            logger.error(f"❌ Erreur décodage curseur: {e}")
            return {}
    
    async def _get_cached_count(self, cache_key: str) -> Optional[int]:
        """Récupérer compte depuis cache"""
        if not self.redis:
            return None
        
        try:
            cached_count = await self.redis.get(cache_key)
            if cached_count:
                self.stats["cache_hits"] += 1
                return int(cached_count)
        except Exception as e:
            logger.error(f"❌ Erreur cache count: {e}")
        
        return None
    
    async def _cache_count(self, cache_key: str, count: int):
        """Mettre en cache le compte"""
        if not self.redis:
            return
        
        try:
            await self.redis.setex(cache_key, self.config.cache_ttl, str(count))
        except Exception as e:
            logger.error(f"❌ Erreur mise en cache count: {e}")
    
    async def _get_approximate_count(self, table_name: str, where_clause: str = "") -> int:
        """Obtenir compte approximatif rapide"""
        try:
            # Utiliser les statistiques PostgreSQL pour estimation rapide
            query = text(f"""
                SELECT reltuples::BIGINT 
                FROM pg_class 
                WHERE relname = :table_name
            """)
            
            result = await self.session.execute(query, {"table_name": table_name})
            row = result.fetchone()
            
            if row and row[0]:
                # Ajuster selon les filtres si nécessaire
                estimated_count = int(row[0])
                
                # Si pas de filtres, retourner l'estimation directe
                if not where_clause:
                    return estimated_count
                
                # Sinon, faire un échantillonnage rapide
                sample_query = text(f"""
                    SELECT COUNT(*) * (
                        SELECT reltuples FROM pg_class WHERE relname = :table_name
                    ) / GREATEST((
                        SELECT COUNT(*) FROM (
                            SELECT 1 FROM {table_name} TABLESAMPLE SYSTEM(1) LIMIT 1000
                        ) sample
                    ), 1)
                    FROM (
                        SELECT 1 FROM {table_name} TABLESAMPLE SYSTEM(1) 
                        {where_clause} LIMIT 1000
                    ) filtered_sample
                """)
                
                result = await self.session.execute(sample_query, {"table_name": table_name})
                row = result.fetchone()
                return int(row[0]) if row and row[0] else estimated_count
            
        except Exception as e:
            logger.error(f"❌ Erreur compte approximatif: {e}")
        
        return 0
    
    async def _determine_best_pagination_type(
        self,
        table_name: str,
        total_items: int,
        request: PaginationRequest
    ) -> PaginationType:
        """Déterminer le meilleur type de pagination"""
        
        # Pour de petits datasets, offset suffit
        if total_items <= 1000:
            return PaginationType.OFFSET
        
        # Pour navigation séquentielle avec curseur
        if request.cursor and request.page is None:
            return PaginationType.CURSOR
        
        # Pour gros datasets avec tri sur index
        if total_items > 10000 and request.sort_by in ["id", "created_at", "updated_at"]:
            return PaginationType.KEYSET
        
        # Hybride pour cas complexes
        if total_items > 50000:
            return PaginationType.HYBRID
        
        return PaginationType.OFFSET
    
    async def paginate_query(
        self,
        base_query: str,
        request: PaginationRequest,
        table_name: str,
        filters: Optional[Dict] = None,
        count_query: Optional[str] = None
    ) -> PaginatedResponse:
        """
        Paginer une requête SQL avec optimisations automatiques
        
        Args:
            base_query: Requête SQL de base (SELECT ... FROM table WHERE ...)
            request: Paramètres de pagination
            table_name: Nom de la table pour optimisations
            filters: Filtres pour cache du compte
            count_query: Requête de compte personnalisée
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        # Configuration de la requête
        page_size = min(request.page_size or self.config.default_page_size, self.config.max_page_size)
        sort_field = request.sort_by or self.config.cursor_field
        sort_order = request.sort_order or "desc"
        
        try:
            # Étape 1: Obtenir le compte total si demandé
            total_items = None
            if request.include_count and self.config.enable_count:
                total_items = await self._get_total_count(
                    count_query or f"SELECT COUNT(*) FROM {table_name}",
                    table_name,
                    filters or {}
                )
            
            # Étape 2: Déterminer le type de pagination optimal
            pagination_type = await self._determine_best_pagination_type(
                table_name, total_items or 0, request
            )
            
            self.stats["pagination_types"][pagination_type.value] += 1
            
            # Étape 3: Exécuter la requête paginée selon le type
            if pagination_type == PaginationType.CURSOR and request.cursor:
                items, next_cursor, prev_cursor = await self._paginate_cursor(
                    base_query, request, sort_field, sort_order, page_size
                )
            elif pagination_type == PaginationType.KEYSET:
                items, next_cursor, prev_cursor = await self._paginate_keyset(
                    base_query, request, sort_field, sort_order, page_size
                )
            else:
                # Fallback sur offset
                items, next_cursor, prev_cursor = await self._paginate_offset(
                    base_query, request, sort_field, sort_order, page_size
                )
            
            # Étape 4: Construire les métadonnées
            current_page = request.page or 1
            total_pages = None
            if total_items:
                total_pages = math.ceil(total_items / page_size)
            
            has_next = len(items) == page_size  # Approximation
            has_prev = current_page > 1 or bool(request.cursor)
            
            # Si on a le total exact, affiner has_next
            if total_items and current_page:
                has_next = current_page * page_size < total_items
            
            meta = PaginationMeta(
                page=current_page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
                next_cursor=next_cursor,
                prev_cursor=prev_cursor,
                query_time=time.time() - start_time,
                pagination_type=pagination_type.value
            )
            
            return PaginatedResponse(items=items, meta=meta)
            
        except Exception as e:
            logger.error(f"❌ Erreur pagination: {e}")
            raise
        
        finally:
            # Mettre à jour statistiques
            query_time = time.time() - start_time
            if self.stats["avg_query_time"] == 0:
                self.stats["avg_query_time"] = query_time
            else:
                self.stats["avg_query_time"] = (
                    self.stats["avg_query_time"] + query_time
                ) / 2
    
    async def _get_total_count(
        self,
        count_query: str,
        table_name: str,
        filters: Dict
    ) -> int:
        """Obtenir compte total avec cache et optimisations"""
        # Générer clé de cache
        cache_key = self._generate_cache_key(table_name, filters, count_query)
        
        # Vérifier cache
        cached_count = await self._get_cached_count(cache_key)
        if cached_count is not None:
            return cached_count
        
        try:
            # Essayer compte approximatif pour gros datasets
            if self.config.use_approximate_count:
                approx_count = await self._get_approximate_count(table_name)
                if approx_count > self.config.count_threshold:
                    await self._cache_count(cache_key, approx_count)
                    return approx_count
            
            # Compte exact
            result = await self.session.execute(text(count_query))
            row = result.fetchone()
            count = int(row[0]) if row else 0
            
            # Mettre en cache
            await self._cache_count(cache_key, count)
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Erreur compte total: {e}")
            return 0
    
    async def _paginate_offset(
        self,
        base_query: str,
        request: PaginationRequest,
        sort_field: str,
        sort_order: str,
        page_size: int
    ) -> tuple:
        """Pagination avec OFFSET/LIMIT"""
        page = request.page or 1
        offset = (page - 1) * page_size
        
        # Construire requête avec tri et limite
        order_clause = f"ORDER BY {sort_field} {sort_order.upper()}"
        limit_clause = f"LIMIT {page_size} OFFSET {offset}"
        
        query = f"{base_query} {order_clause} {limit_clause}"
        
        result = await self.session.execute(text(query))
        items = result.fetchall()
        
        # Curseurs pour compatibilité (basés sur position)
        next_cursor = None
        prev_cursor = None
        
        if len(items) == page_size:
            next_cursor = self._encode_cursor(page + 1, "page")
        
        if page > 1:
            prev_cursor = self._encode_cursor(page - 1, "page")
        
        return items, next_cursor, prev_cursor
    
    async def _paginate_cursor(
        self,
        base_query: str,
        request: PaginationRequest,
        sort_field: str,
        sort_order: str,
        page_size: int
    ) -> tuple:
        """Pagination avec curseur"""
        cursor_data = self._decode_cursor(request.cursor)
        cursor_value = cursor_data.get("value")
        
        if not cursor_value:
            return await self._paginate_offset(base_query, request, sort_field, sort_order, page_size)
        
        # Déterminer opérateur selon direction et ordre
        if request.direction == "next":
            operator = "<" if sort_order.lower() == "desc" else ">"
        else:
            operator = ">" if sort_order.lower() == "desc" else "<"
        
        # Construire clause WHERE pour curseur
        cursor_clause = f"AND {sort_field} {operator} '{cursor_value}'"
        
        # Modifier la requête base
        if "WHERE" in base_query.upper():
            query = f"{base_query} {cursor_clause}"
        else:
            query = f"{base_query} WHERE 1=1 {cursor_clause}"
        
        # Ajouter tri et limite
        order_clause = f"ORDER BY {sort_field} {sort_order.upper()}"
        limit_clause = f"LIMIT {page_size + 1}"  # +1 pour détecter has_next
        
        final_query = f"{query} {order_clause} {limit_clause}"
        
        result = await self.session.execute(text(final_query))
        all_items = result.fetchall()
        
        # Séparer les items et détecter next
        items = all_items[:page_size]
        has_more = len(all_items) > page_size
        
        # Générer curseurs
        next_cursor = None
        prev_cursor = None
        
        if items:
            last_item = items[-1]
            first_item = items[0]
            
            # Récupérer valeur du champ de tri (selon la structure de résultat)
            if hasattr(last_item, sort_field):
                last_value = getattr(last_item, sort_field)
            elif isinstance(last_item, (tuple, list)) and sort_field == "id":
                last_value = last_item[0]  # Supposer que id est la première colonne
            else:
                last_value = str(last_item)
            
            if has_more:
                next_cursor = self._encode_cursor(last_value, sort_field)
            
            # Curseur précédent basé sur le premier item
            if hasattr(first_item, sort_field):
                first_value = getattr(first_item, sort_field)
            elif isinstance(first_item, (tuple, list)) and sort_field == "id":
                first_value = first_item[0]
            else:
                first_value = str(first_item)
            
            prev_cursor = self._encode_cursor(first_value, sort_field)
        
        return items, next_cursor, prev_cursor
    
    async def _paginate_keyset(
        self,
        base_query: str,
        request: PaginationRequest,
        sort_field: str,
        sort_order: str,
        page_size: int
    ) -> tuple:
        """Pagination avec keyset (plus efficace pour gros volumes)"""
        # Pour l'implémentation initiale, utiliser cursor
        # Dans une version complète, optimiser avec plusieurs champs de tri
        return await self._paginate_cursor(base_query, request, sort_field, sort_order, page_size)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir statistiques de pagination"""
        hit_rate = 0.0
        if self.stats["total_queries"] > 0:
            hit_rate = (self.stats["cache_hits"] / self.stats["total_queries"]) * 100
        
        return {
            **self.stats,
            "cache_hit_rate": hit_rate
        }

# Utilitaires pour FastAPI
class PaginationParams:
    """Dependency injection pour FastAPI"""
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        cursor: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_count: bool = True
    ):
        self.request = PaginationRequest(
            page=page,
            page_size=page_size,
            cursor=cursor,
            sort_by=sort_by,
            sort_order=sort_order,
            include_count=include_count
        )

# Factory function
def create_pagination_optimizer(
    session: AsyncSession,
    config: PaginationConfig = None,
    redis_client = None
) -> PaginationOptimizer:
    """Créer optimiseur de pagination"""
    return PaginationOptimizer(session, config, redis_client)