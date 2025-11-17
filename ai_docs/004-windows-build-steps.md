# Windows Build Guide

## Quick Build (Recommended)

**Automated one-command build using PowerShell script:**

1. Open PowerShell

2. Navigate to project:
   ```powershell
   cd "C:\Users\johnw\Desktop\Desktop Reference\GitProjectsDesktop\dwg-extractor-windows"
   ```

3. Run build script:
   ```powershell
   .\scripts\build.ps1
   ```

4. Find your `.exe`:
   ```
   dist\DWGBlockExtractor.exe
   ```

**Options:**
- `.\scripts\build.ps1 -Verbose` - Show detailed build output for debugging
- `.\scripts\build.ps1 -Help` - Display full help documentation

**Prerequisites:**
- PowerShell 5.1 or higher (included in Windows 10+)
- Git installed and in PATH
- UV package manager installed
- Virtual environment at `.venv_windows`

The script automatically handles:
- Git sync (checkout and pull)
- Virtual environment activation
- Build dependency installation
- PyInstaller executable creation
- Build verification

---

## Manual Build Steps

For reference or troubleshooting, here are the individual steps automated by the script:

1. Open PowerShell

2. Navigate to project:
   ```powershell
   cd "C:\Users\johnw\Desktop\Desktop Reference\GitProjectsDesktop\dwg-extractor-windows"
   ```

3. Sync with remote (discard line ending changes):
   ```powershell
   git checkout
   git pull
   ```

4. Activate environment:
   ```powershell
   .venv_windows\Scripts\activate
   ```

5. Install dependencies:
   ```powershell
   uv pip install --group build
   ```

6. Build executable:
   ```powershell
   uv run pyinstaller app/main.py --name DWGBlockExtractor --onefile --windowed --clean
   ```

7. Find your `.exe`:
   ```
   dist\DWGBlockExtractor.exe
   ```

---

## Troubleshooting

### PowerShell Execution Policy Error
If you get "cannot be loaded because running scripts is disabled":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Build Script Fails at Prerequisites
- Run `.\scripts\build.ps1 -Verbose` to see detailed error messages
- Verify all prerequisites are installed and in PATH
- Ensure you're in the project root directory

### Git Issues
If git operations fail:
- Check network connectivity
- Manually resolve any merge conflicts
- Ensure branch is tracking a remote

### UV Not Found
Install UV package manager:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Virtual Environment Missing
Create the Windows virtual environment:
```powershell
uv venv .venv_windows
```
