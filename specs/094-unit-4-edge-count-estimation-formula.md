# Chore: Improve Edge Count Estimation Formula for CIRCLE, ARC, and HATCH

## Chore Description

The `_estimate_edge_count()` function in `app/core/geometry.py` uses fixed hardcoded values for CIRCLE (36 segments), ARC (18 segments), and HATCH (50 segments) that don't account for:
- Entity size (radius) - larger circles need more segments
- Configured sagitta value - higher precision settings produce more segments
- Actual arc angular extent - a 10-degree arc shouldn't estimate the same as a 180-degree arc

Unit 3 (spec 093) already added dynamic estimation formulas for ELLIPSE and SPLINE entities using the Ramanujan approximation and control point multipliers respectively. This chore extends the same principle to CIRCLE, ARC, and HATCH entities using a mathematically derived formula based on the sagitta-to-radius relationship.

**Current hardcoded values (lines 788-831):**
```python
elif entity_type == "CIRCLE":
    count += 36  # Fixed value - doesn't scale with radius
elif entity_type == "ARC":
    count += 18  # Fixed value - ignores angular extent
elif entity_type == "HATCH":
    count += 50  # Fixed value - reasonable for simple hatches
```

**Mathematical Formula:**
The sagitta (s) of an arc segment with radius (r) and half-angle (theta/2) is:
```
s = r * (1 - cos(theta/2))
```
Solving for theta (angle per segment that achieves target sagitta):
```
theta = 2 * arccos(1 - s/r)
```
Number of segments for a given arc angle:
```
n = angle_rad / theta = angle_rad / (2 * arccos(1 - sagitta/radius))
```

This formula produces adaptive segment counts that match the actual `flattening()` behavior used in edge extraction.

## Relevant Files

Use these files to resolve the chore:

- **`app/core/geometry.py`** - Primary implementation file
  - Lines 754-833: `_estimate_edge_count()` function - update CIRCLE, ARC, HATCH estimation
  - Line 36: `ARC_FLATTENING_SAGITTA` constant import (already available)
  - Line 22: `math` module import (already available)
  - Reference ELLIPSE estimation (lines 796-817) for formula pattern

- **`app/core/constants.py`** - Constants file
  - Line 185: `ARC_FLATTENING_SAGITTA = 0.1` - sagitta value used in estimation

- **`app/tests/core/test_geometry.py`** - Unit tests for geometry functions
  - Add new `TestEstimateArcSegments` test class for the helper function
  - Add new `TestEdgeCountEstimation` test class for integration tests

- **`app/tests/assets/circle_arc_hatch_edges_test.dxf`** - Existing test asset with various CIRCLE, ARC, and HATCH entities for testing

### New Files

No new files needed. The existing test asset `app/tests/assets/circle_arc_hatch_edges_test.dxf` already contains appropriate test fixtures.

## Step by Step Tasks

### Step 1: Add `_estimate_arc_segments()` Helper Function

Add a new helper function in `app/core/geometry.py` before `_estimate_edge_count()` (around line 752):

```python
def _estimate_arc_segments(radius: float, angle_rad: float, sagitta: float) -> int:
    """
    Calculate segments needed to approximate arc within sagitta tolerance.

    Uses the mathematical relationship between sagitta and arc geometry:
    - sagitta = radius * (1 - cos(theta/2)) where theta is angle per segment
    - Solving for segments: n = angle / (2 * arccos(1 - sagitta/radius))

    This produces segment counts that closely match ezdxf's flattening() output.

    Args:
        radius: Arc radius in drawing units.
        angle_rad: Total arc angle in radians.
        sagitta: Maximum allowed sagitta (distance from arc to chord center).

    Returns:
        Estimated number of segments needed. Always >= 1.

    Examples:
        >>> _estimate_arc_segments(100, 2*math.pi, 0.1)  # Large circle
        ~141 segments
        >>> _estimate_arc_segments(10, 2*math.pi, 0.1)  # Small circle
        ~45 segments
        >>> _estimate_arc_segments(50, math.pi/2, 0.1)  # 90-degree arc
        ~18 segments
    """
    if radius <= 0 or sagitta <= 0 or angle_rad <= 0:
        return 1

    ratio = sagitta / radius
    if ratio >= 1:
        return 1  # Sagitta larger than radius - use minimum

    # Angle per segment that achieves target sagitta
    theta_per_segment = 2 * math.acos(1 - ratio)

    # Number of segments for the arc
    segments = int(math.ceil(angle_rad / theta_per_segment))
    return max(1, segments)
```

