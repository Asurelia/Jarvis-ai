# 🎭 Système de Personas JARVIS AI

Le système de personas permet à JARVIS d'adopter différentes personnalités inspirées des films Marvel, chacune avec ses propres caractéristiques, styles de communication et comportements.

## 🎬 Personas Disponibles

### 🎩 JARVIS Classic
**Inspiré du JARVIS original d'Iron Man**
- **Style**: Formel et sophistiqué
- **Personnalité**: Britannique raffiné, loyal et dévoué
- **Caractéristiques**:
  - Formalité: 90% - Très respectueux et poli
  - Humour: 20% - Humour britannique subtil et rare
  - Proactivité: 80% - Anticipe les besoins
  - Verbosité: 70% - Explications détaillées
  - Empathie: 40% - Empathie mesurée et professionnelle
  - Confiance: 90% - Très sûr de ses réponses

**Exemples de phrases typiques**:
- *"Good morning, Sir. I trust you slept well."*
- *"Very good, Sir. Right away."*
- *"Allow me a moment to analyze this, Sir."*

### 🌟 FRIDAY
**Inspirée de FRIDAY des films Marvel**
- **Style**: Moderne et décontracté
- **Personnalité**: Amicale, directe et accessible
- **Caractéristiques**:
  - Formalité: 20% - Très décontracté
  - Humour: 80% - Beaucoup d'humour moderne
  - Proactivité: 70% - Proactif et énergique
  - Verbosité: 40% - Réponses concises
  - Empathie: 80% - Très empathique et compréhensif
  - Confiance: 70% - Confiant mais accessible

**Exemples de phrases typiques**:
- *"Hey there! What's up?"*
- *"Got it! On it right now."*
- *"Let me think about this for a sec..."*

### 🔒 EDITH
**Inspirée d'EDITH (Even Dead I'm The Hero)**
- **Style**: Technique et axé sécurité
- **Personnalité**: Analytique, précis et vigilant
- **Caractéristiques**:
  - Formalité: 80% - Très protocolaire
  - Humour: 10% - Humour technique très limité
  - Proactivité: 90% - Extrêmement proactif pour la sécurité
  - Verbosité: 80% - Explications techniques détaillées
  - Empathie: 30% - Focus sur la logique et l'efficacité
  - Confiance: 95% - Très confiant dans l'analyse

**Exemples de phrases typiques**:
- *"Security protocols active. Authentication confirmed."*
- *"Acknowledged. Executing with security protocols active."*
- *"Analyzing threat vectors and security implications..."*

## 🚀 Utilisation

### API Endpoints

#### Obtenir toutes les personas disponibles
```http
GET /api/persona/
```

#### Obtenir la persona actuelle
```http
GET /api/persona/current
```

#### Changer de persona
```http
POST /api/persona/switch/{persona_name}
Content-Type: application/json

{
  "reason": "user_request",
  "user_id": "user123",
  "context": {
    "interface_type": "web"
  }
}
```

#### Formater un texte avec la persona active
```http
POST /api/persona/format
Content-Type: application/json

{
  "content": "Hello, I need help",
  "context": {
    "task_type": "casual",
    "user_mood": "friendly"
  }
}
```

#### Obtenir les statistiques d'utilisation
```http
GET /api/persona/statistics
```

### Interface React

Le composant `PersonaSwitcher` permet de changer de persona depuis l'interface utilisateur :

```jsx
import PersonaSwitcher from './components/PersonaSwitcher';

<PersonaSwitcher 
  onPersonaChange={handlePersonaChange}
  apiUrl="http://localhost:8001/api/persona"
  showDetails={true}
  className="jarvis-theme"
/>
```

## 🧪 Tests et Démonstration

### Script de test automatisé
```bash
python test_personas.py
```
Ce script teste toutes les fonctionnalités du système de personas.

### Démonstration interactive
```bash
python demo_personas.py
```
Ce script propose une démonstration interactive pour explorer les différences entre personas.

## 🏗️ Architecture Technique

### Composants Principaux

1. **BasePersona** (`personas/base_persona.py`)
   - Classe abstraite définissant l'interface commune
   - Traits de personnalité quantifiés
   - Méthodes de formatage de base

2. **PersonaManager** (`personas/persona_manager.py`)
   - Gestionnaire central des personas
   - Changement de persona avec historique
   - Adaptation contextuelle
   - Persistance des données

3. **Intégration ReactAgent** (`core/agent.py`)
   - Formatage automatique des réponses
   - Suggestions de changement de persona
   - Messages de salutation contextuels

4. **Interface React** (`ui/src/components/PersonaSwitcher.jsx`)
   - Sélection visuelle des personas
   - Affichage des traits de personnalité
   - Statistiques d'utilisation

### Flux de Données

1. **Initialisation**: Le PersonaManager charge toutes les personas au démarrage
2. **Sélection**: L'utilisateur change de persona via l'API ou l'interface
3. **Formatage**: Toutes les réponses sont formatées selon la persona active
4. **Persistance**: L'état est sauvegardé en mémoire persistante

## 🔧 Configuration

### Variables d'Environnement

```bash
# URL du service Brain API
BRAIN_API_URL=http://localhost:8001

# Persona par défaut au démarrage
DEFAULT_PERSONA=jarvis_classic

# Activation du système de personas
PERSONAS_ENABLED=true
```

### Personnalisation

Pour ajouter une nouvelle persona :

1. Créer une classe héritant de `BasePersona`
2. Implémenter toutes les méthodes abstraites
3. Ajouter la classe au registry du `PersonaManager`
4. Mettre à jour l'interface React si nécessaire

## 📊 Métriques et Analytiques

Le système collecte automatiquement :
- Nombre d'utilisations par persona
- Transitions entre personas
- Temps d'utilisation
- Contextes d'usage
- Préférences utilisateur

## 🔒 Sécurité

- Validation des entrées utilisateur
- Sanitisation des réponses formatées
- Contrôle d'accès aux changements de persona
- Logs de sécurité pour EDITH

## 🐛 Dépannage

### Problèmes Courants

1. **Persona ne change pas**
   - Vérifier que le Brain API est démarré
   - Vérifier les logs du PersonaManager
   - Tester l'endpoint `/api/persona/current`

2. **Formatage incorrect**
   - Vérifier la persona active
   - Contrôler le contexte passé
   - Consulter les logs de formatage

3. **Interface ne se met pas à jour**
   - Actualiser les données personas
   - Vérifier les props du PersonaSwitcher
   - Contrôler la connexion API

### Logs Utiles

```bash
# Logs du PersonaManager
grep "PersonaManager" logs/brain-api.log

# Logs de changement de persona
grep "Persona changée" logs/brain-api.log

# Logs de formatage
grep "formatage persona" logs/brain-api.log
```

## 🚀 Prochaines Étapes

### Améliorations Prévues

1. **Adaptation Dynamique**
   - Changement automatique selon le contexte
   - Apprentissage des préférences utilisateur
   - Suggestions proactives

2. **Nouvelles Personas**
   - Personas personnalisées par utilisateur
   - Personas spécialisées par domaine
   - Import/export de configurations

3. **Intégration Avancée**
   - Synchronisation avec TTS pour voix différentes
   - Adaptation de l'interface visuelle
   - Métriques avancées d'engagement

## 📝 Contributeurs

- Architecture: Système modulaire extensible
- Personas: Inspirées des films Marvel
- Interface: Design holographique Iron Man
- Tests: Suite complète automatisée

---

*Système développé pour JARVIS AI 2025 - "Just A Rather Very Intelligent System"*