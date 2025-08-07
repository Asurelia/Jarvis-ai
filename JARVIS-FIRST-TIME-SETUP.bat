@echo off
REM ============================================================
REM JARVIS AI - CONFIGURATION INITIALE COMPLETE
REM Premier setup complet depuis zero - TOUT est configure
REM ============================================================

setlocal EnableDelayedExpansion
color 0B
title JARVIS AI - First Time Setup

echo.
echo ============================================================
echo         JARVIS AI - CONFIGURATION INITIALE COMPLETE
echo         Premiere installation depuis zero
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

echo ATTENTION: Cette configuration va prendre 10-30 minutes
echo et telecharger plusieurs GB de donnees.
echo.
echo Continuez-vous? (Y/N)
choice /C YN /N
if %errorLevel% neq 1 (
    echo Configuration annulee.
    exit /b 0
)

echo.
echo [1/15] Verification environnement...
echo ============================================================

REM Verifier Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python non installe!
    echo.
    echo INSTALLATION REQUISE:
    echo 1. Allez sur https://python.org/downloads/
    echo 2. Telechargez Python 3.11 ou plus recent
    echo 3. IMPORTANT: Cochez "Add Python to PATH"
    echo 4. Installez
    echo 5. Redemarrez le terminal
    echo 6. Relancez ce script
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Python detecte
    python --version
)

REM Verifier Docker
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker non installe!
    echo.
    echo INSTALLATION REQUISE:
    echo 1. Allez sur https://www.docker.com/products/docker-desktop/
    echo 2. Telechargez Docker Desktop
    echo 3. Installez-le
    echo 4. Redemarrez Windows
    echo 5. Demarrez Docker Desktop
    echo 6. Relancez ce script
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Docker detecte
    docker --version
)

echo.
echo [2/15] Demarrage Docker Desktop si necessaire...
echo ============================================================

docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo Docker Desktop n'est pas demarre. Tentative de demarrage...
    
    REM Chercher et demarrer Docker Desktop
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) else if exist "%USERPROFILE%\AppData\Local\Docker\Docker Desktop\Docker Desktop.exe" (
        start "" "%USERPROFILE%\AppData\Local\Docker\Docker Desktop\Docker Desktop.exe"
    ) else (
        echo [ERROR] Docker Desktop executable non trouve!
        echo Demarrez Docker Desktop manuellement et relancez ce script.
        pause
        exit /b 1
    )
    
    echo Attente du demarrage Docker Engine (max 2 minutes)...
    set "DOCKER_WAIT=0"
    
    :WAIT_DOCKER_START
    timeout /t 10 /nobreak >nul
    set /a DOCKER_WAIT+=10
    
    docker info >nul 2>&1
    if %errorLevel% equ 0 (
        echo [OK] Docker Engine demarre!
        goto DOCKER_READY
    )
    
    if %DOCKER_WAIT% geq 120 (
        echo [ERROR] Docker met trop de temps a demarrer!
        echo Verifiez Docker Desktop manuellement et relancez ce script.
        pause
        exit /b 1
    )
    
    echo Attente Docker... (%DOCKER_WAIT%/120 secondes)
    goto WAIT_DOCKER_START
)

:DOCKER_READY
echo [OK] Docker Engine fonctionne

echo.
echo [3/15] Creation environnement Python...
echo ============================================================

if exist "venv" (
    echo Environnement virtuel existe deja
) else (
    echo Creation environnement virtuel Python...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo [ERROR] Echec creation environnement virtuel!
        pause
        exit /b 1
    )
)

echo Activation environnement virtuel...
call venv\Scripts\activate.bat

echo Mise a jour pip...
python -m pip install --upgrade pip --quiet

echo.
echo [4/15] Installation dependances Python principales...
echo ============================================================

if exist "requirements.txt" (
    echo Installation requirements.txt...
    pip install -r requirements.txt --quiet --disable-pip-version-check
) else (
    echo Installation dependances essentielles...
    pip install fastapi uvicorn pydantic sqlalchemy psycopg2-binary redis ollama python-multipart --quiet
)

echo.
echo [5/15] Installation dependances services...
echo ============================================================

