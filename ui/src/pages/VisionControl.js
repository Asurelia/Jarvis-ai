/**
 * 🤖 JARVIS UI - Vision Control
 * Interface de contrôle pour le module de vision
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  TextField,
  Chip,
  Avatar,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  Visibility as VisionIcon,
  Screenshot as ScreenshotIcon,
  Image as ImageIcon,
  Search as AnalyzeIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';

function VisionControl() {
  const { state, actions, electronAPI } = useJarvis();
  const [isCapturing, setIsCapturing] = useState(false);
  
  const handleScreenshot = async () => {
    setIsCapturing(true);
    try {
      await electronAPI.executeCommand('screenshot');
      actions.incrementStat('screenshotsTaken');
      actions.addNotification('success', 'Capture d\'écran', 'Screenshot pris avec succès');
    } catch (error) {
      actions.addNotification('error', 'Erreur', 'Impossible de prendre la capture');
    } finally {
      setIsCapturing(false);
    }
  };
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Contrôle Vision
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <VisionIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">Module Vision</Typography>
                  <Chip 
                    label={state.modules.vision.status || 'unknown'} 
                    color={state.modules.vision.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </Box>
              
              <Button
                variant="contained"
                startIcon={<ScreenshotIcon />}
                onClick={handleScreenshot}
                disabled={isCapturing || state.jarvis.status !== 'connected'}
                fullWidth
                sx={{ mb: 2 }}
              >
                {isCapturing ? 'Capture en cours...' : 'Prendre une capture'}
              </Button>
              
              {isCapturing && <LinearProgress sx={{ mb: 2 }} />}
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                Statistiques
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Captures prises
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {state.stats.screenshotsTaken}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Analyse d'image</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Fonctionnalité à venir...
              </Typography>
              <Button variant="outlined" startIcon={<AnalyzeIcon />} disabled>
                Analyser l'écran
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default VisionControl;