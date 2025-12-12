"""
Script to create a test DXF file for LWPOLYLINE bulge handling.

Creates test fixtures for validating:
- LWPOLYLINE with 90-degree arc bulge segments
- LWPOLYLINE with straight segments only (bulge=0)
- LWPOLYLINE with mixed straight and curved segments
- Closed LWPOLYLINE with arc segments
"""

import math

import ezdxf


# Create a new DXF document
doc = ezdxf.new("R2010")

# Bulge formula: bulge = tan(included_angle / 4)
# 90-degree arc: tan(90/4) = tan(22.5) = 0.41421356
BULGE_90_DEG = math.tan(math.radians(22.5))  # ~0.41421356
# 180-degree arc (semicircle): tan(180/4) = tan(45) = 1.0
BULGE_180_DEG = 1.0

# Block 1: LWPOLYLINE with 90-degree arc bulge
# Creates an L-shape with a 90-degree arc at the corner
block_90deg_arc = doc.blocks.new(name="LWPOLY_90DEG_ARC")
# Start at (0,0), go right to (100,0) with straight line,
# then arc up to (100,100) with 90-degree bulge
# The arc bulges outward (positive bulge = counter-clockwise)
lwpoly1 = block_90deg_arc.add_lwpolyline(
    # Format: (x, y, start_width, end_width, bulge)
    # Bulge applies to segment STARTING from this vertex
    [(0, 0, 0, 0, 0), (100, 0, 0, 0, BULGE_90_DEG), (100, 100, 0, 0, 0)],
    close=False,
)

# Block 2: LWPOLYLINE with straight segments only (no bulge)
block_straight = doc.blocks.new(name="LWPOLY_STRAIGHT")
# Simple L-shape with no arcs
lwpoly2 = block_straight.add_lwpolyline(
    [(0, 0), (100, 0), (100, 100)],
    close=False,
)

# Block 3: LWPOLYLINE with mixed straight and curved segments
block_mixed = doc.blocks.new(name="LWPOLY_MIXED")
# Rectangle-like shape with one curved side
# Bottom: straight, Right: arc (90-deg), Top: straight, Left: straight
lwpoly3 = block_mixed.add_lwpolyline(
    [
        (0, 0, 0, 0, 0),        # Bottom-left, straight to next
        (100, 0, 0, 0, BULGE_90_DEG),  # Bottom-right, 90-deg arc to next
        (100, 100, 0, 0, 0),    # Top-right, straight to next
        (0, 100, 0, 0, 0),      # Top-left, straight to close
    ],
    close=True,
)

# Block 4: Closed LWPOLYLINE with arc segment (semicircle top)
block_closed_arc = doc.blocks.new(name="LWPOLY_CLOSED_ARC")
# Rectangle with semicircular top
# The semicircle bulges outward from (0,50) to (100,50)
lwpoly4 = block_closed_arc.add_lwpolyline(
    [
        (0, 0, 0, 0, 0),        # Bottom-left, straight to next
        (100, 0, 0, 0, 0),      # Bottom-right, straight to next
        (100, 50, 0, 0, BULGE_180_DEG),  # Right side top, semicircle to next
        (0, 50, 0, 0, 0),       # Left side top, straight to close
    ],
    close=True,
)

# Block 5: LWPOLYLINE with inward bulge (negative bulge)
block_inward_arc = doc.blocks.new(name="LWPOLY_INWARD_ARC")
# Same as block 1 but with inward arc (clockwise)
lwpoly5 = block_inward_arc.add_lwpolyline(
    [(0, 0, 0, 0, 0), (100, 0, 0, 0, -BULGE_90_DEG), (100, 100, 0, 0, 0)],
    close=False,
)

# Add block references to modelspace
msp = doc.modelspace()
msp.add_blockref("LWPOLY_90DEG_ARC", (0, 0))
msp.add_blockref("LWPOLY_STRAIGHT", (200, 0))
msp.add_blockref("LWPOLY_MIXED", (0, 200))
msp.add_blockref("LWPOLY_CLOSED_ARC", (200, 200))
msp.add_blockref("LWPOLY_INWARD_ARC", (400, 0))

# Save the file
doc.saveas("app/tests/assets/lwpolyline_bulge_test.dxf")
print("Created lwpolyline_bulge_test.dxf successfully")
