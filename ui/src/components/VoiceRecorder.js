/**
 * 🎤 JARVIS UI - Voice Recorder Component
 * Composant pour l'enregistrement vocal dans le navigateur web
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  IconButton,
  Typography,
  Chip,
  Alert,
  LinearProgress,
  Tooltip,
  Button
} from '@mui/material';
import {
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Stop as StopIcon,
  VolumeUp as VolumeIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';

function VoiceRecorder({ onTranscription, disabled = false }) {
  const { state, actions } = useJarvis();
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [hasPermission, setHasPermission] = useState(null);
  const [error, setError] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  // Vérifier les permissions microphone au chargement
  useEffect(() => {
    checkMicrophonePermission();
  }, []);

  // Nettoyer les ressources audio
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const checkMicrophonePermission = async () => {
    try {
      // D'abord essayer d'accéder directement au microphone pour déclencher la demande
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Test rapide pour vérifier la disponibilité
        try {
          const devices = await navigator.mediaDevices.enumerateDevices();
          const hasAudioInput = devices.some(device => device.kind === 'audioinput');
          
          if (!hasAudioInput) {
            setError('Aucun microphone détecté sur ce système');
            setHasPermission(false);
            return;
          }
          
          // Vérifier les permissions si l'API est disponible
          if (navigator.permissions) {
            const permission = await navigator.permissions.query({ name: 'microphone' });
            setHasPermission(permission.state === 'granted');
            
            permission.addEventListener('change', () => {
              setHasPermission(permission.state === 'granted');
              if (permission.state === 'granted') {
                setError(null);
                actions.addNotification('success', 'Microphone', 'Autorisation accordée');
              }
            });
          } else {
            // Si l'API permissions n'est pas disponible, on suppose qu'il faut demander
            setHasPermission(null);
          }
        } catch (deviceError) {
          console.warn('Could not enumerate devices:', deviceError);
          setHasPermission(null);
        }
      } else {
        setError('Votre navigateur ne supporte pas l\'accès au microphone');
        setHasPermission(false);
      }
    } catch (error) {
      console.warn('Could not check microphone permission:', error);
      setHasPermission(null);
    }
  };

  const requestMicrophoneAccess = async () => {
    try {
      setError(null);
      actions.addLog('info', 'Demande d\'autorisation microphone...', 'ui');

      // Configuration audio optimisée pour Windows
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: { ideal: 16000 },
          channelCount: { ideal: 1 },
          volume: { ideal: 1.0 }
        }
      };

      // Demander l'accès au microphone
      const stream = await navigator.mediaDevices.getUserMedia(constraints);

      // Vérifier que le stream est valide
      if (!stream || !stream.active || stream.getAudioTracks().length === 0) {
        throw new Error('Stream microphone invalide');
      }

      const audioTrack = stream.getAudioTracks()[0];
      
      // Log des informations du microphone
      actions.addLog('info', `Microphone: ${audioTrack.label || 'Dispositif par défaut'}`, 'ui');
      
      // Vérifier les capacités du microphone
      const capabilities = audioTrack.getCapabilities ? audioTrack.getCapabilities() : {};
      if (capabilities.sampleRate) {
        actions.addLog('info', `Fréquence d'échantillonnage: ${capabilities.sampleRate.min}-${capabilities.sampleRate.max} Hz`, 'ui');
      }

      streamRef.current = stream;
      setHasPermission(true);
      setupAudioAnalyzer(stream);
      
      actions.addLog('success', 'Autorisation microphone accordée', 'ui');
      actions.addNotification('success', 'Microphone', `Accès autorisé: ${audioTrack.label || 'Microphone par défaut'}`);
      
      return stream;
    } catch (error) {
      setHasPermission(false);
      
      let errorMessage;
      let helpMessage = '';
      
      switch (error.name) {
        case 'NotAllowedError':
          errorMessage = 'Autorisation microphone refusée par l\'utilisateur';
          helpMessage = 'Cliquez sur l\'icône microphone dans la barre d\'adresse pour autoriser l\'accès';
          break;
        case 'NotFoundError':
          errorMessage = 'Aucun microphone trouvé sur ce système';
          helpMessage = 'Vérifiez qu\'un microphone est connecté et configuré dans Windows';
          break;
        case 'NotReadableError':
          errorMessage = 'Microphone utilisé par une autre application';
          helpMessage = 'Fermez les autres applications utilisant le microphone';
          break;
        case 'OverconstrainedError':
          errorMessage = 'Configuration microphone non supportée';
          helpMessage = 'Votre microphone ne supporte pas les paramètres demandés';
          break;
        case 'SecurityError':
          errorMessage = 'Accès microphone bloqué par la sécurité du navigateur';
          helpMessage = 'Utilisez HTTPS ou localhost pour accéder au microphone';
          break;
        default:
          errorMessage = `Erreur microphone: ${error.message}`;
          helpMessage = 'Vérifiez les paramètres de votre navigateur et de Windows';
      }
      
      setError(`${errorMessage}. ${helpMessage}`);
      actions.addLog('error', errorMessage, 'ui');
      actions.addNotification('error', 'Microphone', errorMessage);
      
      throw error;
    }
  };

  const setupAudioAnalyzer = (stream) => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      microphone.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      // Démarrer l'analyse du niveau audio
      updateAudioLevel();
    } catch (error) {
      console.warn('Could not setup audio analyzer:', error);
    }
  };

  const updateAudioLevel = () => {
    if (!analyserRef.current) return;
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const checkLevel = () => {
      if (isRecording && analyserRef.current) {
        analyserRef.current.getByteFrequencyData(dataArray);
        
        // Calculer le niveau audio moyen
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(Math.min(100, (average / 255) * 100));
        
        requestAnimationFrame(checkLevel);
      } else {
        setAudioLevel(0);
      }
    };
    
    if (isRecording) {
      checkLevel();
    }
  };

  const startRecording = async () => {
    try {
      setError(null);
      setIsProcessing(false);

      // Demander l'accès au microphone si nécessaire
      let stream = streamRef.current;
      if (!stream || !hasPermission) {
        stream = await requestMicrophoneAccess();
      }

      // Configurer MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        await processRecording();
      };

      mediaRecorder.start(1000); // Enregistrer par chunks de 1s
      mediaRecorderRef.current = mediaRecorder;
      
      setIsRecording(true);
      updateAudioLevel();
      
      actions.addLog('info', 'Enregistrement vocal démarré', 'ui');
      actions.addNotification('info', 'Enregistrement', 'Parlez maintenant...');

    } catch (error) {
      setError(`Impossible de démarrer l'enregistrement: ${error.message}`);
      actions.addLog('error', `Enregistrement échoué: ${error.message}`, 'ui');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
      
      actions.addLog('info', 'Arrêt de l\'enregistrement...', 'ui');
    }
  };

  const processRecording = async () => {
    try {
      if (chunksRef.current.length === 0) {
        throw new Error('Aucun audio enregistré');
      }

      // Créer un blob audio
      const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm;codecs=opus' });
      
      // Convertir en base64 pour l'envoi à l'API
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const base64Audio = reader.result.split(',')[1];
          
          actions.addLog('info', 'Transcription en cours...', 'ui');
          
          // Envoyer à l'API JARVIS pour transcription
          const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/voice/transcribe`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              audio_data: base64Audio,
              format: 'webm'
            })
          });

          if (!response.ok) {
            throw new Error(`Erreur API: ${response.status}`);
          }

          const result = await response.json();
          
          if (result.success && result.transcription) {
            actions.addLog('success', `Transcription: "${result.transcription}"`, 'voice');
            actions.addNotification('success', 'Transcription', result.transcription);
            
            // Appeler le callback avec la transcription
            if (onTranscription) {
              onTranscription(result.transcription);
            }
            
            // Incrémenter les stats
            actions.incrementStat('voiceCommands');
          } else {
            throw new Error('Transcription échouée');
          }

        } catch (error) {
          setError(`Transcription échouée: ${error.message}`);
          actions.addLog('error', `Transcription échouée: ${error.message}`, 'voice');
          actions.addNotification('error', 'Transcription', error.message);
        } finally {
          setIsProcessing(false);
        }
      };
      
      reader.readAsDataURL(audioBlob);

    } catch (error) {
      setError(`Traitement audio échoué: ${error.message}`);
      actions.addLog('error', `Traitement audio échoué: ${error.message}`, 'voice');
      setIsProcessing(false);
    }
  };

  const handleToggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const getStatusColor = () => {
    if (error) return 'error';
    if (isRecording) return 'success';
    if (isProcessing) return 'warning';
    if (hasPermission) return 'primary';
    return 'default';
  };

  const getStatusText = () => {
    if (error) return 'Erreur';
    if (isRecording) return 'Enregistrement...';
    if (isProcessing) return 'Traitement...';
    if (hasPermission === false) return 'Accès refusé';
    if (hasPermission === null) return 'Vérification...';
    return 'Prêt';
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
      {/* Bouton principal d'enregistrement */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Tooltip title={isRecording ? 'Arrêter l\'enregistrement' : 'Démarrer l\'enregistrement'}>
          <IconButton
            onClick={handleToggleRecording}
            disabled={disabled || isProcessing || (hasPermission === false)}
            sx={{
              width: 56,
              height: 56,
              backgroundColor: isRecording ? 'error.main' : 'primary.main',
              color: 'white',
              '&:hover': {
                backgroundColor: isRecording ? 'error.dark' : 'primary.dark',
              },
              '&:disabled': {
                backgroundColor: 'grey.300',
                color: 'grey.500',
              }
            }}
          >
            {isRecording ? <StopIcon /> : <MicIcon />}
          </IconButton>
        </Tooltip>

        {/* Indicateur de niveau audio */}
        {isRecording && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <VolumeIcon color="primary" />
            <Box sx={{ width: 100 }}>
              <LinearProgress 
                variant="determinate" 
                value={audioLevel} 
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
            <Typography variant="caption" color="text.secondary">
              {Math.round(audioLevel)}%
            </Typography>
          </Box>
        )}
      </Box>

      {/* Statut */}
      <Chip
        label={getStatusText()}
        color={getStatusColor()}
        size="small"
        icon={
          isRecording ? <MicIcon /> : 
          isProcessing ? <VolumeIcon /> : 
          hasPermission ? <MicIcon /> : <MicOffIcon />
        }
      />

      {/* Barre de progression pour le traitement */}
      {isProcessing && (
        <Box sx={{ width: '100%', maxWidth: 300 }}>
          <LinearProgress />
          <Typography variant="caption" color="text.secondary" align="center" sx={{ mt: 1 }}>
            Transcription en cours...
          </Typography>
        </Box>
      )}

      {/* Messages d'erreur */}
      {error && (
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          {error}
          {hasPermission === false && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption">
                Veuillez autoriser l'accès au microphone dans les paramètres de votre navigateur.
              </Typography>
            </Box>
          )}
        </Alert>
      )}

      {/* Instructions et bouton de test */}
      {!error && hasPermission === null && (
        <Box sx={{ textAlign: 'center', maxWidth: 300 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
            Cliquez sur "Tester le microphone" pour vérifier l'accès
          </Typography>
          <Button
            variant="outlined"
            size="small"
            onClick={requestMicrophoneAccess}
            startIcon={<MicIcon />}
            disabled={disabled}
          >
            Tester le microphone
          </Button>
        </Box>
      )}
      
      {!error && hasPermission && !isRecording && !isProcessing && (
        <Typography variant="caption" color="text.secondary" align="center" sx={{ maxWidth: 300 }}>
          ✅ Microphone prêt ! Cliquez sur le bouton pour enregistrer.
          Dites "Jarvis" suivi de votre commande.
        </Typography>
      )}
      
      {!error && hasPermission === false && (
        <Box sx={{ textAlign: 'center', maxWidth: 300 }}>
          <Typography variant="caption" color="error" sx={{ mb: 1, display: 'block' }}>
            ❌ Accès microphone refusé
          </Typography>
          <Button
            variant="contained"
            size="small"
            onClick={requestMicrophoneAccess}
            startIcon={<MicIcon />}
            color="primary"
          >
            Autoriser le microphone
          </Button>
        </Box>
      )}
    </Box>
  );
}

export default VoiceRecorder; 