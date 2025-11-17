# Chore: Refactor Field Naming Convention Compliance

## Chore Description
Update and refactor the entire codebase and Excel template to ensure all field names follow the standardized naming conventions defined in `app_docs/005-field-naming-convention.md`. The current implementation uses human-readable Excel headers (e.g., "Block Name", "Insertion Count") which violates the convention requiring snake_case identifiers with domain prefixes (e.g., `block_name`, `block_insertion_count`). This refactoring will ensure consistency between Python code and Excel output, improve code maintainability, and establish a clear semantic pattern for all field identifiers.

## Relevant Files
Use these files to resolve the chore:

**Core Module Files:**
- `app/core/constants.py` - Contains Excel column name constants that need to be converted from title case (e.g., 'Block Name') to snake_case (e.g., 'block_name') following the domain_attribute pattern
- `app/core/extractor.py` - Contains ExtractionResult TypedDict with dictionary keys that already follow conventions but need validation; internal variable names need review
- `app/core/excel_writer.py` - Uses column constants from constants.py to create Excel sheets; needs to be validated that it properly uses the updated constants

**Test Files:**
- `app/tests/core/test_extractor.py` - Unit tests that validate extraction logic and dictionary key names; needs updates to match new constant values
- `app/tests/core/test_excel_writer.py` - Unit tests that validate Excel generation with column headers; needs comprehensive updates to test new snake_case headers

**Application Files:**
- `app/main.py` - GUI application that doesn't directly reference Excel columns but uses extraction results; needs review for any field references

### New Files
No new files need to be created for this chore.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Excel Column Constants in constants.py
- Review current Excel column constants (all use Title Case with spaces)
- Update all `EXCEL_COLUMN_*` constants to follow the `{domain}_{attribute}[_{qualifier}]` pattern:
  - `EXCEL_COLUMN_BLOCK_NAME: str = 'Block Name'` → `EXCEL_COLUMN_BLOCK_NAME: str = 'block_name'`
  - `EXCEL_COLUMN_COUNT: str = 'Insertion Count'` → `EXCEL_COLUMN_BLOCK_INSERTION_COUNT: str = 'block_insertion_count'`
  - `EXCEL_COLUMN_ENTITIES_IN_DEFINITION: str = 'Entities in Definition'` → `EXCEL_COLUMN_BLOCK_ENTITY_COUNT: str = 'block_entity_count'`
  - `EXCEL_COLUMN_LAYER_NAME: str = 'Layer Name'` → `EXCEL_COLUMN_LAYER_NAME: str = 'layer_name'`
  - `EXCEL_COLUMN_INSERTIONS_ON_LAYER: str = 'Insertions on Layer'` → `EXCEL_COLUMN_LAYER_INSERTION_COUNT: str = 'layer_insertion_count'`
  - `EXCEL_COLUMN_ENTITIES_ON_LAYER: str = 'Entities on Layer'` → `EXCEL_COLUMN_LAYER_ENTITY_COUNT: str = 'layer_entity_count'`
  - `EXCEL_COLUMN_ENTITY_TYPE: str = 'Entity Type'` → `EXCEL_COLUMN_ENTITY_TYPE_NAME: str = 'entity_type_name'`
  - `EXCEL_COLUMN_TOTAL_COUNT: str = 'Total Count'` → `EXCEL_COLUMN_ENTITY_TYPE_COUNT: str = 'entity_type_count'`
- Ensure all constant variable names match their string values semantically (e.g., `EXCEL_COLUMN_BLOCK_INSERTION_COUNT` constant holds the value `'block_insertion_count'`)
- Add comments referencing the naming convention guide: `# See app_docs/005-field-naming-convention.md`

### Step 2: Update excel_writer.py Imports and References
- Update all imports from constants.py to use the new constant names:
  - `EXCEL_COLUMN_COUNT` → `EXCEL_COLUMN_BLOCK_INSERTION_COUNT`
  - `EXCEL_COLUMN_ENTITIES_IN_DEFINITION` → `EXCEL_COLUMN_BLOCK_ENTITY_COUNT`
  - `EXCEL_COLUMN_INSERTIONS_ON_LAYER` → `EXCEL_COLUMN_LAYER_INSERTION_COUNT`
  - `EXCEL_COLUMN_ENTITIES_ON_LAYER` → `EXCEL_COLUMN_LAYER_ENTITY_COUNT`
  - `EXCEL_COLUMN_ENTITY_TYPE` → `EXCEL_COLUMN_ENTITY_TYPE_NAME`
  - `EXCEL_COLUMN_TOTAL_COUNT` → `EXCEL_COLUMN_ENTITY_TYPE_COUNT`
- Update all references throughout excel_writer.py functions:
  - `_create_block_counts_sheet()` function
  - `_create_layer_analysis_sheet()` function
  - `_create_entity_summary_sheet()` function
  - DataFrame sort_values operations
- Verify no hardcoded string literals remain for column names

### Step 3: Review and Validate extractor.py
- Review ExtractionResult TypedDict keys to ensure they follow conventions:
  - `block_counts` - ✓ follows convention (collection of block counts)
  - `block_entities` - ✓ follows convention (collection of block entity counts)
  - `layer_insertions` - should be renamed to `layer_insertion_counts` for consistency
  - `layer_entities` - should be renamed to `layer_entity_counts` for consistency
  - `entity_types` - should be renamed to `entity_type_counts` for clarity
