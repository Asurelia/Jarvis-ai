/**
 * 🧪 JARVIS Error Boundary Tester - Composant de test pour les Error Boundaries
 * Permet de simuler différents types d'erreurs pour tester la robustesse
 */
import React, { useState } from 'react';
import { Box, Typography, Button, Select, MenuItem, FormControl, InputLabel, Alert } from '@mui/material';
import { BugReport as BugReportIcon } from '@mui/icons-material';
import '../styles/jarvis-holographic.css';

// Composants de test qui peuvent générer des erreurs
const CrashingComponent = ({ errorType, delay = 0 }) => {
  const [shouldCrash, setShouldCrash] = useState(false);

  React.useEffect(() => {
    if (delay > 0) {
      const timer = setTimeout(() => setShouldCrash(true), delay);
      return () => clearTimeout(timer);
    }
  }, [delay]);

  if (shouldCrash || delay === 0) {
    switch (errorType) {
      case 'javascript':
        throw new Error('Simulated JavaScript error for testing Error Boundary');
      
      case 'async':
        Promise.reject(new Error('Simulated async error')).catch(() => {
          throw new Error('Unhandled promise rejection');
        });
        break;
      
      case 'component':
        const invalidObject = null;
        return <div>{invalidObject.someProperty}</div>; // Will throw TypeError
      
      case 'render':
        return (
          <div>
            {(() => {
              throw new Error('Error during render phase');
            })()}
          </div>
        );
      
      case 'network':
        fetch('https://invalid-url-that-will-fail.com')
          .catch(() => {
            throw new Error('Network request failed');
          });
        break;
      
      case 'audio':
        // Simuler erreur audio
        const audio = new Audio('invalid-audio-file.mp3');
        audio.play().catch(() => {
          throw new Error('Audio playback failed - no permissions or invalid source');
        });
        break;
      
      case 'visualization':
        // Simuler erreur WebGL/Canvas
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl');
        if (!gl) {
          throw new Error('WebGL not supported - visualization error');
        }
        // Forcer une erreur WebGL
        gl.createShader('invalid-shader-type');
        break;
      
      case 'memory':
        // Simuler erreur de mémoire
        const bigArray = new Array(999999999).fill('memory-test');
        return <div>{bigArray.length}</div>;
      
      default:
        throw new Error('Unknown error type for testing');
    }
  }

  return (
    <Box
      className="jarvis-panel"
      sx={{
        padding: '20px',
        textAlign: 'center',
        border: '1px solid #00ff88',
        boxShadow: '0 0 15px rgba(0, 255, 136, 0.3)'
      }}
    >
      <Typography
        variant="h6"
        sx={{
          color: '#00ff88',
          fontFamily: '"Orbitron", monospace',
          marginBottom: '10px'
        }}
      >
        ✅ Test Component Active
      </Typography>
      <Typography
        variant="body2"
        sx={{ color: '#ffffff' }}
      >
        Component is running normally. Ready to simulate {errorType} error.
      </Typography>
      {delay > 0 && (
        <Typography
          variant="body2"
          sx={{ color: '#ff9500', marginTop: '10px' }}
        >
          Error will trigger in {Math.ceil(delay / 1000)} seconds...
        </Typography>
      )}
    </Box>
  );
};

