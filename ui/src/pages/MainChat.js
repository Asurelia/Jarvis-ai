/**
 * 💬 JARVIS UI - Interface Chat Principale avec Sphère 3D
 * Interface de chat fullscreen avec sphère centrale réactive
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Paper,
  Tooltip,
  Fade,
  Button,
  Fab
} from '@mui/material';
import {
  Send as SendIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  SmartToy as BotIcon,
  Person as UserIcon,
  VolumeUp as VolumeIcon,
  Settings as SettingsIcon,
  Memory as MemoryIcon,
  Code as CodeIcon,
  Visibility as VisionIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

import { useJarvis } from '../contexts/JarvisContext';
import { useJarvisAPI } from '../hooks/useJarvisAPI';
import { useSphereAudioReactive } from '../hooks/useAudioAnalyzer';
import Sphere3D from '../components/Sphere3D';
import VoiceRecorder from '../components/VoiceRecorder';
import '../styles/jarvis-holographic.css';

function MainChat() {
  const theme = useTheme();
  const { state, actions } = useJarvis();
  const { chatWithAI, speakText, isConnected } = useJarvisAPI();
  
  // États du chat
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      type: 'bot',
      content: 'Bonjour ! Je suis JARVIS, votre assistant IA autonome. Je peux vous aider avec de nombreuses tâches : contrôler votre ordinateur, analyser des images, répondre à vos questions, et bien plus encore. Comment puis-je vous aider aujourd\'hui ?',
      timestamp: new Date(),
      status: 'sent'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [showPanels, setShowPanels] = useState(false);
  
  // Refs
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const chatContainerRef = useRef(null);
  
  // Audio réactif pour la sphère
  const {
    audioLevel,
    spectralData,
    isSpeechDetected,
    isAnalyzing,
    startAnalyzing,
    stopAnalyzing,
    connectSphere
  } = useSphereAudioReactive();

  // Auto-scroll vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus sur l'input au chargement
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Envoyer un message
  const sendMessage = async (content, isVoice = false) => {
    if (!content.trim() || !isConnected) return;

    // Ajouter le message utilisateur
    const userMessage = {
      id: Date.now() + '_user',
      type: 'user',
      content: content.trim(),
      timestamp: new Date(),
      status: 'sent',
      isVoice
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);

    try {
      // Envoyer à JARVIS
      const response = await chatWithAI(content, conversationId);
      
      if (response.success) {
        // Mettre à jour l'ID de conversation
        if (response.conversation_id && !conversationId) {
          setConversationId(response.conversation_id);
        }

        // Ajouter la réponse de JARVIS
        const botMessage = {
          id: Date.now() + '_bot',
          type: 'bot',
          content: response.response,
          timestamp: new Date(),
          status: 'sent'
        };
        
        setMessages(prev => [...prev, botMessage]);
        
        // Synthèse vocale si activée
        if (isSpeechDetected || isVoice) {
          setIsSpeaking(true);
          try {
            await speakText(response.response);
          } catch (err) {
            console.warn('Erreur synthèse vocale:', err);
          } finally {
            setIsSpeaking(false);
          }
        }
        
        // Log dans JARVIS
        actions.addLog('success', `Chat: ${content} -> ${response.response.substring(0, 50)}...`, 'chat');
        actions.incrementStat('commandsExecuted');
      } else {
        throw new Error(response.error || 'Réponse invalide');
      }
    } catch (error) {
      // Message d'erreur
      const errorMessage = {
        id: Date.now() + '_error',
        type: 'bot',
        content: `Désolé, je rencontre un problème : ${error.message}. Vérifiez que tous les modules JARVIS sont bien démarrés.`,
        timestamp: new Date(),
        status: 'error'
      };
      
      setMessages(prev => [...prev, errorMessage]);
      actions.addNotification('error', 'Chat', error.message);
    } finally {
      setIsTyping(false);
    }
  };

  // Gérer l'envoi par Enter
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputText);
    }
  };

  // Gérer la transcription vocale
  const handleVoiceTranscription = (transcription) => {
    sendMessage(transcription, true);
    setShowVoiceRecorder(false);
  };

  // Toggle microphone
  const toggleMicrophone = () => {
    if (isAnalyzing) {
      stopAnalyzing();
    } else {
      startAnalyzing();
    }
  };

  // Formater l'heure
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Animation d'effacement progressif des messages
  const getMessageOpacity = (index, total) => {
    const fadeStart = Math.max(0, total - 10); // Commencer à effacer après 10 messages
    if (index < fadeStart) {
      const fadeProgress = (fadeStart - index) / 5; // Effacer sur 5 messages
      return Math.max(0.1, 1 - fadeProgress);
    }
    return 1;
  };

  return (
    <Box
      className="jarvis-holographic-container"
      sx={{
        height: '100vh',
        width: '100vw',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Coins HUD */}
      <div className="jarvis-hud-corner top-left" />
      <div className="jarvis-hud-corner top-right" />
      <div className="jarvis-hud-corner bottom-left" />
      <div className="jarvis-hud-corner bottom-right" />
      
      {/* Particules flottantes */}
      <div className="jarvis-particles">
        {Array.from({ length: 20 }, (_, i) => (
          <div
            key={i}
            className="jarvis-particle"
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 10}s`,
              animationDuration: `${10 + Math.random() * 10}s`
            }}
          />
        ))}
      </div>
      {/* Zone de messages avec effet de fade */}
      <Box
        ref={chatContainerRef}
        className="jarvis-interface"
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 4,
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        {/* Titre JARVIS holographique */}
        <Box
          sx={{
            position: 'absolute',
            top: 40,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 10
          }}
        >
          <h1 className="jarvis-title jarvis-glitch">J.A.R.V.I.S</h1>
        </Box>

        {/* Sphère 3D centrale */}
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 1
          }}
        >
          <Sphere3D
            size={300}
            color={theme.palette.primary.main}
            isListening={isAnalyzing && isSpeechDetected}
            isSpeaking={isSpeaking}
            audioLevel={audioLevel}
            onSphereReady={connectSphere}
          />
        </Box>

        {/* Messages avec animation de fade */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 100,
            overflow: 'auto',
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            zIndex: 2,
            pointerEvents: 'none',
            '&::-webkit-scrollbar': { display: 'none' },
            scrollbarWidth: 'none'
          }}
        >
          {messages.map((message, index) => (
            <Fade
              key={message.id}
              in={true}
              timeout={1000}
            >
              <Box
                sx={{
                  alignSelf: message.type === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '60%',
                  opacity: getMessageOpacity(index, messages.length),
                  transition: 'opacity 2s ease-out',
                  pointerEvents: 'auto'
                }}
              >
                <Paper
                  className={`jarvis-message ${message.type}`}
                  sx={{
                    p: 2,
                    backgroundColor: message.type === 'user' 
                      ? 'rgba(0, 255, 136, 0.1)'
                      : message.status === 'error'
                      ? 'rgba(255, 59, 48, 0.1)'
                      : 'rgba(0, 212, 255, 0.1)',
                    backdropFilter: 'blur(20px)',
                    borderRadius: 3,
                    border: message.type === 'user'
                      ? '1px solid rgba(0, 255, 136, 0.3)'
                      : '1px solid rgba(0, 212, 255, 0.3)',
                    boxShadow: message.type === 'user'
                      ? '0 0 20px rgba(0, 255, 136, 0.2)'
                      : '0 0 20px rgba(0, 212, 255, 0.2)'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    <Avatar
                      sx={{
                        width: 32,
                        height: 32,
                        bgcolor: message.type === 'user' 
                          ? theme.palette.secondary.main 
                          : theme.palette.primary.main
                      }}
                    >
                      {message.type === 'user' ? <UserIcon /> : <BotIcon />}
                    </Avatar>
                    <Box sx={{ flex: 1 }}>
                      <Typography 
                        variant="body1" 
                        className="jarvis-text-glow"
                        sx={{ 
                          whiteSpace: 'pre-wrap', 
                          mb: 1,
                          fontFamily: '"Orbitron", monospace',
                          color: message.type === 'user' ? '#00ff88' : '#00d4ff'
                        }}
                      >
                        {message.content}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {message.isVoice && (
                          <Chip
                            icon={<MicIcon />}
                            label="Vocal"
                            size="small"
                            variant="outlined"
                          />
                        )}
                        <Typography variant="caption" color="text.secondary">
                          {formatTime(message.timestamp)}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </Paper>
              </Box>
            </Fade>
          ))}

          {/* Indicateur de frappe */}
          {isTyping && (
            <Fade in={true}>
              <Box sx={{ alignSelf: 'flex-start', maxWidth: '60%' }}>
                <Paper
                  sx={{
                    p: 2,
                    backgroundColor: theme.palette.background.paper + '90',
                    backdropFilter: 'blur(10px)',
                    borderRadius: 3,
                    border: `1px solid ${theme.palette.divider}40`
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                      <BotIcon />
                    </Avatar>
                    <Typography 
                      variant="body1" 
                      className="jarvis-text-glow"
                      sx={{ 
                        fontStyle: 'italic',
                        fontFamily: '"Orbitron", monospace',
                        color: '#00d4ff'
                      }}
                    >
                      JARVIS PROCESSING...
                    </Typography>
                  </Box>
                </Paper>
              </Box>
            </Fade>
          )}

          <div ref={messagesEndRef} />
        </Box>
      </Box>

      {/* Barre de saisie en bas */}
      <Box
        className="jarvis-panel"
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          p: 3,
          backgroundColor: 'transparent',
          backdropFilter: 'blur(20px)',
          borderTop: '1px solid rgba(0, 212, 255, 0.3)',
          borderRadius: 0,
          zIndex: 10
        }}
      >
        <Box sx={{ maxWidth: 800, mx: 'auto' }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end', mb: 2 }}>
            <TextField
              ref={inputRef}
              fullWidth
              multiline
              maxRows={4}
              placeholder="Entrez votre commande ou requête..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={!isConnected || isTyping}
              variant="outlined"
              className="jarvis-input"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3,
                  backgroundColor: 'rgba(0, 212, 255, 0.05)',
                  fontFamily: '"Orbitron", monospace',
                  color: '#00d4ff',
                  '& fieldset': {
                    borderColor: 'rgba(0, 212, 255, 0.3)'
                  },
                  '&:hover fieldset': {
                    borderColor: 'rgba(0, 212, 255, 0.5)'
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#00d4ff'
                  }
                },
                '& .MuiInputBase-input': {
                  color: '#00d4ff',
                  fontFamily: '"Orbitron", monospace'
                },
                '& .MuiInputBase-input::placeholder': {
                  color: 'rgba(0, 212, 255, 0.5)',
                  opacity: 1
                }
              }}
            />
            
            {/* Bouton micro */}
            <Tooltip title={isAnalyzing ? 'Arrêter le microphone' : 'Activer le microphone'}>
              <IconButton
                onClick={toggleMicrophone}
                disabled={!isConnected}
                className="jarvis-button"
                sx={{
                  backgroundColor: isAnalyzing 
                    ? 'rgba(0, 255, 136, 0.2)' 
                    : 'rgba(0, 212, 255, 0.1)',
                  color: isAnalyzing ? '#00ff88' : '#00d4ff',
                  border: isAnalyzing
                    ? '2px solid #00ff88'
                    : '2px solid #00d4ff',
                  borderRadius: '50px',
                  padding: '12px',
                  '&:hover': {
                    backgroundColor: isAnalyzing 
                      ? 'rgba(0, 255, 136, 0.3)' 
                      : 'rgba(0, 212, 255, 0.2)',
                  }
                }}
              >
                {isAnalyzing ? <MicIcon /> : <MicOffIcon />}
              </IconButton>
            </Tooltip>

            {/* Bouton envoyer */}
            <Tooltip title="Envoyer">
              <IconButton
                onClick={() => sendMessage(inputText)}
                disabled={!inputText.trim() || !isConnected || isTyping}
                className="jarvis-button"
                sx={{
                  backgroundColor: 'rgba(0, 212, 255, 0.2)',
                  color: '#00d4ff',
                  border: '2px solid #00d4ff',
                  borderRadius: '50px',
                  padding: '12px',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 212, 255, 0.3)'
                  },
                  '&:disabled': {
                    backgroundColor: 'rgba(0, 212, 255, 0.05)',
                    borderColor: 'rgba(0, 212, 255, 0.2)',
                    color: 'rgba(0, 212, 255, 0.3)'
                  }
                }}
              >
                <SendIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Indicateurs d'état */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Chip
                label={isConnected ? 'JARVIS ONLINE' : 'JARVIS OFFLINE'}
                className="jarvis-text-glow"
                size="small"
                icon={<BotIcon />}
                sx={{
                  backgroundColor: 'rgba(0, 212, 255, 0.1)',
                  border: `1px solid ${isConnected ? '#00ff88' : '#ff3b30'}`,
                  color: isConnected ? '#00ff88' : '#ff3b30',
                  fontFamily: '"Orbitron", monospace',
                  '& .MuiChip-icon': {
                    color: isConnected ? '#00ff88' : '#ff3b30'
                  }
                }}
              />
              {isAnalyzing && (
                <Chip
                  label={isSpeechDetected ? 'VOICE DETECTED' : 'LISTENING...'}
                  className="jarvis-text-glow"
                  size="small"
                  icon={<MicIcon />}
                  sx={{
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    border: `1px solid ${isSpeechDetected ? '#ff9500' : '#00d4ff'}`,
                    color: isSpeechDetected ? '#ff9500' : '#00d4ff',
                    fontFamily: '"Orbitron", monospace',
                    '& .MuiChip-icon': {
                      color: isSpeechDetected ? '#ff9500' : '#00d4ff'
                    }
                  }}
                />
              )}
              {isSpeaking && (
                <Chip
                  label="JARVIS SPEAKING"
                  className="jarvis-text-glow"
                  size="small"
                  icon={<VolumeIcon />}
                  sx={{
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    border: '1px solid #00ff88',
                    color: '#00ff88',
                    fontFamily: '"Orbitron", monospace',
                    '& .MuiChip-icon': {
                      color: '#00ff88'
                    }
                  }}
                />
              )}
            </Box>

            <Typography 
              variant="caption" 
              className="jarvis-text-glow"
              sx={{ 
                color: '#00d4ff',
                fontFamily: '"Orbitron", monospace'
              }}
            >
              {messages.length - 1} EXCHANGES • SESSION {conversationId ? 'ACTIVE' : 'NEW'}
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Panneaux latéraux escamotables */}
      <Box
        sx={{
          position: 'fixed',
          top: 20,
          right: 20,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          zIndex: 20
        }}
      >
        <Tooltip title="CODE TOOLS">
          <Fab 
            size="small" 
            className="jarvis-button"
            sx={{
              backgroundColor: 'rgba(0, 212, 255, 0.1)',
              border: '2px solid #00d4ff',
              color: '#00d4ff',
              '&:hover': {
                backgroundColor: 'rgba(0, 212, 255, 0.2)',
                transform: 'scale(1.1)'
              }
            }}
          >
            <CodeIcon />
          </Fab>
        </Tooltip>
        <Tooltip title="MEMORY BANK">
          <Fab 
            size="small" 
            className="jarvis-button"
            sx={{
              backgroundColor: 'rgba(0, 255, 136, 0.1)',
              border: '2px solid #00ff88',
              color: '#00ff88',
              '&:hover': {
                backgroundColor: 'rgba(0, 255, 136, 0.2)',
                transform: 'scale(1.1)'
              }
            }}
          >
            <MemoryIcon />
          </Fab>
        </Tooltip>
        <Tooltip title="VISION MODULE">
          <Fab 
            size="small" 
            className="jarvis-button"
            sx={{
              backgroundColor: 'rgba(255, 107, 0, 0.1)',
              border: '2px solid #ff6b00',
              color: '#ff6b00',
              '&:hover': {
                backgroundColor: 'rgba(255, 107, 0, 0.2)',
                transform: 'scale(1.1)'
              }
            }}
          >
            <VisionIcon />
          </Fab>
        </Tooltip>
        <Tooltip title="SYSTEM CONFIG">
          <Fab 
            size="small" 
            className="jarvis-button"
            sx={{
              backgroundColor: 'rgba(0, 212, 255, 0.1)',
              border: '2px solid #00d4ff',
              color: '#00d4ff',
              '&:hover': {
                backgroundColor: 'rgba(0, 212, 255, 0.2)',
                transform: 'scale(1.1)'
              }
            }}
          >
            <SettingsIcon />
          </Fab>
        </Tooltip>
      </Box>

      {/* Enregistreur vocal (si activé) */}
      {showVoiceRecorder && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 120,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 30,
            backgroundColor: theme.palette.background.paper,
            borderRadius: 2,
            p: 2,
            boxShadow: theme.shadows[8],
            border: `1px solid ${theme.palette.divider}`
          }}
        >
          <VoiceRecorder
            onTranscription={handleVoiceTranscription}
            disabled={!isConnected}
          />
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={() => setShowVoiceRecorder(false)}
            >
              Annuler
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
}

export default MainChat;