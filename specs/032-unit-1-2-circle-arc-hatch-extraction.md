# Feature: CIRCLE, ARC, and HATCH Boundary Edge Extraction

## Feature Description
Extend the `_extract_all_edges()` function in `geometry.py` to extract edges from CIRCLE, ARC, and HATCH boundary entities. This enhancement uses ezdxf's built-in `entity.flattening(sagitta)` method for adaptive arc discretization and `ezdxf.path.from_hatch()` for HATCH boundaries, which correctly handles bulge values in PolylinePath segments. The implementation adds a new sagitta constant for consistent arc approximation across all curved entity types.

## User Story
As a CAD drawing analyst
I want CIRCLE, ARC, and HATCH boundary entities to be included in paint-bucket region detection
So that content zone detection works correctly for blocks containing curved geometry and hatched areas

## Problem Statement
Currently, `_extract_all_edges()` only extracts edges from LINE and LWPOLYLINE/POLYLINE entities. Blocks containing CIRCLE, ARC, or HATCH entities with curved boundaries are not fully processed, causing incomplete region detection and potentially incorrect content zone calculations. This is particularly problematic for floor plan blocks that use circles for fixtures, arcs for rounded corners, and hatches for filled areas.

## Solution Statement
Add three new helper functions to extract edges from CIRCLE, ARC, and HATCH entities using ezdxf's built-in geometry methods:
1. `_extract_circle_edges()` - Uses `entity.flattening(sagitta)` to convert circles to line segments
2. `_extract_arc_edges()` - Uses `entity.flattening(sagitta)` to convert arcs to line segments
3. `_extract_hatch_boundary_edges()` - Uses `from_hatch()` to extract boundary paths, handling bulge values correctly

These functions will be integrated into the existing `_extract_all_edges()` function with a new `ARC_FLATTENING_SAGITTA` constant controlling the approximation precision.

## Relevant Files
Use these files to implement the feature:

- **app/core/constants.py** - Add `ARC_FLATTENING_SAGITTA` constant for adaptive arc flattening precision
- **app/core/geometry.py** - Add helper functions and update `_extract_all_edges()` to handle CIRCLE, ARC, and HATCH entities
- **app/tests/core/test_geometry.py** - Add unit tests for new extraction functions
- **app/tests/assets/circles_arcs_points.dxf** - Existing test fixture with CIRCLE and ARC entities
- **app/tests/assets/hatch_test.dxf** - Existing test fixture with HATCH entities
- **ai_docs/ezdxf-geometry-reference.md** - Reference documentation for ezdxf geometry methods

### New Files
- **app/tests/assets/create_circle_arc_hatch_edges_test.py** - Script to create test DXF with edge extraction scenarios
- **app/tests/assets/circle_arc_hatch_edges_test.dxf** - Generated test fixture for edge extraction

## Implementation Plan
### Phase 1: Foundation
Add the sagitta constant to `constants.py` and import the `from_hatch` function in `geometry.py`. This establishes the configuration needed for adaptive arc flattening.

### Phase 2: Core Implementation
Implement three helper functions following the existing pattern in `geometry.py`:
1. `_extract_circle_edges(entity)` - Convert CIRCLE to LineString edges
2. `_extract_arc_edges(entity)` - Convert ARC to LineString edges
3. `_extract_hatch_boundary_edges(entity)` - Convert HATCH boundary paths to LineString edges

### Phase 3: Integration
Update `_extract_all_edges()` to call the new helper functions for CIRCLE, ARC, and HATCH entity types. Add comprehensive unit tests to validate the extraction logic and ensure no regressions in existing functionality.

## Step by Step Tasks

### Step 1: Add Sagitta Constant
- Open `app/core/constants.py`
- Add at the end of the file (after the existing threshold constants):
```python
# Arc Flattening Configuration
ARC_FLATTENING_SAGITTA: float = 0.1
"""Maximum distance from arc center to chord center for flattening.
Smaller values = more segments = higher precision. 0.1 is appropriate for
typical CAD drawings with units in mm or inches."""
```
- This constant will be imported by `geometry.py` for consistent arc approximation

### Step 2: Add Import Statements to geometry.py
- Open `app/core/geometry.py`
- Add `from_hatch` import at the top of the file:
```python
from ezdxf.path import from_hatch
```
- Update the constants import to include the new constant:
```python
from .constants import (
    ARC_FLATTENING_SAGITTA,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
)
```

