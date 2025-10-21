# Security Testing Framework - Test Environment Deployment Script
# WARNING: Only use in environments you control.
# One-line launcher (elevated PowerShell):
#   iwr "https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/deploy_test_environment.ps1" -OutFile "$env:TEMP\stf_deploy.ps1" -UseBasicParsing; \
#   & "$env:TEMP\stf_deploy.ps1" -InstallPath "C:\SecurityTestFramework" -TargetProcess "LockDownBrowser.exe" -AutoStart -Hidden -Persistent

[CmdletBinding()]
param(
    [Parameter()]
    [string]$InstallPath = "C:\SecurityTestFramework",

    [Parameter()]
    [string]$TargetProcess = "LockDownBrowser.exe",

    [Parameter()]
    [switch]$AutoStart = $true,

    [Parameter()]
    [switch]$Hidden = $true,

    [Parameter()]
    [switch]$Persistent = $true,

    [Parameter()]
    [string]$MonitoringDuration = "0",  # 0 = run indefinitely

    [Parameter()]
    [string]$ReleaseTag = "latest",

    [Parameter()]
    [string]$ReleaseOwner = "hira-edu",

    [Parameter()]
    [string]$ReleaseRepo = "security-testing-framework",

    [Parameter()]
    [string]$AssetName = "SecurityTestingFramework.exe"
)

# -- Helper Functions -------------------------------------------------------
function Test-Admin {
    return ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
}

function Ensure-Admin {
    if (-not (Test-Admin)) {
        Write-Host "[!] Elevation required – relaunching with admin rights." -ForegroundColor Yellow
        $args = $MyInvocation.UnboundArguments
        Start-Process PowerShell -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath) + $args
        exit
    }
}

function Get-ReleaseAssetUrl {
    param(
        [string]$Owner,
        [string]$Repo,
        [string]$Tag,
        [string]$Asset
    )

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $apiUrl = if ($Tag -eq "latest") {
        "https://api.github.com/repos/$Owner/$Repo/releases/latest"
    } else {
        "https://api.github.com/repos/$Owner/$Repo/releases/tags/$Tag"
    }

    try {
        $release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "PowerShell"; "Accept" = "application/vnd.github.v3+json" }
        $assetMatch = $release.assets | Where-Object { $_.name -eq $Asset } | Select-Object -First 1
        if ($assetMatch) {
            return @{ Url = $assetMatch.browser_download_url; Version = $release.tag_name }
        }
    } catch {
        Write-Host "[!] GitHub API lookup failed, falling back to latest asset." -ForegroundColor Yellow
    }

    return @{ Url = "https://github.com/$Owner/$Repo/releases/latest/download/$Asset"; Version = ($Tag -eq "latest" ? "latest" : $Tag) }
}