- Update ExtractionResult TypedDict with corrected keys if needed
- Update all references to these keys throughout extractor.py
- Update docstrings to reflect new key names
- Ensure internal variable names follow conventions (e.g., `block_name`, `entity_count`, `layer_name`)

### Step 4: Update excel_writer.py to Use Updated TypedDict Keys
- Update `_create_block_counts_sheet()` to use potentially renamed TypedDict keys
- Update `_create_layer_analysis_sheet()` to use potentially renamed TypedDict keys
- Update `_create_entity_summary_sheet()` to use potentially renamed TypedDict keys
- Update docstrings and comments to reflect changes

### Step 5: Update main.py References
- Review main.py for any direct references to ExtractionResult keys
- Update `_extraction_worker()` method where it checks `extraction_result['block_counts']`
- Verify no other field references exist in the GUI code

### Step 6: Update test_extractor.py Unit Tests
- Update all assertions that check ExtractionResult dictionary keys:
  - Change `result['layer_insertions']` → `result['layer_insertion_counts']` (if renamed)
  - Change `result['layer_entities']` → `result['layer_entity_counts']` (if renamed)
  - Change `result['entity_types']` → `result['entity_type_counts']` (if renamed)
- Update all docstrings and comments in test file
- Ensure tests validate the correct dictionary structure

### Step 7: Update test_excel_writer.py Unit Tests
- Update all constant imports to use new names:
  - `EXCEL_COLUMN_COUNT` → `EXCEL_COLUMN_BLOCK_INSERTION_COUNT`
  - `EXCEL_COLUMN_ENTITIES_IN_DEFINITION` → `EXCEL_COLUMN_BLOCK_ENTITY_COUNT`
  - `EXCEL_COLUMN_INSERTIONS_ON_LAYER` → `EXCEL_COLUMN_LAYER_INSERTION_COUNT`
  - `EXCEL_COLUMN_ENTITIES_ON_LAYER` → `EXCEL_COLUMN_LAYER_ENTITY_COUNT`
  - `EXCEL_COLUMN_ENTITY_TYPE` → `EXCEL_COLUMN_ENTITY_TYPE_NAME`
  - `EXCEL_COLUMN_TOTAL_COUNT` → `EXCEL_COLUMN_ENTITY_TYPE_COUNT`
- Update all test fixture data that creates ExtractionResult dictionaries with updated keys
- Update all assertions that check Excel column headers (now expecting snake_case values)
- Update docstrings and test names if needed
- Verify all tests check for correct snake_case headers in Excel output

### Step 8: Run Type Checking
- Execute mypy to catch any type-related issues introduced by refactoring
- Fix any type errors related to TypedDict key changes
- Verify all constants and references are correctly typed

### Step 9: Run Complete Test Suite
- Execute the full test suite to validate all changes
- Verify all extractor tests pass with updated TypedDict keys
- Verify all excel_writer tests pass with updated column headers
- Fix any test failures that arise from the refactoring
- Ensure test coverage remains at 100%

### Step 10: Manual Integration Verification
- Run the actual application using `bash scripts/start.sh`
- Select a test DWG file (e.g., `app/tests/assets/sample_drawing.dxf`)
- Perform extraction and verify Excel output is generated
- Open the generated Excel file and verify:
  - All three sheets exist (Block Counts, Layer Analysis, Entity Summary)
  - All column headers use snake_case (e.g., `block_name`, `block_insertion_count`)
  - Data is correctly populated under the new headers
  - Auto-filters work correctly
  - Sort order is maintained (descending by count columns)
- Stop the application

### Step 11: Validation Commands
Execute all validation commands to ensure zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/` - Type check entire application to catch any type inconsistencies
- `uv run pytest app/tests/ -v` - Run all unit tests with verbose output to validate functionality
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Run tests with coverage to ensure 100% coverage maintained
- `uv run pytest app/tests/core/test_extractor.py -v` - Specifically validate extractor tests pass
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Specifically validate excel_writer tests pass

## Notes
- The naming convention guide (`app_docs/005-field-naming-convention.md`) is the single source of truth for all field naming decisions
- Excel headers will now use snake_case instead of Title Case - this is a breaking change for Excel output format
- All changes must maintain backward compatibility with the ExtractionResult structure used by the GUI
- The convention pattern is: `{domain}_{attribute}[_{qualifier}]` where:
  - domain = block, layer, entity
  - attribute = name, count, rotation, etc.
  - qualifier = insertion, definition, unique, etc. (optional)
- Pay special attention to singular vs plural naming:
  - Use singular `_count` for counting instances (e.g., `block_insertion_count`)
  - Use plural for collections (e.g., `block_names`, `rotation_angles`)
- Constants in constants.py should use `EXCEL_COLUMN_` prefix followed by the domain and attribute in uppercase (e.g., `EXCEL_COLUMN_BLOCK_INSERTION_COUNT`)
- The refactoring affects Excel output format - users will see snake_case headers instead of human-readable headers
