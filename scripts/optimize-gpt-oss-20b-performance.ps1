# 🚀 JARVIS AI - Script d'Optimisation Performance GPT-OSS 20B
# Configuration automatique système Windows + AMD RX 7800 XT

param(
    [string]$Mode = "setup",  # setup, monitor, restore
    [switch]$Force,
    [switch]$DryRun
)

Write-Host "🤖 JARVIS AI - Optimisation Performance GPT-OSS 20B" -ForegroundColor Cyan
Write-Host "=" * 60

# Configuration optimale
$OptimalConfig = @{
    # Variables Ollama Host
    OllamaEnv = @{
        "OLLAMA_HOST" = "0.0.0.0"
        "OLLAMA_ORIGINS" = "http://localhost:*,http://127.0.0.1:*,http://172.20.0.0/16"
        "OLLAMA_MAX_LOADED_MODELS" = "2"
        "OLLAMA_MAX_QUEUE" = "100"
        "OLLAMA_NUM_PARALLEL" = "2"
        "OLLAMA_FLASH_ATTENTION" = "true"
        "OLLAMA_GPU_OVERHEAD" = "0.95"
        "OLLAMA_BATCH_SIZE" = "512"
    }
    
    # Configuration GPU AMD
    GpuEnv = @{
        "HSA_OVERRIDE_GFX_VERSION" = "10.3.0"
        "ROCR_VISIBLE_DEVICES" = "0"
        "HIP_VISIBLE_DEVICES" = "0"
        "ROCM_PATH" = "C:\Program Files\AMD\ROCm\5.7"
    }
    
    # Configuration réseau Docker
    DockerNetworking = @{
        "net.core.rmem_max" = "134217728"
        "net.core.wmem_max" = "134217728"
        "net.ipv4.tcp_rmem" = "4096 87380 134217728"
        "net.ipv4.tcp_wmem" = "4096 65536 134217728"
    }
    
    # Configuration système
    SystemOptimization = @{
        "ProcessPriorityClass" = "High"
        "ThreadPriority" = "Highest"
        "GPUScheduling" = "Hardware-accelerated"
    }
}

function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Set-OllamaEnvironment {
    Write-Host "🔧 Configuration variables d'environnement Ollama..." -ForegroundColor Yellow
    
    foreach ($var in $OptimalConfig.OllamaEnv.GetEnumerator()) {
        if (-not $DryRun) {
            [Environment]::SetEnvironmentVariable($var.Key, $var.Value, "Machine")
            Write-Host "   ✅ $($var.Key) = $($var.Value)" -ForegroundColor Green
        } else {
            Write-Host "   [DRY-RUN] $($var.Key) = $($var.Value)" -ForegroundColor Gray
        }
    }
    
    # Configuration GPU AMD
    Write-Host "🎮 Configuration variables GPU AMD..." -ForegroundColor Yellow
    foreach ($var in $OptimalConfig.GpuEnv.GetEnumerator()) {
        if (-not $DryRun) {
            [Environment]::SetEnvironmentVariable($var.Key, $var.Value, "Machine")
            Write-Host "   ✅ $($var.Key) = $($var.Value)" -ForegroundColor Green
        } else {
            Write-Host "   [DRY-RUN] $($var.Key) = $($var.Value)" -ForegroundColor Gray
        }
    }
}

function Optimize-GPUPerformance {
    Write-Host "🚀 Optimisation performance GPU..." -ForegroundColor Yellow
    
    # Vérifier AMD Software disponible
    $amdPath = "C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe"
    if (Test-Path $amdPath) {
        Write-Host "   ✅ AMD Software détecté" -ForegroundColor Green
        
        if (-not $DryRun) {
            # Activer mode performance GPU
            try {
                # Note: Commande hypothétique - à adapter selon AMD CLI disponible
                Write-Host "   🎯 Activation mode performance..." -ForegroundColor Cyan
                # & $amdPath --set-performance-mode 2>&1 | Out-Null
                Write-Host "   ℹ️  Activation manuelle recommandée via AMD Software" -ForegroundColor Blue
            } catch {
                Write-Host "   ⚠️  Activation automatique échouée - configuration manuelle requise" -ForegroundColor Orange
            }
        }
    } else {
        Write-Host "   ⚠️  AMD Software non trouvé - optimisation manuelle requise" -ForegroundColor Orange
    }
    
    # Configuration registre GPU scheduling (Windows 10/11)
    Write-Host "   🔧 Configuration GPU Hardware Scheduling..." -ForegroundColor Cyan
    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
    
    if (-not $DryRun) {
        try {
            Set-ItemProperty -Path $regPath -Name "HwSchMode" -Value 2 -Force
            Write-Host "   ✅ Hardware-accelerated GPU scheduling activé" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Impossible de modifier registre GPU" -ForegroundColor Orange
        }
    } else {
        Write-Host "   [DRY-RUN] HwSchMode = 2" -ForegroundColor Gray
    }
}

