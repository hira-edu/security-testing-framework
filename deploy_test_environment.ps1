# Security Testing Framework - Test Environment Deployment Script
# PowerShell Deployment for Controlled Testing Environments
# WARNING: Only use in isolated test environments you own

[CmdletBinding()]
param(
    [Parameter()]
    [string]$InstallPath = "C:\SecurityTestFramework",

    [Parameter()]
    [string]$TargetProcess = "LockDownBrowser.exe",

    [Parameter()]
    [switch]$AutoStart = $true,

    [Parameter()]
    [switch]$Hidden = $false,

    [Parameter()]
    [switch]$Persistent = $false,

    [Parameter()]
    [string]$MonitoringDuration = "0"  # 0 = unlimited
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "SECURITY TESTING FRAMEWORK DEPLOYMENT" -ForegroundColor Cyan
Write-Host "Test Environment Setup Script v1.0" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin privileges
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[!] This script requires Administrator privileges" -ForegroundColor Red
    Write-Host "[*] Restarting with elevated privileges..." -ForegroundColor Yellow
    Start-Process PowerShell -Verb RunAs "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" $PSBoundParameters"
    exit
}

Write-Host "[+] Running with Administrator privileges" -ForegroundColor Green

# Function to download framework
function Install-Framework {
    Write-Host "[*] Installing Security Testing Framework..." -ForegroundColor Yellow

    # Create installation directory
    if (!(Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
        Write-Host "[+] Created directory: $InstallPath" -ForegroundColor Green
    }

    # Download from GitHub
    $repoUrl = "https://github.com/hira-edu/security-testing-framework/archive/refs/heads/main.zip"
    $zipPath = "$env:TEMP\stf_framework.zip"

    Write-Host "[*] Downloading framework..." -ForegroundColor Yellow
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $repoUrl -OutFile $zipPath -UseBasicParsing
        Write-Host "[+] Download complete" -ForegroundColor Green
    } catch {
        Write-Host "[!] Download failed. Installing from direct clone..." -ForegroundColor Red

        # Alternative: Git clone
        if (Get-Command git -ErrorAction SilentlyContinue) {
            Set-Location $InstallPath
            git clone https://github.com/hira-edu/security-testing-framework.git .
        } else {
            Write-Host "[!] Git not found. Please install Git or download manually" -ForegroundColor Red
            exit 1
        }
    }

    # Extract files
    if (Test-Path $zipPath) {
        Write-Host "[*] Extracting files..." -ForegroundColor Yellow
        Expand-Archive -Path $zipPath -DestinationPath $env:TEMP -Force
        Copy-Item -Path "$env:TEMP\security-testing-framework-main\*" -Destination $InstallPath -Recurse -Force
        Remove-Item $zipPath -Force
        Remove-Item "$env:TEMP\security-testing-framework-main" -Recurse -Force
        Write-Host "[+] Extraction complete" -ForegroundColor Green
    }

    # Install Python dependencies
    Write-Host "[*] Installing Python dependencies..." -ForegroundColor Yellow
    Set-Location $InstallPath

    # Create requirements if not exists
    if (!(Test-Path "requirements.txt")) {
        @"
psutil>=5.8.0
pywin32>=300
pillow>=9.0.0
numpy>=1.20.0
requests>=2.26.0
pyyaml>=5.4.1
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8
    }

    # Install requirements
    & python -m pip install --upgrade pip | Out-Null
    & python -m pip install -r requirements.txt | Out-Null
    Write-Host "[+] Dependencies installed" -ForegroundColor Green
}

# Function to create launcher script
function Create-LauncherScript {
    Write-Host "[*] Creating launcher script..." -ForegroundColor Yellow

    $launcherScript = @"
@echo off
cd /d "$InstallPath"
set PYTHONPATH=$InstallPath

:: Kill any existing instances
taskkill /F /IM python.exe /FI "WINDOWTITLE eq SecurityTestFramework*" >nul 2>&1

:: Start with all features enabled
start "SecurityTestFramework" /MIN python launcher.py ^
    --auto ^
    --monitor ^
    --stealth ^
    --comprehensive ^
    --target "$TargetProcess" ^
    --duration $MonitoringDuration ^
    --silent ^
    --export "$InstallPath\monitoring_data"

exit
"@

    $launcherScript | Out-File -FilePath "$InstallPath\start_monitoring.bat" -Encoding ASCII
    Write-Host "[+] Launcher script created: start_monitoring.bat" -ForegroundColor Green

    # Create PowerShell launcher
    $psLauncher = @"
# PowerShell Launcher for Security Testing Framework
Set-Location "$InstallPath"
`$env:PYTHONPATH = "$InstallPath"

# Kill existing instances
Get-Process python -ErrorAction SilentlyContinue | Where-Object {`$_.MainWindowTitle -like "*SecurityTestFramework*"} | Stop-Process -Force

