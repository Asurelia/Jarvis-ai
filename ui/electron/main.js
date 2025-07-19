/**
 * 🤖 JARVIS - Main Electron Process
 * Interface moderne pour l'assistant IA autonome
 */
const { app, BrowserWindow, Menu, ipcMain, screen, dialog, shell } = require('electron');
const path = require('path');
const isDev = require('./isDev');
const { spawn } = require('child_process');

// Variables globales
let mainWindow = null;
let jarvisProcess = null;
let tray = null;

// Configuration de l'application
const APP_CONFIG = {
  name: 'JARVIS Assistant',
  version: '1.0.0',
  width: 1200,
  height: 800,
  minWidth: 900,
  minHeight: 600
};

/**
 * Crée la fenêtre principale
 */
function createMainWindow() {
  // Obtenir les dimensions de l'écran
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  
  // Créer la fenêtre
  mainWindow = new BrowserWindow({
    width: APP_CONFIG.width,
    height: APP_CONFIG.height,
    minWidth: APP_CONFIG.minWidth,
    minHeight: APP_CONFIG.minHeight,
    x: Math.floor((width - APP_CONFIG.width) / 2),
    y: Math.floor((height - APP_CONFIG.height) / 2),
    
    // Apparence moderne
    titleBarStyle: 'hiddenInset',
    frame: process.platform !== 'win32',
    vibrancy: 'ultra-dark', // macOS
    
    // Sécurité
    webSecurity: true,
    nodeIntegration: false,
    contextIsolation: true,
    enableRemoteModule: false,
    
    // Configuration web
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      allowRunningInsecureContent: false
    },
    
    // Icône
    icon: path.join(__dirname, '../assets/icon.png'),
    
    // Affichage
    show: false, // Afficher après le chargement
    backgroundColor: '#1a1a1a',
    darkTheme: true
  });

  // URL de chargement
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../build/index.html')}`;
  
  mainWindow.loadURL(startUrl);
  
  // DevTools en développement
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
  
  // Événements de la fenêtre
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Focus
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });
  
  mainWindow.on('closed', () => {
    mainWindow = null;
    // Arrêter JARVIS si nécessaire
    if (jarvisProcess) {
      jarvisProcess.kill();
      jarvisProcess = null;
    }
  });
  
  // Gérer les liens externes
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
  
  // Menu de l'application
  createApplicationMenu();
}

/**
 * Crée le menu de l'application
 */
