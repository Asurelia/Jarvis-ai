#!/bin/bash
# JARVIS AI - Hybrid Stack Deployment Automation
# Automated deployment with blue/green strategy and health validation

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
JARVIS_VERSION="${JARVIS_VERSION:-latest}"
DEPLOYMENT_STRATEGY="${DEPLOYMENT_STRATEGY:-blue-green}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

# Load environment configuration
load_environment() {
    log "Loading environment configuration for: $DEPLOYMENT_ENV"
    
    local env_file="$PROJECT_ROOT/.env.$DEPLOYMENT_ENV"
    if [[ ! -f "$env_file" ]]; then
        error "Environment file not found: $env_file"
    fi
    
    # Source environment file
    set -a
    source "$env_file"
    set +a
    
    # Validate required variables
    local required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "JWT_SECRET_KEY"
        "JARVIS_API_KEY"
        "OLLAMA_HOST_URL"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable $var is not set"
        fi
    done
    
    success "Environment configuration loaded"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check Docker
    if ! docker --version &>/dev/null; then
        error "Docker is not installed or not running"
    fi
    
    if ! docker-compose --version &>/dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check available resources
    local available_memory=$(free -g | awk 'NR==2{print $7}')
    if [[ $available_memory -lt 8 ]]; then
        warning "Available memory is low: ${available_memory}GB (recommended: 16GB+)"
    fi
    
    local available_disk=$(df / | awk 'NR==2 {print int($4/1024/1024)}')
    if [[ $available_disk -lt 50 ]]; then
        error "Insufficient disk space: ${available_disk}GB (required: 50GB+)"
    fi
    
    # Check Ollama host connectivity
    if ! curl -f "$OLLAMA_HOST_URL/api/tags" &>/dev/null; then
        error "Cannot connect to Ollama host: $OLLAMA_HOST_URL"
    fi
    
    # Check network ports
    local ports=(80 443 8080 5432 6379)
    for port in "${ports[@]}"; do
        if netstat -tuln | grep ":$port " &>/dev/null; then
            warning "Port $port is already in use"
        fi
    done
    
    success "Pre-deployment checks passed"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build all services
    local services=("brain-api" "tts-service" "stt-service")
    
    for service in "${services[@]}"; do
        info "Building $service..."
        docker build \
            -t "jarvis/$service:$JARVIS_VERSION" \
            -f "services/$service/Dockerfile" \
            "services/$service" \
            --build-arg VERSION="$JARVIS_VERSION" \
            --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
            --no-cache
        
        # Tag as latest
        docker tag "jarvis/$service:$JARVIS_VERSION" "jarvis/$service:latest"
    done
    
    success "Docker images built successfully"
}

# Database migration and initialization
initialize_database() {
    log "Initializing database..."
    
    # Start PostgreSQL in temporary mode for initialization
    docker-compose -f devops/infrastructure/docker/docker-compose.hybrid-production.yml \
        up -d postgres-prod
    
    # Wait for PostgreSQL to be ready
    local max_attempts=60
    local attempt=1
    while ! docker exec jarvis_postgres_prod pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" &>/dev/null; do
        if [[ $attempt -ge $max_attempts ]]; then
            error "PostgreSQL failed to start within timeout"
        fi
        info "Waiting for PostgreSQL to be ready... ($attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    # Run database migrations
    info "Running database migrations..."
    docker run --rm \
        --network "jarvis_data" \
        -e POSTGRES_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres-prod:5432/$POSTGRES_DB" \
        -v "$PROJECT_ROOT/database/migrations:/app/migrations" \
        jarvis/brain-api:$JARVIS_VERSION \
        python -m alembic upgrade head
    
    success "Database initialized successfully"
}

