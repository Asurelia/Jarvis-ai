"""
Interface vocale complète pour JARVIS
Combine Whisper STT et Edge-TTS pour une interaction naturelle
"""
import asyncio
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from loguru import logger

from .whisper_stt import WhisperSTT, VoiceConfig as STTConfig, TranscriptionResult
from .edge_tts import EdgeTTS, TTSConfig, SynthesisResult

@dataclass
class VoiceInterfaceConfig:
    """Configuration complète de l'interface vocale"""
    # Configuration STT
    stt_model: str = "base"
    stt_language: str = "fr"
    energy_threshold: int = 300
    wake_word: str = "jarvis"
    
    # Configuration TTS
    tts_voice: str = "fr-FR-DeniseNeural"
    tts_rate: str = "+0%"
    tts_pitch: str = "+0Hz"
    
    # Comportement
    confirmation_enabled: bool = True
    response_timeout: float = 10.0
    auto_listen_after_response: bool = True
    voice_feedback_enabled: bool = True

@dataclass
class VoiceInteraction:
    """Représente une interaction vocale complète"""
    user_input: str
    transcription_result: TranscriptionResult
    ai_response: str
    synthesis_result: Optional[SynthesisResult]
    interaction_time: float
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_input": self.user_input,
            "ai_response": self.ai_response,
            "transcription_confidence": self.transcription_result.confidence,
            "interaction_time": self.interaction_time,
            "success": self.success
        }

