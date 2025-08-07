/**
 * 📝 JARVIS Error Logger - Système de logging avancé des erreurs
 * Composant pour logger, stocker et analyser les erreurs
 */
import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';

// Types d'erreurs
const ERROR_TYPES = {
  COMPONENT: 'component',
  API: 'api',
  AUDIO: 'audio',
  VISUALIZATION: 'visualization',
  NETWORK: 'network',
  SYSTEM: 'system',
  USER: 'user'
};

// Niveaux de sévérité
const SEVERITY_LEVELS = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
  INFO: 'info'
};

// Actions du reducer
const ACTIONS = {
  LOG_ERROR: 'LOG_ERROR',
  CLEAR_ERRORS: 'CLEAR_ERRORS',
  SET_CONFIG: 'SET_CONFIG',
  UPDATE_METRICS: 'UPDATE_METRICS',
  EXPORT_LOGS: 'EXPORT_LOGS'
};

// Configuration par défaut
const DEFAULT_CONFIG = {
  maxLogSize: 1000,
  enableConsoleLogging: true,
  enableRemoteLogging: true,
  enableLocalStorage: true,
  logLevels: Object.values(SEVERITY_LEVELS),
  autoReport: {
    enabled: false,
    threshold: SEVERITY_LEVELS.HIGH,
    maxAutoReports: 5
  },
  retention: {
    days: 7,
    maxSize: 10 * 1024 * 1024 // 10MB
  }
};

// State initial
const initialState = {
  errors: [],
  config: DEFAULT_CONFIG,
  metrics: {
    totalErrors: 0,
    errorsByType: {},
    errorsBySeverity: {},
    lastError: null,
    errorRate: 0,
    uptime: Date.now()
  },
  isInitialized: false
};

// Reducer pour gérer le state
const errorLoggerReducer = (state, action) => {
  switch (action.type) {
    case ACTIONS.LOG_ERROR:
      const newError = {
        ...action.payload,
        id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        sessionId: getSessionId()
      };

      const updatedErrors = [newError, ...state.errors].slice(0, state.config.maxLogSize);
      
      // Mise à jour des métriques
      const newMetrics = {
        ...state.metrics,
        totalErrors: state.metrics.totalErrors + 1,
        errorsByType: {
          ...state.metrics.errorsByType,
          [newError.type]: (state.metrics.errorsByType[newError.type] || 0) + 1
        },
        errorsBySeverity: {
          ...state.metrics.errorsBySeverity,
          [newError.severity]: (state.metrics.errorsBySeverity[newError.severity] || 0) + 1
        },
        lastError: newError,
        errorRate: calculateErrorRate(updatedErrors)
      };

      return {
        ...state,
        errors: updatedErrors,
        metrics: newMetrics
      };

    case ACTIONS.CLEAR_ERRORS:
      return {
        ...state,
        errors: [],
        metrics: {
          ...state.metrics,
          totalErrors: 0,
          errorsByType: {},
          errorsBySeverity: {},
          lastError: null,
          errorRate: 0
        }
      };

    case ACTIONS.SET_CONFIG:
      return {
        ...state,
        config: { ...state.config, ...action.payload }
      };

    case ACTIONS.UPDATE_METRICS:
      return {
        ...state,
        metrics: { ...state.metrics, ...action.payload }
      };

    default:
      return state;
  }
};

