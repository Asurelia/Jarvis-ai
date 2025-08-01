@echo off
REM 🔒 Script de déploiement sécurisé JARVIS AI pour Windows
REM Ce script configure un environnement de déploiement local sécurisé

setlocal enabledelayedexpansion

REM Variables globales
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%\.."
set "LOG_FILE=%PROJECT_ROOT%\logs\jarvis-deploy.log"
set "DATA_DIR=%PROJECT_ROOT%\data"
set "SSL_DIR=%PROJECT_ROOT%\ssl"

REM Créer le répertoire de logs s'il n'existe pas
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

REM Fonction de logging
:log
echo [%date% %time%] %~1 >> "%LOG_FILE%"
echo %~1
goto :eof

:error
call :log "❌ ERREUR: %~1"
pause
exit /b 1

:success
call :log "✅ %~1"
goto :eof

:info
call :log "ℹ️  %~1"
goto :eof

:warning
call :log "⚠️  ATTENTION: %~1"
goto :eof

REM Vérifications préalables
:check_prerequisites
call :info "Vérification des prérequis..."

REM Vérifier Docker
docker --version >nul 2>&1
if !errorlevel! neq 0 (
    call :error "Docker n'est pas installé ou pas dans le PATH"
)

REM Vérifier Docker Compose
docker-compose --version >nul 2>&1
if !errorlevel! neq 0 (
    call :error "Docker Compose n'est pas installé ou pas dans le PATH"
)

REM Vérifier Python
python --version >nul 2>&1
if !errorlevel! neq 0 (
    call :error "Python n'est pas installé ou pas dans le PATH"
)

call :success "Prérequis validés"
goto :eof

REM Configuration des répertoires
:setup_directories
call :info "Configuration des répertoires..."

REM Créer les répertoires nécessaires
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%DATA_DIR%\brain" mkdir "%DATA_DIR%\brain"
if not exist "%DATA_DIR%\memory" mkdir "%DATA_DIR%\memory"
if not exist "%DATA_DIR%\ollama" mkdir "%DATA_DIR%\ollama"
if not exist "%DATA_DIR%\redis" mkdir "%DATA_DIR%\redis"
if not exist "%DATA_DIR%\postgres" mkdir "%DATA_DIR%\postgres"
if not exist "%DATA_DIR%\audio" mkdir "%DATA_DIR%\audio"

if not exist "%SSL_DIR%" mkdir "%SSL_DIR%"
if not exist "%PROJECT_ROOT%\logs\nginx" mkdir "%PROJECT_ROOT%\logs\nginx"
if not exist "%PROJECT_ROOT%\logs\brain" mkdir "%PROJECT_ROOT%\logs\brain"
if not exist "%PROJECT_ROOT%\logs\services" mkdir "%PROJECT_ROOT%\logs\services"

call :success "Répertoires configurés"
goto :eof

REM Génération des mots de passe sécurisés
:generate_passwords
call :info "Génération des mots de passe sécurisés..."

if not exist "%PROJECT_ROOT%\.env.security" (
    call :info "Lancement du générateur de mots de passe..."
    cd /d "%PROJECT_ROOT%"
    python scripts\generate-secure-passwords.py
    if !errorlevel! neq 0 (
        call :error "Échec de la génération des mots de passe"
    )
    call :success "Mots de passe générés"
) else (
    call :info "Fichier .env.security déjà présent"
)
goto :eof

REM Génération des certificats auto-signés
:generate_certificates
call :info "Génération des certificats auto-signés..."

