# Feature: Nested Block Detection - Units 1-2: Types, Constants & Test Asset

## Feature Description
This feature adds foundational type definitions and constants for tracking block definitions with nesting status in DXF files. It introduces a new `BlockDefinitionRecord` TypedDict to represent complete block definition records with insertion and nesting metadata, along with Excel column constants for a new "Block Definitions" sheet. Additionally, it creates a test DXF file with various nested block scenarios to support testing of future nested block detection functionality.

## User Story
As a CAD data analyst
I want to see which blocks are nested inside other blocks
So that I can understand the hierarchical structure of block definitions in my DXF files

## Problem Statement
Currently, the DXF Block Extractor tracks block insertions in modelspace but does not track:
1. Blocks that are only used inside other block definitions (nested blocks)
2. Blocks that are defined but never inserted anywhere (unused blocks)
3. The parent-child relationships between block definitions

This information is valuable for understanding CAD file structure and identifying potentially orphaned or nested-only block definitions.

## Solution Statement
Implement foundational types and constants (Units 1-2) to support nested block detection:
1. Add `BlockDefinitionRecord` TypedDict to track block definition metadata including nesting status
2. Add Excel constants for the new "Block Definitions" sheet and its columns
3. Create a test DXF file with comprehensive nested block scenarios for validation

## Relevant Files
Use these files to implement the feature:

- **app/core/types.py** - Contains TypedDict definitions; will add `BlockDefinitionRecord` TypedDict after `PolygonMetrics`
- **app/core/constants.py** - Contains Excel configuration constants; will add sheet name and column constants
- **app_docs/005-field-naming-convention.md** - Reference for field naming patterns (already read)

### New Files
- **app/tests/assets/create_nested_block_test.py** - Script to generate test DXF file with nested block scenarios
- **app/tests/assets/nested_block_test.dxf** - Generated test DXF file (output of the script)

## Implementation Plan
### Phase 1: Foundation
Add the `BlockDefinitionRecord` TypedDict to `app/core/types.py` with all required fields for tracking block definitions and their nesting status.

### Phase 2: Core Implementation
Add Excel constants to `app/core/constants.py`:
- Sheet name constant for "Block Definitions" sheet
- Column constants for block_raw_name, block_resolved_name, block_insertion_status, block_is_nested, and block_nested_parent_names

### Phase 3: Integration
Create test asset generator script and generate the test DXF file with comprehensive nested block scenarios.

## Step by Step Tasks

### Step 1: Add BlockDefinitionRecord TypedDict
- Open `app/core/types.py`
- Add `BlockDefinitionRecord` TypedDict after the `PolygonMetrics` class (around line 247)
- Include all required fields with proper type annotations:
  - `block_raw_name: str` - Original name from doc.blocks
  - `block_resolved_name: str` - Resolved name (same as raw for non-anonymous)
  - `block_insertion_status: str` - One of "Inserted", "Nested Only", "Unused", "System", "Unresolved (*U)", "Unresolved (A$C)"
  - `block_is_nested: bool` - True if inserted inside another block definition
  - `block_nested_parent_names: list[str]` - List of parent block names
  - `block_entity_count: int` - Number of entities in block definition
- Add comprehensive docstring following existing patterns

### Step 2: Update types.py Module Docstring
- Update the module docstring Usage section to include `BlockDefinitionRecord` in the imports example

### Step 3: Add Excel Sheet Constant
- Open `app/core/constants.py`
- Add `EXCEL_SHEET_BLOCK_DEFINITIONS: str = "Block Definitions"` after existing sheet constants (around line 24)

### Step 4: Add Excel Column Constants
- Add column constants after existing column constants (around line 117):
  - `EXCEL_COLUMN_BLOCK_RAW_NAME: str = "block_raw_name"`
  - `EXCEL_COLUMN_BLOCK_RESOLVED_NAME: str = "block_resolved_name"`
  - `EXCEL_COLUMN_BLOCK_INSERTION_STATUS: str = "block_insertion_status"`
  - `EXCEL_COLUMN_BLOCK_IS_NESTED: str = "block_is_nested"`
  - `EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES: str = "block_nested_parent_names"`
