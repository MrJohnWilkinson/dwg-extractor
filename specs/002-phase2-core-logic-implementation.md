# Feature: Phase 2 - Core Logic Implementation

## Feature Description
Implement the core business logic for the DWG Block Extractor application, including DWG/DXF file parsing, block insertion counting, and Excel file generation. This phase transforms placeholder modules into fully functional extraction and reporting components with comprehensive logging, error handling, and data validation. The implementation will enable the application to read CAD files, extract block insertion counts, and generate formatted Excel reports with proper sorting and auto-filtering.

## User Story
As a developer implementing the DWG Block Extractor
I want to create the core extraction and Excel generation logic
So that the application can process DWG/DXF files and generate accurate Excel reports with block insertion counts

## Problem Statement
Phase 1 established the project structure and dependencies, but the core modules (constants.py, extractor.py, excel_writer.py) are empty placeholders. The application cannot process DWG/DXF files or generate Excel reports without implementing the extraction logic, data aggregation, and file writing functionality. Additionally, proper error handling, logging, and validation are needed to ensure reliability when processing real-world CAD files that may be corrupted, empty, or contain thousands of blocks.

## Solution Statement
Implement three core modules that work together to provide complete extraction and reporting functionality:

1. **constants.py** - Define all application-wide constants including file extensions, Excel column names, worksheet names, and user-facing messages for consistent behavior across modules

2. **extractor.py** - Implement DWG/DXF file parsing using ezdxf library to iterate through modelspace INSERT entities, count block references by name, and return aggregated data with comprehensive error handling and logging

3. **excel_writer.py** - Implement Excel file generation using pandas and openpyxl to create formatted spreadsheets with sorted data, auto-filtering, proper column widths, and timestamped filenames

All modules will integrate with the existing logger.py module to provide real-time stdout logging for monitoring during development and execution.

## Relevant Files
Use these files to implement the feature:

- **`app/core/constants.py`** (exists, currently placeholder) - Will be populated with all application constants including supported file extensions (.dwg, .dxf), Excel configuration (column names, worksheet name), and UI messages for errors and success states

- **`app/core/extractor.py`** (exists, currently placeholder) - Will implement the `extract_blocks(file_path: str) -> dict[str, int]` function to parse DWG/DXF files using ezdxf, iterate through modelspace INSERT entities, count block insertions by name, and return aggregated counts with proper error handling

- **`app/core/excel_writer.py`** (exists, currently placeholder) - Will implement the `write_excel(block_data: dict[str, int], output_path: str) -> str` function to convert block count dictionaries to pandas DataFrames, sort by count descending, write formatted Excel files with auto-filter and column widths, and return the full path to the created file

- **`app/core/logger.py`** (exists, fully implemented in Phase 1) - Provides the `setup_logger(name: str)` function used by all core modules for stdout logging with standardized format

- **`app/pyproject.toml`** (exists, fully configured in Phase 1) - Contains all required dependencies (ezdxf, pandas, openpyxl) that will be used in this phase

### New Files
- **`app/tests/core/test_extractor.py`** - Unit tests for extraction logic including valid files, invalid files, empty drawings, missing files, and count accuracy verification

- **`app/tests/core/test_excel_writer.py`** - Unit tests for Excel generation including basic file creation, header verification, sort order validation, auto-filter confirmation, filename format checks, and empty data handling

- **`app/tests/assets/sample_drawing.dxf`** - Test fixture DXF file with known block counts (10x VALVE_GATE, 5x PIPE_SUPPORT, 3x EQUIPMENT_TAG) for automated testing

- **`app/tests/assets/empty_drawing.dxf`** - Test fixture DXF file with valid structure but no block insertions for edge case testing

- **`app/tests/assets/invalid.dxf`** - Test fixture file with corrupted/invalid DXF content for error handling validation

## Implementation Plan
### Phase 1: Foundation
- Review Phase 1 implementation to understand existing logger.py functionality and project structure
- Verify all dependencies (ezdxf, pandas, openpyxl) are installed and importable via `uv run python -c "import ezdxf, pandas, openpyxl"`
- Study ezdxf documentation for modelspace iteration and INSERT entity handling
- Study pandas/openpyxl documentation for Excel writing with formatting
- Define all constants needed across the application for consistent behavior

