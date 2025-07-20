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
      sx={{
        height: '100vh',
        width: '100vw',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'transparent',
        background: `radial-gradient(circle at center, ${theme.palette.primary.main}08 0%, transparent 70%)`,
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Zone de messages avec effet de fade */}
      <Box
        ref={chatContainerRef}
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
                  sx={{
                    p: 2,
                    backgroundColor: message.type === 'user' 
                      ? theme.palette.secondary.main + '90'
                      : message.status === 'error'
                      ? theme.palette.error.main + '90'
                      : theme.palette.background.paper + '90',
                    backdropFilter: 'blur(10px)',
                    borderRadius: 3,
                    border: `1px solid ${theme.palette.divider}40`,
                    boxShadow: theme.shadows[4]
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
                      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
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
                    <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                      JARVIS réfléchit...
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
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          p: 3,
          backgroundColor: theme.palette.background.paper + '95',
          backdropFilter: 'blur(20px)',
          borderTop: `1px solid ${theme.palette.divider}`,
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
              placeholder="Parlez ou tapez votre message à JARVIS..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={!isConnected || isTyping}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3,
                  backgroundColor: theme.palette.background.default + '50'
                }
              }}
            />
            
            {/* Bouton micro */}
            <Tooltip title={isAnalyzing ? 'Arrêter le microphone' : 'Activer le microphone'}>
              <IconButton
                onClick={toggleMicrophone}
                disabled={!isConnected}
                sx={{
                  backgroundColor: isAnalyzing 
                    ? theme.palette.success.main 
                    : theme.palette.action.hover,
                  color: isAnalyzing ? 'white' : theme.palette.text.primary,
                  '&:hover': {
                    backgroundColor: isAnalyzing 
                      ? theme.palette.success.dark 
                      : theme.palette.action.selected,
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
                sx={{
                  backgroundColor: theme.palette.primary.main,
                  color: theme.palette.primary.contrastText,
                  '&:hover': {
                    backgroundColor: theme.palette.primary.dark
                  },
                  '&:disabled': {
                    backgroundColor: theme.palette.action.disabled
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
                label={isConnected ? 'JARVIS En ligne' : 'JARVIS Hors ligne'}
                color={isConnected ? 'success' : 'error'}
                size="small"
                icon={<BotIcon />}
              />
              {isAnalyzing && (
                <Chip
                  label={isSpeechDetected ? 'Parole détectée' : 'Écoute...'}
                  color={isSpeechDetected ? 'warning' : 'info'}
                  size="small"
                  icon={<MicIcon />}
                />
              )}
              {isSpeaking && (
                <Chip
                  label="JARVIS parle"
                  color="secondary"
                  size="small"
                  icon={<VolumeIcon />}
                />
              )}
            </Box>

            <Typography variant="caption" color="text.secondary">
              {messages.length - 1} échanges • Conversation {conversationId ? 'active' : 'nouvelle'}
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
          gap: 1,
          zIndex: 20
        }}
      >
        <Tooltip title="Outils de développement">
          <Fab size="small" color="primary">
            <CodeIcon />
          </Fab>
        </Tooltip>
        <Tooltip title="Mémoire">
          <Fab size="small" color="secondary">
            <MemoryIcon />
          </Fab>
        </Tooltip>
        <Tooltip title="Vision">
          <Fab size="small" color="info">
            <VisionIcon />
          </Fab>
        </Tooltip>
        <Tooltip title="Paramètres">
          <Fab size="small" color="default">
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