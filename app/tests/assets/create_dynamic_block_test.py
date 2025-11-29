"""
Script to create a test DXF file simulating dynamic blocks from DWG conversion.

When AutoCAD saves a DWG with dynamic blocks to DXF format, it converts
dynamic block definitions to anonymous blocks (names starting with *U).
The original block name is preserved in XDATA under 'AcDbBlockRepBTag'.

This creates test fixtures for validating:
- Resolution of anonymous blocks (*U1, *U2) to original names via XDATA
- Tracking of unresolved anonymous blocks without XDATA
- Proper counting under resolved names instead of anonymous names
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Register the AcDbBlockRepBTag application ID for XDATA
# This is what AutoCAD uses to store original dynamic block names
if "AcDbBlockRepBTag" not in doc.appids:
    doc.appids.new("AcDbBlockRepBTag")

# Create regular (non-anonymous) block for comparison
regular_block = doc.blocks.new(name="REGULAR_BLOCK")
regular_block.add_lwpolyline([(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)])

# Create anonymous blocks simulating dynamic block conversion
# Anonymous block *U1 with XDATA containing original name "DOOR_DYNAMIC"
anon_block_1 = doc.blocks.new(name="*U1", base_point=(0, 0))
anon_block_1.add_lwpolyline([(0, 0), (20, 0), (20, 10), (0, 10), (0, 0)])
# Attach XDATA with original block name to the block record
block_record_1 = anon_block_1.block_record
block_record_1.set_xdata("AcDbBlockRepBTag", [(1000, "DOOR_DYNAMIC")])

# Anonymous block *U2 with XDATA containing original name "WINDOW_DYNAMIC"
anon_block_2 = doc.blocks.new(name="*U2", base_point=(0, 0))
anon_block_2.add_circle(center=(5, 5), radius=3)
block_record_2 = anon_block_2.block_record
block_record_2.set_xdata("AcDbBlockRepBTag", [(1000, "WINDOW_DYNAMIC")])

# Anonymous block *U3 WITHOUT XDATA - simulates unresolved anonymous block
anon_block_3 = doc.blocks.new(name="*U3", base_point=(0, 0))
anon_block_3.add_line((0, 0), (15, 15))
# No XDATA attached - will be reported as extraction issue

# Insert regular blocks
msp.add_blockref("REGULAR_BLOCK", (0, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("REGULAR_BLOCK", (20, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("REGULAR_BLOCK", (0, 20), dxfattribs={"layer": "LAYER_B"})

# Insert anonymous blocks with XDATA (should resolve to DOOR_DYNAMIC)
msp.add_blockref("*U1", (50, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U1", (70, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U1", (90, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U1", (50, 20), dxfattribs={"layer": "LAYER_B"})

# Insert anonymous blocks with XDATA (should resolve to WINDOW_DYNAMIC)
msp.add_blockref("*U2", (100, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U2", (120, 0), dxfattribs={"layer": "LAYER_B"})
msp.add_blockref("*U2", (140, 0), dxfattribs={"layer": "LAYER_B"})

# Insert anonymous blocks WITHOUT XDATA (should be reported as extraction issues)
msp.add_blockref("*U3", (200, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U3", (220, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U3", (240, 0), dxfattribs={"layer": "LAYER_B"})
msp.add_blockref("*U3", (260, 0), dxfattribs={"layer": "LAYER_B"})
msp.add_blockref("*U3", (280, 0), dxfattribs={"layer": "LAYER_B"})

# Save DXF file
doc.saveas("app/tests/assets/dynamic_block_test.dxf")
print("Created app/tests/assets/dynamic_block_test.dxf with dynamic block simulation")
print("\nExpected results after extraction:")
print("  - REGULAR_BLOCK: 3 insertions (2 on LAYER_A, 1 on LAYER_B)")
print("  - DOOR_DYNAMIC: 4 insertions (3 on LAYER_A, 1 on LAYER_B)")
print("  - WINDOW_DYNAMIC: 3 insertions (1 on LAYER_A, 2 on LAYER_B)")
print("\nExtraction Issues:")
print("  - *U3 on LAYER_A: 2 insertions (unresolved)")
print("  - *U3 on LAYER_B: 3 insertions (unresolved)")
