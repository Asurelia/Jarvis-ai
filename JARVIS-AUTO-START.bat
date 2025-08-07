@echo off
REM ============================================================
REM JARVIS AI - DEMARRAGE AUTOMATIQUE COMPLET
REM Demarre Docker Desktop puis JARVIS automatiquement
REM ============================================================

setlocal EnableDelayedExpansion
color 0A
title JARVIS AI - Auto Start

echo.
echo ============================================================
echo           JARVIS AI - DEMARRAGE AUTOMATIQUE
echo ============================================================
echo.

REM Verification privileges admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Privileges administrateur requis!
    echo Clic droit sur ce fichier et "Executer en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

echo [1/4] Verification Docker Desktop...
echo ============================================================

REM Verifier si Docker Desktop est deja en marche
docker info >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Docker Desktop deja en marche!
    goto START_JARVIS
)

REM Chercher Docker Desktop
set "DOCKER_PATH="
if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
    set "DOCKER_PATH=C:\Program Files\Docker\Docker\Docker Desktop.exe"
) else if exist "C:\Users\%USERNAME%\AppData\Local\Docker\Docker Desktop\Docker Desktop.exe" (
    set "DOCKER_PATH=C:\Users\%USERNAME%\AppData\Local\Docker\Docker Desktop\Docker Desktop.exe"
) else (
    echo [ERROR] Docker Desktop non trouve!
    echo.
    echo INSTALLATION REQUISE:
    echo 1. Allez sur https://docker.com
    echo 2. Telechargez Docker Desktop
    echo 3. Installez-le
    echo 4. Redemarrez Windows
    echo 5. Relancez ce script
    echo.
    pause
    exit /b 1
)

echo [2/4] Demarrage Docker Desktop...
echo ============================================================
echo Docker Desktop trouve: %DOCKER_PATH%
echo Demarrage en cours...

start "" "%DOCKER_PATH%"

echo Attente du demarrage de Docker Engine...
set "WAIT_COUNT=0"

:WAIT_DOCKER
set /a WAIT_COUNT+=1
timeout /t 5 /nobreak >nul

docker info >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Docker Engine demarre! (%WAIT_COUNT% tentatives)
    goto START_JARVIS
)

if %WAIT_COUNT% geq 24 (
    echo [ERROR] Docker Desktop met trop de temps a demarrer!
    echo.
    echo SOLUTIONS:
    echo 1. Verifiez que Docker Desktop s'ouvre correctement
    echo 2. Attendez "Engine running" dans Docker Desktop
    echo 3. Redemarrez Windows si probleme
    echo 4. Verifiez que Hyper-V/WSL2 est active
    echo.
    echo Appuyez sur une touche pour continuer quand meme...
    pause >nul
    goto START_JARVIS
)

echo Attente Docker Engine... (%WAIT_COUNT%/24 - %WAIT_COUNT%0 secondes)
goto WAIT_DOCKER

:START_JARVIS
echo.
echo [3/4] Docker pret, verification services...
echo ============================================================

REM Nettoyer les anciens containers
echo Nettoyage des anciens containers...
docker-compose down --remove-orphans >nul 2>&1
docker container prune -f >nul 2>&1

echo.
echo [4/4] Lancement JARVIS AI...
echo ============================================================

REM Lancer le script principal
if exist "JARVIS-LAUNCH-ALL.bat" (
    echo Execution du lanceur principal...
    call JARVIS-LAUNCH-ALL.bat
) else (
    echo [ERROR] JARVIS-LAUNCH-ALL.bat non trouve!
    echo Assurez-vous d'etre dans le bon dossier du projet.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo        JARVIS AI AUTO-START TERMINE
echo ============================================================
echo.

endlocal