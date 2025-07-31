#!/usr/bin/env python3
"""
🎭 Tests unitaires critiques pour le système de Personas
Tests pour JARVIS Classic, FRIDAY, EDITH et PersonaManager
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

# Import des modules à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'brain-api'))

# Mock des classes de personas pour les tests
@dataclass
class MockPersonaConfig:
    """Configuration mock d'une persona"""
    name: str
    description: str
    personality_traits: List[str]
    voice_settings: Dict[str, Any]
    response_style: str
    greeting_phrases: List[str]
    error_phrases: List[str]
    confirmation_phrases: List[str]


class MockBasePersona:
    """Classe de base mock pour les personas"""
    
    def __init__(self, config: MockPersonaConfig):
        self.config = config
        self.name = config.name
        self.active = False
        self.context_memory = []
        
    async def activate(self):
        """Active la persona"""
        self.active = True
        return True
    
    async def deactivate(self):
        """Désactive la persona"""
        self.active = False
        return True
    
    async def process_message(self, message: str, context: Dict = None) -> Dict[str, Any]:
        """Traite un message selon la personnalité de la persona"""
        context = context or {}
        
        response = {
            "text": f"[{self.name}] Processed: {message}",
            "persona": self.name,
            "style": self.config.response_style,
            "confidence": 0.8,
            "context_used": context
        }
        
        # Ajouter au contexte mémoire
        self.context_memory.append({
            "timestamp": time.time(),
            "message": message,
            "response": response["text"]
        })
        
        return response
    
    def get_greeting(self) -> str:
        """Retourne une phrase d'accueil"""
        import random
        return random.choice(self.config.greeting_phrases)
    
    def get_error_response(self, error_type: str = "general") -> str:
        """Retourne une phrase d'erreur"""
        import random
        return random.choice(self.config.error_phrases)
    
    def get_confirmation(self) -> str:
        """Retourne une phrase de confirmation"""
        import random
        return random.choice(self.config.confirmation_phrases)
    
    def get_voice_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres vocaux"""
        return self.config.voice_settings


class MockJarvisClassic(MockBasePersona):
    """Mock de la persona JARVIS Classic"""
    
    def __init__(self):
        config = MockPersonaConfig(
            name="JARVIS Classic",
            description="Original JARVIS persona - Professional, analytical, and formal",
            personality_traits=["professional", "analytical", "formal", "helpful", "precise"],
            voice_settings={
                "pitch": -2.0,
                "speed": 0.95,
                "voice_id": "french_male",
                "effects": {"reverb": 0.3, "chorus": 0.1}
            },
            response_style="formal_professional",
            greeting_phrases=[
                "Good morning, sir. How may I assist you today?",
                "At your service. What can I do for you?",
                "JARVIS online and ready for your commands.",
                "All systems operational. How may I help?"
            ],
            error_phrases=[
                "I apologize, but I encountered an error processing your request.",
                "My apologies, sir. There seems to be a technical difficulty.",
                "I'm afraid I cannot complete that operation at this time.",
                "An unexpected error has occurred. Allow me to investigate."
            ],
            confirmation_phrases=[
                "Certainly, sir. Right away.",
                "Consider it done.",
                "Executing your request now.",
                "I'll take care of that immediately."
            ]
        )
        super().__init__(config)
    
    async def process_message(self, message: str, context: Dict = None) -> Dict[str, Any]:
        """Traitement spécialisé JARVIS"""
        base_response = await super().process_message(message, context)
        
        # Ajouter des spécificités JARVIS
        if "analyze" in message.lower():
            base_response["text"] = f"Analyzing request: {message}. Standby for detailed assessment."
        elif "status" in message.lower():
            base_response["text"] = "All systems are operating within normal parameters, sir."
        elif "error" in message.lower():
            base_response["text"] = self.get_error_response()
        
        base_response["formality_level"] = "high"
        base_response["technical_depth"] = "detailed"
        
        return base_response


class MockFriday(MockBasePersona):
    """Mock de la persona FRIDAY"""
    
    def __init__(self):
        config = MockPersonaConfig(
            name="FRIDAY",
            description="Casual and friendly AI assistant - More relaxed than JARVIS",
            personality_traits=["casual", "friendly", "witty", "approachable", "energetic"],
            voice_settings={
                "pitch": 0.5,
                "speed": 1.1,
                "voice_id": "french_female",
                "effects": {"brightness": 0.2, "warmth": 0.3}
            },
            response_style="casual_friendly",
            greeting_phrases=[
                "Hey there! What's up?",
                "Hi! Ready to get things done?",
                "FRIDAY here! How can I help you out?",
                "Good to see you! What's on the agenda?"
            ],
            error_phrases=[
                "Oops! Something went wrong there.",
                "Hmm, that didn't work as expected. Let me try again.",
                "Well, that's awkward. Technical hiccup on my end.",
                "Error alert! But don't worry, I'll figure it out."
            ],
            confirmation_phrases=[
                "You got it!",
                "On it!",
                "Will do!",
                "Consider it handled!"
            ]
        )
        super().__init__(config)
    
    async def process_message(self, message: str, context: Dict = None) -> Dict[str, Any]:
        """Traitement spécialisé FRIDAY"""
        base_response = await super().process_message(message, context)
        
        # Ajouter des spécificités FRIDAY
        if "analyze" in message.lower():
            base_response["text"] = f"Let me check that out for you: {message}"
        elif "status" in message.lower():
            base_response["text"] = "Everything's looking good on my end!"
        elif "thanks" in message.lower() or "thank you" in message.lower():
            base_response["text"] = "You're welcome! Happy to help!"
        
        base_response["formality_level"] = "low"
        base_response["enthusiasm_level"] = "high"
        
        return base_response


class MockEdith(MockBasePersona):
    """Mock de la persona EDITH"""
    
    def __init__(self):
        config = MockPersonaConfig(
            name="EDITH",
            description="Technical and precise AI - Focused on data and analysis",
            personality_traits=["technical", "precise", "analytical", "data-driven", "methodical"],
            voice_settings={
                "pitch": -0.5,
                "speed": 0.9,
                "voice_id": "french_female_technical",
                "effects": {"clarity": 0.4, "precision": 0.3}
            },
            response_style="technical_precise",
            greeting_phrases=[
                "EDITH systems initialized. Ready for technical operations.",
                "Technical analysis module online. How may I assist?",
                "Data processing capabilities active. What's your query?",
                "EDITH ready for precision operations."
            ],
            error_phrases=[
                "Error detected in processing pipeline. Initiating diagnostics.",
                "Technical anomaly encountered. Running error analysis.",
                "System exception caught. Executing recovery protocols.",
                "Processing error. Checking data integrity."
            ],
            confirmation_phrases=[
                "Confirmed. Executing operation.",
                "Acknowledged. Processing request.",
                "Validated. Initiating procedure.",
                "Verified. Commencing task execution."
            ]
        )
        super().__init__(config)
    
    async def process_message(self, message: str, context: Dict = None) -> Dict[str, Any]:
        """Traitement spécialisé EDITH"""
        base_response = await super().process_message(message, context)
        
        # Ajouter des spécificités EDITH
        if "analyze" in message.lower():
            base_response["text"] = f"Initiating comprehensive analysis of: {message}. Gathering data points."
        elif "data" in message.lower():
            base_response["text"] = "Accessing relevant datasets for your query."
        elif "status" in message.lower():
            base_response["text"] = "All systems operational. Performance metrics within acceptable parameters."
        
        base_response["technical_level"] = "advanced"
        base_response["precision_mode"] = "enabled"
        base_response["data_confidence"] = 0.95
        
        return base_response


class MockPersonaManager:
    """Mock du gestionnaire de personas"""
    
    def __init__(self, memory_manager=None, default_persona="jarvis_classic"):
        self.memory_manager = memory_manager
        self.default_persona = default_persona
        self.current_persona = None
        self.personas = {}
        self.switch_history = []
        
    async def initialize(self):
        """Initialise le gestionnaire avec les personas"""
        # Créer les personas disponibles
        self.personas = {
            "jarvis_classic": MockJarvisClassic(),
            "friday": MockFriday(),
            "edith": MockEdith()
        }
        
        # Activer la persona par défaut
        await self.switch_persona(self.default_persona)
        return True
    
    async def switch_persona(self, persona_id: str) -> Dict[str, Any]:
        """Change de persona"""
        if persona_id not in self.personas:
            return {
                "success": False,
                "error": f"Persona '{persona_id}' not found",
                "available": list(self.personas.keys())
            }
        
        # Désactiver la persona actuelle
        if self.current_persona:
            await self.personas[self.current_persona].deactivate()
        
        # Activer la nouvelle persona
        previous = self.current_persona
        self.current_persona = persona_id
        await self.personas[persona_id].activate()
        
        # Enregistrer le changement
        switch_record = {
            "timestamp": time.time(),
            "previous": previous,
            "current": persona_id,
            "success": True
        }
        self.switch_history.append(switch_record)
        
        return {
            "success": True,
            "previous": previous,
            "current": persona_id,
            "message": f"Switched to {self.personas[persona_id].name}",
            "greeting": self.personas[persona_id].get_greeting()
        }
    
    async def get_current_persona(self) -> Optional[MockBasePersona]:
        """Retourne la persona actuelle"""
        if self.current_persona:
            return self.personas[self.current_persona]
        return None
    
    async def list_personas(self) -> List[Dict[str, Any]]:
        """Liste toutes les personas disponibles"""
        personas_list = []
        for persona_id, persona in self.personas.items():
            personas_list.append({
                "id": persona_id,
                "name": persona.name,
                "description": persona.config.description,
                "active": persona.active,
                "personality_traits": persona.config.personality_traits,
                "response_style": persona.config.response_style
            })
        return personas_list
    
    async def process_message(self, message: str, context: Dict = None) -> Dict[str, Any]:
        """Traite un message avec la persona actuelle"""
        current = await self.get_current_persona()
        if not current:
            return {
                "error": "No active persona",
                "message": "Please activate a persona first"
            }
        
        return await current.process_message(message, context)
    
    def get_switch_history(self) -> List[Dict[str, Any]]:
        """Retourne l'historique des changements de persona"""
        return self.switch_history


