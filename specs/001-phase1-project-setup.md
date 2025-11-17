# Chore: Phase 1 - DWG Extractor Project Setup

## Chore Description
Initialize the DWG Block Extractor project with Python environment using uv package manager, configure dependencies, create the standardized directory structure, and set up centralized logging configuration. This phase establishes the foundation for the entire project, ensuring all dependencies are properly managed and the codebase follows the TAC standardized app structure pattern.

## Relevant Files
Use these files to resolve the chore:

### New Files
- **`app/pyproject.toml`** - Python project configuration with uv dependency management. Contains all required libraries (ezdxf, pandas, openpyxl, customtkinter) and project metadata. Includes optional dev dependencies (pytest, pytest-cov) and build dependencies (pyinstaller).

- **`app/.python-version`** - Specifies Python 3.11 requirement for the project. Used by uv to select the correct Python interpreter.

- **`app/core/__init__.py`** - Python package marker for the core module. Empty file to make core directory importable.

- **`app/core/logger.py`** - Centralized logging configuration module. Sets up logger with stdout handler only for real-time LLM agent monitoring. Uses standard Python logging module with format: `%(asctime)s [%(name)s] %(levelname)s: %(message)s`.

- **`app/core/constants.py`** - Application-wide constants placeholder. Will be populated in Phase 2 with file extensions, Excel column names, UI messages, etc. Created now to establish structure.

- **`app/core/extractor.py`** - DWG/DXF extraction logic placeholder. Will be implemented in Phase 2. Created now to establish structure.

- **`app/core/excel_writer.py`** - Excel file generation module placeholder. Will be implemented in Phase 2. Created now to establish structure.

- **`app/tests/__init__.py`** - Python package marker for tests module. Empty file to make tests directory importable.

- **`app/tests/core/__init__.py`** - Python package marker for core tests module. Empty file to make tests/core directory importable.

### Reference Files
- **`ai_output/002-implementation-plan.md`** - Original implementation plan with detailed Phase 1 requirements and complete project specification.

- **`README.md`** - Project template README with uv installation instructions and Quick Start guide.

- **`app/README.md`** - Application directory guide with Python project structure examples and best practices.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Core Directory Structure
- Create `app/core/` directory for core application logic
- Create `app/tests/core/` directory for unit tests
- Create `app/tests/assets/` directory for test fixtures (will be populated in Phase 4)
- Create all necessary `__init__.py` files to make directories importable Python packages

### Step 2: Create Python Project Configuration Files
- Create `app/.python-version` with content `3.11` to specify Python version
- Create `app/pyproject.toml` with the following configuration:
  - Project metadata: name="dwg-block-extractor", version="0.1.0", requires-python=">=3.8"
  - Production dependencies: ezdxf>=1.0.0, pandas>=2.0.0, openpyxl>=3.1.0, customtkinter>=5.2.0
  - Optional dev dependencies: pytest>=7.0.0, pytest-cov>=4.0.0
  - Optional build dependencies: pyinstaller>=6.0.0
  - Build system: hatchling

### Step 3: Install Dependencies Using uv
- Navigate to `app/` directory
- Run `uv sync` to install all dependencies from pyproject.toml
- Verify installation by running `uv run python --version` to ensure Python 3.11+ is available
- Verify uv created virtual environment and lock file

### Step 4: Create Centralized Logging Module
- Create `app/core/logger.py` with centralized logging configuration:
  - Import Python's standard logging module
  - Create `setup_logger(name: str)` function that:
    - Creates a logger with the provided name
    - Adds stdout handler only (no file handlers)
    - Sets format: `%(asctime)s [%(name)s] %(levelname)s: %(message)s`
    - Sets default level to INFO for real-time monitoring
    - Returns configured logger
  - Add module-level docstring explaining stdout-only logging for LLM agent monitoring

### Step 5: Create Placeholder Core Modules
- Create empty placeholder files to establish structure:
  - `app/core/constants.py` with module docstring: "Application-wide constants - to be populated in Phase 2"
  - `app/core/extractor.py` with module docstring: "DWG/DXF extraction logic - to be implemented in Phase 2"
  - `app/core/excel_writer.py` with module docstring: "Excel file generation - to be implemented in Phase 2"
- Each placeholder should be importable but not functional yet

### Step 6: Verify Project Structure
- Verify the complete directory structure matches the TAC standardized app structure:
  ```
  app/
  ├── core/
  │   ├── __init__.py
  │   ├── logger.py
  │   ├── constants.py
  │   ├── extractor.py
  │   └── excel_writer.py
  ├── tests/
  │   ├── __init__.py
  │   ├── core/
  │   │   └── __init__.py
  │   └── assets/
  ├── pyproject.toml
  └── .python-version
  ```
- Verify all `__init__.py` files exist and directories are importable
- Verify no files are missing from the structure

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd app && uv run python --version` - Verify Python 3.11+ is available via uv
- `cd app && uv run python -c "import ezdxf; print(f'ezdxf: {ezdxf.__version__}')"` - Verify ezdxf dependency installed
- `cd app && uv run python -c "import pandas; print(f'pandas: {pandas.__version__}')"` - Verify pandas dependency installed
- `cd app && uv run python -c "import openpyxl; print(f'openpyxl: {openpyxl.__version__}')"` - Verify openpyxl dependency installed
- `cd app && uv run python -c "import customtkinter; print(f'customtkinter: {customtkinter.__version__}')"` - Verify customtkinter dependency installed
- `cd app && uv run python -c "from core.logger import setup_logger; logger = setup_logger('test'); logger.info('Logging test'); print('Logger setup successful')"` - Verify logger.py works and outputs to stdout
- `cd app && uv run python -c "import core.constants; import core.extractor; import core.excel_writer; print('All core modules importable')"` - Verify all core modules are importable
- `cd app && test -f pyproject.toml && echo 'pyproject.toml exists'` - Verify pyproject.toml exists
- `cd app && test -f .python-version && echo '.python-version exists'` - Verify .python-version exists
- `cd app && test -d core && test -d tests/core && test -d tests/assets && echo 'Directory structure complete'` - Verify complete directory structure

## Notes
- **uv Package Manager**: This project exclusively uses uv for all dependency management. Do not use pip, conda, or other package managers.
- **Logging Strategy**: All logging outputs to stdout only (no file handlers) to enable real-time monitoring by LLM agents during development and ADW workflow execution.
- **TAC Standardized Structure**: The directory layout follows the TAC standardized app structure pattern with clear separation of core logic, tests, and configuration.
- **Phase Isolation**: Phase 1 focuses solely on setup and infrastructure. No business logic implementation occurs in this phase.
- **Python Version**: While the project requires Python 3.8+, we specify 3.11 in `.python-version` for modern features and performance.
- **Placeholder Files**: Placeholder core modules (constants.py, extractor.py, excel_writer.py) are created now to establish structure but will be fully implemented in Phase 2.
- **Virtual Environment**: uv automatically manages the virtual environment - no manual venv creation needed.
- **Lock File**: uv generates `uv.lock` automatically during `uv sync` for reproducible builds.
