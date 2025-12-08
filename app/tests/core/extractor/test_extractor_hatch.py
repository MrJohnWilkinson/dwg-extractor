"""
Unit tests for the extractor module - HATCH entity extraction functionality.

This module contains tests for HATCH entity extraction in color analysis.
"""


from core.extractor import extract_blocks


class TestHatchExtraction:
    """Test suite for HATCH entity extraction in color analysis."""

    def test_color_analysis_extracts_hatch_entities(self) -> None:
        """Verify that HATCH entities are extracted by extract_color_analysis()."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find Hatches records
        hatch_records = [r for r in color_data if r["entity_type"] == "Hatches"]

        # Should have at least one hatch record
        assert len(hatch_records) >= 1, "HATCH entities should be extracted"

    def test_color_analysis_hatch_aggregation(self) -> None:
        """Verify that same color/layer hatches are grouped correctly."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find Hatches on HATCH_LAYER_A with ACI red (255, 0, 0)
        red_hatches = [
            r
            for r in color_data
            if r["entity_type"] == "Hatches"
            and r["layer_name"] == "HATCH_LAYER_A"
            and r["color_r"] == 255
            and r["color_g"] == 0
            and r["color_b"] == 0
        ]

        # Should have exactly one aggregated record with count=3
        assert len(red_hatches) == 1, "Same color/layer hatches should be aggregated"
        assert red_hatches[0]["entity_count"] == 3, (
            "Three red hatches should be counted"
        )

    def test_color_analysis_hatch_entity_type_name(self) -> None:
        """Verify that entity_type is 'Hatches' (plural)."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find any hatch record
        hatch_records = [r for r in color_data if r["entity_type"] == "Hatches"]

        assert len(hatch_records) >= 1, "Should have Hatches records"
        for record in hatch_records:
            assert record["entity_type"] == "Hatches", (
                "Entity type should be 'Hatches' (plural)"
            )

    def test_color_analysis_hatch_with_true_color(self) -> None:
        """Verify True Color hatches work correctly and have color_aci=None."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find Hatches with True Color (124, 82, 165)
        purple_hatches = [
            r
            for r in color_data
            if r["entity_type"] == "Hatches"
            and r["color_r"] == 124
            and r["color_g"] == 82
            and r["color_b"] == 165
        ]

        assert len(purple_hatches) >= 1, "True Color hatches should be extracted"
        for record in purple_hatches:
            assert record["color_aci"] is None, (
                "True Color hatches should have color_aci=None"
            )
            assert record["entity_count"] == 2, (
                "Two purple hatches should be aggregated"
            )

    def test_color_analysis_hatch_mixed_entities(self) -> None:
        """Verify HATCHes work alongside Lines/Polylines/Text."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Gather all entity types present
        entity_types = {r["entity_type"] for r in color_data}

        # Should have multiple entity types
        assert "Hatches" in entity_types, "Should have Hatches"
        assert "Lines" in entity_types, "Should have Lines"
        assert "Polylines" in entity_types, "Should have Polylines"
        assert "TEXT" in entity_types, "Should have TEXT"

    def test_color_analysis_hatch_annotation_contents_empty(self) -> None:
        """Verify annotation_contents is empty string for HATCH entities."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find Hatches records
        hatch_records = [r for r in color_data if r["entity_type"] == "Hatches"]

        for record in hatch_records:
            assert record["annotation_contents"] == "", (
                "HATCH annotation_contents should be empty"
            )

    def test_color_analysis_hatch_aci_colors(self) -> None:
        """Verify ACI color HATCH entities have correct color_aci value."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find Hatches on HATCH_LAYER_A with ACI red
        red_hatches = [
            r
            for r in color_data
            if r["entity_type"] == "Hatches"
            and r["layer_name"] == "HATCH_LAYER_A"
            and r["color_r"] == 255
        ]

        assert len(red_hatches) >= 1, "Should have red ACI hatches"
        for record in red_hatches:
            assert record["color_aci"] == 1, "Red hatches should have color_aci=1"

    def test_color_analysis_hatch_byblock_color(self) -> None:
        """Verify ByBlock hatches default to white as per existing behavior."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find Hatches with ByBlock color (white fallback)
        byblock_hatches = [
            r
            for r in color_data
            if r["entity_type"] == "Hatches" and r["color_aci"] == 0
        ]

        # Should have at least one ByBlock hatch
        assert len(byblock_hatches) >= 1, "Should have ByBlock hatches"
        for record in byblock_hatches:
            assert record["color_r"] == 255, "ByBlock should default to white (R=255)"
            assert record["color_g"] == 255, "ByBlock should default to white (G=255)"
            assert record["color_b"] == 255, "ByBlock should default to white (B=255)"

    def test_color_analysis_hatch_bylayer_color(self) -> None:
        """Verify ByLayer hatches resolve to layer color correctly."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find Hatches on HATCH_LAYER_B with ByLayer (should resolve to layer's ACI 3)
        bylayer_hatches = [
            r
            for r in color_data
            if r["entity_type"] == "Hatches"
            and r["layer_name"] == "HATCH_LAYER_B"
            and r["color_aci"] == 256
        ]

        # Should have at least one ByLayer hatch
        assert len(bylayer_hatches) >= 1, "Should have ByLayer hatches on HATCH_LAYER_B"
        for record in bylayer_hatches:
            # ByLayer should resolve to layer's ACI 3 (green)
            assert record["color_aci"] == 256, "ByLayer should have color_aci=256"
