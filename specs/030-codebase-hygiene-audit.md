# Chore: Codebase Hygiene Audit and Cleanup

## Chore Description
Comprehensive audit and cleanup of testing patterns, coverage, structure, workflow, logging, and documentation in the DWG Block Extractor codebase. This chore identifies and resolves discrepancies such as:
- Misplaced test fixture files in root directory
- Untracked test generator scripts
- Modified spec files marked for deletion
- Generated Excel output files in test assets
- Missing .gitignore patterns for test artifacts
- Overall codebase hygiene and consistency

The goal is to ensure all files are properly organized, tracked, and documented according to project conventions while maintaining zero test regressions.

## Relevant Files
Use these files to resolve the chore:

### Files with Issues (Primary Focus)

- `scale_variance_test.dxf` - **MISPLACED**: Test fixture DXF file in root directory, should be in `app/tests/assets/`
- `app/tests/assets/create_empty_layers_test.py` - **UNTRACKED**: New test generator script, should be added to git
- `app/tests/assets/empty_layers_test.dxf` - **UNTRACKED**: Generated test fixture, should be added to git
- `specs/028-annotations-analysis.md` - **MARKED FOR DELETION**: Modified spec file showing deletion in git status
- `specs/029-color-analysis.md` - **MARKED FOR DELETION**: Modified spec file showing deletion in git status
- `specs/specs.tar` - **MODIFIED**: Archive file showing uncommitted changes
- `app/tests/assets/annotation_test.dxf` - **MODIFIED**: Test fixture showing uncommitted changes
- `app/tests/assets/xdata_test.dxf` - **MODIFIED**: Test fixture showing uncommitted changes
- `app/tests/core/test_extractor.py` - **MODIFIED**: Test file showing uncommitted changes

### Files with Generated Artifacts (Should be Gitignored)

- `app/tests/assets/sample_drawing_blocks_20251117_201105.xlsx` - Generated Excel output in test assets
- `app/tests/assets/samples/AS-1922_XXXX-SSL-XXX-XX-DR-U-0200_blocks_20251120_230740.xlsx` - Generated Excel output in samples directory

### Configuration Files to Update

- `.gitignore` - Needs patterns for test-generated Excel files and potential other artifacts

### Documentation Files for Review

- `README.md` - Verify testing workflow documentation is accurate
- `ai_docs/001-naming-convention-guide.md` - Ensure alignment with actual codebase patterns
- `app_docs/005-field-naming-convention.md` - Verify Excel field naming conventions are followed

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Move Misplaced Test Fixture to Correct Location

- Move `scale_variance_test.dxf` from project root to `app/tests/assets/`
- Verify the file exists in the correct location after move
- Verify the file is staged for git commit with the move operation

### 2. Update .gitignore for Test Artifacts

- Add pattern `app/tests/assets/*_blocks_*.xlsx` to ignore generated Excel test outputs
- Add pattern `**/*_blocks_*.xlsx` to catch Excel outputs in all test subdirectories
- Verify existing Excel files in test assets are now properly ignored by git status

### 3. Stage All Legitimate Test Changes

- Stage `app/tests/assets/create_empty_layers_test.py` - new test generator script
- Stage `app/tests/assets/empty_layers_test.dxf` - generated test fixture
- Stage modified test fixtures: `app/tests/assets/annotation_test.dxf`, `app/tests/assets/xdata_test.dxf`
- Stage modified test file: `app/tests/core/test_extractor.py`
- Review git diff for these files to ensure changes are intentional and documented

### 4. Resolve Spec File Deletions

- Determine if `specs/028-annotations-analysis.md` and `specs/029-color-analysis.md` should actually be deleted
- If deletion is intentional: stage the deletions and document reason in commit message
- If deletion is NOT intentional: restore the files from git history or remove the deletion marker
- Update `specs/specs.tar` if needed to reflect current spec structure

### 5. Verify Test Generator Scripts Consistency

- Review all 9 test generator scripts in `app/tests/assets/create_*.py`
- Ensure each has proper shebang, docstring, and usage instructions
- Verify `create_empty_layers_test.py` follows same pattern as other generators
- Check that all generator scripts are executable: `chmod +x app/tests/assets/create_*.py`

### 6. Audit Test Coverage Gaps

Current coverage: 96% overall (32/788 lines missing)
- Review uncovered lines in `app/core/extractor.py` (22 missing lines at 90% coverage)
- Review uncovered lines in `app/core/excel_writer.py` (5 missing lines at 97% coverage)
- Review uncovered lines in `app/core/geometry.py` (4 missing lines at 97% coverage)
- Review uncovered line in `app/core/excel_formatting.py` (1 missing line at 99% coverage)
- Document which uncovered lines are error handling paths vs. missing test scenarios
- Create follow-up tasks if new tests are needed (do NOT implement tests in this chore)