function Optimize-SystemPerformance {
    Write-Host "⚡ Optimisation performance système..." -ForegroundColor Yellow
    
    # Configuration priorité processus
    Write-Host "   🔧 Configuration priorité processus..." -ForegroundColor Cyan
    
    $processesToOptimize = @("ollama", "jarvis_brain", "jarvis_llm_gateway")
    
    foreach ($processName in $processesToOptimize) {
        $processes = Get-Process -Name $processName -ErrorAction SilentlyContinue
        
        if ($processes) {
            foreach ($process in $processes) {
                if (-not $DryRun) {
                    try {
                        $process.PriorityClass = "High"
                        Write-Host "   ✅ Priorité HIGH pour $processName (PID: $($process.Id))" -ForegroundColor Green
                    } catch {
                        Write-Host "   ⚠️  Impossible de modifier priorité $processName" -ForegroundColor Orange
                    }
                } else {
                    Write-Host "   [DRY-RUN] Priorité HIGH pour $processName" -ForegroundColor Gray
                }
            }
        }
    }
    
    # Optimisation mémoire virtuelle
    Write-Host "   💾 Configuration mémoire virtuelle..." -ForegroundColor Cyan
    
    if (-not $DryRun) {
        # Désactiver trim SSD pour améliorer performances (temporaire)
        try {
            Disable-MMAgent -MemoryCompression -ErrorAction SilentlyContinue
            Write-Host "   ✅ Compression mémoire désactivée temporairement" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Impossible de modifier compression mémoire" -ForegroundColor Orange
        }
    }
}

function Optimize-DockerPerformance {
    Write-Host "🐳 Optimisation performance Docker..." -ForegroundColor Yellow
    
    # Configuration Docker Desktop
    $dockerConfigPath = "$env:APPDATA\Docker\settings.json"
    
    if (Test-Path $dockerConfigPath) {
        Write-Host "   📝 Configuration Docker Desktop trouvée" -ForegroundColor Green
        
        if (-not $DryRun) {
            try {
                $dockerConfig = Get-Content $dockerConfigPath | ConvertFrom-Json
                
                # Optimisations recommandées
                $dockerConfig.memoryMiB = 8192  # 8GB RAM pour Docker
                $dockerConfig.cpus = 8          # Utiliser tous les cœurs
                $dockerConfig.diskSizeMiB = 102400  # 100GB espace disque
                $dockerConfig.swapMiB = 2048    # 2GB swap
                
                # Sauvegarder configuration
                $dockerConfig | ConvertTo-Json -Depth 10 | Out-File $dockerConfigPath -Encoding UTF8
                Write-Host "   ✅ Configuration Docker Desktop optimisée" -ForegroundColor Green
                Write-Host "   ℹ️  Redémarrage Docker Desktop requis" -ForegroundColor Blue
                
            } catch {
                Write-Host "   ⚠️  Impossible de modifier configuration Docker" -ForegroundColor Orange
            }
        } else {
            Write-Host "   [DRY-RUN] Configuration Docker Desktop" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️  Docker Desktop config non trouvée" -ForegroundColor Orange
    }
}

function Test-SystemRequirements {
    Write-Host "🔍 Vérification configuration système..." -ForegroundColor Yellow
    
    $systemInfo = @{
        TotalRAM = [Math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
        CPUCores = (Get-WmiObject Win32_ComputerSystem).NumberOfProcessors
        GPUInfo = Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like "*RX*" } | Select-Object -First 1
        DiskSpace = Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | 
                   Measure-Object -Property Size -Sum | 
                   ForEach-Object { [Math]::Round($_.Sum / 1GB, 1) }
    }
    
    Write-Host "📊 Configuration système détectée:" -ForegroundColor Cyan
    Write-Host "   RAM: $($systemInfo.TotalRAM) GB" -ForegroundColor White
    Write-Host "   CPU Cores: $($systemInfo.CPUCores)" -ForegroundColor White
    Write-Host "   Disk Space: $($systemInfo.DiskSpace) GB total" -ForegroundColor White
    
    if ($systemInfo.GPUInfo) {
        Write-Host "   GPU: $($systemInfo.GPUInfo.Name)" -ForegroundColor White
    } else {
        Write-Host "   ⚠️  GPU AMD RX 7800 XT non détectée" -ForegroundColor Orange
    }
    
    # Vérifications requirements
    $requirements = @{
        RAM_OK = $systemInfo.TotalRAM -ge 16
        CPU_OK = $systemInfo.CPUCores -ge 8
        DISK_OK = $systemInfo.DiskSpace -ge 100
        GPU_OK = $systemInfo.GPUInfo -ne $null
    }
    
    Write-Host "✅ Vérification requirements:" -ForegroundColor Green
    foreach ($req in $requirements.GetEnumerator()) {
        $status = if ($req.Value) { "✅ OK" } else { "❌ INSUFFICIENT" }
        $color = if ($req.Value) { "Green" } else { "Red" }
        Write-Host "   $($req.Key): $status" -ForegroundColor $color
    }
    
    return $requirements
}

function Start-PerformanceMonitoring {
    Write-Host "📊 Démarrage monitoring performance..." -ForegroundColor Yellow
    
    $monitoringScript = @"
# Monitor performance GPU/CPU/RAM
while (`$true) {
    `$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # CPU Usage
    `$cpuUsage = Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1 | 
                Select-Object -ExpandProperty CounterSamples | 
                Select-Object -ExpandProperty CookedValue
    
    # Memory Usage
    `$memUsage = Get-Counter '\Memory\% Committed Bytes In Use' -SampleInterval 1 -MaxSamples 1 |
                Select-Object -ExpandProperty CounterSamples |
                Select-Object -ExpandProperty CookedValue
    
    # GPU Usage (estimation via processus)
    `$gpuProcesses = Get-Process ollama, jarvis* -ErrorAction SilentlyContinue
    `$gpuUsageEst = (`$gpuProcesses | Measure-Object WorkingSet -Sum).Sum / 1GB
    
    Write-Host "`$timestamp - CPU: `$([Math]::Round(`$cpuUsage, 1))% | RAM: `$([Math]::Round(`$memUsage, 1))% | GPU Est: `$([Math]::Round(`$gpuUsageEst, 1))GB" -ForegroundColor Cyan
    
    Start-Sleep -Seconds 5
}
"@
    
    if (-not $DryRun) {
        # Démarrer monitoring en arrière-plan
        $job = Start-Job -ScriptBlock { 
            Invoke-Expression $using:monitoringScript 
        }
        Write-Host "   ✅ Monitoring démarré (Job ID: $($job.Id))" -ForegroundColor Green
        Write-Host "   ℹ️  Utilisez 'Stop-Job $($job.Id)' pour arrêter" -ForegroundColor Blue
    } else {
        Write-Host "   [DRY-RUN] Monitoring script créé" -ForegroundColor Gray
    }
}

