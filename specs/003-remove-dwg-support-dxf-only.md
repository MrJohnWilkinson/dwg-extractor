# Chore: Remove DWG Support - DXF Only

## Chore Description
The application currently references DWG file support throughout documentation, code, and tests. However, DWG extraction requires ODA (Open Design Alliance) File Converter which requires additional licensing fees. Since DWG support is no longer in scope, all references to DWG files must be removed so the application only references and supports DXF files.

This is a documentation and naming cleanup chore - the actual extraction functionality already only works with DXF files (ezdxf library reads DXF natively, DWG was never actually supported without ODA).

## Relevant Files
Use these files to resolve the chore:

- `README.md` - Contains project overview with DWG/DXF references in title, description, user flow, and tech stack
- `app/main.py` - GUI application with DWG references in:
  - Module docstring (line 4)
  - Class name `DWGExtractorApp` (line 41)
  - Window title (line 52)
  - Title label (line 72)
  - File dialog title and filetypes (lines 128-129)
  - Logger messages (line 49)
- `app/core/constants.py` - Contains:
  - Module docstring referencing DWG (lines 2, 5)
  - `SUPPORTED_EXTENSIONS` tuple with ".dwg" (line 14)
  - `MSG_SELECT_FILE` message (line 103)
- `app/core/extractor.py` - Contains:
  - Module docstring referencing DWG (lines 2, 4, 10)
  - Function docstrings (lines 323, 336, 347)
  - Error message for unsupported extensions (line 373)
- `app/core/excel_writer.py` - Contains:
  - Module docstring referencing DWG (lines 2, 11-12)
  - Function docstrings (line 214, 223-224)
- `app/core/types.py` - Module docstring referencing DWG (line 2)
- `app/core/logger.py` - Module docstring referencing DWG (line 2)
- `app/tests/core/test_extractor.py` - Contains:
  - Skipped test `test_extract_real_dwg_file` referencing DWG (lines 192-210)
- `app/tests/core/test_excel_writer.py` - Contains 45 occurrences of `test_drawing.dwg` in output path strings

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Core Constants
Update `app/core/constants.py`:
- Change module docstring from "DWG Block Extractor" to "DXF Block Extractor"
- Update comment from "DWG/DXF files" to "DXF files"
- Change `SUPPORTED_EXTENSIONS` from `(".dwg", ".dxf")` to `(".dxf",)` (single-element tuple)
- Update `MSG_SELECT_FILE` from "Please select a DWG or DXF file" to "Please select a DXF file"

### Step 2: Update Core Extractor Module
Update `app/core/extractor.py`:
- Change module docstring from "DWG/DXF extraction" to "DXF extraction"
- Update description from "DWG and DXF files" to "DXF files"
- Change example from `drawing.dwg` to `drawing.dxf`
- Update function docstrings from "DWG or DXF file" to "DXF file"
- Update error message from "Must be .dwg or .dxf" to "Must be .dxf"

### Step 3: Update Core Excel Writer Module
Update `app/core/excel_writer.py`:
- Change module docstring from "DWG Block Extractor" to "DXF Block Extractor"
- Update examples from `drawing.dwg` to `drawing.dxf`
- Update docstring from "DWG/DXF file" to "DXF file"

### Step 4: Update Core Types Module
Update `app/core/types.py`:
- Change module docstring from "DWG Block Extractor" to "DXF Block Extractor"

### Step 5: Update Core Logger Module
Update `app/core/logger.py`:
- Change module docstring from "DWG Block Extractor" to "DXF Block Extractor"

### Step 6: Update Main GUI Application
Update `app/main.py`:
- Change module docstring from "DWG Block Extractor" to "DXF Block Extractor"
- Update description from "DWG/DXF CAD files" to "DXF CAD files"
- Rename class from `DWGExtractorApp` to `DXFExtractorApp`
- Update class docstring from "DWG Block Extractor" to "DXF Block Extractor"
- Change window title from "DWG Block Extractor" to "DXF Block Extractor"
- Update title label text from "DWG Block Extractor" to "DXF Block Extractor"
- Update logger message from "DWG Block Extractor" to "DXF Block Extractor"
- Change file dialog title from "Select DWG or DXF File" to "Select DXF File"
- Update filetypes from `("DWG/DXF Files", "*.dwg *.dxf")` to `("DXF Files", "*.dxf")`

### Step 7: Update Test Files - Extractor Tests
Update `app/tests/core/test_extractor.py`:
- Remove the entire `test_extract_real_dwg_file` test method (lines 192-210) as it's a skipped DWG-specific test that's no longer relevant

### Step 8: Update Test Files - Excel Writer Tests
Update `app/tests/core/test_excel_writer.py`:
- Replace all 45 occurrences of `test_drawing.dwg` with `test_drawing.dxf` using find/replace

### Step 9: Update README Documentation
Update `README.md`:
- Change title from "DWG Block Extractor" to "DXF Block Extractor"
- Update description from "DWG/DXF CAD files" to "DXF CAD files"
- Change user flow from "Select DWG/DXF" to "Select DXF"
- Update tech stack from "reads DWG/DXF files" to "reads DXF files"
- Keep project directory name `dwg-extractor/` unchanged (renaming directories is out of scope)
- Update extractor.py comment from "DWG/DXF extraction" to "DXF extraction"

### Step 10: Run Validation Commands
Execute all validation commands to ensure zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/ -v` - Run all tests to validate no regressions
- `uv run mypy app/` - Run type checker to ensure type annotations are valid
- `uv run ruff check app/` - Run linter to catch any code issues
- `grep -r -i "dwg" app/ --include="*.py" | grep -v "dwg-extractor"` - Verify no DWG references remain in Python code (excluding directory name)
- `grep -r -i "dwg" README.md | grep -v "dwg-extractor"` - Verify no DWG references remain in README (excluding directory name)

## Notes
- The project directory name `dwg-extractor` is NOT being renamed as that would require updating git remotes, CI/CD configs, and other infrastructure. The directory name is historical and acceptable to keep.
- The `.history/` directory contains historical file versions and should NOT be modified.
- The `DWGBlockExtractor.spec` PyInstaller spec file exists but is a build artifact - consider renaming to `DXFBlockExtractor.spec` if time permits, but it's low priority.
- ezdxf library natively reads DXF files; DWG support was never actually functional without ODA File Converter.
