"""
🔌 WebSocket Handler - JARVIS Brain API
Gestionnaire WebSocket intégré à FastAPI
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import time

logger = logging.getLogger(__name__)

class WebSocketHandler:
    """
    Gestionnaire WebSocket pour intégration FastAPI
    Interface entre FastAPI WebSocket et WebSocketManager
    """
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def handle_websocket(self, websocket: WebSocket, client_id: str = None):
        """
        Gérer une connexion WebSocket depuis FastAPI
        
        Args:
            websocket: Instance WebSocket FastAPI
            client_id: ID optionnel du client
        """
        # Accepter la connexion
        await websocket.accept()
        
        # Générer ID si pas fourni
        if not client_id:
            import uuid
            client_id = str(uuid.uuid4())
        
        # Stocker la connexion
        self.active_connections[client_id] = websocket
        
        try:
            logger.info(f"🔗 Nouvelle connexion WebSocket: {client_id}")
            
            # Message de bienvenue
            welcome_message = {
                "type": "welcome",
                "client_id": client_id,
                "server": "JARVIS Brain API v2.0",
                "timestamp": time.time(),
                "supported_features": [
                    "chat",
                    "audio_streaming", 
                    "real_time_processing",
                    "context_awareness"
                ]
            }
            
            await websocket.send_text(json.dumps(welcome_message))
            
            # Déléguer à WebSocketManager si disponible
            if self.websocket_manager:
                # Créer un wrapper pour compatibilité
                websocket_wrapper = WebSocketWrapper(websocket, client_id)
                await self.websocket_manager.handle_connection(websocket_wrapper, "/ws")
            else:
                # Gestion basique si pas de manager
                await self._handle_basic_connection(websocket, client_id)
                
        except WebSocketDisconnect:
            logger.info(f"🔌 Connexion fermée: {client_id}")
        except Exception as e:
            logger.error(f"❌ Erreur WebSocket {client_id}: {e}")
            await self._send_error(websocket, f"Erreur serveur: {str(e)}")
        finally:
            # Nettoyer la connexion
            if client_id in self.active_connections:
                del self.active_connections[client_id]
    
    async def _handle_basic_connection(self, websocket: WebSocket, client_id: str):
        """
        Gestion basique WebSocket sans WebSocketManager
        """
        try:
            while True:
                # Recevoir message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                logger.info(f"📨 Message reçu de {client_id}: {message.get('type', 'unknown')}")
                
                # Router les messages
                await self._route_message(websocket, client_id, message)
                
        except WebSocketDisconnect:
            pass  # Connexion fermée normalement
        except json.JSONDecodeError:
            await self._send_error(websocket, "Format JSON invalide")
        except Exception as e:
            await self._send_error(websocket, f"Erreur traitement: {str(e)}")
    
    async def _route_message(self, websocket: WebSocket, client_id: str, message: Dict[str, Any]):
        """
        Router les messages vers les bons handlers
        """
        message_type = message.get("type", "unknown")
        
        if message_type == "ping":
            await self._handle_ping(websocket, message)
        elif message_type == "chat":
            await self._handle_chat(websocket, client_id, message)
        elif message_type == "audio_chunk":
            await self._handle_audio(websocket, client_id, message)
        elif message_type == "auth":
            await self._handle_auth(websocket, client_id, message)
        else:
            await self._send_error(websocket, f"Type de message inconnu: {message_type}")
    
    async def _handle_ping(self, websocket: WebSocket, message: Dict[str, Any]):
        """Gérer ping/pong pour maintenir connexion"""
        pong_message = {
            "type": "pong",
            "timestamp": time.time(),
            "original_timestamp": message.get("timestamp")
        }
        await websocket.send_text(json.dumps(pong_message))
    
    async def _handle_chat(self, websocket: WebSocket, client_id: str, message: Dict[str, Any]):
        """Gérer message de chat"""
        user_message = message.get("message", "")
        message_id = message.get("message_id", "unknown")
        
        # Simulation traitement chat
        await asyncio.sleep(0.1)
        
        # Réponse simulée
        if "bonjour" in user_message.lower():
            response_text = "Bonjour ! Je suis JARVIS. Comment puis-je vous aider ?"
        elif "temps" in user_message.lower():
            import datetime
            now = datetime.datetime.now()
            response_text = f"Il est {now.strftime('%H:%M:%S')} le {now.strftime('%d/%m/%Y')}"
        else:
            response_text = f"J'ai bien reçu votre message: '{user_message}'. Je réfléchis à la meilleure réponse."
        
        response_message = {
            "type": "chat_response",
            "message_id": message_id,
            "response": response_text,
            "client_id": client_id,
            "timestamp": time.time(),
            "processing_time": 0.1
        }
        
        await websocket.send_text(json.dumps(response_message))
    
    async def _handle_audio(self, websocket: WebSocket, client_id: str, message: Dict[str, Any]):
        """Gérer chunk audio"""
        chunk_id = message.get("chunk_id", "unknown")
        audio_data = message.get("audio_data", "")
        
        logger.info(f"🎵 Chunk audio reçu: {chunk_id} ({len(audio_data)} bytes)")
        
        # Accusé de réception
        ack_message = {
            "type": "audio_received",
            "chunk_id": chunk_id,
            "status": "received",
            "timestamp": time.time()
        }
        
        await websocket.send_text(json.dumps(ack_message))
        
        # TODO: Traiter avec STT service
    
    async def _handle_auth(self, websocket: WebSocket, client_id: str, message: Dict[str, Any]):
        """Gérer authentification"""
        user_id = message.get("user_id")
        token = message.get("token")
        
        # Simulation authentification
        if user_id:
            auth_response = {
                "type": "auth_success",
                "user_id": user_id,
                "client_id": client_id,
                "session_id": f"session_{client_id}",
                "timestamp": time.time()
            }
            
            logger.info(f"🔐 Utilisateur authentifié: {user_id}")
        else:
            auth_response = {
                "type": "auth_error",
                "error": "user_id requis",
                "timestamp": time.time()
            }
        
        await websocket.send_text(json.dumps(auth_response))
    
    async def _send_error(self, websocket: WebSocket, error_message: str):
        """Envoyer message d'erreur"""
        error_response = {
            "type": "error",
            "error": error_message,
            "timestamp": time.time()
        }
        
        try:
            await websocket.send_text(json.dumps(error_response))
        except:
            pass  # Connexion peut être fermée
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Diffuser message à toutes les connexions actives"""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        
        # Envoyer à toutes les connexions actives
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_json)
            except:
                disconnected.append(client_id)
        
        # Nettoyer les connexions fermées
        for client_id in disconnected:
            del self.active_connections[client_id]
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Envoyer message à un client spécifique"""
        if client_id not in self.active_connections:
            return False
        
        try:
            message_json = json.dumps(message)
            await self.active_connections[client_id].send_text(message_json)
            return True
        except:
            # Connexion fermée
            del self.active_connections[client_id]
            return False
    
    def get_active_connections_count(self) -> int:
        """Obtenir le nombre de connexions actives"""
        return len(self.active_connections)
    
    def get_connection_ids(self) -> list:
        """Obtenir la liste des IDs de connexion actifs"""
        return list(self.active_connections.keys())


class WebSocketWrapper:
    """
    Wrapper pour compatibilité avec WebSocketManager existant
    """
    
    def __init__(self, fastapi_websocket: WebSocket, client_id: str):
        self.fastapi_websocket = fastapi_websocket
        self.client_id = client_id
    
    async def send(self, message: str):
        """Envoyer message (compatible avec websockets library)"""
        await self.fastapi_websocket.send_text(message)
    
    async def recv(self):
        """Recevoir message (compatible avec websockets library)"""
        return await self.fastapi_websocket.receive_text()
    
    async def __aiter__(self):
        """Iterator pour messages (compatible avec websockets library)"""
        try:
            while True:
                yield await self.recv()
        except WebSocketDisconnect:
            return

# Gestionnaire global WebSocket
websocket_handler = WebSocketHandler()

async def websocket_endpoint(websocket: WebSocket):
    """Point d'entrée WebSocket pour FastAPI"""
    # Obtenir le gestionnaire depuis l'état de l'app
    from main import app_state
    
    if not websocket_handler.websocket_manager and app_state.get("websocket_manager"):
        websocket_handler.websocket_manager = app_state["websocket_manager"]
    
    await websocket_handler.handle_websocket(websocket)