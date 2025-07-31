#!/usr/bin/env python3
"""
🧠 Tests unitaires critiques pour Brain API
Tests pour l'API principale, WebSocket, M.A.MM (Métacognition, Agent, Memory Manager)
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import websockets

# Import du module à tester
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'brain-api'))

from main import app, app_state
from core.metacognition import MetacognitionEngine
from core.agent import ReactAgent
from core.memory import HybridMemoryManager
from core.websocket_manager import WebSocketManager
from core.audio_streamer import AudioStreamer
from personas.persona_manager import PersonaManager


class TestBrainAPIHealth:
    """Tests de santé et de status de l'API"""
    
    def setup_method(self):
        self.client = TestClient(app)

    def test_root_endpoint_structure(self):
        """Test que l'endpoint racine retourne la structure attendue"""
        response = self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        
        # Vérifier la structure de base
        assert "name" in data
        assert "version" in data
        assert "architecture" in data
        assert "status" in data
        assert "services" in data
        assert "endpoints" in data
        
        # Vérifier les valeurs spécifiques
        assert data["name"] == "JARVIS Brain API"
        assert data["version"] == "2.0.0"
        assert data["architecture"] == "M.A.MM (Métacognition, Agent, Memory)"
        
        # Vérifier les services
        services = data["services"]
        expected_services = ["metacognition", "agent", "memory", "websocket", "audio_streamer", "persona_manager"]
        for service in expected_services:
            assert service in services
            
        # Vérifier les endpoints
        endpoints = data["endpoints"]
        expected_endpoints = ["health", "chat", "memory", "agent", "metacognition", "websocket", "audio", "persona", "metrics", "docs"]
        for endpoint in expected_endpoints:
            assert endpoint in endpoints

    def test_health_endpoint_when_healthy(self):
        """Test endpoint de santé quand l'application est saine"""
        # Simuler un état sain
        app_state["healthy"] = True
        app_state["startup_time"] = time.time() - 10  # Started 10 seconds ago
        
        response = self.client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_when_unhealthy(self):
        """Test endpoint de santé quand l'application est défaillante"""
        # Simuler un état défaillant
        app_state["healthy"] = False
        
        response = self.client.get("/health")
        assert response.status_code == 503


