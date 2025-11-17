# DWG Block Extractor - Implementation Plan

## Executive Summary
Complete implementation roadmap for building the ultra-simple DWG/DXF block extractor. This plan transforms the project specification into actionable development phases, starting with core infrastructure setup and progressing through GUI implementation, testing, and deployment.

## Table Summary

| Phase | Tasks | Files to Create/Modify | Estimated LOC | Package Manager |
|-------|-------|------------------------|---------------|-----------------|
| **Phase 1: Project Setup** | Environment with uv, dependencies, project structure, logging config | `pyproject.toml`, `.python-version`, `app/core/logger.py` | ~80 | **uv** |
| **Phase 2: Core Logic** | Extraction and Excel writing with logging | `app/core/extractor.py`, `app/core/excel_writer.py`, `app/core/constants.py` | ~200 | **uv sync** |
| **Phase 3: GUI** | Desktop interface with logging integration | `app/main.py` | ~120 | **uv run** |
| **Phase 4: Testing** | Unit tests and test fixtures | `app/tests/core/*.py`, `app/tests/assets/*` | ~120 | **uv run pytest** |
| **Phase 5: Scripts** | Launch and build scripts using uv | `scripts/start.sh`, `scripts/build_executable.sh` | ~60 | **uv run** |
| **Total** | 5 phases | ~12 files | ~580 | All via **uv** |

## Relevant Files

### Files to Create

- **`app/pyproject.toml`** - Python project configuration with uv dependency management. Contains all required libraries (ezdxf, pandas, openpyxl, customtkinter) and project metadata.

- **`app/.python-version`** - Specifies Python 3.8+ requirement for the project.

- **`app/core/extractor.py`** - Core extraction logic. Loads DWG/DXF files with ezdxf, iterates through modelspace INSERT entities, counts block references, and returns aggregated data.

- **`app/core/excel_writer.py`** - Excel file generation module. Accepts block count data, creates formatted Excel file with headers, sorting, and auto-filter using pandas and openpyxl.

- **`app/core/constants.py`** - Application constants including file extensions, Excel column names, worksheet names, and error messages.

- **`app/core/logger.py`** - Centralized logging configuration. All logs output to stdout for real-time LLM agent monitoring.

- **`app/main.py`** - CustomTkinter GUI application with integrated logging. Single-window interface with file picker, extract button, progress bar, and status updates.

- **`app/tests/core/test_extractor.py`** - Unit tests for extraction logic. Tests valid files, invalid files, empty drawings, and various block count scenarios.

- **`app/tests/core/test_excel_writer.py`** - Unit tests for Excel generation. Verifies correct formatting, sorting, headers, and file output.

- **`app/tests/assets/sample_drawing.dxf`** - Test fixture DXF file with known block counts for automated testing.

- **`scripts/start.sh`** - Shell script to launch the application. Sets up environment and runs `main.py`.

- **`scripts/build_executable.sh`** - Optional script to build standalone Windows executable using PyInstaller.

### Files to Reference

- **`ai_output/001-starting-plan.md`** - Original project specification with requirements, UI mockup, and success criteria.

- **`ai_docs/002-standardized-app-structure.md`** - TAC standardized application structure guide. Provides the architectural pattern for organizing `app/`, `core/`, and `tests/` directories.

## Phase 1: Project Setup

### Goals
- Initialize Python project with uv
- Configure dependencies
- Create directory structure
- Set up version control

### Tasks

1. **Create directory structure**

   ```text
   app/
   ├── core/
   │   ├── __init__.py
   │   ├── logger.py              # Logging configuration
   │   ├── extractor.py
   │   ├── excel_writer.py
   │   └── constants.py
   ├── tests/
   │   ├── __init__.py
   │   ├── core/
   │   │   ├── __init__.py
   │   │   ├── test_extractor.py
   │   │   └── test_excel_writer.py
   │   └── assets/
   │       └── (test fixtures)
   ├── main.py
   ├── pyproject.toml
   └── .python-version
   ```

2. **Create `pyproject.toml`**
   ```toml
   [project]
   name = "dwg-block-extractor"
   version = "0.1.0"
   requires-python = ">=3.8"
   dependencies = [
       "ezdxf>=1.0.0",
       "pandas>=2.0.0",
       "openpyxl>=3.1.0",
       "customtkinter>=5.2.0",
   ]

   [project.optional-dependencies]
   dev = [
       "pytest>=7.0.0",
       "pytest-cov>=4.0.0",
   ]
   build = [
       "pyinstaller>=6.0.0",
   ]

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```

