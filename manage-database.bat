@echo off
REM JARVIS Database Management Script for Windows
REM Comprehensive database administration tool

title JARVIS Database Management

echo.
echo ==========================================
echo    JARVIS AI Database Management
echo ==========================================
echo.

if "%1"=="" goto :menu
if "%1"=="help" goto :help
if "%1"=="init" goto :init
if "%1"=="backup" goto :backup
if "%1"=="restore" goto :restore
if "%1"=="health" goto :health
if "%1"=="schedule" goto :schedule
if "%1"=="retention" goto :retention
if "%1"=="service" goto :service
if "%1"=="cli" goto :cli
goto :help

:menu
echo Choose an operation:
echo.
echo 1. Initialize Database
echo 2. Create Backup
echo 3. Health Check
echo 4. Start Backup Service
echo 5. CLI Interface
echo 6. View Logs
echo 7. Help
echo 8. Exit
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto :init
if "%choice%"=="2" goto :backup
if "%choice%"=="3" goto :health
if "%choice%"=="4" goto :service
if "%choice%"=="5" goto :cli
if "%choice%"=="6" goto :logs
if "%choice%"=="7" goto :help
if "%choice%"=="8" goto :exit
echo Invalid choice. Please try again.
goto :menu

:init
echo.
echo ============================================
echo    Initializing JARVIS Database
echo ============================================
echo.
python database\scripts\init_database.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Database initialization failed!
    pause
    goto :menu
)
echo.
echo Database initialization completed successfully!
pause
goto :menu

:backup
echo.
echo ============================================
echo    Creating Database Backup
echo ============================================
echo.
echo Choose backup type:
echo 1. Full backup (all services)
echo 2. PostgreSQL only
echo 3. Redis only
echo 4. ChromaDB only
echo.
set /p backup_choice="Enter choice (1-4): "

if "%backup_choice%"=="1" (
    python -m database.cli.jarvis_db_cli backup create --service all --type full
) else if "%backup_choice%"=="2" (
    python -m database.cli.jarvis_db_cli backup create --service postgresql --type full
) else if "%backup_choice%"=="3" (
    python -m database.cli.jarvis_db_cli backup create --service redis --type full
) else if "%backup_choice%"=="4" (
    python -m database.cli.jarvis_db_cli backup create --service chromadb --type full
) else (
    echo Invalid choice.
    pause
    goto :backup
)

echo.
echo Backup operation completed!
pause
goto :menu

:restore
echo.
echo ============================================
echo    Restoring from Backup
echo ============================================
echo.
echo WARNING: This will overwrite existing data!
set /p confirm="Are you sure you want to continue? (y/N): "
if /i not "%confirm%"=="y" goto :menu

echo.
echo Choose service to restore:
echo 1. PostgreSQL
echo 2. Redis
echo 3. ChromaDB
echo.
set /p restore_choice="Enter choice (1-3): "

set /p backup_path="Enter full path to backup file: "

if "%restore_choice%"=="1" (
    python -m database.cli.jarvis_db_cli backup restore --service postgresql "%backup_path%"
) else if "%restore_choice%"=="2" (
    python -m database.cli.jarvis_db_cli backup restore --service redis "%backup_path%"
) else if "%restore_choice%"=="3" (
    python -m database.cli.jarvis_db_cli backup restore --service chromadb "%backup_path%"
) else (
    echo Invalid choice.
    pause
    goto :restore
)

echo.
echo Restore operation completed!
pause
goto :menu

:health
echo.
echo ============================================
echo    Database Health Check
echo ============================================
echo.
python -m database.cli.jarvis_db_cli health check
echo.
pause
goto :menu

:schedule
echo.
echo ============================================
echo    Backup Schedule Management
echo ============================================
echo.
echo Choose operation:
echo 1. View schedule status
echo 2. Start scheduler
echo 3. Manual backup
echo.
set /p sched_choice="Enter choice (1-3): "