### Step 3: Add CIRCLE Extraction Helper
- Add the following function after the `_count_line_segments()` function (around line 373):
```python
def _extract_circle_edges(entity: Any) -> list[LineString]:
    """Extract edges from CIRCLE entity using adaptive flattening.

    Uses ezdxf's built-in flattening method with sagitta-based precision.
    The sagitta controls the maximum distance from arc to chord, producing
    more segments for larger circles and fewer for smaller ones.

    Args:
        entity: ezdxf CIRCLE entity

    Returns:
        List of LineString objects representing the circle as line segments.
        Returns empty list if flattening fails.
    """
    try:
        points = list(entity.flattening(sagitta=ARC_FLATTENING_SAGITTA))
        edges: list[LineString] = []
        for i in range(len(points) - 1):
            edges.append(LineString([
                (points[i].x, points[i].y),
                (points[i + 1].x, points[i + 1].y)
            ]))
        return edges
    except (AttributeError, TypeError, ValueError):
        return []
```

### Step 4: Add ARC Extraction Helper
- Add the following function after `_extract_circle_edges()`:
```python
def _extract_arc_edges(entity: Any) -> list[LineString]:
    """Extract edges from ARC entity using adaptive flattening.

    Uses ezdxf's built-in flattening method with sagitta-based precision.
    Unlike circles, arcs are open curves (start != end).

    Args:
        entity: ezdxf ARC entity

    Returns:
        List of LineString objects representing the arc as line segments.
        Returns empty list if flattening fails.
    """
    try:
        points = list(entity.flattening(sagitta=ARC_FLATTENING_SAGITTA))
        edges: list[LineString] = []
        for i in range(len(points) - 1):
            edges.append(LineString([
                (points[i].x, points[i].y),
                (points[i + 1].x, points[i + 1].y)
            ]))
        return edges
    except (AttributeError, TypeError, ValueError):
        return []
```

### Step 5: Add HATCH Boundary Extraction Helper
- Add the following function after `_extract_arc_edges()`:
```python
def _extract_hatch_boundary_edges(entity: Any) -> list[LineString]:
    """Extract edges from HATCH boundary paths.

    Uses ezdxf's from_hatch() to correctly handle:
    - PolylinePath with bulge values (curved segments)
    - EdgePath with LineEdge, ArcEdge, etc.

    The from_hatch() function automatically converts bulge values to
    arc approximations, ensuring curved polyline segments are captured.

    Args:
        entity: ezdxf HATCH entity

    Returns:
        List of LineString objects representing all boundary path edges.
        Returns empty list if extraction fails.
    """
    edges: list[LineString] = []
    try:
        for path in from_hatch(entity):
            points = list(path.flattening(distance=ARC_FLATTENING_SAGITTA))
            for i in range(len(points) - 1):
                edges.append(LineString([
                    (points[i].x, points[i].y),
                    (points[i + 1].x, points[i + 1].y)
                ]))
    except (AttributeError, TypeError, ValueError):
        pass
    return edges
```

### Step 6: Update _extract_all_edges() Function
- Locate `_extract_all_edges()` function (around line 375-410)
- Update the function to handle CIRCLE, ARC, and HATCH entities
- Replace the entire function with:
```python
def _extract_all_edges(block_def: BlockLayout) -> list[LineString]:
    """
    Extract ALL edges from block as LineStrings for unified polygonize.

    Extracts edges from:
    - LINE entities (start to end as single edge)
    - LWPOLYLINE/POLYLINE entities (all vertices as edges, closing edge if closed)
    - CIRCLE entities (adaptive flattening to line segments)
    - ARC entities (adaptive flattening to line segments)
    - HATCH boundary paths (PolylinePath and EdgePath variants)

    Args:
        block_def: ezdxf block definition object

    Returns:
        List of LineString objects representing all edges in the block.
    """
    edges: list[LineString] = []

    for entity in block_def:
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            edges.append(LineString([(start.x, start.y), (end.x, end.y)]))

        elif entity_type in ("LWPOLYLINE", "POLYLINE"):
            try:
                points = [(float(p[0]), float(p[1])) for p in entity.get_points()]
                for i in range(len(points) - 1):
                    edges.append(LineString([points[i], points[i + 1]]))
                if hasattr(entity, "closed") and entity.closed and len(points) >= 2:
                    edges.append(LineString([points[-1], points[0]]))
            except (AttributeError, IndexError):
                continue

        elif entity_type == "CIRCLE":
            edges.extend(_extract_circle_edges(entity))

        elif entity_type == "ARC":
            edges.extend(_extract_arc_edges(entity))

        elif entity_type == "HATCH":
            edges.extend(_extract_hatch_boundary_edges(entity))

    logger.debug(f"Extracted {len(edges)} edges from block")
    return edges
```

