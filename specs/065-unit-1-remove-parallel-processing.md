# Chore: Remove Parallel Processing from extractor.py (Phases A1-A3)

## Chore Description

This specification covers the removal of parallel processing from `app/core/extractor.py` as phases A1-A3 of the combined implementation plan (064-combined-gui-settings-and-parallel-removal-plan.md). The parallel processing was added for performance but introduces thread safety complexity that outweighs the benefits. This unit simplifies the codebase by reverting to sequential block analysis.

**Scope:** A1-A3 only (parallel processing removal from extractor.py)
- A1: Remove parallel imports (`concurrent.futures`)
- A2: Delete `_analyze_single_block()` function
- A3: Replace ThreadPoolExecutor block with sequential processing loop

**Out of Scope (handled in later units):**
- A4: Remove `BlockAnalysisResult` TypedDict from types.py
- A5: Update test file `test_extractor_parallel.py`
- A6: Archive parallel spec

## Relevant Files

Use these files to resolve the chore:

- `app/core/extractor.py` - Main file to modify. Contains:
  - Line 16: Import of `concurrent.futures` (to delete)
  - Line 42: Import of `BlockAnalysisResult` (to delete - no longer used after A2)
  - Lines 879-982: `_analyze_single_block()` function (to delete entirely)
  - Lines 1299-1354: Phase 2 ThreadPoolExecutor block (to replace with sequential loop)

- `ai_output/064-combined-gui-settings-and-parallel-removal-plan.md` - Reference plan containing the sequential loop replacement code

## Step by Step Tasks

### Step 1: Remove Parallel Import (A1)

Delete the `concurrent.futures` import from line 16:

**Current code (line 16):**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```

**Action:** Delete this entire line.

### Step 2: Remove BlockAnalysisResult Import

Since `_analyze_single_block()` is being deleted and it's the only user of `BlockAnalysisResult`, remove the import:

**Current code (lines 40-51):**
```python
from .types import (
    AnnotationKey,
    BlockAnalysisResult,
    BlockDefinitionRecord,
    ...
)
```

**Action:** Remove `BlockAnalysisResult,` from the import list (line 42).

### Step 3: Delete _analyze_single_block Function (A2)

Delete the entire `_analyze_single_block()` function spanning lines 879-982 (104 lines total).

**Location:** Lines 879-982 in `app/core/extractor.py`

**Action:** Delete the entire function including:
- Function signature and docstring (lines 879-909)
- Block skipping logic (lines 910-934)
- Entity counting (lines 936-937)
- Nested INSERT scanning (lines 939-946)
- Block geometry analysis (lines 948-962)
- Content zone detection (lines 964-973)
- Result construction and return (lines 975-982)

### Step 4: Replace Phase 2 with Sequential Loop (A3)

Replace the ThreadPoolExecutor block (lines 1299-1354) with a sequential processing loop.

**Current code to delete (lines 1299-1354):**
```python
        # PHASE 2: Parallel block geometry analysis
        block_defs_list = list(doc.blocks)
        max_workers = min(
            8, max(1, len(block_defs_list))
        )  # Cap at 8 threads, minimum 1

        logger.info(
            f"Starting parallel analysis of {len(block_defs_list)} block definitions with {max_workers} workers"
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    _analyze_single_block,
                    block_def,
                    doc,
                    anonymous_to_resolved,
                    abort_event,
                    precision_tolerance,
                    gap_bridge_tolerance,
                    min_area,
                    min_side,
                ): block_def.name
                for block_def in block_defs_list
            }

            for future in as_completed(futures):
                block_name = futures[future]
                try:
                    effective_name, analysis_result = future.result()
                    if effective_name is None or analysis_result is None:
                        continue

                    # Store results (thread-safe: each key is unique)
                    block_entities[effective_name] = analysis_result["entity_count"]
                    block_trimming_data[effective_name] = analysis_result[
                        "trimming_data"
                    ]
                    block_content_zone_data[effective_name] = analysis_result[
                        "content_zone_data"
                    ]

                    # Track nested relationships
                    for nested_name in analysis_result["nested_inserts"]:
                        if nested_name not in nested_block_parents:
                            nested_block_parents[nested_name] = set()
                        nested_block_parents[nested_name].add(effective_name)

                except Exception as e:
                    logger.warning(f"Error analyzing block {block_name}: {e}")
                    continue

        logger.info(f"Analyzed {len(block_entities)} block definitions")
        logger.info(
            f"Analyzed geometry for {len(block_trimming_data)} block definitions"
        )
