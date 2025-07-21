# JARVIS AI - Installation PowerShell pour Windows
# Support Windows 10/11 + WSL2

param(
    [switch]$UseWSL,
    [switch]$SkipDocker,
    [switch]$Quiet,
    [string]$InstallPath = $PWD
)

# Configuration
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Couleurs pour l'affichage
$Colors = @{
    Red = [System.ConsoleColor]::Red
    Green = [System.ConsoleColor]::Green
    Yellow = [System.ConsoleColor]::Yellow
    Blue = [System.ConsoleColor]::Blue
    Cyan = [System.ConsoleColor]::Cyan
    Magenta = [System.ConsoleColor]::Magenta
    White = [System.ConsoleColor]::White
}

function Write-ColorText {
    param([string]$Text, [System.ConsoleColor]$Color = $Colors.White)
    Write-Host $Text -ForegroundColor $Color
}

function Write-Banner {
    Write-ColorText @"

╔══════════════════════════════════════════╗
║          JARVIS AI INSTALLER             ║
║        PowerShell Windows + WSL          ║
╚══════════════════════════════════════════╝

"@ $Colors.Magenta
}

function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-WSLAvailable {
    try {
        $wslStatus = wsl --status 2>$null
        if ($LASTEXITCODE -eq 0) {
            $distros = wsl -l -q 2>$null | Where-Object { $_ -and $_.Trim() }
            if ($distros) {
                return @{
                    Available = $true
                    DefaultDistro = $distros[0].Trim()
                    Distros = $distros
                }
            }
        }
        return @{ Available = $false }
    }
    catch {
        return @{ Available = $false }
    }
}

function Install-Chocolatey {
    Write-ColorText "[INFO] Installation de Chocolatey..." $Colors.Blue
    
    try {
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            Write-ColorText "✓ Chocolatey déjà installé" $Colors.Green
            return $true
        }
        
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        # Recharger l'environnement
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            Write-ColorText "✓ Chocolatey installé avec succès" $Colors.Green
            return $true
        }
        else {
            Write-ColorText "✗ Échec installation Chocolatey" $Colors.Red
            return $false
        }
    }
    catch {
        Write-ColorText "✗ Erreur installation Chocolatey: $_" $Colors.Red
        return $false
    }
}

function Install-Winget {
    Write-ColorText "[INFO] Vérification de winget..." $Colors.Blue
    
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-ColorText "✓ winget disponible" $Colors.Green
        return $true
    }
    
    try {
        # Essayer d'installer via Microsoft Store
        Write-ColorText "Installation de winget..." $Colors.Yellow
        
        $tempPath = "$env:TEMP\Microsoft.DesktopAppInstaller.msixbundle"
        Invoke-WebRequest -Uri "https://aka.ms/getwinget" -OutFile $tempPath -UseBasicParsing
        Add-AppxPackage -Path $tempPath -ForceApplicationShutdown
        Remove-Item $tempPath -Force
        
        # Recharger PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-ColorText "✓ winget installé" $Colors.Green
            return $true
        }
    }
    catch {
        Write-ColorText "⚠ winget non disponible" $Colors.Yellow
        return $false
    }
    
    return $false
}

