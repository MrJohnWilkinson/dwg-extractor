# DWG Block Extractor

A minimal Python desktop application that extracts block insertion counts from DWG/DXF CAD files and exports them to formatted Excel files.

## Purpose

Extracts block reference counts from AutoCAD drawings and generates Excel reports with:
- Block names and insertion counts
- Sorted by count (descending)
- Auto-filtered headers
- Timestamped output files

**User Flow:** Browse → Select DWG/DXF → Extract → Auto-open Excel (2 clicks)

## Tech Stack

- **Python:** 3.11+ (managed with uv)
- **CAD Parsing:** ezdxf (reads DWG/DXF files)
- **Data Processing:** pandas (data manipulation)
- **Excel Generation:** openpyxl (formatted Excel files)
- **GUI Framework:** customtkinter (modern desktop UI)
- **Testing:** pytest with coverage reporting
- **Type Checking:** mypy with strict configuration
- **Package Manager:** uv (all dependency management)
- **Deployment:** PyInstaller (standalone executables)

## Project Structure

```
dwg-extractor/
├── app/                          # Application code
│   ├── core/                     # Business logic
│   │   ├── extractor.py          # DWG/DXF extraction
│   │   ├── excel_writer.py       # Excel generation
│   │   ├── constants.py          # App constants
│   │   └── logger.py             # Stdout logging
│   ├── tests/                    # Test suite
│   │   ├── core/                 # Unit tests
│   │   └── assets/               # Test fixtures
│   └── main.py                   # GUI entry point
│
├── scripts/                      # Utility scripts
│   └── start.sh                  # Launch application
│
├── .venv/                        # Virtual environment (managed by uv)
└── pyproject.toml                # Dependencies and project config (uv)
```

## Usage

### Development Mode

**Quick Start:**
```bash
# Launch application using the start script
scripts/start.sh

# Or run directly with uv
uv run python app/main.py
```

The start script includes helpful features:
- `-v, --verbose`: Show detailed startup diagnostics
- `-h, --help`: Display help message
- Automatic dependency checks and virtual environment setup

**Running Tests:**
```bash
# Run all tests
uv run pytest app/tests/

# Run tests with coverage report
uv run pytest --cov=app/core app/tests/

# Type checking
uv run mypy app/
```

### Building Executable

Create a standalone executable that can run without Python installed:

**Install Build Dependencies:**
```bash
uv pip install --group build
```

**Run Build:**
```bash
scripts/build.sh
```

Build script options:
- `-v, --verbose`: Show detailed build output
- `-p, --preserve`: Preserve build artifacts (build/, *.spec)
- `-h, --help`: Display help message

**Output Location:**
- **Windows:** `dist/DWGBlockExtractor.exe`
- **Linux/macOS:** `dist/DWGBlockExtractor`

**Platform-Specific Notes:**
- **Windows:** Double-click the .exe file or run from command prompt
- **Linux:** May need to set executable permissions: `chmod +x dist/DWGBlockExtractor`
- **macOS:** May need to allow the app in Security & Privacy settings

### Production Mode

The built executable is completely standalone:

**Running the Executable:**
```bash
# Linux/macOS
./dist/DWGBlockExtractor

# Windows
dist\DWGBlockExtractor.exe
```

**No Python Required:** End users can run the executable without installing Python or any dependencies.

**Troubleshooting:**
- **Permission Denied (Linux/macOS):** Run `chmod +x dist/DWGBlockExtractor`
- **Missing Libraries (Linux):** Install system libraries: `sudo apt-get install libx11-6 libxext6 libxrender1 libfontconfig1`
- **Security Warning (macOS):** Go to System Preferences → Security & Privacy and allow the application
- **Windows Defender:** The executable may be flagged as unknown; click "More info" → "Run anyway"

**Working Directory Convention:**
All commands execute from the project root using root-relative paths. Scripts use `uv run` without changing directories, maintaining consistency across the project.

## Reference Files
- ai_docs/001-naming-convention-guide.md
- ai_docs/002-standardized-app-structure.md

## Working Directory Convention
- **Always execute commands from project root** (`/home/john/github-projects-linux/dwg-extractor`) - never use `cd` commands
- **Use `uv run <command>` with root-relative paths**: All paths include `app/` prefix for consistency
  - Run tests: `uv run pytest app/tests/`
  - Run application: `uv run python app/main.py`
  - Coverage: `uv run pytest --cov=app/core app/tests/`
  - Type checking: `uv run mypy app/`
- **File operations use root-relative paths**: `test -f app/tests/assets/sample.dxf`
- **Scripts follow convention**: `scripts/start.sh` uses `uv run python app/main.py` without changing directories
- **Project structure**: `pyproject.toml` and `.venv` at root, application code in `app/`
- **Enforced by Claude Code setting**: `.claude/settings.json` has `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR: 1` to maintain context