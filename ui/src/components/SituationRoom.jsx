/**
 * 🏢 JARVIS Situation Room - Centre de contrôle style Iron Man
 * Dashboard fullscreen avec grille de panneaux holographiques
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useJarvis } from '../contexts/JarvisContext';
import GPUStats from './GPUStats';
import VoiceWaveform from './VoiceWaveform';
import ScanlineEffect from './ScanlineEffect';
import ErrorBoundary from './ErrorBoundary';
import AudioErrorBoundary from './AudioErrorBoundary';
import APIErrorBoundary from './APIErrorBoundary';
import VisualizationErrorBoundary from './VisualizationErrorBoundary';
import ErrorMonitor from './ErrorMonitor';
import ErrorBoundaryTester from './ErrorBoundaryTester';
import { useErrorLogger } from './ErrorLogger';
import '../styles/jarvis-holographic.css';

// Hook pour les statistiques système
const useSystemStats = () => {
  const [stats, setStats] = useState({
    cpu: { usage: 0, temperature: 0, cores: 0 },
    memory: { used: 0, total: 0, percentage: 0 },
    network: { upload: 0, download: 0, status: 'connected' },
    storage: { used: 0, total: 0, percentage: 0 }
  });

  useEffect(() => {
    // Simulation des stats système (à remplacer par vraies données)
    const updateStats = () => {
      setStats({
        cpu: {
          usage: Math.random() * 100,
          temperature: 45 + Math.random() * 30,
          cores: 16
        },
        memory: {
          used: 8.5 + Math.random() * 4,
          total: 32,
          percentage: (8.5 + Math.random() * 4) / 32 * 100
        },
        network: {
          upload: Math.random() * 50,
          download: Math.random() * 100,
          status: Math.random() > 0.1 ? 'connected' : 'limited'
        },
        storage: {
          used: 850 + Math.random() * 100,
          total: 2000,
          percentage: (850 + Math.random() * 100) / 2000 * 100
        }
      });
    };

    const interval = setInterval(updateStats, 2000);
    updateStats();
    return () => clearInterval(interval);
  }, []);

  return stats;
};

// Hook pour les news/météo
const useNewsWeather = () => {
  const [data, setData] = useState({
    weather: {
      temperature: 22,
      condition: 'Clear',
      humidity: 65,
      windSpeed: 12
    },
    news: [
      'Tech: New AI breakthrough in quantum computing',
      'Market: Tech stocks rise 2.5% in early trading',
      'Science: Mars mission reaches milestone'
    ]
  });

  return data;
};

// Panneau Chat Principal
const ChatPanel = ({ messages, onSendMessage, isActive }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim() && onSendMessage) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="situation-panel">
      <div className="panel-header">
        <h3 className="jarvis-text-glow">🤖 JARVIS CENTRAL</h3>
        <div className={`status-indicator ${isActive ? 'active' : 'idle'}`} />
      </div>
      
      <div className="chat-messages" style={{ height: '70%', overflowY: 'auto' }}>
        {messages.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.type}`}>
            <div className="message-header">
              <span className="jarvis-text-glow">
                {msg.type === 'user' ? 'USER' : 'JARVIS'}
              </span>
              <span className="timestamp">{msg.timestamp}</span>
            </div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSend} className="chat-input">
        <input
          type="text"
          className="jarvis-input"
          placeholder="Enter command or query..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{ fontSize: '0.9rem' }}
        />
        <button type="submit" className="jarvis-button">SEND</button>
      </form>
    </div>
  );
};

// Panneau GPU Stats (wrapper)
const GPUPanel = () => (
  <VisualizationErrorBoundary
    componentName="GPU Statistics Panel"
    title="GPU MONITORING ERROR"
    message="The GPU statistics panel has encountered an error. Hardware monitoring may be unavailable."
    variant="warning"
  >
    <div className="situation-panel">
      <GPUStats className="compact-gpu-stats" />
    </div>
  </VisualizationErrorBoundary>
);

// Panneau Système
const SystemPanel = () => {
  const stats = useSystemStats();
  
  const getStatusColor = (value, thresholds = { good: 50, warning: 80 }) => {
    if (value < thresholds.good) return '#00ff88';
    if (value < thresholds.warning) return '#ff9500';
    return '#ff3b30';
  };

  return (
    <div className="situation-panel">
      <div className="panel-header">
        <h3 className="jarvis-text-glow">⚡ SYSTEM STATUS</h3>
        <div className="status-indicator active" />
      </div>
      
      <div className="system-metrics">
        {/* CPU */}
        <div className="metric-row">
          <div className="metric-label">CPU Usage</div>
          <div className="metric-value" style={{ color: getStatusColor(stats.cpu.usage) }}>
            {stats.cpu.usage.toFixed(1)}%
          </div>
          <div className="metric-bar">
            <div 
              className="metric-fill" 
              style={{ 
                width: `${stats.cpu.usage}%`,
                backgroundColor: getStatusColor(stats.cpu.usage)
              }} 
            />
          </div>
        </div>

        {/* Memory */}
        <div className="metric-row">
          <div className="metric-label">Memory</div>
          <div className="metric-value" style={{ color: getStatusColor(stats.memory.percentage) }}>
            {stats.memory.used.toFixed(1)}/{stats.memory.total}GB
          </div>
          <div className="metric-bar">
            <div 
              className="metric-fill" 
              style={{ 
                width: `${stats.memory.percentage}%`,
                backgroundColor: getStatusColor(stats.memory.percentage)
              }} 
            />
          </div>
        </div>

        {/* Network */}
        <div className="metric-row">
          <div className="metric-label">Network</div>
          <div className="metric-value" style={{ 
            color: stats.network.status === 'connected' ? '#00ff88' : '#ff9500' 
          }}>
            {stats.network.status.toUpperCase()}
          </div>
          <div className="metric-details">
            ↑ {stats.network.upload.toFixed(1)} MB/s | ↓ {stats.network.download.toFixed(1)} MB/s
          </div>
        </div>

        {/* Storage */}
        <div className="metric-row">
          <div className="metric-label">Storage</div>
          <div className="metric-value" style={{ color: getStatusColor(stats.storage.percentage) }}>
            {stats.storage.used.toFixed(0)}/{stats.storage.total}GB
          </div>
          <div className="metric-bar">
            <div 
              className="metric-fill" 
              style={{ 
                width: `${stats.storage.percentage}%`,
                backgroundColor: getStatusColor(stats.storage.percentage)
              }} 
            />
          </div>
        </div>

        {/* Temperature */}
        <div className="metric-row">
          <div className="metric-label">CPU Temp</div>
          <div className="metric-value" style={{ color: getStatusColor(stats.cpu.temperature, { good: 60, warning: 80 }) }}>
            {stats.cpu.temperature.toFixed(1)}°C
          </div>
        </div>
      </div>
    </div>
  );
};

