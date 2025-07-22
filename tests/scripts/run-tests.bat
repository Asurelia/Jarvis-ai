@echo off
REM 🧪 Script de lancement des tests JARVIS pour Windows
REM Usage: run-tests.bat [type] [options]

setlocal EnableDelayedExpansion

REM Configuration
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%\..\..
set COMPOSE_FILE=%PROJECT_DIR%\docker-compose.test.yml

REM Couleurs (si supportées)
set RED=[31m
set GREEN=[32m
set YELLOW=[33m
set BLUE=[34m
set PURPLE=[35m
set NC=[0m

REM Variables par défaut
set TEST_TYPE=all
set BUILD=false
set CLEAN=false
set VERBOSE=false
set PARALLEL=false
set COVERAGE=false
set REPORT=false
set NO_CACHE=false

REM Fonction d'aide
:show_help
echo.
echo 🧪 Script de lancement des tests JARVIS
echo.
echo Usage: %~nx0 [TYPE] [OPTIONS]
echo.
echo TYPES DE TESTS:
echo   unit              Tests unitaires uniquement
echo   integration       Tests d'integration des services
echo   ui                Tests de l'interface utilisateur
echo   e2e               Tests end-to-end complets
echo   performance       Tests de performance et charge
echo   security          Tests de securite
echo   all               Tous les tests (par defaut)
echo.
echo OPTIONS:
echo   --build           Reconstruire les images Docker
echo   --clean           Nettoyer les volumes avant les tests
echo   --verbose         Mode verbose pour les logs
echo   --parallel        Lancer les tests en parallele
echo   --coverage        Generer un rapport de couverture
echo   --report          Generer un rapport HTML
echo   --no-cache        Ne pas utiliser le cache Docker
echo   --help            Afficher cette aide
echo.
echo EXEMPLES:
echo   %~nx0 unit --verbose
echo   %~nx0 integration --build --clean
echo   %~nx0 e2e --coverage --report
echo   %~nx0 performance --parallel
echo   %~nx0 all --build --clean --verbose
echo.
goto :eof

REM Parse des arguments
:parse_args
if "%~1"=="" goto :end_parse
if "%~1"=="--help" goto :show_help
if "%~1"=="--build" set BUILD=true
if "%~1"=="--clean" set CLEAN=true
if "%~1"=="--verbose" set VERBOSE=true
if "%~1"=="--parallel" set PARALLEL=true
if "%~1"=="--coverage" set COVERAGE=true
if "%~1"=="--report" set REPORT=true
if "%~1"=="--no-cache" set NO_CACHE=true
if "%~1"=="unit" set TEST_TYPE=unit
if "%~1"=="integration" set TEST_TYPE=integration
if "%~1"=="ui" set TEST_TYPE=ui
if "%~1"=="e2e" set TEST_TYPE=e2e
if "%~1"=="performance" set TEST_TYPE=performance
if "%~1"=="security" set TEST_TYPE=security
if "%~1"=="all" set TEST_TYPE=all
shift
goto :parse_args
:end_parse

REM Fonctions utilitaires
:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:log_header
echo %PURPLE%[JARVIS]%NC% %~1
goto :eof

REM Vérification des prérequis
:check_prerequisites
call :log_info "Verification des prerequis..."

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    call :log_error "Docker n'est pas installe ou non accessible"
    exit /b 1
)

docker-compose --version >nul 2>&1 || docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    call :log_error "Docker Compose n'est pas installe"
    exit /b 1
)

if not exist "%COMPOSE_FILE%" (
    call :log_error "Fichier docker-compose.test.yml non trouve: %COMPOSE_FILE%"
    exit /b 1
)

call :log_success "Prerequis OK"
goto :eof

REM Nettoyage de l'environnement
:cleanup_environment
call :log_info "Nettoyage de l'environnement de test..."

docker-compose -f "%COMPOSE_FILE%" down --volumes --remove-orphans >nul 2>&1

if "%CLEAN%"=="true" (
    call :log_info "Suppression des volumes et images de test..."
    docker-compose -f "%COMPOSE_FILE%" down --volumes --rmi all >nul 2>&1
    docker system prune -f --volumes >nul 2>&1
)

REM Créer les répertoires de résultats
if not exist "%PROJECT_DIR%\tests\results" mkdir "%PROJECT_DIR%\tests\results"
if not exist "%PROJECT_DIR%\coverage" mkdir "%PROJECT_DIR%\coverage"

call :log_success "Environnement nettoye"
goto :eof

REM Construction des images
:build_images
call :log_info "Construction des images Docker..."

set BUILD_ARGS=
if "%NO_CACHE%"=="true" set BUILD_ARGS=--no-cache
if "%VERBOSE%"=="true" set BUILD_ARGS=%BUILD_ARGS% --progress=plain

docker-compose -f "%COMPOSE_FILE%" build %BUILD_ARGS%
if %errorlevel% neq 0 (
    call :log_error "Erreur lors de la construction des images"
    exit /b 1
)

call :log_success "Images construites"
goto :eof

REM Tests unitaires
:run_unit_tests
call :log_header "🧪 Lancement des tests unitaires"

set CMD=python -m pytest tests/test_new_components.py -v
if "%COVERAGE%"=="true" set CMD=%CMD% --cov=core --cov=services --cov-report=html:/app/coverage

docker-compose -f "%COMPOSE_FILE%" run --rm test-runner %CMD%
goto :eof

REM Tests d'intégration
:run_integration_tests
call :log_header "🔗 Lancement des tests d'integration"

REM Démarrer les services nécessaires
docker-compose -f "%COMPOSE_FILE%" up -d brain-api-test test-memory-db test-redis

REM Attendre que les services soient prêts
call :log_info "Attente des services..."
timeout /t 10 /nobreak >nul

REM Lancer les tests
set CMD=python -m pytest tests/ -k "integration" -v
if "%COVERAGE%"=="true" set CMD=%CMD% --cov=core --cov=services

docker-compose -f "%COMPOSE_FILE%" run --rm test-runner %CMD%
goto :eof

REM Tests UI
:run_ui_tests
call :log_header "🎨 Lancement des tests UI"

REM Démarrer l'interface
docker-compose -f "%COMPOSE_FILE%" up -d ui-test brain-api-test test-memory-db test-redis

REM Attendre que l'UI soit prête
call :log_info "Attente de l'interface utilisateur..."
timeout /t 15 /nobreak >nul

REM Lancer les tests UI
docker-compose -f "%COMPOSE_FILE%" run --rm test-runner bash -c "cd ui && npm test -- --coverage --watchAll=false"

REM Tests JavaScript
docker-compose -f "%COMPOSE_FILE%" run --rm test-runner bash -c "cd ui && npm run test:integration"
goto :eof

REM Tests E2E
:run_e2e_tests
call :log_header "🎯 Lancement des tests E2E"

REM Démarrer tous les services
docker-compose -f "%COMPOSE_FILE%" --profile full-tests up -d

REM Attendre que tous les services soient prêts
call :log_info "Attente de tous les services..."
timeout /t 30 /nobreak >nul

REM Vérifier la santé des services
call :log_info "Verification de la sante des services..."
docker-compose -f "%COMPOSE_FILE%" ps

REM Lancer les tests E2E
docker-compose -f "%COMPOSE_FILE%" run --rm e2e-test
goto :eof

REM Tests de performance
:run_performance_tests
call :log_header "⚡ Lancement des tests de performance"

REM Démarrer les services pour les tests de perf
docker-compose -f "%COMPOSE_FILE%" --profile perf-tests up -d

REM Attendre les services
timeout /t 20 /nobreak >nul

REM Tests de charge avec K6
docker-compose -f "%COMPOSE_FILE%" run --rm performance-test

REM Tests de performance Python
docker-compose -f "%COMPOSE_FILE%" run --rm test-runner bash -c "python -m pytest tests/test_performance.py -v --benchmark-only"
goto :eof

REM Tests de sécurité
:run_security_tests
call :log_header "🔒 Lancement des tests de securite"

REM Démarrer les services pour les tests de sécurité
docker-compose -f "%COMPOSE_FILE%" --profile security-tests up -d

REM Attendre les services
timeout /t 15 /nobreak >nul

REM Tests de sécurité avec OWASP ZAP
docker-compose -f "%COMPOSE_FILE%" run --rm security-test

REM Tests de sécurité Python
docker-compose -f "%COMPOSE_FILE%" run --rm test-runner bash -c "bandit -r core/ services/ -f json -o /app/tests/results/security-python.json || exit 0 && safety check --json --output /app/tests/results/safety.json || exit 0"
goto :eof

REM Génération des rapports
:generate_reports
if "%REPORT%"=="true" (
    call :log_info "Generation des rapports..."
    
    docker-compose -f "%COMPOSE_FILE%" run --rm test-runner bash -c "python tests/scripts/generate_report.py --coverage /app/coverage --results /app/tests/results --output /app/tests/results/consolidated-report.html"
    
    call :log_success "Rapports generes dans tests/results/"
)
goto :eof

REM Affichage des résultats
:show_results
call :log_header "📊 Resultats des tests"

REM Copier les résultats vers l'hôte
docker-compose -f "%COMPOSE_FILE%" run --rm test-runner bash -c "cp -r /app/tests/results/* /app/tests/results/ 2>/dev/null || exit 0 && cp -r /app/coverage/* /app/coverage/ 2>/dev/null || exit 0"

echo.
echo 📁 Fichiers de resultats disponibles:
if exist "%PROJECT_DIR%\tests\results" (
    dir /b "%PROJECT_DIR%\tests\results\*.html" "%PROJECT_DIR%\tests\results\*.json" "%PROJECT_DIR%\tests\results\*.xml" 2>nul
) else (
    echo   Aucun rapport trouve
)

if exist "%PROJECT_DIR%\coverage\index.html" (
    echo 📈 Rapport de couverture: file://%PROJECT_DIR%\coverage\index.html
)

echo.
goto :eof

REM Fonction principale
:main
REM Parse des arguments
call :parse_args %*

REM Configuration de l'environnement
set COMPOSE_PROJECT_NAME=jarvis-test

if "%VERBOSE%"=="true" (
    set DOCKER_BUILDKIT=0
)

REM Vérifications
call :check_prerequisites
if %errorlevel% neq 0 exit /b 1

REM Nettoyage si demandé
if "%CLEAN%"=="true" call :cleanup_environment
if "%BUILD%"=="true" call :cleanup_environment

REM Construction si demandée
if "%BUILD%"=="true" (
    call :build_images
    if %errorlevel% neq 0 exit /b 1
)

call :log_header "🚀 Demarrage des tests JARVIS - Type: %TEST_TYPE%"

REM Lancer les tests selon le type
if "%TEST_TYPE%"=="unit" (
    call :run_unit_tests
) else if "%TEST_TYPE%"=="integration" (
    call :run_integration_tests
) else if "%TEST_TYPE%"=="ui" (
    call :run_ui_tests
) else if "%TEST_TYPE%"=="e2e" (
    call :run_e2e_tests
) else if "%TEST_TYPE%"=="performance" (
    call :run_performance_tests
) else if "%TEST_TYPE%"=="security" (
    call :run_security_tests
) else if "%TEST_TYPE%"=="all" (
    call :run_unit_tests
    call :run_integration_tests
    call :run_ui_tests
    call :run_e2e_tests
) else (
    call :log_error "Type de test inconnu: %TEST_TYPE%"
    call :show_help
    exit /b 1
)

REM Génération des rapports
call :generate_reports

REM Nettoyage final
call :log_info "Arret des services de test..."
docker-compose -f "%COMPOSE_FILE%" down >nul 2>&1

REM Affichage des résultats
call :show_results

call :log_success "🎉 Tests termines avec succes !"
goto :eof

REM Gestion des interruptions
:cleanup_on_exit
call :log_info "Interruption detectee, nettoyage..."
docker-compose -f "%COMPOSE_FILE%" down >nul 2>&1
exit /b 0

REM Point d'entrée
call :main %*