### Step 7: Create Test DXF Generator Script
- Create `app/tests/assets/create_circle_arc_hatch_edges_test.py`:
```python
"""
Script to create a test DXF file for CIRCLE, ARC, and HATCH edge extraction.

Creates test fixtures for validating:
- CIRCLE edge extraction with various radii
- ARC edge extraction with various angles
- HATCH boundary extraction (PolylinePath and EdgePath)
- Mixed entity blocks for integration testing
"""

import ezdxf


# Create a new DXF document
doc = ezdxf.new("R2010")

# Block 1: CIRCLE forming closed region (for content zone detection)
block_circle_region = doc.blocks.new(name="CIRCLE_REGION")
# Single circle at center (0, 0) with radius 50
block_circle_region.add_circle(center=(0, 0), radius=50)

# Block 2: Multiple ARCs forming closed region
block_arc_region = doc.blocks.new(name="ARC_REGION")
# Four 90-degree arcs forming a rounded square
block_arc_region.add_arc(center=(50, 50), radius=50, start_angle=90, end_angle=180)
block_arc_region.add_arc(center=(50, 150), radius=50, start_angle=180, end_angle=270)
block_arc_region.add_arc(center=(150, 150), radius=50, start_angle=270, end_angle=360)
block_arc_region.add_arc(center=(150, 50), radius=50, start_angle=0, end_angle=90)
# Connecting lines
block_arc_region.add_line((0, 50), (0, 150))
block_arc_region.add_line((50, 200), (150, 200))
block_arc_region.add_line((200, 150), (200, 50))
block_arc_region.add_line((150, 0), (50, 0))

# Block 3: HATCH with PolylinePath (straight segments)
block_hatch_poly = doc.blocks.new(name="HATCH_POLYLINE")
hatch1 = block_hatch_poly.add_hatch()
hatch1.paths.add_polyline_path(
    [(0, 0), (100, 0), (100, 50), (0, 50)],
    is_closed=True
)

# Block 4: HATCH with PolylinePath containing bulge (curved segment)
block_hatch_bulge = doc.blocks.new(name="HATCH_BULGE")
hatch2 = block_hatch_bulge.add_hatch()
# Bulge of 0.5 creates an arc between vertices
hatch2.paths.add_polyline_path(
    [(0, 0, 0), (100, 0, 0.5), (100, 50, 0), (0, 50, 0)],
    is_closed=True
)

# Block 5: HATCH with EdgePath (LineEdge only)
block_hatch_edge_line = doc.blocks.new(name="HATCH_EDGE_LINE")
hatch3 = block_hatch_edge_line.add_hatch()
edge_path = hatch3.paths.add_edge_path()
edge_path.add_line((0, 0), (100, 0))
edge_path.add_line((100, 0), (100, 50))
edge_path.add_line((100, 50), (0, 50))
edge_path.add_line((0, 50), (0, 0))

# Block 6: HATCH with EdgePath (ArcEdge)
block_hatch_edge_arc = doc.blocks.new(name="HATCH_EDGE_ARC")
hatch4 = block_hatch_edge_arc.add_hatch()
edge_path2 = hatch4.paths.add_edge_path()
edge_path2.add_line((0, 0), (100, 0))
edge_path2.add_arc(center=(100, 25), radius=25, start_angle=270, end_angle=90)
edge_path2.add_line((100, 50), (0, 50))
edge_path2.add_line((0, 50), (0, 0))

# Block 7: Mixed entities (LINE + CIRCLE + ARC + HATCH)
block_mixed = doc.blocks.new(name="MIXED_ENTITIES")
block_mixed.add_line((0, 0), (200, 0))
block_mixed.add_line((200, 0), (200, 100))
block_mixed.add_line((200, 100), (0, 100))
block_mixed.add_line((0, 100), (0, 0))
block_mixed.add_circle(center=(100, 50), radius=30)
block_mixed.add_arc(center=(50, 50), radius=20, start_angle=0, end_angle=180)
hatch5 = block_mixed.add_hatch()
hatch5.paths.add_polyline_path(
    [(150, 20), (180, 20), (180, 40), (150, 40)],
    is_closed=True
)

# Block 8: Small vs large circles (test adaptive segment count)
block_size_test = doc.blocks.new(name="SIZE_TEST")
block_size_test.add_circle(center=(25, 25), radius=10)   # Small circle
block_size_test.add_circle(center=(100, 100), radius=75)  # Large circle

# Add block references to modelspace
msp = doc.modelspace()
msp.add_blockref("CIRCLE_REGION", (0, 0))
msp.add_blockref("ARC_REGION", (200, 0))
msp.add_blockref("HATCH_POLYLINE", (0, 300))
msp.add_blockref("HATCH_BULGE", (200, 300))
msp.add_blockref("HATCH_EDGE_LINE", (400, 300))
msp.add_blockref("HATCH_EDGE_ARC", (600, 300))
msp.add_blockref("MIXED_ENTITIES", (0, 500))
msp.add_blockref("SIZE_TEST", (400, 500))

# Save the file
doc.saveas("app/tests/assets/circle_arc_hatch_edges_test.dxf")
print("Created circle_arc_hatch_edges_test.dxf successfully")
```

