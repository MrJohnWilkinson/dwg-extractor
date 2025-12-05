"""
Script to create a test DXF file simulating A$C anonymous blocks.

A$C blocks are AutoCAD's alternate anonymous block naming convention,
similar to *U blocks but with a different prefix. They represent dynamic
block instances that may or may not have XDATA for name resolution.

This creates test fixtures for validating:
- Resolution of A$C blocks with AcDbBlockRepBTag XDATA to original names
- Resolution of A$C blocks with AcDbDynamicBlockTrueName XDATA (self-referencing = unresolved)
- Handling of A$C blocks without XDATA (use raw name and track in issues)
- Proper processing of unresolved A$C blocks (unlike *U which skips them)
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Register the XDATA application IDs used by AutoCAD
if "AcDbBlockRepBTag" not in doc.appids:
    doc.appids.new("AcDbBlockRepBTag")
if "AcDbDynamicBlockTrueName" not in doc.appids:
    doc.appids.new("AcDbDynamicBlockTrueName")

# Create regular (non-anonymous) block for comparison
regular_block = doc.blocks.new(name="REGULAR_BLOCK")
regular_block.add_lwpolyline([(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)])

# Create A$C block with AcDbBlockRepBTag XDATA (should resolve to SHELF_UNIT)
# Note: A$C names use hexadecimal suffixes (simulating real AutoCAD behavior)
anon_block_1 = doc.blocks.new(name="A$C7F63364D", base_point=(0, 0))
anon_block_1.add_lwpolyline([(0, 0), (30, 0), (30, 15), (0, 15), (0, 0)])
block_record_1 = anon_block_1.block_record
block_record_1.set_xdata("AcDbBlockRepBTag", [(1000, "SHELF_UNIT")])

# Create A$C block with AcDbDynamicBlockTrueName XDATA that self-references (should be unresolved)
# This simulates real-world behavior where some A$C blocks have XDATA but it resolves to itself
anon_block_2 = doc.blocks.new(name="A$C25B30886", base_point=(0, 0))
anon_block_2.add_circle(center=(10, 10), radius=8)
block_record_2 = anon_block_2.block_record
# Self-referencing XDATA - should be treated as unresolved
block_record_2.set_xdata("AcDbDynamicBlockTrueName", [(1000, "A$C25B30886")])

# Create A$C block WITHOUT any XDATA - also unresolved but uses raw name
anon_block_3 = doc.blocks.new(name="A$C0c1c4685", base_point=(0, 0))
anon_block_3.add_line((0, 0), (25, 25))
# No XDATA attached - will use raw A$C name

# Create A$C block with AcDbDynamicBlockGUID only (no useful resolution XDATA)
anon_block_4 = doc.blocks.new(name="A$CABC12345", base_point=(0, 0))
anon_block_4.add_lwpolyline([(0, 0), (20, 0), (20, 20), (0, 20), (0, 0)])
block_record_4 = anon_block_4.block_record
# Only GUID XDATA - not useful for name resolution
if "AcDbDynamicBlockGUID" not in doc.appids:
    doc.appids.new("AcDbDynamicBlockGUID")
block_record_4.set_xdata(
    "AcDbDynamicBlockGUID", [(1000, "{12345678-ABCD-1234-ABCD-123456789ABC}")]
)

# Insert regular blocks
msp.add_blockref("REGULAR_BLOCK", (0, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("REGULAR_BLOCK", (20, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("REGULAR_BLOCK", (0, 20), dxfattribs={"layer": "LAYER_B"})

# Insert A$C block with resolvable XDATA (should become SHELF_UNIT)
msp.add_blockref("A$C7F63364D", (50, 0), dxfattribs={"layer": "LAYER_A", "rotation": 0})
msp.add_blockref(
    "A$C7F63364D", (90, 0), dxfattribs={"layer": "LAYER_A", "rotation": 90}
)
msp.add_blockref(
    "A$C7F63364D",
    (50, 50),
    dxfattribs={"layer": "LAYER_B", "rotation": 0, "xscale": 2.0},
)

# Insert A$C block with self-referencing XDATA (unresolved, uses raw A$C25B30886)
msp.add_blockref("A$C25B30886", (150, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("A$C25B30886", (180, 0), dxfattribs={"layer": "LAYER_B"})

# Insert A$C block with no XDATA (unresolved, uses raw A$C0c1c4685)
msp.add_blockref(
    "A$C0c1c4685", (250, 0), dxfattribs={"layer": "LAYER_A", "rotation": 180}
)
msp.add_blockref("A$C0c1c4685", (280, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref(
    "A$C0c1c4685", (250, 50), dxfattribs={"layer": "LAYER_B", "xscale": -1.0}
)
msp.add_blockref("A$C0c1c4685", (280, 50), dxfattribs={"layer": "LAYER_B"})

# Insert A$C block with GUID-only XDATA (unresolved, uses raw A$CABC12345)
msp.add_blockref("A$CABC12345", (350, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("A$CABC12345", (380, 0), dxfattribs={"layer": "LAYER_B"})
msp.add_blockref("A$CABC12345", (410, 0), dxfattribs={"layer": "LAYER_B"})

# Save DXF file
doc.saveas("app/tests/assets/a_dollar_c_block_test.dxf")
print(
    "Created app/tests/assets/a_dollar_c_block_test.dxf with A$C anonymous block simulation"
)
print("\nExpected results after extraction:")
print("  - REGULAR_BLOCK: 3 insertions (2 on LAYER_A, 1 on LAYER_B)")
print(
    "  - SHELF_UNIT: 3 insertions (2 on LAYER_A, 1 on LAYER_B) - resolved from A$C7F63364D"
)
print(
    "  - A$C25B30886: 2 insertions (1 on LAYER_A, 1 on LAYER_B) - unresolved (self-referencing XDATA)"
)
print(
    "  - A$C0c1c4685: 4 insertions (2 on LAYER_A, 2 on LAYER_B) - unresolved (no XDATA)"
)
print(
    "  - A$CABC12345: 3 insertions (1 on LAYER_A, 2 on LAYER_B) - unresolved (GUID-only XDATA)"
)
print("\nExtraction Issues (unresolved A$C blocks):")
print(
    "  - A$C25B30886: LAYER_A=1, LAYER_B=1 (self-referencing AcDbDynamicBlockTrueName)"
)
print("  - A$C0c1c4685: LAYER_A=2, LAYER_B=2 (no XDATA)")
print("  - A$CABC12345: LAYER_A=1, LAYER_B=2 (only AcDbDynamicBlockGUID)")
print("\nKey differences from *U handling:")
print("  - Unresolved A$C blocks ARE processed (appear in block_counts with raw name)")
print("  - Unresolved *U blocks are NOT processed (only appear in extraction_issues)")
