@echo off
:: 🔐 JARVIS AI 2025 - Générateur de Secrets Sécurisés (Windows)
:: Script pour générer des mots de passe et secrets robustes

setlocal enabledelayedexpansion

:: Configuration
set ENV_FILE=.env
set ENV_EXAMPLE=.env.example
set BACKUP_DIR=backups\env

echo.
echo ╔════════════════════════════════════════╗
echo ║       🔐 JARVIS AI 2025 SECRETS       ║
echo ║      Générateur de Mots de Passe      ║
echo ╚════════════════════════════════════════╝
echo.

:: Vérification des prérequis
echo [✓] Vérification des prérequis...

:: Vérifier PowerShell
powershell -Command "Get-Host" >nul 2>&1
if errorlevel 1 (
    echo [✗] PowerShell requis mais non trouvé
    pause
    exit /b 1
)

:: Vérifier le fichier .env.example
if not exist "%ENV_EXAMPLE%" (
    echo [✗] Fichier %ENV_EXAMPLE% non trouvé. Exécutez ce script depuis la racine du projet.
    pause
    exit /b 1
)

:: Sauvegarder le fichier .env existant
if exist "%ENV_FILE%" (
    echo [✓] Sauvegarde du fichier .env existant...
    if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set mydate=%%c%%a%%b
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do set mytime=%%a%%b
    set mytime=!mytime: =!
    copy "%ENV_FILE%" "%BACKUP_DIR%\env_backup_!mydate!_!mytime!.bak" >nul
    echo [✓] Sauvegarde créée dans %BACKUP_DIR%
)

:: Génération des secrets
echo [✓] Génération des secrets sécurisés...

:: Copier le fichier exemple
copy "%ENV_EXAMPLE%" "%ENV_FILE%" >nul

:: Générer les secrets avec PowerShell
powershell -Command "$postgres_password = [System.Web.Security.Membership]::GeneratePassword(32, 8); $jwt_secret = -join ((1..128) | ForEach {'{0:X}' -f (Get-Random -Max 16)}); $redis_password = [System.Web.Security.Membership]::GeneratePassword(24, 6); $admin_password = [System.Web.Security.Membership]::GeneratePassword(20, 5); $jarvis_password = [System.Web.Security.Membership]::GeneratePassword(20, 5); (Get-Content '.env') -replace 'CHANGEME_STRONG_PASSWORD_HERE', $postgres_password -replace 'CHANGEME_GENERATE_STRONG_JWT_SECRET', $jwt_secret -replace 'CHANGEME_REDIS_PASSWORD', $redis_password -replace 'CHANGEME_ADMIN_PASSWORD', $admin_password -replace 'CHANGEME_JARVIS_PASSWORD', $jarvis_password | Set-Content '.env'"

:: Validation
echo [✓] Validation du fichier .env...
findstr /C:"CHANGEME_" "%ENV_FILE%" >nul
if not errorlevel 1 (
    echo [✗] Certains secrets n'ont pas été générés correctement!
    findstr /C:"CHANGEME_" "%ENV_FILE%"
    pause
    exit /b 1
)

:: Mise à jour .gitignore
if not exist ".gitignore" (
    echo. > .gitignore
)

findstr /C:".env" .gitignore >nul
if errorlevel 1 (
    echo. >> .gitignore
    echo # Environment variables - NEVER commit secrets! >> .gitignore
    echo .env >> .gitignore
    echo [✓] .env ajouté à .gitignore
)

:: Affichage des informations de sécurité
echo.
echo ╔════════════════════════════════════════╗
echo ║           🛡️  SÉCURITÉ INFO           ║
echo ╚════════════════════════════════════════╝
echo.
echo ✓ Fichier .env créé avec des secrets robustes
echo ✓ Mots de passe générés avec PowerShell
echo ✓ JWT Secret de 128 caractères hexadécimaux
echo ✓ Mots de passe système de 20-32 caractères
echo.
echo ⚠️ IMPORTANT - Actions de sécurité requises:
echo   1. Vérifiez le fichier .env généré
echo   2. Ajustez les domaines CORS pour la production
echo   3. Ne commitez JAMAIS le fichier .env
echo   4. Partagez les secrets de manière sécurisée
echo   5. Changez les secrets régulièrement
echo.

echo [✓] Génération terminée avec succès!
echo.
pause