### Phase 2: Core Implementation
- Implement constants.py with all application-wide constants
- Implement extractor.py with full DWG/DXF parsing logic, error handling, and logging
- Implement excel_writer.py with Excel generation, formatting, sorting, and logging
- Create test fixtures (sample_drawing.dxf, empty_drawing.dxf, invalid.dxf) using ezdxf
- Write comprehensive unit tests for both extractor and excel_writer modules
- Validate all modules work correctly with real DWG files from app/tests/assets/

### Phase 3: Integration
- Test integration between extractor.py and excel_writer.py with end-to-end workflow
- Verify logging output appears correctly on stdout for all operations
- Test error handling paths with invalid files, missing files, and empty drawings
- Validate Excel output format matches specification (headers, sorting, auto-filter)
- Run full test suite with pytest to ensure >80% code coverage
- Validate against real DWG files (Supermarket-2020.dwg, floorplan supermarket v3.dwg, floorplan supermarket v3 new chilled dept.dwg)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Implement Application Constants
- Open `app/core/constants.py` and replace placeholder content
- Define file extension constants:
  - `SUPPORTED_EXTENSIONS = ('.dwg', '.dxf')` - Tuple of supported file extensions for validation
- Define Excel configuration constants:
  - `EXCEL_COLUMN_BLOCK_NAME = 'Block Name'` - Column header for block names
  - `EXCEL_COLUMN_COUNT = 'Insertion Count'` - Column header for insertion counts
  - `EXCEL_WORKSHEET_NAME = 'Block Summary'` - Worksheet name for Excel output
- Define UI message constants:
  - `MSG_SELECT_FILE = 'Please select a DWG or DXF file'` - File selection prompt
  - `MSG_PROCESSING = 'Processing...'` - Processing status message
  - `MSG_SUCCESS = 'Extraction complete'` - Success message
  - `MSG_ERROR_INVALID_FILE = 'Invalid or corrupted file'` - Invalid file error
  - `MSG_ERROR_NO_BLOCKS = 'No blocks found in file'` - No blocks warning
  - `MSG_ERROR_FILE_NOT_FOUND = 'File not found'` - Missing file error
- Add comprehensive module docstring explaining the purpose and usage of constants
- Verify the file is importable: `cd app && uv run python -c "from core.constants import *; print('Constants loaded successfully')"`

### Step 2: Implement DWG/DXF Extraction Logic
- Open `app/core/extractor.py` and implement complete extraction functionality
- Add imports:
  - `from pathlib import Path` - For file path handling
  - `import ezdxf` - For DWG/DXF parsing
  - `from .logger import setup_logger` - For logging integration
  - `from .constants import SUPPORTED_EXTENSIONS` - For file validation
- Create module-level logger: `logger = setup_logger(__name__)`
- Implement `extract_blocks(file_path: str) -> dict[str, int]` function:
  - Log INFO: "Starting block extraction from {file_path}"
  - Validate file exists using Path(file_path).exists(), raise FileNotFoundError if missing
  - Validate file extension is in SUPPORTED_EXTENSIONS, raise ValueError if invalid
  - Load DWG/DXF file using `ezdxf.readfile(file_path)` with try/except for DXFError
  - Get modelspace using `doc.modelspace()`
  - Initialize empty dictionary `block_counts = {}`
  - Iterate through modelspace entities: `for entity in msp:`
  - Filter for INSERT entities: `if entity.dxftype() == 'INSERT':`
  - Get block name: `block_name = entity.dxf.name`
  - Increment count: `block_counts[block_name] = block_counts.get(block_name, 0) + 1`
  - Log INFO: "Found {total_count} block insertions across {unique_count} unique blocks"
  - Return block_counts dictionary
  - Add error handling with logging:
    - FileNotFoundError: Log ERROR and re-raise
    - ezdxf.DXFError: Log ERROR "Invalid or corrupted DXF/DWG file" and re-raise as ValueError
    - General Exception: Log ERROR with traceback and re-raise
- Add comprehensive docstring with parameter descriptions, return value, and raises section
- Add type hints for all parameters and return values
- Verify the module works: `cd app && uv run python -c "from core.extractor import extract_blocks; print('Extractor module loaded')"`