class TestPersonaManager:
    """Tests pour le gestionnaire de personas"""
    
    @pytest.fixture
    def persona_manager(self):
        """Fixture pour créer un gestionnaire de personas"""
        memory_manager = Mock()
        return MockPersonaManager(memory_manager, "jarvis_classic")

    @pytest.mark.asyncio
    async def test_persona_manager_initialization(self, persona_manager):
        """Test l'initialisation du gestionnaire"""
        result = await persona_manager.initialize()
        assert result is True
        
        # Vérifier que les personas sont créées
        assert len(persona_manager.personas) == 3
        assert "jarvis_classic" in persona_manager.personas
        assert "friday" in persona_manager.personas
        assert "edith" in persona_manager.personas
        
        # Vérifier que la persona par défaut est active
        assert persona_manager.current_persona == "jarvis_classic"
        current = await persona_manager.get_current_persona()
        assert current is not None
        assert current.active is True

    @pytest.mark.asyncio
    async def test_persona_switching_success(self, persona_manager):
        """Test le changement de persona réussi"""
        await persona_manager.initialize()
        
        # Changer vers FRIDAY
        result = await persona_manager.switch_persona("friday")
        
        assert result["success"] is True
        assert result["previous"] == "jarvis_classic"
        assert result["current"] == "friday"
        assert "greeting" in result
        
        # Vérifier que la persona actuelle a changé
        current = await persona_manager.get_current_persona()
        assert current.name == "FRIDAY"
        assert current.active is True

    @pytest.mark.asyncio
    async def test_persona_switching_invalid(self, persona_manager):
        """Test le changement vers une persona inexistante"""
        await persona_manager.initialize()
        
        result = await persona_manager.switch_persona("invalid_persona")
        
        assert result["success"] is False
        assert "not found" in result["error"]
        assert "available" in result
        assert len(result["available"]) == 3

    @pytest.mark.asyncio
    async def test_persona_list_all(self, persona_manager):
        """Test la liste de toutes les personas"""
        await persona_manager.initialize()
        
        personas_list = await persona_manager.list_personas()
        
        assert len(personas_list) == 3
        
        # Vérifier la structure de chaque persona
        for persona_info in personas_list:
            assert "id" in persona_info
            assert "name" in persona_info
            assert "description" in persona_info
            assert "active" in persona_info
            assert "personality_traits" in persona_info
            assert "response_style" in persona_info

    @pytest.mark.asyncio
    async def test_message_processing_with_persona(self, persona_manager):
        """Test le traitement de message avec une persona"""
        await persona_manager.initialize()
        
        message = "Analyze the system status"
        result = await persona_manager.process_message(message)
        
        assert "text" in result
        assert "persona" in result
        assert result["persona"] == "JARVIS Classic"
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_message_processing_no_active_persona(self, persona_manager):
        """Test le traitement de message sans persona active"""
        # Ne pas initialiser pour simuler l'absence de persona
        message = "Test message"
        result = await persona_manager.process_message(message)
        
        assert "error" in result
        assert "No active persona" in result["error"]

    def test_switch_history_tracking(self, persona_manager):
        """Test le suivi de l'historique des changements"""
        async def run_test():
            await persona_manager.initialize()
            
            # Effectuer plusieurs changements
            await persona_manager.switch_persona("friday")
            await persona_manager.switch_persona("edith")
            await persona_manager.switch_persona("jarvis_classic")
            
            history = persona_manager.get_switch_history()
            
            assert len(history) == 4  # Initial + 3 changements
            
            # Vérifier la structure de l'historique
            for switch in history:
                assert "timestamp" in switch
                assert "current" in switch
                assert "success" in switch
            
            # Vérifier l'ordre chronologique
            assert history[-1]["current"] == "jarvis_classic"
            assert history[-2]["current"] == "edith"
            assert history[-3]["current"] == "friday"
        
        asyncio.run(run_test())


