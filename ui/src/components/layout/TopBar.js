/**
 * 🤖 JARVIS UI - Top Navigation Bar
 * Barre supérieure avec contrôles et informations
 */
import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Button,
  Chip,
  Menu,
  MenuItem,
  Tooltip,
  useTheme,
  alpha
} from '@mui/material';

// Icons
import {
  Menu as MenuIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  AutoAwesome as AutocompleteIcon,
  Security as SandboxIcon,
  BugReport as DebugIcon,
  Refresh as RefreshIcon,
  MoreVert as MoreIcon,
  Screenshot as ScreenshotIcon,
  Memory as MemoryIcon,
  Speed as PerformanceIcon
} from '@mui/icons-material';

import { useJarvis } from '../../contexts/JarvisContext';

// Configuration des pages pour le titre
const pageConfig = {
  '/dashboard': { title: 'Dashboard', subtitle: 'Vue d\'ensemble de JARVIS' },
  '/vision': { title: 'Vision', subtitle: 'Capture et analyse d\'écran' },
  '/voice': { title: 'Interface Vocale', subtitle: 'Reconnaissance et synthèse' },
  '/autocomplete': { title: 'Autocomplétion', subtitle: 'Suggestions intelligentes' },
  '/memory': { title: 'Mémoire', subtitle: 'Système de mémoire persistante' },
  '/executor': { title: 'Exécuteur', subtitle: 'Automation d\'actions' },
  '/logs': { title: 'Logs Système', subtitle: 'Journaux et activité' },
  '/settings': { title: 'Paramètres', subtitle: 'Configuration JARVIS' }
};

