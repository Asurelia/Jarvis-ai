/**
 * 🌊 JARVIS Scanline Effect - Effets de scan holographiques style Iron Man
 * Composant pour contrôler les effets de scanlines animées
 */
import React, { useState, useEffect, useRef } from 'react';

// Configuration par défaut des scanlines
const DEFAULT_CONFIG = {
  enabled: true,
  intensity: 'normal', // 'low', 'normal', 'high', 'intense'
  speed: 'normal', // 'slow', 'normal', 'fast'
  colors: {
    primary: 'rgba(0, 212, 255, 0.8)',
    secondary: 'rgba(0, 255, 136, 0.6)',
    accent: 'rgba(255, 107, 0, 0.4)'
  },
  effects: {
    horizontal: true,
    vertical: true,
    diagonal: false,
    radar: false,
    glitch: false
  },
  count: {
    horizontal: 3,
    vertical: 2,
    diagonal: 1
  }
};

// Composant individuel de scanline
const Scanline = ({ type, className, style, children }) => {
  const baseClass = `jarvis-scanline-${type}`;
  const fullClassName = className ? `${baseClass} ${className}` : baseClass;
  
  return (
    <div className={fullClassName} style={style}>
      {children}
    </div>
  );
};

// Composant radar circulaire
const RadarSweep = ({ enabled, size = 200, position = { top: '50%', left: '50%' } }) => {
  if (!enabled) return null;
  
  return (
    <div 
      className="jarvis-radar-sweep"
      style={{
        width: `${size}px`,
        height: `${size}px`,
        top: position.top,
        left: position.left
      }}
    />
  );
};

// Hook pour générer les scanlines dynamiquement
const useScanlines = (config) => {
  const [scanlines, setScanlines] = useState([]);
  
  useEffect(() => {
    if (!config.enabled) {
      setScanlines([]);
      return;
    }
    
    const newScanlines = [];
    let id = 0;
    
    // Scanlines horizontales
    if (config.effects.horizontal) {
      for (let i = 0; i < config.count.horizontal; i++) {
        const delay = i * (1000 / config.count.horizontal);
        const className = i === 0 ? '' : i % 2 === 1 ? 'fast' : 'slow';
        
        newScanlines.push({
          id: id++,
          type: 'horizontal',
          className,
          style: {
            animationDelay: `${delay}ms`
          }
        });
      }
    }
    
    // Scanlines verticales
    if (config.effects.vertical) {
      for (let i = 0; i < config.count.vertical; i++) {
        const delay = i * (1500 / config.count.vertical);
        const className = i === 0 ? '' : i % 2 === 1 ? 'fast' : 'slow';
        
        newScanlines.push({
          id: id++,
          type: 'vertical',
          className,
          style: {
            animationDelay: `${delay}ms`
          }
        });
      }
    }
    
    // Scanlines diagonales
    if (config.effects.diagonal) {
      for (let i = 0; i < config.count.diagonal; i++) {
        newScanlines.push({
          id: id++,
          type: 'diagonal',
          className: '',
          style: {
            animationDelay: `${i * 2000}ms`
          }
        });
      }
    }
    
    setScanlines(newScanlines);
  }, [config]);
  
  return scanlines;
};

