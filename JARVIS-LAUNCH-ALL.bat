@echo off
REM ============================================================
REM JARVIS AI - ULTIMATE LAUNCH SCRIPT
REM Initializes EVERYTHING: Docker, Services, UI, Monitoring
REM ============================================================

setlocal EnableDelayedExpansion
color 0A
title JARVIS AI - Complete System Launcher

echo.
echo ============================================================
echo           JARVIS AI 2025 - ULTIMATE LAUNCHER
echo           Version 3.0.0 - Full Stack Edition
echo ============================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Set project root
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo [1/15] Setting up environment...
echo ============================================================

REM Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python detected

REM Check Docker
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker is not installed or not running!
    echo Please install Docker Desktop from https://docker.com
    pause
    exit /b 1
)
echo [OK] Docker detected

REM Check Docker running
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Docker Desktop is not running. Starting it...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker to start (30 seconds)...
    timeout /t 30 /nobreak >nul
    docker info >nul 2>&1
    if %errorLevel% neq 0 (
        echo [ERROR] Docker failed to start!
        pause
        exit /b 1
    )
)
echo [OK] Docker is running

echo.
echo [2/15] Checking network configuration...
echo ============================================================

REM Check if ports are available
set "PORTS_TO_CHECK=3000 3001 5002 5003 5004 5005 5006 5007 5432 6379 8080 8081 11434"
set "BLOCKED_PORTS="

for %%p in (%PORTS_TO_CHECK%) do (
    netstat -an | findstr :%%p | findstr LISTENING >nul 2>&1
    if !errorLevel! equ 0 (
        set "BLOCKED_PORTS=!BLOCKED_PORTS! %%p"
        echo [WARNING] Port %%p is already in use
    )
)

if not "!BLOCKED_PORTS!"=="" (
    echo.
    echo [WARNING] The following ports are in use: !BLOCKED_PORTS!
    echo Do you want to stop existing services? (Y/N)
    choice /C YN /N
    if !errorLevel! equ 1 (
        echo Stopping existing Docker containers...
        docker-compose down >nul 2>&1
        docker stop $(docker ps -aq) >nul 2>&1
        timeout /t 3 /nobreak >nul
    )
)

echo.
echo [3/15] Setting up Python virtual environment...
echo ============================================================

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

echo.
echo [4/15] Installing Python dependencies...
echo ============================================================

if exist "requirements.txt" (
    echo Installing main requirements...
    pip install -r requirements.txt --quiet --disable-pip-version-check
)

REM Install service-specific requirements
set "SERVICE_DIRS=services\brain-api services\tts-service services\stt-service database api"
for %%d in (%SERVICE_DIRS%) do (
    if exist "%%d\requirements.txt" (
        echo Installing %%d requirements...
        pip install -r %%d\requirements.txt --quiet --disable-pip-version-check 2>nul
    )
)

echo.
echo [5/15] Generating secure environment variables...
echo ============================================================

if not exist ".env" (
    echo Creating .env file with secure defaults...
    (
        echo # JARVIS AI Environment Configuration
        echo # Generated: %DATE% %TIME%
        echo.
        echo # API Configuration
        echo BRAIN_API_HOST=0.0.0.0
        echo BRAIN_API_PORT=8080
        echo BRAIN_DEBUG=false
        echo JWT_SECRET_KEY=%RANDOM%%RANDOM%%RANDOM%%RANDOM%
        echo JWT_ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # Database Configuration
        echo POSTGRES_USER=jarvis
        echo POSTGRES_PASSWORD=jarvis_%RANDOM%%RANDOM%
        echo POSTGRES_DB=jarvis_memory
        echo DATABASE_URL=postgresql://jarvis:jarvis_%RANDOM%%RANDOM%@localhost:5432/jarvis_memory
        echo.
        echo # Redis Configuration  
        echo REDIS_HOST=localhost
        echo REDIS_PORT=6379
        echo REDIS_PASSWORD=redis_%RANDOM%%RANDOM%
        echo REDIS_URL=redis://:redis_%RANDOM%%RANDOM%@localhost:6379
        echo.
        echo # Ollama Configuration
        echo OLLAMA_HOST=http://localhost:11434
        echo OLLAMA_MODEL=llama3.2:3b
        echo.
        echo # Security
        echo ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
        echo CORS_ALLOW_CREDENTIALS=true
        echo SECURITY_MODE=production
        echo.
        echo # Monitoring
        echo PROMETHEUS_ENABLED=true
        echo GRAFANA_ENABLED=true
        echo LOG_LEVEL=INFO
    ) > .env
    echo [OK] Environment file created
) else (
    echo [OK] Environment file exists
)

echo.
echo [6/15] Cleaning up old containers and volumes...
echo ============================================================

echo Removing orphaned containers...
docker-compose down --remove-orphans >nul 2>&1

echo Pruning unused Docker resources...
docker system prune -f --volumes >nul 2>&1

echo.
echo [7/15] Building Docker images...
echo ============================================================

echo Building all services (this may take a few minutes)...
docker-compose build --parallel

if %errorLevel% neq 0 (
    echo [ERROR] Docker build failed!
    echo Trying sequential build...
    docker-compose build
    if %errorLevel% neq 0 (
        echo [ERROR] Build failed completely!
        pause
        exit /b 1
    )
)

echo.
echo [8/15] Starting core infrastructure...
echo ============================================================

echo Starting PostgreSQL database...
docker-compose up -d memory-db
timeout /t 5 /nobreak >nul

echo Starting Redis cache...
docker-compose up -d redis
timeout /t 3 /nobreak >nul

echo Starting Ollama LLM service...
docker-compose up -d ollama
timeout /t 5 /nobreak >nul

