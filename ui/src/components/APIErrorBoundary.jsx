/**
 * 🌐 JARVIS API Error Boundary - Gestion des erreurs d'API et réseau
 * Error Boundary spécialisé pour les erreurs de communication avec les services JARVIS
 */
import React from 'react';
import { Box, Typography, Button, Alert, Chip, LinearProgress } from '@mui/material';
import { 
  CloudOff as CloudOffIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Refresh as RefreshIcon,
  Speed as SpeedIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import ErrorBoundary from './ErrorBoundary';
import '../styles/jarvis-holographic.css';

class APIErrorBoundary extends ErrorBoundary {
  constructor(props) {
    super(props);
    this.state = {
      ...this.state,
      connectionStatus: 'unknown',
      apiEndpoints: {},
      networkDiagnostics: {},
      retryTimer: null,
      autoRetryCount: 0,
      isRetrying: false
    };
  }

  async componentDidMount() {
    await this.checkNetworkStatus();
    await this.checkAPIEndpoints();
    this.startNetworkMonitoring();
  }

  componentWillUnmount() {
    if (this.networkMonitorInterval) {
      clearInterval(this.networkMonitorInterval);
    }
    if (this.state.retryTimer) {
      clearTimeout(this.state.retryTimer);
    }
  }

  startNetworkMonitoring = () => {
    // Surveillance continue du réseau
    this.networkMonitorInterval = setInterval(async () => {
      if (!this.state.hasError) {
        await this.checkNetworkStatus();
      }
    }, 30000); // Vérification toutes les 30 secondes

    // Écouter les événements de réseau
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
  };

  handleOnline = async () => {
    this.setState({ connectionStatus: 'online' });
    if (this.state.hasError && this.state.autoRetryCount < 3) {
      await this.handleAutoRetry();
    }
  };

  handleOffline = () => {
    this.setState({ connectionStatus: 'offline' });
  };

  checkNetworkStatus = async () => {
    const diagnostics = {
      online: navigator.onLine,
      connection: null,
      latency: null,
      timestamp: Date.now()
    };

    // Informations de connexion si disponibles
    if ('connection' in navigator) {
      const conn = navigator.connection;
      diagnostics.connection = {
        effectiveType: conn.effectiveType,
        downlink: conn.downlink,
        rtt: conn.rtt,
        saveData: conn.saveData
      };
    }

    // Test de latence simple
    try {
      const start = performance.now();
      await fetch('/favicon.ico', { method: 'HEAD', cache: 'no-cache' });
      diagnostics.latency = Math.round(performance.now() - start);
    } catch (e) {
      diagnostics.latency = 'timeout';
    }

    this.setState({ 
      networkDiagnostics: diagnostics,
      connectionStatus: diagnostics.online ? 'online' : 'offline'
    });
  };

  checkAPIEndpoints = async () => {
    const endpoints = {
      brainAPI: { status: 'unknown', latency: null },
      gpuStats: { status: 'unknown', latency: null },
      sttService: { status: 'unknown', latency: null },
      ttsService: { status: 'unknown', latency: null }
    };

    const baseURL = window.location.origin;
    const apiChecks = [
      { name: 'brainAPI', url: `${baseURL}/api/health` },
      { name: 'gpuStats', url: `${baseURL}/api/gpu/status` },
      { name: 'sttService', url: `${baseURL}/api/stt/health` },
      { name: 'ttsService', url: `${baseURL}/api/tts/health` }
    ];

    await Promise.allSettled(apiChecks.map(async (check) => {
      try {
        const start = performance.now();
        const response = await fetch(check.url, {
          method: 'GET',
          timeout: 5000,
          headers: { 'Cache-Control': 'no-cache' }
        });
        const latency = Math.round(performance.now() - start);
        
        endpoints[check.name] = {
          status: response.ok ? 'online' : 'error',
          latency,
          statusCode: response.status
        };
      } catch (error) {
        endpoints[check.name] = {
          status: 'offline',
          latency: null,
          error: error.message
        };
      }
    }));

    this.setState({ apiEndpoints: endpoints });
  };

  logError = (error, errorInfo) => {
    const apiErrorData = {
      ...this.createBaseErrorData(error, errorInfo),
      apiSpecific: {
        connectionStatus: this.state.connectionStatus,
        networkDiagnostics: this.state.networkDiagnostics,
        apiEndpoints: this.state.apiEndpoints,
        autoRetryCount: this.state.autoRetryCount,
        errorContext: this.analyzeAPIError(error)
      }
    };

    console.error('🌐 JARVIS API Error:', apiErrorData);

    if (window.jarvisAPI?.logAPIError) {
      window.jarvisAPI.logAPIError(apiErrorData);
    }

    if (this.props.onError) {
      this.props.onError(apiErrorData);
    }
  };

  analyzeAPIError = (error) => {
    const context = {
      type: 'unknown',
      severity: 'medium',
      recoverable: true,
      suggestedAction: 'retry'
    };

    if (!error) return context;

    const message = error.message?.toLowerCase() || '';
    
    // Classification des erreurs
    if (message.includes('network') || message.includes('fetch')) {
      context.type = 'network';
      context.severity = 'high';
      context.suggestedAction = 'check_connection';
    } else if (message.includes('timeout')) {
      context.type = 'timeout';
      context.severity = 'medium';
      context.suggestedAction = 'retry_with_delay';
    } else if (message.includes('unauthorized') || message.includes('403')) {
      context.type = 'authentication';
      context.severity = 'high';
      context.recoverable = false;
      context.suggestedAction = 'reauth';
    } else if (message.includes('500') || message.includes('server')) {
      context.type = 'server_error';
      context.severity = 'high';
      context.suggestedAction = 'wait_and_retry';
    } else if (message.includes('429')) {
      context.type = 'rate_limit';
      context.severity = 'low';
      context.suggestedAction = 'wait_and_retry';
    }

    return context;
  };

  handleAutoRetry = async () => {
    if (this.state.autoRetryCount >= 3 || this.state.isRetrying) {
      return;
    }

    this.setState({ 
      isRetrying: true,
      autoRetryCount: this.state.autoRetryCount + 1 
    });

    // Délai progressif (exponential backoff)
    const delay = Math.min(1000 * Math.pow(2, this.state.autoRetryCount), 30000);
    
    const retryTimer = setTimeout(async () => {
      await this.checkNetworkStatus();
      await this.checkAPIEndpoints();
      
      this.setState({ isRetrying: false });
      this.handleRetry();
    }, delay);

    this.setState({ retryTimer });
  };

  handleManualRetry = async () => {
    this.setState({ isRetrying: true, autoRetryCount: 0 });
    
    await this.checkNetworkStatus();
    await this.checkAPIEndpoints();
    
    this.setState({ isRetrying: false });
    this.handleRetry();
  };

  getEndpointStatusColor = (status) => {
    switch (status) {
      case 'online': return '#00ff88';
      case 'error': return '#ff9500';
      case 'offline': return '#ff3b30';
      default: return '#666666';
    }
  };

  render() {
    if (this.state.hasError) {
      const { networkDiagnostics, apiEndpoints, isRetrying, connectionStatus } = this.state;
      const isOffline = connectionStatus === 'offline' || !networkDiagnostics.online;

      return (
        <Box
          className="jarvis-panel"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '500px',
            maxWidth: '900px',
            margin: '0 auto',
            padding: '40px',
            textAlign: 'center',
            border: '2px solid #ff3b30',
            boxShadow: '0 0 30px rgba(255, 59, 48, 0.3)'
          }}
        >
          {/* Icône de réseau avec statut */}
          <Box
            sx={{
              fontSize: '4rem',
              color: isOffline ? '#ff3b30' : '#ff9500',
              textShadow: `0 0 20px ${isOffline ? '#ff3b30' : '#ff9500'}`,
              animation: 'error-pulse 2s ease-in-out infinite',
              marginBottom: '20px'
            }}
          >
            {isOffline ? <WifiOffIcon fontSize="inherit" /> : <CloudOffIcon fontSize="inherit" />}
          </Box>

          <Typography
            variant="h4"
            className="jarvis-text-glow"
            sx={{
              fontFamily: '"Orbitron", monospace',
              fontWeight: 'bold',
              color: '#ff3b30',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '20px'
            }}
          >
            {isOffline ? 'NETWORK DISCONNECTED' : 'API COMMUNICATION FAILURE'}
          </Typography>

          <Typography
            variant="body1"
            sx={{
              fontFamily: '"Orbitron", monospace',
              color: '#00d4ff',
              marginBottom: '30px',
              maxWidth: '700px'
            }}
          >
            {isOffline 
              ? 'JARVIS has lost connection to the network. All remote services are unavailable.'
              : 'Communication with JARVIS backend services has been interrupted. Some features may be limited.'}
          </Typography>

          {/* Statut de la connexion */}
          <Box sx={{ marginBottom: '30px', width: '100%', maxWidth: '600px' }}>
            <Typography
              variant="h6"
              sx={{
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '15px'
              }}
            >
              🌐 NETWORK STATUS
            </Typography>

            <Box sx={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '20px' }}>
              <Chip
                icon={networkDiagnostics.online ? <WifiIcon /> : <WifiOffIcon />}
                label={`Connection: ${networkDiagnostics.online ? 'ONLINE' : 'OFFLINE'}`}
                sx={{
                  backgroundColor: networkDiagnostics.online ? 'rgba(0, 255, 136, 0.2)' : 'rgba(255, 59, 48, 0.2)',
                  color: networkDiagnostics.online ? '#00ff88' : '#ff3b30',
                  fontFamily: '"Orbitron", monospace'
                }}
              />
              
              {networkDiagnostics.latency && (
                <Chip
                  icon={<SpeedIcon />}
                  label={`Latency: ${networkDiagnostics.latency}ms`}
                  sx={{
                    backgroundColor: 'rgba(0, 212, 255, 0.2)',
                    color: '#00d4ff',
                    fontFamily: '"Orbitron", monospace'
                  }}
                />
              )}

              {networkDiagnostics.connection?.effectiveType && (
                <Chip
                  label={`Type: ${networkDiagnostics.connection.effectiveType.toUpperCase()}`}
                  sx={{
                    backgroundColor: 'rgba(255, 149, 0, 0.2)',
                    color: '#ff9500',
                    fontFamily: '"Orbitron", monospace'
                  }}
                />
              )}
            </Box>
          </Box>

          {/* Statut des services API */}
          <Box sx={{ marginBottom: '30px', width: '100%', maxWidth: '600px' }}>
            <Typography
              variant="h6"
              sx={{
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '15px'
              }}
            >
              🔧 SERVICE STATUS
            </Typography>

            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px' }}>
              {Object.entries(apiEndpoints).map(([service, status]) => (
                <Box
                  key={service}
                  sx={{
                    padding: '10px',
                    border: `1px solid ${this.getEndpointStatusColor(status.status)}`,
                    borderRadius: '5px',
                    backgroundColor: `${this.getEndpointStatusColor(status.status)}20`
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      color: this.getEndpointStatusColor(status.status),
                      fontFamily: '"Orbitron", monospace',
                      fontWeight: 'bold',
                      marginBottom: '5px'
                    }}
                  >
                    {service.toUpperCase()}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      color: '#ffffff',
                      display: 'block'
                    }}
                  >
                    {status.status.toUpperCase()}
                  </Typography>
                  {status.latency && (
                    <Typography
                      variant="caption"
                      sx={{
                        color: '#999999',
                        display: 'block'
                      }}
                    >
                      {status.latency}ms
                    </Typography>
                  )}
                </Box>
              ))}
            </Box>
          </Box>

          {/* Progress bar si retry en cours */}
          {isRetrying && (
            <Box sx={{ width: '100%', maxWidth: '400px', marginBottom: '20px' }}>
              <Typography
                variant="body2"
                sx={{
                  color: '#00d4ff',
                  fontFamily: '"Orbitron", monospace',
                  marginBottom: '10px'
                }}
              >
                RECONNECTING TO SERVICES...
              </Typography>
              <LinearProgress
                sx={{
                  backgroundColor: 'rgba(0, 212, 255, 0.2)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: '#00d4ff'
                  }
                }}
              />
            </Box>
          )}

          {/* Boutons d'action */}
          <Box sx={{ display: 'flex', gap: '15px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={this.handleManualRetry}
              disabled={isRetrying}
              className="jarvis-button"
              sx={{
                borderColor: '#00ff88',
                color: '#00ff88',
                '&:hover': {
                  borderColor: '#00ff88',
                  backgroundColor: 'rgba(0, 255, 136, 0.1)'
                }
              }}
            >
              {isRetrying ? 'RECONNECTING...' : 'RETRY CONNECTION'}
            </Button>

            <Button
              variant="outlined"
              onClick={() => window.location.reload()}
              className="jarvis-button"
              sx={{
                borderColor: '#00d4ff',
                color: '#00d4ff',
                '&:hover': {
                  borderColor: '#00d4ff',
                  backgroundColor: 'rgba(0, 212, 255, 0.1)'
                }
              }}
            >
              RELOAD APPLICATION
            </Button>

            <Button
              variant="outlined"
              onClick={() => this.handleReset()}
              className="jarvis-button"
              sx={{
                borderColor: '#ff9500',
                color: '#ff9500',
                '&:hover': {
                  borderColor: '#ff9500',
                  backgroundColor: 'rgba(255, 149, 0, 0.1)'
                }
              }}
            >
              OFFLINE MODE
            </Button>
          </Box>

          {/* Info de mode dégradé */}
          <Alert
            severity="info"
            icon={<ErrorIcon />}
            sx={{
              marginTop: '20px',
              backgroundColor: 'rgba(0, 212, 255, 0.1)',
              border: '1px solid rgba(0, 212, 255, 0.3)',
              color: '#00d4ff',
              fontFamily: '"Orbitron", monospace',
              '& .MuiAlert-icon': {
                color: '#00d4ff'
              }
            }}
          >
            JARVIS will attempt automatic reconnection. Some features will operate in degraded mode.
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default APIErrorBoundary;