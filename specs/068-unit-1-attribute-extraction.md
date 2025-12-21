# Feature: Block Attribute Extraction (Unit 1)

## Feature Description
Implement extraction of ATTRIB entities from INSERT blocks to populate the `block_attribute_data` field in ExtractionResult. This is Unit 1 of the Block Attributes Excel implementation, focusing solely on the data extraction layer.

Block attributes (ATTRIB entities) contain metadata attached to block insertions in AutoCAD drawings. Examples include product codes, department names, bay numbers, and other user-defined data. This feature extracts these tag-value pairs and aggregates them by block name across all insertions.

The `block_attribute_data` field already exists in `ExtractionResult` (line 973) but is not populated. The constants `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` and `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` also already exist in `constants.py`.

## User Story
As a CAD analyst
I want block attribute data (ATTRIB entities) extracted from INSERT blocks
So that I can see product codes, department names, and other metadata in the Excel output

## Problem Statement
Currently, the `block_attribute_data` field in `ExtractionResult` is defined but never populated during extraction. Block insertions in DXF files often contain ATTRIB entities with valuable metadata like:
- Product codes (PROD1, PROD2)
- Department identifiers (DEPT)
- Bay numbers (BAY#)
- Custom user data

This metadata is invisible in the current extraction output, forcing users to manually inspect DXF files or use AutoCAD to view attribute data.

## Solution Statement
Extract ATTRIB entities from INSERT blocks during modelspace entity processing and populate the `block_attribute_data` field with aggregated tag-value pairs per block name.

The solution:
1. Initialize a `block_attribute_data` dictionary during extraction setup
2. For each INSERT entity, iterate over its `attribs` collection
3. Extract the tag name and text value from each ATTRIB entity
4. Skip empty values to avoid noise
5. Aggregate unique (tag, value) pairs per block name using a set
6. Convert the sets to sorted lists when building the result dictionary

## Relevant Files
Use these files to implement the feature:

### Core Implementation Files
- `app/core/extractor.py` - Main implementation file. Contains `extract_blocks()` function where `block_attribute_data` needs to be initialized, populated during INSERT processing, and added to the result dictionary. Key locations:
  - Line 973: `block_attribute_data` field already exists in `ExtractionResult` TypedDict
  - Line ~1187: Where other data structures are initialized (add initialization here)
  - Lines ~1424-1560: INSERT entity processing section (add ATTRIB extraction here)
  - Line ~1710: Result dictionary construction (add `block_attribute_data` to result)

### Type Definitions
- `app/core/types.py` - Contains `BlockAttributeRecord` TypedDict (line 274) which is already defined for attribute data. Also contains `ExtractionResult` type definition.

### Constants
- `app/core/constants.py` - Already contains `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` (line 147) and `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` (line 148).

### Test Files
- `app/tests/core/extractor/test_extractor_core.py` - Contains existing tests for `extract_blocks()`. Add new tests for attribute extraction.

### New Files
- `app/tests/assets/create_block_attributes_test.py` - Script to create test DXF file with ATTRIB entities
- `app/tests/assets/block_attributes_test.dxf` - Test fixture with blocks containing attributes

## Implementation Plan

### Phase 1: Foundation
Create the test fixture file with blocks containing ATTRIB entities to enable test-driven development.

1. Create a script to generate `block_attributes_test.dxf` with:
   - Block definitions that include ATTDEF (attribute definitions)
   - INSERT entities with populated ATTRIB values
   - Mix of blocks with and without attributes
   - Various attribute patterns (single, multiple, empty values)

### Phase 2: Core Implementation
Implement the ATTRIB extraction logic in the extractor.

1. Initialize `block_attribute_data` dictionary near other data structures
2. Add ATTRIB extraction logic in the INSERT entity processing section
3. Handle edge cases (missing attribs property, empty values)
4. Convert sets to sorted lists in the result dictionary

### Phase 3: Integration
Ensure the extraction integrates correctly with existing functionality.

1. Add comprehensive unit tests for attribute extraction
2. Verify no regression in existing tests
3. Run full validation suite

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create test fixture generator script
- Create `app/tests/assets/create_block_attributes_test.py`:
```python
"""
Create test DXF file with block attributes (ATTRIB entities).

This script generates a DXF file with blocks containing attribute definitions
and insertions with populated attribute values for testing attribute extraction.
"""

import ezdxf

def create_block_attributes_test() -> None:
    """Create a test DXF file with block attributes."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create layer for testing
    doc.layers.add("TEST_LAYER")

    # Block 1: PRODUCT_BLOCK with multiple attributes
    block1 = doc.blocks.new(name="PRODUCT_BLOCK")
    block1.add_line((0, 0), (100, 0))
    block1.add_line((100, 0), (100, 50))
    block1.add_line((100, 50), (0, 50))
    block1.add_line((0, 50), (0, 0))
    # Add attribute definitions
    block1.add_attdef("PROD1", (10, 10), dxfattribs={"prompt": "Product 1"})
    block1.add_attdef("PROD2", (10, 20), dxfattribs={"prompt": "Product 2"})
    block1.add_attdef("DEPT", (10, 30), dxfattribs={"prompt": "Department"})
    block1.add_attdef("BAY#", (10, 40), dxfattribs={"prompt": "Bay Number"})

    # Block 2: SIMPLE_BLOCK with single attribute
    block2 = doc.blocks.new(name="SIMPLE_BLOCK")
    block2.add_circle((25, 25), 20)
    block2.add_attdef("ID", (25, 25), dxfattribs={"prompt": "Identifier"})

    # Block 3: NO_ATTRIB_BLOCK without attributes
    block3 = doc.blocks.new(name="NO_ATTRIB_BLOCK")
    block3.add_line((0, 0), (50, 50))

    # Block 4: EMPTY_VALUE_BLOCK with attribute that will have empty value
    block4 = doc.blocks.new(name="EMPTY_VALUE_BLOCK")
    block4.add_line((0, 0), (30, 30))
    block4.add_attdef("EMPTY_ATTR", (15, 15), dxfattribs={"prompt": "Empty Attribute"})

    # Insert PRODUCT_BLOCK with filled attributes (first instance)
    insert1 = msp.add_blockref("PRODUCT_BLOCK", (0, 0), dxfattribs={"layer": "TEST_LAYER"})
    insert1.add_auto_attribs({
        "PROD1": "Garage",
        "PROD2": "Door Openers",
        "DEPT": "30",
        "BAY#": "27-004",
    })

    # Insert PRODUCT_BLOCK with different values (second instance)
    insert2 = msp.add_blockref("PRODUCT_BLOCK", (200, 0), dxfattribs={"layer": "TEST_LAYER"})
    insert2.add_auto_attribs({
        "PROD1": "Kitchen",
        "PROD2": "Appliances",
        "DEPT": "45",
        "BAY#": "12-001",
    })

    # Insert PRODUCT_BLOCK with some empty values (third instance)
    insert3 = msp.add_blockref("PRODUCT_BLOCK", (400, 0), dxfattribs={"layer": "TEST_LAYER"})
    insert3.add_auto_attribs({
        "PROD1": "Garage",  # Same as first to test deduplication
        "PROD2": "",  # Empty value - should be skipped
        "DEPT": "30",  # Same as first to test deduplication
        "BAY#": "27-005",  # Different bay
    })

    # Insert SIMPLE_BLOCK with single attribute
    insert4 = msp.add_blockref("SIMPLE_BLOCK", (0, 100), dxfattribs={"layer": "TEST_LAYER"})
    insert4.add_auto_attribs({"ID": "ITEM-001"})

    # Insert SIMPLE_BLOCK with different ID
    insert5 = msp.add_blockref("SIMPLE_BLOCK", (100, 100), dxfattribs={"layer": "TEST_LAYER"})
    insert5.add_auto_attribs({"ID": "ITEM-002"})

    # Insert NO_ATTRIB_BLOCK (no attributes)
    msp.add_blockref("NO_ATTRIB_BLOCK", (0, 200), dxfattribs={"layer": "TEST_LAYER"})
    msp.add_blockref("NO_ATTRIB_BLOCK", (100, 200), dxfattribs={"layer": "TEST_LAYER"})

    # Insert EMPTY_VALUE_BLOCK with empty attribute value
    insert6 = msp.add_blockref("EMPTY_VALUE_BLOCK", (0, 300), dxfattribs={"layer": "TEST_LAYER"})
    insert6.add_auto_attribs({"EMPTY_ATTR": ""})  # Empty value - should be skipped

    # Save the file
    doc.saveas("app/tests/assets/block_attributes_test.dxf")
    print("Created: app/tests/assets/block_attributes_test.dxf")


if __name__ == "__main__":
    create_block_attributes_test()
```
- Run `uv run python app/tests/assets/create_block_attributes_test.py` to generate the test file
- Verify file was created: `ls -la app/tests/assets/block_attributes_test.dxf`

### 2. Initialize block_attribute_data in extract_blocks
- Open `app/core/extractor.py`
- Find the section where result dictionaries are initialized (around line 1187)
- Add initialization after `extraction_issues: list[ExtractionIssue] = []` (around line 1187):
```python
# Track block attribute data from ATTRIB entities on INSERT
block_attribute_data: dict[str, set[tuple[str, str]]] = {}
```
- Run `uv run mypy app/core/extractor.py` to verify no type errors

### 3. Add ATTRIB extraction in INSERT processing section
- Open `app/core/extractor.py`
- Find the INSERT entity processing section (around line 1424-1560)
- After the XDATA extraction section (around line 1556-1559), add:
```python
# Extract ATTRIB entities (block attributes)
try:
    if hasattr(entity, 'attribs'):
        for attrib in entity.attribs:
            tag = attrib.dxf.tag
            value = attrib.dxf.text
            if value:  # Skip empty values
                effective_name = block_name  # Use the resolved block name
                if effective_name not in block_attribute_data:
                    block_attribute_data[effective_name] = set()
                block_attribute_data[effective_name].add((tag, value))
except (AttributeError, TypeError):
    # Entity doesn't support ATTRIB or has malformed attributes
    pass
```
- Run `uv run mypy app/core/extractor.py` to verify no type errors

### 4. Add block_attribute_data to result dictionary
- Open `app/core/extractor.py`
- Find the result dictionary construction (around line 1710)
- Add `block_attribute_data` to the result dict (after `nested_block_parents`, around line 1731):
```python
"block_attribute_data": {
    k: sorted(list(v)) for k, v in block_attribute_data.items()
},
```
- Run `uv run mypy app/core/extractor.py` to verify no type errors

### 5. Create unit tests for attribute extraction
- Create tests in `app/tests/core/extractor/test_extractor_attributes.py`:
```python
"""
Unit tests for the extractor module - block attribute extraction.

This test suite validates ATTRIB entity extraction from INSERT blocks,
including edge cases like empty values, multiple attributes, and blocks
without attributes.
"""

import pytest

from core.extractor import extract_blocks


class TestBlockAttributeExtraction:
    """Test suite for block attribute extraction functionality."""

    def test_block_attribute_data_exists_in_result(self) -> None:
        """Test that block_attribute_data field exists in extraction result."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        assert "block_attribute_data" in result
        assert isinstance(result["block_attribute_data"], dict)

    def test_block_with_multiple_attributes(self) -> None:
        """Test extraction of block with multiple attribute tags."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # PRODUCT_BLOCK should have attributes
        assert "PRODUCT_BLOCK" in result["block_attribute_data"]
        attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]

        # Should be a list of (tag, value) tuples, sorted alphabetically
        assert isinstance(attrs, list)

        # Convert to dict for easier assertions
        attr_dict: dict[str, set[str]] = {}
        for tag, value in attrs:
            if tag not in attr_dict:
                attr_dict[tag] = set()
            attr_dict[tag].add(value)

        # Verify expected tags exist
        assert "PROD1" in attr_dict
        assert "PROD2" in attr_dict
        assert "DEPT" in attr_dict
        assert "BAY#" in attr_dict

        # Verify PROD1 has both unique values
        assert "Garage" in attr_dict["PROD1"]
        assert "Kitchen" in attr_dict["PROD1"]

        # Verify PROD2 has both non-empty values (empty skipped)
        assert "Door Openers" in attr_dict["PROD2"]
        assert "Appliances" in attr_dict["PROD2"]

    def test_block_with_single_attribute(self) -> None:
        """Test extraction of block with single attribute tag."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # SIMPLE_BLOCK should have ID attribute
        assert "SIMPLE_BLOCK" in result["block_attribute_data"]
        attrs = result["block_attribute_data"]["SIMPLE_BLOCK"]

        # Should have 2 unique (tag, value) pairs
        assert len(attrs) == 2

        # Verify both ID values are captured
        values = [v for t, v in attrs if t == "ID"]
        assert "ITEM-001" in values
        assert "ITEM-002" in values

    def test_block_without_attributes(self) -> None:
        """Test that blocks without attributes are not in block_attribute_data."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # NO_ATTRIB_BLOCK should not be in block_attribute_data
        # (or should have empty list, depending on implementation)
        if "NO_ATTRIB_BLOCK" in result["block_attribute_data"]:
            assert len(result["block_attribute_data"]["NO_ATTRIB_BLOCK"]) == 0

    def test_empty_attribute_values_skipped(self) -> None:
        """Test that empty attribute values are not extracted."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # EMPTY_VALUE_BLOCK should not be in results (all values empty)
        if "EMPTY_VALUE_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["EMPTY_VALUE_BLOCK"]
            # Should have no entries since all values are empty
            assert len(attrs) == 0

    def test_attribute_data_sorted_alphabetically(self) -> None:
        """Test that attribute data is sorted alphabetically by tag then value."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        if "PRODUCT_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]
            # Verify list is sorted
            assert attrs == sorted(attrs)

    def test_attribute_deduplication(self) -> None:
        """Test that duplicate (tag, value) pairs are deduplicated."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        if "PRODUCT_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]
            # Should not have duplicate entries
            assert len(attrs) == len(set(attrs))

    def test_block_attribute_data_empty_file(self) -> None:
        """Test attribute extraction from empty file."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")

        assert "block_attribute_data" in result
        assert isinstance(result["block_attribute_data"], dict)
        # Empty file should have no attribute data
        assert len(result["block_attribute_data"]) == 0

    def test_block_attribute_data_file_without_attribs(self) -> None:
        """Test attribute extraction from file with blocks but no ATTRIB entities."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        assert "block_attribute_data" in result
        assert isinstance(result["block_attribute_data"], dict)
        # sample_drawing.dxf has blocks but no ATTRIB entities
        # Result should be empty or have only entries with no attributes

    def test_attribute_tag_value_types(self) -> None:
        """Test that attribute tags and values are strings."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        for block_name, attrs in result["block_attribute_data"].items():
            assert isinstance(block_name, str)
            assert isinstance(attrs, list)
            for tag, value in attrs:
                assert isinstance(tag, str)
                assert isinstance(value, str)


class TestBlockAttributeDataStructure:
    """Test suite for block_attribute_data structure verification."""

    def test_attribute_data_is_list_of_tuples(self) -> None:
        """Test that each block's attribute data is a list of tuples."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        for block_name, attrs in result["block_attribute_data"].items():
            assert isinstance(attrs, list)
            for item in attrs:
                assert isinstance(item, (list, tuple))
                assert len(item) == 2

    def test_attribute_data_conservation(self) -> None:
        """Test that all non-empty attributes from all insertions are captured."""
        result = extract_blocks("app/tests/assets/block_attributes_test.dxf")

        # PRODUCT_BLOCK has 3 insertions with various attribute values
        # After deduplication and empty value filtering:
        # PROD1: "Garage", "Kitchen" (2 values, "Garage" appears twice but deduplicated)
        # PROD2: "Door Openers", "Appliances" (2 values, empty skipped)
        # DEPT: "30", "45" (2 values, "30" appears twice but deduplicated)
        # BAY#: "27-004", "12-001", "27-005" (3 values)

        if "PRODUCT_BLOCK" in result["block_attribute_data"]:
            attrs = result["block_attribute_data"]["PRODUCT_BLOCK"]

            # Count unique values per tag
            tag_values: dict[str, set[str]] = {}
            for tag, value in attrs:
                if tag not in tag_values:
                    tag_values[tag] = set()
                tag_values[tag].add(value)

            # Verify expected counts (these may vary based on test file content)
            assert len(tag_values.get("PROD1", set())) >= 2
            assert len(tag_values.get("PROD2", set())) >= 2
            assert len(tag_values.get("DEPT", set())) >= 2
            assert len(tag_values.get("BAY#", set())) >= 3
```
- Run tests: `uv run pytest app/tests/core/extractor/test_extractor_attributes.py -v`

### 6. Run full validation
- Run `uv run mypy app/` - Full type checking
- Run `uv run pytest app/tests/core/extractor/test_extractor_attributes.py -v` - Run new attribute tests
- Run `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- Run `uv run pytest app/tests/ -v` - Run full test suite
- Run `uv run ruff check app/` - Linting
- Run `uv run ruff format app/ --check` - Format check

## Testing Strategy

### Unit Tests
- **Existence test**: Verify `block_attribute_data` field exists in result
- **Multiple attributes test**: Verify blocks with multiple ATTDEF/ATTRIB pairs are extracted
- **Single attribute test**: Verify blocks with single attribute are extracted
- **No attributes test**: Verify blocks without ATTRIB entities are not in result
- **Empty values test**: Verify empty attribute values are skipped
- **Deduplication test**: Verify duplicate (tag, value) pairs are deduplicated via set
- **Sorting test**: Verify attribute data is sorted alphabetically
- **Type test**: Verify all tags and values are strings

### Integration Tests
- **Empty file test**: Verify extraction from empty DXF returns empty dict
- **File without ATTRIB test**: Verify extraction from file with blocks but no ATTRIBs works
- **Conservation test**: Verify all non-empty attributes across all insertions are captured

### Edge Cases
- Empty DXF file (no blocks)
- DXF with blocks but no ATTRIB entities
- DXF with blocks where some have ATTRIB and some don't
- ATTRIB with empty text value (should be skipped)
- Multiple insertions of same block with different attribute values
- Multiple insertions of same block with identical attribute values (deduplication)
- Blocks with many attributes (stress test)
- Unicode/special characters in attribute values

### Playwright MCP Tests
Not applicable - this is a backend data extraction feature with no UI changes.

## Acceptance Criteria
1. `block_attribute_data` field is populated in `ExtractionResult`
2. ATTRIB entities are extracted from INSERT blocks during modelspace processing
3. Empty attribute values are skipped (not added to result)
4. Attribute data is stored as `dict[str, list[tuple[str, str]]]` (block_name -> sorted list of (tag, value) tuples)
5. Duplicate (tag, value) pairs are deduplicated via set before converting to sorted list
6. Blocks without ATTRIB entities are not present in `block_attribute_data` (or have empty list)
7. All existing tests pass without modification
8. New tests verify attribute extraction behavior
9. Type checking passes with zero errors
10. Code follows existing patterns in extractor.py for entity processing

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run python app/tests/assets/create_block_attributes_test.py` - Create test fixture
- `ls -la app/tests/assets/block_attributes_test.dxf` - Verify fixture exists
- `uv run mypy app/` - Run type checker on full application - must pass with 0 errors
- `uv run pytest app/tests/core/extractor/test_extractor_attributes.py -v` - Run new attribute extraction tests
- `uv run pytest app/tests/core/extractor/test_extractor_core.py -v` - Verify core extraction still works
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run ruff check app/` - Run linter - must pass with 0 errors
- `uv run ruff format app/ --check` - Verify code formatting - must pass

## Notes
- The `block_attribute_data` field in `ExtractionResult` already uses the type signature `dict[str, set[tuple[str, str]]]` but will be converted to `dict[str, list[tuple[str, str]]]` in the result to ensure JSON serializability and consistent ordering
- The ATTRIB extraction uses the same error handling pattern as XDATA extraction in the existing code
- `hasattr(entity, 'attribs')` is used to check if the INSERT entity has ATTRIB entities attached
- The `attrib.dxf.tag` and `attrib.dxf.text` attributes follow ezdxf's standard attribute access pattern
- This is Unit 1 of a multi-unit implementation; subsequent units will add Excel column output using the existing `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` and `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` constants
- The `effective_name` variable used in the ATTRIB extraction is the same resolved block name used for block counting (handles dynamic blocks correctly)
