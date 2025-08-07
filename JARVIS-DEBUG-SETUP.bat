@echo off
REM ============================================================
REM JARVIS AI - SETUP AVEC DEBUG DETAILLE
REM Version debug pour identifier les problemes
REM ============================================================

setlocal EnableDelayedExpansion
color 0C
title JARVIS AI - Debug Setup

echo.
echo ============================================================
echo         JARVIS AI - SETUP DEBUG MODE
echo ============================================================
echo.

echo DEBUG: Script demarre a %TIME%
echo DEBUG: Repertoire courant: %CD%
echo DEBUG: Utilisateur: %USERNAME%
echo.

echo [TEST 1] Verification privileges administrateur...
echo ============================================================
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERREUR] Pas de privileges administrateur!
    echo.
    echo SOLUTION:
    echo 1. Fermez cette fenetre
    echo 2. Clic DROIT sur le fichier .bat
    echo 3. Choisissez "Executer en tant qu'administrateur"
    echo.
    echo Appuyez sur une touche pour fermer...
    pause >nul
    exit /b 1
) else (
    echo [OK] Privileges administrateur detectes
)

echo.
echo [TEST 2] Verification Python...
echo ============================================================
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERREUR] Python non trouve!
    echo.
    echo ETAPES D'INSTALLATION:
    echo 1. Allez sur https://www.python.org/downloads/
    echo 2. Telechargez Python 3.11 ou plus recent
    echo 3. IMPORTANT: Cochez "Add Python to PATH" pendant l'installation
    echo 4. Redemarrez votre ordinateur
    echo 5. Relancez ce script
    echo.
    echo Appuyez sur une touche pour continuer quand meme...
    pause >nul
    goto SKIP_PYTHON
) else (
    echo [OK] Python detecte:
    python --version
)

echo Test import modules Python de base...
python -c "import sys; print('Python OK')" 2>nul
if %errorLevel% neq 0 (
    echo [ERREUR] Python defaillant!
    echo Reinstallez Python completement
    pause
    exit /b 1
)

:SKIP_PYTHON

echo.
echo [TEST 3] Verification Docker...
echo ============================================================
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERREUR] Docker non trouve!
    echo.
    echo ETAPES D'INSTALLATION:
    echo 1. Allez sur https://www.docker.com/products/docker-desktop/
    echo 2. Telechargez Docker Desktop pour Windows
    echo 3. Installez-le (redemarrage requis)
    echo 4. Demarrez Docker Desktop manuellement
    echo 5. Attendez "Engine running" dans Docker Desktop
    echo 6. Relancez ce script
    echo.
    echo Appuyez sur une touche pour continuer quand meme...
    pause >nul
    goto SKIP_DOCKER
) else (
    echo [OK] Docker detecte:
    docker --version
)

echo.
echo [TEST 4] Verification Docker Engine...
echo ============================================================
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERREUR] Docker Engine non demarre!
    echo.
    echo SOLUTIONS:
    echo 1. Ouvrez Docker Desktop manuellement
    echo 2. Attendez le message "Engine running" 
    echo 3. Si ca ne marche pas, redemarrez Windows
    echo 4. Relancez ce script
    echo.
    
    echo Tentative de demarrage automatique...
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        echo Lancement Docker Desktop...
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        
        echo Attente 60 secondes pour le demarrage...
        timeout /t 60 /nobreak
        
        docker info >nul 2>&1
        if %errorLevel% equ 0 (
            echo [OK] Docker Engine demarre!
        ) else (
            echo [ERREUR] Docker ne demarre toujours pas!
            echo Demarrez Docker Desktop manuellement et relancez ce script.
            pause
            exit /b 1
        )
    ) else (
        echo Docker Desktop executable non trouve!
        echo Installez Docker Desktop et relancez ce script.
        pause
        exit /b 1
    )
) else (
    echo [OK] Docker Engine fonctionne
    echo Containers actuels:
    docker ps --format "table {{.Names}}\t{{.Status}}"
)

:SKIP_DOCKER

echo.
echo [TEST 5] Verification fichiers projet...
echo ============================================================
echo Fichiers dans le repertoire:
dir /b

echo.
echo Verification fichiers essentiels:
if exist "docker-compose.yml" (
    echo [OK] docker-compose.yml trouve
) else (
    echo [ERREUR] docker-compose.yml manquant!
)

if exist "services" (
    echo [OK] Dossier services/ trouve
    echo Services disponibles:
    dir services /b
) else (
    echo [ERREUR] Dossier services/ manquant!
)

echo.
echo [TEST 6] Test permissions ecriture...
echo ============================================================
echo test > test_write.tmp 2>nul
if exist "test_write.tmp" (
    echo [OK] Permissions ecriture OK
    del test_write.tmp >nul 2>&1
) else (
    echo [ERREUR] Pas de permissions ecriture!
    echo Changez de repertoire ou executez en tant qu'admin
)

echo.
echo [TEST 7] Verification espace disque...
echo ============================================================
for /f "tokens=3" %%a in ('dir /-c 2^>nul ^| findstr "octets libres"') do set FREE_SPACE=%%a
if defined FREE_SPACE (
    echo Espace disque libre: %FREE_SPACE% octets
) else (
    echo Impossible de determiner l'espace disque
)

echo.
echo [TEST 8] Test creation environnement virtuel...
echo ============================================================
if exist "venv" (
    echo Environnement virtuel existe deja
    if exist "venv\Scripts\python.exe" (
        echo [OK] Python virtuel fonctionnel
    ) else (
        echo [ERREUR] Environnement virtuel corrompu!
        echo Suppression pour recreation...
        rmdir /s /q venv >nul 2>&1
    )
)

if not exist "venv" (
    echo Creation environnement virtuel de test...
    python -m venv venv 2>&1
    if %errorLevel% equ 0 (
        echo [OK] Environnement virtuel cree avec succes
    ) else (
        echo [ERREUR] Echec creation environnement virtuel!
        echo Verifiez que Python est correctement installe
        pause
        exit /b 1
    )
)

echo.
echo [TEST 9] Test activation environnement virtuel...
echo ============================================================
if exist "venv\Scripts\activate.bat" (
    echo Test activation...
    call venv\Scripts\activate.bat
    echo [OK] Environnement virtuel active
    
    echo Test pip...
    pip --version >nul 2>&1
    if %errorLevel% equ 0 (
        echo [OK] pip fonctionnel
    ) else (
        echo [ERREUR] pip non fonctionnel!
    )
) else (
    echo [ERREUR] Script d'activation manquant!
)

echo.
echo ============================================================
echo                  DIAGNOSTIC TERMINE
echo ============================================================
echo.
echo Si tous les tests sont OK, vous pouvez maintenant lancer:
echo JARVIS-FIRST-TIME-SETUP.bat
echo.
echo Si il y a des erreurs:
echo 1. Corrigez les problemes identifies
echo 2. Relancez ce diagnostic
echo 3. Puis lancez le setup complet
echo.
echo ============================================================
echo Appuyez sur une touche pour fermer...
pause >nul

endlocal