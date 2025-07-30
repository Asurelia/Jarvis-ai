/**
 * 🎭 JARVIS Interface Demo - Page de démonstration de l'interface holographique
 * Exemple d'utilisation du composant JarvisInterface
 */
import React, { useState } from 'react';
import JarvisInterface from '../components/JarvisInterface';

function JarvisInterfaceDemo() {
  // État des messages
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: 'Welcome to JARVIS holographic interface. System initialized and ready for your commands.',
      timestamp: new Date()
    }
  ]);

  // Gestionnaire d'envoi de message
  const handleSendMessage = (content) => {
    // Ajouter le message utilisateur
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: content,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);

    // Simuler une réponse de JARVIS après un délai
    setTimeout(() => {
      const responses = [
        'Processing your request. Analysis complete.',
        'Command acknowledged. Executing protocol.',
        'System scan initiated. All modules operational.',
        'Neural network processing. Solution found.',
        'Quantum calculations complete. Results available.'
      ];
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, botMessage]);
    }, 1500);
  };

  return (
    <JarvisInterface 
      messages={messages}
      onSendMessage={handleSendMessage}
      enableScanlines={true}
      showScanlineControls={true}
    >
      {/* Contenu additionnel optionnel */}
      <div style={{ textAlign: 'center' }}>
        <h2 className="jarvis-text-glow" style={{ marginBottom: '20px' }}>
          SYSTEM STATUS
        </h2>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(3, 1fr)', 
          gap: '20px',
          maxWidth: '600px',
          margin: '0 auto'
        }}>
          <div className="jarvis-panel" style={{ padding: '15px' }}>
            <h4 className="jarvis-text-glow">CORE</h4>
            <div style={{ fontSize: '2rem', color: 'var(--jarvis-success)' }}>
              98%
            </div>
          </div>
          <div className="jarvis-panel" style={{ padding: '15px' }}>
            <h4 className="jarvis-text-glow">MEMORY</h4>
            <div style={{ fontSize: '2rem', color: 'var(--jarvis-warning)' }}>
              67%
            </div>
          </div>
          <div className="jarvis-panel" style={{ padding: '15px' }}>
            <h4 className="jarvis-text-glow">NETWORK</h4>
            <div style={{ fontSize: '2rem', color: 'var(--jarvis-primary)' }}>
              OK
            </div>
          </div>
        </div>
      </div>
    </JarvisInterface>
  );
}

export default JarvisInterfaceDemo;