# Start monitoring with all features
`$arguments = @(
    "launcher.py",
    "--auto",
    "--monitor",
    "--stealth",
    "--comprehensive",
    "--target", "$TargetProcess",
    "--duration", "$MonitoringDuration",
    "--silent",
    "--export", "$InstallPath\monitoring_data"
)

if ('$Hidden' -eq `$true) {
    Start-Process python -ArgumentList `$arguments -WindowStyle Hidden
} else {
    Start-Process python -ArgumentList `$arguments -WindowStyle Minimized
}
"@

    $psLauncher | Out-File -FilePath "$InstallPath\start_monitoring.ps1" -Encoding UTF8
    Write-Host "[+] PowerShell launcher created: start_monitoring.ps1" -ForegroundColor Green
}

# Function to create scheduled task
function Create-ScheduledTask {
    Write-Host "[*] Creating scheduled task for automatic startup..." -ForegroundColor Yellow

    $taskName = "SecurityTestFramework"

    # Remove existing task if exists
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    # Create action
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$InstallPath\start_monitoring.ps1`""

    # Create triggers
    $triggers = @()
    $triggers += New-ScheduledTaskTrigger -AtStartup
    $triggers += New-ScheduledTaskTrigger -AtLogOn

    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -Hidden `
        -ExecutionTimeLimit (New-TimeSpan -Days 365) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -StartWhenAvailable

    # Create principal (run as SYSTEM)
    $principal = New-ScheduledTaskPrincipal `
        -UserId "NT AUTHORITY\SYSTEM" `
        -LogonType ServiceAccount `
        -RunLevel Highest

    # Register task
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $triggers `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null

    Write-Host "[+] Scheduled task created: $taskName" -ForegroundColor Green
    Write-Host "[+] Task will run at system startup and user logon" -ForegroundColor Green
}

# Function to create Windows service
function Create-WindowsService {
    Write-Host "[*] Creating Windows service for persistent monitoring..." -ForegroundColor Yellow

    $serviceName = "SecurityTestFramework"
    $displayName = "Security Testing Framework Monitor"
    $description = "Comprehensive security testing and monitoring service"

    # Create service wrapper script
    $serviceWrapper = @"
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
import sys
import os

sys.path.insert(0, r'$InstallPath')
os.chdir(r'$InstallPath')

class SecurityTestService(win32serviceutil.ServiceFramework):
    _svc_name_ = '$serviceName'
    _svc_display_name_ = '$displayName'
    _svc_description_ = '$description'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                             servicemanager.PYS_SERVICE_STARTED,
                             (self._svc_name_, ''))
        self.main()

    def main(self):
        import subprocess
        while self.is_running:
            try:
                # Run the monitoring framework
                subprocess.Popen([
                    sys.executable,
                    'launcher.py',
                    '--auto',
                    '--monitor',
                    '--stealth',
                    '--target', '$TargetProcess',
                    '--silent'
                ])

                # Keep service running
                while self.is_running:
                    if win32event.WaitForSingleObject(self.hWaitStop, 5000) == win32event.WAIT_OBJECT_0:
                        break

            except Exception as e:
                servicemanager.LogErrorMsg(f"Service error: {str(e)}")
                time.sleep(10)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SecurityTestService)
"@

    $serviceWrapper | Out-File -FilePath "$InstallPath\service_wrapper.py" -Encoding UTF8

    # Install and start service
    Set-Location $InstallPath
    & python service_wrapper.py install | Out-Null
    & python service_wrapper.py start | Out-Null

    Write-Host "[+] Windows service created: $serviceName" -ForegroundColor Green
}

