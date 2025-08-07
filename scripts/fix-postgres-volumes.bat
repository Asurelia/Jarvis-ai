@echo off
echo ======================================
echo JARVIS AI - PostgreSQL Volume Fix
echo ======================================
echo.

echo [INFO] Stopping all services...
docker-compose down -v

echo [INFO] Removing PostgreSQL container and volumes...
docker container rm -f jarvis_memory_db 2>nul
docker volume rm jarvis-ai_postgres_data 2>nul

echo [INFO] Cleaning up old PostgreSQL data directory...
if exist "data\postgres" (
    rmdir /s /q "data\postgres"
    echo [INFO] Removed old postgres data directory
)

echo [INFO] Creating fresh data directories...
if not exist "data" mkdir "data"
if not exist "data\postgres" mkdir "data\postgres"

echo [INFO] Starting PostgreSQL with named volume...
docker-compose up -d memory-db

echo [INFO] Waiting for PostgreSQL to initialize...
timeout /t 30 /nobreak >nul

echo [INFO] Checking PostgreSQL status...
docker-compose logs memory-db

echo.
echo [SUCCESS] PostgreSQL volume fix completed!
echo The database is now using a named Docker volume for Windows compatibility.
echo.
pause