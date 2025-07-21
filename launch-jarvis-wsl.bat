@echo off
setlocal enabledelayedexpansion
title JARVIS AI - Lancement WSL
chcp 65001 >nul

echo.
echo ╔══════════════════════════════════════════╗
echo ║            JARVIS AI STARTUP             ║
echo ║              WSL2 Mode                   ║
echo ╚══════════════════════════════════════════╝
echo.

:: Vérification de WSL
echo [1/6] Vérification de WSL...
wsl --status >nul 2>&1
if %errorLevel% neq 0 (
    echo ✗ WSL non disponible
    echo.
    echo Pour installer WSL:
    echo   1. Ouvrez PowerShell en tant qu'administrateur
    echo   2. Exécutez: wsl --install
    echo   3. Redémarrez votre PC
    echo   4. Configurez Ubuntu ou votre distribution préférée
    echo.
    pause
    exit /b 1
)

:: Obtenir la distribution par défaut
for /f "tokens=*" %%i in ('wsl -l -q 2^>nul ^| findstr /v "^$"') do (
    set "WSL_DISTRO=%%i"
    goto :wsl_found
)

:wsl_found
echo ✓ WSL disponible - Distribution: !WSL_DISTRO!

:: [2/6] Préparation de l'environnement WSL
echo [2/6] Préparation de l'environnement WSL...

:: Vérifier si le répertoire existe dans WSL
wsl test -d /home/jarvis-ai
if %errorLevel% neq 0 (
    echo Création du répertoire de travail dans WSL...
    wsl mkdir -p /home/jarvis-ai
    
    echo Copie des fichiers vers WSL...
    :: Convertir le chemin Windows vers WSL
    set "WINDOWS_PATH=%~dp0"
    set "WINDOWS_PATH=!WINDOWS_PATH:\=/!"
    set "WINDOWS_PATH=!WINDOWS_PATH::=!"
    set "WSL_PATH=/mnt/!WINDOWS_PATH!"
    
    echo   Source: !WSL_PATH!
    echo   Destination: /home/jarvis-ai/
    
    wsl bash -c "cp -r '!WSL_PATH!'* /home/jarvis-ai/ 2>/dev/null || echo 'Copie partielle'"
    
    if %errorLevel% neq 0 (
        echo ⚠ Copie avec erreurs - Vérification des fichiers critiques...
        wsl bash -c "ls -la /home/jarvis-ai/"
    )
)

echo ✓ Environnement WSL préparé

:: [3/6] Installation des dépendances WSL
echo [3/6] Vérification des dépendances WSL...

:: Vérifier si Docker est installé dans WSL
wsl which docker >nul 2>&1
if %errorLevel% neq 0 (
    echo Installation de Docker dans WSL...
    wsl bash -c "
        sudo apt-get update -qq
        sudo apt-get install -y docker.io docker-compose python3 python3-pip python3-venv curl
        sudo usermod -aG docker \$USER
        sudo service docker start
    "
    
    if %errorLevel% neq 0 (
        echo ⚠ Installation Docker WSL avec erreurs - Continuation...
    )
) else (
    echo ✓ Docker disponible dans WSL
    
    :: Démarrer le service Docker dans WSL
    wsl sudo service docker start >nul 2>&1
)

:: [4/6] Vérification de la configuration
echo [4/6] Vérification de la configuration WSL...

:: Vérifier les fichiers critiques
wsl bash -c "cd /home/jarvis-ai && ls -la install-jarvis.sh docker-compose.yml start_jarvis.py" >nul 2>&1
if %errorLevel% neq 0 (
    echo ✗ Fichiers critiques manquants dans WSL
    echo.
    echo Vérification des fichiers:
    wsl bash -c "cd /home/jarvis-ai && ls -la"
    echo.
    echo Tentative de recopie...
    
    :: Recopie manuelle des fichiers critiques
    copy "install-jarvis.sh" "\\wsl$\!WSL_DISTRO!\home\jarvis-ai\" >nul 2>&1
    copy "docker-compose.yml" "\\wsl$\!WSL_DISTRO!\home\jarvis-ai\" >nul 2>&1
    copy "start_jarvis.py" "\\wsl$\!WSL_DISTRO!\home\jarvis-ai\" >nul 2>&1
    copy "requirements.txt" "\\wsl$\!WSL_DISTRO!\home\jarvis-ai\" >nul 2>&1
    
    wsl bash -c "cd /home/jarvis-ai && chmod +x *.sh" >nul 2>&1
)

