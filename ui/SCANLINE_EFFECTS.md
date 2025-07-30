# 🌊 JARVIS Scanline Effects - Documentation

## Vue d'ensemble

Les effets Scanline ont été ajoutés à l'interface JARVIS pour reproduire l'expérience visuelle holographique des écrans de Tony Stark dans Iron Man. Ces effets comprennent des lignes de balayage animées, des grilles, et des effets radar circulaires.

## Fonctionnalités

### ✨ Effets visuels disponibles

- **Scanlines horizontales** : Lignes qui balayent du haut vers le bas
- **Scanlines verticales** : Lignes qui balayent de gauche à droite
- **Scanlines diagonales** : Effets diagonaux pour plus de complexité
- **Radar circulaire** : Balayage rotatif style radar
- **Effet Glitch** : Distorsion temporaire des scanlines

### 🎮 Modes d'intensité

- **Low** : Effets minimes, parfait pour des interfaces subtiles
- **Normal** : Configuration équilibrée par défaut
- **High** : Effets prononcés style Iron Man
- **Intense** : Maximum d'effets pour des démonstrations

### ⚡ Vitesses configurables

- **Slow** : Animations lentes et apaisantes
- **Normal** : Vitesse standard
- **Fast** : Animations rapides et dynamiques

## Utilisation

### Intégration de base

```jsx
import JarvisInterface from './components/JarvisInterface';

function App() {
  return (
    <JarvisInterface 
      enableScanlines={true}
      showScanlineControls={false}
      messages={messages}
      onSendMessage={handleMessage}
    />
  );
}
```

### Utilisation avancée avec ScanlineEffect

```jsx
import ScanlineEffect, { useScanlineConfig } from './components/ScanlineEffect';

function CustomInterface() {
  const { config, updateConfig, applyPreset } = useScanlineConfig({
    intensity: 'high',
    effects: { 
      horizontal: true, 
      vertical: true, 
      radar: true 
    }
  });

  return (
    <ScanlineEffect 
      config={config} 
      onConfigChange={updateConfig}
      showControls={true}
    >
      {/* Votre contenu ici */}
    </ScanlineEffect>
  );
}
```

### Presets disponibles

```jsx
// Minimal - Effets discrets
applyPreset('minimal');

// Standard - Configuration équilibrée
applyPreset('standard');

// Intense - Maximum d'effets
applyPreset('intense');

// Iron Man - Style fidèle aux films
applyPreset('ironman');
```

## Configuration détaillée

### Structure de configuration

```javascript
const config = {
  enabled: true,
  intensity: 'high', // 'low', 'normal', 'high', 'intense'
  speed: 'normal', // 'slow', 'normal', 'fast'
  colors: {
    primary: 'rgba(0, 212, 255, 0.8)',    // Cyan holographique
    secondary: 'rgba(0, 255, 136, 0.6)',  // Vert JARVIS
    accent: 'rgba(255, 107, 0, 0.4)'      // Orange accent
  },
  effects: {
    horizontal: true,  // Scanlines horizontales
    vertical: true,    // Scanlines verticales
    diagonal: false,   // Scanlines diagonales
    radar: false,      // Radar circulaire
    glitch: false      // Effet de glitch
  },
  count: {
    horizontal: 3,     // Nombre de scanlines horizontales
    vertical: 2,       // Nombre de scanlines verticales
    diagonal: 1        // Nombre de scanlines diagonales
  }
};
```

### Personnalisation des couleurs

Les scanlines utilisent les variables CSS JARVIS existantes :

```css
:root {
  --jarvis-primary: #00d4ff;    /* Cyan principal */
  --jarvis-secondary: #00ff88;  /* Vert secondaire */
  --jarvis-accent: #ff6b00;     /* Orange accent */
}
```

## Contrôles utilisateur

### Contrôles intégrés

Quand `showScanlineControls={true}` :

- **Panneau de contrôle** : Interface complète en haut à droite
- **Toggle Enable/Disable** : Activer/désactiver tous les effets
- **Sélecteur d'intensité** : Boutons pour changer l'intensité
- **Sélecteur de vitesse** : Contrôle de la vitesse d'animation
- **Toggle effets** : Activer/désactiver individuellement chaque effet

### Contrôles dans l'interface principale

- **SCAN: ON/OFF** : Toggle rapide des scanlines
- **INTENSE** : Active temporairement le mode intense (5 secondes)

## Performance et optimisation

### Considérations techniques

- **Z-index élevé** : Les scanlines sont au-dessus de tout (z-index: 9999)
- **Pointer-events: none** : N'interfèrent pas avec l'interaction utilisateur
- **Animations CSS** : Performances optimales avec accélération GPU
- **Responsive** : Effets adaptés sur mobile (opacity réduite)

### Réduction des effets sur mobile

```css
@media (max-width: 768px) {
  .jarvis-scanlines-container {
    opacity: 0.7; /* Réduction automatique sur mobile */
  }
}
```

## API du Hook useScanlineConfig

```jsx
const {
  config,           // Configuration actuelle
  updateConfig,     // Fonction de mise à jour
  presets,         // Presets disponibles
  applyPreset      // Appliquer un preset
} = useScanlineConfig(initialConfig);
```

### Méthodes disponibles

- `updateConfig(newConfig)` : Met à jour la configuration
- `applyPreset('ironman')` : Applique un preset prédéfini
- `presets` : Objet contenant tous les presets disponibles

## Exemples d'utilisation

### Mode démonstration

```jsx
// Active le mode intense pendant 5 secondes
const activateDemo = () => {
  applyPreset('intense');
  setTimeout(() => applyPreset('ironman'), 5000);
};
```

### Interface personnalisée

```jsx
function CustomJarvis() {
  const [demoMode, setDemoMode] = useState(false);
  
  const config = {
    enabled: true,
    intensity: demoMode ? 'intense' : 'high',
    effects: {
      horizontal: true,
      vertical: true,
      radar: true,
      glitch: demoMode
    }
  };
  
  return (
    <ScanlineEffect config={config}>
      <YourInterface />
    </ScanlineEffect>
  );
}
```

## Classes CSS principales

- `.jarvis-scanlines-container` : Container principal
- `.jarvis-scanline-horizontal` : Scanlines horizontales
- `.jarvis-scanline-vertical` : Scanlines verticales
- `.jarvis-scanline-diagonal` : Scanlines diagonales
- `.jarvis-radar-sweep` : Radar circulaire

## Animations CSS

- `scanline-sweep` : Animation de balayage horizontal
- `scanline-vertical-sweep` : Animation de balayage vertical
- `scanline-glitch` : Animation de glitch
- `radar-sweep` : Animation du radar rotatif

## Support navigateur

- ✅ Chrome/Edge (recommandé)
- ✅ Firefox
- ✅ Safari
- ⚠️ IE11 (support limité des animations)

## Troubleshooting

### Problèmes courants

1. **Scanlines non visibles** : Vérifiez que `enabled: true` dans la config
2. **Performances lentes** : Réduisez l'intensité ou désactivez certains effets
3. **Conflits Z-index** : Les scanlines utilisent z-index: 9999

### Debug

```jsx
// Activer les logs pour debug
const config = {
  enabled: true,
  debug: true // Affiche les logs de performance
};
```

---

**Créé pour le projet JARVIS AI 2025 - Style Iron Man authentique** 🚀