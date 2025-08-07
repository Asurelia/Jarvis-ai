# ============================================================
# JARVIS AI - PowerShell Ultimate Launcher
# Advanced version with better error handling and logging
# ============================================================

param(
    [switch]$SkipChecks,
    [switch]$DevMode,
    [switch]$Quiet,
    [string]$LogFile = "jarvis-launch.log"
)

# Set execution policy for current session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Initialize
$Host.UI.RawUI.WindowTitle = "JARVIS AI - PowerShell Launcher"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

# Logging function
function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    if (-not $Quiet) {
        switch ($Level) {
            "ERROR" { Write-Host $logEntry -ForegroundColor Red }
            "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
            "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
            default { Write-Host $logEntry -ForegroundColor Cyan }
        }
    }
    
    Add-Content -Path $LogFile -Value $logEntry
}

# Banner
Write-Host @"

============================================================
           JARVIS AI 2025 - PowerShell Launcher
           Version 3.0.0 - Full Stack Edition
============================================================

"@ -ForegroundColor Green

Write-Log "Starting JARVIS AI complete initialization"

# Check prerequisites
if (-not $SkipChecks) {
    Write-Log "Checking prerequisites..."
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Log "Python detected: $pythonVersion" "SUCCESS"
    }
    catch {
        Write-Log "Python is not installed or not in PATH!" "ERROR"
        Write-Log "Please install Python 3.11+ from https://python.org" "ERROR"
        exit 1
    }
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>&1
        Write-Log "Docker detected: $dockerVersion" "SUCCESS"
    }
    catch {
        Write-Log "Docker is not installed!" "ERROR"
        Write-Log "Please install Docker Desktop from https://docker.com" "ERROR"
        exit 1
    }
    
    # Check Docker running
    try {
        docker info 2>&1 | Out-Null
        Write-Log "Docker is running" "SUCCESS"
    }
    catch {
        Write-Log "Docker is not running. Attempting to start..." "WARNING"
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
        Write-Log "Waiting 30 seconds for Docker to start..."
        Start-Sleep 30
        
        try {
            docker info 2>&1 | Out-Null
            Write-Log "Docker started successfully" "SUCCESS"
        }
        catch {
            Write-Log "Failed to start Docker!" "ERROR"
            exit 1
        }
    }
}

# Check port availability
Write-Log "Checking port availability..."
$ports = @(3000, 3001, 5002, 5003, 5004, 5005, 5006, 5007, 5432, 6379, 8080, 8081, 11434)
$blockedPorts = @()

foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        $blockedPorts += $port
        Write-Log "Port $port is in use" "WARNING"
    }
}

if ($blockedPorts.Count -gt 0 -and -not $DevMode) {
    $response = Read-Host "Some ports are in use. Stop existing services? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Log "Stopping existing Docker containers..."
        docker-compose down 2>&1 | Out-Null
        docker stop $(docker ps -aq) 2>&1 | Out-Null
        Start-Sleep 3
    }
}

# Setup Python environment
Write-Log "Setting up Python virtual environment..."
if (-not (Test-Path "venv")) {
    Write-Log "Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Failed to create virtual environment!" "ERROR"
        exit 1
    }
}

# Activate virtual environment
Write-Log "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Log "Upgrading pip..."
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null

# Install dependencies
Write-Log "Installing Python dependencies..."
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet --disable-pip-version-check 2>&1 | Out-Null
}

# Install service-specific requirements
$serviceDirs = @("services\brain-api", "services\tts-service", "services\stt-service", "database", "api")
foreach ($dir in $serviceDirs) {
    $reqFile = Join-Path $dir "requirements.txt"
    if (Test-Path $reqFile) {
        Write-Log "Installing $dir requirements..."
        pip install -r $reqFile --quiet --disable-pip-version-check 2>&1 | Out-Null
    }
}

# Generate environment file
Write-Log "Setting up environment configuration..."
if (-not (Test-Path ".env")) {
    Write-Log "Creating secure .env file..."
    $envContent = @"
# JARVIS AI Environment Configuration
# Generated: $(Get-Date)

# API Configuration
BRAIN_API_HOST=0.0.0.0
BRAIN_API_PORT=8080
BRAIN_DEBUG=false
JWT_SECRET_KEY=$(Get-Random -Minimum 100000 -Maximum 999999)$(Get-Random -Minimum 100000 -Maximum 999999)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Configuration
POSTGRES_USER=jarvis
POSTGRES_PASSWORD=jarvis_$(Get-Random -Minimum 10000 -Maximum 99999)
POSTGRES_DB=jarvis_memory
DATABASE_URL=postgresql://jarvis:jarvis_$(Get-Random -Minimum 10000 -Maximum 99999)@localhost:5432/jarvis_memory

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_$(Get-Random -Minimum 10000 -Maximum 99999)
REDIS_URL=redis://:redis_$(Get-Random -Minimum 10000 -Maximum 99999)@localhost:6379

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Security
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true
SECURITY_MODE=production

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
LOG_LEVEL=INFO
"@
    Set-Content -Path ".env" -Value $envContent
    Write-Log "Environment file created" "SUCCESS"
}

# Clean up old containers
Write-Log "Cleaning up old containers and volumes..."
docker-compose down --remove-orphans 2>&1 | Out-Null
docker system prune -f --volumes 2>&1 | Out-Null