function createApplicationMenu() {
  const template = [
    {
      label: 'Fichier',
      submenu: [
        {
          label: 'Nouvelle session',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('new-session');
          }
        },
        {
          label: 'Ouvrir configuration',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            const result = await dialog.showOpenDialog(mainWindow, {
              properties: ['openFile'],
              filters: [
                { name: 'JSON', extensions: ['json'] },
                { name: 'Tous les fichiers', extensions: ['*'] }
              ]
            });
            
            if (!result.canceled) {
              mainWindow.webContents.send('load-config', result.filePaths[0]);
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Quitter',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Édition',
      submenu: [
        { label: 'Annuler', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
        { label: 'Rétablir', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
        { type: 'separator' },
        { label: 'Couper', accelerator: 'CmdOrCtrl+X', role: 'cut' },
        { label: 'Copier', accelerator: 'CmdOrCtrl+C', role: 'copy' },
        { label: 'Coller', accelerator: 'CmdOrCtrl+V', role: 'paste' }
      ]
    },
    {
      label: 'JARVIS',
      submenu: [
        {
          label: 'Démarrer JARVIS',
          accelerator: 'CmdOrCtrl+J',
          click: () => {
            startJarvisProcess();
          }
        },
        {
          label: 'Arrêter JARVIS',
          accelerator: 'CmdOrCtrl+Shift+J',
          click: () => {
            stopJarvisProcess();
          }
        },
        { type: 'separator' },
        {
          label: 'Mode vocal',
          accelerator: 'CmdOrCtrl+V',
          click: () => {
            mainWindow.webContents.send('toggle-voice-mode');
          }
        },
        {
          label: 'Autocomplétion',
          accelerator: 'CmdOrCtrl+A',
          click: () => {
            mainWindow.webContents.send('toggle-autocomplete');
          }
        },
        { type: 'separator' },
        {
          label: 'Prendre capture',
          accelerator: 'CmdOrCtrl+S',
          click: () => {
            mainWindow.webContents.send('take-screenshot');
          }
        }
      ]
    },
    {
      label: 'Affichage',
      submenu: [
        { label: 'Recharger', accelerator: 'CmdOrCtrl+R', role: 'reload' },
        { label: 'Forcer le rechargement', accelerator: 'CmdOrCtrl+Shift+R', role: 'forceReload' },
        { label: 'Outils de développement', accelerator: 'F12', role: 'toggleDevTools' },
        { type: 'separator' },
        { label: 'Zoom avant', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
        { label: 'Zoom arrière', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
        { label: 'Zoom normal', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' },
        { type: 'separator' },
        { label: 'Plein écran', accelerator: 'F11', role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Aide',
      submenu: [
        {
          label: 'À propos de JARVIS',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'À propos de JARVIS',
              message: `${APP_CONFIG.name} v${APP_CONFIG.version}`,
              detail: 'Assistant IA Autonome pour Windows\n\nDéveloppé avec Electron + React\nPowered by Ollama + AMD RX 7800 XT'
            });
          }
        },
        {
          label: 'Documentation',
          click: () => {
            shell.openExternal('https://github.com/jarvis-ai/documentation');
          }
        }
      ]
    }
  ];
  
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Démarre le processus JARVIS Python
 */
function startJarvisProcess() {
  if (jarvisProcess) {
    console.log('JARVIS déjà démarré');
    return;
  }
  
  console.log('Démarrage de JARVIS...');
  
  // Chemin vers le script Python
  const jarvisPath = path.join(__dirname, '../../main.py');
  
  // Démarrer le processus
  jarvisProcess = spawn('python3', [jarvisPath, '--daemon'], {
    cwd: path.join(__dirname, '../..'),
    stdio: ['pipe', 'pipe', 'pipe']
  });
  
  jarvisProcess.stdout.on('data', (data) => {
    console.log(`JARVIS: ${data}`);
    mainWindow.webContents.send('jarvis-output', data.toString());
  });
  
  jarvisProcess.stderr.on('data', (data) => {
    console.error(`JARVIS Error: ${data}`);
    mainWindow.webContents.send('jarvis-error', data.toString());
  });
  
  jarvisProcess.on('close', (code) => {
    console.log(`JARVIS process exited with code ${code}`);
    jarvisProcess = null;
    mainWindow.webContents.send('jarvis-stopped', code);
  });
  
  mainWindow.webContents.send('jarvis-started');
}

/**
 * Arrête le processus JARVIS
 */
function stopJarvisProcess() {
  if (jarvisProcess) {
    console.log('Arrêt de JARVIS...');
    jarvisProcess.kill('SIGTERM');
    jarvisProcess = null;
    mainWindow.webContents.send('jarvis-stopped');
  }
}

// === IPC Handlers ===

ipcMain.handle('app-version', () => {
  return APP_CONFIG.version;
});

ipcMain.handle('get-jarvis-status', () => {
  return {
    running: jarvisProcess !== null,
    pid: jarvisProcess ? jarvisProcess.pid : null
  };
});

ipcMain.handle('start-jarvis', () => {
  startJarvisProcess();
  return { success: true };
});

ipcMain.handle('stop-jarvis', () => {
  stopJarvisProcess();
  return { success: true };
});

ipcMain.handle('execute-jarvis-command', async (event, command) => {
  return new Promise((resolve) => {
    if (!jarvisProcess) {
      resolve({ success: false, error: 'JARVIS not running' });
      return;
    }
    
    // Envoyer la commande via stdin
    jarvisProcess.stdin.write(`${command}\n`);
    
    // Timeout pour la réponse
    const timeout = setTimeout(() => {
      resolve({ success: false, error: 'Timeout' });
    }, 10000);
    
    // Écouter la réponse
    const onData = (data) => {
      clearTimeout(timeout);
      jarvisProcess.stdout.off('data', onData);
      resolve({ success: true, output: data.toString() });
    };
    
    jarvisProcess.stdout.on('data', onData);
  });
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

// === App Events ===

app.whenReady().then(() => {
  createMainWindow();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Arrêter JARVIS proprement
  if (jarvisProcess) {
    jarvisProcess.kill('SIGTERM');
  }
});

// Sécurité - Empêcher la navigation
app.on('web-contents-created', (event, contents) => {
  contents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    
    if (parsedUrl.origin !== 'http://localhost:3000' && parsedUrl.origin !== 'file://') {
      event.preventDefault();
    }
  });
});

console.log(`🤖 JARVIS UI Starting - ${APP_CONFIG.name} v${APP_CONFIG.version}`);