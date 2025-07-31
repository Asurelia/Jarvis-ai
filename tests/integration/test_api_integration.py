"""
🌐 Tests d'intégration API end-to-end pour JARVIS AI
Tests complets des APIs avec vrais services
"""

import pytest
import asyncio
import time
import json
import uuid
from typing import Dict, List, Optional, Any
import requests
import httpx
from unittest.mock import patch, MagicMock

# Configuration des endpoints
API_BASE_URL = "http://localhost:8081"
API_ENDPOINTS = {
    'health': '/health',
    'chat': '/api/chat',
    'memory': '/api/memory',
    'persona': '/api/persona',
    'audio': '/api/audio',
    'system': '/api/system',
    'cache': '/api/cache'
}

class APITestClient:
    """Client de test pour les APIs JARVIS"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'JARVIS-Integration-Tests/1.0'
        })
        self.auth_token = None
    
    def authenticate(self, credentials: Optional[Dict] = None) -> bool:
        """Authentification pour les tests"""
        if not credentials:
            credentials = {
                'username': 'test_user',
                'password': 'test_password'
            }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json=credentials,
                timeout=10
            )
            if response.status_code == 200:
                self.auth_token = response.json().get('token')
                self.session.headers['Authorization'] = f'Bearer {self.auth_token}'
                return True
        except Exception as e:
            print(f"Authentication failed: {e}")
        
        return False
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET request with error handling"""
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url, timeout=kwargs.get('timeout', 10), **kwargs)
    
    def post(self, endpoint: str, data: Any = None, **kwargs) -> requests.Response:
        """POST request with error handling"""
        url = f"{self.base_url}{endpoint}"
        if data:
            kwargs['json'] = data
        return self.session.post(url, timeout=kwargs.get('timeout', 10), **kwargs)
    
    def put(self, endpoint: str, data: Any = None, **kwargs) -> requests.Response:
        """PUT request with error handling"""
        url = f"{self.base_url}{endpoint}"
        if data:
            kwargs['json'] = data
        return self.session.put(url, timeout=kwargs.get('timeout', 10), **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE request with error handling"""
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(url, timeout=kwargs.get('timeout', 10), **kwargs)

@pytest.fixture(scope="session")
def api_client():
    """Fixture pour le client API"""
    client = APITestClient()
    # Optionnel: authentifier si nécessaire
    # client.authenticate()
    yield client

@pytest.fixture(scope="function")
def test_conversation_data():
    """Données de test pour les conversations"""
    return {
        "user_input": "Hello JARVIS, this is a test message",
        "context": {
            "session_id": str(uuid.uuid4()),
            "user_id": "test_user",
            "timestamp": time.time(),
            "test_mode": True
        },
        "persona": "jarvis_classic",
        "metadata": {
            "source": "integration_test",
            "priority": "normal"
        }
    }

@pytest.fixture(scope="function")
def test_memory_data():
    """Données de test pour la mémoire"""
    return {
        "content": "This is a test memory entry for integration testing",
        "type": "conversation_memory",
        "metadata": {
            "test": True,
            "created_by": "integration_test",
            "timestamp": time.time()
        },
        "tags": ["test", "integration", "memory"],
        "importance": 0.7
    }

class TestAPIHealth:
    """Tests de santé des APIs"""
    
    def test_health_endpoint_responds(self, api_client):
        """Test que l'endpoint de santé répond"""
        response = api_client.get('/health')
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        health_data = response.json()
        assert 'status' in health_data
        assert health_data['status'] == 'healthy'
    
    def test_health_includes_dependencies(self, api_client):
        """Test que le health check inclut les dépendances"""
        response = api_client.get('/health')
        assert response.status_code == 200
        
        health_data = response.json()
        required_deps = ['redis', 'database', 'ollama']
        
        for dep in required_deps:
            assert dep in health_data, f"Dependency {dep} missing from health check"
            assert 'status' in health_data[dep], f"Status missing for dependency {dep}"
    
    def test_health_endpoint_performance(self, api_client):
        """Test performance de l'endpoint de santé"""
        start_time = time.time()
        response = api_client.get('/health')
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 2.0, f"Health check too slow: {response_time:.2f}s"

class TestChatAPI:
    """Tests de l'API de chat"""
    
    def test_send_message_basic(self, api_client, test_conversation_data):
        """Test envoi de message basique"""
        response = api_client.post('/api/chat/message', test_conversation_data)
        
        assert response.status_code == 200, f"Chat API failed: {response.text}"
        
        result = response.json()
        assert 'response' in result
        assert 'conversation_id' in result
        assert 'timestamp' in result
        assert len(result['response']) > 0
    
    def test_conversation_context_maintained(self, api_client, test_conversation_data):
        """Test que le contexte de conversation est maintenu"""
        # Premier message
        response1 = api_client.post('/api/chat/message', test_conversation_data)
        assert response1.status_code == 200
        
        conversation_id = response1.json()['conversation_id']
        
        # Deuxième message dans la même conversation
        follow_up_data = test_conversation_data.copy()
        follow_up_data['user_input'] = "Do you remember what I just said?"
        follow_up_data['conversation_id'] = conversation_id
        
        response2 = api_client.post('/api/chat/message', follow_up_data)
        assert response2.status_code == 200
        
        result2 = response2.json()
        assert result2['conversation_id'] == conversation_id
    
    def test_persona_switching(self, api_client, test_conversation_data):
        """Test changement de persona"""
        personas_to_test = ['jarvis_classic', 'friday', 'edith']
        
        for persona in personas_to_test:
            test_data = test_conversation_data.copy()
            test_data['persona'] = persona
            test_data['user_input'] = f"Hello, I'm testing the {persona} persona"
            
            response = api_client.post('/api/chat/message', test_data)
            assert response.status_code == 200, f"Failed with persona {persona}"
            
            result = response.json()
            assert 'response' in result
            # Vérifier que la persona est appliquée
            assert 'persona' in result
            assert result['persona'] == persona
    
    def test_conversation_history_retrieval(self, api_client, test_conversation_data):
        """Test récupération de l'historique de conversation"""
        # Créer une conversation
        response = api_client.post('/api/chat/message', test_conversation_data)
        assert response.status_code == 200
        
        conversation_id = response.json()['conversation_id']
        
        # Récupérer l'historique
        history_response = api_client.get(f'/api/chat/conversation/{conversation_id}')
        assert history_response.status_code == 200
        
        history = history_response.json()
        assert 'messages' in history
        assert len(history['messages']) > 0
        assert history['conversation_id'] == conversation_id
    
    @pytest.mark.asyncio
    async def test_concurrent_conversations(self, api_client, test_conversation_data):
        """Test conversations simultanées"""
        async def send_message(session_id: str):
            data = test_conversation_data.copy()
            data['context']['session_id'] = session_id
            data['user_input'] = f"Message from session {session_id}"
            
            response = api_client.post('/api/chat/message', data)
            return response
        
        # Lancer plusieurs conversations en parallèle
        tasks = []
        session_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        for session_id in session_ids:
            tasks.append(asyncio.create_task(asyncio.to_thread(send_message, session_id)))
        
        responses = await asyncio.gather(*tasks)
        
        # Vérifier que toutes les réponses sont valides
        conversation_ids = set()
        for response in responses:
            assert response.status_code == 200
            result = response.json()
            conversation_ids.add(result['conversation_id'])
        
        # Chaque conversation devrait avoir un ID unique
        assert len(conversation_ids) == len(session_ids)

class TestMemoryAPI:
    """Tests de l'API de mémoire"""
    
    def test_save_memory(self, api_client, test_memory_data):
        """Test sauvegarde de mémoire"""
        response = api_client.post('/api/memory/save', test_memory_data)
        
        assert response.status_code == 200, f"Memory save failed: {response.text}"
        
        result = response.json()
        assert 'id' in result
        assert 'timestamp' in result
        assert result['status'] == 'saved'
    
    def test_retrieve_memory(self, api_client, test_memory_data):
        """Test récupération de mémoire"""
        # Sauvegarder d'abord
        save_response = api_client.post('/api/memory/save', test_memory_data)
        assert save_response.status_code == 200
        
        memory_id = save_response.json()['id']
        
        # Récupérer
        retrieve_response = api_client.get(f'/api/memory/get/{memory_id}')
        assert retrieve_response.status_code == 200
        
        retrieved_data = retrieve_response.json()
        assert retrieved_data['content'] == test_memory_data['content']
        assert retrieved_data['type'] == test_memory_data['type']
        assert retrieved_data['id'] == memory_id
    
    def test_search_memory(self, api_client, test_memory_data):
        """Test recherche dans la mémoire"""
        # Sauvegarder plusieurs mémoires de test
        test_memories = []
        for i in range(3):
            memory_data = test_memory_data.copy()
            memory_data['content'] = f"Test memory content {i} for searching"
            memory_data['tags'] = [f"test_{i}", "search_test"]
            
            response = api_client.post('/api/memory/save', memory_data)
            assert response.status_code == 200
            test_memories.append(response.json()['id'])
        
        # Rechercher
        search_query = {
            'query': 'search_test',
            'type': 'conversation_memory',
            'limit': 10
        }
        
        search_response = api_client.post('/api/memory/search', search_query)
        assert search_response.status_code == 200
        
        results = search_response.json()
        assert 'results' in results
        assert len(results['results']) >= 3
    
    def test_memory_update(self, api_client, test_memory_data):
        """Test mise à jour de mémoire"""
        # Sauvegarder d'abord
        save_response = api_client.post('/api/memory/save', test_memory_data)
        assert save_response.status_code == 200
        
        memory_id = save_response.json()['id']
        
        # Mettre à jour
        updated_data = test_memory_data.copy()
        updated_data['content'] = "Updated test memory content"
        updated_data['importance'] = 0.9
        
        update_response = api_client.put(f'/api/memory/update/{memory_id}', updated_data)
        assert update_response.status_code == 200
        
        # Vérifier la mise à jour
        retrieve_response = api_client.get(f'/api/memory/get/{memory_id}')
        assert retrieve_response.status_code == 200
        
        retrieved_data = retrieve_response.json()
        assert retrieved_data['content'] == updated_data['content']
        assert retrieved_data['importance'] == updated_data['importance']

class TestPersonaAPI:
    """Tests de l'API des personas"""
    
    def test_list_personas(self, api_client):
        """Test listage des personas disponibles"""
        response = api_client.get('/api/persona/list')
        
        assert response.status_code == 200, f"Persona list failed: {response.text}"
        
        personas = response.json()
        assert 'personas' in personas
        assert len(personas['personas']) > 0
        
        # Vérifier que les personas principales sont présentes
        persona_names = [p['name'] for p in personas['personas']]
        expected_personas = ['jarvis_classic', 'friday', 'edith']
        
        for expected in expected_personas:
            assert expected in persona_names, f"Persona {expected} not found"
    
    def test_get_persona_details(self, api_client):
        """Test récupération des détails d'une persona"""
        persona_name = 'jarvis_classic'
        response = api_client.get(f'/api/persona/get/{persona_name}')
        
        assert response.status_code == 200, f"Persona details failed: {response.text}"
        
        persona_data = response.json()
        assert 'name' in persona_data
        assert 'description' in persona_data
        assert 'personality_traits' in persona_data
        assert persona_data['name'] == persona_name
    
    def test_persona_activation(self, api_client):
        """Test activation d'une persona"""
        persona_name = 'friday'
        activation_data = {
            'persona': persona_name,
            'session_id': str(uuid.uuid4())
        }
        
        response = api_client.post('/api/persona/activate', activation_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result['status'] == 'activated'
        assert result['persona'] == persona_name

class TestAudioAPI:
    """Tests de l'API audio (TTS/STT)"""
    
    def test_text_to_speech(self, api_client):
        """Test synthèse vocale"""
        tts_data = {
            'text': 'Hello, this is a test of text to speech integration',
            'voice': 'jarvis_voice',
            'speed': 1.0,
            'format': 'wav'
        }
        
        response = api_client.post('/api/audio/tts', tts_data)
        assert response.status_code == 200
        
        # Vérifier que c'est bien un fichier audio
        assert response.headers.get('content-type', '').startswith('audio/')
        assert len(response.content) > 0
    
    def test_speech_to_text_mock(self, api_client):
        """Test reconnaissance vocale (avec mock)"""
        # Simuler un fichier audio
        audio_data = {
            'audio_format': 'wav',
            'sample_rate': 16000,
            'language': 'en',
            'mock_transcript': 'This is a mock transcription for testing'
        }
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'transcript': 'This is a mock transcription for testing',
                'confidence': 0.95,
                'processing_time': 0.5
            }
            mock_post.return_value = mock_response
            
            response = api_client.post('/api/audio/stt', audio_data)
            assert response.status_code == 200
            
            result = response.json()
            assert 'transcript' in result
            assert 'confidence' in result

class TestSystemAPI:
    """Tests de l'API système"""
    
    def test_system_stats(self, api_client):
        """Test statistiques système"""
        response = api_client.get('/api/system/stats')
        
        assert response.status_code == 200, f"System stats failed: {response.text}"
        
        stats = response.json()
        expected_keys = ['cpu_usage', 'memory_usage', 'disk_usage', 'uptime']
        
        for key in expected_keys:
            assert key in stats, f"Missing stat: {key}"
    
    def test_system_health_detailed(self, api_client):
        """Test santé système détaillée"""
        response = api_client.get('/api/system/health/detailed')
        
        assert response.status_code == 200
        
        health = response.json()
        assert 'services' in health
        assert 'resources' in health
        assert 'performance' in health

class TestCacheAPI:
    """Tests de l'API de cache"""
    
    def test_cache_operations(self, api_client):
        """Test opérations de cache"""
        cache_key = f"test_key_{uuid.uuid4()}"
        cache_value = {
            'data': 'test cache data',
            'timestamp': time.time(),
            'metadata': {'test': True}
        }
        
        # Set cache
        set_response = api_client.post('/api/cache/set', {
            'key': cache_key,
            'value': cache_value,
            'ttl': 300  # 5 minutes
        })
        assert set_response.status_code == 200
        
        # Get cache
        get_response = api_client.get(f'/api/cache/get/{cache_key}')
        assert get_response.status_code == 200
        
        retrieved_data = get_response.json()
        assert retrieved_data['value']['data'] == cache_value['data']
        
        # Delete cache
        delete_response = api_client.delete(f'/api/cache/delete/{cache_key}')
        assert delete_response.status_code == 200
        
        # Verify deletion
        verify_response = api_client.get(f'/api/cache/get/{cache_key}')
        assert verify_response.status_code == 404

@pytest.mark.slow
class TestAPIPerformance:
    """Tests de performance des APIs"""
    
    def test_api_response_times(self, api_client):
        """Test temps de réponse des APIs"""
        endpoints_to_test = [
            ('/health', 1.0),
            ('/api/persona/list', 2.0),
            ('/api/system/stats', 3.0)
        ]
        
        for endpoint, max_time in endpoints_to_test:
            start_time = time.time()
            response = api_client.get(endpoint)
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            assert response_time < max_time, f"Endpoint {endpoint} too slow: {response_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, api_client, test_conversation_data):
        """Test requêtes API simultanées"""
        async def make_request(request_id: int):
            data = test_conversation_data.copy()
            data['user_input'] = f"Concurrent request {request_id}"
            
            response = api_client.post('/api/chat/message', data)
            return response.status_code, time.time()
        
        # Lancer 10 requêtes simultanées
        tasks = []
        start_time = time.time()
        
        for i in range(10):
            tasks.append(asyncio.create_task(asyncio.to_thread(make_request, i)))
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Vérifier que toutes les requêtes ont réussi
        success_count = sum(1 for status_code, _ in results if status_code == 200)
        assert success_count >= 8, f"Only {success_count}/10 requests succeeded"
        
        # Le temps total ne devrait pas être linéaire
        total_time = end_time - start_time
        assert total_time < 30, f"Concurrent requests took too long: {total_time:.2f}s"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])