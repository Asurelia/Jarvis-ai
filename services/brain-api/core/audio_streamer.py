"""
🎵 Audio Streamer - JARVIS Brain API
Streaming audio temps réel avec WebSocket et optimisations latence
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import base64
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class AudioChunk:
    """Chunk audio avec métadonnées"""
    id: str
    data: bytes
    format: str  # wav, mp3, raw
    sample_rate: int
    channels: int
    timestamp: float
    user_id: str
    sequence: int

@dataclass
class StreamSession:
    """Session de streaming audio"""
    session_id: str
    user_id: str
    connection_id: str
    created_at: float
    last_activity: float
    direction: str  # input, output, bidirectional
    format: str
    sample_rate: int
    channels: int
    buffer_size: int
    latency_target: float  # ms
    stats: Dict[str, Any]

class AudioStreamer:
    """
    Gestionnaire de streaming audio temps réel
    Optimisé pour latence <500ms avec buffer adaptatif
    """
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        
        # Sessions actives
        self.active_sessions: Dict[str, StreamSession] = {}
        self.audio_buffers: Dict[str, deque] = {}
        
        # Configuration streaming
        self.config = {
            "target_latency_ms": 200,  # Latence cible
            "max_latency_ms": 500,     # Latence max acceptable
            "buffer_size": 1024,       # Taille buffer audio
            "chunk_duration_ms": 20,   # Durée chunk audio
            "sample_rate": 16000,      # Fréquence échantillonnage
            "channels": 1,             # Mono
            "format": "wav"            # Format audio
        }
        
        # Optimisations performance
        self.adaptive_buffering = True
        self.jitter_compensation = True
        self.quality_adaptation = True
        
        # Statistiques temps réel
        self.stats = {
            "active_sessions": 0,
            "total_chunks_processed": 0,
            "avg_latency_ms": 0.0,
            "packet_loss_rate": 0.0,
            "quality_score": 1.0,
            "throughput_kbps": 0.0
        }
        
        # Callbacks pour traitement audio
        self.audio_processors: Dict[str, Callable] = {}
        
        logger.info("🎵 Audio Streamer initialisé")
    
    async def initialize(self):
        """Initialisation asynchrone"""
        logger.info("🚀 Initialisation Audio Streamer...")
        
        # Démarrer les tâches de gestion
        asyncio.create_task(self._latency_monitor())
        asyncio.create_task(self._buffer_manager())
        asyncio.create_task(self._stats_collector())
        
        logger.info("✅ Audio Streamer prêt")
    
    async def shutdown(self):
        """Arrêt propre du streamer"""
        logger.info("🛑 Arrêt Audio Streamer...")
        
        # Fermer toutes les sessions
        for session_id in list(self.active_sessions.keys()):
            await self.end_session(session_id)
        
        logger.info("✅ Audio Streamer arrêté")
    
    async def start_session(self, connection_id: str, user_id: str, config: Optional[Dict] = None) -> str:
        """
        Démarrer une session de streaming audio
        
        Args:
            connection_id: ID de connexion WebSocket
            user_id: ID utilisateur
            config: Configuration session (optionnelle)
        
        Returns:
            str: ID de session créée
        """
        session_id = f"audio_{user_id}_{int(time.time() * 1000)}"
        
        # Fusionner config par défaut avec config fournie
        session_config = {**self.config, **(config or {})}
        
        session = StreamSession(
            session_id=session_id,
            user_id=user_id,
            connection_id=connection_id,
            created_at=time.time(),
            last_activity=time.time(),
            direction=session_config.get("direction", "bidirectional"),
            format=session_config["format"],
            sample_rate=session_config["sample_rate"],
            channels=session_config["channels"],
            buffer_size=session_config["buffer_size"],
            latency_target=session_config["target_latency_ms"],
            stats={
                "chunks_sent": 0,
                "chunks_received": 0,
                "bytes_transferred": 0,
                "avg_chunk_latency": 0.0,
                "quality_degradations": 0
            }
        )
        
        self.active_sessions[session_id] = session
        self.audio_buffers[session_id] = deque(maxlen=100)  # Buffer 100 chunks
        self.stats["active_sessions"] += 1
        
        logger.info(f"🎵 Session audio démarrée: {session_id} (user: {user_id})")
        
        # Notifier client
        if self.websocket_manager:
            await self.websocket_manager._send_message(connection_id, {
                "type": "audio_session_started",
                "session_id": session_id,
                "config": session_config,
                "timestamp": time.time()
            })
        
        return session_id
    
    async def end_session(self, session_id: str):
        """Terminer une session de streaming"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        # Notifier client
        if self.websocket_manager:
            await self.websocket_manager._send_message(session.connection_id, {
                "type": "audio_session_ended",
                "session_id": session_id,
                "stats": session.stats,
                "timestamp": time.time()
            })
        
        # Nettoyer ressources
        del self.active_sessions[session_id]
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]
        
        self.stats["active_sessions"] -= 1
        
        logger.info(f"🎵 Session audio terminée: {session_id}")
    
    async def process_audio_chunk(self, session_id: str, chunk_data: Dict[str, Any]):
        """
        Traiter un chunk audio reçu
        
        Args:
            session_id: ID de session
            chunk_data: Données du chunk avec métadonnées
        """
        if session_id not in self.active_sessions:
            logger.warning(f"⚠️ Session inconnue: {session_id}")
            return
        
        session = self.active_sessions[session_id]
        session.last_activity = time.time()
        
        try:
            # Décoder données audio
            audio_data = base64.b64decode(chunk_data.get("data", ""))
            chunk_id = chunk_data.get("chunk_id", f"chunk_{int(time.time() * 1000)}")
            sequence = chunk_data.get("sequence", 0)
            
            # Créer chunk audio
            chunk = AudioChunk(
                id=chunk_id,
                data=audio_data,
                format=chunk_data.get("format", session.format),
                sample_rate=chunk_data.get("sample_rate", session.sample_rate),
                channels=chunk_data.get("channels", session.channels),
                timestamp=time.time(),
                user_id=session.user_id,
                sequence=sequence
            )
            
            # Ajouter au buffer
            self.audio_buffers[session_id].append(chunk)
            
            # Calculer latence
            receive_time = time.time()
            client_timestamp = chunk_data.get("timestamp", receive_time)
            latency_ms = (receive_time - client_timestamp) * 1000
            
            # Mettre à jour stats session
            session.stats["chunks_received"] += 1
            session.stats["bytes_transferred"] += len(audio_data)
            session.stats["avg_chunk_latency"] = (
                (session.stats["avg_chunk_latency"] * (session.stats["chunks_received"] - 1) + latency_ms) 
                / session.stats["chunks_received"]
            )
            
            # Traitement audio selon le type
            if chunk_data.get("type") == "input":
                await self._process_input_audio(session, chunk)
            elif chunk_data.get("type") == "output":
                await self._process_output_audio(session, chunk)
            
            # Optimisation adaptative
            if self.adaptive_buffering:
                await self._adapt_buffer_size(session, latency_ms)
            
            # Accusé de réception
            if self.websocket_manager:
                await self.websocket_manager._send_message(session.connection_id, {
                    "type": "audio_chunk_ack",
                    "chunk_id": chunk_id,
                    "session_id": session_id,
                    "latency_ms": latency_ms,
                    "buffer_level": len(self.audio_buffers[session_id]),
                    "timestamp": time.time()
                })
            
            logger.debug(f"🎵 Chunk traité: {chunk_id} (latence: {latency_ms:.1f}ms)")
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement chunk audio: {e}")
            session.stats["quality_degradations"] += 1
    
    async def send_audio_chunk(self, session_id: str, audio_data: bytes, metadata: Optional[Dict] = None):
        """
        Envoyer un chunk audio au client
        
        Args:
            session_id: ID de session
            audio_data: Données audio brutes
            metadata: Métadonnées additionnelles
        """
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        # Encoder données
        encoded_data = base64.b64encode(audio_data).decode('utf-8')
        chunk_id = f"out_{int(time.time() * 1000)}_{session.stats['chunks_sent']}"
        
        # Créer message
        message = {
            "type": "audio_chunk",
            "session_id": session_id,
            "chunk_id": chunk_id,
            "data": encoded_data,
            "format": session.format,
            "sample_rate": session.sample_rate,
            "channels": session.channels,
            "sequence": session.stats["chunks_sent"],
            "timestamp": time.time()
        }
        
        # Ajouter métadonnées si fournies
        if metadata:
            message.update(metadata)
        
        # Envoyer via WebSocket
        if self.websocket_manager:
            await self.websocket_manager._send_message(session.connection_id, message)
        
        session.stats["chunks_sent"] += 1
        session.stats["bytes_transferred"] += len(audio_data)
        
        logger.debug(f"🎵 Chunk envoyé: {chunk_id}")
    
    async def _process_input_audio(self, session: StreamSession, chunk: AudioChunk):
        """Traiter audio d'entrée (microphone utilisateur)"""
        
        # Traitement STT si disponible
        processor = self.audio_processors.get("stt")
        if processor:
            try:
                text_result = await processor(chunk.data, {
                    "format": chunk.format,
                    "sample_rate": chunk.sample_rate,
                    "channels": chunk.channels,
                    "user_id": session.user_id
                })
                
                # Envoyer résultat transcription
                if text_result and self.websocket_manager:
                    await self.websocket_manager._send_message(session.connection_id, {
                        "type": "transcription",
                        "text": text_result,
                        "chunk_id": chunk.id,
                        "confidence": 0.95,  # TODO: vraie confidence
                        "timestamp": time.time()
                    })
                    
            except Exception as e:
                logger.error(f"❌ Erreur STT: {e}")
    
    async def _process_output_audio(self, session: StreamSession, chunk: AudioChunk):
        """Traiter audio de sortie (vers haut-parleurs)"""
        
        # Optimisations qualité audio
        if self.quality_adaptation:
            # Ajuster qualité selon latence
            if session.stats["avg_chunk_latency"] > session.latency_target:
                # Réduire qualité pour améliorer latence
                pass
    
    async def _adapt_buffer_size(self, session: StreamSession, current_latency: float):
        """Adapter la taille du buffer selon la latence"""
        
        if current_latency > session.latency_target * 1.5:
            # Latence trop élevée, réduire buffer
            session.buffer_size = max(512, session.buffer_size - 128)
        elif current_latency < session.latency_target * 0.5:
            # Latence très faible, augmenter buffer pour stabilité
            session.buffer_size = min(4096, session.buffer_size + 128)
    
    async def _latency_monitor(self):
        """Monitorer la latence en continu"""
        while True:
            try:
                total_latency = 0
                session_count = 0
                
                for session in self.active_sessions.values():
                    if session.stats["avg_chunk_latency"] > 0:
                        total_latency += session.stats["avg_chunk_latency"]
                        session_count += 1
                
                if session_count > 0:
                    self.stats["avg_latency_ms"] = total_latency / session_count
                
                await asyncio.sleep(1)  # Check chaque seconde
                
            except Exception as e:
                logger.error(f"❌ Erreur monitoring latence: {e}")
                await asyncio.sleep(5)
    
    async def _buffer_manager(self):
        """Gérer les buffers audio"""
        while True:
            try:
                for session_id, buffer in self.audio_buffers.items():
                    # Nettoyer les vieux chunks
                    current_time = time.time()
                    while buffer and (current_time - buffer[0].timestamp) > 30:  # 30s max
                        buffer.popleft()
                
                await asyncio.sleep(5)  # Check toutes les 5s
                
            except Exception as e:
                logger.error(f"❌ Erreur gestion buffers: {e}")
                await asyncio.sleep(10)
    
    async def _stats_collector(self):
        """Collecter statistiques performance"""
        while True:
            try:
                # Calculer throughput
                total_bytes = sum(s.stats["bytes_transferred"] for s in self.active_sessions.values())
                self.stats["throughput_kbps"] = (total_bytes * 8) / 1000  # Convert to kbps
                
                # Calculer packet loss (simulé pour l'instant)
                total_chunks = sum(s.stats["chunks_received"] for s in self.active_sessions.values())
                self.stats["total_chunks_processed"] = total_chunks
                
                # Score qualité global
                latency_score = max(0, 1 - (self.stats["avg_latency_ms"] / self.config["max_latency_ms"]))
                self.stats["quality_score"] = latency_score
                
                await asyncio.sleep(10)  # Update toutes les 10s
                
            except Exception as e:
                logger.error(f"❌ Erreur collecte stats: {e}")
                await asyncio.sleep(30)
    
    def register_audio_processor(self, processor_type: str, callback: Callable):
        """
        Enregistrer un processeur audio (STT, TTS, etc.)
        
        Args:
            processor_type: Type de processeur (stt, tts, effects)
            callback: Fonction de traitement audio
        """
        self.audio_processors[processor_type] = callback
        logger.info(f"🔧 Processeur audio enregistré: {processor_type}")
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtenir les statistiques d'une session"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "duration": time.time() - session.created_at,
            "buffer_level": len(self.audio_buffers.get(session_id, [])),
            **session.stats
        }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques globales"""
        return {
            **self.stats,
            "config": self.config,
            "active_sessions_details": {
                sid: self.get_session_stats(sid) 
                for sid in self.active_sessions.keys()
            }
        }