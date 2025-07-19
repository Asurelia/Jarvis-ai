/**
 * 🤖 JARVIS UI - Settings
 * Interface de configuration de JARVIS
 */
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Switch,
  FormControlLabel,
  Divider,
  Button,
  Chip
} from '@mui/material';
import {
  Save as SaveIcon,
  RestoreFromTrash as ResetIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';

function Settings() {
  const { state, actions } = useJarvis();
  
  const handleSave = () => {
    actions.addNotification('success', 'Paramètres', 'Configuration sauvegardée');
  };
  
  const handleReset = () => {
    actions.addNotification('info', 'Paramètres', 'Configuration remise à zéro');
  };
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Paramètres
      </Typography>
      
      <Grid container spacing={3}>
        {/* Configuration générale */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Configuration Générale
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={state.config.voiceMode}
                    onChange={actions.toggleVoiceMode}
                  />
                }
                label="Mode vocal"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={state.config.autocompleteEnabled}
                    onChange={actions.toggleAutocomplete}
                  />
                }
                label="Autocomplétion globale"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={state.config.sandboxMode}
                    onChange={actions.toggleSandboxMode}
                  />
                }
                label="Mode sandbox (sécurisé)"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={state.config.debugMode}
                    onChange={actions.toggleDebugMode}
                  />
                }
                label="Mode debug"
                sx={{ mb: 2, display: 'block' }}
              />
            </CardContent>
          </Card>
        </Grid>
        
        {/* Informations système */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Informations Système
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Version JARVIS
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {state.jarvis.version || 'v1.0.0'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Statut
                </Typography>
                <Chip
                  label={state.jarvis.status === 'connected' ? 'Connecté' : 'Déconnecté'}
                  size="small"
                  color={state.jarvis.status === 'connected' ? 'success' : 'error'}
                />
              </Box>
              
              {state.jarvis.pid && (
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    PID
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, fontFamily: 'monospace' }}>
                    {state.jarvis.pid}
                  </Typography>
                </Box>
              )}
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                Statistiques
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Commandes exécutées
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {state.stats.commandsExecuted}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Captures d'écran
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {state.stats.screenshotsTaken}
                </Typography>
              </Box>
              
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
        
        {/* Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Actions
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSave}
                >
                  Sauvegarder
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<ResetIcon />}
                  onClick={handleReset}
                  color="warning"
                >
                  Remettre à zéro
                </Button>
                
                <Button
                  variant="outlined"
                  onClick={actions.resetStats}
                  color="info"
                >
                  Reset Statistiques
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Settings;