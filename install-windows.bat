@echo off
setlocal enabledelayedexpansion
title JARVIS AI - Installation Windows avec Support WSL
chcp 65001 >nul

:: Configuration des couleurs
set "ESC="
set "RESET=%ESC%[0m"
set "RED=%ESC%[31m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "BLUE=%ESC%[34m"
set "PURPLE=%ESC%[35m"
set "CYAN=%ESC%[36m"
set "WHITE=%ESC%[37m"

echo.
echo ╔══════════════════════════════════════════╗
echo ║          JARVIS AI INSTALLER             ║
echo ║      Installation Windows + WSL          ║
echo ╚══════════════════════════════════════════╝
echo.

:: Vérification des privilèges administrateur
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] ✓ Privilèges administrateur détectés
) else (
    echo [WARN] ⚠ Exécution sans privilèges administrateur
    echo        Certaines fonctionnalités peuvent être limitées
    echo.
    timeout /t 3 /nobreak >nul
)

:: Détection de WSL
echo [1/12] Détection de l'environnement...
wsl --status >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ WSL détecté et fonctionnel
    set "WSL_AVAILABLE=1"
    
    :: Obtenir la distribution par défaut
    for /f "tokens=*" %%i in ('wsl -l -q 2^>nul ^| findstr /v "^$"') do (
        set "WSL_DISTRO=%%i"
        goto :wsl_found
    )
    :wsl_found
    echo   Distribution par défaut: !WSL_DISTRO!
    
    :: Proposer l'installation dans WSL
    echo.
    echo Voulez-vous installer JARVIS dans WSL pour de meilleures performances Docker? (O/N)
    set /p use_wsl="> "
    if /i "!use_wsl!"=="O" (
        set "USE_WSL=1"
        echo ✓ Installation WSL sélectionnée
    ) else (
        set "USE_WSL=0"
        echo ✓ Installation Windows native sélectionnée
    )
) else (
    echo ⚠ WSL non disponible - Installation Windows native
    set "WSL_AVAILABLE=0"
    set "USE_WSL=0"
)

:: Installation WSL si demandée
if "!USE_WSL!"=="1" (
    echo.
    echo [2/12] Configuration de WSL pour JARVIS...
    
    :: Créer le répertoire de travail dans WSL
    wsl mkdir -p /home/jarvis-ai
    wsl cp -r . /home/jarvis-ai/ 2>nul
    
    :: Lancer l'installation dans WSL
    echo Lancement de l'installation dans WSL...
    wsl bash -c "cd /home/jarvis-ai && chmod +x install-jarvis.sh && ./install-jarvis.sh"
    
    if !errorLevel! == 0 (
        echo ✓ Installation WSL terminée avec succès
        
        :: Créer un script de lancement WSL
        echo @echo off > launch-jarvis-wsl.bat
        echo title JARVIS AI - WSL >> launch-jarvis-wsl.bat
        echo echo Démarrage de JARVIS dans WSL... >> launch-jarvis-wsl.bat
        echo wsl bash -c "cd /home/jarvis-ai && ./launch-jarvis.sh" >> launch-jarvis-wsl.bat
        echo pause >> launch-jarvis-wsl.bat
        
        echo.
        echo ════════════════════════════════════════════════════════════════
        echo ✓ INSTALLATION WSL TERMINÉE!
        echo.
        echo Pour démarrer JARVIS:
        echo   📄 Double-cliquez sur: launch-jarvis-wsl.bat
        echo.
        echo Ou depuis PowerShell/CMD:
        echo   wsl bash -c "cd /home/jarvis-ai && ./launch-jarvis.sh"
        echo ════════════════════════════════════════════════════════════════
        goto :end
    ) else (
        echo ✗ Erreur installation WSL - Basculement vers Windows natif
        set "USE_WSL=0"
    )
)

