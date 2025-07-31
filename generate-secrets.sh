#!/bin/bash
# 🔐 JARVIS AI 2025 - Générateur de Secrets Sécurisés
# Script pour générer des mots de passe et secrets robustes

set -euo pipefail

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"
BACKUP_DIR="./backups/env"

# Fonction d'affichage
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║       🔐 JARVIS AI 2025 SECRETS       ║${NC}"
    echo -e "${BLUE}║      Générateur de Mots de Passe      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Fonction de génération de mots de passe
generate_password() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

generate_jwt_secret() {
    openssl rand -hex 64
}

generate_strong_password() {
    local length=${1:-24}
    # Génère un mot de passe avec majuscules, minuscules, chiffres et symboles
    < /dev/urandom tr -dc 'A-Za-z0-9!@#$%^&*()_+-=[]{}|;:,.<>?' | head -c$length
}

# Vérification des prérequis
check_requirements() {
    print_step "Vérification des prérequis..."
    
    if ! command -v openssl &> /dev/null; then
        print_error "OpenSSL n'est pas installé. Installation requise."
        exit 1
    fi
    
    if [[ ! -f "$ENV_EXAMPLE" ]]; then
        print_error "Fichier $ENV_EXAMPLE non trouvé. Exécutez ce script depuis la racine du projet."
        exit 1
    fi
}

# Sauvegarde du fichier .env existant
backup_env() {
    if [[ -f "$ENV_FILE" ]]; then
        print_step "Sauvegarde du fichier .env existant..."
        mkdir -p "$BACKUP_DIR"
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        cp "$ENV_FILE" "$BACKUP_DIR/env_backup_$timestamp"
        print_step "Sauvegarde créée: $BACKUP_DIR/env_backup_$timestamp"
    fi
}

# Génération des secrets
generate_secrets() {
    print_step "Génération des secrets sécurisés..."
    
    # Copier le fichier exemple
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    
    # Générer les secrets
    local postgres_password=$(generate_strong_password 32)
    local jwt_secret=$(generate_jwt_secret)
    local redis_password=$(generate_strong_password 24)
    local admin_password=$(generate_strong_password 20)
    local jarvis_password=$(generate_strong_password 20)
    
    # Remplacer les valeurs dans le fichier .env
    sed -i "s/CHANGEME_STRONG_PASSWORD_HERE/$postgres_password/g" "$ENV_FILE"
    sed -i "s/CHANGEME_GENERATE_STRONG_JWT_SECRET/$jwt_secret/g" "$ENV_FILE"
    sed -i "s/CHANGEME_REDIS_PASSWORD/$redis_password/g" "$ENV_FILE"
    sed -i "s/CHANGEME_ADMIN_PASSWORD/$admin_password/g" "$ENV_FILE"
    sed -i "s/CHANGEME_JARVIS_PASSWORD/$jarvis_password/g" "$ENV_FILE"
    
    print_step "Secrets générés et configurés dans $ENV_FILE"
}

# Affichage des informations de sécurité
display_security_info() {
    echo ""
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║           🛡️  SÉCURITÉ INFO           ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}✓${NC} Fichier .env créé avec des secrets robustes"
    echo -e "${GREEN}✓${NC} Mots de passe générés avec OpenSSL"
    echo -e "${GREEN}✓${NC} JWT Secret de 128 caractères hexadécimaux"
    echo -e "${GREEN}✓${NC} Mots de passe système de 20-32 caractères"
    echo ""
    print_warning "IMPORTANT - Actions de sécurité requises:"
    echo "  1. Vérifiez le fichier .env généré"
    echo "  2. Ajustez les domaines CORS pour la production"
    echo "  3. Ne commitez JAMAIS le fichier .env"
    echo "  4. Partagez les secrets de manière sécurisée"
    echo "  5. Changez les secrets régulièrement"
    echo ""
}

# Validation du fichier généré
validate_env() {
    print_step "Validation du fichier .env..."
    
    # Vérifier que tous les CHANGEME ont été remplacés
    if grep -q "CHANGEME_" "$ENV_FILE"; then
        print_error "Certains secrets n'ont pas été générés correctement!"
        grep "CHANGEME_" "$ENV_FILE"
        return 1
    fi
    
    # Vérifier que les variables critiques sont définies
    local critical_vars=("POSTGRES_PASSWORD" "JWT_SECRET_KEY" "REDIS_PASSWORD")
    for var in "${critical_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE"; then
            print_error "Variable critique manquante: $var"
            return 1
        fi
    done
    
    print_step "Validation réussie - Tous les secrets sont configurés"
}

# Génération du fichier .gitignore
update_gitignore() {
    local gitignore_file=".gitignore"
    
    if [[ ! -f "$gitignore_file" ]]; then
        touch "$gitignore_file"
    fi
    
    # Ajouter .env s'il n'y est pas déjà
    if ! grep -q "^\.env$" "$gitignore_file"; then
        echo "" >> "$gitignore_file"
        echo "# Environment variables - NEVER commit secrets!" >> "$gitignore_file"
        echo ".env" >> "$gitignore_file"
        print_step ".env ajouté à .gitignore"
    fi
}

# Menu interactif
interactive_menu() {
    echo ""
    echo -e "${BLUE}Options disponibles:${NC}"
    echo "1. Générer tous les secrets automatiquement"
    echo "2. Générer seulement les mots de passe manquants"
    echo "3. Régénérer tous les secrets (écrase l'ancien .env)"
    echo "4. Valider le fichier .env existant"
    echo "5. Quitter"
    echo ""
    read -p "Choisissez une option [1-5]: " choice
    
    case $choice in
        1)
            backup_env
            generate_secrets
            validate_env
            update_gitignore
            display_security_info
            ;;
        2)
            print_warning "Fonctionnalité en développement..."
            ;;
        3)
            print_warning "Cette action écrasera complètement votre fichier .env existant!"
            read -p "Êtes-vous sûr? [y/N]: " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                backup_env
                generate_secrets
                validate_env
                update_gitignore
                display_security_info
            else
                print_step "Opération annulée"
            fi
            ;;
        4)
            if [[ -f "$ENV_FILE" ]]; then
                validate_env
            else
                print_error "Aucun fichier .env trouvé"
            fi
            ;;
        5)
            print_step "Au revoir!"
            exit 0
            ;;
        *)
            print_error "Option invalide"
            interactive_menu
            ;;
    esac
}

# Fonction principale
main() {
    print_header
    check_requirements
    
    # Si pas d'arguments, mode interactif
    if [[ $# -eq 0 ]]; then
        interactive_menu
    else
        case "$1" in
            --auto|--generate)
                backup_env
                generate_secrets
                validate_env
                update_gitignore
                display_security_info
                ;;
            --validate)
                validate_env
                ;;
            --help|-h)
                echo "Usage: $0 [--auto|--generate|--validate|--help]"
                echo ""
                echo "Options:"
                echo "  --auto, --generate    Génère automatiquement tous les secrets"
                echo "  --validate           Valide le fichier .env existant"
                echo "  --help, -h           Affiche cette aide"
                echo ""
                echo "Sans arguments: Mode interactif"
                ;;
            *)
                print_error "Option inconnue: $1"
                echo "Utilisez --help pour l'aide"
                exit 1
                ;;
        esac
    fi
}

# Gestion des signaux
trap 'print_error "Script interrompu"; exit 1' INT TERM

# Exécution
main "$@"