#!/bin/bash
# JARVIS AI - GPT-OSS 20B Migration - Ollama Host Provisioning Script
# Production-ready infrastructure automation with security hardening

set -euo pipefail

# Configuration
JARVIS_HOME="${JARVIS_HOME:-/opt/jarvis}"
OLLAMA_VERSION="${OLLAMA_VERSION:-0.3.12}"
GPT_OSS_MODEL="${GPT_OSS_MODEL:-gpt-oss:20b}"
LOG_FILE="/var/log/jarvis-provision.log"
BACKUP_DIR="/backup/jarvis"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Pre-flight checks
preflight_checks() {
    log "Starting pre-flight checks..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
    
    # Check system requirements
    local min_ram_gb=32
    local available_ram_gb=$(free -g | awk 'NR==2{print $7}')
    if [[ $available_ram_gb -lt $min_ram_gb ]]; then
        error "Insufficient RAM. Required: ${min_ram_gb}GB, Available: ${available_ram_gb}GB"
    fi
    
    # Check disk space
    local min_disk_gb=100
    local available_disk_gb=$(df / | awk 'NR==2 {print int($4/1024/1024)}')
    if [[ $available_disk_gb -lt $min_disk_gb ]]; then
        error "Insufficient disk space. Required: ${min_disk_gb}GB, Available: ${available_disk_gb}GB"
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com &> /dev/null; then
        error "No internet connectivity"
    fi
    
    success "Pre-flight checks passed"
}

# System hardening
harden_system() {
    log "Hardening system security..."
    
    # Update system packages
    apt-get update && apt-get upgrade -y
    
    # Install security tools
    apt-get install -y \
        fail2ban \
        ufw \
        auditd \
        aide \
        rkhunter \
        chkrootkit \
        unattended-upgrades
    
    # Configure firewall
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 11434/tcp  # Ollama API
    ufw allow 8080/tcp   # JARVIS API
    ufw --force enable
    
    # Configure fail2ban
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
EOF
    
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    # Configure automatic security updates
    cat > /etc/apt/apt.conf.d/50unattended-upgrades << EOF
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-WithUsers "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
EOF
    
    success "System hardening completed"
}

# Install Docker with security configurations
install_docker() {
    log "Installing Docker with security configurations..."
    
    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Configure Docker daemon with security settings
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true,
  "seccomp-profile": "/etc/docker/seccomp.json",
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "default-ulimits": {
    "nofile": {
      "hard": 65536,
      "soft": 65536
    }
  }
}
EOF
    
    # Create Docker security profile
    curl -o /etc/docker/seccomp.json https://raw.githubusercontent.com/docker/labs/master/security/seccomp/seccomp-profiles/default.json
    
    # Add jarvis user to docker group
    useradd -m -s /bin/bash jarvis || true
    usermod -aG docker jarvis
    
    systemctl enable docker
    systemctl restart docker
    
    success "Docker installed and configured"
}

# Install Ollama with GPU optimization
install_ollama() {
    log "Installing Ollama with GPU optimization..."
    
    # Download and install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Create Ollama service configuration
    mkdir -p /etc/systemd/system/ollama.service.d
    cat > /etc/systemd/system/ollama.service.d/override.conf << EOF
[Unit]
Description=Ollama Service with GPU Support
After=docker.service
Requires=docker.service

[Service]
User=jarvis
Group=jarvis
ExecStart=/usr/local/bin/ollama serve
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MODELS=/opt/jarvis/models"
Environment="OLLAMA_KEEP_ALIVE=24h"
Environment="OLLAMA_MAX_LOADED_MODELS=3"
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_FLASH_ATTENTION=1"
Restart=always
RestartSec=10
LimitNOFILE=65536
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Create models directory
    mkdir -p /opt/jarvis/models
    chown -R jarvis:jarvis /opt/jarvis
    
    # Enable and start Ollama service
    systemctl daemon-reload
    systemctl enable ollama
    systemctl start ollama
    
    # Wait for Ollama to be ready
    local max_attempts=30
    local attempt=1
    while ! curl -f http://localhost:11434/api/tags > /dev/null 2>&1; do
        if [[ $attempt -ge $max_attempts ]]; then
            error "Ollama service failed to start"
        fi
        log "Waiting for Ollama to start... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    success "Ollama installed and running"
}

# Pull and optimize GPT-OSS 20B model
setup_gpt_oss_model() {
    log "Setting up GPT-OSS 20B model..."
    
    # Create model configuration
    cat > /opt/jarvis/gpt-oss-20b.modelfile << EOF
FROM ${GPT_OSS_MODEL}

# Performance optimizations
PARAMETER num_ctx 8192
PARAMETER num_batch 512
PARAMETER num_gqa 8
PARAMETER num_gpu 99
PARAMETER num_thread 8
PARAMETER repeat_penalty 1.1
PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9

# Memory optimizations
PARAMETER use_mmap true
PARAMETER use_mlock true
PARAMETER numa true

SYSTEM """
You are JARVIS, an advanced AI assistant with multi-modal capabilities.
You are helpful, efficient, and maintain context across conversations.
"""
EOF
    
    # Pull the model as jarvis user
    sudo -u jarvis ollama pull ${GPT_OSS_MODEL}
    
    # Create optimized model
    sudo -u jarvis ollama create jarvis-gpt-oss-20b -f /opt/jarvis/gpt-oss-20b.modelfile
    
    # Verify model is loaded
    if sudo -u jarvis ollama list | grep -q "jarvis-gpt-oss-20b"; then
        success "GPT-OSS 20B model installed and optimized"
    else
        error "Failed to install GPT-OSS 20B model"
    fi
}

