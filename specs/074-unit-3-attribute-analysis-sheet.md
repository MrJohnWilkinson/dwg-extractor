# Feature: Implement Attribute Analysis Sheet

## Feature Description
This unit implements the `_create_attribute_analysis_sheet` function in `excel_writer.py` that creates a new "Attribute Analysis" Excel sheet. This sheet provides detailed block-attribute-value analysis showing each unique (block_name, tag) combination with all its observed values and layer information. This is Unit 3 of the Attribute Analysis Sheet feature, building upon:
- Unit 1: Renamed `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS` and updated the All Blocks sheet to show comma-separated unique tags
- Unit 2: Added `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` sheet constant and 5 column constants (`EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME`, `EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES`, `EXCEL_COLUMN_ATTRIBUTE_TAG`, `EXCEL_COLUMN_ATTRIBUTE_VALUES`, `EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT`)

## User Story
As a CAD data analyst
I want a dedicated sheet showing block-attribute-value relationships
So that I can see which blocks have which attributes and what values each attribute takes across all insertions

## Problem Statement
Currently, attribute information is only shown in the "All Blocks" sheet as a count and a comma-separated list of unique tags. Users cannot see:
- Which specific values each attribute takes
- How many unique values exist for each attribute
- Which layers a block with attributes appears on
- The relationship between blocks, their attributes, and the attribute values

This limits the user's ability to analyze attribute data patterns across their CAD drawings.

## Solution Statement
Implement the `_create_attribute_analysis_sheet` function that:
1. Extracts `block_attribute_data` and `block_layer_pairs` from the extraction result
2. Builds a lookup mapping block names to their associated layer names
3. Groups attributes by (block_name, tag) and collects all unique values
4. Creates one row per unique (block_name, tag) combination with:
   - Block name
   - Comma-separated layer names where the block appears
   - Attribute tag name
   - Comma-separated list of unique values
   - Count of unique values
5. Sorts rows by (block_name, tag) alphabetically
6. Formats headers using the existing `format_header()` function
7. Integrates with `write_excel()` function to add the sheet after other sheets

## Relevant Files
Use these files to implement the feature:

- **app/core/excel_writer.py** - Primary file to modify. Add imports for new constants and implement `_create_attribute_analysis_sheet` function. Add call to new function in `write_excel()`.
- **app/core/constants.py** - Reference for constants. Contains `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` and 5 `EXCEL_COLUMN_ATTRIBUTE_*` constants (already added in Unit 2).
- **app/core/excel_formatting.py** - Reference for `format_header()` function used to convert snake_case headers to Title Case.
- **app/core/types.py** - Reference for `BlockLayerKey` dataclass used to access layer information.
- **app/tests/core/excel_writer/conftest.py** - Contains shared fixtures including `sample_extraction_data` which already has `block_attribute_data` populated.
- **app/tests/core/excel_writer/test_excel_writer_core.py** - Reference for test patterns. Add tests for new sheet functionality.

### New Files
None required for this unit.

## Implementation Plan

### Phase 1: Foundation
1. Review existing sheet creation functions in `excel_writer.py` to understand the pattern:
   - Each sheet has a `_create_*_sheet` function
   - Functions take `data: ExtractionResult` and `writer: pd.ExcelWriter` parameters
   - Functions handle empty data case with headers-only DataFrame
   - Functions apply `format_header()` to column names before writing

2. Review the existing constants in `constants.py` (added in Unit 2):
   - `EXCEL_SHEET_ATTRIBUTE_ANALYSIS = "Attribute Analysis"`
   - `EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME = "attribute_block_name"`
   - `EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES = "attribute_block_layer_names"`
   - `EXCEL_COLUMN_ATTRIBUTE_TAG = "attribute_tag"`
   - `EXCEL_COLUMN_ATTRIBUTE_VALUES = "attribute_values"`
   - `EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT = "attribute_value_count"`

### Phase 2: Core Implementation
1. Add imports for the new constants to `excel_writer.py`
2. Implement `_create_attribute_analysis_sheet` function following the provided specification
3. Add call to `_create_attribute_analysis_sheet` in `write_excel()` function

### Phase 3: Integration
1. Add unit tests for the new sheet functionality
2. Verify the sheet appears in the workbook with correct headers
3. Verify data is correctly aggregated and sorted
4. Ensure empty data case is handled properly

