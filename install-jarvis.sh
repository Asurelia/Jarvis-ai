#!/bin/bash
set -e

# Configuration des couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Fonction d'affichage avec couleurs
print_header() {
    echo -e "${PURPLE}${BOLD}"
    echo "╔══════════════════════════════════════════╗"
    echo "║          JARVIS AI INSTALLER             ║"
    echo "║         Installation Unix/Linux          ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Détection du système d'exploitation
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get >/dev/null 2>&1; then
            DISTRO="debian"
        elif command -v yum >/dev/null 2>&1; then
            DISTRO="redhat"
        elif command -v pacman >/dev/null 2>&1; then
            DISTRO="arch"
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="mac"
        DISTRO="mac"
    else
        OS="unknown"
        DISTRO="unknown"
    fi
    
    print_info "Système détecté: $OS ($DISTRO)"
}

# Vérification des privilèges
check_privileges() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Exécution en tant que root détectée"
        print_warning "L'installation peut échouer pour certains composants"
    fi
}

# Installation des prérequis système
install_system_dependencies() {
    print_info "[1/8] Installation des dépendances système..."
    
    case "$DISTRO" in
        "debian")
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv git curl wget
            # Docker
            if ! command -v docker >/dev/null 2>&1; then
                print_info "Installation de Docker..."
                curl -fsSL https://get.docker.com -o get-docker.sh
                sudo sh get-docker.sh
                sudo usermod -aG docker $USER
                rm get-docker.sh
            fi
            # Docker Compose
            if ! command -v docker-compose >/dev/null 2>&1; then
                print_info "Installation de Docker Compose..."
                sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                sudo chmod +x /usr/local/bin/docker-compose
            fi
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y python3 python3-pip git curl wget
            # Docker
            if ! command -v docker >/dev/null 2>&1; then
                sudo yum install -y docker
                sudo systemctl start docker
                sudo systemctl enable docker
                sudo usermod -aG docker $USER
            fi
            ;;
        "arch")
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm python python-pip git curl wget docker docker-compose
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            ;;
        "mac")
            # Vérification de Homebrew
            if ! command -v brew >/dev/null 2>&1; then
                print_info "Installation de Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python git curl wget
            # Docker Desktop pour Mac doit être installé manuellement
            if ! command -v docker >/dev/null 2>&1; then
                print_warning "Docker Desktop n'est pas installé"
                print_warning "Téléchargez Docker Desktop depuis: https://docker.com"
                read -p "Appuyez sur Entrée après avoir installé Docker Desktop..."
            fi
            ;;
        *)
            print_warning "Distribution non reconnue, installation manuelle requise"
            ;;
    esac
}

# Vérification des prérequis
check_prerequisites() {
    print_info "[2/8] Vérification des prérequis..."
    local missing=()
    
    # Python
    if command -v python3 >/dev/null 2>&1; then
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python $python_version"
    else
        print_error "Python 3 non trouvé"
        missing+=("python3")
    fi
    
    # Pip
    if command -v pip3 >/dev/null 2>&1; then
        print_success "pip3 installé"
    else
        print_error "pip3 non trouvé"
        missing+=("pip3")
    fi
    
    # Docker
    if command -v docker >/dev/null 2>&1; then
        local docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker $docker_version"
        
        # Vérification que Docker fonctionne
        if docker info >/dev/null 2>&1; then
            print_success "Docker opérationnel"
        else
            print_warning "Docker installé mais non fonctionnel"
            print_info "Démarrage du service Docker..."
            sudo systemctl start docker 2>/dev/null || true
        fi
    else
        print_error "Docker non trouvé"
        missing+=("docker")
    fi
    
    # Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        local compose_version=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker Compose $compose_version"
    else
        print_error "Docker Compose non trouvé"
        missing+=("docker-compose")
    fi
    
    # Git
    if command -v git >/dev/null 2>&1; then
        local git_version=$(git --version | awk '{print $3}')
        print_success "Git $git_version"
    else
        print_warning "Git non trouvé (optionnel)"
    fi
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_error "Prérequis manquants: ${missing[*]}"
        return 1
    fi
    
    return 0
}

# Installation de Node.js (optionnel)
install_nodejs() {
    print_info "[3/8] Vérification de Node.js..."
    
    if command -v node >/dev/null 2>&1; then
        local node_version=$(node --version)
        print_success "Node.js $node_version"
        
        if command -v npm >/dev/null 2>&1; then
            local npm_version=$(npm --version)
            print_success "npm $npm_version"
        else
            print_warning "npm non trouvé"
        fi
    else
        print_warning "Node.js non trouvé"
        print_info "Installation de Node.js via NodeSource..."
        
        case "$DISTRO" in
            "debian")
                curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
                sudo apt-get install -y nodejs
                ;;
            "redhat")
                curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
                sudo yum install -y nodejs
                ;;
            "arch")
                sudo pacman -S --noconfirm nodejs npm
                ;;
            "mac")
                brew install node
                ;;
            *)
                print_warning "Installation Node.js manuelle requise"
                print_warning "Interface web limitée"
                ;;
        esac
    fi
}

