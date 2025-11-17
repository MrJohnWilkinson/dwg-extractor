# Chore: Automate Windows Build with PowerShell Script

## Chore Description
Create a PowerShell script (`scripts/build.ps1`) that automates the Windows build process with a single command. The script should handle git sync, dependency installation, building the executable, and provide clear feedback throughout the process. This eliminates the manual 7-step process currently documented in `ai_docs/004-windows-build-steps.md` and reduces friction when building Windows executables from the Windows environment.

The script should:
- Handle all git operations (checkout, pull)
- Manage virtual environment activation automatically
- Install build dependencies
- Run PyInstaller to create the executable
- Provide colored console output with status updates
- Handle errors gracefully with clear messages
- Support optional verbose mode for debugging
- Work from the project root directory
- Be compatible with PowerShell 5.1+ (Windows default)

## Relevant Files
Use these files to resolve the chore:

**Reference Files:**
- `scripts/build.sh` (lines 1-325) - Linux build script to use as reference for structure, error handling, and feature parity
- `ai_docs/004-windows-build-steps.md` (lines 1-35) - Current manual Windows build process to automate
- `pyproject.toml` (lines 22-25) - Contains build dependency group configuration
- `README.md` (lines 42-44, 73-76) - Project structure and dev environment context

**Why Relevant:**
- `scripts/build.sh` provides proven patterns for build automation, error handling, color output, verbose mode, and build verification
- Manual steps doc defines exact Windows-specific requirements (venv path, git workflow, uv commands)
- `pyproject.toml` shows the correct build group syntax for dependency installation
- README shows project conventions and Windows/WSL workflow context

### New Files
- `scripts/build.ps1` - PowerShell build automation script with one-command Windows builds

## Step by Step Tasks

### 1. Create PowerShell Build Script Structure
- Create `scripts/build.ps1` with PowerShell script header and strict error handling (`$ErrorActionPreference = "Stop"`)
- Add script metadata (description, version, usage)
- Define configuration constants: `$APP_NAME = "DWGBlockExtractor"`, `$APP_VERSION = "0.1.0"`
- Create parameter block supporting `-Verbose` and `-Help` flags
- Add color output functions (`Write-ColorOutput`) for consistent messaging (Success/Green, Error/Red, Info/Blue, Warning/Yellow)

### 2. Implement Pre-Build Checks
- Create `Test-Prerequisites` function to verify:
  - PowerShell version (require 5.1+)
  - Git is installed and accessible
  - UV package manager is installed (`uv --version`)
  - Current directory is project root (check for `pyproject.toml`)
  - `.venv_windows` virtual environment exists
- Each check should provide clear error message with remediation steps on failure
- Log all checks when `-Verbose` is specified

### 3. Implement Git Sync Operations
- Create `Sync-Repository` function to:
  - Display current branch name
  - Run `git checkout .` to discard line ending changes
  - Run `git pull` to sync with remote
  - Capture and display git output
  - Handle common git errors (no remote, conflicts, network issues) with user-friendly messages
- Add `-Verbose` logging for git operations

### 4. Implement Dependency Installation
- Create `Install-BuildDependencies` function to:
  - Activate virtual environment using `.venv_windows\Scripts\Activate.ps1`
  - Run `uv pip install --group build` to install PyInstaller
  - Capture installation output
  - Verify PyInstaller was installed successfully
  - Display success message with installed package info
- Add error handling for activation and installation failures

### 5. Implement PyInstaller Build
- Create `Build-Executable` function to:
  - Run PyInstaller command: `uv run pyinstaller app/main.py --name DWGBlockExtractor --onefile --windowed --clean`
  - Capture build output (show in verbose mode, hide in normal mode)
  - Monitor build progress
  - Handle build failures with diagnostic information
- Add timeout protection (10 minute max build time)

