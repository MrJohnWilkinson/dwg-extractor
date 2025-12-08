# Logical Rules for Defining Polygons/Regions in a Drawing

## The Paint Bucket Principle

> **Operational Definition**: Imagine using a paint bucket tool—each region is a separate area that would fill independently. Count how many times you'd need to click to fill the entire figure.

This concept maps directly to **faces in a planar graph**, excluding the unbounded exterior.

---

## Core Definitions

### Primitives

| Term | Definition |
|------|------------|
| **Vertex** | A point where edges meet or terminate |
| **Edge** | A line segment (or curve) connecting two vertices |
| **Region/Face** | A maximal connected area bounded by edges (excluding the infinite exterior) |

---

## Rule Set

### Rule 1: Edge Intersection Creates Vertices

```
IF edge_A intersects edge_B at point P
THEN P becomes a vertex, splitting both edges
```

Every crossing point must be treated as a vertex, even if not explicitly drawn as one.

---

### Rule 2: Closed Boundary Requirement

```
A region exists IFF it is bounded by a closed loop of connected edges
WHERE start_vertex == end_vertex
```

Open paths and dangling edges do not create regions.

---

### Rule 3: Minimal Enclosure (Atomic Region)

```
A region is ATOMIC (single paint-bucket fill) IFF
it contains no other closed boundaries within it
```

This distinguishes:
- A **donut** → 2 regions (the ring + the hole's interior)
- A **solid circle** → 1 region

---

### Rule 4: Adjacency via Shared Edges

```
IF region_A and region_B share an edge
THEN they are adjacent but distinct regions
```

Interior edges are shared by exactly **2 regions**. Boundary edges (touching the exterior) belong to only **1 counted region**.

---

### Rule 5: Exclude the Unbounded Exterior

```
The infinite area outside all edges is NOT counted as a region
```

Only enclosed, finite areas are counted. The "background" or "canvas" is ignored.

---

## Region Count Formula

For a connected planar graph, the count of interior regions can be derived from Euler's formula:

```
Regions = Edges - Vertices + 1
```

*(This is a simplification of V - E + F = 2, solving for F - 1 to exclude the exterior face)*

---

## Algorithmic Detection

| Step | Operation |
|------|-----------|
| 1 | **Collect** all edges from the drawing |
| 2 | **Intersect** — find all crossing points, split edges at intersections |
| 3 | **Build graph** — create vertex and edge-segment lists |
| 4 | **Trace faces** — walk edges using the "leftmost turn" rule to find minimal cycles |
| 5 | **Filter** — discard the unbounded exterior face |
| 6 | **Classify** — optionally build containment hierarchy (nesting relationships) |

---

## Edge Cases

| Scenario | Treatment |
|----------|-----------|
| **Dangling edge** (dead end) | Does NOT create a region—no closed boundary |
| **Self-intersecting polygon** | Creates multiple regions at each intersection |
| **Coincident/overlapping edges** | Treat as single edge (or flag as error) |
| **Nested shapes** (e.g., hole) | Each closed boundary creates its own region |
| **Touching but not crossing** | Shared vertex only; no edge split needed |
| **Disconnected shapes** | Each closed shape counted independently |

---

## Summary

A **region** in a CAD drawing or block is:

1. ✅ Bounded by a closed loop of edges
2. ✅ Atomic (contains no smaller closed loops)
3. ✅ Finite (not the unbounded exterior)
4. ✅ Fillable with a single paint-bucket click