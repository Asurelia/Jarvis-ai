/**
 * 🧠 JARVIS UI - Memory Viewer Component
 * Composant pour visualiser et gérer le système de mémoire JARVIS
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  Divider,
  IconButton,
  Tooltip,
  LinearProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Chat as ConversationIcon,
  Screenshot as ScreenshotIcon,
  Settings as PreferenceIcon,
  Code as CommandIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Delete as DeleteIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

import { useJarvis } from '../contexts/JarvisContext';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`memory-tabpanel-${index}`}
      aria-labelledby={`memory-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

function MemoryViewer() {
  const theme = useTheme();
  const { state, actions } = useJarvis();
  
  // États
  const [currentTab, setCurrentTab] = useState(0);
  const [conversations, setConversations] = useState([]);
  const [memoryStats, setMemoryStats] = useState({
    collections: 0,
    total_entries: 0,
    conversations: 0,
    commands: 0,
    screenshots: 0,
    preferences: 0
  });
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [showConversationDialog, setShowConversationDialog] = useState(false);

  useEffect(() => {
    loadMemoryData();
  }, []);

  const loadMemoryData = async () => {
    setIsLoading(true);
    try {
      // Charger les conversations
      await loadConversations();
      
      // Charger les statistiques
      await loadMemoryStats();
      
    } catch (error) {
      actions.addLog('error', `Erreur chargement mémoire: ${error.message}`, 'memory');
    } finally {
      setIsLoading(false);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/memory/conversations`);
      
      if (response.ok) {
        const result = await response.json();
        setConversations(result.conversations || []);
      } else {
        throw new Error(`Erreur API: ${response.status}`);
      }
    } catch (error) {
      actions.addLog('warning', `Conversations indisponibles: ${error.message}`, 'memory');
      setConversations([]);
    }
  };

  const loadMemoryStats = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/memory/stats`);
      
      if (response.ok) {
        const result = await response.json();
        setMemoryStats(result.stats || memoryStats);
      } else {
        throw new Error(`Erreur API: ${response.status}`);
      }
    } catch (error) {
      actions.addLog('warning', `Statistiques mémoire indisponibles: ${error.message}`, 'memory');
    }
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const viewConversation = (conversation) => {
    setSelectedConversation(conversation);
    setShowConversationDialog(true);
  };

  const filteredConversations = conversations.filter(conv =>
    !searchQuery || 
    conv.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleString('fr-FR');
    } catch {
      return dateString;
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MemoryIcon />
            Système de Mémoire JARVIS
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Actualiser les données">
              <IconButton onClick={loadMemoryData} size="small" disabled={isLoading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Statistiques globales */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Box sx={{ textAlign: 'center', minWidth: 80 }}>
            <Typography variant="h4" color="primary">
              {memoryStats.collections}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Collections
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center', minWidth: 80 }}>
            <Typography variant="h4" color="secondary">
              {memoryStats.total_entries}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Entrées totales
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center', minWidth: 80 }}>
            <Typography variant="h4" color="info.main">
              {memoryStats.conversations}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Conversations
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center', minWidth: 80 }}>
            <Typography variant="h4" color="success.main">
              {memoryStats.commands}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Commandes
            </Typography>
          </Box>
        </Box>

        {/* Barre de progression */}
        {isLoading && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
              Chargement des données mémoire...
            </Typography>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Onglets */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange}>
            <Tab 
              label="Conversations" 
              icon={<ConversationIcon />} 
              iconPosition="start"
            />
            <Tab 
              label="Commandes" 
              icon={<CommandIcon />} 
              iconPosition="start"
              disabled
            />
            <Tab 
              label="Captures" 
              icon={<ScreenshotIcon />} 
              iconPosition="start"
              disabled
            />
            <Tab 
              label="Préférences" 
              icon={<PreferenceIcon />} 
              iconPosition="start"
              disabled
            />
          </Tabs>
        </Box>

        {/* Panneau Conversations */}
        <TabPanel value={currentTab} index={0}>
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Rechercher dans les conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ color: 'text.secondary', mr: 1 }} />
              }}
            />
          </Box>

          {filteredConversations.length > 0 ? (
            <List>
              {filteredConversations.map((conversation, index) => (
                <ListItem
                  key={conversation.id || index}
                  button
                  onClick={() => viewConversation(conversation)}
                  sx={{
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 1,
                    mb: 1,
                    '&:hover': {
                      backgroundColor: theme.palette.action.hover,
                    }
                  }}
                >
                  <ListItemIcon>
                    <ConversationIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ flexGrow: 1 }}>
                          {conversation.summary || 'Conversation sans titre'}
                        </Typography>
                        <Chip
                          label={`${conversation.message_count} messages`}
                          size="small"
                          color="primary"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          ID: {conversation.id}
                        </Typography>
                        <br />
                        <Typography variant="caption" color="text.secondary">
                          Créée: {formatDate(conversation.created_at)}
                        </Typography>
                        {conversation.last_activity && (
                          <>
                            <br />
                            <Typography variant="caption" color="text.secondary">
                              Dernière activité: {formatDate(conversation.last_activity)}
                            </Typography>
                          </>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Alert severity={searchQuery ? "info" : "warning"}>
              {searchQuery 
                ? `Aucune conversation trouvée pour "${searchQuery}"`
                : "Aucune conversation enregistrée. Commencez à discuter avec JARVIS pour créer des conversations."
              }
            </Alert>
          )}
        </TabPanel>

        {/* Autres panneaux (à implémenter) */}
        <TabPanel value={currentTab} index={1}>
          <Alert severity="info">
            Historique des commandes - Fonctionnalité en développement
          </Alert>
        </TabPanel>

        <TabPanel value={currentTab} index={2}>
          <Alert severity="info">
            Captures d'écran archivées - Fonctionnalité en développement
          </Alert>
        </TabPanel>

        <TabPanel value={currentTab} index={3}>
          <Alert severity="info">
            Préférences utilisateur - Fonctionnalité en développement
          </Alert>
        </TabPanel>

        {/* Informations sur le système */}
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Système de mémoire :</strong> Utilise ChromaDB pour le stockage vectoriel<br />
            <strong>Collections :</strong> conversations, commandes, captures, préférences, contexte<br />
            <strong>Recherche :</strong> Recherche sémantique et par mots-clés disponible<br />
            <strong>Persistance :</strong> Toutes les données sont sauvegardées automatiquement
          </Typography>
        </Alert>
      </CardContent>

      {/* Dialog de conversation */}
      <Dialog
        open={showConversationDialog}
        onClose={() => setShowConversationDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ConversationIcon />
          Détails de la conversation
        </DialogTitle>
        <DialogContent>
          {selectedConversation && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {selectedConversation.summary}
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                <Chip 
                  label={`${selectedConversation.message_count} messages`}
                  color="primary"
                  icon={<ConversationIcon />}
                />
                <Chip 
                  label={selectedConversation.id}
                  color="default"
                  icon={<InfoIcon />}
                />
              </Box>

              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Informations temporelles:
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                <strong>Créée:</strong> {formatDate(selectedConversation.created_at)}
              </Typography>
              {selectedConversation.last_activity && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  <strong>Dernière activité:</strong> {formatDate(selectedConversation.last_activity)}
                </Typography>
              )}

              <Alert severity="info">
                Fonctionnalité de visualisation des messages en cours de développement.
                Utilisez l'interface de chat pour voir l'historique complet.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowConversationDialog(false)}>
            Fermer
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}

export default MemoryViewer; 