const ErrorBoundaryTester = ({ isVisible = false, onClose = () => {} }) => {
  const [selectedErrorType, setSelectedErrorType] = useState('javascript');
  const [testComponent, setTestComponent] = useState(null);
  const [delay, setDelay] = useState(0);

  const errorTypes = [
    { value: 'javascript', label: 'JavaScript Error', description: 'Basic JS exception' },
    { value: 'component', label: 'Component Error', description: 'React component crash' },
    { value: 'render', label: 'Render Error', description: 'Error during render phase' },
    { value: 'async', label: 'Async Error', description: 'Unhandled promise rejection' },
    { value: 'network', label: 'Network Error', description: 'API/fetch failure' },
    { value: 'audio', label: 'Audio Error', description: 'Audio system failure' },
    { value: 'visualization', label: 'WebGL Error', description: 'Graphics/3D error' },
    { value: 'memory', label: 'Memory Error', description: 'Out of memory condition' }
  ];

  const delayOptions = [
    { value: 0, label: 'Immediate' },
    { value: 2000, label: '2 seconds' },
    { value: 5000, label: '5 seconds' },
    { value: 10000, label: '10 seconds' }
  ];

  const handleTriggerError = () => {
    const key = `test-${Date.now()}`;
    setTestComponent(
      <CrashingComponent 
        key={key}
        errorType={selectedErrorType} 
        delay={delay}
      />
    );
  };

  const handleResetTest = () => {
    setTestComponent(null);
  };

  const handleGlobalError = () => {
    // Déclencher une erreur globale (non capturée par Error Boundary React)
    setTimeout(() => {
      throw new Error('Global error not caught by React Error Boundary');
    }, 100);
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
          width: '90%',
          maxWidth: '800px',
          maxHeight: '80vh',
          overflowY: 'auto',
          padding: '30px',
          border: '2px solid #ff9500',
          boxShadow: '0 0 30px rgba(255, 149, 0, 0.3)'
        }}
      >
        {/* Header */}
        <Box sx={{ textAlign: 'center', marginBottom: '30px' }}>
          <BugReportIcon
            sx={{
              fontSize: '3rem',
              color: '#ff9500',
              textShadow: '0 0 15px #ff9500',
              marginBottom: '15px'
            }}
          />
          
          <Typography
            variant="h4"
            className="jarvis-text-glow"
            sx={{
              fontFamily: '"Orbitron", monospace',
              fontWeight: 'bold',
              color: '#ff9500',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '10px'
            }}
          >
            🧪 ERROR BOUNDARY TESTER
          </Typography>
          
          <Typography
            variant="body1"
            sx={{
              fontFamily: '"Orbitron", monospace',
              color: '#ffffff',
              opacity: 0.8
            }}
          >
            Test the robustness of JARVIS Error Boundaries by simulating various error conditions
          </Typography>
        </Box>

        {/* Configuration */}
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
          <FormControl fullWidth>
            <InputLabel 
              sx={{ 
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace'
              }}
            >
              Error Type
            </InputLabel>
            <Select
              value={selectedErrorType}
              onChange={(e) => setSelectedErrorType(e.target.value)}
              sx={{
                color: '#ffffff',
                fontFamily: '"Orbitron", monospace',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#00d4ff'
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#00ff88'
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#00ff88'
                }
              }}
            >
              {errorTypes.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  <Box>
                    <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                      {type.label}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#cccccc', fontSize: '0.8rem' }}>
                      {type.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel 
              sx={{ 
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace'
              }}
            >
              Trigger Delay
            </InputLabel>
            <Select
              value={delay}
              onChange={(e) => setDelay(e.target.value)}
              sx={{
                color: '#ffffff',
                fontFamily: '"Orbitron", monospace',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#00d4ff'
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#00ff88'
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#00ff88'
                }
              }}
            >
              {delayOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {/* Description de l'erreur sélectionnée */}
        <Alert
          severity="info"
          sx={{
            backgroundColor: 'rgba(0, 212, 255, 0.1)',
            border: '1px solid rgba(0, 212, 255, 0.3)',
            color: '#00d4ff',
            fontFamily: '"Orbitron", monospace',
            marginBottom: '30px',
            '& .MuiAlert-icon': {
              color: '#00d4ff'
            }
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold', marginBottom: '5px' }}>
            Test Description:
          </Typography>
          <Typography variant="body2">
            {errorTypes.find(type => type.value === selectedErrorType)?.description}
            {delay > 0 && ` - Will trigger after ${delay / 1000} seconds`}
          </Typography>
        </Alert>

        {/* Zone de test */}
        <Box
          sx={{
            minHeight: '200px',
            marginBottom: '30px',
            border: '2px dashed rgba(255, 149, 0, 0.3)',
            borderRadius: '10px',
            padding: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {testComponent || (
            <Typography
              variant="h6"
              sx={{
                color: '#999999',
                fontFamily: '"Orbitron", monospace',
                textAlign: 'center'
              }}
            >
              🎯 Test Area<br/>
              <Typography variant="body2" sx={{ marginTop: '10px' }}>
                Click "Trigger Error" to start the test
              </Typography>
            </Typography>
          )}
        </Box>

        {/* Boutons de contrôle */}
        <Box sx={{ display: 'flex', gap: '15px', justifyContent: 'center', marginBottom: '20px' }}>
          <Button
            variant="outlined"
            onClick={handleTriggerError}
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
            🚨 TRIGGER ERROR
          </Button>

          <Button
            variant="outlined"
            onClick={handleResetTest}
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
            🔄 RESET TEST
          </Button>

          <Button
            variant="outlined"
            onClick={handleGlobalError}
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
            💥 GLOBAL ERROR
          </Button>

          <Button
            variant="outlined"
            onClick={onClose}
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
            CLOSE
          </Button>
        </Box>

        {/* Instructions */}
        <Alert
          severity="warning"
          sx={{
            backgroundColor: 'rgba(255, 149, 0, 0.1)',
            border: '1px solid rgba(255, 149, 0, 0.3)',
            color: '#ff9500',
            fontFamily: '"Orbitron", monospace',
            '& .MuiAlert-icon': {
              color: '#ff9500'
            }
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold', marginBottom: '10px' }}>
            Testing Instructions:
          </Typography>
          <Typography variant="body2" component="div">
            • Select an error type and optional delay<br/>
            • Click "Trigger Error" to test the Error Boundary<br/>
            • Observe how the interface handles the error gracefully<br/>
            • Check the Error Monitor for logged error details<br/>
            • Use "Global Error" to test errors outside React boundaries
          </Typography>
        </Alert>
      </Box>
    </Box>
  );
};

export default ErrorBoundaryTester;