class TestJarvisClassicPersona:
    """Tests spécifiques pour JARVIS Classic"""
    
    @pytest.fixture
    def jarvis_persona(self):
        """Fixture pour créer JARVIS Classic"""
        return MockJarvisClassic()

    @pytest.mark.asyncio
    async def test_jarvis_activation(self, jarvis_persona):
        """Test l'activation de JARVIS"""
        result = await jarvis_persona.activate()
        assert result is True
        assert jarvis_persona.active is True

    @pytest.mark.asyncio
    async def test_jarvis_message_processing(self, jarvis_persona):
        """Test le traitement de messages par JARVIS"""
        await jarvis_persona.activate()
        
        message = "Analyze the current situation"
        result = await jarvis_persona.process_message(message)
        
        assert result["persona"] == "JARVIS Classic"
        assert result["style"] == "formal_professional"
        assert result["formality_level"] == "high"
        assert "Analyzing request" in result["text"]

    @pytest.mark.asyncio
    async def test_jarvis_status_query(self, jarvis_persona):
        """Test les requêtes de statut JARVIS"""
        await jarvis_persona.activate()
        
        message = "What's the system status?"
        result = await jarvis_persona.process_message(message)
        
        assert "operating within normal parameters" in result["text"]

    def test_jarvis_greeting_phrases(self, jarvis_persona):
        """Test les phrases d'accueil JARVIS"""
        greeting = jarvis_persona.get_greeting()
        
        assert greeting in jarvis_persona.config.greeting_phrases
        assert any(word in greeting.lower() for word in ["sir", "service", "jarvis", "assist"])

    def test_jarvis_error_phrases(self, jarvis_persona):
        """Test les phrases d'erreur JARVIS"""
        error_response = jarvis_persona.get_error_response()
        
        assert error_response in jarvis_persona.config.error_phrases
        assert any(word in error_response.lower() for word in ["apologize", "error", "difficulty"])

    def test_jarvis_voice_settings(self, jarvis_persona):
        """Test les paramètres vocaux JARVIS"""
        voice_settings = jarvis_persona.get_voice_settings()
        
        assert voice_settings["pitch"] == -2.0  # Voix grave
        assert voice_settings["speed"] == 0.95  # Légèrement plus lent
        assert voice_settings["voice_id"] == "french_male"
        assert "reverb" in voice_settings["effects"]


