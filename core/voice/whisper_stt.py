"""
Module de reconnaissance vocale avec Whisper pour JARVIS
Speech-to-Text haute performance avec support multilingue
"""
import asyncio
import time
import io
import wave
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from loguru import logger

# Imports conditionnels
try:
    import whisper
    import speech_recognition as sr
    import pyaudio
    WHISPER_AVAILABLE = True
except ImportError as e:
    WHISPER_AVAILABLE = False
    logger.warning(f"Modules vocaux non disponibles: {e}")

@dataclass
class VoiceConfig:
    """Configuration pour la reconnaissance vocale"""
    model_name: str = "base"  # tiny, base, small, medium, large
    language: str = "fr"  # auto-détection si None
    energy_threshold: int = 300
    timeout: float = 5.0
    phrase_timeout: float = 1.0
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1

@dataclass
class TranscriptionResult:
    """Résultat d'une transcription"""
    text: str
    confidence: float
    language: str
    processing_time: float
    segments: List[Dict[str, Any]]
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "processing_time": self.processing_time,
            "segments": self.segments,
            "success": self.success,
            "error": self.error
        }

class AudioCapture:
    """Gestionnaire de capture audio"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.recognizer = None
        self.microphone = None
        self.is_listening = False
        self.audio_queue = asyncio.Queue()
        
        if WHISPER_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = config.energy_threshold
            self.recognizer.timeout = config.timeout
            self.recognizer.phrase_timeout = config.phrase_timeout
    
    async def initialize(self):
        """Initialise la capture audio"""
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Modules vocaux non disponibles")
        
        try:
            # Initialiser le microphone
            self.microphone = sr.Microphone(sample_rate=self.config.sample_rate)
            
            # Calibrer le bruit ambiant
            logger.info("🎤 Calibration du microphone...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.success(f"✅ Microphone calibré (seuil: {self.recognizer.energy_threshold})")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation microphone: {e}")
            raise
    
    async def listen_once(self) -> Optional[bytes]:
        """Écoute un seul énoncé"""
        if not self.recognizer or not self.microphone:
            return None
        
        try:
            logger.debug("👂 Écoute en cours...")
            
            # Écouter avec timeout
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source, 
                    timeout=self.config.timeout,
                    phrase_time_limit=10  # Maximum 10 secondes par phrase
                )
            
            logger.debug("🎵 Audio capturé")
            return audio.get_wav_data()
            
        except sr.WaitTimeoutError:
            logger.debug("⏱️ Timeout d'écoute")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur capture audio: {e}")
            return None
    
    async def start_continuous_listening(self, callback: Callable):
        """Démarre l'écoute continue avec callback"""
        if self.is_listening:
            logger.warning("⚠️ Écoute déjà en cours")
            return
        
        self.is_listening = True
        logger.info("🔄 Démarrage de l'écoute continue...")
        
        try:
            while self.is_listening:
                audio_data = await self.listen_once()
                if audio_data:
                    await callback(audio_data)
                
                # Petite pause pour éviter la surcharge CPU
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"❌ Erreur écoute continue: {e}")
        finally:
            self.is_listening = False
            logger.info("⏹️ Écoute continue arrêtée")
    
    def stop_listening(self):
        """Arrête l'écoute continue"""
        self.is_listening = False

