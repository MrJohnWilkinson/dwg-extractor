# Chore: Remove BlockAnalysisResult + Update Tests + Archive (Phases A4-A6)

## Chore Description

This specification covers the cleanup work following the removal of parallel processing from `app/core/extractor.py` (completed in Unit 1). It encompasses phases A4-A6 of the combined implementation plan (064-combined-gui-settings-and-parallel-removal-plan.md):

- **A4**: Remove the now-unused `BlockAnalysisResult` TypedDict from `app/core/types.py`
- **A5**: Update test file `test_extractor_parallel.py` - rename to `test_extractor_consistency.py`, remove thread-specific tests, update docstrings to remove parallel processing references
- **A6**: Archive the original parallel processing spec to `specs/archive/`

**Scope:** A4-A6 only (cleanup after parallel processing removal)

**Prerequisite:** Unit 1 (A1-A3) must be completed - parallel processing removed from extractor.py, all 857 tests passing.

**Implementation Learnings from Unit 1:**
- Removed 92 lines of code from extractor.py
- Removed ThreadPoolExecutor, as_completed imports
- Deleted `_analyze_single_block()` function (104 lines)
- Replaced parallel block with sequential for-loop in `extract_blocks()`
- `BlockAnalysisResult` import was already removed from extractor.py
- All tests passing with sequential processing

## Relevant Files

Use these files to resolve the chore:

- `app/core/types.py` - Contains the `BlockAnalysisResult` TypedDict (lines 274-291) that needs to be deleted. This TypedDict was created specifically for parallel processing and is no longer used anywhere in the codebase.

- `app/tests/core/extractor/test_extractor_parallel.py` - Contains tests for parallel block processing. Needs to be renamed to `test_extractor_consistency.py` and updated to remove thread-specific tests while keeping result consistency tests.

- `specs/058-unit-3-parallel-block-processing.md` - Original spec for parallel block processing feature. Needs to be archived since the feature has been removed.

- `ai_output/064-combined-gui-settings-and-parallel-removal-plan.md` - Reference document containing the combined implementation plan with phases A4-A6 details.

### New Files/Directories