if not exist "%SSL_DIR%\localhost.crt" (
    REM Utiliser PowerShell pour générer les certificats
    powershell -Command "& {
        $cert = New-SelfSignedCertificate -DnsName 'localhost', '127.0.0.1' -CertStoreLocation 'cert:\LocalMachine\My' -KeyUsage DigitalSignature, KeyEncipherment -Type SSLServerAuthentication -Subject 'CN=JARVIS Local'
        $pwd = ConvertTo-SecureString -String 'jarvis123' -Force -AsPlainText
        $path = '%SSL_DIR%\localhost.pfx'
        Export-PfxCertificate -Cert $cert -FilePath $path -Password $pwd
        
        # Exporter en format PEM
        openssl pkcs12 -in '%SSL_DIR%\localhost.pfx' -out '%SSL_DIR%\localhost.crt' -nokeys -passin pass:jarvis123 2>nul
        openssl pkcs12 -in '%SSL_DIR%\localhost.pfx' -out '%SSL_DIR%\localhost.key' -nocerts -nodes -passin pass:jarvis123 2>nul
    }"
    
    if exist "%SSL_DIR%\localhost.crt" (
        call :success "Certificats auto-signés générés"
    ) else (
        call :warning "Génération des certificats échouée, utilisation des certificats Docker"
    )
) else (
    call :info "Certificats déjà présents"
)
goto :eof

REM Configuration Windows Defender
:configure_defender
call :info "Configuration de Windows Defender..."

REM Ajouter des exclusions pour les performances
powershell -Command "Add-MpPreference -ExclusionPath '%PROJECT_ROOT%\data'" 2>nul
powershell -Command "Add-MpPreference -ExclusionPath '%PROJECT_ROOT%\logs'" 2>nul
powershell -Command "Add-MpPreference -ExclusionProcess 'docker.exe'" 2>nul
powershell -Command "Add-MpPreference -ExclusionProcess 'dockerd.exe'" 2>nul

call :success "Windows Defender configuré"
goto :eof

REM Validation de la configuration
:validate_config
call :info "Validation de la configuration..."

if not exist "%PROJECT_ROOT%\.env.security" (
    call :error "Fichier .env.security manquant. Relancez avec l'option passwords"
)

REM Charger et vérifier les variables
for /f "tokens=1,2 delims==" %%a in ('type "%PROJECT_ROOT%\.env.security" ^| findstr /v "^#"') do (
    set "%%a=%%b"
)

if "!JWT_SECRET_KEY!" == "" (
    call :error "JWT_SECRET_KEY manquant dans .env.security"
)

if "!SYSTEM_CONTROL_ADMIN_PASSWORD_HASH!" == "" (
    call :error "Hashs de mots de passe manquants dans .env.security"
)

call :success "Configuration validée"
goto :eof

REM Déploiement des services
:deploy_services
call :info "Déploiement des services..."

cd /d "%PROJECT_ROOT%"

REM Charger les variables d'environnement
if exist ".env.security" (
    for /f "tokens=1,2 delims==" %%a in ('type ".env.security" ^| findstr /v "^#"') do (
        set "%%a=%%b"
    )
)

REM Configuration pour développement local
set "CERTBOT_DOMAIN=localhost"
set "CERTBOT_EMAIL=admin@localhost"
set "ALLOWED_ORIGINS=http://localhost:3000,https://localhost:3000"
set "SECURITY_MODE=development"
set "TRUSTED_HOSTS=localhost,127.0.0.1"

REM Arrêter les services existants
call :info "Arrêt des services existants..."
docker-compose down --remove-orphans >nul 2>&1

REM Construire les images
call :info "Construction des images..."
docker-compose build --no-cache
if !errorlevel! neq 0 (
    call :error "Échec de construction des images"
)

REM Démarrer les services de base
call :info "Démarrage des services de base..."
docker-compose up -d redis memory-db
if !errorlevel! neq 0 (
    call :error "Échec du démarrage des services de base"
)

REM Attendre que les DB soient prêtes
call :info "Attente de la disponibilité des bases de données..."
timeout /t 30 /nobreak >nul

REM Démarrer tous les services
call :info "Démarrage de tous les services..."
docker-compose up -d
if !errorlevel! neq 0 (
    call :error "Échec du démarrage des services"
)

call :success "Services déployés"
goto :eof

REM Vérifications post-déploiement
:post_deploy_checks
call :info "Vérifications post-déploiement..."

REM Attendre que les services démarrent
call :info "Attente du démarrage complet des services..."
timeout /t 60 /nobreak >nul