class VoiceInterface:
    """Interface vocale complète pour JARVIS"""
    
    def __init__(self, config: VoiceInterfaceConfig = None):
        self.config = config or VoiceInterfaceConfig()
        
        # Initialiser les modules
        stt_config = STTConfig(
            model_name=self.config.stt_model,
            language=self.config.stt_language,
            energy_threshold=self.config.energy_threshold
        )
        
        tts_config = TTSConfig(
            voice=self.config.tts_voice,
            rate=self.config.tts_rate,
            pitch=self.config.tts_pitch
        )
        
        self.stt = WhisperSTT(stt_config)
        self.tts = EdgeTTS(tts_config)
        
        # État de l'interface
        self.is_listening = False
        self.is_speaking = False
        self.is_active = False
        
        # Callbacks
        self.command_callback: Optional[Callable] = None
        self.conversation_callback: Optional[Callable] = None
        
        # Historique
        self.interaction_history: List[VoiceInteraction] = []
        
        # Statistiques
        self.stats = {
            "total_interactions": 0,
            "successful_interactions": 0,
            "avg_response_time": 0.0,
            "avg_confidence": 0.0
        }
        
        logger.info("🎤🗣️ Interface vocale JARVIS initialisée")
    
    async def initialize(self):
        """Initialise tous les composants vocaux"""
        try:
            logger.info("🚀 Initialisation de l'interface vocale...")
            
            # Initialiser STT
            logger.info("🎤 Initialisation de la reconnaissance vocale...")
            if not await self.stt.initialize():
                raise RuntimeError("Échec initialisation STT")
            
            # Initialiser TTS
            logger.info("🗣️ Initialisation de la synthèse vocale...")
            if not await self.tts.initialize():
                raise RuntimeError("Échec initialisation TTS")
            
            logger.success("✅ Interface vocale prête!")
            
            # Message de bienvenue
            if self.config.voice_feedback_enabled:
                await self.speak("Interface vocale JARVIS activée. Dites 'Jarvis' pour commencer.")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation interface vocale: {e}")
            return False
    
    async def speak(self, text: str, interrupt_current: bool = True) -> bool:
        """Fait parler JARVIS"""
        if not text or not text.strip():
            return False
        
        try:
            # Arrêter la parole en cours si demandé
            if interrupt_current and self.is_speaking:
                self.tts.stop_speaking()
            
            self.is_speaking = True
            logger.info(f"🗣️ JARVIS: {text}")
            
            result = await self.tts.speak_text(text)
            
            self.is_speaking = False
            return result.success
            
        except Exception as e:
            logger.error(f"❌ Erreur synthèse vocale: {e}")
            self.is_speaking = False
            return False
    
    async def listen_for_command(self) -> Optional[str]:
        """Écoute une commande utilisateur"""
        try:
            self.is_listening = True
            
            if self.config.voice_feedback_enabled:
                await self.speak("Je vous écoute.")
            
            logger.info("👂 En attente de votre commande...")
            
            result = await self.stt.listen_and_transcribe()
            
            self.is_listening = False
            
            if result.success and result.text:
                logger.success(f"📝 Commande reçue: '{result.text}'")
                return result.text
            else:
                if self.config.voice_feedback_enabled:
                    await self.speak("Je n'ai pas bien compris. Pouvez-vous répéter ?")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur écoute commande: {e}")
            self.is_listening = False
            return None
    
    async def process_voice_command(self, command: str) -> Optional[str]:
        """Traite une commande vocale et retourne la réponse"""
        if not self.command_callback:
            logger.warning("⚠️ Aucun callback de commande défini")
            return "Aucun système de traitement de commande configuré."
        
        try:
            # Traitement de la commande via callback
            response = await self.command_callback(command)
            
            if isinstance(response, dict):
                # Réponse structurée
                if response.get("success"):
                    return response.get("message", "Commande exécutée avec succès.")
                else:
                    return response.get("error", "Erreur lors de l'exécution de la commande.")
            
            elif isinstance(response, str):
                return response
            
            else:
                return "Commande traitée."
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement commande: {e}")
            return f"Erreur lors du traitement: {str(e)}"
    
    async def handle_conversation(self, user_input: str) -> VoiceInteraction:
        """Gère une interaction conversationnelle complète"""
        start_time = time.time()
        
        # Simuler la transcription (dans un vrai cas, on l'aurait déjà)
        transcription = TranscriptionResult(
            text=user_input,
            confidence=1.0,
            language="fr",
            processing_time=0.0,
            segments=[],
            success=True
        )
        
        try:
            # Traiter la commande
            ai_response = await self.process_voice_command(user_input)
            
            if not ai_response:
                ai_response = "Je n'ai pas pu traiter votre demande."
            
            # Synthèse vocale de la réponse
            synthesis_result = None
            if self.config.voice_feedback_enabled:
                synthesis_result = await self.tts.speak_text(ai_response)
            
            interaction_time = time.time() - start_time
            success = ai_response is not None
            
            # Créer l'interaction
            interaction = VoiceInteraction(
                user_input=user_input,
                transcription_result=transcription,
                ai_response=ai_response,
                synthesis_result=synthesis_result,
                interaction_time=interaction_time,
                success=success
            )
            
            # Ajouter à l'historique
            self.interaction_history.append(interaction)
            
            # Mettre à jour les statistiques
            self._update_stats(interaction)
            
            return interaction
            
        except Exception as e:
            logger.error(f"❌ Erreur conversation: {e}")
            
            return VoiceInteraction(
                user_input=user_input,
                transcription_result=transcription,
                ai_response=f"Erreur: {str(e)}",
                synthesis_result=None,
                interaction_time=time.time() - start_time,
                success=False
            )
    
    async def start_voice_activation(self):
        """Démarre l'écoute du mot d'activation"""
        if self.is_active:
            logger.warning("⚠️ Interface vocale déjà active")
            return
        
        self.is_active = True
        logger.info(f"🎤 Activation vocale démarrée (mot-clé: '{self.config.wake_word}')")
        
        if self.config.voice_feedback_enabled:
            await self.speak(f"Mode vocal activé. Dites '{self.config.wake_word}' pour me parler.")
        
        async def command_handler(command: str, transcription: TranscriptionResult):
            """Gestionnaire des commandes détectées"""
            try:
                # Enregistrer l'interaction
                interaction = await self.handle_conversation(command)
                
                # Feedback sur la qualité
                if transcription.confidence < 0.7:
                    await self.speak("J'ai eu du mal à vous comprendre. N'hésitez pas à répéter si nécessaire.")
                
                # Continuer l'écoute si configuré
                if self.config.auto_listen_after_response:
                    logger.debug("🔄 Retour en mode écoute automatique")
                
            except Exception as e:
                logger.error(f"❌ Erreur gestionnaire commande: {e}")
                if self.config.voice_feedback_enabled:
                    await self.speak("Une erreur s'est produite lors du traitement de votre commande.")
        
        try:
            # Démarrer l'écoute du mot d'activation
            await self.stt.start_voice_activation(self.config.wake_word, command_handler)
            
        except KeyboardInterrupt:
            logger.info("⏹️ Arrêt de l'activation vocale demandé")
        except Exception as e:
            logger.error(f"❌ Erreur activation vocale: {e}")
        finally:
            self.is_active = False
    
    def stop_voice_activation(self):
        """Arrête l'activation vocale"""
        self.stt.stop_voice_activation()
        self.is_active = False
        logger.info("⏹️ Activation vocale arrêtée")
    
    def set_command_callback(self, callback: Callable):
        """Définit le callback pour le traitement des commandes"""
        self.command_callback = callback
        logger.info("📞 Callback de commande configuré")
    
    def set_conversation_callback(self, callback: Callable):
        """Définit le callback pour les conversations"""
        self.conversation_callback = callback
        logger.info("💬 Callback de conversation configuré")
    
    def change_voice(self, voice_name: str):
        """Change la voix de JARVIS"""
        self.tts.set_voice(voice_name)
        logger.info(f"🗣️ Voix changée: {voice_name}")
    
    def adjust_voice_parameters(self, rate: str = None, pitch: str = None, volume: str = None):
        """Ajuste les paramètres de la voix"""
        self.tts.set_voice_parameters(rate, pitch, volume)
    
    def adjust_listening_sensitivity(self, energy_threshold: int):
        """Ajuste la sensibilité du microphone"""
        self.stt.audio_capture.recognizer.energy_threshold = energy_threshold
        self.config.energy_threshold = energy_threshold
        logger.info(f"🎤 Sensibilité microphone: {energy_threshold}")
    
    def _update_stats(self, interaction: VoiceInteraction):
        """Met à jour les statistiques"""
        self.stats["total_interactions"] += 1
        
        if interaction.success:
            self.stats["successful_interactions"] += 1
        
        # Temps de réponse moyen
        total_successful = self.stats["successful_interactions"]
        if total_successful > 0:
            old_avg = self.stats["avg_response_time"]
            self.stats["avg_response_time"] = (
                (old_avg * (total_successful - 1) + interaction.interaction_time) / total_successful
            )
        
        # Confiance moyenne
        if interaction.transcription_result.success:
            old_confidence = self.stats["avg_confidence"]
            self.stats["avg_confidence"] = (
                (old_confidence * (total_successful - 1) + interaction.transcription_result.confidence) / total_successful
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes"""
        stats = self.stats.copy()
        
        # Ajouter les stats des modules
        stt_stats = self.stt.get_stats()
        tts_stats = self.tts.get_stats()
        
        stats.update({
            "stt": stt_stats,
            "tts": tts_stats,
            "current_state": {
                "is_listening": self.is_listening,
                "is_speaking": self.is_speaking,
                "is_active": self.is_active
            },
            "config": {
                "wake_word": self.config.wake_word,
                "voice": self.config.tts_voice,
                "language": self.config.stt_language
            }
        })
        
        return stats
    
    def get_interaction_history(self, limit: int = 50) -> List[VoiceInteraction]:
        """Retourne l'historique des interactions"""
        return self.interaction_history[-limit:]
    
    def clear_history(self):
        """Efface l'historique des interactions"""
        self.interaction_history.clear()
        logger.info("🗑️ Historique vocal effacé")

# Fonctions utilitaires
async def quick_voice_test() -> bool:
    """Test rapide de l'interface vocale"""
    interface = VoiceInterface()
    
    if not await interface.initialize():
        return False
    
    # Test de parole
    await interface.speak("Test de l'interface vocale JARVIS.")
    
    # Test d'écoute
    logger.info("🎤 Dites quelque chose pour tester l'écoute...")
    command = await interface.listen_for_command()
    
    if command:
        await interface.speak(f"J'ai entendu: {command}")
        return True
    
    return False

if __name__ == "__main__":
    async def demo_voice_interface():
        # Callback de démonstration
        async def demo_command_callback(command: str) -> str:
            command_lower = command.lower()
            
            if "bonjour" in command_lower or "salut" in command_lower:
                return "Bonjour ! Comment puis-je vous aider ?"
            elif "ça va" in command_lower:
                return "Je vais très bien, merci ! Et vous ?"
            elif "merci" in command_lower:
                return "Je vous en prie, c'est un plaisir de vous aider."
            elif "au revoir" in command_lower or "bye" in command_lower:
                return "Au revoir ! À bientôt !"
            else:
                return f"Vous avez dit : {command}. Je traite votre demande."
        
        # Créer l'interface
        interface = VoiceInterface()
        
        if not await interface.initialize():
            print("❌ Impossible d'initialiser l'interface vocale")
            return
        
        # Configurer le callback
        interface.set_command_callback(demo_command_callback)
        
        print("🎤 Interface vocale de démonstration")
        print(f"Dites '{interface.config.wake_word}' puis votre commande")
        print("Ctrl+C pour arrêter")
        
        # Démarrer l'activation vocale
        await interface.start_voice_activation()
        
        # Statistiques finales
        stats = interface.get_stats()
        print(f"\n📊 Statistiques finales:")
        print(f"- Interactions: {stats['total_interactions']}")
        print(f"- Succès: {stats['successful_interactions']}")
        print(f"- Temps moyen: {stats['avg_response_time']:.2f}s")
    
    asyncio.run(demo_voice_interface())