"""
🔌 WebSocket Manager - JARVIS Brain API
Gestion des connexions WebSocket temps réel
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
import websockets
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

@dataclass
class WebSocketConnection:
    id: str
    websocket: websockets.WebSocketServerProtocol
    user_id: Optional[str]
    connected_at: float
    last_activity: float
    meta_data: Dict[str, Any]

class WebSocketManager:
    """Gestionnaire des connexions WebSocket pour streaming audio et communication temps réel"""
    
    def __init__(self, agent=None, memory=None, audio_streamer=None):
        self.agent = agent
        self.memory = memory
        self.audio_streamer = audio_streamer
        
        # Connexions actives
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, List[str]] = {}
        
        # Statistiques
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0
        }
        
        logger.info("🔌 WebSocket Manager initialisé")
    
    async def initialize(self):
        """Initialisation asynchrone"""
        logger.info("🚀 Initialisation WebSocket Manager...")
        await asyncio.sleep(0.1)
        logger.info("✅ WebSocket Manager prêt")
    
    async def shutdown(self):
        """Arrêt propre du gestionnaire"""
        logger.info("🛑 Arrêt WebSocket Manager...")
        
        # Fermer toutes les connexions
        for connection in list(self.connections.values()):
            await self._disconnect_client(connection.id)
        
        logger.info("✅ WebSocket Manager arrêté")
    
    async def handle_connection(self, websocket, path):
        """Gérer une nouvelle connexion WebSocket"""
        connection_id = str(uuid.uuid4())
        
        try:
            connection = WebSocketConnection(
                id=connection_id,
                websocket=websocket,
                user_id=None,
                connected_at=asyncio.get_event_loop().time(),
                last_activity=asyncio.get_event_loop().time(),
                meta_data={}
            )
            
            self.connections[connection_id] = connection
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
            logger.info(f"🔗 Nouvelle connexion WebSocket: {connection_id}")
            
            # Envoyer message de bienvenue
            await self._send_message(connection_id, {
                "type": "welcome",
                "connection_id": connection_id,
                "timestamp": connection.connected_at
            })
            
            # Boucle de traitement des messages
            async for message in websocket:
                await self._handle_message(connection_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Connexion fermée: {connection_id}")
        except Exception as e:
            logger.error(f"❌ Erreur connexion {connection_id}: {e}")
        finally:
            await self._disconnect_client(connection_id)
    
    async def _handle_message(self, connection_id: str, message: str):
        """Traiter un message reçu via WebSocket"""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        connection.last_activity = asyncio.get_event_loop().time()
        self.stats["messages_received"] += 1
        
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            logger.info(f"📨 Message reçu ({connection_id}): {message_type}")
            
            # Router les messages selon le type
            if message_type == "auth":
                await self._handle_auth(connection_id, data)
            elif message_type == "chat":
                await self._handle_chat_message(connection_id, data)
            elif message_type == "audio_chunk":
                await self._handle_audio_chunk(connection_id, data)
            elif message_type == "audio_session_start":
                await self._handle_audio_session_start(connection_id, data)
            elif message_type == "audio_session_end":
                await self._handle_audio_session_end(connection_id, data)
            elif message_type == "ping":
                await self._handle_ping(connection_id, data)
            else:
                await self._send_error(connection_id, f"Type de message inconnu: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error(connection_id, "Format JSON invalide")
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
            await self._send_error(connection_id, f"Erreur interne: {str(e)}")
    
    async def _handle_auth(self, connection_id: str, data: Dict):
        """Gérer l'authentification utilisateur"""
        user_id = data.get("user_id")
        if not user_id:
            await self._send_error(connection_id, "user_id requis pour l'authentification")
            return
        
        connection = self.connections[connection_id]
        connection.user_id = user_id
        
        # Associer la connexion à l'utilisateur
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        await self._send_message(connection_id, {
            "type": "auth_success",
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        logger.info(f"🔐 Utilisateur authentifié: {user_id} ({connection_id})")
    
    async def _handle_chat_message(self, connection_id: str, data: Dict):
        """Gérer un message de chat"""
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        if not user_id:
            await self._send_error(connection_id, "Authentification requise")
            return
        
        message_content = data.get("message", "")
        if not message_content:
            await self._send_error(connection_id, "Message vide")
            return
        
        # Envoyer accusé de réception
        await self._send_message(connection_id, {
            "type": "message_received",
            "message_id": data.get("message_id"),
            "timestamp": asyncio.get_event_loop().time()
        })
        
        try:
            # Traiter avec l'agent si disponible
            if self.agent:
                # Obtenir le contexte utilisateur
                context = {}
                if self.memory:
                    context = await self.memory.get_context_for_user(user_id, message_content)
                
                # Exécuter la tâche avec l'agent
                execution = await self.agent.execute_task(message_content, context)
                
                # Envoyer la réponse
                await self._send_message(connection_id, {
                    "type": "chat_response",
                    "message_id": data.get("message_id"),
                    "response": execution.final_answer or "Désolé, je n'ai pas pu traiter votre demande.",
                    "execution_time": execution.total_duration,
                    "steps_count": len(execution.steps),
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # Enregistrer l'interaction en mémoire
                if self.memory:
                    await self.memory.record_interaction(
                        user_id=user_id,
                        query=message_content,
                        response=execution.final_answer or "Erreur",
                        context={"websocket": True, "connection_id": connection_id}
                    )
            else:
                # Réponse simulée si pas d'agent
                await self._send_message(connection_id, {
                    "type": "chat_response",
                    "message_id": data.get("message_id"),
                    "response": f"Echo: {message_content}",
                    "timestamp": asyncio.get_event_loop().time()
                })
        
        except Exception as e:
            logger.error(f"❌ Erreur traitement chat: {e}")
            await self._send_error(connection_id, f"Erreur traitement: {str(e)}")
    
    async def _handle_audio_chunk(self, connection_id: str, data: Dict):
        """Gérer un chunk audio pour streaming"""
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        if not user_id:
            await self._send_error(connection_id, "Authentification requise")
            return
        
        try:
            # Déléguer au streamer audio si disponible
            if self.audio_streamer:
                session_id = data.get("session_id")
                if session_id:
                    await self.audio_streamer.process_audio_chunk(session_id, data)
                else:
                    await self._send_error(connection_id, "session_id requis pour streaming audio")
            else:
                # Fallback: traitement basique
                chunk_id = data.get("chunk_id")
                audio_data = data.get("audio_data", data.get("data"))
                
                await self._send_message(connection_id, {
                    "type": "audio_received",
                    "chunk_id": chunk_id,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                logger.info(f"🎵 Chunk audio reçu: {chunk_id}")
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement audio: {e}")
            await self._send_error(connection_id, f"Erreur audio: {str(e)}")
    
    async def _handle_audio_session_start(self, connection_id: str, data: Dict):
        """Démarrer une session de streaming audio"""
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        if not user_id:
            await self._send_error(connection_id, "Authentification requise")
            return
        
        try:
            if self.audio_streamer:
                config = data.get("config", {})
                session_id = await self.audio_streamer.start_session(connection_id, user_id, config)
                
                await self._send_message(connection_id, {
                    "type": "audio_session_started", 
                    "session_id": session_id,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                logger.info(f"🎵 Session audio démarrée: {session_id}")
            else:
                await self._send_error(connection_id, "Audio streaming non disponible")
                
        except Exception as e:
            logger.error(f"❌ Erreur démarrage session audio: {e}")
            await self._send_error(connection_id, f"Erreur session audio: {str(e)}")
    
    async def _handle_audio_session_end(self, connection_id: str, data: Dict):
        """Terminer une session de streaming audio"""
        try:
            if self.audio_streamer:
                session_id = data.get("session_id")
                if session_id:
                    await self.audio_streamer.end_session(session_id)
                    
                    await self._send_message(connection_id, {
                        "type": "audio_session_ended",
                        "session_id": session_id,
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    
                    logger.info(f"🎵 Session audio terminée: {session_id}")
                else:
                    await self._send_error(connection_id, "session_id requis")
            else:
                await self._send_error(connection_id, "Audio streaming non disponible")
                
        except Exception as e:
            logger.error(f"❌ Erreur arrêt session audio: {e}")
            await self._send_error(connection_id, f"Erreur arrêt session: {str(e)}")
    
    async def _handle_ping(self, connection_id: str, data: Dict):
        """Gérer un ping pour maintenir la connexion"""
        await self._send_message(connection_id, {
            "type": "pong",
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def _send_message(self, connection_id: str, message: Dict):
        """Envoyer un message via WebSocket"""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        try:
            await connection.websocket.send(json.dumps(message))
            self.stats["messages_sent"] += 1
        except websockets.exceptions.ConnectionClosed:
            await self._disconnect_client(connection_id)
        except Exception as e:
            logger.error(f"❌ Erreur envoi message: {e}")
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Envoyer un message d'erreur"""
        await self._send_message(connection_id, {
            "type": "error",
            "error": error_message,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def _disconnect_client(self, connection_id: str):
        """Déconnecter un client"""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        # Retirer de la liste des connexions utilisateur
        if connection.user_id and connection.user_id in self.user_connections:
            if connection_id in self.user_connections[connection.user_id]:
                self.user_connections[connection.user_id].remove(connection_id)
            
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Retirer de la liste des connexions
        del self.connections[connection_id]
        self.stats["active_connections"] -= 1
        
        logger.info(f"🔌 Client déconnecté: {connection_id}")
    
    async def broadcast_to_user(self, user_id: str, message: Dict):
        """Diffuser un message à toutes les connexions d'un utilisateur"""
        if user_id not in self.user_connections:
            return
        
        for connection_id in self.user_connections[user_id]:
            await self._send_message(connection_id, message)
    
    async def broadcast_to_all(self, message: Dict):
        """Diffuser un message à toutes les connexions actives"""
        for connection_id in list(self.connections.keys()):
            await self._send_message(connection_id, message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du gestionnaire WebSocket"""
        return {
            **self.stats,
            "unique_users": len(self.user_connections),
            "avg_connections_per_user": len(self.connections) / max(len(self.user_connections), 1)
        }