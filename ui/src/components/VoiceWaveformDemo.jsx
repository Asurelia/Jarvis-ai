/**
 * 🎵 Voice Waveform Demo - Démonstration complète des composants
 * Showcase de tous les styles et configurations de visualisation audio
 */
import React, { useState } from 'react';
import VoiceWaveform from './VoiceWaveform';
import VoiceWaveformAdvanced from './VoiceWaveformAdvanced';
import JarvisInterface from './JarvisInterface';

const VoiceWaveformDemo = () => {
  const [selectedStyle, setSelectedStyle] = useState('bars');
  const [selectedSize, setSelectedSize] = useState('medium');
  const [selectedTheme, setSelectedTheme] = useState('blue');
  
  // Configurations de taille
  const sizeConfigs = {
    small: { width: 300, height: 120 },
    medium: { width: 500, height: 200 },
    large: { width: 700, height: 280 }
  };
  
  // Configurations de thème
  const themeConfigs = {
    blue: {
      primary: '#00d4ff',
      secondary: '#0099cc',
      accent: '#66e5ff'
    },
    green: {
      primary: '#00ff88',
      secondary: '#00cc66',
      accent: '#66ffaa'
    },
    orange: {
      primary: '#ff6b00',
      secondary: '#cc5500',
      accent: '#ff9944'
    },
    purple: {
      primary: '#aa44ff',
      secondary: '#8833cc',
      accent: '#cc66ff'
    }
  };
  
  const currentSize = sizeConfigs[selectedSize];
  const currentTheme = themeConfigs[selectedTheme];
  
  const [messages, setMessages] = useState([
    { 
      type: 'bot', 
      content: 'Voice Waveform Demo initialized. Audio visualization ready for testing.' 
    }
  ]);

  const handleSendMessage = (message) => {
    setMessages(prev => [...prev, { type: 'user', content: message }]);
    
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        type: 'bot', 
        content: `Processing audio visualization with ${selectedStyle} style...` 
      }]);
    }, 1000);
  };

  return (
    <JarvisInterface messages={messages} onSendMessage={handleSendMessage}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        {/* Titre */}
        <h2 className="jarvis-text-glow" style={{ 
          textAlign: 'center',
          fontSize: '2rem',
          marginBottom: '30px',
          background: 'linear-gradient(45deg, #00d4ff, #00ff88)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          JARVIS AUDIO VISUALIZATION SUITE
        </h2>
        
        {/* Contrôles */}
        <div className="jarvis-panel" style={{ marginBottom: '30px' }}>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '20px',
            marginBottom: '20px'
          }}>
            {/* Sélecteur de style */}
            <div>
              <label className="jarvis-text-glow" style={{ 
                display: 'block', 
                marginBottom: '10px',
                fontSize: '0.9rem'
              }}>
                VISUALIZATION STYLE
              </label>
              <select 
                value={selectedStyle} 
                onChange={(e) => setSelectedStyle(e.target.value)}
                className="jarvis-input"
                style={{ width: '100%' }}
              >
                <option value="bars">Frequency Bars</option>
                <option value="circular">Circular Radial</option>
                <option value="wave">Waveform</option>
              </select>
            </div>
            
            {/* Sélecteur de taille */}
            <div>
              <label className="jarvis-text-glow" style={{ 
                display: 'block', 
                marginBottom: '10px',
                fontSize: '0.9rem'
              }}>
                SIZE CONFIGURATION
              </label>
              <select 
                value={selectedSize} 
                onChange={(e) => setSelectedSize(e.target.value)}
                className="jarvis-input"
                style={{ width: '100%' }}
              >
                <option value="small">Compact (300x120)</option>
                <option value="medium">Standard (500x200)</option>
                <option value="large">Extended (700x280)</option>
              </select>
            </div>
            
            {/* Sélecteur de thème */}
            <div>
              <label className="jarvis-text-glow" style={{ 
                display: 'block', 
                marginBottom: '10px',
                fontSize: '0.9rem'
              }}>
                COLOR THEME
              </label>
              <select 
                value={selectedTheme} 
                onChange={(e) => setSelectedTheme(e.target.value)}
                className="jarvis-input"
                style={{ width: '100%' }}
              >
                <option value="blue">Arctic Blue</option>
                <option value="green">Matrix Green</option>
                <option value="orange">Reactor Orange</option>
                <option value="purple">Plasma Purple</option>
              </select>
            </div>
          </div>
          
          {/* Informations de configuration */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            fontSize: '0.8rem',
            color: 'var(--jarvis-primary)',
            borderTop: '1px solid rgba(0, 212, 255, 0.2)',
            paddingTop: '15px'
          }}>
            <span>STYLE: {selectedStyle.toUpperCase()}</span>
            <span>SIZE: {currentSize.width}×{currentSize.height}</span>
            <span>THEME: {selectedTheme.toUpperCase()}</span>
          </div>
        </div>
        
        {/* Visualisation principale */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          marginBottom: '40px' 
        }}>
          <VoiceWaveformAdvanced
            width={currentSize.width}
            height={currentSize.height}
            style={selectedStyle}
            primaryColor={currentTheme.primary}
            secondaryColor={currentTheme.secondary}
            accentColor={currentTheme.accent}
          />
        </div>
        
        {/* Comparaison des styles */}
        <div className="jarvis-panel" style={{ marginBottom: '30px' }}>
          <h3 className="jarvis-text-glow" style={{ 
            textAlign: 'center',
            marginBottom: '25px',
            fontSize: '1.3rem'
          }}>
            STYLE COMPARISON MATRIX
          </h3>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
            gap: '20px' 
          }}>
            {/* Style Bars */}
            <div style={{ textAlign: 'center' }}>
              <h4 className="jarvis-text-glow" style={{ 
                marginBottom: '15px',
                fontSize: '1rem',
                color: currentTheme.primary
              }}>
                FREQUENCY BARS
              </h4>
              <VoiceWaveform
                width={280}
                height={140}
                barCount={48}
                barWidth={3}
                barSpacing={2}
                color={currentTheme.primary}
                glowColor={currentTheme.primary}
                showStatus={false}
              />
              <p style={{ 
                fontSize: '0.8rem', 
                color: 'var(--jarvis-primary)', 
                marginTop: '10px',
                opacity: 0.8
              }}>
                Classic frequency visualization with animated bars
              </p>
            </div>
            
            {/* Style Circular */}
            <div style={{ textAlign: 'center' }}>
              <h4 className="jarvis-text-glow" style={{ 
                marginBottom: '15px',
                fontSize: '1rem',
                color: currentTheme.secondary
              }}>
                CIRCULAR RADIAL
              </h4>
              <VoiceWaveformAdvanced
                width={280}
                height={140}
                style="circular"
                primaryColor={currentTheme.secondary}
                secondaryColor={currentTheme.primary}
                accentColor={currentTheme.accent}
              />
              <p style={{ 
                fontSize: '0.8rem', 
                color: 'var(--jarvis-primary)', 
                marginTop: '10px',
                opacity: 0.8
              }}>
                360° radial display with pulsing center core
              </p>
            </div>
            
            {/* Style Wave */}
            <div style={{ textAlign: 'center' }}>
              <h4 className="jarvis-text-glow" style={{ 
                marginBottom: '15px',
                fontSize: '1rem',
                color: currentTheme.accent
              }}>
                WAVEFORM
              </h4>
              <VoiceWaveformAdvanced
                width={280}
                height={140}
                style="wave"
                primaryColor={currentTheme.accent}
                secondaryColor={currentTheme.secondary}
                accentColor={currentTheme.primary}
              />
              <p style={{ 
                fontSize: '0.8rem', 
                color: 'var(--jarvis-primary)', 
                marginTop: '10px',
                opacity: 0.8
              }}>
                Traditional oscilloscope-style waveform display
              </p>
            </div>
          </div>
        </div>
        
        {/* Métriques audio */}
        <div className="jarvis-panel">
          <h3 className="jarvis-text-glow" style={{ 
            textAlign: 'center',
            marginBottom: '25px',
            fontSize: '1.3rem'
          }}>
            AUDIO PROCESSING METRICS
          </h3>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
            gap: '20px' 
          }}>
            <div style={{ textAlign: 'center' }}>
              <div className="jarvis-text-glow" style={{ fontSize: '0.9rem' }}>FFT SIZE</div>
              <div style={{ 
                color: currentTheme.primary, 
                fontSize: '1.5rem', 
                fontWeight: 'bold',
                textShadow: `0 0 10px ${currentTheme.primary}`
              }}>
                2048
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div className="jarvis-text-glow" style={{ fontSize: '0.9rem' }}>SAMPLE RATE</div>
              <div style={{ 
                color: currentTheme.secondary, 
                fontSize: '1.5rem', 
                fontWeight: 'bold',
                textShadow: `0 0 10px ${currentTheme.secondary}`
              }}>
                44.1k
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div className="jarvis-text-glow" style={{ fontSize: '0.9rem' }}>SMOOTHING</div>
              <div style={{ 
                color: currentTheme.accent, 
                fontSize: '1.5rem', 
                fontWeight: 'bold',
                textShadow: `0 0 10px ${currentTheme.accent}`
              }}>
                0.85
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div className="jarvis-text-glow" style={{ fontSize: '0.9rem' }}>LATENCY</div>
              <div style={{ 
                color: 'var(--jarvis-success)', 
                fontSize: '1.5rem', 
                fontWeight: 'bold',
                textShadow: '0 0 10px var(--jarvis-success)'
              }}>
                ~8ms
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div className="jarvis-text-glow" style={{ fontSize: '0.9rem' }}>CHANNELS</div>
              <div style={{ 
                color: 'var(--jarvis-warning)', 
                fontSize: '1.5rem', 
                fontWeight: 'bold',
                textShadow: '0 0 10px var(--jarvis-warning)'
              }}>
                MONO
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div className="jarvis-text-glow" style={{ fontSize: '0.9rem' }}>RANGE</div>
              <div style={{ 
                color: 'var(--jarvis-primary)', 
                fontSize: '1.5rem', 
                fontWeight: 'bold',
                textShadow: '0 0 10px var(--jarvis-primary)'
              }}>
                -85dB
              </div>
            </div>
          </div>
        </div>
        
        {/* Instructions d'utilisation */}
        <div className="jarvis-panel" style={{ marginTop: '30px' }}>
          <h3 className="jarvis-text-glow" style={{ 
            textAlign: 'center',
            marginBottom: '20px',
            fontSize: '1.3rem'
          }}>
            INTEGRATION INSTRUCTIONS
          </h3>
          
          <div style={{ 
            fontSize: '0.9rem',
            lineHeight: '1.6',
            color: 'var(--jarvis-primary)',
            opacity: 0.9
          }}>
            <p style={{ marginBottom: '15px' }}>
              <strong>Basic Usage:</strong> Import and use VoiceWaveform component for simple frequency bars visualization.
            </p>
            <p style={{ marginBottom: '15px' }}>
              <strong>Advanced Usage:</strong> Use VoiceWaveformAdvanced for WebSocket integration and multiple visualization styles.
            </p>
            <p style={{ marginBottom: '15px' }}>
              <strong>WebSocket Integration:</strong> Components automatically connect to JARVIS WebSocket for real-time status updates.
            </p>
            <p style={{ marginBottom: '0' }}>
              <strong>Customization:</strong> Full control over colors, sizes, styles, and audio processing parameters.
            </p>
          </div>
        </div>
      </div>
    </JarvisInterface>
  );
};

export default VoiceWaveformDemo;