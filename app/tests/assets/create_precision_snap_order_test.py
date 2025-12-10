"""
Script to create a test DXF file for precision snap order fix testing.

This file contains a block with LINE entities that have floating-point
precision errors in their endpoint coordinates, simulating the real-world
case where AutoCAD exports have nanometer-scale precision artifacts.

Block: PRECISION_ERROR_SHELF
- A closed LWPOLYLINE rectangle (0,0) to (900, 1200)
- Two horizontal LINE dividers at Y=400 and Y=800
- Left endpoints are exact: (0, 400), (0, 800)
- Right endpoints have precision error: (899.9999999962746, 400.0000000002328)
- Expected: 3 horizontal regions when snapped correctly before union
- Bug behavior: 1 region when snap happens after union (dividers don't split)
"""

import ezdxf


# Create a new DXF document
doc = ezdxf.new("R2010")

# Block: PRECISION_ERROR_SHELF
block = doc.blocks.new(name="PRECISION_ERROR_SHELF")

# Outer rectangle: closed LWPOLYLINE from (0,0) to (900, 1200)
block.add_lwpolyline(
    [(0, 0), (900, 0), (900, 1200), (0, 1200)],
    close=True,
)

# Horizontal divider 1 at Y=400 with precision error on right endpoint
# Left endpoint is exact, right endpoint has floating-point precision error
block.add_line(
    (0, 400),  # Exact left endpoint
    (899.9999999962746, 400.0000000002328),  # Right endpoint with precision error
)

# Horizontal divider 2 at Y=800 with precision error on right endpoint
block.add_line(
    (0, 800),  # Exact left endpoint
    (899.9999999962746, 800.0000000002328),  # Right endpoint with precision error
)

# Add block reference to modelspace
msp = doc.modelspace()
msp.add_blockref("PRECISION_ERROR_SHELF", (0, 0))

# Save the file
doc.saveas("app/tests/assets/precision_snap_order_test.dxf")
print("Created precision_snap_order_test.dxf successfully")