### Step 3: Implement Excel Generation Logic
- Open `app/core/excel_writer.py` and implement complete Excel writing functionality
- Add imports:
  - `from pathlib import Path` - For file path handling
  - `from datetime import datetime` - For timestamp generation
  - `import pandas as pd` - For DataFrame creation and Excel writing
  - `from openpyxl import load_workbook` - For post-processing formatting
  - `from openpyxl.utils import get_column_letter` - For column width adjustment
  - `from .logger import setup_logger` - For logging integration
  - `from .constants import EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_COUNT, EXCEL_WORKSHEET_NAME` - For Excel configuration
- Create module-level logger: `logger = setup_logger(__name__)`
- Implement `write_excel(block_data: dict[str, int], output_path: str) -> str` function:
  - Log INFO: "Starting Excel file generation with {len(block_data)} unique blocks"
  - Validate block_data is not None, raise ValueError if None
  - Handle empty block_data gracefully (create Excel with headers only, log WARNING)
  - Convert dictionary to pandas DataFrame with columns from constants
  - Sort DataFrame by count column descending: `df.sort_values(by=EXCEL_COLUMN_COUNT, ascending=False, inplace=True)`
  - Generate timestamped filename: `timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')`, `filename = f"{Path(output_path).stem}_blocks_{timestamp}.xlsx"`
  - Construct full output path: `full_path = Path(output_path).parent / filename`
  - Write Excel file using pandas: `df.to_excel(full_path, sheet_name=EXCEL_WORKSHEET_NAME, index=False, engine='openpyxl')`
  - Load workbook for post-processing: `wb = load_workbook(full_path)`
  - Get worksheet: `ws = wb[EXCEL_WORKSHEET_NAME]`
  - Apply auto-filter: `ws.auto_filter.ref = ws.dimensions`
  - Adjust column widths:
    - Block Name column: 30 characters
    - Insertion Count column: 15 characters
  - Save workbook: `wb.save(full_path)`
  - Log INFO: "Excel file created successfully at {full_path}"
  - Return full path as string: `return str(full_path)`
  - Add error handling with logging:
    - ValueError for invalid inputs: Log ERROR and re-raise
    - General Exception during write: Log ERROR with traceback and re-raise
- Add comprehensive docstring with parameter descriptions, return value, and raises section
- Add type hints for all parameters and return values
- Verify the module works: `cd app && uv run python -c "from core.excel_writer import write_excel; print('Excel writer module loaded')"`

### Step 4: Create Test Fixtures
- Create test fixture DXF files using ezdxf for automated testing
- Create a temporary Python script `app/tests/assets/generate_fixtures.py`:
  - Import ezdxf
  - Generate `sample_drawing.dxf` with known block counts:
    - Create new DXF document: `doc = ezdxf.new('R2010')`
    - Get modelspace: `msp = doc.modelspace()`
    - Create block definitions: `doc.blocks.new(name='VALVE_GATE')`, `doc.blocks.new(name='PIPE_SUPPORT')`, `doc.blocks.new(name='EQUIPMENT_TAG')`
    - Insert 10x VALVE_GATE blocks: `for i in range(10): msp.add_blockref('VALVE_GATE', (i*10, 0))`
    - Insert 5x PIPE_SUPPORT blocks: `for i in range(5): msp.add_blockref('PIPE_SUPPORT', (i*10, 10))`
    - Insert 3x EQUIPMENT_TAG blocks: `for i in range(3): msp.add_blockref('EQUIPMENT_TAG', (i*10, 20))`
    - Save: `doc.saveas('app/tests/assets/sample_drawing.dxf')`
  - Generate `empty_drawing.dxf` with no blocks:
    - Create new DXF document: `doc = ezdxf.new('R2010')`
    - Save immediately without adding blocks: `doc.saveas('app/tests/assets/empty_drawing.dxf')`
  - Generate `invalid.dxf` as corrupted file:
    - Write random text content to file to simulate corruption: `Path('app/tests/assets/invalid.dxf').write_text('INVALID DXF CONTENT\nNOT A REAL DXF FILE')`