```

**Replacement code:**
```python
        # PHASE 2: Sequential block geometry analysis
        for block_def in doc.blocks:
            block_name = block_def.name

            # Skip modelspace/paperspace blocks
            if block_name in ("*Model_Space", "*Paper_Space") or block_name.startswith(
                "*Paper_Space"
            ):
                continue

            # Handle anonymous blocks starting with *U (dynamic block instances)
            if block_name.startswith("*U"):
                if block_name in anonymous_to_resolved:
                    effective_name = anonymous_to_resolved[block_name]
                else:
                    continue  # Skip unresolved *U blocks
            elif block_name.startswith("A$C"):
                if block_name in anonymous_to_resolved:
                    effective_name = anonymous_to_resolved[block_name]
                else:
                    effective_name = block_name
            elif block_name.startswith("*"):
                continue  # Skip other system blocks
            else:
                effective_name = block_name

            # Count entities
            entity_count = sum(1 for _ in block_def)
            block_entities[effective_name] = entity_count

            # Scan for nested INSERTs
            for entity in block_def:
                if entity.dxftype() == "INSERT":
                    nested_name = entity.dxf.name
                    if nested_name in anonymous_to_resolved:
                        nested_name = anonymous_to_resolved[nested_name]
                    if nested_name not in nested_block_parents:
                        nested_block_parents[nested_name] = set()
                    nested_block_parents[nested_name].add(effective_name)

            # Analyze block geometry
            bbox = _get_block_bounding_box(block_def)
            native_width = round(bbox[2] - bbox[0], 2)
            native_height = round(bbox[3] - bbox[1], 2)

            vertical_points, horizontal_points = _get_intersection_points(block_def)
            vertical_segments = _calculate_segments(vertical_points)
            horizontal_segments = _calculate_segments(horizontal_points)

            block_trimming_data[effective_name] = {
                "native_width": native_width,
                "native_height": native_height,
                "vertical_segments": vertical_segments,
                "horizontal_segments": horizontal_segments,
            }

            # Detect content zone
            content_zone = _detect_content_zone(
                block_def,
                bbox,
                abort_event,
                precision_tolerance,
                gap_bridge_tolerance,
                min_area,
                min_side,
            )
            block_content_zone_data[effective_name] = content_zone

        logger.info(f"Analyzed {len(block_entities)} block definitions")
        logger.info(f"Analyzed geometry for {len(block_trimming_data)} block definitions")
```

**Key changes in the replacement:**
1. Removed `block_defs_list = list(doc.blocks)` - iterate directly
2. Removed `max_workers` calculation
3. Removed `ThreadPoolExecutor` context manager
4. Removed `futures` dictionary and `as_completed()` iterator
5. Removed `future.result()` exception handling wrapper
6. Updated logging messages to remove "parallel" and "workers" references
7. Inlined all block analysis logic from `_analyze_single_block()` into the loop
8. Store results directly instead of through `analysis_result` dict
9. Changed nested INSERT tracking to use `set()` directly (matching existing data structure)

### Step 5: Run Validation Commands

Execute all validation commands to ensure the changes are correct.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/core/extractor.py` - Type check extractor.py to ensure no type errors after removing parallel processing
- `uv run mypy app/` - Full type check to catch any cascading issues
- `uv run ruff check app/core/extractor.py` - Lint extractor.py for code quality issues
- `uv run ruff format app/core/extractor.py --check` - Verify formatting is correct
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests to verify sequential processing produces identical results
- `uv run pytest app/tests/ -v` - Run full test suite to catch any regressions

## Notes

1. **Line numbers may shift** - After deleting the import (Step 1) and `_analyze_single_block()` function (Step 3), subsequent line numbers will change. The implementation should:
   - First remove the concurrent.futures import (line 16)
   - Then remove BlockAnalysisResult from imports (around line 42)
   - Then delete `_analyze_single_block()` function
   - Finally replace the Phase 2 block

2. **BlockAnalysisResult import removal** - Although A4 (removing the TypedDict from types.py) is out of scope, we MUST remove the import from extractor.py in this unit because `_analyze_single_block()` is the only code using it. If we don't remove the import, mypy will report an "imported but unused" error.

3. **No behavior change expected** - The sequential loop should produce exactly the same results as the parallel version. All existing tests should pass without modification.

4. **Thread safety simplified** - After this change:
   - No `concurrent.futures` dependency
   - No thread pool management
   - No future result handling
   - Simpler error handling (no need to wrap in try/except for future.result())

5. **Net code reduction** - Approximately 60 lines removed:
   - 1 line: concurrent.futures import
   - 1 line: BlockAnalysisResult import
   - 104 lines: _analyze_single_block() function
   - ~55 lines: ThreadPoolExecutor block
   - +67 lines: Sequential loop replacement
   - Net: ~94 lines removed

6. **Reference document** - Full context available in `ai_output/064-combined-gui-settings-and-parallel-removal-plan.md`
