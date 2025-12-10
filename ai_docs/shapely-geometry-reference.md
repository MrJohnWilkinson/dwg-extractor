# Shapely Geometry Reference

Reference documentation for Shapely geometry operations used in polygon detection from DXF edges. Covers LineString, polygonize, and related operations.

## LineString

A sequence of points forming a line. Has non-zero length but zero area.

### Creation

```python
from shapely.geometry import LineString

# From coordinate tuples
line = LineString([(0, 0), (1, 1), (2, 0)])

# From list of points
coords = [(0, 0), (10, 10)]
line = LineString(coords)

# Minimum 2 points required
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `coords` | CoordinateSequence | Access to coordinate tuples |
| `length` | float | Total length of the line |
| `bounds` | tuple | Bounding box `(minx, miny, maxx, maxy)` |
| `is_empty` | bool | True if geometry has no points |
| `is_valid` | bool | True if geometry is valid |
| `is_ring` | bool | True if line forms closed ring (start == end) |

### Coordinate Access

```python
line = LineString([(0, 0), (1, 1), (2, 0)])

# Get all coordinates as list
list(line.coords)  # [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]

# Indexing
line.coords[0]     # (0.0, 0.0)
line.coords[-1]    # (2.0, 0.0)

# Slicing
line.coords[1:]    # [(1.0, 1.0), (2.0, 0.0)]
```

### Key Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `interpolate(distance)` | Point | Point at specified distance along line |
| `project(point)` | float | Distance along line to nearest point |
| `simplify(tolerance)` | LineString | Simplified geometry |
| `buffer(distance)` | Polygon | Buffered polygon around line |

---

## polygonize()

Constructs polygons from a set of touching/overlapping lines.

### Import

```python
from shapely.ops import polygonize
```

### Function Signature

```python
def polygonize(lines: Iterable[LineString]) -> GeometryCollection:
    """Construct polygons from lines that form closed rings.

    Args:
        lines: Iterable of LineString objects

    Returns:
        GeometryCollection containing formed Polygon objects.
        Access individual polygons via .geoms attribute.
    """
```

### Usage

```python
from shapely.geometry import LineString
from shapely.ops import polygonize

# Define edges forming a triangle
edges = [
    LineString([(0, 0), (1, 0)]),
    LineString([(1, 0), (0.5, 1)]),
    LineString([(0.5, 1), (0, 0)]),
]

# Create polygons from edges
result = polygonize(edges)

# Access formed polygons
polygons = list(result.geoms)
print(len(polygons))  # 1
print(polygons[0].area)  # 0.5
```

### polygonize_full()

Extended version returning additional diagnostic information.

```python
from shapely.ops import polygonize_full

polygons, cut_edges, dangles, invalid_rings = polygonize_full(edges)
```

| Return Value | Description |
|--------------|-------------|
| `polygons` | GeometryCollection of formed polygons |
| `cut_edges` | Lines that were cut during processing |
| `dangles` | Lines with one end not connected |
| `invalid_rings` | Rings that couldn't form valid polygons |

**Use `polygonize_full()` for debugging when `polygonize()` produces unexpected results.**

---

## Point and buffer()

### Point Creation

```python
from shapely.geometry import Point

# Positional arguments
p = Point(0.0, 0.0)

# Tuple form
p = Point((0.0, 0.0))
```

### buffer() Method

Creates a circular polygon approximation around a point.

```python
def buffer(
    self,
    distance: float,
    quad_segs: int = 16,
    cap_style: str = "round",
    join_style: str = "round"
) -> Polygon:
    """Create buffered polygon.

    Args:
        distance: Buffer radius
        quad_segs: Segments per quarter circle (default 16)

    Returns:
        Polygon approximating a circle (for Point input)
    """
```

**Usage:**

```python
from shapely.geometry import Point

# Create circle approximation
circle = Point(0, 0).buffer(10.0)

# Higher precision
circle_precise = Point(0, 0).buffer(10.0, quad_segs=32)

# Access boundary as LineString
boundary = circle.exterior  # LinearRing
coords = list(boundary.coords)
```

**Note:** With default `quad_segs=16`, the buffer approximates 99.8% of the true circle area.

---

## Common Patterns for Edge Extraction

### Converting DXF Edges to Shapely LineStrings

```python
from shapely.geometry import LineString

def points_to_edges(points: list[tuple[float, float]]) -> list[LineString]:
    """Convert consecutive points to LineString edges."""
    edges = []
    for i in range(len(points) - 1):
        edges.append(LineString([points[i], points[i + 1]]))
    return edges
```

### Paint-Bucket Region Detection

```python
from shapely.geometry import LineString
from shapely.ops import polygonize

def detect_regions(edges: list[LineString]) -> list:
    """Detect enclosed regions from edge set."""
    result = polygonize(edges)
    return list(result.geoms)
```

### Complete Edge-to-Polygon Workflow

```python
from shapely.geometry import LineString, Point
from shapely.ops import polygonize

# 1. Collect edges from various sources
all_edges: list[LineString] = []

# Add line edges
all_edges.append(LineString([(0, 0), (10, 0)]))
all_edges.append(LineString([(10, 0), (10, 10)]))
all_edges.append(LineString([(10, 10), (0, 10)]))
all_edges.append(LineString([(0, 10), (0, 0)]))

# 2. Detect enclosed regions
regions = polygonize(all_edges)

# 3. Process results
for polygon in regions.geoms:
    print(f"Area: {polygon.area}")
    print(f"Centroid: {polygon.centroid}")
    print(f"Bounds: {polygon.bounds}")
```

### Filtering Regions by Point Containment

```python
from shapely.geometry import Point

def find_region_containing_point(
    regions: list,
    point: tuple[float, float]
) -> object | None:
    """Find the region containing a specific point."""
    test_point = Point(point)
    for region in regions:
        if region.contains(test_point):
            return region
    return None
```

---

## Geometry Predicates

Useful for filtering and validation.

| Method | Returns | Description |
|--------|---------|-------------|
| `contains(other)` | bool | True if geometry contains other |
| `within(other)` | bool | True if geometry is within other |
| `intersects(other)` | bool | True if geometries intersect |
| `touches(other)` | bool | True if geometries touch but don't overlap |
| `is_valid` | bool | True if geometry is valid |
| `is_empty` | bool | True if geometry is empty |

---

## Sources

- [Shapely Manual](https://shapely.readthedocs.io/en/stable/manual.html)
- [Shapely 2.0 Documentation](https://shapely.readthedocs.io/en/stable/)