- Run the fixture generation script: `cd app && uv run python tests/assets/generate_fixtures.py`
- Verify fixtures were created: `ls -la app/tests/assets/*.dxf`
- Delete the generation script after fixtures are created: `rm app/tests/assets/generate_fixtures.py`
- Verify sample_drawing.dxf can be loaded: `cd app && uv run python -c "import ezdxf; doc = ezdxf.readfile('tests/assets/sample_drawing.dxf'); print('Fixture valid')"`

### Step 5: Implement Unit Tests for Extractor Module
- Create `app/tests/core/test_extractor.py` with comprehensive test coverage
- Add imports:
  - `import pytest` - Testing framework
  - `from pathlib import Path` - Path handling
  - `from core.extractor import extract_blocks` - Function under test
  - `import ezdxf` - For error type checking
- Define test class: `class TestExtractor:`
- Implement test cases:
  - `test_extract_valid_file()`:
    - Load `tests/assets/sample_drawing.dxf`
    - Call extract_blocks()
    - Assert result is dict with 3 keys: VALVE_GATE, PIPE_SUPPORT, EQUIPMENT_TAG
    - Assert counts are correct: VALVE_GATE=10, PIPE_SUPPORT=5, EQUIPMENT_TAG=3
  - `test_extract_empty_file()`:
    - Load `tests/assets/empty_drawing.dxf`
    - Call extract_blocks()
    - Assert result is empty dict {}
  - `test_extract_invalid_file()`:
    - Load `tests/assets/invalid.dxf`
    - Use pytest.raises(ValueError) to assert ValueError is raised
  - `test_extract_missing_file()`:
    - Provide non-existent file path
    - Use pytest.raises(FileNotFoundError) to assert FileNotFoundError is raised
  - `test_extract_counts_accuracy()`:
    - Load `tests/assets/sample_drawing.dxf`
    - Call extract_blocks()
    - Assert total count equals 18 (10+5+3)
    - Assert all counts are positive integers
  - `test_extract_returns_dict()`:
    - Load `tests/assets/sample_drawing.dxf`
    - Call extract_blocks()
    - Assert return type is dict
    - Assert all keys are strings
    - Assert all values are integers
- Add module docstring explaining test purpose and coverage
- Verify tests can be discovered: `cd app && uv run pytest tests/core/test_extractor.py --collect-only`

### Step 6: Implement Unit Tests for Excel Writer Module
- Create `app/tests/core/test_excel_writer.py` with comprehensive test coverage
- Add imports:
  - `import pytest` - Testing framework
  - `from pathlib import Path` - Path handling
  - `import pandas as pd` - For Excel verification
  - `from openpyxl import load_workbook` - For format verification
  - `from core.excel_writer import write_excel` - Function under test
  - `from core.constants import EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_COUNT, EXCEL_WORKSHEET_NAME` - For validation
  - `import tempfile` - For temporary output directories
  - `import os` - For file cleanup
- Define test class: `class TestExcelWriter:`
- Implement test cases:
  - `test_write_excel_basic()`:
    - Create sample block data: `{'VALVE': 10, 'PIPE': 5}`
    - Use tempfile for output directory
    - Call write_excel()
    - Assert file exists at returned path
    - Assert file is valid Excel format by loading with pandas
    - Clean up temp file
  - `test_excel_has_headers()`:
    - Create sample block data
    - Call write_excel()
    - Load Excel with pandas
    - Assert columns match constants: EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_COUNT
    - Clean up temp file
  - `test_excel_sorted_descending()`:
    - Create unsorted block data: `{'VALVE': 5, 'PIPE': 10, 'TAG': 3}`
    - Call write_excel()
    - Load Excel with pandas
    - Assert first row has count=10 (PIPE)
    - Assert last row has count=3 (TAG)
    - Clean up temp file
  - `test_excel_autofilter()`:
    - Create sample block data
    - Call write_excel()
    - Load workbook with openpyxl
    - Get worksheet
    - Assert auto_filter.ref is not None
    - Clean up temp file
  - `test_filename_format()`:
    - Create sample block data
    - Provide output path: `/tmp/test_drawing.dwg`
    - Call write_excel()
    - Assert returned filename matches pattern: `test_drawing_blocks_YYYYMMDD_HHMMSS.xlsx`
    - Assert file exists at returned path
    - Clean up temp file
  - `test_empty_data()`:
    - Create empty block data: `{}`
    - Call write_excel()
    - Assert file is created
    - Load Excel with pandas
    - Assert DataFrame has 0 rows (headers only)
    - Clean up temp file
  - `test_column_widths()`:
    - Create sample block data
    - Call write_excel()
    - Load workbook with openpyxl
    - Get worksheet
    - Assert column widths are set correctly (Block Name=30, Insertion Count=15)
    - Clean up temp file
