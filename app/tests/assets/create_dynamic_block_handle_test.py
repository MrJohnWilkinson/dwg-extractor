"""
Script to create a test DXF file simulating dynamic blocks with handle-based XDATA.

Real AutoCAD DWG-to-DXF conversions store the original block name as a database
handle reference (tag code 1005) in XDATA rather than a direct string (tag code 1000).
This creates test fixtures for validating handle resolution.

This creates test fixtures for validating:
- Resolution of anonymous blocks via handle reference (tag code 1005) in XDATA
- Proper lookup through doc.entitydb to resolve handle to block name
- Backwards compatibility with direct string storage (tag code 1000)
- Graceful handling of invalid handles
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

# Create the original block definition that the handle will point to
# This is what the anonymous block's handle in XDATA should resolve to
original_door_block = doc.blocks.new(name="DOOR_HANDLE_TEST")
original_door_block.add_lwpolyline([(0, 0), (30, 0), (30, 15), (0, 15), (0, 0)])
# Get the handle of the original block's block_record
door_block_handle = original_door_block.block_record.dxf.handle

# Create another original block for second anonymous block test
original_window_block = doc.blocks.new(name="WINDOW_HANDLE_TEST")
original_window_block.add_circle(center=(10, 10), radius=8)
window_block_handle = original_window_block.block_record.dxf.handle

# Create anonymous block *U1 with XDATA containing handle reference (tag code 1005)
# This simulates real AutoCAD DXF export behavior
anon_block_1 = doc.blocks.new(name="*U1", base_point=(0, 0))
anon_block_1.add_lwpolyline([(0, 0), (30, 0), (30, 15), (0, 15), (0, 0)])
block_record_1 = anon_block_1.block_record
# Use tag code 1005 (database handle) instead of 1000 (string)
block_record_1.set_xdata("AcDbBlockRepBTag", [(1005, door_block_handle)])

# Create anonymous block *U2 with XDATA containing handle reference
anon_block_2 = doc.blocks.new(name="*U2", base_point=(0, 0))
anon_block_2.add_circle(center=(10, 10), radius=8)
block_record_2 = anon_block_2.block_record
block_record_2.set_xdata("AcDbBlockRepBTag", [(1005, window_block_handle)])

# Create anonymous block *U3 with XDATA containing INVALID handle
# This tests graceful error handling when handle doesn't exist
anon_block_3 = doc.blocks.new(name="*U3", base_point=(0, 0))
anon_block_3.add_line((0, 0), (20, 20))
block_record_3 = anon_block_3.block_record
# Use a handle that doesn't exist in the document
block_record_3.set_xdata("AcDbBlockRepBTag", [(1005, "DEADBEEF")])

# Create anonymous block *U4 with XDATA containing direct string (tag code 1000)
# This tests backwards compatibility with existing test fixtures
anon_block_4 = doc.blocks.new(name="*U4", base_point=(0, 0))
anon_block_4.add_line((0, 0), (25, 25))
block_record_4 = anon_block_4.block_record
# Use tag code 1000 (direct string) - should still work
block_record_4.set_xdata("AcDbBlockRepBTag", [(1000, "DIRECT_STRING_BLOCK")])

# Create anonymous block *U5 WITHOUT XDATA - simulates completely unresolved block
anon_block_5 = doc.blocks.new(name="*U5", base_point=(0, 0))
anon_block_5.add_line((0, 0), (15, 15))
# No XDATA attached

# Insert regular blocks
msp.add_blockref("REGULAR_BLOCK", (0, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("REGULAR_BLOCK", (20, 0), dxfattribs={"layer": "LAYER_B"})

# Insert anonymous blocks with handle XDATA (should resolve to DOOR_HANDLE_TEST)
msp.add_blockref("*U1", (50, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U1", (70, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U1", (90, 0), dxfattribs={"layer": "LAYER_B"})

# Insert anonymous blocks with handle XDATA (should resolve to WINDOW_HANDLE_TEST)
msp.add_blockref("*U2", (100, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U2", (120, 0), dxfattribs={"layer": "LAYER_B"})

# Insert anonymous blocks with invalid handle (should be unresolved)
msp.add_blockref("*U3", (200, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U3", (220, 0), dxfattribs={"layer": "LAYER_B"})
msp.add_blockref("*U3", (240, 0), dxfattribs={"layer": "LAYER_B"})

# Insert anonymous blocks with direct string XDATA (should resolve to DIRECT_STRING_BLOCK)
msp.add_blockref("*U4", (300, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U4", (320, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U4", (340, 0), dxfattribs={"layer": "LAYER_B"})
msp.add_blockref("*U4", (360, 0), dxfattribs={"layer": "LAYER_B"})

# Insert anonymous blocks without XDATA (should be unresolved)
msp.add_blockref("*U5", (400, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("*U5", (420, 0), dxfattribs={"layer": "LAYER_B"})

# Save DXF file
doc.saveas("app/tests/assets/dynamic_block_handle_test.dxf")
print("Created app/tests/assets/dynamic_block_handle_test.dxf with handle-based XDATA")
print("\nExpected results after extraction:")
print("  - REGULAR_BLOCK: 2 insertions (1 on LAYER_A, 1 on LAYER_B)")
print(
    "  - DOOR_HANDLE_TEST: 3 insertions (2 on LAYER_A, 1 on LAYER_B) - resolved from *U1 via handle"
)
print(
    "  - WINDOW_HANDLE_TEST: 2 insertions (1 on LAYER_A, 1 on LAYER_B) - resolved from *U2 via handle"
)
print(
    "  - DIRECT_STRING_BLOCK: 4 insertions (2 on LAYER_A, 2 on LAYER_B) - resolved from *U4 via string"
)
print("\nExtraction Issues (unresolved anonymous blocks):")
print("  - *U3 on LAYER_A: 1 insertion (invalid handle)")
print("  - *U3 on LAYER_B: 2 insertions (invalid handle)")
print("  - *U5 on LAYER_A: 1 insertion (no XDATA)")
print("  - *U5 on LAYER_B: 1 insertion (no XDATA)")
