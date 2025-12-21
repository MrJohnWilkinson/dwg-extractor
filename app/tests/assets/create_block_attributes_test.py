"""
Create test DXF file with block attributes (ATTRIB entities).

This script generates a DXF file with blocks containing attribute definitions
and insertions with populated attribute values for testing attribute extraction.
"""

import ezdxf


def create_block_attributes_test() -> None:
    """Create a test DXF file with block attributes."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create layer for testing
    doc.layers.add("TEST_LAYER")

    # Block 1: PRODUCT_BLOCK with multiple attributes
    block1 = doc.blocks.new(name="PRODUCT_BLOCK")
    block1.add_line((0, 0), (100, 0))
    block1.add_line((100, 0), (100, 50))
    block1.add_line((100, 50), (0, 50))
    block1.add_line((0, 50), (0, 0))
    # Add attribute definitions
    block1.add_attdef("PROD1", (10, 10), dxfattribs={"prompt": "Product 1"})
    block1.add_attdef("PROD2", (10, 20), dxfattribs={"prompt": "Product 2"})
    block1.add_attdef("DEPT", (10, 30), dxfattribs={"prompt": "Department"})
    block1.add_attdef("BAY#", (10, 40), dxfattribs={"prompt": "Bay Number"})

    # Block 2: SIMPLE_BLOCK with single attribute
    block2 = doc.blocks.new(name="SIMPLE_BLOCK")
    block2.add_circle((25, 25), 20)
    block2.add_attdef("ID", (25, 25), dxfattribs={"prompt": "Identifier"})

    # Block 3: NO_ATTRIB_BLOCK without attributes
    block3 = doc.blocks.new(name="NO_ATTRIB_BLOCK")
    block3.add_line((0, 0), (50, 50))

    # Block 4: EMPTY_VALUE_BLOCK with attribute that will have empty value
    block4 = doc.blocks.new(name="EMPTY_VALUE_BLOCK")
    block4.add_line((0, 0), (30, 30))
    block4.add_attdef("EMPTY_ATTR", (15, 15), dxfattribs={"prompt": "Empty Attribute"})

    # Insert PRODUCT_BLOCK with filled attributes (first instance)
    insert1 = msp.add_blockref(
        "PRODUCT_BLOCK", (0, 0), dxfattribs={"layer": "TEST_LAYER"}
    )
    insert1.add_auto_attribs(
        {
            "PROD1": "Garage",
            "PROD2": "Door Openers",
            "DEPT": "30",
            "BAY#": "27-004",
        }
    )

    # Insert PRODUCT_BLOCK with different values (second instance)
    insert2 = msp.add_blockref(
        "PRODUCT_BLOCK", (200, 0), dxfattribs={"layer": "TEST_LAYER"}
    )
    insert2.add_auto_attribs(
        {
            "PROD1": "Kitchen",
            "PROD2": "Appliances",
            "DEPT": "45",
            "BAY#": "12-001",
        }
    )

    # Insert PRODUCT_BLOCK with some empty values (third instance)
    insert3 = msp.add_blockref(
        "PRODUCT_BLOCK", (400, 0), dxfattribs={"layer": "TEST_LAYER"}
    )
    insert3.add_auto_attribs(
        {
            "PROD1": "Garage",  # Same as first to test deduplication
            "PROD2": "",  # Empty value - should be skipped
            "DEPT": "30",  # Same as first to test deduplication
            "BAY#": "27-005",  # Different bay
        }
    )

    # Insert SIMPLE_BLOCK with single attribute
    insert4 = msp.add_blockref(
        "SIMPLE_BLOCK", (0, 100), dxfattribs={"layer": "TEST_LAYER"}
    )
    insert4.add_auto_attribs({"ID": "ITEM-001"})

    # Insert SIMPLE_BLOCK with different ID
    insert5 = msp.add_blockref(
        "SIMPLE_BLOCK", (100, 100), dxfattribs={"layer": "TEST_LAYER"}
    )
    insert5.add_auto_attribs({"ID": "ITEM-002"})

    # Insert NO_ATTRIB_BLOCK (no attributes)
    msp.add_blockref("NO_ATTRIB_BLOCK", (0, 200), dxfattribs={"layer": "TEST_LAYER"})
    msp.add_blockref("NO_ATTRIB_BLOCK", (100, 200), dxfattribs={"layer": "TEST_LAYER"})

    # Insert EMPTY_VALUE_BLOCK with empty attribute value
    insert6 = msp.add_blockref(
        "EMPTY_VALUE_BLOCK", (0, 300), dxfattribs={"layer": "TEST_LAYER"}
    )
    insert6.add_auto_attribs({"EMPTY_ATTR": ""})  # Empty value - should be skipped

    # Save the file
    doc.saveas("app/tests/assets/block_attributes_test.dxf")
    print("Created: app/tests/assets/block_attributes_test.dxf")


if __name__ == "__main__":
    create_block_attributes_test()