- Add pytest fixtures:
  - `@pytest.fixture` for temp directory creation and cleanup
  - `@pytest.fixture` for sample block data
- Add module docstring explaining test purpose and coverage
- Verify tests can be discovered: `cd app && uv run pytest tests/core/test_excel_writer.py --collect-only`

### Step 7: Run Unit Tests and Validate Coverage
- Run all core tests: `cd app && uv run pytest tests/core/ -v`
- Verify all tests pass with 0 failures
- Run tests with coverage report: `cd app && uv run pytest tests/core/ --cov=core --cov-report=term-missing`
- Verify code coverage is >80% for extractor.py and excel_writer.py
- Review coverage report for any missing lines and add tests if needed
- Generate HTML coverage report for detailed analysis: `cd app && uv run pytest tests/core/ --cov=core --cov-report=html`
- Fix any failing tests before proceeding

### Step 8: Integration Testing with Real DWG Files
- Test extractor.py with real DWG files from app/tests/assets/:
  - Extract blocks from `Supermarket-2020.dwg`: `cd app && uv run python -c "from core.extractor import extract_blocks; result = extract_blocks('tests/assets/Supermarket-2020.dwg'); print(f'Found {len(result)} unique blocks with {sum(result.values())} total insertions')"`
  - Extract blocks from `floorplan supermarket v3.dwg`: `cd app && uv run python -c "from core.extractor import extract_blocks; result = extract_blocks('tests/assets/floorplan supermarket v3.dwg'); print(f'Found {len(result)} unique blocks')"`
  - Extract blocks from `floorplan supermarket v3 new chilled dept.dwg`: `cd app && uv run python -c "from core.extractor import extract_blocks; result = extract_blocks('tests/assets/floorplan supermarket v3 new chilled dept.dwg'); print(f'Found {len(result)} unique blocks')"`
- Verify all extractions complete without errors and log to stdout correctly
- Test end-to-end workflow (extraction + Excel generation):
  - Create test script: `cd app && uv run python -c "from core.extractor import extract_blocks; from core.excel_writer import write_excel; blocks = extract_blocks('tests/assets/Supermarket-2020.dwg'); excel_path = write_excel(blocks, 'tests/assets/Supermarket-2020.dwg'); print(f'Excel created: {excel_path}')"`
  - Verify Excel file is created with correct format
  - Open Excel file manually to verify headers, sorting, and auto-filter
  - Clean up generated Excel files after verification
- Verify logging output appears on stdout for all operations
- Document any issues or edge cases discovered during integration testing

### Step 9: Validate All Implementation Against Success Criteria
- Verify `extract_blocks()` correctly counts blocks in valid DXF files (run tests)
- Verify `extract_blocks()` raises appropriate exceptions for invalid files (run tests)
- Verify `write_excel()` creates properly formatted Excel files (run tests)
- Verify Excel files have correct headers, sorting, and auto-filter (manual + automated tests)
- Verify all modules log to stdout for real-time monitoring (check logs during test runs)
- Run full validation command suite from this plan's Validation Commands section
- Fix any validation failures before marking phase complete

## Testing Strategy
### Unit Tests
- **Extractor Module Tests**:
  - Valid file processing with known block counts
  - Empty file handling (no blocks)
  - Invalid/corrupted file error handling
  - Missing file error handling
  - Count accuracy verification
  - Return type validation (dict with string keys, int values)

- **Excel Writer Module Tests**:
  - Basic file creation with sample data
  - Header column name verification
  - Descending sort order validation
  - Auto-filter presence confirmation
  - Timestamped filename format verification
  - Empty data handling (headers only)
  - Column width formatting verification

### Integration Tests
- **End-to-End Workflow**:
  - Extract blocks from real DWG file
  - Generate Excel file from extracted data
  - Verify Excel file format, headers, sorting, auto-filter
  - Verify logging output appears on stdout

