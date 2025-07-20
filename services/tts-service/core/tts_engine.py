"""
🎯 TTS Engine - Coqui.ai XTTS
Moteur de synthèse vocale avec modèles avancés
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
import os
import numpy as np
import torch
from TTS.api import TTS
import soundfile as sf
import io
import time

logger = logging.getLogger(__name__)

class TTSEngine:
    """
    Moteur TTS utilisant Coqui.ai XTTS
    Supporte multi-langues et clonage de voix
    """
    
    def __init__(
        self,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        device: str = "cpu",
        enable_anti_hallucination: bool = True
    ):
        self.model_name = model_name
        self.device = device
        self.enable_anti_hallucination = enable_anti_hallucination
        
        self.tts = None
        self.voices: Dict[str, Dict[str, Any]] = {}
        self.model_loaded = False
        
        # Configuration anti-hallucination
        self.hallucination_patterns = [
            "thank you for watching",
            "please subscribe",
            "don't forget to",
            "in the next video",
            "merci d'avoir regardé",
            "n'oubliez pas de"
        ]
        
        logger.info(f"🎯 TTS Engine initialisé: {model_name} sur {device}")
    
    async def initialize(self):
        """Initialisation asynchrone du moteur TTS"""
        try:
            # Charger le modèle TTS
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._load_model
            )
            
            # Charger les voix par défaut
            self._load_default_voices()
            
            self.model_loaded = True
            logger.info("✅ Modèle TTS chargé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle TTS: {e}")
            raise
    
    def _load_model(self):
        """Charger le modèle TTS (opération bloquante)"""
        # Accepter les conditions d'utilisation automatiquement
        os.environ["COQUI_TOS_AGREED"] = "1"
        self.tts = TTS(self.model_name, progress_bar=False).to(self.device)
        
    def _load_default_voices(self):
        """Charger les voix par défaut"""
        self.voices = {
            "default": {
                "name": "Voix par défaut",
                "language": "fr",
                "gender": "neutral",
                "description": "Voix synthétique française standard"
            },
            "french_male": {
                "name": "Homme français",
                "language": "fr",
                "gender": "male",
                "description": "Voix masculine française"
            },
            "french_female": {
                "name": "Femme française", 
                "language": "fr",
                "gender": "female",
                "description": "Voix féminine française"
            },
            "english_male": {
                "name": "English Male",
                "language": "en",
                "gender": "male",
                "description": "Male English voice"
            },
            "english_female": {
                "name": "English Female",
                "language": "en", 
                "gender": "female",
                "description": "Female English voice"
            }
        }
    
    async def synthesize(
        self,
        text: str,
        voice_id: str = "default",
        language: str = "fr",
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> bytes:
        """
        Synthétiser du texte en audio
        
        Args:
            text: Texte à synthétiser
            voice_id: ID de la voix à utiliser
            language: Langue du texte
            speed: Vitesse de parole (0.5-2.0)
            pitch: Hauteur de voix (0.5-2.0)
            
        Returns:
            bytes: Audio WAV en bytes
        """
        if not self.model_loaded:
            raise RuntimeError("Modèle TTS non chargé")
        
        try:
            # Anti-hallucination
            if self.enable_anti_hallucination:
                text = self._remove_hallucinations(text)
            
            # Synthèse dans un thread séparé
            audio_array = await asyncio.get_event_loop().run_in_executor(
                None,
                self._synthesize_sync,
                text,
                voice_id,
                language,
                speed
            )
            
            # Post-traitement pitch si nécessaire
            if pitch != 1.0:
                audio_array = self._adjust_pitch(audio_array, pitch)
            
            # Convertir en WAV bytes
            audio_bytes = self._array_to_wav_bytes(audio_array)
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"❌ Erreur synthèse TTS: {e}")
            raise
    
    def _synthesize_sync(
        self,
        text: str,
        voice_id: str,
        language: str,
        speed: float
    ) -> np.ndarray:
        """Synthèse synchrone (pour thread executor)"""
        # Paramètres selon la voix
        voice_config = self.voices.get(voice_id, self.voices["default"])
        
        # Synthétiser avec Coqui
        wav = self.tts.tts(
            text=text,
            language=language,
            speed=speed
        )
        
        # Convertir en numpy array
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        elif isinstance(wav, list):
            wav = np.array(wav)
            
        return wav
    
    def _remove_hallucinations(self, text: str) -> str:
        """Retirer les patterns d'hallucination connus"""
        clean_text = text
        
        for pattern in self.hallucination_patterns:
            if pattern.lower() in clean_text.lower():
                logger.warning(f"⚠️ Pattern d'hallucination détecté: {pattern}")
                clean_text = clean_text.replace(pattern, "")
                clean_text = clean_text.replace(pattern.lower(), "")
                clean_text = clean_text.replace(pattern.upper(), "")
        
        return clean_text.strip()
    
    def _adjust_pitch(self, audio: np.ndarray, pitch_factor: float) -> np.ndarray:
        """Ajuster la hauteur de voix"""
        # Utiliser librosa pour le pitch shifting
        import librosa
        
        # Shift pitch
        shifted = librosa.effects.pitch_shift(
            audio,
            sr=self.tts.synthesizer.output_sample_rate,
            n_steps=int((pitch_factor - 1.0) * 12)  # Convertir en demi-tons
        )
        
        return shifted
    
    def _array_to_wav_bytes(self, audio_array: np.ndarray) -> bytes:
        """Convertir array numpy en bytes WAV"""
        buffer = io.BytesIO()
        
        # Normaliser l'audio
        audio_array = audio_array / np.max(np.abs(audio_array))
        
        # Écrire en WAV
        sf.write(
            buffer,
            audio_array,
            self.tts.synthesizer.output_sample_rate,
            format='WAV',
            subtype='PCM_16'
        )
        
        buffer.seek(0)
        return buffer.read()
    
    async def list_voices(self) -> List[Dict[str, Any]]:
        """Lister toutes les voix disponibles"""
        return [
            {
                "id": voice_id,
                **voice_data
            }
            for voice_id, voice_data in self.voices.items()
        ]
    
    async def clone_voice(
        self,
        name: str,
        audio_data: bytes,
        description: str = ""
    ) -> str:
        """
        Cloner une voix à partir d'un échantillon audio
        
        Args:
            name: Nom de la nouvelle voix
            audio_data: Données audio de référence
            description: Description de la voix
            
        Returns:
            str: ID de la nouvelle voix
        """
        try:
            # Générer ID unique
            voice_id = f"cloned_{name.lower().replace(' ', '_')}_{int(time.time())}"
            
            # Sauvegarder l'audio de référence
            ref_path = f"/app/models/voices/{voice_id}.wav"
            os.makedirs(os.path.dirname(ref_path), exist_ok=True)
            
            with open(ref_path, 'wb') as f:
                f.write(audio_data)
            
            # Enregistrer la voix
            self.voices[voice_id] = {
                "name": name,
                "language": "multilingual",
                "gender": "unknown",
                "description": description,
                "reference_audio": ref_path,
                "cloned": True
            }
            
            logger.info(f"✅ Voix clonée: {voice_id}")
            return voice_id
            
        except Exception as e:
            logger.error(f"❌ Erreur clonage voix: {e}")
            raise
    
    def is_model_loaded(self) -> bool:
        """Vérifier si le modèle est chargé"""
        return self.model_loaded
    
    async def shutdown(self):
        """Arrêt propre du moteur"""
        logger.info("🛑 Arrêt TTS Engine...")
        
        # Libérer la mémoire GPU si utilisée
        if self.tts and self.device != "cpu":
            torch.cuda.empty_cache()
        
        self.model_loaded = False
        logger.info("✅ TTS Engine arrêté")