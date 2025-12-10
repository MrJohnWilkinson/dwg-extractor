# Feature: Two-Stage Snapping Test Suite Completion (Group E - Units 9-10)

## Feature Description
Complete the test suite for the two-stage snapping implementation by adding comprehensive tests that verify the snapping behavior works correctly. This includes tests for Stage 1 precision snapping (fixing nanometer-scale floating-point artifacts), Stage 2 gap bridging (user-controlled bridging of intentional design gaps), and unit-to-tolerance constant mappings.

Prior groups have already added some tests. This spec identifies and adds any missing tests to ensure complete coverage of all snapping behaviors documented in the implementation plan.

## User Story
As a developer maintaining the DXF Block Extractor
I want comprehensive tests for the two-stage snapping feature
So that I can confidently make changes knowing the snapping behavior is correctly verified

## Problem Statement
The two-stage snapping implementation (Groups A-D) has been completed, but the test suite needs verification to ensure all critical snapping behaviors are tested. Specifically:
1. The raw Shapely snap behavior for nanometer gaps needs explicit testing
2. Unit-to-tolerance constant mappings need direct verification tests
3. Gap bridging of larger gaps needs Shapely-level validation

## Solution Statement
Add missing tests to `test_geometry.py` and verify completeness of `test_extractor_units.py`. The tests will directly validate the Shapely snap operations and constant mappings as specified in the implementation plan (Units 9-10).

## Relevant Files
Use these files to implement the feature:

- `app/tests/core/test_geometry.py` - Main file for geometry-related tests including snapping behavior. Already contains `TestPrecisionSnapping`, `TestGapBridging`, and `TestTolerancePropagation` classes but needs additional tests from the implementation plan.
- `app/tests/core/extractor/test_extractor_units.py` - Already contains comprehensive tests for `_get_drawing_units()` and `get_snap_tolerances()`. Verify completeness.
- `app/tests/core/test_constants.py` - Contains tests for constants including tolerance ranges. May need additional unit-to-tolerance mapping tests.
- `app/core/constants.py` - Contains the tolerance constants being tested (PRECISION_SNAP_TOLERANCE, DEFAULT_GAP_BRIDGE_TOLERANCE).
- `app/core/geometry.py` - Contains `_extract_paint_bucket_regions()` which implements the two-stage snapping.
- `app/core/extractor.py` - Contains `_get_drawing_units()` and `get_snap_tolerances()` functions being tested.

### New Files
No new files needed. Tests will be added to existing test files.

## Implementation Plan
### Phase 1: Gap Analysis
Review existing tests against the implementation plan requirements for Units 9-10. Identify specific tests that are missing or need enhancement.

**Analysis Results:**

From Unit 9 (test_geometry.py), the following tests from the implementation plan are MISSING:
1. `test_stage1_fixes_nanometer_gap` - Tests raw Shapely snap behavior with ~3.7nm gap
2. `test_stage2_bridges_large_gaps` - Tests raw Shapely snap bridging 1-unit gaps
3. `test_mm_tolerance` - Direct constant verification
4. `test_meter_tolerance` - Direct constant verification
5. `test_inch_tolerance` - Direct constant verification
6. `test_default_gap_amounts` - Direct constant verification

From Unit 10 (test_extractor_units.py), all tests are already present:
- Unit detection tests: all present and comprehensive
- Tolerance calculation tests: all present and comprehensive

### Phase 2: Core Implementation
Add missing tests to the appropriate test files following existing patterns and conventions.

### Phase 3: Integration
Run the full test suite to ensure new tests pass and no regressions occur.

## Step by Step Tasks

### Step 1: Add TestUnitToleranceMapping class to test_geometry.py
Add direct constant verification tests as specified in Unit 9:

- Add `TestUnitToleranceMapping` class after existing test classes
- Add `test_mm_tolerance()` - Verify PRECISION_SNAP_TOLERANCE[4] == 1e-6
- Add `test_meter_tolerance()` - Verify PRECISION_SNAP_TOLERANCE[6] == 1e-4
- Add `test_inch_tolerance()` - Verify PRECISION_SNAP_TOLERANCE[1] == 1e-6 (corrected from plan - actual implementation uses 1e-6)
- Add `test_default_gap_amounts()` - Verify DEFAULT_GAP_BRIDGE_TOLERANCE values for each unit

**Implementation:**
```python
class TestUnitToleranceMapping:
    """Tests for unit-to-tolerance constant mappings."""

    def test_mm_tolerance(self) -> None:
        """MM drawings should use 1e-6 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[4] == 1e-6

    def test_meter_tolerance(self) -> None:
        """Meter drawings should use 1e-4 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[6] == 1e-4

    def test_inch_tolerance(self) -> None:
        """Inch drawings should use appropriate precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[1] == 1e-6

    def test_feet_tolerance(self) -> None:
        """Feet drawings should use 1e-5 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[2] == 1e-5

    def test_cm_tolerance(self) -> None:
        """Centimeter drawings should use 1e-5 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[5] == 1e-5

    def test_unitless_tolerance(self) -> None:
        """Unitless drawings should use 1e-6 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[0] == 1e-6

    def test_default_gap_amounts(self) -> None:
        """Default gap amounts should be appropriate for each unit."""
        # Verify key unit defaults
        assert DEFAULT_GAP_BRIDGE_TOLERANCE[4] == 0.5   # MM: 0.5mm
        assert DEFAULT_GAP_BRIDGE_TOLERANCE[6] == 0.001  # M: 1mm in meters
        assert DEFAULT_GAP_BRIDGE_TOLERANCE[1] == 0.01   # IN: 0.01 inches
        assert DEFAULT_GAP_BRIDGE_TOLERANCE[2] == 0.1    # FT: 0.1 feet
        assert DEFAULT_GAP_BRIDGE_TOLERANCE[5] == 0.05   # CM: 0.05 cm
        assert DEFAULT_GAP_BRIDGE_TOLERANCE[0] == 0.1    # Unitless
```

