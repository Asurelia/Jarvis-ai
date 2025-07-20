/**
 * 🤖 JARVIS UI - Action Executor
 * Interface pour l'exécuteur d'actions
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
  PlayArrow as ExecutorIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';
import ActionExecutorComponent from '../components/ActionExecutor';

function ActionExecutor() {
  const { state } = useJarvis();
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Exécuteur d'Actions
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <ExecutorIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">Module Exécuteur</Typography>
                  <Chip 
                    label={state.modules.executor.status || 'unknown'} 
                    color={state.modules.executor.status === 'active' ? 'success' : 'default'}
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
                  Actions exécutées
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {state.stats.commandsExecuted}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Exécuteur d'actions */}
        <Grid item xs={12}>
          <ActionExecutorComponent />
        </Grid>
      </Grid>
    </Box>
  );
}

export default ActionExecutor;