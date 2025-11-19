"""
Script to create a test DXF file with XDATA scenarios.

This creates test fixtures for validating the XDATA application ID detection feature.
The file includes blocks with:
- Blocks with multiple XDATA application IDs on one layer
- Blocks with different XDATA application IDs on different layers
- Blocks without XDATA for comparison
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Register XDATA application IDs (required before attaching XDATA)
# Note: ACAD already exists by default in ezdxf
if "CUSTOM_APP" not in doc.appids:
    doc.appids.new("CUSTOM_APP")
if "BIM_TOOL" not in doc.appids:
    doc.appids.new("BIM_TOOL")

# Create block definitions with simple geometry
# Block 1: WITH_XDATA - will have XDATA attached
block_with_xdata = doc.blocks.new(name="WITH_XDATA")
block_with_xdata.add_lwpolyline([(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)])

# Block 2: NO_XDATA - will have no XDATA attached
block_no_xdata = doc.blocks.new(name="NO_XDATA")
block_no_xdata.add_circle(center=(5, 5), radius=3)

# Insert WITH_XDATA blocks on LAYER_A with XDATA from ACAD and CUSTOM_APP
insert1 = msp.add_blockref("WITH_XDATA", (0, 0), dxfattribs={"layer": "LAYER_A"})
insert1.set_xdata("ACAD", [(1000, "ACAD metadata")])

insert2 = msp.add_blockref("WITH_XDATA", (20, 0), dxfattribs={"layer": "LAYER_A"})
insert2.set_xdata("CUSTOM_APP", [(1000, "Custom data")])

insert3 = msp.add_blockref("WITH_XDATA", (40, 0), dxfattribs={"layer": "LAYER_A"})
insert3.set_xdata("ACAD", [(1000, "More ACAD data")])
insert3.set_xdata("CUSTOM_APP", [(1000, "More custom data")])

# Insert WITH_XDATA blocks on LAYER_B with XDATA from BIM_TOOL and ACAD
insert4 = msp.add_blockref("WITH_XDATA", (0, 20), dxfattribs={"layer": "LAYER_B"})
insert4.set_xdata("BIM_TOOL", [(1000, "BIM metadata")])

insert5 = msp.add_blockref("WITH_XDATA", (20, 20), dxfattribs={"layer": "LAYER_B"})
insert5.set_xdata("ACAD", [(1000, "ACAD on layer B")])
insert5.set_xdata("BIM_TOOL", [(1000, "More BIM data")])

# Insert NO_XDATA blocks on LAYER_A with no XDATA
msp.add_blockref("NO_XDATA", (0, 40), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("NO_XDATA", (20, 40), dxfattribs={"layer": "LAYER_A"})

# Save DXF file
doc.saveas("app/tests/assets/xdata_test.dxf")
print("Created app/tests/assets/xdata_test.dxf with XDATA scenarios")