// Panneau Audio/Voice
const AudioPanel = () => {
  const { state } = useJarvis();
  
  return (
    <AudioErrorBoundary
      componentName="Audio Interface Panel"
      title="AUDIO SYSTEM ERROR"
      message="The audio interface panel has encountered an error. Voice features may be limited."
    >
      <div className="situation-panel">
        <div className="panel-header">
          <h3 className="jarvis-text-glow">🎤 AUDIO INTERFACE</h3>
          <div className={`status-indicator ${state.config.voiceMode ? 'active' : 'idle'}`} />
        </div>
        
        <div className="audio-content">
          <ErrorBoundary
            componentName="Voice Waveform"
            showHome={false}
            variant="info"
          >
            <VoiceWaveform 
              width={280} 
              height={120} 
              barCount={32} 
              showStatus={false}
              color="#00d4ff"
            />
          </ErrorBoundary>
          
          <div className="audio-controls">
            <div className="control-row">
              <span>Voice Mode:</span>
              <span style={{ color: state.config.voiceMode ? '#00ff88' : '#ff9500' }}>
                {state.config.voiceMode ? 'ACTIVE' : 'STANDBY'}
              </span>
            </div>
            <div className="control-row">
              <span>Audio Level:</span>
              <span style={{ color: '#00d4ff' }}>NOMINAL</span>
            </div>
          </div>
        </div>
      </div>
    </AudioErrorBoundary>
  );
};

