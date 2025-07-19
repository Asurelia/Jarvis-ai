/**
 * 🤖 JARVIS UI - Notification System
 * Système de notifications toast moderne
 */
import React from 'react';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Box,
  IconButton,
  useTheme,
  alpha
} from '@mui/material';
import {
  Close as CloseIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon
} from '@mui/icons-material';

import { useJarvis } from '../../contexts/JarvisContext';

// Configuration des types de notifications
const notificationConfig = {
  success: {
    icon: SuccessIcon,
    color: 'success',
    defaultDuration: 4000
  },
  error: {
    icon: ErrorIcon,
    color: 'error',
    defaultDuration: 8000
  },
  warning: {
    icon: WarningIcon,
    color: 'warning',
    defaultDuration: 6000
  },
  info: {
    icon: InfoIcon,
    color: 'info',
    defaultDuration: 5000
  }
};

function NotificationItem({ notification, onClose }) {
  const theme = useTheme();
  const config = notificationConfig[notification.type] || notificationConfig.info;
  const IconComponent = config.icon;
  
  return (
    <Alert
      severity={notification.type}
      variant="filled"
      onClose={() => onClose(notification.id)}
      sx={{
        minWidth: 300,
        maxWidth: 500,
        marginBottom: 1,
        backgroundColor: alpha(theme.palette[config.color].main, 0.9),
        backdropFilter: 'blur(10px)',
        border: `1px solid ${alpha(theme.palette[config.color].main, 0.3)}`,
        borderRadius: 2,
        boxShadow: theme.shadows[8],
        '& .MuiAlert-icon': {
          fontSize: '1.2rem'
        },
        '& .MuiAlert-message': {
          flex: 1
        },
        '& .MuiAlert-action': {
          paddingLeft: 1
        }
      }}
      action={
        <IconButton
          size="small"
          onClick={() => onClose(notification.id)}
          sx={{
            color: 'inherit',
            opacity: 0.8,
            '&:hover': {
              opacity: 1,
              backgroundColor: alpha(theme.palette.common.white, 0.1)
            }
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      }
    >
      {notification.title && (
        <AlertTitle sx={{ fontWeight: 600, marginBottom: 0.5 }}>
          {notification.title}
        </AlertTitle>
      )}
      {notification.message}
    </Alert>
  );
}

function NotificationSystem() {
  const theme = useTheme();
  const { state, actions } = useJarvis();
  
  // Style du container des notifications
  const containerStyle = {
    position: 'fixed',
    top: 80, // Sous la top bar
    right: 20,
    zIndex: 2000,
    maxHeight: 'calc(100vh - 100px)',
    overflow: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: 1,
    
    // Scrollbar personnalisée
    '&::-webkit-scrollbar': {
      width: '4px'
    },
    '&::-webkit-scrollbar-track': {
      background: 'transparent'
    },
    '&::-webkit-scrollbar-thumb': {
      background: alpha(theme.palette.text.secondary, 0.3),
      borderRadius: '2px'
    }
  };
  
  // Gestionnaire de fermeture
  const handleClose = (notificationId) => {
    actions.removeNotification(notificationId);
  };
  
  // Auto-hide des notifications
  React.useEffect(() => {
    state.ui.notifications.forEach(notification => {
      if (notification.autoHide !== false) {
        const timer = setTimeout(() => {
          actions.removeNotification(notification.id);
        }, notification.duration || notificationConfig[notification.type]?.defaultDuration || 5000);
        
        return () => clearTimeout(timer);
      }
    });
  }, [state.ui.notifications, actions]);
  
  if (state.ui.notifications.length === 0) {
    return null;
  }
  
  return (
    <Box sx={containerStyle}>
      {state.ui.notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClose={handleClose}
        />
      ))}
    </Box>
  );
}

export default NotificationSystem;