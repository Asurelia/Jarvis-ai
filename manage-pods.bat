@echo off
REM 🤖 JARVIS 2025 - Gestionnaire de Pods Windows
REM Gestion des services par pods indépendants

setlocal enabledelayedexpansion

REM Couleurs (limitées sur Windows)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "PURPLE=[95m"
set "NC=[0m"

REM Configuration pods
set "POD_COUNT=4"
set "POD_1=ai:docker-compose.ai-pod.yml:🧠:AI Pod (Brain+Ollama+Memory)"
set "POD_2=audio:docker-compose.audio-pod.yml:🗣️:Audio Pod (TTS+STT Processing)"
set "POD_3=control:docker-compose.control-pod.yml:🖥️:Control Pod (System+Terminal)"
set "POD_4=integration:docker-compose.integration-pod.yml:🔧:Integration Pod (MCP+UI+Autocomplete)"

REM Banner JARVIS
echo %BLUE%
echo     ╔═══════════════════════════════════════╗
echo     ║           🤖 JARVIS 2025              ║
echo     ║        Gestionnaire de Pods           ║
echo     ║      Architecture Microservices       ║
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

echo %GREEN%✅ Prérequis validés%NC%

REM Traitement des arguments
set "COMMAND=%~1"
set "POD_NAME=%~2"

if "%COMMAND%"=="" set "COMMAND=help"
if "%COMMAND%"=="help" goto :help
if "%COMMAND%"=="--help" goto :help
if "%COMMAND%"=="-h" goto :help

if "%COMMAND%"=="start" goto :start
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="restart" goto :restart
if "%COMMAND%"=="status" goto :status
if "%COMMAND%"=="logs" goto :logs
if "%COMMAND%"=="build" goto :build
if "%COMMAND%"=="clean" goto :clean
if "%COMMAND%"=="health" goto :health

echo %RED%❌ Commande inconnue: %COMMAND%%NC%
goto :help

:help
echo %YELLOW%Usage: manage-pods.bat [COMMAND] [POD]%NC%
echo.
echo Commands:
echo   start [pod]     Démarrer un pod ou tous les pods
echo   stop [pod]      Arrêter un pod ou tous les pods
echo   restart [pod]   Redémarrer un pod ou tous les pods
echo   status          Afficher l'état de tous les pods
echo   logs [pod]      Afficher les logs d'un pod
echo   build [pod]     Rebuild un pod ou tous les pods
echo   clean           Nettoyer les ressources inutilisées
echo   health          Vérifier la santé de tous les services
echo.
echo Pods disponibles:
echo   🧠 ai           AI Pod (Brain+Ollama+Memory)
echo   🗣️ audio        Audio Pod (TTS+STT Processing)
echo   🖥️ control      Control Pod (System+Terminal)
echo   🔧 integration  Integration Pod (MCP+UI+Autocomplete)
echo.
echo Exemples:
echo   manage-pods.bat start ai           # Démarrer seulement le pod IA
echo   manage-pods.bat start              # Démarrer tous les pods
echo   manage-pods.bat logs audio         # Voir les logs du pod audio
echo   manage-pods.bat health             # Vérifier la santé
pause
exit /b 0

:start
if "%POD_NAME%"=="" (
    echo %GREEN%🚀 Démarrage de tous les pods...%NC%
    call :start_pod ai
    call :start_pod audio
    call :start_pod control
    call :start_pod integration
    echo %GREEN%🎉 Tous les pods sont démarrés !%NC%
    echo.
    echo %YELLOW%💡 N'oubliez pas de démarrer le Voice Bridge:%NC%
    echo %BLUE%  cd local-interface ^&^& python voice-bridge.py%NC%
) else (
    call :start_pod %POD_NAME%
)
goto :end

:stop
if "%POD_NAME%"=="" (
    echo %YELLOW%⏹️ Arrêt de tous les pods...%NC%
    call :stop_pod ai
    call :stop_pod audio
    call :stop_pod control
    call :stop_pod integration
    echo %GREEN%✅ Tous les pods sont arrêtés%NC%
) else (
    call :stop_pod %POD_NAME%
)
goto :end

:restart
if "%POD_NAME%"=="" (
    echo %BLUE%🔄 Redémarrage de tous les pods...%NC%
    call :restart_pod ai
    call :restart_pod audio
    call :restart_pod control
    call :restart_pod integration
) else (
    call :restart_pod %POD_NAME%
)
goto :end

:status
echo %BLUE%📊 État des pods JARVIS:%NC%
echo.
call :show_pod_status ai "🧠" "AI Pod (Brain+Ollama+Memory)"
call :show_pod_status audio "🗣️" "Audio Pod (TTS+STT Processing)"
call :show_pod_status control "🖥️" "Control Pod (System+Terminal)"
call :show_pod_status integration "🔧" "Integration Pod (MCP+UI+Autocomplete)"
goto :end

:logs
if "%POD_NAME%"=="" (
    echo %RED%❌ Spécifiez un pod pour voir les logs%NC%
    goto :help
)
call :show_logs %POD_NAME%
goto :end

