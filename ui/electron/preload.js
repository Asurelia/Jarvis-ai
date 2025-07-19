/**
 * 🤖 JARVIS - Preload Script
 * Bridge sécurisé entre Electron et React
 */
const { contextBridge, ipcRenderer } = require('electron');

// API exposée au processus de rendu
const electronAPI = {
  // === Informations sur l'application ===
  getAppVersion: () => ipcRenderer.invoke('app-version'),
  
  // === Gestion de JARVIS ===
  getJarvisStatus: () => ipcRenderer.invoke('get-jarvis-status'),
  startJarvis: () => ipcRenderer.invoke('start-jarvis'),
  stopJarvis: () => ipcRenderer.invoke('stop-jarvis'),
  executeJarvisCommand: (command) => ipcRenderer.invoke('execute-jarvis-command', command),
  
  // === Dialogues système ===
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  
  // === Événements depuis le main process ===
  onJarvisStarted: (callback) => ipcRenderer.on('jarvis-started', callback),
  onJarvisStopped: (callback) => ipcRenderer.on('jarvis-stopped', callback),
  onJarvisOutput: (callback) => ipcRenderer.on('jarvis-output', callback),
  onJarvisError: (callback) => ipcRenderer.on('jarvis-error', callback),
  
  // === Commandes depuis le menu ===
  onNewSession: (callback) => ipcRenderer.on('new-session', callback),
  onLoadConfig: (callback) => ipcRenderer.on('load-config', callback),
  onToggleVoiceMode: (callback) => ipcRenderer.on('toggle-voice-mode', callback),
  onToggleAutocomplete: (callback) => ipcRenderer.on('toggle-autocomplete', callback),
  onTakeScreenshot: (callback) => ipcRenderer.on('take-screenshot', callback),
  
  // === Nettoyage des événements ===
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),
  
  // === Utilitaires ===
  platform: process.platform,
  versions: process.versions
};

// === Logs pour debugging ===
const logAPI = {
  info: (message) => console.log(`[JARVIS-UI] ${message}`),
  warn: (message) => console.warn(`[JARVIS-UI] ${message}`),
  error: (message) => console.error(`[JARVIS-UI] ${message}`),
  debug: (message) => {
    if (process.env.NODE_ENV === 'development') {
      console.debug(`[JARVIS-UI] ${message}`);
    }
  }
};

// === Exposition sécurisée des APIs ===
contextBridge.exposeInMainWorld('electronAPI', electronAPI);
contextBridge.exposeInMainWorld('logAPI', logAPI);

// === Informations de démarrage ===
window.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 JARVIS UI Preload script loaded');
  console.log('📦 Electron version:', process.versions.electron);
  console.log('🌐 Chrome version:', process.versions.chrome);
  console.log('🟢 Node version:', process.versions.node);
});