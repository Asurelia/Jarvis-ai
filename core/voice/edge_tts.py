"""
Module de synthèse vocale avec Edge-TTS pour JARVIS
Text-to-Speech haute qualité avec voix naturelles Microsoft
"""
import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import io
from loguru import logger

# Imports conditionnels
try:
    import edge_tts
    import pygame
    EDGE_TTS_AVAILABLE = True
except ImportError as e:
    EDGE_TTS_AVAILABLE = False
    logger.warning(f"Modules TTS non disponibles: {e}")

@dataclass
class TTSConfig:
    """Configuration pour la synthèse vocale"""
    voice: str = "fr-FR-DeniseNeural"  # Voix féminine française
    rate: str = "+0%"  # Vitesse normale
    pitch: str = "+0Hz"  # Ton normal
    volume: str = "+0%"  # Volume normal
    output_format: str = "audio-24khz-48kbitrate-mono-mp3"

@dataclass
class SynthesisResult:
    """Résultat d'une synthèse vocale"""
    text: str
    audio_data: bytes
    voice_used: str
    synthesis_time: float
    audio_duration: float
    success: bool = True
    error: Optional[str] = None
    
    def save_to_file(self, filepath: str) -> bool:
        """Sauvegarde l'audio dans un fichier"""
        try:
            with open(filepath, 'wb') as f:
                f.write(self.audio_data)
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde audio: {e}")
            return False

class VoiceManager:
    """Gestionnaire des voix disponibles"""
    
    # Voix recommandées par langue
    RECOMMENDED_VOICES = {
        "fr": {
            "female": ["fr-FR-DeniseNeural", "fr-FR-EloiseNeural", "fr-FR-JosephineNeural"],
            "male": ["fr-FR-HenriNeural", "fr-FR-JeromeNeural", "fr-FR-MauriceNeural"]
        },
        "en": {
            "female": ["en-US-AriaNeural", "en-US-JennyNeural", "en-US-MichelleNeural"],
            "male": ["en-US-GuyNeural", "en-US-TonyNeural", "en-US-JacobNeural"]
        },
        "es": {
            "female": ["es-ES-ElviraNeural", "es-ES-AbrilNeural"],
            "male": ["es-ES-AlvaroNeural", "es-ES-ArnauNeural"]
        }
    }
    
    def __init__(self):
        self.available_voices: List[Dict[str, str]] = []
        self.voices_loaded = False
    
    async def load_available_voices(self):
        """Charge la liste des voix disponibles"""
        if not EDGE_TTS_AVAILABLE:
            return
        
        try:
            logger.info("🔄 Chargement des voix disponibles...")
            
            voices = await edge_tts.list_voices()
            self.available_voices = []
            
            for voice in voices:
                voice_info = {
                    "name": voice["Name"],
                    "short_name": voice["ShortName"],
                    "gender": voice["Gender"],
                    "locale": voice["Locale"],
                    "language": voice["Locale"][:2],
                    "display_name": voice["FriendlyName"]
                }
                self.available_voices.append(voice_info)
            
            self.voices_loaded = True
            logger.success(f"✅ {len(self.available_voices)} voix chargées")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement voix: {e}")
    
    def get_voices_by_language(self, language: str) -> List[Dict[str, str]]:
        """Retourne les voix pour une langue"""
        return [v for v in self.available_voices if v["language"] == language.lower()]
    
    def get_recommended_voice(self, language: str = "fr", gender: str = "female") -> str:
        """Retourne une voix recommandée"""
        if language in self.RECOMMENDED_VOICES:
            voices = self.RECOMMENDED_VOICES[language].get(gender, [])
            if voices:
                return voices[0]
        
        # Fallback
        return "fr-FR-DeniseNeural"
    
    def find_voice_by_name(self, name: str) -> Optional[Dict[str, str]]:
        """Trouve une voix par son nom"""
        name_lower = name.lower()
        
        for voice in self.available_voices:
            if (name_lower in voice["name"].lower() or 
                name_lower in voice["short_name"].lower() or
                name_lower in voice["display_name"].lower()):
                return voice
        
        return None

class AudioPlayer:
    """Lecteur audio pour la synthèse vocale"""
    
    def __init__(self):
        self.pygame_initialized = False
        self.is_playing = False
    
    def initialize(self):
        """Initialise pygame pour la lecture audio"""
        if not self.pygame_initialized:
            try:
                pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=1024)
                self.pygame_initialized = True
                logger.debug("🔊 Lecteur audio initialisé")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation audio: {e}")
                return False
        return True
    
    async def play_audio_data(self, audio_data: bytes) -> bool:
        """Joue des données audio"""
        if not self.initialize():
            return False
        
        try:
            # Créer un objet Sound depuis les données
            audio_buffer = io.BytesIO(audio_data)
            sound = pygame.mixer.Sound(audio_buffer)
            
            # Jouer le son
            self.is_playing = True
            channel = sound.play()
            
            # Attendre la fin de la lecture
            while channel.get_busy():
                await asyncio.sleep(0.1)
            
            self.is_playing = False
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture audio: {e}")
            self.is_playing = False
            return False
    
    def stop_playback(self):
        """Arrête la lecture audio"""
        if self.pygame_initialized:
            pygame.mixer.stop()
            self.is_playing = False

