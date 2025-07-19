@echo off
REM 🪟 Script d'installation JARVIS pour Windows
setlocal enabledelayedexpansion

echo 🤖 Installation JARVIS Phase 2 pour Windows
echo ============================================

REM Couleurs pour l'affichage (Windows 10+)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Variables
set "ERRORS=0"
set "WARNINGS=0"

REM Fonctions utilitaires
:print_step
echo %BLUE%[INFO]%NC% %~1
goto :eof

:print_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
set /a WARNINGS+=1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
set /a ERRORS+=1
goto :eof

REM Vérification des commandes
:check_command
where %1 >nul 2>&1
if %errorlevel% equ 0 (
    call :print_success "%1 trouvé"
    exit /b 0
) else (
    call :print_warning "%1 non trouvé"
    exit /b 1
)

REM Vérification de Python
:check_python
call :print_step "Vérification de Python..."
call :check_command python
if %errorlevel% neq 0 (
    call :check_command python3
    if %errorlevel% neq 0 (
        call :print_error "Python non trouvé. Installez Python 3.11+ depuis python.org"
        exit /b 1
    ) else (
        set "PYTHON_CMD=python3"
    )
) else (
    set "PYTHON_CMD=python"
)

REM Vérifier la version de Python
%PYTHON_CMD% -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if %errorlevel% neq 0 (
    call :print_error "Python 3.11+ requis"
    exit /b 1
)

call :print_success "Python OK"
exit /b 0

REM Vérification de Node.js
:check_node
call :print_step "Vérification de Node.js et npm..."
call :check_command node
if %errorlevel% neq 0 (
    call :print_warning "Node.js non trouvé - interface web non disponible"
    call :print_warning "Installez Node.js depuis nodejs.org"
    exit /b 1
)

call :check_command npm
if %errorlevel% neq 0 (
    call :print_warning "npm non trouvé"
    exit /b 1
)

call :print_success "Node.js et npm OK"
exit /b 0

REM Installation des dépendances Python avec Chocolatey (optionnel)
:install_chocolatey_deps
call :print_step "Installation des dépendances avec Chocolatey..."
call :check_command choco
if %errorlevel% neq 0 (
    call :print_warning "Chocolatey non trouvé - installation manuelle requise"
    exit /b 1
)

choco install tesseract -y
call :print_success "Tesseract installé via Chocolatey"
exit /b 0

REM Installation d'Ollama
:install_ollama
call :print_step "Vérification d'Ollama..."
call :check_command ollama
if %errorlevel% equ 0 (
    call :print_success "Ollama déjà installé"
    goto :install_models
)

call :print_step "Téléchargement et installation d'Ollama..."
REM Télécharger Ollama pour Windows
powershell -Command "& {Invoke-WebRequest -Uri 'https://ollama.ai/download/windows' -OutFile 'ollama-windows.exe'}"
if exist ollama-windows.exe (
    call :print_step "Installation d'Ollama..."
    ollama-windows.exe /S
    del ollama-windows.exe
    
    REM Attendre qu'Ollama soit prêt
    timeout /t 10 /nobreak >nul
    
    call :check_command ollama
    if %errorlevel% equ 0 (
        call :print_success "Ollama installé avec succès"
    ) else (
        call :print_warning "Ollama installé mais non disponible dans PATH"
    )
) else (
    call :print_warning "Échec du téléchargement d'Ollama"
)

:install_models
call :print_step "Installation des modèles IA recommandés..."
ollama pull llama3.2:3b
ollama pull llava:7b
call :print_success "Modèles IA installés"
exit /b 0

REM Configuration de l'environnement Python
:setup_python_env
call :print_step "Configuration de l'environnement Python..."

REM Création de l'environnement virtuel
if exist venv (
    call :print_success "Environnement virtuel existe déjà"
) else (
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        call :print_error "Échec création environnement virtuel"
        exit /b 1
    )
    call :print_success "Environnement virtuel créé"
)

REM Activation de l'environnement
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    call :print_error "Échec activation environnement virtuel"
    exit /b 1
)