## Step by Step Tasks

### Step 1: Add Imports for New Constants
- Open `app/core/excel_writer.py`
- Add imports for the sheet constant and column constants in the existing import block from `.constants`:
  ```python
  EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES,
  EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME,
  EXCEL_COLUMN_ATTRIBUTE_TAG,
  EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT,
  EXCEL_COLUMN_ATTRIBUTE_VALUES,
  EXCEL_SHEET_ATTRIBUTE_ANALYSIS,
  ```

### Step 2: Implement `_create_attribute_analysis_sheet` Function
- Add the function after `_create_all_blocks_sheet` (around line 1341):
```python
def _create_attribute_analysis_sheet(
    data: ExtractionResult,
    writer: pd.ExcelWriter,
) -> None:
    """Create the Attribute Analysis sheet with block-attribute-value details.

    This sheet provides a detailed view of block attributes, grouping by
    (block_name, tag) and showing all unique values observed across all
    insertions of that block.

    Args:
        data: ExtractionResult containing block_attribute_data and block_layer_pairs
        writer: pandas ExcelWriter object for output
    """
    logger.info("Creating Attribute Analysis sheet...")

    block_attribute_data = data.get("block_attribute_data", {})
    block_layer_pairs = data.get("block_layer_pairs", {})

    if not block_attribute_data:
        # Create empty sheet with headers only
        logger.info("No block attribute data found, creating empty Attribute Analysis sheet")
        df = pd.DataFrame(columns=[
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME,
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES,
            EXCEL_COLUMN_ATTRIBUTE_TAG,
            EXCEL_COLUMN_ATTRIBUTE_VALUES,
            EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT,
        ])
        df.columns = [format_header(col) for col in df.columns]
        df.to_excel(writer, sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS, index=False)
        return

    # Build a lookup for block -> layer names
    block_to_layers: dict[str, set[str]] = {}
    for key in block_layer_pairs.keys():
        if key.block_name not in block_to_layers:
            block_to_layers[key.block_name] = set()
        block_to_layers[key.block_name].add(key.layer_name)

    # Group attributes by (block_name, tag) -> set of values
    block_tag_values: dict[tuple[str, str], set[str]] = {}
    for block_name, attrs in block_attribute_data.items():
        for tag, value in attrs:
            key = (block_name, tag)
            if key not in block_tag_values:
                block_tag_values[key] = set()
            block_tag_values[key].add(value)

    # Build rows
    rows = []
    for (block_name, tag), values in sorted(block_tag_values.items()):
        layer_names = sorted(block_to_layers.get(block_name, set()))
        layer_str = ", ".join(layer_names)
        values_str = ", ".join(sorted(values))
        rows.append({
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME: block_name,
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES: layer_str,
            EXCEL_COLUMN_ATTRIBUTE_TAG: tag,
            EXCEL_COLUMN_ATTRIBUTE_VALUES: values_str,
            EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT: len(values),
        })

    df = pd.DataFrame(rows)
    # Apply header formatting
    df.columns = [format_header(col) for col in df.columns]
    df.to_excel(writer, sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS, index=False)
    logger.info(f"Attribute Analysis sheet created with {len(df)} rows")
```

### Step 3: Update `write_excel` Function
- Locate the `write_excel` function in `excel_writer.py`
- Find the section where sheets are created (around lines 391-416)
- Add call to `_create_attribute_analysis_sheet` after `_create_block_definitions_sheet`:
  ```python
  # Sheet 10: Attribute Analysis
  _create_attribute_analysis_sheet(extraction_data, writer)
  ```
- Update the docstring to mention the new sheet (10 sheets total instead of 9)

