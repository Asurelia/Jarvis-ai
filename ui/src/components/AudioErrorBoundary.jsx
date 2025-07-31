/**
 * 🎤 JARVIS Audio Error Boundary - Gestion des erreurs audio/voix
 * Error Boundary spécialisé pour les composants audio avec diagnostics avancés
 */
import React from 'react';
import { Box, Typography, Button, Alert, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { 
  VolumeOff as VolumeOffIcon, 
  Mic as MicIcon, 
  SettingsVoice as SettingsVoiceIcon,
  Refresh as RefreshIcon,
  Build as BuildIcon
} from '@mui/icons-material';
import ErrorBoundary from './ErrorBoundary';
import '../styles/jarvis-holographic.css';

class AudioErrorBoundary extends ErrorBoundary {
  constructor(props) {
    super(props);
    this.state = {
      ...this.state,
      audioPermissions: null,
      audioDevices: [],
      audioContext: null,
      diagnostics: {}
    };
  }

  async componentDidMount() {
    await this.checkAudioCapabilities();
  }

  checkAudioCapabilities = async () => {
    const diagnostics = {
      permissions: 'unknown',
      devices: 'unknown',
      context: 'unknown',
      webAudio: 'unknown',
      mediaRecorder: 'unknown',
      speechRecognition: 'unknown'
    };

    try {
      // Vérifier les permissions audio
      if (navigator.permissions) {
        try {
          const permission = await navigator.permissions.query({ name: 'microphone' });
          diagnostics.permissions = permission.state;
        } catch (e) {
          diagnostics.permissions = 'not_supported';
        }
      }

      // Vérifier les périphériques audio
      if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        try {
          const devices = await navigator.mediaDevices.enumerateDevices();
          const audioDevices = devices.filter(device => 
            device.kind === 'audioinput' || device.kind === 'audiooutput'
          );
          diagnostics.devices = `${audioDevices.length} devices found`;
          this.setState({ audioDevices });
        } catch (e) {
          diagnostics.devices = `error: ${e.message}`;
        }
      }

      // Vérifier Web Audio API
      try {
        const context = new (window.AudioContext || window.webkitAudioContext)();
        diagnostics.context = context.state || 'available';
        diagnostics.webAudio = 'supported';
        this.setState({ audioContext: context });
      } catch (e) {
        diagnostics.webAudio = `not_supported: ${e.message}`;
      }

      // Vérifier MediaRecorder
      if (window.MediaRecorder) {
        diagnostics.mediaRecorder = 'supported';
      } else {
        diagnostics.mediaRecorder = 'not_supported';
      }

      // Vérifier Speech Recognition
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        diagnostics.speechRecognition = 'supported';
      } else {
        diagnostics.speechRecognition = 'not_supported';
      }

    } catch (error) {
      console.warn('Audio diagnostics failed:', error);
    }

    this.setState({ diagnostics });
  };

  logError = (error, errorInfo) => {
    const audioErrorData = {
      ...this.createBaseErrorData(error, errorInfo),
      audioSpecific: {
        permissions: this.state.audioPermissions,
        devices: this.state.audioDevices.length,
        contextState: this.state.audioContext?.state,
        diagnostics: this.state.diagnostics,
        userMedia: navigator.mediaDevices ? 'available' : 'not_available',
        autoplay: this.checkAutoplayPolicy()
      }
    };

    console.error('🎤 JARVIS Audio Error:', audioErrorData);

    if (window.jarvisAPI?.logAudioError) {
      window.jarvisAPI.logAudioError(audioErrorData);
    }

    if (this.props.onError) {
      this.props.onError(audioErrorData);
    }
  };

  checkAutoplayPolicy = () => {
    try {
      // Tenter de détecter la politique d'autoplay
      if (navigator.getAutoplayPolicy) {
        return navigator.getAutoplayPolicy('mediaelement');
      }
      return 'unknown';
    } catch (e) {
      return 'not_supported';
    }
  };

  handleAudioRetry = async () => {
    try {
      // Réinitialiser le contexte audio
      if (this.state.audioContext) {
        await this.state.audioContext.close();
      }

      // Recréer le contexte audio
      const newContext = new (window.AudioContext || window.webkitAudioContext)();
      this.setState({ audioContext: newContext });

      // Redemander les permissions
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      // Retry normal
      this.handleRetry();
    } catch (error) {
      console.error('Audio retry failed:', error);
      this.setState({ 
        error: new Error(`Audio retry failed: ${error.message}`) 
      });
    }
  };

  requestPermissions = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop()); // Arrêter le stream de test
      this.setState({ audioPermissions: 'granted' });
      await this.checkAudioCapabilities();
    } catch (error) {
      this.setState({ audioPermissions: 'denied' });
      console.error('Audio permissions denied:', error);
    }
  };

  render() {
    if (this.state.hasError) {
      const { diagnostics } = this.state;

      return (
        <Box
          className="jarvis-panel"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px',
            maxWidth: '800px',
            margin: '0 auto',
            padding: '40px',
            textAlign: 'center',
            border: '2px solid #ff9500',
            boxShadow: '0 0 30px rgba(255, 149, 0, 0.3)'
          }}
        >
          {/* Icône audio avec effet */}
          <Box
            sx={{
              fontSize: '4rem',
              color: '#ff9500',
              textShadow: '0 0 20px #ff9500',
              animation: 'error-pulse 2s ease-in-out infinite',
              marginBottom: '20px'
            }}
          >
            🎤
          </Box>

          <Typography
            variant="h4"
            className="jarvis-text-glow"
            sx={{
              fontFamily: '"Orbitron", monospace',
              fontWeight: 'bold',
              color: '#ff9500',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '20px'
            }}
          >
            AUDIO SYSTEM FAILURE
          </Typography>

          <Typography
            variant="body1"
            sx={{
              fontFamily: '"Orbitron", monospace',
              color: '#00d4ff',
              marginBottom: '30px',
              maxWidth: '600px'
            }}
          >
            The JARVIS audio interface has encountered a critical error. 
            Audio processing, voice recognition, and speech synthesis may be affected.
          </Typography>

          {/* Diagnostics audio */}
          <Box
            sx={{
              width: '100%',
              maxWidth: '600px',
              marginBottom: '30px',
              textAlign: 'left'
            }}
          >
            <Typography
              variant="h6"
              sx={{
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '15px',
                textAlign: 'center'
              }}
            >
              🔍 AUDIO DIAGNOSTICS
            </Typography>

            <List dense>
              <ListItem>
                <ListItemIcon>
                  <MicIcon sx={{ color: diagnostics.permissions === 'granted' ? '#00ff88' : '#ff3b30' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Microphone Permissions"
                  secondary={`Status: ${diagnostics.permissions || 'checking...'}`}
                  sx={{
                    '& .MuiListItemText-primary': { 
                      color: '#ffffff', 
                      fontFamily: '"Orbitron", monospace' 
                    },
                    '& .MuiListItemText-secondary': { 
                      color: diagnostics.permissions === 'granted' ? '#00ff88' : '#ff9500' 
                    }
                  }}
                />
              </ListItem>

              <ListItem>
                <ListItemIcon>
                  <VolumeOffIcon sx={{ color: diagnostics.devices.includes('devices found') ? '#00ff88' : '#ff3b30' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Audio Devices"
                  secondary={`Status: ${diagnostics.devices}`}
                  sx={{
                    '& .MuiListItemText-primary': { 
                      color: '#ffffff', 
                      fontFamily: '"Orbitron", monospace' 
                    },
                    '& .MuiListItemText-secondary': { 
                      color: diagnostics.devices.includes('error') ? '#ff3b30' : '#00ff88' 
                    }
                  }}
                />
              </ListItem>

              <ListItem>
                <ListItemIcon>
                  <SettingsVoiceIcon sx={{ color: diagnostics.webAudio === 'supported' ? '#00ff88' : '#ff3b30' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Web Audio API"
                  secondary={`Status: ${diagnostics.webAudio}`}
                  sx={{
                    '& .MuiListItemText-primary': { 
                      color: '#ffffff', 
                      fontFamily: '"Orbitron", monospace' 
                    },
                    '& .MuiListItemText-secondary': { 
                      color: diagnostics.webAudio === 'supported' ? '#00ff88' : '#ff3b30' 
                    }
                  }}
                />
              </ListItem>

              <ListItem>
                <ListItemIcon>
                  <BuildIcon sx={{ color: diagnostics.speechRecognition === 'supported' ? '#00ff88' : '#ff3b30' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Speech Recognition"
                  secondary={`Status: ${diagnostics.speechRecognition}`}
                  sx={{
                    '& .MuiListItemText-primary': { 
                      color: '#ffffff', 
                      fontFamily: '"Orbitron", monospace' 
                    },
                    '& .MuiListItemText-secondary': { 
                      color: diagnostics.speechRecognition === 'supported' ? '#00ff88' : '#ff3b30' 
                    }
                  }}
                />
              </ListItem>
            </List>
          </Box>

          {/* Solutions suggérées */}
          {(diagnostics.permissions === 'denied' || diagnostics.permissions === 'prompt') && (
            <Alert
              severity="warning"
              sx={{
                backgroundColor: 'rgba(255, 149, 0, 0.1)',
                border: '1px solid rgba(255, 149, 0, 0.3)',
                color: '#ff9500',
                marginBottom: '20px',
                fontFamily: '"Orbitron", monospace'
              }}
            >
              Microphone permissions required. Click "Grant Audio Access" to enable voice features.
            </Alert>
          )}

          {/* Boutons d'action spécialisés */}
          <Box sx={{ display: 'flex', gap: '15px', flexWrap: 'wrap', justifyContent: 'center' }}>
            {diagnostics.permissions !== 'granted' && (
              <Button
                variant="outlined"
                startIcon={<MicIcon />}
                onClick={this.requestPermissions}
                className="jarvis-button"
                sx={{
                  borderColor: '#00ff88',
                  color: '#00ff88',
                  '&:hover': {
                    borderColor: '#00ff88',
                    backgroundColor: 'rgba(0, 255, 136, 0.1)'
                  }
                }}
              >
                GRANT AUDIO ACCESS
              </Button>
            )}

            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={this.handleAudioRetry}
              className="jarvis-button"
              sx={{
                borderColor: '#00d4ff',
                color: '#00d4ff',
                '&:hover': {
                  borderColor: '#00d4ff',
                  backgroundColor: 'rgba(0, 212, 255, 0.1)'
                }
              }}
            >
              REINITIALIZE AUDIO
            </Button>

            <Button
              variant="outlined"
              onClick={() => this.handleReset()}
              className="jarvis-button"
              sx={{
                borderColor: '#ff9500',
                color: '#ff9500',
                '&:hover': {
                  borderColor: '#ff9500',
                  backgroundColor: 'rgba(255, 149, 0, 0.1)'
                }
              }}
            >
              DISABLE AUDIO MODE
            </Button>
          </Box>

          {/* Fallback mode notice */}
          <Typography
            variant="body2"
            sx={{
              marginTop: '20px',
              color: '#00d4ff',
              fontFamily: '"Orbitron", monospace',
              fontStyle: 'italic'
            }}
          >
            JARVIS will continue operating in text-only mode until audio is restored.
          </Typography>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default AudioErrorBoundary;