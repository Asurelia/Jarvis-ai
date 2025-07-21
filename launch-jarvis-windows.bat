@echo off
setlocal enabledelayedexpansion
title JARVIS AI - Lancement Windows
chcp 65001 >nul

:: Configuration
set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%venv"
set "LOG_FILE=%PROJECT_DIR%logs\jarvis-startup.log"

:: Créer le répertoire de logs
if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"

:: Fonction de logging
echo [%date% %time%] === DÉMARRAGE JARVIS AI === >> "%LOG_FILE%"

echo.
echo ╔══════════════════════════════════════════╗
echo ║            JARVIS AI STARTUP             ║
echo ║           Windows Native Mode            ║
echo ╚══════════════════════════════════════════╝
echo.

cd /d "%PROJECT_DIR%"

:: [1/8] Vérification de l'environnement
echo [1/8] Vérification de l'environnement...
echo [%date% %time%] Vérification environnement >> "%LOG_FILE%"

:: Vérifier l'environnement virtuel Python
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo ✗ Environnement virtuel Python non trouvé
    echo Création de l'environnement virtuel...
    python -m venv venv
    if !errorLevel! neq 0 (
        echo ✗ Échec création environnement virtuel
        echo [%date% %time%] ERREUR: Échec création venv >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

:: Activer l'environnement virtuel
echo Activation de l'environnement Python...
call "%VENV_DIR%\Scripts\activate.bat"
if !errorLevel! neq 0 (
    echo ✗ Échec activation environnement virtuel
    echo [%date% %time%] ERREUR: Échec activation venv >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo ✓ Environnement Python activé

:: [2/8] Vérification des dépendances critiques
echo [2/8] Vérification des dépendances critiques...
echo [%date% %time%] Vérification dépendances >> "%LOG_FILE%"

:: Vérifier les imports Python critiques
python -c "import fastapi, uvicorn, websockets" >nul 2>&1
if !errorLevel! neq 0 (
    echo ⚠ Dépendances Python manquantes - Installation...
    pip install -r requirements.txt
    if !errorLevel! neq 0 (
        echo ✗ Échec installation dépendances Python
        echo [%date% %time%] ERREUR: Échec pip install >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

echo ✓ Dépendances Python validées

:: [3/8] Vérification et démarrage de Docker
echo [3/8] Vérification de Docker...
echo [%date% %time%] Vérification Docker >> "%LOG_FILE%"

docker info >nul 2>&1
if !errorLevel! neq 0 (
    echo ⚠ Docker non accessible - Tentative de démarrage...
    
    :: Chercher Docker Desktop
    set "DOCKER_EXE="
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        set "DOCKER_EXE=C:\Program Files\Docker\Docker\Docker Desktop.exe"
    )
    if exist "%USERPROFILE%\AppData\Local\Programs\Docker\Docker\Docker Desktop.exe" (
        set "DOCKER_EXE=%USERPROFILE%\AppData\Local\Programs\Docker\Docker\Docker Desktop.exe"
    )
    
    if defined DOCKER_EXE (
        echo Démarrage de Docker Desktop...
        start "" "!DOCKER_EXE!"
        
        :: Attendre que Docker soit prêt
        echo Attente du démarrage de Docker (maximum 60 secondes)...
        set /a "attempts=0"
        :wait_docker
        timeout /t 5 /nobreak >nul
        docker info >nul 2>&1
        if !errorLevel! == 0 (
            echo ✓ Docker opérationnel
            goto :docker_ready
        )
        
        set /a "attempts+=1"
        if !attempts! lss 12 (
            echo   Tentative !attempts!/12...
            goto :wait_docker
        )
        
        echo ✗ Timeout - Docker ne démarre pas
        echo [%date% %time%] ERREUR: Docker timeout >> "%LOG_FILE%"
        echo.
        echo Solutions possibles:
        echo 1. Démarrez Docker Desktop manuellement
        echo 2. Redémarrez votre PC
        echo 3. Réinstallez Docker Desktop
        pause
        exit /b 1
    ) else (
        echo ✗ Docker Desktop non trouvé
        echo [%date% %time%] ERREUR: Docker non trouvé >> "%LOG_FILE%"
        echo Installez Docker Desktop depuis: https://docker.com
        pause
        exit /b 1
    )
) else (
    echo ✓ Docker opérationnel
)

:docker_ready

:: [4/8] Vérification de la configuration Docker Compose
echo [4/8] Validation de la configuration Docker Compose...
echo [%date% %time%] Validation docker-compose >> "%LOG_FILE%"

docker-compose config >nul 2>&1
if !errorLevel! neq 0 (
    echo ✗ Configuration Docker Compose invalide
    echo [%date% %time%] ERREUR: docker-compose config invalide >> "%LOG_FILE%"
    docker-compose config
    pause
    exit /b 1
)

echo ✓ Configuration Docker Compose validée

:: [5/8] Arrêt propre des services existants
echo [5/8] Arrêt des services existants...
echo [%date% %time%] Arrêt services existants >> "%LOG_FILE%"

docker-compose down --remove-orphans >nul 2>&1
echo ✓ Services précédents arrêtés

:: [6/8] Démarrage des services Docker
echo [6/8] Démarrage des services Docker...
echo [%date% %time%] Démarrage services Docker >> "%LOG_FILE%"

echo   Lancement des conteneurs...
docker-compose up -d --build
if !errorLevel! neq 0 (
    echo ✗ Échec du démarrage des services Docker
    echo [%date% %time%] ERREUR: docker-compose up failed >> "%LOG_FILE%"
    echo.
    echo Affichage des logs pour diagnostic:
    docker-compose logs --tail=50
    pause
    exit /b 1
)

echo ✓ Services Docker démarrés

:: Attendre que les services soient prêts
echo [6/8] Attente de l'initialisation des services...
echo [%date% %time%] Attente initialisation >> "%LOG_FILE%"

set /a "wait_time=0"
:wait_services
timeout /t 2 /nobreak >nul
set /a "wait_time+=2"

:: Vérifier l'API Brain (service principal)
curl -s http://localhost:5000/health >nul 2>&1
if !errorLevel! == 0 (
    echo ✓ Services initialisés (!wait_time!s)
    goto :services_ready
)

if !wait_time! lss 30 (
    echo   Attente... (!wait_time!/30s)
    goto :wait_services
)

echo ⚠ Services lents à démarrer - Continuation
echo [%date% %time%] WARNING: Services lents >> "%LOG_FILE%"

:services_ready

:: [7/8] Démarrage du pont vocal local
echo [7/8] Démarrage du pont vocal...
echo [%date% %time%] Démarrage pont vocal >> "%LOG_FILE%"

if exist "local-interface\voice-bridge.py" (
    echo   Lancement du pont vocal local...
    start "JARVIS Voice Bridge" /min python local-interface\voice-bridge.py
    timeout /t 2 /nobreak >nul
    echo ✓ Pont vocal démarré
) else (
    echo ⚠ Pont vocal non trouvé (local-interface\voice-bridge.py)
    echo [%date% %time%] WARNING: Pont vocal manquant >> "%LOG_FILE%"
)

:: [8/8] Démarrage de l'interface principale
echo [8/8] Démarrage de l'interface principale JARVIS...
echo [%date% %time%] Démarrage interface principale >> "%LOG_FILE%"

if exist "start_jarvis.py" (
    echo   Lancement de l'interface JARVIS...
    start "JARVIS Main Interface" python start_jarvis.py --mode full
    timeout /t 3 /nobreak >nul
    echo ✓ Interface principale démarrée
) else (
    echo ✗ Script principal non trouvé (start_jarvis.py)
    echo [%date% %time%] ERREUR: start_jarvis.py manquant >> "%LOG_FILE%"
    pause
    exit /b 1
)

:: Vérification finale des services
echo.
echo ══════════════════════════════════════════════════════════════════
echo                    ✓ JARVIS AI DÉMARRÉ AVEC SUCCÈS!
echo ══════════════════════════════════════════════════════════════════
echo.

:: Afficher les URLs des services
echo Services disponibles:
echo   🌐 Interface web:     http://localhost:3000
echo   🔗 API principale:    http://localhost:5000
echo   📚 Documentation:     http://localhost:5000/docs
echo   🧠 Brain API:         http://localhost:5000/health
echo   🎤 Voice Bridge:      Port local (selon config)
echo.

:: Vérification rapide des services critiques
echo Vérification des services:
timeout /t 2 /nobreak >nul

curl -s http://localhost:5000/health >nul 2>&1
if !errorLevel! == 0 (
    echo   ✓ Brain API: Opérationnel
) else (
    echo   ⚠ Brain API: Non accessible
)

curl -s http://localhost:3000 >nul 2>&1
if !errorLevel! == 0 (
    echo   ✓ Interface Web: Accessible
) else (
    echo   ⚠ Interface Web: En cours de démarrage
)

echo.
echo [%date% %time%] === JARVIS DÉMARRÉ AVEC SUCCÈS === >> "%LOG_FILE%"

:: Proposer d'ouvrir l'interface web
echo Voulez-vous ouvrir l'interface web automatiquement? (O/N)
set /p open_web="> "
if /i "!open_web!"=="O" (
    echo Ouverture de l'interface web...
    start http://localhost:3000
)

echo.
echo ══════════════════════════════════════════════════════════════════
echo Pour arrêter JARVIS, utilisez: stop-jarvis.bat
echo Logs disponibles dans: logs\jarvis-startup.log
echo ══════════════════════════════════════════════════════════════════
echo.

echo Appuyez sur une touche pour fermer cette fenêtre...
pause >nul

:: Garder la fenêtre ouverte en arrière-plan pour monitoring
echo JARVIS AI en cours d'exécution...
echo Fermez cette fenêtre pour arrêter le monitoring.
echo.
:monitor_loop
timeout /t 30 /nobreak >nul
docker-compose ps --format "table {{.Name}}\t{{.Status}}" 2>nul
goto :monitor_loop