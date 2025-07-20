"""
📡 Stream Manager - TTS Service
Gestion du streaming audio temps réel
"""

import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
import numpy as np
import time
from collections import deque
import io

logger = logging.getLogger(__name__)

class StreamManager:
    """
    Gestionnaire de streaming audio pour synthèse temps réel
    - Chunking intelligent
    - Buffer adaptatif
    - Gestion latence
    """
    
    def __init__(
        self,
        tts_engine,
        audio_processor,
        chunk_duration_ms: int = 20,
        buffer_size: int = 5
    ):
        self.tts_engine = tts_engine
        self.audio_processor = audio_processor
        self.chunk_duration_ms = chunk_duration_ms
        self.buffer_size = buffer_size
        
        # État des streams
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.stream_counter = 0
        
        # Configuration streaming
        self.sample_rate = 22050
        self.channels = 1
        self.bytes_per_sample = 2  # 16-bit
        
        # Calcul taille chunk
        self.samples_per_chunk = int(
            self.sample_rate * self.chunk_duration_ms / 1000
        )
        self.bytes_per_chunk = (
            self.samples_per_chunk * self.channels * self.bytes_per_sample
        )
        
        logger.info(
            f"📡 Stream Manager initialisé: "
            f"{chunk_duration_ms}ms chunks, "
            f"{self.bytes_per_chunk} bytes/chunk"
        )
    
    async def initialize(self):
        """Initialisation asynchrone"""
        logger.info("🚀 Initialisation Stream Manager...")
        
        # Démarrer tâche de monitoring
        asyncio.create_task(self._monitor_streams())
        
        logger.info("✅ Stream Manager prêt")
    
    async def stream_synthesis(
        self,
        text: str,
        voice_id: str = "default",
        language: str = "fr",
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        """
        Générer un stream audio à partir du texte
        
        Args:
            text: Texte à synthétiser
            voice_id: ID de la voix
            language: Langue
            speed: Vitesse
            pitch: Hauteur
            
        Yields:
            bytes: Chunks audio WAV
        """
        stream_id = f"stream_{self.stream_counter}"
        self.stream_counter += 1
        
        try:
            # Enregistrer le stream
            self.active_streams[stream_id] = {
                "start_time": time.time(),
                "text_length": len(text),
                "chunks_sent": 0,
                "status": "active"
            }
            
            logger.info(f"📡 Démarrage stream {stream_id}: {len(text)} caractères")
            
            # Stratégie de chunking selon la longueur
            if len(text) < 100:
                # Texte court: synthèse complète
                async for chunk in self._stream_full_synthesis(
                    text, voice_id, language, speed, pitch
                ):
                    self.active_streams[stream_id]["chunks_sent"] += 1
                    yield chunk
            else:
                # Texte long: synthèse par phrases
                async for chunk in self._stream_sentence_synthesis(
                    text, voice_id, language, speed, pitch
                ):
                    self.active_streams[stream_id]["chunks_sent"] += 1
                    yield chunk
            
            # Marquer comme terminé
            self.active_streams[stream_id]["status"] = "completed"
            self.active_streams[stream_id]["end_time"] = time.time()
            
            duration = time.time() - self.active_streams[stream_id]["start_time"]
            logger.info(
                f"✅ Stream {stream_id} terminé: "
                f"{self.active_streams[stream_id]['chunks_sent']} chunks, "
                f"{duration:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur stream {stream_id}: {e}")
            if stream_id in self.active_streams:
                self.active_streams[stream_id]["status"] = "error"
            raise
        
        finally:
            # Nettoyer après délai
            asyncio.create_task(self._cleanup_stream(stream_id, delay=60))
    
    async def _stream_full_synthesis(
        self,
        text: str,
        voice_id: str,
        language: str,
        speed: float,
        pitch: float
    ) -> AsyncGenerator[bytes, None]:
        """Stream avec synthèse complète puis chunking"""
        
        # Synthétiser tout l'audio
        audio_data = await self.tts_engine.synthesize(
            text, voice_id, language, speed, pitch
        )
        
        # Traiter l'audio
        processed_audio = await self.audio_processor.process(
            audio_data,
            normalize=True,
            remove_silence=False  # Garder timing pour streaming
        )
        
        # Chunker l'audio
        async for chunk in self._chunk_audio(processed_audio):
            yield chunk
    
    async def _stream_sentence_synthesis(
        self,
        text: str,
        voice_id: str,
        language: str,
        speed: float,
        pitch: float
    ) -> AsyncGenerator[bytes, None]:
        """Stream avec synthèse par phrases"""
        
        # Découper en phrases
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # Synthétiser la phrase
            audio_data = await self.tts_engine.synthesize(
                sentence, voice_id, language, speed, pitch
            )
            
            # Traiter l'audio
            processed_audio = await self.audio_processor.process(
                audio_data,
                normalize=True,
                remove_silence=False
            )
            
            # Chunker et yielder
            async for chunk in self._chunk_audio(processed_audio):
                yield chunk
    
    def _split_sentences(self, text: str) -> List[str]:
        """Découper le texte en phrases"""
        # Séparateurs de phrases
        separators = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        
        sentences = []
        current = ""
        
        for char in text:
            current += char
            
            # Vérifier si on a un séparateur
            for sep in separators:
                if current.endswith(sep):
                    sentences.append(current)
                    current = ""
                    break
        
        # Ajouter le reste
        if current:
            sentences.append(current)
        
        return sentences
    
    async def _chunk_audio(self, audio_data: bytes) -> AsyncGenerator[bytes, None]:
        """Découper l'audio en chunks de taille fixe"""
        
        # Créer buffer
        buffer = io.BytesIO(audio_data)
        
        # Lire et envoyer par chunks
        while True:
            chunk = buffer.read(self.bytes_per_chunk)
            
            if not chunk:
                break
            
            # Padder si nécessaire
            if len(chunk) < self.bytes_per_chunk:
                chunk += b'\x00' * (self.bytes_per_chunk - len(chunk))
            
            # Petit délai pour simuler streaming temps réel
            await asyncio.sleep(self.chunk_duration_ms / 1000)
            
            yield chunk
    
    async def _monitor_streams(self):
        """Monitorer les streams actifs"""
        while True:
            try:
                active_count = sum(
                    1 for s in self.active_streams.values()
                    if s["status"] == "active"
                )
                
                if active_count > 0:
                    logger.debug(f"📊 Streams actifs: {active_count}")
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Erreur monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_stream(self, stream_id: str, delay: int = 60):
        """Nettoyer un stream après délai"""
        await asyncio.sleep(delay)
        
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
            logger.debug(f"🧹 Stream {stream_id} nettoyé")
    
    def get_active_streams_count(self) -> int:
        """Nombre de streams actifs"""
        return sum(
            1 for s in self.active_streams.values()
            if s["status"] == "active"
        )
    
    def get_stream_stats(self) -> Dict[str, Any]:
        """Statistiques des streams"""
        active_streams = [
            s for s in self.active_streams.values()
            if s["status"] == "active"
        ]
        
        completed_streams = [
            s for s in self.active_streams.values()
            if s["status"] == "completed"
        ]
        
        return {
            "active_count": len(active_streams),
            "completed_count": len(completed_streams),
            "total_chunks_sent": sum(
                s.get("chunks_sent", 0)
                for s in self.active_streams.values()
            ),
            "average_duration": np.mean([
                s.get("end_time", time.time()) - s["start_time"]
                for s in completed_streams
            ]) if completed_streams else 0
        }
    
    async def shutdown(self):
        """Arrêt propre du manager"""
        logger.info("🛑 Arrêt Stream Manager...")
        
        # Marquer tous les streams comme terminés
        for stream_id in self.active_streams:
            self.active_streams[stream_id]["status"] = "terminated"
        
        logger.info("✅ Stream Manager arrêté")