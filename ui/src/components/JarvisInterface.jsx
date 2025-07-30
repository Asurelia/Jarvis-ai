/**
 * 🎭 JARVIS Interface - Composant d'interface holographique style Iron Man
 * Interface futuriste avec effets visuels holographiques
 */
import React, { useState, useRef, useEffect } from 'react';
import ScanlineEffect, { useScanlineConfig } from './ScanlineEffect';
import PersonaSwitcher from './PersonaSwitcher';
import '../styles/jarvis-holographic.css';
import '../styles/persona-switcher.css';

// Composant de particules flottantes
const FloatingParticles = ({ count = 50 }) => {
  const particles = Array.from({ length: count }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 10,
    duration: 10 + Math.random() * 10
  }));

  return (
    <div className="jarvis-particles">
      {particles.map(particle => (
        <div
          key={particle.id}
          className="jarvis-particle"
          style={{
            left: `${particle.left}%`,
            animationDelay: `${particle.delay}s`,
            animationDuration: `${particle.duration}s`
          }}
        />
      ))}
    </div>
  );
};

// Composant HUD Corners
const HUDCorners = () => (
  <>
    <div className="jarvis-hud-corner top-left" />
    <div className="jarvis-hud-corner top-right" />
    <div className="jarvis-hud-corner bottom-left" />
    <div className="jarvis-hud-corner bottom-right" />
  </>
);

// Composant Message holographique
const HolographicMessage = ({ message, type = 'bot' }) => (
  <div className={`jarvis-message ${type}`}>
    <div className="message-header">
      <span className="jarvis-text-glow">{type === 'user' ? 'USER' : 'JARVIS'}</span>
    </div>
    <div className="message-content">
      {message}
    </div>
  </div>
);

