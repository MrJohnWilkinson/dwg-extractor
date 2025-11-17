# Feature: Native DWG File Extraction Support

## Feature Description
Add true DWG file extraction capability to the DWG Block Extractor application using ezdxf's ODA File Converter addon. Currently, the application claims to support DWG files but only works with DXF files because `ezdxf.readfile()` doesn't support DWG format natively. This feature implements a fallback mechanism that attempts standard DXF reading first, then automatically uses the ODA File Converter addon for true DWG files, providing seamless support for both formats without requiring users to manually convert files.

## User Story
As a CAD professional working with AutoCAD drawings
I want to extract block counts directly from native DWG files
So that I don't have to manually convert DWG files to DXF format before processing them

## Problem Statement
The application currently advertises DWG support in its name ("DWG Block Extractor"), UI file dialogs, and documentation, but `ezdxf.readfile()` can only read DXF files natively. When users select actual DWG files (which are binary AutoCAD format), the extraction fails. This creates a poor user experience and misleading expectations. The test suite even includes three real DWG files (`Supermarket-2020.dwg`, `floorplan supermarket v3.dwg`, `floorplan supermarket v3 new chilled dept.dwg`) but has a skipped test acknowledging this limitation.

## Solution Statement
Implement a two-tier extraction strategy in the `extract_blocks()` function:

1. **Primary Path**: Attempt to read files using standard `ezdxf.readfile()` (works for DXF and some DWG variants)
2. **Fallback Path**: If the primary method fails with a DWG file, automatically use `ezdxf.addons.odafc.readfile()` to convert and load the file

This approach provides:
- **Graceful degradation**: Works without ODA File Converter for DXF files
- **Automatic DWG support**: Seamlessly handles true DWG files when ODA File Converter is installed
- **Clear error messaging**: Informs users if they need to install ODA File Converter for DWG support
- **No breaking changes**: Existing DXF functionality remains unchanged

## Relevant Files
Use these files to implement the feature:

- **app/core/extractor.py** (lines 24-88) - Core extraction logic that currently uses `ezdxf.readfile()`. Needs modification to add fallback to `odafc.readfile()` for DWG files with proper error handling for missing ODA File Converter.

- **app/core/constants.py** (lines 13-27) - Contains `SUPPORTED_EXTENSIONS` tuple and user-facing error messages. May need new constant for ODA File Converter installation instructions.

- **app/core/logger.py** - Logging utility used throughout extraction process. Will log fallback attempts and ODA File Converter status.

- **app/tests/core/test_extractor.py** (lines 98-113) - Contains skipped test `test_extract_real_dwg_file()` that explicitly documents DWG limitation. This test should be enabled and enhanced to validate the new DWG support.

- **pyproject.toml** (lines 1-47) - Project dependencies managed by uv. The ezdxf library already includes the odafc addon, so no new dependencies are required.

- **README.md** (lines 1-73) - Documentation claiming DWG support. Should be updated to mention ODA File Converter requirement for true DWG files.

### New Files
No new files are required. All changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation
1. Research and document the exact error types raised by `ezdxf.readfile()` when it encounters a true DWG file vs. a corrupted file
2. Research the exact error raised by `odafc.readfile()` when ODA File Converter is not installed
3. Add new error message constants to `app/core/constants.py` for ODA File Converter installation instructions
4. Update `SUPPORTED_EXTENSIONS` documentation in `app/core/constants.py` to clarify DWG support requirements

### Phase 2: Core Implementation
1. Modify `extract_blocks()` in `app/core/extractor.py` to implement two-tier reading strategy:
   - Attempt primary read with `ezdxf.readfile()`
   - On DWGStructureError or similar DWG-specific exceptions, attempt fallback to `odafc.readfile()`
   - Add comprehensive logging for both attempts and fallback scenarios