function Install-Prerequisites {
    Write-ColorText "`n[1/10] Installation des prérequis..." $Colors.Blue
    
    $hasWinget = Install-Winget
    $hasChoco = $false
    
    if (-not $hasWinget) {
        $hasChoco = Install-Chocolatey
    }
    
    if (-not $hasWinget -and -not $hasChoco) {
        Write-ColorText "⚠ Aucun gestionnaire de paquets disponible - Installation manuelle requise" $Colors.Yellow
        return $false
    }
    
    # Python
    Write-ColorText "Vérification de Python..." $Colors.Cyan
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonVersion = python --version 2>&1
        Write-ColorText "✓ $pythonVersion" $Colors.Green
    }
    else {
        Write-ColorText "Installation de Python..." $Colors.Yellow
        if ($hasWinget) {
            winget install Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements
        }
        elseif ($hasChoco) {
            choco install python311 -y
        }
        
        # Recharger PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (Get-Command python -ErrorAction SilentlyContinue) {
            Write-ColorText "✓ Python installé" $Colors.Green
        }
        else {
            Write-ColorText "✗ Échec installation Python" $Colors.Red
            return $false
        }
    }
    
    # Git
    Write-ColorText "Vérification de Git..." $Colors.Cyan
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $gitVersion = git --version
        Write-ColorText "✓ $gitVersion" $Colors.Green
    }
    else {
        Write-ColorText "Installation de Git..." $Colors.Yellow
        if ($hasWinget) {
            winget install Git.Git --silent --accept-source-agreements --accept-package-agreements
        }
        elseif ($hasChoco) {
            choco install git -y
        }
    }
    
    # Node.js
    Write-ColorText "Vérification de Node.js..." $Colors.Cyan
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $nodeVersion = node --version
        Write-ColorText "✓ Node.js $nodeVersion" $Colors.Green
    }
    else {
        Write-ColorText "Installation de Node.js..." $Colors.Yellow
        if ($hasWinget) {
            winget install OpenJS.NodeJS --silent --accept-source-agreements --accept-package-agreements
        }
        elseif ($hasChoco) {
            choco install nodejs -y
        }
    }
    
    return $true
}

function Install-Docker {
    if ($SkipDocker) {
        Write-ColorText "Docker ignoré (paramètre --SkipDocker)" $Colors.Yellow
        return $true
    }
    
    Write-ColorText "`n[2/10] Installation de Docker..." $Colors.Blue
    
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-ColorText "✓ Docker déjà installé" $Colors.Green
        
        # Vérifier que Docker fonctionne
        try {
            docker info | Out-Null
            Write-ColorText "✓ Docker opérationnel" $Colors.Green
            return $true
        }
        catch {
            Write-ColorText "⚠ Docker installé mais non fonctionnel" $Colors.Yellow
        }
    }
    
    Write-ColorText "Téléchargement de Docker Desktop..." $Colors.Yellow
    
    try {
        $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
        
        Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller -UseBasicParsing
        
        Write-ColorText "Installation de Docker Desktop..." $Colors.Yellow
        Start-Process -FilePath $dockerInstaller -ArgumentList "install --quiet" -Wait -Verb RunAs
        
        Remove-Item $dockerInstaller -Force
        
        Write-ColorText "✓ Docker Desktop installé" $Colors.Green
        Write-ColorText "⚠ Redémarrage nécessaire pour Docker" $Colors.Yellow
        
        return $true
    }
    catch {
        Write-ColorText "✗ Erreur installation Docker: $_" $Colors.Red
        return $false
    }
}

function Install-Ollama {
    Write-ColorText "`n[3/10] Installation d'Ollama..." $Colors.Blue
    
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        Write-ColorText "✓ Ollama déjà installé" $Colors.Green
        return $true
    }
    
    try {
        Write-ColorText "Téléchargement d'Ollama..." $Colors.Yellow
        
        $ollamaUrl = "https://ollama.ai/download/windows"
        $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
        
        Invoke-WebRequest -Uri $ollamaUrl -OutFile $ollamaInstaller -UseBasicParsing
        Start-Process -FilePath $ollamaInstaller -ArgumentList "/S" -Wait
        Remove-Item $ollamaInstaller -Force
        
        # Recharger PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (Get-Command ollama -ErrorAction SilentlyContinue) {
            Write-ColorText "✓ Ollama installé" $Colors.Green
            
            # Démarrer le service
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep 3
        }
        else {
            Write-ColorText "⚠ Ollama installé mais non accessible" $Colors.Yellow
        }
        
        return $true
    }
    catch {
        Write-ColorText "⚠ Erreur installation Ollama: $_" $Colors.Yellow
        return $true  # Non bloquant
    }
}