echo ✓ Configuration WSL validée

:: [5/6] Lancement de l'installation/démarrage WSL
echo [5/6] Lancement dans WSL...
echo.
echo ══════════════════════════════════════════════════════════════════
echo                    EXÉCUTION DANS WSL2
echo ══════════════════════════════════════════════════════════════════
echo.

:: Vérifier si JARVIS est déjà installé
wsl bash -c "cd /home/jarvis-ai && test -d venv && test -f launch-jarvis.sh"
if %errorLevel% == 0 (
    echo JARVIS détecté dans WSL - Démarrage direct...
    
    wsl bash -c "cd /home/jarvis-ai && ./launch-jarvis.sh"
    set "WSL_RESULT=%errorLevel%"
) else (
    echo Installation de JARVIS dans WSL...
    
    :: Rendre les scripts exécutables
    wsl bash -c "cd /home/jarvis-ai && chmod +x *.sh" >nul 2>&1
    
    :: Lancer l'installation
    wsl bash -c "cd /home/jarvis-ai && ./install-jarvis.sh"
    set "WSL_INSTALL_RESULT=%errorLevel%"
    
    if !WSL_INSTALL_RESULT! == 0 (
        echo ✓ Installation WSL réussie - Démarrage...
        wsl bash -c "cd /home/jarvis-ai && ./launch-jarvis.sh"
        set "WSL_RESULT=%errorLevel%"
    ) else (
        echo ✗ Échec installation WSL
        set "WSL_RESULT=1"
    )
)

:: [6/6] Résultats et accès
echo.
echo ══════════════════════════════════════════════════════════════════

if !WSL_RESULT! == 0 (
    echo                    ✓ JARVIS AI DÉMARRÉ DANS WSL!
    echo ══════════════════════════════════════════════════════════════════
    echo.
    echo Services accessibles depuis Windows:
    echo   🌐 Interface web:     http://localhost:3000
    echo   🔗 API principale:    http://localhost:5000
    echo   📚 Documentation:     http://localhost:5000/docs
    echo.
    echo Commandes WSL utiles:
    echo   Status:    wsl bash -c "cd /home/jarvis-ai && docker-compose ps"
    echo   Logs:      wsl bash -c "cd /home/jarvis-ai && docker-compose logs"
    echo   Arrêt:     wsl bash -c "cd /home/jarvis-ai && docker-compose down"
    echo   Shell:     wsl bash -c "cd /home/jarvis-ai && bash"
    echo.
    
    :: Proposer d'ouvrir l'interface web
    echo Voulez-vous ouvrir l'interface web? (O/N)
    set /p open_web="> "
    if /i "!open_web!"=="O" (
        echo Ouverture de l'interface web...
        start http://localhost:3000
    )
    
    echo.
    echo ══════════════════════════════════════════════════════════════════
    echo JARVIS fonctionne dans WSL en arrière-plan
    echo Fermez cette fenêtre ou utilisez Ctrl+C pour revenir au prompt
    echo ══════════════════════════════════════════════════════════════════
    
    :: Monitoring en arrière-plan
    echo.
    echo Monitoring des services WSL (Ctrl+C pour arrêter):
    :monitor_wsl
    timeout /t 30 /nobreak >nul
    echo [%time%] Services actifs:
    wsl bash -c "cd /home/jarvis-ai && docker-compose ps --format 'table {{.Name}}\t{{.Status}}'" 2>nul
    echo.
    goto :monitor_wsl
    
) else (
    echo                    ✗ ERREUR DÉMARRAGE WSL
    echo ══════════════════════════════════════════════════════════════════
    echo.
    echo Diagnostic WSL:
    wsl bash -c "cd /home/jarvis-ai && echo 'Répertoire WSL:' && pwd && echo 'Fichiers:' && ls -la"
    echo.
    echo Solutions possibles:
    echo   1. Relancer avec des privilèges administrateur
    echo   2. Vérifier l'installation WSL: wsl --status
    echo   3. Redémarrer WSL: wsl --shutdown puis relancer
    echo   4. Utiliser l'installation Windows native: launch-jarvis-windows.bat
    echo.
)

echo.
echo Appuyez sur une touche pour fermer...
pause >nul