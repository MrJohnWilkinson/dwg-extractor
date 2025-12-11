# Chore: Update Gap Bridge Tests for Mutual Exclusivity and Terminology

## Chore Description
Update the `TestGapBridging` and `TestTolerancePropagation` test classes in `app/tests/core/test_geometry.py` to reflect the mutual exclusivity between Precision Fix and Gap Bridge options implemented in Unit 1. The tests currently use outdated "Stage 1/Stage 2" terminology and some tests call the function with both `precision_tolerance` and `gap_bridge_tolerance` set, which violates the new mutual exclusivity design.

Unit 1 (commit `4fca481`) changed the Gap Bridge algorithm from post-union snapping to pre-union snapping, making it an alternative approach to Precision Fix rather than a sequential second stage. The tests need to:
1. Rename methods from "stage2" terminology to "gap_bridge" terminology
2. Use `precision_tolerance=0` when testing gap bridge (enforcing mutual exclusivity)
3. Update or remove tests that combined both tolerances
4. Update class docstrings to reflect the new design

## Relevant Files
Use these files to resolve the chore:

- **`app/tests/core/test_geometry.py`** (lines 1106-1296) - Contains the test classes that need updating:
  - `TestGapBridging` class (lines 1106-1226): Tests gap bridge functionality with "stage2" terminology
  - `TestTolerancePropagation` class (lines 1228-1296): Tests tolerance parameter handling including combined usage

- **`app/core/geometry.py`** (reference only) - The implementation being tested, already updated in Unit 1 to use pre-union snapping for gap bridge

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `TestGapBridging` class docstring

**File:** `app/tests/core/test_geometry.py`

**Location:** Lines 1106-1112

**Current docstring:**
```python
class TestGapBridging:
    """Test suite for Stage 2 gap bridging in _extract_paint_bucket_regions.

    Note: Shapely's snap() function adds vertices to nearby geometries within
    tolerance. This can help bridge small gaps in certain topologies by adding
    connection points, though it doesn't directly merge separate line endpoints.
    """
```

**Replace with:**
```python
class TestGapBridging:
    """Test suite for gap bridge functionality in _extract_paint_bucket_regions.

    Gap Bridge is an alternative to Precision Fix (mutually exclusive). Both close
    gaps for accurate polygon counts. Gap Bridge snaps edges to reference geometry
    before union using Shapely's snap() function, which adds vertices where edges
    pass within tolerance of each other.
    """
```

### Step 2: Rename `test_stage2_disabled_by_default` to `test_gap_bridge_disabled_by_default`

**File:** `app/tests/core/test_geometry.py`

**Location:** Lines 1114-1127

**Current method:**
```python
def test_stage2_disabled_by_default(self) -> None:
    """Test that default gap_bridge_tolerance=0.0 doesn't modify geometry."""
```

**Rename to:**
```python
def test_gap_bridge_disabled_by_default(self) -> None:
    """Test that default gap_bridge_tolerance=0.0 doesn't modify geometry."""
```

**Also update the function call** to use `precision_tolerance=0` (line 1122-1124):
```python
regions = _extract_paint_bucket_regions(
    block, precision_tolerance=0, gap_bridge_tolerance=0
)
```

### Step 3: Rename `test_stage2_tolerance_parameter_accepted` to `test_gap_bridge_tolerance_parameter_accepted`

**File:** `app/tests/core/test_geometry.py`

**Location:** Lines 1129-1149

**Current method:**
```python
def test_stage2_tolerance_parameter_accepted(self) -> None:
    """Test that gap_bridge_tolerance parameter is accepted."""
```

**Rename to:**
```python
def test_gap_bridge_tolerance_parameter_accepted(self) -> None:
    """Test that gap_bridge_tolerance parameter is accepted with precision_tolerance=0."""
```

**Update all function calls** to use `precision_tolerance=0` (mutual exclusivity):
```python
# Should not raise with various tolerance values
regions_zero = _extract_paint_bucket_regions(
    block, precision_tolerance=0, gap_bridge_tolerance=0.0
)
regions_small = _extract_paint_bucket_regions(
    block, precision_tolerance=0, gap_bridge_tolerance=0.5
)
regions_large = _extract_paint_bucket_regions(
    block, precision_tolerance=0, gap_bridge_tolerance=10.0
)
```