### Step 2: Update CIRCLE Estimation in `_estimate_edge_count()`

Replace the fixed CIRCLE estimation (lines 788-790) with the formula-based approach:

```python
elif entity_type == "CIRCLE":
    # Dynamic estimation based on radius and sagitta
    try:
        radius = entity.dxf.radius
        count += _estimate_arc_segments(radius, 2 * math.pi, ARC_FLATTENING_SAGITTA)
    except (AttributeError, TypeError, ValueError):
        count += 36  # Fallback to default if properties unavailable
```

### Step 3: Update ARC Estimation in `_estimate_edge_count()`

Replace the fixed ARC estimation (lines 792-794) with the formula-based approach:

```python
elif entity_type == "ARC":
    # Dynamic estimation based on radius, angle, and sagitta
    try:
        radius = entity.dxf.radius
        start = math.radians(entity.dxf.start_angle)
        end = math.radians(entity.dxf.end_angle)
        angle = (end - start) % (2 * math.pi)
        if angle == 0:
            angle = 2 * math.pi  # Full circle case
        count += _estimate_arc_segments(radius, angle, ARC_FLATTENING_SAGITTA)
    except (AttributeError, TypeError, ValueError):
        count += 18  # Fallback to default if properties unavailable
```

### Step 4: Review HATCH Estimation

HATCH entities are complex with multiple boundary path types (PolylinePath, EdgePath with LineEdge, ArcEdge, EllipseEdge, SplineEdge). The current fixed estimate of 50 is reasonable for average cases. For this chore, keep the existing HATCH estimation but add a comment documenting the complexity:

```python
elif entity_type == "HATCH":
    # HATCH has complex boundary paths (PolylinePath, EdgePath with various edge types).
    # A fixed estimate of 50 is reasonable for typical hatches.
    # More accurate estimation would require iterating boundary paths,
    # which defeats the purpose of fast estimation.
    count += 50
```

### Step 5: Add Unit Tests for `_estimate_arc_segments()` Helper Function

Add new test class to `app/tests/core/test_geometry.py`:

```python
class TestEstimateArcSegments:
    """Test suite for _estimate_arc_segments helper function."""

    def test_full_circle_large_radius(self) -> None:
        """Large radius circle should produce more segments."""
        from core.geometry import _estimate_arc_segments
        import math

        # Large circle: radius=100, full circle, sagitta=0.1
        segments = _estimate_arc_segments(100, 2 * math.pi, 0.1)

        # Should produce ~140 segments for large circle
        assert 100 < segments < 200

    def test_full_circle_small_radius(self) -> None:
        """Small radius circle should produce fewer segments."""
        from core.geometry import _estimate_arc_segments
        import math

        # Small circle: radius=10, full circle, sagitta=0.1
        segments = _estimate_arc_segments(10, 2 * math.pi, 0.1)

        # Should produce ~45 segments for small circle
        assert 30 < segments < 60

    def test_quarter_arc(self) -> None:
        """90-degree arc should produce ~1/4 of full circle segments."""
        from core.geometry import _estimate_arc_segments
        import math

        full_circle = _estimate_arc_segments(50, 2 * math.pi, 0.1)
        quarter_arc = _estimate_arc_segments(50, math.pi / 2, 0.1)

        # Quarter arc should be approximately 1/4 of full circle
        assert 0.20 < (quarter_arc / full_circle) < 0.30

    def test_half_arc(self) -> None:
        """180-degree arc should produce ~1/2 of full circle segments."""
        from core.geometry import _estimate_arc_segments
        import math

        full_circle = _estimate_arc_segments(50, 2 * math.pi, 0.1)
        half_arc = _estimate_arc_segments(50, math.pi, 0.1)

        # Half arc should be approximately 1/2 of full circle
        assert 0.45 < (half_arc / full_circle) < 0.55

    def test_invalid_radius_returns_one(self) -> None:
        """Zero or negative radius should return 1."""
        from core.geometry import _estimate_arc_segments
        import math

        assert _estimate_arc_segments(0, 2 * math.pi, 0.1) == 1
        assert _estimate_arc_segments(-10, 2 * math.pi, 0.1) == 1

    def test_invalid_sagitta_returns_one(self) -> None:
        """Zero or negative sagitta should return 1."""
        from core.geometry import _estimate_arc_segments
        import math

        assert _estimate_arc_segments(50, 2 * math.pi, 0) == 1
        assert _estimate_arc_segments(50, 2 * math.pi, -0.1) == 1

    def test_sagitta_larger_than_radius_returns_one(self) -> None:
        """Sagitta >= radius should return 1 (edge case)."""
        from core.geometry import _estimate_arc_segments
        import math

        assert _estimate_arc_segments(0.05, 2 * math.pi, 0.1) == 1

    def test_larger_sagitta_fewer_segments(self) -> None:
        """Larger sagitta tolerance should produce fewer segments."""
        from core.geometry import _estimate_arc_segments
        import math

        fine = _estimate_arc_segments(50, 2 * math.pi, 0.01)    # Fine tolerance
        coarse = _estimate_arc_segments(50, 2 * math.pi, 1.0)   # Coarse tolerance

        assert fine > coarse
```