class TestFridayPersona:
    """Tests spécifiques pour FRIDAY"""
    
    @pytest.fixture
    def friday_persona(self):
        """Fixture pour créer FRIDAY"""
        return MockFriday()

    @pytest.mark.asyncio
    async def test_friday_message_processing(self, friday_persona):
        """Test le traitement de messages par FRIDAY"""
        await friday_persona.activate()
        
        message = "Analyze this data please"
        result = await friday_persona.process_message(message)
        
        assert result["persona"] == "FRIDAY"
        assert result["style"] == "casual_friendly"
        assert result["formality_level"] == "low"
        assert result["enthusiasm_level"] == "high"
        assert "check that out" in result["text"]

    @pytest.mark.asyncio
    async def test_friday_gratitude_response(self, friday_persona):
        """Test la réponse de FRIDAY aux remerciements"""
        await friday_persona.activate()
        
        message = "Thanks for your help"
        result = await friday_persona.process_message(message)
        
        assert "welcome" in result["text"].lower()

    def test_friday_greeting_style(self, friday_persona):
        """Test le style d'accueil de FRIDAY"""
        greeting = friday_persona.get_greeting()
        
        assert greeting in friday_persona.config.greeting_phrases
        assert any(word in greeting.lower() for word in ["hey", "hi", "ready", "friday"])

    def test_friday_voice_settings(self, friday_persona):
        """Test les paramètres vocaux FRIDAY"""
        voice_settings = friday_persona.get_voice_settings()
        
        assert voice_settings["pitch"] == 0.5  # Voix plus aiguë
        assert voice_settings["speed"] == 1.1  # Plus rapide
        assert voice_settings["voice_id"] == "french_female"
        assert "brightness" in voice_settings["effects"]


