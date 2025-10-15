# Security Testing Framework - PowerShell Installer
# Usage: irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.ps1 | iex
# Or: iwr -useb https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.ps1 | iex

param(
    [string]$InstallPath = "$env:LOCALAPPDATA\SecurityTestingFramework",
    [string]$Version = "latest",
    [switch]$NoDesktopShortcut,
    [switch]$NoStartMenu,
    [switch]$Portable,
    [switch]$Silent
)

$ErrorActionPreference = "Stop"

# Configuration
$RepoOwner = "hira-edu"
$RepoName = "security-testing-framework"
$AppName = "SecurityTestingFramework"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Banner
if (-not $Silent) {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║     Security Testing Framework - PowerShell Installer        ║" -ForegroundColor Cyan
    Write-Host "║                  Professional Security Tools                 ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "⚠️  Warning: Not running as administrator. Some features may be limited." -ForegroundColor Yellow
    Write-Host "   For full functionality, run PowerShell as Administrator." -ForegroundColor Yellow
    Write-Host ""
}

try {
    # Step 1: Get release information
    Write-Host "[1/6] Fetching release information..." -ForegroundColor Green

    $ApiUrl = if ($Version -eq "latest") {
        "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"
    } else {
        "https://api.github.com/repos/$RepoOwner/$RepoName/releases/tags/$Version"
    }

    # Use TLS 1.2 for GitHub API
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    try {
        $Release = Invoke-RestMethod -Uri $ApiUrl -Headers @{
            "User-Agent" = "PowerShell"
            "Accept" = "application/vnd.github.v3+json"
        }
    } catch {
        # Fallback to direct download if API fails
        Write-Host "⚠️  GitHub API unavailable, using direct download..." -ForegroundColor Yellow
        $DownloadUrl = "https://github.com/$RepoOwner/$RepoName/releases/latest/download/$AppName.exe"
        $ReleaseVersion = "latest"
    }

    if ($Release) {
        $ReleaseVersion = $Release.tag_name
        $Asset = $Release.assets | Where-Object { $_.name -like "*$AppName*.exe" } | Select-Object -First 1

        if ($Asset) {
            $DownloadUrl = $Asset.browser_download_url
            $FileSize = [math]::Round($Asset.size / 1MB, 2)
            Write-Host "   Found version: $ReleaseVersion ($FileSize MB)" -ForegroundColor Gray
        } else {
            # Try to construct URL if asset not found
            $DownloadUrl = "https://github.com/$RepoOwner/$RepoName/releases/download/$ReleaseVersion/$AppName.exe"
            Write-Host "   Version: $ReleaseVersion" -ForegroundColor Gray
        }
    }

    # Step 2: Create installation directory
    Write-Host "[2/6] Preparing installation directory..." -ForegroundColor Green

    if ($Portable) {
        $InstallPath = Get-Location
        Write-Host "   Portable mode: Installing to current directory" -ForegroundColor Gray
    } else {
        # Normalize and harden InstallPath selection for non-admin/svc contexts
        # 1) If LOCALAPPDATA points to systemprofile or is empty, prefer USERPROFILE
        # 2) If path is not writable, fall back to user-writable locations

        function Test-PathWritable([string]$p) {
            try {
                if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
                $test = Join-Path $p '.__writetest'
                Set-Content -Path $test -Value 'ok' -Force -ErrorAction Stop
                Remove-Item $test -Force -ErrorAction SilentlyContinue
                return $true
            } catch { return $false }
        }

        $resolved = $InstallPath
        $isSystemProfile = $resolved -match "\\Windows\\System32\\config\\systemprofile\\"
        if ($isSystemProfile -and $env:USERPROFILE) {
            $resolved = Join-Path $env:USERPROFILE 'AppData\\Local\\SecurityTestingFramework'
        }

        if (-not (Test-PathWritable $resolved)) {
            if ($env:USERPROFILE) {
                $candidate = Join-Path $env:USERPROFILE 'SecurityTestingFramework'
                if (Test-PathWritable $candidate) { $resolved = $candidate }
            }
        }
        if (-not (Test-PathWritable $resolved)) {
            if ($env:TEMP) {
                $candidate = Join-Path $env:TEMP 'SecurityTestingFramework'
                if (Test-PathWritable $candidate) { $resolved = $candidate }
            }
        }

        if (-not (Test-PathWritable $resolved)) {
            throw "Unable to find a writable installation directory (tried LOCALAPPDATA, USERPROFILE, TEMP)."
        }

        $InstallPath = $resolved
        if (-not (Test-Path $InstallPath)) { New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null }
        Write-Host "   Install path: $InstallPath" -ForegroundColor Gray
    }

    # Step 3: Download the executable
    Write-Host "[3/6] Downloading Security Testing Framework..." -ForegroundColor Green
    Write-Host "   URL: $DownloadUrl" -ForegroundColor Gray

    $ExePath = Join-Path $InstallPath "$AppName.exe"
    $TempPath = Join-Path $env:TEMP "$AppName.tmp"

    # Download with progress bar
    $ProgressPreference = 'SilentlyContinue'
    if (-not $Silent) {
        $ProgressPreference = 'Continue'
    }

    try {
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempPath -UseBasicParsing
        Move-Item -Path $TempPath -Destination $ExePath -Force
        Write-Host "   ✓ Download complete" -ForegroundColor Green
    } catch {
        Write-Host "❌ Download failed: $_" -ForegroundColor Red

        # Alternative download methods
        Write-Host "   Trying alternative download method..." -ForegroundColor Yellow

        # Try with System.Net.WebClient
        try {
            $WebClient = New-Object System.Net.WebClient
            $WebClient.Headers.Add("User-Agent", "PowerShell")
            $WebClient.DownloadFile($DownloadUrl, $ExePath)
            Write-Host "   ✓ Download complete (alternative method)" -ForegroundColor Green
        } catch {
            # Try with curl if available
            if (Get-Command curl -ErrorAction SilentlyContinue) {
                curl -L -o $ExePath $DownloadUrl
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "   ✓ Download complete (curl)" -ForegroundColor Green
                } else {
                    throw "All download methods failed"
                }
            } else {
                throw "All download methods failed"
            }
        }
    }

    # Step 4: Verify download
    Write-Host "[4/6] Verifying download..." -ForegroundColor Green

    if (Test-Path $ExePath) {
        $FileInfo = Get-Item $ExePath
        $FileSizeMB = [math]::Round($FileInfo.Length / 1MB, 2)
        Write-Host "   File size: $FileSizeMB MB" -ForegroundColor Gray

        # Optional: Add hash verification here
        # $Hash = Get-FileHash $ExePath -Algorithm SHA256
        # Write-Host "   SHA256: $($Hash.Hash)" -ForegroundColor Gray
    } else {
        throw "Download verification failed - file not found"
    }

    # Step 5: Create shortcuts (unless portable or disabled)
    if (-not $Portable) {
        Write-Host "[5/6] Creating shortcuts..." -ForegroundColor Green

        $WshShell = New-Object -ComObject WScript.Shell

        # Desktop shortcut
        if (-not $NoDesktopShortcut) {
            $DesktopPath = [Environment]::GetFolderPath("Desktop")
            $Shortcut = $WshShell.CreateShortcut("$DesktopPath\Security Testing Framework.lnk")
            $Shortcut.TargetPath = $ExePath
            $Shortcut.WorkingDirectory = $InstallPath
            $Shortcut.Description = "Professional Security Testing Framework"
            $Shortcut.Save()
            Write-Host "   ✓ Desktop shortcut created" -ForegroundColor Green
        }

        # Start Menu shortcut
        if (-not $NoStartMenu) {
            $StartMenuPath = [Environment]::GetFolderPath("StartMenu")
            $ProgramsPath = Join-Path $StartMenuPath "Programs\Security Testing Framework"

            if (-not (Test-Path $ProgramsPath)) {
                New-Item -ItemType Directory -Path $ProgramsPath -Force | Out-Null
            }

            $Shortcut = $WshShell.CreateShortcut("$ProgramsPath\Security Testing Framework.lnk")
            $Shortcut.TargetPath = $ExePath
            $Shortcut.WorkingDirectory = $InstallPath
            $Shortcut.Description = "Professional Security Testing Framework"
            $Shortcut.Save()
            Write-Host "   ✓ Start menu entry created" -ForegroundColor Green
        }

        # Add to PATH (optional, requires admin)
        if ($isAdmin) {
            $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
            if ($CurrentPath -notlike "*$InstallPath*") {
                [Environment]::SetEnvironmentVariable("Path", "$CurrentPath;$InstallPath", "Machine")
                Write-Host "   ✓ Added to system PATH" -ForegroundColor Green
            }
        }
    }

    # Step 6: Create uninstaller
    if (-not $Portable) {
        Write-Host "[6/6] Creating uninstaller..." -ForegroundColor Green

        $UninstallerScript = @"
# Security Testing Framework Uninstaller
Write-Host 'Uninstalling Security Testing Framework...'

# Remove executable
if (Test-Path '$ExePath') {
    Remove-Item -Path '$ExePath' -Force
}

# Remove shortcuts
`$Desktop = [Environment]::GetFolderPath('Desktop')
if (Test-Path "`$Desktop\Security Testing Framework.lnk") {
    Remove-Item "`$Desktop\Security Testing Framework.lnk" -Force
}

