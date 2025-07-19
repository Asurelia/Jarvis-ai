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
  Divider
} from '@mui/material';
import {
  Mic as MicIcon,
  VolumeUp as SpeakIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';

function VoiceInterface() {
  const { state, actions } = useJarvis();
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Interface Vocale
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: 'secondary.main' }}>
                  <MicIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">Module Vocal</Typography>
                  <Chip 
                    label={state.modules.voice.status || 'unknown'} 
                    color={state.modules.voice.status === 'active' ? 'success' : 'default'}
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
      </Grid>
    </Box>
  );
}

export default VoiceInterface;