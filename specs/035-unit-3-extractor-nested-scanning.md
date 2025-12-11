# Feature: Nested Block Detection - Unit 3: Extractor Nested Scanning

## Feature Description
This unit implements the core nested block scanning logic in `app/core/extractor.py`. It scans INSERT entities within block definitions to detect parent-child relationships between blocks, builds complete `BlockDefinitionRecord` entries for every block in the DXF file, and updates the `ExtractionResult` TypedDict with the new fields. This is the foundational extraction logic that will power the "Block Definitions" sheet in future Excel writer units.

## User Story
As a CAD data analyst
I want to see which blocks are nested inside other blocks
So that I can understand the hierarchical structure of block definitions in my DXF files

## Problem Statement
The DXF Block Extractor currently tracks block insertions in modelspace but does not:
1. Detect INSERT entities within block definitions (nested blocks)
2. Build parent-child relationship mappings between blocks
3. Track all block definitions regardless of insertion status
4. Classify blocks as "Inserted", "Nested Only", "Unused", "System", or "Unresolved"

This information is critical for understanding complex CAD file structures where blocks contain other blocks.

## Solution Statement
Modify `app/core/extractor.py` to:
1. Add tracking variables for nested block relationships (`all_block_definitions`, `nested_block_parents`)
2. Scan INSERT entities within each block definition to build parent-child mappings
3. Build complete `BlockDefinitionRecord` entries after modelspace scan when `block_counts` is populated
4. Add a helper function `_classify_block_insertion_status()` to determine block status
5. Update `ExtractionResult` TypedDict with new fields
6. Return the new data structures in the extraction result

## Relevant Files
Use these files to implement the feature:

- **app/core/extractor.py** - Main extraction logic; will add nested scanning code to `extract_blocks()` function and update `ExtractionResult` TypedDict
- **app/core/types.py** - Contains `BlockDefinitionRecord` TypedDict (already added in Unit 1-2)
- **app/tests/assets/nested_block_test.dxf** - Test fixture with nested block scenarios (created in Unit 1-2)

### New Files
- **app/tests/core/extractor/test_extractor_nested.py** - New test file for nested block detection tests

## Implementation Plan
### Phase 1: Foundation
Update the `ExtractionResult` TypedDict in `extractor.py` to include the two new fields: `all_block_definitions` and `nested_block_parents`.

### Phase 2: Core Implementation
Add nested block scanning logic to `extract_blocks()`:
1. Initialize tracking variables after existing declarations
2. Scan INSERT entities within block definitions during the block definition loop
3. Add a helper function to classify block insertion status
4. Build complete `BlockDefinitionRecord` entries after modelspace scan

### Phase 3: Integration
Update the return statement to include the new data structures and add comprehensive tests.

## Step by Step Tasks

### Step 1: Import BlockDefinitionRecord Type
- Open `app/core/extractor.py`
- Add `BlockDefinitionRecord` to the imports from `.types`
- Verify the import is correct (type was added in Unit 1-2)

### Step 2: Update ExtractionResult TypedDict
- Locate the `ExtractionResult` TypedDict class (around line 877)
- Add two new fields to the TypedDict:
  - `all_block_definitions: dict[str, BlockDefinitionRecord]` - Maps raw block name to complete record
  - `nested_block_parents: dict[str, list[str]]` - Maps child block name to list of parent names
- Update the docstring to document the new fields with examples

### Step 3: Add Nested Block Tracking Variables
- In `extract_blocks()` function, after the existing variable declarations (around line 1120), add:
  ```python
  # Track all block definitions and nested relationships
  all_block_definitions: dict[str, BlockDefinitionRecord] = {}
  nested_block_parents: dict[str, set[str]] = {}  # child_name -> {parent_names}
  ```

