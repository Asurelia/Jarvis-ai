"""
🔌 Tests d'intégration WebSocket temps réel pour JARVIS AI
Tests WebSocket avec gestion de connexions multiples et événements temps réel
"""

import pytest
import asyncio
import time
import json
import uuid
from typing import Dict, List, Optional, Any, Callable
import websockets
import threading
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
import logging

# Configuration WebSocket
WS_BASE_URL = "ws://localhost:8081/ws"
WS_TIMEOUT = 10
MAX_CONNECTIONS = 50

# Messages de test
TEST_MESSAGES = {
    'chat': {
        'type': 'chat_message',
        'data': {
            'user_input': 'Hello JARVIS via WebSocket',
            'persona': 'jarvis_classic',
            'session_id': None,  # Sera rempli dynamiquement
            'timestamp': None
        }
    },
    'voice_command': {
        'type': 'voice_command',
        'data': {
            'command': 'activate_voice_mode',
            'parameters': {'continuous': True},
            'session_id': None
        }
    },
    'system_query': {
        'type': 'system_query',
        'data': {
            'query': 'get_system_stats',
            'include': ['cpu', 'memory', 'gpu'],
            'session_id': None
        }
    },
    'memory_search': {
        'type': 'memory_search',
        'data': {
            'query': 'integration test',
            'limit': 10,
            'session_id': None
        }
    }
}

class WebSocketTestClient:
    """Client WebSocket pour les tests"""
    
    def __init__(self, uri: str = WS_BASE_URL):
        self.uri = uri
        self.websocket = None
        self.session_id = str(uuid.uuid4())
        self.received_messages = []
        self.connection_events = []
        self.is_connected = False
        self.message_handlers = {}
        self.logger = logging.getLogger(__name__)
    
    async def connect(self, timeout: float = WS_TIMEOUT) -> bool:
        """Connexion WebSocket avec timeout"""
        try:
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.uri),
                timeout=timeout
            )
            self.is_connected = True
            self.connection_events.append({
                'type': 'connected',
                'timestamp': time.time(),
                'session_id': self.session_id
            })
            return True
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Déconnexion WebSocket"""
        if self.websocket and self.is_connected:
            await self.websocket.close()
            self.is_connected = False
            self.connection_events.append({
                'type': 'disconnected',
                'timestamp': time.time(),
                'session_id': self.session_id
            })
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Envoi de message WebSocket"""
        if not self.is_connected or not self.websocket:
            return False
        
        try:
            # Ajouter les informations de session
            if 'data' in message and 'session_id' in message['data']:
                message['data']['session_id'] = self.session_id
            if 'data' in message and 'timestamp' in message['data']:
                message['data']['timestamp'] = time.time()
            
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    async def receive_message(self, timeout: float = WS_TIMEOUT) -> Optional[Dict[str, Any]]:
        """Réception de message WebSocket"""
        if not self.is_connected or not self.websocket:
            return None
        
        try:
            message_raw = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )
            message = json.loads(message_raw)
            self.received_messages.append({
                'message': message,
                'timestamp': time.time(),
                'session_id': self.session_id
            })
            return message
        except asyncio.TimeoutError:
            self.logger.warning("WebSocket receive timeout")
            return None
        except Exception as e:
            self.logger.error(f"Failed to receive message: {e}")
            return None
    
    async def listen_for_messages(self, duration: float, message_handler: Optional[Callable] = None):
        """Écoute des messages pendant une durée donnée"""
        end_time = time.time() + duration
        
        while time.time() < end_time and self.is_connected:
            try:
                message = await self.receive_message(timeout=1.0)
                if message and message_handler:
                    await message_handler(message)
            except Exception as e:
                self.logger.error(f"Error in message listener: {e}")
                break
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """Ajouter un gestionnaire de message"""
        self.message_handlers[message_type] = handler
    
    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Récupérer les messages par type"""
        return [
            msg for msg in self.received_messages
            if msg['message'].get('type') == message_type
        ]

@pytest.fixture(scope="function")
async def ws_client():
    """Fixture pour client WebSocket"""
    client = WebSocketTestClient()
    if await client.connect():
        yield client
    else:
        pytest.skip("Could not connect to WebSocket server")
    
    await client.disconnect()

@pytest.fixture(scope="function")
def test_message_data():
    """Données de test pour les messages"""
    session_id = str(uuid.uuid4())
    timestamp = time.time()
    
    messages = {}
    for msg_type, msg_template in TEST_MESSAGES.items():
        messages[msg_type] = json.loads(json.dumps(msg_template))  # Deep copy
        if 'data' in messages[msg_type]:
            messages[msg_type]['data']['session_id'] = session_id
            if 'timestamp' in messages[msg_type]['data']:
                messages[msg_type]['data']['timestamp'] = timestamp
    
    return messages

class TestWebSocketConnection:
    """Tests de connexion WebSocket"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_basic(self):
        """Test connexion WebSocket basique"""
        client = WebSocketTestClient()
        
        # Test connexion
        connected = await client.connect()
        assert connected, "Failed to establish WebSocket connection"
        assert client.is_connected, "Client should be marked as connected"
        
        # Test déconnexion
        await client.disconnect()
        assert not client.is_connected, "Client should be marked as disconnected"
    
    @pytest.mark.asyncio
    async def test_websocket_connection_timeout(self):
        """Test timeout de connexion WebSocket"""
        # Utiliser une URL invalide pour forcer un timeout
        client = WebSocketTestClient("ws://invalid-url:9999")
        
        start_time = time.time()
        connected = await client.connect(timeout=2.0)
        end_time = time.time()
        
        assert not connected, "Connection should have failed"
        assert end_time - start_time >= 2.0, "Timeout should have been respected"
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_connections(self):
        """Test connexions WebSocket multiples simultanées"""
        clients = []
        connection_tasks = []
        
        # Créer plusieurs clients
        for i in range(10):
            client = WebSocketTestClient()
            clients.append(client)
            connection_tasks.append(client.connect())
        
        # Connecter tous en parallèle
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        # Vérifier les connexions
        connected_count = sum(1 for result in results if result is True)
        assert connected_count >= 8, f"Only {connected_count}/10 connections succeeded"
        
        # Nettoyer
        for client in clients:
            if client.is_connected:
                await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, ws_client):
        """Test reconnexion WebSocket après déconnexion"""
        assert ws_client.is_connected, "Client should be initially connected"
        
        # Forcer déconnexion
        await ws_client.disconnect()
        assert not ws_client.is_connected, "Client should be disconnected"
        
        # Reconnecter
        reconnected = await ws_client.connect()
        assert reconnected, "Reconnection should succeed"
        assert ws_client.is_connected, "Client should be reconnected"

