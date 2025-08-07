@echo off
REM ============================================================
REM JARVIS AI - STATUS CHECKER & HEALTH MONITOR
REM Real-time monitoring of all JARVIS services
REM ============================================================

setlocal EnableDelayedExpansion
color 0E
title JARVIS AI - Status Monitor

:MAIN_LOOP
cls
echo.
echo ============================================================
echo           JARVIS AI - REAL-TIME STATUS MONITOR
echo           Updated: %DATE% %TIME%
echo ============================================================
echo.

cd /d "%~dp0"

REM Check Docker status
echo [INFRASTRUCTURE STATUS]
echo ------------------------------------------------
docker info >nul 2>&1
if %errorLevel% equ 0 (
    echo Docker Engine:     [RUNNING]
) else (
    echo Docker Engine:     [STOPPED] - Start Docker Desktop
)

REM Check Python environment
if exist "venv\Scripts\python.exe" (
    echo Python Venv:       [READY]
) else (
    echo Python Venv:       [NOT FOUND] - Run full setup
)

echo.
echo [CONTAINER STATUS]
echo ------------------------------------------------
for %%s in (jarvis-brain-api jarvis-memory-db jarvis-redis jarvis-ollama jarvis-tts-service jarvis-stt-service jarvis-system-control jarvis-mcp-gateway) do (
    docker inspect %%s >nul 2>&1
    if !errorLevel! equ 0 (
        for /f "tokens=*" %%i in ('docker inspect --format="{{.State.Status}}" %%s 2^>nul') do (
            if "%%i"=="running" (
                echo %%s: [RUNNING]
            ) else (
                echo %%s: [%%i]
            )
        )
    ) else (
        echo %%s: [NOT FOUND]
    )
)

echo.
echo [SERVICE HEALTH CHECKS]
echo ------------------------------------------------

REM Brain API Health
curl -f -s http://localhost:8080/health >nul 2>&1
if %errorLevel% equ 0 (
    echo Brain API (8080):         [HEALTHY]
) else (
    echo Brain API (8080):         [DOWN/UNHEALTHY]
)

REM Frontend Health
curl -f -s http://localhost:3000 >nul 2>&1
if %errorLevel% equ 0 (
    echo Frontend UI (3000):       [HEALTHY]
) else (
    echo Frontend UI (3000):       [DOWN/STARTING]
)

REM TTS Service Health
curl -f -s http://localhost:5002/health >nul 2>&1
if %errorLevel% equ 0 (
    echo TTS Service (5002):       [HEALTHY]
) else (
    echo TTS Service (5002):       [DOWN/UNHEALTHY]
)

REM STT Service Health
curl -f -s http://localhost:5003/health >nul 2>&1
if %errorLevel% equ 0 (
    echo STT Service (5003):       [HEALTHY]
) else (
    echo STT Service (5003):       [DOWN/UNHEALTHY]
)

REM Ollama Health
curl -f -s http://localhost:11434/api/tags >nul 2>&1
if %errorLevel% equ 0 (
    echo Ollama LLM (11434):       [HEALTHY]
) else (
    echo Ollama LLM (11434):       [DOWN/LOADING]
)

REM Voice Bridge Health
curl -f -s http://localhost:3001 >nul 2>&1
if %errorLevel% equ 0 (
    echo Voice Bridge (3001):      [HEALTHY]
) else (
    echo Voice Bridge (3001):      [DOWN/OPTIONAL]
)

echo.
echo [RESOURCE USAGE]
echo ------------------------------------------------

REM Docker stats for JARVIS containers
for /f "skip=1 tokens=1,3,4" %%a in ('docker stats jarvis-brain-api jarvis-memory-db jarvis-redis --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2^>nul') do (
    echo %%a: CPU=%%b MEM=%%c
)

echo.
echo [PORT USAGE]
echo ------------------------------------------------
set "JARVIS_PORTS=3000 3001 5002 5003 5004 5005 5006 5007 5432 6379 8080 8081 11434"
for %%p in (%JARVIS_PORTS%) do (
    netstat -an | findstr :%%p | findstr LISTENING >nul 2>&1
    if !errorLevel! equ 0 (
        echo Port %%p: [IN USE]
    ) else (
        echo Port %%p: [FREE]
    )
)

echo.
echo [RECENT LOGS - Last 5 Lines]
echo ------------------------------------------------
docker logs --tail 5 jarvis-brain-api 2>nul | findstr /V "INFO.*GET /health"
if %errorLevel% neq 0 echo No recent brain-api logs

echo.
echo ============================================================
echo [R] Refresh   [L] View Logs   [S] Start Services   [Q] Quit
echo ============================================================

choice /C RLSQ /N /T 10 /D R /M ""
if %errorLevel% equ 1 goto MAIN_LOOP
if %errorLevel% equ 2 goto VIEW_LOGS
if %errorLevel% equ 3 goto START_SERVICES
if %errorLevel% equ 4 goto QUIT

:VIEW_LOGS
cls
echo Select service to view logs:
echo 1. Brain API
echo 2. TTS Service  
echo 3. STT Service
echo 4. All Services
echo 5. Back to Status

choice /C 12345 /N
if %errorLevel% equ 1 docker logs -f jarvis-brain-api
if %errorLevel% equ 2 docker logs -f jarvis-tts-service
if %errorLevel% equ 3 docker logs -f jarvis-stt-service
if %errorLevel% equ 4 docker-compose logs -f
if %errorLevel% equ 5 goto MAIN_LOOP

goto MAIN_LOOP

:START_SERVICES
echo Starting JARVIS services...
docker-compose up -d
timeout /t 5 /nobreak >nul
goto MAIN_LOOP

:QUIT
echo Exiting JARVIS Status Monitor...
endlocal
exit /b 0