# Blue/Green deployment strategy
blue_green_deployment() {
    log "Starting blue/green deployment..."
    
    local current_env="blue"
    local new_env="green"
    
    # Check if blue environment is running
    if docker-compose -f devops/infrastructure/docker/docker-compose.hybrid-production.yml \
        ps --services --filter "status=running" | grep -q "brain-api"; then
        current_env="green"
        new_env="blue"
    fi
    
    info "Deploying to $new_env environment (current: $current_env)"
    
    # Create new environment configuration
    export COMPOSE_PROJECT_NAME="jarvis-$new_env"
    export BRAIN_API_PORT=$((8080 + (new_env == "blue" ? 0 : 100)))
    export BRAIN_WEBSOCKET_PORT=$((8081 + (new_env == "blue" ? 0 : 100)))
    
    # Deploy new environment
    docker-compose -f devops/infrastructure/docker/docker-compose.hybrid-production.yml \
        --project-name "jarvis-$new_env" \
        up -d
    
    # Wait for new environment to be healthy
    wait_for_health_check "$new_env"
    
    # Run deployment tests
    run_deployment_tests "$new_env"
    
    # Switch traffic to new environment
    switch_traffic "$current_env" "$new_env"
    
    # Cleanup old environment
    cleanup_old_environment "$current_env"
    
    success "Blue/green deployment completed"
}

# Rolling deployment strategy
rolling_deployment() {
    log "Starting rolling deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Deploy with rolling update
    docker-compose -f devops/infrastructure/docker/docker-compose.hybrid-production.yml \
        up -d --scale brain-api=2
    
    # Wait for new instances to be healthy
    wait_for_health_check "production"
    
    # Update remaining services
    docker-compose -f devops/infrastructure/docker/docker-compose.hybrid-production.yml \
        up -d
    
    success "Rolling deployment completed"
}

# Wait for health checks
wait_for_health_check() {
    local env="$1"
    log "Waiting for health checks to pass for $env environment..."
    
    local services=("brain-api" "tts-service" "stt-service" "postgres-prod" "redis-prod")
    local max_attempts=120
    
    for service in "${services[@]}"; do
        info "Checking health of $service..."
        local attempt=1
        local container_name="jarvis_${service//-/_}_prod"
        
        if [[ "$env" != "production" ]]; then
            container_name="jarvis-$env-${service//-/_}-1"
        fi
        
        while [[ $attempt -le $max_attempts ]]; do
            if docker exec "$container_name" \
                sh -c 'curl -f http://localhost:$(echo $0 | grep -o "[0-9]*")/health' \
                "$service" &>/dev/null; then
                success "$service is healthy"
                break
            fi
            
            if [[ $attempt -eq $max_attempts ]]; then
                error "$service failed health check after $max_attempts attempts"
            fi
            
            sleep 5
            ((attempt++))
        done
    done
    
    success "All services are healthy"
}

# Run deployment tests
run_deployment_tests() {
    local env="$1"
    log "Running deployment tests for $env environment..."
    
    local base_url="http://localhost:${BRAIN_API_PORT:-8080}"
    
    # Test API health
    if ! curl -f "$base_url/health/ready" &>/dev/null; then
        error "API health check failed"
    fi
    
    # Test Ollama connectivity
    local test_payload='{"model": "jarvis-gpt-oss-20b", "messages": [{"role": "user", "content": "Test"}]}'
    if ! curl -f "$base_url/api/chat" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JARVIS_API_KEY" \
        -d "$test_payload" &>/dev/null; then
        error "Ollama integration test failed"
    fi
    
    # Test database connectivity
    if ! curl -f "$base_url/api/health/db" &>/dev/null; then
        error "Database connectivity test failed"
    fi
    
    # Test Redis connectivity
    if ! curl -f "$base_url/api/health/cache" &>/dev/null; then
        error "Redis connectivity test failed"
    fi
    
    success "All deployment tests passed"
}

# Switch traffic between environments
switch_traffic() {
    local old_env="$1"
    local new_env="$2"
    log "Switching traffic from $old_env to $new_env..."
    
    # Update load balancer configuration
    info "Updating load balancer..."
    
    # For Traefik, we update the service labels
    docker-compose -f devops/infrastructure/docker/docker-compose.hybrid-production.yml \
        --project-name "jarvis-$new_env" \
        up -d traefik
    
    success "Traffic switched to $new_env environment"
}

# Cleanup old environment
cleanup_old_environment() {
    local old_env="$1"
    log "Cleaning up $old_env environment..."
    
    # Wait for grace period
    sleep 30
    
    # Stop old environment
    docker-compose -f devops/infrastructure/docker/docker-compose.hybrid-production.yml \
        --project-name "jarvis-$old_env" \
        down
    
    # Remove old images
    docker image prune -f --filter "label=jarvis.environment=$old_env"
    
    success "$old_env environment cleaned up"
}

