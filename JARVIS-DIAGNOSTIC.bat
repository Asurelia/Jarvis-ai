@echo off
REM ============================================================
REM JARVIS AI - DIAGNOSTIC COMPLET
REM Identifie tous les problèmes avant lancement
REM ============================================================

color 0E
title JARVIS AI - Diagnostic
echo.
echo ============================================================
echo           JARVIS AI - DIAGNOSTIC COMPLET
echo ============================================================
echo.

set "ISSUES_FOUND=0"

echo [1/8] Verification des fichiers du projet...
echo ============================================================
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml manquant!
    set /a ISSUES_FOUND+=1
) else (
    echo [OK] docker-compose.yml trouve
)

if not exist "services" (
    echo [ERROR] Dossier services/ manquant!
    set /a ISSUES_FOUND+=1
) else (
    echo [OK] Dossier services/ trouve
)

if not exist "ui" (
    echo [ERROR] Dossier ui/ manquant!
    set /a ISSUES_FOUND+=1
) else (
    echo [OK] Dossier ui/ trouve
)

echo.
echo [2/8] Verification Python...
echo ============================================================
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python non installe ou pas dans PATH!
    echo Telechargez Python 3.11+ depuis https://python.org
    set /a ISSUES_FOUND+=1
) else (
    echo [OK] Python detecte
    python --version
)

echo.
echo [3/8] Verification Docker...
echo ============================================================
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker non installe!
    echo Telechargez Docker Desktop depuis https://docker.com
    set /a ISSUES_FOUND+=1
) else (
    echo [OK] Docker installe
    docker --version
)

echo.
echo [4/8] Verification Docker Desktop...
echo ============================================================
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker Desktop n'est PAS demarre!
    echo.
    echo SOLUTION:
    echo 1. Ouvrez Docker Desktop manuellement
    echo 2. Attendez qu'il affiche "Engine running"
    echo 3. Puis relancez JARVIS
    echo.
    set /a ISSUES_FOUND+=1
) else (
    echo [OK] Docker Desktop est en marche
)

echo.
echo [5/8] Verification des ports...
echo ============================================================
set "BLOCKED_PORTS="
set "PORTS_TO_CHECK=3000 5002 5003 8080 5432 6379 11434"

for %%p in (%PORTS_TO_CHECK%) do (
    netstat -an | findstr :%%p | findstr LISTENING >nul 2>&1
    if !errorLevel! equ 0 (
        echo [WARNING] Port %%p occupe
        set "BLOCKED_PORTS=!BLOCKED_PORTS! %%p"
    ) else (
        echo [OK] Port %%p libre
    )
)

if not "%BLOCKED_PORTS%"=="" (
    echo.
    echo [INFO] Ports occupes: %BLOCKED_PORTS%
    echo Utilisez JARVIS-STOP-ALL.bat pour les liberer
)

echo.
echo [6/8] Verification Node.js (pour UI)...
echo ============================================================
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Node.js non installe (optionnel pour Docker)
    echo Pour developpement local, installez Node.js 18+
) else (
    echo [OK] Node.js detecte
    node --version
)

echo.
echo [7/8] Verification espace disque...
echo ============================================================
for /f "tokens=3" %%a in ('dir /-c ^| findstr "octets libres"') do set FREE_SPACE=%%a
echo Espace libre: %FREE_SPACE% octets
REM Verification basique espace (simplifie)
if %FREE_SPACE% LSS 5000000000 (
    echo [WARNING] Moins de 5GB libres - Docker peut avoir des problemes
) else (
    echo [OK] Espace disque suffisant
)

echo.
echo [8/8] Verification permissions...
echo ============================================================
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Pas de privileges administrateur
    echo Recommande pour Docker - clic droit "Executer en tant qu'admin"
) else (
    echo [OK] Privileges administrateur detectes
)

echo.
echo ============================================================
echo                    RESUME DIAGNOSTIC
echo ============================================================
echo.
if %ISSUES_FOUND% equ 0 (
    echo [SUCCESS] Aucun probleme detecte!
    echo Vous pouvez lancer JARVIS avec JARVIS-LAUNCH-ALL.bat
    echo.
) else (
    echo [ERROR] %ISSUES_FOUND% probleme(s) detecte(s)
    echo.
    echo ACTIONS RECOMMANDEES:
    echo.
    echo 1. Si Docker Desktop n'est pas demarre:
    echo    - Ouvrez Docker Desktop manuellement
    echo    - Attendez "Engine running"
    echo    - Relancez ce diagnostic
    echo.
    echo 2. Si Python manque:
    echo    - Installez Python 3.11+ depuis python.org
    echo    - Redemarrez le terminal
    echo.
    echo 3. Si Docker manque:
    echo    - Installez Docker Desktop depuis docker.com
    echo    - Redemarrez Windows
    echo.
    echo 4. Si ports occupes:
    echo    - Lancez JARVIS-STOP-ALL.bat
    echo    - Ou redemarrez Windows
)

echo.
echo ============================================================
echo Appuyez sur une touche pour continuer...
pause >nul