"""
Système de mémoire persistante pour JARVIS avec ChromaDB
Stockage vectoriel pour conversations, patterns et préférences utilisateur
"""
import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import uuid
from loguru import logger

# Imports conditionnels
try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    MEMORY_AVAILABLE = True
except ImportError as e:
    MEMORY_AVAILABLE = False
    logger.warning(f"Modules de mémoire non disponibles: {e}")

@dataclass
class MemoryEntry:
    """Entrée de mémoire"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5  # 0.0 = peu important, 1.0 = très important
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "importance": self.importance
        }

@dataclass
class ConversationMemory:
    """Mémoire d'une conversation"""
    conversation_id: str
    messages: List[Dict[str, str]]
    context: Dict[str, Any]
    start_time: float
    end_time: Optional[float] = None
    summary: Optional[str] = None
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Ajoute un message à la conversation"""
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
    
    def get_duration(self) -> float:
        """Retourne la durée de la conversation"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

@dataclass
class UserPreference:
    """Préférence utilisateur"""
    key: str
    value: Any
    category: str
    confidence: float = 1.0
    learned_from: str = "explicit"  # explicit, implicit, inferred
    last_updated: float = field(default_factory=time.time)

class EmbeddingGenerator:
    """Générateur d'embeddings pour la recherche sémantique"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # Dimension du modèle MiniLM
        
    async def initialize(self):
        """Initialise le modèle d'embeddings"""
        if not MEMORY_AVAILABLE:
            return False
        
        try:
            logger.info(f"🔄 Chargement du modèle d'embeddings {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            logger.success(f"✅ Modèle d'embeddings prêt (dimension: {self.dimension})")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle embeddings: {e}")
            return False
    
    def generate_embedding(self, text: str) -> List[float]:
        """Génère un embedding pour un texte"""
        if not self.model:
            return [0.0] * self.dimension
        
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Erreur génération embedding: {e}")
            return [0.0] * self.dimension
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Génère des embeddings pour une liste de textes"""
        if not self.model:
            return [[0.0] * self.dimension] * len(texts)
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"❌ Erreur génération embeddings batch: {e}")
            return [[0.0] * self.dimension] * len(texts)

class ChromaMemoryStore:
    """Store de mémoire basé sur ChromaDB"""
    
    def __init__(self, persist_directory: str = "memory"):
        self.persist_directory = Path(persist_directory)
        self.client = None
        self.collections = {}
        
        # Collections prédéfinies
        self.collection_names = {
            "conversations": "jarvis_conversations",
            "commands": "jarvis_commands", 
            "preferences": "jarvis_preferences",
            "patterns": "jarvis_patterns",
            "knowledge": "jarvis_knowledge"
        }
        
        logger.info(f"💾 Store mémoire ChromaDB initialisé ({persist_directory})")
    
    async def initialize(self):
        """Initialise ChromaDB"""
        if not MEMORY_AVAILABLE:
            logger.error("❌ ChromaDB non disponible")
            return False
        
        try:
            # Créer le dossier de persistance
            self.persist_directory.mkdir(exist_ok=True)
            
            # Configurer ChromaDB
            settings = Settings(
                persist_directory=str(self.persist_directory),
                anonymized_telemetry=False
            )
            
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=settings
            )
            
            # Créer/récupérer les collections
            for category, collection_name in self.collection_names.items():
                try:
                    collection = self.client.get_or_create_collection(
                        name=collection_name,
                        metadata={"category": category}
                    )
                    self.collections[category] = collection
                    logger.debug(f"📚 Collection '{category}' prête")
                except Exception as e:
                    logger.error(f"❌ Erreur collection '{category}': {e}")
            
            logger.success(f"✅ ChromaDB initialisé avec {len(self.collections)} collections")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation ChromaDB: {e}")
            return False
    
    def store_memory(self, category: str, entry: MemoryEntry):
        """Stocke une entrée de mémoire"""
        if category not in self.collections:
            logger.warning(f"⚠️ Catégorie '{category}' non trouvée")
            return False
        
        try:
            collection = self.collections[category]
            
            # Préparer les données
            documents = [entry.content]
            metadatas = [entry.metadata]
            ids = [entry.id]
            
            if entry.embedding:
                embeddings = [entry.embedding]
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            logger.debug(f"💾 Mémoire stockée: {category}/{entry.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur stockage mémoire: {e}")
            return False
    
    def search_memories(self, category: str, query: str, 
                       n_results: int = 5, 
                       where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Recherche des mémoires par similarité sémantique"""
        if category not in self.collections:
            return []
        
        try:
            collection = self.collections[category]
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # Formater les résultats
            memories = []
            for i in range(len(results['ids'][0])):
                memory = {
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                }
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche mémoires: {e}")
            return []
    
    def get_memory(self, category: str, memory_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une mémoire spécifique par ID"""
        if category not in self.collections:
            return None
        
        try:
            collection = self.collections[category]
            
            results = collection.get(ids=[memory_id])
            
            if results['ids']:
                return {
                    "id": results['ids'][0],
                    "content": results['documents'][0],
                    "metadata": results['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération mémoire: {e}")
            return None
    
    def update_memory(self, category: str, memory_id: str, 
                     content: str = None, metadata: Dict[str, Any] = None):
        """Met à jour une mémoire existante"""
        if category not in self.collections:
            return False
        
        try:
            collection = self.collections[category]
            
            update_data = {"ids": [memory_id]}
            
            if content:
                update_data["documents"] = [content]
            
            if metadata:
                update_data["metadatas"] = [metadata]
            
            collection.update(**update_data)
            
            logger.debug(f"🔄 Mémoire mise à jour: {category}/{memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour mémoire: {e}")
            return False
    
    def delete_memory(self, category: str, memory_id: str):
        """Supprime une mémoire"""
        if category not in self.collections:
            return False
        
        try:
            collection = self.collections[category]
            collection.delete(ids=[memory_id])
            
            logger.debug(f"🗑️ Mémoire supprimée: {category}/{memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur suppression mémoire: {e}")
            return False
    
    def get_collection_stats(self, category: str) -> Dict[str, Any]:
        """Retourne les statistiques d'une collection"""
        if category not in self.collections:
            return {}
        
        try:
            collection = self.collections[category]
            count = collection.count()
            
            return {
                "category": category,
                "count": count,
                "name": self.collection_names[category]
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur stats collection: {e}")
            return {}

class MemorySystem:
    """Système de mémoire principal pour JARVIS"""
    
    def __init__(self, persist_directory: str = "memory"):
        self.embedding_generator = EmbeddingGenerator()
        self.memory_store = ChromaMemoryStore(persist_directory)
        
        # Conversations actives
        self.active_conversations: Dict[str, ConversationMemory] = {}
        
        # Préférences utilisateur
        self.user_preferences: Dict[str, UserPreference] = {}
        
        # Cache des mémoires fréquemment accédées
        self.memory_cache = {}
        
        # Statistiques
        self.stats = {
            "memories_stored": 0,
            "memories_retrieved": 0,
            "conversations_tracked": 0,
            "preferences_learned": 0
        }
        
        logger.info("🧠 Système de mémoire JARVIS initialisé")
    
    async def initialize(self):
        """Initialise le système de mémoire"""
        try:
            logger.info("🚀 Initialisation du système de mémoire...")
            
            # Initialiser les composants
            if not await self.embedding_generator.initialize():
                logger.warning("⚠️ Modèle d'embeddings non disponible")
            
            if not await self.memory_store.initialize():
                logger.error("❌ Store de mémoire non disponible")
                return False
            
            # Charger les préférences utilisateur
            await self._load_user_preferences()
            
            logger.success("✅ Système de mémoire prêt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation mémoire: {e}")
            return False
    
    # === Gestion des conversations ===
    
    def start_conversation(self, context: Dict[str, Any] = None) -> str:
        """Démarre une nouvelle conversation"""
        conversation_id = str(uuid.uuid4())
        
        conversation = ConversationMemory(
            conversation_id=conversation_id,
            messages=[],
            context=context or {},
            start_time=time.time()
        )
        
        self.active_conversations[conversation_id] = conversation
        self.stats["conversations_tracked"] += 1
        
        logger.debug(f"💬 Nouvelle conversation: {conversation_id}")
        return conversation_id
    
    def add_message_to_conversation(self, conversation_id: str, 
                                  role: str, content: str, 
                                  metadata: Dict[str, Any] = None):
        """Ajoute un message à une conversation"""
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]
            conversation.add_message(role, content, metadata)
            logger.debug(f"💬 Message ajouté à {conversation_id}: {role}")
    
    async def end_conversation(self, conversation_id: str, 
                             save_to_memory: bool = True) -> Optional[str]:
        """Termine une conversation et la sauvegarde"""
        if conversation_id not in self.active_conversations:
            return None
        
        conversation = self.active_conversations[conversation_id]
        conversation.end_time = time.time()
        
        summary = None
        
        if save_to_memory and conversation.messages:
            # Générer un résumé de la conversation
            summary = await self._generate_conversation_summary(conversation)
            
            # Créer l'entrée de mémoire
            memory_entry = MemoryEntry(
                id=conversation_id,
                content=summary,
                metadata={
                    "type": "conversation",
                    "message_count": len(conversation.messages),
                    "duration": conversation.get_duration(),
                    "context": conversation.context,
                    "start_time": conversation.start_time,
                    "end_time": conversation.end_time
                },
                tags=["conversation"],
                importance=self._calculate_conversation_importance(conversation)
            )
            
            # Générer l'embedding
            memory_entry.embedding = self.embedding_generator.generate_embedding(summary)
            
            # Stocker en mémoire
            self.memory_store.store_memory("conversations", memory_entry)
            self.stats["memories_stored"] += 1
        
        # Nettoyer la conversation active
        del self.active_conversations[conversation_id]
        
        logger.info(f"💬 Conversation terminée: {conversation_id}")
        return summary
    
    async def _generate_conversation_summary(self, conversation: ConversationMemory) -> str:
        """Génère un résumé d'une conversation"""
        # Construire le texte de la conversation
        conversation_text = ""
        for message in conversation.messages:
            role = message["role"]
            content = message["content"]
            conversation_text += f"{role}: {content}\n"
        
        # Pour l'instant, résumé simple
        # TODO: Utiliser l'IA pour générer un vrai résumé
        summary = f"Conversation avec {len(conversation.messages)} messages. "
        
        if conversation.context:
            summary += f"Contexte: {conversation.context}. "
        
        # Extraire les mots-clés principaux
        words = conversation_text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Ignorer les mots courts
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_words:
            keywords = [word for word, _ in top_words]
            summary += f"Mots-clés: {', '.join(keywords)}."
        
        return summary
    
    def _calculate_conversation_importance(self, conversation: ConversationMemory) -> float:
        """Calcule l'importance d'une conversation"""
        importance = 0.5  # Base
        
        # Plus de messages = plus important
        message_bonus = min(0.3, len(conversation.messages) * 0.02)
        importance += message_bonus
        
        # Durée de conversation
        duration_bonus = min(0.2, conversation.get_duration() / 3600)  # Bonus pour durée
        importance += duration_bonus
        
        return min(1.0, importance)
    
    # === Stockage de commandes et patterns ===
    
    async def store_command_execution(self, command: str, result: Dict[str, Any], 
                                    context: Dict[str, Any] = None):
        """Stocke l'exécution d'une commande"""
        entry_id = hashlib.md5(f"{command}_{time.time()}".encode()).hexdigest()
        
        memory_entry = MemoryEntry(
            id=entry_id,
            content=command,
            metadata={
                "type": "command",
                "result": result,
                "context": context or {},
                "success": result.get("success", False),
                "execution_time": result.get("execution_time", 0)
            },
            tags=["command", "execution"],
            importance=0.7 if result.get("success") else 0.3
        )
        
        memory_entry.embedding = self.embedding_generator.generate_embedding(command)
        
        self.memory_store.store_memory("commands", memory_entry)
        self.stats["memories_stored"] += 1
        
        logger.debug(f"📝 Commande stockée: {command[:50]}...")
    
    async def store_user_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]):
        """Stocke un pattern d'utilisation"""
        entry_id = hashlib.md5(f"{pattern_type}_{time.time()}".encode()).hexdigest()
        
        memory_entry = MemoryEntry(
            id=entry_id,
            content=json.dumps(pattern_data),
            metadata={
                "type": "pattern",
                "pattern_type": pattern_type,
                **pattern_data
            },
            tags=["pattern", pattern_type],
            importance=0.6
        )
        
        self.memory_store.store_memory("patterns", memory_entry)
        self.stats["memories_stored"] += 1
        
        logger.debug(f"🔄 Pattern stocké: {pattern_type}")
    
    # === Gestion des préférences ===
    
    def learn_preference(self, key: str, value: Any, category: str = "general",
                        confidence: float = 1.0, source: str = "explicit"):
        """Apprend une préférence utilisateur"""
        preference = UserPreference(
            key=key,
            value=value,
            category=category,
            confidence=confidence,
            learned_from=source
        )
        
        self.user_preferences[key] = preference
        self.stats["preferences_learned"] += 1
        
        logger.debug(f"📚 Préférence apprise: {key} = {value}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Récupère une préférence utilisateur"""
        if key in self.user_preferences:
            return self.user_preferences[key].value
        return default
    
    async def _load_user_preferences(self):
        """Charge les préférences utilisateur depuis la mémoire"""
        try:
            preferences = self.memory_store.search_memories(
                "preferences", 
                "user preferences",
                n_results=100
            )
            
            for pref_data in preferences:
                metadata = pref_data["metadata"]
                if "key" in metadata and "value" in metadata:
                    preference = UserPreference(
                        key=metadata["key"],
                        value=metadata["value"],
                        category=metadata.get("category", "general"),
                        confidence=metadata.get("confidence", 1.0),
                        learned_from=metadata.get("learned_from", "stored"),
                        last_updated=metadata.get("last_updated", time.time())
                    )
                    self.user_preferences[metadata["key"]] = preference
            
            logger.info(f"📚 {len(self.user_preferences)} préférences chargées")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement préférences: {e}")
    
    async def save_user_preferences(self):
        """Sauvegarde les préférences utilisateur"""
        try:
            for key, preference in self.user_preferences.items():
                entry_id = f"pref_{hashlib.md5(key.encode()).hexdigest()}"
                
                memory_entry = MemoryEntry(
                    id=entry_id,
                    content=f"Préférence utilisateur: {key} = {preference.value}",
                    metadata={
                        "type": "preference",
                        "key": key,
                        "value": preference.value,
                        "category": preference.category,
                        "confidence": preference.confidence,
                        "learned_from": preference.learned_from,
                        "last_updated": preference.last_updated
                    },
                    tags=["preference", preference.category],
                    importance=0.8
                )
                
                self.memory_store.store_memory("preferences", memory_entry)
            
            logger.info(f"💾 {len(self.user_preferences)} préférences sauvegardées")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde préférences: {e}")
    
    # === Recherche et récupération ===
    
    async def search_memories(self, query: str, category: str = None, 
                            limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche des mémoires par similarité sémantique"""
        self.stats["memories_retrieved"] += 1
        
        if category:
            return self.memory_store.search_memories(category, query, limit)
        else:
            # Rechercher dans toutes les catégories
            all_results = []
            for cat in self.memory_store.collection_names.keys():
                results = self.memory_store.search_memories(cat, query, limit)
                all_results.extend(results)
            
            # Trier par pertinence (distance)
            all_results.sort(key=lambda x: x.get("distance", 1.0))
            return all_results[:limit]
    
    async def get_relevant_context(self, query: str, max_context: int = 3) -> str:
        """Récupère le contexte pertinent pour une requête"""
        memories = await self.search_memories(query, limit=max_context)
        
        context_parts = []
        for memory in memories:
            content = memory["content"]
            context_parts.append(content)
        
        return "\n".join(context_parts) if context_parts else ""
    
    # === Statistiques et maintenance ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système de mémoire"""
        stats = self.stats.copy()
        
        # Ajouter les stats des collections
        collection_stats = {}
        for category in self.memory_store.collection_names.keys():
            collection_stats[category] = self.memory_store.get_collection_stats(category)
        
        stats.update({
            "collections": collection_stats,
            "active_conversations": len(self.active_conversations),
            "user_preferences": len(self.user_preferences),
            "memory_available": MEMORY_AVAILABLE
        })
        
        return stats
    
    def clear_memory_cache(self):
        """Vide le cache mémoire"""
        self.memory_cache.clear()
        logger.info("🗑️ Cache mémoire vidé")
    
    async def cleanup_old_memories(self, days_old: int = 30):
        """Nettoie les vieilles mémoires peu importantes"""
        # TODO: Implémenter le nettoyage basé sur l'âge et l'importance
        logger.info(f"🧹 Nettoyage des mémoires > {days_old} jours")

# Fonctions utilitaires
async def test_memory_system():
    """Test du système de mémoire"""
    try:
        memory = MemorySystem("test_memory")
        
        if not await memory.initialize():
            return False
        
        # Test de conversation
        conv_id = memory.start_conversation({"app": "test", "mode": "demo"})
        memory.add_message_to_conversation(conv_id, "user", "Bonjour JARVIS")
        memory.add_message_to_conversation(conv_id, "assistant", "Bonjour ! Comment puis-je vous aider ?")
        memory.add_message_to_conversation(conv_id, "user", "Peux-tu m'aider avec Python ?")
        memory.add_message_to_conversation(conv_id, "assistant", "Bien sûr ! Que voulez-vous savoir sur Python ?")
        
        summary = await memory.end_conversation(conv_id)
        logger.info(f"📝 Résumé de conversation: {summary}")
        
        # Test de stockage de commande
        await memory.store_command_execution(
            "take a screenshot",
            {"success": True, "execution_time": 1.2},
            {"app": "test"}
        )
        
        # Test de préférences
        memory.learn_preference("preferred_voice", "fr-FR-DeniseNeural", "voice")
        memory.learn_preference("auto_complete", True, "interface")
        
        # Test de recherche
        results = await memory.search_memories("Python programmation")
        logger.info(f"🔍 Résultats de recherche: {len(results)}")
        
        # Statistiques
        stats = memory.get_stats()
        logger.info(f"📊 Statistiques mémoire:")
        logger.info(f"  - Mémoires stockées: {stats['memories_stored']}")
        logger.info(f"  - Conversations: {stats['conversations_tracked']}")
        logger.info(f"  - Préférences: {stats['preferences_learned']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test mémoire: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_memory_system())