### 7. Verify Documentation Accuracy

- Verify `README.md` testing commands work as documented:
  - `uv run pytest app/tests/` - Run all tests
  - `uv run pytest --cov=app app/tests/` - Run with coverage
- Verify working directory convention is correctly documented and followed
- Check that reference files section lists all relevant docs
- Verify `app_docs/005-field-naming-convention.md` is followed in Excel generation

### 8. Review Git Status for Remaining Issues

- Run `git status --porcelain` to check for any remaining untracked or modified files
- Verify `.history/` directory is properly ignored (should not show in git status)
- Verify `.venv/` directory is properly ignored
- Check for any unexpected files that should be cleaned up or gitignored

### 9. Clean Up Generated Artifacts

- Remove generated Excel files from test assets:
  - `app/tests/assets/sample_drawing_blocks_20251117_201105.xlsx`
  - `app/tests/assets/samples/AS-1922_XXXX-SSL-XXX-XX-DR-U-0200_blocks_20251120_230740.xlsx` (if samples dir exists after gitignore rules)
- Verify these files don't reappear in git status after cleanup

### 10. Final Validation

- Run all validation commands (see Validation Commands section below)
- Verify git status shows only intended staged changes
- Verify no test regressions or failures
- Verify mypy type checking passes
- Create summary of changes and commit with descriptive message

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/` - Run all 248 tests to ensure zero regressions
- `uv run pytest --cov=app/core app/tests/` - Verify coverage remains at 96% or higher
- `uv run mypy app/` - Verify type checking passes with zero errors
- `git status --porcelain` - Verify only intended files are staged/modified
- `test -f app/tests/assets/scale_variance_test.dxf` - Verify fixture moved to correct location
- `test ! -f scale_variance_test.dxf` - Verify fixture removed from root
- `git ls-files --others --ignored --exclude-standard | grep -E '\.(xlsx|log)$'` - Verify generated artifacts are gitignored
- `find app/tests/assets -name "*.xlsx" -type f` - List any Excel files in test assets (should be none after cleanup)
- `ls -la app/tests/assets/create_*.py | wc -l` - Verify all 9 test generator scripts are present

## Notes

### Current Test Suite Status
- **Total tests**: 248 (247 passed, 1 skipped)
- **Coverage**: 96% overall (788 lines, 32 missing)
- **Type checking**: Clean (mypy passes with zero errors)
- **Test generators**: 9 Python scripts in `app/tests/assets/`

### Coverage Breakdown by Module
- `app/core/constants.py` - 100% (55/55 lines)
- `app/core/logger.py` - 100% (12/12 lines)
- `app/core/__init__.py` - 100% (0/0 lines)
- `app/core/excel_formatting.py` - 99% (188/189 lines, 1 missing)
- `app/core/geometry.py` - 97% (119/123 lines, 4 missing)
- `app/core/excel_writer.py` - 97% (178/183 lines, 5 missing)
- `app/core/extractor.py` - 90% (204/226 lines, 22 missing)

### Identified Discrepancies
1. **File Organization**: `scale_variance_test.dxf` in wrong directory (root instead of `app/tests/assets/`)
2. **Untracked Files**: New test generator and fixture not in git
3. **Modified Specs**: Two spec files marked for deletion, unclear if intentional
4. **Generated Artifacts**: Excel output files in test directories (should be gitignored)
5. **Git Status**: Multiple modified test files and fixtures need review

### Testing Patterns Observed
- Comprehensive test coverage across all modules
- Separate test classes for different functional areas
- Parametrized tests for rotation/scale variations
- Fixture-based testing with generated DXF files
- Test generators with clear documentation
- Good separation of unit tests by module

### Logging Configuration
- Centralized in `app/core/logger.py`
- Stdout-only logging (no file handlers)
- Designed for LLM agent monitoring during development
- Clear formatting with timestamps and log levels

### Documentation Structure
- `ai_docs/` - AI/LLM-focused documentation and guides
- `ai_output/` - Analysis reports and generated documentation
- `app_docs/` - Application-specific documentation (field naming conventions)
- `specs/` - Feature specifications and implementation plans (currently none tracked, but 2 marked for deletion)

### Workflow Observations
- Uses `uv` for all Python package management
- Root-relative paths enforced by `.claude/settings.json`
- WSL2 environment with GUI test skip patterns
- Clean separation between test assets, fixtures, and generators