### 6. Implement Build Verification
- Create `Test-BuildOutput` function to:
  - Check if `dist\DWGBlockExtractor.exe` exists
  - Get file size and display in human-readable format (MB)
  - Optionally verify exe can load (check file signature)
  - Display full path to executable
- Return success/failure status for main workflow

### 7. Implement Main Workflow and Summary
- Create `Invoke-Build` main function that orchestrates:
  - Pre-build checks
  - Git sync
  - Dependency installation
  - Executable build
  - Build verification
- Add try-catch-finally block for error handling and cleanup
- Create `Show-BuildSummary` function displaying:
  - Build status (Success/Failed)
  - Application name and version
  - Platform (Windows)
  - Executable location
  - File size
  - Next steps / usage instructions
- Add elapsed time tracking and display

### 8. Add Documentation and Help
- Implement `-Help` parameter to display:
  - Script description and purpose
  - Usage examples: `.\scripts\build.ps1`, `.\scripts\build.ps1 -Verbose`
  - Parameter descriptions
  - Requirements and prerequisites
  - Output location
- Add inline comments explaining complex PowerShell sections
- Document any Windows-specific gotchas (execution policy, path handling)

### 9. Update Documentation Files
- Update `ai_docs/004-windows-build-steps.md`:
  - Add new "Quick Build" section at the top showing one-command approach
  - Keep existing manual steps in "Manual Build Steps" section for reference
  - Add troubleshooting section for common PowerShell issues
  - Document `-Verbose` flag usage for debugging
- Update `README.md` if needed to reference new automated build script

### 10. Test Script in Dry-Run Mode
- Create test checklist for validation:
  - Script help displays correctly (`.\scripts\build.ps1 -Help`)
  - Pre-build checks detect missing prerequisites
  - Script executes from project root
  - Color output renders correctly in PowerShell console
  - Error handling works (simulate failures)
  - Verbose mode shows detailed output
- Document any Windows-specific testing requirements

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

**Note:** These validation commands are designed to be run in WSL/Linux environment. The actual PowerShell script will be tested manually in Windows environment following the test checklist in Step 10.

- `test -f scripts/build.ps1` - Verify PowerShell script was created
- `head -n 20 scripts/build.ps1 | grep -q "param"` - Verify script has parameter block
- `grep -q "ErrorActionPreference" scripts/build.ps1` - Verify error handling is configured
- `grep -q "Write-ColorOutput\|Write-Host.*-ForegroundColor" scripts/build.ps1` - Verify color output functions exist
- `grep -q "Test-Prerequisites" scripts/build.ps1` - Verify pre-build checks function exists
- `grep -q "Sync-Repository" scripts/build.ps1` - Verify git sync function exists
- `grep -q "Install-BuildDependencies" scripts/build.ps1` - Verify dependency install function exists
- `grep -q "Build-Executable" scripts/build.ps1` - Verify build function exists
- `grep -q "Test-BuildOutput" scripts/build.ps1` - Verify verification function exists
- `grep -q "pyinstaller.*--onefile.*--windowed.*--clean" scripts/build.ps1` - Verify correct PyInstaller command
- `test -f ai_docs/004-windows-build-steps.md` - Verify documentation still exists
- `uv run pytest app/tests/` - Run all tests to ensure no regressions in application code

## Notes
- The PowerShell script is designed to run on Windows, so full testing will require running it in the Windows environment at `C:\Users\johnw\Desktop\Desktop Reference\GitProjectsDesktop\dwg-extractor-windows`
- PowerShell execution policy may need to be adjusted on first run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- The script should be idempotent - running it multiple times should produce consistent results
- Consider the script modeled after `scripts/build.sh` for feature parity between Linux and Windows builds
- Virtual environment path differs between platforms: `.venv` (Linux) vs `.venv_windows` (Windows)
- Git line ending handling is important due to Windows/WSL cross-platform development
- The script should work with the exact paths and conventions shown in `ai_docs/004-windows-build-steps.md`