- Note: `EXCEL_COLUMN_BLOCK_ENTITY_COUNT` already exists (line 29)
- Add section comment referencing app_docs/005-field-naming-convention.md

### Step 5: Create Test Asset Generator Script
- Create `app/tests/assets/create_nested_block_test.py`
- Create DXF with the following block scenarios:
  - **OUTER_BLOCK**: Contains INSERT references to INNER_BLOCK and MULTI_PARENT_BLOCK
  - **INNER_BLOCK**: Nested only (no modelspace insertion)
  - **STANDALONE_BLOCK**: Inserted in modelspace, not nested in any other block
  - **UNUSED_BLOCK**: Defined but never inserted anywhere
  - **MULTI_PARENT_BLOCK**: Inserted in both OUTER_BLOCK and SECOND_OUTER, also in modelspace
  - **SECOND_OUTER**: Contains INSERT of MULTI_PARENT_BLOCK
- Follow the pattern from `create_a_dollar_c_block_test.py`
- Include print statements documenting expected results

### Step 6: Generate Test DXF File
- Run the script to create `app/tests/assets/nested_block_test.dxf`
- Verify the file was created successfully

### Step 7: Run Validation Commands
- Run type checking with mypy
- Run all tests to ensure no regressions
- Verify the test DXF file exists and is readable

## Testing Strategy
### Unit Tests
- No new unit tests required for this phase (types and constants only)
- Existing tests should continue to pass

### Integration Tests
- The generated test DXF file will be used by future nested block detection tests (Units 3+)

### Edge Cases
The test DXF file covers these edge cases:
- Nested-only blocks (never inserted in modelspace)
- Multi-parent blocks (nested in multiple parent blocks)
- Unused blocks (defined but never inserted)
- Standalone blocks (inserted in modelspace, not nested)
- Blocks inserted both in modelspace and nested in other blocks

### Playwright MCP Tests
- Not applicable for this phase (types and constants only)

## Acceptance Criteria
1. `BlockDefinitionRecord` TypedDict is defined in `app/core/types.py` with all 6 required fields
2. Module docstring in `types.py` includes `BlockDefinitionRecord` in the Usage example
3. `EXCEL_SHEET_BLOCK_DEFINITIONS` constant is defined in `constants.py`
4. All 5 new column constants are defined in `constants.py` (block_raw_name, block_resolved_name, block_insertion_status, block_is_nested, block_nested_parent_names)
5. `create_nested_block_test.py` script exists and runs without errors
6. `nested_block_test.dxf` file is generated with all 6 block scenarios
7. `uv run mypy app/` passes with no errors
8. `uv run pytest app/tests/` passes with no failures

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to verify new types are valid
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to verify no regressions
- `uv run pytest app/tests/ -v` - Run all tests to verify no regressions
- `uv run python app/tests/assets/create_nested_block_test.py` - Generate the test DXF file
- `test -f app/tests/assets/nested_block_test.dxf && echo "Test DXF exists"` - Verify test file was created
- `uv run python -c "import ezdxf; doc = ezdxf.readfile('app/tests/assets/nested_block_test.dxf'); print(f'Blocks: {len(list(doc.blocks))}')"` - Verify test DXF is readable

## Notes
- `EXCEL_COLUMN_BLOCK_ENTITY_COUNT` already exists in constants.py (line 29), so it does not need to be added
- The `block_insertion_status` field uses string literals rather than an Enum for simplicity and Excel compatibility
- Valid status values: "Inserted", "Nested Only", "Unused", "System", "Unresolved (*U)", "Unresolved (A$C)"
- System blocks include AutoCAD internal blocks like `*Model_Space`, `*Paper_Space`, dimension blocks, etc.
- Future units (3+) will implement the actual nested block detection logic and Excel writer updates