REM Mise à jour de pip
python -m pip install --upgrade pip

REM Installation des dépendances
if exist requirements.txt (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        call :print_error "Échec installation dépendances Python"
        exit /b 1
    )
    call :print_success "Dépendances Python installées"
) else (
    call :print_error "requirements.txt non trouvé"
    exit /b 1
)

exit /b 0

REM Configuration de l'environnement Node.js
:setup_node_env
call :print_step "Configuration de l'environnement Node.js..."

if exist ui\package.json (
    cd ui
    npm install
    if %errorlevel% neq 0 (
        call :print_warning "Échec installation dépendances Node.js"
        cd ..
        exit /b 1
    )
    cd ..
    call :print_success "Dépendances Node.js installées"
) else (
    call :print_warning "Interface UI non trouvée"
)

exit /b 0

REM Configuration des fichiers
:setup_config
call :print_step "Configuration des fichiers..."

REM Création des répertoires
if not exist logs mkdir logs
if not exist memory mkdir memory
if not exist screenshots mkdir screenshots
if not exist temp mkdir temp

REM Configuration .env
if exist .env.example (
    if not exist .env (
        copy .env.example .env >nul
        call :print_success "Fichier .env créé"
    )
) else (
    call :print_warning ".env.example non trouvé"
)

call :print_success "Configuration terminée"
exit /b 0

REM Tests
:run_tests
call :print_step "Lancement des tests d'intégration..."

call venv\Scripts\activate.bat
python start_jarvis.py --test

if %errorlevel% equ 0 (
    call :print_success "Tests réussis"
) else (
    call :print_warning "Tests échoués - vérifiez la configuration"
)

exit /b 0

REM Fonction principale
:main
call :print_step "Début de l'installation JARVIS Phase 2"

REM Vérifications
call :check_python
if %errorlevel% neq 0 exit /b 1

call :check_node
REM Continuer même si Node.js n'est pas disponible

REM Essayer d'installer via Chocolatey
if "%SKIP_CHOCO%" neq "true" (
    call :install_chocolatey_deps
)

REM Installation d'Ollama
if "%SKIP_OLLAMA%" neq "true" (
    call :install_ollama
)

REM Configuration
call :setup_python_env
if %errorlevel% neq 0 exit /b 1

call :setup_node_env

call :setup_config

REM Tests
if "%SKIP_TESTS%" neq "true" (
    call :run_tests
)

REM Résumé
echo.
echo 🎉 Installation terminée !
echo.
echo Pour démarrer JARVIS :
echo   venv\Scripts\activate.bat
echo   python start_jarvis.py
echo.
echo Interfaces disponibles :
echo   • Interface web: http://localhost:3000
echo   • API: http://localhost:8000/api/docs
echo.

if %ERRORS% gtr 0 (
    echo %RED%⚠️ %ERRORS% erreur(s) détectée(s)%NC%
    exit /b 1
) else if %WARNINGS% gtr 0 (
    echo %YELLOW%⚠️ %WARNINGS% avertissement(s)%NC%
    exit /b 0
) else (
    echo %GREEN%✅ Installation réussie sans erreurs%NC%
    exit /b 0
)

REM Gestion des arguments
:parse_args
if "%1"=="--skip-choco" (
    set "SKIP_CHOCO=true"
    shift
    goto :parse_args
)
if "%1"=="--skip-ollama" (
    set "SKIP_OLLAMA=true"
    shift
    goto :parse_args
)
if "%1"=="--skip-tests" (
    set "SKIP_TESTS=true"
    shift
    goto :parse_args
)
if "%1"=="--help" (
    echo Usage: %0 [options]
    echo.
    echo Options:
    echo   --skip-choco    Ignorer l'installation via Chocolatey
    echo   --skip-ollama   Ignorer l'installation d'Ollama
    echo   --skip-tests    Ignorer les tests d'intégration
    echo   --help          Afficher cette aide
    exit /b 0
)
if "%1" neq "" (
    call :print_error "Option inconnue: %1"
    exit /b 1
)

REM Point d'entrée
call :parse_args %*
call :main