### Step 8: Generate Test DXF File
- Run the generator script:
```bash
uv run python app/tests/assets/create_circle_arc_hatch_edges_test.py
```

### Step 9: Add Unit Tests for CIRCLE Extraction
- Add the following test class to `app/tests/core/test_geometry.py`:
```python
class TestExtractCircleEdges:
    """Test suite for _extract_circle_edges function."""

    def test_circle_produces_edges(self) -> None:
        """Test that CIRCLE entity produces line segment edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLE_TEST")
        block.add_circle(center=(50, 50), radius=25)

        edges = _extract_all_edges(block)

        # Circle should produce multiple edges (exact count depends on sagitta)
        assert len(edges) > 10  # At minimum, should have many segments
        # All edges should be LineStrings
        assert all(isinstance(e, LineString) for e in edges)

    def test_circle_edges_form_closed_loop(self) -> None:
        """Test that circle edges form a closed polygon via polygonize."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLE_CLOSED")
        block.add_circle(center=(0, 0), radius=50)

        regions = _extract_paint_bucket_regions(block)

        # Circle should form exactly one closed region
        assert len(regions) == 1

    def test_small_vs_large_circle_segment_count(self) -> None:
        """Test that larger circles produce more segments (adaptive flattening)."""
        doc = ezdxf.new()

        block_small = doc.blocks.new(name="SMALL_CIRCLE")
        block_small.add_circle(center=(0, 0), radius=10)

        block_large = doc.blocks.new(name="LARGE_CIRCLE")
        block_large.add_circle(center=(0, 0), radius=100)

        edges_small = _extract_all_edges(block_small)
        edges_large = _extract_all_edges(block_large)

        # Larger circle should have more segments due to sagitta-based flattening
        assert len(edges_large) > len(edges_small)
```
- Also add import for `LineString` at the top:
```python
from shapely.geometry import LineString
```

### Step 10: Add Unit Tests for ARC Extraction
- Add the following test class to `app/tests/core/test_geometry.py`:
```python
class TestExtractArcEdges:
    """Test suite for _extract_arc_edges function."""

    def test_arc_produces_edges(self) -> None:
        """Test that ARC entity produces line segment edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARC_TEST")
        block.add_arc(center=(100, 100), radius=50, start_angle=0, end_angle=90)

        edges = _extract_all_edges(block)

        # 90-degree arc should produce multiple edges
        assert len(edges) > 5
        assert all(isinstance(e, LineString) for e in edges)

    def test_180_degree_arc_segment_count(self) -> None:
        """Test that 180-degree arc produces appropriate segment count."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARC_180")
        block.add_arc(center=(0, 0), radius=50, start_angle=0, end_angle=180)

        edges = _extract_all_edges(block)

        # 180-degree arc should have more segments than 90-degree
        assert len(edges) > 10

    def test_multiple_arcs_forming_closed_shape(self) -> None:
        """Test that multiple arcs + lines can form closed region."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARCS_CLOSED")

        # Two semicircles forming a closed shape
        block.add_arc(center=(50, 0), radius=50, start_angle=0, end_angle=180)
        block.add_arc(center=(50, 0), radius=50, start_angle=180, end_angle=360)

        regions = _extract_paint_bucket_regions(block)

        # Should form one closed region (circle from two semicircles)
        assert len(regions) == 1
```

