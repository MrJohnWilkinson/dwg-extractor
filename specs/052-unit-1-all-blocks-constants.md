# Feature: Add Constants for All Blocks Consolidated Sheet

## Feature Description
Add new constants to `app/core/constants.py` to support the "All Blocks" consolidated sheet feature. This sheet will combine block data from multiple existing sheets into a single comprehensive view with 29 columns. Most columns already have constants defined; this unit adds only the new constants that don't already exist.

## User Story
As a CAD data analyst
I want the All Blocks consolidated sheet to have properly defined column constants
So that column names are consistent, maintainable, and follow the established naming conventions

## Problem Statement
The upcoming "All Blocks" consolidated sheet feature requires three new constants that don't currently exist in the codebase:
1. A sheet name constant for "All Blocks"
2. A column constant for `block_layer_count` (count of layers a block appears on)
3. A column constant for `block_layer_names` (comma-separated list of layer names)

Without these constants, the consolidated sheet implementation would use hardcoded strings, violating the DRY principle and established project conventions.

## Solution Statement
Add three new constants to `app/core/constants.py`:
- `EXCEL_SHEET_ALL_BLOCKS` - Sheet name for the consolidated view
- `EXCEL_COLUMN_BLOCK_LAYER_COUNT` - Column for layer count per block
- `EXCEL_COLUMN_BLOCK_LAYER_NAMES` - Column for layer names list

These follow the existing naming patterns and conventions documented in `app_docs/005-field-naming-convention.md`.

## Relevant Files
Use these files to implement the feature:

- `app/core/constants.py` - Main file to modify. Contains all Excel sheet names and column constants. New constants will be added in appropriate sections.
- `app/tests/core/test_constants.py` - Test file to update. Contains tests validating constant naming conventions and values.
- `app_docs/005-field-naming-convention.md` - Reference only. Documents naming patterns for field names.

### New Files
No new files required.

## Implementation Plan
### Phase 1: Foundation
Review existing constants in `app/core/constants.py` to identify:
- Existing sheet name constants pattern (lines 17-24)
- Existing block column constants pattern (lines 26-126)
- Verify the three target constants don't already exist

### Phase 2: Core Implementation
Add three new constants to `app/core/constants.py`:
1. Add `EXCEL_SHEET_ALL_BLOCKS` in the sheet names section (after line 24)
2. Add `EXCEL_COLUMN_BLOCK_LAYER_COUNT` in the block columns section (after Block Definitions)
3. Add `EXCEL_COLUMN_BLOCK_LAYER_NAMES` in the block columns section (after layer count)

### Phase 3: Integration
Add unit tests to `app/tests/core/test_constants.py` to validate:
- New constants follow naming conventions
- New column constants start with "block_" prefix
- Sheet name constant has correct value

## Step by Step Tasks

### Step 1: Add Sheet Name Constant
- Open `app/core/constants.py`
- Locate the sheet name constants section (lines 17-24)
- Add `EXCEL_SHEET_ALL_BLOCKS: str = "All Blocks"` after `EXCEL_SHEET_BLOCK_DEFINITIONS`

### Step 2: Add Block Layer Count Column Constant
- Locate the Block Definitions section (around line 119-126)
- Add a new comment section for "All Blocks sheet additional columns"
- Add `EXCEL_COLUMN_BLOCK_LAYER_COUNT: str = "block_layer_count"`
- Include docstring comment referencing naming convention guide

### Step 3: Add Block Layer Names Column Constant
- Add `EXCEL_COLUMN_BLOCK_LAYER_NAMES: str = "block_layer_names"` after layer count
- Note: Follows naming convention - plural "names" indicates collection/list

### Step 4: Add Unit Tests for New Constants
- Open `app/tests/core/test_constants.py`
- Add imports for the three new constants
- Create new test class `TestAllBlocksSheetConstants`
- Add test for sheet name value
- Add test for column constants following naming convention (block_ prefix)
- Add test for layer_names being plural (collection indicator)

### Step 5: Run Validation Commands
- Run all tests to ensure no regressions
- Run type checking to validate constant types
- Run linting to ensure code quality

## Testing Strategy
### Unit Tests
- Test that `EXCEL_SHEET_ALL_BLOCKS` equals "All Blocks"
- Test that `EXCEL_COLUMN_BLOCK_LAYER_COUNT` starts with "block_" prefix
- Test that `EXCEL_COLUMN_BLOCK_LAYER_NAMES` starts with "block_" prefix
- Test that `EXCEL_COLUMN_BLOCK_LAYER_NAMES` ends with "_names" (plural for collections)

### Integration Tests
Not applicable for this unit - constants are standalone values.

### Edge Cases
- Verify no duplicate constant names exist
- Verify constant values don't conflict with existing column names

### Playwright MCP Tests
Not applicable for this unit - no UI changes.

## Acceptance Criteria
- [ ] `EXCEL_SHEET_ALL_BLOCKS` constant exists with value "All Blocks"
- [ ] `EXCEL_COLUMN_BLOCK_LAYER_COUNT` constant exists with value "block_layer_count"
- [ ] `EXCEL_COLUMN_BLOCK_LAYER_NAMES` constant exists with value "block_layer_names"
- [ ] All new constants follow the established naming convention pattern
- [ ] Unit tests pass for new constants
- [ ] All existing tests continue to pass (no regressions)
- [ ] Type checking passes (`uv run mypy app/`)
- [ ] Linting passes (`uv run ruff check app/`)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to validate new constants
- `uv run pytest app/tests/ -v` - Run all tests to ensure no regressions
- `uv run mypy app/` - Run type checking to validate constant types
- `uv run ruff check app/` - Run linting to ensure code quality

## Notes
- This is Unit 1 of a larger implementation plan for the "All Blocks" consolidated sheet feature
- Most of the 29 columns for the All Blocks sheet already have constants defined from other sheets
- Only three constants need to be added; all others can be reused from existing definitions
- The `block_layer_names` field uses plural suffix per naming convention to indicate it contains a collection (comma-separated list of layer names)
- Future units will implement the actual sheet generation logic using these constants