### Step 6: Add Integration Tests for Updated Estimation

Add integration tests verifying the estimation matches actual flattening output:

```python
class TestEdgeCountEstimation:
    """Test suite for _estimate_edge_count with formula-based estimation."""

    def test_circle_estimation_matches_flattening(self) -> None:
        """Verify CIRCLE estimation closely matches actual flattening output."""
        import ezdxf
        from core.geometry import _estimate_edge_count, _extract_circle_edges
        from core.constants import ARC_FLATTENING_SAGITTA

        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLE_TEST")
        block.add_circle(center=(0, 0), radius=50)

        estimated = _estimate_edge_count(block)

        # Get actual edge count from flattening
        circle_entity = list(block)[0]
        actual_edges = _extract_circle_edges(circle_entity)
        actual_count = len(actual_edges)

        # Estimation should be within 10% of actual
        assert abs(estimated - actual_count) <= actual_count * 0.10

    def test_arc_estimation_matches_flattening(self) -> None:
        """Verify ARC estimation closely matches actual flattening output."""
        import ezdxf
        from core.geometry import _estimate_edge_count, _extract_arc_edges

        doc = ezdxf.new()
        block = doc.blocks.new(name="ARC_TEST")
        block.add_arc(center=(0, 0), radius=50, start_angle=0, end_angle=90)

        estimated = _estimate_edge_count(block)

        # Get actual edge count from flattening
        arc_entity = list(block)[0]
        actual_edges = _extract_arc_edges(arc_entity)
        actual_count = len(actual_edges)

        # Estimation should be within 10% of actual
        assert abs(estimated - actual_count) <= actual_count * 0.10

    def test_large_circle_more_segments_than_small(self) -> None:
        """Large circles should estimate more segments than small circles."""
        import ezdxf
        from core.geometry import _estimate_edge_count

        doc = ezdxf.new()

        small_block = doc.blocks.new(name="SMALL_CIRCLE")
        small_block.add_circle(center=(0, 0), radius=10)

        large_block = doc.blocks.new(name="LARGE_CIRCLE")
        large_block.add_circle(center=(0, 0), radius=100)

        small_estimate = _estimate_edge_count(small_block)
        large_estimate = _estimate_edge_count(large_block)

        assert large_estimate > small_estimate
        # Large circle (100 radius) should have roughly 3x more segments than small (10 radius)
        # because segments scale with sqrt(radius) for fixed sagitta
        assert large_estimate > small_estimate * 2

    def test_full_arc_more_segments_than_quarter_arc(self) -> None:
        """Full arc (360) should estimate more segments than quarter arc (90)."""
        import ezdxf
        from core.geometry import _estimate_edge_count

        doc = ezdxf.new()

        quarter_block = doc.blocks.new(name="QUARTER_ARC")
        quarter_block.add_arc(center=(0, 0), radius=50, start_angle=0, end_angle=90)

        full_block = doc.blocks.new(name="FULL_ARC")
        full_block.add_arc(center=(0, 0), radius=50, start_angle=0, end_angle=360)

        quarter_estimate = _estimate_edge_count(quarter_block)
        full_estimate = _estimate_edge_count(full_block)

        assert full_estimate > quarter_estimate
        # Full arc should have ~4x more segments than quarter arc
        assert 3 < (full_estimate / quarter_estimate) < 5

    def test_mixed_block_estimation(self) -> None:
        """Test estimation with mixed entity types."""
        import ezdxf
        from core.geometry import _estimate_edge_count

        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED_TEST")

        # 4 LINE edges
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))
        block.add_line((100, 50), (0, 50))
        block.add_line((0, 50), (0, 0))

        # 1 CIRCLE (should be >0 segments)
        block.add_circle(center=(50, 25), radius=20)

        estimate = _estimate_edge_count(block)

        # Should be at least 4 (lines) + some circle segments
        assert estimate > 4

    def test_uses_existing_test_asset(self) -> None:
        """Verify estimation works with existing test DXF file."""
        import ezdxf
        from core.geometry import _estimate_edge_count

        doc = ezdxf.readfile("app/tests/assets/circle_arc_hatch_edges_test.dxf")

        # Test SIZE_TEST block which has small and large circles
        size_test_block = doc.blocks.get("SIZE_TEST")
        estimate = _estimate_edge_count(size_test_block)

        # Should have > 0 segments for both circles
        assert estimate > 0

        # Test MIXED_ENTITIES block
        mixed_block = doc.blocks.get("MIXED_ENTITIES")
        mixed_estimate = _estimate_edge_count(mixed_block)

        # Should include LINE, CIRCLE, ARC, and HATCH contributions
        assert mixed_estimate > 50  # At least HATCH (50) + other entities
```