// Composant principal JarvisInterface
const JarvisInterface = ({ children, messages = [], onSendMessage, enableScanlines = true, showScanlineControls = false }) => {
  const [inputValue, setInputValue] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentPersona, setCurrentPersona] = useState(null);
  const messagesEndRef = useRef(null);
  
  // Configuration des scanlines avec preset Iron Man par défaut
  const { config: scanlineConfig, updateConfig: updateScanlineConfig, applyPreset } = useScanlineConfig({
    enabled: enableScanlines,
    intensity: 'high',
    effects: { 
      horizontal: true, 
      vertical: true, 
      diagonal: false, 
      radar: true, 
      glitch: false 
    },
    count: { horizontal: 3, vertical: 2, diagonal: 0 }
  });

  // Auto-scroll vers le bas
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Gestionnaire d'envoi de message
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (inputValue.trim() && onSendMessage) {
      onSendMessage(inputValue);
      setInputValue('');
      setIsProcessing(true);
      // Simuler le traitement
      setTimeout(() => setIsProcessing(false), 1500);
    }
  };

  // Toggle microphone
  const toggleListening = () => {
    setIsListening(!isListening);
  };
  
  // Toggle scanlines avec effet de glitch temporaire
  const toggleScanlines = () => {
    updateScanlineConfig({ enabled: !scanlineConfig.enabled });
  };
  
  // Activer mode intense temporairement
  const activateIntenseMode = () => {
    applyPreset('intense');
    setTimeout(() => {
      applyPreset('ironman');
    }, 5000);
  };

  // Gestionnaire de changement de persona
  const handlePersonaChange = (personaData) => {
    setCurrentPersona(personaData.current);
    console.log('Persona changée:', personaData);
    
    // Ajuster l'interface selon la persona
    if (personaData.current === 'friday') {
      // Style plus décontracté pour FRIDAY
      applyPreset('friendly');
    } else if (personaData.current === 'edith') {
      // Style plus technique pour EDITH
      applyPreset('technical');
    } else {
      // Style classique pour JARVIS
      applyPreset('ironman');
    }
  };

  return (
    <ScanlineEffect 
      config={scanlineConfig} 
      onConfigChange={updateScanlineConfig}
      showControls={showScanlineControls}
    >
      <div className="jarvis-holographic-container">
        <FloatingParticles count={30} />
        <HUDCorners />
      
      <div className="jarvis-interface">
        {/* Titre principal */}
        <h1 className="jarvis-title jarvis-glitch">J.A.R.V.I.S</h1>
        <p className="jarvis-text-glow" style={{ textAlign: 'center', marginBottom: '2rem' }}>
          Just A Rather Very Intelligent System
        </p>

        {/* Panneau principal */}
        <div className="jarvis-panel" style={{ maxWidth: '800px', margin: '0 auto' }}>
          {/* Zone de messages */}
          <div style={{ height: '400px', overflowY: 'auto', marginBottom: '20px' }}>
            {messages.map((msg, index) => (
              <HolographicMessage 
                key={index} 
                message={msg.content} 
                type={msg.type}
              />
            ))}
            {isProcessing && (
              <div style={{ textAlign: 'center', margin: '20px' }}>
                <span className="jarvis-loading"></span>
                <span className="jarvis-text-glow" style={{ marginLeft: '10px' }}>
                  Processing...
                </span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Zone de saisie */}
          <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              className="jarvis-input"
              placeholder="Enter command or query..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isProcessing}
            />
            <button 
              type="button"
              className={`jarvis-button ${isListening ? 'active' : ''}`}
              onClick={toggleListening}
              style={{ minWidth: '60px' }}
            >
              {isListening ? '🎤' : '🎙️'}
            </button>
            <button 
              type="submit"
              className="jarvis-button"
              disabled={!inputValue.trim() || isProcessing}
            >
              SEND
            </button>
          </form>

          {/* Indicateurs d'état */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            marginTop: '20px',
            fontSize: '0.9rem'
          }}>
            <span className="jarvis-text-glow">
              STATUS: <span style={{ color: 'var(--jarvis-success)' }}>ONLINE</span>
            </span>
            <span className="jarvis-text-glow">
              CORE: <span style={{ color: 'var(--jarvis-primary)' }}>ACTIVE</span>
            </span>
            <span className="jarvis-text-glow">
              AI: <span style={{ color: 'var(--jarvis-secondary)' }}>READY</span>
            </span>
          </div>
          
          {/* Contrôles de scanlines */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            gap: '10px', 
            marginTop: '15px' 
          }}>
            <button 
              className={`jarvis-button ${scanlineConfig.enabled ? 'active' : ''}`}
              onClick={toggleScanlines}
              style={{ fontSize: '0.7rem', padding: '5px 15px' }}
              title="Toggle Scanline Effects"
            >
              SCAN: {scanlineConfig.enabled ? 'ON' : 'OFF'}
            </button>
            <button 
              className="jarvis-button"
              onClick={activateIntenseMode}
              style={{ fontSize: '0.7rem', padding: '5px 15px' }}
              title="Activate Intense Scan Mode"
            >
              INTENSE
            </button>
          </div>
        </div>

        {/* Contenu additionnel si fourni */}
        {children && (
          <div className="jarvis-panel" style={{ maxWidth: '800px', margin: '20px auto' }}>
            {children}
          </div>
        )}

        {/* Panneaux latéraux de données */}
        <div style={{ 
          position: 'fixed', 
          top: '50%', 
          left: '20px', 
          transform: 'translateY(-50%)',
          width: '200px'
        }}>
          <div className="jarvis-panel" style={{ marginBottom: '20px' }}>
            <h3 className="jarvis-text-glow" style={{ fontSize: '1rem', marginBottom: '10px' }}>
              SYSTEM METRICS
            </h3>
            <div style={{ fontSize: '0.8rem', lineHeight: '1.8' }}>
              <div>CPU: <span style={{ color: 'var(--jarvis-success)' }}>28%</span></div>
              <div>RAM: <span style={{ color: 'var(--jarvis-warning)' }}>67%</span></div>
              <div>NETWORK: <span style={{ color: 'var(--jarvis-success)' }}>STABLE</span></div>
              <div>TEMP: <span style={{ color: 'var(--jarvis-success)' }}>42°C</span></div>
            </div>
          </div>

          <div className="jarvis-panel">
            <h3 className="jarvis-text-glow" style={{ fontSize: '1rem', marginBottom: '10px' }}>
              AI MODULES
            </h3>
            <div style={{ fontSize: '0.8rem', lineHeight: '1.8' }}>
              <div>NLP: <span style={{ color: 'var(--jarvis-primary)' }}>ACTIVE</span></div>
              <div>VISION: <span style={{ color: 'var(--jarvis-primary)' }}>ACTIVE</span></div>
              <div>MEMORY: <span style={{ color: 'var(--jarvis-primary)' }}>ACTIVE</span></div>
              <div>LEARNING: <span style={{ color: 'var(--jarvis-secondary)' }}>ENABLED</span></div>
            </div>
          </div>
        </div>

        {/* Panneau droit avec PersonaSwitcher et actions rapides */}
        <div style={{ 
          position: 'fixed', 
          top: '50%', 
          right: '20px', 
          transform: 'translateY(-50%)',
          width: '250px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}>
          {/* PersonaSwitcher */}
          <PersonaSwitcher 
            onPersonaChange={handlePersonaChange}
            apiUrl="http://localhost:8001/api/persona"
            showDetails={false}
            className="jarvis-theme"
          />

          {/* Actions rapides */}
          <div className="jarvis-panel">
            <h3 className="jarvis-text-glow" style={{ fontSize: '1rem', marginBottom: '15px' }}>
              QUICK ACTIONS
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button className="jarvis-button" style={{ fontSize: '0.8rem' }}>
                ANALYZE
              </button>
              <button className="jarvis-button" style={{ fontSize: '0.8rem' }}>
                SCAN
              </button>
              <button className="jarvis-button" style={{ fontSize: '0.8rem' }}>
                EXECUTE
              </button>
              <button className="jarvis-button" style={{ fontSize: '0.8rem' }}>
                REPORT
              </button>
            </div>
          </div>
        </div>
      </div>
      </div>
    </ScanlineEffect>
  );
};

export default JarvisInterface;