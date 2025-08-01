#!/bin/bash

# 🔍 JARVIS AI 2025 - Démarrage du système de monitoring complet
# Script Unix/Linux pour lancer Prometheus, Grafana, Alertmanager, Loki et Jaeger

set -e

echo ""
echo "==============================================="
echo "🤖 JARVIS AI 2025 - Monitoring Stack"
echo "==============================================="
echo ""

# Fonction pour logger
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Vérification Docker
log "⏳ Vérification de Docker..."
if ! command -v docker &> /dev/null; then
    log "❌ Docker n'est pas installé"
    log "Veuillez installer Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
log "✅ Docker trouvé: $(docker --version)"

# Vérification docker-compose
log "⏳ Vérification de Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    log "❌ Docker Compose n'est pas installé"
    log "Veuillez installer Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
log "✅ Docker Compose trouvé: $(docker-compose --version)"

# Création des répertoires de données
log "⏳ Création des répertoires de données..."
mkdir -p monitoring/data/{prometheus,grafana,alertmanager,loki,jaeger}

# Configuration des permissions
log "⏳ Configuration des permissions..."
chmod -R 755 monitoring/data/
chown -R 472:472 monitoring/data/grafana/ 2>/dev/null || true  # Grafana user
chown -R 65534:65534 monitoring/data/prometheus/ 2>/dev/null || true  # Nobody user
chown -R 65534:65534 monitoring/data/alertmanager/ 2>/dev/null || true
chown -R 10001:10001 monitoring/data/loki/ 2>/dev/null || true
chown -R 10001:10001 monitoring/data/jaeger/ 2>/dev/null || true

# Variables d'environnement par défaut
export GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-"jarvis2025!"}
export REDIS_PASSWORD=${REDIS_PASSWORD:-"jarvis_redis_2025!"}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"jarvis_db_2025!"}

# Configuration des alertes (optionnel)
export SMTP_HOST=${SMTP_HOST:-"smtp.gmail.com:587"}
export TEAM_EMAIL=${TEAM_EMAIL:-"admin@localhost"}
export SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-""}

echo ""
log "🚀 Démarrage de la stack de monitoring..."
echo ""

# Arrêt des services existants
log "⏳ Arrêt des services de monitoring existants..."
docker-compose -f docker-compose.monitoring.yml down -v 2>/dev/null || true

# Démarrage des services de monitoring
log "⏳ Démarrage des services de monitoring..."
docker-compose -f docker-compose.monitoring.yml up -d

if [ $? -ne 0 ]; then
    log "❌ Erreur lors du démarrage des services de monitoring"
    log "Vérifiez les logs avec: docker-compose -f docker-compose.monitoring.yml logs"
    exit 1
fi

echo ""
log "⏳ Attente du démarrage des services (30 secondes)..."
sleep 30

echo ""
log "✅ Stack de monitoring JARVIS démarrée avec succès!"
echo ""
echo "📊 Accès aux services:"
echo "   • Grafana:      http://localhost:3001 (admin/jarvis2025!)"
echo "   • Prometheus:   http://localhost:9090"
echo "   • AlertManager: http://localhost:9093"
echo "   • Jaeger:       http://localhost:16686"
echo ""
echo "📈 Dashboards Grafana disponibles:"
echo "   • JARVIS Overview: http://localhost:3001/d/jarvis-overview"
echo "   • AI Services:     http://localhost:3001/d/jarvis-ai-services"
echo "   • GPU Monitoring:  http://localhost:3001/d/jarvis-gpu"
echo "   • Infrastructure:  http://localhost:3001/d/jarvis-infra"
echo ""
echo "🔍 Pour voir les logs: docker-compose -f docker-compose.monitoring.yml logs -f"
echo "🔄 Pour redémarrer:   docker-compose -f docker-compose.monitoring.yml restart"
echo "🛑 Pour arrêter:      docker-compose -f docker-compose.monitoring.yml down"
echo ""

# Vérification santé des services
log "⏳ Vérification de la santé des services..."
sleep 10

echo ""
echo "Service Status:"
docker-compose -f docker-compose.monitoring.yml ps

# Test de connectivité
echo ""
log "🔍 Test de connectivité des services..."

# Test Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    log "✅ Prometheus: Healthy"
else
    log "⚠️ Prometheus: Not responding"
fi

# Test Grafana
if curl -s http://localhost:3001/api/health > /dev/null; then
    log "✅ Grafana: Healthy"
else
    log "⚠️ Grafana: Not responding"
fi

# Test AlertManager
if curl -s http://localhost:9093/-/healthy > /dev/null; then
    log "✅ AlertManager: Healthy"
else
    log "⚠️ AlertManager: Not responding"
fi

echo ""
log "🎉 Système de monitoring JARVIS AI prêt!"
log "   Consultez Grafana pour visualiser vos métriques"
echo ""

# Affichage des métriques initiales
log "📊 Métriques initiales disponibles:"
echo ""
curl -s http://localhost:9090/api/v1/label/__name__/values | jq -r '.data[]' | grep jarvis | head -10 2>/dev/null || echo "   (Métriques en cours de collecte...)"

echo ""
log "✨ Monitoring JARVIS AI configuré avec succès!"