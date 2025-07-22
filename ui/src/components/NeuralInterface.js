/**
 * 🌐 JARVIS - Interface Neurale Étendue
 * Connexion multi-modalités avec vision, voix, gestes et RA
 */
import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { 
  Box, Card, CardContent, Typography, Grid, Paper, Switch, 
  FormControlLabel, Slider, Chip, Badge, LinearProgress,
  IconButton, Tooltip, Accordion, AccordionSummary, AccordionDetails,
  Alert, CircularProgress
} from '@mui/material';
import { 
  ExpandMore as ExpandMoreIcon, Visibility as VisibilityIcon,
  Mic as MicIcon, PanTool as GestureIcon, Psychology as BrainIcon,
  Timeline as PatternIcon, Speed as SpeedIcon, ViewInAr as ARIcon,
  Settings as SettingsIcon, FlashOn as FlashIcon
} from '@mui/icons-material';
import * as THREE from 'three';

// Modalités d'entrée
const INPUT_MODALITIES = {
  VOICE: {
    name: 'Vocal',
    icon: '🎤',
    color: '#4CAF50',
    active: false,
    confidence: 0
  },
  VISION: {
    name: 'Vision',
    icon: '👁️',  
    color: '#2196F3',
    active: false,
    confidence: 0
  },
  GESTURE: {
    name: 'Gestes',
    icon: '✋',
    color: '#FF9800', 
    active: false,
    confidence: 0
  },
  NEURAL: {
    name: 'Neural',
    icon: '🧠',
    color: '#9C27B0',
    active: false,
    confidence: 0
  },
  KEYBOARD: {
    name: 'Clavier',
    icon: '⌨️',
    color: '#607D8B',
    active: false,
    confidence: 0
  },
  MOUSE: {
    name: 'Souris',
    icon: '🖱️',
    color: '#795548',
    active: false,
    confidence: 0
  }
};

// Patterns neuraux simulés
const NEURAL_PATTERNS = {
  FOCUS: {
    name: 'Concentration',
    brainwaves: 'Beta (13-30 Hz)',
    pattern: [0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.8],
    color: '#FF5722'
  },
  CREATIVE: {
    name: 'Créativité',
    brainwaves: 'Alpha (8-12 Hz)', 
    pattern: [0.5, 0.6, 0.7, 0.8, 0.9, 0.8, 0.6],
    color: '#E91E63'
  },
  RELAXED: {
    name: 'Détendu',
    brainwaves: 'Theta (4-8 Hz)',
    pattern: [0.3, 0.4, 0.5, 0.4, 0.3, 0.4, 0.5],
    color: '#9C27B0'
  },
  ALERT: {
    name: 'Alerte',
    brainwaves: 'Gamma (30-100 Hz)',
    pattern: [0.8, 0.9, 1.0, 0.9, 0.8, 0.9, 1.0],
    color: '#F44336'
  }
};

// Modes de réalité augmentée
const AR_MODES = {
  OVERLAY: {
    name: 'Superposition',
    description: 'Infos flottantes sur l\'écran',
    enabled: false
  },
  SPATIAL: {
    name: 'Spatial',
    description: 'Mapping 3D de l\'espace',
    enabled: false
  },
  CONTEXTUAL: {
    name: 'Contextuel',
    description: 'Annotations intelligentes',
    enabled: false
  },
  HOLOGRAM: {
    name: 'Hologramme',
    description: 'Projection holographique',
    enabled: false
  }
};