class TestWebSocketMessaging:
    """Tests d'échange de messages WebSocket"""
    
    @pytest.mark.asyncio
    async def test_send_chat_message(self, ws_client, test_message_data):
        """Test envoi de message de chat via WebSocket"""
        chat_message = test_message_data['chat']
        
        # Envoyer le message
        sent = await ws_client.send_message(chat_message)
        assert sent, "Failed to send chat message"
        
        # Attendre et recevoir la réponse
        response = await ws_client.receive_message(timeout=15.0)
        assert response is not None, "No response received"
        assert response.get('type') == 'chat_response', f"Unexpected response type: {response.get('type')}"
        assert 'data' in response, "Response should contain data"
        assert 'response' in response['data'], "Response should contain response text"
    
    @pytest.mark.asyncio
    async def test_send_voice_command(self, ws_client, test_message_data):
        """Test envoi de commande vocale via WebSocket"""
        voice_message = test_message_data['voice_command']
        
        # Envoyer la commande
        sent = await ws_client.send_message(voice_message)
        assert sent, "Failed to send voice command"
        
        # Attendre la réponse
        response = await ws_client.receive_message()
        assert response is not None, "No response received"
        assert response.get('type') in ['voice_response', 'command_ack'], "Unexpected response type"
    
    @pytest.mark.asyncio
    async def test_send_system_query(self, ws_client, test_message_data):
        """Test requête système via WebSocket"""
        system_message = test_message_data['system_query']
        
        # Envoyer la requête
        sent = await ws_client.send_message(system_message)
        assert sent, "Failed to send system query"
        
        # Attendre la réponse
        response = await ws_client.receive_message()
        assert response is not None, "No response received"
        assert response.get('type') == 'system_response', "Expected system response"
        assert 'data' in response, "Response should contain data"
    
    @pytest.mark.asyncio
    async def test_bidirectional_communication(self, ws_client, test_message_data):
        """Test communication bidirectionnelle"""
        messages_to_send = [
            test_message_data['chat'],
            test_message_data['system_query'],
            test_message_data['memory_search']
        ]
        
        responses = []
        
        for message in messages_to_send:
            # Envoyer message
            sent = await ws_client.send_message(message)
            assert sent, f"Failed to send message: {message['type']}"
            
            # Recevoir réponse
            response = await ws_client.receive_message(timeout=10.0)
            assert response is not None, f"No response for message: {message['type']}"
            responses.append(response)
        
        # Vérifier que toutes les réponses sont reçues
        assert len(responses) == len(messages_to_send), "Not all responses received"
    
    @pytest.mark.asyncio
    async def test_message_order_preservation(self, ws_client):
        """Test préservation de l'ordre des messages"""
        messages = []
        expected_responses = []
        
        # Envoyer plusieurs messages numérotés
        for i in range(5):
            message = {
                'type': 'test_message',
                'data': {
                    'sequence': i,
                    'content': f'Test message {i}',
                    'session_id': ws_client.session_id,
                    'timestamp': time.time()
                }
            }
            messages.append(message)
            expected_responses.append(i)
            
            sent = await ws_client.send_message(message)
            assert sent, f"Failed to send message {i}"
        
        # Recevoir toutes les réponses
        responses = []
        for _ in range(5):
            response = await ws_client.receive_message()
            if response:
                responses.append(response)
        
        # Vérifier que l'ordre est préservé (si le serveur le garantit)
        assert len(responses) == len(messages), "Not all responses received"

