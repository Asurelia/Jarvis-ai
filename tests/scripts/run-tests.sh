#!/bin/bash

# 🚀 Script de lancement des tests JARVIS
# Usage: ./run-tests.sh [type] [options]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.test.yml"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Fonctions utilitaires
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "${PURPLE}[JARVIS]${NC} $1"; }

# Fonction d'aide
show_help() {
    cat << EOF
🧪 Script de lancement des tests JARVIS

Usage: $0 [TYPE] [OPTIONS]

TYPES DE TESTS:
  unit              Tests unitaires uniquement
  integration       Tests d'intégration des services
  ui                Tests de l'interface utilisateur
  e2e               Tests end-to-end complets
  performance       Tests de performance et charge
  security          Tests de sécurité
  all               Tous les tests (par défaut)

OPTIONS:
  --build           Reconstruire les images Docker
  --clean           Nettoyer les volumes avant les tests
  --verbose         Mode verbose pour les logs
  --parallel        Lancer les tests en parallèle
  --coverage        Générer un rapport de couverture
  --report          Générer un rapport HTML
  --no-cache        Ne pas utiliser le cache Docker
  --help            Afficher cette aide

EXEMPLES:
  $0 unit --verbose
  $0 integration --build --clean
  $0 e2e --coverage --report
  $0 performance --parallel
  $0 all --build --clean --verbose

PROFILS DOCKER COMPOSE:
  - unit-tests: Services minimaux pour tests unitaires
  - integration-tests: Services pour tests d'intégration
  - full-tests: Tous les services pour tests E2E
  - perf-tests: Services pour tests de performance
  - security-tests: Services pour tests de sécurité

EOF
}

# Vérifier les prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Fichier docker-compose.test.yml non trouvé: $COMPOSE_FILE"
        exit 1
    fi
    
    log_success "Prérequis OK"
}

# Nettoyer l'environnement
cleanup_environment() {
    log_info "Nettoyage de l'environnement de test..."
    
    # Arrêter et supprimer les conteneurs de test
    docker-compose -f "$COMPOSE_FILE" down --volumes --remove-orphans 2>/dev/null || true
    
    # Supprimer les images si demandé
    if [ "$CLEAN" = true ]; then
        log_info "Suppression des volumes et images de test..."
        docker-compose -f "$COMPOSE_FILE" down --volumes --rmi all 2>/dev/null || true
        docker system prune -f --volumes 2>/dev/null || true
    fi
    
    # Créer les répertoires de résultats
    mkdir -p "$PROJECT_DIR/tests/results"
    mkdir -p "$PROJECT_DIR/coverage"
    
    log_success "Environnement nettoyé"
}

# Construire les images
build_images() {
    log_info "Construction des images Docker..."
    
    local build_args=""
    if [ "$NO_CACHE" = true ]; then
        build_args="--no-cache"
    fi
    
    if [ "$VERBOSE" = true ]; then
        build_args="$build_args --progress=plain"
    fi
    
    docker-compose -f "$COMPOSE_FILE" build $build_args
    
    log_success "Images construites"
}

# Lancer les tests unitaires
run_unit_tests() {
    log_header "🧪 Lancement des tests unitaires"
    
    local services="test-runner test-memory-db test-redis"
    local cmd="python -m pytest tests/test_new_components.py -v"
    
    if [ "$COVERAGE" = true ]; then
        cmd="$cmd --cov=core --cov=services --cov-report=html:/app/coverage"
    fi
    
    docker-compose -f "$COMPOSE_FILE" run --rm test-runner $cmd
}

# Lancer les tests d'intégration
run_integration_tests() {
    log_header "🔗 Lancement des tests d'intégration"
    
    # Démarrer les services nécessaires
    docker-compose -f "$COMPOSE_FILE" up -d brain-api-test test-memory-db test-redis
    
    # Attendre que les services soient prêts
    log_info "Attente des services..."
    sleep 10
    
    # Lancer les tests
    local cmd="python -m pytest tests/ -k 'integration' -v"
    if [ "$COVERAGE" = true ]; then
        cmd="$cmd --cov=core --cov=services"
    fi
    
    docker-compose -f "$COMPOSE_FILE" run --rm test-runner $cmd
}

# Lancer les tests UI
run_ui_tests() {
    log_header "🎨 Lancement des tests UI"
    
    # Démarrer l'interface
    docker-compose -f "$COMPOSE_FILE" up -d ui-test brain-api-test test-memory-db test-redis
    
    # Attendre que l'UI soit prête
    log_info "Attente de l'interface utilisateur..."
    sleep 15
    
    # Lancer les tests UI
    docker-compose -f "$COMPOSE_FILE" run --rm test-runner bash -c "
        cd ui && npm test -- --coverage --watchAll=false
    "
    
    # Tests JavaScript
    docker-compose -f "$COMPOSE_FILE" run --rm test-runner bash -c "
        cd ui && npm run test:integration
    "
}

# Lancer les tests E2E
run_e2e_tests() {
    log_header "🎯 Lancement des tests E2E"
    
    # Démarrer tous les services
    docker-compose -f "$COMPOSE_FILE" --profile full-tests up -d
    
    # Attendre que tous les services soient prêts
    log_info "Attente de tous les services..."
    sleep 30
    
    # Vérifier la santé des services
    log_info "Vérification de la santé des services..."
    docker-compose -f "$COMPOSE_FILE" ps
    
    # Lancer les tests E2E
    docker-compose -f "$COMPOSE_FILE" run --rm e2e-test
}

