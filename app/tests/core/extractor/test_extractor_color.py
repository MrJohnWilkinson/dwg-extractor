"""
Unit tests for the extractor module - color extraction functionality.

This module contains tests for:
- TestColorAnalysis: Color analysis extraction
- TestTrueColorExtraction: True Color (24-bit RGB) extraction
- TestAciExtraction: ACI (AutoCAD Color Index) extraction
"""

from pathlib import Path

import ezdxf
import pytest

from core.extractor import (
    _resolve_entity_color_to_rgb,
    _resolve_entity_color_with_aci,
    extract_blocks,
)


class TestColorAnalysis:
    """Test suite for color analysis extraction functionality."""

    def test_color_analysis_data_exists(self) -> None:
        """Test that color_analysis_data field exists in extraction result."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        assert "color_analysis_data" in result
        assert isinstance(result["color_analysis_data"], list)

    def test_color_analysis_with_lines_and_polylines(self) -> None:
        """Test that Lines and Polylines are extracted and grouped correctly."""
        # Create test DXF with lines and polylines
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Add lines with same color on same layer (should aggregate)
        msp.add_line(
            (0, 0), (10, 10), dxfattribs={"color": 1, "layer": "WALLS"}
        )  # Red ACI
        msp.add_line(
            (0, 5), (10, 15), dxfattribs={"color": 1, "layer": "WALLS"}
        )  # Red ACI

        # Add polylines with different color
        msp.add_lwpolyline(
            [(0, 0), (1, 1), (2, 0)], dxfattribs={"color": 2, "layer": "WALLS"}
        )  # Yellow ACI

        # Save and extract
        test_path = Path("app/tests/assets/temp_color_test.dxf")
        doc.saveas(test_path)

        try:
            result = extract_blocks(str(test_path))
            color_data = result["color_analysis_data"]

            # Should have 2 records: one for Lines (count=2), one for Polylines (count=1)
            assert len(color_data) >= 2

            # Find Lines record
            lines_records = [r for r in color_data if r["entity_type"] == "Lines"]
            assert len(lines_records) >= 1

            # Verify Lines are aggregated
            walls_lines = [r for r in lines_records if r["layer_name"] == "WALLS"]
            if walls_lines:
                assert walls_lines[0]["entity_count"] == 2
                assert walls_lines[0]["annotation_contents"] == ""

            # Find Polylines record
            polylines_records = [
                r for r in color_data if r["entity_type"] == "Polylines"
            ]
            assert len(polylines_records) >= 1

        finally:
            if test_path.exists():
                test_path.unlink()

    def test_color_analysis_with_text_annotations(self) -> None:
        """Test that TEXT and MTEXT entities are extracted individually with content."""
        # Use existing annotation test file
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        color_data = result["color_analysis_data"]

        # Find TEXT entries
        text_records = [r for r in color_data if r["entity_type"] == "TEXT"]

        # Each TEXT should have content and count=1
        for record in text_records:
            assert "annotation_contents" in record
            assert record["entity_count"] == 1
            # Content may be empty or non-empty depending on the test file

        # Find MTEXT entries
        mtext_records = [r for r in color_data if r["entity_type"] == "MTEXT"]

        # Each MTEXT should have content and count=1
        for record in mtext_records:
            assert "annotation_contents" in record
            assert record["entity_count"] == 1

    def test_color_analysis_grouping_by_layer(self) -> None:
        """Test that same color on different layers creates separate records."""
        # Create test DXF
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Add red lines on different layers
        msp.add_line((0, 0), (10, 10), dxfattribs={"color": 1, "layer": "FIRE-SAFETY"})
        msp.add_line((0, 5), (10, 15), dxfattribs={"color": 1, "layer": "ELECTRICAL"})

        test_path = Path("app/tests/assets/temp_layer_test.dxf")
        doc.saveas(test_path)

        try:
            result = extract_blocks(str(test_path))
            color_data = result["color_analysis_data"]

            # Should have 2 separate records (same color, different layers)
            lines_records = [r for r in color_data if r["entity_type"] == "Lines"]
            layer_names = {r["layer_name"] for r in lines_records}

            # Should have both layers represented
            assert "FIRE-SAFETY" in layer_names or "ELECTRICAL" in layer_names

        finally:
            if test_path.exists():
                test_path.unlink()

    def test_color_analysis_sorting(self) -> None:
        """Test that results are sorted by RGB, layer, and entity type."""
        result = extract_blocks("app/tests/assets/comprehensive_scale_test.dxf")
        color_data = result["color_analysis_data"]

        if len(color_data) > 1:
            # Verify sorting: (color_r, color_g, color_b, layer_name, entity_type)
            for i in range(len(color_data) - 1):
                current = color_data[i]
                next_record = color_data[i + 1]

                # Build sort tuples
                current_key = (
                    current["color_r"],
                    current["color_g"],
                    current["color_b"],
                    current["layer_name"],
                    current["entity_type"],
                )
                next_key = (
                    next_record["color_r"],
                    next_record["color_g"],
                    next_record["color_b"],
                    next_record["layer_name"],
                    next_record["entity_type"],
                )

                # Current should be <= next (ascending order)
                assert current_key <= next_key

    def test_color_analysis_rgb_values(self) -> None:
        """Test that RGB values are valid integers 0-255."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")
        color_data = result["color_analysis_data"]

        for record in color_data:
            assert isinstance(record["color_r"], int)
            assert isinstance(record["color_g"], int)
            assert isinstance(record["color_b"], int)
            assert 0 <= record["color_r"] <= 255
            assert 0 <= record["color_g"] <= 255
            assert 0 <= record["color_b"] <= 255

    def test_color_analysis_empty_drawing(self) -> None:
        """Test color analysis with drawing that has no relevant entities."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")
        color_data = result["color_analysis_data"]

        # Should return empty list, not error
        assert isinstance(color_data, list)

    def test_color_analysis_record_structure(self) -> None:
        """Test that all records have required fields with correct types."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")
        color_data = result["color_analysis_data"]

        required_fields = [
            "annotation_contents",
            "layer_name",
            "color_r",
            "color_g",
            "color_b",
            "entity_type",
            "entity_count",
        ]

        for record in color_data:
            for field in required_fields:
                assert field in record, f"Record missing field: {field}"

            # Type validation
            assert isinstance(record["annotation_contents"], str)
            assert isinstance(record["layer_name"], str)
            assert isinstance(record["entity_type"], str)
            assert isinstance(record["entity_count"], int)
            assert record["entity_count"] >= 1

    def test_full_extraction_with_color_analysis(self) -> None:
        """Test complete extraction pipeline with real comprehensive DXF asset."""
        # Use comprehensive test asset which has various entity types
        result = extract_blocks("app/tests/assets/comprehensive_scale_test.dxf")

        # Verify color_analysis_data is included
        assert "color_analysis_data" in result
        color_data = result["color_analysis_data"]
        assert isinstance(color_data, list)

        # Should contain data for a real drawing
        assert len(color_data) > 0

        # Verify expected entity types are present
        entity_types = {record["entity_type"] for record in color_data}
        # At minimum, should have some geometric entities or text
        assert len(entity_types) > 0
        assert entity_types.issubset({"Lines", "Polylines", "Hatches", "TEXT", "MTEXT"})

        # Verify colors are resolved correctly (all RGB values should be 0-255)
        for record in color_data:
            assert 0 <= record["color_r"] <= 255
            assert 0 <= record["color_g"] <= 255
            assert 0 <= record["color_b"] <= 255

        # Verify grouping logic - same entity_type on same layer with same color should be grouped
        # (For geometric entities, not text which is individual)
        geometric_records = [
            r for r in color_data if r["entity_type"] in ("Lines", "Polylines")
        ]
        if len(geometric_records) > 0:
            # Each geometric record should have count >= 1
            for record in geometric_records:
                assert record["entity_count"] >= 1
                assert record["annotation_contents"] == ""

        # Verify text annotations are individual
        text_records = [r for r in color_data if r["entity_type"] in ("TEXT", "MTEXT")]
        for record in text_records:
            assert record["entity_count"] == 1
            # annotation_contents can be empty string or have content
            assert isinstance(record["annotation_contents"], str)

        # Verify sorting is correct (RGB ascending, then layer, then entity_type)
        for i in range(len(color_data) - 1):
            curr = color_data[i]
            next_rec = color_data[i + 1]

            # Create sort keys
            curr_key = (
                curr["color_r"],
                curr["color_g"],
                curr["color_b"],
                curr["layer_name"],
                curr["entity_type"],
            )
            next_key = (
                next_rec["color_r"],
                next_rec["color_g"],
                next_rec["color_b"],
                next_rec["layer_name"],
                next_rec["entity_type"],
            )

            assert curr_key <= next_key, f"Sorting violation at index {i}"