// Panneau Horloge/Calendrier
const ClockPanel = () => {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="situation-panel">
      <div className="panel-header">
        <h3 className="jarvis-text-glow">🕒 TEMPORAL</h3>
      </div>
      
      <div className="time-display">
        <div className="current-time jarvis-text-glow">
          {time.toLocaleTimeString('en-US', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          })}
        </div>
        <div className="current-date">
          {time.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </div>
        
        <div className="time-zones">
          <div className="timezone-item">
            <span>UTC:</span>
            <span>{new Date().toISOString().split('T')[1].split('.')[0]}</span>
          </div>
          <div className="timezone-item">
            <span>UNIX:</span>
            <span>{Math.floor(Date.now() / 1000)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Panneau News/Météo
const NewsWeatherPanel = () => {
  const { weather, news } = useNewsWeather();
  
  return (
    <div className="situation-panel">
      <div className="panel-header">
        <h3 className="jarvis-text-glow">🌍 INTEL FEED</h3>
      </div>
      
      <div className="intel-content">
        {/* Météo */}
        <div className="weather-section">
          <div className="weather-main">
            <span className="temperature jarvis-text-glow">{weather.temperature}°C</span>
            <span className="condition">{weather.condition}</span>
          </div>
          <div className="weather-details">
            <div>Humidity: {weather.humidity}%</div>
            <div>Wind: {weather.windSpeed} km/h</div>
          </div>
        </div>
        
        {/* News */}
        <div className="news-section">
          <h4>Latest Intel:</h4>
          {news.map((item, index) => (
            <div key={index} className="news-item">
              <div className="news-indicator">●</div>
              <div className="news-text">{item}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Panneau Commandes Rapides
const CommandsPanel = () => {
  const { actions, electronAPI, apiService } = useJarvis();
  
  const quickCommands = [
    { label: '📸 CAPTURE', action: 'screenshot', color: '#00d4ff' },
    { label: '🔍 ANALYZE', action: 'analyze', color: '#00ff88' },
    { label: '⚡ EXECUTE', action: 'execute', color: '#ff9500' },
    { label: '🧠 LEARN', action: 'learn', color: '#ff6b00' },
    { label: '🔒 SECURE', action: 'secure', color: '#ff3b30' },
    { label: '📊 REPORT', action: 'report', color: '#00d4ff' }
  ];

  const handleQuickCommand = async (action) => {
    try {
      actions.addLog('info', `Executing quick command: ${action}`, 'ui');
      
      switch (action) {
        case 'screenshot':
          await (electronAPI.executeCommand || apiService.takeScreenshot)('screenshot');
          break;
        case 'analyze':
          actions.addNotification('info', 'Analysis', 'Starting system analysis...');
          break;
        case 'execute':
          actions.addNotification('info', 'Execute', 'Ready for command execution');
          break;
        default:
          actions.addNotification('info', 'Command', `${action} initiated`);
      }
    } catch (error) {
      actions.addLog('error', `Quick command failed: ${error.message}`, 'ui');
    }
  };

  return (
    <APIErrorBoundary
      componentName="Quick Commands Panel"
      title="COMMAND SYSTEM ERROR"
      message="The rapid deployment panel has encountered an error. Some commands may be unavailable."
    >
      <div className="situation-panel">
        <div className="panel-header">
          <h3 className="jarvis-text-glow">⚡ RAPID DEPLOY</h3>
        </div>
        
        <div className="commands-grid">
          {quickCommands.map((cmd, index) => (
            <button
              key={index}
              className="quick-command-btn"
              style={{ borderColor: cmd.color, color: cmd.color }}
              onClick={() => handleQuickCommand(cmd.action)}
            >
              {cmd.label}
            </button>
          ))}
        </div>
      </div>
    </APIErrorBoundary>
  );
};

// Panneau Logs
const LogsPanel = () => {
  const { state } = useJarvis();
  const logsEndRef = useRef(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.logs]);

  const getLogColor = (level) => {
    switch (level) {
      case 'error': return '#ff3b30';
      case 'warning': return '#ff9500';
      case 'success': return '#00ff88';
      case 'info': return '#00d4ff';
      default: return '#ffffff';
    }
  };

  return (
    <div className="situation-panel">
      <div className="panel-header">
        <h3 className="jarvis-text-glow">📋 ACTIVITY LOG</h3>
        <div className="log-count">{state.logs.length}</div>
      </div>
      
      <div className="logs-container">
        {state.logs.slice(0, 20).map((log, index) => (
          <div key={log.id || index} className="log-entry">
            <span className="log-time">
              {new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false })}
            </span>
            <span 
              className="log-level" 
              style={{ color: getLogColor(log.level) }}
            >
              [{log.level.toUpperCase()}]
            </span>
            <span className="log-source">[{log.source}]</span>
            <span className="log-message">{log.message}</span>
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

// Composant principal SituationRoom
const SituationRoom = ({ isVisible, onClose }) => {
  const { state, actions } = useJarvis();
  const { logError } = useErrorLogger();
  const [messages, setMessages] = useState([
    { type: 'bot', content: 'Situation Room activated. All systems online.', timestamp: new Date().toLocaleTimeString() }
  ]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showErrorMonitor, setShowErrorMonitor] = useState(false);
  const [showErrorTester, setShowErrorTester] = useState(false);
  const containerRef = useRef(null);

  // Handler d'erreur pour Situation Room
  const handleSituationRoomError = (errorData) => {
    logError({
      type: 'visualization',
      severity: 'high',
      message: errorData.error?.message || 'Situation Room component error',
      component: 'SituationRoom',
      context: 'situation-room-panel',
      stack: errorData.error?.stack
    });
  };

  // Gestion du plein écran
  const toggleFullscreen = useCallback(async () => {
    if (!document.fullscreenElement) {
      try {
        await containerRef.current?.requestFullscreen();
        setIsFullscreen(true);
      } catch (error) {
        console.warn('Fullscreen not supported:', error);
      }
    } else {
      try {
        await document.exitFullscreen();
        setIsFullscreen(false);
      } catch (error) {
        console.warn('Exit fullscreen failed:', error);
      }
    }
  }, []);

  // Gestion des messages chat
  const handleSendMessage = useCallback((message) => {
    const userMessage = {
      type: 'user',
      content: message,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // Simuler réponse JARVIS
    setTimeout(() => {
      const botMessage = {
        type: 'bot',
        content: `Processing: ${message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, botMessage]);
    }, 1000);
    
    actions.addLog('info', `User command: ${message}`, 'situation-room');
  }, [actions]);

  // Raccourcis clavier
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Ctrl+Shift+J pour toggle
      if (e.ctrlKey && e.shiftKey && e.key === 'J') {
        e.preventDefault();
        if (onClose) onClose();
      }
      
      // ESC pour sortir du fullscreen
      if (e.key === 'Escape' && isFullscreen) {
        toggleFullscreen();
      }
      
      // F11 pour toggle fullscreen
      if (e.key === 'F11') {
        e.preventDefault();
        toggleFullscreen();
      }
    };

    if (isVisible) {
      document.addEventListener('keydown', handleKeyPress);
      return () => document.removeEventListener('keydown', handleKeyPress);
    }
  }, [isVisible, isFullscreen, onClose, toggleFullscreen]);

  // Gestionnaire pour les changements de fullscreen
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  if (!isVisible) return null;

  return (
    <ScanlineEffect config={{ enabled: true, intensity: 'high' }}>
      <div 
        ref={containerRef}
        className={`situation-room ${isFullscreen ? 'fullscreen' : ''}`}
      >
        {/* Header avec contrôles */}
        <div className="situation-header">
          <div className="header-left">
            <h1 className="jarvis-title" style={{ fontSize: '2rem', margin: 0 }}>
              SITUATION ROOM
            </h1>
            <div className="status-line">
              <span className="jarvis-text-glow">STATUS: ACTIVE</span>
              <span className="jarvis-text-glow">CORE: ONLINE</span>
              <span className="jarvis-text-glow">THREAT LEVEL: GREEN</span>
            </div>
          </div>
          
          <div className="header-controls">
            <button 
              className="jarvis-button" 
              onClick={() => setShowErrorMonitor(true)}
              style={{ fontSize: '0.8rem', padding: '8px 16px', marginRight: '10px' }}
            >
              🔍 ERROR MONITOR
            </button>
            <button 
              className="jarvis-button" 
              onClick={() => setShowErrorTester(true)}
              style={{ fontSize: '0.8rem', padding: '8px 16px', marginRight: '10px' }}
            >
              🧪 ERROR TESTER
            </button>
            <button 
              className="jarvis-button" 
              onClick={toggleFullscreen}
              style={{ fontSize: '0.8rem', padding: '8px 16px' }}
            >
              {isFullscreen ? 'EXIT FULLSCREEN' : 'FULLSCREEN'}
            </button>
            <button 
              className="jarvis-button" 
              onClick={onClose}
              style={{ fontSize: '0.8rem', padding: '8px 16px' }}
            >
              CLOSE [ESC]
            </button>
          </div>
        </div>

        {/* Grille principale 4x4 */}
        <div className="situation-grid">
          {/* Ligne 1 */}
          <div className="grid-item span-2">
            <ChatPanel 
              messages={messages} 
              onSendMessage={handleSendMessage}
              isActive={state.jarvis.status === 'connected'}
            />
          </div>
          <div className="grid-item">
            <ClockPanel />
          </div>
          <div className="grid-item">
            <NewsWeatherPanel />
          </div>

          {/* Ligne 2 */}
          <div className="grid-item">
            <GPUPanel />
          </div>
          <div className="grid-item">
            <SystemPanel />
          </div>
          <div className="grid-item">
            <AudioPanel />
          </div>
          <div className="grid-item">
            <CommandsPanel />
          </div>

          {/* Ligne 3 - Logs sur toute la largeur */}
          <div className="grid-item span-4">
            <LogsPanel />
          </div>
        </div>

        {/* Effets visuels */}
        <div className="situation-effects">
          {/* Coins HUD */}
          <div className="hud-corner top-left" />
          <div className="hud-corner top-right" />
          <div className="hud-corner bottom-left" />
          <div className="hud-corner bottom-right" />
          
          {/* Grille de fond */}
          <div className="grid-overlay" />
        </div>
      </div>

      {/* Error Monitor Dialog */}
      <ErrorMonitor
        isVisible={showErrorMonitor}
        onClose={() => setShowErrorMonitor(false)}
      />

      {/* Error Boundary Tester Dialog */}
      <ErrorBoundaryTester
        isVisible={showErrorTester}
        onClose={() => setShowErrorTester(false)}
      />
    </ScanlineEffect>
  );
};

export default SituationRoom;