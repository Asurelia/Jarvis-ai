/**
 * 🤖 JARVIS UI - Composant App principal
 * Interface moderne pour l'assistant IA autonome
 */
import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, useTheme } from '@mui/material';

// Context
import { useJarvis } from './contexts/JarvisContext';

// Layout components
import Sidebar from './components/layout/Sidebar';
import TopBar from './components/layout/TopBar';
import NotificationSystem from './components/layout/NotificationSystem';

// Page components
import Dashboard from './pages/Dashboard';
import VisionControl from './pages/VisionControl';
import VoiceInterface from './pages/VoiceInterface';
import AutocompleteManager from './pages/AutocompleteManager';
import MemoryExplorer from './pages/MemoryExplorer';
import ActionExecutor from './pages/ActionExecutor';
import SystemLogs from './pages/SystemLogs';
import Settings from './pages/Settings';

// Hook pour la responsivité
function useResponsive() {
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  
  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768);
      setIsTablet(window.innerWidth >= 768 && window.innerWidth < 1024);
    };
    
    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);
  
  return { isMobile, isTablet, isDesktop: !isMobile && !isTablet };
}

function App() {
  const theme = useTheme();
  const { state } = useJarvis();
  const { isMobile, isTablet, isDesktop } = useResponsive();
  
  // État local pour l'interface
  const [sidebarWidth] = useState(280);
  const [topBarHeight] = useState(64);
  
  // Vérifier si on est dans Electron
  const isElectron = window.electronAPI !== undefined;
  
  // Layout responsive
  const layoutConfig = {
    sidebarWidth: state.ui.sidebarOpen ? sidebarWidth : 0,
    topBarHeight,
    isMobile,
    isTablet,
    isDesktop,
    contentPadding: isMobile ? 16 : 24,
    showSidebar: !isMobile && state.ui.sidebarOpen
  };
  
  // Style du container principal
  const mainContainerStyle = {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden',
    backgroundColor: theme.palette.background.default,
    position: 'relative'
  };
  
  // Style de la zone de contenu
  const contentAreaStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    marginLeft: layoutConfig.showSidebar ? `${sidebarWidth}px` : 0,
    transition: 'margin-left 0.3s ease',
    overflow: 'hidden',
    position: 'relative'
  };
  
  // Style du contenu principal
  const mainContentStyle = {
    flex: 1,
    overflow: 'auto',
    padding: `${layoutConfig.contentPadding}px`,
    paddingTop: `${topBarHeight + layoutConfig.contentPadding}px`,
    background: `linear-gradient(135deg, 
      ${theme.palette.background.default} 0%, 
      ${theme.palette.background.paper} 100%)`,
    position: 'relative',
    
    // Scrollbar personnalisée
    '&::-webkit-scrollbar': {
      width: '8px'
    },
    '&::-webkit-scrollbar-track': {
      background: 'rgba(255, 255, 255, 0.05)'
    },
    '&::-webkit-scrollbar-thumb': {
      background: 'rgba(255, 255, 255, 0.2)',
      borderRadius: '4px'
    },
    '&::-webkit-scrollbar-thumb:hover': {
      background: 'rgba(255, 255, 255, 0.3)'
    }
  };
  
  return (
    <Box sx={mainContainerStyle}>
      {/* Sidebar de navigation */}
      {layoutConfig.showSidebar && (
        <Sidebar 
          width={sidebarWidth}
          isElectron={isElectron}
        />
      )}
      
      {/* Zone de contenu principale */}
      <Box sx={contentAreaStyle}>
        {/* Barre supérieure */}
        <TopBar 
          height={topBarHeight}
          showMenuButton={isMobile}
          isElectron={isElectron}
        />
        
        {/* Contenu principal avec routage */}
        <Box sx={mainContentStyle}>
          <Routes>
            {/* Page d'accueil - Dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            
            {/* Modules JARVIS */}
            <Route path="/vision" element={<VisionControl />} />
            <Route path="/voice" element={<VoiceInterface />} />
            <Route path="/autocomplete" element={<AutocompleteManager />} />
            <Route path="/memory" element={<MemoryExplorer />} />
            <Route path="/executor" element={<ActionExecutor />} />
            
            {/* Système */}
            <Route path="/logs" element={<SystemLogs />} />
            <Route path="/settings" element={<Settings />} />
            
            {/* Route par défaut */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Box>
      </Box>
      
      {/* Système de notifications */}
      <NotificationSystem />
      
      {/* Overlay de chargement global */}
      {state.ui.loading && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            color: theme.palette.primary.main
          }}
        >
          <Box className="animate-spin">
            <Box
              sx={{
                width: 50,
                height: 50,
                border: `3px solid ${theme.palette.primary.main}20`,
                borderTop: `3px solid ${theme.palette.primary.main}`,
                borderRadius: '50%'
              }}
            />
          </Box>
        </Box>
      )}
      
      {/* Indicateur de statut JARVIS (floating) */}
      <Box
        sx={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 2,
          padding: '8px 12px',
          backdropFilter: 'blur(10px)',
          transition: 'all 0.3s ease',
          opacity: state.jarvis.status === 'disconnected' ? 0.7 : 1,
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: theme.shadows[4]
          }
        }}
      >
        {/* Indicateur de statut */}
        <Box
          sx={{
            width: 8,
            height: 8,
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
        <Box
          sx={{
            fontSize: '0.75rem',
            fontWeight: 500,
            color: theme.palette.text.secondary,
            userSelect: 'none'
          }}
        >
          JARVIS {state.jarvis.status === 'connected' ? 'Online' : 
                 state.jarvis.status === 'connecting' ? 'Connecting...' :
                 state.jarvis.status === 'error' ? 'Error' : 'Offline'}
        </Box>
        
        {/* Uptime si connecté */}
        {state.jarvis.status === 'connected' && state.jarvis.uptime > 0 && (
          <Box
            sx={{
              fontSize: '0.625rem',
              color: theme.palette.text.disabled,
              borderLeft: `1px solid ${theme.palette.divider}`,
              paddingLeft: 1,
              marginLeft: 1
            }}
          >
            {formatUptime(state.jarvis.uptime)}
          </Box>
        )}
      </Box>
      
      {/* Effets de particules en arrière-plan (optionnel) */}
      {isDesktop && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            pointerEvents: 'none',
            zIndex: -1,
            opacity: 0.1,
            background: `radial-gradient(circle at 20% 20%, ${theme.palette.primary.main}20 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, ${theme.palette.secondary.main}20 0%, transparent 50%),
                        radial-gradient(circle at 40% 60%, ${theme.palette.primary.main}10 0%, transparent 50%)`
          }}
        />
      )}
    </Box>
  );
}

// Utilitaire pour formater l'uptime
function formatUptime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
}

export default App;