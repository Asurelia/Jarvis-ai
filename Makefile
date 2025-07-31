# 🧪 Makefile pour JARVIS AI - Tests et Développement
# Commandes pour faciliter le développement et les tests

.PHONY: help install install-dev test test-unit test-integration test-security test-performance test-all lint format coverage clean docker-test setup-test-env

# Variables
PYTHON := python3
PIP := pip3
PYTEST := pytest
VENV := venv
TEST_REPORTS := tests/reports
COVERAGE_MIN := 80

# Couleurs pour l'affichage
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## 📖 Afficher l'aide
	@echo "🤖 JARVIS AI - Commandes de développement"
	@echo ""
	@echo "📦 INSTALLATION:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(install|setup)"
	@echo ""
	@echo "🧪 TESTS:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "test"
	@echo ""
	@echo "🔧 DÉVELOPPEMENT:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(lint|format|clean|coverage)"
	@echo ""
	@echo "🐳 DOCKER:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(RED)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "docker"

# ==========================================
# INSTALLATION ET SETUP
# ==========================================

install: ## 📦 Installer les dépendances de production
	@echo "$(BLUE)📦 Installation des dépendances JARVIS...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dépendances installées$(NC)"

install-dev: install ## 🔧 Installer les dépendances de développement
	@echo "$(BLUE)🔧 Installation des dépendances de développement...$(NC)"
	$(PIP) install -r tests/requirements-test.txt
	@echo "$(GREEN)✅ Environnement de développement prêt$(NC)"

setup-venv: ## 🌐 Créer un environnement virtuel
	@echo "$(BLUE)🌐 Création de l'environnement virtuel...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(YELLOW)⚠️  Activez l'environnement avec: source $(VENV)/bin/activate$(NC)"

setup-test-env: ## 🧪 Configurer l'environnement de test complet
	@echo "$(BLUE)🧪 Configuration de l'environnement de test...$(NC)"
	mkdir -p $(TEST_REPORTS)
	mkdir -p $(TEST_REPORTS)/coverage-html
	@echo "$(GREEN)✅ Environnement de test configuré$(NC)"

# ==========================================
# TESTS
# ==========================================

test: setup-test-env ## 🧪 Lancer tous les tests
	@echo "$(GREEN)🧪 Lancement de tous les tests JARVIS...$(NC)"
	$(PYTEST) --verbose

test-unit: setup-test-env ## ⚡ Tests unitaires rapides
	@echo "$(GREEN)⚡ Tests unitaires...$(NC)"
	$(PYTEST) -m "unit and not slow" --verbose

test-integration: setup-test-env ## 🔗 Tests d'intégration
	@echo "$(GREEN)🔗 Tests d'intégration...$(NC)"
	$(PYTEST) -m "integration" --verbose

test-security: setup-test-env ## 🔒 Tests de sécurité
	@echo "$(GREEN)🔒 Tests de sécurité...$(NC)"
	$(PYTEST) -m "security" tests/security/ --verbose

test-performance: setup-test-env ## 📊 Tests de performance
	@echo "$(GREEN)📊 Tests de performance...$(NC)"
	$(PYTEST) -m "performance" tests/performance/ --verbose

test-gpu: setup-test-env ## 🎮 Tests GPU AMD
	@echo "$(GREEN)🎮 Tests GPU AMD...$(NC)"
	$(PYTEST) -m "gpu" --verbose

test-backend: setup-test-env ## 🔧 Tests backend Python
	@echo "$(GREEN)🔧 Tests backend Python...$(NC)"
	$(PYTEST) tests/backend/ --verbose

test-personas: setup-test-env ## 🎭 Tests système de personas
	@echo "$(GREEN)🎭 Tests système de personas...$(NC)"
	$(PYTEST) tests/backend/test_personas.py -m "persona" --verbose

test-tts: setup-test-env ## 🗣️  Tests service TTS
	@echo "$(GREEN)🗣️ Tests service TTS...$(NC)"
	$(PYTEST) tests/backend/test_tts_service.py -m "tts" --verbose

