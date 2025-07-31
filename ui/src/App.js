/**
 * 🤖 JARVIS UI - Composant App principal
 * Interface moderne pour l'assistant IA autonome
 */
import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, useTheme } from '@mui/material';

// Context
import { useJarvis } from './contexts/JarvisContext';

// Error Boundaries
import ErrorBoundary from './components/ErrorBoundary';
import APIErrorBoundary from './components/APIErrorBoundary';
import VisualizationErrorBoundary from './components/VisualizationErrorBoundary';
import { ErrorLoggerProvider, useErrorLogger } from './components/ErrorLogger';

// Layout components
import Sidebar from './components/layout/Sidebar';
import TopBar from './components/layout/TopBar';
import NotificationSystem from './components/layout/NotificationSystem';
import ChatWindow from './components/ChatWindow';
import ChatButton from './components/ChatButton';

// Page components
import MainChat from './pages/MainChat';
import Dashboard from './pages/Dashboard';
import VisionControl from './pages/VisionControl';
import VoiceInterface from './pages/VoiceInterface';
import AutocompleteManager from './pages/AutocompleteManager';
import MemoryExplorer from './pages/MemoryExplorer';
import ActionExecutor from './pages/ActionExecutor';
import SystemLogs from './pages/SystemLogs';
import Settings from './pages/Settings';
import Chat from './pages/Chat';

