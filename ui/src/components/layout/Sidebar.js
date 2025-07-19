/**
 * 🤖 JARVIS UI - Sidebar Navigation
 * Barre latérale de navigation avec modules JARVIS
 */
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Badge,
  Tooltip,
  useTheme
} from '@mui/material';

// Icons
import {
  Dashboard as DashboardIcon,
  Visibility as VisionIcon,
  Mic as VoiceIcon,
  TextFields as AutocompleteIcon,
  Memory as MemoryIcon,
  PlayArrow as ExecutorIcon,
  Assignment as LogsIcon,
  Settings as SettingsIcon,
  Computer as SystemIcon,
  Psychology as AIIcon
} from '@mui/icons-material';

import { useJarvis } from '../../contexts/JarvisContext';

// Configuration de navigation
const navigationConfig = [
  {
    section: 'Principal',
    items: [
      {
        id: 'dashboard',
        label: 'Dashboard',
        path: '/dashboard',
        icon: DashboardIcon,
        description: 'Vue d\'ensemble de JARVIS'
      }
    ]
  },
  {
    section: 'Modules IA',
    items: [
      {
        id: 'vision',
        label: 'Vision',
        path: '/vision',
        icon: VisionIcon,
        description: 'Capture d\'écran et analyse visuelle',
        module: 'vision'
      },
      {
        id: 'voice',
        label: 'Interface Vocale',
        path: '/voice',
        icon: VoiceIcon,
        description: 'Reconnaissance et synthèse vocale',
        module: 'voice'
      },
      {
        id: 'autocomplete',
        label: 'Autocomplétion',
        path: '/autocomplete',
        icon: AutocompleteIcon,
        description: 'Suggestions intelligentes globales',
        module: 'autocomplete'
      },
      {
        id: 'memory',
        label: 'Mémoire',
        path: '/memory',
        icon: MemoryIcon,
        description: 'Système de mémoire persistante',
        module: 'memory'
      },
      {
        id: 'executor',
        label: 'Exécuteur',
        path: '/executor',
        icon: ExecutorIcon,
        description: 'Exécution automatique d\'actions',
        module: 'executor'
      }
    ]
  },
  {
    section: 'Système',
    items: [
      {
        id: 'logs',
        label: 'Logs Système',
        path: '/logs',
        icon: LogsIcon,
        description: 'Journaux et activité système'
      },
      {
        id: 'settings',
        label: 'Paramètres',
        path: '/settings',
        icon: SettingsIcon,
        description: 'Configuration de JARVIS'
      }
    ]
  }
];