### Step 4: Add Unit Tests
- Add new test file or add to existing `test_excel_writer_core.py`:
```python
class TestAttributeAnalysisSheet:
    """Test suite for the Attribute Analysis sheet."""

    def test_attribute_analysis_sheet_exists(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Attribute Analysis sheet is created."""
        from core.constants import EXCEL_SHEET_ATTRIBUTE_ANALYSIS

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_ATTRIBUTE_ANALYSIS in wb.sheetnames

    def test_attribute_analysis_sheet_headers(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Attribute Analysis sheet has correct column headers."""
        from core.constants import (
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME,
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES,
            EXCEL_COLUMN_ATTRIBUTE_TAG,
            EXCEL_COLUMN_ATTRIBUTE_VALUES,
            EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT,
            EXCEL_SHEET_ATTRIBUTE_ANALYSIS,
        )

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS)
        expected_headers = [
            format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME),
            format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES),
            format_header(EXCEL_COLUMN_ATTRIBUTE_TAG),
            format_header(EXCEL_COLUMN_ATTRIBUTE_VALUES),
            format_header(EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT),
        ]
        assert list(df.columns) == expected_headers

    def test_attribute_analysis_sheet_data_aggregation(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Attribute Analysis sheet correctly aggregates attribute data."""
        from core.constants import (
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME,
            EXCEL_COLUMN_ATTRIBUTE_TAG,
            EXCEL_COLUMN_ATTRIBUTE_VALUES,
            EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT,
            EXCEL_SHEET_ATTRIBUTE_ANALYSIS,
        )

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS)

        # sample_extraction_data has VALVE with 3 attributes (DEPT, PROD1, PROD2)
        # and PIPE with 1 attribute (ID)
        # Total: 4 rows (one per block-tag combination)
        assert len(df) == 4

        # Verify VALVE rows exist with correct tags
        valve_rows = df[df[format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME)] == "VALVE"]
        assert len(valve_rows) == 3

        # Verify PIPE row exists with correct tag
        pipe_rows = df[df[format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME)] == "PIPE"]
        assert len(pipe_rows) == 1
        assert pipe_rows.iloc[0][format_header(EXCEL_COLUMN_ATTRIBUTE_TAG)] == "ID"
        assert pipe_rows.iloc[0][format_header(EXCEL_COLUMN_ATTRIBUTE_VALUES)] == "PIPE-001"
        assert pipe_rows.iloc[0][format_header(EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT)] == 1

    def test_attribute_analysis_sheet_layer_names(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Attribute Analysis sheet shows correct layer names for each block."""
        from core.constants import (
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES,
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME,
            EXCEL_SHEET_ATTRIBUTE_ANALYSIS,
        )

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS)

        # VALVE appears on Layer1 and Layer2 in sample_extraction_data
        valve_rows = df[df[format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME)] == "VALVE"]
        valve_layers = valve_rows.iloc[0][format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES)]
        assert "Layer1" in valve_layers
        assert "Layer2" in valve_layers

        # PIPE appears only on Layer1
        pipe_rows = df[df[format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME)] == "PIPE"]
        assert pipe_rows.iloc[0][format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES)] == "Layer1"

    def test_attribute_analysis_sheet_sorted_by_block_and_tag(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Attribute Analysis sheet is sorted by block name then tag name."""
        from core.constants import (
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME,
            EXCEL_COLUMN_ATTRIBUTE_TAG,
            EXCEL_SHEET_ATTRIBUTE_ANALYSIS,
        )

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS)

        # Should be sorted: PIPE then VALVE (alphabetical by block)
        # Within VALVE: DEPT, PROD1, PROD2 (alphabetical by tag)
        block_names = list(df[format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME)])
        assert block_names[0] == "PIPE"
        assert block_names[1] == "VALVE"

        # Verify VALVE tags are sorted
        valve_rows = df[df[format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME)] == "VALVE"]
        valve_tags = list(valve_rows[format_header(EXCEL_COLUMN_ATTRIBUTE_TAG)])
        assert valve_tags == ["DEPT", "PROD1", "PROD2"]

    def test_attribute_analysis_sheet_empty_data(
        self, temp_dir: str
    ) -> None:
        """Test Attribute Analysis sheet with no attribute data creates headers only."""
        from core.constants import (
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME,
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES,
            EXCEL_COLUMN_ATTRIBUTE_TAG,
            EXCEL_COLUMN_ATTRIBUTE_VALUES,
            EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT,
            EXCEL_SHEET_ATTRIBUTE_ANALYSIS,
        )
        from core.types import BlockLayerKey

        # Create minimal extraction data with no attributes
        empty_attr_data: ExtractionResult = {
            "block_counts": {},
            "block_entities": {},
            "block_layer_pairs": {},
            "block_rotation_counts": {},
            "block_scale_data": {},
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {},
            "layer_entity_counts": {},
            "layer_unique_color_counts": {},
            "layer_annotation_counts": {},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "extraction_issues": [],
            "block_trimming_data": {},
            "block_content_zone_data": {},
            "all_block_definitions": {},
            "nested_block_parents": {},
            "block_attribute_data": {},  # Empty!
        }

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(empty_attr_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS)

        # Should have headers but no data rows
        expected_headers = [
            format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME),
            format_header(EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES),
            format_header(EXCEL_COLUMN_ATTRIBUTE_TAG),
            format_header(EXCEL_COLUMN_ATTRIBUTE_VALUES),
            format_header(EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT),
        ]
        assert list(df.columns) == expected_headers
        assert len(df) == 0
```