test-brain-api: setup-test-env ## 🧠 Tests Brain API
	@echo "$(GREEN)🧠 Tests Brain API...$(NC)"
	$(PYTEST) tests/backend/test_brain_api.py -m "brain_api" --verbose

test-slow: setup-test-env ## 🐌 Tests lents (>30s)
	@echo "$(YELLOW)🐌 Tests lents...$(NC)"
	$(PYTEST) -m "slow" --verbose

test-watch: setup-test-env ## 👀 Tests en mode watch (redémarrage automatique)
	@echo "$(BLUE)👀 Mode watch activé...$(NC)"
	$(PYTEST) --verbose -f

test-parallel: setup-test-env ## ⚡ Tests en parallèle
	@echo "$(GREEN)⚡ Tests parallèles...$(NC)"
	$(PYTEST) -n auto --verbose

test-failed: setup-test-env ## 🔄 Relancer uniquement les tests échoués
	@echo "$(YELLOW)🔄 Tests échoués uniquement...$(NC)"
	$(PYTEST) --lf --verbose

test-with-docker: ## 🐳 Tests avec services Docker
	@echo "$(RED)🐳 Tests avec Docker...$(NC)"
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# ==========================================
# COVERAGE ET RAPPORTS
# ==========================================

coverage: setup-test-env ## 📊 Générer le rapport de couverture complet
	@echo "$(BLUE)📊 Génération du rapport de couverture...$(NC)"
	$(PYTEST) --cov=services --cov=core --cov=tools --cov-report=html:$(TEST_REPORTS)/coverage-html --cov-report=xml:$(TEST_REPORTS)/coverage.xml --cov-report=term-missing --cov-fail-under=$(COVERAGE_MIN)
	@echo "$(GREEN)✅ Rapport de couverture généré dans $(TEST_REPORTS)/coverage-html/index.html$(NC)"

coverage-open: coverage ## 🌐 Ouvrir le rapport de couverture dans le navigateur
	@echo "$(BLUE)🌐 Ouverture du rapport de couverture...$(NC)"
ifeq ($(OS),Windows_NT)
	start $(TEST_REPORTS)/coverage-html/index.html
else
	open $(TEST_REPORTS)/coverage-html/index.html || xdg-open $(TEST_REPORTS)/coverage-html/index.html
endif

report: setup-test-env ## 📋 Générer un rapport complet des tests
	@echo "$(BLUE)📋 Génération du rapport complet...$(NC)"
	$(PYTEST) --html=$(TEST_REPORTS)/report.html --self-contained-html --junit-xml=$(TEST_REPORTS)/junit.xml
	@echo "$(GREEN)✅ Rapport HTML généré: $(TEST_REPORTS)/report.html$(NC)"

# ==========================================
# QUALITÉ DE CODE
# ==========================================

lint: ## 🔍 Vérifier la qualité du code
	@echo "$(BLUE)🔍 Vérification de la qualité du code...$(NC)"
	@echo "$(YELLOW)📏 Flake8...$(NC)"
	-flake8 services/ core/ tools/ tests/ --max-line-length=120 --ignore=E203,W503
	@echo "$(YELLOW)🔍 Pylint...$(NC)"
	-pylint services/ core/ tools/ --disable=C0111,R0903,R0913
	@echo "$(YELLOW)📝 MyPy...$(NC)"
	-mypy services/ core/ tools/ --ignore-missing-imports
	@echo "$(GREEN)✅ Vérification terminée$(NC)"

format: ## 🎨 Formater le code avec Black
	@echo "$(BLUE)🎨 Formatage du code...$(NC)"
	black services/ core/ tools/ tests/ --line-length=120
	@echo "$(GREEN)✅ Code formaté$(NC)"