# Lancer les tests de performance
run_performance_tests() {
    log_header "⚡ Lancement des tests de performance"
    
    # Démarrer les services pour les tests de perf
    docker-compose -f "$COMPOSE_FILE" --profile perf-tests up -d
    
    # Attendre les services
    sleep 20
    
    # Tests de charge avec K6
    docker-compose -f "$COMPOSE_FILE" run --rm performance-test
    
    # Tests de performance Python
    docker-compose -f "$COMPOSE_FILE" run --rm test-runner bash -c "
        python -m pytest tests/test_performance.py -v --benchmark-only
    "
}

# Lancer les tests de sécurité
run_security_tests() {
    log_header "🔒 Lancement des tests de sécurité"
    
    # Démarrer les services pour les tests de sécurité
    docker-compose -f "$COMPOSE_FILE" --profile security-tests up -d
    
    # Attendre les services
    sleep 15
    
    # Tests de sécurité avec OWASP ZAP
    docker-compose -f "$COMPOSE_FILE" run --rm security-test
    
    # Tests de sécurité Python
    docker-compose -f "$COMPOSE_FILE" run --rm test-runner bash -c "
        bandit -r core/ services/ -f json -o /app/tests/results/security-python.json || true
        safety check --json --output /app/tests/results/safety.json || true
    "
}

# Générer les rapports
generate_reports() {
    if [ "$REPORT" = true ]; then
        log_info "Génération des rapports..."
        
        # Créer un rapport HTML consolidé
        docker-compose -f "$COMPOSE_FILE" run --rm test-runner bash -c "
            python tests/scripts/generate_report.py \
                --coverage /app/coverage \
                --results /app/tests/results \
                --output /app/tests/results/consolidated-report.html
        "
        
        log_success "Rapports générés dans tests/results/"
    fi
}

# Afficher les résultats
show_results() {
    log_header "📊 Résultats des tests"
    
    # Copier les résultats vers l'hôte
    if [ -d "$PROJECT_DIR/tests/results" ]; then
        docker-compose -f "$COMPOSE_FILE" run --rm test-runner bash -c "
            cp -r /app/tests/results/* /app/tests/results/ 2>/dev/null || true
            cp -r /app/coverage/* /app/coverage/ 2>/dev/null || true
        "
    fi
    
    echo ""
    echo "📁 Fichiers de résultats disponibles:"
    find "$PROJECT_DIR/tests/results" -name "*.html" -o -name "*.json" -o -name "*.xml" 2>/dev/null | head -10 || echo "  Aucun rapport trouvé"
    
    if [ -f "$PROJECT_DIR/coverage/index.html" ]; then
        echo "📈 Rapport de couverture: file://$PROJECT_DIR/coverage/index.html"
    fi
    
    echo ""
}

# Fonction principale
main() {
    local test_type="${1:-all}"
    
    # Parse des arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build) BUILD=true ;;
            --clean) CLEAN=true ;;
            --verbose) VERBOSE=true ;;
            --parallel) PARALLEL=true ;;
            --coverage) COVERAGE=true ;;
            --report) REPORT=true ;;
            --no-cache) NO_CACHE=true ;;
            --help) show_help; exit 0 ;;
            unit|integration|ui|e2e|performance|security|all) test_type="$1" ;;
            *) log_warning "Option inconnue: $1" ;;
        esac
        shift
    done
    
    # Configuration de l'environnement
    export COMPOSE_PROJECT_NAME="jarvis-test"
    
    if [ "$VERBOSE" = true ]; then
        set -x
        export DOCKER_BUILDKIT=0
    fi
    
    # Vérifications
    check_prerequisites
    
    # Nettoyage si demandé
    if [ "$CLEAN" = true ] || [ "$BUILD" = true ]; then
        cleanup_environment
    fi
    
    # Construction si demandée
    if [ "$BUILD" = true ]; then
        build_images
    fi
    
    log_header "🚀 Démarrage des tests JARVIS - Type: $test_type"
    
    # Lancer les tests selon le type
    case $test_type in
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        ui)
            run_ui_tests
            ;;
        e2e)
            run_e2e_tests
            ;;
        performance)
            run_performance_tests
            ;;
        security)
            run_security_tests
            ;;
        all)
            run_unit_tests
            run_integration_tests
            run_ui_tests
            run_e2e_tests
            ;;
        *)
            log_error "Type de test inconnu: $test_type"
            show_help
            exit 1
            ;;
    esac
    
    # Génération des rapports
    generate_reports
    
    # Nettoyage final
    log_info "Arrêt des services de test..."
    docker-compose -f "$COMPOSE_FILE" down
    
    # Affichage des résultats
    show_results
    
    log_success "🎉 Tests terminés avec succès !"
}

# Gestion des signaux
cleanup_on_exit() {
    log_info "Interruption détectée, nettoyage..."
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    exit 0
}

trap cleanup_on_exit SIGINT SIGTERM

# Point d'entrée
main "$@"