3. **Create `.python-version`**
   ```
   3.11
   ```

4. **Initialize dependencies with uv**

   ```bash
   cd app

   # Install uv if not already installed
   # curl -LsSf https://astral.sh/uv/install.sh | sh

   # Sync dependencies from pyproject.toml
   uv sync

   # Verify installation
   uv run python --version
   ```

5. **Create logging configuration in `app/core/logger.py`**
   - Set up logger with stdout handler only
   - Use standard Python logging module
   - Format: `%(asctime)s [%(name)s] %(levelname)s: %(message)s`
   - Default level: INFO for stdout monitoring by LLM agents

### Success Criteria
- [ ] All dependencies install without errors using `uv sync`
- [ ] Python version is 3.8+
- [ ] Logging outputs to stdout correctly
- [ ] uv commands work correctly

## Phase 2: Core Logic Implementation

### Goals
- Implement DWG/DXF extraction logic
- Implement Excel generation
- Define application constants

### Tasks

1. **Create `app/core/constants.py`**
   ```python
   # File extensions
   SUPPORTED_EXTENSIONS = ('.dwg', '.dxf')

   # Excel configuration
   EXCEL_COLUMN_BLOCK_NAME = 'Block Name'
   EXCEL_COLUMN_COUNT = 'Insertion Count'
   EXCEL_WORKSHEET_NAME = 'Block Summary'

   # UI messages
   MSG_SELECT_FILE = 'Please select a DWG or DXF file'
   MSG_PROCESSING = 'Processing...'
   MSG_SUCCESS = 'Extraction complete'
   MSG_ERROR_INVALID_FILE = 'Invalid or corrupted file'
   MSG_ERROR_NO_BLOCKS = 'No blocks found in file'
   ```

2. **Create `app/core/extractor.py`**
   - Import logger: `from .logger import setup_logger`
   - Function: `extract_blocks(file_path: str) -> dict[str, int]`
   - Load DWG/DXF with `ezdxf.readfile()`
   - Iterate modelspace entities, filter INSERT types
   - Count by block name
   - Log INFO: start, completion with counts
   - Log ERROR: file not found, invalid format
   - Raise appropriate exceptions

3. **Create `app/core/excel_writer.py`**
   - Import logger: `from .logger import setup_logger`
   - Function: `write_excel(block_data: dict[str, int], output_path: str) -> str`
   - Convert dict to pandas DataFrame
   - Sort by count descending
   - Write Excel with openpyxl engine
   - Apply auto-filter and column widths
   - Generate timestamped filename
   - Log INFO: start, completion with file path
   - Log ERROR: write failures
   - Return full path to created file

### Success Criteria
- [ ] `extract_blocks()` correctly counts blocks in valid DXF files
- [ ] `extract_blocks()` raises appropriate exceptions for invalid files
- [ ] `write_excel()` creates properly formatted Excel files
- [ ] Excel files have correct headers, sorting, and auto-filter
- [ ] All modules log to stdout for real-time monitoring

## Phase 3: GUI Implementation

### Goals
- Build single-window CustomTkinter interface
- Implement file picker dialog
- Add progress bar and status updates
- Connect UI to core logic

### Tasks

1. **Create `app/main.py`**

   **Logging integration:**
   - Import logger: `from core.logger import setup_logger`
   - Initialize logger: `logger = setup_logger(__name__)`
   - Log all user actions and errors to stdout

   **Main components:**
   - `DWGExtractorApp(ctk.CTk)` - Main application class
   - File path display (CTkEntry, read-only)
   - Browse button (CTkButton) - Opens file dialog
   - Extract button (CTkButton) - Triggers extraction
   - Progress bar (CTkProgressBar) - Shows extraction progress
   - Status label (CTkLabel) - Displays current operation

   **Key methods:**
   - `__init__()` - Set up UI layout, log startup
   - `browse_file()` - Open file picker, log file selection
   - `extract_blocks()` - Validate file, call core logic, log progress
   - `update_progress(value, message)` - Update progress bar and status
   - `show_error(message)` - Display error dialog, log error
   - `show_success(excel_path)` - Show success message, log completion, open Excel

   **Layout:**
   ```
   Window: 500x300px
   - Title: "DWG Block Extractor"
   - Padding: 20px
   - File path entry (width: full, height: 40)
   - Button row: Browse (120px) | Extract (120px)
   - Progress bar (width: full, height: 20)
   - Status label (centered)
   ```

   **File dialog configuration:**
   - Title: "Select DWG or DXF File"
   - File types: [("DWG/DXF Files", "*.dwg *.dxf"), ("All Files", "*.*")]