class WhisperSTT:
    """Service de reconnaissance vocale Whisper"""
    
    def __init__(self, config: VoiceConfig = None):
        self.config = config or VoiceConfig()
        self.model = None
        self.audio_capture = AudioCapture(self.config)
        self.stats = {
            "transcriptions_total": 0,
            "transcriptions_success": 0,
            "total_processing_time": 0.0,
            "avg_confidence": 0.0
        }
        
        logger.info("🎤 Module Whisper STT initialisé")
    
    async def initialize(self):
        """Initialise Whisper et l'audio"""
        if not WHISPER_AVAILABLE:
            logger.error("❌ Whisper non disponible")
            return False
        
        try:
            # Charger le modèle Whisper
            logger.info(f"🔄 Chargement du modèle Whisper {self.config.model_name}...")
            self.model = whisper.load_model(self.config.model_name)
            logger.success(f"✅ Modèle Whisper {self.config.model_name} chargé")
            
            # Initialiser la capture audio
            await self.audio_capture.initialize()
            
            logger.success("✅ Whisper STT prêt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Whisper: {e}")
            return False
    
    async def transcribe_audio_data(self, audio_data: bytes) -> TranscriptionResult:
        """Transcrit des données audio"""
        if not self.model:
            return TranscriptionResult(
                text="", confidence=0.0, language="", processing_time=0.0,
                segments=[], success=False, error="Modèle non initialisé"
            )
        
        start_time = time.time()
        self.stats["transcriptions_total"] += 1
        
        try:
            # Convertir les données audio en fichier temporaire
            temp_audio_path = self._save_temp_audio(audio_data)
            
            # Transcription avec Whisper
            result = self.model.transcribe(
                str(temp_audio_path),
                language=self.config.language if self.config.language != "auto" else None,
                word_timestamps=True
            )
            
            # Nettoyer le fichier temporaire
            temp_audio_path.unlink()
            
            # Extraire les informations
            text = result["text"].strip()
            language = result["language"]
            segments = result.get("segments", [])
            
            # Calculer la confiance moyenne
            confidences = []
            for segment in segments:
                if "confidence" in segment:
                    confidences.append(segment["confidence"])
                elif "words" in segment:
                    word_confidences = [w.get("confidence", 0.5) for w in segment["words"] if "confidence" in w]
                    if word_confidences:
                        confidences.extend(word_confidences)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.7
            
            processing_time = time.time() - start_time
            
            # Mettre à jour les statistiques
            self.stats["transcriptions_success"] += 1
            self.stats["total_processing_time"] += processing_time
            self.stats["avg_confidence"] = (
                (self.stats["avg_confidence"] * (self.stats["transcriptions_success"] - 1) + avg_confidence) 
                / self.stats["transcriptions_success"]
            )
            
            logger.debug(f"🎤 Transcription: '{text}' ({avg_confidence:.2%} confiance)")
            
            return TranscriptionResult(
                text=text,
                confidence=avg_confidence,
                language=language,
                processing_time=processing_time,
                segments=segments,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Erreur transcription: {e}")
            
            return TranscriptionResult(
                text="", confidence=0.0, language="", processing_time=processing_time,
                segments=[], success=False, error=str(e)
            )
    
    def _save_temp_audio(self, audio_data: bytes) -> Path:
        """Sauvegarde temporaire des données audio"""
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        temp_path = temp_dir / f"temp_audio_{int(time.time() * 1000)}.wav"
        
        with open(temp_path, 'wb') as f:
            f.write(audio_data)
        
        return temp_path
    
    async def listen_and_transcribe(self) -> TranscriptionResult:
        """Écoute et transcrit un énoncé"""
        try:
            logger.info("👂 En écoute... Parlez maintenant")
            
            audio_data = await self.audio_capture.listen_once()
            if not audio_data:
                return TranscriptionResult(
                    text="", confidence=0.0, language="", processing_time=0.0,
                    segments=[], success=False, error="Aucun audio capturé"
                )
            
            logger.info("🔄 Transcription en cours...")
            result = await self.transcribe_audio_data(audio_data)
            
            if result.success and result.text:
                logger.success(f"✅ Transcrit: '{result.text}'")
            else:
                logger.warning("⚠️ Aucun texte détecté")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur écoute/transcription: {e}")
            return TranscriptionResult(
                text="", confidence=0.0, language="", processing_time=0.0,
                segments=[], success=False, error=str(e)
            )
    
    async def start_voice_activation(self, wake_word: str = "jarvis", 
                                   command_callback: Callable = None) -> None:
        """Démarre la détection de mot d'activation"""
        if not command_callback:
            logger.warning("⚠️ Aucun callback défini pour les commandes")
            return
        
        logger.info(f"🎤 Activation vocale démarrée (mot-clé: '{wake_word}')")
        
        async def audio_callback(audio_data: bytes):
            # Transcription rapide pour détecter le mot d'activation
            result = await self.transcribe_audio_data(audio_data)
            
            if result.success and wake_word.lower() in result.text.lower():
                logger.info(f"🔥 Mot d'activation détecté: '{wake_word}'")
                
                # Écouter la commande suivante
                logger.info("👂 En attente de votre commande...")
                command_result = await self.listen_and_transcribe()
                
                if command_result.success and command_result.text:
                    logger.info(f"📝 Commande reçue: '{command_result.text}'")
                    await command_callback(command_result.text, command_result)
                else:
                    logger.warning("⚠️ Commande non comprise")
        
        try:
            await self.audio_capture.start_continuous_listening(audio_callback)
        except KeyboardInterrupt:
            logger.info("⏹️ Activation vocale arrêtée par l'utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur activation vocale: {e}")
    
    def stop_voice_activation(self):
        """Arrête la détection vocale"""
        self.audio_capture.stop_listening()
        logger.info("⏹️ Activation vocale arrêtée")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du service"""
        stats = self.stats.copy()
        
        if stats["transcriptions_success"] > 0:
            stats["success_rate"] = stats["transcriptions_success"] / stats["transcriptions_total"]
            stats["avg_processing_time"] = stats["total_processing_time"] / stats["transcriptions_success"]
        else:
            stats["success_rate"] = 0.0
            stats["avg_processing_time"] = 0.0
        
        stats["whisper_available"] = WHISPER_AVAILABLE
        stats["model_name"] = self.config.model_name
        
        return stats
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.stats = {
            "transcriptions_total": 0,
            "transcriptions_success": 0,
            "total_processing_time": 0.0,
            "avg_confidence": 0.0
        }
        logger.info("📊 Statistiques Whisper remises à zéro")

# Fonctions utilitaires
async def quick_listen() -> str:
    """Écoute rapide et retourne le texte"""
    stt = WhisperSTT()
    
    if not await stt.initialize():
        return ""
    
    result = await stt.listen_and_transcribe()
    return result.text if result.success else ""

async def test_microphone() -> bool:
    """Test du microphone"""
    try:
        stt = WhisperSTT()
        
        if not await stt.initialize():
            return False
        
        logger.info("🎤 Test du microphone - dites quelque chose...")
        result = await stt.listen_and_transcribe()
        
        if result.success:
            logger.success(f"✅ Test réussi: '{result.text}'")
            return True
        else:
            logger.error(f"❌ Test échoué: {result.error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test microphone: {e}")
        return False

if __name__ == "__main__":
    async def demo_whisper():
        stt = WhisperSTT()
        
        if not await stt.initialize():
            print("❌ Impossible d'initialiser Whisper")
            return
        
        print("🎤 Demo Whisper STT - Parlez après le signal...")
        
        # Test d'écoute simple
        result = await stt.listen_and_transcribe()
        
        if result.success:
            print(f"✅ Transcription: '{result.text}'")
            print(f"📊 Confiance: {result.confidence:.2%}")
            print(f"🌍 Langue: {result.language}")
            print(f"⏱️ Temps: {result.processing_time:.2f}s")
        else:
            print(f"❌ Erreur: {result.error}")
        
        # Statistiques
        stats = stt.get_stats()
        print(f"\n📊 Statistiques:")
        print(f"- Transcriptions: {stats['transcriptions_total']}")
        print(f"- Taux de succès: {stats['success_rate']:.1%}")
        print(f"- Temps moyen: {stats['avg_processing_time']:.2f}s")
    
    asyncio.run(demo_whisper())