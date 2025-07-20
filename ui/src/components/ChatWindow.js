/**
 * 💬 JARVIS UI - Chat Window Component
 * Fenêtre de chat moderne pour communiquer avec JARVIS
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Divider,
  CircularProgress,
  Tooltip,
  Menu,
  MenuItem,
  Fade
} from '@mui/material';
import {
  Send as SendIcon,
  Mic as MicIcon,
  SmartToy as BotIcon,
  Person as UserIcon,
  MoreVert as MoreIcon,
  Clear as ClearIcon,
  VolumeUp as VolumeIcon,
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

import { useJarvis } from '../contexts/JarvisContext';
import { useJarvisAPI } from '../hooks/useJarvisAPI';
import VoiceRecorder from './VoiceRecorder';

function ChatWindow({ isOpen = true, onClose, height = 600, width = 400 }) {
  const theme = useTheme();
  const { state, actions } = useJarvis();
  const { chatWithAI, speakText, isConnected } = useJarvisAPI();
  
  // États du chat
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      type: 'bot',
      content: 'Bonjour ! Je suis JARVIS, votre assistant IA. Comment puis-je vous aider ?',
      timestamp: new Date(),
      status: 'sent'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  
  // Refs
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const [menuAnchor, setMenuAnchor] = useState(null);

  // Auto-scroll vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus sur l'input quand la fenêtre s'ouvre
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

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
        
        // Log dans JARVIS
        actions.addLog('success', `Chat: ${content} -> ${response.response.substring(0, 50)}...`, 'chat');
      } else {
        throw new Error(response.error || 'Réponse invalide');
      }
    } catch (error) {
      // Message d'erreur
      const errorMessage = {
        id: Date.now() + '_error',
        type: 'bot',
        content: `Désolé, je rencontre un problème : ${error.message}`,
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

  // Lire un message à voix haute
  const speakMessage = async (content) => {
    try {
      await speakText(content);
    } catch (error) {
      actions.addNotification('error', 'Synthèse vocale', error.message);
    }
  };

  // Copier un message
  const copyMessage = (content) => {
    navigator.clipboard.writeText(content);
    actions.addNotification('success', 'Copié', 'Message copié dans le presse-papiers');
  };

  // Vider le chat
  const clearChat = () => {
    setMessages([{
      id: 'welcome_new',
      type: 'bot',
      content: 'Chat vidé. Comment puis-je vous aider ?',
      timestamp: new Date(),
      status: 'sent'
    }]);
    setConversationId(null);
    setMenuAnchor(null);
  };

  // Recharger la conversation
  const refreshChat = () => {
    actions.addNotification('info', 'Chat', 'Conversation actualisée');
    setMenuAnchor(null);
  };

  // Formater l'heure
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Style de la fenêtre de chat
  const chatWindowStyle = {
    position: 'fixed',
    bottom: 20,
    right: 20,
    width: width,
    height: height,
    zIndex: 1300,
    display: isOpen ? 'flex' : 'none',
    flexDirection: 'column',
    backgroundColor: theme.palette.background.paper,
    border: `1px solid ${theme.palette.divider}`,
    borderRadius: 2,
    boxShadow: theme.shadows[12],
    overflow: 'hidden'
  };

  if (!isOpen) return null;

  return (
    <Paper sx={chatWindowStyle}>
      {/* En-tête du chat */}
      <Box
        sx={{
          p: 2,
          backgroundColor: theme.palette.primary.main,
          color: theme.palette.primary.contrastText,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar sx={{ width: 32, height: 32, bgcolor: theme.palette.primary.dark }}>
            <BotIcon />
          </Avatar>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              JARVIS Chat
            </Typography>
            <Chip
              label={isConnected ? 'En ligne' : 'Hors ligne'}
              size="small"
              sx={{
                height: 16,
                fontSize: '0.6rem',
                backgroundColor: isConnected 
                  ? theme.palette.success.main 
                  : theme.palette.error.main,
                color: 'white'
              }}
            />
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton
            size="small"
            onClick={(e) => setMenuAnchor(e.currentTarget)}
            sx={{ color: 'inherit' }}
          >
            <MoreIcon />
          </IconButton>
          {onClose && (
            <IconButton
              size="small"
              onClick={onClose}
              sx={{ color: 'inherit', ml: 1 }}
            >
              ✕
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Menu contextuel */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
        TransitionComponent={Fade}
      >
        <MenuItem onClick={refreshChat}>
          <RefreshIcon sx={{ mr: 1 }} />
          Actualiser
        </MenuItem>
        <MenuItem onClick={clearChat}>
          <ClearIcon sx={{ mr: 1 }} />
          Vider le chat
        </MenuItem>
      </Menu>

      {/* Zone des messages */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 1,
          backgroundColor: theme.palette.background.default
        }}
      >
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              mb: 2,
              display: 'flex',
              flexDirection: message.type === 'user' ? 'row-reverse' : 'row',
              alignItems: 'flex-start',
              gap: 1
            }}
          >
            {/* Avatar */}
            <Avatar
              sx={{
                width: 28,
                height: 28,
                bgcolor: message.type === 'user' 
                  ? theme.palette.secondary.main 
                  : message.status === 'error'
                  ? theme.palette.error.main
                  : theme.palette.primary.main
              }}
            >
              {message.type === 'user' ? <UserIcon /> : <BotIcon />}
            </Avatar>

            {/* Bulle de message */}
            <Paper
              sx={{
                p: 1.5,
                maxWidth: '75%',
                backgroundColor: message.type === 'user' 
                  ? theme.palette.secondary.main
                  : message.status === 'error'
                  ? theme.palette.error.light
                  : theme.palette.background.paper,
                color: message.type === 'user' 
                  ? theme.palette.secondary.contrastText
                  : message.status === 'error'
                  ? theme.palette.error.contrastText
                  : theme.palette.text.primary,
                borderRadius: 2,
                position: 'relative',
                '&:hover .message-actions': {
                  opacity: 1
                }
              }}
            >
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {message.content}
              </Typography>
              
              {/* Indicateur vocal */}
              {message.isVoice && (
                <Chip
                  icon={<MicIcon />}
                  label="Vocal"
                  size="small"
                  sx={{ 
                    mt: 0.5,
                    height: 20,
                    fontSize: '0.6rem'
                  }}
                />
              )}

              {/* Timestamp */}
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  mt: 0.5,
                  opacity: 0.7,
                  fontSize: '0.65rem'
                }}
              >
                {formatTime(message.timestamp)}
              </Typography>

              {/* Actions du message */}
              <Box
                className="message-actions"
                sx={{
                  position: 'absolute',
                  top: -8,
                  right: message.type === 'user' ? 'auto' : -8,
                  left: message.type === 'user' ? -8 : 'auto',
                  display: 'flex',
                  gap: 0.5,
                  opacity: 0,
                  transition: 'opacity 0.2s',
                  backgroundColor: theme.palette.background.paper,
                  borderRadius: 1,
                  p: 0.5,
                  boxShadow: theme.shadows[2]
                }}
              >
                {message.type === 'bot' && (
                  <Tooltip title="Lire à voix haute">
                    <IconButton
                      size="small"
                      onClick={() => speakMessage(message.content)}
                      disabled={!isConnected}
                    >
                      <VolumeIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Tooltip>
                )}
                <Tooltip title="Copier">
                  <IconButton
                    size="small"
                    onClick={() => copyMessage(message.content)}
                  >
                    <CopyIcon sx={{ fontSize: 14 }} />
                  </IconButton>
                </Tooltip>
              </Box>
            </Paper>
          </Box>
        ))}

        {/* Indicateur de frappe */}
        {isTyping && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Avatar sx={{ width: 28, height: 28, bgcolor: theme.palette.primary.main }}>
              <BotIcon />
            </Avatar>
            <Paper sx={{ p: 1.5, borderRadius: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={16} />
                <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                  JARVIS réfléchit...
                </Typography>
              </Box>
            </Paper>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Enregistreur vocal (si activé) */}
      {showVoiceRecorder && (
        <Box sx={{ p: 2, backgroundColor: theme.palette.background.default }}>
          <VoiceRecorder
            onTranscription={handleVoiceTranscription}
            disabled={!isConnected}
          />
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
            <IconButton
              size="small"
              onClick={() => setShowVoiceRecorder(false)}
              sx={{ color: theme.palette.text.secondary }}
            >
              ✕
            </IconButton>
          </Box>
        </Box>
      )}

      <Divider />

      {/* Zone de saisie */}
      <Box sx={{ p: 2, backgroundColor: theme.palette.background.paper }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={3}
            placeholder="Tapez votre message..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={!isConnected || isTyping}
            variant="outlined"
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2
              }
            }}
          />
          
          {/* Bouton micro */}
          <Tooltip title="Message vocal">
            <IconButton
              onClick={() => setShowVoiceRecorder(!showVoiceRecorder)}
              disabled={!isConnected}
              sx={{
                color: showVoiceRecorder 
                  ? theme.palette.primary.main 
                  : theme.palette.text.secondary
              }}
            >
              <MicIcon />
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
                  backgroundColor: theme.palette.action.disabled,
                  color: theme.palette.action.disabled
                }
              }}
            >
              <SendIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Indicateur de statut */}
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            mt: 1,
            textAlign: 'center',
            color: theme.palette.text.secondary
          }}
        >
          {!isConnected 
            ? 'JARVIS hors ligne - Reconnexion...'
            : conversationId 
            ? `Conversation active (${messages.length - 1} messages)`
            : 'Nouvelle conversation'
          }
        </Typography>
      </Box>
    </Paper>
  );
}

export default ChatWindow; 