### Step 2: Add test_stage1_fixes_nanometer_gap to TestPrecisionSnapping
Add the specific nanometer gap test from the implementation plan:

- Add `test_stage1_fixes_nanometer_gap()` method to `TestPrecisionSnapping` class
- Test uses raw Shapely snap operations to verify the snapping behavior
- Simulates ~3.7nm gap scenario from SPAR Gulv issue

**Implementation:**
```python
def test_stage1_fixes_nanometer_gap(self) -> None:
    """Stage 1 should fix floating-point precision gaps (~3.7nm)."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, snap, unary_union

    # Create edges with ~3.7nm gap (like SPAR Gulv issue)
    edges = [
        LineString([(0, 0), (10, 0)]),
        LineString([(10, 0), (10, 10)]),
        LineString([(10, 10), (0, 10)]),
        LineString([(0, 10), (0, 0)]),
        # Horizontal line with precision error (~3.7nm short)
        LineString([(0, 5), (9.9999999962746, 5)]),
    ]

    # Without snapping: only 1 polygon (gap prevents split)
    merged_no_snap = unary_union(edges)
    polygons_no_snap = list(polygonize(list(merged_no_snap.geoms)))
    assert len(polygons_no_snap) == 1

    # With Stage 1 snapping: 2 polygons (gap fixed)
    merged = unary_union(edges)
    merged = snap(merged, merged, 1e-6)
    polygons_with_snap = list(polygonize(list(merged.geoms)))
    assert len(polygons_with_snap) == 2
```

### Step 3: Add test_stage2_bridges_large_gaps to TestGapBridging
Add the explicit gap bridging test from the implementation plan:

- Add `test_stage2_bridges_large_gaps()` method to `TestGapBridging` class
- Test uses raw Shapely snap operations to verify large gap bridging
- Simulates 1-unit intentional design gap scenario

**Implementation:**
```python
def test_stage2_bridges_large_gaps(self) -> None:
    """Stage 2 should bridge intentional design gaps when enabled."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, snap, unary_union

    edges = [
        LineString([(0, 0), (10, 0)]),
        LineString([(10, 0), (10, 10)]),
        LineString([(10, 10), (0, 10)]),
        LineString([(0, 10), (0, 0)]),
        LineString([(0, 5), (9, 5)]),  # 1 unit gap
    ]

    merged = unary_union(edges)
    merged = snap(merged, merged, 1e-6)   # Stage 1
    merged = snap(merged, merged, 2.0)    # Stage 2 with 2.0 tolerance
    polygons = list(polygonize(list(merged.geoms)))

    # Gap bridged - now 2 polygons
    assert len(polygons) == 2
```

### Step 4: Add import statements for new tests
Update imports in test_geometry.py:

- Add imports for PRECISION_SNAP_TOLERANCE and DEFAULT_GAP_BRIDGE_TOLERANCE from core.constants

**Implementation:**
```python
from core.constants import (
    DEFAULT_GAP_BRIDGE_TOLERANCE,
    PRECISION_SNAP_TOLERANCE,
)
```

### Step 5: Run validation tests
Execute all tests to ensure:
- New tests pass
- No regressions in existing tests
- Type checking passes

## Testing Strategy
### Unit Tests
- Direct constant value verification (TestUnitToleranceMapping)
- Raw Shapely snap behavior verification (nanometer gap test)
- Gap bridging behavior with explicit tolerance (large gap test)

### Integration Tests
Already covered by existing tests:
- `_extract_paint_bucket_regions()` with tolerance parameters
- `_detect_content_zone()` tolerance propagation
- `extract_blocks()` with tolerance parameters

### Edge Cases
- Nanometer-scale gaps (~3.7nm) that cause polygon detection failures
- 1-unit intentional design gaps that require Stage 2 bridging
- Clean geometry that should be unaffected by snapping
- All supported unit codes (0, 1, 2, 4, 5, 6)

### Playwright MCP Tests
Not applicable - this is a CLI/library feature, not a web interface.

## Acceptance Criteria
1. `TestUnitToleranceMapping` class added with 7 tests for constant verification
2. `test_stage1_fixes_nanometer_gap()` test added and passing
3. `test_stage2_bridges_large_gaps()` test added and passing
4. All existing tests continue to pass (no regressions)
5. Type checking passes with `uv run mypy app/`
6. Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests including new snapping tests
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests
- `uv run pytest app/tests/core/extractor/test_extractor_units.py -v` - Run extractor unit tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run mypy app/` - Verify type checking passes
- `uv run ruff check app/` - Verify linting passes

## Notes
- The implementation plan specified `PRECISION_SNAP_TOLERANCE[1] == 1e-7` for inches, but the actual implementation uses `1e-6`. Tests should verify actual implementation values.
- The DEFAULT_GAP_BRIDGE_TOLERANCE values in the implementation plan differed from what was actually implemented. Tests should verify actual values:
  - Plan said MM=100.0, actual is 0.5
  - Plan said M=0.1, actual is 0.001
  - Plan said IN=4.0, actual is 0.01
- Some tests from the implementation plan already exist in different forms (e.g., `test_stage1_no_effect_on_clean_geometry`). These don't need to be duplicated.
- The TestPrecisionSnapping and TestGapBridging classes already have tests that verify the function-level behavior. The new tests verify the raw Shapely snap operations that those functions rely on.