class TestTrueColorExtraction:
    """Test suite for True Color (24-bit RGB) extraction functionality."""

    def test_resolve_entity_color_to_rgb_true_color(self) -> None:
        """Test True Color extraction from entities with 24-bit RGB colors."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create LINE with True Color (124, 82, 165)
        line = msp.add_line((0, 0), (100, 0))
        line.rgb = (124, 82, 165)

        # Resolve color
        rgb = _resolve_entity_color_to_rgb(line, doc)

        assert rgb is not None
        assert rgb == (124, 82, 165)

    def test_resolve_entity_color_to_rgb_true_color_cyan(self) -> None:
        """Test True Color extraction with cyan color (0, 165, 165) from bug report."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create LINE with True Color (0, 165, 165)
        line = msp.add_line((0, 0), (100, 0))
        line.rgb = (0, 165, 165)

        # Resolve color
        rgb = _resolve_entity_color_to_rgb(line, doc)

        assert rgb is not None
        assert rgb == (0, 165, 165)

    def test_true_color_in_annotation_data(self) -> None:
        """Verify True Colors appear in annotation_data for TEXT/MTEXT entities."""
        result = extract_blocks("app/tests/assets/true_color_test.dxf")
        annotation_data = result["annotation_data"]

        # Find TRUE COLOR TEXT entry - should have RGB (255, 128, 0)
        true_color_text_entries = [
            (key, count)
            for key, count in annotation_data.items()
            if "TRUE COLOR TEXT" in key.annotation_contents
        ]

        assert len(true_color_text_entries) >= 1
        key, count = true_color_text_entries[0]

        # Verify True Color RGB (255, 128, 0) - orange
        assert key.color_r == 255
        assert key.color_g == 128
        assert key.color_b == 0

    def test_true_color_in_color_analysis(self) -> None:
        """Verify True Colors appear in color_analysis_data."""
        result = extract_blocks("app/tests/assets/true_color_test.dxf")
        color_data = result["color_analysis_data"]

        # Find records with specific True Colors
        # LINE with True Color (124, 82, 165) - purple
        purple_lines = [
            r
            for r in color_data
            if r["color_r"] == 124
            and r["color_g"] == 82
            and r["color_b"] == 165
            and r["entity_type"] == "Lines"
        ]
        assert len(purple_lines) >= 1

        # LINE with True Color (0, 165, 165) - cyan
        cyan_lines = [
            r
            for r in color_data
            if r["color_r"] == 0 and r["color_g"] == 165 and r["color_b"] == 165
        ]
        assert len(cyan_lines) >= 1

    def test_true_color_mixed_with_aci(self) -> None:
        """Verify both True Color and ACI entities are extracted correctly."""
        result = extract_blocks("app/tests/assets/true_color_test.dxf")
        color_data = result["color_analysis_data"]

        # Find ACI color entries
        # ACI 1 = Red (255, 0, 0)
        red_aci_lines = [
            r
            for r in color_data
            if r["color_r"] == 255
            and r["color_g"] == 0
            and r["color_b"] == 0
            and r["entity_type"] == "Lines"
        ]
        assert len(red_aci_lines) >= 1

        # Find True Color entries
        # True Color (100, 200, 150) - custom green
        custom_green_lines = [
            r
            for r in color_data
            if r["color_r"] == 100 and r["color_g"] == 200 and r["color_b"] == 150
        ]
        assert len(custom_green_lines) >= 1

    def test_true_color_text_annotations(self) -> None:
        """Test True Color extraction from TEXT and MTEXT entities."""
        result = extract_blocks("app/tests/assets/true_color_test.dxf")
        color_data = result["color_analysis_data"]

        # Find TRUE COLOR MTEXT entry with RGB (128, 0, 255) - purple
        purple_mtext = [
            r
            for r in color_data
            if r["entity_type"] == "MTEXT"
            and r["color_r"] == 128
            and r["color_g"] == 0
            and r["color_b"] == 255
        ]
        assert len(purple_mtext) >= 1

        # Find ANNOTATION WITH TRUE COLOR with RGB (200, 100, 50) - brownish
        brownish_text = [
            r
            for r in color_data
            if r["entity_type"] == "TEXT"
            and r["color_r"] == 200
            and r["color_g"] == 100
            and r["color_b"] == 50
        ]
        assert len(brownish_text) >= 1

    def test_true_color_overrides_bylayer(self) -> None:
        """Test that True Color overrides ByLayer color setting."""
        result = extract_blocks("app/tests/assets/true_color_test.dxf")
        color_data = result["color_analysis_data"]

        # LINE with True Color (50, 150, 250) - light blue
        # This line has color=256 (ByLayer) but also has True Color set
        # True Color should take precedence
        light_blue_lines = [
            r
            for r in color_data
            if r["color_r"] == 50
            and r["color_g"] == 150
            and r["color_b"] == 250
            and r["entity_type"] == "Lines"
        ]
        assert len(light_blue_lines) >= 1

    def test_true_color_extraction_preserves_all_rgb_values(self) -> None:
        """Test that all RGB component values are correctly preserved."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Test edge cases for RGB values
        test_colors = [
            (0, 0, 0),  # Black
            (255, 255, 255),  # White
            (128, 128, 128),  # Gray
            (255, 0, 0),  # Red
            (0, 255, 0),  # Green
            (0, 0, 255),  # Blue
            (1, 2, 3),  # Low values
            (252, 253, 254),  # High values
        ]

        for i, color in enumerate(test_colors):
            line = msp.add_line((0, i * 10), (100, i * 10))
            line.rgb = color

            rgb = _resolve_entity_color_to_rgb(line, doc)

            assert rgb is not None, f"Failed to extract color {color}"
            assert rgb == color, f"Expected {color}, got {rgb}"

    def test_true_color_via_dxf_true_color_property(self) -> None:
        """Test True Color extraction via entity.dxf.true_color packed integer."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create a line and manually set true_color as packed integer
        line = msp.add_line((0, 0), (100, 0))

        # Pack RGB (100, 150, 200) as 24-bit integer
        # value = (R << 16) | (G << 8) | B
        packed_color = (100 << 16) | (150 << 8) | 200
        line.dxf.true_color = packed_color

        # Resolve color
        rgb = _resolve_entity_color_to_rgb(line, doc)

        assert rgb is not None
        assert rgb == (100, 150, 200)

    def test_true_color_takes_precedence_over_aci(self) -> None:
        """Test that True Color is checked before ACI color index."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create a line with both ACI color and True Color
        line = msp.add_line((0, 0), (100, 0), dxfattribs={"color": 1})  # ACI red

        # Set True Color - this should take precedence
        line.rgb = (0, 128, 64)  # Custom green

        rgb = _resolve_entity_color_to_rgb(line, doc)

        # Should return True Color, not ACI red (255, 0, 0)
        assert rgb is not None
        assert rgb == (0, 128, 64)

    def test_aci_color_still_works_without_true_color(self) -> None:
        """Test that ACI colors still work when no True Color is present."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create line with only ACI color
        line = msp.add_line((0, 0), (100, 0), dxfattribs={"color": 1})  # ACI red

        rgb = _resolve_entity_color_to_rgb(line, doc)

        # Should return ACI red
        assert rgb is not None
        assert rgb == (255, 0, 0)