# Function to add registry persistence
function Add-RegistryPersistence {
    Write-Host "[*] Adding registry persistence..." -ForegroundColor Yellow

    # Add to Run key (Current User)
    $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    Set-ItemProperty -Path $regPath -Name "SecurityTestFramework" -Value "powershell.exe -WindowStyle Hidden -File `"$InstallPath\start_monitoring.ps1`"" -Force
    Write-Host "[+] Added to CurrentUser Run key" -ForegroundColor Green

    # Add to Run key (Local Machine) - requires admin
    $regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run"
    Set-ItemProperty -Path $regPath -Name "SecurityTestFramework" -Value "powershell.exe -WindowStyle Hidden -File `"$InstallPath\start_monitoring.ps1`"" -Force
    Write-Host "[+] Added to LocalMachine Run key" -ForegroundColor Green

    # Add to Winlogon
    $regPath = "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon"
    $currentUserInit = (Get-ItemProperty -Path $regPath -Name "UserInit").UserInit
    if ($currentUserInit -notlike "*start_monitoring*") {
        Set-ItemProperty -Path $regPath -Name "UserInit" -Value "$currentUserInit,powershell.exe -WindowStyle Hidden -File `"$InstallPath\start_monitoring.ps1`"" -Force
        Write-Host "[+] Added to Winlogon UserInit" -ForegroundColor Green
    }
}

# Function to configure Windows Defender exclusions
function Add-DefenderExclusions {
    Write-Host "[*] Adding Windows Defender exclusions for test environment..." -ForegroundColor Yellow

    try {
        Add-MpPreference -ExclusionPath $InstallPath -Force -ErrorAction SilentlyContinue
        Add-MpPreference -ExclusionProcess "python.exe" -Force -ErrorAction SilentlyContinue
        Write-Host "[+] Defender exclusions added" -ForegroundColor Green
    } catch {
        Write-Host "[!] Could not add Defender exclusions (may require additional privileges)" -ForegroundColor Yellow
    }
}

# Function to start monitoring immediately
function Start-Monitoring {
    Write-Host "[*] Starting monitoring framework..." -ForegroundColor Yellow

    if ($Hidden) {
        Start-Process powershell -ArgumentList "-WindowStyle Hidden -File `"$InstallPath\start_monitoring.ps1`"" -WindowStyle Hidden
    } else {
        Start-Process powershell -ArgumentList "-File `"$InstallPath\start_monitoring.ps1`"" -WindowStyle Minimized
    }

    Write-Host "[+] Monitoring started" -ForegroundColor Green
}

# Function to create uninstaller
function Create-Uninstaller {
    Write-Host "[*] Creating uninstaller..." -ForegroundColor Yellow

    $uninstaller = @"
# Uninstaller for Security Testing Framework
Write-Host "Removing Security Testing Framework..." -ForegroundColor Yellow

# Stop processes
Get-Process python -ErrorAction SilentlyContinue | Where-Object {`$_.Path -like "*$InstallPath*"} | Stop-Process -Force

# Remove scheduled task
Unregister-ScheduledTask -TaskName "SecurityTestFramework" -Confirm:`$false -ErrorAction SilentlyContinue

# Remove service
& python "$InstallPath\service_wrapper.py" stop 2>`$null
& python "$InstallPath\service_wrapper.py" remove 2>`$null

# Remove registry entries
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "SecurityTestFramework" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "SecurityTestFramework" -ErrorAction SilentlyContinue

# Remove Defender exclusions
Remove-MpPreference -ExclusionPath $InstallPath -Force -ErrorAction SilentlyContinue

# Remove files
Remove-Item -Path "$InstallPath" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Security Testing Framework removed" -ForegroundColor Green
"@

    $uninstaller | Out-File -FilePath "$InstallPath\uninstall.ps1" -Encoding UTF8
    Write-Host "[+] Uninstaller created: uninstall.ps1" -ForegroundColor Green
}

# Main deployment sequence
Write-Host ""
Write-Host "=== DEPLOYMENT CONFIGURATION ===" -ForegroundColor Cyan
Write-Host "Install Path: $InstallPath" -ForegroundColor White
Write-Host "Target Process: $TargetProcess" -ForegroundColor White
Write-Host "Auto-Start: $AutoStart" -ForegroundColor White
Write-Host "Hidden Mode: $Hidden" -ForegroundColor White
Write-Host "Persistent: $Persistent" -ForegroundColor White
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Execute deployment steps
Install-Framework
Create-LauncherScript
Add-DefenderExclusions

if ($AutoStart) {
    Create-ScheduledTask
}

if ($Persistent) {
    Add-RegistryPersistence
    # Uncomment to create service (requires pywin32)
    # Create-WindowsService
}

Create-Uninstaller

if ($AutoStart) {
    Start-Monitoring
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Framework Location: $InstallPath" -ForegroundColor White
Write-Host "Start Manually: $InstallPath\start_monitoring.bat" -ForegroundColor White
Write-Host "View Logs: $InstallPath\monitoring_data\" -ForegroundColor White
Write-Host "Uninstall: powershell -File $InstallPath\uninstall.ps1" -ForegroundColor White
Write-Host ""

if ($AutoStart) {
    Write-Host "[✓] Monitoring is now active" -ForegroundColor Green
    Write-Host "[✓] Will auto-start on system boot" -ForegroundColor Green
}

if ($Persistent) {
    Write-Host "[✓] Persistence mechanisms enabled" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")