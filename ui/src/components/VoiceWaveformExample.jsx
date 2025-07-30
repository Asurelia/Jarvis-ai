/**
 * 🎵 Exemple d'utilisation du composant VoiceWaveform
 * Montre comment intégrer la visualisation audio dans l'interface JARVIS
 */
import React, { useState } from 'react';
import VoiceWaveform from './VoiceWaveform';
import JarvisInterface from './JarvisInterface';

const VoiceWaveformExample = () => {
  const [messages, setMessages] = useState([
    { type: 'bot', content: 'Hello, I am JARVIS. How can I assist you today?' }
  ]);

  const handleSendMessage = (message) => {
    setMessages(prev => [...prev, { type: 'user', content: message }]);
    
    // Simuler une réponse de JARVIS
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        type: 'bot', 
        content: 'Processing your request...' 
      }]);
    }, 1000);
  };

  return (
    <JarvisInterface messages={messages} onSendMessage={handleSendMessage}>
      {/* Section de visualisation audio */}
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '20px',
        alignItems: 'center' 
      }}>
        <h2 className="jarvis-text-glow" style={{ 
          textAlign: 'center',
          fontSize: '1.5rem',
          marginBottom: '20px'
        }}>
          AUDIO VISUALIZATION
        </h2>
        
        {/* Waveform principal */}
        <VoiceWaveform 
          width={600}
          height={200}
          barCount={80}
          barWidth={4}
          barSpacing={3}
          color="#00d4ff"
          glowColor="#00d4ff"
          showStatus={true}
        />
        
        {/* Variations de styles */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(2, 1fr)', 
          gap: '20px',
          width: '100%',
          maxWidth: '600px'
        }}>
          {/* Style vert */}
          <VoiceWaveform 
            width={280}
            height={100}
            barCount={40}
            barWidth={3}
            barSpacing={2}
            color="#00ff88"
            glowColor="#00ff88"
            showStatus={false}
          />
          
          {/* Style orange */}
          <VoiceWaveform 
            width={280}
            height={100}
            barCount={40}
            barWidth={3}
            barSpacing={2}
            color="#ff6b00"
            glowColor="#ff6b00"
            showStatus={false}
          />
        </div>
        
        {/* Contrôles audio */}
        <div className="jarvis-panel" style={{ 
          width: '100%',
          maxWidth: '600px',
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center'
        }}>
          <button className="jarvis-button" style={{ minWidth: '120px' }}>
            🎤 START
          </button>
          <button className="jarvis-button" style={{ minWidth: '120px' }}>
            ⏸️ PAUSE
          </button>
          <button className="jarvis-button" style={{ minWidth: '120px' }}>
            ⏹️ STOP
          </button>
        </div>
        
        {/* Informations audio */}
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '20px',
          width: '100%',
          maxWidth: '600px',
          fontSize: '0.9rem'
        }}>
          <div className="jarvis-panel" style={{ textAlign: 'center' }}>
            <div className="jarvis-text-glow">FREQUENCY</div>
            <div style={{ color: 'var(--jarvis-success)', fontSize: '1.2rem' }}>
              44.1 kHz
            </div>
          </div>
          
          <div className="jarvis-panel" style={{ textAlign: 'center' }}>
            <div className="jarvis-text-glow">BITRATE</div>
            <div style={{ color: 'var(--jarvis-primary)', fontSize: '1.2rem' }}>
              320 kbps
            </div>
          </div>
          
          <div className="jarvis-panel" style={{ textAlign: 'center' }}>
            <div className="jarvis-text-glow">LATENCY</div>
            <div style={{ color: 'var(--jarvis-warning)', fontSize: '1.2rem' }}>
              12 ms
            </div>
          </div>
        </div>
      </div>
    </JarvisInterface>
  );
};

export default VoiceWaveformExample;