# Rollback deployment
rollback_deployment() {
    log "Rolling back deployment..."
    
    # Get previous version from Git
    local previous_version=$(git log --oneline -n 2 | tail -n 1 | cut -d' ' -f1)
    
    info "Rolling back to version: $previous_version"
    
    # Checkout previous version
    git checkout "$previous_version"
    
    # Redeploy previous version
    JARVIS_VERSION="$previous_version" deploy_services
    
    success "Rollback completed to version $previous_version"
}

# Deploy services based on strategy
deploy_services() {
    case "$DEPLOYMENT_STRATEGY" in
        "blue-green")
            blue_green_deployment
            ;;
        "rolling")
            rolling_deployment
            ;;
        *)
            error "Unknown deployment strategy: $DEPLOYMENT_STRATEGY"
            ;;
    esac
}

# Post-deployment tasks
post_deployment_tasks() {
    log "Running post-deployment tasks..."
    
    # Update monitoring dashboards
    info "Updating monitoring dashboards..."
    docker exec jarvis_grafana_prod \
        curl -X POST http://admin:${GRAFANA_ADMIN_PASSWORD}@localhost:3000/api/dashboards/import \
        -H "Content-Type: application/json" \
        -d @/etc/grafana/provisioning/dashboards/jarvis-overview.json
    
    # Send deployment notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        info "Sending deployment notification..."
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"✅ JARVIS AI deployed successfully to $DEPLOYMENT_ENV (version: $JARVIS_VERSION)\"}"
    fi
    
    # Update service discovery
    info "Updating service discovery..."
    # This would integrate with your service discovery system
    
    success "Post-deployment tasks completed"
}

# Backup before deployment
backup_current_state() {
    log "Creating backup before deployment..."
    
    local backup_dir="/backup/jarvis/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    docker exec jarvis_postgres_prod \
        pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        > "$backup_dir/database_backup.sql"
    
    # Backup Redis
    docker exec jarvis_redis_prod \
        redis-cli -a "$REDIS_PASSWORD" --rdb - \
        > "$backup_dir/redis_backup.rdb"
    
    # Backup configuration
    cp -r "$PROJECT_ROOT/.env.$DEPLOYMENT_ENV" "$backup_dir/"
    cp -r "$PROJECT_ROOT/devops/infrastructure" "$backup_dir/"
    
    success "Backup created: $backup_dir"
}

# Main deployment function
main() {
    log "Starting JARVIS AI Hybrid Stack Deployment..."
    info "Environment: $DEPLOYMENT_ENV"
    info "Version: $JARVIS_VERSION"
    info "Strategy: $DEPLOYMENT_STRATEGY"
    
    # Deployment steps
    load_environment
    pre_deployment_checks
    backup_current_state
    build_images
    initialize_database
    deploy_services
    post_deployment_tasks
    
    success "🚀 JARVIS AI Hybrid Stack deployed successfully!"
    
    # Display deployment summary
    cat << EOF

╔══════════════════════════════════════════════════════════════════╗
║                    DEPLOYMENT SUMMARY                           ║
║                                                                  ║
║  Environment:    $DEPLOYMENT_ENV                                          ║
║  Version:        $JARVIS_VERSION                                          ║
║  Strategy:       $DEPLOYMENT_STRATEGY                                     ║
║                                                                  ║
║  Services:                                                       ║
║  - Brain API:    http://localhost:${BRAIN_API_PORT:-8080}                         ║
║  - TTS Service:  http://localhost:${TTS_PORT:-5002}                           ║
║  - STT Service:  http://localhost:${STT_PORT:-5003}                           ║
║  - Grafana:      http://localhost:${GRAFANA_PORT:-3001}                        ║
║  - Prometheus:   http://localhost:${PROMETHEUS_PORT:-9090}                     ║
║                                                                  ║
║  Ollama Host:    $OLLAMA_HOST_URL                                ║
║  Model:          jarvis-gpt-oss-20b                             ║
║                                                                  ║
║  Next Steps:                                                     ║
║  1. Test all endpoints                                           ║
║  2. Monitor performance metrics                                  ║
║  3. Run integration tests                                        ║
╚══════════════════════════════════════════════════════════════════╝
EOF
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback_deployment
        ;;
    "health-check")
        wait_for_health_check "production"
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|health-check}"
        exit 1
        ;;
esac