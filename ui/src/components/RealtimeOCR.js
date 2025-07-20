/**
 * 👁️ JARVIS UI - Realtime OCR Component
 * Composant pour l'OCR en temps réel de l'écran
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Switch,
  FormControlLabel,
  Chip,
  LinearProgress,
  Alert,
  TextField,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Visibility as VisionIcon,
  VisibilityOff as VisionOffIcon,
  Screenshot as ScreenshotIcon,
  TextFields as TextIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  Search as SearchIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

import { useJarvis } from '../contexts/JarvisContext';
import { useJarvisAPI } from '../hooks/useJarvisAPI';

function RealtimeOCR() {
  const theme = useTheme();
  const { state, actions } = useJarvis();
  const { takeScreenshot, isConnected } = useJarvisAPI();
  
  // États
  const [isRealtimeActive, setIsRealtimeActive] = useState(false);
  const [currentText, setCurrentText] = useState('');
  const [lastCapture, setLastCapture] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredText, setFilteredText] = useState('');
  const [ocrHistory, setOcrHistory] = useState([]);
  const [confidence, setConfidence] = useState(0);
  
  // Refs
  const intervalRef = useRef(null);
  const lastHashRef = useRef('');

  // Effet pour le mode temps réel
  useEffect(() => {
    if (isRealtimeActive && isConnected) {
      startRealtimeOCR();
    } else {
      stopRealtimeOCR();
    }
    
    return () => stopRealtimeOCR();
  }, [isRealtimeActive, isConnected]);

  // Filtrage du texte selon la recherche
  useEffect(() => {
    if (searchQuery.trim()) {
      const filtered = currentText
        .split('\n')
        .filter(line => line.toLowerCase().includes(searchQuery.toLowerCase()))
        .join('\n');
      setFilteredText(filtered);
    } else {
      setFilteredText(currentText);
    }
  }, [currentText, searchQuery]);

  const startRealtimeOCR = () => {
    if (intervalRef.current) return;

    actions.addLog('info', 'Démarrage OCR temps réel...', 'vision');
    
    intervalRef.current = setInterval(async () => {
      await performOCR();
    }, 2000); // Capture toutes les 2 secondes
  };

  const stopRealtimeOCR = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
      actions.addLog('info', 'Arrêt OCR temps réel', 'vision');
    }
  };

  const performOCR = async () => {
    if (isProcessing) return;
    
    try {
      setIsProcessing(true);
      
      // Prendre une capture d'écran
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/screenshot`);
      
      if (!response.ok) {
        throw new Error(`Erreur API: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // Effectuer l'OCR sur la capture
        const ocrResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/vision/ocr`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            screenshot_path: result.filename,
            engine: 'auto'
          })
        });

        if (ocrResponse.ok) {
          const ocrResult = await ocrResponse.json();
          
          if (ocrResult.success && ocrResult.text) {
            // Vérifier si le contenu a changé
            const textHash = btoa(ocrResult.text).substring(0, 16);
            
            if (textHash !== lastHashRef.current) {
              setCurrentText(ocrResult.text);
              setConfidence(ocrResult.confidence_avg || 0);
              setLastCapture(new Date().toLocaleTimeString());
              lastHashRef.current = textHash;
              
              // Ajouter à l'historique
              setOcrHistory(prev => [{
                timestamp: new Date().toLocaleTimeString(),
                text: ocrResult.text.substring(0, 100) + '...',
                confidence: ocrResult.confidence_avg || 0,
                wordCount: ocrResult.words?.length || 0
              }, ...prev.slice(0, 9)]); // Garder 10 derniers
              
              actions.addLog('success', `OCR: ${ocrResult.words?.length || 0} mots détectés`, 'vision');
            }
          }
        }
      }
    } catch (error) {
      actions.addLog('error', `Erreur OCR: ${error.message}`, 'vision');
    } finally {
      setIsProcessing(false);
    }
  };

  const takeManualScreenshot = async () => {
    try {
      setIsProcessing(true);
      await performOCR();
      actions.addNotification('success', 'OCR', 'Capture et analyse effectuées');
    } catch (error) {
      actions.addNotification('error', 'OCR', error.message);
    }
  };

  const copyTextToClipboard = () => {
    navigator.clipboard.writeText(filteredText || currentText);
    actions.addNotification('success', 'Copié', 'Texte copié dans le presse-papiers');
  };

  const searchInText = (query) => {
    if (!query.trim()) return;
    
    const lines = currentText.split('\n');
    const matches = lines.filter(line => 
      line.toLowerCase().includes(query.toLowerCase())
    );
    
    actions.addNotification('info', 'Recherche', `${matches.length} résultats trouvés`);
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <VisionIcon />
            OCR Temps Réel
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={isConnected ? 'En ligne' : 'Hors ligne'}
              color={isConnected ? 'success' : 'error'}
              size="small"
            />
            {confidence > 0 && (
              <Chip
                label={`${Math.round(confidence * 100)}% confiance`}
                color={confidence > 0.8 ? 'success' : confidence > 0.6 ? 'warning' : 'error'}
                size="small"
              />
            )}
          </Box>
        </Box>

        {/* Contrôles */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={isRealtimeActive}
                onChange={(e) => setIsRealtimeActive(e.target.checked)}
                disabled={!isConnected}
              />
            }
            label="Mode temps réel"
          />
          
          <Button
            variant="outlined"
            startIcon={<ScreenshotIcon />}
            onClick={takeManualScreenshot}
            disabled={!isConnected || isProcessing}
            size="small"
          >
            Capture manuelle
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={performOCR}
            disabled={!isConnected || isProcessing}
            size="small"
          >
            Actualiser
          </Button>
        </Box>

        {/* Barre de progression */}
        {isProcessing && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
              Analyse en cours...
            </Typography>
          </Box>
        )}

        {/* Recherche */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Rechercher dans le texte..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ color: 'text.secondary', mr: 1 }} />
            }}
          />
          <Tooltip title="Copier le texte">
            <IconButton
              onClick={copyTextToClipboard}
              disabled={!currentText}
            >
              <CopyIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Informations */}
        {lastCapture && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Dernière capture: {lastCapture}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {currentText.length} caractères
            </Typography>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Zone de texte OCR */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Texte détecté:
          </Typography>
          
          {currentText ? (
            <Box
              sx={{
                p: 2,
                backgroundColor: theme.palette.background.default,
                borderRadius: 1,
                border: `1px solid ${theme.palette.divider}`,
                maxHeight: 300,
                overflow: 'auto',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                whiteSpace: 'pre-wrap'
              }}
            >
              {filteredText || currentText}
            </Box>
          ) : (
            <Alert severity="info">
              {isConnected 
                ? 'Activez le mode temps réel ou prenez une capture manuelle pour voir le texte'
                : 'Connexion à JARVIS requise'
              }
            </Alert>
          )}
        </Box>

        {/* Historique */}
        {ocrHistory.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Historique des captures:
            </Typography>
            <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
              {ocrHistory.map((entry, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemText
                    primary={entry.text}
                    secondary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{entry.timestamp}</span>
                        <span>{entry.wordCount} mots • {Math.round(entry.confidence * 100)}%</span>
                      </Box>
                    }
                    sx={{
                      '& .MuiListItemText-primary': {
                        fontSize: '0.875rem',
                        color: theme.palette.text.secondary
                      }
                    }}
                  />
                </ListItem>
              ))}
            </List>
          </>
        )}

        {/* Instructions */}
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Mode temps réel :</strong> Analyse automatique de l'écran toutes les 2 secondes<br />
            <strong>Capture manuelle :</strong> Analyse ponctuelle de l'écran actuel<br />
            <strong>Recherche :</strong> Filtrez le texte détecté en temps réel
          </Typography>
        </Alert>
      </CardContent>
    </Card>
  );
}

export default RealtimeOCR; 