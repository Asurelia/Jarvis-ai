# 🧪 Tests Automatisés JARVIS

Ce répertoire contient tous les scripts de test automatisés pour le système JARVIS AI, incluant les tests unitaires, d'intégration, de performance et end-to-end.

## 📋 Structure des Tests

```
tests/
├── test_new_components.py      # Tests Python des nouveaux modules
├── test_ui_integration.js      # Tests d'intégration UI React
├── requirements-test.txt       # Dépendances Python pour les tests
├── scripts/
│   ├── run-tests.sh           # Script principal de lancement
│   ├── init-tests.sh          # Initialisation de l'environnement
│   └── generate_report.py     # Générateur de rapports
├── e2e/
│   ├── specs/                 # Tests end-to-end Playwright
│   ├── playwright.config.js   # Configuration Playwright
│   └── Dockerfile            # Image Docker pour E2E
├── performance/
│   └── load_test.js          # Tests de charge K6
└── results/                   # Résultats et rapports
```

## 🚀 Démarrage Rapide

### 1. Tests Unitaires Simple

```bash
# Depuis la racine du projet JARVIS
cd tests
./scripts/run-tests.sh unit --verbose
```

### 2. Tests Complets avec Docker

```bash
# Tous les types de tests
./scripts/run-tests.sh all --build --clean --coverage --report

# Tests spécifiques
./scripts/run-tests.sh integration --verbose
./scripts/run-tests.sh performance --parallel
./scripts/run-tests.sh e2e --coverage
```

### 3. Tests Sans Docker (Local)

```bash
# Installation des dépendances
pip install -r requirements-test.txt

# Tests Python
python -m pytest test_new_components.py -v

# Tests JavaScript (depuis ui/)
cd ../ui && npm test -- test_ui_integration.js
```

## 📊 Types de Tests

### 🧪 Tests Unitaires (`test_new_components.py`)

Teste l'importation et le fonctionnement des nouveaux modules JARVIS :

- **Modules Core** : Agent, AI, Vision, Voice, Control
- **WebWorkers** : Simulation du traitement parallèle
- **WASM** : Tests des modules WebAssembly simulés
- **Communication** : API, WebSocket, Redis, Ollama
- **Performance** : Métriques de temps de réponse

```python
# Exemple d'utilisation
from tests.test_new_components import TestModuleImports
test = TestModuleImports()
test.test_core_imports()
```

### 🎨 Tests UI (`test_ui_integration.js`)

Teste les composants React et les interactions utilisateur :

- **Composants** : CognitiveIntelligenceModule, Sphere3D, ChatWindow
- **Interactions** : Clavier, souris, navigation
- **Performance** : Temps de rendu, utilisation mémoire
- **Compatibilité** : Responsive, navigateurs

```javascript
// Exemple de test
import { render, screen } from '@testing-library/react';
import CognitiveIntelligenceModule from '../ui/src/components/CognitiveIntelligenceModule';

test('doit afficher les états cognitifs', () => {
  render(<CognitiveIntelligenceModule />);
  expect(screen.getByText(/Réflexion|Analyse/)).toBeInTheDocument();
});
```

### 🎯 Tests E2E (`e2e/specs/`)

Tests end-to-end complets avec Playwright :

- **Interface** : Navigation, responsivité, accessibilité
- **Fonctionnalités** : Chat, voix, vision, modules avancés
- **Intégration** : WebSocket, API, services
- **Multi-plateforme** : Chrome, Firefox, Safari, Mobile

```javascript
// Exemple de test E2E
test('doit permettre une conversation complète', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="chat-button"]');
  await page.fill('input', 'Bonjour JARVIS');
  await page.press('input', 'Enter');
  await expect(page.getByText(/réponse/i)).toBeVisible();
});
```

### ⚡ Tests de Performance (`performance/`)

Tests de charge et performance avec K6 :

- **API** : Temps de réponse, débit, gestion des erreurs
- **WebSocket** : Connexions concurrentes, latence
- **UI** : Temps de chargement, animations
- **Services** : STT, TTS, contrôle système

```javascript
// Exemple de test de charge
export default function() {
  const response = http.get('http://api:8080/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
}
```

## 🐳 Configuration Docker

### Docker Compose Test

Le fichier `docker-compose.test.yml` configure un environnement de test complet :

```yaml
services:
  # Services de test isolés
  brain-api-test:     # API principale (port 8081)
  test-memory-db:     # PostgreSQL test (port 5433)
  test-redis:         # Redis test (port 6380)
  test-ollama:        # Ollama léger (port 11435)
  
  # Tests runners
  test-runner:        # Tests Python
  e2e-test:          # Tests Playwright
  performance-test:   # Tests K6
  security-test:     # Tests OWASP ZAP
```

### Profils Docker Compose

```bash
# Tests unitaires uniquement
docker-compose -f docker-compose.test.yml --profile unit-tests up

# Tests d'intégration
docker-compose -f docker-compose.test.yml --profile integration-tests up

# Tests complets E2E
docker-compose -f docker-compose.test.yml --profile full-tests up

# Tests de performance
docker-compose -f docker-compose.test.yml --profile perf-tests up

# Tests de sécurité
docker-compose -f docker-compose.test.yml --profile security-tests up
```

## 🎛️ Options du Script de Test

### `run-tests.sh [TYPE] [OPTIONS]`

**Types de Tests :**
- `unit` - Tests unitaires Python uniquement
- `integration` - Tests d'intégration des services
- `ui` - Tests de l'interface utilisateur React
- `e2e` - Tests end-to-end complets avec Playwright
- `performance` - Tests de performance et charge avec K6
- `security` - Tests de sécurité avec OWASP ZAP
- `all` - Tous les tests (défaut)

