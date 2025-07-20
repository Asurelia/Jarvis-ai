/**
 * 🎤 JARVIS UI - Microphone Test Component
 * Composant de diagnostic pour tester et configurer le microphone
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
  Alert,
  Divider
} from '@mui/material';
import {
  Mic as MicIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  VolumeUp as VolumeIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';

function MicrophoneTest() {
  const { actions } = useJarvis();
  const [devices, setDevices] = useState([]);
  const [permissions, setPermissions] = useState(null);
  const [testStream, setTestStream] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isTestingAudio, setIsTestingAudio] = useState(false);
  const [diagnostics, setDiagnostics] = useState([]);

  useEffect(() => {
    runDiagnostics();
    return () => {
      if (testStream) {
        testStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const runDiagnostics = async () => {
    const results = [];

    // Test 1: Vérifier la disponibilité de l'API
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      results.push({
        test: 'API MediaDevices',
        status: 'success',
        message: 'API disponible'
      });
    } else {
      results.push({
        test: 'API MediaDevices',
        status: 'error',
        message: 'API non supportée par ce navigateur'
      });
      setDiagnostics(results);
      return;
    }

    // Test 2: Énumérer les dispositifs
    try {
      const deviceList = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = deviceList.filter(device => device.kind === 'audioinput');
      
      setDevices(audioInputs);
      
      if (audioInputs.length > 0) {
        results.push({
          test: 'Dispositifs audio',
          status: 'success',
          message: `${audioInputs.length} microphone(s) détecté(s)`
        });
      } else {
        results.push({
          test: 'Dispositifs audio',
          status: 'error',
          message: 'Aucun microphone détecté'
        });
      }
    } catch (error) {
      results.push({
        test: 'Dispositifs audio',
        status: 'error',
        message: `Erreur énumération: ${error.message}`
      });
    }

    // Test 3: Vérifier les permissions
    try {
      if (navigator.permissions) {
        const permission = await navigator.permissions.query({ name: 'microphone' });
        setPermissions(permission.state);
        
        results.push({
          test: 'Permissions',
          status: permission.state === 'granted' ? 'success' : 'warning',
          message: `État: ${permission.state}`
        });
      } else {
        results.push({
          test: 'Permissions',
          status: 'warning',
          message: 'API Permissions non disponible'
        });
      }
    } catch (error) {
      results.push({
        test: 'Permissions',
        status: 'warning',
        message: 'Impossible de vérifier les permissions'
      });
    }

    // Test 4: Vérifier le contexte sécurisé
    if (window.location.protocol === 'https:' || window.location.hostname === 'localhost') {
      results.push({
        test: 'Contexte sécurisé',
        status: 'success',
        message: 'HTTPS ou localhost - OK'
      });
    } else {
      results.push({
        test: 'Contexte sécurisé',
        status: 'warning',
        message: 'HTTP non sécurisé - peut limiter l\'accès'
      });
    }

    setDiagnostics(results);
  };

  const testMicrophone = async () => {
    try {
      setIsTestingAudio(true);
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      setTestStream(stream);
      
      // Analyser le niveau audio
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      microphone.connect(analyser);
      
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const updateLevel = () => {
        if (isTestingAudio) {
          analyser.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(Math.min(100, (average / 255) * 100));
          requestAnimationFrame(updateLevel);
        }
      };
      
      updateLevel();
      
      actions.addNotification('success', 'Test microphone', 'Microphone testé avec succès');
      
      // Arrêter le test après 10 secondes
      setTimeout(() => {
        stopTest();
      }, 10000);
      
    } catch (error) {
      actions.addNotification('error', 'Test microphone', `Erreur: ${error.message}`);
      setIsTestingAudio(false);
    }
  };

  const stopTest = () => {
    if (testStream) {
      testStream.getTracks().forEach(track => track.stop());
      setTestStream(null);
    }
    setIsTestingAudio(false);
    setAudioLevel(0);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return <CheckIcon color="success" />;
      case 'warning': return <WarningIcon color="warning" />;
      case 'error': return <ErrorIcon color="error" />;
      default: return <SettingsIcon />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <MicIcon />
          Diagnostic Microphone
        </Typography>

        {/* Résultats des tests */}
        <List dense>
          {diagnostics.map((result, index) => (
            <ListItem key={index}>
              <ListItemIcon>
                {getStatusIcon(result.status)}
              </ListItemIcon>
              <ListItemText
                primary={result.test}
                secondary={result.message}
              />
              <Chip
                label={result.status}
                size="small"
                color={getStatusColor(result.status)}
              />
            </ListItem>
          ))}
        </List>

        <Divider sx={{ my: 2 }} />

        {/* Dispositifs détectés */}
        {devices.length > 0 && (
          <>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Microphones détectés :
            </Typography>
            <List dense>
              {devices.map((device, index) => (
                <ListItem key={device.deviceId || index}>
                  <ListItemIcon>
                    <MicIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={device.label || `Microphone ${index + 1}`}
                    secondary={`ID: ${device.deviceId.substring(0, 20)}...`}
                  />
                </ListItem>
              ))}
            </List>
            <Divider sx={{ my: 2 }} />
          </>
        )}

        {/* Test audio */}
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="subtitle2" sx={{ mb: 2 }}>
            Test du microphone
          </Typography>
          
          {isTestingAudio && (
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'center', mb: 1 }}>
                <VolumeIcon />
                <LinearProgress 
                  variant="determinate" 
                  value={audioLevel} 
                  sx={{ width: 200, height: 8, borderRadius: 4 }}
                />
                <Typography variant="caption">
                  {Math.round(audioLevel)}%
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Parlez dans le microphone pour voir le niveau audio
              </Typography>
            </Box>
          )}
          
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
            <Button
              variant="contained"
              onClick={testMicrophone}
              disabled={isTestingAudio || devices.length === 0}
              startIcon={<MicIcon />}
            >
              {isTestingAudio ? 'Test en cours...' : 'Tester le microphone'}
            </Button>
            
            {isTestingAudio && (
              <Button
                variant="outlined"
                onClick={stopTest}
              >
                Arrêter
              </Button>
            )}
          </Box>
        </Box>

        {/* Instructions */}
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Instructions :</strong><br />
            1. Autorisez l'accès au microphone dans votre navigateur<br />
            2. Vérifiez que votre microphone fonctionne dans Windows<br />
            3. Fermez les autres applications utilisant le microphone<br />
            4. Testez le microphone avec le bouton ci-dessus
          </Typography>
        </Alert>

        {/* Conseils Windows */}
        <Alert severity="warning" sx={{ mt: 1 }}>
          <Typography variant="body2">
            <strong>Windows :</strong> Si le microphone ne fonctionne pas, vérifiez dans 
            Paramètres → Confidentialité → Microphone que l'accès est autorisé pour les applications de bureau et votre navigateur.
          </Typography>
        </Alert>
      </CardContent>
    </Card>
  );
}

export default MicrophoneTest; 