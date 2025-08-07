@echo off
REM ============================================================
REM JARVIS AI - COMPLETE SHUTDOWN SCRIPT
REM Stops all services, containers, and cleans up resources
REM ============================================================

setlocal EnableDelayedExpansion
color 0C
title JARVIS AI - Shutdown Manager

echo.
echo ============================================================
echo           JARVIS AI - COMPLETE SHUTDOWN
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/8] Stopping all Docker Compose services...
docker-compose down --remove-orphans

echo [2/8] Stopping monitoring services...
if exist "docker-compose.monitoring.yml" (
    docker-compose -f docker-compose.monitoring.yml down
)

echo [3/8] Stopping individual service pods...
docker-compose -f docker-compose.ai-pod.yml down 2>nul
docker-compose -f docker-compose.audio-pod.yml down 2>nul
docker-compose -f docker-compose.control-pod.yml down 2>nul
docker-compose -f docker-compose.integration-pod.yml down 2>nul

echo [4/8] Killing Node.js processes (UI)...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM npm.cmd 2>nul

echo [5/8] Stopping Python processes...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO TABLE /NH 2^>nul') do (
    tasklist /FI "PID eq %%i" /FO CSV | findstr "voice-bridge\|jarvis\|brain-api" >nul
    if !errorLevel! equ 0 (
        taskkill /F /PID %%i 2>nul
    )
)

echo [6/8] Cleaning Docker resources...
echo    Removing stopped containers...
docker container prune -f >nul 2>&1

echo    Removing unused networks...
docker network prune -f >nul 2>&1

echo    Removing dangling images...
docker image prune -f >nul 2>&1

echo [7/8] Checking for persistent processes...
netstat -ano | findstr ":8080\|:3000\|:5002\|:5003\|:11434" | findstr "LISTENING" >nul
if %errorLevel% equ 0 (
    echo [WARNING] Some processes are still listening on JARVIS ports
    echo You may need to restart your computer for complete cleanup
)

echo [8/8] Final status check...
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr jarvis
if %errorLevel% equ 0 (
    echo [WARNING] Some JARVIS containers are still running
) else (
    echo [OK] All JARVIS services stopped successfully
)

echo.
echo ============================================================
echo              JARVIS AI SHUTDOWN COMPLETE
echo ============================================================
echo.
echo All services have been stopped and resources cleaned up.
echo.
echo To restart JARVIS:
echo   - Full setup: JARVIS-LAUNCH-ALL.bat
echo   - Quick start: JARVIS-QUICK-START.bat
echo.
pause

endlocal