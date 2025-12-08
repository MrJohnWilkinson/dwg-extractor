"""
Script to create a test DXF file for content zone detection testing.

This file contains blocks with various shapes for testing:
- NESTED_RECTANGLES: Outer and inner rectangle using closed LWPOLYLINE
- CHAMFERED_SHAPE: Rectangle with chamfered corners using LINE segments
- MIXED_SHAPES: Multiple LWPOLYLINE shapes for containment testing
- SINGLE_RECTANGLE: Single closed LWPOLYLINE
- OPEN_POLYLINE: Non-closed LWPOLYLINE (should be ignored)
- LINE_RECTANGLE: Simple rectangle using LINE segments
"""

import ezdxf


# Create a new DXF document
doc = ezdxf.new("R2010")

# Block 1: NESTED_RECTANGLES - Two nested rectangles using closed LWPOLYLINE
block_nested = doc.blocks.new(name="NESTED_RECTANGLES")
# Outer rectangle: (0, 0) to (100, 80)
block_nested.add_lwpolyline(
    [(0, 0), (100, 0), (100, 80), (0, 80)],
    close=True,
)
# Inner rectangle: (10, 10) to (90, 70) - content zone
block_nested.add_lwpolyline(
    [(10, 10), (90, 10), (90, 70), (10, 70)],
    close=True,
)

# Block 2: CHAMFERED_SHAPE - Rectangle with chamfered corners using LINE segments
block_chamfered = doc.blocks.new(name="CHAMFERED_SHAPE")
# Create a rectangle 100x60 with 5-unit chamfers at corners
# Using LINE segments that form a closed cycle
chamfer = 5
# Bottom edge
block_chamfered.add_line((chamfer, 0), (100 - chamfer, 0))
# Bottom-right chamfer
block_chamfered.add_line((100 - chamfer, 0), (100, chamfer))
# Right edge
block_chamfered.add_line((100, chamfer), (100, 60 - chamfer))
# Top-right chamfer
block_chamfered.add_line((100, 60 - chamfer), (100 - chamfer, 60))
# Top edge
block_chamfered.add_line((100 - chamfer, 60), (chamfer, 60))
# Top-left chamfer
block_chamfered.add_line((chamfer, 60), (0, 60 - chamfer))
# Left edge
block_chamfered.add_line((0, 60 - chamfer), (0, chamfer))
# Bottom-left chamfer
block_chamfered.add_line((0, chamfer), (chamfer, 0))

# Block 3: MIXED_SHAPES - Multiple shapes for containment testing
block_mixed = doc.blocks.new(name="MIXED_SHAPES")
# Large outer shape
block_mixed.add_lwpolyline(
    [(0, 0), (200, 0), (200, 150), (0, 150)],
    close=True,
)
# Medium inner shape (contained by outer)
block_mixed.add_lwpolyline(
    [(20, 20), (180, 20), (180, 130), (20, 130)],
    close=True,
)
# Small innermost shape (contained by medium)
block_mixed.add_lwpolyline(
    [(50, 50), (150, 50), (150, 100), (50, 100)],
    close=True,
)

# Block 4: SINGLE_RECTANGLE - Just one closed polyline
block_single = doc.blocks.new(name="SINGLE_RECTANGLE")
block_single.add_lwpolyline(
    [(0, 0), (50, 0), (50, 30), (0, 30)],
    close=True,
)

# Block 5: OPEN_POLYLINE - Non-closed polyline (should be ignored)
block_open = doc.blocks.new(name="OPEN_POLYLINE")
block_open.add_lwpolyline(
    [(0, 0), (50, 0), (50, 30), (0, 30)],
    close=False,  # Not closed!
)
# Add a closed one to make the block valid
block_open.add_lwpolyline(
    [(60, 0), (110, 0), (110, 30), (60, 30)],
    close=True,
)

# Block 6: LINE_RECTANGLE - Simple rectangle using LINE segments
block_line_rect = doc.blocks.new(name="LINE_RECTANGLE")
block_line_rect.add_line((0, 0), (80, 0))
block_line_rect.add_line((80, 0), (80, 50))
block_line_rect.add_line((80, 50), (0, 50))
block_line_rect.add_line((0, 50), (0, 0))

# Block 7: EMPTY_BLOCK - No geometric entities
block_empty = doc.blocks.new(name="EMPTY_BLOCK")
# Just add a text entity which doesn't count as geometry for content zone
block_empty.add_text("Empty", dxfattribs={"height": 5})

# Block 8: TWO_DISJOINT_RECTANGLES - Two non-overlapping rectangles
block_disjoint = doc.blocks.new(name="TWO_DISJOINT_RECTANGLES")
block_disjoint.add_lwpolyline(
    [(0, 0), (40, 0), (40, 30), (0, 30)],
    close=True,
)
block_disjoint.add_lwpolyline(
    [(60, 0), (100, 0), (100, 30), (60, 30)],
    close=True,
)

# Add block references to modelspace
msp = doc.modelspace()
msp.add_blockref("NESTED_RECTANGLES", (0, 0))
msp.add_blockref("CHAMFERED_SHAPE", (150, 0))
msp.add_blockref("MIXED_SHAPES", (300, 0))
msp.add_blockref("SINGLE_RECTANGLE", (0, 100))
msp.add_blockref("OPEN_POLYLINE", (100, 100))
msp.add_blockref("LINE_RECTANGLE", (200, 100))
msp.add_blockref("EMPTY_BLOCK", (300, 100))
msp.add_blockref("TWO_DISJOINT_RECTANGLES", (0, 200))

# Save the file
doc.saveas("app/tests/assets/content_zone_test.dxf")
print("Created content_zone_test.dxf successfully")
