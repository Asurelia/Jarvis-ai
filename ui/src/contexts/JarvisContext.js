/**
 * 🤖 JARVIS Context - Gestion d'état global
 * Context React pour la communication avec JARVIS via API REST et WebSocket
 */
import React, { createContext, useContext, useReducer, useEffect, useRef } from 'react';

// Configuration API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

// État initial
const initialState = {
  // État de JARVIS
  jarvis: {
    status: 'disconnected', // 'disconnected', 'connecting', 'connected', 'error'
    pid: null,
    version: null,
    uptime: 0
  },
  
  // Connexion API
  api: {
    connected: false,
    websocket: null,
    lastPing: null,
    reconnectAttempts: 0
  },
  
  // Modules et leurs états
  modules: {
    vision: { status: 'unknown', lastActivity: null },
    control: { status: 'unknown', lastActivity: null },
    voice: { status: 'unknown', lastActivity: null },
    memory: { status: 'unknown', lastActivity: null },
    autocomplete: { status: 'unknown', lastActivity: null },
    executor: { status: 'unknown', lastActivity: null }
  },
  
  // Configuration
  config: {
    voiceMode: false,
    autocompleteEnabled: true,
    sandboxMode: true,
    debugMode: false
  },
  
  // Statistiques en temps réel
  stats: {
    commandsExecuted: 0,
    screenshotsTaken: 0,
    voiceCommands: 0,
    autocompleteUsage: 0,
    memoryEntries: 0
  },
  
  // Logs et sorties
  logs: [],
  
  // État de l'interface
  ui: {
    currentPage: 'dashboard',
    sidebarOpen: true,
    loading: false,
    error: null,
    notifications: []
  }
};

// Types d'actions
const ActionTypes = {
  // JARVIS Core
  SET_JARVIS_STATUS: 'SET_JARVIS_STATUS',
  SET_JARVIS_VERSION: 'SET_JARVIS_VERSION',
  UPDATE_JARVIS_UPTIME: 'UPDATE_JARVIS_UPTIME',
  
  // Modules
  UPDATE_MODULE_STATUS: 'UPDATE_MODULE_STATUS',
  UPDATE_ALL_MODULES: 'UPDATE_ALL_MODULES',
  
  // Configuration
  UPDATE_CONFIG: 'UPDATE_CONFIG',
  TOGGLE_VOICE_MODE: 'TOGGLE_VOICE_MODE',
  TOGGLE_AUTOCOMPLETE: 'TOGGLE_AUTOCOMPLETE',
  TOGGLE_SANDBOX_MODE: 'TOGGLE_SANDBOX_MODE',
  TOGGLE_DEBUG_MODE: 'TOGGLE_DEBUG_MODE',
  
  // Statistiques
  UPDATE_STATS: 'UPDATE_STATS',
  INCREMENT_STAT: 'INCREMENT_STAT',
  RESET_STATS: 'RESET_STATS',
  
  // Logs
  ADD_LOG: 'ADD_LOG',
  CLEAR_LOGS: 'CLEAR_LOGS',
  
  // UI
  SET_CURRENT_PAGE: 'SET_CURRENT_PAGE',
  TOGGLE_SIDEBAR: 'TOGGLE_SIDEBAR',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  CLEAR_NOTIFICATIONS: 'CLEAR_NOTIFICATIONS'
};