// Situation Room
import SituationRoom from './components/SituationRoom';
import './styles/situation-room.css';

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
  
  // Error logging hook
  const { logError } = useErrorLogger();
  
  // État local pour l'interface
  const [sidebarWidth] = useState(280);
  const [topBarHeight] = useState(64);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isSituationRoomOpen, setIsSituationRoomOpen] = useState(false);
  
  // Vérifier si on est dans Electron
  const isElectron = window.electronAPI !== undefined;
  
  // Gestion du raccourci clavier pour le Situation Room
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Ctrl+Shift+J pour ouvrir/fermer le Situation Room
      if (e.ctrlKey && e.shiftKey && e.key === 'J') {
        e.preventDefault();
        setIsSituationRoomOpen(prev => !prev);
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, []);
  
  // Vérifier si on est sur la page de chat principal (fullscreen)
  const isMainChatRoute = window.location.pathname === '/' || window.location.pathname === '/chat';
  
  // Layout responsive
  const layoutConfig = {
    sidebarWidth: (state.ui.sidebarOpen && !isMainChatRoute) ? sidebarWidth : 0,
    topBarHeight: isMainChatRoute ? 0 : topBarHeight,
    isMobile,
    isTablet,
    isDesktop,
    contentPadding: isMainChatRoute ? 0 : (isMobile ? 16 : 24),
    showSidebar: !isMobile && state.ui.sidebarOpen && !isMainChatRoute,
    showTopBar: !isMainChatRoute
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
    overflow: isMainChatRoute ? 'hidden' : 'auto',
    padding: `${layoutConfig.contentPadding}px`,
    paddingTop: `${layoutConfig.topBarHeight + layoutConfig.contentPadding}px`,
    background: isMainChatRoute ? 'transparent' : 
      `linear-gradient(135deg, 
        ${theme.palette.background.default} 0%, 
        ${theme.palette.background.paper} 100%)`,
    position: 'relative',
    
    // Scrollbar personnalisée (seulement si pas MainChat)
    ...(isMainChatRoute ? {} : {
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
    })
  };
  
  // Handler d'erreur global pour l'app
  const handleAppError = (errorData) => {
    logError({
      type: 'component',
      severity: 'high',
      message: errorData.error?.message || 'App component error',
      component: 'App',
      stack: errorData.error?.stack,
      context: 'main-app',
      url: window.location.href
    });
  };

  return (
    <ErrorBoundary
      componentName="JARVIS Main Application"
      onError={handleAppError}
      title="JARVIS SYSTEM FAILURE"
      message="The main JARVIS interface has encountered a critical error. Please restart the application."
      fullHeight={true}
      variant="critical"
    >
      <Box sx={mainContainerStyle}>
        {/* Sidebar de navigation */}
        {layoutConfig.showSidebar && (
          <ErrorBoundary
            componentName="Sidebar Navigation"
            onError={handleAppError}
            title="NAVIGATION ERROR"
            message="The navigation sidebar has encountered an error."
            showHome={false}
            variant="warning"
          >
            <Sidebar 
              width={sidebarWidth}
              isElectron={isElectron}
            />
          </ErrorBoundary>
        )}
      
      {/* Zone de contenu principale */}
      <Box sx={contentAreaStyle}>
          {/* Barre supérieure (masquée sur MainChat) */}
          {layoutConfig.showTopBar && (
            <ErrorBoundary
              componentName="Top Navigation Bar"
              onError={handleAppError}
              title="TOP BAR ERROR"
              message="The top navigation bar has encountered an error."
              showHome={false}
              variant="warning"
            >
              <TopBar 
                height={topBarHeight}
                showMenuButton={isMobile}
                isElectron={isElectron}
                onChatToggle={() => setIsChatOpen(!isChatOpen)}
                isChatOpen={isChatOpen}
                onSituationRoomToggle={() => setIsSituationRoomOpen(!isSituationRoomOpen)}
              />
            </ErrorBoundary>
          )}
        
          {/* Contenu principal avec routage */}
          <Box sx={mainContentStyle}>
            <APIErrorBoundary
              componentName="Main Content Routes"
              onError={handleAppError}
            >
              <Routes>
                {/* Page d'accueil - Chat Principal avec Sphère 3D */}
                <Route path="/" element={
                  <VisualizationErrorBoundary
                    componentName="Main Chat Interface"
                    onError={handleAppError}
                  >
                    <MainChat />
                  </VisualizationErrorBoundary>
                } />
                <Route path="/chat" element={
                  <VisualizationErrorBoundary
                    componentName="Main Chat Interface"
                    onError={handleAppError}
                  >
                    <MainChat />
                  </VisualizationErrorBoundary>
                } />
            
                {/* Modules JARVIS */}
                <Route path="/dashboard" element={
                  <ErrorBoundary componentName="Dashboard" onError={handleAppError}>
                    <Dashboard />
                  </ErrorBoundary>
                } />
                <Route path="/legacy-chat" element={
                  <ErrorBoundary componentName="Legacy Chat" onError={handleAppError}>
                    <Chat />
                  </ErrorBoundary>
                } />
                <Route path="/vision" element={
                  <VisualizationErrorBoundary componentName="Vision Control" onError={handleAppError}>
                    <VisionControl />
                  </VisualizationErrorBoundary>
                } />
                <Route path="/voice" element={
                  <APIErrorBoundary componentName="Voice Interface" onError={handleAppError}>
                    <VoiceInterface />
                  </APIErrorBoundary>
                } />
                <Route path="/autocomplete" element={
                  <APIErrorBoundary componentName="Autocomplete Manager" onError={handleAppError}>
                    <AutocompleteManager />
                  </APIErrorBoundary>
                } />
                <Route path="/memory" element={
                  <APIErrorBoundary componentName="Memory Explorer" onError={handleAppError}>
                    <MemoryExplorer />
                  </APIErrorBoundary>
                } />
                <Route path="/executor" element={
                  <APIErrorBoundary componentName="Action Executor" onError={handleAppError}>
                    <ActionExecutor />
                  </APIErrorBoundary>
                } />
            
                {/* Système */}
                <Route path="/logs" element={
                  <ErrorBoundary componentName="System Logs" onError={handleAppError}>
                    <SystemLogs />
                  </ErrorBoundary>
                } />
                <Route path="/settings" element={
                  <ErrorBoundary componentName="Settings" onError={handleAppError}>
                    <Settings />
                  </ErrorBoundary>
                } />
            
                {/* Route par défaut */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </APIErrorBoundary>
          </Box>
      </Box>
      
        {/* Système de notifications */}
        <ErrorBoundary
          componentName="Notification System"
          onError={handleAppError}
          title="NOTIFICATION ERROR"
          message="The notification system has encountered an error."
          showHome={false}
          variant="warning"
        >
          <NotificationSystem />
        </ErrorBoundary>
      
        {/* Fenêtre de chat JARVIS */}
        <APIErrorBoundary
          componentName="Chat Window"
          onError={handleAppError}
        >
          <ChatWindow 
            isOpen={isChatOpen}
            onClose={() => setIsChatOpen(false)}
            height={isMobile ? window.innerHeight - 100 : 600}
            width={isMobile ? window.innerWidth - 40 : 400}
          />
        </APIErrorBoundary>
      
        {/* Bouton de chat flottant */}
        <ErrorBoundary
          componentName="Chat Button"
          onError={handleAppError}
          showHome={false}
          variant="info"
        >
          <ChatButton
            isOpen={isChatOpen}
            onClick={() => setIsChatOpen(!isChatOpen)}
            bottom={20}
            right={20}
          />
        </ErrorBoundary>
      
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
      
        {/* Situation Room - Centre de contrôle Iron Man */}
        <VisualizationErrorBoundary
          componentName="Situation Room"
          onError={handleAppError}
        >
          <SituationRoom 
            isVisible={isSituationRoomOpen}
            onClose={() => setIsSituationRoomOpen(false)}
          />
        </VisualizationErrorBoundary>

      {/* Effets de particules en arrière-plan (optionnel) */}
      {isDesktop && !isSituationRoomOpen && (
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
    </ErrorBoundary>
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