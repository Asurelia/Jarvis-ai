/**
 * 🎵 Hook personnalisé pour l'analyse audio temps réel
 * Analyse le microphone et les sons système pour la sphère 3D
 */
import { useState, useRef, useEffect, useCallback } from 'react';

export function useAudioAnalyzer({
  fftSize = 256,
  smoothingTimeConstant = 0.8,
  sensitivity = 1.0,
  onAudioLevel = null,
  onFrequencyData = null
}) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [frequencyData, setFrequencyData] = useState(null);
  const [hasPermission, setHasPermission] = useState(null);
  const [error, setError] = useState(null);

  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);
  const animationFrameRef = useRef(null);
  const dataArrayRef = useRef(null);

  // Initialiser l'analyse audio
  const startAnalyzing = useCallback(async () => {
    try {
      setError(null);
      
      // Demander l'accès au microphone
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: { ideal: 44100 },
          channelCount: { ideal: 1 }
        } 
      });

      // Créer le contexte audio
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);

      // Configuration de l'analyseur
      analyser.fftSize = fftSize;
      analyser.smoothingTimeConstant = smoothingTimeConstant;
      microphone.connect(analyser);

      // Stockage des références
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      streamRef.current = stream;

      // Buffer pour les données de fréquence
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      dataArrayRef.current = dataArray;

      setHasPermission(true);
      setIsAnalyzing(true);

      console.log('🎵 Analyse audio démarrée:', {
        fftSize,
        bufferLength,
        sampleRate: audioContext.sampleRate
      });

    } catch (err) {
      console.error('Erreur accès microphone:', err);
      setError(err.message);
      setHasPermission(false);
    }
  }, [fftSize, smoothingTimeConstant]);

  // Arrêter l'analyse
  const stopAnalyzing = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    dataArrayRef.current = null;
    
    setIsAnalyzing(false);
    setAudioLevel(0);
    setFrequencyData(null);

    console.log('🔇 Analyse audio arrêtée');
  }, []);

  // Boucle d'analyse des données audio
  const analyzeAudio = useCallback(() => {
    if (!analyserRef.current || !dataArrayRef.current || !isAnalyzing) {
      return;
    }

    // Obtenir les données de fréquence
    analyserRef.current.getByteFrequencyData(dataArrayRef.current);
    
    // Calculer le niveau audio global (RMS)
    let sum = 0;
    for (let i = 0; i < dataArrayRef.current.length; i++) {
      sum += dataArrayRef.current[i] * dataArrayRef.current[i];
    }
    const rms = Math.sqrt(sum / dataArrayRef.current.length);
    const normalizedLevel = Math.min((rms / 255) * sensitivity, 1.0);

    // Analyse spectrale pour effets visuels avancés
    const spectralData = {
      bass: 0,      // 20-200 Hz
      mids: 0,      // 200-2000 Hz  
      treble: 0,    // 2000-20000 Hz
      overall: normalizedLevel
    };

    // Calcul des bandes de fréquence
    const nyquist = (audioContextRef.current?.sampleRate || 44100) / 2;
    const binWidth = nyquist / dataArrayRef.current.length;
    
    let bassSum = 0, bassCount = 0;
    let midsSum = 0, midsCount = 0;
    let trebleSum = 0, trebleCount = 0;

    for (let i = 0; i < dataArrayRef.current.length; i++) {
      const freq = i * binWidth;
      const amplitude = dataArrayRef.current[i] / 255;

      if (freq <= 200) {
        bassSum += amplitude;
        bassCount++;
      } else if (freq <= 2000) {
        midsSum += amplitude;
        midsCount++;
      } else {
        trebleSum += amplitude;
        trebleCount++;
      }
    }

    spectralData.bass = bassCount > 0 ? bassSum / bassCount : 0;
    spectralData.mids = midsCount > 0 ? midsSum / midsCount : 0;
    spectralData.treble = trebleCount > 0 ? trebleSum / trebleCount : 0;

    // Mise à jour des états
    setAudioLevel(normalizedLevel);
    setFrequencyData({
      raw: Array.from(dataArrayRef.current),
      spectral: spectralData,
      peak: Math.max(...dataArrayRef.current) / 255,
      timestamp: Date.now()
    });

    // Callbacks
    if (onAudioLevel) {
      onAudioLevel(normalizedLevel, spectralData);
    }
    if (onFrequencyData) {
      onFrequencyData(dataArrayRef.current, spectralData);
    }

    // Continuer l'analyse
    animationFrameRef.current = requestAnimationFrame(analyzeAudio);
  }, [isAnalyzing, sensitivity, onAudioLevel, onFrequencyData]);

  // Démarrer/arrêter l'analyse quand l'état change
  useEffect(() => {
    if (isAnalyzing && analyserRef.current) {
      analyzeAudio();
    }
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isAnalyzing, analyzeAudio]);

  // Nettoyage lors du démontage
  useEffect(() => {
    return () => {
      stopAnalyzing();
    };
  }, [stopAnalyzing]);

  // Utilitaires pour la visualisation
  const getVolumeLevel = useCallback(() => {
    if (audioLevel < 0.1) return 'silent';
    if (audioLevel < 0.3) return 'quiet';
    if (audioLevel < 0.6) return 'normal';
    if (audioLevel < 0.8) return 'loud';
    return 'very_loud';
  }, [audioLevel]);

  const getDominantFrequency = useCallback(() => {
    if (!frequencyData?.spectral) return null;
    
    const { bass, mids, treble } = frequencyData.spectral;
    const max = Math.max(bass, mids, treble);
    
    if (max === bass) return 'bass';
    if (max === mids) return 'mids';
    return 'treble';
  }, [frequencyData]);

  // Détecter la parole (heuristique simple)
  const isSpeechDetected = useCallback(() => {
    if (!frequencyData?.spectral) return false;
    
    const { bass, mids, treble } = frequencyData.spectral;
    
    // La parole a généralement plus d'énergie dans les médiums
    return mids > 0.2 && mids > bass * 1.5 && audioLevel > 0.15;
  }, [frequencyData, audioLevel]);

  return {
    // États
    isAnalyzing,
    audioLevel,
    frequencyData,
    hasPermission,
    error,
    
    // Contrôles
    startAnalyzing,
    stopAnalyzing,
    
    // Utilitaires
    getVolumeLevel,
    getDominantFrequency,
    isSpeechDetected,
    
    // Données en temps réel
    spectralData: frequencyData?.spectral || null,
    peak: frequencyData?.peak || 0
  };
}

// Hook spécialisé pour la sphère 3D
export function useSphereAudioReactive(sphereRef) {
  const [sphereAPI, setSphereAPI] = useState(null);
  
  const { 
    audioLevel, 
    spectralData, 
    isSpeechDetected, 
    startAnalyzing, 
    stopAnalyzing,
    isAnalyzing 
  } = useAudioAnalyzer({
    fftSize: 512,
    sensitivity: 2.0,
    onAudioLevel: (level, spectral) => {
      // Réagir en temps réel à l'audio
      if (sphereAPI) {
        sphereAPI.setGlow(level);
        
        // Pulse pour les pics audio
        if (level > 0.7) {
          sphereAPI.pulse(level, 300);
        }
      }
    }
  });

  // Connecter l'API de la sphère
  const connectSphere = useCallback((api) => {
    setSphereAPI(api);
  }, []);

  return {
    audioLevel,
    spectralData,
    isSpeechDetected,
    isAnalyzing,
    startAnalyzing,
    stopAnalyzing,
    connectSphere
  };
}

export default useAudioAnalyzer;