:: Installation Windows native
echo.
echo [2/12] Vérification de Python...
python --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
    echo ✓ Python !PYTHON_VERSION! installé
) else (
    echo ✗ Python non trouvé
    echo.
    echo Installation automatique de Python...
    
    :: Télécharger et installer Python
    echo Téléchargement de Python 3.11...
    powershell -Command "& {
        $url = 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe'
        $output = '$env:TEMP\python-installer.exe'
        try {
            Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
            Start-Process -FilePath $output -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait
            Remove-Item $output -Force
        } catch {
            Write-Host 'Erreur téléchargement Python'
            exit 1
        }
    }"
    
    if !errorLevel! neq 0 (
        echo ✗ Échec de l'installation Python automatique
        echo Veuillez installer Python manuellement depuis python.org
        pause
        exit /b 1
    )
    
    :: Recharger PATH
    call refreshenv >nul 2>&1
    python --version >nul 2>&1
    if !errorLevel! == 0 (
        echo ✓ Python installé avec succès
    ) else (
        echo ✗ Python non accessible après installation
        echo Redémarrez l'invite de commande et relancez l'installation
        pause
        exit /b 1
    )
)

:: Vérification/Installation de Docker Desktop
echo [3/12] Vérification de Docker Desktop...
docker --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=3" %%i in ('docker --version') do (
        set "DOCKER_VERSION=%%i"
        set "DOCKER_VERSION=!DOCKER_VERSION:,=!"
    )
    echo ✓ Docker !DOCKER_VERSION! installé
    
    :: Vérifier que Docker fonctionne
    docker info >nul 2>&1
    if !errorLevel! == 0 (
        echo ✓ Docker opérationnel
    ) else (
        echo ⚠ Docker installé mais non fonctionnel
        echo Démarrage de Docker Desktop...
        
        :: Chercher Docker Desktop
        set "DOCKER_PATH="
        if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
            set "DOCKER_PATH=C:\Program Files\Docker\Docker\Docker Desktop.exe"
        )
        if exist "%USERPROFILE%\AppData\Local\Programs\Docker\Docker\Docker Desktop.exe" (
            set "DOCKER_PATH=%USERPROFILE%\AppData\Local\Programs\Docker\Docker\Docker Desktop.exe"
        )
        
        if defined DOCKER_PATH (
            start "" "!DOCKER_PATH!"
            echo Attente du démarrage de Docker (45 secondes)...
            timeout /t 45 /nobreak >nul
            
            docker info >nul 2>&1
            if !errorLevel! == 0 (
                echo ✓ Docker démarré avec succès
            ) else (
                echo ✗ Docker ne démarre pas correctement
                echo Veuillez démarrer Docker Desktop manuellement
                pause
                exit /b 1
            )
        ) else (
            echo ✗ Docker Desktop non trouvé
            goto :install_docker
        )
    )
) else (
    :install_docker
    echo ✗ Docker non installé
    echo.
    echo Installation automatique de Docker Desktop...
    
    :: Télécharger Docker Desktop
    echo Téléchargement de Docker Desktop...
    powershell -Command "& {
        $url = 'https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe'
        $output = '$env:TEMP\DockerDesktopInstaller.exe'
        try {
            Write-Host 'Téléchargement en cours...'
            Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
            Write-Host 'Installation de Docker Desktop...'
            Start-Process -FilePath $output -ArgumentList 'install --quiet' -Wait
            Remove-Item $output -Force
        } catch {
            Write-Host 'Erreur installation Docker'
            exit 1
        }
    }"
    
    if !errorLevel! neq 0 (
        echo ✗ Échec de l'installation Docker automatique
        echo.
        echo Veuillez installer Docker Desktop manuellement:
        echo 1. Allez sur https://docker.com/products/docker-desktop
        echo 2. Téléchargez Docker Desktop pour Windows
        echo 3. Installez et redémarrez votre PC
        echo 4. Relancez cette installation
        pause
        exit /b 1
    )
    
    echo ✓ Docker Desktop installé
    echo IMPORTANT: Redémarrez votre PC et relancez l'installation
    pause
    exit /b 0
)

