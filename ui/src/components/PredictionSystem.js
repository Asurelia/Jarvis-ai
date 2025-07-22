/**
 * 🔮 JARVIS - Système de Prédiction et Anticipation
 * Timeline prédictive avec analyse comportementale et suggestions proactives
 */
import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { 
  Box, Card, CardContent, Typography, Timeline, TimelineItem, TimelineSeparator, 
  TimelineConnector, TimelineContent, TimelineDot, Chip, LinearProgress,
  Grid, Paper, List, ListItem, ListItemText, ListItemIcon, Accordion,
  AccordionSummary, AccordionDetails, Avatar, Badge, IconButton
} from '@mui/material';
import { 
  ExpandMore as ExpandMoreIcon, TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon, Schedule as ScheduleIcon,
  AutoAwesome as AutoAwesomeIcon, Timeline as TimelineIcon,
  Lightbulb as LightbulbIcon, Speed as SpeedIcon
} from '@mui/icons-material';
import * as THREE from 'three';

// Types de prédictions
const PREDICTION_TYPES = {
  IMMEDIATE: {
    name: 'Immédiate',
    color: '#FF5722',
    horizon: 5, // minutes
    icon: '⚡'
  },
  SHORT_TERM: {
    name: 'Court Terme',
    color: '#FF9800', 
    horizon: 60, // minutes
    icon: '⏱️'
  },
  MEDIUM_TERM: {
    name: 'Moyen Terme',
    color: '#2196F3',
    horizon: 1440, // 24h
    icon: '📅'
  },
  LONG_TERM: {
    name: 'Long Terme',
    color: '#9C27B0',
    horizon: 10080, // 7 jours
    icon: '🔮'
  }
};

// Catégories de comportements
const BEHAVIOR_CATEGORIES = {
  WORK: {
    name: 'Travail',
    patterns: ['coding', 'meetings', 'research', 'documentation'],
    color: '#4CAF50',
    icon: '💻'
  },
  COMMUNICATION: {
    name: 'Communication',
    patterns: ['email', 'slack', 'calls', 'messages'],
    color: '#2196F3',
    icon: '💬'
  },
  LEARNING: {
    name: 'Apprentissage',
    patterns: ['tutorials', 'documentation', 'research', 'experimentation'],
    color: '#9C27B0',
    icon: '📚'
  },
  MAINTENANCE: {
    name: 'Maintenance',
    patterns: ['updates', 'backups', 'cleanup', 'optimization'],
    color: '#FF9800',
    icon: '🔧'
  },
  CREATIVE: {
    name: 'Créatif',
    patterns: ['design', 'brainstorming', 'prototyping', 'writing'],
    color: '#E91E63',
    icon: '🎨'
  }
};

// Algorithmes de prédiction
const PREDICTION_ALGORITHMS = {
  PATTERN_RECOGNITION: 'Reconnaissance de motifs',
  TEMPORAL_ANALYSIS: 'Analyse temporelle',  
  CONTEXT_AWARENESS: 'Conscience contextuelle',
  BEHAVIORAL_MODELING: 'Modélisation comportementale',
  PROBABILISTIC: 'Inférence probabiliste'
};

