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
hatch1.paths.add_polyline_path([(0, 0), (100, 0), (100, 50), (0, 50)], is_closed=True)

# Block 4: HATCH with PolylinePath containing bulge (curved segment)
block_hatch_bulge = doc.blocks.new(name="HATCH_BULGE")
hatch2 = block_hatch_bulge.add_hatch()
# Bulge of 0.5 creates an arc between vertices
hatch2.paths.add_polyline_path(
    [(0, 0, 0), (100, 0, 0.5), (100, 50, 0), (0, 50, 0)], is_closed=True
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
    [(150, 20), (180, 20), (180, 40), (150, 40)], is_closed=True
)

# Block 8: Small vs large circles (test adaptive segment count)
block_size_test = doc.blocks.new(name="SIZE_TEST")
block_size_test.add_circle(center=(25, 25), radius=10)  # Small circle
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