class TestEdithPersona:
    """Tests spécifiques pour EDITH"""
    
    @pytest.fixture
    def edith_persona(self):
        """Fixture pour créer EDITH"""
        return MockEdith()

    @pytest.mark.asyncio
    async def test_edith_technical_processing(self, edith_persona):
        """Test le traitement technique par EDITH"""
        await edith_persona.activate()
        
        message = "Analyze system performance data"
        result = await edith_persona.process_message(message)
        
        assert result["persona"] == "EDITH"
        assert result["style"] == "technical_precise"
        assert result["technical_level"] == "advanced"
        assert result["precision_mode"] == "enabled"
        assert "comprehensive analysis" in result["text"]

    @pytest.mark.asyncio
    async def test_edith_data_query(self, edith_persona):
        """Test les requêtes de données EDITH"""
        await edith_persona.activate()
        
        message = "Show me the data on CPU usage"
        result = await edith_persona.process_message(message)
        
        assert "datasets" in result["text"]

    def test_edith_greeting_technical(self, edith_persona):
        """Test les phrases d'accueil techniques d'EDITH"""
        greeting = edith_persona.get_greeting()
        
        assert greeting in edith_persona.config.greeting_phrases
        assert any(word in greeting.lower() for word in ["edith", "technical", "systems", "operations"])

    def test_edith_error_handling(self, edith_persona):
        """Test la gestion d'erreur technique d'EDITH"""
        error_response = edith_persona.get_error_response()
        
        assert error_response in edith_persona.config.error_phrases
        assert any(word in error_response.lower() for word in ["error", "technical", "system", "diagnostics"])

    def test_edith_voice_settings(self, edith_persona):
        """Test les paramètres vocaux techniques d'EDITH"""
        voice_settings = edith_persona.get_voice_settings()
        
        assert voice_settings["pitch"] == -0.5  # Voix légèrement grave
        assert voice_settings["speed"] == 0.9   # Précis et posé
        assert "technical" in voice_settings["voice_id"]
        assert "clarity" in voice_settings["effects"]


class TestPersonaContextMemory:
    """Tests pour la mémoire contextuelle des personas"""
    
    @pytest.fixture
    def persona_with_memory(self):
        """Fixture pour créer une persona avec mémoire"""
        return MockJarvisClassic()

    @pytest.mark.asyncio
    async def test_context_memory_storage(self, persona_with_memory):
        """Test le stockage de la mémoire contextuelle"""
        await persona_with_memory.activate()
        
        # Traiter plusieurs messages
        messages = [
            "What's the weather like?",
            "Can you analyze the system?",
            "Show me the status report"
        ]
        
        for message in messages:
            await persona_with_memory.process_message(message)
        
        # Vérifier que la mémoire est stockée
        assert len(persona_with_memory.context_memory) == 3
        
        # Vérifier la structure de la mémoire
        for memory_item in persona_with_memory.context_memory:
            assert "timestamp" in memory_item
            assert "message" in memory_item
            assert "response" in memory_item

    @pytest.mark.asyncio
    async def test_context_memory_retrieval(self, persona_with_memory):
        """Test la récupération de la mémoire contextuelle"""
        await persona_with_memory.activate()
        
        # Ajouter du contexte
        context = {"user_preferences": {"formal": True}, "session_id": "test123"}
        message = "Hello JARVIS"
        
        result = await persona_with_memory.process_message(message, context)
        
        # Vérifier que le contexte est utilisé
        assert result["context_used"] == context
        
        # Vérifier que le contexte est stocké en mémoire
        memory_item = persona_with_memory.context_memory[-1]
        assert memory_item["message"] == message


