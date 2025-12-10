# Feature: Extract Blocks Signature Update and Integration Tests - Unit 3

## Feature Description
This feature completes the precision tolerance GUI implementation by updating the `extract_blocks()` function signature to accept a `precision_fix_amount` parameter, passing this parameter through to `get_snap_tolerances()`, and updating the GUI extraction worker to pass the user-specified precision fix amount from the entry field. Additionally, it adds comprehensive tests to verify the end-to-end integration of the precision fix amount from GUI entry field to polygon detection tolerance.

This is Unit 3 of the Precision Tolerance GUI Implementation, building on:
- Unit 1 (spec 034): Backend constants and `get_snap_tolerances()` with `precision_fix_amount` parameter
- Unit 2 (spec 035): GUI layout restructuring and `_get_precision_fix_amount()` method

## User Story
As a CAD engineer using the DXF Block Extractor
I want my custom precision fix amount settings to be applied during extraction
So that I can fine-tune the coordinate snapping tolerance to match my specific drawing's precision requirements

## Problem Statement
Currently, the GUI has the precision fix amount entry field and the `_get_precision_fix_amount()` getter method (from Unit 2), and `get_snap_tolerances()` accepts the `precision_fix_amount` parameter (from Unit 1). However:
1. The `extract_blocks()` function does not accept `precision_fix_amount` in its signature
2. The GUI extraction worker does not pass the precision fix amount to `extract_blocks()`
3. The `get_snap_tolerances()` call inside `extract_blocks()` does not receive the precision fix amount

This means users can enter a custom precision fix amount in the GUI, but it is never actually used during extraction.

## Solution Statement
1. Add `precision_fix_amount: float | None = None` parameter to `extract_blocks()` function signature
2. Pass `precision_fix_amount` through to `get_snap_tolerances()` call inside `extract_blocks()`
3. Update `_extraction_worker()` in main.py to pass `precision_fix_amount=self._get_precision_fix_amount()` to `extract_blocks()`
4. Add comprehensive tests to verify the integration works correctly
5. Update extraction logging to include the precision fix amount value

## Relevant Files
Use these files to implement the feature:

- **app/core/extractor.py** - Contains `extract_blocks()` function
  - Add `precision_fix_amount: float | None = None` parameter to function signature
  - Update docstring to document the new parameter
  - Pass `precision_fix_amount` to `get_snap_tolerances()` call
  - Update logging to show precision fix amount value

- **app/main.py** - Contains GUI application and `_extraction_worker()` method
  - Update `_extraction_worker()` to pass `precision_fix_amount=self._get_precision_fix_amount()` to `extract_blocks()`
  - Update extraction logging to include precision fix amount

- **app/tests/core/extractor/test_extractor_precision_fix.py** - Tests for precision fix functionality
  - Add tests for `extract_blocks()` accepting `precision_fix_amount` parameter
  - Add tests for custom amount being passed through correctly
  - Add tests for integration with other extraction parameters

- **app/tests/core/test_constants.py** - Tests for constants module (read-only reference)
  - Already contains tests for `DEFAULT_PRECISION_FIX_TOLERANCE`, `PRECISION_FIX_MIN`, `PRECISION_FIX_MAX`
  - No changes needed, but reference for test patterns

### New Files
None - all changes are to existing files.

## Implementation Plan
### Phase 1: Foundation
Update `extract_blocks()` function signature to accept the new `precision_fix_amount` parameter. This is a non-breaking change since the parameter has a default value of None.

### Phase 2: Core Implementation
1. Pass the `precision_fix_amount` parameter through to `get_snap_tolerances()` inside `extract_blocks()`
2. Update logging to show the precision fix amount value in extraction output
3. Update `_extraction_worker()` in main.py to pass the GUI value to `extract_blocks()`

### Phase 3: Integration
Add comprehensive tests to verify:
1. `extract_blocks()` accepts and passes through `precision_fix_amount`
2. Custom amounts are used for polygon detection tolerance
3. Integration with existing extraction parameters works correctly
4. Backward compatibility is maintained (calling without the parameter still works)

## Step by Step Tasks

### Step 1: Update extract_blocks() Function Signature
- Open `app/core/extractor.py`
- Add `precision_fix_amount: float | None = None` parameter to `extract_blocks()` function signature after `precision_fix_enabled`
- The new signature should be:
  ```python
  def extract_blocks(
      file_path: str,
      abort_event: threading.Event | None = None,
      unit_override: int | None = None,
      gap_bridge_enabled: bool = False,
      gap_bridge_amount: float | None = None,
      precision_fix_enabled: bool = True,
      precision_fix_amount: float | None = None,  # NEW PARAMETER
  ) -> ExtractionResult:
  ```

