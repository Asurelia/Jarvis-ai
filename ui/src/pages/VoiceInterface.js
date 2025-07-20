/**
 * 🤖 JARVIS UI - Voice Interface
 * Interface de contrôle pour le module vocal
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Avatar,
  Switch,
  FormControlLabel,
  Divider,
  TextField
} from '@mui/material';
import {
  Mic as MicIcon,
  VolumeUp as SpeakIcon,
  Settings as SettingsIcon,
  Send as SendIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';
import { useJarvisAPI } from '../hooks/useJarvisAPI';
import VoiceRecorder from '../components/VoiceRecorder';
import MicrophoneTest from '../components/MicrophoneTest';

function VoiceInterface() {
  const { state, actions } = useJarvis();
  const { executeCommand, speakText, isConnected } = useJarvisAPI();
  const [textCommand, setTextCommand] = useState('');
  const [isProcessingCommand, setIsProcessingCommand] = useState(false);

  // Gérer la transcription vocale
  const handleVoiceTranscription = async (transcription) => {
    setIsProcessingCommand(true);
    try {
      actions.addLog('info', `Commande vocale: "${transcription}"`, 'voice');
      
      // Exécuter la commande transcrite
      const result = await executeCommand(transcription);
      
      if (result.success) {
        actions.addNotification('success', 'Commande exécutée', 
          `${result.actions_count} actions planifiées`);
      }
    } catch (error) {
      actions.addNotification('error', 'Erreur', error.message);
    } finally {
      setIsProcessingCommand(false);
    }
  };

  // Exécuter une commande texte
  const handleTextCommand = async () => {
    if (!textCommand.trim()) return;
    
    setIsProcessingCommand(true);
    try {
      const result = await executeCommand(textCommand);
      
      if (result.success) {
        actions.addNotification('success', 'Commande exécutée', 
          `${result.actions_count} actions planifiées`);
        setTextCommand('');
      }
    } catch (error) {
      actions.addNotification('error', 'Erreur', error.message);
    } finally {
      setIsProcessingCommand(false);
    }
  };

  // Test de synthèse vocale
  const handleVoiceTest = async () => {
    try {
      await speakText('Test de l\'interface vocale JARVIS. Le système fonctionne correctement.');
    } catch (error) {
      actions.addNotification('error', 'Erreur', 'Test vocal échoué');
    }
  };
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Interface Vocale
      </Typography>
      
      <Grid container spacing={3}>
        {/* Interface d'enregistrement vocal */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: 'secondary.main' }}>
                  <MicIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">Commandes Vocales</Typography>
                  <Chip 
                    label={isConnected ? 'En ligne' : 'Hors ligne'} 
                    color={isConnected ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
              </Box>
              
              {/* Composant d'enregistrement vocal */}
              <Box sx={{ py: 3 }}>
                <VoiceRecorder 
                  onTranscription={handleVoiceTranscription}
                  disabled={!isConnected || isProcessingCommand}
                />
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              {/* Interface texte alternative */}
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                Commande Texte (Alternative)
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  variant="outlined"
                  placeholder="Tapez votre commande ici..."
                  value={textCommand}
                  onChange={(e) => setTextCommand(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleTextCommand();
                    }
                  }}
                  disabled={!isConnected || isProcessingCommand}
                  size="small"
                />
                <Button
                  variant="contained"
                  onClick={handleTextCommand}
                  disabled={!isConnected || isProcessingCommand || !textCommand.trim()}
                  startIcon={<SendIcon />}
                >
                  Envoyer
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Panneau de contrôle et statistiques */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <SettingsIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">Contrôles</Typography>
                  <Chip 
                    label={state.modules.voice?.status || 'unknown'} 
                    color={state.modules.voice?.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </Box>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={state.config.voiceMode}
                    onChange={actions.toggleVoiceMode}
                  />
                }
                label="Mode vocal activé"
                sx={{ mb: 2 }}
              />
              
              <Button
                variant="outlined"
                startIcon={<SpeakIcon />}
                onClick={handleVoiceTest}
                disabled={!isConnected}
                fullWidth
                sx={{ mb: 2 }}
              >
                Test Vocal
              </Button>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                Statistiques
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Commandes vocales
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {state.stats.voiceCommands}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Configuration</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Paramètres avancés à venir...
              </Typography>
              <Button variant="outlined" startIcon={<SettingsIcon />} disabled>
                Configurer
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Diagnostic microphone */}
        <Grid item xs={12}>
          <MicrophoneTest />
        </Grid>
      </Grid>
    </Box>
  );
}

export default VoiceInterface;