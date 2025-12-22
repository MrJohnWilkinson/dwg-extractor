# Chore: Rename Attribute Constant and Update All Blocks Sheet

## Chore Description
Rename the constant `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS` in constants.py and update all references throughout the codebase. Additionally, modify the attribute string formatting in the All Blocks sheet to display unique tags only (instead of TAG:VALUE pairs) while preserving the `attr_count` as the total number of (tag, value) pairs.

This is Unit 1 of a refactoring effort to change the attribute column from showing full TAG:VALUE pairs to showing only unique attribute tags. The attribute count column (`block_attribute_count`) will continue to show the total number of attribute entries (tag-value pairs), while the renamed column (`block_attribute_tags`) will show a comma-separated list of unique tag names.

## Relevant Files
Use these files to resolve the chore:

- `app/core/constants.py` - Contains the constant definition `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` at line 148. This is the source of truth that needs to be renamed to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS` with updated comment.

- `app/core/excel_writer.py` - Imports and uses `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` in multiple locations:
  - Line 32: Import statement
  - Line 1097: Empty DataFrame column list (empty data case)
  - Line 1237: Attribute string formatting (change from TAG:VALUE pairs to unique tags)
  - Line 1272: Row dict population
  - Line 1311: Empty DataFrame column list (empty rows case)

- `app/tests/core/excel_writer/test_excel_writer_all_blocks.py` - Contains test imports and assertions using `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA`:
  - Line 23: Import statement
  - Line 129: Column list verification
  - Line 640, 662, 733, 762: Test assertions checking attribute data format

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Rename constant in constants.py

**File:** `app/core/constants.py`
**Location:** Line 144-148

- Change the constant name from `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS`
- Update the value from `"block_attribute_data"` to `"block_attribute_tags"`
- Update the comment to reflect the new purpose (unique tags, not TAG:VALUE pairs)

**Before:**
```python
# Excel configuration - Block Attributes columns
# See app_docs/005-field-naming-convention.md for naming conventions
# Domain: block, Attribute: attribute, Qualifier: count/data
EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT: str = "block_attribute_count"
EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA: str = "block_attribute_data"
```

**After:**
```python
# Excel configuration - Block Attributes columns
# See app_docs/005-field-naming-convention.md for naming conventions
# Domain: block, Attribute: attribute, Qualifier: count/tags
EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT: str = "block_attribute_count"
EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS: str = "block_attribute_tags"
```

### 2. Update import in excel_writer.py

**File:** `app/core/excel_writer.py`
**Location:** Line 32

- Replace `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` with `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS` in the import statement

**Before:**
```python
    EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA,
```

**After:**
```python
    EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS,
```

### 3. Modify attribute string formatting

**File:** `app/core/excel_writer.py`
**Location:** Lines 1232-1238 (in `_create_all_blocks_sheet` function)

- Change the formatting from TAG:VALUE pairs to unique tags only
- Keep `attr_count` as the total number of (tag, value) pairs
- Extract unique tags from the attributes list and format as comma-separated string

**Before:**
```python
        # Get attributes for this block
        attrs = block_attribute_data.get(resolved_name, [])
        attr_count = len(attrs)

        # Format as newline-separated TAG:VALUE pairs (already sorted from extraction)
        attr_str = "\n".join(f"{tag}:{value}" for tag, value in attrs)
        attr_str = _truncate_segment_string(attr_str)
```

**After:**
```python
        # Get attributes for this block
        attrs = block_attribute_data.get(resolved_name, [])
        attr_count = len(attrs)

        # Extract unique tags (sorted alphabetically) - count remains total (tag, value) pairs
        unique_tags = sorted(set(tag for tag, value in attrs))
        attr_str = ", ".join(unique_tags)
        attr_str = _truncate_segment_string(attr_str)
```

### 4. Update column reference in row dict

**File:** `app/core/excel_writer.py`
**Location:** Line 1272

- Change the dictionary key from `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS`

**Before:**
```python
                EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA: attr_str,
```

**After:**
```python
                EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS: attr_str,
```

### 5. Update empty DataFrame column lists

**File:** `app/core/excel_writer.py`

Update both occurrences of `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` in the empty DataFrame column lists:

**Location 1:** Line 1097 (empty data case)
**Location 2:** Line 1311 (empty rows case)

**Before (both locations):**
```python
                EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA,
```

**After (both locations):**
```python
                EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS,
```

### 6. Update test imports and references

**File:** `app/tests/core/excel_writer/test_excel_writer_all_blocks.py`

**6.1 Update import (Line 23):**

**Before:**
```python
    EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA,
```

**After:**
```python
    EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS,
```

**6.2 Update column list verification (Line 129):**

**Before:**
```python
            format_header(EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA),
```

**After:**
```python
            format_header(EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS),
```

**6.3 Update test assertions (Lines 640, 662, 733, 762):**

For each location, update:
- The constant reference from `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS`
- The expected format from newline-separated TAG:VALUE pairs to comma-separated unique tags

**Example transformation for line 640:**

**Before:**
```python
        attr_data = valve_row.iloc[0][format_header(EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA)]
        assert "DEPT:30" in attr_data
        assert "PROD1:Garage" in attr_data
```

**After:**
```python
        attr_data = valve_row.iloc[0][format_header(EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS)]
        # Now shows unique tags only, comma-separated
        assert "DEPT" in attr_data
        assert "PROD1" in attr_data
```

### 7. Run validation

Execute the following commands to validate the changes:

```bash
uv run mypy app/core/constants.py app/core/excel_writer.py
uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v
```

Fix any import errors or test failures before proceeding.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

```bash
# Type checking for modified files
uv run mypy app/core/constants.py app/core/excel_writer.py

# Run specific tests for All Blocks sheet
uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v

# Run all excel_writer tests to ensure no regressions
uv run pytest app/tests/core/excel_writer/ -v

# Run full test suite
uv run pytest app/tests/ -v
```

## Notes

- The `attr_count` column value remains the total number of (tag, value) pairs to preserve backward compatibility and provide useful information about the total number of attribute entries.
- The unique tags are sorted alphabetically for consistent output.
- The truncation logic using `_truncate_segment_string` is preserved to handle cases with many unique tags.
- The change from newline-separated format to comma-separated format makes the column more compact and easier to read in Excel.
- Test assertions need to be updated to expect comma-separated unique tags instead of newline-separated TAG:VALUE pairs.