- `specs/archive/` - Directory to create for archiving old specs (if it doesn't exist)
- `app/tests/core/extractor/test_extractor_consistency.py` - Renamed test file (from `test_extractor_parallel.py`)

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify BlockAnalysisResult is Not Used

Before deleting, confirm `BlockAnalysisResult` has no remaining usages in the codebase:

```bash
uv run grep -r "BlockAnalysisResult" app/
```

Expected result: No matches in `app/core/extractor.py` (import was removed in Unit 1). The only match should be in `app/core/types.py` where it's defined.

### Step 2: Delete BlockAnalysisResult TypedDict from types.py (A4)

Open `app/core/types.py` and delete lines 274-291 (the entire `BlockAnalysisResult` class):

**Code to delete:**
```python
class BlockAnalysisResult(TypedDict):
    """
    Result from analyzing a single block definition for parallel processing.

    Contains all data extracted from a block that will be stored in result dictionaries.

    Attributes:
        entity_count: Number of entities in the block definition
        trimming_data: Block geometry analysis data (native dimensions and segments)
        content_zone_data: Content zone detection results
        nested_inserts: List of block names inserted within this block
    """

    entity_count: int
    trimming_data: BlockTrimmingData
    content_zone_data: ContentZoneData
    nested_inserts: list[str]
```

Also delete the blank line (line 273) before the class to maintain proper spacing.

**After deletion:** The file should end at line 272 with `block_entity_count: int` followed by a single trailing newline.

### Step 3: Validate types.py Changes

Run type checking on types.py to ensure no errors:

```bash
uv run mypy app/core/types.py
```

Expected: Success with no errors.

### Step 4: Rename Test File (A5 - Part 1)

Rename the parallel processing test file to reflect its new purpose (consistency testing):

```bash
git mv app/tests/core/extractor/test_extractor_parallel.py app/tests/core/extractor/test_extractor_consistency.py
```

### Step 5: Update Test File Content (A5 - Part 2)

Open `app/tests/core/extractor/test_extractor_consistency.py` and make the following changes:

#### 5a. Update Module Docstring

**Replace the module docstring (lines 1-10):**

```python
"""
Unit tests for the extractor module - result consistency verification.

This test suite validates that extraction produces consistent, correct results:
- Result consistency (identical results across multiple runs)
- Abort functionality
- Dynamic block resolution
- Nested block tracking
- Edge case handling
"""
```

#### 5b. Remove Unused Imports

**Remove the `threading` import if not needed by remaining tests.** After removing `test_multiple_concurrent_extractions`, the only threading usage is for abort tests which still need it. Keep the import.

#### 5c. Rename TestParallelBlockProcessing Class

**Change class name and docstring:**

```python
class TestExtractionConsistency:
    """Test suite for extraction result consistency."""
```

#### 5d. Rename and Update Test Methods in TestExtractionConsistency

Update the test method names and docstrings to remove "parallel" references:

| Old Name | New Name |
|----------|----------|
| `test_parallel_processing_consistent_results` | `test_consistent_results` |
| `test_parallel_processing_with_dynamic_blocks` | `test_with_dynamic_blocks` |
| `test_parallel_processing_with_nested_blocks` | `test_with_nested_blocks` |
| `test_parallel_processing_abort_event` | `test_abort_event` |
| `test_parallel_processing_abort_event_not_set` | `test_abort_event_not_set` |
| `test_parallel_processing_empty_file` | `test_empty_file` |
| `test_parallel_processing_block_trimming_data` | `test_block_trimming_data` |
| `test_parallel_processing_content_zone_data` | `test_content_zone_data` |
| `test_parallel_processing_preserves_entity_counts` | `test_preserves_entity_counts` |

**Update docstrings to remove "parallel processing" references:**

- `test_consistent_results`: "Test that extraction produces consistent results across multiple runs."
- `test_with_dynamic_blocks`: "Test extraction correctly resolves dynamic blocks."
- `test_with_nested_blocks`: "Test extraction correctly identifies nested block relationships."
- `test_abort_event`: "Test that abort event works correctly during extraction."
- `test_abort_event_not_set`: "Test extraction completes when abort event is not set."
- `test_empty_file`: "Test extraction handles empty files correctly."
- `test_block_trimming_data`: "Test that block trimming data is correctly populated."
- `test_content_zone_data`: "Test that content zone data is correctly populated."
- `test_preserves_entity_counts`: "Test that entity counts match expected values after extraction."

#### 5e. Update TestParallelProcessingThreadSafety Class

**Rename class and update docstring:**

```python
class TestExtractionResultIntegrity:
    """Test suite for extraction result data integrity."""
```

#### 5f. Delete test_multiple_concurrent_extractions Method

**Delete the entire `test_multiple_concurrent_extractions` method (lines 133-155 in original file):**

This test was specifically for verifying thread safety of concurrent parallel extractions and is no longer relevant.

```python
# DELETE THIS ENTIRE METHOD:
def test_multiple_concurrent_extractions(self) -> None:
    """Test that multiple concurrent extractions don't interfere."""
    import concurrent.futures

    from core.extractor import ExtractionResult

    def run_extraction(file_path: str) -> ExtractionResult:
        return extract_blocks(file_path)

    # Run multiple extractions concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(run_extraction, "app/tests/assets/sample_drawing.dxf"),
            executor.submit(run_extraction, "app/tests/assets/sample_drawing.dxf"),
            executor.submit(run_extraction, "app/tests/assets/sample_drawing.dxf"),
        ]

        results = [f.result() for f in futures]

    # All results should be identical
    for i in range(1, len(results)):
        assert results[0]["block_counts"] == results[i]["block_counts"]
```

#### 5g. Rename Remaining Methods in TestExtractionResultIntegrity

| Old Name | New Name |
|----------|----------|
| `test_no_race_conditions_in_result_collection` | `test_result_collection_consistency` |
| `test_nested_block_parents_thread_safety` | `test_nested_block_parents_structure` |

**Update docstrings:**

- `test_result_collection_consistency`: "Test that result collection is internally consistent."
- `test_nested_block_parents_structure`: "Test that nested_block_parents dictionary is built correctly."

### Step 6: Create Archive Directory and Move Spec (A6)

Create the archive directory and move the original parallel processing spec:

```bash
mkdir -p specs/archive
git mv specs/058-unit-3-parallel-block-processing.md specs/archive/
```

### Step 7: Run Validation Commands

Execute all validation commands to ensure the changes are correct.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/core/types.py` - Type check types.py to ensure BlockAnalysisResult removal causes no errors
- `uv run mypy app/` - Full type check to catch any cascading issues from types.py changes
- `uv run ruff check app/core/types.py` - Lint types.py for code quality issues
- `uv run ruff check app/tests/core/extractor/test_extractor_consistency.py` - Lint renamed test file
- `uv run ruff format app/core/types.py --check` - Verify types.py formatting
- `uv run ruff format app/tests/core/extractor/test_extractor_consistency.py --check` - Verify test file formatting
- `uv run pytest app/tests/core/extractor/test_extractor_consistency.py -v` - Run renamed test file to verify all tests pass
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests to verify no regressions
- `uv run pytest app/tests/ -v` - Run full test suite (should be 857 tests, all passing)
- `test -d specs/archive && test -f specs/archive/058-unit-3-parallel-block-processing.md && echo "Archive successful"` - Verify spec was archived correctly
- `test ! -f specs/058-unit-3-parallel-block-processing.md && echo "Original spec removed"` - Verify original spec no longer exists in specs/
- `test ! -f app/tests/core/extractor/test_extractor_parallel.py && echo "Old test file removed"` - Verify old test file no longer exists

## Notes

1. **Order of operations matters** - Delete types.py content first, then update tests, then archive spec. This ensures type checking validates correctly at each step.

2. **Git mv for file operations** - Use `git mv` instead of `mv` to preserve git history for renamed/moved files.

3. **Test count should remain the same** - After removing `test_multiple_concurrent_extractions`, there will be one fewer test method. However, this test was specifically for parallel thread safety and is no longer meaningful. The remaining tests verify functional correctness.

4. **No behavior change expected** - All remaining tests should pass unchanged because:
   - `test_consistent_results` verifies the extraction loop produces identical results (still valid for sequential)
   - Abort tests verify abort_event functionality (still works with sequential processing)
   - Data structure tests verify output format (unchanged by sequential processing)

5. **Reference documents:**
   - Combined implementation plan: `ai_output/064-combined-gui-settings-and-parallel-removal-plan.md`
   - Unit 1 spec (completed): `specs/065-unit-1-remove-parallel-processing.md`

6. **Lines of code impact:**
   - types.py: -18 lines (BlockAnalysisResult TypedDict)
   - test file: -23 lines (test_multiple_concurrent_extractions method)
   - Net reduction: ~41 lines

7. **After this unit completes:**
   - `BlockAnalysisResult` TypedDict no longer exists
   - Test file renamed to `test_extractor_consistency.py`
   - All parallel processing references removed from test docstrings
   - Original parallel spec archived to `specs/archive/`
   - Ready for Phase B (GUI Settings Infrastructure) of the combined plan
