# Chore: Unit D - Shapely Constants and Final Validation

## Chore Description
This is the final unit of US-8: Shapely Geometry Refactor. The task focuses on updating the remaining threshold constant (`LINE_SEGMENT_THRESHOLD` from 200 to 5000), removing obsolete code (`CYCLE_DETECTION_TIMEOUT_SECONDS` which is no longer used after Unit B), updating test assets and test bounds to reflect the new thresholds, and running comprehensive validation to ensure zero regressions across all 484 tests.

The prior units (A, B, C) have successfully:
- Added Shapely imports and adapter functions (Unit A)
- Replaced DFS cycle detection with `polygonize()` - complexity improved from O(exponential) to O(n log n) (Unit B)
- Replaced manual net area calculation with Shapely's `difference()` - complexity improved from O(n^3) to O(n^2) (Unit C)
- Increased `POLYGON_COUNT_THRESHOLD` from 30 to 500 (Unit C)

With Shapely's efficient GEOS-based `polygonize()` algorithm, the `LINE_SEGMENT_THRESHOLD` can be safely raised from 200 to 5000, and the `CYCLE_DETECTION_TIMEOUT_SECONDS` constant is no longer needed since `polygonize()` completes in milliseconds even for thousands of segments.

## Relevant Files
Use these files to resolve the chore:

- `app/core/constants.py` - Contains `LINE_SEGMENT_THRESHOLD` (currently 200) that needs to be increased to 5000, and `CYCLE_DETECTION_TIMEOUT_SECONDS` (5.0) that should be removed. Also update the docstring comment explaining Shapely's performance improvements.

- `app/core/geometry.py` - Main geometry module with Shapely implementations from Units A, B, C. The docstring in `_detect_content_zone()` references `CYCLE_DETECTION_TIMEOUT_SECONDS` which needs to be updated since the timeout is no longer used.

- `app/tests/core/test_constants.py` - Contains tests for threshold bounds:
  - `test_line_threshold_reasonable()` - Currently asserts `50 <= LINE_SEGMENT_THRESHOLD <= 500`. Needs update for new bounds.
  - `test_timeout_reasonable()` - Tests `CYCLE_DETECTION_TIMEOUT_SECONDS`. Will need removal since constant is removed.
  - Imports `CYCLE_DETECTION_TIMEOUT_SECONDS` which will need removal.

- `app/tests/core/test_content_zone.py` - Contains threshold skip tests and imports both `LINE_SEGMENT_THRESHOLD` and `CYCLE_DETECTION_TIMEOUT_SECONDS`. Tests depend on specific line counts in test DXF files. The timeout constant usage needs removal.

- `app/tests/assets/create_many_lines_test.py` - Script that generates `many_lines_test.dxf` with blocks having specific line counts (200, 201). Need to regenerate with new threshold values (5000, 5001).

- `app/tests/assets/many_lines_test.dxf` - Test DXF file containing blocks: `EXACTLY_THRESHOLD` (200 lines) and `JUST_OVER_THRESHOLD` (201 lines). Must be regenerated with 5000/5001 line counts.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify Prerequisites
- Run `uv run pytest app/tests/ -q` to confirm all 484 tests pass before making changes
- Run `uv run mypy app/` to confirm type checking passes
- Run `uv run ruff check app/` to confirm linting passes

### Step 2: Update LINE_SEGMENT_THRESHOLD in constants.py
- In `app/core/constants.py`, change line 142:
  - From: `LINE_SEGMENT_THRESHOLD: int = 200`
  - To: `LINE_SEGMENT_THRESHOLD: int = 5000`
- Update the docstring (lines 143-145):
  ```python
  LINE_SEGMENT_THRESHOLD: int = 5000
  """Maximum LINE segments for cycle detection using Shapely polygonize.
  Blocks with more LINE segments skip LINE cycle extraction.
  Rationale: With Shapely's GEOS-based polygonize(), can handle 5000 segments
  efficiently (previously 200 with DFS-based cycle detection)."""
  ```

