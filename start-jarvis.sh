#!/bin/bash
# 🤖 JARVIS 2025 - Script de démarrage intelligent
# Usage: ./start-jarvis.sh [--dev|--prod|--build|--stop|--logs]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner JARVIS
print_banner() {
    echo -e "${BLUE}"
    echo "    ╔═══════════════════════════════════════╗"
    echo "    ║           🤖 JARVIS 2025              ║"
    echo "    ║      Assistant IA Personnel          ║"
    echo "    ║     Architecture Microservices       ║"
    echo "    ╚═══════════════════════════════════════╝"
    echo -e "${NC}"
}

# Fonction d'aide
print_help() {
    echo -e "${YELLOW}Usage: ./start-jarvis.sh [OPTIONS]${NC}"
    echo ""
    echo "Options:"
    echo "  --dev      Démarrage en mode développement"
    echo "  --prod     Démarrage en mode production (défaut)"
    echo "  --build    Rebuild tous les containers"
    echo "  --stop     Arrêter tous les services"
    echo "  --logs     Afficher les logs en temps réel"
    echo "  --status   Vérifier l'état des services"
    echo "  --help     Afficher cette aide"
}

# Vérifier les prérequis
check_prerequisites() {
    echo -e "${BLUE}🔍 Vérification des prérequis...${NC}"
    
    # Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker n'est pas installé${NC}"
        exit 1
    fi
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose n'est pas installé${NC}"
        exit 1
    fi
    
    # Fichier docker-compose.yml
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}❌ docker-compose.yml introuvable${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prérequis validés${NC}"
}

# Vérifier l'état des services
check_services_status() {
    echo -e "${BLUE}📊 État des services:${NC}"
    
    services=("brain-api" "ollama" "redis" "memory-db" "tts-service" "stt-service" "frontend")
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "jarvis_$service\|jarvis-$service"; then
            echo -e "${GREEN}✅ $service${NC}"
        else
            echo -e "${RED}❌ $service${NC}"
        fi
    done
}

# Télécharger les modèles Ollama
setup_ollama_models() {
    echo -e "${YELLOW}🤖 Configuration des modèles Ollama...${NC}"
    
    # Attendre qu'Ollama soit prêt
    echo "Attente du démarrage d'Ollama..."
    sleep 30
    
    # Modèles essentiels pour 2025
    models=("llama3.1:8b" "mistral:7b" "qwen2.5-coder:7b")
    
    for model in "${models[@]}"; do
        echo -e "${BLUE}📥 Téléchargement du modèle $model...${NC}"
        docker exec jarvis_ollama ollama pull "$model" || echo -e "${YELLOW}⚠️  Échec du téléchargement de $model${NC}"
    done
    
    echo -e "${GREEN}✅ Modèles Ollama configurés${NC}"
}

# Démarrage des services
start_services() {
    local mode=$1
    
    echo -e "${BLUE}🚀 Démarrage de JARVIS en mode $mode...${NC}"
    
    if [ "$mode" = "dev" ]; then
        docker-compose up -d
    else
        docker-compose up -d --remove-orphans
    fi
    
    echo -e "${GREEN}✅ Services démarrés${NC}"
    
    # Configurer Ollama en arrière-plan
    setup_ollama_models &
    
    echo ""
    echo -e "${GREEN}🎉 JARVIS 2025 est maintenant actif !${NC}"
    echo ""
    echo -e "${YELLOW}📋 Accès aux services:${NC}"
    echo "  🌐 Frontend:    http://localhost:3000"
    echo "  🧠 Brain API:   http://localhost:8080"
    echo "  🗣️  TTS Service: http://localhost:5002"
    echo "  🎤 STT Service: http://localhost:5003"
    echo "  🤖 Ollama:      http://localhost:11434"
    echo "  📊 API Docs:    http://localhost:8080/docs"
    echo ""
    echo -e "${BLUE}💡 Commandes utiles:${NC}"
    echo "  ./start-jarvis.sh --logs     # Voir les logs"
    echo "  ./start-jarvis.sh --status   # État des services"
    echo "  ./start-jarvis.sh --stop     # Arrêter JARVIS"
}

# Rebuild des containers
rebuild_services() {
    echo -e "${YELLOW}🔨 Rebuild des containers...${NC}"
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    echo -e "${GREEN}✅ Rebuild terminé${NC}"
}

# Arrêt des services
stop_services() {
    echo -e "${YELLOW}⏹️  Arrêt de JARVIS...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ JARVIS arrêté${NC}"
}

# Affichage des logs
show_logs() {
    echo -e "${BLUE}📋 Logs de JARVIS (Ctrl+C pour quitter):${NC}"
    docker-compose logs -f
}

# Main
main() {
    print_banner
    
    case "${1:-}" in
        --help|-h)
            print_help
            ;;
        --dev)
            check_prerequisites
            start_services "dev"
            ;;
        --prod|"")
            check_prerequisites
            start_services "prod"
            ;;
        --build)
            check_prerequisites
            rebuild_services
            ;;
        --stop)
            stop_services
            ;;
        --logs)
            show_logs
            ;;
        --status)
            check_services_status
            ;;
        *)
            echo -e "${RED}❌ Option inconnue: $1${NC}"
            print_help
            exit 1
            ;;
    esac
}

# Gestion des signaux
trap 'echo -e "\n${YELLOW}⚠️  Interruption détectée${NC}"; exit 1' INT TERM

# Exécution
main "$@"