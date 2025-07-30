"""
🎭 Base Persona - Classe de base pour toutes les personnalités IA
Architecture modulaire pour personnalisation comportementale
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
import random


class ResponseStyle(Enum):
    """Styles de réponse possibles"""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"


class Priority(Enum):
    """Priorités de comportement"""
    SECURITY = "security"
    EFFICIENCY = "efficiency"
    FRIENDLINESS = "friendliness"
    ACCURACY = "accuracy"
    CREATIVITY = "creativity"


@dataclass
class PersonalityTraits:
    """Traits de personnalité quantifiés (0.0 à 1.0)"""
    formality: float = 0.5      # Niveau de formalité
    humor: float = 0.3          # Utilisation de l'humour
    proactivity: float = 0.6    # Tendance à anticiper les besoins
    verbosity: float = 0.5      # Longueur des réponses
    empathy: float = 0.4        # Réactions émotionnelles
    confidence: float = 0.7     # Assurance dans les réponses
    
    def __post_init__(self):
        """Validation des valeurs entre 0 et 1"""
        for field_name, value in asdict(self).items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{field_name} doit être entre 0.0 et 1.0, reçu: {value}")


@dataclass
class VoicePreferences:
    """Préférences vocales pour la synthèse vocale"""
    pitch: float = 0.0          # Hauteur de voix (-1.0 à 1.0)
    speed: float = 0.0          # Vitesse (-1.0 à 1.0)
    volume: float = 0.8         # Volume (0.0 à 1.0)
    emotion: str = "neutral"    # Émotion de base
    accent: str = "american"    # Accent vocal


class BasePersona(ABC):
    """
    Classe de base abstraite pour toutes les personas IA
    Définit l'interface commune et les comportements de base
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.personality = self._define_personality()
        self.voice = self._define_voice_preferences()
        self.response_style = self._define_response_style()
        self.priorities = self._define_priorities()
        
        # Phrases typiques et expressions
        self.greetings = self._define_greetings()
        self.confirmations = self._define_confirmations() 
        self.thinking_phrases = self._define_thinking_phrases()
        self.error_responses = self._define_error_responses()
        self.farewells = self._define_farewells()
        
        # Comportements spécifiques
        self.behavior_patterns = self._define_behavior_patterns()
    
    @abstractmethod
    def _define_personality(self) -> PersonalityTraits:
        """Définir les traits de personnalité spécifiques"""
        pass
    
    @abstractmethod
    def _define_voice_preferences(self) -> VoicePreferences:
        """Définir les préférences vocales"""
        pass
    
    @abstractmethod
    def _define_response_style(self) -> ResponseStyle:
        """Définir le style de réponse par défaut"""
        pass
    
    @abstractmethod
    def _define_priorities(self) -> List[Priority]:
        """Définir les priorités comportementales"""
        pass
    
    @abstractmethod
    def _define_greetings(self) -> List[str]:
        """Phrases de salutation"""
        pass
    
    @abstractmethod
    def _define_confirmations(self) -> List[str]:
        """Phrases de confirmation"""
        pass
    
    @abstractmethod
    def _define_thinking_phrases(self) -> List[str]:
        """Phrases pendant la réflexion"""
        pass
    
    @abstractmethod
    def _define_error_responses(self) -> List[str]:
        """Réponses en cas d'erreur"""
        pass
    
    @abstractmethod
    def _define_farewells(self) -> List[str]:
        """Phrases d'au revoir"""
        pass
    
    def _define_behavior_patterns(self) -> Dict[str, Any]:
        """Patterns comportementaux par défaut (peut être surchargé)"""
        return {
            "interrupt_threshold": 0.5,  # Seuil pour interrompre
            "context_memory": 10,        # Messages à retenir
            "suggestion_frequency": 0.3,  # Fréquence de suggestions
            "explanation_detail": 0.7    # Niveau de détail
        }
    
    def get_random_phrase(self, phrase_type: str) -> str:
        """Obtenir une phrase aléatoire d'un type donné"""
        phrases = getattr(self, phrase_type, [])
        if phrases:
            return random.choice(phrases)
        return ""
    
    def format_response(self, content: str, context: Optional[Dict] = None) -> str:
        """
        Formater une réponse selon la personnalité
        
        Args:
            content: Contenu de base de la réponse
            context: Contexte additionnel (utilisateur, situation, etc.)
        
        Returns:
            Réponse formatée selon la persona
        """
        # Ajouter un préfixe selon la personnalité
        if self.personality.formality > 0.7:
            prefix = "Monsieur, " if context and context.get("user_title") else ""
        elif self.personality.formality < 0.3:
            prefix = ""
        else:
            prefix = ""
        
        # Ajuster la verbosité
        if self.personality.verbosity > 0.7:
            # Ajouter des détails supplémentaires
            if self.personality.confidence > 0.6:
                suffix = " Je suis confiant dans cette réponse."
            else:
                suffix = " N'hésitez pas si vous avez des questions."
        elif self.personality.verbosity < 0.3:
            # Réponse plus concise
            content = self._make_concise(content)
            suffix = ""
        else:
            suffix = ""
        
        # Ajouter de l'humour si approprié
        if self.personality.humor > 0.6 and random.random() < 0.3:
            humor_touch = self._add_humor_touch(content, context)
            if humor_touch:
                content = humor_touch
        
        return f"{prefix}{content}{suffix}".strip()
    
    def _make_concise(self, content: str) -> str:
        """Rendre le contenu plus concis"""
        # Supprimer les phrases redondantes ou trop détaillées
        sentences = content.split('. ')
        if len(sentences) > 2:
            # Garder les phrases les plus importantes
            return '. '.join(sentences[:2]) + '.'
        return content
    
    def _add_humor_touch(self, content: str, context: Optional[Dict]) -> Optional[str]:
        """Ajouter une touche d'humour (peut être surchargé par les sous-classes)"""
        return None
    
    def should_interrupt(self, confidence_score: float) -> bool:
        """Déterminer si la persona devrait interrompre basé sur sa personnalité"""
        threshold = self.behavior_patterns.get("interrupt_threshold", 0.5)
        proactivity_factor = self.personality.proactivity
        
        # Ajuster le seuil selon la proactivité
        adjusted_threshold = threshold * (1 - proactivity_factor * 0.3)
        
        return confidence_score > adjusted_threshold
    
    def get_suggestion_probability(self) -> float:
        """Probabilité de faire une suggestion proactive"""
        base_freq = self.behavior_patterns.get("suggestion_frequency", 0.3)
        return base_freq * self.personality.proactivity
    
    def adapt_to_user_context(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapter le comportement selon le profil utilisateur
        
        Args:
            user_profile: Profil utilisateur avec préférences
        
        Returns:
            Ajustements comportementaux temporaires
        """
        adjustments = {}
        
        # Adapter selon les préférences utilisateur
        if user_profile.get("prefers_concise"):
            adjustments["verbosity_modifier"] = -0.3
        
        if user_profile.get("technical_level") == "expert":
            adjustments["technical_detail"] = 0.9
        elif user_profile.get("technical_level") == "beginner":
            adjustments["technical_detail"] = 0.3
            adjustments["explanation_detail"] = 0.9
        
        if user_profile.get("interaction_style") == "formal":
            adjustments["formality_modifier"] = 0.2
        elif user_profile.get("interaction_style") == "casual":
            adjustments["formality_modifier"] = -0.2
        
        return adjustments
    
    def get_persona_info(self) -> Dict[str, Any]:
        """Obtenir les informations complètes de la persona"""
        return {
            "name": self.name,
            "description": self.description,
            "personality": asdict(self.personality),
            "voice": asdict(self.voice),
            "response_style": self.response_style.value,
            "priorities": [p.value for p in self.priorities],
            "behavior_patterns": self.behavior_patterns,
            "sample_phrases": {
                "greeting": self.get_random_phrase("greetings"),
                "confirmation": self.get_random_phrase("confirmations"),
                "thinking": self.get_random_phrase("thinking_phrases"),
                "farewell": self.get_random_phrase("farewells")
            }
        }
    
    def __str__(self) -> str:
        return f"Persona({self.name}): {self.description}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"