:: Vérification Docker Compose
echo [4/12] Vérification de Docker Compose...
docker-compose --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=3" %%i in ('docker-compose --version') do (
        set "COMPOSE_VERSION=%%i"
        set "COMPOSE_VERSION=!COMPOSE_VERSION:,=!"
    )
    echo ✓ Docker Compose !COMPOSE_VERSION!
) else (
    echo ✗ Docker Compose non trouvé
    echo Docker Compose est inclus avec Docker Desktop
    echo Vérifiez votre installation Docker Desktop
    pause
    exit /b 1
)

:: Vérification Git
echo [5/12] Vérification de Git...
git --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=3" %%i in ('git --version') do set "GIT_VERSION=%%i"
    echo ✓ Git !GIT_VERSION!
) else (
    echo ⚠ Git non trouvé
    echo Installation de Git...
    
    :: Installer Git via winget si disponible
    winget install Git.Git --silent --accept-source-agreements --accept-package-agreements >nul 2>&1
    if !errorLevel! == 0 (
        echo ✓ Git installé via winget
        call refreshenv >nul 2>&1
    ) else (
        echo ⚠ Installation Git automatique échouée
        echo Git n'est pas strictement nécessaire pour JARVIS
    )
)

:: Installation Visual C++ Redistributable
echo [6/12] Vérification de Visual C++ Redistributable...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Visual C++ Redistributable installé
) else (
    echo Installation de Visual C++ Redistributable...
    powershell -Command "& {
        $url = 'https://aka.ms/vs/17/release/vc_redist.x64.exe'
        $output = '$env:TEMP\vc_redist.x64.exe'
        try {
            Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
            Start-Process -FilePath $output -ArgumentList '/quiet' -Wait
            Remove-Item $output -Force
        } catch {
            Write-Host 'Installation VC++ ignorée'
        }
    }" 2>nul
    echo ✓ Visual C++ Redistributable traité
)

:: Vérification/Installation Node.js
echo [7/12] Vérification de Node.js...
node --version >nul 2>&1
if %errorLevel% == 0 (
    for /f %%i in ('node --version') do set "NODE_VERSION=%%i"
    echo ✓ Node.js !NODE_VERSION!
    
    npm --version >nul 2>&1
    if %errorLevel% == 0 (
        for /f %%i in ('npm --version') do set "NPM_VERSION=%%i"
        echo ✓ npm !NPM_VERSION!
    )
) else (
    echo Installation de Node.js...
    
    :: Installer Node.js via winget
    winget install OpenJS.NodeJS --silent --accept-source-agreements --accept-package-agreements >nul 2>&1
    if !errorLevel! == 0 (
        echo ✓ Node.js installé via winget
        call refreshenv >nul 2>&1
    ) else (
        echo ⚠ Installation Node.js automatique échouée
        echo Interface web sera limitée
    )
)

:: Installation/Vérification Ollama
echo [8/12] Vérification d'Ollama...
ollama version >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Ollama installé
) else (
    echo Installation d'Ollama...
    
    :: Télécharger et installer Ollama
    powershell -Command "& {
        $url = 'https://ollama.ai/download/windows'
        $output = '$env:TEMP\OllamaSetup.exe'
        try {
            Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
            Start-Process -FilePath $output -ArgumentList '/S' -Wait
            Remove-Item $output -Force
        } catch {
            Write-Host 'Installation Ollama échouée'
            exit 1
        }
    }"
    
    if !errorLevel! == 0 (
        echo ✓ Ollama installé
        call refreshenv >nul 2>&1
        
        :: Démarrer le service Ollama
        start "" ollama serve
        timeout /t 5 /nobreak >nul
    ) else (
        echo ⚠ Installation Ollama échouée - Fonctionnalités IA limitées
    )
)

:: Préparation de l'environnement Python
echo [9/12] Préparation de l'environnement Python...