### Step 11: Add Unit Tests for HATCH Boundary Extraction
- Add the following test class to `app/tests/core/test_geometry.py`:
```python
class TestExtractHatchBoundaryEdges:
    """Test suite for _extract_hatch_boundary_edges function."""

    def test_hatch_polyline_path_produces_edges(self) -> None:
        """Test that HATCH with PolylinePath produces edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCH_POLY_TEST")
        hatch = block.add_hatch()
        hatch.paths.add_polyline_path(
            [(0, 0), (100, 0), (100, 50), (0, 50)],
            is_closed=True
        )

        edges = _extract_all_edges(block)

        # Rectangular hatch boundary should produce 4 edges
        assert len(edges) == 4
        assert all(isinstance(e, LineString) for e in edges)

    def test_hatch_with_bulge_produces_curved_edges(self) -> None:
        """Test that HATCH with bulge values produces curved segment edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCH_BULGE_TEST")
        hatch = block.add_hatch()
        # Bulge of 1.0 creates a semicircle
        hatch.paths.add_polyline_path(
            [(0, 0, 0), (100, 0, 1.0), (100, 50, 0), (0, 50, 0)],
            is_closed=True
        )

        edges = _extract_all_edges(block)

        # Should have more than 4 edges due to curved segment
        assert len(edges) > 4

    def test_hatch_edge_path_line_edges(self) -> None:
        """Test that HATCH with EdgePath LineEdge produces edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCH_EDGE_TEST")
        hatch = block.add_hatch()
        edge_path = hatch.paths.add_edge_path()
        edge_path.add_line((0, 0), (100, 0))
        edge_path.add_line((100, 0), (100, 50))
        edge_path.add_line((100, 50), (0, 50))
        edge_path.add_line((0, 50), (0, 0))

        edges = _extract_all_edges(block)

        # Should produce 4 edges for rectangular boundary
        assert len(edges) == 4

    def test_hatch_forms_closed_region(self) -> None:
        """Test that HATCH boundary forms closed region via polygonize."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCH_REGION_TEST")
        hatch = block.add_hatch()
        hatch.paths.add_polyline_path(
            [(0, 0), (100, 0), (100, 50), (0, 50)],
            is_closed=True
        )

        regions = _extract_paint_bucket_regions(block)

        # HATCH boundary should form exactly one closed region
        assert len(regions) == 1
```

### Step 12: Add Integration Tests
- Add the following test class to `app/tests/core/test_geometry.py`:
```python
class TestCircleArcHatchIntegration:
    """Integration tests for CIRCLE, ARC, and HATCH edge extraction."""

    def test_mixed_entities_produces_all_edges(self) -> None:
        """Test that block with mixed entities extracts all edge types."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED_TEST")

        # Add various entity types
        block.add_line((0, 0), (100, 0))
        block.add_circle(center=(150, 25), radius=20)
        block.add_arc(center=(200, 25), radius=15, start_angle=0, end_angle=180)
        hatch = block.add_hatch()
        hatch.paths.add_polyline_path(
            [(250, 0), (300, 0), (300, 50), (250, 50)],
            is_closed=True
        )

        edges = _extract_all_edges(block)

        # Should have edges from all entity types
        # 1 LINE + circle edges + arc edges + 4 HATCH edges
        assert len(edges) > 10

    def test_content_zone_with_circle_boundary(self) -> None:
        """Test content zone detection with CIRCLE defining boundary."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLE_BOUNDARY")
        # Circle as outer boundary
        block.add_circle(center=(50, 50), radius=50)
        # Small inner circle (hole)
        block.add_circle(center=(50, 50), radius=10)

        regions = _extract_paint_bucket_regions(block)

        # Should detect 2 regions: inner circle and outer ring
        assert len(regions) == 2

    def test_content_zone_with_arc_boundary(self) -> None:
        """Test content zone detection with ARCs forming boundary."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARC_BOUNDARY")
        # Rounded rectangle using arcs at corners
        block.add_line((20, 0), (80, 0))
        block.add_arc(center=(80, 20), radius=20, start_angle=270, end_angle=360)
        block.add_line((100, 20), (100, 80))
        block.add_arc(center=(80, 80), radius=20, start_angle=0, end_angle=90)
        block.add_line((80, 100), (20, 100))
        block.add_arc(center=(20, 80), radius=20, start_angle=90, end_angle=180)
        block.add_line((0, 80), (0, 20))
        block.add_arc(center=(20, 20), radius=20, start_angle=180, end_angle=270)

        regions = _extract_paint_bucket_regions(block)

        # Should form one closed rounded rectangle region
        assert len(regions) == 1

    def test_real_file_circles_arcs(self) -> None:
        """Test edge extraction from real test file with CIRCLE and ARC entities."""
        doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")

        # Test CIRCLE block
        block_circles = doc.blocks.get("TEST_CIRCLES")
        edges_circles = _extract_all_edges(block_circles)

        # Should have edges from all 3 circles
        assert len(edges_circles) > 30  # Multiple segments per circle

        # Test ARC block
        block_arcs = doc.blocks.get("TEST_ARCS")
        edges_arcs = _extract_all_edges(block_arcs)

        # Should have edges from all 3 arcs
        assert len(edges_arcs) > 15  # Multiple segments per arc
```