function Write-ConfigJson {
    param(
        [string]$Path,
        [string]$Target
    )

    $config = [ordered]@{
        version        = "1.0.0"
        build_time     = (Get-Date -Format "yyyyMMdd_HHmmss")
        security_level = "HIGH"
        enable_logging = $true
        stealth_mode   = $true
        auto_update    = $true
        modules        = [ordered]@{
            screen_capture   = $true
            process_monitor  = $true
            api_hooks        = $true
            memory_scanner   = $true
            network_monitor  = $true
            gui              = $false
        }
        capture = [ordered]@{
            method           = "enhanced_capture"
            fallback_chain   = @("windows_graphics_capture","dxgi_desktop_duplication","direct3d_capture","gdi_capture")
            frame_rate       = 60
            quality          = "high"
            compression      = $true
            compression_level= 6
            hardware_acceleration = $true
            buffer_size      = 10485760
        }
        hooks = [ordered]@{
            directx = [ordered]@{
                enabled    = $true
                versions   = @("11","12")
                interfaces = @("IDXGISwapChain","ID3D11Device","ID3D12Device")
            }
            windows_api = [ordered]@{
                enabled   = $true
                functions = @("SetForegroundWindow","GetForegroundWindow","CreateProcess","TerminateProcess")
            }
            keyboard = [ordered]@{
                enabled      = $true
                blocked_keys = @("F12","VK_SNAPSHOT")
                hotkeys      = @{ "ctrl+alt+s" = "screenshot"; "ctrl+alt+q" = "quit" }
            }
            process = [ordered]@{
                enabled = $false
            }
        }
        performance = [ordered]@{
            monitoring        = $true
            sampling_interval = 1000
            memory_tracking   = $true
            leak_threshold    = 1048576
            optimization      = [ordered]@{
                memory_pool            = $true
                thread_pool            = $true
                hardware_acceleration  = $true
            }
            limits = [ordered]@{
                max_cpu_usage    = 80.0
                max_memory_usage = 1073741824
                max_frame_rate   = 60
            }
        }
        security = [ordered]@{
            anti_detection    = $true
            obfuscation       = $false
            integrity_checking= $true
        }
        logging = [ordered]@{
            level          = "medium"
            file           = "undownunlock.log"
            console_output = $true
        }
        bypass_methods = [ordered]@{
            enabled      = $true
            package_root = "src.external.bypass_methods"
            native       = [ordered]@{
                dll        = "native/bypass_methods/dll/UndownUnlockDXHook.dll"
                auto_stage = $true
            }
            features     = [ordered]@{
                capture  = $true
                api_hooks= $true
                security = $true
                gui      = $false
            }
        }
        $targetList = [System.Collections.Generic.List[string]]::new()
        foreach ($defaultTarget in @(
            "LockDownBrowser.exe",
            "LockDownBrowserOEM.exe",
            "Lockdown.exe",
            "SafeExamBrowser.exe",
            "Respondus.exe",
            "OnVUE.exe",
            "ProProctor.exe",
            "ETSBrowser.exe",
            "Prometric.exe",
            "ProctorTrack.exe",
            "ExamitySecureBrowser.exe",
            "Examplify.exe",
            "RPNow.exe",
            "GuardianBrowser.exe",
            "HonorlockBrowser.exe"
        )) {
            $targetList.Add($defaultTarget)
        }
        if ($Target -and -not $targetList.Contains($Target)) {
            $targetList.Add($Target)
        }
        targets = $targetList.ToArray()
    }

    $config | ConvertTo-Json -Depth 6 | Set-Content -Path $Path -Encoding UTF8
}

function Install-Framework {
    param(
        [string]$Owner,
        [string]$Repo,
        [string]$Tag,
        [string]$Asset,
        [string]$Destination
    )

    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
    foreach ($sub in @("logs","captures","native","data")) {
        New-Item -ItemType Directory -Path (Join-Path $Destination $sub) -Force | Out-Null
    }

    $assetInfo = Get-ReleaseAssetUrl -Owner $Owner -Repo $Repo -Tag $Tag -Asset $Asset
    $downloadUrl = $assetInfo.Url
    $version = $assetInfo.Version

    Write-Host "[*] Downloading release $version" -ForegroundColor Yellow
    Write-Host "    $downloadUrl" -ForegroundColor Gray

    $tempExe = Join-Path $env:TEMP $Asset
    Remove-Item $tempExe -Force -ErrorAction SilentlyContinue

    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempExe -UseBasicParsing
    Copy-Item $tempExe -Destination (Join-Path $Destination $Asset) -Force
    Remove-Item $tempExe -Force -ErrorAction SilentlyContinue

    Write-Host "[+] Executable staged at $(Join-Path $Destination $Asset)" -ForegroundColor Green
    return (Join-Path $Destination $Asset)
}

function New-LaunchScripts {
    param(
        [string]$InstallPath,
        [string]$ExePath,
        [string]$ConfigPath,
        [string]$Target,
        [string]$Duration,
        [switch]$Hidden
    )

    $args = @(
        "--auto",
        "--monitor",
        "--stealth",
        "--comprehensive",
        "--target", $Target,
        "--duration", $Duration,
        "--silent",
        "--export", (Join-Path $InstallPath "monitoring_data"),
        "--config", $ConfigPath
    )

    $exeLeaf = [System.IO.Path]::GetFileName($ExePath)
    $exeName = [System.IO.Path]::GetFileNameWithoutExtension($ExePath)

    $bat = @"
@echo off
cd /d "$InstallPath"
set STF_EXE="$ExePath"
:: stop current instance
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq $exeLeaf" ^| findstr /I $exeLeaf') do taskkill /PID %%i /F >nul 2>&1
start "SecurityTestingFramework" /MIN %STF_EXE% $($args -join ' ')
exit
"@
    $bat | Out-File -FilePath (Join-Path $InstallPath "start_monitoring.bat") -Encoding ASCII

    $ps = @"
param()
Set-Location "$InstallPath"
Stop-Process -Name "$exeName" -Force -ErrorAction SilentlyContinue
Start-Process "$ExePath" -ArgumentList $args -WindowStyle $([string]($Hidden ? "Hidden" : "Minimized"))
"@
    $ps | Out-File -FilePath (Join-Path $InstallPath "start_monitoring.ps1") -Encoding UTF8
}