// Utilitaires
const getSessionId = () => {
  if (!window.jarvisSessionId) {
    window.jarvisSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  return window.jarvisSessionId;
};

const calculateErrorRate = (errors) => {
  if (errors.length < 2) return 0;
  
  const now = Date.now();
  const recentErrors = errors.filter(error => now - error.timestamp < 60000); // 1 minute
  return recentErrors.length;
};

const getBrowserInfo = () => ({
  userAgent: navigator.userAgent,
  platform: navigator.platform,
  language: navigator.language,
  cookieEnabled: navigator.cookieEnabled,
  onLine: navigator.onLine,
  viewport: {
    width: window.innerWidth,
    height: window.innerHeight
  },
  screen: {
    width: window.screen.width,
    height: window.screen.height,
    colorDepth: window.screen.colorDepth
  }
});

const getPerformanceInfo = () => {
  try {
    const navigation = performance.getEntriesByType('navigation')[0];
    const memory = performance.memory;
    
    return {
      loadTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : null,
      domContentLoaded: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : null,
      memory: memory ? {
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit
      } : null,
      timing: performance.now()
    };
  } catch (error) {
    return { error: error.message };
  }
};

// Context
const ErrorLoggerContext = createContext();

// Provider component
export const ErrorLoggerProvider = ({ children, config = {} }) => {
  const [state, dispatch] = useReducer(errorLoggerReducer, {
    ...initialState,
    config: { ...DEFAULT_CONFIG, ...config }
  });

  // Initialisation
  useEffect(() => {
    const init = async () => {
      try {
        // Charger les logs depuis localStorage si activé
        if (state.config.enableLocalStorage) {
          const savedLogs = localStorage.getItem('jarvis-error-logs');
          if (savedLogs) {
            const parsedLogs = JSON.parse(savedLogs);
            parsedLogs.forEach(log => {
              dispatch({ type: ACTIONS.LOG_ERROR, payload: log });
            });
          }
        }

        // Configurer les event listeners globaux
        setupGlobalErrorHandlers();
        
        dispatch({ type: ACTIONS.UPDATE_METRICS, payload: { isInitialized: true } });
      } catch (error) {
        console.error('Failed to initialize ErrorLogger:', error);
      }
    };

    init();
  }, []);

  // Sauvegarde automatique
  useEffect(() => {
    if (state.config.enableLocalStorage && state.errors.length > 0) {
      try {
        const logsToSave = state.errors.slice(0, 100); // Limiter à 100 pour localStorage
        localStorage.setItem('jarvis-error-logs', JSON.stringify(logsToSave));
      } catch (error) {
        console.warn('Failed to save logs to localStorage:', error);
      }
    }
  }, [state.errors, state.config.enableLocalStorage]);

  // Configuration des handlers globaux
  const setupGlobalErrorHandlers = useCallback(() => {
    // Erreurs JavaScript non capturées
    window.addEventListener('error', (event) => {
      logError({
        type: ERROR_TYPES.SYSTEM,
        severity: SEVERITY_LEVELS.HIGH,
        message: event.message,
        source: event.filename,
        line: event.lineno,
        column: event.colno,
        stack: event.error?.stack,
        context: 'global-error-handler'
      });
    });

    // Promesses rejetées non capturées
    window.addEventListener('unhandledrejection', (event) => {
      logError({
        type: ERROR_TYPES.SYSTEM,
        severity: SEVERITY_LEVELS.HIGH,
        message: event.reason?.message || 'Unhandled Promise Rejection',
        stack: event.reason?.stack,
        context: 'unhandled-rejection'
      });
    });

    // Erreurs de ressources
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        logError({
          type: ERROR_TYPES.SYSTEM,
          severity: SEVERITY_LEVELS.MEDIUM,
          message: `Resource failed to load: ${event.target.src || event.target.href}`,
          source: event.target.tagName,
          context: 'resource-error'
        });
      }
    }, true);
  }, []);

  // Fonction principale de logging
  const logError = useCallback((errorData) => {
    try {
      // Validation des données
      if (!errorData.type || !errorData.severity || !errorData.message) {
        console.warn('Invalid error data provided to ErrorLogger:', errorData);
        return;
      }

      // Vérifier si ce niveau de log est activé
      if (!state.config.logLevels.includes(errorData.severity)) {
        return;
      }

      // Enrichir les données d'erreur
      const enrichedError = {
        ...errorData,
        browserInfo: getBrowserInfo(),
        performanceInfo: getPerformanceInfo(),
        jarvisVersion: window.jarvisVersion || 'unknown',
        buildInfo: window.jarvisBuildInfo || {},
        url: window.location.href,
        referrer: document.referrer,
        userInteraction: document.hasFocus(),
        networkStatus: navigator.onLine ? 'online' : 'offline'
      };

      // Dispatch vers le reducer
      dispatch({ type: ACTIONS.LOG_ERROR, payload: enrichedError });

      // Log console si activé
      if (state.config.enableConsoleLogging) {
        const logLevel = errorData.severity === SEVERITY_LEVELS.CRITICAL ? 'error' :
                        errorData.severity === SEVERITY_LEVELS.HIGH ? 'error' :
                        errorData.severity === SEVERITY_LEVELS.MEDIUM ? 'warn' :
                        'info';
        
        console[logLevel]('🚨 JARVIS Error:', {
          type: errorData.type,
          severity: errorData.severity,
          message: errorData.message,
          data: enrichedError
        });
      }

      // Envoi distant si activé
      if (state.config.enableRemoteLogging) {
        sendToRemoteLogger(enrichedError);
      }

      // Auto-report si configuré
      if (state.config.autoReport.enabled && 
          shouldAutoReport(errorData.severity, state.metrics.totalErrors)) {
        triggerAutoReport(enrichedError);
      }

    } catch (error) {
      console.error('Failed to log error:', error);
    }
  }, [state.config, state.metrics]);

  // Envoi vers serveur distant
  const sendToRemoteLogger = useCallback(async (errorData) => {
    try {
      if (window.jarvisAPI?.logError) {
        await window.jarvisAPI.logError(errorData);
      }
    } catch (error) {
      console.warn('Failed to send error to remote logger:', error);
    }
  }, []);

  // Vérifier si auto-report nécessaire
  const shouldAutoReport = (severity, totalErrors) => {
    const config = state.config.autoReport;
    
    if (totalErrors >= config.maxAutoReports) return false;
    
    const severityOrder = [
      SEVERITY_LEVELS.INFO,
      SEVERITY_LEVELS.LOW,
      SEVERITY_LEVELS.MEDIUM,
      SEVERITY_LEVELS.HIGH,
      SEVERITY_LEVELS.CRITICAL
    ];
    
    const currentIndex = severityOrder.indexOf(severity);
    const thresholdIndex = severityOrder.indexOf(config.threshold);
    
    return currentIndex >= thresholdIndex;
  };

  // Déclencher rapport automatique
  const triggerAutoReport = useCallback((errorData) => {
    if (window.jarvisAPI?.submitAutoErrorReport) {
      window.jarvisAPI.submitAutoErrorReport(errorData);
    }
  }, []);

  // Autres fonctions utilitaires
  const clearErrors = useCallback(() => {
    dispatch({ type: ACTIONS.CLEAR_ERRORS });
    if (state.config.enableLocalStorage) {
      localStorage.removeItem('jarvis-error-logs');
    }
  }, [state.config.enableLocalStorage]);

  const updateConfig = useCallback((newConfig) => {
    dispatch({ type: ACTIONS.SET_CONFIG, payload: newConfig });
  }, []);

  const getErrorsByType = useCallback((type) => {
    return state.errors.filter(error => error.type === type);
  }, [state.errors]);

  const getErrorsBySeverity = useCallback((severity) => {
    return state.errors.filter(error => error.severity === severity);
  }, [state.errors]);

  const exportLogs = useCallback((format = 'json') => {
    try {
      const exportData = {
        metadata: {
          exportedAt: new Date().toISOString(),
          jarvisVersion: window.jarvisVersion || 'unknown',
          sessionId: getSessionId(),
          totalErrors: state.errors.length,
          metrics: state.metrics
        },
        errors: state.errors
      };

      if (format === 'json') {
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `jarvis-error-logs-${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(url);
      }

      return exportData;
    } catch (error) {
      console.error('Failed to export logs:', error);
      return null;
    }
  }, [state.errors, state.metrics]);

  const contextValue = {
    // State
    errors: state.errors,
    config: state.config,
    metrics: state.metrics,
    isInitialized: state.isInitialized,
    
    // Actions
    logError,
    clearErrors,
    updateConfig,
    exportLogs,
    
    // Queries
    getErrorsByType,
    getErrorsBySeverity,
    
    // Constants
    ERROR_TYPES,
    SEVERITY_LEVELS
  };

  return (
    <ErrorLoggerContext.Provider value={contextValue}>
      {children}
    </ErrorLoggerContext.Provider>
  );
};

// Hook pour utiliser le logger
export const useErrorLogger = () => {
  const context = useContext(ErrorLoggerContext);
  if (!context) {
    throw new Error('useErrorLogger must be used within an ErrorLoggerProvider');
  }
  return context;
};

// HOC pour wrap des composants avec logging automatique
export const withErrorLogging = (WrappedComponent, componentName) => {
  return class extends React.Component {
    constructor(props) {
      super(props);
      this.state = { hasError: false };
    }

    static getDerivedStateFromError(error) {
      return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
      const logger = this.context;
      if (logger) {
        logger.logError({
          type: ERROR_TYPES.COMPONENT,
          severity: SEVERITY_LEVELS.HIGH,
          message: error.message,
          component: componentName || WrappedComponent.name,
          stack: error.stack,
          componentStack: errorInfo.componentStack,
          props: this.props
        });
      }
    }

    render() {
      if (this.state.hasError) {
        return (
          <div style={{ 
            padding: '20px', 
            color: '#ff3b30', 
            fontFamily: '"Orbitron", monospace',
            textAlign: 'center'
          }}>
            ⚠️ Component Error: {componentName || WrappedComponent.name}
          </div>
        );
      }

      return <WrappedComponent {...this.props} />;
    }
  };
};

export default ErrorLoggerProvider;