### Step 3: Remove CYCLE_DETECTION_TIMEOUT_SECONDS from constants.py
- In `app/core/constants.py`, remove lines 147-149:
  ```python
  CYCLE_DETECTION_TIMEOUT_SECONDS: float = 5.0
  """Safety timeout for cycle detection algorithm.
  Prevents indefinite hang even if threshold check is bypassed."""
  ```
- Update the comment on line 133-134 to reflect Shapely optimizations:
  ```python
  # Content Zone Detection Thresholds
  # Conservative limits for Shapely-based geometry operations
  ```

### Step 4: Update _detect_content_zone docstring in geometry.py
- In `app/core/geometry.py`, update the docstring in `_detect_content_zone()` function (lines 642-645):
  - From:
    ```
    Performance safeguards:
    - Skips LINE cycle detection if > LINE_SEGMENT_THRESHOLD segments
    - Skips net area calculation if > POLYGON_COUNT_THRESHOLD polygons
    - Times out cycle detection after CYCLE_DETECTION_TIMEOUT_SECONDS
    ```
  - To:
    ```
    Performance safeguards:
    - Skips LINE cycle detection if > LINE_SEGMENT_THRESHOLD segments (5000)
    - Skips net area calculation if > POLYGON_COUNT_THRESHOLD polygons (500)
    ```

### Step 5: Update test_constants.py
- In `app/tests/core/test_constants.py`:
  - Remove `CYCLE_DETECTION_TIMEOUT_SECONDS` from imports (line 10)
  - Update `test_line_threshold_reasonable()` (line 33-34):
    - From: `assert 50 <= LINE_SEGMENT_THRESHOLD <= 500`
    - To: `assert 1000 <= LINE_SEGMENT_THRESHOLD <= 10000`
  - Update the docstring to reflect Shapely:
    ```python
    def test_line_threshold_reasonable(self) -> None:
        """Threshold should be between 1000 and 10000.

        With Shapely's efficient GEOS-based polygonize(), the threshold can be
        much higher than the original DFS implementation. 5000 is conservative.
        """
        assert 1000 <= LINE_SEGMENT_THRESHOLD <= 10000
    ```
  - Remove `test_timeout_reasonable()` test method entirely (lines 36-38)

### Step 6: Update test_content_zone.py
- In `app/tests/core/test_content_zone.py`:
  - Remove `CYCLE_DETECTION_TIMEOUT_SECONDS` from imports (line 23)
  - Keep all existing test methods - they will work with updated threshold values
  - Note: The tests reference blocks in `many_lines_test.dxf` that have hardcoded line counts. These need to match the new threshold.

### Step 7: Update create_many_lines_test.py script
- In `app/tests/assets/create_many_lines_test.py`:
  - Update comment on line 5 to reflect new threshold:
    - From: `- MANY_LINES: 500+ LINE segments (grid pattern) to exceed LINE_SEGMENT_THRESHOLD`
    - To: `- MANY_LINES: 5500+ LINE segments (grid pattern) to exceed LINE_SEGMENT_THRESHOLD`
  - Update comment on line 16:
    - From: `# This exceeds LINE_SEGMENT_THRESHOLD (200) to test threshold skip`
    - To: `# This exceeds LINE_SEGMENT_THRESHOLD (5000) to test threshold skip`
  - Update `EXACTLY_THRESHOLD` block (lines 60-65):
    - From: 200 LINE segments
    - To: 5000 LINE segments
    ```python
    # Block 3: EXACTLY_THRESHOLD - Exactly 5000 LINE segments
    block_exact = doc.blocks.new(name="EXACTLY_THRESHOLD")
    for i in range(5000):
        x = (i % 100) * 10
        y = (i // 100) * 10
        block_exact.add_line((x, y), (x + 5, y))
    ```
  - Update `JUST_OVER_THRESHOLD` block (lines 67-72):
    - From: 201 LINE segments
    - To: 5001 LINE segments
    ```python
    # Block 4: JUST_OVER_THRESHOLD - 5001 LINE segments
    block_over = doc.blocks.new(name="JUST_OVER_THRESHOLD")
    for i in range(5001):
        x = (i % 100) * 10
        y = (i // 100) * 10
        block_over.add_line((x, y), (x + 5, y))
    ```
  - Update `MANY_LINES` block to have more than 5000 segments (increase grid_size or add more lines)

