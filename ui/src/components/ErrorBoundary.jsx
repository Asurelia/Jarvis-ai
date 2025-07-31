/**
 * 🛡️ JARVIS Error Boundary - Gestion générique des erreurs
 * Composant d'erreur avec style holographique Iron Man
 */
import React from 'react';
import { Box, Typography, Button, Alert, Collapse, IconButton } from '@mui/material';
import { ExpandMore as ExpandMoreIcon, Refresh as RefreshIcon, Home as HomeIcon } from '@mui/icons-material';
import '../styles/jarvis-holographic.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      showDetails: false,
      startTime: Date.now()
    };
  }

  static getDerivedStateFromError(error) {
    // Mettre à jour le state pour afficher l'UI d'erreur
    return {
      hasError: true,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log de l'erreur avec détails complets
    this.logError(error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
      hasError: true
    });
  }

  logError = (error, errorInfo) => {
    const errorData = {
      timestamp: new Date().toISOString(),
      errorId: this.state.errorId || `error_${Date.now()}`,
      component: this.props.componentName || 'Unknown',
      error: {
        name: error?.name,
        message: error?.message,
        stack: error?.stack
      },
      errorInfo: {
        componentStack: errorInfo?.componentStack
      },
      props: this.props.logProps ? this.props : 'Props logging disabled',
      retryCount: this.state.retryCount,
      uptime: Date.now() - this.state.startTime,
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // Log dans la console
    console.error('🚨 JARVIS Error Boundary:', errorData);

    // Envoyer au système de logging JARVIS si disponible
    if (window.jarvisAPI?.logError) {
      window.jarvisAPI.logError(errorData);
    }

    // Log vers le contexte JARVIS si disponible
    if (this.props.onError) {
      this.props.onError(errorData);
    }
  };

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1,
      showDetails: false
    }));

    // Callback de retry personnalisé
    if (this.props.onRetry) {
      this.props.onRetry(this.state.retryCount + 1);
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      showDetails: false
    });

    // Callback de reset personnalisé
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  handleHome = () => {
    if (this.props.onHome) {
      this.props.onHome();
    } else {
      window.location.href = '/';
    }
  };

  toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails
    }));
  };

  render() {
    if (this.state.hasError) {
      const { error, errorInfo, showDetails, retryCount } = this.state;
      const { 
        title = "SYSTEM ERROR DETECTED",
        message = "A critical error has occurred in the JARVIS interface",
        showRetry = true,
        showReset = true,
        showHome = true,
        maxRetries = 3,
        variant = "critical" // critical, warning, info
      } = this.props;

      const canRetry = showRetry && retryCount < maxRetries;

      return (
        <Box
          className="jarvis-panel"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: this.props.fullHeight ? '100vh' : '400px',
            maxWidth: '800px',
            margin: '0 auto',
            padding: '40px',
            textAlign: 'center',
            position: 'relative',
            overflow: 'hidden',
            border: variant === 'critical' ? '2px solid #ff3b30' : 
                   variant === 'warning' ? '2px solid #ff9500' : '2px solid #00d4ff',
            boxShadow: variant === 'critical' ? '0 0 30px rgba(255, 59, 48, 0.3)' :
                      variant === 'warning' ? '0 0 30px rgba(255, 149, 0, 0.3)' : '0 0 30px rgba(0, 212, 255, 0.3)'
          }}
        >
          {/* Animation de scan d'erreur */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '2px',
              background: variant === 'critical' ? 
                'linear-gradient(90deg, transparent 0%, #ff3b30 50%, transparent 100%)' :
                'linear-gradient(90deg, transparent 0%, #ff9500 50%, transparent 100%)',
              animation: 'error-scan 2s linear infinite'
            }}
          />

          {/* Icône d'erreur holographique */}
          <Box
            sx={{
              fontSize: '4rem',
              color: variant === 'critical' ? '#ff3b30' : '#ff9500',
              textShadow: `0 0 20px ${variant === 'critical' ? '#ff3b30' : '#ff9500'}`,
              animation: 'error-pulse 2s ease-in-out infinite',
              marginBottom: '20px'
            }}
          >
            ⚠️
          </Box>

          {/* Titre d'erreur */}
          <Typography
            variant="h4"
            className="jarvis-text-glow"
            sx={{
              fontFamily: '"Orbitron", monospace',
              fontWeight: 'bold',
              color: variant === 'critical' ? '#ff3b30' : '#ff9500',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '20px',
              textShadow: `0 0 15px ${variant === 'critical' ? '#ff3b30' : '#ff9500'}`
            }}
          >
            {title}
          </Typography>

          {/* Message d'erreur */}
          <Typography
            variant="body1"
            sx={{
              fontFamily: '"Orbitron", monospace',
              color: '#00d4ff',
              marginBottom: '20px',
              maxWidth: '600px',
              lineHeight: 1.6
            }}
          >
            {message}
          </Typography>

          {/* Informations d'erreur */}
          {error && (
            <Alert
              severity="error"
              sx={{
                backgroundColor: 'rgba(255, 59, 48, 0.1)',
                border: '1px solid rgba(255, 59, 48, 0.3)',
                color: '#ff3b30',
                marginBottom: '20px',
                fontFamily: '"Orbitron", monospace',
                '& .MuiAlert-icon': {
                  color: '#ff3b30'
                }
              }}
            >
              <strong>{error.name}:</strong> {error.message}
            </Alert>
          )}

          {/* Compteur de tentatives */}
          {retryCount > 0 && (
            <Typography
              variant="body2"
              sx={{
                color: '#ff9500',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '20px'
              }}
            >
              Retry attempts: {retryCount}/{maxRetries}
            </Typography>
          )}

          {/* Boutons d'action */}
          <Box sx={{ display: 'flex', gap: '15px', flexWrap: 'wrap', justifyContent: 'center' }}>
            {canRetry && (
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={this.handleRetry}
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
                RETRY SYSTEM
              </Button>
            )}

            {showReset && (
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={this.handleReset}
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
                RESET MODULE
              </Button>
            )}

            {showHome && (
              <Button
                variant="outlined"
                startIcon={<HomeIcon />}
                onClick={this.handleHome}
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
                RETURN HOME
              </Button>
            )}
          </Box>

          {/* Détails techniques (collapsible) */}
          {(error || errorInfo) && (
            <Box sx={{ width: '100%', marginTop: '30px' }}>
              <Box
                onClick={this.toggleDetails}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  color: '#00d4ff',
                  fontFamily: '"Orbitron", monospace',
                  fontSize: '0.9rem',
                  '&:hover': {
                    color: '#00ff88'
                  }
                }}
              >
                <span>TECHNICAL DETAILS</span>
                <IconButton
                  size="small"
                  sx={{
                    color: '#00d4ff',
                    transform: showDetails ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s ease'
                  }}
                >
                  <ExpandMoreIcon />
                </IconButton>
              </Box>

              <Collapse in={showDetails}>
                <Box
                  sx={{
                    marginTop: '15px',
                    padding: '20px',
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(0, 212, 255, 0.3)',
                    borderRadius: '5px',
                    fontFamily: 'monospace',
                    fontSize: '0.8rem',
                    color: '#ffffff',
                    textAlign: 'left',
                    maxHeight: '300px',
                    overflowY: 'auto'
                  }}
                >
                  {error && (
                    <Box sx={{ marginBottom: '15px' }}>
                      <Typography variant="subtitle2" sx={{ color: '#ff3b30', fontWeight: 'bold' }}>
                        Error Stack:
                      </Typography>
                      <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.7rem', margin: '5px 0' }}>
                        {error.stack}
                      </pre>
                    </Box>
                  )}

                  {errorInfo && (
                    <Box>
                      <Typography variant="subtitle2" sx={{ color: '#ff9500', fontWeight: 'bold' }}>
                        Component Stack:
                      </Typography>
                      <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.7rem', margin: '5px 0' }}>
                        {errorInfo.componentStack}
                      </pre>
                    </Box>
                  )}

                  <Box sx={{ marginTop: '15px', fontSize: '0.7rem', color: '#00d4ff' }}>
                    <div>Error ID: {this.state.errorId}</div>
                    <div>Timestamp: {new Date().toISOString()}</div>
                    <div>Component: {this.props.componentName || 'Unknown'}</div>
                  </Box>
                </Box>
              </Collapse>
            </Box>
          )}

          {/* Grille holographique de fond pour l'erreur */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundImage: 
                variant === 'critical' ? 
                  'linear-gradient(rgba(255, 59, 48, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 59, 48, 0.1) 1px, transparent 1px)' :
                  'linear-gradient(rgba(255, 149, 0, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 149, 0, 0.1) 1px, transparent 1px)',
              backgroundSize: '20px 20px',
              opacity: 0.3,
              pointerEvents: 'none',
              zIndex: -1
            }}
          />
        </Box>
      );
    }

    // Rendu normal des enfants si pas d'erreur
    return this.props.children;
  }
}

// Styles CSS pour les animations (à ajouter au fichier CSS global)
const errorStyles = `
@keyframes error-scan {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@keyframes error-pulse {
  0%, 100% { 
    transform: scale(1);
    opacity: 1;
  }
  50% { 
    transform: scale(1.1);
    opacity: 0.8;
  }
}
`;

// Injecter les styles si pas déjà présents
if (typeof document !== 'undefined' && !document.getElementById('error-boundary-styles')) {
  const style = document.createElement('style');
  style.id = 'error-boundary-styles';
  style.textContent = errorStyles;
  document.head.appendChild(style);
}

export default ErrorBoundary;