### Step 4: Add INSERT Entity Scanning in Block Definition Loop
- In the block definition loop (starting around line 1145), after the entity count calculation and geometry analysis
- Add INSERT entity scanning AFTER the effective_name is determined but BEFORE content zone detection:
  ```python
  # Scan block definition for nested INSERT entities
  for entity in block_def:
      if entity.dxftype() == "INSERT":
          nested_name = entity.dxf.name
          # Resolve anonymous block names if mapping exists
          if nested_name in anonymous_to_resolved:
              nested_name = anonymous_to_resolved[nested_name]
          # Track parent relationship
          if nested_name not in nested_block_parents:
              nested_block_parents[nested_name] = set()
          nested_block_parents[nested_name].add(effective_name)
  ```
- Note: This must be placed inside the existing block_def loop, after effective_name is set

### Step 5: Add _classify_block_insertion_status Helper Function
- Add a new helper function before the second pass through doc.blocks:
  ```python
  def _classify_block_insertion_status(
      block_name: str,
      raw_name: str,
      block_counts: dict[str, int],
      nested_parents: dict[str, set[str]],
  ) -> str:
      """Determine insertion status for a block."""
      # System blocks
      if raw_name in ("*Model_Space", "*Paper_Space") or raw_name.startswith("*Paper_Space"):
          return "System"
      if raw_name.startswith("*D") and len(raw_name) > 2 and raw_name[2:].isdigit():
          return "System (Dimension)"
      if raw_name.startswith("*X") and len(raw_name) > 2 and raw_name[2:].isdigit():
          return "System (Hatch)"

      # Unresolved anonymous blocks
      if raw_name.startswith("*U") and raw_name not in anonymous_to_resolved:
          return "Unresolved (*U)"
      if raw_name.startswith("A$C"):
          resolved = anonymous_to_resolved.get(raw_name)
          if resolved is None or resolved == raw_name:
              return "Unresolved (A$C)"

      # Regular/resolved blocks - check insertion status
      if block_name in block_counts:
          return "Inserted"
      if block_name in nested_parents:
          return "Nested Only"
      return "Unused"
  ```
- Note: This function is defined as a local function inside `extract_blocks()` to access `anonymous_to_resolved`

### Step 6: Build All Block Definitions After Modelspace Scan
- After the modelspace entity loop completes (around line 1481, before "Convert color sets to counts")
- Add a second pass through `doc.blocks` to build `all_block_definitions`:
  ```python
  # Build complete block definition records after modelspace scan
  # This must happen AFTER block_counts is populated
  logger.info("Building complete block definition records...")

  for block_def in doc.blocks:
      raw_name = block_def.name

      # Determine effective (resolved) name
      if raw_name in anonymous_to_resolved:
          effective_name = anonymous_to_resolved[raw_name]
      else:
          effective_name = raw_name

      # Count entities
      entity_count = sum(1 for _ in block_def)

      # Get parent names (sorted for consistency)
      parent_names = sorted(list(nested_block_parents.get(effective_name, set())))

      # Determine insertion status
      insertion_status = _classify_block_insertion_status(
          effective_name,
          raw_name,
          block_counts,
          nested_block_parents,
      )

      # Build record
      all_block_definitions[raw_name] = BlockDefinitionRecord(
          block_raw_name=raw_name,
          block_resolved_name=effective_name,
          block_insertion_status=insertion_status,
          block_is_nested=effective_name in nested_block_parents,
          block_nested_parent_names=parent_names,
          block_entity_count=entity_count,
      )

  logger.info(f"Tracked {len(all_block_definitions)} total block definitions")
  ```

### Step 7: Update ExtractionResult Return Statement
- Locate the return statement (around line 1550)
- Add the new fields to the result dictionary:
  ```python
  "all_block_definitions": all_block_definitions,
  "nested_block_parents": {k: sorted(list(v)) for k, v in nested_block_parents.items()},
  ```
- Note: Convert sets to sorted lists for JSON serialization compatibility

