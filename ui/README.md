# JARVIS UI - Interface Moderne

Interface utilisateur moderne pour JARVIS - Assistant IA Autonome, développée avec Electron + React + Material-UI.

## 🚀 Fonctionnalités

### Interface Moderne
- **Design sombre** avec thème Material-UI personnalisé
- **Responsive** - S'adapte à toutes les tailles d'écran
- **Animations fluides** et effets visuels
- **Navigation intuitive** avec sidebar et routage
- **Système de notifications** en temps réel

### Modules JARVIS
- **Dashboard** - Vue d'ensemble complète de l'état du système
- **Vision Control** - Contrôle du module de capture et analyse d'écran
- **Interface Vocale** - Gestion de la reconnaissance et synthèse vocale
- **Autocomplétion** - Configuration des suggestions intelligentes
- **Mémoire** - Exploration du système de mémoire persistante
- **Exécuteur** - Monitoring des actions automatisées
- **Logs Système** - Visualisation et filtrage des journaux
- **Paramètres** - Configuration complète de JARVIS

### Communication Electron
- **API sécurisée** avec preload.js et contextIsolation
- **Communication bidirectionnelle** avec le processus Python
- **Gestion d'état** avec React Context
- **Notifications système** intégrées

## 🛠️ Technologies

- **Electron** - Framework desktop cross-platform
- **React 18** - Bibliothèque UI moderne
- **Material-UI v5** - Composants Material Design
- **React Router** - Routage côté client
- **Context API** - Gestion d'état globale

## 📦 Installation

```bash
# Aller dans le dossier UI
cd ui/

# Installer les dépendances
npm install

# Mode développement (React + Electron)
npm run electron-dev

# Build production
npm run build

# Créer l'executable
npm run dist
```

## 🏗️ Structure

```
ui/
├── public/                 # Fichiers statiques
│   ├── index.html         # HTML principal avec loading screen
│   └── manifest.json      # Manifest PWA
├── src/
│   ├── components/        # Composants React
│   │   └── layout/        # Composants de layout
│   ├── contexts/          # Contexts React
│   │   └── JarvisContext.js # État global JARVIS
│   ├── pages/             # Pages de l'application
│   ├── styles/            # Styles CSS globaux
│   ├── App.js             # Composant principal
│   └── index.js           # Point d'entrée React
├── electron/              # Processus Electron
│   ├── main.js            # Processus principal
│   ├── preload.js         # Bridge sécurisé
│   └── isDev.js           # Détection mode dev
├── package.json           # Configuration npm
└── README.md              # Documentation
```

## 🎨 Interface

### Dashboard
- **Métriques en temps réel** : Commandes exécutées, captures d'écran, etc.
- **État des modules** : Vision, voix, mémoire, autocomplétion, etc.
- **Logs récents** : Activité système avec filtrage par niveau
- **Informations système** : Statut JARVIS, PID, uptime
- **Actions rapides** : Capture d'écran, tests, configuration

### Navigation
- **Sidebar animée** avec statut des modules
- **Top bar** avec contrôles rapides et indicateurs
- **Breadcrumbs** et navigation contextuelle
- **Raccourcis clavier** pour toutes les actions

### Thème
- **Couleurs** : Palette sombre avec accents cyan/bleu
- **Typographie** : Inter pour le texte, JetBrains Mono pour le code
- **Animations** : Transitions fluides et effets hover
- **Responsive** : S'adapte mobile, tablette et desktop

## 🔧 Configuration

### Variables d'environnement
```bash
NODE_ENV=development    # Mode développement
DEBUG_PROD=true        # Debug en production
```

### Menu Electron
- **Fichier** : Nouvelle session, ouvrir config, quitter
- **JARVIS** : Démarrer/arrêter, mode vocal, autocomplétion, capture
- **Affichage** : Zoom, plein écran, outils de développement
- **Aide** : À propos, documentation

### Raccourcis clavier
- `Ctrl+J` - Démarrer/arrêter JARVIS
- `Ctrl+V` - Toggle mode vocal
- `Ctrl+A` - Toggle autocomplétion
- `Ctrl+S` - Prendre capture d'écran
- `Ctrl+N` - Nouvelle session
- `F12` - Outils de développement

## 🚀 Développement

### Scripts disponibles
```bash
npm start              # React dev server
npm run build          # Build production
npm run electron       # Electron en mode production
npm run electron-dev   # Electron + React dev
npm run dist          # Créer l'executable
npm run dist-win      # Build Windows
npm run dist-linux    # Build Linux
```

### API Electron
```javascript
// Disponible dans le renderer via window.electronAPI
await electronAPI.startJarvis()
await electronAPI.stopJarvis()
await electronAPI.executeJarvisCommand(command)
await electronAPI.getJarvisStatus()
```

### Context JARVIS
```javascript
const { state, actions, electronAPI } = useJarvis();

// État global
state.jarvis.status     // 'connected' | 'disconnected' | 'connecting'
state.modules          // État des modules
state.config          // Configuration
state.stats           // Statistiques
state.logs            // Logs système

// Actions
actions.setJarvisStatus(status)
actions.toggleVoiceMode()
actions.addNotification(type, title, message)
```

## 📊 Monitoring

### Métriques suivies
- Commandes exécutées
- Captures d'écran prises
- Commandes vocales
- Utilisation autocomplétion
- Entrées en mémoire

### Logs système
- **Niveaux** : info, success, warning, error
- **Sources** : ui, jarvis, system
- **Filtrage** : Par niveau, source, texte
- **Export** : Fonctionnalité à venir

## 🔒 Sécurité

- **Context Isolation** activé
- **Node Integration** désactivé
- **Web Security** activé
- **Preload script** sécurisé
- **Navigation** restreinte aux domaines autorisés

## 🎯 Roadmap

- [ ] Visualisation graphique en temps réel
- [ ] Éditeur de séquences d'actions
- [ ] Gestionnaire de plugins
- [ ] Thèmes personnalisables
- [ ] Mode hors ligne
- [ ] Synchronisation cloud

## 🤝 Contribution

L'interface est conçue de manière modulaire pour faciliter l'ajout de nouvelles fonctionnalités. Chaque page est un composant React indépendant qui utilise le context JARVIS pour la communication avec le backend.

---

**JARVIS UI** - Interface moderne pour l'assistant IA autonome 🤖