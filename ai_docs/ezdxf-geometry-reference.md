# ezdxf Geometry Reference

Reference documentation for ezdxf geometry operations used in DXF edge extraction. Covers Arc, Circle, Path, and Hatch entities.

## Arc Entity

DXF type: `'ARC'` - Circular arc defined by center, radius, and angular endpoints.

### DXF Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `dxf.center` | Vec3 | Center point in OCS coordinates |
| `dxf.radius` | float | Arc radius |
| `dxf.start_angle` | float | Starting angle in degrees |
| `dxf.end_angle` | float | Ending angle in degrees |

Arc follows counter-clockwise path from start to end angle.

### flattening() Method

```python
def flattening(self, sagitta: float) -> Iterator[Vec3]:
    """Approximate arc by vertices in WCS.

    Args:
        sagitta: Maximum distance from arc center to chord center.
                 Smaller values = more segments = higher precision.

    Returns:
        Iterator of Vec3 points in World Coordinate System (WCS).
    """
```

**Usage:**

```python
from ezdxf.math import Vec3

# Extract arc as line segments
arc_entity = msp.query("ARC")[0]
points: list[Vec3] = list(arc_entity.flattening(sagitta=0.1))

# Convert to coordinate tuples
coords = [(p.x, p.y) for p in points]
```

### Other Arc Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `start_point` | Vec3 | Arc start point in WCS |
| `end_point` | Vec3 | Arc end point in WCS |
| `angles(num)` | Iterator[float] | Yields `num` angles between start and end |

---

## Circle Entity

DXF type: `'CIRCLE'` - Circle defined by center point and radius.

### DXF Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `dxf.center` | Vec3 | Center point in OCS coordinates |
| `dxf.radius` | float | Circle radius |

### flattening() Method

```python
def flattening(self, sagitta: float) -> Iterator[Vec3]:
    """Approximate circle by polygon vertices in WCS.

    Args:
        sagitta: Maximum distance from arc center to chord center.

    Returns:
        Iterator of Vec3 points. Start vertex equals end vertex (closed polygon).
    """
```

**Usage:**

```python
# Extract circle as closed polygon
circle_entity = msp.query("CIRCLE")[0]
points = list(circle_entity.flattening(sagitta=0.1))

# Note: points[0] == points[-1] (closed)
coords = [(p.x, p.y) for p in points]
```

**Sagitta Selection Guide:**

| Sagitta | Use Case |
|---------|----------|
| 0.01 | High precision (small arcs, detailed work) |
| 0.1 | Standard precision (typical CAD drawings) |
| 1.0 | Low precision (large-scale approximations) |

---

## Path Module

Import: `from ezdxf.path import from_hatch, make_path`

### from_hatch() Function

```python
def from_hatch(hatch: DXFPolygon, offset: Vec3 = NULLVEC) -> Iterator[Path]:
    """Yield all HATCH/MPOLYGON boundary paths as Path objects in WCS.

    Args:
        hatch: A HATCH or MPOLYGON entity
        offset: Optional coordinate offset (default: origin)

    Returns:
        Iterator of Path objects, one per boundary path.
    """
```

**Usage:**

```python
from ezdxf.path import from_hatch

hatch_entity = msp.query("HATCH")[0]

for path in from_hatch(hatch_entity):
    # Flatten path to line segments
    vertices = list(path.flattening(distance=0.1))
    coords = [(v.x, v.y) for v in vertices]
```

**Key Advantage:** `from_hatch()` handles bulge values in PolylinePath automatically, converting curved segments to line approximations.

### make_path() Function

```python
def make_path(entity: DXFEntity) -> Path:
    """Factory function to create Path from DXF entity.

    Supported entity types:
        LINE, CIRCLE, ARC, ELLIPSE, SPLINE, HELIX,
        LWPOLYLINE, 2D/3D POLYLINE, SOLID, TRACE, 3DFACE,
        IMAGE, WIPEOUT, VIEWPORT clipping paths, HATCH

    Raises:
        TypeError: For unsupported entity types
    """
```

**Usage:**

```python
from ezdxf.path import make_path

# Uniform handling for multiple entity types
for entity in msp.query("CIRCLE ARC LWPOLYLINE"):
    path = make_path(entity)
    vertices = list(path.flattening(distance=0.1))
```