### Step 8: Regenerate many_lines_test.dxf
- Run the updated script to regenerate the test DXF file:
  - `uv run python app/tests/assets/create_many_lines_test.py`
- Verify the output shows correct line counts:
  - `MANY_LINES` > 5000
  - `FEW_LINES` < 5000
  - `EXACTLY_THRESHOLD` = 5000
  - `JUST_OVER_THRESHOLD` = 5001

### Step 9: Run Constants Tests
- Execute: `uv run pytest app/tests/core/test_constants.py -v`
- Verify all tests pass with new threshold bounds

### Step 10: Run Content Zone Tests
- Execute: `uv run pytest app/tests/core/test_content_zone.py -v`
- Verify threshold skip tests work correctly with new values
- Verify all 52+ content zone tests pass

### Step 11: Run Geometry Tests
- Execute: `uv run pytest app/tests/core/test_geometry.py -v`
- Verify all geometry tests pass (should be unaffected by threshold changes)

### Step 12: Run Full Test Suite
- Execute: `uv run pytest app/tests/ -v`
- All 484 tests must pass with zero failures
- Verify no regressions from threshold changes

### Step 13: Run Type Checker
- Execute: `uv run mypy app/`
- Must pass with no errors
- Verify removal of `CYCLE_DETECTION_TIMEOUT_SECONDS` doesn't break imports

### Step 14: Run Linter and Formatter
- Execute: `uv run ruff check app/`
- Execute: `uv run ruff format app/`
- Fix any issues reported

### Step 15: Verify All Acceptance Criteria
Confirm all US-8 acceptance criteria are met:
1. All 480+ existing tests pass with zero failures
2. Type checking passes with `uv run mypy app/`
3. Linting passes with `uv run ruff check app/`
4. `shapely>=2.0.0` added to dependencies (DONE - prior units)
5. `_extract_line_cycles()` uses `polygonize()` instead of DFS (DONE - Unit B)
6. `_calculate_net_areas()` uses Shapely difference operations (DONE - Unit C)
7. Basic geometry functions use Shapely equivalents (DONE - Unit A)
8. `LINE_SEGMENT_THRESHOLD` increased to 5000 (this unit)
9. `POLYGON_COUNT_THRESHOLD` increased to 500 (DONE - Unit C)
10. No behavioral changes - same trim values for same inputs

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to verify threshold bounds
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests including threshold skip tests
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests (should be unaffected)
- `uv run pytest app/tests/ -v` - Run full test suite (484 tests expected)
- `uv run mypy app/` - Run type checker to verify no import errors
- `uv run ruff check app/` - Run linter to verify code quality
- `uv run ruff format --check app/` - Verify formatting is correct

## Notes
- **Test DXF Regeneration Required**: The `many_lines_test.dxf` file must be regenerated after updating `create_many_lines_test.py` because the tests assert exact line counts that match the threshold values.

- **CYCLE_DETECTION_TIMEOUT_SECONDS Removal**: This constant was used for safety timeout in the old DFS-based cycle detection. With Shapely's `polygonize()`, timeouts are unnecessary since the algorithm completes in milliseconds even for thousands of segments.

- **Backwards Compatibility**: The increased threshold (200 -> 5000) means more complex blocks will now have content zone detection run instead of being skipped. This is the desired behavior and should not cause regressions.

- **Performance Verification**: While formal benchmarks are not required, the tests should complete in reasonable time. If any test takes unusually long, it may indicate an issue with the Shapely implementation.

- **Unit D Completes US-8**: After this unit, the Shapely Geometry Refactor feature is complete. All custom geometry algorithms have been replaced with Shapely equivalents, and thresholds have been raised to take advantage of the improved performance.