### Step 7: Update Test Import Statement

Ensure `_estimate_arc_segments` is exported and imported in test file. Add to imports in `app/tests/core/test_geometry.py`:

```python
from core.geometry import (
    # ... existing imports ...
    _estimate_arc_segments,  # Add this
)
```

### Step 8: Run Validation Commands

Execute every command to validate the chore is complete with zero regressions.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py::TestEstimateArcSegments -v` - Run new helper function tests
- `uv run pytest app/tests/core/test_geometry.py::TestEdgeCountEstimation -v` - Run new integration tests
- `uv run pytest app/tests/core/test_geometry.py -v` - Run all geometry tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests (uses edge estimation)
- `uv run pytest app/tests/core/extractor/test_extractor_prefilters.py -v` - Run prefilter tests (uses edge estimation)
- `uv run pytest app/tests/ -v` - Run complete test suite to verify zero regressions
- `uv run mypy app/` - Run type checking to ensure no type errors

## Notes

1. **Formula derivation**: The formula `n = angle / (2 * arccos(1 - sagitta/radius))` is mathematically derived from the geometric relationship between sagitta, chord, and arc. This is the same relationship that ezdxf's `flattening()` method uses internally.

2. **Edge case handling**: The helper function handles edge cases gracefully:
   - `radius <= 0`: Returns 1 (degenerate circle)
   - `sagitta <= 0`: Returns 1 (invalid tolerance)
   - `sagitta >= radius`: Returns 1 (very coarse approximation)
   - `angle <= 0`: Returns 1 (degenerate arc)

3. **HATCH complexity**: HATCH entities have multiple boundary path types that would require significant computation to estimate accurately. The fixed value of 50 is a reasonable average that doesn't defeat the purpose of fast estimation.

4. **Pattern consistency**: This implementation follows the same pattern established in Unit 3 (spec 093) for ELLIPSE and SPLINE estimation - use mathematical formulas with fallback to fixed defaults.

5. **Performance**: The `_estimate_arc_segments()` function uses only basic math operations (`acos`, `ceil`) and is O(1), maintaining the fast O(n) complexity of `_estimate_edge_count()`.

6. **Current test count**: The test suite currently has 1081 tests. This chore adds approximately 15 new tests.

7. **Prior unit learnings**:
   - **Unit 1 (spec 091)**: LWPOLYLINE bulge handling established pattern for test asset creation
   - **Unit 2 (spec 092)**: Nested INSERT expansion added helper functions with clear responsibilities
   - **Unit 3 (spec 093)**: ELLIPSE/SPLINE support added estimation formulas (Ramanujan for ellipse, control point multiplier for spline). This chore extends that pattern to CIRCLE and ARC.

8. **Reference document**: Detailed analysis in `ai_output/087-geometry-handling-gap-analysis-report.md` Section 3.1 (Edge Count Estimation Formula).
