"""
Script to create a test DXF file with scale variance scenarios.

This creates test fixtures for validating the scale variance detection feature.
The file includes blocks with:
- Same block at different X scales (Y consistent)
- Same block at different Y scales (X consistent)
- Same block at different X and Y scales
- Same block at consistent scales across multiple insertions
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Create block definitions with simple geometry
# Block 1: X_VARIES - will be inserted with varying X scales
block_x_varies = doc.blocks.new(name="X_VARIES")
block_x_varies.add_lwpolyline([(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)])

# Block 2: Y_VARIES - will be inserted with varying Y scales
block_y_varies = doc.blocks.new(name="Y_VARIES")
block_y_varies.add_lwpolyline([(0, 0), (8, 0), (8, 4), (0, 4), (0, 0)])

# Block 3: BOTH_VARY - will be inserted with varying X and Y scales
block_both_vary = doc.blocks.new(name="BOTH_VARY")
block_both_vary.add_lwpolyline([(0, 0), (6, 0), (6, 6), (0, 6), (0, 0)])

# Block 4: CONSISTENT - will be inserted with consistent scales
block_consistent = doc.blocks.new(name="CONSISTENT")
block_consistent.add_lwpolyline([(0, 0), (5, 0), (5, 3), (0, 3), (0, 0)])

# Insert X_VARIES block with varying X scales (Y consistent at 1.0)
msp.add_blockref("X_VARIES", (0, 0), dxfattribs={"layer": "LAYER_A", "xscale": 1.0, "yscale": 1.0, "rotation": 0})
msp.add_blockref("X_VARIES", (20, 0), dxfattribs={"layer": "LAYER_A", "xscale": 2.0, "yscale": 1.0, "rotation": 0})
msp.add_blockref("X_VARIES", (40, 0), dxfattribs={"layer": "LAYER_B", "xscale": 1.5, "yscale": 1.0, "rotation": 0})

# Insert Y_VARIES block with varying Y scales (X consistent at 1.0)
msp.add_blockref("Y_VARIES", (0, 20), dxfattribs={"layer": "LAYER_A", "xscale": 1.0, "yscale": 1.0, "rotation": 0})
msp.add_blockref("Y_VARIES", (20, 20), dxfattribs={"layer": "LAYER_A", "xscale": 1.0, "yscale": 2.0, "rotation": 0})
msp.add_blockref("Y_VARIES", (40, 20), dxfattribs={"layer": "LAYER_B", "xscale": 1.0, "yscale": 0.5, "rotation": 0})

# Insert BOTH_VARY block with varying X and Y scales
msp.add_blockref("BOTH_VARY", (0, 40), dxfattribs={"layer": "LAYER_A", "xscale": 1.0, "yscale": 1.0, "rotation": 0})
msp.add_blockref("BOTH_VARY", (20, 40), dxfattribs={"layer": "LAYER_A", "xscale": 2.0, "yscale": 2.0, "rotation": 0})
msp.add_blockref("BOTH_VARY", (40, 40), dxfattribs={"layer": "LAYER_B", "xscale": -1.0, "yscale": 1.5, "rotation": 0})

# Insert CONSISTENT block with consistent scales across multiple insertions
msp.add_blockref("CONSISTENT", (0, 60), dxfattribs={"layer": "LAYER_A", "xscale": 1.5, "yscale": 1.5, "rotation": 0})
msp.add_blockref("CONSISTENT", (20, 60), dxfattribs={"layer": "LAYER_A", "xscale": 1.5, "yscale": 1.5, "rotation": 0})
msp.add_blockref("CONSISTENT", (40, 60), dxfattribs={"layer": "LAYER_B", "xscale": 1.5, "yscale": 1.5, "rotation": 0})
msp.add_blockref("CONSISTENT", (60, 60), dxfattribs={"layer": "LAYER_B", "xscale": 1.5, "yscale": 1.5, "rotation": 90})

# Save DXF file
doc.saveas("scale_variance_test.dxf")
print("Created scale_variance_test.dxf with scale variance scenarios")