function Register-Autostart {
    param(
        [string]$ExePath,
        [string[]]$Arguments,
        [switch]$Hidden
    )

    $taskName = "SecurityTestingFramework"
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    $argString = $Arguments -join ' '
    $action = New-ScheduledTaskAction -Execute $ExePath -Argument $argString -WorkingDirectory (Split-Path $ExePath -Parent)
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden -StartWhenAvailable

    try {
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    } catch {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    }
    Write-Host "[+] Scheduled task registered ($taskName)" -ForegroundColor Green

    if ($Persistent) {
        $cmd = "`"$ExePath`" $argString"
        Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "SecurityTestingFramework" -Value $cmd -Force
        Set-ItemProperty -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "SecurityTestingFramework" -Value $cmd -Force
        Write-Host "[+] Registry persistence added" -ForegroundColor Green
    }
}

function Start-Monitoring {
    param(
        [string]$ExePath,
        [string[]]$Arguments,
        [switch]$Hidden
    )

    $exeName = [System.IO.Path]::GetFileNameWithoutExtension($ExePath)
    Stop-Process -Name $exeName -Force -ErrorAction SilentlyContinue
    Start-Process $ExePath -ArgumentList $Arguments -WindowStyle ($Hidden ? "Hidden" : "Minimized")
    Write-Host "[+] Monitoring session started" -ForegroundColor Green
}

function New-Uninstaller {
    param(
        [string]$InstallPath,
        [string]$ExePath
    )

    $script = @"
Write-Host 'Removing Security Testing Framework...' -ForegroundColor Yellow
Stop-Process -Name '$([System.IO.Path]::GetFileNameWithoutExtension($ExePath))' -Force -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName SecurityTestingFramework -Confirm:$false -ErrorAction SilentlyContinue
Remove-Item 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run\SecurityTestingFramework' -ErrorAction SilentlyContinue
Remove-Item 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run\SecurityTestingFramework' -ErrorAction SilentlyContinue
Remove-Item '$InstallPath' -Recurse -Force -ErrorAction SilentlyContinue
Write-Host 'Uninstall complete.' -ForegroundColor Green
"@
    $script | Out-File -FilePath (Join-Path $InstallPath "uninstall.ps1") -Encoding UTF8
}

# -- Main -------------------------------------------------------------------
Ensure-Admin

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "SECURITY TESTING FRAMEWORK DEPLOYMENT" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$exePath = Install-Framework -Owner $ReleaseOwner -Repo $ReleaseRepo -Tag $ReleaseTag -Asset $AssetName -Destination $InstallPath
$configPath = Join-Path $InstallPath "config.json"
Write-ConfigJson -Path $configPath -Target $TargetProcess
Write-Host "[+] Configuration written to $configPath" -ForegroundColor Green

$args = @(
    "--auto",
    "--monitor",
    "--stealth",
    "--comprehensive",
    "--target", $TargetProcess,
    "--duration", $MonitoringDuration,
    "--silent",
    "--export", (Join-Path $InstallPath "monitoring_data"),
    "--config", $configPath
)

$processName = [System.IO.Path]::GetFileNameWithoutExtension($exePath)

New-LaunchScripts -InstallPath $InstallPath -ExePath $exePath -ConfigPath $configPath -Target $TargetProcess -Duration $MonitoringDuration -Hidden:$Hidden
New-Uninstaller -InstallPath $InstallPath -ExePath $exePath

if ($AutoStart) {
    Register-Autostart -ExePath $exePath -Arguments $args -Hidden:$Hidden -Persistent:$Persistent
}

Start-Monitoring -ExePath $exePath -Arguments $args -Hidden:$Hidden

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " DEPLOYMENT COMPLETE" -ForegroundColor Cyan
Write-Host " Executable : $exePath" -ForegroundColor Cyan
Write-Host " Config     : $configPath" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
