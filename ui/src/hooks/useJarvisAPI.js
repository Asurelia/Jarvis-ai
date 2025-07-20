/**
 * 🔌 Hook personnalisé pour l'API JARVIS
 * Simplifie les appels API et gère les états de chargement/erreur
 */
import { useState, useCallback } from 'react';
import { useJarvis } from '../contexts/JarvisContext';

export function useJarvisAPI() {
  const { apiService, actions, state } = useJarvis();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Wrapper générique pour les appels API
  const apiCall = useCallback(async (apiFunction, ...args) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiFunction(...args);
      
      // Log de succès si nécessaire
      if (result.success !== false) {
        actions.addLog('info', `API call successful`, 'api');
      }
      
      return result;
    } catch (err) {
      const errorMessage = err.message || 'Unknown API error';
      setError(errorMessage);
      actions.addLog('error', `API error: ${errorMessage}`, 'api');
      actions.addNotification('error', 'API Error', errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiService, actions]);

  // Commandes JARVIS
  const executeCommand = useCallback(async (command, mode = 'auto') => {
    actions.addLog('info', `Executing command: ${command}`, 'ui');
    actions.setLoading(true);
    
    try {
      const result = await apiCall(apiService.executeCommand, command, mode);
      
      if (result.success) {
        actions.addNotification('success', 'Command Executed', 
          `${result.actions_count} actions planned`);
        actions.incrementStat('commandsExecuted');
      }
      
      return result;
    } finally {
      actions.setLoading(false);
    }
  }, [apiCall, apiService.executeCommand, actions]);

  // Chat avec l'IA
  const chatWithAI = useCallback(async (message, conversationId = null) => {
    actions.addLog('info', `Chatting: ${message.substring(0, 50)}...`, 'ui');
    
    const result = await apiCall(apiService.chatWithAI, message, conversationId);
    
    if (result.success) {
      actions.addLog('success', `AI responded`, 'jarvis');
    }
    
    return result;
  }, [apiCall, apiService.chatWithAI, actions]);

  // Synthèse vocale
  const speakText = useCallback(async (text, voice = null) => {
    actions.addLog('info', `Speaking: ${text.substring(0, 30)}...`, 'ui');
    
    const result = await apiCall(apiService.speakText, text, voice);
    
    if (result.success) {
      actions.incrementStat('voiceCommands');
      actions.addNotification('success', 'Speech', 'Text spoken successfully');
    }
    
    return result;
  }, [apiCall, apiService.speakText, actions]);

  // Capture d'écran
  const takeScreenshot = useCallback(async () => {
    actions.addLog('info', 'Taking screenshot...', 'ui');
    
    const result = await apiCall(apiService.takeScreenshot);
    
    if (result.success) {
      actions.incrementStat('screenshotsTaken');
      actions.addNotification('success', 'Screenshot', 
        `Saved as ${result.filename}`);
    }
    
    return result;
  }, [apiCall, apiService.takeScreenshot, actions]);

  // Applications en cours
  const getRunningApps = useCallback(async () => {
    const result = await apiCall(apiService.getRunningApps);
    
    if (result.success) {
      actions.addLog('info', `Found ${result.apps.length} running applications`, 'jarvis');
    }
    
    return result;
  }, [apiCall, apiService.getRunningApps, actions]);

  // Statut système
  const refreshSystemStatus = useCallback(async () => {
    const result = await apiCall(apiService.getSystemStatus);
    
    if (result) {
      // Mettre à jour les modules
      const moduleStatus = {};
      result.modules.forEach(module => {
        moduleStatus[module.name] = {
          status: module.status,
          lastActivity: module.last_update
        };
      });
      actions.updateAllModules(moduleStatus);
      
      // Mettre à jour les stats
      if (result.performance) {
        actions.updateStats({
          commandsExecuted: result.performance.modules_loaded || 0
        });
      }
      
      actions.addLog('info', 'System status refreshed', 'api');
    }
    
    return result;
  }, [apiCall, apiService.getSystemStatus, actions]);

  // Conversations mémoire
  const getConversations = useCallback(async () => {
    const result = await apiCall(apiService.getConversations);
    
    if (result.success) {
      actions.addLog('info', `Found ${result.conversations.length} conversations`, 'jarvis');
      actions.updateStats({
        memoryEntries: result.total_count
      });
    }
    
    return result;
  }, [apiCall, apiService.getConversations, actions]);

  // Health check
  const checkAPIHealth = useCallback(async () => {
    try {
      const isHealthy = await apiService.checkHealth();
      
      if (isHealthy) {
        actions.addLog('success', 'API server is healthy', 'api');
        actions.setJarvisStatus('connected');
      } else {
        actions.addLog('error', 'API server is unhealthy', 'api');
        actions.setJarvisStatus('error');
      }
      
      return isHealthy;
    } catch (err) {
      const errorMessage = err.message || 'Health check failed';
      actions.addLog('error', `Health check failed: ${errorMessage}`, 'api');
      actions.setJarvisStatus('error');
      throw err;
    }
  }, [apiService.checkHealth, actions]);

  // Commandes rapides
  const quickCommands = {
    screenshot: () => takeScreenshot(),
    analyze: () => executeCommand('analyze current screen'),
    apps: () => getRunningApps(),
    status: () => refreshSystemStatus(),
    health: () => checkAPIHealth()
  };

  return {
    // États
    loading,
    error,
    isConnected: state.jarvis.status === 'connected',
    
    // Méthodes principales
    executeCommand,
    chatWithAI,
    speakText,
    takeScreenshot,
    getRunningApps,
    refreshSystemStatus,
    getConversations,
    checkAPIHealth,
    
    // Commandes rapides
    quickCommands,
    
    // Utilitaires
    clearError: () => setError(null),
    apiCall // Pour des appels personnalisés
  };
}

// Hook spécialisé pour les commandes vocales
export function useVoiceCommands() {
  const { speakText, executeCommand } = useJarvisAPI();
  const { actions } = useJarvis();

  const speakAndExecute = useCallback(async (command, confirmationText = null) => {
    try {
      // Optionnel: confirmer vocalement la commande
      if (confirmationText) {
        await speakText(confirmationText);
      }
      
      // Exécuter la commande
      const result = await executeCommand(command);
      
      // Annoncer le résultat
      if (result.success) {
        await speakText(`Command executed successfully. ${result.actions_count} actions completed.`);
      } else {
        await speakText('Command execution failed.');
      }
      
      return result;
    } catch (error) {
      await speakText('An error occurred while executing the command.');
      throw error;
    }
  }, [speakText, executeCommand]);

  const announceStatus = useCallback(async () => {
    const statusText = `JARVIS interface is ready`;
    await speakText(statusText);
  }, [speakText]);

  return {
    speakAndExecute,
    announceStatus,
    speak: speakText
  };
}

// Hook pour la gestion des erreurs globales
export function useErrorHandler() {
  const { actions } = useJarvis();

  const handleError = useCallback((error, context = 'Unknown') => {
    const errorMessage = error.message || error.toString();
    
    actions.addLog('error', `${context}: ${errorMessage}`, 'error');
    actions.addNotification('error', 'Error', errorMessage);
    actions.setError(errorMessage);
    
    console.error(`JARVIS Error [${context}]:`, error);
  }, [actions]);

  const handleAPIError = useCallback((error, endpoint) => {
    handleError(error, `API ${endpoint}`);
  }, [handleError]);

  const clearError = useCallback(() => {
    actions.clearError();
  }, [actions]);

  return {
    handleError,
    handleAPIError,
    clearError
  };
}