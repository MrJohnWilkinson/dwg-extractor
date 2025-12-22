# Feature: Add Attribute Analysis Sheet Constants

## Feature Description
This unit adds the foundational constants required for the new "Attribute Analysis" Excel sheet. The Attribute Analysis sheet will provide detailed analysis of which blocks contain which attributes with their varying values. This is part of a larger feature to enhance block attribute reporting by:
1. Simplifying the All Blocks sheet to show only unique attribute tag names (Unit 1 - completed)
2. Adding a dedicated Attribute Analysis sheet with detailed attribute-value information (Units 2-4)

This unit focuses specifically on adding the sheet name constant and five column constants to `constants.py` that will be used by subsequent units to implement the actual sheet creation and formatting.

## User Story
As a CAD data analyst
I want well-defined constants for the Attribute Analysis sheet
So that the codebase maintains consistent naming conventions and the sheet can be reliably referenced across multiple modules

## Problem Statement
The codebase currently lacks the necessary constants to support the new Attribute Analysis sheet. Without these constants:
- Sheet and column names would be scattered as string literals
- Type checking with mypy would be less effective
- Refactoring would be error-prone
- The naming convention established in `app_docs/005-field-naming-convention.md` wouldn't be consistently applied

## Solution Statement
Add six new constants to `app/core/constants.py`:
1. One sheet name constant: `EXCEL_SHEET_ATTRIBUTE_ANALYSIS`
2. Five column constants following the `attribute_*` domain pattern as defined in the naming convention guide

These constants will follow the existing patterns in the codebase for sheet and column constant definitions.

## Relevant Files
Use these files to implement the feature:

- **app/core/constants.py** - Primary file to modify. Add new sheet constant and five column constants for the Attribute Analysis sheet. Follow existing patterns for sheet constants (lines 24-32) and column constants with domain prefixes.
- **app_docs/005-field-naming-convention.md** - Reference for naming convention. The new columns use the `attribute_` domain prefix as they relate to block attribute analysis.
- **app/tests/core/test_constants.py** - Add new test class to verify the new constants follow naming conventions and have correct values.

### New Files
None required for this unit.

## Implementation Plan

### Phase 1: Foundation
Review existing constant patterns in `constants.py` to ensure new constants follow established conventions:
- Sheet constants are grouped together (lines 24-32)
- Column constants follow the pattern `EXCEL_COLUMN_{DOMAIN}_{ATTRIBUTE}[_{QUALIFIER}]`
- Each constant has a type annotation `: str`
- Related constants are grouped with section comments

### Phase 2: Core Implementation
Add the new constants to `constants.py`:
1. Add `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` in the sheet constants section
2. Add a new section comment for "Attribute Analysis columns"
3. Add five column constants using the `attribute_` domain prefix

### Phase 3: Integration
Add unit tests to `test_constants.py` to verify:
- Sheet constant has correct value
- Column constants follow naming conventions (start with `attribute_`)
- Column constants have expected string values

## Step by Step Tasks

### Step 1: Add Sheet Constant
- Open `app/core/constants.py`
- Locate the sheet constants section (lines 24-32)
- Add new constant after `EXCEL_SHEET_ALL_BLOCKS`:
  ```python
  EXCEL_SHEET_ATTRIBUTE_ANALYSIS: str = "Attribute Analysis"
  ```

### Step 2: Add Column Constants Section
- Add a new section comment after the Block Attributes columns section (around line 149):
  ```python
  # Excel configuration - Attribute Analysis columns
  # See app_docs/005-field-naming-convention.md for naming conventions
  # Domain: attribute (attribute-specific analysis across blocks)
  ```

### Step 3: Add Column Constants
- Add five column constants following the naming convention:
  ```python
  EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME: str = "attribute_block_name"
  EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES: str = "attribute_block_layer_names"
  EXCEL_COLUMN_ATTRIBUTE_TAG: str = "attribute_tag"
  EXCEL_COLUMN_ATTRIBUTE_VALUES: str = "attribute_values"
  EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT: str = "attribute_value_count"
  ```