// Reducer
function jarvisReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_JARVIS_STATUS:
      return {
        ...state,
        jarvis: {
          ...state.jarvis,
          status: action.payload.status,
          pid: action.payload.pid || state.jarvis.pid
        }
      };
    
    case ActionTypes.SET_JARVIS_VERSION:
      return {
        ...state,
        jarvis: {
          ...state.jarvis,
          version: action.payload
        }
      };
    
    case ActionTypes.UPDATE_JARVIS_UPTIME:
      return {
        ...state,
        jarvis: {
          ...state.jarvis,
          uptime: action.payload
        }
      };
    
    case ActionTypes.UPDATE_MODULE_STATUS:
      return {
        ...state,
        modules: {
          ...state.modules,
          [action.payload.module]: {
            ...state.modules[action.payload.module],
            status: action.payload.status,
            lastActivity: action.payload.lastActivity || Date.now()
          }
        }
      };
    
    case ActionTypes.UPDATE_ALL_MODULES:
      return {
        ...state,
        modules: {
          ...state.modules,
          ...action.payload
        }
      };
    
    case ActionTypes.UPDATE_CONFIG:
      return {
        ...state,
        config: {
          ...state.config,
          ...action.payload
        }
      };
    
    case ActionTypes.TOGGLE_VOICE_MODE:
      return {
        ...state,
        config: {
          ...state.config,
          voiceMode: !state.config.voiceMode
        }
      };
    
    case ActionTypes.TOGGLE_AUTOCOMPLETE:
      return {
        ...state,
        config: {
          ...state.config,
          autocompleteEnabled: !state.config.autocompleteEnabled
        }
      };
    
    case ActionTypes.TOGGLE_SANDBOX_MODE:
      return {
        ...state,
        config: {
          ...state.config,
          sandboxMode: !state.config.sandboxMode
        }
      };
    
    case ActionTypes.TOGGLE_DEBUG_MODE:
      return {
        ...state,
        config: {
          ...state.config,
          debugMode: !state.config.debugMode
        }
      };
    
    case ActionTypes.UPDATE_STATS:
      return {
        ...state,
        stats: {
          ...state.stats,
          ...action.payload
        }
      };
    
    case ActionTypes.INCREMENT_STAT:
      return {
        ...state,
        stats: {
          ...state.stats,
          [action.payload]: (state.stats[action.payload] || 0) + 1
        }
      };
    
    case ActionTypes.RESET_STATS:
      return {
        ...state,
        stats: {
          commandsExecuted: 0,
          screenshotsTaken: 0,
          voiceCommands: 0,
          autocompleteUsage: 0,
          memoryEntries: 0
        }
      };
    
    case ActionTypes.ADD_LOG:
      const newLog = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        level: action.payload.level || 'info',
        message: action.payload.message,
        source: action.payload.source || 'system'
      };
      
      return {
        ...state,
        logs: [newLog, ...state.logs.slice(0, 999)] // Garder max 1000 logs
      };
    
    case ActionTypes.CLEAR_LOGS:
      return {
        ...state,
        logs: []
      };
    
    case ActionTypes.SET_CURRENT_PAGE:
      return {
        ...state,
        ui: {
          ...state.ui,
          currentPage: action.payload
        }
      };
    
    case ActionTypes.TOGGLE_SIDEBAR:
      return {
        ...state,
        ui: {
          ...state.ui,
          sidebarOpen: !state.ui.sidebarOpen
        }
      };
    
    case ActionTypes.SET_LOADING:
      return {
        ...state,
        ui: {
          ...state.ui,
          loading: action.payload
        }
      };
    
    case ActionTypes.SET_ERROR:
      return {
        ...state,
        ui: {
          ...state.ui,
          error: action.payload
        }
      };
    
    case ActionTypes.CLEAR_ERROR:
      return {
        ...state,
        ui: {
          ...state.ui,
          error: null
        }
      };
    
    case ActionTypes.ADD_NOTIFICATION:
      const notification = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        type: action.payload.type || 'info',
        title: action.payload.title,
        message: action.payload.message,
        autoHide: action.payload.autoHide !== false,
        duration: action.payload.duration || 5000
      };
      
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: [notification, ...state.ui.notifications]
        }
      };
    
    case ActionTypes.REMOVE_NOTIFICATION:
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: state.ui.notifications.filter(n => n.id !== action.payload)
        }
      };
    
    case ActionTypes.CLEAR_NOTIFICATIONS:
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: []
        }
      };
    
    default:
      return state;
  }
}

// Context
const JarvisContext = createContext();

// Hook pour utiliser le context
export function useJarvis() {
  const context = useContext(JarvisContext);
  if (!context) {
    throw new Error('useJarvis must be used within a JarvisProvider');
  }
  return context;
}

