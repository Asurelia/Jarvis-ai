/**
 * 🤖 JARVIS UI - Dashboard Principal
 * Vue d'ensemble complète de l'état de JARVIS
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Avatar,
  IconButton,
  Button,
  Divider,
  useTheme,
  alpha
} from '@mui/material';

// Icons
import {
  Computer as SystemIcon,
  Visibility as VisionIcon,
  Mic as VoiceIcon,
  Memory as MemoryIcon,
  Speed as PerformanceIcon,
  TrendingUp as TrendingUpIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Screenshot as ScreenshotIcon,
  Psychology as AIIcon,
  AutoAwesome as AutocompleteIcon,
  Security as SecurityIcon,
  Timeline as ActivityIcon,
  Storage as StorageIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';
import { useJarvisAPI } from '../hooks/useJarvisAPI';

// Composant de carte de statut de module
function ModuleStatusCard({ title, icon: Icon, status, description, stats, color = 'primary' }) {
  const theme = useTheme();
  
  const getStatusColor = () => {
    switch (status) {
      case 'active':
      case 'ready':
        return theme.palette.success.main;
      case 'error':
        return theme.palette.error.main;
      case 'loading':
        return theme.palette.warning.main;
      default:
        return theme.palette.text.disabled;
    }
  };
  
  const getStatusText = () => {
    switch (status) {
      case 'active':
      case 'ready':
        return 'Actif';
      case 'error':
        return 'Erreur';
      case 'loading':
        return 'Chargement';
      default:
        return 'Inactif';
    }
  };
  
  return (
    <Card
      sx={{
        height: '100%',
        background: `linear-gradient(135deg, ${alpha(theme.palette[color].main, 0.05)} 0%, ${alpha(theme.palette.background.paper, 0.8)} 100%)`,
        border: `1px solid ${alpha(theme.palette[color].main, 0.2)}`,
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[8],
          border: `1px solid ${alpha(theme.palette[color].main, 0.4)}`
        }
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar
              sx={{
                backgroundColor: alpha(theme.palette[color].main, 0.1),
                color: theme.palette[color].main,
                width: 40,
                height: 40
              }}
            >
              <Icon fontSize="small" />
            </Avatar>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                {title}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                {description}
              </Typography>
            </Box>
          </Box>
          
          <Chip
            label={getStatusText()}
            size="small"
            sx={{
              backgroundColor: alpha(getStatusColor(), 0.1),
              color: getStatusColor(),
              border: `1px solid ${alpha(getStatusColor(), 0.3)}`,
              fontWeight: 500
            }}
          />
        </Box>
        
        {stats && (
          <Box sx={{ mt: 2 }}>
            {Object.entries(stats).map(([key, value]) => (
              <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {key}
                </Typography>
                <Typography variant="caption" sx={{ fontWeight: 500 }}>
                  {value}
                </Typography>
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

// Composant de métrique avec graphique
function MetricCard({ title, value, unit, trend, icon: Icon, color = 'primary' }) {
  const theme = useTheme();
  
  return (
    <Card
      sx={{
        background: `linear-gradient(135deg, ${alpha(theme.palette[color].main, 0.05)} 0%, ${alpha(theme.palette.background.paper, 0.8)} 100%)`,
        border: `1px solid ${alpha(theme.palette[color].main, 0.2)}`
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette[color].main }}>
              {value}
              <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
                {unit}
              </Typography>
            </Typography>
            {trend !== undefined && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUpIcon 
                  fontSize="small" 
                  sx={{ 
                    color: trend >= 0 ? theme.palette.success.main : theme.palette.error.main,
                    mr: 0.5 
                  }} 
                />
                <Typography 
                  variant="caption" 
                  sx={{ 
                    color: trend >= 0 ? theme.palette.success.main : theme.palette.error.main,
                    fontWeight: 500 
                  }}
                >
                  {trend >= 0 ? '+' : ''}{trend}%
                </Typography>
              </Box>
            )}
          </Box>
          
          <Avatar
            sx={{
              backgroundColor: alpha(theme.palette[color].main, 0.1),
              color: theme.palette[color].main,
              width: 48,
              height: 48
            }}
          >
            <Icon />
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );
}

// Composant de logs récents
function RecentLogsCard() {
  const theme = useTheme();
  const { state } = useJarvis();
  
  const recentLogs = state.logs.slice(0, 5);
  
  const getLogColor = (level) => {
    switch (level) {
      case 'error':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'success':
        return theme.palette.success.main;
      default:
        return theme.palette.info.main;
    }
  };
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Activité Récente
          </Typography>
          <IconButton size="small">
            <ActivityIcon fontSize="small" />
          </IconButton>
        </Box>
        
        <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
          {recentLogs.length > 0 ? (
            recentLogs.map((log) => (
              <Box key={log.id} sx={{ mb: 1.5, pb: 1.5, borderBottom: `1px solid ${theme.palette.divider}` }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Box
                    sx={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      backgroundColor: getLogColor(log.level)
                    }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </Typography>
                  <Chip
                    label={log.source}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: '0.6rem', height: 20 }}
                  />
                </Box>
                <Typography variant="body2" sx={{ fontSize: '0.8rem', lineHeight: 1.4 }}>
                  {log.message}
                </Typography>
              </Box>
            ))
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
              Aucune activité récente
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

function Dashboard() {
  const theme = useTheme();
  const { state, actions, isWebMode } = useJarvis();
  const { takeScreenshot, refreshSystemStatus, speakText, loading, isConnected } = useJarvisAPI();
  const [systemInfo, setSystemInfo] = useState(null);
  
  // Charger les informations système
  useEffect(() => {
    // Simuler le chargement des infos système
    setSystemInfo({
      cpu: '65%',
      memory: '8.2 GB / 16 GB',
      uptime: formatUptime(state.jarvis.uptime)
    });
  }, [state.jarvis.uptime]);
  
  // Rafraîchir le statut périodiquement
  useEffect(() => {
    if (isWebMode && isConnected) {
      const interval = setInterval(() => {
        refreshSystemStatus();
      }, 10000); // Toutes les 10 secondes
      
      return () => clearInterval(interval);
    }
  }, [isWebMode, isConnected, refreshSystemStatus]);
  
  // Actions rapides
  const handleQuickAction = async (action) => {
    try {
      switch (action) {
        case 'screenshot':
          await takeScreenshot();
          break;
        case 'voice_test':
          await speakText('Test de l\'interface vocale JARVIS. Tout fonctionne correctement.');
          break;
        case 'refresh_status':
          await refreshSystemStatus();
          break;
        default:
          console.log('Action non implémentée:', action);
      }
    } catch (error) {
      actions.addNotification('error', 'Erreur', `Action échouée: ${error.message}`);
    }
  };
  
  return (
    <Box sx={{ p: 0 }}>
      {/* En-tête du dashboard */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Bienvenue dans JARVIS
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Tableau de bord de votre assistant IA autonome
        </Typography>
      </Box>
      
      {/* Métriques principales */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Commandes Exécutées"
            value={state.stats.commandsExecuted}
            unit=""
            trend={12}
            icon={PlayIcon}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Captures d'Écran"
            value={state.stats.screenshotsTaken}
            unit=""
            trend={5}
            icon={ScreenshotIcon}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Commandes Vocales"
            value={state.stats.voiceCommands}
            unit=""
            trend={-2}
            icon={VoiceIcon}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Autocomplétion"
            value={state.stats.autocompleteUsage}
            unit="utilisations"
            trend={25}
            icon={AutocompleteIcon}
            color="success"
          />
        </Grid>
      </Grid>
      
      {/* Statut des modules */}
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
        État des Modules
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6} lg={4}>
          <ModuleStatusCard
            title="Vision"
            icon={VisionIcon}
            status={state.modules.vision.status}
            description="Capture et analyse d'écran"
            stats={{
              'Dernière capture': '2 min ago',
              'Résolution': '1920x1080',
              'FPS': '30'
            }}
            color="info"
          />
        </Grid>
        
        <Grid item xs={12} md={6} lg={4}>
          <ModuleStatusCard
            title="Interface Vocale"
            icon={VoiceIcon}
            status={state.modules.voice.status}
            description="Reconnaissance et synthèse"
            stats={{
              'Dernière commande': '5 min ago',
              'Précision': '95%',
              'Langue': 'Français'
            }}
            color="secondary"
          />
        </Grid>
        
        <Grid item xs={12} md={6} lg={4}>
          <ModuleStatusCard
            title="Mémoire"
            icon={MemoryIcon}
            status={state.modules.memory.status}
            description="Stockage et apprentissage"
            stats={{
              'Entrées': state.stats.memoryEntries,
              'Conversations': '12',
              'Taille': '45 MB'
            }}
            color="success"
          />
        </Grid>
        
        <Grid item xs={12} md={6} lg={4}>
          <ModuleStatusCard
            title="Autocomplétion"
            icon={AutocompleteIcon}
            status={state.modules.autocomplete.status}
            description="Suggestions intelligentes"
            stats={{
              'Suggestions': '1,245',
              'Précision': '87%',
              'Cache': '92% hit'
            }}
            color="warning"
          />
        </Grid>
        
        <Grid item xs={12} md={6} lg={4}>
          <ModuleStatusCard
            title="Contrôle"
            icon={SystemIcon}
            status={state.modules.control.status}
            description="Souris et clavier"
            stats={{
              'Actions/min': '12',
              'Précision': '99.8%',
              'Sandbox': state.config.sandboxMode ? 'Actif' : 'Inactif'
            }}
            color="error"
          />
        </Grid>
        
        <Grid item xs={12} md={6} lg={4}>
          <ModuleStatusCard
            title="Exécuteur"
            icon={AIIcon}
            status={state.modules.executor.status}
            description="Automation d'actions"
            stats={{
              'Séquences': '8',
              'Succès': '96%',
              'Queue': '2 pending'
            }}
            color="primary"
          />
        </Grid>
      </Grid>
      
      {/* Informations système et logs */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <RecentLogsCard />
        </Grid>
        
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Informations Système
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Statut JARVIS
                  </Typography>
                  <Chip
                    label={isConnected ? 'Connecté' : 'Déconnecté'}
                    size="small"
                    color={isConnected ? 'success' : 'error'}
                  />
                </Box>
                
                {isWebMode && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Mode
                    </Typography>
                    <Chip
                      label="Web API"
                      size="small"
                      color="info"
                      variant="outlined"
                    />
                  </Box>
                )}
                
                {loading && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Statut
                    </Typography>
                    <Chip
                      label="Chargement..."
                      size="small"
                      color="warning"
                    />
                  </Box>
                )}
                
                {state.jarvis.status === 'connected' && (
                  <>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        PID
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {state.jarvis.pid}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Temps de fonctionnement
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {formatUptime(state.jarvis.uptime)}
                      </Typography>
                    </Box>
                  </>
                )}
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                Actions Rapides
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<ScreenshotIcon />}
                  onClick={() => handleQuickAction('screenshot')}
                  disabled={!isConnected || loading}
                  size="small"
                >
                  Capture d'écran
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<VoiceIcon />}
                  onClick={() => handleQuickAction('voice_test')}
                  disabled={!isConnected || loading}
                  size="small"
                >
                  Test vocal
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<PerformanceIcon />}
                  onClick={() => handleQuickAction('refresh_status')}
                  disabled={loading}
                  size="small"
                >
                  Actualiser statut
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<SecurityIcon />}
                  onClick={actions.toggleSandboxMode}
                  size="small"
                  color={state.config.sandboxMode ? 'success' : 'warning'}
                >
                  {state.config.sandboxMode ? 'Désactiver' : 'Activer'} Sandbox
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

// Utilitaire pour formater l'uptime
function formatUptime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
}

export default Dashboard;