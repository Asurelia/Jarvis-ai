/**
 * 📊 JARVIS Error Reporter - Système de reporting d'erreurs
 * Composant pour collecter et envoyer les rapports d'erreurs
 */
import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  TextField, 
  Accordion, 
  AccordionSummary, 
  AccordionDetails,
  Chip,
  Alert,
  Snackbar
} from '@mui/material';
import { 
  ExpandMore as ExpandMoreIcon,
  Send as SendIcon,
  BugReport as BugReportIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import '../styles/jarvis-holographic.css';

const ErrorReporter = ({ 
  errorData = {}, 
  onSubmit = () => {}, 
  onClose = () => {},
  isVisible = false 
}) => {
  const [userDescription, setUserDescription] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [includeSystemInfo, setIncludeSystemInfo] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null);

  // Extraire les informations système
  const systemInfo = {
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    cookieEnabled: navigator.cookieEnabled,
    onLine: navigator.onLine,
    screen: {
      width: window.screen.width,
      height: window.screen.height,
      colorDepth: window.screen.colorDepth,
      pixelRatio: window.devicePixelRatio
    },
    memory: navigator.deviceMemory || 'unknown',
    cores: navigator.hardwareConcurrency || 'unknown',
    connection: navigator.connection ? {
      effectiveType: navigator.connection.effectiveType,
      downlink: navigator.connection.downlink,
      rtt: navigator.connection.rtt
    } : 'unknown'
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const reportData = {
        errorData,
        userDescription,
        userEmail: userEmail || 'anonymous',
        systemInfo: includeSystemInfo ? systemInfo : null,
        reportId: `report_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        submittedAt: new Date().toISOString()
      };

      // Log du rapport
      console.log('📊 Error Report Submitted:', reportData);

      // Envoyer via API JARVIS si disponible
      if (window.jarvisAPI?.submitErrorReport) {
        await window.jarvisAPI.submitErrorReport(reportData);
      }

      // Callback personnalisé
      if (onSubmit) {
        await onSubmit(reportData);
      }

      setSubmitStatus({ type: 'success', message: 'Error report submitted successfully!' });
      
      // Auto-fermeture après 3 secondes
      setTimeout(() => {
        onClose();
      }, 3000);

    } catch (error) {
      console.error('Failed to submit error report:', error);
      setSubmitStatus({ type: 'error', message: 'Failed to submit report. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatErrorData = (data) => {
    return JSON.stringify(data, null, 2);
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#ff3b30';
      case 'high': return '#ff9500';
      case 'medium': return '#00d4ff';
      case 'low': return '#00ff88';
      default: return '#ffffff';
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
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        padding: '20px'
      }}
    >
      <Box
        className="jarvis-panel"
        sx={{
          maxWidth: '800px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '30px',
          border: '2px solid #00d4ff',
          boxShadow: '0 0 30px rgba(0, 212, 255, 0.3)'
        }}
      >
        {/* Header */}
        <Box sx={{ textAlign: 'center', marginBottom: '30px' }}>
          <BugReportIcon
            sx={{
              fontSize: '3rem',
              color: '#00d4ff',
              textShadow: '0 0 15px #00d4ff',
              marginBottom: '15px'
            }}
          />
          
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
            ERROR REPORT SYSTEM
          </Typography>
          
          <Typography
            variant="body1"
            sx={{
              fontFamily: '"Orbitron", monospace',
              color: '#ffffff',
              opacity: 0.8
            }}
          >
            Help improve JARVIS by reporting this error
          </Typography>
        </Box>

        {/* Formulaire */}
        <form onSubmit={handleSubmit}>
          {/* Informations d'erreur */}
          {errorData.error && (
            <Box sx={{ marginBottom: '25px' }}>
              <Typography
                variant="h6"
                sx={{
                  color: '#ff9500',
                  fontFamily: '"Orbitron", monospace',
                  marginBottom: '15px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}
              >
                <InfoIcon /> Error Summary
              </Typography>
              
              <Box sx={{ display: 'flex', gap: '10px', marginBottom: '15px', flexWrap: 'wrap' }}>
                <Chip
                  label={`Type: ${errorData.error.name || 'Unknown'}`}
                  sx={{
                    backgroundColor: 'rgba(255, 149, 0, 0.2)',
                    color: '#ff9500',
                    fontFamily: '"Orbitron", monospace',
                    fontSize: '0.8rem'
                  }}
                />
                
                {errorData.component && (
                  <Chip
                    label={`Component: ${errorData.component}`}
                    sx={{
                      backgroundColor: 'rgba(0, 212, 255, 0.2)',
                      color: '#00d4ff',
                      fontFamily: '"Orbitron", monospace',
                      fontSize: '0.8rem'
                    }}
                  />
                )}
                
                {errorData.severity && (
                  <Chip
                    label={`Severity: ${errorData.severity.toUpperCase()}`}
                    sx={{
                      backgroundColor: `${getSeverityColor(errorData.severity)}20`,
                      color: getSeverityColor(errorData.severity),
                      fontFamily: '"Orbitron", monospace',
                      fontSize: '0.8rem'
                    }}
                  />
                )}
              </Box>
              
              <Typography
                variant="body2"
                sx={{
                  color: '#ffffff',
                  backgroundColor: 'rgba(255, 149, 0, 0.1)',
                  padding: '10px',
                  borderRadius: '5px',
                  border: '1px solid rgba(255, 149, 0, 0.3)',
                  fontFamily: 'monospace'
                }}
              >
                {errorData.error.message}
              </Typography>
            </Box>
          )}

          {/* Description utilisateur */}
          <Box sx={{ marginBottom: '25px' }}>
            <Typography
              variant="h6"
              sx={{
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '10px'
              }}
            >
              What were you doing when this error occurred?
            </Typography>
            
            <TextField
              multiline
              rows={4}
              fullWidth
              value={userDescription}
              onChange={(e) => setUserDescription(e.target.value)}
              placeholder="Please describe the steps that led to this error..."
              className="jarvis-input"
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: 'rgba(0, 212, 255, 0.05)',
                  border: '1px solid rgba(0, 212, 255, 0.3)',
                  color: '#ffffff',
                  fontFamily: '"Orbitron", monospace',
                  '&:hover': {
                    borderColor: 'rgba(0, 212, 255, 0.5)'
                  },
                  '&.Mui-focused': {
                    borderColor: '#00d4ff',
                    boxShadow: '0 0 10px rgba(0, 212, 255, 0.3)'
                  }
                },
                '& .MuiOutlinedInput-input': {
                  color: '#ffffff'
                },
                '& .MuiInputLabel-root': {
                  color: 'rgba(0, 212, 255, 0.7)'
                }
              }}
            />
          </Box>

          {/* Email optionnel */}
          <Box sx={{ marginBottom: '25px' }}>
            <Typography
              variant="h6"
              sx={{
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '10px'
              }}
            >
              Contact Email (Optional)
            </Typography>
            
            <TextField
              type="email"
              fullWidth
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
              placeholder="your-email@example.com"
              className="jarvis-input"
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: 'rgba(0, 212, 255, 0.05)',
                  border: '1px solid rgba(0, 212, 255, 0.3)',
                  color: '#ffffff',
                  fontFamily: '"Orbitron", monospace',
                  '&:hover': {
                    borderColor: 'rgba(0, 212, 255, 0.5)'
                  },
                  '&.Mui-focused': {
                    borderColor: '#00d4ff',
                    boxShadow: '0 0 10px rgba(0, 212, 255, 0.3)'
                  }
                },
                '& .MuiOutlinedInput-input': {
                  color: '#ffffff'
                }
              }}
            />
            
            <Typography
              variant="body2"
              sx={{
                color: '#999999',
                marginTop: '5px',
                fontSize: '0.8rem'
              }}
            >
              We'll only contact you if we need more information about this error
            </Typography>
          </Box>

          {/* Détails techniques (collapsible) */}
          <Accordion
            sx={{
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(0, 212, 255, 0.3)',
              marginBottom: '25px',
              '&:before': {
                display: 'none'
              }
            }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon sx={{ color: '#00d4ff' }} />}
              sx={{
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace'
              }}
            >
              <Typography variant="body2">
                📋 Technical Details (Click to expand)
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box
                sx={{
                  maxHeight: '300px',
                  overflowY: 'auto',
                  backgroundColor: 'rgba(0, 0, 0, 0.5)',
                  padding: '15px',
                  borderRadius: '5px'
                }}
              >
                <pre
                  style={{
                    color: '#ffffff',
                    fontSize: '0.75rem',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                    margin: 0
                  }}
                >
                  {formatErrorData({ errorData, systemInfo })}
                </pre>
              </Box>
            </AccordionDetails>
          </Accordion>

          {/* Boutons d'action */}
          <Box sx={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
            <Button
              type="submit"
              variant="outlined"
              startIcon={<SendIcon />}
              disabled={isSubmitting}
              className="jarvis-button"
              sx={{
                borderColor: '#00ff88',
                color: '#00ff88',
                minWidth: '150px',
                '&:hover': {
                  borderColor: '#00ff88',
                  backgroundColor: 'rgba(0, 255, 136, 0.1)'
                },
                '&:disabled': {
                  borderColor: '#666666',
                  color: '#666666'
                }
              }}
            >
              {isSubmitting ? 'SENDING...' : 'SEND REPORT'}
            </Button>

            <Button
              variant="outlined"
              onClick={onClose}
              disabled={isSubmitting}
              className="jarvis-button"
              sx={{
                borderColor: '#ff9500',
                color: '#ff9500',
                minWidth: '150px',
                '&:hover': {
                  borderColor: '#ff9500',
                  backgroundColor: 'rgba(255, 149, 0, 0.1)'
                }
              }}
            >
              CANCEL
            </Button>
          </Box>
        </form>

        {/* Snackbar pour le statut */}
        <Snackbar
          open={!!submitStatus}
          autoHideDuration={6000}
          onClose={() => setSubmitStatus(null)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert
            onClose={() => setSubmitStatus(null)}
            severity={submitStatus?.type || 'info'}
            sx={{
              backgroundColor: submitStatus?.type === 'success' ? 
                'rgba(0, 255, 136, 0.1)' : 'rgba(255, 59, 48, 0.1)',
              border: `1px solid ${submitStatus?.type === 'success' ? 
                'rgba(0, 255, 136, 0.3)' : 'rgba(255, 59, 48, 0.3)'}`,
              color: submitStatus?.type === 'success' ? '#00ff88' : '#ff3b30',
              fontFamily: '"Orbitron", monospace'
            }}
          >
            {submitStatus?.message}
          </Alert>
        </Snackbar>
      </Box>
    </Box>
  );
};

export default ErrorReporter;