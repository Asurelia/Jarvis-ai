"""
🎵 Audio Processor - TTS Service
Traitement et optimisation audio post-synthèse
"""

import asyncio
import logging
from typing import Optional, Tuple, Union, Dict, Any
import numpy as np
import scipy.signal
import librosa
import soundfile as sf
import io

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Processeur audio pour optimisation post-TTS
    - Normalisation
    - Suppression silence
    - Filtrage
    - Conversion formats
    """
    
    def __init__(
        self,
        sample_rate: int = 22050,
        channels: int = 1,
        chunk_size: int = 1024
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        
        # Paramètres de traitement
        self.silence_threshold = 0.01
        self.pre_emphasis = 0.97
        
        logger.info(f"🎵 Audio Processor initialisé: {sample_rate}Hz, {channels}ch")
    
    async def initialize(self):
        """Initialisation asynchrone"""
        logger.info("🚀 Initialisation Audio Processor...")
        await asyncio.sleep(0.1)  # Simulation init
        logger.info("✅ Audio Processor prêt")
    
    async def process(
        self,
        audio_data: Union[bytes, np.ndarray],
        normalize: bool = True,
        remove_silence: bool = True,
        apply_filters: bool = True
    ) -> bytes:
        """
        Traiter l'audio avec différentes optimisations
        
        Args:
            audio_data: Audio brut (bytes ou numpy array)
            normalize: Normaliser le volume
            remove_silence: Supprimer les silences
            apply_filters: Appliquer filtres audio
            
        Returns:
            bytes: Audio traité en WAV
        """
        try:
            # Convertir en numpy array si nécessaire
            if isinstance(audio_data, bytes):
                audio_array = self._bytes_to_array(audio_data)
            else:
                audio_array = audio_data.copy()
            
            # Traitement dans un thread
            processed = await asyncio.get_event_loop().run_in_executor(
                None,
                self._process_sync,
                audio_array,
                normalize,
                remove_silence,
                apply_filters
            )
            
            # Convertir en bytes WAV
            return self._array_to_wav_bytes(processed)
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement audio: {e}")
            raise
    
    def _process_sync(
        self,
        audio: np.ndarray,
        normalize: bool,
        remove_silence: bool,
        apply_filters: bool
    ) -> np.ndarray:
        """Traitement synchrone (pour thread executor)"""
        
        # 1. Pre-emphasis
        if apply_filters:
            audio = self._apply_pre_emphasis(audio)
        
        # 2. Suppression silence
        if remove_silence:
            audio = self._remove_silence(audio)
        
        # 3. Filtrage
        if apply_filters:
            audio = self._apply_filters(audio)
        
        # 4. Normalisation
        if normalize:
            audio = self._normalize(audio)
        
        return audio
    
    def _apply_pre_emphasis(self, audio: np.ndarray) -> np.ndarray:
        """Appliquer filtre de pré-emphasis"""
        return np.append(audio[0], audio[1:] - self.pre_emphasis * audio[:-1])
    
    def _remove_silence(self, audio: np.ndarray) -> np.ndarray:
        """Supprimer les parties silencieuses"""
        # Calculer l'énergie
        energy = librosa.feature.rms(y=audio, frame_length=self.chunk_size)[0]
        
        # Trouver indices non-silence
        non_silent = energy > self.silence_threshold
        
        # Indices temporels
        indices = librosa.frames_to_samples(
            np.nonzero(non_silent)[0],
            hop_length=self.chunk_size // 2
        )
        
        if len(indices) > 0:
            # Garder un peu de silence au début/fin
            start = max(0, indices[0] - self.chunk_size)
            end = min(len(audio), indices[-1] + self.chunk_size)
            return audio[start:end]
        
        return audio
    
    def _apply_filters(self, audio: np.ndarray) -> np.ndarray:
        """Appliquer filtres audio"""
        # Filtre passe-haut pour retirer les basses fréquences
        sos = scipy.signal.butter(
            4,  # Ordre
            80,  # Fréquence de coupure
            'hp',
            fs=self.sample_rate,
            output='sos'
        )
        audio = scipy.signal.sosfilt(sos, audio)
        
        # Filtre passe-bas pour adoucir
        sos = scipy.signal.butter(
            4,
            8000,  # Fréquence de coupure
            'lp',
            fs=self.sample_rate,
            output='sos'
        )
        audio = scipy.signal.sosfilt(sos, audio)
        
        return audio
    
    def _normalize(self, audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        """Normaliser le volume audio"""
        # Calculer RMS actuel
        rms = np.sqrt(np.mean(audio**2))
        
        if rms > 0:
            # Calculer gain nécessaire
            target_rms = 10**(target_db / 20)
            gain = target_rms / rms
            
            # Appliquer gain avec limitation
            audio = audio * gain
            audio = np.clip(audio, -1.0, 1.0)
        
        return audio
    
    def _bytes_to_array(self, audio_bytes: bytes) -> np.ndarray:
        """Convertir bytes audio en numpy array"""
        buffer = io.BytesIO(audio_bytes)
        audio, _ = sf.read(buffer)
        return audio
    
    def _array_to_wav_bytes(self, audio_array: np.ndarray) -> bytes:
        """Convertir numpy array en bytes WAV"""
        buffer = io.BytesIO()
        
        sf.write(
            buffer,
            audio_array,
            self.sample_rate,
            format='WAV',
            subtype='PCM_16'
        )
        
        buffer.seek(0)
        return buffer.read()
    
    async def convert_format(
        self,
        audio_data: bytes,
        target_format: str = "mp3",
        bitrate: str = "128k"
    ) -> bytes:
        """
        Convertir l'audio dans un autre format
        
        Args:
            audio_data: Audio source en WAV
            target_format: Format cible (mp3, ogg, etc.)
            bitrate: Bitrate pour formats compressés
            
        Returns:
            bytes: Audio converti
        """
        # TODO: Implémenter avec ffmpeg-python
        logger.warning(f"⚠️ Conversion {target_format} non implémentée")
        return audio_data
    
    def get_audio_info(self, audio_data: bytes) -> Dict[str, Any]:
        """Obtenir les informations d'un fichier audio"""
        try:
            buffer = io.BytesIO(audio_data)
            info = sf.info(buffer)
            
            return {
                "duration": info.duration,
                "sample_rate": info.samplerate,
                "channels": info.channels,
                "format": info.format,
                "subtype": info.subtype,
                "frames": info.frames
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur info audio: {e}")
            return {}
    
    async def shutdown(self):
        """Arrêt propre du processeur"""
        logger.info("🛑 Arrêt Audio Processor...")
        await asyncio.sleep(0.1)
        logger.info("✅ Audio Processor arrêté")