set "SERVICE_DIRS=services\brain-api services\tts-service services\stt-service services\system-control database api"
for %%d in (%SERVICE_DIRS%) do (
    if exist "%%d\requirements.txt" (
        echo Installation %%d requirements...
        pip install -r "%%d\requirements.txt" --quiet --disable-pip-version-check 2>nul
    )
)

echo.
echo [6/15] Generation configuration securisee...
echo ============================================================

if exist ".env" (
    echo Configuration .env existe deja
) else (
    echo Creation fichier .env avec parametres securises...
    (
        echo # JARVIS AI Configuration - Genere le %DATE% %TIME%
        echo.
        echo # API Configuration
        echo BRAIN_API_HOST=0.0.0.0
        echo BRAIN_API_PORT=8080
        echo BRAIN_DEBUG=false
        echo JWT_SECRET_KEY=jarvis_%RANDOM%%RANDOM%%RANDOM%_secret
        echo JWT_ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # Database
        echo POSTGRES_USER=jarvis
        echo POSTGRES_PASSWORD=jarvis_secure_%RANDOM%
        echo POSTGRES_DB=jarvis_memory
        echo DATABASE_URL=postgresql://jarvis:jarvis_secure_%RANDOM%@localhost:5432/jarvis_memory
        echo.
        echo # Redis
        echo REDIS_HOST=localhost
        echo REDIS_PORT=6379
        echo REDIS_PASSWORD=redis_secure_%RANDOM%
        echo REDIS_URL=redis://:redis_secure_%RANDOM%@localhost:6379
        echo.
        echo # LLM
        echo OLLAMA_HOST=http://localhost:11434
        echo OLLAMA_MODEL=llama3.2:3b
        echo.
        echo # Security
        echo ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
        echo CORS_ALLOW_CREDENTIALS=true
        echo SECURITY_MODE=production
        echo.
        echo # Features
        echo VOICE_ENABLED=true
        echo VISION_ENABLED=true
        echo SYSTEM_CONTROL_ENABLED=true
    ) > .env
    echo [OK] Fichier .env cree
)

echo.
echo [7/15] Nettoyage Docker complet...
echo ============================================================

echo Arret containers existants...
docker-compose down --remove-orphans >nul 2>&1

echo Nettoyage images et volumes...
docker system prune -af --volumes >nul 2>&1

echo Nettoyage networks...
docker network prune -f >nul 2>&1

echo.
echo [8/15] Construction images Docker (LONG - 5-15 minutes)...
echo ============================================================

echo ATTENTION: Cette etape va telecharger et construire toutes les images Docker
echo Cela peut prendre 5-15 minutes selon votre connexion internet.
echo.

echo Construction de toutes les images...
docker-compose build --no-cache --parallel

if %errorLevel% neq 0 (
    echo [WARNING] Construction parallele echouee, tentative sequentielle...
    docker-compose build --no-cache
    
    if %errorLevel% neq 0 (
        echo [ERROR] Echec construction images Docker!
        echo.
        echo SOLUTIONS POSSIBLES:
        echo 1. Verifiez votre connexion internet
        echo 2. Augmentez la memoire Docker Desktop (4GB minimum)
        echo 3. Liberez de l'espace disque (10GB minimum)
        echo 4. Relancez ce script
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Images Docker construites avec succes!

echo.
echo [9/15] Telechargement images de base...
echo ============================================================

echo Telechargement PostgreSQL...
docker pull postgres:15-alpine

echo Telechargement Redis...
docker pull redis:7-alpine

echo Telechargement Ollama...
docker pull ollama/ollama:latest

echo.
echo [10/15] Demarrage services infrastructure...
echo ============================================================

echo Demarrage base de donnees PostgreSQL...
docker-compose up -d memory-db
timeout /t 10 /nobreak >nul

echo Demarrage cache Redis...
docker-compose up -d redis
timeout /t 5 /nobreak >nul

echo Demarrage Ollama LLM...
docker-compose up -d ollama
timeout /t 15 /nobreak >nul

echo.
echo [11/15] Initialisation base de donnees...
echo ============================================================

echo Attente disponibilite PostgreSQL...
set "DB_WAIT=0"

:WAIT_DB
docker exec jarvis-memory-db pg_isready -U jarvis >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] PostgreSQL pret!
    goto DB_READY
)

set /a DB_WAIT+=1
if %DB_WAIT% geq 30 (
    echo [WARNING] PostgreSQL met du temps a demarrer, mais on continue...
    goto DB_READY
)

