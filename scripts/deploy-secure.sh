#!/bin/bash
# 🔒 Script de déploiement sécurisé JARVIS AI Production
# Ce script configure un environnement de production sécurisé

set -euo pipefail  # Fail fast on errors

# Variables globales
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/jarvis-deploy.log"
BACKUP_DIR="/var/backup/jarvis"
SSL_CERT_DIR="/var/jarvis/ssl"
DATA_DIR="/var/jarvis/data"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging sécurisé
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

error() {
    log "${RED}❌ ERREUR: $1${NC}" >&2
    exit 1
}

warning() {
    log "${YELLOW}⚠️  ATTENTION: $1${NC}"
}

success() {
    log "${GREEN}✅ $1${NC}"
}

info() {
    log "${BLUE}ℹ️  $1${NC}"
}

# Vérifications préalables
check_prerequisites() {
    info "Vérification des prérequis..."
    
    # Vérifier si on est root
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root"
    fi
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        error "Docker n'est pas installé"
    fi
    
    # Vérifier Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose n'est pas installé"
    fi
    
    # Vérifier openssl
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL n'est pas installé"
    fi
    
    # Vérifier les variables d'environnement critiques
    if [[ -z "${CERTBOT_DOMAIN:-}" ]]; then
        error "CERTBOT_DOMAIN doit être défini"
    fi
    
    if [[ -z "${CERTBOT_EMAIL:-}" ]]; then
        error "CERTBOT_EMAIL doit être défini"
    fi
    
    success "Prérequis validés"
}

# Configuration des répertoires sécurisés
setup_directories() {
    info "Configuration des répertoires..."
    
    # Créer les répertoires avec permissions sécurisées
    mkdir -p "$DATA_DIR"/{brain,memory,ollama,redis,postgres,audio}
    mkdir -p "$SSL_CERT_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p /var/jarvis/logs/{nginx,brain,services}
    
    # Permissions sécurisées
    chmod 755 "$DATA_DIR"
    chmod 700 "$SSL_CERT_DIR"
    chmod 700 "$BACKUP_DIR"
    chmod 755 /var/jarvis/logs
    
    # Propriétaires appropriés
    chown -R 1000:1000 "$DATA_DIR"
    chown -R root:root "$SSL_CERT_DIR"
    chown -R root:root "$BACKUP_DIR"
    
    success "Répertoires configurés"
}

# Génération des certificats auto-signés de fallback
generate_fallback_certs() {
    info "Génération des certificats de fallback..."
    
    if [[ ! -f "$SSL_CERT_DIR/selfsigned.crt" ]]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_CERT_DIR/selfsigned.key" \
            -out "$SSL_CERT_DIR/selfsigned.crt" \
            -subj "/C=FR/ST=France/L=Paris/O=JARVIS/OU=AI/CN=localhost"
        
        chmod 600 "$SSL_CERT_DIR/selfsigned.key"
        chmod 644 "$SSL_CERT_DIR/selfsigned.crt"
        
        success "Certificats de fallback générés"
    else
        info "Certificats de fallback déjà présents"
    fi
}

# Génération des paramètres DH
generate_dhparam() {
    info "Génération des paramètres Diffie-Hellman..."
    
    if [[ ! -f "$SSL_CERT_DIR/dhparam.pem" ]]; then
        openssl dhparam -out "$SSL_CERT_DIR/dhparam.pem" 2048
        chmod 644 "$SSL_CERT_DIR/dhparam.pem"
        success "Paramètres DH générés"
    else
        info "Paramètres DH déjà présents"
    fi
}

