#Requires -RunAsAdministrator
<#!
.SYNOPSIS
    Hot Deployment wrapper that pulls the latest Security Testing Framework release and enables autonomous monitoring.
.DESCRIPTION
    Downloads the latest prebuilt executable from GitHub, writes the full configuration, registers persistence,
    and kicks off monitoring/injection with stealth options enabled. This is a higher-level wrapper around
    deploy_test_environment.ps1 for quick red/blue team exercises.
.EXAMPLE
    .\HOT_DEPLOY.ps1 -TargetProcess "LockDownBrowser.exe" -Stealth
.EXAMPLE
    irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/HOT_DEPLOY.ps1 | iex
#>

param(
    [string]$InstallPath = "$env:LOCALAPPDATA\SecurityTestingFramework",
    [string]$TargetProcess = "LockDownBrowser.exe",
    [switch]$Stealth = $true,
    [switch]$Hidden = $true,
    [switch]$Persistent = $true,
    [switch]$AutoStart = $true,
    [string]$MonitoringDuration = "0",
    [string]$ReleaseTag = "latest",
    [string]$ReleaseOwner = "hira-edu",
    [string]$ReleaseRepo = "security-testing-framework",
    [string]$AssetName = "SecurityTestingFramework.exe"
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  SECURITY TESTING FRAMEWORK - HOT DEPLOYMENT          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$deployScript = Join-Path $env:TEMP "stf_deploy.ps1"

Write-Host "[*] Downloading deployment helper..." -ForegroundColor Yellow
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/$ReleaseOwner/$ReleaseRepo/main/deploy_test_environment.ps1" -OutFile $deployScript -UseBasicParsing

$deployParams = @{
    InstallPath         = $InstallPath
    TargetProcess       = $TargetProcess
    AutoStart           = $AutoStart
    Hidden              = $Hidden
    Persistent          = $Persistent
    MonitoringDuration  = $MonitoringDuration
    ReleaseTag          = $ReleaseTag
    ReleaseOwner        = $ReleaseOwner
    ReleaseRepo         = $ReleaseRepo
    AssetName           = $AssetName
}

Write-Host "[*] Staging latest release and configuration..." -ForegroundColor Yellow
& $deployScript @deployParams
Remove-Item $deployScript -Force -ErrorAction SilentlyContinue

# Optional hardening/exclusions for red-team style execution
try {
    Add-MpPreference -ExclusionPath $InstallPath -Force -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionProcess "$InstallPath\$AssetName" -Force -ErrorAction SilentlyContinue
    Write-Host "[+] Defender exclusions applied" -ForegroundColor Green
} catch {
    Write-Host "[!] Could not add Defender exclusions (non-fatal)" -ForegroundColor Yellow
}

Write-Host "`nDeployment complete." -ForegroundColor Green
Write-Host "Executable : $InstallPath\$AssetName" -ForegroundColor Cyan
Write-Host "Config     : $InstallPath\config.json" -ForegroundColor Cyan
Write-Host "Run again : & \"$InstallPath\\$AssetName\" --auto --monitor --stealth --target '$TargetProcess' --config \"$InstallPath\\config.json\"" -ForegroundColor Yellow
