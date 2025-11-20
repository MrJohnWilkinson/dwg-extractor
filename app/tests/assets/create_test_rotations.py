"""
Script to create test_rotations.dxf fixture with known rotation angles.

This fixture contains blocks at specific rotation angles for testing:
- 5 blocks at 0°
- 3 blocks at 90°
- 2 blocks at 180°
- 1 block at 270°
- 2 blocks at non-standard angles (45°, 135°)
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Create a simple block definition
block = doc.blocks.new(name="TEST_BLOCK")
block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])

# Insert blocks at 0° (5 times)
for i in range(5):
    msp.add_blockref(
        "TEST_BLOCK", (i * 20, 0), dxfattribs={"rotation": 0, "layer": "LAYER_A"}
    )

# Insert blocks at 90° (3 times)
for i in range(3):
    msp.add_blockref(
        "TEST_BLOCK", (i * 20, 20), dxfattribs={"rotation": 90, "layer": "LAYER_A"}
    )

# Insert blocks at 180° (2 times)
for i in range(2):
    msp.add_blockref(
        "TEST_BLOCK", (i * 20, 40), dxfattribs={"rotation": 180, "layer": "LAYER_B"}
    )

# Insert block at 270° (1 time)
msp.add_blockref(
    "TEST_BLOCK", (0, 60), dxfattribs={"rotation": 270, "layer": "LAYER_B"}
)

# Insert blocks at non-standard angles (2 times)
msp.add_blockref(
    "TEST_BLOCK", (20, 60), dxfattribs={"rotation": 45, "layer": "LAYER_C"}
)
msp.add_blockref(
    "TEST_BLOCK", (40, 60), dxfattribs={"rotation": 135, "layer": "LAYER_C"}
)

# Save the DXF file
doc.saveas(
    "/home/john/github-projects-linux/dwg-extractor/app/tests/assets/test_rotations.dxf"
)
print("Created test_rotations.dxf with known rotation angles")