# Build images
Write-Log "Building Docker images (this may take a few minutes)..."
try {
    docker-compose build --parallel 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Parallel build failed, trying sequential..." "WARNING"
        docker-compose build 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Build failed"
        }
    }
    Write-Log "Docker images built successfully" "SUCCESS"
}
catch {
    Write-Log "Docker build failed!" "ERROR"
    exit 1
}

# Start services in sequence
Write-Log "Starting core infrastructure..."

Write-Log "Starting PostgreSQL database..."
docker-compose up -d memory-db 2>&1 | Out-Null
Start-Sleep 5

Write-Log "Starting Redis cache..."
docker-compose up -d redis 2>&1 | Out-Null
Start-Sleep 3

Write-Log "Starting Ollama LLM service..."
docker-compose up -d ollama 2>&1 | Out-Null
Start-Sleep 5

# Initialize database
Write-Log "Initializing database..."
$attempts = 0
do {
    $attempts++
    try {
        docker exec jarvis-memory-db pg_isready -U jarvis 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
    }
    catch {}
    Start-Sleep 2
} while ($attempts -lt 30)

if (Test-Path "database\scripts\init_database.py") {
    python database\scripts\init_database.py 2>&1 | Out-Null
}

# Start AI services
Write-Log "Starting AI services pod..."
docker-compose up -d brain-api 2>&1 | Out-Null
Start-Sleep 5

# Wait for Brain API health
Write-Log "Waiting for Brain API health check..."
$attempts = 0
do {
    $attempts++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 5 2>&1
        if ($response.StatusCode -eq 200) { 
            Write-Log "Brain API is healthy" "SUCCESS"
            break 
        }
    }
    catch {}
    Start-Sleep 2
} while ($attempts -lt 30)

# Start audio services
Write-Log "Starting Audio services pod..."
docker-compose up -d tts-service stt-service 2>&1 | Out-Null
Start-Sleep 3

# Start control services
Write-Log "Starting Control services pod..."
docker-compose up -d system-control terminal-service 2>&1 | Out-Null
Start-Sleep 2

# Start integration services
Write-Log "Starting Integration services..."
docker-compose up -d mcp-gateway autocomplete-service 2>&1 | Out-Null
docker-compose up -d gpu-stats-service 2>&1 | Out-Null
Start-Sleep 2

# Start monitoring
if (Test-Path "docker-compose.monitoring.yml") {
    Write-Log "Starting monitoring stack..."
    docker-compose -f docker-compose.monitoring.yml up -d prometheus grafana loki 2>&1 | Out-Null
}

# Start frontend
Write-Log "Starting Frontend UI..."
Set-Location ui
if (-not (Test-Path "node_modules")) {
    Write-Log "Installing UI dependencies (first time setup)..."
    npm install 2>&1 | Out-Null
}

Write-Log "Building and starting UI..."
Start-Process -FilePath "npm" -ArgumentList "start" -WindowStyle Hidden
Set-Location ..

# Start voice bridge
if (Test-Path "local-interface\voice-bridge.py") {
    Write-Log "Starting voice bridge..."
    Set-Location local-interface
    Start-Process -FilePath "python" -ArgumentList "voice-bridge.py" -WindowStyle Hidden
    Set-Location ..
}

# Final health checks
Write-Log "Running final health checks..."
Start-Sleep 10

$services = @{
    "Brain API" = "http://localhost:8080/health"
    "Frontend UI" = "http://localhost:3000"
    "TTS Service" = "http://localhost:5002/health"
    "STT Service" = "http://localhost:5003/health"
    "Ollama LLM" = "http://localhost:11434/api/tags"
    "Voice Bridge" = "http://localhost:3001"
}

$healthyServices = 0
$totalServices = $services.Count

Write-Log "`nService Status:" "INFO"
Write-Log "-------------------" "INFO"

foreach ($service in $services.GetEnumerator()) {
    try {
        $response = Invoke-WebRequest -Uri $service.Value -UseBasicParsing -TimeoutSec 5 2>&1
        if ($response.StatusCode -eq 200) {
            Write-Log "$($service.Key): HEALTHY" "SUCCESS"
            $healthyServices++
        } else {
            Write-Log "$($service.Key): UNHEALTHY" "WARNING"
        }
    }
    catch {
        if ($service.Key -eq "Voice Bridge") {
            Write-Log "$($service.Key): OPTIONAL" "INFO"
        } else {
            Write-Log "$($service.Key): DOWN" "ERROR"
        }
    }
}

# Final summary
Write-Host @"

============================================================
              JARVIS AI LAUNCH COMPLETE!
============================================================

Services Running: $healthyServices / $totalServices

Access Points:
--------------
  Main Interface:    http://localhost:3000
  API Documentation: http://localhost:8080/docs
  Voice Bridge:      http://localhost:3001
  Monitoring:        http://localhost:9090 (Prometheus)
                     http://localhost:3000 (Grafana)

Quick Commands:
---------------
  View Logs:     docker-compose logs -f [service-name]
  Stop All:      docker-compose down
  Restart:       docker-compose restart [service-name]
  Health Check:  Invoke-WebRequest http://localhost:8080/health

Memory Usage:  docker stats
Clean Cache:   python cleanup-project.py

============================================================
         JARVIS IS READY!
============================================================

"@ -ForegroundColor Green

# Open browser
Start-Sleep 3
Start-Process "http://localhost:3000"

Write-Log "JARVIS AI launch completed successfully" "SUCCESS"
Write-Log "Log file saved to: $LogFile" "INFO"

# Keep PowerShell window open
if (-not $Quiet) {
    Read-Host "Press Enter to exit"
}