### Step 2: Update extract_blocks() Docstring
- Update the docstring to document the new `precision_fix_amount` parameter:
  ```python
  precision_fix_amount: Custom precision fix amount. If provided and > 0,
                        this value is used instead of the default tolerance
                        for the unit. If None, 0, or negative, uses the
                        default from DEFAULT_PRECISION_FIX_TOLERANCE.
                        Defaults to None.
  ```
- Add example usage in docstring Examples section

### Step 3: Pass precision_fix_amount to get_snap_tolerances()
- Update the `get_snap_tolerances()` call inside `extract_blocks()` to include `precision_fix_amount`:
  ```python
  precision_tolerance, gap_bridge_tolerance = get_snap_tolerances(
      detected_units,
      unit_override,
      gap_bridge_enabled,
      gap_bridge_amount,
      precision_fix_enabled,
      precision_fix_amount,  # NEW
  )
  ```

### Step 4: Update Extraction Logging in extractor.py
- Update the logging statement after `get_snap_tolerances()` to include precision fix amount:
  ```python
  logger.info(
      f"Using tolerances: precision={precision_tolerance}, "
      f"gap_bridge={gap_bridge_tolerance} "
      f"(units={'auto' if unit_override in (None, -1) else unit_override}, "
      f"precision_fix={'enabled' if precision_fix_enabled else 'disabled'}, "
      f"precision_fix_amount={precision_fix_amount})"
  )
  ```

### Step 5: Update _extraction_worker() in main.py
- Open `app/main.py`
- In `_extraction_worker()` method, update the `extract_blocks()` call to pass the precision fix amount:
  ```python
  extraction_result = extract_blocks(
      self.selected_file_path,
      self.abort_event,
      unit_override=unit_override,
      gap_bridge_enabled=gap_bridge_enabled,
      gap_bridge_amount=gap_bridge_amount,
      precision_fix_enabled=precision_fix_enabled,
      precision_fix_amount=self._get_precision_fix_amount(),  # NEW
  )
  ```

### Step 6: Update Extraction Logging in main.py
- Update the logging statement before extraction to include precision fix amount:
  ```python
  precision_fix_amount = self._get_precision_fix_amount()
  self.logger.info(
      f"Extraction settings: unit_override={unit_override}, "
      f"gap_bridge_enabled={gap_bridge_enabled}, "
      f"gap_bridge_amount={gap_bridge_amount}, "
      f"precision_fix_enabled={precision_fix_enabled}, "
      f"precision_fix_amount={precision_fix_amount}"
  )
  ```
- Note: Get the precision fix amount value once and reuse it for both logging and the extract_blocks call

### Step 7: Add Tests for extract_blocks() precision_fix_amount Parameter
- Open `app/tests/core/extractor/test_extractor_precision_fix.py`
- Add new test class `TestExtractBlocksPrecisionFixAmount` with the following tests:
  - `test_extract_blocks_accepts_precision_fix_amount_parameter` - Verify function accepts the parameter
  - `test_extract_blocks_with_custom_precision_fix_amount` - Verify custom amount is accepted
  - `test_extract_blocks_with_precision_fix_amount_none` - Verify None uses default
  - `test_extract_blocks_with_precision_fix_amount_zero` - Verify 0 uses default
  - `test_extract_blocks_with_all_tolerance_parameters` - Verify all parameters work together

### Step 8: Add Integration Tests for Precision Fix Amount
- Add test class `TestPrecisionFixAmountIntegration` with the following tests:
  - `test_precision_fix_amount_with_unit_override` - Verify custom amount works with unit override
  - `test_precision_fix_amount_with_gap_bridge` - Verify custom amount works with gap bridging
  - `test_precision_fix_amount_disabled_ignores_amount` - Verify disabled flag overrides amount
  - `test_precision_fix_amount_backward_compatibility` - Verify calling without amount still works

### Step 9: Run Type Checking
- Run `uv run mypy app/` to verify type hints are correct
- Fix any type errors if present

### Step 10: Run Linting
- Run `uv run ruff check app/` to verify code style compliance
- Run `uv run ruff format app/` if formatting is needed

### Step 11: Run Validation Commands
- Run `uv run pytest app/tests/core/extractor/test_extractor_precision_fix.py -v` to validate new tests pass
- Run `uv run pytest app/tests/core/test_constants.py -v` to validate constants tests still pass
- Run `uv run pytest app/tests/ -v` to ensure zero regressions across all tests

