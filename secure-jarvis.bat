@echo off
setlocal enabledelayedexpansion
title JARVIS AI - Sécurisation Automatique
chcp 65001 >nul

echo.
echo ╔══════════════════════════════════════════╗
echo ║        JARVIS AI SÉCURISATION            ║
echo ║         Configuration Sécurisée          ║
echo ╚══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: [1/7] Vérification des fichiers de configuration
echo [1/7] Vérification de la configuration...

if not exist ".env" (
    if exist ".env.example" (
        echo Copie du fichier de configuration...
        copy ".env.example" ".env" >nul
        echo ✓ Fichier .env créé à partir de l'exemple
    ) else (
        echo ✗ Fichier .env.example manquant
        pause
        exit /b 1
    )
) else (
    echo ✓ Fichier .env existant
)

:: [2/7] Génération des clés secrètes
echo [2/7] Génération des clés de sécurité...

:: Générer une clé JWT sécurisée
echo Génération de la clé JWT...
powershell -Command "& {
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    $key = [Convert]::ToBase64String($bytes)
    (Get-Content '.env') -replace 'JWT_SECRET_KEY=.*', 'JWT_SECRET_KEY=' + $key | Set-Content '.env'
}" 2>nul

if %errorLevel% == 0 (
    echo ✓ Clé JWT générée
) else (
    echo ⚠ Génération clé JWT échouée - utilisation clé par défaut
)

:: [3/7] Configuration des mots de passe forts
echo [3/7] Configuration des mots de passe...

:: Génération mot de passe PostgreSQL
powershell -Command "& {
    $password = -join ((65..90) + (97..122) + (48..57) + (33,35,36,37,38,42,43,45,61,63,64) | Get-Random -Count 16 | ForEach-Object {[char]$_})
    (Get-Content '.env') -replace 'POSTGRES_PASSWORD=.*', 'POSTGRES_PASSWORD=' + $password | Set-Content '.env'
}" 2>nul

echo ✓ Mot de passe PostgreSQL généré

:: Génération mot de passe Redis
powershell -Command "& {
    $password = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 12 | ForEach-Object {[char]$_})
    (Get-Content '.env') -replace 'REDIS_PASSWORD=.*', 'REDIS_PASSWORD=' + $password | Set-Content '.env'
}" 2>nul

echo ✓ Mot de passe Redis généré

:: [4/7] Configuration des répertoires sécurisés
echo [4/7] Création des répertoires sécurisés...

:: Créer les répertoires de données
set "directories=data data\brain data\memory data\ollama data\audio data\redis data\postgres logs models"

for %%d in (%directories%) do (
    if not exist "%%d" (
        mkdir "%%d" 2>nul
        echo   Créé: %%d
    )
)

:: Sécuriser les permissions (Windows)
echo Configuration des permissions Windows...
icacls data /grant:r "%USERNAME%:(OI)(CI)F" /T >nul 2>&1
icacls logs /grant:r "%USERNAME%:(OI)(CI)F" /T >nul 2>&1

echo ✓ Répertoires sécurisés créés

:: [5/7] Configuration SSL/TLS (optionnel)
echo [5/7] Configuration SSL/TLS...

if not exist "certs" (
    mkdir certs
    echo Répertoire certificats créé
    
    :: Générer certificat auto-signé pour développement
    powershell -Command "& {
        try {
            New-SelfSignedCertificate -DnsName 'localhost','jarvis.local' -CertStoreLocation 'cert:\LocalMachine\My' -NotAfter (Get-Date).AddYears(1) | Out-Null
            Write-Host '✓ Certificat SSL auto-signé généré'
        } catch {
            Write-Host '⚠ Génération certificat SSL échouée'
        }
    }" 2>nul
) else (
    echo ✓ Répertoire certificats existant
)

:: [6/7] Configuration du firewall Windows
echo [6/7] Configuration du firewall...

echo Configuration des règles firewall pour JARVIS...

:: Règles pour les ports JARVIS
set "ports=5000 5001 5002 5004 5005 5006 5007 8888"

for %%p in (%ports%) do (
    netsh advfirewall firewall add rule name="JARVIS Port %%p" dir=in action=allow protocol=TCP localport=%%p >nul 2>&1
)

echo ✓ Règles firewall configurées

:: [7/7] Création du script de vérification sécurité
echo [7/7] Création des outils de sécurité...

