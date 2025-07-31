#!/bin/bash
# Script pour lancer les tests d'intégration JARVIS AI
# Nécessite Docker et les services en cours d'exécution

set -e

echo "🧪 JARVIS AI - Tests d'Intégration et Performance"
echo "================================================="

# Variables
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$PROJECT_ROOT/test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Créer le répertoire de résultats
mkdir -p "$RESULTS_DIR"

# Vérifier que Docker est en cours d'exécution
echo "🐳 Vérification de Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker n'est pas en cours d'exécution!"
    exit 1
fi

# Vérifier les services JARVIS
echo "🔍 Vérification des services JARVIS..."
REQUIRED_SERVICES=(
    "jarvis_brain"
    "jarvis_tts"
    "jarvis_stt"
    "jarvis_system_control"
    "jarvis_terminal"
    "jarvis_mcp_gateway"
    "jarvis_autocomplete"
    "jarvis_redis"
    "jarvis_memory_db"
)

MISSING_SERVICES=()
for service in "${REQUIRED_SERVICES[@]}"; do
    if ! docker ps --format "table {{.Names}}" | grep -q "$service"; then
        MISSING_SERVICES+=("$service")
    fi
done

if [ ${#MISSING_SERVICES[@]} -gt 0 ]; then
    echo "❌ Services manquants : ${MISSING_SERVICES[*]}"
    echo "Lancement des services..."
    docker-compose up -d
    echo "⏳ Attente du démarrage des services (30s)..."
    sleep 30
fi

# Installer les dépendances de test si nécessaire
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

echo "📦 Installation des dépendances de test..."
pip install -q pytest pytest-asyncio pytest-benchmark pytest-cov docker aiohttp websockets requests

# Exécuter les tests d'intégration
echo ""
echo "🧪 Lancement des tests d'intégration..."
echo "======================================="

# Tests Docker Services
echo ""
echo "🐳 Tests des services Docker..."
pytest tests/integration/test_docker_services.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/docker-services-$TIMESTAMP.xml" || true

# Tests API Integration
echo ""
echo "🔌 Tests d'intégration API..."
pytest tests/integration/test_api_integration.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/api-integration-$TIMESTAMP.xml" || true

# Tests WebSocket
echo ""
echo "🌐 Tests WebSocket..."
pytest tests/integration/test_websocket_integration.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/websocket-$TIMESTAMP.xml" || true

# Tests Audio Pipeline
echo ""
echo "🎵 Tests pipeline audio..."
pytest tests/integration/test_audio_pipeline.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/audio-pipeline-$TIMESTAMP.xml" || true

# Exécuter les tests de performance
echo ""
echo "⚡ Lancement des tests de performance..."
echo "======================================="

# Tests de charge Brain API
echo ""
echo "🧠 Tests de charge Brain API..."
pytest tests/performance/test_load_brain_api.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/load-brain-api-$TIMESTAMP.xml" || true

# Tests latence audio
echo ""
echo "🎤 Tests latence audio..."
pytest tests/performance/test_audio_latency.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/audio-latency-$TIMESTAMP.xml" || true

# Tests débit WebSocket
echo ""
echo "📊 Tests débit WebSocket..."
pytest tests/performance/test_websocket_throughput.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/websocket-throughput-$TIMESTAMP.xml" || true

# Tests monitoring GPU
echo ""
echo "🎮 Tests performance GPU monitoring..."
pytest tests/performance/test_gpu_monitoring.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/gpu-monitoring-$TIMESTAMP.xml" || true

# Exécuter les tests de résilience
echo ""
echo "🛡️ Lancement des tests de résilience..."
echo "======================================="

# Tests de coupures réseau
echo ""
echo "🔌 Tests coupures réseau..."
pytest tests/resilience/test_network_failures.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/network-failures-$TIMESTAMP.xml" || true

# Tests de récupération
echo ""
echo "🔄 Tests récupération après crash..."
pytest tests/resilience/test_service_recovery.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/service-recovery-$TIMESTAMP.xml" || true

# Tests limites ressources
echo ""
echo "📈 Tests limites ressources..."
pytest tests/resilience/test_resource_limits.py -v --tb=short \
    --junit-xml="$RESULTS_DIR/resource-limits-$TIMESTAMP.xml" || true

# Générer le rapport de synthèse
echo ""
echo "📊 Génération du rapport de synthèse..."
echo "======================================"

# Compter les résultats
TOTAL_TESTS=$(find "$RESULTS_DIR" -name "*-$TIMESTAMP.xml" -exec grep -c 'testcase' {} \; | awk '{sum += $1} END {print sum}')
FAILED_TESTS=$(find "$RESULTS_DIR" -name "*-$TIMESTAMP.xml" -exec grep -c 'failure\|error' {} \; | awk '{sum += $1} END {print sum}')
SUCCESS_RATE=$((100 * (TOTAL_TESTS - FAILED_TESTS) / TOTAL_TESTS))

# Créer le rapport HTML
cat > "$RESULTS_DIR/report-$TIMESTAMP.html" <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>JARVIS AI - Rapport de Tests d'Intégration</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #0a0a0a; color: #00d4ff; }
        h1 { color: #00ff88; text-align: center; }
        .summary { background: rgba(0,212,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0; }
        .metric { display: inline-block; margin: 10px 20px; }
        .success { color: #00ff88; }
        .failure { color: #ff6b00; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border: 1px solid #00d4ff; }
        th { background: rgba(0,212,255,0.2); }
    </style>
</head>
<body>
    <h1>🤖 JARVIS AI - Rapport de Tests d'Intégration</h1>
    <div class="summary">
        <h2>📊 Résumé</h2>
        <div class="metric">Total Tests: <strong>$TOTAL_TESTS</strong></div>
        <div class="metric">Réussis: <strong class="success">$((TOTAL_TESTS - FAILED_TESTS))</strong></div>
        <div class="metric">Échoués: <strong class="failure">$FAILED_TESTS</strong></div>
        <div class="metric">Taux de Réussite: <strong class="$([[ $SUCCESS_RATE -ge 80 ]] && echo "success" || echo "failure")">$SUCCESS_RATE%</strong></div>
        <div class="metric">Date: <strong>$(date)</strong></div>
    </div>
    
    <h2>🧪 Résultats Détaillés</h2>
    <table>
        <tr>
            <th>Catégorie</th>
            <th>Fichier de Résultats</th>
            <th>Statut</th>
        </tr>
EOF

# Ajouter les résultats au rapport
for result_file in "$RESULTS_DIR"/*-"$TIMESTAMP".xml; do
    if [ -f "$result_file" ]; then
        basename_file=$(basename "$result_file")
        category=$(echo "$basename_file" | sed "s/-$TIMESTAMP.xml//")
        
        # Vérifier si des tests ont échoué
        if grep -q 'failure\|error' "$result_file"; then
            status="<span class='failure'>❌ Échec</span>"
        else
            status="<span class='success'>✅ Succès</span>"
        fi
        
        echo "        <tr><td>$category</td><td>$basename_file</td><td>$status</td></tr>" >> "$RESULTS_DIR/report-$TIMESTAMP.html"
    fi
done

# Fermer le rapport HTML
cat >> "$RESULTS_DIR/report-$TIMESTAMP.html" <<EOF
    </table>
    
    <h2>🚀 Prochaines Étapes</h2>
    <ul>
        <li>Examiner les tests échoués dans les fichiers XML</li>
        <li>Vérifier les logs des services pour plus de détails</li>
        <li>Relancer les tests échoués individuellement</li>
        <li>Optimiser les performances si nécessaire</li>
    </ul>
</body>
</html>
EOF

# Afficher le résumé
echo ""
echo "✅ Tests terminés!"
echo "=================="
echo "📊 Total: $TOTAL_TESTS tests"
echo "✅ Réussis: $((TOTAL_TESTS - FAILED_TESTS))"
echo "❌ Échoués: $FAILED_TESTS"
echo "📈 Taux de réussite: $SUCCESS_RATE%"
echo ""
echo "📁 Résultats sauvegardés dans: $RESULTS_DIR"
echo "📄 Rapport HTML: $RESULTS_DIR/report-$TIMESTAMP.html"
echo ""

# Ouvrir le rapport si possible
if command -v xdg-open > /dev/null; then
    xdg-open "$RESULTS_DIR/report-$TIMESTAMP.html"
elif command -v open > /dev/null; then
    open "$RESULTS_DIR/report-$TIMESTAMP.html"
fi

# Code de sortie basé sur le taux de réussite
if [ $SUCCESS_RATE -lt 80 ]; then
    echo "⚠️ Taux de réussite inférieur à 80%!"
    exit 1
else
    echo "🎉 Tests d'intégration réussis!"
    exit 0
fi