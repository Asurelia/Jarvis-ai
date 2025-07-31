/**
 * 🎨 JARVIS Visualization Error Boundary - Gestion des erreurs graphiques 3D/Canvas
 * Error Boundary spécialisé pour les composants de visualisation et effets graphiques
 */
import React from 'react';
import { Box, Typography, Button, Alert, List, ListItem, ListItemText, Switch, FormControlLabel } from '@mui/material';
import { 
  ThreeDRotation as ThreeDRotationIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Memory as MemoryIcon
} from '@mui/icons-material';
import ErrorBoundary from './ErrorBoundary';
import '../styles/jarvis-holographic.css';

class VisualizationErrorBoundary extends ErrorBoundary {
  constructor(props) {
    super(props);
    this.state = {
      ...this.state,
      webglSupport: null,
      canvasSupport: null,
      gpuInfo: null,
      performanceMode: 'auto',
      reducedEffects: false,
      fallbackMode: false
    };
  }

  async componentDidMount() {
    await this.checkGraphicsCapabilities();
  }

  checkGraphicsCapabilities = async () => {
    const capabilities = {
      webgl: this.checkWebGLSupport(),
      webgl2: this.checkWebGL2Support(),
      canvas: this.checkCanvasSupport(),
      gpu: await this.getGPUInfo(),
      memory: this.checkMemoryInfo(),
      performance: this.checkPerformanceCapabilities()
    };

    this.setState({
      webglSupport: capabilities.webgl,
      canvasSupport: capabilities.canvas,
      gpuInfo: capabilities.gpu
    });

    // Déterminer le mode de performance automatiquement
    const performanceMode = this.determinePerformanceMode(capabilities);
    this.setState({ performanceMode });
  };