:: Créer l'environnement virtuel
if not exist "venv" (
    echo Création de l'environnement virtuel...
    python -m venv venv
    if !errorLevel! neq 0 (
        echo ✗ Erreur création environnement virtuel
        pause
        exit /b 1
    )
)

:: Activer l'environnement virtuel
call venv\Scripts\activate.bat

:: Mise à jour de pip
echo Mise à jour de pip...
python -m pip install --upgrade pip setuptools wheel

:: Installation des dépendances Windows spécifiques
echo Installation des dépendances Windows...
pip install pywin32 pyautogui keyboard psutil

echo ✓ Environnement Python configuré

:: Configuration Docker
echo [10/12] Configuration de l'environnement Docker...

:: Créer le réseau Docker si nécessaire
docker network create jarvis-network >nul 2>&1

:: Créer les répertoires nécessaires
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache
if not exist "memory" mkdir memory
if not exist "models" mkdir models
if not exist "data" mkdir data

echo ✓ Environnement Docker configuré

:: Test de la configuration
echo [11/12] Test de la configuration...

:: Test Docker
docker run --rm hello-world >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Docker fonctionne correctement
) else (
    echo ⚠ Problème avec Docker
)

:: Test Docker Compose
docker-compose config >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Configuration Docker Compose valide
) else (
    echo ⚠ Configuration Docker Compose invalide
)

:: Lancement de l'installation principale Python
echo [12/12] Lancement de l'installation principale...
echo.
echo ════════════════════════════════════════════════════════════════
echo              INSTALLATION JARVIS AI EN COURS...
echo ════════════════════════════════════════════════════════════════
echo.

python install-jarvis.py
set install_result=%errorLevel%

echo.
echo ════════════════════════════════════════════════════════════════

if %install_result% == 0 (
    echo.
    echo ✓ INSTALLATION WINDOWS RÉUSSIE!
    echo.
    
    :: Créer un script de lancement Windows optimisé
    call :create_windows_launcher
    
    echo Scripts de lancement créés:
    echo   📄 launch-jarvis-windows.bat  - Lancement complet
    echo   📄 launch-voice-bridge.bat    - Pont vocal uniquement
    echo   📄 stop-jarvis.bat           - Arrêt propre
    echo.
    echo Accès aux services:
    echo   🌐 Interface web: http://localhost:3000
    echo   🔗 API principale: http://localhost:5000
    echo   📚 Documentation: http://localhost:5000/docs
    echo.
    
    if "!WSL_AVAILABLE!"=="1" (
        echo Alternative WSL disponible:
        echo   📄 launch-jarvis-wsl.bat      - Via WSL (recommandé pour Docker)
        echo.
    )
    
    echo Voulez-vous démarrer JARVIS maintenant? (O/N)
    set /p start_now="> "
    if /i "!start_now!"=="O" (
        echo Démarrage de JARVIS AI...
        call launch-jarvis-windows.bat
    )
) else (
    echo.
    echo ✗ ERREUR LORS DE L'INSTALLATION
    echo.
    echo Consultez le fichier jarvis-install.log pour plus de détails
    echo.
)

:end
echo.
echo Appuyez sur une touche pour fermer cette fenêtre...
pause >nul
goto :eof

