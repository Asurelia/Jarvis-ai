/**
 * 💬 JARVIS UI - Chat Button Component
 * Bouton flottant pour ouvrir/fermer la fenêtre de chat
 */
import React from 'react';
import {
  Fab,
  Badge,
  Tooltip,
  Box,
  Zoom
} from '@mui/material';
import {
  Chat as ChatIcon,
  Close as CloseIcon,
  SmartToy as BotIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

import { useJarvis } from '../contexts/JarvisContext';

function ChatButton({ 
  isOpen = false, 
  onClick, 
  hasNewMessages = false,
  messageCount = 0,
  bottom = 100,
  right = 20 
}) {
  const theme = useTheme();
  const { state } = useJarvis();

  const isConnected = state.jarvis.status === 'connected';

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: bottom,
        right: right,
        zIndex: 1200
      }}
    >
      <Zoom in={true} timeout={300}>
        <Tooltip 
          title={isOpen ? 'Fermer le chat' : 'Ouvrir le chat JARVIS'}
          placement="left"
        >
          <Badge
            badgeContent={hasNewMessages ? messageCount : 0}
            color="error"
            max={99}
            invisible={!hasNewMessages || isOpen}
          >
            <Fab
              color="primary"
              onClick={onClick}
              sx={{
                width: 60,
                height: 60,
                backgroundColor: isOpen 
                  ? theme.palette.error.main 
                  : theme.palette.primary.main,
                '&:hover': {
                  backgroundColor: isOpen 
                    ? theme.palette.error.dark 
                    : theme.palette.primary.dark,
                  transform: 'scale(1.1)'
                },
                transition: 'all 0.3s ease',
                boxShadow: theme.shadows[8],
                opacity: isConnected ? 1 : 0.7,
                '&:disabled': {
                  backgroundColor: theme.palette.action.disabled,
                  color: theme.palette.action.disabled
                }
              }}
              disabled={!isConnected}
            >
              {isOpen ? <CloseIcon /> : <BotIcon />}
            </Fab>
          </Badge>
        </Tooltip>
      </Zoom>

      {/* Indicateur de connexion */}
      <Box
        sx={{
          position: 'absolute',
          top: -2,
          right: -2,
          width: 16,
          height: 16,
          borderRadius: '50%',
          backgroundColor: isConnected 
            ? theme.palette.success.main 
            : theme.palette.error.main,
          border: `2px solid ${theme.palette.background.paper}`,
          boxShadow: theme.shadows[2]
        }}
      />
    </Box>
  );
}

export default ChatButton; 