  checkWebGLSupport = () => {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      
      if (!gl) {
        return { supported: false, reason: 'Context not available' };
      }

      const info = {
        supported: true,
        version: gl.getParameter(gl.VERSION),
        vendor: gl.getParameter(gl.VENDOR),
        renderer: gl.getParameter(gl.RENDERER),
        maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
        maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
        extensions: gl.getSupportedExtensions()
      };

      // Nettoyage
      canvas.width = 1;
      canvas.height = 1;
      return info;
    } catch (error) {
      return { supported: false, reason: error.message };
    }
  };

  checkWebGL2Support = () => {
    try {
      const canvas = document.createElement('canvas');
      const gl2 = canvas.getContext('webgl2');
      
      canvas.width = 1;
      canvas.height = 1;
      
      return {
        supported: !!gl2,
        version: gl2 ? gl2.getParameter(gl2.VERSION) : null
      };
    } catch (error) {
      return { supported: false, reason: error.message };
    }
  };

  checkCanvasSupport = () => {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        return { supported: false, reason: 'Canvas 2D context not available' };
      }

      return {
        supported: true,
        imageSmoothingEnabled: ctx.imageSmoothingEnabled !== undefined,
        filters: 'filter' in ctx
      };
    } catch (error) {
      return { supported: false, reason: error.message };
    }
  };

  getGPUInfo = async () => {
    try {
      // Tentative d'obtenir les infos GPU via WebGL
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl');
      
      if (!gl) {
        return { available: false, reason: 'WebGL not available' };
      }

      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      const info = {
        available: true,
        vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'Unknown',
        renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'Unknown'
      };

      // Tentative d'obtenir plus d'infos via GPU API si disponible
      if ('gpu' in navigator) {
        try {
          const adapter = await navigator.gpu.requestAdapter();
          if (adapter) {
            info.webgpu = {
              supported: true,
              features: Array.from(adapter.features),
              limits: adapter.limits
            };
          }
        } catch (e) {
          info.webgpu = { supported: false, reason: e.message };
        }
      }

      canvas.width = 1;
      canvas.height = 1;
      return info;
    } catch (error) {
      return { available: false, reason: error.message };
    }
  };

  checkMemoryInfo = () => {
    const info = { available: false };
    
    try {
      // Informations de mémoire si disponibles
      if ('memory' in performance) {
        info.available = true;
        info.jsHeapSizeLimit = performance.memory.jsHeapSizeLimit;
        info.totalJSHeapSize = performance.memory.totalJSHeapSize;
        info.usedJSHeapSize = performance.memory.usedJSHeapSize;
      }

      // Informations sur le device si disponibles
      if ('deviceMemory' in navigator) {
        info.deviceMemory = navigator.deviceMemory;
      }

      if ('hardwareConcurrency' in navigator) {
        info.cpuCores = navigator.hardwareConcurrency;
      }
    } catch (error) {
      info.error = error.message;
    }

    return info;
  };

  checkPerformanceCapabilities = () => {
    try {
      const capabilities = {
        requestAnimationFrame: 'requestAnimationFrame' in window,
        intersectionObserver: 'IntersectionObserver' in window,
        resizeObserver: 'ResizeObserver' in window,
        offscreenCanvas: 'OffscreenCanvas' in window
      };

      return capabilities;
    } catch (error) {
      return { error: error.message };
    }
  };

  determinePerformanceMode = (capabilities) => {
    let score = 0;

    // WebGL support
    if (capabilities.webgl?.supported) score += 2;
    if (capabilities.webgl2?.supported) score += 1;

    // GPU info
    if (capabilities.gpu?.available) {
      const renderer = capabilities.gpu.renderer?.toLowerCase() || '';
      if (renderer.includes('nvidia') || renderer.includes('amd') || renderer.includes('intel iris')) {
        score += 2;
      } else if (renderer.includes('intel')) {
        score += 1;
      }
    }

    // Memory
    if (capabilities.memory?.deviceMemory >= 8) score += 2;
    else if (capabilities.memory?.deviceMemory >= 4) score += 1;

    // CPU
    if (capabilities.memory?.cpuCores >= 8) score += 1;

    // Déterminer le mode
    if (score >= 6) return 'high';
    if (score >= 4) return 'medium';
    if (score >= 2) return 'low';
    return 'fallback';
  };

  logError = (error, errorInfo) => {
    const visualErrorData = {
      ...this.createBaseErrorData(error, errorInfo),
      visualizationSpecific: {
        webglSupport: this.state.webglSupport,
        canvasSupport: this.state.canvasSupport,
        gpuInfo: this.state.gpuInfo,
        performanceMode: this.state.performanceMode,
        reducedEffects: this.state.reducedEffects,
        fallbackMode: this.state.fallbackMode,
        userAgent: navigator.userAgent,
        screen: {
          width: screen.width,
          height: screen.height,
          colorDepth: screen.colorDepth,
          pixelRatio: window.devicePixelRatio
        }
      }
    };

    console.error('🎨 JARVIS Visualization Error:', visualErrorData);

    if (window.jarvisAPI?.logVisualizationError) {
      window.jarvisAPI.logVisualizationError(visualErrorData);
    }

    if (this.props.onError) {
      this.props.onError(visualErrorData);
    }
  };

  handleFallbackMode = () => {
    this.setState({ 
      fallbackMode: true,
      reducedEffects: true,
      performanceMode: 'fallback'
    });
    
    // Notifier le parent du changement de mode
    if (this.props.onFallbackMode) {
      this.props.onFallbackMode(true);
    }
  };

  handleRetryWithSettings = () => {
    // Activer le mode performance réduite et retry
    this.setState({ 
      reducedEffects: true,
      performanceMode: 'low'
    });
    
    this.handleRetry();
  };

  toggleReducedEffects = () => {
    this.setState(prevState => ({
      reducedEffects: !prevState.reducedEffects
    }));

    if (this.props.onSettingsChange) {
      this.props.onSettingsChange({
        reducedEffects: !this.state.reducedEffects
      });
    }
  };

  render() {
    if (this.state.hasError) {
      const { webglSupport, canvasSupport, gpuInfo, performanceMode, reducedEffects, fallbackMode } = this.state;

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
            border: '2px solid #ff6b00',
            boxShadow: '0 0 30px rgba(255, 107, 0, 0.3)'
          }}
        >
          {/* Icône 3D avec rotation */}
          <Box
            sx={{
              fontSize: '4rem',
              color: '#ff6b00',
              textShadow: '0 0 20px #ff6b00',
              animation: 'error-pulse 2s ease-in-out infinite',
              marginBottom: '20px'
            }}
          >
            <ThreeDRotationIcon fontSize="inherit" />
          </Box>

          <Typography
            variant="h4"
            className="jarvis-text-glow"
            sx={{
              fontFamily: '"Orbitron", monospace',
              fontWeight: 'bold',
              color: '#ff6b00',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '20px'
            }}
          >
            GRAPHICS SYSTEM ERROR
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
            The JARVIS visualization engine has encountered a critical error. 
            3D graphics, holographic effects, and visual interfaces may be impacted.
          </Typography>

          {/* Diagnostics graphiques */}
          <Box
            sx={{
              width: '100%',
              maxWidth: '700px',
              marginBottom: '30px',
              textAlign: 'left'
            }}
          >
            <Typography
              variant="h6"
              sx={{
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '15px',
                textAlign: 'center'
              }}
            >
              🖥️ GRAPHICS DIAGNOSTICS
            </Typography>

            <List dense>
              <ListItem>
                <ListItemText
                  primary="WebGL Support"
                  secondary={webglSupport?.supported ? 
                    `✅ Supported - ${webglSupport.renderer}` : 
                    `❌ Not Supported - ${webglSupport?.reason}`}
                  sx={{
                    '& .MuiListItemText-primary': { 
                      color: '#ffffff', 
                      fontFamily: '"Orbitron", monospace' 
                    },
                    '& .MuiListItemText-secondary': { 
                      color: webglSupport?.supported ? '#00ff88' : '#ff3b30',
                      fontSize: '0.8rem'
                    }
                  }}
                />
              </ListItem>

              <ListItem>
                <ListItemText
                  primary="Canvas 2D Support"
                  secondary={canvasSupport?.supported ? 
                    '✅ Supported' : 
                    `❌ Not Supported - ${canvasSupport?.reason}`}
                  sx={{
                    '& .MuiListItemText-primary': { 
                      color: '#ffffff', 
                      fontFamily: '"Orbitron", monospace' 
                    },
                    '& .MuiListItemText-secondary': { 
                      color: canvasSupport?.supported ? '#00ff88' : '#ff3b30',
                      fontSize: '0.8rem'
                    }
                  }}
                />
              </ListItem>

              <ListItem>
                <ListItemText
                  primary="GPU Information"
                  secondary={gpuInfo?.available ? 
                    `${gpuInfo.vendor} - ${gpuInfo.renderer}` : 
                    `❌ Not Available - ${gpuInfo?.reason}`}
                  sx={{
                    '& .MuiListItemText-primary': { 
                      color: '#ffffff', 
                      fontFamily: '"Orbitron", monospace' 
                    },
                    '& .MuiListItemText-secondary': { 
                      color: gpuInfo?.available ? '#00ff88' : '#ff9500',
                      fontSize: '0.8rem'
                    }
                  }}
                />
              </ListItem>

              <ListItem>
                <ListItemText
                  primary="Performance Mode"
                  secondary={`Current: ${performanceMode.toUpperCase()}`}
                  sx={{
                    '& .MuiListItemText-primary': { 
                      color: '#ffffff', 
                      fontFamily: '"Orbitron", monospace' 
                    },
                    '& .MuiListItemText-secondary': { 
                      color: performanceMode === 'high' ? '#00ff88' : 
                             performanceMode === 'medium' ? '#00d4ff' :
                             performanceMode === 'low' ? '#ff9500' : '#ff3b30',
                      fontSize: '0.8rem'
                    }
                  }}
                />
              </ListItem>
            </List>
          </Box>

          {/* Options de performance */}
          <Box
            sx={{
              width: '100%',
              maxWidth: '500px',
              marginBottom: '30px',
              padding: '20px',
              border: '1px solid rgba(0, 212, 255, 0.3)',
              borderRadius: '10px',
              backgroundColor: 'rgba(0, 212, 255, 0.05)'
            }}
          >
            <Typography
              variant="h6"
              sx={{
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace',
                marginBottom: '15px',
                textAlign: 'center'
              }}
            >
              ⚙️ PERFORMANCE SETTINGS
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={reducedEffects}
                  onChange={this.toggleReducedEffects}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': {
                      color: '#00ff88'
                    },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                      backgroundColor: '#00ff88'
                    }
                  }}
                />
              }
              label="Reduced Visual Effects"
              sx={{
                color: '#ffffff',
                fontFamily: '"Orbitron", monospace',
                width: '100%',
                justifyContent: 'space-between',
                marginLeft: 0,
                '& .MuiFormControlLabel-label': {
                  fontSize: '0.9rem'
                }
              }}
            />

            <Typography
              variant="body2"
              sx={{
                color: '#999999',
                fontSize: '0.8rem',
                marginTop: '10px',
                textAlign: 'center'
              }}
            >
              Disable intensive visual effects to improve compatibility
            </Typography>
          </Box>

          {/* Boutons d'action spécialisés */}
          <Box sx={{ display: 'flex', gap: '15px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={this.handleRetryWithSettings}
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
              RETRY WITH LOW SETTINGS
            </Button>

            <Button
              variant="outlined"
              startIcon={fallbackMode ? <VisibilityOffIcon /> : <VisibilityIcon />}
              onClick={this.handleFallbackMode}
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
              {fallbackMode ? 'VISUAL MODE ACTIVE' : 'ENABLE FALLBACK MODE'}
            </Button>

            <Button
              variant="outlined"
              startIcon={<MemoryIcon />}
              onClick={() => window.location.reload()}
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
              CLEAR GRAPHICS CACHE
            </Button>
          </Box>

          {/* Recommandations */}
          <Alert
            severity="info"
            sx={{
              marginTop: '30px',
              backgroundColor: 'rgba(0, 212, 255, 0.1)',
              border: '1px solid rgba(0, 212, 255, 0.3)',
              color: '#00d4ff',
              fontFamily: '"Orbitron", monospace',
              '& .MuiAlert-icon': {
                color: '#00d4ff'
              }
            }}
          >
            <Typography variant="body2" sx={{ fontWeight: 'bold', marginBottom: '10px' }}>
              COMPATIBILITY RECOMMENDATIONS:
            </Typography>
            <Typography variant="body2" component="div">
              • Update your graphics drivers<br/>
              • Enable hardware acceleration in browser<br/>
              • Close other graphics-intensive applications<br/>
              • Use Chrome or Firefox for best WebGL support
            </Typography>
          </Alert>

          {/* Mode fallback activé */}
          {fallbackMode && (
            <Alert
              severity="success"
              sx={{
                marginTop: '15px',
                backgroundColor: 'rgba(0, 255, 136, 0.1)',
                border: '1px solid rgba(0, 255, 136, 0.3)',
                color: '#00ff88',
                fontFamily: '"Orbitron", monospace',
                '& .MuiAlert-icon': {
                  color: '#00ff88'
                }
              }}
            >
              FALLBACK MODE ACTIVATED - JARVIS interface will use simplified 2D graphics
            </Alert>
          )}
        </Box>
      );
    }

    return this.props.children;
  }
}

export default VisualizationErrorBoundary;