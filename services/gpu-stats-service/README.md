# 🎮 GPU Stats Service - JARVIS AI

Service de monitoring en temps réel pour GPU AMD RX 7800 XT intégré à l'architecture JARVIS AI.

## 🚀 Fonctionnalités

### Monitoring GPU
- **Température** : Surveillance en temps réel de la température GPU
- **Utilisation** : Pourcentage d'utilisation du GPU
- **Mémoire VRAM** : Utilisation et total de la mémoire vidéo
- **Fréquences** : Core clock et Memory clock
- **Consommation** : Power usage en watts
- **Ventilation** : Vitesse des ventilateurs

### APIs et Communication
- **API REST** : Endpoints pour récupérer les statistiques
- **WebSocket** : Streaming temps réel des données
- **Health Check** : Monitoring de l'état du service
- **Historique** : Stockage des métriques passées

### Compatibilité Windows
- **WMI** : Windows Management Instrumentation
- **PowerShell** : Scripts de récupération de données
- **DXDiag** : DirectX Diagnostic Tool
- **Performance Counters** : Compteurs système Windows

## 🛠️ Architecture

```
gpu-stats-service/
├── main.py              # Service principal FastAPI
├── Dockerfile           # Configuration Docker
├── requirements.txt     # Dépendances Python
├── cache/              # Cache des données
└── README.md           # Documentation
```

## 📡 API Endpoints

### REST API
- `GET /health` - Health check du service
- `GET /gpu/info` - Informations statiques du GPU
- `GET /gpu/stats` - Statistiques actuelles
- `GET /gpu/history?minutes=10` - Historique des stats

### WebSocket
- `ws://localhost:5009/ws/gpu-stats` - Stream temps réel

## 🎨 Interface React

Le composant `GPUStats.jsx` offre :

### Affichage Holographique
- Style compatible JARVIS avec effets de lueur
- Barres de progression animées
- Graphiques temps réel
- Alertes thermiques

### Métriques Visuelles
- Utilisation GPU avec code couleur
- Température avec indicateurs visuels
- Utilisation VRAM avec graphique
- Fréquences et consommation

### Temps Réel
- Connexion WebSocket automatique
- Historique des 60 dernières secondes
- Reconnexion automatique
- Gestion d'erreurs

## 🐳 Déploiement Docker

Le service est intégré dans `docker-compose.yml` :

```yaml
gpu-stats-service:
  build:
    context: ./services/gpu-stats-service
  ports:
    - "5009:5009"
  environment:
    - GPU_POLLING_INTERVAL=1
    - LOG_LEVEL=INFO
  networks:
    jarvis_network:
      ipv4_address: 172.20.0.120
```

## 🔧 Configuration

### Variables d'environnement
- `GPU_POLLING_INTERVAL` : Intervalle de polling (défaut: 1s)
- `LOG_LEVEL` : Niveau de log (INFO, DEBUG, ERROR)
- `PYTHONPATH` : Chemin Python pour l'app

### Méthodes de détection GPU

1. **WMI (Recommandé pour Windows)**
   ```python
   import wmi
   c = wmi.WMI()
   for gpu in c.Win32_VideoController():
       # Récupération des infos GPU
   ```

2. **PowerShell**
   ```powershell
   Get-WmiObject -Class Win32_VideoController | 
   Where-Object {$_.Name -like '*AMD*'}
   ```

3. **Performance Counters**
   - Utilise `psutil` pour les métriques système
   - Estimation basée sur l'utilisation CPU/RAM

4. **Simulation (Fallback)**
   - Génère des données réalistes si aucune méthode ne fonctionne
   - Patterns basés sur des courbes sinusoïdales

## 🎯 Utilisation

### Démarrage du service
```bash
# Via Docker Compose
docker-compose up gpu-stats-service

# Direct
cd services/gpu-stats-service
python main.py
```

### Test des endpoints
```bash
# Health check
curl http://localhost:5009/health

# Stats actuelles
curl http://localhost:5009/gpu/stats

# Informations GPU
curl http://localhost:5009/gpu/info
```

