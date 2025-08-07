@echo off
REM ============================================================
REM JARVIS AI - QUICK START (For Already Configured Systems)
REM Fast startup for development/daily use
REM ============================================================

setlocal EnableDelayedExpansion
color 0B
title JARVIS AI - Quick Start

echo.
echo ============================================================
echo           JARVIS AI - QUICK START MODE
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/5] Checking Docker status...
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker is not running! Use JARVIS-LAUNCH-ALL.bat instead
    pause
    exit /b 1
)

echo [2/5] Activating Python environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo [3/5] Starting core services...
docker-compose up -d memory-db redis ollama brain-api

echo [4/5] Starting audio and UI services...
docker-compose up -d tts-service stt-service
cd ui && start /B npm start >nul 2>&1 && cd ..

echo [5/5] Health check...
timeout /t 10 /nobreak >nul
curl -f http://localhost:8080/health >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] JARVIS is ready!
    start "" "http://localhost:3000"
) else (
    echo [WARNING] Services starting, please wait...
)

echo.
echo Quick Start Complete!
echo Main Interface: http://localhost:3000
echo.
pause

endlocal