"""
🎭 Persona Manager - Gestionnaire central des personnalités IA
Orchestre les différentes personas et gère les transitions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .base_persona import BasePersona
from .jarvis_classic import JarvisClassicPersona
from .friday import FridayPersona
from .edith import EdithPersona

logger = logging.getLogger(__name__)


@dataclass
class PersonaState:
    """État actuel d'une persona"""
    name: str
    active_since: datetime
    usage_count: int = 0
    last_interaction: Optional[datetime] = None
    user_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_preferences is None:
            self.user_preferences = {}


@dataclass
class PersonaTransition:
    """Information de transition entre personas"""
    from_persona: str
    to_persona: str
    timestamp: datetime
    reason: str
    user_id: Optional[str] = None


class PersonaManager:
    """
    Gestionnaire central des personas JARVIS
    
    Responsabilités:
    - Chargement et initialisation des personas
    - Changement de persona actif
    - Gestion de l'état et des préférences
    - Adaptation contextuelle
    - Persistance des données
    """
    
    def __init__(self, memory_manager=None, default_persona: str = "jarvis_classic"):
        self.memory_manager = memory_manager
        self.default_persona_name = default_persona
        
        # Registry des personas disponibles
        self._persona_classes: Dict[str, Type[BasePersona]] = {
            "jarvis_classic": JarvisClassicPersona,
            "friday": FridayPersona,
            "edith": EdithPersona
        }
        
        # Instances des personas
        self._personas: Dict[str, BasePersona] = {}
        
        # État du gestionnaire
        self._current_persona: Optional[BasePersona] = None
        self._persona_states: Dict[str, PersonaState] = {}
        self._transition_history: List[PersonaTransition] = []
        
        # Configuration
        self._transition_delay = 0.5  # Délai entre transitions (secondes)
        self._max_history = 100       # Historique des transitions
        
        # Cache d'adaptation contextuelle
        self._context_cache: Dict[str, Any] = {}
        self._cache_timeout = timedelta(minutes=30)
        
        logger.info("🎭 PersonaManager initialisé")
    
    async def initialize(self):
        """Initialisation asynchrone du gestionnaire"""
        logger.info("🚀 Initialisation PersonaManager...")
        
        # Charger toutes les personas
        await self._load_all_personas()
        
        # Restaurer l'état depuis la mémoire persistante
        await self._restore_state()
        
        # Activer la persona par défaut si aucune n'est active
        if not self._current_persona:
            await self.switch_persona(self.default_persona_name)
        
        logger.info(f"✅ PersonaManager prêt - Persona active: {self._current_persona.name}")
    
    async def shutdown(self):
        """Arrêt propre du gestionnaire"""
        logger.info("🛑 Arrêt PersonaManager...")
        
        # Sauvegarder l'état
        await self._save_state()
        
        # Nettoyer les ressources
        self._personas.clear()
        self._context_cache.clear()
        
        logger.info("✅ PersonaManager arrêté proprement")
    
    async def _load_all_personas(self):
        """Charger toutes les personas disponibles"""
        for name, persona_class in self._persona_classes.items():
            try:
                persona = persona_class()
                self._personas[name] = persona
                
                # Initialiser l'état de la persona
                self._persona_states[name] = PersonaState(
                    name=name,
                    active_since=datetime.now()
                )
                
                logger.info(f"✅ Persona '{name}' chargée")
                
            except Exception as e:
                logger.error(f"❌ Erreur chargement persona '{name}': {e}")
    
    async def switch_persona(self, persona_name: str, reason: str = "user_request", user_id: Optional[str] = None) -> bool:
        """
        Changer la persona active
        
        Args:
            persona_name: Nom de la persona à activer
            reason: Raison du changement
            user_id: ID de l'utilisateur si applicable
        
        Returns:
            bool: True si le changement a réussi
        """
        if persona_name not in self._personas:
            logger.warning(f"⚠️ Persona inconnue: {persona_name}")
            return False
        
        # Éviter les changements inutiles
        if self._current_persona and self._current_persona.name == persona_name:
            logger.info(f"📌 Persona '{persona_name}' déjà active")
            return True
        
        try:
            # Délai de transition pour éviter les changements trop rapides
            await asyncio.sleep(self._transition_delay)
            
            # Enregistrer la transition
            old_persona_name = self._current_persona.name if self._current_persona else None
            transition = PersonaTransition(
                from_persona=old_persona_name or "none",
                to_persona=persona_name,
                timestamp=datetime.now(),
                reason=reason,
                user_id=user_id
            )
            self._transition_history.append(transition)
            
            # Limiter l'historique
            if len(self._transition_history) > self._max_history:
                self._transition_history = self._transition_history[-self._max_history:]
            
            # Changer la persona
            self._current_persona = self._personas[persona_name]
            
            # Mettre à jour l'état
            state = self._persona_states[persona_name]
            state.active_since = datetime.now()
            state.usage_count += 1
            state.last_interaction = datetime.now()
            
            # Sauvegarder l'état
            await self._save_current_persona(persona_name)
            
            logger.info(f"🎭 Persona changée: {old_persona_name} → {persona_name} (raison: {reason})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur changement persona: {e}")
            return False
    
    def get_current_persona(self) -> Optional[BasePersona]:
        """Obtenir la persona actuellement active"""
        return self._current_persona
    
    def get_available_personas(self) -> Dict[str, Dict[str, Any]]:
        """Obtenir la liste des personas disponibles avec leurs infos"""
        result = {}
        
        for name, persona in self._personas.items():
            state = self._persona_states.get(name)
            result[name] = {
                **persona.get_persona_info(),
                "is_active": self._current_persona and self._current_persona.name == name,
                "usage_count": state.usage_count if state else 0,
                "last_used": state.last_interaction.isoformat() if state and state.last_interaction else None
            }
        
        return result
    
    def format_response(self, content: str, context: Optional[Dict] = None) -> str:
        """
        Formater une réponse avec la persona active
        
        Args:
            content: Contenu de base
            context: Contexte additionnel
        
        Returns:
            Réponse formatée selon la persona active
        """
        if not self._current_persona:
            return content
        
        try:
            # Adapter le contexte si nécessaire
            adapted_context = self._adapt_context(context)
            
            # Appliquer le formatage de la persona
            formatted = self._current_persona.format_response(content, adapted_context)
            
            # Mettre à jour les statistiques d'interaction
            state = self._persona_states.get(self._current_persona.name)
            if state:
                state.last_interaction = datetime.now()
            
            return formatted
            
        except Exception as e:
            logger.error(f"❌ Erreur formatage réponse: {e}")
            return content
    
    def _adapt_context(self, context: Optional[Dict]) -> Optional[Dict]:
        """Adapter le contexte selon la persona active"""
        if not context or not self._current_persona:
            return context
        
        adapted = context.copy()
        
        # Ajouter les informations de la persona
        adapted["current_persona"] = self._current_persona.name
        adapted["persona_style"] = self._current_persona.response_style.value
        
        # Adapter selon les préférences utilisateur stockées
        state = self._persona_states.get(self._current_persona.name)
        if state and state.user_preferences:
            adapted.update(state.user_preferences)
        
        return adapted
    
    async def suggest_persona_switch(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Suggérer un changement de persona basé sur le contexte
        
        Args:
            context: Contexte de la conversation/situation
            
        Returns:
            Nom de la persona suggérée ou None
        """
        if not context:
            return None
        
        # Analyser le contexte pour suggérer la meilleure persona
        task_type = context.get("task_type", "").lower()
        user_mood = context.get("user_mood", "").lower()
        technical_level = context.get("technical_level", "").lower()
        
        current_name = self._current_persona.name if self._current_persona else ""
        
        # Règles de suggestion
        if "security" in task_type or "analysis" in task_type or "technical" in task_type:
            if current_name != "edith":
                return "edith"
        
        elif "casual" in user_mood or "relaxed" in user_mood or "friendly" in task_type:
            if current_name != "friday":
                return "friday"
        
        elif "formal" in user_mood or "professional" in task_type or technical_level == "expert":
            if current_name != "jarvis_classic":
                return "jarvis_classic"
        
        return None
    
    def get_persona_statistics(self) -> Dict[str, Any]:
        """Obtenir les statistiques d'utilisation des personas"""
        total_usage = sum(state.usage_count for state in self._persona_states.values())
        
        stats = {
            "total_interactions": total_usage,
            "current_persona": self._current_persona.name if self._current_persona else None,
            "total_transitions": len(self._transition_history),
            "personas": {}
        }
        
        for name, state in self._persona_states.items():
            usage_percentage = (state.usage_count / total_usage * 100) if total_usage > 0 else 0
            
            stats["personas"][name] = {
                "usage_count": state.usage_count,
                "usage_percentage": round(usage_percentage, 2),
                "active_since": state.active_since.isoformat(),
                "last_interaction": state.last_interaction.isoformat() if state.last_interaction else None,
                "is_current": self._current_persona and self._current_persona.name == name
            }
        
        return stats
    
    def get_transition_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtenir l'historique des transitions"""
        recent_transitions = self._transition_history[-limit:]
        
        return [
            {
                "from_persona": t.from_persona,
                "to_persona": t.to_persona,
                "timestamp": t.timestamp.isoformat(),
                "reason": t.reason,
                "user_id": t.user_id
            }
            for t in recent_transitions
        ]
    
    async def update_user_preferences(self, persona_name: str, preferences: Dict[str, Any]):
        """Mettre à jour les préférences utilisateur pour une persona"""
        if persona_name in self._persona_states:
            state = self._persona_states[persona_name]
            state.user_preferences.update(preferences)
            
            # Sauvegarder les préférences
            await self._save_state()
            
            logger.info(f"📝 Préférences mises à jour pour {persona_name}")
    
    async def _save_state(self):
        """Sauvegarder l'état dans la mémoire persistante"""
        if not self.memory_manager:
            return
        
        try:
            state_data = {
                "current_persona": self._current_persona.name if self._current_persona else None,
                "persona_states": {
                    name: {
                        "name": state.name,
                        "active_since": state.active_since.isoformat(),
                        "usage_count": state.usage_count,
                        "last_interaction": state.last_interaction.isoformat() if state.last_interaction else None,
                        "user_preferences": state.user_preferences
                    }
                    for name, state in self._persona_states.items()
                },
                "transition_history": [
                    {
                        "from_persona": t.from_persona,
                        "to_persona": t.to_persona,
                        "timestamp": t.timestamp.isoformat(),
                        "reason": t.reason,
                        "user_id": t.user_id
                    }
                    for t in self._transition_history[-50:]  # Garder les 50 dernières
                ]
            }
            
            await self.memory_manager.store_data(
                "persona_manager_state",
                state_data,
                metadata={"type": "persona_state", "timestamp": datetime.now().isoformat()}
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde état: {e}")
    
    async def _restore_state(self):
        """Restaurer l'état depuis la mémoire persistante"""
        if not self.memory_manager:
            return
        
        try:
            state_data = await self.memory_manager.get_data("persona_manager_state")
            
            if state_data:
                # Restaurer les états des personas
                if "persona_states" in state_data:
                    for name, state_info in state_data["persona_states"].items():
                        if name in self._persona_states:
                            state = self._persona_states[name]
                            state.usage_count = state_info.get("usage_count", 0)
                            state.user_preferences = state_info.get("user_preferences", {})
                            
                            if state_info.get("last_interaction"):
                                state.last_interaction = datetime.fromisoformat(state_info["last_interaction"])
                
                # Restaurer l'historique des transitions
                if "transition_history" in state_data:
                    self._transition_history = [
                        PersonaTransition(
                            from_persona=t["from_persona"],
                            to_persona=t["to_persona"],
                            timestamp=datetime.fromisoformat(t["timestamp"]),
                            reason=t["reason"],
                            user_id=t.get("user_id")
                        )
                        for t in state_data["transition_history"]
                    ]
                
                # Restaurer la persona active
                current_persona_name = state_data.get("current_persona")
                if current_persona_name and current_persona_name in self._personas:
                    self._current_persona = self._personas[current_persona_name]
                
                logger.info("✅ État restauré depuis la mémoire persistante")
                
        except Exception as e:
            logger.warning(f"⚠️ Impossible de restaurer l'état: {e}")
    
    async def _save_current_persona(self, persona_name: str):
        """Sauvegarder juste la persona actuelle (rapide)"""
        if not self.memory_manager:
            return
        
        try:
            await self.memory_manager.store_data(
                "current_persona",
                {"name": persona_name, "timestamp": datetime.now().isoformat()},
                metadata={"type": "current_persona"}
            )
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde persona actuelle: {e}")
    
    def __str__(self) -> str:
        current = self._current_persona.name if self._current_persona else "None"
        return f"PersonaManager(current={current}, available={len(self._personas)})"