### Step 4: Add Unit Tests
- Open `app/tests/core/test_constants.py`
- Add imports for new constants
- Add new test class `TestAttributeAnalysisSheetConstants`:
  ```python
  class TestAttributeAnalysisSheetConstants:
      """Tests for Attribute Analysis sheet constants."""

      def test_excel_sheet_attribute_analysis_value(self) -> None:
          """EXCEL_SHEET_ATTRIBUTE_ANALYSIS should have value 'Attribute Analysis'."""

      def test_attribute_column_constants_follow_naming_convention(self) -> None:
          """All attribute analysis columns should start with 'attribute_' prefix."""

      def test_attribute_block_name_value(self) -> None:
          """EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME should have value 'attribute_block_name'."""

      def test_attribute_block_layer_names_value(self) -> None:
          """EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES should have value 'attribute_block_layer_names'."""

      def test_attribute_block_layer_names_uses_plural_suffix(self) -> None:
          """EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES should end with '_names' (plural for collections)."""

      def test_attribute_tag_value(self) -> None:
          """EXCEL_COLUMN_ATTRIBUTE_TAG should have value 'attribute_tag'."""

      def test_attribute_values_value(self) -> None:
          """EXCEL_COLUMN_ATTRIBUTE_VALUES should have value 'attribute_values'."""

      def test_attribute_values_uses_plural_suffix(self) -> None:
          """EXCEL_COLUMN_ATTRIBUTE_VALUES should end with '_values' (plural for collections)."""

      def test_attribute_value_count_value(self) -> None:
          """EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT should have value 'attribute_value_count'."""
  ```

### Step 5: Run Validation Commands
- Run type checking, tests, and linting to ensure zero regressions

## Testing Strategy

### Unit Tests
- Verify sheet constant has exact string value "Attribute Analysis"
- Verify all five column constants follow the `attribute_` domain prefix convention
- Verify each column constant has its expected string value
- Verify collection columns use plural suffixes (`_names`, `_values`)

### Integration Tests
Not applicable for this unit - constants are standalone values with no integration dependencies.

### Edge Cases
- Ensure no typos in constant values (exact string matching in tests)
- Ensure naming convention consistency with other sheets/columns

### Playwright MCP Tests
Not applicable for this unit - no GUI or end-to-end functionality added.

## Acceptance Criteria
- [ ] `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` constant added with value "Attribute Analysis"
- [ ] `EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME` constant added with value "attribute_block_name"
- [ ] `EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES` constant added with value "attribute_block_layer_names"
- [ ] `EXCEL_COLUMN_ATTRIBUTE_TAG` constant added with value "attribute_tag"
- [ ] `EXCEL_COLUMN_ATTRIBUTE_VALUES` constant added with value "attribute_values"
- [ ] `EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT` constant added with value "attribute_value_count"
- [ ] All column constants follow the naming convention in `app_docs/005-field-naming-convention.md`
- [ ] Unit tests added and passing for all new constants
- [ ] `uv run mypy app/` passes with no errors
- [ ] `uv run pytest app/tests/` passes with all tests (1134+ tests)
- [ ] `uv run ruff check app/` passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/constants.py` - Type check the modified constants file
- `uv run mypy app/tests/core/test_constants.py` - Type check the modified test file
- `uv run mypy app/` - Run full type checking to ensure no regressions
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to verify new tests pass
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run ruff check app/` - Lint check for code quality
- `uv run ruff format app/ --check` - Verify code formatting

## Notes
- This unit is part of the Attribute Analysis Sheet feature broken down into multiple units:
  - Unit 1 (completed): Renamed `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS` and updated excel_writer.py
  - **Unit 2 (this spec)**: Add Attribute Analysis sheet constants
  - Unit 3 (future): Implement `_create_attribute_analysis_sheet` function
  - Unit 4 (future): Add formatting and tests
- The constants follow the `attribute_` domain prefix which is a new domain in the codebase, distinct from `block_`, `layer_`, and `entity_` domains
- The column names will automatically be converted to Title Case in Excel headers by the existing `format_header()` function