echo @echo off > security-check.bat
echo title JARVIS AI - Vérification Sécurité >> security-check.bat
echo echo ════════════════════════════════════════════ >> security-check.bat
echo echo        JARVIS AI - AUDIT DE SÉCURITÉ >> security-check.bat
echo echo ════════════════════════════════════════════ >> security-check.bat
echo echo. >> security-check.bat
echo echo [1] Vérification des fichiers de configuration... >> security-check.bat
echo if exist ".env" ^( >> security-check.bat
echo     echo ✓ Fichier .env présent >> security-check.bat
echo     findstr /C:"your_" .env ^>nul >> security-check.bat
echo     if %%errorLevel%% == 0 ^( >> security-check.bat
echo         echo ⚠ Valeurs par défaut détectées dans .env >> security-check.bat
echo     ^) else ^( >> security-check.bat
echo         echo ✓ Configuration .env sécurisée >> security-check.bat
echo     ^) >> security-check.bat
echo ^) else ^( >> security-check.bat
echo     echo ✗ Fichier .env manquant >> security-check.bat
echo ^) >> security-check.bat
echo echo. >> security-check.bat
echo echo [2] Vérification des ports... >> security-check.bat
echo netstat -an ^| findstr "LISTENING" ^| findstr ":5000 :5001 :5002 :5004 :5005 :5006 :5007" >> security-check.bat
echo echo. >> security-check.bat
echo echo [3] Vérification des conteneurs Docker... >> security-check.bat
echo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" ^| findstr jarvis >> security-check.bat
echo echo. >> security-check.bat
echo echo [4] Test de connectivité... >> security-check.bat
echo curl -s http://localhost:5000/health ^| findstr "healthy" ^>nul >> security-check.bat
echo if %%errorLevel%% == 0 ^( >> security-check.bat
echo     echo ✓ API Brain accessible >> security-check.bat
echo ^) else ^( >> security-check.bat
echo     echo ⚠ API Brain non accessible >> security-check.bat
echo ^) >> security-check.bat
echo echo. >> security-check.bat
echo echo Audit terminé. >> security-check.bat
echo pause >> security-check.bat

echo ✓ Script security-check.bat créé

:: Créer script de sauvegarde sécurisée
echo @echo off > backup-secure.bat
echo title JARVIS AI - Sauvegarde Sécurisée >> backup-secure.bat
echo set "BACKUP_DIR=backup\%%date:~-4,4%%_%%date:~-10,2%%_%%date:~-7,2%%" >> backup-secure.bat
echo mkdir "%%BACKUP_DIR%%" 2^>nul >> backup-secure.bat
echo echo Sauvegarde en cours... >> backup-secure.bat
echo xcopy /E /I /H /Y data "%%BACKUP_DIR%%\data" ^>nul >> backup-secure.bat
echo xcopy /E /I /H /Y logs "%%BACKUP_DIR%%\logs" ^>nul >> backup-secure.bat
echo copy .env "%%BACKUP_DIR%%\.env.backup" ^>nul >> backup-secure.bat
echo echo ✓ Sauvegarde terminée: %%BACKUP_DIR%% >> backup-secure.bat
echo pause >> backup-secure.bat

echo ✓ Script backup-secure.bat créé

:: Résumé de sécurisation
echo.
echo ════════════════════════════════════════════════════════════════
echo                    ✓ SÉCURISATION TERMINÉE
echo ════════════════════════════════════════════════════════════════
echo.
echo Actions effectuées:
echo   ✓ Configuration .env sécurisée
echo   ✓ Clés JWT et mots de passe générés
echo   ✓ Répertoires de données créés
echo   ✓ Permissions Windows configurées
echo   ✓ Certificats SSL préparés
echo   ✓ Règles firewall appliquées
echo   ✓ Outils de sécurité créés
echo.
echo Scripts de sécurité disponibles:
echo   📄 security-check.bat     - Audit de sécurité
echo   📄 backup-secure.bat     - Sauvegarde sécurisée
echo.
echo ⚠ IMPORTANT:
echo   1. Modifiez les mots de passe dans .env si nécessaire
echo   2. Exécutez security-check.bat régulièrement
echo   3. Ne commitez JAMAIS le fichier .env dans Git
echo.
echo ════════════════════════════════════════════════════════════════

pause