function TopBar({ height, showMenuButton, isElectron }) {
  const theme = useTheme();
  const location = useLocation();
  const { state, actions, electronAPI } = useJarvis();
  
  // État local
  const [moreMenuAnchor, setMoreMenuAnchor] = useState(null);
  const [isExecutingCommand, setIsExecutingCommand] = useState(false);
  
  // Configuration de la page actuelle
  const currentPage = pageConfig[location.pathname] || { 
    title: 'JARVIS', 
    subtitle: 'Assistant IA Autonome' 
  };
  
  // Gestionnaires d'événements
  const handleStartStopJarvis = async () => {
    setIsExecutingCommand(true);
    
    try {
      if (state.jarvis.status === 'connected') {
        await electronAPI.stopJarvis();
      } else {
        await electronAPI.startJarvis();
      }
    } catch (error) {
      actions.addNotification('error', 'Erreur', error.message);
    } finally {
      setIsExecutingCommand(false);
    }
  };
  
  const handleTakeScreenshot = async () => {
    try {
      setIsExecutingCommand(true);
      await electronAPI.executeCommand('screenshot');
      actions.addNotification('success', 'Capture d\'écran', 'Screenshot pris avec succès');
    } catch (error) {
      actions.addNotification('error', 'Erreur', 'Impossible de prendre la capture');
    } finally {
      setIsExecutingCommand(false);
    }
  };
  
  const handleRefreshStatus = async () => {
    try {
      setIsExecutingCommand(true);
      const status = await electronAPI.getJarvisStatus();
      actions.setJarvisStatus(status.running ? 'connected' : 'disconnected', status.pid);
      actions.addNotification('info', 'Statut', 'Statut JARVIS mis à jour');
    } catch (error) {
      actions.addNotification('error', 'Erreur', 'Impossible de mettre à jour le statut');
    } finally {
      setIsExecutingCommand(false);
    }
  };
  
  const handleMoreMenuOpen = (event) => {
    setMoreMenuAnchor(event.currentTarget);
  };
  
  const handleMoreMenuClose = () => {
    setMoreMenuAnchor(null);
  };
  
  // Style de la barre
  const appBarStyle = {
    height: height,
    backgroundColor: alpha(theme.palette.background.paper, 0.9),
    backdropFilter: 'blur(10px)',
    borderBottom: `1px solid ${theme.palette.divider}`,
    boxShadow: 'none',
    position: 'fixed',
    zIndex: 1100
  };
  
  return (
    <AppBar sx={appBarStyle}>
      <Toolbar sx={{ height: height, paddingLeft: 2, paddingRight: 2 }}>
        {/* Menu burger (mobile) */}
        {showMenuButton && (
          <IconButton
            edge="start"
            color="inherit"
            onClick={actions.toggleSidebar}
            sx={{ marginRight: 2 }}
          >
            <MenuIcon />
          </IconButton>
        )}
        
        {/* Titre de la page */}
        <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box>
            <Typography
              variant="h6"
              component="h1"
              sx={{
                fontWeight: 600,
                color: theme.palette.text.primary,
                lineHeight: 1.2
              }}
            >
              {currentPage.title}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: theme.palette.text.secondary,
                fontSize: '0.75rem'
              }}
            >
              {currentPage.subtitle}
            </Typography>
          </Box>
          
          {/* Indicateurs de statut des modules */}
          <Box sx={{ display: 'flex', gap: 1, marginLeft: 2 }}>
            {Object.entries(state.modules).map(([moduleName, moduleData]) => {
              const getStatusColor = (status) => {
                switch (status) {
                  case 'active':
                  case 'ready':
                    return 'success';
                  case 'error':
                    return 'error';
                  case 'loading':
                    return 'warning';
                  default:
                    return 'default';
                }
              };
              
              return (
                <Tooltip
                  key={moduleName}
                  title={`${moduleName}: ${moduleData.status}`}
                >
                  <Chip
                    label={moduleName}
                    size="small"
                    color={getStatusColor(moduleData.status)}
                    variant="outlined"
                    sx={{
                      fontSize: '0.7rem',
                      height: 24,
                      '& .MuiChip-label': {
                        padding: '0 6px'
                      }
                    }}
                  />
                </Tooltip>
              );
            })}
          </Box>
        </Box>
        
        {/* Contrôles rapides */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Toggle Voice Mode */}
          <Tooltip title={`Mode vocal ${state.config.voiceMode ? 'activé' : 'désactivé'}`}>
            <IconButton
              size="small"
              onClick={actions.toggleVoiceMode}
              sx={{
                color: state.config.voiceMode 
                  ? theme.palette.primary.main 
                  : theme.palette.text.secondary,
                backgroundColor: state.config.voiceMode 
                  ? alpha(theme.palette.primary.main, 0.1) 
                  : 'transparent'
              }}
            >
              {state.config.voiceMode ? <MicIcon /> : <MicOffIcon />}
            </IconButton>
          </Tooltip>
          
          {/* Toggle Autocomplete */}
          <Tooltip title={`Autocomplétion ${state.config.autocompleteEnabled ? 'activée' : 'désactivée'}`}>
            <IconButton
              size="small"
              onClick={actions.toggleAutocomplete}
              sx={{
                color: state.config.autocompleteEnabled 
                  ? theme.palette.primary.main 
                  : theme.palette.text.secondary,
                backgroundColor: state.config.autocompleteEnabled 
                  ? alpha(theme.palette.primary.main, 0.1) 
                  : 'transparent'
              }}
            >
              <AutocompleteIcon />
            </IconButton>
          </Tooltip>
          
          {/* Toggle Sandbox Mode */}
          <Tooltip title={`Mode sandbox ${state.config.sandboxMode ? 'activé' : 'désactivé'}`}>
            <IconButton
              size="small"
              onClick={actions.toggleSandboxMode}
              sx={{
                color: state.config.sandboxMode 
                  ? theme.palette.success.main 
                  : theme.palette.text.secondary,
                backgroundColor: state.config.sandboxMode 
                  ? alpha(theme.palette.success.main, 0.1) 
                  : 'transparent'
              }}
            >
              <SandboxIcon />
            </IconButton>
          </Tooltip>
          
          {/* Screenshot rapide */}
          {isElectron && (
            <Tooltip title="Prendre une capture d'écran">
              <IconButton
                size="small"
                onClick={handleTakeScreenshot}
                disabled={isExecutingCommand || state.jarvis.status !== 'connected'}
                sx={{ color: theme.palette.text.secondary }}
              >
                <ScreenshotIcon />
              </IconButton>
            </Tooltip>
          )}
          
          {/* Refresh status */}
          <Tooltip title="Actualiser le statut">
            <IconButton
              size="small"
              onClick={handleRefreshStatus}
              disabled={isExecutingCommand}
              sx={{ color: theme.palette.text.secondary }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          {/* Start/Stop JARVIS */}
          {isElectron && (
            <Button
              variant="contained"
              size="small"
              startIcon={
                state.jarvis.status === 'connected' ? <StopIcon /> : <StartIcon />
              }
              onClick={handleStartStopJarvis}
              disabled={isExecutingCommand || state.jarvis.status === 'connecting'}
              color={state.jarvis.status === 'connected' ? 'error' : 'primary'}
              sx={{
                minWidth: 100,
                fontSize: '0.75rem',
                textTransform: 'none',
                fontWeight: 500
              }}
            >
              {state.jarvis.status === 'connected' ? 'Arrêter' : 'Démarrer'}
            </Button>
          )}
          
          {/* Menu Plus d'actions */}
          <IconButton
            size="small"
            onClick={handleMoreMenuOpen}
            sx={{ color: theme.palette.text.secondary }}
          >
            <MoreIcon />
          </IconButton>
          
          <Menu
            anchorEl={moreMenuAnchor}
            open={Boolean(moreMenuAnchor)}
            onClose={handleMoreMenuClose}
            PaperProps={{
              sx: {
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                backdropFilter: 'blur(10px)',
                minWidth: 200
              }
            }}
          >
            <MenuItem 
              onClick={() => {
                actions.toggleDebugMode();
                handleMoreMenuClose();
              }}
            >
              <BugReport sx={{ marginRight: 1, fontSize: '1rem' }} />
              Mode Debug
              <Chip
                label={state.config.debugMode ? 'ON' : 'OFF'}
                size="small"
                color={state.config.debugMode ? 'warning' : 'default'}
                sx={{ marginLeft: 'auto', fontSize: '0.7rem' }}
              />
            </MenuItem>
            
            <MenuItem onClick={handleMoreMenuClose}>
              <MemoryIcon sx={{ marginRight: 1, fontSize: '1rem' }} />
              Vider la mémoire
            </MenuItem>
            
            <MenuItem onClick={handleMoreMenuClose}>
              <PerformanceIcon sx={{ marginRight: 1, fontSize: '1rem' }} />
              Diagnostics
            </MenuItem>
          </Menu>
        </Box>
        
        {/* Indicateur de performance (optionnel) */}
        {state.jarvis.status === 'connected' && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              marginLeft: 2,
              padding: '4px 8px',
              borderRadius: 1,
              backgroundColor: alpha(theme.palette.success.main, 0.1),
              border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`
            }}
          >
            <Box
              sx={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                backgroundColor: theme.palette.success.main,
                animation: 'pulse 2s infinite'
              }}
            />
            <Typography
              variant="caption"
              sx={{
                color: theme.palette.success.main,
                fontSize: '0.7rem',
                fontWeight: 500
              }}
            >
              {state.stats.commandsExecuted} commandes
            </Typography>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}

export default TopBar;