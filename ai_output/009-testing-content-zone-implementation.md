# Testing Content Zone Implementation Before Commit

## Executive Summary

This report provides a testing guide for the newly implemented content zone features (US-1 through US-7) before committing to production. You have two parallel environments: WSL2 (Linux) for development/testing and Windows for building the executable. The build script requires the code to be pushed to remote first.

## Table Summary

| Testing Method | Environment | Command/Action | Purpose |
|---------------|-------------|----------------|---------|
| Unit Tests | WSL2 | `uv run pytest app/tests/ -v` | Verify all logic works |
| Type Check | WSL2 | `uv run mypy app/` | Ensure type correctness |
| Lint | WSL2 | `uv run ruff check app/` | Code quality check |
| Coverage | WSL2 | `uv run pytest --cov=app/core app/tests/` | Check test coverage |
| Run GUI | WSL2 (limited) | `bash scripts/start.sh` | Manual GUI test (may fail on WSL) |
| Build EXE | Windows | `.\scripts\build.ps1` | Create standalone executable |
| Run EXE | Windows | `.\dist\DWGBlockExtractor.exe` | Full manual test |

## Relevant Files

- **scripts/build.ps1** - Windows PowerShell build script, pulls from git remote before building
- **scripts/build.sh** - Linux/macOS build script for reference
- **ai_docs/004-windows-build-steps.md** - Detailed Windows build documentation
- **app/tests/** - All unit tests for the implemented features
- **specs/014-019** - The specification files you implemented

## Testing Workflow

### Step 1: Run Automated Tests in WSL2 (Immediate)

```bash
# Run all unit tests with verbose output
uv run pytest app/tests/ -v

# Run specific content zone tests
uv run pytest app/tests/core/test_content_zone.py -v
uv run pytest app/tests/core/test_geometry.py -v
uv run pytest app/tests/core/extractor/test_extractor_abort.py -v

# Type checking
uv run mypy app/

# Linting
uv run ruff check app/

# Coverage report
uv run pytest --cov=app/core app/tests/
```

### Step 2: Windows Build & Test (Requires Push)

The `build.ps1` script does `git pull` before building, so code must be pushed first.

**Option A: Push to remote, then build**
```bash
# In WSL2
git push --set-upstream origin content-zone-rebuild-v2
```

Then in Windows PowerShell:
```powershell
cd "C:\Users\johnw\Desktop\Desktop Reference\GitProjectsDesktop\dwg-extractor-windows"
.\scripts\build.ps1
.\dist\DWGBlockExtractor.exe
```

**Option B: Test without push (manual Windows steps)**

Skip the git sync in build.ps1 and run manually:
```powershell
cd "C:\Users\johnw\Desktop\Desktop Reference\GitProjectsDesktop\dwg-extractor-windows"

# Manually sync from WSL (copy files or use shared drive)
# Then activate venv and run directly:
.venv_windows\Scripts\activate
uv run python app/main.py
```

### Step 3: Manual GUI Testing Checklist

Once the app is running (either via Python or .exe), verify:

1. **File Selection**: Browse button opens file dialog, selects DXF
2. **Extraction Start**: Extract button begins processing
3. **Abort Button**: Appears during extraction, clicking stops within 2 seconds
4. **Log Viewer**: Shows real-time log messages with level filtering
5. **Debug Log File**: Check that `{filename}_debug_{timestamp}.log` is created
6. **Excel Output**: Generated file contains new columns:
   - block_suggested_trim_left
   - block_suggested_trim_right
   - block_suggested_trim_top
   - block_suggested_trim_bottom
   - block_content_zone_detected

## Key Test Files to Verify

| Test File | Tests What |
|-----------|------------|
| `test_constants.py` | Threshold values are reasonable |
| `test_logger.py` | FlushingFileHandler works correctly |
| `test_content_zone.py` | Content zone detection algorithms |
| `test_geometry.py` | Geometric calculations |
| `test_extractor_abort.py` | Abort mechanism responsiveness |
| `test_excel_writer_*.py` | Excel output with new columns |

## Prerequisites for Windows Build

Before running `.\scripts\build.ps1`:

1. **Virtual environment exists**: `.venv_windows` directory
2. **UV installed**: `uv --version` works in PowerShell
3. **Git configured**: Can pull from remote
4. **PowerShell execution policy**: May need `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

If `.venv_windows` doesn't exist:
```powershell
uv venv .venv_windows
```

## Recommendations

1. **Run unit tests first** - Quick feedback on whether logic is correct
2. **Check test coverage** - Ensure new features have adequate test coverage
3. **Test abort responsiveness** - Critical for user experience, should complete within 2 seconds
4. **Verify log file creation** - Essential for debugging content zone issues in production
5. **Test with real DXF files** - Small test fixtures may not reveal performance issues

## Next Steps

1. Run `uv run pytest app/tests/ -v` to verify all tests pass
2. Run `uv run mypy app/` to check types
3. Decide whether to push and use Windows build, or test directly in Python
4. Manual GUI test with a real DXF file
5. Verify Excel output has new content zone columns
6. If all passes, commit and push
