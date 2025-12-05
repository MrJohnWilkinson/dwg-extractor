"""
Script to create a test DXF file simulating orphaned dynamic block handles.

This creates a test fixture for validating:
- Proper reporting when XDATA contains a handle that doesn't exist in the document
- Distinction between "no XDATA" vs "orphaned handle" in error messages
- The scenario where original block definition was purged but instances remain

Orphaned dynamic blocks occur when:
1. A dynamic block is inserted multiple times in a drawing
2. The original block definition is later purged/deleted
3. The anonymous block instances remain with XDATA pointing to the deleted block
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Register the AcDbBlockRepBTag application ID for XDATA
if "AcDbBlockRepBTag" not in doc.appids:
    doc.appids.new("AcDbBlockRepBTag")

# Create regular (non-anonymous) block for comparison
regular_block = doc.blocks.new(name="REGULAR_BLOCK")
regular_block.add_lwpolyline([(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)])

# Create a valid original block that will be resolved
valid_original_block = doc.blocks.new(name="VALID_ORIGINAL")
valid_original_block.add_lwpolyline([(0, 0), (20, 0), (20, 10), (0, 10), (0, 0)])
valid_block_handle = valid_original_block.block_record.dxf.handle

# Create anonymous block *U1 with valid handle reference (should resolve)
anon_block_1 = doc.blocks.new(name="*U1", base_point=(0, 0))
anon_block_1.add_lwpolyline([(0, 0), (20, 0), (20, 10), (0, 10), (0, 0)])
block_record_1 = anon_block_1.block_record
block_record_1.set_xdata("AcDbBlockRepBTag", [(1005, valid_block_handle)])

# Create anonymous block *U999 with ORPHANED handle reference
# This simulates a dynamic block whose original definition was purged
# The handle B0DE5 doesn't exist in the document
anon_block_orphan = doc.blocks.new(name="*U999", base_point=(0, 0))
anon_block_orphan.add_lwpolyline([(0, 0), (30, 0), (30, 15), (0, 15), (0, 0)])
block_record_orphan = anon_block_orphan.block_record
# Use a handle that doesn't exist in the document - simulates purged block
block_record_orphan.set_xdata("AcDbBlockRepBTag", [(1005, "B0DE5")])

# Create anonymous block *U888 with another orphaned handle
anon_block_orphan2 = doc.blocks.new(name="*U888", base_point=(0, 0))
anon_block_orphan2.add_circle(center=(10, 10), radius=8)
block_record_orphan2 = anon_block_orphan2.block_record
# Different orphaned handle
block_record_orphan2.set_xdata("AcDbBlockRepBTag", [(1005, "DEADBEEF")])

# Create anonymous block *U777 WITHOUT any XDATA (for comparison)
# This should report "No XDATA found" vs orphaned handle's different message
anon_block_no_xdata = doc.blocks.new(name="*U777", base_point=(0, 0))
anon_block_no_xdata.add_line((0, 0), (25, 25))
# No XDATA attached

# Insert regular blocks
msp.add_blockref("REGULAR_BLOCK", (0, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("REGULAR_BLOCK", (20, 0), dxfattribs={"layer": "LAYER_B"})

# Insert valid resolved blocks (*U1 -> VALID_ORIGINAL)
msp.add_blockref("*U1", (50, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U1", (70, 0), dxfattribs={"layer": "LAYER_B"})

# Insert orphaned blocks (*U999 with non-existent handle B0DE5)
msp.add_blockref("*U999", (100, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U999", (120, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U999", (140, 0), dxfattribs={"layer": "LAYER_B"})

# Insert more orphaned blocks (*U888 with non-existent handle DEADBEEF)
msp.add_blockref("*U888", (200, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U888", (220, 0), dxfattribs={"layer": "LAYER_B"})

# Insert blocks without XDATA (*U777)
msp.add_blockref("*U777", (300, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U777", (320, 0), dxfattribs={"layer": "LAYER_B"})
msp.add_blockref("*U777", (340, 0), dxfattribs={"layer": "LAYER_B"})

# Save DXF file
doc.saveas("app/tests/assets/orphaned_handle_test.dxf")
print("Created app/tests/assets/orphaned_handle_test.dxf with orphaned handle XDATA")
print("\nExpected results after extraction:")
print("  - REGULAR_BLOCK: 2 insertions (1 on LAYER_A, 1 on LAYER_B)")
print(
    "  - VALID_ORIGINAL: 2 insertions (1 on LAYER_A, 1 on LAYER_B) - resolved from *U1"
)
print("\nExtraction Issues (unresolved anonymous blocks):")
print("  - *U999 on LAYER_A: 2 insertions (orphaned handle B0DE5)")
print("  - *U999 on LAYER_B: 1 insertion (orphaned handle B0DE5)")
print("  - *U888 on LAYER_A: 1 insertion (orphaned handle DEADBEEF)")
print("  - *U888 on LAYER_B: 1 insertion (orphaned handle DEADBEEF)")
print("  - *U777 on LAYER_A: 1 insertion (no XDATA)")
print("  - *U777 on LAYER_B: 2 insertions (no XDATA)")
print("\nKey test: *U999/*U888 should report 'Handle X not found' not 'No XDATA found'")