security-check: ## 🔒 Vérifier la sécurité du code
	@echo "$(BLUE)🔒 Vérification de sécurité...$(NC)"
	@echo "$(YELLOW)🛡️  Bandit...$(NC)"
	-bandit -r services/ core/ tools/ -f json -o $(TEST_REPORTS)/bandit-report.json
	@echo "$(YELLOW)🔍 Safety...$(NC)"
	-safety check --json --output $(TEST_REPORTS)/safety-report.json
	@echo "$(GREEN)✅ Vérification de sécurité terminée$(NC)"

# ==========================================
# FRONTEND (React)
# ==========================================

test-frontend: ## ⚛️  Tests frontend React
	@echo "$(GREEN)⚛️ Tests frontend React...$(NC)"
	cd ui && npm test -- --coverage --watchAll=false

test-frontend-watch: ## 👀 Tests frontend en mode watch
	@echo "$(BLUE)👀 Tests frontend en mode watch...$(NC)"
	cd ui && npm test

# ==========================================
# NETTOYAGE
# ==========================================

clean: ## 🧹 Nettoyer les fichiers temporaires
	@echo "$(YELLOW)🧹 Nettoyage des fichiers temporaires...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	@echo "$(GREEN)✅ Nettoyage terminé$(NC)"

clean-reports: ## 🗑️  Supprimer les rapports de tests
	@echo "$(YELLOW)🗑️ Suppression des rapports...$(NC)"
	rm -rf $(TEST_REPORTS)/*
	@echo "$(GREEN)✅ Rapports supprimés$(NC)"

clean-all: clean clean-reports ## 🗑️  Nettoyage complet
	@echo "$(GREEN)✅ Nettoyage complet terminé$(NC)"

# ==========================================
# DOCKER
# ==========================================

docker-build: ## 🐳 Construire les images Docker de test
	@echo "$(RED)🐳 Construction des images Docker...$(NC)"
	docker-compose -f docker-compose.test.yml build

docker-test: docker-build ## 🧪 Lancer les tests dans Docker
	@echo "$(RED)🧪 Tests dans Docker...$(NC)"
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit
	docker-compose -f docker-compose.test.yml down

docker-test-interactive: ## 🐳 Shell interactif dans le conteneur de test
	@echo "$(RED)🐳 Shell interactif...$(NC)"
	docker-compose -f docker-compose.test.yml run --rm test-runner bash

docker-clean: ## 🗑️  Nettoyer les conteneurs et images Docker
	@echo "$(RED)🗑️ Nettoyage Docker...$(NC)"
	docker-compose -f docker-compose.test.yml down --volumes --remove-orphans
	docker system prune -f

# ==========================================
# SURVEILLANCE ET MONITORING
# ==========================================

monitor-tests: ## 📊 Surveiller les tests en continu
	@echo "$(BLUE)📊 Surveillance des tests...$(NC)"
	watch -n 10 make test-unit

# ==========================================
# UTILS ET DEBUGGING
# ==========================================

debug-env: ## 🐛 Afficher les informations d'environnement
	@echo "$(BLUE)🐛 Informations d'environnement:$(NC)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Pytest: $(shell $(PYTEST) --version)"
	@echo "Répertoire courant: $(shell pwd)"
	@echo "Variables d'environnement JARVIS:"
	@env | grep -E "(JARVIS|TESTING)" || echo "Aucune variable JARVIS trouvée"

install-pre-commit: ## 🔗 Installer les hooks pre-commit
	@echo "$(BLUE)🔗 Installation des hooks pre-commit...$(NC)"
	pre-commit install
	@echo "$(GREEN)✅ Hooks pre-commit installés$(NC)"

validate: lint test coverage ## ✅ Validation complète (lint + tests + coverage)
	@echo "$(GREEN)✅ Validation complète réussie!$(NC)"

# ==========================================
# RACCOURCIS UTILES
# ==========================================

quick: test-unit ## ⚡ Tests rapides (alias pour test-unit)

full: test coverage report ## 📊 Suite complète (tests + coverage + rapport)

ci: lint test-parallel coverage ## 🤖 Pipeline CI (lint + tests parallèles + coverage)

dev-setup: setup-venv install-dev setup-test-env ## 🚀 Setup complet pour développement

# Message par défaut
default: help