:build
if "%POD_NAME%"=="" (
    echo %YELLOW%🔨 Rebuild de tous les pods...%NC%
    call :build_pod ai
    call :build_pod audio
    call :build_pod control
    call :build_pod integration
) else (
    call :build_pod %POD_NAME%
)
goto :end

:clean
echo %YELLOW%🧹 Nettoyage des ressources Docker...%NC%
docker-compose -f docker-compose.ai-pod.yml down 2>nul
docker-compose -f docker-compose.audio-pod.yml down 2>nul
docker-compose -f docker-compose.control-pod.yml down 2>nul
docker-compose -f docker-compose.integration-pod.yml down 2>nul
docker system prune -f
docker volume prune -f
docker network prune -f
echo %GREEN%✅ Nettoyage terminé%NC%
goto :end

:health
echo %BLUE%🏥 Vérification de la santé des services:%NC%
echo.
call :check_service "🧠 Brain API" "http://localhost:8080/health"
call :check_service "🗣️ TTS Service" "http://localhost:5002/health"
call :check_service "🎤 STT Service" "http://localhost:5003/health"
call :check_service "🖥️ System Control" "http://localhost:5004/health"
call :check_service "💻 Terminal Service" "http://localhost:5005/health"
call :check_service "🔧 MCP Gateway" "http://localhost:5006/health"
call :check_service "🧠 Autocomplete" "http://localhost:5007/health"
call :check_service "🤖 Ollama" "http://localhost:11434/api/tags"
call :check_service "🎤 Voice Bridge" "http://localhost:3001/health"
call :check_service "🌐 Frontend" "http://localhost:3000"
echo.
echo %BLUE%💡 Pour démarrer le Voice Bridge local:%NC%
echo %YELLOW%  cd local-interface ^&^& python voice-bridge.py%NC%
goto :end

REM Fonctions utilitaires
:start_pod
set "pod=%~1"
call :get_compose_file %pod%
if "%compose_file%"=="" (
    echo %RED%❌ Pod '%pod%' non trouvé%NC%
    exit /b 1
)
echo %GREEN%🚀 Démarrage du pod %pod%...%NC%
docker-compose -f %compose_file% up -d
if errorlevel 1 (
    echo %RED%❌ Échec du démarrage du pod %pod%%NC%
) else (
    echo %GREEN%✅ Pod %pod% démarré avec succès%NC%
)
exit /b 0

:stop_pod
set "pod=%~1"
call :get_compose_file %pod%
if "%compose_file%"=="" (
    echo %RED%❌ Pod '%pod%' non trouvé%NC%
    exit /b 1
)
echo %YELLOW%⏹️ Arrêt du pod %pod%...%NC%
docker-compose -f %compose_file% down
if errorlevel 1 (
    echo %RED%❌ Échec de l'arrêt du pod %pod%%NC%
) else (
    echo %GREEN%✅ Pod %pod% arrêté avec succès%NC%
)
exit /b 0

:restart_pod
set "pod=%~1"
echo %BLUE%🔄 Redémarrage du pod %pod%...%NC%
call :stop_pod %pod%
timeout /t 2 /nobreak >nul
call :start_pod %pod%
exit /b 0

:build_pod
set "pod=%~1"
call :get_compose_file %pod%
if "%compose_file%"=="" (
    echo %RED%❌ Pod '%pod%' non trouvé%NC%
    exit /b 1
)
echo %YELLOW%🔨 Rebuild du pod %pod%...%NC%
docker-compose -f %compose_file% down
docker-compose -f %compose_file% build --no-cache
docker-compose -f %compose_file% up -d
echo %GREEN%✅ Rebuild du pod %pod% terminé%NC%
exit /b 0

:show_pod_status
set "pod=%~1"
set "icon=%~2"
set "desc=%~3"
call :get_compose_file %pod%
echo %PURPLE%%icon% %pod% - %desc%%NC%
if exist %compose_file% (
    docker-compose -f %compose_file% ps 2>nul
    if errorlevel 1 (
        echo %YELLOW%  ⏸️ Aucun conteneur actif%NC%
    )
) else (
    echo %RED%  ❌ Fichier de configuration manquant%NC%
)
echo.
exit /b 0

:show_logs
set "pod=%~1"
call :get_compose_file %pod%
if "%compose_file%"=="" (
    echo %RED%❌ Pod '%pod%' non trouvé%NC%
    exit /b 1
)
echo %BLUE%📋 Logs du pod %pod%:%NC%
docker-compose -f %compose_file% logs -f
exit /b 0

:check_service
set "service_name=%~1"
set "url=%~2"
curl -s -f "%url%" >nul 2>&1
if errorlevel 1 (
    echo %RED%❌ %service_name%%NC%
) else (
    echo %GREEN%✅ %service_name%%NC%
)
exit /b 0

:get_compose_file
set "pod_name=%~1"
set "compose_file="
if "%pod_name%"=="ai" set "compose_file=docker-compose.ai-pod.yml"
if "%pod_name%"=="audio" set "compose_file=docker-compose.audio-pod.yml"
if "%pod_name%"=="control" set "compose_file=docker-compose.control-pod.yml"
if "%pod_name%"=="integration" set "compose_file=docker-compose.integration-pod.yml"
exit /b 0

:end
pause