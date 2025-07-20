/**
 * 💡 JARVIS UI - Autocomplete Manager Component
 * Composant pour gérer l'autocomplétion globale
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Button,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  Divider,
  IconButton,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  AutoAwesome as AutocompleteIcon,
  Lightbulb as SuggestionIcon,
  Settings as SettingsIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Psychology as AIIcon,
  Keyboard as KeyboardIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

import { useJarvis } from '../contexts/JarvisContext';

function AutocompleteManager() {
  const theme = useTheme();
  const { state, actions } = useJarvis();
  
  // États
  const [isActive, setIsActive] = useState(false);
  const [testText, setTestText] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState({
    suggestions_generated: 0,
    words_learned: 0,
    patterns_detected: 0
  });

  useEffect(() => {
    loadAutocompleteStatus();
  }, []);

  const loadAutocompleteStatus = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/autocomplete/status`);
      
      if (response.ok) {
        const result = await response.json();
        setIsActive(result.active || false);
        setStats(result.stats || stats);
      }
    } catch (error) {
      actions.addLog('warning', `Statut autocomplétion indisponible: ${error.message}`, 'autocomplete');
    }
  };

  const toggleAutocomplete = async () => {
    try {
      const newState = !isActive;
      
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/autocomplete/${newState ? 'start' : 'stop'}`, {
        method: 'POST'
      });

      if (response.ok) {
        setIsActive(newState);
        actions.addNotification(
          'success', 
          'Autocomplétion', 
          newState ? 'Activée globalement' : 'Désactivée'
        );
        actions.addLog('info', `Autocomplétion ${newState ? 'activée' : 'désactivée'}`, 'autocomplete');
      } else {
        throw new Error(`Erreur API: ${response.status}`);
      }
    } catch (error) {
      actions.addNotification('error', 'Autocomplétion', error.message);
      actions.addLog('error', `Erreur autocomplétion: ${error.message}`, 'autocomplete');
    }
  };

  const testSuggestions = async () => {
    if (!testText.trim()) return;

    try {
      setIsLoading(true);
      setSuggestions([]);

      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/autocomplete/suggest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: testText,
          context: 'test',
          max_suggestions: 5
        })
      });

      if (response.ok) {
        const result = await response.json();
        setSuggestions(result.suggestions || []);
        
        if (result.suggestions && result.suggestions.length > 0) {
          actions.addNotification('success', 'Test', `${result.suggestions.length} suggestions générées`);
        } else {
          actions.addNotification('info', 'Test', 'Aucune suggestion trouvée');
        }
      } else {
        throw new Error(`Erreur API: ${response.status}`);
      }
    } catch (error) {
      actions.addNotification('error', 'Test', error.message);
      setSuggestions([
        `${testText} - suggestion par défaut 1`,
        `${testText} - suggestion par défaut 2`,
        `${testText} - suggestion par défaut 3`
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearSuggestions = () => {
    setSuggestions([]);
    setTestText('');
  };

  const applySuggestion = (suggestion) => {
    setTestText(suggestion);
    actions.addNotification('info', 'Suggestion', 'Suggestion appliquée');
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AutocompleteIcon />
            Gestionnaire d'Autocomplétion
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={isActive ? 'Actif' : 'Inactif'}
              color={isActive ? 'success' : 'default'}
              size="small"
            />
            <Tooltip title="Actualiser le statut">
              <IconButton onClick={loadAutocompleteStatus} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Contrôle principal */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <FormControlLabel
            control={
              <Switch
                checked={isActive}
                onChange={toggleAutocomplete}
                color="primary"
              />
            }
            label="Autocomplétion globale"
          />
          
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            size="small"
            disabled
          >
            Configuration
          </Button>
        </Box>

        {/* Statistiques */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="primary">
              {stats.suggestions_generated}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Suggestions générées
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="secondary">
              {stats.words_learned}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Mots appris
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="info.main">
              {stats.patterns_detected}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Motifs détectés
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Zone de test */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Test d'autocomplétion:
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Tapez du texte pour tester l'autocomplétion..."
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              disabled={isLoading}
            />
            <Button
              variant="contained"
              onClick={testSuggestions}
              disabled={!testText.trim() || isLoading}
              startIcon={<SuggestionIcon />}
            >
              Suggérer
            </Button>
            <Button
              variant="outlined"
              onClick={clearSuggestions}
              disabled={isLoading}
            >
              Effacer
            </Button>
          </Box>

          {/* Barre de progression */}
          {isLoading && (
            <Box sx={{ mb: 2 }}>
              <LinearProgress />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                Génération des suggestions...
              </Typography>
            </Box>
          )}

          {/* Liste des suggestions */}
          {suggestions.length > 0 && (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Suggestions ({suggestions.length}):
              </Typography>
              <List dense sx={{ bgcolor: theme.palette.background.default, borderRadius: 1 }}>
                {suggestions.map((suggestion, index) => (
                  <ListItem
                    key={index}
                    button
                    onClick={() => applySuggestion(suggestion)}
                    sx={{
                      '&:hover': {
                        backgroundColor: theme.palette.action.hover,
                      }
                    }}
                  >
                    <ListItemIcon>
                      <SuggestionIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={suggestion}
                      sx={{
                        '& .MuiListItemText-primary': {
                          fontSize: '0.9rem',
                          fontFamily: 'monospace'
                        }
                      }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </Box>

        {/* Instructions */}
        <Alert severity="info">
          <Typography variant="body2">
            <strong>Autocomplétion globale :</strong> Fonctionne dans toutes les applications Windows<br />
            <strong>Raccourci :</strong> Ctrl+Space pour déclencher les suggestions<br />
            <strong>IA intégrée :</strong> Apprend de vos habitudes de frappe<br />
            <strong>Test :</strong> Utilisez la zone ci-dessus pour tester les suggestions
          </Typography>
        </Alert>

        {/* État du système */}
        {!isActive && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              L'autocomplétion globale est désactivée. Activez-la pour bénéficier des suggestions 
              intelligentes dans toutes vos applications.
            </Typography>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

export default AutocompleteManager; 