`$StartMenu = [Environment]::GetFolderPath('StartMenu')
`$StartMenuPath = Join-Path `$StartMenu 'Programs\Security Testing Framework'
if (Test-Path `$StartMenuPath) {
    Remove-Item -Path `$StartMenuPath -Recurse -Force
}

# Remove from PATH
if (([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    `$Path = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    `$NewPath = (`$Path -split ';' | Where-Object { `$_ -ne '$InstallPath' }) -join ';'
    [Environment]::SetEnvironmentVariable('Path', `$NewPath, 'Machine')
}

# Remove installation directory
if ((Get-ChildItem '$InstallPath' | Measure-Object).Count -eq 1) {
    Remove-Item -Path '$InstallPath' -Recurse -Force
}

Write-Host 'Uninstallation complete!' -ForegroundColor Green
"@

        $UninstallerPath = Join-Path $InstallPath "uninstall.ps1"
        $UninstallerScript | Out-File -FilePath $UninstallerPath -Encoding UTF8
        Write-Host "   ✓ Uninstaller created" -ForegroundColor Green
    }

    # Success message
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║           INSTALLATION COMPLETED SUCCESSFULLY!               ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Installed to: $ExePath" -ForegroundColor Cyan

    if (-not $Portable) {
        Write-Host "📝 Uninstall: Run $InstallPath\uninstall.ps1" -ForegroundColor Cyan
    }

    Write-Host ""
    Write-Host "To run the framework:" -ForegroundColor Yellow
    Write-Host "  • Double-click the desktop shortcut" -ForegroundColor Gray
    Write-Host "  • Or run: $ExePath" -ForegroundColor Gray
    Write-Host "  • Or from CMD/PowerShell: SecurityTestingFramework" -ForegroundColor Gray
    Write-Host ""

    # Ask to run now
    if (-not $Silent) {
        $RunNow = Read-Host "Would you like to run Security Testing Framework now? (Y/N)"
        if ($RunNow -eq 'Y' -or $RunNow -eq 'y') {
            Write-Host "Starting Security Testing Framework..." -ForegroundColor Green
            Start-Process -FilePath $ExePath
        }
    }

} catch {
    Write-Host ""
    Write-Host "❌ INSTALLATION FAILED" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check your internet connection" -ForegroundColor Gray
    Write-Host "  2. Try running PowerShell as Administrator" -ForegroundColor Gray
    Write-Host "  3. Check if antivirus is blocking the download" -ForegroundColor Gray
    Write-Host "  4. Try downloading manually from:" -ForegroundColor Gray
    Write-Host "     https://github.com/$RepoOwner/$RepoName/releases" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