# Configuration du firewall
setup_firewall() {
    info "Configuration du firewall..."
    
    # Installer ufw si pas présent
    if ! command -v ufw &> /dev/null; then
        apt-get update && apt-get install -y ufw
    fi
    
    # Configuration de base
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Règles essentielles
    ufw allow ssh
    ufw allow 80/tcp  # HTTP (redirection vers HTTPS)
    ufw allow 443/tcp # HTTPS
    
    # Règles pour monitoring (optionnel, IPs restreintes)
    # ufw allow from 10.0.0.0/8 to any port 9090  # Prometheus
    # ufw allow from 192.168.0.0/16 to any port 3001  # Grafana
    
    # Activer le firewall
    ufw --force enable
    
    success "Firewall configuré"
}

# Sécurisation du système
harden_system() {
    info "Durcissement du système..."
    
    # Mise à jour du système
    apt-get update && apt-get upgrade -y
    
    # Installation des outils de sécurité
    apt-get install -y \
        fail2ban \
        rkhunter \
        chkrootkit \
        lynis \
        unattended-upgrades
    
    # Configuration fail2ban
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/jarvis/logs/nginx/access.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/jarvis/logs/nginx/error.log
maxretry = 10
EOF
    
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    # Configuration des mises à jour automatiques
    cat > /etc/apt/apt.conf.d/50unattended-upgrades << EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
    "\${distro_id}ESMApps:\${distro_codename}-apps-security";
    "\${distro_id}ESM:\${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
    
    systemctl enable unattended-upgrades
    
    success "Système durci"
}

# Validation de la configuration de sécurité
validate_security_config() {
    info "Validation de la configuration de sécurité..."
    
    # Vérifier les variables d'environnement sensibles
    if [[ -f "$PROJECT_ROOT/.env.security" ]]; then
        source "$PROJECT_ROOT/.env.security"
        
        # Vérifier JWT_SECRET_KEY
        if [[ -z "${JWT_SECRET_KEY:-}" ]]; then
            error "JWT_SECRET_KEY manquant dans .env.security"
        fi
        
        # Vérifier les hashs de mots de passe
        if [[ -z "${SYSTEM_CONTROL_ADMIN_PASSWORD_HASH:-}" ]]; then
            error "Hashs de mots de passe manquants. Exécutez d'abord generate-secure-passwords.py"
        fi
        
        success "Configuration de sécurité validée"
    else
        error "Fichier .env.security manquant. Exécutez d'abord generate-secure-passwords.py"
    fi
}

# Sauvegarde avant déploiement
backup_existing() {
    info "Sauvegarde de l'installation existante..."
    
    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/jarvis_backup_$BACKUP_TIMESTAMP"
    
    if [[ -d "$DATA_DIR" ]]; then
        mkdir -p "$BACKUP_PATH"
        cp -r "$DATA_DIR" "$BACKUP_PATH/"
        
        # Compresser la sauvegarde
        tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "jarvis_backup_$BACKUP_TIMESTAMP"
        rm -rf "$BACKUP_PATH"
        
        success "Sauvegarde créée: $BACKUP_PATH.tar.gz"
    else
        info "Aucune installation existante à sauvegarder"
    fi
}

# Déploiement des services
deploy_services() {
    info "Déploiement des services..."
    
    cd "$PROJECT_ROOT"
    
    # Copier la configuration de production
    cp docker-compose.production.yml docker-compose.override.yml
    
    # Charger les variables d'environnement
    source .env.security
    export $(cat .env.security | grep -v '^#' | xargs)
    
    # Arrêter les services existants
    docker-compose down --remove-orphans || true
    
    # Construire les images
    docker-compose build --no-cache
    
    # Démarrer les services de base (DB, cache)
    docker-compose up -d redis memory-db
    
    # Attendre que les DB soient prêtes
    sleep 30
    
    # Démarrer tous les services
    docker-compose up -d
    
    success "Services déployés"
}

