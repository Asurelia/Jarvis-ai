@echo off
REM 🤖 JARVIS 2025 - Script de démarrage Windows
REM Usage: start-jarvis.bat [dev|prod|build|stop|logs|status]

setlocal enabledelayedexpansion

REM Couleurs (limitées sur Windows)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Banner JARVIS
echo %BLUE%
echo     ╔═══════════════════════════════════════╗
echo     ║           🤖 JARVIS 2025              ║
echo     ║      Assistant IA Personnel          ║
echo     ║     Architecture Microservices       ║
echo     ╚═══════════════════════════════════════╝
echo %NC%

REM Vérifier les prérequis
echo %BLUE%🔍 Vérification des prérequis...%NC%

docker --version >nul 2>&1
if errorlevel 1 (
    echo %RED%❌ Docker n'est pas installé ou non accessible%NC%
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo %RED%❌ Docker Compose n'est pas installé%NC%
        pause
        exit /b 1
    )
)

if not exist "docker-compose.yml" (
    echo %RED%❌ docker-compose.yml introuvable%NC%
    pause
    exit /b 1
)

echo %GREEN%✅ Prérequis validés%NC%

REM Traitement des arguments
set "MODE=%~1"
if "%MODE%"=="" set "MODE=prod"

if "%MODE%"=="help" goto :help
if "%MODE%"=="--help" goto :help
if "%MODE%"=="-h" goto :help

if "%MODE%"=="dev" goto :start_dev
if "%MODE%"=="prod" goto :start_prod
if "%MODE%"=="build" goto :build
if "%MODE%"=="stop" goto :stop
if "%MODE%"=="logs" goto :logs
if "%MODE%"=="status" goto :status

echo %RED%❌ Option inconnue: %MODE%%NC%
goto :help

:help
echo %YELLOW%Usage: start-jarvis.bat [OPTIONS]%NC%
echo.
echo Options:
echo   dev       Démarrage en mode développement
echo   prod      Démarrage en mode production (défaut)
echo   build     Rebuild tous les containers
echo   stop      Arrêter tous les services
echo   logs      Afficher les logs en temps réel
echo   status    Vérifier l'état des services
echo   help      Afficher cette aide
pause
exit /b 0

:start_dev
echo %BLUE%🚀 Démarrage de JARVIS en mode développement...%NC%
docker-compose up -d
goto :success

:start_prod
echo %BLUE%🚀 Démarrage de JARVIS en mode production...%NC%
docker-compose up -d --remove-orphans
goto :success

:build
echo %YELLOW%🔨 Rebuild des containers...%NC%
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo %GREEN%✅ Rebuild terminé%NC%
goto :end

:stop
echo %YELLOW%⏹️ Arrêt de JARVIS...%NC%
docker-compose down
echo %GREEN%✅ JARVIS arrêté%NC%
goto :end

:logs
echo %BLUE%📋 Logs de JARVIS (Ctrl+C pour quitter):%NC%
docker-compose logs -f
goto :end

:status
echo %BLUE%📊 État des services:%NC%
docker ps --filter "name=jarvis" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
goto :end

:success
echo %GREEN%✅ Services démarrés%NC%
echo.
echo %GREEN%🎉 JARVIS 2025 est maintenant actif !%NC%
echo.
echo %YELLOW%📋 Accès aux services:%NC%
echo   🌐 Frontend:    http://localhost:3000
echo   🧠 Brain API:   http://localhost:8080
echo   🗣️ TTS Service: http://localhost:5002
echo   🎤 STT Service: http://localhost:5003
echo   🤖 Ollama:      http://localhost:11434
echo   📊 API Docs:    http://localhost:8080/docs
echo.
echo %BLUE%💡 Commandes utiles:%NC%
echo   start-jarvis.bat logs     # Voir les logs
echo   start-jarvis.bat status   # État des services
echo   start-jarvis.bat stop     # Arrêter JARVIS
echo.
echo %YELLOW%⏳ Téléchargement des modèles IA en cours...%NC%
echo (Cela peut prendre quelques minutes lors du premier démarrage)

:end
echo.
pause