function NeuralInterface({
  isEnabled = true,
  onModalityChange = null,
  onNeuralPattern = null,
  onGestureDetected = null,
  augmentedRealityMode = false
}) {
  const neuralCanvasRef = useRef(null);
  const gestureCanvasRef = useRef(null);
  const arOverlayRef = useRef(null);
  const brainwaveAnalyzerRef = useRef(null);
  const eyeTrackerRef = useRef(null);
  const voiceAnalyzerRef = useRef(null);
  const animationFrameRef = useRef(null);

  const [activeModalities, setActiveModalities] = useState(new Set());
  const [modalityData, setModalityData] = useState(INPUT_MODALITIES);
  const [currentNeuralPattern, setCurrentNeuralPattern] = useState('FOCUS');
  const [neuralActivity, setNeuralActivity] = useState(0.5);
  const [gestureBuffer, setGestureBuffer] = useState([]);
  const [eyePosition, setEyePosition] = useState({ x: 0, y: 0 });
  const [voiceCommand, setVoiceCommand] = useState('');
  const [arObjects, setArObjects] = useState([]);
  const [neuralSync, setNeuralSync] = useState(false);
  const [adaptiveMode, setAdaptiveMode] = useState(true);

  // Simulation du tracking oculaire
  useEffect(() => {
    if (!isEnabled) return;

    const simulateEyeTracking = () => {
      const mouseHandler = (e) => {
        const rect = document.body.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width;
        const y = (e.clientY - rect.top) / rect.height;
        
        setEyePosition({ x, y });
        
        // Activation de la modalité vision basée sur le mouvement oculaire
        updateModalityActivity('VISION', 0.3 + Math.random() * 0.4);
      };

      document.addEventListener('mousemove', mouseHandler);
      return () => document.removeEventListener('mousemove', mouseHandler);
    };

    return simulateEyeTracking();
  }, [isEnabled]);

  // Analyse des patterns de frappe pour simulation neurale
  useEffect(() => {
    if (!isEnabled) return;

    const keyPatterns = [];
    let lastKeyTime = 0;

    const keyHandler = (e) => {
      const now = performance.now();
      const timeDiff = now - lastKeyTime;
      
      keyPatterns.push({
        key: e.code,
        time: now,
        interval: timeDiff
      });
      
      // Garder seulement les 20 dernières frappes
      if (keyPatterns.length > 20) {
        keyPatterns.shift();
      }
      
      // Analyse du pattern pour déduire l'état mental
      const avgInterval = keyPatterns.reduce((sum, p) => sum + p.interval, 0) / keyPatterns.length;
      
      let pattern = 'FOCUS';
      if (avgInterval < 100) pattern = 'ALERT';
      else if (avgInterval > 300) pattern = 'RELAXED';
      else if (Math.random() > 0.7) pattern = 'CREATIVE';
      
      setCurrentNeuralPattern(pattern);
      updateModalityActivity('NEURAL', 0.6 + Math.random() * 0.3);
      updateModalityActivity('KEYBOARD', 0.8);
      
      lastKeyTime = now;
    };

    document.addEventListener('keydown', keyHandler);
    return () => document.removeEventListener('keydown', keyHandler);
  }, [isEnabled]);

  // Détection de gestes de souris
  useEffect(() => {
    if (!isEnabled) return;

    const mouseGestures = [];
    let isDrawing = false;

    const mouseDownHandler = (e) => {
      isDrawing = true;
      mouseGestures.length = 0; // Clear buffer
      mouseGestures.push({ x: e.clientX, y: e.clientY, timestamp: Date.now() });
    };

    const mouseMoveHandler = (e) => {
      if (isDrawing) {
        mouseGestures.push({ x: e.clientX, y: e.clientY, timestamp: Date.now() });
        updateModalityActivity('MOUSE', 0.7);
        updateModalityActivity('GESTURE', 0.5 + Math.random() * 0.4);
      }
    };

    const mouseUpHandler = () => {
      if (isDrawing && mouseGestures.length > 5) {
        const gesture = analyzeGesture(mouseGestures);
        if (gesture && onGestureDetected) {
          onGestureDetected(gesture);
        }
        setGestureBuffer([...mouseGestures]);
      }
      isDrawing = false;
    };

    document.addEventListener('mousedown', mouseDownHandler);
    document.addEventListener('mousemove', mouseMoveHandler);
    document.addEventListener('mouseup', mouseUpHandler);

    return () => {
      document.removeEventListener('mousedown', mouseDownHandler);
      document.removeEventListener('mousemove', mouseMoveHandler);
      document.removeEventListener('mouseup', mouseUpHandler);
    };
  }, [isEnabled, onGestureDetected]);

  // Analyse des gestes
  const analyzeGesture = useCallback((points) => {
    if (points.length < 3) return null;

    const start = points[0];
    const end = points[points.length - 1];
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const duration = end.timestamp - start.timestamp;

    // Classification simple des gestes
    if (distance > 100 && duration < 1000) {
      if (Math.abs(dx) > Math.abs(dy)) {
        return dx > 0 ? 'swipe_right' : 'swipe_left';
      } else {
        return dy > 0 ? 'swipe_down' : 'swipe_up';
      }
    }
    
    // Geste circulaire
    const isCircular = checkCircularGesture(points);
    if (isCircular) {
      return 'circle';
    }

    return 'tap';
  }, []);

  // Détection de geste circulaire
  const checkCircularGesture = (points) => {
    if (points.length < 8) return false;
    
    const center = {
      x: points.reduce((sum, p) => sum + p.x, 0) / points.length,
      y: points.reduce((sum, p) => sum + p.y, 0) / points.length
    };
    
    let angleSum = 0;
    for (let i = 1; i < points.length; i++) {
      const p1 = points[i - 1];
      const p2 = points[i];
      
      const angle1 = Math.atan2(p1.y - center.y, p1.x - center.x);
      const angle2 = Math.atan2(p2.y - center.y, p2.x - center.x);
      
      let deltaAngle = angle2 - angle1;
      if (deltaAngle > Math.PI) deltaAngle -= 2 * Math.PI;
      if (deltaAngle < -Math.PI) deltaAngle += 2 * Math.PI;
      
      angleSum += deltaAngle;
    }
    
    return Math.abs(angleSum) > Math.PI * 1.2; // Plus de 1.2 tours
  };

  // Mise à jour de l'activité des modalités
  const updateModalityActivity = useCallback((modalityKey, activity) => {
    setModalityData(prev => ({
      ...prev,
      [modalityKey]: {
        ...prev[modalityKey],
        active: activity > 0.3,
        confidence: Math.min(0.95, activity)
      }
    }));

    setActiveModalities(prev => {
      const newSet = new Set(prev);
      if (activity > 0.3) {
        newSet.add(modalityKey);
      } else {
        newSet.delete(modalityKey);
      }
      return newSet;
    });
  }, []);

  // Simulation des ondes cérébrales
  useEffect(() => {
    if (!neuralCanvasRef.current || !isEnabled) return;

    const canvas = neuralCanvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = 400;
    canvas.height = 200;

    const animateNeuralPatterns = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const pattern = NEURAL_PATTERNS[currentNeuralPattern];
      const time = Date.now() * 0.001;
      
      // Fond dégradé
      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, 'rgba(0,0,0,0.8)');
      gradient.addColorStop(1, 'rgba(0,0,0,0.2)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Dessiner les ondes cérébrales
      ctx.strokeStyle = pattern.color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      
      for (let x = 0; x < canvas.width; x += 2) {
        const baseY = canvas.height / 2;
        const frequency = 0.02 + (pattern.pattern.length / 1000);
        let y = baseY;
        
        // Superposition de plusieurs fréquences
        pattern.pattern.forEach((amplitude, i) => {
          y += Math.sin(time * (i + 1) + x * frequency) * amplitude * 30 * neuralActivity;
        });
        
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      
      ctx.stroke();
      
      // Particules d'activité neurale
      for (let i = 0; i < 10; i++) {
        const x = Math.random() * canvas.width;
        const y = canvas.height / 2 + Math.sin(time * 3 + i) * 50 * neuralActivity;
        
        ctx.fillStyle = pattern.color + '80';
        ctx.beginPath();
        ctx.arc(x, y, 2 + Math.sin(time * 2 + i) * 1, 0, Math.PI * 2);
        ctx.fill();
      }
      
      animationFrameRef.current = requestAnimationFrame(animateNeuralPatterns);
    };

    animateNeuralPatterns();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [currentNeuralPattern, neuralActivity, isEnabled]);

  // Simulation vocale (activation aléatoire)
  useEffect(() => {
    if (!isEnabled) return;

    const interval = setInterval(() => {
      if (Math.random() > 0.8) {
        const commands = ['Hello JARVIS', 'What time is it?', 'Show status', 'Execute plan'];
        const randomCommand = commands[Math.floor(Math.random() * commands.length)];
        setVoiceCommand(randomCommand);
        updateModalityActivity('VOICE', 0.8 + Math.random() * 0.2);
        
        setTimeout(() => {
          setVoiceCommand('');
          updateModalityActivity('VOICE', 0);
        }, 2000);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isEnabled, updateModalityActivity]);

  // Mise à jour de l'activité neurale
  useEffect(() => {
    const interval = setInterval(() => {
      setNeuralActivity(prev => {
        const target = NEURAL_PATTERNS[currentNeuralPattern].pattern.reduce((a, b) => a + b) / 
                      NEURAL_PATTERNS[currentNeuralPattern].pattern.length;
        return prev + (target - prev) * 0.1;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [currentNeuralPattern]);

  // Notification des changements de modalité
  useEffect(() => {
    if (onModalityChange) {
      onModalityChange({
        active: Array.from(activeModalities),
        data: modalityData,
        neuralPattern: currentNeuralPattern,
        neuralActivity
      });
    }
  }, [activeModalities, modalityData, currentNeuralPattern, neuralActivity, onModalityChange]);

  // Rendu des objets AR
  const renderAROverlay = () => {
    if (!augmentedRealityMode) return null;

    return (
      <Box 
        ref={arOverlayRef}
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          zIndex: 1000
        }}
      >
        {/* Curseur de regard */}
        <Box
          sx={{
            position: 'absolute',
            left: `${eyePosition.x * 100}%`,
            top: `${eyePosition.y * 100}%`,
            width: 20,
            height: 20,
            borderRadius: '50%',
            border: '2px solid #00BCD4',
            backgroundColor: 'rgba(0,188,212,0.2)',
            transform: 'translate(-50%, -50%)',
            transition: 'all 0.1s ease'
          }}
        />
        
        {/* Infos contextuelles */}
        <Paper
          sx={{
            position: 'absolute',
            top: 20,
            right: 20,
            p: 1,
            backgroundColor: 'rgba(0,0,0,0.8)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <Typography variant="caption" color="primary">
            AR Mode • Eye: ({Math.round(eyePosition.x * 100)}, {Math.round(eyePosition.y * 100)})
          </Typography>
        </Paper>
      </Box>
    );
  };

  if (!isEnabled) return null;

  return (
    <Card sx={{ mb: 2, backgroundColor: 'rgba(0,0,0,0.8)', position: 'relative' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ color: '#9C27B0', display: 'flex', alignItems: 'center', gap: 1 }}>
          <BrainIcon />
          🌐 Interface Neurale Étendue
          {neuralSync && <Badge color="secondary" variant="dot" />}
        </Typography>

        {renderAROverlay()}

        <Grid container spacing={2}>
          {/* Modalités d'entrée */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <FlashIcon />
                Modalités Actives
              </Typography>
              
              <Grid container spacing={1}>
                {Object.entries(modalityData).map(([key, modality]) => (
                  <Grid item xs={4} key={key}>
                    <Paper 
                      sx={{ 
                        p: 1.5, 
                        textAlign: 'center',
                        backgroundColor: modality.active ? `${modality.color}33` : 'rgba(255,255,255,0.05)',
                        border: modality.active ? `2px solid ${modality.color}` : '1px solid rgba(255,255,255,0.1)',
                        transition: 'all 0.3s ease'
                      }}
                    >
                      <Typography variant="h4">
                        {modality.icon}
                      </Typography>
                      <Typography variant="caption" display="block">
                        {modality.name}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={modality.confidence * 100}
                        sx={{ 
                          mt: 0.5, 
                          height: 4, 
                          borderRadius: 2,
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: modality.color
                          }
                        }}
                      />
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Grid>

          {/* Analyse neurale */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PatternIcon />
                Patterns Neuraux
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  État Mental: {NEURAL_PATTERNS[currentNeuralPattern].name}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {NEURAL_PATTERNS[currentNeuralPattern].brainwaves}
                </Typography>
              </Box>
              
              <canvas 
                ref={neuralCanvasRef}
                style={{ 
                  width: '100%', 
                  height: '120px',
                  border: '1px solid #333',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(0,0,0,0.3)'
                }}
              />
              
              <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {Object.entries(NEURAL_PATTERNS).map(([key, pattern]) => (
                  <Chip
                    key={key}
                    label={pattern.name}
                    size="small"
                    variant={currentNeuralPattern === key ? "filled" : "outlined"}
                    sx={{
                      color: pattern.color,
                      borderColor: pattern.color,
                      ...(currentNeuralPattern === key && {
                        backgroundColor: pattern.color + '33'
                      })
                    }}
                  />
                ))}
              </Box>
            </Paper>
          </Grid>

          {/* Contrôles et paramètres */}
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SettingsIcon />
                  Paramètres de l'Interface
                </Typography>
              </AccordionSummary>
              
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={neuralSync}
                          onChange={(e) => setNeuralSync(e.target.checked)}
                        />
                      }
                      label="Synchronisation Neurale"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={adaptiveMode}
                          onChange={(e) => setAdaptiveMode(e.target.checked)}
                        />
                      }
                      label="Mode Adaptatif"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Typography gutterBottom>Sensibilité Neurale</Typography>
                    <Slider
                      value={neuralActivity}
                      onChange={(e, val) => setNeuralActivity(val)}
                      min={0}
                      max={1}
                      step={0.1}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(val) => `${Math.round(val * 100)}%`}
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    {voiceCommand && (
                      <Alert severity="info" sx={{ mb: 1 }}>
                        Commande vocale détectée: "{voiceCommand}"
                      </Alert>
                    )}
                    
                    {gestureBuffer.length > 0 && (
                      <Alert severity="success">
                        Geste détecté: {gestureBuffer.length} points
                      </Alert>
                    )}
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

export default NeuralInterface;