function Setup-WSLEnvironment {
    Write-ColorText "`n[4/10] Configuration WSL..." $Colors.Blue
    
    $wslInfo = Test-WSLAvailable
    
    if (-not $wslInfo.Available) {
        Write-ColorText "⚠ WSL non disponible" $Colors.Yellow
        return $false
    }
    
    Write-ColorText "✓ WSL disponible - Distribution: $($wslInfo.DefaultDistro)" $Colors.Green
    
    try {
        # Créer le répertoire dans WSL
        wsl mkdir -p /home/jarvis-ai 2>$null
        
        # Copier les fichiers vers WSL
        Write-ColorText "Copie des fichiers vers WSL..." $Colors.Cyan
        wsl bash -c "cp -r /mnt/$(($InstallPath -split ':')[0].ToLower())$(($InstallPath -split ':')[1] -replace '\\', '/')/* /home/jarvis-ai/" 2>$null
        
        # Installer les dépendances Linux
        Write-ColorText "Installation des dépendances WSL..." $Colors.Cyan
        wsl bash -c "cd /home/jarvis-ai && sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv docker.io docker-compose"
        
        # Rendre exécutable
        wsl bash -c "cd /home/jarvis-ai && chmod +x *.sh"
        
        Write-ColorText "✓ Environnement WSL configuré" $Colors.Green
        return $true
    }
    catch {
        Write-ColorText "✗ Erreur configuration WSL: $_" $Colors.Red
        return $false
    }
}

function Setup-PythonEnvironment {
    Write-ColorText "`n[5/10] Configuration de l'environnement Python..." $Colors.Blue
    
    try {
        # Créer l'environnement virtuel
        if (-not (Test-Path "venv")) {
            Write-ColorText "Création de l'environnement virtuel..." $Colors.Cyan
            python -m venv venv
        }
        
        # Activer l'environnement virtuel
        & ".\venv\Scripts\Activate.ps1"
        
        # Mise à jour de pip
        Write-ColorText "Mise à jour de pip..." $Colors.Cyan
        python -m pip install --upgrade pip setuptools wheel
        
        # Installation des dépendances Windows
        Write-ColorText "Installation des dépendances Windows..." $Colors.Cyan
        pip install pywin32 pyautogui keyboard psutil
        
        Write-ColorText "✓ Environnement Python configuré" $Colors.Green
        return $true
    }
    catch {
        Write-ColorText "✗ Erreur configuration Python: $_" $Colors.Red
        return $false
    }
}

function Setup-DockerEnvironment {
    Write-ColorText "`n[6/10] Configuration Docker..." $Colors.Blue
    
    try {
        # Créer les répertoires nécessaires
        $directories = @("logs", "cache", "memory", "models", "data")
        foreach ($dir in $directories) {
            if (-not (Test-Path $dir)) {
                New-Item -ItemType Directory -Path $dir | Out-Null
            }
        }
        
        # Créer le réseau Docker
        try {
            docker network create jarvis-network 2>$null | Out-Null
        }
        catch {
            # Le réseau existe probablement déjà
        }
        
        # Test Docker
        docker run --rm hello-world 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorText "✓ Docker fonctionne correctement" $Colors.Green
        }
        else {
            Write-ColorText "⚠ Docker non fonctionnel" $Colors.Yellow
        }
        
        return $true
    }
    catch {
        Write-ColorText "⚠ Configuration Docker partielle: $_" $Colors.Yellow
        return $true  # Non bloquant
    }
}