:: Fonction pour créer le script de lancement Windows
:create_windows_launcher
echo @echo off > launch-jarvis-windows.bat
echo title JARVIS AI - Windows Native >> launch-jarvis-windows.bat
echo. >> launch-jarvis-windows.bat
echo echo ╔══════════════════════════════════════════╗ >> launch-jarvis-windows.bat
echo echo ║            JARVIS AI STARTUP             ║ >> launch-jarvis-windows.bat
echo echo ║           Windows Native Mode            ║ >> launch-jarvis-windows.bat
echo echo ╚══════════════════════════════════════════╝ >> launch-jarvis-windows.bat
echo echo. >> launch-jarvis-windows.bat
echo. >> launch-jarvis-windows.bat
echo cd /d "%~dp0" >> launch-jarvis-windows.bat
echo. >> launch-jarvis-windows.bat
echo echo [1/5] Vérification des services... >> launch-jarvis-windows.bat
echo docker info ^>nul 2^>^&1 >> launch-jarvis-windows.bat
echo if %%errorlevel%% neq 0 ( >> launch-jarvis-windows.bat
echo     echo ✗ Docker non accessible - Démarrage de Docker Desktop... >> launch-jarvis-windows.bat
echo     start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" >> launch-jarvis-windows.bat
echo     echo Attente du démarrage de Docker... >> launch-jarvis-windows.bat
echo     timeout /t 30 /nobreak ^>nul >> launch-jarvis-windows.bat
echo ) >> launch-jarvis-windows.bat
echo. >> launch-jarvis-windows.bat
echo echo [2/5] Démarrage des services Docker... >> launch-jarvis-windows.bat
echo docker-compose up -d >> launch-jarvis-windows.bat
echo if %%errorlevel%% neq 0 ( >> launch-jarvis-windows.bat
echo     echo ✗ Erreur démarrage Docker Compose >> launch-jarvis-windows.bat
echo     pause >> launch-jarvis-windows.bat
echo     exit /b 1 >> launch-jarvis-windows.bat
echo ) >> launch-jarvis-windows.bat
echo. >> launch-jarvis-windows.bat
echo echo [3/5] Attente de l'initialisation... >> launch-jarvis-windows.bat
echo timeout /t 15 /nobreak ^>nul >> launch-jarvis-windows.bat
echo. >> launch-jarvis-windows.bat
echo echo [4/5] Démarrage du pont vocal... >> launch-jarvis-windows.bat
echo if exist "start-voice-bridge.bat" ( >> launch-jarvis-windows.bat
echo     start "Voice Bridge" start-voice-bridge.bat >> launch-jarvis-windows.bat
echo ) else ( >> launch-jarvis-windows.bat
echo     echo ⚠ Pont vocal non trouvé >> launch-jarvis-windows.bat
echo ) >> launch-jarvis-windows.bat
echo. >> launch-jarvis-windows.bat
echo echo [5/5] Démarrage de l'interface principale... >> launch-jarvis-windows.bat
echo call venv\Scripts\activate.bat >> launch-jarvis-windows.bat
echo start "JARVIS Main" python start_jarvis.py >> launch-jarvis-windows.bat
echo. >> launch-jarvis-windows.bat
echo echo ✓ JARVIS AI démarré avec succès! >> launch-jarvis-windows.bat
echo echo   - Interface web: http://localhost:3000 >> launch-jarvis-windows.bat
echo echo   - API principale: http://localhost:5000 >> launch-jarvis-windows.bat
echo echo   - Documentation: http://localhost:5000/docs >> launch-jarvis-windows.bat
echo echo. >> launch-jarvis-windows.bat
echo echo Appuyez sur une touche pour ouvrir l'interface web... >> launch-jarvis-windows.bat
echo pause ^>nul >> launch-jarvis-windows.bat
echo start http://localhost:3000 >> launch-jarvis-windows.bat

:: Script d'arrêt
echo @echo off > stop-jarvis.bat
echo title JARVIS AI - Arrêt >> stop-jarvis.bat
echo echo Arrêt de JARVIS AI... >> stop-jarvis.bat
echo docker-compose down >> stop-jarvis.bat
echo taskkill /f /im python.exe /fi "WINDOWTITLE eq Voice Bridge*" 2^>nul >> stop-jarvis.bat
echo taskkill /f /im python.exe /fi "WINDOWTITLE eq JARVIS Main*" 2^>nul >> stop-jarvis.bat
echo echo ✓ JARVIS AI arrêté >> stop-jarvis.bat
echo pause >> stop-jarvis.bat

goto :eof