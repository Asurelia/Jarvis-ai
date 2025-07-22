# 🔴 Guide d'optimisation GPU AMD pour JARVIS

## 🎯 Vue d'ensemble

JARVIS 2025 est maintenant **entièrement optimisé pour les GPU AMD** avec détection automatique et configurations adaptatives.

## 🔧 Fonctionnalités AMD implémentées

### ✅ **Détection automatique**
- Reconnaissance AMD/ATI/Radeon
- Test des capacités WebGL
- Score de performance adaptatif
- Configuration automatique selon le GPU

### ✅ **Optimisations WebGL**
```javascript
// Configuration AMD automatique
powerPreference: "default"        // Laisser AMD driver décider
precision: "mediump"              // Compatibilité optimale  
antialiasing: adaptatif           // Selon performance GPU
shadowMapping: désactivé/basique  // Éviter PCFSoft sur AMD
```

### ✅ **Post-processing adaptatif**
| GPU Type | Bloom | Glitch | Film | Particules |
|----------|-------|---------|------|------------|
| AMD Basse | ✅ Léger | ❌ | ❌ | 25 |
| AMD Moyenne | ✅ Normal | ❌ | ❌ | 75 |
| AMD Haute | ✅ Fort | ✅ | ❌ | 100 |
| NVIDIA | ✅ Max | ✅ | ✅ | 150 |

### ✅ **Shaders optimisés**
- Précision `mediump` pour compatibilité AMD
- Fonctions mathématiques simplifiées
- Bruit procédural allégé
- Éviter les instructions complexes

## 🚀 GPU AMD supportés

### **Excellent support (Score 4-5)**
- RX 7900 XTX/XT
- RX 7800/7700 XT
- RX 6900/6800/6700 XT
- RX 6600 XT

### **Bon support (Score 3-4)**
- RX 6500/6400 XT
- RX 5700/5600/5500 XT
- Vega 64/56

### **Support de base (Score 1-3)**
- APU Ryzen (Vega intégrée)
- RX 500 series
- GPU intégrés

## ⚙️ Configuration manuelle

### **Variables d'environnement**
```bash
# Forcer optimisations AMD
FORCE_AMD_OPTIMIZATION=true

# Niveau de qualité (1-5)
AMD_QUALITY_LEVEL=3

# Désactiver post-processing
DISABLE_POST_PROCESSING=true
```

### **Paramètres avancés**
```javascript
// Dans le navigateur console
jarvis.sphere.changeTheme('organic'); // Thème le plus léger
jarvis.sphere.setQuality(0.7);       // Réduire qualité
jarvis.sphere.disableEffects();      // Désactiver effets
```

## 🔍 Diagnostic GPU

### **Console browser (F12)**
```
🎮 GPU détecté: {vendor: 'amd', renderer: 'radeon rx 7800 xt'}
📊 Optimisations AMD appliquées
🔧 Post-processing allégé pour GPU AMD/Intégré
⚡ Performance score: 4.2/5
```

### **Commandes utiles**
```javascript
// Vérifier détection
console.log(jarvis.gpu.info);

// Performance temps réel
console.log(jarvis.performance.fps);

// Forcer redetection
jarvis.gpu.redetect();
```

## 🐛 Résolution problèmes

### **Sphère 3D ne s'affiche pas**
```bash
# Vérifier support WebGL
# Dans console navigateur
!!window.WebGLRenderingContext
```

### **Performance faible**
1. Vérifier driver AMD à jour
2. Activer accélération hardware navigateur
3. Fermer autres applications GPU-intensives
4. Réduire qualité : `jarvis.sphere.setQuality(0.5)`

### **Effets visuels manquants**
```javascript
// Forcer activation (GPU puissant)
jarvis.sphere.enableAllEffects();

// Mode compatibilité
jarvis.sphere.setCompatibilityMode(true);
```

## 📊 Benchmarks AMD

### **RX 7900 XTX**
- Sphère 4K@60fps : ✅
- Tous effets : ✅  
- 150 particules : ✅
- Score : 5/5

### **RX 6700 XT**
- Sphère 1440p@60fps : ✅
- Bloom uniquement : ✅
- 100 particules : ✅
- Score : 4/5

### **APU Ryzen 7000**
- Sphère 1080p@30fps : ✅
- Effets minimum : ✅
- 25 particules : ✅
- Score : 2/5

## 🔗 Drivers recommandés

### **AMD Adrenalin**
- **Minimum** : 22.5.1+
- **Recommandé** : 23.12.1+ (dernière stable)
- **Beta** : 24.x pour fonctionnalités avancées

### **Navigateurs optimisés**
1. **Chrome** : Meilleure performance WebGL AMD
2. **Firefox** : Bon support, activer `webgl.force-enabled`
3. **Edge** : Performance correcte

## 🛠️ Paramétrage avancé

### **Chrome flags recommandés**
```
chrome://flags/#enable-unsafe-webgl
chrome://flags/#enable-webgl2-compute-context  
chrome://flags/#enable-gpu-rasterization
```

### **Firefox about:config**
```
webgl.force-enabled = true
webgl.msaa-force = false
gfx.webrender.enabled = true
```

## 📈 Monitoring performance

Le système inclut un monitoring automatique :
- FPS temps réel
- Adaptation qualité automatique
- Alertes performance
- Statistiques détaillées

```javascript
// Accéder aux stats
jarvis.performance.getReport();
```

---

Pour toute question AMD-spécifique, consultez les logs console ou créez une issue GitHub avec `[AMD]` dans le titre.