function Run-MainInstallation {
    Write-ColorText "`n[7/10] Installation principale JARVIS..." $Colors.Blue
    
    try {
        # Activer l'environnement virtuel si nécessaire
        if (Test-Path "venv\Scripts\Activate.ps1") {
            & ".\venv\Scripts\Activate.ps1"
        }
        
        # Lancer l'installation Python
        python install-jarvis.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorText "✓ Installation principale réussie" $Colors.Green
            return $true
        }
        else {
            Write-ColorText "✗ Échec installation principale" $Colors.Red
            return $false
        }
    }
    catch {
        Write-ColorText "✗ Erreur installation principale: $_" $Colors.Red
        return $false
    }
}

function Create-LaunchScripts {
    Write-ColorText "`n[8/10] Création des scripts de lancement..." $Colors.Blue
    
    # Script principal Windows
    $windowsLauncher = @"
@echo off
title JARVIS AI - Windows PowerShell
echo.
echo ╔══════════════════════════════════════════╗
echo ║            JARVIS AI STARTUP             ║
echo ║         Windows PowerShell Mode          ║
echo ╚══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/4] Activation de l'environnement Python...
call venv\Scripts\activate.bat

echo [2/4] Démarrage des services Docker...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ✗ Erreur Docker Compose
    pause
    exit /b 1
)

echo [3/4] Démarrage du pont vocal...
if exist "start-voice-bridge.bat" (
    start "Voice Bridge" start-voice-bridge.bat
)

echo [4/4] Démarrage de JARVIS...
start "JARVIS Main" python start_jarvis.py

echo.
echo ✓ JARVIS AI démarré!
echo   🌐 Interface: http://localhost:3000
echo   🔗 API: http://localhost:5000
echo.
pause
"@
    
    $windowsLauncher | Out-File -FilePath "launch-jarvis-ps.bat" -Encoding ASCII
    
    # Script PowerShell moderne
    $psLauncher = @"
# JARVIS AI - Lanceur PowerShell
Write-Host "
╔══════════════════════════════════════════╗
║            JARVIS AI STARTUP             ║
║            PowerShell Mode               ║
╚══════════════════════════════════════════╝
" -ForegroundColor Magenta

Set-Location `$PSScriptRoot

Write-Host "[1/4] Activation de l'environnement Python..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

Write-Host "[2/4] Démarrage des services Docker..." -ForegroundColor Cyan
docker-compose up -d

Write-Host "[3/4] Démarrage du pont vocal..." -ForegroundColor Cyan
if (Test-Path "start-voice-bridge.bat") {
    Start-Process -FilePath "start-voice-bridge.bat" -WindowStyle Normal
}

Write-Host "[4/4] Démarrage de JARVIS..." -ForegroundColor Cyan
Start-Process -FilePath "python" -ArgumentList "start_jarvis.py" -WindowStyle Normal

Write-Host "
✓ JARVIS AI démarré!
  🌐 Interface: http://localhost:3000
  🔗 API: http://localhost:5000
" -ForegroundColor Green

Start-Sleep 2
Start-Process "http://localhost:3000"
"@
    
    $psLauncher | Out-File -FilePath "launch-jarvis.ps1" -Encoding UTF8
    
    # Script d'arrêt
    $stopScript = @"
@echo off
echo Arrêt de JARVIS AI...
docker-compose down
taskkill /f /im python.exe /fi "WINDOWTITLE eq Voice Bridge*" 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq JARVIS Main*" 2>nul
echo ✓ JARVIS AI arrêté
pause
"@
    
    $stopScript | Out-File -FilePath "stop-jarvis.bat" -Encoding ASCII
    
    Write-ColorText "✓ Scripts de lancement créés" $Colors.Green
    return $true
}

function Test-Installation {
    Write-ColorText "`n[9/10] Tests de validation..." $Colors.Blue
    
    $tests = @(
        @{ Name = "Python"; Command = "python --version" },
        @{ Name = "Docker"; Command = "docker --version" },
        @{ Name = "Docker Compose"; Command = "docker-compose --version" },
        @{ Name = "Node.js"; Command = "node --version" }
    )
    
    foreach ($test in $tests) {
        try {
            $result = Invoke-Expression $test.Command 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorText "✓ $($test.Name): OK" $Colors.Green
            }
            else {
                Write-ColorText "⚠ $($test.Name): Non disponible" $Colors.Yellow
            }
        }
        catch {
            Write-ColorText "⚠ $($test.Name): Non testé" $Colors.Yellow
        }
    }
    
    return $true
}

