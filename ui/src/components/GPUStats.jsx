/**
 * 🎮 JARVIS GPU Stats - Monitoring AMD RX 7800 XT
 * Interface holographique pour les statistiques GPU en temps réel
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Grid, 
  LinearProgress, 
  Chip,
  Alert,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Thermostat as ThermoIcon,
  ElectricBolt as PowerIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as VisibilityIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';

// Hook personnalisé pour les stats GPU
const useGPUStats = () => {
  const [stats, setStats] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const wsRef = useRef(null);

  const connectWebSocket = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//localhost:5009/ws/gpu-stats`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('🔗 WebSocket GPU Stats connecté');
        setConnected(true);
        setError(null);
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'gpu_stats' && data.data) {
            setStats(data.data);
            
            // Maintenir un historique des 60 dernières secondes
            setHistory(prev => {
              const newHistory = [...prev, {
                timestamp: data.data.timestamp,
                utilization: data.data.utilization,
                temperature: data.data.temperature,
                memory_utilization: data.data.memory_utilization
              }];
              
              // Garder seulement les 60 dernières entrées
              return newHistory.slice(-60);
            });
          }
        } catch (err) {
          console.error('Erreur parsing WebSocket data:', err);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('📡 WebSocket GPU Stats déconnecté');
        setConnected(false);
        
        // Tentative de reconnexion après 3 secondes
        setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current.onerror = (err) => {
        console.error('❌ Erreur WebSocket GPU Stats:', err);
        setError('Erreur de connexion au service GPU');
        setConnected(false);
      };
      
    } catch (err) {
      console.error('❌ Erreur création WebSocket:', err);
      setError('Impossible de se connecter au service GPU');
    }
  }, []);

  // Récupération initiale des stats via REST API
  const fetchInitialStats = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:5009/gpu/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.warn('Stats GPU initiales non disponibles:', err);
    }
  }, []);

  useEffect(() => {
    fetchInitialStats();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket, fetchInitialStats]);

  return { stats, connected, error, history };
};

// Composant de barre de progression avec style holographique
const HolographicProgressBar = ({ value, max = 100, color = 'primary', label, unit = '%' }) => {
  const percentage = Math.min(100, (value / max) * 100);
  
  const getColorByValue = (val) => {
    if (val < 30) return '#00ff88'; // Vert
    if (val < 70) return '#00d4ff'; // Bleu
    if (val < 85) return '#ff9500'; // Orange
    return '#ff3b30'; // Rouge
  };

  const barColor = getColorByValue(percentage);

  return (
    <Box sx={{ width: '100%', mb: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" sx={{ color: barColor, fontFamily: 'Orbitron' }}>
          {label}
        </Typography>
        <Typography variant="body2" sx={{ color: barColor, fontFamily: 'Orbitron' }}>
          {value.toFixed(1)}{unit}
        </Typography>
      </Box>
      
      <Box sx={{ position: 'relative', height: 12, borderRadius: 6, overflow: 'hidden' }}>
        {/* Fond avec effet holographique */}
        <Box
          sx={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            background: `linear-gradient(90deg, 
              rgba(0, 212, 255, 0.1) 0%, 
              rgba(0, 212, 255, 0.05) 100%)`,
            border: '1px solid rgba(0, 212, 255, 0.3)',
            borderRadius: 6,
          }}
        />
        
        {/* Barre de progression */}
        <Box
          sx={{
            position: 'absolute',
            width: `${percentage}%`,
            height: '100%',
            background: `linear-gradient(90deg, 
              ${barColor} 0%, 
              ${barColor}80 100%)`,
            borderRadius: 6,
            boxShadow: `0 0 10px ${barColor}50, inset 0 0 10px ${barColor}30`,
            animation: 'pulse 2s infinite',
            transition: 'width 0.5s ease-in-out',
            '@keyframes pulse': {
              '0%, 100%': { opacity: 1 },
              '50%': { opacity: 0.8 }
            }
          }}
        />
        
        {/* Effet de scan */}
        <Box
          sx={{
            position: 'absolute',
            width: '20px',
            height: '100%',
            background: `linear-gradient(90deg, 
              transparent 0%, 
              ${barColor} 50%, 
              transparent 100%)`,
            animation: 'scan 3s linear infinite',
            '@keyframes scan': {
              '0%': { left: '-20px' },
              '100%': { left: '100%' }
            }
          }}
        />
      </Box>
    </Box>
  );
};