### Step 4: Rename `test_stage2_no_effect_on_clean_geometry` to `test_gap_bridge_no_effect_on_clean_geometry`

**File:** `app/tests/core/test_geometry.py`

**Location:** Lines 1151-1167

**Current method:**
```python
def test_stage2_no_effect_on_clean_geometry(self) -> None:
    """Test Stage 2 doesn't negatively impact clean geometry."""
```

**Rename to:**
```python
def test_gap_bridge_no_effect_on_clean_geometry(self) -> None:
    """Test gap bridge doesn't negatively impact clean geometry."""
```

**Update the function call** to use `precision_tolerance=0` (line 1163-1165):
```python
regions = _extract_paint_bucket_regions(
    block, precision_tolerance=0, gap_bridge_tolerance=10.0
)
```

### Step 5: Rename `test_stage2_with_grid_pattern` to `test_gap_bridge_with_grid_pattern`

**File:** `app/tests/core/test_geometry.py`

**Location:** Lines 1169-1184

**Current method:**
```python
def test_stage2_with_grid_pattern(self) -> None:
    """Test Stage 2 works correctly with complex grid geometry."""
```

**Rename to:**
```python
def test_gap_bridge_with_grid_pattern(self) -> None:
    """Test gap bridge works correctly with complex grid geometry."""
```

**Update the function call** to use `precision_tolerance=0` (line 1179-1181):
```python
regions = _extract_paint_bucket_regions(
    block, precision_tolerance=0, gap_bridge_tolerance=1.0
)
```

### Step 6: Rename `test_stage2_bridges_large_gaps` to `test_gap_bridge_bridges_large_gaps`

**File:** `app/tests/core/test_geometry.py`

**Location:** Lines 1186-1225

**Current method:**
```python
def test_stage2_bridges_large_gaps(self) -> None:
    """Stage 2 should add vertices at larger gap bridge tolerance points.

    Shapely's snap() adds vertices where edges pass within tolerance
    of each other. With a 2.0 tolerance on a 1-unit gap, the endpoint
    at (9, 5) is within tolerance of the right edge at (10, 5), so
    a vertex is added to the right edge. This effectively bridges the gap
    by adding a connection point.
    """
```

**Rename to:**
```python
def test_gap_bridge_bridges_large_gaps(self) -> None:
    """Gap bridge should add vertices at larger tolerance points.

    Shapely's snap() adds vertices where edges pass within tolerance
    of each other. With a 2.0 tolerance on a 1-unit gap, the endpoint
    at (9, 5) is within tolerance of the right edge at (10, 5), so
    a vertex is added to the right edge. This effectively bridges the gap
    by adding a connection point.
    """
```

**Update the comments** in the function body (lines 1203-1205):
- Change `# Stage 1` comment to `# Precision fix equivalent`
- Change `# Stage 2 with 2.0 tolerance` comment to `# Gap bridge with 2.0 tolerance`

Replace:
```python
merged = snap(merged, merged, 1e-6)  # Stage 1
merged_stage2 = snap(merged, merged, 2.0)  # Stage 2 with 2.0 tolerance
```

With:
```python
merged = snap(merged, merged, 1e-6)  # Precision fix equivalent
merged_gap_bridge = snap(merged, merged, 2.0)  # Gap bridge with 2.0 tolerance
```

**Update variable reference** (line 1209-1213):
Replace `merged_stage2` with `merged_gap_bridge`:
```python
line_segments = (
    list(merged_gap_bridge.geoms)
    if hasattr(merged_gap_bridge, "geoms")
    else [merged_gap_bridge]
)
```

### Step 7: Update `test_gap_bridge_only_parameter` in TestTolerancePropagation

**File:** `app/tests/core/test_geometry.py`

**Location:** Lines 1254-1265

**Current method:**
```python
def test_gap_bridge_only_parameter(self) -> None:
    """Test passing gap_bridge_tolerance with default precision."""
    ...
    # Default precision + gap bridging
    regions = _extract_paint_bucket_regions(block, gap_bridge_tolerance=2.0)
```