// Composant principal ScanlineEffect
const ScanlineEffect = ({ 
  config = DEFAULT_CONFIG, 
  onConfigChange,
  showControls = false,
  children 
}) => {
  const [currentConfig, setCurrentConfig] = useState({ ...DEFAULT_CONFIG, ...config });
  const containerRef = useRef(null);
  const scanlines = useScanlines(currentConfig);
  
  // Mise à jour de la configuration
  const updateConfig = (newConfig) => {
    const updatedConfig = { ...currentConfig, ...newConfig };
    setCurrentConfig(updatedConfig);
    onConfigChange?.(updatedConfig);
  };
  
  // Toggle activation des scanlines
  const toggleEnabled = () => {
    updateConfig({ enabled: !currentConfig.enabled });
  };
  
  // Changer l'intensité
  const setIntensity = (intensity) => {
    updateConfig({ intensity });
  };
  
  // Changer la vitesse
  const setSpeed = (speed) => {
    updateConfig({ speed });
  };
  
  // Toggle effets spéciaux
  const toggleEffect = (effectName) => {
    updateConfig({
      effects: {
        ...currentConfig.effects,
        [effectName]: !currentConfig.effects[effectName]
      }
    });
  };
  
  // Générer les classes CSS du container
  const getContainerClasses = () => {
    const classes = ['jarvis-scanlines-container'];
    
    if (!currentConfig.enabled) classes.push('disabled');
    if (currentConfig.intensity === 'intense') classes.push('intense');
    if (currentConfig.effects.glitch) classes.push('glitch');
    if (currentConfig.speed === 'slow') classes.push('reduced-motion');
    
    return classes.join(' ');
  };
  
  // Contrôles de configuration (optionnels)
  const renderControls = () => {
    if (!showControls) return null;
    
    return (
      <div className="jarvis-panel" style={{ 
        position: 'fixed', 
        top: '20px', 
        right: '20px', 
        width: '250px',
        zIndex: 10000 
      }}>
        <h3 className="jarvis-text-glow" style={{ fontSize: '1rem', marginBottom: '15px' }}>
          SCANLINE CONTROLS
        </h3>
        
        {/* Toggle principal */}
        <div style={{ marginBottom: '15px' }}>
          <button 
            className={`jarvis-button ${currentConfig.enabled ? 'active' : ''}`}
            onClick={toggleEnabled}
            style={{ width: '100%', fontSize: '0.8rem' }}
          >
            {currentConfig.enabled ? 'DISABLE' : 'ENABLE'} SCANLINES
          </button>
        </div>
        
        {/* Contrôles d'intensité */}
        <div style={{ marginBottom: '15px' }}>
          <div className="jarvis-text-glow" style={{ fontSize: '0.8rem', marginBottom: '8px' }}>
            INTENSITY
          </div>
          <div style={{ display: 'flex', gap: '5px' }}>
            {['low', 'normal', 'high', 'intense'].map(intensity => (
              <button
                key={intensity}
                className={`jarvis-button ${currentConfig.intensity === intensity ? 'active' : ''}`}
                onClick={() => setIntensity(intensity)}
                style={{ flex: 1, fontSize: '0.7rem', padding: '5px' }}
              >
                {intensity.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        
        {/* Contrôles de vitesse */}
        <div style={{ marginBottom: '15px' }}>
          <div className="jarvis-text-glow" style={{ fontSize: '0.8rem', marginBottom: '8px' }}>
            SPEED
          </div>
          <div style={{ display: 'flex', gap: '5px' }}>
            {['slow', 'normal', 'fast'].map(speed => (
              <button
                key={speed}
                className={`jarvis-button ${currentConfig.speed === speed ? 'active' : ''}`}
                onClick={() => setSpeed(speed)}
                style={{ flex: 1, fontSize: '0.7rem', padding: '5px' }}
              >
                {speed.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        
        {/* Toggle effets */}
        <div>
          <div className="jarvis-text-glow" style={{ fontSize: '0.8rem', marginBottom: '8px' }}>
            EFFECTS
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {Object.entries(currentConfig.effects).map(([effect, enabled]) => (
              <button
                key={effect}
                className={`jarvis-button ${enabled ? 'active' : ''}`}
                onClick={() => toggleEffect(effect)}
                style={{ fontSize: '0.7rem', padding: '5px' }}
              >
                {effect.toUpperCase()}: {enabled ? 'ON' : 'OFF'}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <>
      {/* Container principal des scanlines */}
      <div ref={containerRef} className={getContainerClasses()}>
        {/* Rendu des scanlines dynamiques */}
        {scanlines.map(scanline => (
          <Scanline
            key={scanline.id}
            type={scanline.type}
            className={scanline.className}
            style={scanline.style}
          />
        ))}
        
        {/* Radar sweep si activé */}
        <RadarSweep enabled={currentConfig.effects.radar} />
      </div>
      
      {/* Contrôles de configuration */}
      {renderControls()}
      
      {/* Contenu enfant */}
      {children}
    </>
  );
};

// Hook personnalisé pour utiliser les scanlines facilement
export const useScanlineConfig = (initialConfig = {}) => {
  const [config, setConfig] = useState({ ...DEFAULT_CONFIG, ...initialConfig });
  
  const updateConfig = (newConfig) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  };
  
  const presets = {
    minimal: {
      intensity: 'low',
      effects: { horizontal: true, vertical: false, diagonal: false, radar: false, glitch: false },
      count: { horizontal: 1, vertical: 0, diagonal: 0 }
    },
    standard: {
      intensity: 'normal',
      effects: { horizontal: true, vertical: true, diagonal: false, radar: false, glitch: false },
      count: { horizontal: 2, vertical: 1, diagonal: 0 }
    },
    intense: {
      intensity: 'intense',
      effects: { horizontal: true, vertical: true, diagonal: true, radar: true, glitch: true },
      count: { horizontal: 4, vertical: 3, diagonal: 2 }
    },
    ironman: {
      intensity: 'high',
      effects: { horizontal: true, vertical: true, diagonal: false, radar: true, glitch: false },
      count: { horizontal: 3, vertical: 2, diagonal: 0 }
    }
  };
  
  const applyPreset = (presetName) => {
    if (presets[presetName]) {
      updateConfig(presets[presetName]);
    }
  };
  
  return {
    config,
    updateConfig,
    presets,
    applyPreset
  };
};

export default ScanlineEffect;