## Testing Strategy

### Unit Tests
1. **extract_blocks() Parameter Tests**:
   - Function accepts `precision_fix_amount` parameter without error
   - Function returns valid ExtractionResult with custom amount
   - Function returns valid ExtractionResult with amount=None (default)
   - Function returns valid ExtractionResult with amount=0 (use default)

2. **Integration with Existing Parameters**:
   - Custom amount works correctly with `unit_override` parameter
   - Custom amount works correctly with `gap_bridge_enabled` and `gap_bridge_amount`
   - `precision_fix_enabled=False` overrides any specified amount (returns 0.0 tolerance)
   - All parameters together produce expected results

### Integration Tests
1. **End-to-End Extraction**:
   - Verify extraction with custom precision amount produces valid results
   - Verify extraction with default precision amount produces valid results
   - Verify content zone detection uses the correct tolerance

2. **Backward Compatibility**:
   - Verify calling `extract_blocks()` without `precision_fix_amount` still works
   - Verify existing tests pass without modification

### Edge Cases
1. `precision_fix_amount = 0.0` - should use default tolerance
2. `precision_fix_amount = -1.0` - should use default tolerance
3. `precision_fix_amount = None` - should use default tolerance
4. `precision_fix_amount` with very small value (e.g., 1e-9) - should work correctly
5. `precision_fix_amount` with large value (e.g., 5.0) - should work correctly
6. `precision_fix_enabled = False` with `precision_fix_amount = 0.05` - should use 0.0 tolerance
7. Unknown unit code with custom `precision_fix_amount` - should use custom amount

### Playwright MCP Tests
Not applicable for this unit - GUI testing in WSL is unreliable per README. The GUI integration is validated through:
1. Type checking ensures the call signature is correct
2. The `_get_precision_fix_amount()` method was already implemented in Unit 2
3. Manual testing can verify the GUI passes values correctly

## Acceptance Criteria
1. `extract_blocks()` function signature includes `precision_fix_amount: float | None = None` parameter
2. `extract_blocks()` docstring documents the new parameter with examples
3. `get_snap_tolerances()` inside `extract_blocks()` receives the `precision_fix_amount` value
4. `_extraction_worker()` in main.py passes `precision_fix_amount=self._get_precision_fix_amount()` to `extract_blocks()`
5. Extraction logging shows the precision fix amount value
6. All new tests pass
7. All existing tests pass (backward compatibility)
8. Type checking passes with `uv run mypy app/`
9. Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting
- `uv run pytest app/tests/core/extractor/test_extractor_precision_fix.py -v` - Run precision fix tests
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to ensure no regressions
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions

## Notes
- This unit completes the Precision Tolerance GUI Implementation by connecting the GUI entry field value to the actual extraction process
- The implementation follows the exact pattern already established for `gap_bridge_amount` parameter, ensuring consistency
- After this unit, users will be able to:
  1. Enter a custom precision fix amount in the GUI entry field
  2. Have that amount validated by `_get_precision_fix_amount()` (range 0.0 to 10.0)
  3. Have the value passed to `extract_blocks()` and then to `get_snap_tolerances()`
  4. Have the custom tolerance applied during polygon detection for content zone calculation
- The `_get_precision_fix_amount()` method returns None when:
  - Precision fix checkbox is unchecked
  - Entry field value is not a valid float
  - Value is outside the range [PRECISION_FIX_MIN, PRECISION_FIX_MAX]
- When `_get_precision_fix_amount()` returns None, `get_snap_tolerances()` uses the default tolerance from `DEFAULT_PRECISION_FIX_TOLERANCE`

### Dependencies on Previous Units
This unit depends on:
- **Unit 1 (spec 034)**: `get_snap_tolerances()` already accepts `precision_fix_amount` parameter
- **Unit 2 (spec 035)**: `_get_precision_fix_amount()` method already exists in main.py

### Code Flow After Implementation
```
GUI Entry Field (precision_fix_amount_var)
        |
        v
_get_precision_fix_amount() -> float | None
        |
        v
_extraction_worker()
        |
        v
extract_blocks(..., precision_fix_amount=value)  <- Unit 3 adds this
        |
        v
get_snap_tolerances(..., precision_fix_amount=value)  <- Unit 3 connects this
        |
        v
_detect_content_zone(precision_tolerance, gap_bridge_tolerance)
        |
        v
_extract_paint_bucket_regions(precision_tolerance, gap_bridge_tolerance)
        |
        v
_snap_linestring_coords(precision_tolerance)  <- Custom tolerance applied here
```
