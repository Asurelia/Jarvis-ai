#!/bin/bash

# 🧪 Script d'initialisation des tests JARVIS
# Prépare l'environnement de test et lance les tests

set -e

echo "🚀 Initialisation de l'environnement de test JARVIS..."

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des variables d'environnement
check_env_vars() {
    log_info "Vérification des variables d'environnement..."
    
    required_vars=(
        "TEST_DATABASE_URL"
        "TEST_REDIS_URL"
        "TEST_API_URL"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "Variable d'environnement manquante: $var"
            exit 1
        else
            log_success "✓ $var définie"
        fi
    done
}

# Attendre que les services soient prêts
wait_for_service() {
    local service_name=$1
    local service_url=$2
    local max_attempts=30
    local attempt=1
    
    log_info "Attente du service $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sSf "$service_url" > /dev/null 2>&1; then
            log_success "✓ $service_name est prêt"
            return 0
        fi
        
        log_info "Tentative $attempt/$max_attempts - $service_name pas encore prêt..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "✗ $service_name n'est pas accessible après $max_attempts tentatives"
    return 1
}

# Initialisation de la base de données de test
init_test_database() {
    log_info "Initialisation de la base de données de test..."
    
    # Attendre que PostgreSQL soit prêt
    until pg_isready -h $(echo $TEST_DATABASE_URL | sed -n 's|.*@\([^:]*\):.*|\1|p') -p $(echo $TEST_DATABASE_URL | sed -n 's|.*:\([0-9]*\)/.*|\1|p'); do
        log_info "Attente de PostgreSQL..."
        sleep 1
    done
    
    # Créer les tables de test
    python -c "
from sqlalchemy import create_engine
from core.ai.memory_system import Base
engine = create_engine('$TEST_DATABASE_URL')
Base.metadata.create_all(engine)
print('Tables de test créées')
" || log_warning "Impossible de créer les tables de test"
    
    log_success "Base de données de test initialisée"
}

# Vérification de Redis
check_redis() {
    log_info "Vérification de Redis..."
    
    redis_host=$(echo $TEST_REDIS_URL | sed -n 's|redis://\([^:]*\):.*|\1|p')
    redis_port=$(echo $TEST_REDIS_URL | sed -n 's|redis://[^:]*:\([0-9]*\)|\1|p')
    
    if redis-cli -h "$redis_host" -p "$redis_port" ping > /dev/null 2>&1; then
        log_success "✓ Redis accessible"
    else
        log_error "✗ Redis non accessible"
        return 1
    fi
}

# Préparation des données de test
prepare_test_data() {
    log_info "Préparation des données de test..."
    
    # Créer les répertoires nécessaires
    mkdir -p /app/tests/data/audio
    mkdir -p /app/tests/data/images
    mkdir -p /app/tests/data/models
    mkdir -p /app/test-results
    mkdir -p /app/coverage
    mkdir -p /app/screenshots
    
    # Générer des fichiers audio de test si nécessaire
    if [ ! -f "/app/tests/data/audio/test_sample.wav" ]; then
        log_info "Génération des échantillons audio de test..."
        python -c "
import numpy as np
import wave
import struct

# Générer un signal de test (440 Hz, 1 seconde)
sample_rate = 16000
duration = 1.0
frequency = 440
t = np.linspace(0, duration, int(sample_rate * duration))
signal = np.sin(2 * np.pi * frequency * t) * 0.3

# Sauvegarder en WAV
with wave.open('/app/tests/data/audio/test_sample.wav', 'w') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    for sample in signal:
        wav_file.writeframes(struct.pack('<h', int(sample * 32767)))

print('Échantillon audio de test généré')
"
    fi
    
    # Créer une image de test si nécessaire
    if [ ! -f "/app/tests/data/images/test_image.png" ]; then
        log_info "Génération d'image de test..."
        python -c "
import numpy as np
from PIL import Image

# Créer une image de test simple
img_array = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
img = Image.fromarray(img_array)
img.save('/app/tests/data/images/test_image.png')

print('Image de test générée')
"
    fi
    
    log_success "Données de test préparées"
}

# Vérification de l'intégrité des tests
check_test_integrity() {
    log_info "Vérification de l'intégrité des tests..."
    
    # Vérifier que les modules Python peuvent être importés
    python -c "
import sys
sys.path.append('/app')
try:
    from tests.test_new_components import TestModuleImports
    from core.agent import JarvisAgent
    print('✓ Imports des modules OK')
except Exception as e:
    print(f'✗ Erreur d import: {e}')
    sys.exit(1)
"
    
    # Vérifier la syntaxe des tests JavaScript
    if command -v node &> /dev/null; then
        log_info "Vérification de la syntaxe JavaScript..."
        cd /app/ui && npm run lint:check || log_warning "Problèmes de linting JavaScript détectés"
    fi
    
    log_success "Intégrité des tests vérifiée"
}

# Fonction principale
main() {
    log_info "🧪 Démarrage de l'initialisation des tests JARVIS"
    
    # Vérifications préliminaires
    check_env_vars
    
    # Attendre les services
    wait_for_service "API" "${TEST_API_URL}/health"
    wait_for_service "UI" "${TEST_UI_URL}"
    
    # Initialiser les composants
    init_test_database
    check_redis
    prepare_test_data
    check_test_integrity
    
    log_success "🎉 Environnement de test initialisé avec succès !"
    
    # Afficher les informations de test
    echo ""
    echo "📊 Informations de test:"
    echo "  - Base de données: $TEST_DATABASE_URL"
    echo "  - Redis: $TEST_REDIS_URL"
    echo "  - API: $TEST_API_URL"
    echo "  - Interface: ${TEST_UI_URL:-http://ui-test:80}"
    echo ""
    
    # Lancer les tests si des arguments sont fournis
    if [ "$#" -gt 0 ]; then
        log_info "🚀 Lancement des tests avec: $@"
        exec "$@"
    else
        log_info "🎯 Environnement prêt pour les tests manuels"
        exec /bin/bash
    fi
}

# Gestion des signaux pour un arrêt propre
cleanup() {
    log_info "🧹 Nettoyage en cours..."
    
    # Arrêter les processus de test en cours
    pkill -f pytest || true
    pkill -f playwright || true
    
    # Nettoyer les fichiers temporaires
    rm -rf /tmp/jarvis-test-* || true
    
    log_info "Nettoyage terminé"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Point d'entrée
main "$@"