function Show-Summary {
    Write-ColorText "`n[10/10] Résumé de l'installation" $Colors.Blue
    
    Write-ColorText @"

╔═══════════════════════════════════════════════╗
║              INSTALLATION TERMINÉE            ║
╚═══════════════════════════════════════════════╝

Scripts disponibles:
  📄 launch-jarvis.ps1         - PowerShell moderne
  📄 launch-jarvis-ps.bat      - Batch Windows
  📄 stop-jarvis.bat          - Arrêt propre

"@ $Colors.Green
    
    $wslInfo = Test-WSLAvailable
    if ($wslInfo.Available -and $UseWSL) {
        Write-ColorText @"
Alternative WSL:
  📄 wsl bash -c "cd /home/jarvis-ai && ./launch-jarvis.sh"

"@ $Colors.Cyan
    }
    
    Write-ColorText @"
Accès aux services:
  🌐 Interface web: http://localhost:3000
  🔗 API principale: http://localhost:5000
  📚 Documentation: http://localhost:5000/docs

Pour démarrer JARVIS:
  > .\launch-jarvis.ps1

"@ $Colors.White
}

# MAIN EXECUTION
function Main {
    Write-Banner
    
    # Vérification des privilèges
    if (Test-AdminRights) {
        Write-ColorText "✓ Privilèges administrateur détectés" $Colors.Green
    }
    else {
        Write-ColorText "⚠ Exécution sans privilèges administrateur" $Colors.Yellow
        Write-ColorText "  Certaines installations peuvent échouer" $Colors.Yellow
    }
    
    # Détection WSL
    $wslInfo = Test-WSLAvailable
    if ($wslInfo.Available) {
        Write-ColorText "✓ WSL disponible - Distribution: $($wslInfo.DefaultDistro)" $Colors.Green
        
        if (-not $UseWSL -and -not $Quiet) {
            $response = Read-Host "Utiliser WSL pour l'installation? (O/N)"
            if ($response -eq "O" -or $response -eq "o") {
                $UseWSL = $true
            }
        }
    }
    
    # Installation WSL si demandée
    if ($UseWSL -and $wslInfo.Available) {
        if (Setup-WSLEnvironment) {
            Write-ColorText "Installation WSL terminée. Lancement dans WSL..." $Colors.Green
            wsl bash -c "cd /home/jarvis-ai && ./install-jarvis.sh"
            
            if ($LASTEXITCODE -eq 0) {
                Show-Summary
                return
            }
            else {
                Write-ColorText "Échec WSL - Basculement vers Windows natif" $Colors.Yellow
                $UseWSL = $false
            }
        }
    }
    
    # Installation Windows native
    $steps = @(
        { Install-Prerequisites },
        { Install-Docker },
        { Install-Ollama },
        { Setup-PythonEnvironment },
        { Setup-DockerEnvironment },
        { Run-MainInstallation },
        { Create-LaunchScripts },
        { Test-Installation }
    )
    
    $success = $true
    foreach ($step in $steps) {
        if (-not (& $step)) {
            $success = $false
            Write-ColorText "⚠ Étape échouée - Continuation..." $Colors.Yellow
        }
    }
    
    Show-Summary
    
    if (-not $Quiet) {
        $response = Read-Host "`nDémarrer JARVIS maintenant? (O/N)"
        if ($response -eq "O" -or $response -eq "o") {
            & ".\launch-jarvis.ps1"
        }
    }
}

# Exécution
try {
    Main
}
catch {
    Write-ColorText "Erreur fatale: $_" $Colors.Red
    exit 1
}