**Update to explicitly set precision_tolerance=0** for mutual exclusivity:
```python
def test_gap_bridge_only_parameter(self) -> None:
    """Test passing gap_bridge_tolerance with precision_tolerance=0 (mutual exclusivity)."""
    doc = ezdxf.new()
    block = doc.blocks.new(name="GAP_BRIDGE_ONLY")

    # Clean rectangle should work with gap bridging enabled
    block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

    # Gap bridge with precision_tolerance=0 (mutually exclusive)
    regions = _extract_paint_bucket_regions(block, precision_tolerance=0, gap_bridge_tolerance=2.0)

    assert len(regions) == 1
```

### Step 8: Replace `test_both_tolerances_combined` with `test_mutual_exclusivity_design`

**File:** `app/tests/core/test_geometry.py`

**Location:** Lines 1267-1279

**Current method:**
```python
def test_both_tolerances_combined(self) -> None:
    """Test using both tolerance parameters together."""
    doc = ezdxf.new()
    block = doc.blocks.new(name="BOTH_TOLERANCES")

    # Clean rectangle with both tolerances specified
    block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

    regions = _extract_paint_bucket_regions(
        block, precision_tolerance=1e-5, gap_bridge_tolerance=0.5
    )

    assert len(regions) == 1
```

**Replace with a test documenting the mutual exclusivity design:**
```python
def test_mutual_exclusivity_design(self) -> None:
    """Document that precision_tolerance and gap_bridge_tolerance are mutually exclusive.

    The GUI enforces mutual exclusivity - users can only enable one option at a time.
    This test documents the design by showing both approaches work independently.
    Note: The function technically accepts both parameters, but the GUI prevents this.
    """
    doc = ezdxf.new()
    block = doc.blocks.new(name="MUTUAL_EXCLUSIVITY")

    block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

    # Precision Fix approach (gap_bridge_tolerance=0)
    regions_precision = _extract_paint_bucket_regions(
        block, precision_tolerance=1e-5, gap_bridge_tolerance=0
    )
    assert len(regions_precision) == 1

    # Gap Bridge approach (precision_tolerance=0)
    regions_gap_bridge = _extract_paint_bucket_regions(
        block, precision_tolerance=0, gap_bridge_tolerance=0.5
    )
    assert len(regions_gap_bridge) == 1
```

### Step 9: Update `test_abort_event_still_works_with_tolerances` to use mutually exclusive parameters

**File:** `app/tests/core/test_geometry.py`

**Location:** Lines 1281-1295

**Current function call:**
```python
with pytest.raises(GeometryAbortedError):
    _extract_paint_bucket_regions(
        block, abort_event, precision_tolerance=1e-6, gap_bridge_tolerance=1.0
    )
```

**Update to use only gap_bridge_tolerance** (demonstrating mutual exclusivity):
```python
with pytest.raises(GeometryAbortedError):
    _extract_paint_bucket_regions(
        block, abort_event, precision_tolerance=0, gap_bridge_tolerance=1.0
    )
```

### Step 10: Run validation commands

Execute the test suite to ensure all changes work correctly with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py::TestGapBridging -v` - Run updated gap bridging tests
- `uv run pytest app/tests/core/test_geometry.py::TestTolerancePropagation -v` - Run updated tolerance propagation tests
- `uv run pytest app/tests/ -q` - Run all tests to ensure zero regressions
- `uv run mypy app/` - Run type checking to ensure type safety

## Notes
- The function `_extract_paint_bucket_regions()` technically still accepts both parameters, but the GUI enforces mutual exclusivity. The tests should reflect the intended usage pattern.
- Unit 1 changed the Gap Bridge algorithm from post-union snapping (`snap(merged, merged, tolerance)`) to pre-union snapping (same pattern as Precision Fix), so the tests should work correctly with the new implementation.
- The `test_gap_bridge_bridges_large_gaps` test uses direct Shapely operations (not `_extract_paint_bucket_regions`), so it demonstrates the snapping behavior at a lower level. The variable renaming from `merged_stage2` to `merged_gap_bridge` aligns with the terminology update.
- These are terminology and test parameter updates with minimal functional impact, but validation ensures all tests pass correctly.
