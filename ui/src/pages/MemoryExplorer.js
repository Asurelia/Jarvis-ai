/**
 * 🤖 JARVIS UI - Memory Explorer
 * Interface d'exploration de la mémoire
 */
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Avatar,
  Divider
} from '@mui/material';
import {
  Memory as MemoryIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';

function MemoryExplorer() {
  const { state } = useJarvis();
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Explorateur de Mémoire
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <MemoryIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">Module Mémoire</Typography>
                  <Chip 
                    label={state.modules.memory.status || 'unknown'} 
                    color={state.modules.memory.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                Statistiques
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Entrées en mémoire
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {state.stats.memoryEntries}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default MemoryExplorer;