**Options :**
- `--build` - Reconstruire les images Docker
- `--clean` - Nettoyer les volumes avant les tests
- `--verbose` - Mode verbose pour les logs détaillés
- `--parallel` - Lancer les tests en parallèle
- `--coverage` - Générer un rapport de couverture de code
- `--report` - Générer un rapport HTML consolidé
- `--no-cache` - Ne pas utiliser le cache Docker

### Exemples d'Utilisation

```bash
# Tests de développement rapides
./scripts/run-tests.sh unit --verbose

# Tests d'intégration avec reconstruction
./scripts/run-tests.sh integration --build --clean

# Tests E2E complets avec rapports
./scripts/run-tests.sh e2e --coverage --report

# Tests de performance en parallèle
./scripts/run-tests.sh performance --parallel

# Suite complète pour CI/CD
./scripts/run-tests.sh all --build --clean --verbose --coverage --report
```

## 📊 Rapports et Métriques

### Génération de Rapports

```bash
# Rapport consolidé automatique
./scripts/run-tests.sh all --report

# Génération manuelle
python scripts/generate_report.py \
  --results ./results \
  --coverage ./coverage \
  --output ./results/consolidated-report.html
```

### Types de Rapports

1. **HTML Consolidé** : Vue d'ensemble avec métriques visuelles
2. **Coverage HTML** : Couverture de code détaillée par fichier
3. **Playwright HTML** : Rapports E2E interactifs avec traces
4. **K6 JSON** : Métriques de performance détaillées
5. **JUnit XML** : Pour intégration CI/CD

### Métriques Surveillées

- **Taux de Réussite** : Pourcentage de tests passés
- **Couverture de Code** : Lignes et branches couvertes
- **Performance** : Temps de réponse, débit, latence
- **Accessibilité** : Contraste, navigation clavier
- **Sécurité** : Vulnérabilités détectées

## 🔧 Configuration Avancée

### Variables d'Environnement

```bash
# URLs des services
export TEST_API_URL="http://localhost:8081"
export TEST_UI_URL="http://localhost:3001"
export TEST_DATABASE_URL="postgresql://postgres:test123@localhost:5433/jarvis_test"
export TEST_REDIS_URL="redis://localhost:6380"

# Configuration des tests
export PYTEST_ARGS="--verbose --tb=short --color=yes"
export PLAYWRIGHT_BROWSER="chromium"
export K6_VUS=10  # Utilisateurs virtuels
```

### Personnalisation des Tests

```python
# test_custom.py - Tests personnalisés
import unittest
from tests.test_new_components import TestModuleImports

class CustomJarvisTests(TestModuleImports):
    def test_custom_feature(self):
        # Votre test personnalisé
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
```

## 🚨 Dépannage

### Problèmes Courants

1. **Services non disponibles**
```bash
# Vérifier les services
docker-compose -f docker-compose.test.yml ps
docker-compose -f docker-compose.test.yml logs brain-api-test
```

2. **Tests timeout**
```bash
# Augmenter les timeouts
export PYTEST_TIMEOUT=300
export PLAYWRIGHT_TIMEOUT=60000
```

3. **Problèmes de permissions**
```bash
# Fixer les permissions
chmod +x scripts/*.sh
sudo chown -R $USER:$USER ./tests/results
```

4. **Mémoire insuffisante**
```bash
# Limiter les workers
export PYTEST_WORKERS=2
export PLAYWRIGHT_WORKERS=1
```

### Logs et Debug

```bash
# Logs détaillés
./scripts/run-tests.sh unit --verbose

# Debug Playwright
npx playwright test --debug

# Logs Docker
docker-compose -f docker-compose.test.yml logs --follow
```

## 📈 Intégration CI/CD

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: JARVIS Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: ./tests/scripts/run-tests.sh all --build --coverage --report
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: tests/results/
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh './tests/scripts/run-tests.sh all --build --coverage'
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'tests/results',
                        reportFiles: 'consolidated-report.html',
                        reportName: 'JARVIS Test Report'
                    ])
                }
            }
        }
    }
}
```

## 🏗️ Développement des Tests

### Ajouter de Nouveaux Tests

1. **Test Python**
```python
# Dans test_new_components.py
def test_my_new_feature(self):
    from core.my_module import MyClass
    instance = MyClass()
    self.assertEqual(instance.method(), "expected_value")
```

2. **Test React**
```javascript
// Dans test_ui_integration.js
test('mon nouveau composant', () => {
  render(<MonComposant />);
  expect(screen.getByText('Mon Texte')).toBeInTheDocument();
});
```

3. **Test E2E**
```javascript
// Dans e2e/specs/my-feature.spec.js
test('ma nouvelle fonctionnalité', async ({ page }) => {
  await page.goto('/ma-page');
  await expect(page.getByText('Ma Fonctionnalité')).toBeVisible();
});
```

### Best Practices

- **Nommage** : Tests descriptifs en français
- **Isolation** : Chaque test doit être indépendant
- **Cleanup** : Nettoyer les ressources après les tests
- **Timeouts** : Utiliser des timeouts appropriés
- **Assertions** : Vérifications spécifiques et claires

## 🤝 Contribution

Pour contribuer aux tests :

1. Créer une branche feature : `git checkout -b feature/new-tests`
2. Ajouter vos tests avec documentation
3. Tester localement : `./scripts/run-tests.sh all --verbose`
4. Créer une PR avec les résultats de tests

## 📞 Support

Pour toute question ou problème :

- 📧 Email : support@jarvis-ai.local
- 📖 Documentation : `/docs`
- 🐛 Issues : GitHub Issues
- 💬 Chat : Canal #tests sur Discord

---

🤖 **Tests automatisés JARVIS** - Garantir la qualité et la fiabilité de l'IA