class EdgeTTS:
    """Service de synthèse vocale Edge-TTS"""
    
    def __init__(self, config: TTSConfig = None):
        self.config = config or TTSConfig()
        self.voice_manager = VoiceManager()
        self.audio_player = AudioPlayer()
        self.stats = {
            "syntheses_total": 0,
            "syntheses_success": 0,
            "total_synthesis_time": 0.0,
            "total_audio_duration": 0.0,
            "total_characters": 0
        }
        
        logger.info("🗣️ Module Edge-TTS initialisé")
    
    async def initialize(self):
        """Initialise Edge-TTS"""
        if not EDGE_TTS_AVAILABLE:
            logger.error("❌ Edge-TTS non disponible")
            return False
        
        try:
            # Charger les voix disponibles
            await self.voice_manager.load_available_voices()
            
            # Initialiser le lecteur audio
            self.audio_player.initialize()
            
            logger.success("✅ Edge-TTS prêt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Edge-TTS: {e}")
            return False
    
    async def synthesize_text(self, text: str, voice: str = None) -> SynthesisResult:
        """Synthétise du texte en audio"""
        if not text or not text.strip():
            return SynthesisResult(
                text="", audio_data=b"", voice_used="", synthesis_time=0.0,
                audio_duration=0.0, success=False, error="Texte vide"
            )
        
        voice = voice or self.config.voice
        start_time = time.time()
        self.stats["syntheses_total"] += 1
        self.stats["total_characters"] += len(text)
        
        try:
            logger.debug(f"🗣️ Synthèse: '{text[:50]}...' avec {voice}")
            
            # Créer le communicateur Edge-TTS
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=self.config.rate,
                pitch=self.config.pitch,
                volume=self.config.volume
            )
            
            # Synthétiser l'audio
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            synthesis_time = time.time() - start_time
            
            # Estimer la durée audio (approximation)
            # MP3 à 48kbps: ~6KB par seconde
            estimated_duration = len(audio_data) / (48000 // 8)  # Approximation
            
            # Mettre à jour les statistiques
            self.stats["syntheses_success"] += 1
            self.stats["total_synthesis_time"] += synthesis_time
            self.stats["total_audio_duration"] += estimated_duration
            
            logger.debug(f"✅ Synthèse terminée en {synthesis_time:.2f}s ({len(audio_data)} bytes)")
            
            return SynthesisResult(
                text=text,
                audio_data=audio_data,
                voice_used=voice,
                synthesis_time=synthesis_time,
                audio_duration=estimated_duration,
                success=True
            )
            
        except Exception as e:
            synthesis_time = time.time() - start_time
            logger.error(f"❌ Erreur synthèse: {e}")
            
            return SynthesisResult(
                text=text, audio_data=b"", voice_used=voice,
                synthesis_time=synthesis_time, audio_duration=0.0,
                success=False, error=str(e)
            )
    
    async def speak_text(self, text: str, voice: str = None, play_audio: bool = True) -> SynthesisResult:
        """Synthétise et joue du texte"""
        result = await self.synthesize_text(text, voice)
        
        if result.success and play_audio and result.audio_data:
            try:
                logger.info(f"🔊 Lecture: '{text[:50]}...'")
                await self.audio_player.play_audio_data(result.audio_data)
            except Exception as e:
                logger.error(f"❌ Erreur lecture audio: {e}")
                result.error = f"Synthèse OK, erreur lecture: {e}"
        
        return result
    
    async def speak_long_text(self, text: str, voice: str = None, 
                            chunk_size: int = 200, pause_between: float = 0.5) -> List[SynthesisResult]:
        """Synthétise et joue un texte long par chunks"""
        # Découper le texte en phrases
        sentences = self._split_into_sentences(text, chunk_size)
        results = []
        
        logger.info(f"🗣️ Lecture de texte long ({len(sentences)} parties)")
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                logger.debug(f"🗣️ Partie {i+1}/{len(sentences)}")
                result = await self.speak_text(sentence, voice)
                results.append(result)
                
                # Pause entre les chunks
                if i < len(sentences) - 1 and pause_between > 0:
                    await asyncio.sleep(pause_between)
        
        return results
    
    def _split_into_sentences(self, text: str, max_length: int) -> List[str]:
        """Découpe un texte en phrases de longueur maximale"""
        if len(text) <= max_length:
            return [text]
        
        sentences = []
        current = ""
        
        # Découper par phrases (points, points d'exclamation, questions)
        import re
        sentence_endings = re.split(r'([.!?]+)', text)
        
        for i in range(0, len(sentence_endings), 2):
            sentence = sentence_endings[i]
            if i + 1 < len(sentence_endings):
                sentence += sentence_endings[i + 1]
            
            if len(current + sentence) <= max_length:
                current += sentence
            else:
                if current:
                    sentences.append(current.strip())
                current = sentence
        
        if current:
            sentences.append(current.strip())
        
        return sentences
    
    def set_voice(self, voice_name: str):
        """Change la voix par défaut"""
        # Vérifier si la voix existe
        voice_info = self.voice_manager.find_voice_by_name(voice_name)
        
        if voice_info:
            self.config.voice = voice_info["short_name"]
            logger.info(f"🗣️ Voix changée: {voice_info['display_name']}")
        else:
            logger.warning(f"⚠️ Voix '{voice_name}' non trouvée")
    
    def set_voice_parameters(self, rate: str = None, pitch: str = None, volume: str = None):
        """Modifie les paramètres de la voix"""
        if rate is not None:
            self.config.rate = rate
        if pitch is not None:
            self.config.pitch = pitch
        if volume is not None:
            self.config.volume = volume
        
        logger.info(f"🎛️ Paramètres voix: rate={self.config.rate}, pitch={self.config.pitch}, volume={self.config.volume}")
    
    def get_available_voices(self, language: str = None) -> List[Dict[str, str]]:
        """Retourne les voix disponibles"""
        if language:
            return self.voice_manager.get_voices_by_language(language)
        return self.voice_manager.available_voices
    
    def stop_speaking(self):
        """Arrête la lecture en cours"""
        self.audio_player.stop_playback()
        logger.info("⏹️ Lecture arrêtée")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du service"""
        stats = self.stats.copy()
        
        if stats["syntheses_success"] > 0:
            stats["success_rate"] = stats["syntheses_success"] / stats["syntheses_total"]
            stats["avg_synthesis_time"] = stats["total_synthesis_time"] / stats["syntheses_success"]
            stats["avg_audio_duration"] = stats["total_audio_duration"] / stats["syntheses_success"]
            stats["avg_characters_per_synthesis"] = stats["total_characters"] / stats["syntheses_success"]
        else:
            stats["success_rate"] = 0.0
            stats["avg_synthesis_time"] = 0.0
            stats["avg_audio_duration"] = 0.0
            stats["avg_characters_per_synthesis"] = 0.0
        
        stats["edge_tts_available"] = EDGE_TTS_AVAILABLE
        stats["current_voice"] = self.config.voice
        stats["available_voices_count"] = len(self.voice_manager.available_voices)
        
        return stats
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.stats = {
            "syntheses_total": 0,
            "syntheses_success": 0,
            "total_synthesis_time": 0.0,
            "total_audio_duration": 0.0,
            "total_characters": 0
        }
        logger.info("📊 Statistiques Edge-TTS remises à zéro")

# Fonctions utilitaires
async def quick_speak(text: str, voice: str = None) -> bool:
    """Parle rapidement un texte"""
    tts = EdgeTTS()
    
    if not await tts.initialize():
        return False
    
    result = await tts.speak_text(text, voice)
    return result.success

async def save_speech_to_file(text: str, filepath: str, voice: str = None) -> bool:
    """Synthétise et sauvegarde dans un fichier"""
    tts = EdgeTTS()
    
    if not await tts.initialize():
        return False
    
    result = await tts.synthesize_text(text, voice)
    
    if result.success:
        return result.save_to_file(filepath)
    
    return False

if __name__ == "__main__":
    async def demo_edge_tts():
        tts = EdgeTTS()
        
        if not await tts.initialize():
            print("❌ Impossible d'initialiser Edge-TTS")
            return
        
        # Test de base
        print("🗣️ Demo Edge-TTS")
        
        test_text = "Bonjour, je suis JARVIS, votre assistant intelligent."
        
        result = await tts.speak_text(test_text)
        
        if result.success:
            print(f"✅ Synthèse réussie")
            print(f"🗣️ Voix: {result.voice_used}")
            print(f"⏱️ Temps de synthèse: {result.synthesis_time:.2f}s")
            print(f"🎵 Durée audio: {result.audio_duration:.2f}s")
        else:
            print(f"❌ Erreur: {result.error}")
        
        # Afficher les voix disponibles françaises
        french_voices = tts.get_available_voices("fr")
        print(f"\n🇫🇷 Voix françaises disponibles ({len(french_voices)}):")
        for voice in french_voices[:5]:  # Top 5
            print(f"  - {voice['display_name']} ({voice['gender']})")
        
        # Statistiques
        stats = tts.get_stats()
        print(f"\n📊 Statistiques:")
        print(f"- Synthèses: {stats['syntheses_total']}")
        print(f"- Taux de succès: {stats['success_rate']:.1%}")
        print(f"- Temps moyen: {stats['avg_synthesis_time']:.2f}s")
    
    asyncio.run(demo_edge_tts())