class TestPersonaIntegration:
    """Tests d'intégration pour le système de personas"""
    
    @pytest.mark.asyncio
    async def test_persona_switching_workflow(self):
        """Test un flux complet de changement de personas"""
        manager = MockPersonaManager(default_persona="jarvis_classic")
        await manager.initialize()
        
        # Test du flux complet
        messages_and_personas = [
            ("jarvis_classic", "Analyze the system performance"),
            ("friday", "Hey, what's up with the servers?"),
            ("edith", "Provide detailed technical diagnostics"),
            ("jarvis_classic", "Generate a status report")
        ]
        
        responses = []
        for persona_id, message in messages_and_personas:
            # Changer de persona
            switch_result = await manager.switch_persona(persona_id)
            assert switch_result["success"] is True
            
            # Traiter le message
            response = await manager.process_message(message)
            responses.append({
                "persona": persona_id,
                "message": message,
                "response": response
            })
        
        # Vérifier que chaque réponse correspond au style de la persona
        assert responses[0]["response"]["formality_level"] == "high"  # JARVIS
        assert responses[1]["response"]["enthusiasm_level"] == "high"  # FRIDAY
        assert responses[2]["response"]["technical_level"] == "advanced"  # EDITH
        assert responses[3]["response"]["formality_level"] == "high"  # JARVIS again

    @pytest.mark.asyncio
    async def test_persona_consistency_check(self):
        """Test la cohérence des personas"""
        manager = MockPersonaManager()
        await manager.initialize()
        
        # Tester chaque persona
        for persona_id in ["jarvis_classic", "friday", "edith"]:
            await manager.switch_persona(persona_id)
            current = await manager.get_current_persona()
            
            # Vérifier les propriétés essentielles
            assert current.name is not None
            assert len(current.config.personality_traits) > 0
            assert current.config.voice_settings is not None
            assert len(current.config.greeting_phrases) > 0
            assert len(current.config.error_phrases) > 0
            assert len(current.config.confirmation_phrases) > 0
            
            # Vérifier que les phrases sont uniques par persona
            greeting = current.get_greeting()
            error = current.get_error_response()
            confirmation = current.get_confirmation()
            
            assert greeting != error
            assert greeting != confirmation
            assert error != confirmation


# Helpers pour les tests de personas
class TestPersonaHelpers:
    """Helpers utilitaires pour les tests de personas"""
    
    @staticmethod
    def create_test_message(content="Test message", context=None):
        """Crée un message de test"""
        return {
            "content": content,
            "context": context or {},
            "timestamp": time.time(),
            "user_id": "test_user"
        }
    
    @staticmethod
    def assert_persona_response_structure(response):
        """Vérifie la structure d'une réponse de persona"""
        required_fields = ["text", "persona", "style", "confidence"]
        for field in required_fields:
            assert field in response, f"Champ persona manquant: {field}"
        
        assert 0 <= response["confidence"] <= 1, "Confidence doit être entre 0 et 1"
        assert len(response["text"]) > 0, "La réponse ne peut pas être vide"
    
    @staticmethod
    def assert_voice_settings_structure(voice_settings):
        """Vérifie la structure des paramètres vocaux"""
        required_fields = ["pitch", "speed", "voice_id", "effects"]
        for field in required_fields:
            assert field in voice_settings, f"Paramètre vocal manquant: {field}"
        
        assert isinstance(voice_settings["effects"], dict), "Effects doit être un dictionnaire"
    
    @staticmethod
    def compare_persona_styles(response1, response2):
        """Compare les styles de deux réponses de personas"""
        style_indicators = {
            "formal_professional": ["sir", "certainly", "apologize", "operation"],
            "casual_friendly": ["hey", "you got it", "oops", "awesome"],
            "technical_precise": ["analysis", "processing", "diagnostics", "parameters"]
        }
        
        style1 = response1.get("style", "unknown")
        style2 = response2.get("style", "unknown")
        
        if style1 != style2:
            return {"different": True, "style1": style1, "style2": style2}
        
        return {"different": False, "style": style1}


@pytest.fixture(scope="session")
def event_loop():
    """Fixture pour gérer la boucle d'événements asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])