@echo off
title JARVIS AI - Installation Automatique
chcp 65001 >nul

:: Configuration des couleurs
for /f %%A in ('"prompt $H &echo on &for %%B in (1) do rem"') do set BS=%%A

echo.
echo ╔══════════════════════════════════════════╗
echo ║          JARVIS AI INSTALLER             ║
echo ║         Installation Windows             ║
echo ╚══════════════════════════════════════════╝
echo.

:: Vérification des privilèges administrateur
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Privilèges administrateur détectés
) else (
    echo [WARN] Exécution sans privilèges administrateur
    echo        Certaines fonctionnalités peuvent être limitées
    echo.
)

:: Vérification de Python
echo [1/8] Vérification de Python...
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Python installé
) else (
    echo ✗ Python non trouvé
    echo.
    echo ERREUR: Python est requis pour l'installation
    echo Téléchargez Python depuis: https://python.org
    echo.
    pause
    exit /b 1
)

:: Vérification de Docker
echo [2/8] Vérification de Docker...
docker --version >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Docker installé
) else (
    echo ✗ Docker non trouvé
    echo.
    echo ERREUR: Docker est requis pour l'installation
    echo Téléchargez Docker Desktop depuis: https://docker.com
    echo.
    pause
    exit /b 1
)

:: Vérification de Docker Compose
echo [3/8] Vérification de Docker Compose...
docker-compose --version >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Docker Compose installé
) else (
    echo ✗ Docker Compose non trouvé
    echo.
    echo ERREUR: Docker Compose est requis
    echo.
    pause
    exit /b 1
)

:: Vérification de Git
echo [4/8] Vérification de Git...
git --version >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Git installé
) else (
    echo ⚠ Git non trouvé (optionnel)
)

:: Installation des dépendances système
echo [5/8] Installation des dépendances système...
echo Installation de Visual C++ Redistributable (si nécessaire)...
:: Tentative d'installation silencieuse de VC++ Redist
powershell -Command "& {
    try {
        $url = 'https://aka.ms/vs/17/release/vc_redist.x64.exe'
        $output = '$env:TEMP\vc_redist.x64.exe'
        if (!(Test-Path $output)) {
            Invoke-WebRequest -Uri $url -OutFile $output -ErrorAction SilentlyContinue
            if (Test-Path $output) {
                Start-Process -FilePath $output -ArgumentList '/quiet' -Wait -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-Host 'Installation VC++ ignorée'
    }
}" 2>nul

:: Démarrage de Docker Desktop si nécessaire
echo [6/8] Vérification de Docker Desktop...
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo Démarrage de Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Attente du démarrage de Docker (30 secondes)...
    timeout /t 30 /nobreak >nul
    
    :: Vérification après attente
    docker info >nul 2>&1
    if %errorLevel% neq 0 (
        echo.
        echo ERREUR: Docker ne démarre pas
        echo Veuillez démarrer Docker Desktop manuellement et relancer l'installation
        echo.
        pause
        exit /b 1
    )
)
echo ✓ Docker opérationnel

:: Vérification de Node.js (optionnel pour l'interface web)
echo [7/8] Vérification de Node.js...
node --version >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Node.js installé
    npm --version >nul 2>&1
    if %errorLevel% == 0 (
        echo ✓ npm installé
    ) else (
        echo ⚠ npm non trouvé
    )
) else (
    echo ⚠ Node.js non trouvé (interface web limitée)
    echo   Pour l'interface web complète, installez Node.js depuis nodejs.org
)

:: Lancement de l'installation Python
echo [8/8] Lancement de l'installation principale...
echo.
echo ═══════════════════════════════════════════════════════════════
echo              INSTALLATION JARVIS AI EN COURS...
echo ═══════════════════════════════════════════════════════════════
echo.

python install-jarvis.py
set install_result=%errorLevel%

echo.
echo ═══════════════════════════════════════════════════════════════

if %install_result% == 0 (
    echo.
    echo ✓ INSTALLATION RÉUSSIE!
    echo.
    echo Pour démarrer JARVIS AI:
    echo   📄 Double-cliquez sur: launch-jarvis.bat
    echo.
    echo Accès aux services:
    echo   🌐 Interface web: http://localhost:3000
    echo   🔗 API principale: http://localhost:5000
    echo   📚 Documentation: http://localhost:5000/docs
    echo.
    echo Voulez-vous démarrer JARVIS maintenant? (O/N)
    set /p start_now="> "
    if /i "!start_now!"=="O" (
        echo Démarrage de JARVIS AI...
        call launch-jarvis.bat
    )
) else (
    echo.
    echo ✗ ERREUR LORS DE L'INSTALLATION
    echo.
    echo Consultez le fichier jarvis-install.log pour plus de détails
    echo.
)

echo.
echo Appuyez sur une touche pour fermer cette fenêtre...
pause >nul