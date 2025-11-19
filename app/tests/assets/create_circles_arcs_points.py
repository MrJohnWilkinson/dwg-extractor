"""
Script to create a test DXF file with CIRCLE, ARC, and POINT entities.

This file is used for testing _get_block_bounding_box() and _get_intersection_points()
with various entity types.
"""

import ezdxf

# Create a new DXF document
doc = ezdxf.new('R2010')

# Create test blocks with different entity types

# Block 1: Contains CIRCLE entities
block_circles = doc.blocks.new(name='TEST_CIRCLES')
block_circles.add_circle(center=(50, 50), radius=25)  # Circle at (50, 50) with radius 25
block_circles.add_circle(center=(150, 100), radius=30)  # Circle at (150, 100) with radius 30
block_circles.add_circle(center=(100, 150), radius=20)  # Circle at (100, 150) with radius 20

# Block 2: Contains ARC entities
block_arcs = doc.blocks.new(name='TEST_ARCS')
block_arcs.add_arc(center=(100, 100), radius=50, start_angle=0, end_angle=90)
block_arcs.add_arc(center=(200, 150), radius=40, start_angle=45, end_angle=180)
block_arcs.add_arc(center=(150, 50), radius=30, start_angle=270, end_angle=360)

# Block 3: Contains POINT entities
block_points = doc.blocks.new(name='TEST_POINTS')
block_points.add_point(location=(10, 10))
block_points.add_point(location=(50, 30))
block_points.add_point(location=(90, 70))
block_points.add_point(location=(120, 90))

# Block 4: Mixed LINE + CIRCLE + ARC + POINT
block_mixed = doc.blocks.new(name='TEST_MIXED')
block_mixed.add_line(start=(0, 0), end=(200, 0))
block_mixed.add_line(start=(200, 0), end=(200, 100))
block_mixed.add_circle(center=(100, 50), radius=25)
block_mixed.add_arc(center=(150, 75), radius=20, start_angle=0, end_angle=180)
block_mixed.add_point(location=(50, 25))
block_mixed.add_point(location=(175, 85))

# Add some INSERT entities to the modelspace to make this a valid test file
msp = doc.modelspace()
msp.add_blockref('TEST_CIRCLES', (0, 0))
msp.add_blockref('TEST_ARCS', (300, 0))
msp.add_blockref('TEST_POINTS', (600, 0))
msp.add_blockref('TEST_MIXED', (900, 0))

# Save the file
doc.saveas('app/tests/assets/circles_arcs_points.dxf')
print("Created circles_arcs_points.dxf successfully")