function PredictionSystem({
  userHistory = [],
  currentContext = {},
  onPredictionUpdate = null,
  isEnabled = true,
  visualizationMode = 'timeline'
}) {
  const timelineRef = useRef(null);
  const predictionEngineRef = useRef(null);
  const behavioralModelRef = useRef(new Map());
  
  const [predictions, setPredictions] = useState([]);
  const [behaviorPatterns, setBehaviorPatterns] = useState(new Map());
  const [confidenceScores, setConfidenceScores] = useState(new Map());
  const [suggestions, setSuggestions] = useState([]);
  const [predictionAccuracy, setPredictionAccuracy] = useState(0.75);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedTimeHorizon, setSelectedTimeHorizon] = useState('SHORT_TERM');

  // Modèle comportemental utilisateur
  const behavioralModel = useMemo(() => {
    if (!userHistory.length) return null;

    const model = {
      dailyPatterns: new Map(),
      weeklyPatterns: new Map(), 
      actionSequences: new Map(),
      contextualTriggers: new Map(),
      preferredTimes: new Map(),
      efficiency: new Map()
    };

    // Analyse des patterns temporels
    userHistory.forEach(action => {
      const hour = new Date(action.timestamp).getHours();
      const day = new Date(action.timestamp).getDay();
      const actionType = action.type || 'unknown';

      // Patterns quotidiens
      if (!model.dailyPatterns.has(hour)) {
        model.dailyPatterns.set(hour, new Map());
      }
      const hourlyActions = model.dailyPatterns.get(hour);
      hourlyActions.set(actionType, (hourlyActions.get(actionType) || 0) + 1);

      // Patterns hebdomadaires  
      if (!model.weeklyPatterns.has(day)) {
        model.weeklyPatterns.set(day, new Map());
      }
      const dailyActions = model.weeklyPatterns.get(day);
      dailyActions.set(actionType, (dailyActions.get(actionType) || 0) + 1);
    });

    return model;
  }, [userHistory]);

  // Algorithme de prédiction principale
  const predictFutureActions = useCallback(() => {
    if (!behavioralModel || !userHistory.length) return [];

    const now = Date.now();
    const currentHour = new Date().getHours();
    const currentDay = new Date().getDay();
    const predictions = [];

    // Prédictions basées sur les patterns temporels
    Object.entries(PREDICTION_TYPES).forEach(([typeKey, type]) => {
      const futureTime = now + (type.horizon * 60 * 1000);
      const futureHour = new Date(futureTime).getHours();
      
      // Actions probables à cette heure
      const hourlyPatterns = behavioralModel.dailyPatterns.get(futureHour);
      if (hourlyPatterns) {
        const sortedActions = Array.from(hourlyPatterns.entries())
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3);

        sortedActions.forEach(([action, frequency], index) => {
          const confidence = Math.min(0.9, (frequency / userHistory.length) + 0.1);
          const priority = 1 - (index * 0.2);

          predictions.push({
            id: `${typeKey}_${action}_${futureTime}`,
            type: typeKey,
            action,
            predictedTime: futureTime,
            confidence,
            priority,
            reasoning: `Pattern temporel: ${action} fréquent à ${futureHour}h`,
            algorithm: 'TEMPORAL_ANALYSIS',
            category: inferActionCategory(action)
          });
        });
      }
    });

    // Prédictions contextuelles
    if (currentContext.activeApp) {
      const contextPredictions = generateContextualPredictions(currentContext);
      predictions.push(...contextPredictions);
    }

    // Prédictions séquentielles (actions qui suivent souvent)
    const sequentialPredictions = generateSequentialPredictions(userHistory);
    predictions.push(...sequentialPredictions);

    // Tri par priorité et confiance
    return predictions
      .sort((a, b) => (b.confidence * b.priority) - (a.confidence * a.priority))
      .slice(0, 20);

  }, [behavioralModel, userHistory, currentContext]);

  // Génération de prédictions contextuelles
  const generateContextualPredictions = useCallback((context) => {
    const predictions = [];
    const now = Date.now();

    // Prédictions basées sur l'application active
    if (context.activeApp === 'vscode') {
      predictions.push({
        id: `context_vscode_${now}`,
        type: 'IMMEDIATE',
        action: 'save_file',
        predictedTime: now + (5 * 60 * 1000),
        confidence: 0.8,
        priority: 0.9,
        reasoning: 'VSCode actif, sauvegarde probable',
        algorithm: 'CONTEXT_AWARENESS',
        category: 'WORK'
      });
    }

    // Prédictions basées sur l'heure
    const hour = new Date().getHours();
    if (hour >= 9 && hour <= 17) {
      predictions.push({
        id: `context_work_hours_${now}`,
        type: 'SHORT_TERM',
        action: 'check_email',
        predictedTime: now + (30 * 60 * 1000),
        confidence: 0.7,
        priority: 0.6,
        reasoning: 'Heures de travail, vérification email probable',
        algorithm: 'CONTEXT_AWARENESS',
        category: 'COMMUNICATION'
      });
    }

    return predictions;
  }, []);

  // Génération de prédictions séquentielles
  const generateSequentialPredictions = useCallback((history) => {
    const predictions = [];
    const sequences = new Map();
    
    // Analyse des séquences d'actions
    for (let i = 0; i < history.length - 1; i++) {
      const current = history[i];
      const next = history[i + 1];
      const key = `${current.type}->${next.type}`;
      
      sequences.set(key, (sequences.get(key) || 0) + 1);
    }

    // Dernière action de l'utilisateur
    const lastAction = history[history.length - 1];
    if (lastAction) {
      // Recherche des actions qui suivent souvent
      Array.from(sequences.entries())
        .filter(([key]) => key.startsWith(lastAction.type))
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .forEach(([key, frequency]) => {
          const nextAction = key.split('->')[1];
          const confidence = Math.min(0.85, frequency / history.length + 0.2);
          
          predictions.push({
            id: `sequence_${nextAction}_${Date.now()}`,
            type: 'IMMEDIATE',
            action: nextAction,
            predictedTime: Date.now() + (10 * 60 * 1000),
            confidence,
            priority: 0.8,
            reasoning: `Séquence habituelle après ${lastAction.type}`,
            algorithm: 'PATTERN_RECOGNITION',
            category: inferActionCategory(nextAction)
          });
        });
    }

    return predictions;
  }, []);

  // Inférence de catégorie d'action
  const inferActionCategory = useCallback((action) => {
    for (const [category, data] of Object.entries(BEHAVIOR_CATEGORIES)) {
      if (data.patterns.some(pattern => action.toLowerCase().includes(pattern))) {
        return category;
      }
    }
    return 'WORK'; // Défaut
  }, []);

  // Génération de suggestions proactives
  const generateProactiveSuggestions = useCallback((predictions) => {
    const suggestions = [];
    const now = Date.now();

    // Suggestions basées sur les prédictions
    predictions.slice(0, 5).forEach(prediction => {
      if (prediction.confidence > 0.6) {
        let suggestionText = '';
        let actionable = false;

        switch (prediction.action) {
          case 'save_file':
            suggestionText = 'Sauvegarder le fichier actuel';
            actionable = true;
            break;
          case 'check_email':
            suggestionText = 'Vérifier les nouveaux emails';
            actionable = true;
            break;
          case 'commit_code':
            suggestionText = 'Faire un commit des modifications';
            actionable = true;
            break;
          case 'take_break':
            suggestionText = 'Prendre une pause (travail intensif détecté)';
            actionable = false;
            break;
          default:
            suggestionText = `Préparer: ${prediction.action}`;
        }

        suggestions.push({
          id: `suggestion_${prediction.id}`,
          text: suggestionText,
          confidence: prediction.confidence,
          category: prediction.category,
          timeframe: PREDICTION_TYPES[prediction.type].name,
          actionable,
          reasoning: prediction.reasoning
        });
      }
    });

    // Suggestions d'optimisation
    const workingSince = calculateWorkingTime();
    if (workingSince > 120) { // Plus de 2h
      suggestions.push({
        id: 'suggestion_break',
        text: 'Faire une pause (travail intensif depuis 2h+)',
        confidence: 0.9,
        category: 'MAINTENANCE',
        timeframe: 'Immédiat',
        actionable: false,
        reasoning: 'Optimisation de productivité'
      });
    }

    return suggestions;
  }, []);

  // Calcul du temps de travail
  const calculateWorkingTime = () => {
    // Simulation - dans une vraie implémentation, 
    // on analyserait l'activité système
    return Math.floor(Math.random() * 180); // 0-3h
  };

  // Moteur de prédiction principal
  useEffect(() => {
    if (!isEnabled || !userHistory.length) return;

    const runPredictionEngine = () => {
      setIsAnalyzing(true);

      // Génération des prédictions
      const newPredictions = predictFutureActions();
      setPredictions(newPredictions);

      // Calcul des scores de confiance
      const scores = new Map();
      newPredictions.forEach(pred => {
        scores.set(pred.id, pred.confidence);
      });
      setConfidenceScores(scores);

      // Génération des suggestions
      const newSuggestions = generateProactiveSuggestions(newPredictions);
      setSuggestions(newSuggestions);

      // Mise à jour de la précision
      // Dans une vraie implémentation, on comparerait avec les actions réelles
      setPredictionAccuracy(0.75 + Math.random() * 0.2);

      setIsAnalyzing(false);

      if (onPredictionUpdate) {
        onPredictionUpdate({
          predictions: newPredictions,
          suggestions: newSuggestions,
          accuracy: predictionAccuracy
        });
      }
    };

    // Exécution initiale
    runPredictionEngine();

    // Mise à jour périodique
    const interval = setInterval(runPredictionEngine, 60000); // Chaque minute

    return () => clearInterval(interval);
  }, [userHistory, currentContext, isEnabled, predictFutureActions, generateProactiveSuggestions, onPredictionUpdate, predictionAccuracy]);

  // Rendu de la timeline prédictive
  const renderPredictiveTimeline = () => {
    const filteredPredictions = predictions.filter(p => 
      selectedTimeHorizon === 'ALL' || p.type === selectedTimeHorizon
    );

    return (
      <Timeline>
        {filteredPredictions.slice(0, 8).map((prediction, index) => (
          <TimelineItem key={prediction.id}>
            <TimelineSeparator>
              <TimelineDot 
                sx={{ 
                  backgroundColor: PREDICTION_TYPES[prediction.type].color,
                  animation: prediction.confidence > 0.8 ? 'pulse 2s infinite' : 'none'
                }}
              >
                <Typography variant="caption">
                  {PREDICTION_TYPES[prediction.type].icon}
                </Typography>
              </TimelineDot>
              {index < filteredPredictions.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            
            <TimelineContent>
              <Paper sx={{ p: 2, mb: 1, backgroundColor: 'rgba(0,0,0,0.3)' }}>
                <Typography variant="h6" color="primary">
                  {prediction.action.replace(/_/g, ' ').toUpperCase()}
                </Typography>
                
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  {new Date(prediction.predictedTime).toLocaleTimeString()}
                </Typography>
                
                <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                  <Chip 
                    label={`${Math.round(prediction.confidence * 100)}% confiance`}
                    size="small" 
                    color="primary"
                    variant="outlined"
                  />
                  <Chip 
                    label={BEHAVIOR_CATEGORIES[prediction.category]?.name || 'Général'}
                    size="small"
                    sx={{ 
                      backgroundColor: BEHAVIOR_CATEGORIES[prediction.category]?.color || '#666',
                      color: 'white'
                    }}
                  />
                </Box>
                
                <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
                  {prediction.reasoning}
                </Typography>
                
                <LinearProgress 
                  variant="determinate" 
                  value={prediction.confidence * 100}
                  sx={{ mt: 1, height: 4, borderRadius: 2 }}
                />
              </Paper>
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    );
  };

  if (!isEnabled) return null;

  return (
    <Card sx={{ mb: 2, backgroundColor: 'rgba(0,0,0,0.8)' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ color: '#FF9800', display: 'flex', alignItems: 'center', gap: 1 }}>
          <TrendingUpIcon />
          🔮 Système de Prédiction et Anticipation
          {isAnalyzing && <Badge color="secondary" variant="dot" />}
        </Typography>

        <Grid container spacing={2}>
          {/* Métriques du système */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)' }}>
              <Grid container spacing={2}>
                <Grid item xs={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {predictions.length}
                    </Typography>
                    <Typography variant="caption">
                      Prédictions Actives
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" sx={{ color: '#4CAF50' }}>
                      {Math.round(predictionAccuracy * 100)}%
                    </Typography>
                    <Typography variant="caption">
                      Précision Moyenne
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" sx={{ color: '#2196F3' }}>
                      {suggestions.length}
                    </Typography>
                    <Typography variant="caption">
                      Suggestions Actives
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" sx={{ color: '#9C27B0' }}>
                      {userHistory.length}
                    </Typography>
                    <Typography variant="caption">
                      Actions Analysées
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Timeline prédictive */}
          <Grid item xs={12} md={8}>
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TimelineIcon />
                  Timeline Prédictive
                </Typography>
              </AccordionSummary>
              
              <AccordionDetails>
                <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {Object.entries(PREDICTION_TYPES).map(([key, type]) => (
                    <Chip
                      key={key}
                      label={type.name}
                      onClick={() => setSelectedTimeHorizon(key)}
                      variant={selectedTimeHorizon === key ? 'filled' : 'outlined'}
                      sx={{ 
                        color: type.color,
                        borderColor: type.color,
                        ...(selectedTimeHorizon === key && {
                          backgroundColor: type.color + '33'
                        })
                      }}
                    />
                  ))}
                  <Chip
                    label="Tout"
                    onClick={() => setSelectedTimeHorizon('ALL')}
                    variant={selectedTimeHorizon === 'ALL' ? 'filled' : 'outlined'}
                  />
                </Box>
                
                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {renderPredictiveTimeline()}
                </Box>
              </AccordionDetails>
            </Accordion>
          </Grid>

          {/* Suggestions proactives */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)', height: '100%' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AutoAwesomeIcon />
                Suggestions Proactives
              </Typography>
              
              <List>
                {suggestions.slice(0, 6).map((suggestion, index) => (
                  <ListItem 
                    key={suggestion.id} 
                    sx={{ 
                      borderLeft: `3px solid ${BEHAVIOR_CATEGORIES[suggestion.category]?.color || '#666'}`,
                      mb: 1,
                      backgroundColor: 'rgba(255,255,255,0.05)',
                      borderRadius: 1
                    }}
                  >
                    <ListItemIcon>
                      <Avatar sx={{ 
                        backgroundColor: BEHAVIOR_CATEGORIES[suggestion.category]?.color || '#666',
                        width: 32, 
                        height: 32 
                      }}>
                        <Typography variant="caption">
                          {BEHAVIOR_CATEGORIES[suggestion.category]?.icon || '💡'}
                        </Typography>
                      </Avatar>
                    </ListItemIcon>
                    
                    <ListItemText
                      primary={suggestion.text}
                      secondary={
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            {suggestion.timeframe} • {Math.round(suggestion.confidence * 100)}% confiance
                          </Typography>
                          <br />
                          <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
                            {suggestion.reasoning}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

export default PredictionSystem;