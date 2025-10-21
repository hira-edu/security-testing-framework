# Quick Deploy - One-Line Deployment Script
# Run from an elevated PowerShell prompt:
#   irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/quick_deploy.ps1 | iex

param(
    [string]$InstallPath = "C:\SecurityTestFramework",
    [string]$TargetProcess = "LockDownBrowser.exe",
    [switch]$AutoStart = $true,
    [switch]$Hidden = $true,
    [switch]$Persistent = $true,
    [string]$MonitoringDuration = "0",
    [string]$ReleaseTag = "latest",
    [string]$ReleaseOwner = "hira-edu",
    [string]$ReleaseRepo = "security-testing-framework",
    [string]$AssetName = "SecurityTestingFramework.exe"
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$deployPath = Join-Path $env:TEMP "stf_deploy.ps1"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/$ReleaseOwner/$ReleaseRepo/main/deploy_test_environment.ps1" `
    -OutFile $deployPath -UseBasicParsing

& $deployPath `
    -InstallPath $InstallPath `
    -TargetProcess $TargetProcess `
    -AutoStart:$AutoStart `
    -Hidden:$Hidden `
    -Persistent:$Persistent `
    -MonitoringDuration $MonitoringDuration `
    -ReleaseTag $ReleaseTag `
    -ReleaseOwner $ReleaseOwner `
    -ReleaseRepo $ReleaseRepo `
    -AssetName $AssetName

Remove-Item $deployPath -Force -ErrorAction SilentlyContinue

Write-Host "`n[DEPLOYMENT COMPLETE]" -ForegroundColor Green
Write-Host "Framework deployed to: $InstallPath" -ForegroundColor Green
Write-Host "Monitoring data directory: $InstallPath\monitoring_data" -ForegroundColor Yellow