### Step 5: Update Test for Sheet Count
- Update the existing test `test_write_excel_nine_sheets` to expect 10 sheets
- Rename the test to `test_write_excel_ten_sheets`
- Add assertion for `EXCEL_SHEET_ATTRIBUTE_ANALYSIS`

### Step 6: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- Test that Attribute Analysis sheet is created in the workbook
- Test that sheet has correct 5-column header structure
- Test that data is correctly aggregated by (block_name, tag)
- Test that layer names are correctly looked up and comma-separated
- Test that values are correctly collected and comma-separated
- Test that value_count is correct (number of unique values)
- Test that rows are sorted by block_name then tag
- Test empty data case creates sheet with headers only

### Integration Tests
- Test full Excel generation with sample_extraction_data fixture
- Verify sheet appears alongside existing 9 sheets
- Verify sheet count is now 10

### Edge Cases
- Empty block_attribute_data dictionary
- Block with attributes but not in block_layer_pairs (no layer info)
- Block with multiple tags having the same value
- Block with single attribute having multiple different values
- Very long attribute value strings (truncation if needed)

### Playwright MCP Tests
Not applicable for this unit - no GUI or end-to-end functionality added.

## Acceptance Criteria
- [ ] `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` constant imported in excel_writer.py
- [ ] All 5 `EXCEL_COLUMN_ATTRIBUTE_*` constants imported in excel_writer.py
- [ ] `_create_attribute_analysis_sheet` function implemented with correct logic
- [ ] Function creates DataFrame with 5 columns in correct order
- [ ] Function handles empty block_attribute_data with headers-only sheet
- [ ] Function builds block-to-layers lookup from block_layer_pairs
- [ ] Function groups attributes by (block_name, tag) and collects unique values
- [ ] Rows are sorted by (block_name, tag) alphabetically
- [ ] Layer names are comma-separated and sorted alphabetically
- [ ] Values are comma-separated and sorted alphabetically
- [ ] Value count is the number of unique values for that (block, tag) pair
- [ ] Headers are formatted using format_header() function
- [ ] Sheet is written with sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS
- [ ] `write_excel()` function calls `_create_attribute_analysis_sheet`
- [ ] `write_excel()` docstring updated to mention 10 sheets
- [ ] All unit tests pass
- [ ] `uv run mypy app/` passes with no errors
- [ ] `uv run pytest app/tests/` passes with all tests
- [ ] `uv run ruff check app/` passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/excel_writer.py` - Type check the modified excel_writer file
- `uv run mypy app/` - Run full type checking to ensure no regressions
- `uv run pytest app/tests/core/excel_writer/ -v` - Run excel_writer tests to verify new tests pass
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run ruff check app/` - Lint check for code quality
- `uv run ruff format app/ --check` - Verify code formatting

## Notes
- This is Unit 3 of the Attribute Analysis Sheet feature:
  - Unit 1 (completed): Renamed constant and updated All Blocks sheet for unique tags
  - Unit 2 (completed): Added sheet and column constants (1143 tests passing)
  - **Unit 3 (this spec)**: Implement `_create_attribute_analysis_sheet` function
  - Unit 4 (future): Add formatting function and tests
- The implementation follows the existing pattern for sheet creation functions in excel_writer.py
- The function uses the same data structures already populated by the extractor: `block_attribute_data` (dict[str, list[tuple[str, str]]]) and `block_layer_pairs` (dict[BlockLayerKey, int])
- Sorting by (block_name, tag) ensures deterministic output for testing
- The sample_extraction_data fixture in conftest.py already has block_attribute_data populated with test data
