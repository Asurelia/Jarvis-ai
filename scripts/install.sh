#!/bin/bash
# 🐧 Script d'installation JARVIS pour Linux/macOS

set -e  # Arrêter en cas d'erreur

echo "🤖 Installation JARVIS Phase 2 pour Linux/macOS"
echo "================================================"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
print_step() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des prérequis
check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 trouvé"
        return 0
    else
        print_warning "$1 non trouvé"
        return 1
    fi
}

# Détection de l'OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt &> /dev/null; then
            PACKAGE_MANAGER="apt"
        elif command -v yum &> /dev/null; then
            PACKAGE_MANAGER="yum"
        elif command -v pacman &> /dev/null; then
            PACKAGE_MANAGER="pacman"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        if command -v brew &> /dev/null; then
            PACKAGE_MANAGER="brew"
        fi
    else
        print_error "OS non supporté: $OSTYPE"
        exit 1
    fi
    
    print_step "OS détecté: $OS avec gestionnaire de paquets: ${PACKAGE_MANAGER:-aucun}"
}

# Installation des dépendances système
install_system_dependencies() {
    print_step "Installation des dépendances système..."
    
    case $PACKAGE_MANAGER in
        "apt")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv nodejs npm tesseract-ocr
            ;;
        "yum")
            sudo yum install -y python3 python3-pip nodejs npm tesseract
            ;;
        "pacman")
            sudo pacman -S --noconfirm python python-pip nodejs npm tesseract
            ;;
        "brew")
            brew install python3 node tesseract
            ;;
        *)
            print_warning "Gestionnaire de paquets non supporté, installation manuelle requise"
            ;;
    esac
}

# Installation d'Ollama
install_ollama() {
    print_step "Installation d'Ollama..."
    
    if ! check_command ollama; then
        print_step "Téléchargement et installation d'Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        
        # Attendre qu'Ollama soit prêt
        sleep 5
        
        if check_command ollama; then
            print_success "Ollama installé avec succès"
            
            # Installation des modèles recommandés
            print_step "Installation des modèles IA recommandés..."
            ollama pull llama3.2:3b
            ollama pull llava:7b
            print_success "Modèles IA installés"
        else
            print_warning "Ollama non disponible après installation"
        fi
    fi
}

# Configuration de l'environnement Python
setup_python_environment() {
    print_step "Configuration de l'environnement Python..."
    
    # Création de l'environnement virtuel
    python3 -m venv venv
    source venv/bin/activate
    
    # Mise à jour de pip
    pip install --upgrade pip
    
    # Installation des dépendances
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dépendances Python installées"
    else
        print_error "requirements.txt non trouvé"
        exit 1
    fi
}

# Configuration de l'environnement Node.js
setup_node_environment() {
    print_step "Configuration de l'environnement Node.js..."
    
    if [ -d "ui" ] && [ -f "ui/package.json" ]; then
        cd ui
        npm install
        cd ..
        print_success "Dépendances Node.js installées"
    else
        print_warning "Interface UI non trouvée"
    fi
}

# Configuration des fichiers
setup_configuration() {
    print_step "Configuration des fichiers..."
    
    # Création des répertoires
    mkdir -p logs memory screenshots temp
    
    # Configuration .env
    if [ -f ".env.example" ] && [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Fichier .env créé"
    fi
    
    # Permissions d'exécution
    chmod +x start_jarvis.py
    chmod +x install.py
    
    print_success "Configuration terminée"
}

# Tests
run_tests() {
    print_step "Lancement des tests d'intégration..."
    
    source venv/bin/activate
    python start_jarvis.py --test
    
    if [ $? -eq 0 ]; then
        print_success "Tests réussis"
    else
        print_warning "Tests échoués - vérifiez la configuration"
    fi
}

# Fonction principale
main() {
    print_step "Début de l'installation JARVIS Phase 2"
    
    # Vérification des prérequis
    detect_os
    
    # Installation
    if [ "${SKIP_SYSTEM_DEPS:-false}" != "true" ]; then
        install_system_dependencies
    fi
    
    install_ollama
    setup_python_environment
    setup_node_environment
    setup_configuration
    
    if [ "${SKIP_TESTS:-false}" != "true" ]; then
        run_tests
    fi
    
    # Résumé
    echo ""
    echo "🎉 Installation terminée !"
    echo ""
    echo "Pour démarrer JARVIS :"
    echo "  source venv/bin/activate"
    echo "  python start_jarvis.py"
    echo ""
    echo "Interfaces disponibles :"
    echo "  • Interface web: http://localhost:3000"
    echo "  • API: http://localhost:8000/api/docs"
    echo ""
}

# Gestion des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-system-deps)
            SKIP_SYSTEM_DEPS=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-system-deps   Ignorer l'installation des dépendances système"
            echo "  --skip-tests         Ignorer les tests d'intégration"
            echo "  --help               Afficher cette aide"
            exit 0
            ;;
        *)
            print_error "Option inconnue: $1"
            exit 1
            ;;
    esac
done

# Lancer l'installation
main