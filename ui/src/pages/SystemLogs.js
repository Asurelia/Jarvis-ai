/**
 * 🤖 JARVIS UI - System Logs
 * Interface pour visualiser les logs système
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon
} from '@mui/icons-material';

import { useJarvis } from '../contexts/JarvisContext';

function SystemLogs() {
  const { state, actions } = useJarvis();
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');
  const [sourceFilter, setSourceFilter] = useState('all');
  
  // Filtrer les logs
  const filteredLogs = state.logs.filter(log => {
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLevel = levelFilter === 'all' || log.level === levelFilter;
    const matchesSource = sourceFilter === 'all' || log.source === sourceFilter;
    
    return matchesSearch && matchesLevel && matchesSource;
  });
  
  // Obtenir les sources uniques
  const uniqueSources = [...new Set(state.logs.map(log => log.source))];
  
  // Couleur selon le niveau
  const getLevelColor = (level) => {
    switch (level) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'success':
        return 'success';
      default:
        return 'info';
    }
  };
  
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Logs Système
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Actualiser">
            <IconButton onClick={() => window.location.reload()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Exporter">
            <IconButton disabled>
              <ExportIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<ClearIcon />}
            onClick={actions.clearLogs}
            size="small"
          >
            Vider
          </Button>
        </Box>
      </Box>
      
      {/* Filtres */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              size="small"
              placeholder="Rechercher dans les logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
              sx={{ flex: 1, minWidth: 200 }}
            />
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Niveau</InputLabel>
              <Select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                label="Niveau"
              >
                <MenuItem value="all">Tous</MenuItem>
                <MenuItem value="info">Info</MenuItem>
                <MenuItem value="success">Succès</MenuItem>
                <MenuItem value="warning">Warning</MenuItem>
                <MenuItem value="error">Erreur</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Source</InputLabel>
              <Select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                label="Source"
              >
                <MenuItem value="all">Toutes</MenuItem>
                {uniqueSources.map(source => (
                  <MenuItem key={source} value={source}>{source}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>
      
      {/* Liste des logs */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Logs ({filteredLogs.length})
          </Typography>
          
          <Box sx={{ maxHeight: 600, overflow: 'auto' }}>
            {filteredLogs.length > 0 ? (
              filteredLogs.map((log) => (
                <Box
                  key={log.id}
                  sx={{
                    mb: 2,
                    p: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    backgroundColor: 'background.paper'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                      {formatTime(log.timestamp)}
                    </Typography>
                    <Chip
                      label={log.level}
                      size="small"
                      color={getLevelColor(log.level)}
                      variant="outlined"
                    />
                    <Chip
                      label={log.source}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    {log.message}
                  </Typography>
                </Box>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                {searchTerm || levelFilter !== 'all' || sourceFilter !== 'all' 
                  ? 'Aucun log correspondant aux filtres'
                  : 'Aucun log disponible'
                }
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default SystemLogs;