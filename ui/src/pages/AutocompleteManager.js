/**
 * 🤖 JARVIS UI - Autocomplete Manager
 * Interface de gestion de l'autocomplétion
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
  Switch,
  FormControlLabel,
  Divider
} from '@mui/material';
import {
  AutoAwesome as AutocompleteIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';

function AutocompleteManager() {
  const { state, actions } = useJarvis();
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Gestionnaire d'Autocomplétion
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <AutocompleteIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">Module Autocomplétion</Typography>
                  <Chip 
                    label={state.modules.autocomplete.status || 'unknown'} 
                    color={state.modules.autocomplete.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </Box>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={state.config.autocompleteEnabled}
                    onChange={actions.toggleAutocomplete}
                  />
                }
                label="Autocomplétion activée"
                sx={{ mb: 2 }}
              />
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                Statistiques
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Utilisations
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {state.stats.autocompleteUsage}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default AutocompleteManager;