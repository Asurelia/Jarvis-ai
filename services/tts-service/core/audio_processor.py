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
from scipy.signal import freqz

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
        apply_filters: bool = True,
        preset_effects: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Traiter l'audio avec différentes optimisations
        
        Args:
            audio_data: Audio brut (bytes ou numpy array)
            normalize: Normaliser le volume
            remove_silence: Supprimer les silences
            apply_filters: Appliquer filtres audio
            preset_effects: Configuration d'effets preset (Jarvis, etc.)
            
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
                apply_filters,
                preset_effects
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
        apply_filters: bool,
        preset_effects: Optional[Dict[str, Any]] = None
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
        
        # 4. Effets preset (Jarvis, etc.)
        if preset_effects:
            audio = self._apply_preset_effects(audio, preset_effects)
        
        # 5. Normalisation
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
    
    def _apply_preset_effects(self, audio: np.ndarray, effects_config: Dict[str, Any]) -> np.ndarray:
        """
        Appliquer les effets d'un preset (Jarvis, etc.)
        
        Args:
            audio: Signal audio
            effects_config: Configuration des effets
            
        Returns:
            np.ndarray: Audio avec effets appliqués
        """
        processed_audio = audio.copy()
        
        try:
            # 1. Égalisation
            if 'eq' in effects_config:
                processed_audio = self._apply_eq(processed_audio, effects_config['eq'])
            
            # 2. Compression
            if 'compression' in effects_config:
                processed_audio = self._apply_compression(processed_audio, effects_config['compression'])
            
            # 3. Effets spéciaux
            if 'fx' in effects_config:
                processed_audio = self._apply_special_fx(processed_audio, effects_config['fx'])
            
            # 4. Réverbération
            if 'reverb' in effects_config:
                processed_audio = self._apply_reverb(processed_audio, effects_config['reverb'])
            
        except Exception as e:
            logger.error(f"❌ Erreur application effets preset: {e}")
            return audio  # Retourner l'audio original en cas d'erreur
        
        return processed_audio
    
    def _apply_eq(self, audio: np.ndarray, eq_config: Dict[str, Any]) -> np.ndarray:
        """Appliquer égalisation 3 bandes (grave, médium, aigu)"""
        try:
            processed = audio.copy()
            
            # Filtre passe-bas pour graves
            low_freq = eq_config.get('low_freq', 80)
            low_gain = eq_config.get('low_gain', 0.0)
            if low_gain != 0:
                sos_low = scipy.signal.butter(4, low_freq * 2, 'lp', fs=self.sample_rate, output='sos')
                low_band = scipy.signal.sosfilt(sos_low, audio)
                gain_linear = 10**(low_gain / 20)
                processed += low_band * (gain_linear - 1)
            
            # Filtre passe-bande pour médiums
            mid_freq = eq_config.get('mid_freq', 1000)
            mid_gain = eq_config.get('mid_gain', 0.0)
            if mid_gain != 0:
                low_cut = mid_freq / 2
                high_cut = mid_freq * 2
                sos_mid = scipy.signal.butter(4, [low_cut, high_cut], 'bp', fs=self.sample_rate, output='sos')
                mid_band = scipy.signal.sosfilt(sos_mid, audio)
                gain_linear = 10**(mid_gain / 20)
                processed += mid_band * (gain_linear - 1)
            
            # Filtre passe-haut pour aigus
            high_freq = eq_config.get('high_freq', 8000)
            high_gain = eq_config.get('high_gain', 0.0)
            if high_gain != 0:
                sos_high = scipy.signal.butter(4, high_freq, 'hp', fs=self.sample_rate, output='sos')
                high_band = scipy.signal.sosfilt(sos_high, audio)
                gain_linear = 10**(high_gain / 20)
                processed += high_band * (gain_linear - 1)
            
            # Boost de présence
            presence_freq = eq_config.get('presence_freq', 4000)
            presence_gain = eq_config.get('presence_gain', 0.0)
            if presence_gain != 0:
                # Filtre en cloche pour la présence
                Q = 2.0  # Facteur de qualité
                w0 = 2 * np.pi * presence_freq / self.sample_rate
                alpha = np.sin(w0) / (2 * Q)
                A = 10**(presence_gain / 40)
                
                # Coefficients du filtre
                b0 = 1 + alpha * A
                b1 = -2 * np.cos(w0)
                b2 = 1 - alpha * A
                a0 = 1 + alpha / A
                a1 = -2 * np.cos(w0)
                a2 = 1 - alpha / A
                
                # Normaliser
                b = np.array([b0, b1, b2]) / a0
                a = np.array([1, a1, a2]) / a0
                
                processed = scipy.signal.lfilter(b, a, processed)
            
            return np.clip(processed, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Erreur EQ: {e}")
            return audio
    
    def _apply_compression(self, audio: np.ndarray, comp_config: Dict[str, Any]) -> np.ndarray:
        """Appliquer compression dynamique"""
        try:
            threshold = comp_config.get('threshold', -18.0)  # dB
            ratio = comp_config.get('ratio', 3.0)
            attack = comp_config.get('attack', 5.0)  # ms
            release = comp_config.get('release', 50.0)  # ms
            
            # Convertir en secondes
            attack_samples = int(attack * self.sample_rate / 1000)
            release_samples = int(release * self.sample_rate / 1000)
            
            # Seuil linéaire
            threshold_linear = 10**(threshold / 20)
            
            # Envelope follower
            envelope = np.abs(audio)
            
            # Lissage de l'envelope
            for i in range(1, len(envelope)):
                if envelope[i] > envelope[i-1]:
                    # Attaque
                    envelope[i] = envelope[i-1] + (envelope[i] - envelope[i-1]) / attack_samples
                else:
                    # Relâchement
                    envelope[i] = envelope[i-1] + (envelope[i] - envelope[i-1]) / release_samples
            
            # Calcul du gain de compression
            gain = np.ones_like(envelope)
            over_threshold = envelope > threshold_linear
            
            if np.any(over_threshold):
                # Gain de réduction pour les signaux au-dessus du seuil
                gain[over_threshold] = threshold_linear / envelope[over_threshold]
                gain[over_threshold] = gain[over_threshold] ** (1 - 1/ratio)
            
            return audio * gain
            
        except Exception as e:
            logger.error(f"❌ Erreur compression: {e}")
            return audio
    
    def _apply_special_fx(self, audio: np.ndarray, fx_config: Dict[str, Any]) -> np.ndarray:
        """Appliquer effets spéciaux (métallique, chorus, etc.)"""
        try:
            processed = audio.copy()
            
            # Filtre métallique
            metallic = fx_config.get('metallic_filter', {})
            if metallic.get('enabled', False):
                center_freq = metallic.get('center_freq', 2000)
                bandwidth = metallic.get('bandwidth', 1.5)
                gain = metallic.get('gain', 2.0)
                
                # Filtre résonant
                Q = center_freq / bandwidth
                w0 = 2 * np.pi * center_freq / self.sample_rate
                alpha = np.sin(w0) / (2 * Q)
                A = 10**(gain / 40)
                
                b0 = 1 + alpha * A
                b1 = -2 * np.cos(w0)
                b2 = 1 - alpha * A
                a0 = 1 + alpha / A
                a1 = -2 * np.cos(w0)
                a2 = 1 - alpha / A
                
                b = np.array([b0, b1, b2]) / a0
                a = np.array([1, a1, a2]) / a0
                
                processed = scipy.signal.lfilter(b, a, processed)
            
            # Enhancer harmonique
            harmonic = fx_config.get('harmonic_enhancer', {})
            if harmonic.get('enabled', False):
                intensity = harmonic.get('intensity', 0.3)
                harmonics = harmonic.get('harmonics', [2, 3])
                
                enhanced = processed.copy()
                for h in harmonics:
                    # Génération d'harmoniques par distorsion contrôlée
                    harmonic_content = np.tanh(processed * h) * intensity / h
                    enhanced += harmonic_content
                
                processed = enhanced
            
            # Chorus subtil
            chorus = fx_config.get('subtle_chorus', {})
            if chorus.get('enabled', False):
                rate = chorus.get('rate', 0.5)  # Hz
                depth = chorus.get('depth', 0.1)
                delay_ms = chorus.get('delay', 10)
                
                delay_samples = int(delay_ms * self.sample_rate / 1000)
                
                # LFO pour modulation
                lfo = np.sin(2 * np.pi * rate * np.arange(len(audio)) / self.sample_rate)
                
                # Appliquer chorus simple
                delayed = np.zeros_like(audio)
                if delay_samples < len(audio):
                    delayed[delay_samples:] = audio[:-delay_samples]
                
                # Modulation de la voix retardée
                modulated_delay = delayed * (1 + depth * lfo)
                processed = (processed + modulated_delay) * 0.5
            
            return np.clip(processed, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Erreur effets spéciaux: {e}")
            return audio
    
    def _apply_reverb(self, audio: np.ndarray, reverb_config: Dict[str, Any]) -> np.ndarray:
        """Appliquer réverbération (algorithme Freeverb simplifié)"""
        try:
            room_size = reverb_config.get('room_size', 0.7)
            damping = reverb_config.get('damping', 0.3)
            wet_level = reverb_config.get('wet_level', 0.25)
            dry_level = reverb_config.get('dry_level', 0.75)
            width = reverb_config.get('width', 0.8)
            
            # Réverbération simplifiée avec délais multiples
            delays = [int(0.03 * self.sample_rate), int(0.05 * self.sample_rate), 
                     int(0.07 * self.sample_rate), int(0.09 * self.sample_rate)]
            
            reverb_signal = np.zeros_like(audio)
            
            for delay in delays:
                if delay < len(audio):
                    # Signal retardé
                    delayed = np.zeros_like(audio)
                    delayed[delay:] = audio[:-delay]
                    
                    # Feedback avec amortissement
                    feedback = room_size * (1 - damping)
                    delayed = delayed * feedback
                    
                    reverb_signal += delayed
            
            # Mélange wet/dry
            processed = dry_level * audio + wet_level * reverb_signal
            
            return np.clip(processed, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Erreur réverbération: {e}")
            return audio
    
    async def shutdown(self):
        """Arrêt propre du processeur"""
        logger.info("🛑 Arrêt Audio Processor...")
        await asyncio.sleep(0.1)
        logger.info("✅ Audio Processor arrêté")

