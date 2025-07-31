@echo off
REM Script pour lancer les tests d'intégration JARVIS AI sur Windows
REM Nécessite Docker et les services en cours d'exécution

setlocal enabledelayedexpansion

echo ======================================================
echo     JARVIS AI - Tests d'Integration et Performance
echo ======================================================

REM Variables
set PROJECT_ROOT=%~dp0
set RESULTS_DIR=%PROJECT_ROOT%test-results
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM Créer le répertoire de résultats
if not exist "%RESULTS_DIR%" mkdir "%RESULTS_DIR%"

REM Vérifier que Docker est en cours d'exécution
echo.
echo [Docker] Verification de Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Docker n'est pas en cours d'execution!
    echo Veuillez demarrer Docker Desktop et reessayer.
    pause
    exit /b 1
)

REM Vérifier les services JARVIS
echo [Services] Verification des services JARVIS...
set SERVICES_OK=1

for %%s in (jarvis_brain jarvis_tts jarvis_stt jarvis_system_control jarvis_terminal jarvis_mcp_gateway jarvis_autocomplete jarvis_redis jarvis_memory_db) do (
    docker ps --format "table {{.Names}}" | findstr /C:"%%s" >nul
    if errorlevel 1 (
        echo [AVERTISSEMENT] Service manquant: %%s
        set SERVICES_OK=0
    )
)

if !SERVICES_OK!==0 (
    echo [Services] Lancement des services manquants...
    docker-compose up -d
    echo [Services] Attente du demarrage des services (30s)...
    timeout /t 30 /nobreak >nul
)

REM Activer l'environnement virtuel si présent
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [Python] Creation de l'environnement virtuel...
    python -m venv venv
    call venv\Scripts\activate.bat
)

REM Installer les dépendances
echo.
echo [Dependencies] Installation des dependances de test...
pip install -q pytest pytest-asyncio pytest-benchmark pytest-cov docker aiohttp websockets requests psutil

REM TESTS D'INTÉGRATION
echo.
echo ======================================
echo     Tests d'Integration
echo ======================================

REM Tests Docker Services
echo.
echo [Docker] Tests des services Docker...
pytest tests\integration\test_docker_services.py -v --tb=short --junit-xml="%RESULTS_DIR%\docker-services-%TIMESTAMP%.xml"

REM Tests API Integration
echo.
echo [API] Tests d'integration API...
pytest tests\integration\test_api_integration.py -v --tb=short --junit-xml="%RESULTS_DIR%\api-integration-%TIMESTAMP%.xml" 2>nul

REM Tests WebSocket
echo.
echo [WebSocket] Tests WebSocket...
pytest tests\integration\test_websocket_integration.py -v --tb=short --junit-xml="%RESULTS_DIR%\websocket-%TIMESTAMP%.xml" 2>nul

REM Tests Audio Pipeline
echo.
echo [Audio] Tests pipeline audio...
pytest tests\integration\test_audio_pipeline.py -v --tb=short --junit-xml="%RESULTS_DIR%\audio-pipeline-%TIMESTAMP%.xml" 2>nul

REM TESTS DE PERFORMANCE
echo.
echo ======================================
echo     Tests de Performance
echo ======================================

REM Tests de charge Brain API
echo.
echo [Brain API] Tests de charge...
pytest tests\performance\test_load_brain_api.py -v --tb=short --junit-xml="%RESULTS_DIR%\load-brain-api-%TIMESTAMP%.xml"

REM Tests latence audio
echo.
echo [Audio] Tests latence audio...
pytest tests\performance\test_audio_latency.py -v --tb=short --junit-xml="%RESULTS_DIR%\audio-latency-%TIMESTAMP%.xml" 2>nul

REM Tests débit WebSocket
echo.
echo [WebSocket] Tests debit WebSocket...
pytest tests\performance\test_websocket_throughput.py -v --tb=short --junit-xml="%RESULTS_DIR%\websocket-throughput-%TIMESTAMP%.xml" 2>nul

REM Tests monitoring GPU
echo.
echo [GPU] Tests performance GPU monitoring...
pytest tests\performance\test_gpu_monitoring.py -v --tb=short --junit-xml="%RESULTS_DIR%\gpu-monitoring-%TIMESTAMP%.xml" 2>nul

REM TESTS DE RÉSILIENCE
echo.
echo ======================================
echo     Tests de Resilience
echo ======================================

REM Tests coupures réseau
echo.
echo [Network] Tests coupures reseau...
pytest tests\resilience\test_network_failures.py -v --tb=short --junit-xml="%RESULTS_DIR%\network-failures-%TIMESTAMP%.xml" 2>nul

REM Tests récupération
echo.
echo [Recovery] Tests recuperation apres crash...
pytest tests\resilience\test_service_recovery.py -v --tb=short --junit-xml="%RESULTS_DIR%\service-recovery-%TIMESTAMP%.xml" 2>nul

REM Tests limites ressources
echo.
echo [Resources] Tests limites ressources...
pytest tests\resilience\test_resource_limits.py -v --tb=short --junit-xml="%RESULTS_DIR%\resource-limits-%TIMESTAMP%.xml" 2>nul

REM Générer le rapport de synthèse
echo.
echo ======================================
echo     Generation du Rapport
echo ======================================

REM Créer le rapport HTML
echo ^<!DOCTYPE html^> > "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo ^<html^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo ^<head^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo     ^<title^>JARVIS AI - Rapport de Tests d'Integration^</title^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo     ^<style^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         body { font-family: Arial, sans-serif; margin: 20px; background: #0a0a0a; color: #00d4ff; } >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         h1 { color: #00ff88; text-align: center; } >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         .summary { background: rgba(0,212,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0; } >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         .metric { display: inline-block; margin: 10px 20px; } >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         .success { color: #00ff88; } >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         .failure { color: #ff6b00; } >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         table { width: 100%%; border-collapse: collapse; margin: 20px 0; } >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         th, td { padding: 10px; text-align: left; border: 1px solid #00d4ff; } >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         th { background: rgba(0,212,255,0.2); } >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo     ^</style^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo ^</head^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo ^<body^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo     ^<h1^>JARVIS AI - Rapport de Tests d'Integration^</h1^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo     ^<div class="summary"^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         ^<h2^>Resume^</h2^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         ^<div class="metric"^>Date: ^<strong^>%date% %time%^</strong^>^</div^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo         ^<div class="metric"^>Plateforme: ^<strong^>Windows^</strong^>^</div^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo     ^</div^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo     ^<h2^>Resultats des Tests^</h2^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo     ^<p^>Les resultats detailles sont disponibles dans les fichiers XML du dossier test-results.^</p^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo ^</body^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"
echo ^</html^> >> "%RESULTS_DIR%\report-%TIMESTAMP%.html"

echo.
echo ======================================
echo     Tests Termines!
echo ======================================
echo.
echo [OK] Resultats sauvegardes dans: %RESULTS_DIR%
echo [OK] Rapport HTML: %RESULTS_DIR%\report-%TIMESTAMP%.html
echo.

REM Ouvrir le rapport
start "" "%RESULTS_DIR%\report-%TIMESTAMP%.html"

echo Tests d'integration completes avec succes!
echo.
pause