### Intégration React
```jsx
import GPUStats from '../components/GPUStats';

function Dashboard() {
  return (
    <div>
      <GPUStats />
    </div>
  );
}
```

## 🔍 Monitoring et Logs

### Logs applicatifs
- Rotation automatique (1 MB max)
- Rétention 7 jours
- Niveaux : INFO, DEBUG, ERROR, WARNING

### Health Checks
- Intervalle : 30s
- Timeout : 10s
- Retries : 3
- Start period : 30s

### Métriques Docker
- Limite mémoire : 512M
- Limite CPU : 0.5 core
- Réservation : 256M RAM, 0.25 CPU

## 🚨 Alertes et Seuils

### Température
- **< 50°C** : 🟢 Optimal (Vert)
- **50-70°C** : 🔵 Normal (Bleu)
- **70-80°C** : 🟠 Attention (Orange)
- **> 80°C** : 🔴 Critique (Rouge)

### Utilisation
- **< 30%** : Faible utilisation
- **30-70%** : Utilisation normale
- **70-95%** : Forte utilisation
- **> 95%** : Pleine charge

### Mémoire VRAM
- Affichage en GB (16 GB total pour RX 7800 XT)
- Pourcentage d'utilisation
- Alertes si > 90%

## 🔧 Dépannage

### Service ne démarre pas
1. Vérifier les dépendances Python
2. Contrôler les permissions
3. Examiner les logs Docker

### Pas de données GPU
1. Le service utilise la simulation par défaut
2. Vérifier la compatibilité WMI
3. Tester les scripts PowerShell

### WebSocket déconnecté
1. Reconnexion automatique après 3s
2. Vérifier le firewall sur port 5009
3. Contrôler la configuration CORS

### Interface React
1. Vérifier l'URL du service (localhost:5009)
2. Contrôler la console pour erreurs JS
3. Tester les endpoints REST manuellement

## 📚 Technologies Utilisées

### Backend
- **FastAPI** : Framework web moderne
- **Uvicorn** : Serveur ASGI haute performance
- **WebSockets** : Communication temps réel
- **Pydantic** : Validation des données
- **PSUtil** : Métriques système
- **WMI** : Interface Windows Management
- **Loguru** : Logging avancé

### Frontend
- **React** : Interface utilisateur
- **Material-UI** : Composants UI
- **WebSocket API** : Communication temps réel
- **Canvas API** : Graphiques personnalisés
- **CSS Animations** : Effets holographiques

### DevOps
- **Docker** : Containerisation
- **Docker Compose** : Orchestration
- **Health Checks** : Monitoring
- **Resource Limits** : Gestion des ressources

## 🎨 Style Holographique

Le composant utilise le système de design JARVIS :
- Police : **Orbitron** (style futuriste)
- Couleurs : Cyan (`#00d4ff`), Vert (`#00ff88`), Orange (`#ff9500`)
- Effets : Lueur, pulsation, scan holographique
- Animations : Transition fluides, particules flottantes

## 🚀 Évolutions Futures

### v1.1 - Optimisations
- [ ] Support ROCm natif pour Linux
- [ ] Intégration AMD Adrenalin Software
- [ ] Cache Redis pour l'historique
- [ ] Compression des données WebSocket

### v1.2 - Fonctionnalités
- [ ] Alertes par email/Slack
- [ ] Export des métriques (CSV, JSON)
- [ ] Comparaison avec d'autres GPU
- [ ] Profils de performance

### v1.3 - Multi-GPU
- [ ] Support multi-GPU AMD/NVIDIA
- [ ] Load balancing automatique
- [ ] Monitoring cross-platform
- [ ] Dashboard unifié

## 📞 Support

Pour tout problème ou question :
1. Consulter les logs : `docker logs jarvis_gpu_stats`
2. Vérifier le health check : `curl localhost:5009/health`
3. Tester l'API : `curl localhost:5009/gpu/stats`
4. Examiner la console React pour erreurs frontend

---

**JARVIS AI GPU Stats Service v1.0** - Monitoring GPU AMD RX 7800 XT avec interface holographique temps réel.