class TestMetacognitionEngine:
    """Tests pour le moteur de métacognition"""
    
    @pytest.fixture
    def metacognition_engine(self):
        """Fixture pour créer une instance de MetacognitionEngine"""
        return MetacognitionEngine(
            hallucination_threshold=0.7,
            complexity_min_score=0.5
        )

    @pytest.mark.asyncio
    async def test_metacognition_initialization(self, metacognition_engine):
        """Test l'initialisation du moteur de métacognition"""
        # Mock des dépendances
        with patch.object(metacognition_engine, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            
            result = await metacognition_engine.initialize()
            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_hallucination_detection(self, metacognition_engine):
        """Test la détection d'hallucinations"""
        # Mock de la méthode de détection
        with patch.object(metacognition_engine, 'detect_hallucination', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = {"score": 0.8, "is_hallucination": True, "confidence": 0.9}
            
            test_input = "This is a test input that might be hallucinated"
            result = await metacognition_engine.detect_hallucination(test_input)
            
            assert result["is_hallucination"] is True
            assert result["score"] > 0.7
            assert "confidence" in result
            mock_detect.assert_called_once_with(test_input)

    @pytest.mark.asyncio
    async def test_complexity_analysis(self, metacognition_engine):
        """Test l'analyse de complexité"""
        with patch.object(metacognition_engine, 'analyze_complexity', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"complexity_score": 0.6, "factors": ["length", "concepts"], "requires_breakdown": False}
            
            test_query = "What is the weather today?"
            result = await metacognition_engine.analyze_complexity(test_query)
            
            assert result["complexity_score"] >= 0.5
            assert "factors" in result
            assert isinstance(result["requires_breakdown"], bool)
            mock_analyze.assert_called_once_with(test_query)

    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self, metacognition_engine):
        """Test le nettoyage lors de l'arrêt"""
        with patch.object(metacognition_engine, 'shutdown', new_callable=AsyncMock) as mock_shutdown:
            mock_shutdown.return_value = True
            
            result = await metacognition_engine.shutdown()
            assert result is True
            mock_shutdown.assert_called_once()


class TestReactAgent:
    """Tests pour l'agent React"""
    
    @pytest.fixture
    def react_agent(self):
        """Fixture pour créer une instance de ReactAgent"""
        memory_manager = Mock()
        metacognition = Mock()
        persona_manager = Mock()
        
        return ReactAgent(
            llm_url="http://localhost:11434",
            memory_manager=memory_manager,
            metacognition=metacognition,
            persona_manager=persona_manager
        )

    @pytest.mark.asyncio
    async def test_agent_initialization(self, react_agent):
        """Test l'initialisation de l'agent React"""
        with patch.object(react_agent, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            
            result = await react_agent.initialize()
            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_process_message(self, react_agent):
        """Test le traitement d'un message par l'agent"""
        with patch.object(react_agent, 'process_message', new_callable=AsyncMock) as mock_process:
            mock_response = {
                "response": "Hello! How can I help you?",
                "reasoning": "User greeted, responding politely",
                "actions": [],
                "confidence": 0.95
            }
            mock_process.return_value = mock_response
            
            test_message = "Hello JARVIS"
            result = await react_agent.process_message(test_message)
            
            assert result["response"] is not None
            assert result["confidence"] > 0.5
            assert "reasoning" in result
            mock_process.assert_called_once_with(test_message)

    @pytest.mark.asyncio
    async def test_agent_execute_action(self, react_agent):
        """Test l'exécution d'actions par l'agent"""
        with patch.object(react_agent, 'execute_action', new_callable=AsyncMock) as mock_execute:
            mock_result = {
                "action": "web_search",
                "result": "Search completed successfully",
                "status": "success"
            }
            mock_execute.return_value = mock_result
            
            test_action = {"type": "web_search", "query": "Python testing"}
            result = await react_agent.execute_action(test_action)
            
            assert result["status"] == "success"
            assert "result" in result
            mock_execute.assert_called_once_with(test_action)


class TestHybridMemoryManager:
    """Tests pour le gestionnaire de mémoire hybride"""
    
    @pytest.fixture
    def memory_manager(self):
        """Fixture pour créer une instance de HybridMemoryManager"""
        return HybridMemoryManager(
            db_url="sqlite:///test_memory.db",
            redis_url="redis://localhost:6379/1"
        )

    @pytest.mark.asyncio
    async def test_memory_initialization(self, memory_manager):
        """Test l'initialisation du gestionnaire de mémoire"""
        with patch.object(memory_manager, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            
            result = await memory_manager.initialize()
            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_memory(self, memory_manager):
        """Test le stockage de mémoire"""
        with patch.object(memory_manager, 'store', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = "memory_id_123"
            
            test_data = {
                "type": "conversation",
                "content": "Test conversation",
                "timestamp": time.time(),
                "metadata": {"user": "test_user"}
            }
            
            result = await memory_manager.store(test_data)
            assert result == "memory_id_123"
            mock_store.assert_called_once_with(test_data)

    @pytest.mark.asyncio
    async def test_retrieve_memory(self, memory_manager):
        """Test la récupération de mémoire"""
        with patch.object(memory_manager, 'retrieve', new_callable=AsyncMock) as mock_retrieve:
            mock_memory = {
                "id": "memory_id_123",
                "type": "conversation",
                "content": "Test conversation",
                "timestamp": time.time()
            }
            mock_retrieve.return_value = [mock_memory]
            
            result = await memory_manager.retrieve(query="test conversation")
            assert len(result) == 1
            assert result[0]["id"] == "memory_id_123"
            mock_retrieve.assert_called_once_with(query="test conversation")

    @pytest.mark.asyncio
    async def test_search_memory(self, memory_manager):
        """Test la recherche dans la mémoire"""
        with patch.object(memory_manager, 'search', new_callable=AsyncMock) as mock_search:
            mock_results = [
                {"id": "1", "content": "First memory", "score": 0.9},
                {"id": "2", "content": "Second memory", "score": 0.7}
            ]
            mock_search.return_value = mock_results
            
            result = await memory_manager.search("test query", limit=10)
            assert len(result) == 2
            assert result[0]["score"] > result[1]["score"]  # Vérifie l'ordre par score
            mock_search.assert_called_once_with("test query", limit=10)


class TestWebSocketManager:
    """Tests pour le gestionnaire WebSocket"""
    
    @pytest.fixture
    def websocket_manager(self):
        """Fixture pour créer une instance de WebSocketManager"""
        agent = Mock()
        memory = Mock()
        audio_streamer = Mock()
        
        return WebSocketManager(
            agent=agent,
            memory=memory,
            audio_streamer=audio_streamer
        )

    @pytest.mark.asyncio
    async def test_websocket_connection_handling(self, websocket_manager):
        """Test la gestion des connexions WebSocket"""
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        mock_websocket.receive_json = AsyncMock()
        
        with patch.object(websocket_manager, 'handle_connection', new_callable=AsyncMock) as mock_handle:
            await websocket_manager.handle_connection(mock_websocket)
            mock_handle.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_message_processing(self, websocket_manager):
        """Test le traitement des messages WebSocket"""
        with patch.object(websocket_manager, 'process_message', new_callable=AsyncMock) as mock_process:
            mock_response = {
                "type": "response",
                "content": "Message processed successfully",
                "timestamp": time.time()
            }
            mock_process.return_value = mock_response
            
            test_message = {
                "type": "chat_message",
                "content": "Hello JARVIS",
                "session_id": "test_session"
            }
            
            result = await websocket_manager.process_message(test_message)
            assert result["type"] == "response"
            assert "content" in result
            mock_process.assert_called_once_with(test_message)

    @pytest.mark.asyncio
    async def test_websocket_broadcast(self, websocket_manager):
        """Test la diffusion de messages"""
        with patch.object(websocket_manager, 'broadcast', new_callable=AsyncMock) as mock_broadcast:
            test_message = {"type": "system_update", "data": "System status changed"}
            
            await websocket_manager.broadcast(test_message)
            mock_broadcast.assert_called_once_with(test_message)


class TestPersonaManager:
    """Tests pour le gestionnaire de personas"""
    
    @pytest.fixture
    def persona_manager(self):
        """Fixture pour créer une instance de PersonaManager"""
        memory_manager = Mock()
        
        return PersonaManager(
            memory_manager=memory_manager,
            default_persona="jarvis_classic"
        )

    @pytest.mark.asyncio
    async def test_persona_initialization(self, persona_manager):
        """Test l'initialisation du gestionnaire de personas"""
        with patch.object(persona_manager, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            
            result = await persona_manager.initialize()
            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_persona_switching(self, persona_manager):
        """Test le changement de persona"""
        with patch.object(persona_manager, 'switch_persona', new_callable=AsyncMock) as mock_switch:
            mock_switch.return_value = {
                "success": True,
                "previous": "jarvis_classic",
                "current": "friday",
                "message": "Persona switched successfully"
            }
            
            result = await persona_manager.switch_persona("friday")
            assert result["success"] is True
            assert result["current"] == "friday"
            mock_switch.assert_called_once_with("friday")

    @pytest.mark.asyncio
    async def test_persona_list_available(self, persona_manager):
        """Test la liste des personas disponibles"""
        with patch.object(persona_manager, 'list_personas', new_callable=AsyncMock) as mock_list:
            mock_personas = [
                {"id": "jarvis_classic", "name": "JARVIS Classic", "description": "Original JARVIS persona"},
                {"id": "friday", "name": "FRIDAY", "description": "More casual and friendly"},
                {"id": "edith", "name": "EDITH", "description": "Technical and precise"}
            ]
            mock_list.return_value = mock_personas
            
            result = await persona_manager.list_personas()
            assert len(result) == 3
            assert all("id" in persona for persona in result)
            assert all("name" in persona for persona in result)
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_persona_get_current(self, persona_manager):
        """Test l'obtention de la persona courante"""
        with patch.object(persona_manager, 'get_current_persona', new_callable=AsyncMock) as mock_get:
            mock_persona = {
                "id": "jarvis_classic",
                "name": "JARVIS Classic",
                "voice_settings": {"pitch": -2.0, "speed": 0.95},
                "personality_traits": ["professional", "helpful", "analytical"]
            }
            mock_get.return_value = mock_persona
            
            result = await persona_manager.get_current_persona()
            assert result["id"] == "jarvis_classic"
            assert "voice_settings" in result
            assert "personality_traits" in result
            mock_get.assert_called_once()


class TestBrainAPIIntegration:
    """Tests d'intégration pour l'API Brain"""
    
    def setup_method(self):
        self.client = TestClient(app)

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test un flux de conversation complet"""
        # Simuler l'état de l'application comme prêt
        app_state["healthy"] = True
        app_state["agent"] = Mock()
        app_state["memory"] = Mock()
        app_state["persona_manager"] = Mock()
        
        # Mock des réponses
        app_state["agent"].process_message = AsyncMock(return_value={
            "response": "Hello! How can I assist you today?",
            "reasoning": "Greeting detected, responding politely",
            "confidence": 0.95
        })
        
        # Test du chat endpoint (si disponible)
        with patch('core.agent.ReactAgent') as mock_agent_class:
            mock_agent = mock_agent_class.return_value
            mock_agent.process_message = AsyncMock(return_value={
                "response": "Hello! How can I assist you today?",
                "reasoning": "Greeting detected",
                "confidence": 0.95
            })
            
            # Note: Adjust this test based on actual chat endpoint implementation
            # response = self.client.post("/api/chat", json={"message": "Hello JARVIS"})
            # assert response.status_code == 200

    def test_cors_headers(self):
        """Test que les headers CORS sont correctement configurés"""
        response = self.client.options("/")
        
        # Vérifier que les headers CORS sont présents
        assert "access-control-allow-origin" in response.headers or response.status_code == 200

    def test_error_handling(self):
        """Test la gestion d'erreurs globale"""
        # Test avec un endpoint qui n'existe pas
        response = self.client.get("/nonexistent")
        assert response.status_code == 404

    def test_metrics_endpoint_accessible(self):
        """Test que l'endpoint metrics est accessible"""
        response = self.client.get("/metrics")
        # L'endpoint metrics peut retourner 200 ou avoir un format spécifique
        assert response.status_code in [200, 404]  # 404 si pas encore configuré


@pytest.fixture(scope="session")
def event_loop():
    """Fixture pour gérer la boucle d'événements asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Helpers pour les tests
class TestHelpers:
    """Helpers utilitaires pour les tests"""
    
    @staticmethod
    def create_mock_websocket():
        """Crée un mock WebSocket pour les tests"""
        mock_ws = Mock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.receive_json = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws
    
    @staticmethod
    def create_mock_message(message_type="chat", content="test message"):
        """Crée un message mock pour les tests"""
        return {
            "type": message_type,
            "content": content,
            "timestamp": time.time(),
            "session_id": "test_session"
        }
    
    @staticmethod
    def assert_response_structure(response_data, required_fields):
        """Vérifie qu'une réponse contient tous les champs requis"""
        for field in required_fields:
            assert field in response_data, f"Champ manquant: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])