### Step 8: Create Test File for Nested Block Detection
- Create new file `app/tests/core/extractor/test_extractor_nested.py`
- Add comprehensive tests using `nested_block_test.dxf` fixture:
  - Test `all_block_definitions` field exists and has correct structure
  - Test `nested_block_parents` field exists and has correct structure
  - Test insertion status classification for each block type
  - Test `block_is_nested` flag accuracy
  - Test `block_nested_parent_names` lists
  - Test system blocks are correctly classified
  - Test entity counts are accurate

### Step 9: Run Validation Commands
- Run type checking with mypy
- Run all extractor tests
- Run full test suite to ensure no regressions

## Testing Strategy
### Unit Tests
Create `app/tests/core/extractor/test_extractor_nested.py` with tests for:
- `test_extract_all_block_definitions_exists` - Verify field exists in result
- `test_extract_nested_block_parents_exists` - Verify field exists in result
- `test_nested_block_insertion_status_inserted` - Blocks with modelspace insertions
- `test_nested_block_insertion_status_nested_only` - Blocks only in other blocks
- `test_nested_block_insertion_status_unused` - Blocks never inserted anywhere
- `test_nested_block_insertion_status_system` - System blocks (*Model_Space, etc.)
- `test_nested_block_is_nested_flag` - Verify block_is_nested accuracy
- `test_nested_block_parent_names` - Verify parent names lists
- `test_nested_block_multi_parent` - Blocks nested in multiple parents
- `test_nested_block_entity_counts` - Entity count accuracy
- `test_nested_block_empty_file` - Empty file handling

### Integration Tests
- Test with `nested_block_test.dxf` fixture which has known block relationships
- Verify all 6 user-defined blocks are tracked
- Verify system blocks are classified correctly

### Edge Cases
- Empty DXF files (no blocks)
- Files with only system blocks
- Deep nesting (blocks containing blocks containing blocks)
- Self-referencing blocks (if possible in DXF)
- Anonymous blocks (*U, A$C patterns)
- Mixed resolved and unresolved anonymous blocks

### Playwright MCP Tests
- Not applicable for this unit (backend extraction logic only)

## Acceptance Criteria
1. `ExtractionResult` TypedDict includes `all_block_definitions` and `nested_block_parents` fields
2. `BlockDefinitionRecord` import is added to extractor.py
3. `nested_block_parents` tracking variable is initialized in `extract_blocks()`
4. INSERT entities within block definitions are scanned to build parent-child relationships
5. `_classify_block_insertion_status()` helper function correctly classifies all block types
6. `all_block_definitions` is built after modelspace scan with accurate data
7. Return statement includes both new fields with proper type conversion
8. All tests in `test_extractor_nested.py` pass
9. `uv run mypy app/` passes with no errors
10. `uv run pytest app/tests/` passes with no failures

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to verify types are valid
- `uv run pytest app/tests/core/extractor/test_extractor_nested.py -v` - Run nested block tests
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- `uv run pytest app/tests/ -v` - Run full test suite for regression testing
- `uv run python -c "from core.extractor import extract_blocks; r = extract_blocks('app/tests/assets/nested_block_test.dxf'); print(f'Block definitions: {len(r[\"all_block_definitions\"])}')"` - Verify extraction works

## Notes
- The `_classify_block_insertion_status()` function is defined as a local function inside `extract_blocks()` to access the `anonymous_to_resolved` dictionary without passing it as a parameter
- `nested_block_parents` uses `set[str]` internally for efficient deduplication but is converted to `list[str]` in the return value for JSON compatibility
- Parent names lists are sorted alphabetically for consistent output
- The INSERT scanning happens during the FIRST pass through doc.blocks (where geometry analysis happens)
- The BlockDefinitionRecord building happens in a SECOND pass through doc.blocks AFTER modelspace scan completes
- System blocks are identified by their naming patterns: `*Model_Space`, `*Paper_Space*`, `*D#` (dimensions), `*X#` (hatches)
- The `block_is_nested` flag is True if the block appears as a child in ANY parent block's definition