echo.
echo [9/15] Initializing database...
echo ============================================================

echo Waiting for database to be ready...
:WAIT_DB
docker exec jarvis-memory-db pg_isready -U jarvis >nul 2>&1
if %errorLevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto WAIT_DB
)

echo Running database migrations...
if exist "database\scripts\init_database.py" (
    python database\scripts\init_database.py
)

echo.
echo [10/15] Starting AI services pod...
echo ============================================================

echo Starting Brain API...
docker-compose up -d brain-api
timeout /t 5 /nobreak >nul

echo Waiting for Brain API health check...
:WAIT_BRAIN
curl -f http://localhost:8080/health >nul 2>&1
if %errorLevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto WAIT_BRAIN
)
echo [OK] Brain API is healthy

echo.
echo [11/15] Starting Audio services pod...
echo ============================================================

echo Starting TTS service...
docker-compose up -d tts-service
timeout /t 3 /nobreak >nul

echo Starting STT service...
docker-compose up -d stt-service
timeout /t 3 /nobreak >nul

echo.
echo [12/15] Starting Control services pod...
echo ============================================================

echo Starting System Control (secured)...
docker-compose up -d system-control
timeout /t 2 /nobreak >nul

echo Starting Terminal service...
docker-compose up -d terminal-service
timeout /t 2 /nobreak >nul

echo.
echo [13/15] Starting Integration services...
echo ============================================================

echo Starting MCP Gateway...
docker-compose up -d mcp-gateway
timeout /t 2 /nobreak >nul

echo Starting Autocomplete service...
docker-compose up -d autocomplete-service
timeout /t 2 /nobreak >nul

echo Starting GPU Stats service...
docker-compose up -d gpu-stats-service 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [14/15] Starting monitoring stack...
echo ============================================================

if exist "docker-compose.monitoring.yml" (
    echo Starting Prometheus...
    docker-compose -f docker-compose.monitoring.yml up -d prometheus
    
    echo Starting Grafana...
    docker-compose -f docker-compose.monitoring.yml up -d grafana
    
    echo Starting Loki...
    docker-compose -f docker-compose.monitoring.yml up -d loki
)

echo.
echo [15/15] Starting Frontend UI...
echo ============================================================

cd ui
if not exist "node_modules" (
    echo Installing UI dependencies (first time setup)...
    call npm install
)

echo Building UI for production...
call npm run build >nul 2>&1

echo Starting UI server...
start /B npm start >nul 2>&1

cd ..

echo.
echo [BONUS] Starting Voice Bridge (local audio)...
echo ============================================================

if exist "local-interface\voice-bridge.py" (
    echo Starting voice bridge on port 3001...
    cd local-interface
    start /B python voice-bridge.py >nul 2>&1
    cd ..
)

echo.
echo [FINAL] Running health checks...
echo ============================================================

timeout /t 5 /nobreak >nul

set "SERVICES_OK=0"
set "SERVICES_FAILED=0"

echo.
echo Service Status:
echo -------------------

REM Check all services
curl -f http://localhost:8080/health >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Brain API - http://localhost:8080
    set /a SERVICES_OK+=1
) else (
    echo [FAIL] Brain API
    set /a SERVICES_FAILED+=1
)

curl -f http://localhost:3000 >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Frontend UI - http://localhost:3000
    set /a SERVICES_OK+=1
) else (
    echo [PENDING] Frontend UI (may take 30s to start)
    set /a SERVICES_FAILED+=1
)

curl -f http://localhost:5002/health >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] TTS Service - http://localhost:5002
    set /a SERVICES_OK+=1
) else (
    echo [FAIL] TTS Service
    set /a SERVICES_FAILED+=1
)

curl -f http://localhost:5003/health >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] STT Service - http://localhost:5003
    set /a SERVICES_OK+=1
) else (
    echo [FAIL] STT Service
    set /a SERVICES_FAILED+=1
)

curl -f http://localhost:11434/api/tags >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Ollama LLM - http://localhost:11434
    set /a SERVICES_OK+=1
) else (
    echo [FAIL] Ollama LLM
    set /a SERVICES_FAILED+=1
)

curl -f http://localhost:3001 >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Voice Bridge - http://localhost:3001
    set /a SERVICES_OK+=1
) else (
    echo [INFO] Voice Bridge (optional)
)

echo.
echo ============================================================
echo              JARVIS AI LAUNCH COMPLETE!
echo ============================================================
echo.
echo Services Running: %SERVICES_OK% / 6
echo.
echo Access Points:
echo --------------
echo   Main Interface:    http://localhost:3000
echo   API Documentation: http://localhost:8080/docs
echo   Voice Bridge:      http://localhost:3001
echo   Monitoring:        http://localhost:9090 (Prometheus)
echo                      http://localhost:3000 (Grafana)
echo.
echo Quick Commands:
echo ---------------
echo   View Logs:     docker-compose logs -f [service-name]
echo   Stop All:      docker-compose down
echo   Restart:       docker-compose restart [service-name]
echo   Health Check:  curl http://localhost:8080/health
echo.
echo Memory Usage:  docker stats
echo Clean Cache:   python cleanup-project.py
echo.
echo ============================================================
echo         JARVIS IS READY! Press any key to minimize...
echo ============================================================

REM Open main interface in browser
timeout /t 3 /nobreak >nul
start "" "http://localhost:3000"

REM Keep window open but minimized
pause >nul

REM Create a background monitoring loop
:MONITOR_LOOP
timeout /t 60 /nobreak >nul
docker-compose ps | findstr "Exit" >nul
if %errorLevel% equ 0 (
    echo [WARNING] Some services have stopped. Restarting...
    docker-compose up -d
)
goto MONITOR_LOOP

endlocal