function Sidebar({ width, isElectron }) {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { state } = useJarvis();
  
  // Style du container
  const sidebarStyle = {
    width: width,
    height: '100vh',
    position: 'fixed',
    left: 0,
    top: 0,
    zIndex: 1200,
    backgroundColor: 'rgba(26, 26, 26, 0.95)',
    backdropFilter: 'blur(10px)',
    borderRight: `1px solid ${theme.palette.divider}`,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  };
  
  // Vérifier si un item est actif
  const isActiveItem = (path) => {
    return location.pathname === path;
  };
  
  // Obtenir le statut d'un module
  const getModuleStatus = (moduleName) => {
    if (!moduleName) return null;
    const module = state.modules[moduleName];
    return module ? module.status : 'unknown';
  };
  
  // Obtenir l'indicateur de statut
  const getStatusIndicator = (moduleName) => {
    const status = getModuleStatus(moduleName);
    
    switch (status) {
      case 'active':
      case 'ready':
        return { color: theme.palette.success.main, label: 'Actif' };
      case 'inactive':
      case 'stopped':
        return { color: theme.palette.text.disabled, label: 'Inactif' };
      case 'error':
        return { color: theme.palette.error.main, label: 'Erreur' };
      case 'loading':
        return { color: theme.palette.warning.main, label: 'Chargement' };
      default:
        return { color: theme.palette.text.secondary, label: 'Inconnu' };
    }
  };
  
  return (
    <Box sx={sidebarStyle}>
      {/* Header avec logo JARVIS */}
      <Box
        sx={{
          padding: '20px 24px',
          borderBottom: `1px solid ${theme.palette.divider}`,
          display: 'flex',
          alignItems: 'center',
          gap: 2
        }}
      >
        {/* Logo/Icône JARVIS */}
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.light})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '1.2rem',
            fontWeight: 'bold',
            boxShadow: theme.shadows[3]
          }}
        >
          <AIIcon />
        </Box>
        
        {/* Nom et version */}
        <Box>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.light})`,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              lineHeight: 1.2
            }}
          >
            JARVIS
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: theme.palette.text.secondary,
              fontSize: '0.7rem'
            }}
          >
            {state.jarvis.version || 'v1.0.0'} {isElectron && '• Desktop'}
          </Typography>
        </Box>
      </Box>
      
      {/* Navigation */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          padding: '8px 0',
          
          // Custom scrollbar
          '&::-webkit-scrollbar': {
            width: '4px'
          },
          '&::-webkit-scrollbar-track': {
            background: 'transparent'
          },
          '&::-webkit-scrollbar-thumb': {
            background: theme.palette.divider,
            borderRadius: '2px'
          }
        }}
      >
        {navigationConfig.map((section, sectionIndex) => (
          <Box key={section.section}>
            {/* Section header */}
            <Typography
              variant="overline"
              sx={{
                color: theme.palette.text.secondary,
                fontSize: '0.7rem',
                fontWeight: 600,
                padding: '16px 24px 8px',
                display: 'block',
                letterSpacing: '0.1em'
              }}
            >
              {section.section}
            </Typography>
            
            {/* Section items */}
            <List sx={{ padding: 0 }}>
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = isActiveItem(item.path);
                const statusInfo = item.module ? getStatusIndicator(item.module) : null;
                
                return (
                  <ListItem key={item.id} sx={{ padding: '2px 16px' }}>
                    <Tooltip
                      title={
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {item.label}
                          </Typography>
                          <Typography variant="caption" sx={{ opacity: 0.8 }}>
                            {item.description}
                          </Typography>
                          {statusInfo && (
                            <Typography variant="caption" sx={{ opacity: 0.8, display: 'block', mt: 0.5 }}>
                              Statut: {statusInfo.label}
                            </Typography>
                          )}
                        </Box>
                      }
                      placement="right"
                      arrow
                    >
                      <ListItemButton
                        onClick={() => navigate(item.path)}
                        sx={{
                          borderRadius: 2,
                          margin: '2px 0',
                          backgroundColor: isActive 
                            ? `${theme.palette.primary.main}20` 
                            : 'transparent',
                          border: isActive 
                            ? `1px solid ${theme.palette.primary.main}40`
                            : '1px solid transparent',
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            backgroundColor: isActive 
                              ? `${theme.palette.primary.main}30`
                              : `${theme.palette.action.hover}`,
                            transform: 'translateX(4px)'
                          },
                          '&:active': {
                            transform: 'translateX(2px)'
                          }
                        }}
                      >
                        <ListItemIcon
                          sx={{
                            color: isActive 
                              ? theme.palette.primary.main 
                              : theme.palette.text.secondary,
                            minWidth: 40,
                            transition: 'color 0.2s ease'
                          }}
                        >
                          {statusInfo ? (
                            <Badge
                              badgeContent=""
                              sx={{
                                '& .MuiBadge-badge': {
                                  backgroundColor: statusInfo.color,
                                  width: 8,
                                  height: 8,
                                  borderRadius: '50%',
                                  minWidth: 8,
                                  right: 2,
                                  top: 2
                                }
                              }}
                            >
                              <Icon fontSize="small" />
                            </Badge>
                          ) : (
                            <Icon fontSize="small" />
                          )}
                        </ListItemIcon>
                        
                        <ListItemText
                          primary={item.label}
                          sx={{
                            '& .MuiListItemText-primary': {
                              fontSize: '0.875rem',
                              fontWeight: isActive ? 600 : 400,
                              color: isActive 
                                ? theme.palette.primary.main 
                                : theme.palette.text.primary,
                              transition: 'all 0.2s ease'
                            }
                          }}
                        />
                        
                        {/* Indicateur de nouvelles notifications */}
                        {item.id === 'logs' && state.logs.length > 0 && (
                          <Badge
                            badgeContent={state.logs.filter(log => log.level === 'error').length || null}
                            color="error"
                            sx={{
                              '& .MuiBadge-badge': {
                                fontSize: '0.6rem',
                                height: 16,
                                minWidth: 16
                              }
                            }}
                          />
                        )}
                      </ListItemButton>
                    </Tooltip>
                  </ListItem>
                );
              })}
            </List>
            
            {/* Divider entre sections */}
            {sectionIndex < navigationConfig.length - 1 && (
              <Divider 
                sx={{ 
                  margin: '8px 24px',
                  borderColor: theme.palette.divider
                }} 
              />
            )}
          </Box>
        ))}
      </Box>
      
      {/* Footer avec statut de connexion */}
      <Box
        sx={{
          padding: '16px 24px',
          borderTop: `1px solid ${theme.palette.divider}`,
          backgroundColor: 'rgba(0, 0, 0, 0.2)'
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            padding: '8px 12px',
            borderRadius: 2,
            backgroundColor: state.jarvis.status === 'connected' 
              ? `${theme.palette.success.main}10`
              : `${theme.palette.text.disabled}10`,
            border: `1px solid ${
              state.jarvis.status === 'connected' 
                ? theme.palette.success.main 
                : theme.palette.text.disabled
            }40`
          }}
        >
          {/* Icône de statut */}
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: 
                state.jarvis.status === 'connected' ? theme.palette.success.main :
                state.jarvis.status === 'connecting' ? theme.palette.warning.main :
                state.jarvis.status === 'error' ? theme.palette.error.main :
                theme.palette.text.disabled,
              animation: state.jarvis.status === 'connecting' ? 'pulse 2s infinite' : 'none'
            }}
          />
          
          {/* Texte de statut */}
          <Box>
            <Typography
              variant="caption"
              sx={{
                fontWeight: 500,
                color: theme.palette.text.primary,
                display: 'block',
                lineHeight: 1.2
              }}
            >
              {state.jarvis.status === 'connected' ? 'Connecté' :
               state.jarvis.status === 'connecting' ? 'Connexion...' :
               state.jarvis.status === 'error' ? 'Erreur' : 'Déconnecté'}
            </Typography>
            
            {state.jarvis.status === 'connected' && state.jarvis.pid && (
              <Typography
                variant="caption"
                sx={{
                  color: theme.palette.text.secondary,
                  fontSize: '0.65rem'
                }}
              >
                PID: {state.jarvis.pid}
              </Typography>
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default Sidebar;