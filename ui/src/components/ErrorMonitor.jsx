/**
 * 📊 JARVIS Error Monitor - Dashboard de surveillance des erreurs
 * Composant pour surveiller et afficher les métriques d'erreurs en temps réel
 */
import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Chip, 
  List, 
  ListItem, 
  ListItemText,
  LinearProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import { 
  TrendingUp as TrendingUpIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Timeline as TimelineIcon,
  CloudDownload as CloudDownloadIcon
} from '@mui/icons-material';
import { useErrorLogger } from './ErrorLogger';
import ErrorReporter from './ErrorReporter';
import '../styles/jarvis-holographic.css';

const ErrorMonitor = ({ isVisible = false, onClose = () => {} }) => {
  const { errors, metrics, clearErrors, exportLogs, ERROR_TYPES, SEVERITY_LEVELS } = useErrorLogger();
  const [selectedError, setSelectedError] = useState(null);
  const [showReporter, setShowReporter] = useState(false);
  const [timeRange, setTimeRange] = useState('1h'); // 1h, 6h, 24h, all

  // Calcul des métriques en temps réel
  const [realtimeMetrics, setRealtimeMetrics] = useState({
    errorRate: 0,
    uptime: 0,
    healthScore: 100,
    criticalCount: 0,
    recentErrors: []
  });

  useEffect(() => {
    const calculateMetrics = () => {
      const now = Date.now();
      const timeRanges = {
        '1h': 60 * 60 * 1000,
        '6h': 6 * 60 * 60 * 1000,
        '24h': 24 * 60 * 60 * 1000,
        'all': Infinity
      };

      const rangeMs = timeRanges[timeRange];
      const filteredErrors = errors.filter(error => 
        now - error.timestamp < rangeMs
      );

      const criticalErrors = filteredErrors.filter(error => 
        error.severity === SEVERITY_LEVELS.CRITICAL
      );

      const errorRate = filteredErrors.length / Math.max((rangeMs / (60 * 60 * 1000)), 1);
      const healthScore = Math.max(0, 100 - (criticalErrors.length * 10) - (filteredErrors.length * 2));

      setRealtimeMetrics({
        errorRate: Math.round(errorRate * 100) / 100,
        uptime: Math.round((now - metrics.uptime) / 1000),
        healthScore: Math.round(healthScore),
        criticalCount: criticalErrors.length,
        recentErrors: filteredErrors.slice(0, 10)
      });
    };

    calculateMetrics();
    const interval = setInterval(calculateMetrics, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [errors, metrics.uptime, timeRange, SEVERITY_LEVELS]);

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case SEVERITY_LEVELS.CRITICAL:
        return <ErrorIcon sx={{ color: '#ff3b30' }} />;
      case SEVERITY_LEVELS.HIGH:
        return <ErrorIcon sx={{ color: '#ff9500' }} />;
      case SEVERITY_LEVELS.MEDIUM:
        return <WarningIcon sx={{ color: '#ffcc00' }} />;
      case SEVERITY_LEVELS.LOW:
        return <InfoIcon sx={{ color: '#00d4ff' }} />;
      default:
        return <CheckCircleIcon sx={{ color: '#00ff88' }} />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case SEVERITY_LEVELS.CRITICAL: return '#ff3b30';
      case SEVERITY_LEVELS.HIGH: return '#ff9500';
      case SEVERITY_LEVELS.MEDIUM: return '#ffcc00';
      case SEVERITY_LEVELS.LOW: return '#00d4ff';
      default: return '#00ff88';
    }
  };

  const getHealthColor = (score) => {
    if (score >= 80) return '#00ff88';
    if (score >= 60) return '#ffcc00';
    if (score >= 40) return '#ff9500';
    return '#ff3b30';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatUptime = (seconds) => {
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
  };

  const handleExportLogs = () => {
    exportLogs('json');
  };

  const handleClearErrors = () => {
    if (window.confirm('Are you sure you want to clear all error logs?')) {
      clearErrors();
    }
  };

  if (!isVisible) return null;

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px'
      }}
    >
      <Box
        className="jarvis-panel"
        sx={{
          width: '95%',
          height: '90%',
          overflowY: 'auto',
          padding: '30px',
          border: '2px solid #00d4ff',
          boxShadow: '0 0 30px rgba(0, 212, 255, 0.3)'
        }}
      >
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <Box>
            <Typography
              variant="h4"
              className="jarvis-text-glow"
              sx={{
                fontFamily: '"Orbitron", monospace',
                fontWeight: 'bold',
                color: '#00d4ff',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                marginBottom: '10px'
              }}
            >
              🔍 ERROR MONITOR
            </Typography>
            <Typography
              variant="body1"
              sx={{
                fontFamily: '"Orbitron", monospace',
                color: '#ffffff',
                opacity: 0.8
              }}
            >
              Real-time error tracking and system health monitoring
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: '10px' }}>
            {['1h', '6h', '24h', 'all'].map((range) => (
              <Button
                key={range}
                variant={timeRange === range ? 'contained' : 'outlined'}
                size="small"
                onClick={() => setTimeRange(range)}
                className="jarvis-button"
                sx={{
                  minWidth: '50px',
                  height: '32px',
                  fontSize: '0.75rem'
                }}
              >
                {range.toUpperCase()}
              </Button>
            ))}
          </Box>
        </Box>

        {/* Métriques principales */}
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
          {/* System Health */}
          <Card className="jarvis-panel" sx={{ padding: '20px' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: '15px' }}>
              <CheckCircleIcon sx={{ color: getHealthColor(realtimeMetrics.healthScore), marginRight: '10px' }} />
              <Typography variant="h6" sx={{ color: '#ffffff', fontFamily: '"Orbitron", monospace' }}>
                System Health
              </Typography>
            </Box>
            <Typography
              variant="h3"
              sx={{
                color: getHealthColor(realtimeMetrics.healthScore),
                fontFamily: '"Orbitron", monospace',
                fontWeight: 'bold',
                textAlign: 'center'
              }}
            >
              {realtimeMetrics.healthScore}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={realtimeMetrics.healthScore}
              sx={{
                marginTop: '10px',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: getHealthColor(realtimeMetrics.healthScore)
                }
              }}
            />
          </Card>

          {/* Error Rate */}
          <Card className="jarvis-panel" sx={{ padding: '20px' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: '15px' }}>
              <TrendingUpIcon sx={{ color: '#ff9500', marginRight: '10px' }} />
              <Typography variant="h6" sx={{ color: '#ffffff', fontFamily: '"Orbitron", monospace' }}>
                Error Rate
              </Typography>
            </Box>
            <Typography
              variant="h3"
              sx={{
                color: '#ff9500',
                fontFamily: '"Orbitron", monospace',
                fontWeight: 'bold',
                textAlign: 'center'
              }}
            >
              {realtimeMetrics.errorRate}/h
            </Typography>
            <Typography
              variant="body2"
              sx={{ color: '#999999', textAlign: 'center', marginTop: '5px' }}
            >
              Last {timeRange}
            </Typography>
          </Card>

          {/* Critical Errors */}
          <Card className="jarvis-panel" sx={{ padding: '20px' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: '15px' }}>
              <ErrorIcon sx={{ color: '#ff3b30', marginRight: '10px' }} />
              <Typography variant="h6" sx={{ color: '#ffffff', fontFamily: '"Orbitron", monospace' }}>
                Critical Errors
              </Typography>
            </Box>
            <Typography
              variant="h3"
              sx={{
                color: '#ff3b30',
                fontFamily: '"Orbitron", monospace',
                fontWeight: 'bold',
                textAlign: 'center'
              }}
            >
              {realtimeMetrics.criticalCount}
            </Typography>
            <Typography
              variant="body2"
              sx={{ color: '#999999', textAlign: 'center', marginTop: '5px' }}
            >
              Requires attention
            </Typography>
          </Card>

          {/* Uptime */}
          <Card className="jarvis-panel" sx={{ padding: '20px' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: '15px' }}>
              <TimelineIcon sx={{ color: '#00ff88', marginRight: '10px' }} />
              <Typography variant="h6" sx={{ color: '#ffffff', fontFamily: '"Orbitron", monospace' }}>
                Uptime
              </Typography>
            </Box>
            <Typography
              variant="h4"
              sx={{
                color: '#00ff88',
                fontFamily: '"Orbitron", monospace',
                fontWeight: 'bold',
                textAlign: 'center',
                fontSize: '1.5rem'
              }}
            >
              {formatUptime(realtimeMetrics.uptime)}
            </Typography>
            <Typography
              variant="body2"
              sx={{ color: '#999999', textAlign: 'center', marginTop: '5px' }}
            >
              Session duration
            </Typography>
          </Card>
        </Box>

        {/* Erreurs récentes */}
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
          {/* Liste des erreurs récentes */}
          <Box>
            <Typography
              variant="h5"
              sx={{
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '20px'
              }}
            >
              📋 Recent Errors
            </Typography>
            
            <List sx={{ maxHeight: '400px', overflowY: 'auto' }}>
              {realtimeMetrics.recentErrors.length === 0 ? (
                <ListItem>
                  <ListItemText
                    primary="No errors in selected time range"
                    sx={{
                      '& .MuiListItemText-primary': {
                        color: '#00ff88',
                        fontFamily: '"Orbitron", monospace',
                        textAlign: 'center'
                      }
                    }}
                  />
                </ListItem>
              ) : (
                realtimeMetrics.recentErrors.map((error, index) => (
                  <ListItem
                    key={error.id || index}
                    sx={{
                      backgroundColor: 'rgba(0, 0, 0, 0.3)',
                      marginBottom: '10px',
                      borderRadius: '5px',
                      border: `1px solid ${getSeverityColor(error.severity)}30`,
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'rgba(0, 0, 0, 0.5)'
                      }
                    }}
                    onClick={() => setSelectedError(error)}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      {getSeverityIcon(error.severity)}
                      <Box sx={{ marginLeft: '15px', flex: 1 }}>
                        <Typography
                          variant="body1"
                          sx={{
                            color: '#ffffff',
                            fontFamily: '"Orbitron", monospace',
                            fontWeight: 'bold'
                          }}
                        >
                          {error.component || 'Unknown Component'}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            color: '#cccccc',
                            marginTop: '5px'
                          }}
                        >
                          {error.message?.substring(0, 80)}...
                        </Typography>
                        <Typography
                          variant="caption"
                          sx={{
                            color: '#999999',
                            marginTop: '5px',
                            display: 'block'
                          }}
                        >
                          {formatTimestamp(error.timestamp)}
                        </Typography>
                      </Box>
                      <Chip
                        label={error.severity.toUpperCase()}
                        size="small"
                        sx={{
                          backgroundColor: `${getSeverityColor(error.severity)}20`,
                          color: getSeverityColor(error.severity),
                          fontFamily: '"Orbitron", monospace',
                          fontSize: '0.7rem'
                        }}
                      />
                    </Box>
                  </ListItem>
                ))
              )}
            </List>
          </Box>

          {/* Statistiques par type et sévérité */}
          <Box>
            <Typography
              variant="h5"
              sx={{
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '20px'
              }}
            >
              📊 Error Statistics
            </Typography>

            {/* Par sévérité */}
            <Box sx={{ marginBottom: '30px' }}>
              <Typography
                variant="h6"
                sx={{
                  color: '#ffffff',
                  fontFamily: '"Orbitron", monospace',
                  marginBottom: '15px'
                }}
              >
                By Severity
              </Typography>
              {Object.entries(metrics.errorsBySeverity).map(([severity, count]) => (
                <Box
                  key={severity}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '10px'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    {getSeverityIcon(severity)}
                    <Typography
                      sx={{
                        color: '#ffffff',
                        fontFamily: '"Orbitron", monospace',
                        marginLeft: '10px'
                      }}
                    >
                      {severity.toUpperCase()}
                    </Typography>
                  </Box>
                  <Chip
                    label={count}
                    size="small"
                    sx={{
                      backgroundColor: `${getSeverityColor(severity)}20`,
                      color: getSeverityColor(severity),
                      fontWeight: 'bold'
                    }}
                  />
                </Box>
              ))}
            </Box>

            {/* Par type */}
            <Box>
              <Typography
                variant="h6"
                sx={{
                  color: '#ffffff',
                  fontFamily: '"Orbitron", monospace',
                  marginBottom: '15px'
                }}
              >
                By Component Type
              </Typography>
              {Object.entries(metrics.errorsByType).map(([type, count]) => (
                <Box
                  key={type}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '10px'
                  }}
                >
                  <Typography
                    sx={{
                      color: '#ffffff',
                      fontFamily: '"Orbitron", monospace'
                    }}
                  >
                    {type.toUpperCase()}
                  </Typography>
                  <Chip
                    label={count}
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(0, 212, 255, 0.2)',
                      color: '#00d4ff',
                      fontWeight: 'bold'
                    }}
                  />
                </Box>
              ))}
            </Box>
          </Box>
        </Box>

        {/* Actions */}
        <Box sx={{ display: 'flex', gap: '15px', justifyContent: 'center', marginTop: '30px' }}>
          <Button
            variant="outlined"
            startIcon={<CloudDownloadIcon />}
            onClick={handleExportLogs}
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
            EXPORT LOGS
          </Button>

          <Button
            variant="outlined"
            onClick={() => setShowReporter(true)}
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
            REPORT ISSUE
          </Button>

          <Button
            variant="outlined"
            onClick={handleClearErrors}
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
            CLEAR LOGS
          </Button>

          <Button
            variant="outlined"
            onClick={onClose}
            className="jarvis-button"
            sx={{
              borderColor: '#ff3b30',
              color: '#ff3b30',
              '&:hover': {
                borderColor: '#ff3b30',
                backgroundColor: 'rgba(255, 59, 48, 0.1)'
              }
            }}
          >
            CLOSE
          </Button>
        </Box>

        {/* Dialog pour les détails d'erreur */}
        <Dialog
          open={!!selectedError}
          onClose={() => setSelectedError(null)}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: {
              backgroundColor: 'rgba(26, 26, 26, 0.95)',
              border: '1px solid rgba(0, 212, 255, 0.3)',
              backdropFilter: 'blur(10px)'
            }
          }}
        >
          <DialogTitle
            sx={{
              color: '#00d4ff',
              fontFamily: '"Orbitron", monospace',
              borderBottom: '1px solid rgba(0, 212, 255, 0.3)'
            }}
          >
            🔍 Error Details
          </DialogTitle>
          <DialogContent sx={{ marginTop: '20px' }}>
            {selectedError && (
              <Box>
                <Typography variant="h6" sx={{ color: '#ffffff', marginBottom: '10px' }}>
                  Component: {selectedError.component}
                </Typography>
                <Typography variant="body1" sx={{ color: '#cccccc', marginBottom: '15px' }}>
                  {selectedError.message}
                </Typography>
                <Box sx={{ marginBottom: '15px' }}>
                  <Chip
                    label={`Severity: ${selectedError.severity.toUpperCase()}`}
                    sx={{
                      backgroundColor: `${getSeverityColor(selectedError.severity)}20`,
                      color: getSeverityColor(selectedError.severity),
                      marginRight: '10px'
                    }}
                  />
                  <Chip
                    label={`Time: ${formatTimestamp(selectedError.timestamp)}`}
                    sx={{
                      backgroundColor: 'rgba(0, 212, 255, 0.2)',
                      color: '#00d4ff'
                    }}
                  />
                </Box>
                {selectedError.stack && (
                  <Box
                    sx={{
                      backgroundColor: 'rgba(0, 0, 0, 0.5)',
                      padding: '15px',
                      borderRadius: '5px',
                      marginTop: '15px'
                    }}
                  >
                    <Typography variant="subtitle2" sx={{ color: '#ff9500', marginBottom: '10px' }}>
                      Stack Trace:
                    </Typography>
                    <pre
                      style={{
                        color: '#ffffff',
                        fontSize: '0.8rem',
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap',
                        margin: 0,
                        maxHeight: '300px',
                        overflowY: 'auto'
                      }}
                    >
                      {selectedError.stack}
                    </pre>
                  </Box>
                )}
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setSelectedError(null)}
              className="jarvis-button"
              sx={{
                borderColor: '#00d4ff',
                color: '#00d4ff'
              }}
            >
              Close
            </Button>
          </DialogActions>
        </Dialog>

        {/* Error Reporter Dialog */}
        <ErrorReporter
          isVisible={showReporter}
          onClose={() => setShowReporter(false)}
          errorData={selectedError || {}}
        />
      </Box>
    </Box>
  );
};

export default ErrorMonitor;