### Path.flattening() Method

```python
def flattening(self, distance: float, segments: int = 4) -> Iterator[Vec3]:
    """Approximate path by vertices using adaptive recursive flattening.

    Args:
        distance: Maximum deviation from curve to line segment.
        segments: Minimum subdivision count per Bezier curve.

    Returns:
        Iterator of Vec3 vertices. Empty for empty paths.
    """
```

---

## Hatch Entity

DXF type: `'HATCH'` - Hatched area defined by boundary paths.

### Boundary Path Types

| Type | Identifier | Description |
|------|------------|-------------|
| PolylinePath | `BoundaryPathType.POLYLINE` | Polyline-based boundary with optional bulge |
| EdgePath | `BoundaryPathType.EDGE` | Composed of individual edge segments |

### Accessing Boundary Paths

```python
from ezdxf.entities import BoundaryPathType

hatch = msp.query("HATCH")[0]

for path in hatch.paths:
    if path.path_type == BoundaryPathType.POLYLINE:
        # PolylinePath
        vertices = path.vertices  # List of (x, y, bulge) tuples
        is_closed = path.is_closed
    elif path.path_type == BoundaryPathType.EDGE:
        # EdgePath
        edges = path.edges  # List of edge objects
```

### PolylinePath

| Property | Type | Description |
|----------|------|-------------|
| `vertices` | list[tuple] | List of `(x, y, bulge)` tuples |
| `is_closed` | bool | True if polyline is closed |
| `path_type_flags` | int | Bit flags (1=external, 4=derived, 16=outermost) |

**Bulge Values:**

- `bulge = 0`: Straight segment to next vertex
- `bulge != 0`: Curved (arc) segment to next vertex
- Bulge = tan(angle/4) where angle is the included arc angle

**Direct vertex access misses bulge curves - use `from_hatch()` instead.**

### EdgePath Edge Types

| Edge Type | Properties |
|-----------|------------|
| LineEdge | `start`, `end` (Vec2 points) |
| ArcEdge | `center`, `radius`, `start_angle`, `end_angle`, `ccw` |
| EllipseEdge | `center`, `major_axis`, `ratio`, `start_angle`, `end_angle`, `ccw` |
| SplineEdge | `control_points`, `knot_values`, `degree` |

ArcEdge and EllipseEdge are always counter-clockwise orientation.

---

## Recommended Pattern for Edge Extraction

```python
from ezdxf.path import from_hatch
from shapely.geometry import LineString

ARC_FLATTENING_SAGITTA = 0.1

def extract_circle_edges(entity) -> list[LineString]:
    """Extract edges from CIRCLE entity."""
    points = list(entity.flattening(sagitta=ARC_FLATTENING_SAGITTA))
    edges = []
    for i in range(len(points) - 1):
        edges.append(LineString([
            (points[i].x, points[i].y),
            (points[i + 1].x, points[i + 1].y)
        ]))
    return edges

def extract_arc_edges(entity) -> list[LineString]:
    """Extract edges from ARC entity."""
    points = list(entity.flattening(sagitta=ARC_FLATTENING_SAGITTA))
    edges = []
    for i in range(len(points) - 1):
        edges.append(LineString([
            (points[i].x, points[i].y),
            (points[i + 1].x, points[i + 1].y)
        ]))
    return edges

def extract_hatch_boundary_edges(entity) -> list[LineString]:
    """Extract edges from HATCH boundary paths."""
    edges = []
    for path in from_hatch(entity):
        points = list(path.flattening(distance=ARC_FLATTENING_SAGITTA))
        for i in range(len(points) - 1):
            edges.append(LineString([
                (points[i].x, points[i].y),
                (points[i + 1].x, points[i + 1].y)
            ]))
    return edges
```

---

## Sources

- [Arc - ezdxf documentation](https://ezdxf.readthedocs.io/en/stable/dxfentities/arc.html)
- [Circle - ezdxf documentation](https://ezdxf.readthedocs.io/en/stable/dxfentities/circle.html)
- [Path - ezdxf documentation](https://ezdxf.readthedocs.io/en/stable/path.html)
- [Hatch - ezdxf documentation](https://ezdxf.readthedocs.io/en/stable/dxfentities/hatch.html)