2. **Threading for extraction**
   - Run extraction in separate thread to prevent UI freeze
   - Use `threading.Thread` for async execution
   - Update progress bar via `after()` method for thread safety

3. **Auto-open Excel file**
   - Use `os.startfile()` on Windows
   - Use `subprocess.run(['xdg-open', path])` on Linux (if needed)

### Success Criteria
- [ ] Window displays correctly at 500x300px
- [ ] File picker opens and filters DWG/DXF files
- [ ] Selected file path displays in read-only field
- [ ] Extract button triggers extraction process
- [ ] Progress bar updates during extraction
- [ ] Excel file opens automatically on success
- [ ] Error dialogs display for invalid files

## Phase 4: Testing

### Goals
- Create comprehensive unit tests
- Add test fixtures
- Achieve >80% code coverage

### Tasks

1. **Create test fixtures in `app/tests/assets/`**

   **Sample DXF file** (`sample_drawing.dxf`):
   ```python
   # Generate using ezdxf
   import ezdxf

   doc = ezdxf.new('R2010')
   msp = doc.modelspace()

   # Create block definitions
   doc.blocks.new(name='VALVE_GATE')
   doc.blocks.new(name='PIPE_SUPPORT')
   doc.blocks.new(name='EQUIPMENT_TAG')

   # Insert blocks (known counts)
   for _ in range(10):
       msp.add_blockref('VALVE_GATE', (0, 0))
   for _ in range(5):
       msp.add_blockref('PIPE_SUPPORT', (0, 0))
   for _ in range(3):
       msp.add_blockref('EQUIPMENT_TAG', (0, 0))

   doc.saveas('sample_drawing.dxf')
   ```

   **Invalid DXF file** (`invalid.dxf`):
   - Create text file with random content

   **Empty drawing** (`empty.dxf`):
   - Valid DXF with no blocks

2. **Create `app/tests/core/test_extractor.py`**

   Test cases:
   - `test_extract_valid_file()` - Verify correct counts
   - `test_extract_empty_file()` - Returns empty dict
   - `test_extract_invalid_file()` - Raises exception
   - `test_extract_missing_file()` - Raises FileNotFoundError
   - `test_extract_counts_accuracy()` - Validates specific counts match fixture

3. **Create `app/tests/core/test_excel_writer.py`**

   Test cases:
   - `test_write_excel_basic()` - Creates valid Excel file
   - `test_excel_has_headers()` - Verifies column headers
   - `test_excel_sorted_descending()` - Checks sort order
   - `test_excel_autofilter()` - Confirms auto-filter enabled
   - `test_filename_format()` - Validates filename pattern
   - `test_empty_data()` - Handles empty dict

4. **Run tests**
   ```bash
   cd app
   uv run pytest
   uv run pytest --cov=core --cov-report=term-missing
   ```

### Success Criteria
- [ ] All tests pass
- [ ] Code coverage >80%
- [ ] Test fixtures are reproducible
- [ ] Tests run in <5 seconds

## Phase 5: Scripts and Deployment

### Goals
- Create launch script
- Create build script for executable (optional)
- Document usage

### Tasks

1. **Create `scripts/start.sh`**
   ```bash
   #!/bin/bash

   # DWG Block Extractor Launcher

   cd "$(dirname "$0")/../app" || exit 1

   # Check if .python-version matches
   if ! command -v python &> /dev/null; then
       echo "Error: Python not found"
       exit 1
   fi

   # Launch application
   uv run python main.py
   ```

   Make executable:
   ```bash
   chmod +x scripts/start.sh
   ```