REM Vérifier les services Docker
docker-compose ps | findstr "Up" >nul
if !errorlevel! equ 0 (
    call :success "Services Docker démarrés"
) else (
    call :warning "Certains services peuvent ne pas être démarrés"
)

REM Test des endpoints
curl -k -f http://localhost:5000/health >nul 2>&1
if !errorlevel! equ 0 (
    call :success "Health check réussi"
) else (
    call :warning "Health check échoué - services peut-être en cours de démarrage"
)

call :success "Vérifications terminées"
goto :eof

REM Affichage des informations
:display_info
echo.
echo =================================="
echo 🔒 JARVIS AI - DÉPLOIEMENT LOCAL SÉCURISÉ
echo ==================================
echo.
echo 🌐 URLs d'accès:
echo   - Interface: http://localhost:3000
echo   - API Brain: http://localhost:5000
echo   - Health: http://localhost:5000/health
echo.
echo 📁 Répertoires:
echo   - Données: %DATA_DIR%
echo   - Logs: %PROJECT_ROOT%\logs
echo   - SSL: %SSL_DIR%
echo.
echo 🔧 Commandes utiles:
echo   - Logs: docker-compose logs -f
echo   - Status: docker-compose ps
echo   - Arrêt: docker-compose down
echo   - Redémarrage: docker-compose restart
echo.
echo 🚨 Sécurité:
echo   - Changez les mots de passe par défaut
echo   - Surveillez les logs dans %PROJECT_ROOT%\logs
echo   - Utilisez HTTPS en production
echo ==================================
goto :eof

REM Sauvegarde
:do_backup
call :info "Sauvegarde des données..."

set "BACKUP_TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "BACKUP_TIMESTAMP=!BACKUP_TIMESTAMP: =0!"
set "BACKUP_DIR=%PROJECT_ROOT%\backups\jarvis_backup_!BACKUP_TIMESTAMP!"

if not exist "%PROJECT_ROOT%\backups" mkdir "%PROJECT_ROOT%\backups"
mkdir "!BACKUP_DIR!"

REM Arrêter temporairement les services
docker-compose stop

REM Copier les données
xcopy "%DATA_DIR%" "!BACKUP_DIR!\data\" /E /I /Q
if exist "%PROJECT_ROOT%\.env.security" copy "%PROJECT_ROOT%\.env.security" "!BACKUP_DIR!\"

REM Redémarrer les services
docker-compose start

call :success "Sauvegarde créée: !BACKUP_DIR!"
goto :eof

REM Menu principal
:main
set "ACTION=%~1"
if "!ACTION!" == "" set "ACTION=deploy"

call :info "🚀 JARVIS AI - Script de déploiement sécurisé Windows"

if "!ACTION!" == "deploy" (
    call :check_prerequisites
    call :setup_directories
    call :generate_passwords
    call :generate_certificates
    call :configure_defender
    call :validate_config
    call :deploy_services
    call :post_deploy_checks
    call :display_info
    call :success "🎉 Déploiement terminé avec succès!"
) else if "!ACTION!" == "passwords" (
    call :generate_passwords
) else if "!ACTION!" == "backup" (
    call :do_backup
) else if "!ACTION!" == "logs" (
    cd /d "%PROJECT_ROOT%"
    docker-compose logs -f
) else if "!ACTION!" == "status" (
    cd /d "%PROJECT_ROOT%"
    docker-compose ps
) else if "!ACTION!" == "stop" (
    cd /d "%PROJECT_ROOT%"
    docker-compose down
    call :success "Services arrêtés"
) else if "!ACTION!" == "restart" (
    cd /d "%PROJECT_ROOT%"
    docker-compose restart
    call :success "Services redémarrés"
) else (
    echo Usage: %~0 [action]
    echo Actions disponibles:
    echo   deploy     - Déploiement complet ^(défaut^)
    echo   passwords  - Génération des mots de passe seulement
    echo   backup     - Sauvegarde des données
    echo   logs       - Afficher les logs
    echo   status     - Statut des services
    echo   stop       - Arrêter les services
    echo   restart    - Redémarrer les services
    pause
    exit /b 1
)

pause
goto :eof

REM Point d'entrée
call :main %*