# Install monitoring and observability stack
install_monitoring() {
    log "Installing monitoring stack..."
    
    # Install Node Exporter
    wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
    tar xvfz node_exporter-1.6.1.linux-amd64.tar.gz
    sudo cp node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
    rm -rf node_exporter-1.6.1.linux-amd64*
    
    # Create node_exporter service
    cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=jarvis
Group=jarvis
Type=simple
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:9100
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl enable node_exporter
    systemctl start node_exporter
    
    # Install GPU monitoring (for AMD)
    if lspci | grep -i amd | grep -i vga; then
        apt-get install -y radeontop
        
        # Create GPU monitoring script
        cat > /usr/local/bin/gpu-monitor.sh << 'EOF'
#!/bin/bash
while true; do
    radeontop -d /dev/dri/card0 -l 1 | grep -E "(gpu|vram)" >> /var/log/gpu-stats.log
    sleep 5
done
EOF
        chmod +x /usr/local/bin/gpu-monitor.sh
        
        # Create GPU monitoring service
        cat > /etc/systemd/system/gpu-monitor.service << EOF
[Unit]
Description=GPU Monitoring Service
After=multi-user.target

[Service]
Type=simple
User=jarvis
ExecStart=/usr/local/bin/gpu-monitor.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl enable gpu-monitor
        systemctl start gpu-monitor
    fi
    
    success "Monitoring stack installed"
}

# Setup backup system
setup_backup_system() {
    log "Setting up backup system..."
    
    mkdir -p "$BACKUP_DIR"/{models,data,configs}
    
    # Create backup script
    cat > /usr/local/bin/jarvis-backup.sh << EOF
#!/bin/bash
set -euo pipefail

TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT="$BACKUP_DIR/\$TIMESTAMP"

mkdir -p "\$BACKUP_ROOT"

# Backup Ollama models
rsync -av /opt/jarvis/models/ "\$BACKUP_ROOT/models/"

# Backup configuration files
cp -r /etc/docker "\$BACKUP_ROOT/configs/"
cp -r /etc/systemd/system/ollama.service.d "\$BACKUP_ROOT/configs/"

# Compress backup
tar -czf "$BACKUP_DIR/jarvis-backup-\$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "\$TIMESTAMP"
rm -rf "\$BACKUP_ROOT"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "jarvis-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed: jarvis-backup-\$TIMESTAMP.tar.gz"
EOF
    
    chmod +x /usr/local/bin/jarvis-backup.sh
    
    # Setup daily backup cron
    echo "0 2 * * * root /usr/local/bin/jarvis-backup.sh" >> /etc/crontab
    
    success "Backup system configured"
}

# Configure health checks
setup_health_checks() {
    log "Setting up health checks..."
    
    cat > /usr/local/bin/jarvis-health-check.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Health check endpoints
OLLAMA_URL="http://localhost:11434/api/tags"
DOCKER_CHECK="docker system df"

# Check Ollama
if ! curl -f "$OLLAMA_URL" > /dev/null 2>&1; then
    echo "CRITICAL: Ollama service is down"
    exit 2
fi

# Check Docker
if ! $DOCKER_CHECK > /dev/null 2>&1; then
    echo "CRITICAL: Docker service is down"
    exit 2
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [[ $DISK_USAGE -gt 90 ]]; then
    echo "WARNING: Disk usage is at ${DISK_USAGE}%"
    exit 1
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [[ $MEM_USAGE -gt 90 ]]; then
    echo "WARNING: Memory usage is at ${MEM_USAGE}%"
    exit 1
fi

echo "OK: All services healthy"
exit 0
EOF
    
    chmod +x /usr/local/bin/jarvis-health-check.sh
    
    # Setup health check cron (every 5 minutes)
    echo "*/5 * * * * root /usr/local/bin/jarvis-health-check.sh" >> /etc/crontab
    
    success "Health checks configured"
}

# Main installation function
main() {
    log "Starting JARVIS AI GPT-OSS 20B Host Provisioning..."
    
    preflight_checks
    harden_system
    install_docker
    install_ollama
    setup_gpt_oss_model
    install_monitoring
    setup_backup_system
    setup_health_checks
    
    # Final system status
    log "Provisioning completed successfully!"
    log "System Status:"
    log "- Docker: $(docker --version)"
    log "- Ollama: $(ollama --version)"
    log "- Models: $(sudo -u jarvis ollama list | wc -l) installed"
    log "- Monitoring: Node Exporter on :9100"
    log "- Backups: Daily at 2:00 AM"
    log "- Health Checks: Every 5 minutes"
    
    success "JARVIS AI GPT-OSS 20B Host ready for production!"
    
    cat << EOF

╔══════════════════════════════════════════════════════════════════╗
║                    JARVIS AI HOST READY                         ║
║                                                                  ║
║  Ollama API:     http://$(hostname -I | awk '{print $1}'):11434              ║
║  Health Check:   /usr/local/bin/jarvis-health-check.sh          ║
║  Backup:         /usr/local/bin/jarvis-backup.sh                ║
║  Logs:           /var/log/jarvis-provision.log                  ║
║                                                                  ║
║  Next Steps:                                                     ║
║  1. Test model: ollama run jarvis-gpt-oss-20b                   ║
║  2. Deploy Docker services                                       ║
║  3. Configure monitoring dashboard                               ║
╚══════════════════════════════════════════════════════════════════╝
EOF
}

# Run main function
main "$@"