// Composant principal GPUStats
function GPUStats({ className = "" }) {
  const { stats, connected, error, history } = useGPUStats();
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Animation du graphique temps réel
  useEffect(() => {
    if (!canvasRef.current || !history.length) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Configuration du canvas
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    const animate = () => {
      ctx.clearRect(0, 0, rect.width, rect.height);
      
      // Fond dégradé holographique
      const gradient = ctx.createLinearGradient(0, 0, 0, rect.height);
      gradient.addColorStop(0, 'rgba(0, 212, 255, 0.1)');
      gradient.addColorStop(0.5, 'rgba(0, 212, 255, 0.05)');
      gradient.addColorStop(1, 'rgba(0, 18, 32, 0.8)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, rect.width, rect.height);
      
      if (history.length < 2) {
        animationFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      // Dessiner les courbes
      const metrics = [
        { data: history.map(h => h.utilization), color: '#00d4ff', label: 'GPU' },
        { data: history.map(h => h.temperature), color: '#ff9500', label: 'Temp', scale: 100 },
        { data: history.map(h => h.memory_utilization), color: '#00ff88', label: 'VRAM' }
      ];

      metrics.forEach((metric, index) => {
        ctx.strokeStyle = metric.color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        const scale = metric.scale || 100;
        
        metric.data.forEach((value, i) => {
          const x = (i / (history.length - 1)) * rect.width;
          const y = rect.height - (value / scale) * rect.height;
          
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        });
        
        ctx.stroke();
        
        // Ajouter un effet de lueur
        ctx.shadowColor = metric.color;
        ctx.shadowBlur = 10;
        ctx.stroke();
        ctx.shadowBlur = 0;
        
        // Légende
        ctx.fillStyle = metric.color;
        ctx.font = '10px Orbitron, monospace';
        ctx.fillText(
          `${metric.label}: ${metric.data[metric.data.length - 1]?.toFixed(1) || 0}${metric.scale ? '°C' : '%'}`,
          10,
          20 + index * 15
        );
      });
      
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [history]);

  // Fonction pour obtenir la couleur de température
  const getTempColor = (temp) => {
    if (temp < 50) return '#00ff88'; // Vert
    if (temp < 70) return '#00d4ff'; // Bleu
    if (temp < 80) return '#ff9500'; // Orange
    return '#ff3b30'; // Rouge
  };

  if (error) {
    return (
      <Card className={`jarvis-panel ${className}`}>
        <CardContent>
          <Alert severity="error" sx={{ backgroundColor: 'rgba(255, 59, 48, 0.1)' }}>
            🚨 {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`jarvis-panel ${className}`} sx={{ mb: 2 }}>
      <CardContent>
        {/* En-tête */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography 
            variant="h5" 
            className="jarvis-text-glow"
            sx={{ 
              fontFamily: 'Orbitron', 
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }}
          >
            <MemoryIcon sx={{ fontSize: 28 }} />
            🎮 GPU MONITORING
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              icon={connected ? <VisibilityIcon /> : <CircularProgress size={14} />}
              label={connected ? 'CONNECTÉ' : 'CONNEXION...'}
              variant="filled"
              sx={{
                backgroundColor: connected ? 'rgba(0, 255, 136, 0.2)' : 'rgba(255, 149, 0, 0.2)',
                color: connected ? '#00ff88' : '#ff9500',
                fontFamily: 'Orbitron',
                fontWeight: 600,
                border: `1px solid ${connected ? '#00ff88' : '#ff9500'}`,
                '& .MuiChip-icon': {
                  color: connected ? '#00ff88' : '#ff9500'
                }
              }}
            />
          </Box>
        </Box>

        {stats ? (
          <Grid container spacing={3}>
            {/* Informations GPU principales */}
            <Grid item xs={12} md={6}>
              <Paper className="jarvis-panel" sx={{ p: 2, height: '100%' }}>
                <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff', fontFamily: 'Orbitron' }}>
                  📊 STATISTIQUES TEMPS RÉEL
                </Typography>
                
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" sx={{ color: '#fff', opacity: 0.8, mb: 1 }}>
                    {stats.name}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#00d4ff' }}>
                    Driver: {stats.driver_version}
                  </Typography>
                </Box>

                {/* Utilisation GPU */}
                <HolographicProgressBar 
                  value={stats.utilization} 
                  label="🔥 UTILISATION GPU"
                  color="primary"
                />

                {/* Température */}
                <HolographicProgressBar 
                  value={stats.temperature} 
                  max={100}
                  label="🌡️ TEMPÉRATURE"
                  unit="°C"
                />

                {/* Utilisation VRAM */}
                <HolographicProgressBar 
                  value={stats.memory_utilization} 
                  label="🧠 UTILISATION VRAM"
                />

                {/* Informations additionnelles */}
                <Grid container spacing={2} sx={{ mt: 2 }}>
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center', p: 1 }}>
                      <Typography variant="h6" sx={{ color: '#00d4ff', fontFamily: 'Orbitron' }}>
                        {stats.core_clock} MHz
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#fff', opacity: 0.7 }}>
                        GPU Clock
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center', p: 1 }}>
                      <Typography variant="h6" sx={{ color: '#00ff88', fontFamily: 'Orbitron' }}>
                        {stats.memory_clock} MHz
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#fff', opacity: 0.7 }}>
                        Memory Clock
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center', p: 1 }}>
                      <Typography variant="h6" sx={{ color: '#ff9500', fontFamily: 'Orbitron' }}>
                        {stats.power_usage.toFixed(0)}W
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#fff', opacity: 0.7 }}>
                        Power Usage
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center', p: 1 }}>
                      <Typography variant="h6" sx={{ color: '#00d4ff', fontFamily: 'Orbitron' }}>
                        {stats.fan_speed}%
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#fff', opacity: 0.7 }}>
                        Fan Speed
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Graphique temps réel */}
            <Grid item xs={12} md={6}>
              <Paper className="jarvis-panel" sx={{ p: 2, height: '100%' }}>
                <Typography variant="h6" sx={{ mb: 2, color: '#00d4ff', fontFamily: 'Orbitron' }}>
                  📈 GRAPHIQUE TEMPS RÉEL
                </Typography>
                
                <Box sx={{ position: 'relative', height: 200, mb: 2 }}>
                  <canvas
                    ref={canvasRef}
                    style={{
                      width: '100%',
                      height: '100%',
                      border: '1px solid rgba(0, 212, 255, 0.3)',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(0, 18, 32, 0.5)'
                    }}
                  />
                </Box>

                {/* Métriques de mémoire */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" sx={{ color: '#00ff88', mb: 1, fontFamily: 'Orbitron' }}>
                    💾 MÉMOIRE VIDÉO
                  </Typography>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" sx={{ color: '#fff', opacity: 0.8 }}>
                      Utilisée: {(stats.memory_used / 1024).toFixed(1)} GB
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#fff', opacity: 0.8 }}>
                      Total: {(stats.memory_total / 1024).toFixed(1)} GB
                    </Typography>
                  </Box>
                  
                  <LinearProgress
                    variant="determinate"
                    value={stats.memory_utilization}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: 'rgba(0, 255, 136, 0.1)',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: '#00ff88',
                        borderRadius: 4,
                        boxShadow: '0 0 10px rgba(0, 255, 136, 0.5)'
                      }
                    }}
                  />
                </Box>
              </Paper>
            </Grid>

            {/* Statut et alertes */}
            <Grid item xs={12}>
              <Accordion className="jarvis-panel">
                <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: '#00d4ff' }} />}>
                  <Typography variant="h6" sx={{ color: '#00d4ff', fontFamily: 'Orbitron', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TimelineIcon />
                    📋 DÉTAILS & HISTORIQUE
                  </Typography>
                </AccordionSummary>
                
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" sx={{ color: '#00ff88', mb: 1 }}>
                        🔧 État du Système
                      </Typography>
                      
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Chip
                          label={`STATUT: ${stats.status.toUpperCase()}`}
                          variant="filled"
                          sx={{
                            backgroundColor: stats.status === 'healthy' ? 'rgba(0, 255, 136, 0.2)' : 'rgba(255, 149, 0, 0.2)',
                            color: stats.status === 'healthy' ? '#00ff88' : '#ff9500',
                            fontFamily: 'Orbitron',
                            fontWeight: 600
                          }}
                        />
                        
                        <Typography variant="body2" sx={{ color: '#fff', opacity: 0.7 }}>
                          Dernière mise à jour: {new Date(stats.timestamp * 1000).toLocaleTimeString()}
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" sx={{ color: '#00ff88', mb: 1 }}>
                        ⚠️ Alertes Thermiques
                      </Typography>
                      
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {stats.temperature > 80 && (
                          <Alert severity="warning" sx={{ backgroundColor: 'rgba(255, 149, 0, 0.1)' }}>
                            🔥 Température élevée: {stats.temperature.toFixed(1)}°C
                          </Alert>
                        )}
                        
                        {stats.temperature > 90 && (
                          <Alert severity="error" sx={{ backgroundColor: 'rgba(255, 59, 48, 0.1)' }}>
                            🚨 ALERTE: Température critique!
                          </Alert>
                        )}
                        
                        {stats.utilization > 95 && (
                          <Alert severity="info" sx={{ backgroundColor: 'rgba(0, 212, 255, 0.1)' }}>
                            ⚡ GPU à pleine charge
                          </Alert>
                        )}
                        
                        {stats.temperature < 80 && stats.utilization < 95 && (
                          <Alert severity="success" sx={{ backgroundColor: 'rgba(0, 255, 136, 0.1)' }}>
                            ✅ Fonctionnement optimal
                          </Alert>
                        )}
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>
          </Grid>
        ) : (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress sx={{ color: '#00d4ff', mb: 2 }} />
            <Typography variant="body1" sx={{ color: '#00d4ff', fontFamily: 'Orbitron' }}>
              📡 Connexion au GPU en cours...
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export default GPUStats;