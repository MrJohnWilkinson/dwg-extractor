<#
.SYNOPSIS
    DWG Block Extractor Build Script for Windows

.DESCRIPTION
    Automates the Windows build process with a single command. Handles git sync,
    dependency installation, building the executable, and provides clear feedback
    throughout the process.

.PARAMETER Verbose
    Show detailed build output and logging information

.PARAMETER Help
    Display this help message

.EXAMPLE
    .\scripts\build.ps1
    Run the build with standard output

.EXAMPLE
    .\scripts\build.ps1 -Verbose
    Run the build with detailed logging

.NOTES
    Version: 1.0.0
    Requires: PowerShell 5.1+, Git, UV package manager
    Execute from project root directory
#>

[CmdletBinding()]
param(
    [switch]$Help
)

# Exit on error
$ErrorActionPreference = "Stop"

# Configuration
$APP_NAME = "DWGBlockExtractor"
$APP_VERSION = "0.1.0"
$VENV_PATH = ".venv_windows"

#region Helper Functions

function Write-ColorOutput {
    param(
        [string]$Message,
        [ValidateSet('Success', 'Error', 'Info', 'Warning')]
        [string]$Type = 'Info'
    )

    $color = switch ($Type) {
        'Success' { 'Green' }
        'Error'   { 'Red' }
        'Info'    { 'Cyan' }
        'Warning' { 'Yellow' }
    }

    Write-Host $Message -ForegroundColor $color
}

function Write-VerboseLog {
    param([string]$Message)

    if ($VerbosePreference -eq 'Continue') {
        Write-Host "[VERBOSE] $Message" -ForegroundColor Blue
    }
}

function Show-Help {
    Get-Help $PSCommandPath -Detailed
    exit 0
}

#endregion

#region Pre-Build Checks

function Test-Prerequisites {
    Write-ColorOutput "Checking prerequisites..." -Type Info

    # Check PowerShell version
    Write-VerboseLog "Checking PowerShell version..."
    $psVersion = $PSVersionTable.PSVersion
    if ($psVersion.Major -lt 5 -or ($psVersion.Major -eq 5 -and $psVersion.Minor -lt 1)) {
        Write-ColorOutput "Error: PowerShell 5.1 or higher is required. Current version: $psVersion" -Type Error
        Write-Host "Please upgrade PowerShell: https://aka.ms/powershell"
        exit 1
    }
    Write-VerboseLog "PowerShell version: $psVersion"

    # Check Git
    Write-VerboseLog "Checking for Git..."
    try {
        $gitVersion = git --version 2>&1
        Write-VerboseLog "Found Git: $gitVersion"
    }
    catch {
        Write-ColorOutput "Error: Git is not installed or not in PATH" -Type Error
        Write-Host "Please install Git: https://git-scm.com/download/win"
        exit 1
    }

    # Check UV
    Write-VerboseLog "Checking for UV package manager..."
    try {
        $uvVersion = uv --version 2>&1
        Write-VerboseLog "Found UV: $uvVersion"
    }
    catch {
        Write-ColorOutput "Error: UV package manager is not installed or not in PATH" -Type Error
        Write-Host "Please install UV: https://github.com/astral-sh/uv"
        exit 1
    }

    # Check project root
    Write-VerboseLog "Checking current directory is project root..."
    if (-not (Test-Path "pyproject.toml")) {
        Write-ColorOutput "Error: Not in project root directory" -Type Error
        Write-Host "Please run this script from the project root where pyproject.toml exists"
        exit 1
    }
    Write-VerboseLog "Found pyproject.toml in current directory"

    # Check virtual environment
    Write-VerboseLog "Checking for virtual environment..."
    if (-not (Test-Path $VENV_PATH)) {
        Write-ColorOutput "Error: Virtual environment not found at $VENV_PATH" -Type Error
        Write-Host "Please create the virtual environment first:"
        Write-Host "  uv venv $VENV_PATH"
        exit 1
    }
    Write-VerboseLog "Found virtual environment at $VENV_PATH"

    Write-ColorOutput "All prerequisites met" -Type Success
}

#endregion

#region Git Operations

function Sync-Repository {
    Write-ColorOutput "Syncing repository..." -Type Info

    # Get current branch
    $currentBranch = git rev-parse --abbrev-ref HEAD 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Error: Not in a git repository" -Type Error
        exit 1
    }
    Write-Host "Current branch: $currentBranch"

    # Fetch latest from origin
    Write-VerboseLog "Fetching from origin..."
    $fetchOutput = git fetch origin 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Error: git fetch failed - check network connectivity" -Type Error
        Write-Host $fetchOutput
        exit 1
    }
    Write-VerboseLog $fetchOutput

    # Hard reset to remote branch (discards ALL local changes)
    Write-VerboseLog "Resetting to origin/$currentBranch..."
    $resetOutput = git reset --hard "origin/$currentBranch" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Error: git reset failed" -Type Error
        Write-Host $resetOutput
        exit 1
    }
    Write-Host $resetOutput

    Write-ColorOutput "Repository synced to origin/$currentBranch" -Type Success
}

#endregion

#region Dependency Installation