// Provider
export function JarvisProvider({ children }) {
  const [state, dispatch] = useReducer(jarvisReducer, initialState);
  
  // Actions
  const actions = {
    // JARVIS Core
    setJarvisStatus: (status, pid = null) => {
      dispatch({ type: ActionTypes.SET_JARVIS_STATUS, payload: { status, pid } });
    },
    
    setJarvisVersion: (version) => {
      dispatch({ type: ActionTypes.SET_JARVIS_VERSION, payload: version });
    },
    
    updateJarvisUptime: (uptime) => {
      dispatch({ type: ActionTypes.UPDATE_JARVIS_UPTIME, payload: uptime });
    },
    
    // Modules
    updateModuleStatus: (module, status, lastActivity = null) => {
      dispatch({ 
        type: ActionTypes.UPDATE_MODULE_STATUS, 
        payload: { module, status, lastActivity } 
      });
    },
    
    updateAllModules: (modules) => {
      dispatch({ type: ActionTypes.UPDATE_ALL_MODULES, payload: modules });
    },
    
    // Configuration
    updateConfig: (config) => {
      dispatch({ type: ActionTypes.UPDATE_CONFIG, payload: config });
    },
    
    toggleVoiceMode: () => {
      dispatch({ type: ActionTypes.TOGGLE_VOICE_MODE });
    },
    
    toggleAutocomplete: () => {
      dispatch({ type: ActionTypes.TOGGLE_AUTOCOMPLETE });
    },
    
    toggleSandboxMode: () => {
      dispatch({ type: ActionTypes.TOGGLE_SANDBOX_MODE });
    },
    
    toggleDebugMode: () => {
      dispatch({ type: ActionTypes.TOGGLE_DEBUG_MODE });
    },
    
    // Statistiques
    updateStats: (stats) => {
      dispatch({ type: ActionTypes.UPDATE_STATS, payload: stats });
    },
    
    incrementStat: (statName) => {
      dispatch({ type: ActionTypes.INCREMENT_STAT, payload: statName });
    },
    
    resetStats: () => {
      dispatch({ type: ActionTypes.RESET_STATS });
    },
    
    // Logs
    addLog: (level, message, source = 'system') => {
      dispatch({ 
        type: ActionTypes.ADD_LOG, 
        payload: { level, message, source } 
      });
    },
    
    clearLogs: () => {
      dispatch({ type: ActionTypes.CLEAR_LOGS });
    },
    
    // UI
    setCurrentPage: (page) => {
      dispatch({ type: ActionTypes.SET_CURRENT_PAGE, payload: page });
    },
    
    toggleSidebar: () => {
      dispatch({ type: ActionTypes.TOGGLE_SIDEBAR });
    },
    
    setLoading: (loading) => {
      dispatch({ type: ActionTypes.SET_LOADING, payload: loading });
    },
    
    setError: (error) => {
      dispatch({ type: ActionTypes.SET_ERROR, payload: error });
    },
    
    clearError: () => {
      dispatch({ type: ActionTypes.CLEAR_ERROR });
    },
    
    addNotification: (type, title, message, options = {}) => {
      dispatch({ 
        type: ActionTypes.ADD_NOTIFICATION, 
        payload: { type, title, message, ...options } 
      });
    },
    
    removeNotification: (id) => {
      dispatch({ type: ActionTypes.REMOVE_NOTIFICATION, payload: id });
    },
    
    clearNotifications: () => {
      dispatch({ type: ActionTypes.CLEAR_NOTIFICATIONS });
    }
  };
  
  // API REST et WebSocket
  const apiService = {
    // Configuration
    baseURL: API_BASE_URL,
    wsURL: WS_URL,
    
    // Méthodes HTTP
    async request(endpoint, options = {}) {
      try {
        const url = `${API_BASE_URL}${endpoint}`;
        const response = await fetch(url, {
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          },
          ...options
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
      } catch (error) {
        console.error(`API request failed: ${endpoint}`, error);
        throw error;
      }
    },
    
    // Health check
    async checkHealth() {
      try {
        const response = await this.request('/api/health');
        return response.status === 'healthy';
      } catch (error) {
        return false;
      }
    },
    
    // Statut système
    async getSystemStatus() {
      return await this.request('/api/status');
    },
    
    // Exécuter une commande
    async executeCommand(command, mode = 'auto') {
      return await this.request('/api/command', {
        method: 'POST',
        body: JSON.stringify({ command, mode })
      });
    },
    
    // Chat avec l'IA
    async chatWithAI(message, conversationId = null) {
      return await this.request('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message, conversation_id: conversationId })
      });
    },
    
    // Synthèse vocale
    async speakText(text, voice = null) {
      return await this.request('/api/voice/speak', {
        method: 'POST',
        body: JSON.stringify({ text, voice })
      });
    },
    
    // Capture d'écran
    async takeScreenshot() {
      return await this.request('/api/screenshot');
    },
    
    // Applications en cours
    async getRunningApps() {
      return await this.request('/api/apps');
    },
    
    // Conversations mémoire
    async getConversations() {
      return await this.request('/api/memory/conversations');
    }
  };
  
  // WebSocket Management
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  const connectWebSocket = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return; // Déjà connecté
    }
    
    try {
      actions.addLog('info', 'Connecting to WebSocket...', 'api');
      wsRef.current = new WebSocket(WS_URL);
      
      wsRef.current.onopen = () => {
        actions.addLog('success', 'WebSocket connected', 'api');
        dispatch({ 
          type: ActionTypes.SET_JARVIS_STATUS, 
          payload: { status: 'connected' } 
        });
        
        // Reset reconnect attempts
        dispatch({ 
          type: ActionTypes.UPDATE_CONFIG, 
          payload: { reconnectAttempts: 0 } 
        });
        
        // Start ping/pong
        const pingInterval = setInterval(() => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          } else {
            clearInterval(pingInterval);
          }
        }, 30000); // Ping every 30s
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        actions.addLog('warning', 'WebSocket disconnected', 'api');
        dispatch({ 
          type: ActionTypes.SET_JARVIS_STATUS, 
          payload: { status: 'disconnected' } 
        });
        
        // Attempt reconnect
        scheduleReconnect();
      };
      
      wsRef.current.onerror = (error) => {
        actions.addLog('error', `WebSocket error: ${error.message || 'Unknown error'}`, 'api');
      };
      
    } catch (error) {
      actions.addLog('error', `Failed to connect WebSocket: ${error.message}`, 'api');
      scheduleReconnect();
    }
  };
  
  const scheduleReconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    const attempts = state.api?.reconnectAttempts || 0;
    const delay = Math.min(1000 * Math.pow(2, attempts), 30000); // Exponential backoff, max 30s
    
    reconnectTimeoutRef.current = setTimeout(() => {
      dispatch({ 
        type: ActionTypes.UPDATE_CONFIG, 
        payload: { reconnectAttempts: attempts + 1 } 
      });
      connectWebSocket();
    }, delay);
  };
  
  const handleWebSocketMessage = (message) => {
    const { type, data } = message;
    
    switch (type) {
      case 'welcome':
        actions.addLog('info', data.message, 'jarvis');
        break;
        
      case 'pong':
        // Update last ping time
        break;
        
      case 'status_update':
        // Update system status
        if (data.modules) {
          const moduleStatus = {};
          data.modules.forEach(module => {
            moduleStatus[module.name] = {
              status: module.status,
              lastActivity: module.last_update
            };
          });
          actions.updateAllModules(moduleStatus);
        }
        
        if (data.performance) {
          actions.updateStats({
            commandsExecuted: data.performance.modules_loaded || 0
          });
        }
        break;
        
      case 'command_planned':
        actions.addLog('info', `Command planned: ${data.name}`, 'jarvis');
        actions.addNotification('info', 'Command Planned', `${data.actions_count} actions ready`);
        break;
        
      case 'execution_started':
        actions.addLog('info', `Executing sequence: ${data.sequence_id}`, 'jarvis');
        break;
        
      case 'execution_completed':
        const status = data.success ? 'success' : 'error';
        const message = data.success 
          ? `Executed ${data.actions_executed} actions in ${data.execution_time}s`
          : `Execution failed: ${data.error}`;
        actions.addLog(status, message, 'jarvis');
        
        if (data.success) {
          actions.incrementStat('commandsExecuted');
          actions.addNotification('success', 'Command Executed', message);
        } else {
          actions.addNotification('error', 'Execution Failed', data.error);
        }
        break;
        
      case 'execution_error':
        actions.addLog('error', `Execution error: ${data.error}`, 'jarvis');
        actions.addNotification('error', 'Execution Error', data.error);
        break;
        
      case 'chat_response':
        actions.addLog('info', `AI: ${data.message.substring(0, 100)}...`, 'jarvis');
        break;
        
      case 'screenshot_taken':
        actions.addLog('success', `Screenshot saved: ${data.filename}`, 'jarvis');
        actions.incrementStat('screenshotsTaken');
        actions.addNotification('success', 'Screenshot', 'Screen captured successfully');
        break;
        
      default:
        console.log('Unknown WebSocket message type:', type, data);
    }
  };
  
  // API Electron (fallback pour mode desktop)
  const electronAPI = {
    // Vérifications de disponibilité
    isElectron: () => window.electronAPI !== undefined,
    
    // JARVIS
    getJarvisStatus: async () => {
      if (!window.electronAPI) return { running: false, pid: null };
      try {
        return await window.electronAPI.getJarvisStatus();
      } catch (error) {
        console.error('Error getting JARVIS status:', error);
        return { running: false, pid: null };
      }
    },
    
    startJarvis: async () => {
      if (!window.electronAPI) return { success: false, error: 'Electron API not available' };
      try {
        const result = await window.electronAPI.startJarvis();
        if (result.success) {
          actions.setJarvisStatus('connecting');
          actions.addLog('info', 'JARVIS starting...', 'ui');
        }
        return result;
      } catch (error) {
        console.error('Error starting JARVIS:', error);
        return { success: false, error: error.message };
      }
    },
    
    stopJarvis: async () => {
      if (!window.electronAPI) return { success: false, error: 'Electron API not available' };
      try {
        const result = await window.electronAPI.stopJarvis();
        if (result.success) {
          actions.setJarvisStatus('disconnected');
          actions.addLog('info', 'JARVIS stopped', 'ui');
        }
        return result;
      } catch (error) {
        console.error('Error stopping JARVIS:', error);
        return { success: false, error: error.message };
      }
    },
    
    executeCommand: async (command) => {
      if (!window.electronAPI) return { success: false, error: 'Electron API not available' };
      try {
        actions.addLog('info', `Executing: ${command}`, 'ui');
        const result = await window.electronAPI.executeJarvisCommand(command);
        
        if (result.success) {
          actions.incrementStat('commandsExecuted');
          actions.addLog('success', `Command executed: ${command}`, 'jarvis');
        } else {
          actions.addLog('error', `Command failed: ${result.error}`, 'jarvis');
        }
        
        return result;
      } catch (error) {
        console.error('Error executing command:', error);
        actions.addLog('error', `Command error: ${error.message}`, 'ui');
        return { success: false, error: error.message };
      }
    },
    
    // Version de l'app
    getAppVersion: async () => {
      if (!window.electronAPI) return 'web';
      try {
        return await window.electronAPI.getAppVersion();
      } catch (error) {
        console.error('Error getting app version:', error);
        return 'unknown';
      }
    }
  };
  
  // Effets de setup
  useEffect(() => {
    // Initialisation
    const initializeApp = async () => {
      actions.addLog('info', 'Initializing JARVIS UI...', 'ui');
      
      // Vérifier si on est en mode Electron ou Web
      const isElectron = window.electronAPI !== undefined;
      
      if (isElectron) {
        // Mode Electron - utiliser l'API Electron
        actions.addLog('info', 'Running in Electron mode', 'ui');
        
        const version = await electronAPI.getAppVersion();
        actions.setJarvisVersion(version);
        
        const status = await electronAPI.getJarvisStatus();
        actions.setJarvisStatus(status.running ? 'connected' : 'disconnected', status.pid);
      } else {
        // Mode Web - utiliser l'API REST
        actions.addLog('info', 'Running in Web mode', 'ui');
        actions.setJarvisVersion('web-1.0.0');
        
        // Vérifier la santé de l'API
        try {
          const isHealthy = await apiService.checkHealth();
          if (isHealthy) {
            actions.addLog('success', 'API server is healthy', 'api');
            // Connecter le WebSocket
            connectWebSocket();
          } else {
            actions.addLog('error', 'API server is not responding', 'api');
            actions.setJarvisStatus('error');
          }
        } catch (error) {
          actions.addLog('error', `Failed to connect to API: ${error.message}`, 'api');
          actions.setJarvisStatus('error');
        }
      }
      
      actions.addLog('info', 'JARVIS UI initialized', 'ui');
    };
    
    initializeApp();
    
    // Cleanup WebSocket on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);
  
  // Listeners Electron
  useEffect(() => {
    if (!window.electronAPI) return;
    
    // JARVIS events
    const handleJarvisStarted = () => {
      actions.setJarvisStatus('connected');
      actions.addNotification('success', 'JARVIS Started', 'Assistant IA ready');
    };
    
    const handleJarvisStopped = () => {
      actions.setJarvisStatus('disconnected');
      actions.addNotification('info', 'JARVIS Stopped', 'Assistant IA disconnected');
    };
    
    const handleJarvisOutput = (event, output) => {
      actions.addLog('info', output.trim(), 'jarvis');
    };
    
    const handleJarvisError = (event, error) => {
      actions.addLog('error', error.trim(), 'jarvis');
    };
    
    // Menu events
    const handleNewSession = () => {
      actions.clearLogs();
      actions.resetStats();
      actions.addNotification('info', 'New Session', 'Started fresh session');
    };
    
    const handleToggleVoice = () => {
      actions.toggleVoiceMode();
      const enabled = !state.config.voiceMode;
      actions.addNotification('info', 'Voice Mode', `Voice mode ${enabled ? 'enabled' : 'disabled'}`);
    };
    
    const handleToggleAutocomplete = () => {
      actions.toggleAutocomplete();
      const enabled = !state.config.autocompleteEnabled;
      actions.addNotification('info', 'Autocomplete', `Autocomplete ${enabled ? 'enabled' : 'disabled'}`);
    };
    
    const handleTakeScreenshot = async () => {
      await electronAPI.executeCommand('screenshot');
      actions.incrementStat('screenshotsTaken');
    };
    
    // Bind events
    window.electronAPI.onJarvisStarted(handleJarvisStarted);
    window.electronAPI.onJarvisStopped(handleJarvisStopped);
    window.electronAPI.onJarvisOutput(handleJarvisOutput);
    window.electronAPI.onJarvisError(handleJarvisError);
    window.electronAPI.onNewSession(handleNewSession);
    window.electronAPI.onToggleVoiceMode(handleToggleVoice);
    window.electronAPI.onToggleAutocomplete(handleToggleAutocomplete);
    window.electronAPI.onTakeScreenshot(handleTakeScreenshot);
    
    // Cleanup
    return () => {
      // Remove listeners if API available
      if (window.electronAPI.removeAllListeners) {
        window.electronAPI.removeAllListeners('jarvis-started');
        window.electronAPI.removeAllListeners('jarvis-stopped');
        window.electronAPI.removeAllListeners('jarvis-output');
        window.electronAPI.removeAllListeners('jarvis-error');
        window.electronAPI.removeAllListeners('new-session');
        window.electronAPI.removeAllListeners('toggle-voice-mode');
        window.electronAPI.removeAllListeners('toggle-autocomplete');
        window.electronAPI.removeAllListeners('take-screenshot');
      }
    };
  }, [state.config.voiceMode, state.config.autocompleteEnabled]);
  
  // Auto-hide notifications
  useEffect(() => {
    state.ui.notifications.forEach(notification => {
      if (notification.autoHide) {
        setTimeout(() => {
          actions.removeNotification(notification.id);
        }, notification.duration);
      }
    });
  }, [state.ui.notifications]);
  
  // Update uptime every second
  useEffect(() => {
    if (state.jarvis.status === 'connected') {
      const interval = setInterval(() => {
        actions.updateJarvisUptime(state.jarvis.uptime + 1);
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [state.jarvis.status, state.jarvis.uptime]);
  
  // Polling pour maintenir le statut à jour (mode web seulement)
  useEffect(() => {
    if (window.electronAPI) return; // Skip en mode Electron
    
    const pollStatus = async () => {
      try {
        const status = await apiService.getSystemStatus();
        
        // Mettre à jour les modules
        const moduleStatus = {};
        status.modules.forEach(module => {
          moduleStatus[module.name] = {
            status: module.status,
            lastActivity: module.last_update
          };
        });
        actions.updateAllModules(moduleStatus);
        
        // Mettre à jour les stats
        if (status.performance) {
          actions.updateStats({
            commandsExecuted: status.performance.modules_loaded || 0
          });
        }
        
        // Mettre à jour l'uptime
        if (status.uptime) {
          actions.updateJarvisUptime(Math.floor(status.uptime));
        }
        
      } catch (error) {
        // Ne pas spammer les logs en cas d'erreur de polling
        console.debug('Status polling failed:', error);
      }
    };
    
    // Poll toutes les 5 secondes si pas de WebSocket
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      const interval = setInterval(pollStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [state.jarvis.status]);
  
  const value = {
    state,
    actions,
    electronAPI,
    apiService,
    connectWebSocket,
    isWebMode: !window.electronAPI
  };
  
  return (
    <JarvisContext.Provider value={value}>
      {children}
    </JarvisContext.Provider>
  );
}

export { ActionTypes };