### Step 13: Update Test Imports
- Ensure `app/tests/core/test_geometry.py` has all necessary imports at the top:
```python
from shapely.geometry import LineString
```
- The import for `_extract_all_edges` and `_extract_paint_bucket_regions` should already exist

### Step 14: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy
### Unit Tests
- Test each helper function in isolation:
  - `_extract_circle_edges()` produces valid LineString edges
  - `_extract_arc_edges()` produces valid LineString edges
  - `_extract_hatch_boundary_edges()` handles PolylinePath and EdgePath
- Test edge count varies with entity size (adaptive flattening)
- Test error handling for invalid entities

### Integration Tests
- Test `_extract_all_edges()` with mixed entity blocks
- Test `_extract_paint_bucket_regions()` with new entity types
- Test content zone detection with CIRCLE/ARC boundaries
- Test with existing test fixtures (circles_arcs_points.dxf, hatch_test.dxf)

### Edge Cases
- Empty blocks return empty edge lists
- Entities with zero radius/invalid geometry are handled gracefully
- HATCH with multiple boundary paths extracts all paths
- Very small and very large circles produce different segment counts
- HATCH with bulge values produces curved segment approximations
- HATCH EdgePath with ArcEdge components is discretized correctly

### Playwright MCP Tests
Not applicable - this is a backend geometry processing feature with no UI components.

## Acceptance Criteria
- [ ] `ARC_FLATTENING_SAGITTA` constant is defined in `constants.py` with value 0.1
- [ ] `from_hatch` is imported from `ezdxf.path` in `geometry.py`
- [ ] `_extract_circle_edges()` function exists and produces LineString edges
- [ ] `_extract_arc_edges()` function exists and produces LineString edges
- [ ] `_extract_hatch_boundary_edges()` function exists and handles PolylinePath + EdgePath
- [ ] `_extract_all_edges()` handles CIRCLE, ARC, and HATCH entity types
- [ ] All existing tests in `test_geometry.py` continue to pass
- [ ] New unit tests validate CIRCLE, ARC, and HATCH edge extraction
- [ ] Integration tests validate mixed entity blocks
- [ ] Content zone detection works with CIRCLE/ARC boundaries
- [ ] Type checking passes with `uv run mypy app/`
- [ ] Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run python app/tests/assets/create_circle_arc_hatch_edges_test.py` - Generate test DXF fixture
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests with verbose output
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests to verify no regressions
- `uv run pytest app/tests/ -v` - Run full test suite
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting

## Notes
- The sagitta value of 0.1 is appropriate for typical CAD drawings with units in mm or inches. If drawings use significantly different units, this value may need adjustment.
- The `from_hatch()` function automatically handles bulge values, which is critical for correctly extracting curved segments from PolylinePath boundaries.
- Future enhancements could use `ezdxf.path.make_path()` for unified handling of ELLIPSE and SPLINE entities if needed.
- POINT entities have no edges and are intentionally not included in edge extraction.
- The implementation follows the existing pattern in `_extract_all_edges()` for consistency and maintainability.