# Installation d'Ollama (optionnel)
install_ollama() {
    print_info "[4/8] Vérification d'Ollama..."
    
    if command -v ollama >/dev/null 2>&1; then
        print_success "Ollama installé"
    else
        print_info "Installation d'Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        
        # Démarrage du service Ollama
        if [[ "$OS" == "linux" ]]; then
            sudo systemctl start ollama 2>/dev/null || true
            sudo systemctl enable ollama 2>/dev/null || true
        fi
    fi
}

# Configuration des permissions Docker
setup_docker_permissions() {
    print_info "[5/8] Configuration des permissions Docker..."
    
    if groups $USER | grep -q docker; then
        print_success "Utilisateur dans le groupe docker"
    else
        print_info "Ajout de l'utilisateur au groupe docker..."
        sudo usermod -aG docker $USER
        print_warning "Vous devrez vous déconnecter/reconnecter pour que les changements prennent effet"
        print_warning "Ou utilisez: newgrp docker"
    fi
}

# Préparation de l'environnement
prepare_environment() {
    print_info "[6/8] Préparation de l'environnement..."
    
    # Création des répertoires nécessaires
    mkdir -p logs cache memory models data
    
    # Permissions pour les volumes Docker
    chmod 755 logs cache memory models data
    
    print_success "Environnement préparé"
}

# Test des services Docker
test_docker_services() {
    print_info "[7/8] Test des services Docker..."
    
    # Test de la configuration Docker Compose
    if docker-compose config >/dev/null 2>&1; then
        print_success "Configuration Docker Compose valide"
    else
        print_warning "Configuration Docker Compose invalide"
    fi
    
    # Test de l'accès au registry Docker
    if docker pull hello-world >/dev/null 2>&1; then
        print_success "Accès au Docker Hub"
        docker rmi hello-world >/dev/null 2>&1
    else
        print_warning "Problème d'accès au Docker Hub"
    fi
}

# Lancement de l'installation principale
run_main_installation() {
    print_info "[8/8] Lancement de l'installation principale..."
    echo
    echo "═══════════════════════════════════════════════════════════════"
    echo "              INSTALLATION JARVIS AI EN COURS..."
    echo "═══════════════════════════════════════════════════════════════"
    echo
    
    # Utiliser python3 explicitement
    if command -v python3 >/dev/null 2>&1; then
        python3 install-jarvis.py
        local install_result=$?
    else
        python install-jarvis.py
        local install_result=$?
    fi
    
    echo
    echo "═══════════════════════════════════════════════════════════════"
    
    if [ $install_result -eq 0 ]; then
        print_success "INSTALLATION RÉUSSIE!"
        echo
        echo "Pour démarrer JARVIS AI:"
        echo "  📄 Exécutez: ./launch-jarvis.sh"
        echo
        echo "Accès aux services:"
        echo "  🌐 Interface web: http://localhost:3000"
        echo "  🔗 API principale: http://localhost:5000"
        echo "  📚 Documentation: http://localhost:5000/docs"
        echo
        
        read -p "Voulez-vous démarrer JARVIS maintenant? (o/N): " start_now
        if [[ "$start_now" =~ ^[oO]$ ]]; then
            echo "Démarrage de JARVIS AI..."
            chmod +x launch-jarvis.sh
            ./launch-jarvis.sh
        fi
    else
        print_error "ERREUR LORS DE L'INSTALLATION"
        echo
        echo "Consultez le fichier jarvis-install.log pour plus de détails"
        echo
        return 1
    fi
}

# Fonction principale
main() {
    print_header
    detect_os
    check_privileges
    
    # Installation interactive
    echo
    read -p "Installer les dépendances système automatiquement? (o/N): " install_deps
    if [[ "$install_deps" =~ ^[oO]$ ]]; then
        install_system_dependencies
    fi
    
    # Vérification des prérequis
    if ! check_prerequisites; then
        print_error "Prérequis manquants. Installation interrompue."
        echo
        echo "Installez les prérequis manquants et relancez l'installation."
        exit 1
    fi
    
    install_nodejs
    install_ollama
    setup_docker_permissions
    prepare_environment
    test_docker_services
    run_main_installation
}

# Gestion des signaux
trap 'echo -e "\n${YELLOW}Installation interrompue par l\'utilisateur.${NC}"; exit 1' INT TERM

# Point d'entrée
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi