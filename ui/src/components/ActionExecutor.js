/**
 * ⚡ JARVIS UI - Action Executor Component
 * Composant pour exécuter des actions système via JARVIS
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  Divider,
  IconButton,
  Tooltip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  PlayArrow as ExecuteIcon,
  Mouse as ClickIcon,
  Keyboard as TypeIcon,
  Screenshot as ScreenshotIcon,
  Visibility as AnalyzeIcon,
  AccessTime as WaitIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  Clear as ClearIcon,
  Code as CodeIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

import { useJarvis } from '../contexts/JarvisContext';

const ACTION_TYPES = {
  'click': { label: 'Clic', icon: <ClickIcon />, description: 'Cliquer à une position' },
  'type': { label: 'Saisie', icon: <TypeIcon />, description: 'Taper du texte' },
  'key': { label: 'Touche', icon: <TypeIcon />, description: 'Presser une touche' },
  'screenshot': { label: 'Capture', icon: <ScreenshotIcon />, description: 'Prendre une capture d\'écran' },
  'analyze': { label: 'Analyse', icon: <AnalyzeIcon />, description: 'Analyser l\'écran' },
  'wait': { label: 'Attendre', icon: <WaitIcon />, description: 'Attendre un délai' }
};

function ActionExecutor() {
  const theme = useTheme();
  const { state, actions } = useJarvis();
  
  // États
  const [selectedAction, setSelectedAction] = useState('click');
  const [parameters, setParameters] = useState('{}');
  const [description, setDescription] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionHistory, setExecutionHistory] = useState([]);
  const [showParametersDialog, setShowParametersDialog] = useState(false);

  useEffect(() => {
    // Charger l'historique depuis le localStorage
    const savedHistory = localStorage.getItem('jarvis_execution_history');
    if (savedHistory) {
      try {
        setExecutionHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.warn('Erreur chargement historique:', error);
      }
    }
  }, []);

  const updateParameters = (actionType) => {
    const defaultParams = {
      'click': '{"x": 100, "y": 100}',
      'type': '{"text": "Hello World"}',
      'key': '{"key": "Enter"}',
      'screenshot': '{}',
      'analyze': '{}',
      'wait': '{"duration": 1000}'
    };
    
    setParameters(defaultParams[actionType] || '{}');
    setDescription(`Exécuter ${ACTION_TYPES[actionType]?.label.toLowerCase()}`);
  };

  const handleActionTypeChange = (actionType) => {
    setSelectedAction(actionType);
    updateParameters(actionType);
  };

  const executeAction = async () => {
    if (isExecuting) return;

    try {
      setIsExecuting(true);
      
      // Parser les paramètres JSON
      let parsedParams = {};
      try {
        parsedParams = JSON.parse(parameters);
      } catch (error) {
        throw new Error('Paramètres JSON invalides');
      }

      const requestData = {
        action_type: selectedAction,
        parameters: parsedParams,
        description: description || `Exécuter ${selectedAction}`
      };

      actions.addLog('info', `Exécution action: ${selectedAction}`, 'executor');

      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/executor/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`Erreur API: ${response.status}`);
      }

      const result = await response.json();

      // Ajouter à l'historique
      const historyEntry = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        action_type: selectedAction,
        description: description,
        parameters: parsedParams,
        success: result.success,
        result: result.result
      };

      const newHistory = [historyEntry, ...executionHistory.slice(0, 19)]; // Garder 20 dernières
      setExecutionHistory(newHistory);
      localStorage.setItem('jarvis_execution_history', JSON.stringify(newHistory));

      if (result.success) {
        actions.addNotification('success', 'Exécution', 'Action exécutée avec succès');
        actions.addLog('success', `Action ${selectedAction} réussie`, 'executor');
      } else {
        actions.addNotification('warning', 'Exécution', 'Action exécutée avec des avertissements');
        actions.addLog('warning', `Action ${selectedAction} avec avertissements`, 'executor');
      }

    } catch (error) {
      actions.addNotification('error', 'Exécution', error.message);
      actions.addLog('error', `Erreur exécution: ${error.message}`, 'executor');
      
      // Ajouter l'échec à l'historique
      const historyEntry = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        action_type: selectedAction,
        description: description,
        parameters: parameters,
        success: false,
        error: error.message
      };
      
      const newHistory = [historyEntry, ...executionHistory.slice(0, 19)];
      setExecutionHistory(newHistory);
      localStorage.setItem('jarvis_execution_history', JSON.stringify(newHistory));
    } finally {
      setIsExecuting(false);
    }
  };

  const clearHistory = () => {
    setExecutionHistory([]);
    localStorage.removeItem('jarvis_execution_history');
    actions.addNotification('info', 'Historique', 'Historique effacé');
  };

  const replayAction = (historyItem) => {
    setSelectedAction(historyItem.action_type);
    setParameters(JSON.stringify(historyItem.parameters, null, 2));
    setDescription(historyItem.description);
  };

  const getStatusColor = (success, error) => {
    if (error) return 'error';
    return success ? 'success' : 'warning';
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ExecuteIcon />
            Exécuteur d'Actions
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Historique des actions">
              <IconButton onClick={() => setShowParametersDialog(true)} size="small">
                <HistoryIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Effacer l'historique">
              <IconButton onClick={clearHistory} size="small">
                <ClearIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Sélection de l'action */}
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Type d'action</InputLabel>
          <Select
            value={selectedAction}
            label="Type d'action"
            onChange={(e) => handleActionTypeChange(e.target.value)}
          >
            {Object.entries(ACTION_TYPES).map(([key, config]) => (
              <MenuItem key={key} value={key}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {config.icon}
                  <Box>
                    <Typography variant="body2">{config.label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {config.description}
                    </Typography>
                  </Box>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Description */}
        <TextField
          fullWidth
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description de l'action à exécuter"
          sx={{ mb: 2 }}
        />

        {/* Paramètres JSON */}
        <TextField
          fullWidth
          multiline
          rows={4}
          label="Paramètres (JSON)"
          value={parameters}
          onChange={(e) => setParameters(e.target.value)}
          placeholder='{"key": "value"}'
          sx={{ 
            mb: 2,
            '& .MuiInputBase-input': {
              fontFamily: 'monospace',
              fontSize: '0.875rem'
            }
          }}
          helperText="Paramètres au format JSON pour l'action"
        />

        {/* Bouton d'exécution */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Button
            variant="contained"
            startIcon={<ExecuteIcon />}
            onClick={executeAction}
            disabled={isExecuting || !parameters.trim()}
            fullWidth
          >
            {isExecuting ? 'Exécution...' : 'Exécuter l\'action'}
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<CodeIcon />}
            onClick={() => setShowParametersDialog(true)}
          >
            Exemples
          </Button>
        </Box>

        {/* Barre de progression */}
        {isExecuting && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
              Exécution de l'action en cours...
            </Typography>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Historique récent */}
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Historique récent ({executionHistory.length}):
        </Typography>

        {executionHistory.length > 0 ? (
          <List dense sx={{ maxHeight: 300, overflow: 'auto' }}>
            {executionHistory.slice(0, 5).map((item) => (
              <ListItem
                key={item.id}
                button
                onClick={() => replayAction(item)}
                sx={{
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 1,
                  mb: 1,
                  '&:hover': {
                    backgroundColor: theme.palette.action.hover,
                  }
                }}
              >
                <ListItemIcon>
                  {ACTION_TYPES[item.action_type]?.icon}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2">
                        {item.description || item.action_type}
                      </Typography>
                      <Chip
                        label={item.success ? 'Succès' : item.error ? 'Erreur' : 'Avertissement'}
                        color={getStatusColor(item.success, item.error)}
                        size="small"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        {item.timestamp} • {item.action_type}
                      </Typography>
                      {item.error && (
                        <Typography variant="caption" color="error" sx={{ display: 'block' }}>
                          Erreur: {item.error}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Alert severity="info">
            Aucune action exécutée récemment. Configurez et exécutez une action ci-dessus.
          </Alert>
        )}

        {/* Instructions */}
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Types d'actions disponibles :</strong><br />
            • <strong>Clic :</strong> {"x, y"} - Coordonnées de clic<br />
            • <strong>Saisie :</strong> {"text"} - Texte à taper<br />
            • <strong>Touche :</strong> {"key"} - Touche à presser<br />
            • <strong>Capture :</strong> Aucun paramètre requis<br />
            • <strong>Analyse :</strong> Aucun paramètre requis<br />
            • <strong>Attendre :</strong> {"duration"} - Durée en millisecondes
          </Typography>
        </Alert>
      </CardContent>

      {/* Dialog d'exemples */}
      <Dialog
        open={showParametersDialog}
        onClose={() => setShowParametersDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Exemples de paramètres</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1 }}>
            {Object.entries(ACTION_TYPES).map(([key, config]) => (
              <Box key={key} sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  {config.icon}
                  {config.label} - {config.description}
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  value={(() => {
                    const examples = {
                      'click': '{"x": 500, "y": 300}',
                      'type': '{"text": "Bonjour JARVIS!"}',
                      'key': '{"key": "Enter"}\n// Autres: "Ctrl+C", "Alt+Tab", "F1"',
                      'screenshot': '{}',
                      'analyze': '{}',
                      'wait': '{"duration": 2000}\n// Attendre 2 secondes'
                    };
                    return examples[key] || '{}';
                  })()}
                  InputProps={{
                    readOnly: true,
                    style: { fontFamily: 'monospace', fontSize: '0.875rem' }
                  }}
                  sx={{ mb: 1 }}
                />
              </Box>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowParametersDialog(false)}>
            Fermer
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}

export default ActionExecutor; 