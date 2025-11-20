"""
Generate test DXF file with negative scale scenarios for testing three-tier highlighting.

This script creates a DXF file with four distinct blocks demonstrating all highlighting scenarios:
1. VARY_POSITIVE: Variance with all positive scales → Yellow highlight, "VARIES" text
2. MIRROR_CONSISTENT: Consistent negative scale → Orange highlight, -1.0 numeric
3. VARY_NEGATIVE: Variance with mixed positive/negative → Red highlight, "VARIES (-)" text
4. NORMAL: Consistent positive scale → No highlight, 1.0 numeric

Run this script to regenerate the test asset:
    python app/tests/assets/create_negative_scale_test.py
"""

from pathlib import Path

import ezdxf


def create_negative_scale_test_dxf() -> None:
    """Create test DXF with blocks demonstrating all three highlighting scenarios."""
    # Create new DXF document
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create block definitions (simple rectangles)
    # Block 1: VARY_POSITIVE - will be inserted with varying positive scales
    block_vary_positive = doc.blocks.new(name="VARY_POSITIVE")
    block_vary_positive.add_lwpolyline(
        [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    )

    # Block 2: MIRROR_CONSISTENT - will be inserted with consistent negative scale
    block_mirror = doc.blocks.new(name="MIRROR_CONSISTENT")
    block_mirror.add_lwpolyline(
        [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    )

    # Block 3: VARY_NEGATIVE - will be inserted with mixed positive/negative scales
    block_vary_negative = doc.blocks.new(name="VARY_NEGATIVE")
    block_vary_negative.add_lwpolyline(
        [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    )

    # Block 4: NORMAL - will be inserted with consistent positive scale
    block_normal = doc.blocks.new(name="NORMAL")
    block_normal.add_lwpolyline(
        [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    )

    # Insert blocks with different scale scenarios
    # Scenario 1: VARY_POSITIVE - Yellow highlighting, "VARIES" text
    # Insert at (1.0, 1.0) and (2.0, 1.0) to create X-scale variance
    msp.add_blockref("VARY_POSITIVE", (0, 0), dxfattribs={"xscale": 1.0, "yscale": 1.0})
    msp.add_blockref("VARY_POSITIVE", (20, 0), dxfattribs={"xscale": 2.0, "yscale": 1.0})

    # Scenario 2: MIRROR_CONSISTENT - Orange highlighting, -1.0 numeric
    # Insert at (-1.0, 1.0) three times consistently
    msp.add_blockref("MIRROR_CONSISTENT", (0, 20), dxfattribs={"xscale": -1.0, "yscale": 1.0})
    msp.add_blockref("MIRROR_CONSISTENT", (20, 20), dxfattribs={"xscale": -1.0, "yscale": 1.0})
    msp.add_blockref("MIRROR_CONSISTENT", (40, 20), dxfattribs={"xscale": -1.0, "yscale": 1.0})

    # Scenario 3: VARY_NEGATIVE - Red highlighting, "VARIES (-)" text
    # Insert at (1.0, 1.0) and (-1.0, 1.0) to create variance with negatives
    msp.add_blockref("VARY_NEGATIVE", (0, 40), dxfattribs={"xscale": 1.0, "yscale": 1.0})
    msp.add_blockref("VARY_NEGATIVE", (20, 40), dxfattribs={"xscale": -1.0, "yscale": 1.0})

    # Scenario 4: NORMAL - No highlighting, 1.0 numeric
    # Insert at (1.0, 1.0) three times consistently
    msp.add_blockref("NORMAL", (0, 60), dxfattribs={"xscale": 1.0, "yscale": 1.0})
    msp.add_blockref("NORMAL", (20, 60), dxfattribs={"xscale": 1.0, "yscale": 1.0})
    msp.add_blockref("NORMAL", (40, 60), dxfattribs={"xscale": 1.0, "yscale": 1.0})

    # Save to test assets directory
    output_path = Path(__file__).parent / "negative_scale_test.dxf"
    doc.saveas(output_path)
    print(f"Created test DXF file: {output_path}")
    print("\nExpected results:")
    print("1. VARY_POSITIVE: X scale = 'VARIES' (yellow highlight)")
    print("2. MIRROR_CONSISTENT: X scale = -1.0 (orange highlight)")
    print("3. VARY_NEGATIVE: X scale = 'VARIES (-)' (red highlight)")
    print("4. NORMAL: X scale = 1.0 (no highlight)")


if __name__ == "__main__":
    create_negative_scale_test_dxf()
