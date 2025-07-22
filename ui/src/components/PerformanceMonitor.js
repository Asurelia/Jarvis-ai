/**
 * ⚡ JARVIS - Moniteur de Performance Avancé
 * Interface pour les optimisations Web Workers et WASM
 */
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { 
  Box, Card, CardContent, Typography, Grid, Paper, Switch, 
  FormControlLabel, Button, LinearProgress, Chip, Badge,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Accordion, AccordionSummary, AccordionDetails, Alert
} from '@mui/material';
import { 
  ExpandMore as ExpandMoreIcon, Speed as SpeedIcon,
  Memory as MemoryIcon, Gpu as GpuIcon, Group as WorkersIcon,
  Science as WasmIcon, PlayArrow as PlayIcon, Assessment as StatsIcon
} from '@mui/icons-material';
import { performanceOptimizer } from '../utils/PerformanceOptimizer';
import * as THREE from 'three';

function PerformanceMonitor({ isEnabled = true, autoOptimize = true }) {
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  
  const [isInitialized, setIsInitialized] = useState(false);
  const [stats, setStats] = useState(null);
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [realtimeMetrics, setRealtimeMetrics] = useState({
    cpuUsage: 0,
    memoryUsage: 0,
    gpuUsage: 0,
    workerLoad: 0
  });
  const [optimizationLevel, setOptimizationLevel] = useState('balanced');
  const [capabilities, setCapabilities] = useState({
    webWorkers: true,
    webAssembly: false,
    webGL: false,
    sharedArrayBuffer: false
  });

  // Initialisation du système d'optimisation
  useEffect(() => {
    if (!isEnabled) return;

    const initializeOptimizer = async () => {
      try {
        await performanceOptimizer.initialize();
        setIsInitialized(true);
        
        // Vérifier les capacités du navigateur
        checkBrowserCapabilities();
        
        console.log('✅ Performance Monitor initialized');
      } catch (error) {
        console.error('❌ Performance Monitor initialization failed:', error);
      }
    };

    initializeOptimizer();
  }, [isEnabled]);

  // Vérification des capacités du navigateur
  const checkBrowserCapabilities = useCallback(() => {
    const caps = {
      webWorkers: typeof Worker !== 'undefined',
      webAssembly: typeof WebAssembly !== 'undefined',
      webGL: (() => {
        const canvas = document.createElement('canvas');
        return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
      })(),
      sharedArrayBuffer: typeof SharedArrayBuffer !== 'undefined'
    };

    setCapabilities(caps);
  }, []);

  // Mise à jour des statistiques en temps réel
  useEffect(() => {
    if (!isInitialized) return;

    const updateStats = () => {
      const currentStats = performanceOptimizer.getPerformanceStats();
      setStats(currentStats);

      // Simulation de métriques temps réel
      setRealtimeMetrics({
        cpuUsage: Math.random() * 100,
        memoryUsage: performance.memory ? 
          (performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize) * 100 : 
          Math.random() * 100,
        gpuUsage: Math.random() * 100,
        workerLoad: (currentStats.workers.activeWorkers / currentStats.workers.maxWorkers) * 100
      });
    };

    updateStats();
    const interval = setInterval(updateStats, 1000);

    return () => clearInterval(interval);
  }, [isInitialized]);

  // Animation des métriques de performance
  useEffect(() => {
    if (!canvasRef.current || !isEnabled) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = 600;
    canvas.height = 200;

    const metricsHistory = {
      cpu: [],
      memory: [],
      gpu: [],
      workers: []
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Fond dégradé
      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, 'rgba(0,0,0,0.8)');
      gradient.addColorStop(1, 'rgba(0,0,0,0.2)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Ajouter nouvelles données
      metricsHistory.cpu.push(realtimeMetrics.cpuUsage);
      metricsHistory.memory.push(realtimeMetrics.memoryUsage);
      metricsHistory.gpu.push(realtimeMetrics.gpuUsage);
      metricsHistory.workers.push(realtimeMetrics.workerLoad);

      // Limiter l'historique
      Object.keys(metricsHistory).forEach(key => {
        if (metricsHistory[key].length > 120) {
          metricsHistory[key].shift();
        }
      });

      // Dessiner les graphiques
      const colors = {
        cpu: '#FF5722',
        memory: '#2196F3', 
        gpu: '#4CAF50',
        workers: '#FF9800'
      };

      Object.entries(metricsHistory).forEach(([metric, data], index) => {
        if (data.length < 2) return;

        ctx.strokeStyle = colors[metric];
        ctx.lineWidth = 2;
        ctx.beginPath();

        data.forEach((value, i) => {
          const x = (i / data.length) * canvas.width;
          const y = canvas.height - (value / 100) * canvas.height;
          
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        });

        ctx.stroke();

        // Légende
        ctx.fillStyle = colors[metric];
        ctx.font = '12px monospace';
        const label = `${metric.toUpperCase()}: ${Math.round(data[data.length - 1] || 0)}%`;
        ctx.fillText(label, 10, 20 + index * 20);
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [realtimeMetrics, isEnabled]);

  // Test de performance
  const runPerformanceTest = useCallback(async () => {
    if (!isInitialized) return;

    setIsRunningTest(true);
    setTestResults(null);

    try {
      const results = await performanceOptimizer.runPerformanceTest();
      setTestResults(results);
    } catch (error) {
      console.error('Performance test failed:', error);
    } finally {
      setIsRunningTest(false);
    }
  }, [isInitialized]);

  // Démonstration IA
  const runAIDemo = useCallback(async (useGPU = false, useWASM = false) => {
    if (!isInitialized) return;

    const demoData = {
      input: [0.8, 0.2, 0.5, 0.9],
      weights: [
        [[0.1, 0.3, 0.2], [0.4, 0.1, 0.6], [0.3, 0.8, 0.2], [0.7, 0.1, 0.4]],
        [[0.5, 0.2], [0.3, 0.7], [0.1, 0.9]]
      ],
      biases: [[0.1, 0.2, 0.1], [0.05, 0.15]]
    };

    try {
      const startTime = performance.now();
      const result = await performanceOptimizer.processAI(
        demoData, 
        'neural_network', 
        useGPU, 
        useWASM
      );
      const duration = performance.now() - startTime;

      console.log(`🧠 AI Demo completed in ${duration.toFixed(2)}ms:`, result);
      
      // Afficher notification de succès
      alert(`IA Demo: ${duration.toFixed(2)}ms - ${useGPU ? 'GPU' : useWASM ? 'WASM' : 'Worker'}`);
    } catch (error) {
      console.error('AI demo failed:', error);
      alert('AI Demo failed: ' + error.message);
    }
  }, [isInitialized]);

  if (!isEnabled) return null;

  return (
    <Card sx={{ mb: 2, backgroundColor: 'rgba(0,0,0,0.8)' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ color: '#FF5722', display: 'flex', alignItems: 'center', gap: 1 }}>
          <SpeedIcon />
          ⚡ Moniteur de Performance Avancé
          {isInitialized && <Badge color="success" variant="dot" />}
        </Typography>

        <Grid container spacing={2}>
          {/* Capacités du système */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <StatsIcon />
                Capacités Système
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {Object.entries(capabilities).map(([capability, supported]) => (
                  <Box key={capability} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">
                      {capability.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                    </Typography>
                    <Chip 
                      label={supported ? 'Supporté' : 'Non supporté'}
                      color={supported ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                ))}
              </Box>

              {stats && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    État des Workers
                  </Typography>
                  <Typography variant="caption" display="block">
                    Actifs: {stats.workers.activeWorkers}/{stats.workers.maxWorkers}
                  </Typography>
                  <Typography variant="caption" display="block">
                    File d'attente: {stats.workers.queuedTasks}
                  </Typography>
                  
                  {stats.gpu.initialized && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        GPU Computing
                      </Typography>
                      <Typography variant="caption" display="block">
                        Programmes: {stats.gpu.programs}
                      </Typography>
                      <Typography variant="caption" display="block">
                        Texture Max: {stats.gpu.maxTextureSize}px
                      </Typography>
                    </Box>
                  )}
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Métriques temps réel */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MemoryIcon />
                Métriques Temps Réel
              </Typography>
              
              <canvas 
                ref={canvasRef}
                style={{ 
                  width: '100%', 
                  height: '150px',
                  border: '1px solid #333',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(0,0,0,0.3)'
                }}
              />

              <Grid container spacing={2} sx={{ mt: 1 }}>
                {Object.entries(realtimeMetrics).map(([metric, value]) => (
                  <Grid item xs={3} key={metric}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" sx={{ 
                        color: metric === 'cpuUsage' ? '#FF5722' :
                               metric === 'memoryUsage' ? '#2196F3' :
                               metric === 'gpuUsage' ? '#4CAF50' : '#FF9800'
                      }}>
                        {Math.round(value)}%
                      </Typography>
                      <Typography variant="caption">
                        {metric.replace('Usage', '').replace('Load', ' Load').toUpperCase()}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Grid>

          {/* Tests de performance */}
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PlayIcon />
                  Tests de Performance et Démos IA
                </Typography>
              </AccordionSummary>
              
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Button
                        variant="contained"
                        onClick={runPerformanceTest}
                        disabled={isRunningTest || !isInitialized}
                        startIcon={isRunningTest ? <LinearProgress /> : <PlayIcon />}
                        sx={{ backgroundColor: '#FF5722' }}
                      >
                        {isRunningTest ? 'Test en cours...' : 'Lancer Test Performance'}
                      </Button>

                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => runAIDemo(false, false)}
                          disabled={!isInitialized}
                          startIcon={<WorkersIcon />}
                        >
                          Demo IA (Worker)
                        </Button>
                        
                        <Button
                          variant="outlined" 
                          size="small"
                          onClick={() => runAIDemo(true, false)}
                          disabled={!isInitialized || !capabilities.webGL}
                          startIcon={<GpuIcon />}
                        >
                          Demo IA (GPU)
                        </Button>
                        
                        <Button
                          variant="outlined"
                          size="small" 
                          onClick={() => runAIDemo(false, true)}
                          disabled={!isInitialized || !capabilities.webAssembly}
                          startIcon={<WasmIcon />}
                        >
                          Demo IA (WASM)
                        </Button>
                      </Box>
                    </Box>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    {testResults && (
                      <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.3)' }}>
                        <Typography variant="h6" gutterBottom>
                          Résultats des Tests
                        </Typography>
                        
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Méthode</TableCell>
                                <TableCell align="right">Temps (ms)</TableCell>
                                <TableCell align="right">Performance</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {Object.entries(testResults).map(([method, time]) => {
                                const fastest = Math.min(...Object.values(testResults));
                                const speedup = fastest / time;
                                
                                return (
                                  <TableRow key={method}>
                                    <TableCell>
                                      {method.toUpperCase()}
                                    </TableCell>
                                    <TableCell align="right">
                                      {time.toFixed(2)}
                                    </TableCell>
                                    <TableCell align="right">
                                      <Chip
                                        label={`${speedup.toFixed(1)}x`}
                                        size="small"
                                        color={speedup > 0.9 ? 'success' : speedup > 0.5 ? 'warning' : 'error'}
                                      />
                                    </TableCell>
                                  </TableRow>
                                );
                              })}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Paper>
                    )}

                    {stats?.metrics && (
                      <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.3)', mt: 2 }}>
                        <Typography variant="h6" gutterBottom>
                          Métriques d'Opérations
                        </Typography>
                        
                        {Object.entries(stats.metrics).map(([operation, metric]) => (
                          <Box key={operation} sx={{ mb: 1 }}>
                            <Typography variant="subtitle2">
                              {operation.replace(/-/g, ' ').toUpperCase()}
                            </Typography>
                            <Typography variant="caption" display="block">
                              Moy: {metric.avg.toFixed(2)}ms | 
                              Min: {metric.min.toFixed(2)}ms | 
                              Max: {metric.max.toFixed(2)}ms | 
                              Count: {metric.count}
                            </Typography>
                          </Box>
                        ))}
                      </Paper>
                    )}
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Grid>

          {/* Paramètres d'optimisation */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.5)' }}>
              <Typography variant="h6" gutterBottom>
                Paramètres d'Optimisation
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={autoOptimize}
                      onChange={(e) => setOptimizationLevel(e.target.checked ? 'auto' : 'manual')}
                    />
                  }
                  label="Optimisation Automatique"
                />

                <Box sx={{ display: 'flex', gap: 1 }}>
                  {['low', 'balanced', 'high', 'maximum'].map(level => (
                    <Chip
                      key={level}
                      label={level.charAt(0).toUpperCase() + level.slice(1)}
                      onClick={() => setOptimizationLevel(level)}
                      variant={optimizationLevel === level ? 'filled' : 'outlined'}
                      color={
                        level === 'low' ? 'default' :
                        level === 'balanced' ? 'primary' :
                        level === 'high' ? 'warning' : 'error'
                      }
                    />
                  ))}
                </Box>
              </Box>

              <Alert severity="info" sx={{ mt: 2 }}>
                💡 Les optimisations s'adaptent automatiquement aux capacités du navigateur.
                Les calculs intensifs utilisent Web Workers, WASM et GPU Computing selon disponibilité.
              </Alert>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

export default PerformanceMonitor;