2. Implement proper exception handling chain:
   - Catch ODA File Converter missing errors and provide installation instructions
   - Preserve existing error handling for file not found, unsupported extensions, and corrupted files
   - Ensure error messages clearly distinguish between "file corrupted" vs "needs ODA File Converter"
3. Add type hints for new code paths to maintain mypy compliance

### Phase 3: Integration
1. Update test suite to validate DWG extraction with real DWG files
2. Add tests for graceful degradation when ODA File Converter is not available
3. Update README.md with ODA File Converter installation instructions and clarified DWG support documentation
4. Verify GUI still works correctly with both DXF and DWG files

## Step by Step Tasks

### Step 1: Research Exception Types
- Create a test script to identify exact exceptions raised by `ezdxf.readfile()` for DWG files
- Document the exception types in implementation notes
- Test with actual DWG files from `app/tests/assets/` directory

### Step 2: Add New Constants
- Add `MSG_ERROR_ODA_CONVERTER_REQUIRED` constant with installation instructions to `app/core/constants.py`
- Add docstring explaining when this message is shown
- Run mypy to verify type correctness

### Step 3: Implement Two-Tier Extraction Strategy
- Import `odafc` addon in `app/core/extractor.py`: `from ezdxf.addons import odafc`
- Wrap existing `ezdxf.readfile()` call in try-except block
- Add fallback logic for DWG-specific errors to attempt `odafc.readfile()`
- Add logging statements for primary attempt, fallback attempt, and success/failure of each
- Handle missing ODA File Converter with clear error message
- Preserve all existing error handling (FileNotFoundError, ValueError for corrupted files, etc.)
- Maintain function signature and return type unchanged
- Run mypy to ensure type safety

### Step 4: Create Comprehensive Unit Tests
- Create new test file `app/tests/core/test_extractor_dwg.py` for DWG-specific tests
- Add test: `test_extract_real_dwg_file_with_odafc()` - validates extraction from actual DWG file when ODA Converter is available
- Add test: `test_extract_real_dwg_file_without_odafc()` - validates graceful error when ODA Converter is missing (use pytest.skip if converter is installed)
- Add test: `test_fallback_logging()` - validates that fallback attempts are properly logged
- Enable and update the currently skipped `test_extract_real_dwg_file()` test in `app/tests/core/test_extractor.py`
- All tests must pass with proper skip conditions for environments without ODA File Converter

### Step 5: Update Existing Tests
- Remove `@pytest.mark.skip` decorator from `test_extract_real_dwg_file()` in `app/tests/core/test_extractor.py`
- Update test to check for either successful extraction or clear error about missing ODA Converter
- Ensure test validates proper block count structure (dict with string keys and int values)
- Ensure test works on systems both with and without ODA File Converter installed

### Step 6: Update Documentation
- Update README.md "Tech Stack" section to mention optional ODA File Converter for DWG support
- Add new "DWG File Support" section to README.md explaining:
  - DXF files work out of the box
  - DWG files require ODA File Converter installation
  - Installation instructions for Windows, Linux, macOS
  - Link to ODA File Converter download page
- Update "Usage" section to clarify file format support

### Step 7: Validation and Testing
- Run all validation commands to ensure zero regressions
- Test manually with the application using both DXF and DWG files
- Verify error messages are user-friendly
- Verify logging provides adequate debugging information
- Ensure mypy passes with no type errors

## Testing Strategy

### Unit Tests
1. **Primary path tests** (DXF files):
   - Existing tests continue to work unchanged
   - `test_extract_valid_file()` validates DXF extraction
   - `test_extract_empty_file()` validates empty DXF handling

2. **Fallback path tests** (DWG files):
   - `test_extract_real_dwg_file_with_odafc()` validates successful DWG extraction when ODA Converter is available
   - `test_extract_real_dwg_file_without_odafc()` validates graceful error when ODA Converter is missing
   - `test_fallback_logging()` validates proper logging of fallback attempts

3. **Error handling tests**:
   - Existing error tests remain unchanged (FileNotFoundError, ValueError, etc.)
   - New test validates ODA Converter missing error provides installation instructions

