# 🤖 JARVIS Voice Preset - Documentation

## Vue d'ensemble

Le preset vocal **JARVIS** transforme le service TTS pour reproduire la voix sophistiquée et métallique de l'IA Jarvis des films Iron Man. Ce preset applique des effets audio avancés et utilise des phrases contextuelles pour créer une expérience vocale immersive.

## 🎯 Caractéristiques

### Paramètres Vocaux
- **Vitesse**: 0.95 (légèrement plus lent pour plus de gravité)
- **Pitch**: -2.0 (voix plus grave)
- **Volume**: 0.85 (niveau modéré mais autoritaire)
- **Langue**: Français avec style sophistiqué

### Effets Audio Appliqués

#### 🎛️ Égalisation (EQ)
- **Graves (80Hz)**: +3dB pour plus de profondeur
- **Médiums (1000Hz)**: -1dB pour réduire la nasalité
- **Aigus (8000Hz)**: +2dB pour la clarté métallique
- **Présence (4000Hz)**: +1.5dB pour l'intelligibilité

#### 🌊 Réverbération
- **Room Size**: 0.7 (salle de taille moyenne)
- **Damping**: 0.3 (peu d'amortissement pour effet métallique)
- **Wet/Dry**: 25%/75% (mélange subtil)

#### 🔧 Compression Dynamique
- **Threshold**: -18dB
- **Ratio**: 3:1
- **Attack**: 5ms
- **Release**: 50ms

#### ✨ Effets Spéciaux
- **Filtre Métallique**: Résonance à 2000Hz
- **Harmonic Enhancer**: Enrichissement harmonique
- **Chorus Subtil**: Modulation légère pour la texture

## 📱 Utilisation

### Endpoint Principal
```
POST /api/tts/jarvis
```

#### Paramètres
```json
{
  "text": "Texte à synthétiser",
  "context": "greeting|system|analysis|calculation|recommendation", 
  "phrase_category": "greetings|confirmations|status_reports|initiatives|closings|errors"
}
```

### Exemples d'utilisation

#### Salutation Basique
```bash
curl -X POST "http://localhost:5002/api/tts/jarvis" \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour Monsieur. Comment puis-je vous assister?"}'
```

#### Avec Catégorie de Phrase
```bash
curl -X POST "http://localhost:5002/api/tts/jarvis" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Analyse des systèmes en cours.",
    "phrase_category": "status_reports"
  }'
```

#### Avec Contexte
```bash
curl -X POST "http://localhost:5002/api/tts/jarvis" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "La température est de 22 degrés.",
    "context": "weather"
  }'
```

## 💬 Phrases Typiques de Jarvis

### Salutations (`greetings`)
- "Bonjour, Monsieur."
- "Comment puis-je vous assister aujourd'hui ?"
- "Tous les systèmes sont opérationnels."
- "À votre service, Monsieur."

### Confirmations (`confirmations`)
- "Comme vous voudrez, Monsieur."
- "Bien reçu, Monsieur."
- "Immédiatement, Monsieur."
- "Considérez que c'est fait."

### Rapports de Statut (`status_reports`)
- "Systèmes nominaux à {percentage}%."
- "Tous les paramètres sont dans les limites normales."
- "Diagnostic complet : aucune anomalie détectée."
- "Performances optimales maintenues."

### Initiatives (`initiatives`)
- "J'ai pris la liberté de..."
- "Permettez-moi de suggérer..."
- "Puis-je recommander..."
- "Il serait peut-être judicieux de..."

### Conclusions (`closings`)
- "Toujours un plaisir, Monsieur."
- "À votre disposition."
- "N'hésitez pas si vous avez besoin d'autre chose."
- "Mission accomplie."

### Erreurs (`errors`)
- "Je crains qu'il y ait un problème, Monsieur."
- "Cela semble poser quelques difficultés."
- "Permettez-moi de résoudre cela."
- "Un moment, je reconfigure les paramètres."

## 🧠 Amélorations Contextuelles

Le preset Jarvis améliore automatiquement le texte selon le contexte :

| Contexte | Préfixe Ajouté |
|----------|----------------|
| `weather` | "D'après mes données météorologiques..." |
| `time` | "Il est actuellement..." |
| `calculation` | "Selon mes calculs..." |
| `analysis` | "Mon analyse indique que..." |
| `system` | "État des systèmes :" |
| `recommendation` | "Je recommande vivement..." |

## 🎪 API Endpoints Additionnels

### Lister les Presets
```
GET /api/presets
```

### Informations Preset Jarvis
```
GET /api/presets/jarvis
```

### Phrases Jarvis
```
GET /api/jarvis/phrases
GET /api/jarvis/phrases/{category}
```

## 🧪 Tests et Exemples

### Script de Test Automatique
```bash
python test_jarvis_preset.py
```

### Exemples Interactifs
```bash
python jarvis_examples.py
```

### Tests Manuels avec cURL

#### Test Basique
```bash
curl -X POST "http://localhost:5002/api/tts/jarvis" \
  -H "Content-Type: application/json" \
  -d '{"text": "Diagnostics système terminés. Aucune anomalie détectée."}' \
  | jq -r '.audio' | base64 -d > jarvis_test.wav
```

#### Test avec Catégorie
```bash
curl -X POST "http://localhost:5002/api/tts/jarvis" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Analyse des données en cours.",
    "phrase_category": "status_reports",
    "context": "system"
  }' | jq -r '.audio' | base64 -d > jarvis_status.wav
```

## 🔧 Configuration Technique

### Paramètres Audio
- **Sample Rate**: 22050 Hz
- **Channels**: Mono (1)
- **Format**: WAV PCM 16-bit
- **Latence**: < 500ms

### Effets DSP
- **Égalisation**: 4-band parametric EQ
- **Réverbération**: Multi-tap delay reverb
- **Compression**: Feed-forward compressor
- **Filtres**: Résonant metallic filter

## 📊 Réponse Type

```json
{
  "status": "success",
  "audio": "UklGRjw...", // Audio en base64
  "format": "wav",
  "sample_rate": 22050,
  "channels": 1,
  "duration_ms": 2340,
  "text_length": 45,
  "original_text": "Bonjour Monsieur.",
  "enhanced_text": "Bonjour, Monsieur. Comment puis-je vous assister aujourd'hui ?",
  "preset": "jarvis",
  "voice_effects": "applied"
}
```

## ⚠️ Notes Importantes

1. **Performance**: Les effets audio ajoutent ~200ms de latence
2. **Mémoire**: Utilisation accrue due aux filtres DSP
3. **Compatibilité**: Nécessite scipy, librosa et numpy
4. **Qualité**: Optimisé pour voix masculine française

## 🛠️ Dépannage

### Service Non Disponible
```bash
# Vérifier le statut
curl http://localhost:5002/health

# Redémarrer le service
python main.py
```

### Preset Non Trouvé
```bash
# Vérifier les presets disponibles
curl http://localhost:5002/api/presets
```

### Audio Corrompu
- Vérifier l'encodage base64
- Valider le format WAV
- Contrôler la taille des données

## 🎭 Personnalisation

Pour créer votre propre preset, consultez :
- `presets/jarvis_voice.py` - Configuration de référence
- `presets/preset_manager.py` - Gestionnaire de presets
- `core/audio_processor.py` - Processeur d'effets

---

*Développé pour le projet JARVIS AI 2025 - "Like Jarvis, but real."*