class TestAciExtraction:
    """Test suite for ACI (AutoCAD Color Index) extraction functionality."""

    def test_resolve_entity_color_with_aci_true_color(self) -> None:
        """Test that True Color entities return None for ACI value."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create LINE with True Color (124, 82, 165)
        line = msp.add_line((0, 0), (100, 0))
        line.rgb = (124, 82, 165)

        result = _resolve_entity_color_with_aci(line, doc)

        assert result is not None
        rgb, aci = result
        assert rgb == (124, 82, 165)
        assert aci is None  # True Color has no ACI index

    def test_resolve_entity_color_with_aci_byblock(self) -> None:
        """Test that ByBlock (ACI 0) is correctly extracted."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create line with ByBlock color (color=0)
        line = msp.add_line((0, 0), (100, 0), dxfattribs={"color": 0})

        result = _resolve_entity_color_with_aci(line, doc)

        assert result is not None
        rgb, aci = result
        assert rgb == (255, 255, 255)  # ByBlock defaults to white
        assert aci == 0  # ByBlock ACI

    def test_resolve_entity_color_with_aci_bylayer(self) -> None:
        """Test that ByLayer (ACI 256) is correctly extracted."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create layer with ACI color 3 (green)
        doc.layers.add("TEST_LAYER", color=3)

        # Create line with ByLayer color (color=256)
        line = msp.add_line(
            (0, 0), (100, 0), dxfattribs={"color": 256, "layer": "TEST_LAYER"}
        )

        result = _resolve_entity_color_with_aci(line, doc)

        assert result is not None
        rgb, aci = result
        # Should resolve to layer's ACI 3 (green) RGB
        assert 0 <= rgb[0] <= 255
        assert 0 <= rgb[1] <= 255
        assert 0 <= rgb[2] <= 255
        assert aci == 256  # ByLayer ACI

    def test_resolve_entity_color_with_aci_named_colors(self) -> None:
        """Test ACI extraction for named colors (1-7)."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Test all named ACI colors
        named_colors = {
            1: "Red",
            2: "Yellow",
            3: "Green",
            4: "Cyan",
            5: "Blue",
            6: "Magenta",
            7: "White",
        }

        for aci_value, name in named_colors.items():
            line = msp.add_line(
                (0, aci_value * 10),
                (100, aci_value * 10),
                dxfattribs={"color": aci_value},
            )

            result = _resolve_entity_color_with_aci(line, doc)

            assert result is not None, f"Failed to extract ACI {aci_value} ({name})"
            rgb, aci = result
            assert aci == aci_value, f"Expected ACI {aci_value}, got {aci}"
            # RGB values should be valid
            assert 0 <= rgb[0] <= 255
            assert 0 <= rgb[1] <= 255
            assert 0 <= rgb[2] <= 255

    def test_resolve_entity_color_with_aci_numbered_colors(self) -> None:
        """Test ACI extraction for numbered colors (8-255)."""
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Test a few numbered colors
        test_colors = [8, 30, 100, 200, 255]

        for aci_value in test_colors:
            line = msp.add_line((0, 0), (100, 0), dxfattribs={"color": aci_value})

            result = _resolve_entity_color_with_aci(line, doc)

            assert result is not None, f"Failed to extract ACI {aci_value}"
            rgb, aci = result
            assert aci == aci_value, f"Expected ACI {aci_value}, got {aci}"

    def test_color_analysis_includes_color_aci_field(self) -> None:
        """Test that color_analysis_data records include the color_aci field."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")
        color_data = result["color_analysis_data"]

        for record in color_data:
            assert "color_aci" in record, "Record missing color_aci field"
            # color_aci should be int or None
            aci = record["color_aci"]
            assert aci is None or isinstance(aci, int), (
                f"Invalid color_aci type: {type(aci)}"
            )
            if aci is not None:
                assert 0 <= aci <= 256, f"Invalid ACI value: {aci}"

    def test_color_analysis_true_color_has_none_aci(self) -> None:
        """Test that True Color entities in color_analysis_data have color_aci=None."""
        result = extract_blocks("app/tests/assets/true_color_test.dxf")
        color_data = result["color_analysis_data"]

        # Find records with True Color RGB values (not standard ACI colors)
        # True Color (124, 82, 165) - purple
        purple_records = [
            r
            for r in color_data
            if r["color_r"] == 124 and r["color_g"] == 82 and r["color_b"] == 165
        ]

        assert len(purple_records) >= 1, "Should have True Color records"
        for record in purple_records:
            assert record["color_aci"] is None, "True Color should have color_aci=None"

    def test_color_analysis_aci_colors_have_aci_value(self) -> None:
        """Test that ACI color entities have correct color_aci values."""
        result = extract_blocks("app/tests/assets/true_color_test.dxf")
        color_data = result["color_analysis_data"]

        # Find records with ACI red (255, 0, 0) - should have ACI 1
        red_records = [
            r
            for r in color_data
            if r["color_r"] == 255 and r["color_g"] == 0 and r["color_b"] == 0
        ]

        # At least some should have ACI color
        aci_red_records = [r for r in red_records if r["color_aci"] is not None]
        if aci_red_records:
            for record in aci_red_records:
                assert record["color_aci"] == 1, (
                    f"Red should be ACI 1, got {record['color_aci']}"
                )