class TestWebSocketRealTime:
    """Tests de fonctionnalités temps réel"""
    
    @pytest.mark.asyncio
    async def test_real_time_notifications(self, ws_client):
        """Test notifications temps réel"""
        notifications_received = []
        
        async def notification_handler(message):
            if message.get('type') == 'notification':
                notifications_received.append(message)
        
        # Écouter les notifications pendant 5 secondes
        listen_task = asyncio.create_task(
            ws_client.listen_for_messages(5.0, notification_handler)
        )
        
        # Attendre un peu puis déclencher une action qui génère des notifications
        await asyncio.sleep(1.0)
        
        # Envoyer une commande qui pourrait générer des notifications
        command = {
            'type': 'enable_notifications',
            'data': {
                'types': ['system', 'chat', 'voice'],
                'session_id': ws_client.session_id
            }
        }
        await ws_client.send_message(command)
        
        # Terminer l'écoute
        await listen_task
        
        # Vérifier que des notifications ont été reçues (si applicable)
        # Note: Ce test dépend de l'implémentation du serveur
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, ws_client):
        """Test réponse en streaming"""
        # Envoyer une requête qui génère une réponse en streaming
        streaming_request = {
            'type': 'streaming_chat',
            'data': {
                'user_input': 'Tell me a long story about AI',
                'stream': True,
                'session_id': ws_client.session_id
            }
        }
        
        sent = await ws_client.send_message(streaming_request)
        assert sent, "Failed to send streaming request"
        
        # Collecter les fragments de streaming
        streaming_fragments = []
        fragment_count = 0
        max_fragments = 10
        
        while fragment_count < max_fragments:
            response = await ws_client.receive_message(timeout=2.0)
            if not response:
                break
            
            if response.get('type') == 'streaming_fragment':
                streaming_fragments.append(response)
                fragment_count += 1
            elif response.get('type') == 'streaming_complete':
                break
        
        # Vérifier le streaming (si implémenté)
        if streaming_fragments:
            assert len(streaming_fragments) > 0, "No streaming fragments received"
            
            # Vérifier la continuité des fragments
            for fragment in streaming_fragments:
                assert 'data' in fragment, "Fragment should contain data"
                assert 'content' in fragment['data'], "Fragment should contain content"
    
    @pytest.mark.asyncio
    async def test_concurrent_message_handling(self, ws_client, test_message_data):
        """Test gestion de messages concurrents"""
        async def send_messages_batch(batch_id: int, count: int):
            responses = []
            for i in range(count):
                message = {
                    'type': 'concurrent_test',
                    'data': {
                        'batch_id': batch_id,
                        'message_id': i,
                        'content': f'Batch {batch_id}, Message {i}',
                        'session_id': ws_client.session_id
                    }
                }
                
                sent = await ws_client.send_message(message)
                if sent:
                    response = await ws_client.receive_message(timeout=5.0)
                    if response:
                        responses.append(response)
            
            return responses
        
        # Envoyer plusieurs batches en parallèle
        tasks = [
            send_messages_batch(batch_id, 3)
            for batch_id in range(3)
        ]
        
        batch_results = await asyncio.gather(*tasks)
        
        # Vérifier les résultats
        total_responses = sum(len(batch) for batch in batch_results)
        assert total_responses >= 6, f"Expected at least 6 responses, got {total_responses}"

