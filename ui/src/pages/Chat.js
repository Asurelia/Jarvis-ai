/**
 * 💬 JARVIS UI - Chat Page
 * Page de chat plein écran pour JARVIS
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Divider,
  CircularProgress,
  Tooltip,
  Button,
  Grid,
  Paper,
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
  Refresh as RefreshIcon,
  History as HistoryIcon,
  Download as ExportIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

import { useJarvis } from '../contexts/JarvisContext';
import { useJarvisAPI } from '../hooks/useJarvisAPI';
import VoiceRecorder from '../components/VoiceRecorder';

function Chat() {
  const theme = useTheme();
  const { state, actions } = useJarvis();
  const { chatWithAI, speakText, isConnected, getConversations } = useJarvisAPI();
  
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
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  
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

  // Focus sur l'input au chargement
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
    loadConversations();
  }, []);

  // Charger l'historique des conversations
  const loadConversations = async () => {
    try {
      const result = await getConversations();
      if (result.success) {
        setConversations(result.conversations || []);
      }
    } catch (error) {
      console.error('Erreur chargement conversations:', error);
    }
  };

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
        
        // Incrémenter les stats
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
      content: 'Chat vidé. Nouvelle conversation démarrée. Comment puis-je vous aider ?',
      timestamp: new Date(),
      status: 'sent'
    }]);
    setConversationId(null);
    setMenuAnchor(null);
    actions.addNotification('info', 'Chat', 'Conversation réinitialisée');
  };

  // Exporter la conversation
  const exportChat = () => {
    const chatText = messages.map(msg => 
      `[${new Date(msg.timestamp).toLocaleString()}] ${msg.type === 'user' ? 'Vous' : 'JARVIS'}: ${msg.content}`
    ).join('\n\n');
    
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `jarvis-chat-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setMenuAnchor(null);
    actions.addNotification('success', 'Export', 'Conversation exportée');
  };

  // Formater l'heure
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Suggestions de commandes
  const quickCommands = [
    "Prends une capture d'écran",
    "Quelles applications sont ouvertes ?",
    "Aide-moi à organiser mon bureau",
    "Explique-moi comment tu fonctionnes",
    "Quelles sont tes capacités ?",
    "Peux-tu analyser ce que je vois à l'écran ?"
  ];

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Chat JARVIS
      </Typography>
      
      <Grid container spacing={3} sx={{ height: 'calc(100vh - 200px)' }}>
        {/* Panneau principal du chat */}
        <Grid item xs={12} md={9}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* En-tête du chat */}
            <CardContent sx={{ pb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                    <BotIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">
                      Assistant JARVIS
                    </Typography>
                    <Chip
                      label={isConnected ? 'En ligne' : 'Hors ligne'}
                      size="small"
                      color={isConnected ? 'success' : 'error'}
                    />
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    {messages.length - 1} messages
                  </Typography>
                  <IconButton
                    size="small"
                    onClick={(e) => setMenuAnchor(e.currentTarget)}
                  >
                    <MoreIcon />
                  </IconButton>
                </Box>
              </Box>

              {/* Menu contextuel */}
              <Menu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={() => setMenuAnchor(null)}
                TransitionComponent={Fade}
              >
                <MenuItem onClick={() => { loadConversations(); setMenuAnchor(null); }}>
                  <RefreshIcon sx={{ mr: 1 }} />
                  Actualiser
                </MenuItem>
                <MenuItem onClick={exportChat}>
                  <ExportIcon sx={{ mr: 1 }} />
                  Exporter
                </MenuItem>
                <MenuItem onClick={clearChat}>
                  <ClearIcon sx={{ mr: 1 }} />
                  Nouvelle conversation
                </MenuItem>
              </Menu>
            </CardContent>

            <Divider />

            {/* Zone des messages */}
            <Box
              sx={{
                flex: 1,
                overflow: 'auto',
                p: 2,
                backgroundColor: theme.palette.background.default
              }}
            >
              {messages.map((message) => (
                <Box
                  key={message.id}
                  sx={{
                    mb: 3,
                    display: 'flex',
                    flexDirection: message.type === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                    gap: 2
                  }}
                >
                  {/* Avatar */}
                  <Avatar
                    sx={{
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
                      p: 2,
                      maxWidth: '70%',
                      backgroundColor: message.type === 'user' 
                        ? theme.palette.secondary.light
                        : message.status === 'error'
                        ? theme.palette.error.light
                        : theme.palette.background.paper,
                      borderRadius: 2,
                      position: 'relative',
                      '&:hover .message-actions': {
                        opacity: 1
                      }
                    }}
                  >
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
                      {message.content}
                    </Typography>
                    
                    {/* Indicateurs */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
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

                    {/* Actions du message */}
                    <Box
                      className="message-actions"
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: message.type === 'user' ? 'auto' : 8,
                        left: message.type === 'user' ? 8 : 'auto',
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
                            <VolumeIcon sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Copier">
                        <IconButton
                          size="small"
                          onClick={() => copyMessage(message.content)}
                        >
                          <CopyIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Paper>
                </Box>
              ))}

              {/* Indicateur de frappe */}
              {isTyping && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                    <BotIcon />
                  </Avatar>
                  <Paper sx={{ p: 2, borderRadius: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CircularProgress size={20} />
                      <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
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
              <>
                <Divider />
                <Box sx={{ p: 2 }}>
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
              </>
            )}

            <Divider />

            {/* Zone de saisie */}
            <CardContent>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end', mb: 2 }}>
                <TextField
                  ref={inputRef}
                  fullWidth
                  multiline
                  maxRows={4}
                  placeholder="Tapez votre message ou question..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={!isConnected || isTyping}
                  variant="outlined"
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
                        : theme.palette.text.secondary,
                      backgroundColor: showVoiceRecorder 
                        ? theme.palette.primary.light + '20' 
                        : 'transparent'
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
                        backgroundColor: theme.palette.action.disabled
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
                  textAlign: 'center',
                  color: theme.palette.text.secondary
                }}
              >
                {!isConnected 
                  ? '⚠️ JARVIS hors ligne - Vérifiez la connexion'
                  : conversationId 
                  ? `✅ Conversation active • ${messages.length - 1} échanges`
                  : '🆕 Nouvelle conversation'
                }
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Panneau latéral */}
        <Grid item xs={12} md={3}>
          {/* Suggestions rapides */}
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                💡 Suggestions
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {quickCommands.map((command, index) => (
                  <Button
                    key={index}
                    variant="outlined"
                    size="small"
                    onClick={() => sendMessage(command)}
                    disabled={!isConnected || isTyping}
                    sx={{ 
                      textAlign: 'left', 
                      justifyContent: 'flex-start',
                      textTransform: 'none',
                      fontSize: '0.8rem'
                    }}
                  >
                    {command}
                  </Button>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Historique des conversations */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <HistoryIcon />
                Historique
              </Typography>
              
              {conversations.length > 0 ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {conversations.slice(0, 5).map((conv) => (
                    <Paper
                      key={conv.id}
                      sx={{
                        p: 1,
                        cursor: 'pointer',
                        '&:hover': {
                          backgroundColor: theme.palette.action.hover
                        }
                      }}
                      onClick={() => {
                        // TODO: Charger la conversation
                        actions.addNotification('info', 'Historique', 'Chargement des conversations à venir');
                      }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {conv.summary}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {conv.message_count} messages • {new Date(conv.created_at).toLocaleDateString()}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Aucune conversation précédente
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Chat; 