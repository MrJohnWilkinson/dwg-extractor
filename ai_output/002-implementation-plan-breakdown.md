# Breakdown: DWG Block Extractor - Implementation Plan

## Source Document
- **Path**: ai_output/002-implementation-plan.md
- **Type**: plan
- **Original Scope**: Complete implementation roadmap for building an ultra-simple DWG/DXF block extractor with GUI, testing, and deployment

## Overview
Breaking down the DWG Block Extractor implementation into 5 sequential tasks. The breakdown follows the natural architecture layers: foundation setup, core business logic, user interface, quality assurance, and deployment tooling. Tasks must be executed in order due to dependencies, with each task representing approximately one day of focused work.

## Task Breakdown

### Task 1: Project Foundation and Logging Infrastructure
**Focus Area**: Development environment and project structure
**Suggested Command**: `/dev:chore`
**Complexity**: Simple
**Dependencies**: None

**Description**:
- Initialize Python project with uv package manager and create directory structure (`app/core/`, `app/tests/`)
- Create `pyproject.toml` with dependencies (ezdxf, pandas, openpyxl, customtkinter) and Python version specification
- Implement centralized logging configuration (`app/core/logger.py`) with stdout output for real-time monitoring
- Verify dependency installation and Python 3.8+ compatibility

**Key Files**: `pyproject.toml`, `.python-version`, `app/core/logger.py`

---

### Task 2: Core Extraction and Excel Generation Logic
**Focus Area**: Backend business logic
**Suggested Command**: `/dev:feature`
**Complexity**: Medium
**Dependencies**: Task 1 must be completed first

**Description**:
- Create application constants module (`app/core/constants.py`) for file extensions, Excel configuration, and UI messages
- Implement DWG/DXF block extraction logic (`app/core/extractor.py`) using ezdxf to iterate modelspace INSERT entities and count block references
- Implement Excel file generation (`app/core/excel_writer.py`) with pandas/openpyxl for formatted output with sorting and auto-filter
- Integrate logging into all core modules with INFO/ERROR level messages to stdout

**Key Files**: `app/core/constants.py`, `app/core/extractor.py`, `app/core/excel_writer.py`

---

### Task 3: CustomTkinter GUI Implementation
**Focus Area**: Desktop user interface
**Suggested Command**: `/dev:feature`
**Complexity**: Medium
**Dependencies**: Task 2 must be completed first

**Description**:
- Build single-window CustomTkinter application (`app/main.py`) with file picker, extract button, progress bar, and status updates
- Implement threaded extraction to prevent UI freezing during file processing
- Connect GUI to core extraction and Excel generation logic with error handling and success dialogs
- Add auto-open functionality for generated Excel files on extraction completion

**Key Files**: `app/main.py`

---

### Task 4: Test Suite and Quality Assurance
**Focus Area**: Testing infrastructure
**Suggested Command**: `/dev:chore`
**Complexity**: Medium
**Dependencies**: Tasks 2 and 3 must be completed first

**Description**:
- Create test fixtures in `app/tests/assets/` (sample DXF with known block counts, invalid file, empty drawing)
- Implement unit tests for extractor logic (`app/tests/core/test_extractor.py`) covering valid files, invalid files, and edge cases
- Implement unit tests for Excel writer (`app/tests/core/test_excel_writer.py`) verifying formatting, sorting, headers, and file output
- Achieve >80% code coverage and ensure all tests pass in <5 seconds

**Key Files**: `app/tests/core/test_extractor.py`, `app/tests/core/test_excel_writer.py`, `app/tests/assets/sample_drawing.dxf`

---

### Task 5: Launch Scripts and Deployment Tooling
**Focus Area**: Deployment and packaging
**Suggested Command**: `/dev:chore`
**Complexity**: Simple
**Dependencies**: Tasks 1-4 must be completed first

**Description**:
- Create application launch script (`scripts/start.sh`) using uv to run the GUI application
- Create optional Windows executable build script (`scripts/build_executable.sh`) using PyInstaller
- Update main README.md with quick start instructions, requirements, and usage examples
- Verify scripts work correctly and document platform-specific considerations

**Key Files**: `scripts/start.sh`, `scripts/build_executable.sh`, `README.md`

---

## Execution Order
1. Task 1 (no dependencies)
2. Task 2 (depends on Task 1 - needs logging and project structure)
3. Task 3 (depends on Task 2 - needs core extraction logic)
4. Task 4 (depends on Tasks 2 and 3 - tests both core and GUI)
5. Task 5 (depends on all previous tasks - final packaging)

## Notes
This breakdown maintains the strict sequential order outlined in the original implementation plan. Each task is self-contained with clear inputs and outputs. The core logic (Task 2) is independent of the UI, allowing for thorough testing before GUI integration. Task 4 can begin testing core logic while GUI is being finalized, but both must be complete before proceeding to Task 5. All tasks emphasize stdout logging for real-time monitoring by LLM agents during development.