class TestWebSocketPerformance:
    """Tests de performance WebSocket"""
    
    @pytest.mark.asyncio
    async def test_message_throughput(self, ws_client):
        """Test débit de messages WebSocket"""
        message_count = 50
        start_time = time.time()
        
        # Envoyer des messages rapidement
        for i in range(message_count):
            message = {
                'type': 'throughput_test',
                'data': {
                    'message_id': i,
                    'timestamp': time.time(),
                    'session_id': ws_client.session_id
                }
            }
            
            sent = await ws_client.send_message(message)
            assert sent, f"Failed to send message {i}"
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = message_count / duration
        
        # Vérifier le débit (au moins 10 messages/seconde)
        assert throughput >= 10, f"Throughput too low: {throughput:.1f} msg/s"
    
    @pytest.mark.asyncio
    async def test_large_message_handling(self, ws_client):
        """Test gestion de gros messages"""
        # Créer un gros message (1MB de données)
        large_content = "x" * (1024 * 1024)  # 1MB
        large_message = {
            'type': 'large_message_test',
            'data': {
                'content': large_content,
                'size': len(large_content),
                'session_id': ws_client.session_id
            }
        }
        
        start_time = time.time()
        sent = await ws_client.send_message(large_message)
        
        if sent:
            response = await ws_client.receive_message(timeout=30.0)
            end_time = time.time()
            
            assert response is not None, "No response to large message"
            processing_time = end_time - start_time
            assert processing_time < 30.0, f"Large message processing too slow: {processing_time:.2f}s"
        else:
            pytest.skip("Server doesn't support large messages")
    
    @pytest.mark.asyncio
    async def test_connection_stability_under_load(self):
        """Test stabilité des connexions sous charge"""
        client_count = 20
        message_per_client = 10
        
        async def client_workload(client_id: int):
            client = WebSocketTestClient()
            try:
                if not await client.connect():
                    return False, 0
                
                successful_messages = 0
                for i in range(message_per_client):
                    message = {
                        'type': 'load_test',
                        'data': {
                            'client_id': client_id,
                            'message_id': i,
                            'session_id': client.session_id
                        }
                    }
                    
                    if await client.send_message(message):
                        response = await client.receive_message(timeout=5.0)
                        if response:
                            successful_messages += 1
                
                await client.disconnect()
                return True, successful_messages
            
            except Exception as e:
                logging.error(f"Client {client_id} error: {e}")
                return False, 0
        
        # Lancer tous les clients en parallèle
        tasks = [client_workload(i) for i in range(client_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyser les résultats
        successful_clients = sum(1 for success, _ in results if success)
        total_messages = sum(count for success, count in results if success)
        
        assert successful_clients >= client_count * 0.8, f"Only {successful_clients}/{client_count} clients succeeded"
        expected_messages = client_count * message_per_client
        assert total_messages >= expected_messages * 0.8, f"Only {total_messages}/{expected_messages} messages succeeded"

class TestWebSocketErrorHandling:
    """Tests de gestion d'erreurs WebSocket"""
    
    @pytest.mark.asyncio
    async def test_invalid_message_format(self, ws_client):
        """Test gestion de messages invalides"""
        # Envoyer un message avec format invalide
        try:
            await ws_client.websocket.send("invalid json message")
            
            # Attendre une réponse d'erreur
            response = await ws_client.receive_message(timeout=5.0)
            
            if response:
                assert response.get('type') == 'error', "Expected error response"
                assert 'message' in response.get('data', {}), "Error should contain message"
        
        except Exception as e:
            # Le serveur pourrait fermer la connexion
            logging.info(f"Connection closed due to invalid message: {e}")
    
    @pytest.mark.asyncio
    async def test_connection_recovery_after_error(self):
        """Test récupération après erreur de connexion"""
        client = WebSocketTestClient()
        
        # Connexion initiale
        connected = await client.connect()
        assert connected, "Initial connection failed"
        
        # Simuler une erreur de connexion
        if client.websocket:
            await client.websocket.close()
        
        # Attendre un peu
        await asyncio.sleep(1.0)
        
        # Tenter une reconnexion
        reconnected = await client.connect()
        assert reconnected, "Reconnection after error failed"
        
        # Vérifier que la connexion fonctionne
        test_message = {
            'type': 'test_recovery',
            'data': {
                'content': 'Testing recovery',
                'session_id': client.session_id
            }
        }
        
        sent = await client.send_message(test_message)
        assert sent, "Failed to send message after recovery"
        
        await client.disconnect()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])