- **Real File Processing**:
  - Test with 3 real DWG files from app/tests/assets/
  - Verify extraction completes without errors
  - Verify Excel generation succeeds
  - Verify file sizes and performance

### Edge Cases
- **File Handling Edge Cases**:
  - Non-existent file path
  - Invalid file extension (e.g., .txt, .pdf)
  - Corrupted DWG/DXF file
  - Empty DXF file (valid structure, no blocks)
  - Very large files (10,000+ blocks)
  - Files with special characters in block names
  - Files with duplicate block names (same block inserted multiple times)

- **Data Edge Cases**:
  - Empty block_data dictionary (no blocks found)
  - Single block type with 1 insertion
  - Hundreds of unique block types
  - Block names with Unicode characters
  - Block names with spaces and special characters

- **Excel Generation Edge Cases**:
  - Output path with spaces in directory names
  - Output path to non-existent directory (should fail gracefully)
  - Insufficient disk space (rare, but should be handled)
  - File already exists with same timestamp (extremely rare)

### Playwright MCP Tests
Not applicable for Phase 2. GUI testing will be implemented in Phase 3 after the CustomTkinter interface is built. Phase 2 focuses on core business logic only, which is tested via unit and integration tests.

## Acceptance Criteria
- [ ] `app/core/constants.py` contains all required constants (file extensions, Excel configuration, UI messages)
- [ ] `app/core/extractor.py` successfully extracts block counts from valid DWG/DXF files
- [ ] `app/core/extractor.py` raises FileNotFoundError for missing files
- [ ] `app/core/extractor.py` raises ValueError for invalid/corrupted files
- [ ] `app/core/extractor.py` returns empty dict for valid files with no blocks
- [ ] `app/core/extractor.py` logs all operations to stdout with INFO and ERROR levels
- [ ] `app/core/excel_writer.py` creates valid Excel files with proper formatting
- [ ] `app/core/excel_writer.py` sorts block data by count descending
- [ ] `app/core/excel_writer.py` applies auto-filter to Excel headers
- [ ] `app/core/excel_writer.py` sets proper column widths (Block Name=30, Count=15)
- [ ] `app/core/excel_writer.py` generates timestamped filenames matching pattern `{input_name}_blocks_{timestamp}.xlsx`
- [ ] `app/core/excel_writer.py` handles empty block data gracefully (creates headers-only file)
- [ ] `app/core/excel_writer.py` logs all operations to stdout with INFO, WARNING, and ERROR levels
- [ ] Test fixtures exist: `sample_drawing.dxf`, `empty_drawing.dxf`, `invalid.dxf`
- [ ] `test_extractor.py` has 6+ test cases with 100% pass rate
- [ ] `test_excel_writer.py` has 7+ test cases with 100% pass rate
- [ ] Code coverage for core modules is >80%
- [ ] All unit tests pass: `cd app && uv run pytest tests/core/ -v`
- [ ] Integration testing with real DWG files completes successfully
- [ ] All validation commands execute without errors
- [ ] No regressions in Phase 1 functionality (logging still works correctly)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd app && uv run python -c "from core.constants import *; print(f'SUPPORTED_EXTENSIONS: {SUPPORTED_EXTENSIONS}'); print(f'EXCEL_COLUMN_BLOCK_NAME: {EXCEL_COLUMN_BLOCK_NAME}'); print(f'EXCEL_COLUMN_COUNT: {EXCEL_COLUMN_COUNT}'); print('Constants loaded successfully')"` - Verify constants module is implemented correctly

- `cd app && uv run python -c "from core.extractor import extract_blocks; print('Extractor module imported successfully')"` - Verify extractor module is importable

- `cd app && uv run python -c "from core.excel_writer import write_excel; print('Excel writer module imported successfully')"` - Verify excel_writer module is importable

- `cd app && test -f tests/assets/sample_drawing.dxf && echo 'sample_drawing.dxf exists'` - Verify sample test fixture exists

- `cd app && test -f tests/assets/empty_drawing.dxf && echo 'empty_drawing.dxf exists'` - Verify empty test fixture exists

- `cd app && test -f tests/assets/invalid.dxf && echo 'invalid.dxf exists'` - Verify invalid test fixture exists

- `cd app && uv run python -c "import ezdxf; doc = ezdxf.readfile('tests/assets/sample_drawing.dxf'); msp = doc.modelspace(); print(f'Sample fixture loaded: {len(list(msp))} entities')"` - Verify sample fixture is valid DXF

- `cd app && uv run python -c "from core.extractor import extract_blocks; result = extract_blocks('tests/assets/sample_drawing.dxf'); print(f'Extraction result: {result}'); assert result['VALVE_GATE'] == 10; assert result['PIPE_SUPPORT'] == 5; assert result['EQUIPMENT_TAG'] == 3; print('Extraction counts verified')"` - Verify extractor works with sample fixture

- `cd app && uv run python -c "from core.extractor import extract_blocks; from core.excel_writer import write_excel; blocks = extract_blocks('tests/assets/sample_drawing.dxf'); excel_path = write_excel(blocks, 'tests/assets/sample_drawing.dxf'); print(f'End-to-end test: Excel created at {excel_path}'); import os; os.remove(excel_path); print('Cleanup complete')"` - Verify end-to-end workflow (extraction + Excel generation)

- `cd app && uv run pytest tests/core/test_extractor.py -v` - Run all extractor unit tests

- `cd app && uv run pytest tests/core/test_excel_writer.py -v` - Run all excel_writer unit tests

- `cd app && uv run pytest tests/core/ -v` - Run all core module tests

- `cd app && uv run pytest tests/core/ --cov=core --cov-report=term-missing` - Run tests with coverage report (must show >80% coverage)

- `cd app && uv run python -c "from core.extractor import extract_blocks; result = extract_blocks('tests/assets/Supermarket-2020.dwg'); print(f'Real file test: Found {len(result)} unique blocks with {sum(result.values())} total insertions')"` - Test with real DWG file (Supermarket-2020.dwg)

- `cd app && uv run python -c "from core.extractor import extract_blocks; result = extract_blocks('tests/assets/floorplan supermarket v3.dwg'); print(f'Real file test: Found {len(result)} unique blocks with {sum(result.values())} total insertions')"` - Test with real DWG file (floorplan supermarket v3.dwg)

- `cd app && uv run python -c "from core.logger import setup_logger; logger = setup_logger('test'); logger.info('Phase 1 logger still works'); print('Logger validation successful')"` - Verify Phase 1 logging functionality has no regressions

## Notes
- **Phase 2 Scope**: This phase implements only the core business logic (extraction and Excel generation). GUI implementation will happen in Phase 3.

- **Test-Driven Development**: Tests should be written alongside implementation, not after. This ensures better design and catches issues early.

- **Real DWG Files**: Three real DWG files already exist in `app/tests/assets/` from Phase 1 setup. These will be used for integration testing in addition to the generated DXF fixtures.

- **ezdxf DWG Support**: The ezdxf library can read DWG files directly (R13-R2018+) without conversion. Older DWG versions (R12 and earlier) may require the ODA File Converter, but this is not expected to be an issue for modern CAD files.

- **Performance Considerations**: Phase 2 implementation is single-threaded. Performance optimization and threading will be addressed in Phase 3 (GUI) if needed. Initial target is processing 1,000 blocks in <5 seconds, which should be easily achievable.

- **Error Handling Strategy**: All errors should be logged to stdout before raising exceptions. This ensures LLM agents can monitor and debug issues during ADW workflow execution.

- **Excel Timestamp Format**: The timestamp format `YYYYMMDD_HHMMSS` ensures filenames are sortable and prevents overwrites. Example: `drawing_blocks_20250117_143022.xlsx`.

- **Logging Integration**: All modules use the centralized logger from Phase 1. Logging format is consistent: `%(asctime)s [%(name)s] %(levelname)s: %(message)s`.

- **Code Coverage Target**: Aim for >80% coverage as specified in the original plan. Focus coverage on critical paths (extraction logic, Excel generation) rather than trivial code (getters, constants).

- **Future Phases**: Phase 3 will build the CustomTkinter GUI that calls these core modules. Phase 4 will add additional integration tests. Phase 5 will create deployment scripts.

- **Dependency Note**: All required dependencies (ezdxf, pandas, openpyxl) are already installed via Phase 1. No new dependencies needed for Phase 2.