### Integration Tests
1. Test GUI workflow end-to-end with DWG file:
   - Browse and select DWG file
   - Extract blocks
   - Verify Excel generation
   - Verify auto-open functionality

2. Test error dialogs show appropriate messages for missing ODA Converter

### Edge Cases
1. **DWG file that ezdxf.readfile() can actually read**: Some DWG variants may work with primary path, should not trigger fallback
2. **Corrupted DWG file**: Should fail with "corrupted file" error, not "install ODA Converter"
3. **DWG file with no blocks**: Should return empty dict, just like DXF files
4. **Very large DWG file**: Should process successfully with progress updates
5. **DWG file with spaces in filename**: Should handle correctly (file paths are already quoted properly)

### Playwright MCP Tests
Not applicable for this feature. The feature is backend extraction logic, and the existing GUI tests will cover the integration. Manual testing of the GUI with DWG files is sufficient for E2E validation.

## Acceptance Criteria
1. ✅ Application successfully extracts blocks from real DWG files when ODA File Converter is installed
2. ✅ Application provides clear, actionable error message when DWG file requires ODA Converter but it's not installed
3. ✅ Existing DXF functionality remains completely unchanged (zero regressions)
4. ✅ All existing unit tests continue to pass
5. ✅ Previously skipped `test_extract_real_dwg_file()` test is enabled and passes
6. ✅ New DWG-specific tests are added and pass (or skip gracefully on systems without ODA Converter)
7. ✅ Mypy type checking passes with zero errors
8. ✅ Logging provides clear visibility into primary vs fallback extraction paths
9. ✅ README.md clearly documents ODA File Converter requirement and installation
10. ✅ Error messages distinguish between "corrupted file" and "needs ODA Converter"

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Verify type checking passes with new code
- `uv run pytest app/tests/ -v` - Run all tests including new DWG tests
- `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_extract_real_dwg_file -v` - Run the previously skipped DWG test
- `uv run pytest app/tests/core/test_extractor_dwg.py -v` - Run new DWG-specific tests
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify code coverage includes new paths
- `bash scripts/start.sh` - Manually launch GUI and test with DWG file from app/tests/assets/

## Notes

### Design Decisions
1. **Two-tier fallback strategy** was chosen over "always use odafc" to:
   - Avoid ODA File Converter dependency for DXF-only users
   - Maximize compatibility and performance for DXF files
   - Provide graceful degradation

2. **No new dependencies required**: The ezdxf library already includes the odafc addon as part of its standard distribution, so no changes to pyproject.toml are needed. However, users must install the external ODA File Converter application separately.

3. **Error message clarity**: Distinguishing between "corrupted file" and "needs ODA Converter" is critical for user experience. The implementation must inspect exception types carefully to route users to the correct solution.

4. **Test skip conditions**: Tests requiring ODA File Converter should use `pytest.skip` when the converter is not installed, not `pytest.mark.skip`. This allows tests to run when the converter IS installed, providing validation in CI/CD environments that include it.

### ODA File Converter Installation
- **Windows**: Download installer from OpenDesign Alliance, run setup.exe
- **Linux**: Download, extract, and add to PATH: `export PATH=$PATH:/path/to/ODAFileConverter`
- **macOS**: Download DMG, install app, add to PATH
- **Download URL**: https://www.opendesign.com/guestfiles/oda_file_converter

### Future Considerations
1. Could add UI indicator showing whether ODA File Converter is detected at startup
2. Could cache ODA File Converter availability check to avoid repeated failed imports
3. Could provide "Download ODA Converter" button in error dialog that opens browser
4. Consider adding ezdxf's `recover` module as a third-tier fallback for severely corrupted files

### Security Considerations
The ODA File Converter is a trusted application from the Open Design Alliance, the same organization that maintains the DWG file format specification. No additional security concerns beyond normal file I/O.
