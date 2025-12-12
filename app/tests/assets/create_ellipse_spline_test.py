"""
Script to create a test DXF file for ELLIPSE and SPLINE entity handling.

Creates test fixtures for validating:
- ELLIPSE with various eccentricities (near-circular, elongated, very elongated)
- Partial ellipse (elliptical arc)
- SPLINE with simple and complex control points
- Closed spline
- Mixed ELLIPSE + SPLINE + LINE entities
"""

import math

import ezdxf


# Create a new DXF document
doc = ezdxf.new("R2010")

# Block 1: Near-circular ellipse (ratio ~0.9)
# Semi-major axis = 50, semi-minor = 45, so ratio = 45/50 = 0.9
block_circular = doc.blocks.new(name="ELLIPSE_CIRCULAR")
# Center at (50, 50), major axis along X, ratio 0.9
block_circular.add_ellipse(
    center=(50, 50),
    major_axis=(50, 0),  # Major axis 50 units along X
    ratio=0.9,  # Semi-minor = 50 * 0.9 = 45
)

# Block 2: Elongated ellipse (ratio ~0.5)
block_elongated = doc.blocks.new(name="ELLIPSE_ELONGATED")
# Center at (100, 50), major axis along X, ratio 0.5
block_elongated.add_ellipse(
    center=(100, 50),
    major_axis=(80, 0),  # Major axis 80 units along X
    ratio=0.5,  # Semi-minor = 80 * 0.5 = 40
)

# Block 3: Very elongated ellipse (ratio ~0.2)
block_very_elongated = doc.blocks.new(name="ELLIPSE_VERY_ELONGATED")
# Center at (150, 50), major axis along X, ratio 0.2
block_very_elongated.add_ellipse(
    center=(150, 50),
    major_axis=(100, 0),  # Major axis 100 units along X
    ratio=0.2,  # Semi-minor = 100 * 0.2 = 20
)

# Block 4: Partial ellipse (elliptical arc, 0-180 degrees)
block_arc = doc.blocks.new(name="ELLIPSE_ARC")
# Center at (100, 100), major axis along X
block_arc.add_ellipse(
    center=(100, 100),
    major_axis=(60, 0),
    ratio=0.5,
    start_param=0,  # Start at 0 radians (rightmost point)
    end_param=math.pi,  # End at pi radians (leftmost point) = upper half
)

# Block 5: Simple spline (4 fit points)
block_simple_spline = doc.blocks.new(name="SPLINE_SIMPLE")
# Simple cubic spline with 4 fit points
fit_points = [(0, 0), (50, 100), (100, 100), (150, 0)]
block_simple_spline.add_spline(
    fit_points=fit_points,
    degree=3,
)

# Block 6: Complex spline (8+ fit points)
block_complex_spline = doc.blocks.new(name="SPLINE_COMPLEX")
# Complex spline with 9 fit points forming a wave
fit_points_complex = [
    (0, 50),
    (25, 100),
    (50, 75),
    (75, 100),
    (100, 50),
    (125, 0),
    (150, 25),
    (175, 0),
    (200, 50),
]
block_complex_spline.add_spline(
    fit_points=fit_points_complex,
    degree=3,
)

# Block 7: Closed spline using set_closed method
block_closed_spline = doc.blocks.new(name="SPLINE_CLOSED")
# Create empty spline and set it as closed
# Note: ezdxf requires 3D control points for set_closed
control_points_closed = [
    (50, 0, 0),
    (100, 25, 0),
    (75, 75, 0),
    (25, 75, 0),
    (0, 25, 0),
]
spline_closed = block_closed_spline.add_spline()
spline_closed.set_closed(control_points_closed, degree=3)

# Block 8: Mixed entities (ELLIPSE + SPLINE + LINE)
block_mixed = doc.blocks.new(name="MIXED_ENTITIES")
# Add an ellipse
block_mixed.add_ellipse(
    center=(50, 50),
    major_axis=(40, 0),
    ratio=0.6,
)
# Add a spline
block_mixed.add_spline(
    fit_points=[(0, 100), (50, 150), (100, 100)],
    degree=3,
)
# Add a line extending beyond both
block_mixed.add_line((0, 0), (150, 0))

# Add block references to modelspace
msp = doc.modelspace()
msp.add_blockref("ELLIPSE_CIRCULAR", (0, 0))
msp.add_blockref("ELLIPSE_ELONGATED", (200, 0))
msp.add_blockref("ELLIPSE_VERY_ELONGATED", (0, 200))
msp.add_blockref("ELLIPSE_ARC", (200, 200))
msp.add_blockref("SPLINE_SIMPLE", (0, 400))
msp.add_blockref("SPLINE_COMPLEX", (200, 400))
msp.add_blockref("SPLINE_CLOSED", (0, 600))
msp.add_blockref("MIXED_ENTITIES", (200, 600))

# Save the file
doc.saveas("app/tests/assets/ellipse_spline_test.dxf")
print("Created ellipse_spline_test.dxf successfully")