if "%sched_choice%"=="1" (
    python -m database.cli.jarvis_db_cli schedule status
) else if "%sched_choice%"=="2" (
    echo Starting backup scheduler...
    echo Press Ctrl+C to stop
    python -m database.cli.jarvis_db_cli schedule start
) else if "%sched_choice%"=="3" (
    python -m database.cli.jarvis_db_cli backup create --service all --type full
) else (
    echo Invalid choice.
    pause
    goto :schedule
)

echo.
pause
goto :menu

:retention
echo.
echo ============================================
echo    Data Retention Management
echo ============================================
echo.
echo Choose operation:
echo 1. View retention statistics
echo 2. Preview cleanup (dry run)
echo 3. Execute cleanup
echo.
set /p ret_choice="Enter choice (1-3): "

if "%ret_choice%"=="1" (
    python -m database.cli.jarvis_db_cli retention stats
) else if "%ret_choice%"=="2" (
    python -m database.cli.jarvis_db_cli retention cleanup --dry-run
) else if "%ret_choice%"=="3" (
    echo WARNING: This will permanently delete old data!
    set /p confirm="Continue? (y/N): "
    if /i "%confirm%"=="y" (
        python -m database.cli.jarvis_db_cli retention cleanup
    )
) else (
    echo Invalid choice.
    pause
    goto :retention
)

echo.
pause
goto :menu

:service
echo.
echo ============================================
echo    Database Backup Service
echo ============================================
echo.
echo Choose operation:
echo 1. Start service (daemon mode)
echo 2. Check service status
echo 3. Test backup
echo 4. Health check
echo 5. Stop service (if running)
echo.
set /p serv_choice="Enter choice (1-5): "

if "%serv_choice%"=="1" (
    echo Starting backup service...
    echo Press Ctrl+C to stop
    python database\scripts\backup_service.py
) else if "%serv_choice%"=="2" (
    python database\scripts\backup_service.py --status
) else if "%serv_choice%"=="3" (
    python database\scripts\backup_service.py --test-backup
) else if "%serv_choice%"=="4" (
    python database\scripts\backup_service.py --health-check
) else if "%serv_choice%"=="5" (
    echo Stopping service...
    taskkill /f /im python.exe /fi "WINDOWTITLE eq *backup_service*" 2>nul
    echo Service stop attempted.
) else (
    echo Invalid choice.
    pause
    goto :service
)

echo.
pause
goto :menu

:cli
echo.
echo ============================================
echo    Database CLI Interface
echo ============================================
echo.
echo Entering interactive CLI mode...
echo Type 'exit' to return to main menu
echo.
python -m database.cli.jarvis_db_cli
goto :menu

:logs
echo.
echo ============================================
echo    Database Logs
echo ============================================
echo.
if exist "logs\backup_service.log" (
    echo Recent backup service logs:
    echo ----------------------------------------
    powershell "Get-Content logs\backup_service.log -Tail 20"
) else (
    echo No backup service logs found.
)

echo.
if exist "logs\jarvis.log" (
    echo Recent application logs:
    echo ----------------------------------------
    powershell "Get-Content logs\jarvis.log -Tail 10"
) else (
    echo No application logs found.
)

echo.
pause
goto :menu

:help
echo.
echo ==========================================
echo    JARVIS Database Management Help
echo ==========================================
echo.
echo Usage: %0 [command]
echo.
echo Commands:
echo   init         Initialize database with schema and data
echo   backup       Create database backups  
echo   restore      Restore from backup files
echo   health       Run health checks on all services
echo   schedule     Manage backup scheduling
echo   retention    Manage data retention policies
echo   service      Control backup service daemon
echo   cli          Launch interactive CLI
echo   help         Show this help message
echo.
echo Interactive Mode:
echo   Run without arguments to enter interactive menu
echo.
echo Examples:
echo   %0 init                    # Initialize database
echo   %0 backup                  # Interactive backup
echo   %0 health                  # Check system health
echo   %0 service                 # Start backup service
echo.
echo For detailed CLI options:
echo   python -m database.cli.jarvis_db_cli --help
echo.

if "%1"=="help" exit /b 0
pause
goto :menu

:exit
echo.
echo Goodbye! JARVIS Database Management exiting...
exit /b 0

:error
echo.
echo ERROR: An error occurred during operation.
echo Check logs for more details.
pause
goto :menu