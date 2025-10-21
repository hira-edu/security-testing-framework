#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Hot Install & Deploy - Security Testing Framework
.DESCRIPTION
    Single-command installation and deployment script
    Installs, builds, configures, and starts the framework
.PARAMETER TargetProcess
    Target process to monitor (default: LockDownBrowser.exe)
.PARAMETER Stealth
    Enable maximum stealth mode
.PARAMETER SkipBuild
    Skip building (use existing dist\SecurityTestingFramework.exe)
.EXAMPLE
    .\HOT_DEPLOY.ps1
.EXAMPLE
    .\HOT_DEPLOY.ps1 -TargetProcess "SafeExamBrowser.exe" -Stealth
#>

param(
    [string]$TargetProcess = "LockDownBrowser.exe",
    [switch]$Stealth = $true,
    [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"

Write-Host "`n" -NoNewline
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  SECURITY TESTING FRAMEWORK - HOT DEPLOYMENT          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Configuration
$repoPath = $PSScriptRoot
$installPath = "$env:LOCALAPPDATA\SecurityTestingFramework"
$exeName = "SecurityTestingFramework.exe"

# Step 1: Check Python
Write-Host "[1/8] Checking Python environment..." -ForegroundColor Yellow
try {
    $pythonVer = python --version 2>&1
    Write-Host "      ✓ $pythonVer" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Python not found - Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Step 2: Install dependencies
Write-Host "[2/8] Installing Python dependencies..." -ForegroundColor Yellow
cd $repoPath
try {
    python -m pip install --upgrade pip --quiet --disable-pip-version-check
    python -m pip install -r requirements.txt --quiet --disable-pip-version-check
    Write-Host "      ✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Dependency installation failed: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Build executable
if (!$SkipBuild) {
    Write-Host "[3/8] Building standalone executable..." -ForegroundColor Yellow
    try {
        python build_single_file.py 2>&1 | Out-Null
        if (Test-Path "dist\$exeName") {
            $size = [math]::Round(((Get-Item "dist\$exeName").Length/1MB),2)
            Write-Host "      ✓ Build complete ($size MB)" -ForegroundColor Green
        } else {
            throw "Executable not found after build"
        }
    } catch {
        Write-Host "      ✗ Build failed: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[3/8] Skipping build (using existing)..." -ForegroundColor Yellow
    if (!(Test-Path "dist\$exeName")) {
        Write-Host "      ✗ No existing executable found" -ForegroundColor Red
        exit 1
    }
    Write-Host "      ✓ Existing executable found" -ForegroundColor Green
}

# Step 4: Create installation structure
Write-Host "[4/8] Creating installation structure..." -ForegroundColor Yellow
try {
    @("$installPath", "$installPath\config", "$installPath\logs", "$installPath\captures", "$installPath\native") | ForEach-Object {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
    Write-Host "      ✓ Directory structure created" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Failed to create directories: $_" -ForegroundColor Red
    exit 1
}

# Step 5: Deploy files
Write-Host "[5/8] Deploying framework files..." -ForegroundColor Yellow
try {
    Copy-Item -Path "dist\$exeName" -Destination "$installPath\$exeName" -Force
    Copy-Item -Path "config.json" -Destination "$installPath\config\config.json" -Force
    if (Test-Path "native\*.dll") {
        Copy-Item -Path "native\*.dll" -Destination "$installPath\native\" -Force
    }
    Write-Host "      ✓ Files deployed" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Deployment failed: $_" -ForegroundColor Red
    exit 1
}

# Step 6: Configure framework
Write-Host "[6/8] Configuring framework..." -ForegroundColor Yellow
$config = @{
    version = "1.1.0"
    build_time = Get-Date -Format "yyyyMMdd_HHmmss"
    deployment_time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    security_level = "HIGH"
    enable_logging = $true
    stealth_mode = [bool]$Stealth
    auto_update = $false
    install_path = $installPath
    modules = @{
        screen_capture = $true
        process_monitor = $true
        api_hooks = $true
        memory_scanner = $true
        network_monitor = $true
    }
    targets = @($TargetProcess)
}
$config | ConvertTo-Json -Depth 10 | Set-Content "$installPath\config\config.json"
Write-Host "      ✓ Configuration saved" -ForegroundColor Green

# Step 7: Security configuration
Write-Host "[7/8] Configuring security settings..." -ForegroundColor Yellow
try {
    # Firewall rules
    New-NetFirewallRule -DisplayName "STF-Out" `
                        -Direction Outbound `
                        -Program "$installPath\$exeName" `
                        -Action Allow `
                        -Profile Any `
                        -Enabled True `
                        -ErrorAction SilentlyContinue | Out-Null

    # Defender exclusions (optional)
    Add-MpPreference -ExclusionPath $installPath -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionProcess $exeName -ErrorAction SilentlyContinue

    # Scheduled task for persistence
    $action = New-ScheduledTaskAction -Execute "$installPath\$exeName" -Argument "--config `"$installPath\config\config.json`" --stealth --hidden"
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden
    Register-ScheduledTask -TaskName "SecurityTestFramework" `
                           -Action $action `
                           -Trigger $trigger `
                           -Principal $principal `
                           -Settings $settings `
                           -Force `
                           -ErrorAction SilentlyContinue | Out-Null

    Write-Host "      ✓ Security configured" -ForegroundColor Green
} catch {
    Write-Host "      ! Security configuration partial (non-critical)" -ForegroundColor Yellow
}

# Step 8: Start framework
Write-Host "[8/8] Starting framework..." -ForegroundColor Yellow
try {
    $proc = Start-Process -FilePath "$installPath\$exeName" `
                          -ArgumentList "--config `"$installPath\config\config.json`"$(if($Stealth){' --stealth --hidden'})" `
                          -WindowStyle $(if($Stealth){'Hidden'}else{'Normal'}) `
                          -PassThru

    Start-Sleep -Seconds 2

    if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
        Write-Host "      ✓ Framework started (PID: $($proc.Id))" -ForegroundColor Green
    } else {
        Write-Host "      ! Framework may have exited" -ForegroundColor Yellow
    }
} catch {
    Write-Host "      ✗ Failed to start: $_" -ForegroundColor Red
}

# Summary
Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  HOT DEPLOYMENT COMPLETE!                              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Installation Path:" -ForegroundColor Cyan -NoNewline
Write-Host "  $installPath"
Write-Host "Executable:" -ForegroundColor Cyan -NoNewline
Write-Host "         $installPath\$exeName"
Write-Host "Config File:" -ForegroundColor Cyan -NoNewline
Write-Host "        $installPath\config\config.json"
Write-Host "Logs Directory:" -ForegroundColor Cyan -NoNewline
Write-Host "     $installPath\logs\"
Write-Host "Target Process:" -ForegroundColor Cyan -NoNewline
Write-Host "     $TargetProcess"
Write-Host "Stealth Mode:" -ForegroundColor Cyan -NoNewline
Write-Host "       $Stealth"
Write-Host ""

# Quick commands
Write-Host "Quick Commands:" -ForegroundColor Yellow
Write-Host "  Status:    " -NoNewline -ForegroundColor Gray
Write-Host "Get-Process -Name SecurityTestingFramework"
Write-Host "  Stop:      " -NoNewline -ForegroundColor Gray
Write-Host "Stop-Process -Name SecurityTestingFramework -Force"
Write-Host "  Logs:      " -NoNewline -ForegroundColor Gray
Write-Host "Get-Content `"$installPath\logs\*.log`" -Tail 50 -Wait"
Write-Host "  Uninstall: " -NoNewline -ForegroundColor Gray
Write-Host "Unregister-ScheduledTask -TaskName SecurityTestFramework -Confirm:`$false; Remove-Item -Path `"$installPath`" -Recurse -Force"
Write-Host ""