function Install-BuildDependencies {
    Write-ColorOutput "Installing build dependencies..." -Type Info

    # Activate virtual environment
    Write-VerboseLog "Activating virtual environment..."
    $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"

    if (-not (Test-Path $activateScript)) {
        Write-ColorOutput "Error: Activation script not found at $activateScript" -Type Error
        exit 1
    }

    try {
        & $activateScript
        Write-VerboseLog "Virtual environment activated"
    }
    catch {
        Write-ColorOutput "Error: Failed to activate virtual environment: $_" -Type Error
        exit 1
    }

    # Install build dependencies
    Write-VerboseLog "Installing PyInstaller from build group..."
    try {
        if ($VerbosePreference -eq 'Continue') {
            uv pip install --group build
        }
        else {
            $null = uv pip install --group build 2>&1
        }
        Write-VerboseLog "Build dependencies installed"
    }
    catch {
        Write-ColorOutput "Error: Failed to install build dependencies: $_" -Type Error
        Write-Host "Please ensure pyproject.toml has build group configured"
        exit 1
    }

    # Verify PyInstaller installation
    try {
        $pyiVersion = uv run pyinstaller --version 2>&1
        Write-VerboseLog "PyInstaller version: $pyiVersion"
    }
    catch {
        Write-ColorOutput "Warning: Could not verify PyInstaller installation" -Type Warning
    }

    Write-ColorOutput "Build dependencies installed successfully" -Type Success
}

#endregion

#region Build Process

function Build-Executable {
    Write-ColorOutput "Building executable..." -Type Info

    # Build command arguments
    $pyinstallerArgs = @(
        "app/main.py",
        "--name", $APP_NAME,
        "--onefile",
        "--windowed",
        "--clean"
    )

    Write-VerboseLog "Running: uv run pyinstaller $($pyinstallerArgs -join ' ')"

    try {
        if ($VerbosePreference -eq 'Continue') {
            # Show all output in verbose mode
            uv run pyinstaller @pyinstallerArgs
        }
        else {
            # Suppress output in normal mode, only show errors
            $null = uv run pyinstaller @pyinstallerArgs 2>&1
        }

        Write-VerboseLog "Build completed"
    }
    catch {
        Write-ColorOutput "Error: PyInstaller build failed" -Type Error
        Write-Host "Error details: $_"
        Write-Host ""
        Write-Host "Run with -Verbose flag for detailed build output"
        exit 1
    }

    Write-ColorOutput "Build completed successfully" -Type Success
}

#endregion

#region Build Verification

function Test-BuildOutput {
    Write-VerboseLog "Verifying build output..."

    $exePath = "dist\$APP_NAME.exe"

    if (Test-Path $exePath) {
        $fileInfo = Get-Item $exePath
        $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)

        Write-ColorOutput "Executable created: $exePath ($fileSizeMB MB)" -Type Success

        if ($VerbosePreference -eq 'Continue') {
            Write-Host ""
            Write-ColorOutput "Build artifacts:" -Type Info
            Get-ChildItem "dist\" | Format-Table Name, Length, LastWriteTime -AutoSize
        }

        return $true
    }
    else {
        Write-ColorOutput "Error: Expected executable not found: $exePath" -Type Error
        return $false
    }
}

#endregion

#region Main Workflow

function Invoke-Build {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        Write-ColorOutput "DWG Block Extractor - Build Script" -Type Info
        Write-Host ""

        # Pre-build checks
        Test-Prerequisites
        Write-Host ""

        # Git sync
        Sync-Repository
        Write-Host ""

        # Install dependencies
        Install-BuildDependencies
        Write-Host ""

        # Build executable
        Build-Executable
        Write-Host ""

        # Verify build
        if (-not (Test-BuildOutput)) {
            Write-ColorOutput "Build verification failed" -Type Error
            exit 1
        }

        Write-Host ""
        Show-BuildSummary -ElapsedTime $stopwatch.Elapsed

        return 0
    }
    catch {
        Write-ColorOutput "Build failed with error: $_" -Type Error
        Write-VerboseLog $_.ScriptStackTrace
        return 1
    }
    finally {
        $stopwatch.Stop()
    }
}

function Show-BuildSummary {
    param([TimeSpan]$ElapsedTime)

    $platform = "Windows"
    $exePath = "dist\$APP_NAME.exe"

    Write-Host ""
    Write-ColorOutput "=== Build Summary ===" -Type Info
    Write-Host "Status: Success" -ForegroundColor Green
    Write-Host "Application: $APP_NAME"
    Write-Host "Version: $APP_VERSION"
    Write-Host "Platform: $platform"
    Write-Host "Executable: $exePath"

    if (Test-Path $exePath) {
        $fileInfo = Get-Item $exePath
        $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        Write-Host "File Size: $fileSizeMB MB"
    }

    $elapsedFormatted = "{0:mm\:ss}" -f $ElapsedTime
    Write-Host "Build Time: $elapsedFormatted"
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Test the executable: .\$exePath"
    Write-Host "  2. Distribute the file from the dist\ directory"
    Write-ColorOutput "=====================" -Type Info
}

#endregion

#region Entry Point

# Show help if requested
if ($Help) {
    Show-Help
}

# Run main build workflow
$exitCode = Invoke-Build
exit $exitCode

#endregion