function Restore-SystemDefaults {
    Write-Host "🔄 Restauration configuration par défaut..." -ForegroundColor Yellow
    
    # Supprimer variables Ollama
    foreach ($var in $OptimalConfig.OllamaEnv.Keys) {
        if (-not $DryRun) {
            [Environment]::SetEnvironmentVariable($var, $null, "Machine")
            Write-Host "   ✅ $var supprimé" -ForegroundColor Green
        } else {
            Write-Host "   [DRY-RUN] Suppression $var" -ForegroundColor Gray
        }
    }
    
    # Restaurer priorités processus normales
    $processesToRestore = @("ollama", "jarvis_brain", "jarvis_llm_gateway")
    
    foreach ($processName in $processesToRestore) {
        $processes = Get-Process -Name $processName -ErrorAction SilentlyContinue
        
        if ($processes) {
            foreach ($process in $processes) {
                if (-not $DryRun) {
                    try {
                        $process.PriorityClass = "Normal"
                        Write-Host "   ✅ Priorité NORMAL restaurée pour $processName" -ForegroundColor Green
                    } catch {
                        Write-Host "   ⚠️  Impossible de restaurer priorité $processName" -ForegroundColor Orange
                    }
                }
            }
        }
    }
    
    Write-Host "✅ Configuration par défaut restaurée" -ForegroundColor Green
}

# Vérification droits administrateur
if (-not (Test-AdminRights)) {
    Write-Host "❌ Droits administrateur requis!" -ForegroundColor Red
    Write-Host "   Relancer PowerShell en tant qu'administrateur" -ForegroundColor Yellow
    exit 1
}

# Exécution selon mode
switch ($Mode) {
    "setup" {
        Write-Host "🚀 Mode: Configuration optimisation complète" -ForegroundColor Cyan
        
        $requirements = Test-SystemRequirements
        
        if (-not $Force) {
            $allOK = $requirements.Values | Where-Object { -not $_ } | Measure-Object | Select-Object -ExpandProperty Count
            if ($allOK -gt 0) {
                Write-Host "⚠️  Certains requirements ne sont pas satisfaits" -ForegroundColor Orange
                Write-Host "   Utilisez -Force pour continuer malgré tout" -ForegroundColor Yellow
                exit 1
            }
        }
        
        Set-OllamaEnvironment
        Optimize-GPUPerformance  
        Optimize-SystemPerformance
        Optimize-DockerPerformance
        
        Write-Host "" 
        Write-Host "🎉 Optimisation terminée avec succès!" -ForegroundColor Green
        Write-Host "📝 Actions recommandées:" -ForegroundColor Yellow
        Write-Host "   1. Redémarrer Docker Desktop" -ForegroundColor White
        Write-Host "   2. Redémarrer services JARVIS" -ForegroundColor White
        Write-Host "   3. Tester performance avec: python benchmark_gpt_oss_20b_migration.py" -ForegroundColor White
    }
    
    "monitor" {
        Write-Host "📊 Mode: Monitoring performance" -ForegroundColor Cyan
        Start-PerformanceMonitoring
    }
    
    "restore" {
        Write-Host "🔄 Mode: Restauration configuration" -ForegroundColor Cyan
        Restore-SystemDefaults
    }
    
    default {
        Write-Host "❌ Mode invalide: $Mode" -ForegroundColor Red
        Write-Host "Modes disponibles: setup, monitor, restore" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "🤖 JARVIS AI - Script terminé" -ForegroundColor Cyan