2. **Create `scripts/build_executable.sh`** (optional, Windows-focused)
   ```bash
   #!/bin/bash

   # Build standalone Windows executable

   cd "$(dirname "$0")/../app" || exit 1

   echo "Building Windows executable..."

   uv run pyinstaller \
       --onefile \
       --windowed \
       --name="DWG-Block-Extractor" \
       --icon="icon.ico" \
       main.py

   echo "Executable created in app/dist/"
   ```

3. **Update main README.md**
   - Add quick start instructions
   - Document requirements
   - Show usage examples
   - List supported file types

### Success Criteria
- [ ] `scripts/start.sh` launches application without errors
- [ ] Executable builds successfully (if using PyInstaller)
- [ ] README has clear usage instructions

## Implementation Order

Execute phases in strict sequence:

1. **Phase 1** (Setup) - Required foundation
2. **Phase 2** (Core) - Business logic independent of UI
3. **Phase 3** (GUI) - Depends on Phase 2
4. **Phase 4** (Testing) - Validates Phase 2 and 3
5. **Phase 5** (Scripts) - Final packaging

## Risk Mitigation

### Potential Issues

| Risk | Impact | Mitigation |
|------|--------|------------|
| ezdxf fails to read DWG files | High | Use ezdxf's ODA File Converter integration, or require DXF conversion |
| Large files freeze UI | Medium | Implement threading in Phase 3 |
| CustomTkinter platform issues | Medium | Test on Windows first (primary target), document platform limitations |
| Excel file locking | Low | Check if file exists before overwriting, add unique timestamp |

### Testing Strategy

- **Unit tests** for core logic (Phase 2)
- **Manual testing** for GUI (Phase 3)
- **Integration tests** with real DWG/DXF files
- **Edge cases**: empty files, 10,000+ blocks, special characters in block names

## Dependencies Deep Dive

### Core Dependencies

1. **ezdxf (>= 1.0.0)**
   - Reads DWG/DXF files
   - Provides modelspace entity iteration
   - Handles AutoCAD formats R12 through R2018+

2. **pandas (>= 2.0.0)**
   - DataFrame manipulation
   - Sorting by count
   - Excel export integration

3. **openpyxl (>= 3.1.0)**
   - Excel file writing (via pandas)
   - Auto-filter support
   - Column formatting

4. **customtkinter (>= 5.2.0)**
   - Modern tkinter wrapper
   - Clean UI components
   - Cross-platform (Windows-focused)

### Development Dependencies

1. **pytest (>= 7.0.0)**
   - Unit testing framework
   - Fixture management

2. **pytest-cov (>= 4.0.0)**
   - Code coverage reporting

3. **pyinstaller (>= 6.0.0)** (optional)
   - Standalone executable creation
   - Windows distribution

## Recommendations

### Before Starting

1. **Install uv** - `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux)
2. **Verify Python 3.8+** - `python --version`
3. **Prepare test DWG files** - Have 2-3 real files for testing
4. **Target Windows** - Primary platform

### During Development

1. **Use uv exclusively** - `uv sync`, `uv run python`, `uv run pytest`
2. **Implement logging** - All logs to stdout for LLM agent monitoring
3. **Start with core logic** - Test extraction independently before GUI
4. **Follow TDD** - Write tests alongside implementation
5. **Monitor stdout** - Watch logs in real-time for debugging

### After Implementation

1. **UAT with real files** - Test 5-10 DWG files, monitor stdout
2. **Performance test** - Verify with 1,000+ blocks
3. **Package with uv** - `uv run pyinstaller main.py`

## Next Steps

1. **Create GitHub issue** for Phase 1 setup
2. **Set up project structure** following the plan
3. **Implement core extraction logic** (Phase 2)
4. **Build GUI** (Phase 3)
5. **Write tests** (Phase 4)
6. **Package application** (Phase 5)

## Success Metrics

Final application should achieve:

- **Simplicity**: 2-click operation (Browse, Extract)
- **Speed**: Process 1,000 blocks in <5 seconds
- **Reliability**: Handle corrupted files gracefully
- **Code quality**: >80% test coverage
- **Size**: <500 lines of code (excluding tests)
- **Dependencies**: Exactly 4 production libraries

---

**Estimated Total Development Time**: 6-8 hours for experienced developer
- Phase 1: 30 minutes
- Phase 2: 2 hours
- Phase 3: 2 hours
- Phase 4: 2 hours
- Phase 5: 1 hour
- Testing/debugging: 1-2 hours
