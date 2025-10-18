param(
    [string]$InstallPath = "$env:LOCALAPPDATA\SecurityTestingFramework",
    [string]$Version = "latest",
    [switch]$NoDesktopShortcut,
    [switch]$NoStartMenu,
    [switch]$Portable,
    [switch]$Silent
)

$ErrorActionPreference = "Stop"

# Config
$RepoOwner = "hira-edu"
$RepoName = "security-testing-framework"
$AppName = "SecurityTestingFramework"

if (-not $Silent) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host " Security Testing Framework - PowerShell Installer" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
}

# Check admin (for PATH change only)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "Warning: Not running as administrator (some features may be limited)." -ForegroundColor Yellow
}

try {
    # Step 1: Resolve download URL
    Write-Host "[1/6] Fetching release information..." -ForegroundColor Green
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $DownloadUrl = $null
    $ReleaseVersion = $Version
    try {
        $ApiUrl = if ($Version -eq "latest") { "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest" } else { "https://api.github.com/repos/$RepoOwner/$RepoName/releases/tags/$Version" }
        $Release = Invoke-RestMethod -Uri $ApiUrl -Headers @{ "User-Agent" = "PowerShell"; "Accept" = "application/vnd.github.v3+json" }
        if ($Release) {
            $ReleaseVersion = $Release.tag_name
            $Asset = $Release.assets | Where-Object { $_.name -like "*$AppName*.exe" } | Select-Object -First 1
            if ($Asset) {
                $DownloadUrl = $Asset.browser_download_url
                $SizeMB = [math]::Round(($Asset.size/1MB),2)
                Write-Host "   Found version: $ReleaseVersion ($SizeMB MB)" -ForegroundColor Gray
            }
        }
    } catch {}
    if (-not $DownloadUrl) {
        $DownloadUrl = "https://github.com/$RepoOwner/$RepoName/releases/latest/download/$AppName.exe"
        if (-not $ReleaseVersion) { $ReleaseVersion = "latest" }
        Write-Host "   Using fallback download URL" -ForegroundColor Yellow
    }

    # Step 2: Prepare install dir (hardened)
    Write-Host "[2/6] Preparing installation directory..." -ForegroundColor Green
    function Test-PathWritable([string]$p) {
        try {
            if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
            $t = Join-Path $p '.__writetest'
            Set-Content -Path $t -Value 'ok' -Force -ErrorAction Stop
            Remove-Item $t -Force -ErrorAction SilentlyContinue
            return $true
        } catch { return $false }
    }
    if ($Portable) { $InstallPath = (Get-Location).Path; Write-Host "   Portable mode: current directory" -ForegroundColor Gray }
    $candidates = @()
    if ($InstallPath) { $candidates += $InstallPath }
    if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA $AppName) }
    if ($env:USERPROFILE) {
        $candidates += (Join-Path $env:USERPROFILE ("AppData\Local\{0}" -f $AppName))
        $candidates += (Join-Path $env:USERPROFILE $AppName)
    }
    if ($env:TEMP) { $candidates += (Join-Path $env:TEMP $AppName) }
    $resolved = $null
    foreach ($p in $candidates) { if (Test-PathWritable $p) { $resolved = $p; break } }
    if (-not $resolved) { throw "Unable to find a writable installation directory" }
    $InstallPath = $resolved
    Write-Host "   Install path: $InstallPath" -ForegroundColor Gray

    # Step 3: Download
    Write-Host "[3/6] Downloading Security Testing Framework..." -ForegroundColor Green
    Write-Host "   URL: $DownloadUrl" -ForegroundColor Gray
    $ExePath = Join-Path $InstallPath ("{0}.exe" -f $AppName)
    $Tmp = Join-Path $env:TEMP ("{0}.tmp" -f $AppName)
    try {
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $Tmp -UseBasicParsing
        Move-Item -Path $Tmp -Destination $ExePath -Force
        Write-Host "   Download complete" -ForegroundColor Green
    } catch {
        throw "Download failed: $($_.Exception.Message)"
    }

    # Step 4: Verify
    Write-Host "[4/6] Verifying download..." -ForegroundColor Green
    if (-not (Test-Path $ExePath)) { throw "Download verification failed - file not found" }
    $sz = [math]::Round(((Get-Item $ExePath).Length/1MB),2)
    Write-Host "   File size: $sz MB" -ForegroundColor Gray

    # Step 5: Shortcuts
    if (-not $Portable) {
        Write-Host "[5/6] Creating shortcuts..." -ForegroundColor Green

        # Check if running as SYSTEM (no user profile)
        $isSystem = $env:USERNAME -eq "SYSTEM" -or [string]::IsNullOrEmpty($env:USERPROFILE) -or $env:USERPROFILE -like "*systemprofile*"

        if ($isSystem) {
            Write-Host "   Running as SYSTEM - skipping user shortcuts" -ForegroundColor Yellow
        } else {
            try {
                $W = New-Object -ComObject WScript.Shell

                if (-not $NoDesktopShortcut) {
                    $Desktop = [Environment]::GetFolderPath("Desktop")
                    if (![string]::IsNullOrEmpty($Desktop) -and (Test-Path (Split-Path $Desktop -Parent))) {
                        $S = $W.CreateShortcut((Join-Path $Desktop "Security Testing Framework.lnk"))
                        $S.TargetPath = $ExePath; $S.WorkingDirectory = $InstallPath; $S.Description = "Security Testing Framework"; $S.Save()
                        Write-Host "   Desktop shortcut created" -ForegroundColor Green
                    }
                }

                if (-not $NoStartMenu) {
                    $StartMenu = [Environment]::GetFolderPath("StartMenu")
                    if (![string]::IsNullOrEmpty($StartMenu) -and (Test-Path (Split-Path $StartMenu -Parent))) {
                        $Prog = Join-Path $StartMenu "Programs\Security Testing Framework"
                        if (-not (Test-Path $Prog)) { New-Item -ItemType Directory -Path $Prog -Force | Out-Null }
                        $S = $W.CreateShortcut((Join-Path $Prog "Security Testing Framework.lnk"))
                        $S.TargetPath = $ExePath; $S.WorkingDirectory = $InstallPath; $S.Description = "Security Testing Framework"; $S.Save()
                        Write-Host "   Start menu entry created" -ForegroundColor Green
                    }
                }
            } catch {
                Write-Host "   Shortcuts skipped (profile unavailable)" -ForegroundColor Yellow
            }
        }
        if ($isAdmin) {
            $MachinePath = [Environment]::GetEnvironmentVariable("Path","Machine")
            if ($MachinePath -and ($MachinePath -notlike ("*{0}*" -f $InstallPath))) {
                [Environment]::SetEnvironmentVariable("Path", ($MachinePath + ";" + $InstallPath), "Machine")
                Write-Host "   Added to system PATH" -ForegroundColor Green
            }
        }
    }

    # Step 6: Uninstaller
    if (-not $Portable) {
        Write-Host "[6/6] Creating uninstaller..." -ForegroundColor Green
        $UninstallPath = Join-Path $InstallPath "uninstall.ps1"
        @"
# Security Testing Framework Uninstaller
param()
Write-Host 'Uninstalling Security Testing Framework...'
if (Test-Path '$ExePath') { Remove-Item -Path '$ExePath' -Force }
$Desktop = [Environment]::GetFolderPath('Desktop')
if (Test-Path (Join-Path $Desktop 'Security Testing Framework.lnk')) { Remove-Item (Join-Path $Desktop 'Security Testing Framework.lnk') -Force }
$StartMenu = [Environment]::GetFolderPath('StartMenu')
$SMPath = Join-Path $StartMenu 'Programs\Security Testing Framework'
if (Test-Path $SMPath) { Remove-Item -Path $SMPath -Recurse -Force }
Write-Host 'Uninstallation complete!' -ForegroundColor Green
"@ | Out-File -FilePath $UninstallPath -Encoding UTF8
        Write-Host "   Uninstaller created" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "INSTALLATION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "Installed to: $ExePath" -ForegroundColor Cyan
    if (-not $Portable) { Write-Host "Uninstall: Run $InstallPath\uninstall.ps1" -ForegroundColor Cyan }
    if (-not $Silent) {
        $Run = Read-Host "Run Security Testing Framework now? (Y/N)"
        if ($Run -match '^[Yy]$') { Start-Process -FilePath $ExePath }
    }
} catch {
    Write-Host "INSTALLATION FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Try downloading from: https://github.com/$RepoOwner/$RepoName/releases" -ForegroundColor Yellow
    exit 1
}
