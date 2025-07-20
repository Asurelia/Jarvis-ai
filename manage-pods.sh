#!/bin/bash
# 🤖 JARVIS 2025 - Gestionnaire de Pods Métier
# Gestion des services par pods indépendants

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration pods
PODS=(
    "ai:docker-compose.ai-pod.yml:🧠:AI Pod (Brain+Ollama+Memory)"
    "audio:docker-compose.audio-pod.yml:🗣️:Audio Pod (TTS+STT Processing)"
    "control:docker-compose.control-pod.yml:🖥️:Control Pod (System+Terminal)"
    "integration:docker-compose.integration-pod.yml:🔧:Integration Pod (MCP+UI+Autocomplete)"
)

# Banner JARVIS
print_banner() {
    echo -e "${BLUE}"
    echo "    ╔═══════════════════════════════════════╗"
    echo "    ║           🤖 JARVIS 2025              ║"
    echo "    ║        Gestionnaire de Pods           ║"
    echo "    ║      Architecture Microservices       ║"
    echo "    ╚═══════════════════════════════════════╝"
    echo -e "${NC}"
}

# Fonction d'aide
print_help() {
    echo -e "${YELLOW}Usage: ./manage-pods.sh [COMMAND] [POD]${NC}"
    echo ""
    echo "Commands:"
    echo "  start [pod]     Démarrer un pod ou tous les pods"
    echo "  stop [pod]      Arrêter un pod ou tous les pods"
    echo "  restart [pod]   Redémarrer un pod ou tous les pods"
    echo "  status          Afficher l'état de tous les pods"
    echo "  logs [pod]      Afficher les logs d'un pod"
    echo "  build [pod]     Rebuild un pod ou tous les pods"
    echo "  clean           Nettoyer les ressources inutilisées"
    echo "  health          Vérifier la santé de tous les services"
    echo ""
    echo "Pods disponibles:"
    for pod_info in "${PODS[@]}"; do
        IFS=':' read -r name file icon desc <<< "$pod_info"
        echo "  $icon $name        $desc"
    done
    echo ""
    echo "Exemples:"
    echo "  ./manage-pods.sh start ai           # Démarrer seulement le pod IA"
    echo "  ./manage-pods.sh start              # Démarrer tous les pods"
    echo "  ./manage-pods.sh logs audio         # Voir les logs du pod audio"
    echo "  ./manage-pods.sh health             # Vérifier la santé"
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
    
    echo -e "${GREEN}✅ Prérequis validés${NC}"
}

# Obtenir les informations d'un pod
get_pod_info() {
    local pod_name=$1
    for pod_info in "${PODS[@]}"; do
        IFS=':' read -r name file icon desc <<< "$pod_info"
        if [ "$name" = "$pod_name" ]; then
            echo "$file:$icon:$desc"
            return 0
        fi
    done
    return 1
}

# Démarrer un pod
start_pod() {
    local pod_name=$1
    local pod_info=$(get_pod_info "$pod_name")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Pod '$pod_name' non trouvé${NC}"
        return 1
    fi
    
    IFS=':' read -r file icon desc <<< "$pod_info"
    echo -e "${GREEN}🚀 Démarrage du pod $icon $pod_name...${NC}"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Fichier de configuration '$file' non trouvé${NC}"
        return 1
    fi
    
    docker-compose -f "$file" up -d
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Pod $pod_name démarré avec succès${NC}"
    else
        echo -e "${RED}❌ Échec du démarrage du pod $pod_name${NC}"
        return 1
    fi
}

# Arrêter un pod
stop_pod() {
    local pod_name=$1
    local pod_info=$(get_pod_info "$pod_name")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Pod '$pod_name' non trouvé${NC}"
        return 1
    fi
    
    IFS=':' read -r file icon desc <<< "$pod_info"
    echo -e "${YELLOW}⏹️ Arrêt du pod $icon $pod_name...${NC}"
    
    docker-compose -f "$file" down
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Pod $pod_name arrêté avec succès${NC}"
    else
        echo -e "${RED}❌ Échec de l'arrêt du pod $pod_name${NC}"
        return 1
    fi
}

# Redémarrer un pod
restart_pod() {
    local pod_name=$1
    echo -e "${BLUE}🔄 Redémarrage du pod $pod_name...${NC}"
    
    stop_pod "$pod_name"
    sleep 2
    start_pod "$pod_name"
}

# Afficher l'état des pods
show_status() {
    echo -e "${BLUE}📊 État des pods JARVIS:${NC}"
    echo ""
    
    for pod_info in "${PODS[@]}"; do
        IFS=':' read -r name file icon desc <<< "$pod_info"
        echo -e "${PURPLE}$icon $name - $desc${NC}"
        
        if [ -f "$file" ]; then
            # Vérifier si des conteneurs de ce pod sont actifs
            local containers=$(docker-compose -f "$file" ps -q 2>/dev/null)
            if [ -n "$containers" ]; then
                docker-compose -f "$file" ps
            else
                echo -e "${YELLOW}  ⏸️  Aucun conteneur actif${NC}"
            fi
        else
            echo -e "${RED}  ❌ Fichier de configuration manquant${NC}"
        fi
        echo ""
    done
}

# Afficher les logs d'un pod
show_logs() {
    local pod_name=$1
    local pod_info=$(get_pod_info "$pod_name")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Pod '$pod_name' non trouvé${NC}"
        return 1
    fi
    
    IFS=':' read -r file icon desc <<< "$pod_info"
    echo -e "${BLUE}📋 Logs du pod $icon $pod_name:${NC}"
    
    docker-compose -f "$file" logs -f
}