# Vérification post-déploiement
post_deploy_checks() {
    info "Vérifications post-déploiement..."
    
    # Attendre que les services démarrent
    sleep 60
    
    # Vérifier les services
    if docker-compose ps | grep -q "Up"; then
        success "Services Docker démarrés"
    else
        error "Problème avec les services Docker"
    fi
    
    # Test des endpoints
    if curl -k -f https://localhost/health &> /dev/null; then
        success "Health check réussi"
    else
        warning "Health check échoué - services peut-être en cours de démarrage"
    fi
    
    # Vérifier les logs pour les erreurs
    if docker-compose logs --tail=50 | grep -i error; then
        warning "Erreurs détectées dans les logs"
    fi
    
    success "Vérifications terminées"
}

# Affichage des informations de sécurité
display_security_info() {
    info "🔒 INFORMATIONS DE SÉCURITÉ"
    echo "=================================="
    echo "Domaine: $CERTBOT_DOMAIN"
    echo "URL d'accès: https://$CERTBOT_DOMAIN"
    echo "Logs: /var/jarvis/logs/"
    echo "Données: $DATA_DIR"
    echo "SSL: $SSL_CERT_DIR"
    echo ""
    echo "🔧 COMMANDES UTILES:"
    echo "- Voir les logs: docker-compose logs -f"
    echo "- Redémarrer: systemctl restart docker"
    echo "- Backup: $0 backup"
    echo "- Status: docker-compose ps"
    echo ""
    echo "🚨 RAPPELS SÉCURITÉ:"
    echo "- Changez les mots de passe par défaut"
    echo "- Surveillez les logs régulièrement"
    echo "- Mettez à jour le système fréquemment"
    echo "- Testez les sauvegardes"
    echo "=================================="
}

# Fonction de sauvegarde
do_backup() {
    info "Sauvegarde complète..."
    
    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/jarvis_full_backup_$BACKUP_TIMESTAMP"
    
    # Arrêter temporairement les services pour cohérence
    docker-compose stop
    
    # Créer la sauvegarde
    mkdir -p "$BACKUP_PATH"
    cp -r "$DATA_DIR" "$BACKUP_PATH/"
    cp -r "$PROJECT_ROOT/.env.security" "$BACKUP_PATH/" 2>/dev/null || true
    cp -r "$SSL_CERT_DIR" "$BACKUP_PATH/"
    
    # Exporter la configuration Docker
    docker-compose config > "$BACKUP_PATH/docker-compose-config.yml"
    
    # Compresser
    tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "jarvis_full_backup_$BACKUP_TIMESTAMP"
    rm -rf "$BACKUP_PATH"
    
    # Redémarrer les services
    docker-compose start
    
    success "Sauvegarde complète: $BACKUP_PATH.tar.gz"
}

# Fonction principale
main() {
    case "${1:-deploy}" in
        "deploy")
            info "🚀 Démarrage du déploiement sécurisé JARVIS..."
            check_prerequisites
            setup_directories
            generate_fallback_certs
            generate_dhparam
            setup_firewall
            harden_system
            validate_security_config
            backup_existing
            deploy_services
            post_deploy_checks
            display_security_info
            success "🎉 Déploiement sécurisé terminé!"
            ;;
        "backup")
            do_backup
            ;;
        "update")
            info "🔄 Mise à jour des services..."
            cd "$PROJECT_ROOT"
            docker-compose pull
            docker-compose up -d --force-recreate
            post_deploy_checks
            success "Mise à jour terminée"
            ;;
        "logs")
            cd "$PROJECT_ROOT"
            docker-compose logs -f
            ;;
        "status")
            cd "$PROJECT_ROOT"
            docker-compose ps
            ;;
        *)
            echo "Usage: $0 [deploy|backup|update|logs|status]"
            echo "  deploy - Déploiement complet sécurisé (défaut)"
            echo "  backup - Sauvegarde complète"
            echo "  update - Mise à jour des services"
            echo "  logs   - Afficher les logs"
            echo "  status - Statut des services"
            exit 1
            ;;
    esac
}

# Gestion des signaux pour arrêt propre
cleanup() {
    warning "Arrêt du script..."
    exit 1
}

trap cleanup SIGINT SIGTERM

# Exécution
main "$@"