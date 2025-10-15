# Quick Deploy - One-Line Deployment Script
# Run this with: irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/quick_deploy.ps1 | iex

# Quick deployment with maximum capabilities
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Download and execute main deployment script
$deployUrl = "https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/deploy_test_environment.ps1"
$deployScript = (New-Object Net.WebClient).DownloadString($deployUrl)

# Execute with all features enabled
$scriptBlock = [ScriptBlock]::Create($deployScript)
& $scriptBlock -InstallPath "C:\SecurityTestFramework" `
             -TargetProcess "LockDownBrowser.exe" `
             -AutoStart `
             -Hidden `
             -Persistent `
             -MonitoringDuration "0"

Write-Host "`n[DEPLOYMENT COMPLETE]" -ForegroundColor Green
Write-Host "Framework is now monitoring in the background" -ForegroundColor Green
Write-Host "Data will be saved to: C:\SecurityTestFramework\monitoring_data\" -ForegroundColor Yellow