# Rebuild un pod
build_pod() {
    local pod_name=$1
    local pod_info=$(get_pod_info "$pod_name")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Pod '$pod_name' non trouvé${NC}"
        return 1
    fi
    
    IFS=':' read -r file icon desc <<< "$pod_info"
    echo -e "${YELLOW}🔨 Rebuild du pod $icon $pod_name...${NC}"
    
    docker-compose -f "$file" down
    docker-compose -f "$file" build --no-cache
    docker-compose -f "$file" up -d
    
    echo -e "${GREEN}✅ Rebuild du pod $pod_name terminé${NC}"
}

# Nettoyer les ressources
clean_resources() {
    echo -e "${YELLOW}🧹 Nettoyage des ressources Docker...${NC}"
    
    # Arrêter tous les pods
    for pod_info in "${PODS[@]}"; do
        IFS=':' read -r name file icon desc <<< "$pod_info"
        if [ -f "$file" ]; then
            docker-compose -f "$file" down 2>/dev/null || true
        fi
    done
    
    # Nettoyer les ressources inutilisées
    docker system prune -f
    docker volume prune -f
    docker network prune -f
    
    echo -e "${GREEN}✅ Nettoyage terminé${NC}"
}

# Vérifier la santé des services
check_health() {
    echo -e "${BLUE}🏥 Vérification de la santé des services:${NC}"
    echo ""
    
    # Services à vérifier avec leurs ports
    declare -A HEALTH_ENDPOINTS=(
        ["🧠 Brain API"]="http://localhost:8080/health"
        ["🗣️ TTS Service"]="http://localhost:5002/health"
        ["🎤 STT Service"]="http://localhost:5003/health"
        ["🖥️ System Control"]="http://localhost:5004/health"
        ["💻 Terminal Service"]="http://localhost:5005/health"
        ["🔧 MCP Gateway"]="http://localhost:5006/health"
        ["🧠 Autocomplete"]="http://localhost:5007/health"
        ["🤖 Ollama"]="http://localhost:11434/api/tags"
        ["🎤 Voice Bridge"]="http://localhost:3001/health"
        ["🌐 Frontend"]="http://localhost:3000"
    )
    
    for service in "${!HEALTH_ENDPOINTS[@]}"; do
        local url="${HEALTH_ENDPOINTS[$service]}"
        
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service${NC}"
        else
            echo -e "${RED}❌ $service${NC}"
        fi
    done
    
    echo ""
    echo -e "${BLUE}💡 Pour démarrer le Voice Bridge local:${NC}"
    echo -e "${YELLOW}  cd local-interface && python voice-bridge.py${NC}"
}

# Commande principale
main() {
    print_banner
    
    local command="${1:-help}"
    local pod_name="${2:-}"
    
    case "$command" in
        "start")
            check_prerequisites
            if [ -n "$pod_name" ]; then
                start_pod "$pod_name"
            else
                echo -e "${GREEN}🚀 Démarrage de tous les pods...${NC}"
                for pod_info in "${PODS[@]}"; do
                    IFS=':' read -r name file icon desc <<< "$pod_info"
                    start_pod "$name"
                done
                echo -e "${GREEN}🎉 Tous les pods sont démarrés !${NC}"
                echo ""
                echo -e "${YELLOW}💡 N'oubliez pas de démarrer le Voice Bridge:${NC}"
                echo -e "${BLUE}  cd local-interface && python voice-bridge.py${NC}"
            fi
            ;;
        "stop")
            if [ -n "$pod_name" ]; then
                stop_pod "$pod_name"
            else
                echo -e "${YELLOW}⏹️ Arrêt de tous les pods...${NC}"
                for pod_info in "${PODS[@]}"; do
                    IFS=':' read -r name file icon desc <<< "$pod_info"
                    stop_pod "$name"
                done
                echo -e "${GREEN}✅ Tous les pods sont arrêtés${NC}"
            fi
            ;;
        "restart")
            if [ -n "$pod_name" ]; then
                restart_pod "$pod_name"
            else
                echo -e "${BLUE}🔄 Redémarrage de tous les pods...${NC}"
                for pod_info in "${PODS[@]}"; do
                    IFS=':' read -r name file icon desc <<< "$pod_info"
                    restart_pod "$name"
                done
            fi
            ;;
        "status")
            show_status
            ;;
        "logs")
            if [ -n "$pod_name" ]; then
                show_logs "$pod_name"
            else
                echo -e "${RED}❌ Spécifiez un pod pour voir les logs${NC}"
                print_help
                exit 1
            fi
            ;;
        "build")
            check_prerequisites
            if [ -n "$pod_name" ]; then
                build_pod "$pod_name"
            else
                echo -e "${YELLOW}🔨 Rebuild de tous les pods...${NC}"
                for pod_info in "${PODS[@]}"; do
                    IFS=':' read -r name file icon desc <<< "$pod_info"
                    build_pod "$name"
                done
            fi
            ;;
        "clean")
            clean_resources
            ;;
        "health")
            check_health
            ;;
        "help"|"--help"|"-h")
            print_help
            ;;
        *)
            echo -e "${RED}❌ Commande inconnue: $command${NC}"
            print_help
            exit 1
            ;;
    esac
}

# Gestion des signaux
trap 'echo -e "\n${YELLOW}⚠️ Interruption détectée${NC}"; exit 1' INT TERM

# Exécution
main "$@"