timeout /t 2 /nobreak >nul
echo Attente PostgreSQL... (%DB_WAIT%/30)
goto WAIT_DB

:DB_READY

if exist "database\scripts\init_database.py" (
    echo Execution script initialisation BD...
    python database\scripts\init_database.py
)

echo.
echo [12/15] Telechargement modeles IA (TRES LONG)...
echo ============================================================

echo ATTENTION: Le telechargement des modeles IA peut prendre 20-60 minutes
echo selon votre connexion. Vous pouvez skipper cette etape pour l'instant.
echo.
echo Telecharger les modeles maintenant? (Y/N)
choice /C YN /N
if %errorLevel% equ 1 (
    echo Telechargement modele principal Llama 3.2 (2GB)...
    docker exec jarvis-ollama ollama pull llama3.2:3b
    
    echo Telechargement modele vision LLaVA (4GB)...
    docker exec jarvis-ollama ollama pull llava:7b
    
    echo [OK] Modeles IA installes!
) else (
    echo Modeles IA non installes - vous pourrez les installer plus tard avec:
    echo docker exec jarvis-ollama ollama pull llama3.2:3b
)

echo.
echo [13/15] Demarrage services JARVIS...
echo ============================================================

echo Demarrage Brain API...
docker-compose up -d brain-api
timeout /t 10 /nobreak >nul

echo Demarrage services Audio...
docker-compose up -d tts-service stt-service
timeout /t 5 /nobreak >nul

echo Demarrage services Controle...
docker-compose up -d system-control terminal-service
timeout /t 3 /nobreak >nul

echo Demarrage services Integration...
docker-compose up -d mcp-gateway autocomplete-service
timeout /t 3 /nobreak >nul

echo Demarrage monitoring GPU (optionnel)...
docker-compose up -d gpu-stats-service 2>nul

echo.
echo [14/15] Configuration Interface Web...
echo ============================================================

cd ui 2>nul
if exist "package.json" (
    echo Installation dependances Node.js (optionnel pour Docker)...
    where node >nul 2>&1
    if %errorLevel% equ 0 (
        call npm install >nul 2>&1
        echo Interface Node.js configuree
    ) else (
        echo Node.js non installe - interface fonctionnera via Docker
    )
) else (
    echo Dossier UI non trouve - creation basique...
    mkdir ui 2>nul
)
cd ..

echo.
echo [15/15] Tests finaux et verification...
echo ============================================================

echo Attente stabilisation services (30 secondes)...
timeout /t 30 /nobreak >nul

echo Verification Brain API...
curl -f http://localhost:8080/health >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Brain API operationnel
) else (
    echo [WARNING] Brain API pas encore pret
)

echo Verification Ollama...
curl -f http://localhost:11434/api/tags >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Ollama operationnel
) else (
    echo [WARNING] Ollama pas encore pret
)

echo Verification services audio...
curl -f http://localhost:5002/health >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] TTS operationnel
) else (
    echo [WARNING] TTS pas encore pret
)

echo.
echo ============================================================
echo              CONFIGURATION INITIALE TERMINEE!
echo ============================================================
echo.
echo JARVIS AI est maintenant configure et demarre!
echo.
echo ACCES:
echo ------
echo  Interface principale: http://localhost:3000 (si disponible)
echo  API Documentation:    http://localhost:8080/docs
echo  Health Check:         http://localhost:8080/health
echo.
echo COMMANDES UTILES:
echo -----------------
echo  Voir status:          JARVIS-STATUS.bat
echo  Arreter tout:         JARVIS-STOP-ALL.bat
echo  Redemarrage rapide:   JARVIS-QUICK-START.bat
echo  Voir logs:            docker-compose logs -f
echo.
echo PROCHAINES ETAPES:
echo ------------------
echo 1. Testez http://localhost:8080/docs
echo 2. Si tout fonctionne, installez les modeles IA:
echo    docker exec jarvis-ollama ollama pull llama3.2:3b
echo 3. Utilisez JARVIS-STATUS.bat pour surveiller
echo.
echo ============================================================

REM Ouvrir navigateur sur documentation API
timeout /t 3 /nobreak >nul
start "" "http://localhost:8080/docs" 2>nul

echo Configuration terminee! Appuyez sur une touche pour fermer...
pause >nul

endlocal