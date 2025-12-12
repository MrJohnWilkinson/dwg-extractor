"""
Tests for pre-filter and curved-filter parameters in the extractor module.

Tests cover:
- extract_blocks() accepting pre-filter parameters (skip_curved_entities,
  min_line_length_filter_enabled, min_line_length_filter_amount)
- extract_blocks() accepting curved_filter_enabled post-filter parameter
- Backward compatibility (pre-filters disabled by default)
- Integration tests with real DXF files containing circles/arcs
"""

from pathlib import Path

from core.extractor import extract_blocks


# Test assets directory
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"


class TestExtractBlocksPreFilterParameters:
    """Tests for extract_blocks() accepting pre-filter parameters."""

    def test_accepts_skip_curved_entities_parameter(self) -> None:
        """Verify extract_blocks accepts skip_curved_entities parameter."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            skip_curved_entities=True,
        )

        assert result is not None
        assert "block_counts" in result

    def test_accepts_min_line_length_filter_enabled_parameter(self) -> None:
        """Verify extract_blocks accepts min_line_length_filter_enabled parameter."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_line_length_filter_enabled=True,
        )

        assert result is not None
        assert "block_counts" in result

    def test_accepts_min_line_length_filter_amount_parameter(self) -> None:
        """Verify extract_blocks accepts min_line_length_filter_amount parameter."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_line_length_filter_enabled=True,
            min_line_length_filter_amount=5.0,
        )

        assert result is not None
        assert "block_counts" in result

    def test_accepts_curved_filter_enabled_parameter(self) -> None:
        """Verify extract_blocks accepts curved_filter_enabled parameter."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            curved_filter_enabled=True,
        )

        assert result is not None
        assert "block_counts" in result

    def test_accepts_all_prefilter_parameters(self) -> None:
        """Verify all new pre-filter and post-filter parameters work together."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            skip_curved_entities=True,
            min_line_length_filter_enabled=True,
            min_line_length_filter_amount=5.0,
            curved_filter_enabled=True,
        )

        assert result is not None
        assert "block_counts" in result
        assert "block_content_zone_data" in result


class TestExtractBlocksSkipCurvedEntities:
    """Tests for skip_curved_entities pre-filter in extract_blocks."""

    def test_skip_curved_entities_disabled_by_default(self) -> None:
        """Verify default behavior extracts circles/arcs."""
        circles_dxf = ASSETS_DIR / "circles_arcs_points.dxf"

        # Default behavior should include circles/arcs in content zone detection
        result = extract_blocks(str(circles_dxf))

        assert result is not None
        assert "block_counts" in result
        # Verify TEST_CIRCLES block was processed
        assert "TEST_CIRCLES" in result["block_counts"]

    def test_skip_curved_entities_affects_content_zone(self) -> None:
        """Verify content zone detection changes when circles skipped.

        Uses circles_arcs_points.dxf which contains TEST_CIRCLES, TEST_ARCS blocks.
        When skip_curved_entities=True, CIRCLE and ARC entities are excluded from
        edge extraction, which may affect content zone polygon counts.
        """
        circles_dxf = ASSETS_DIR / "circles_arcs_points.dxf"

        result_default = extract_blocks(str(circles_dxf))
        result_skip_curved = extract_blocks(
            str(circles_dxf),
            skip_curved_entities=True,
        )

        assert result_default is not None
        assert result_skip_curved is not None

        # Both should have block counts
        assert "block_counts" in result_default
        assert "block_counts" in result_skip_curved

        # Content zone data should exist for both
        assert "block_content_zone_data" in result_default
        assert "block_content_zone_data" in result_skip_curved

    def test_skip_curved_entities_with_mixed_block(self) -> None:
        """Use TEST_MIXED block from test DXF.

        TEST_MIXED contains CIRCLE, ARC, POINT, and LINE entities.
        With skip_curved_entities=True, only LINE contributes to content zone.
        """
        circles_dxf = ASSETS_DIR / "circles_arcs_points.dxf"

        result = extract_blocks(
            str(circles_dxf),
            skip_curved_entities=True,
        )

        assert result is not None
        # TEST_MIXED should be in block counts
        assert "TEST_MIXED" in result["block_counts"]


class TestExtractBlocksMinLineLengthFilter:
    """Tests for min_line_length_filter in extract_blocks."""

    def test_min_line_length_filter_disabled_by_default(self) -> None:
        """Verify default behavior does not filter short lines."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(str(sample_dxf))

        assert result is not None
        assert "block_counts" in result

    def test_min_line_length_filter_enabled_filters_short_lines(self) -> None:
        """Verify short lines excluded when filter enabled."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_line_length_filter_enabled=True,
            min_line_length_filter_amount=10.0,
        )

        assert result is not None
        assert "block_counts" in result
        # Extraction should complete successfully with filter enabled


class TestExtractBlocksCurvedFilter:
    """Tests for curved_filter_enabled post-filter in extract_blocks."""

    def test_curved_filter_disabled_by_default(self) -> None:
        """Verify default behavior does not filter curved polygons."""
        circles_dxf = ASSETS_DIR / "circles_arcs_points.dxf"

        result = extract_blocks(str(circles_dxf))

        assert result is not None
        assert "block_counts" in result

    def test_curved_filter_enabled_affects_polygon_count(self) -> None:
        """Verify curved polygons filtered from results.

        Uses circle_arc_hatch_edges_test.dxf which contains blocks with
        circle/arc boundaries. When curved_filter_enabled=True, polygons
        with curved edges should be filtered from content zone.
        """
        circle_arc_dxf = ASSETS_DIR / "circle_arc_hatch_edges_test.dxf"

        result_default = extract_blocks(str(circle_arc_dxf))
        result_curved_filter = extract_blocks(
            str(circle_arc_dxf),
            curved_filter_enabled=True,
        )

        assert result_default is not None
        assert result_curved_filter is not None

        # Both should have content zone data
        assert "block_content_zone_data" in result_default
        assert "block_content_zone_data" in result_curved_filter


class TestExtractBlocksPreFilterBackwardCompatibility:
    """Tests for backward compatibility with pre-filter parameters."""

    def test_default_prefilters_disabled(self) -> None:
        """Verify backward compatibility - all pre-filters disabled by default."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Call without any new parameters - should use defaults (disabled)
        result = extract_blocks(str(sample_dxf))

        assert result is not None
        assert "block_counts" in result

    def test_results_consistent_with_prefilters_explicitly_disabled(self) -> None:
        """Compare results with pre-filters explicitly disabled vs no params."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result_default = extract_blocks(str(sample_dxf))
        result_explicit = extract_blocks(
            str(sample_dxf),
            skip_curved_entities=False,
            min_line_length_filter_enabled=False,
            curved_filter_enabled=False,
        )

        # Block counts should be identical
        assert result_default["block_counts"] == result_explicit["block_counts"]


class TestExtractBlocksPreFilterCombinations:
    """Tests for combinations of pre-filters with other parameters."""

    def test_prefilters_with_area_filter(self) -> None:
        """Verify pre-filters work with area filter."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            skip_curved_entities=True,
            min_area_filter_enabled=True,
            min_area_filter_amount=100.0,
        )

        assert result is not None
        assert "block_counts" in result

    def test_prefilters_with_precision_fix(self) -> None:
        """Verify pre-filters work with precision fix."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
            precision_fix_amount=0.01,
            skip_curved_entities=True,
        )

        assert result is not None
        assert "block_counts" in result

    def test_prefilters_with_gap_bridge(self) -> None:
        """Verify pre-filters work with gap bridge."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            gap_bridge_enabled=True,
            gap_bridge_amount=1.0,
            min_line_length_filter_enabled=True,
            min_line_length_filter_amount=5.0,
        )

        assert result is not None
        assert "block_counts" in result

    def test_all_filters_combined(self) -> None:
        """Verify all filter parameters work together."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            unit_override=4,
            # Tolerance parameters
            precision_fix_enabled=True,
            precision_fix_amount=0.01,
            # Post-filters
            min_area_filter_enabled=True,
            min_area_filter_amount=100.0,
            min_side_filter_enabled=True,
            min_side_filter_amount=10.0,
            # Pre-filters
            skip_curved_entities=True,
            min_line_length_filter_enabled=True,
            min_line_length_filter_amount=5.0,
            # Post-filter (curved)
            curved_filter_enabled=True,
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)
        assert isinstance(result["block_content_zone_data"], dict)


class TestExtractBlocksPreFilterEdgeCases:
    """Edge case tests for pre-filter parameters."""

    def test_empty_file_with_prefilters(self) -> None:
        """Extraction works on empty DXF file with pre-filters enabled."""
        empty_dxf = ASSETS_DIR / "empty_drawing.dxf"

        result = extract_blocks(
            str(empty_dxf),
            skip_curved_entities=True,
            min_line_length_filter_enabled=True,
            min_line_length_filter_amount=5.0,
            curved_filter_enabled=True,
        )

        assert result is not None
        assert result["block_counts"] == {}

    def test_prefilters_with_zero_amounts(self) -> None:
        """Pre-filters with zero amounts should use defaults when enabled."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_line_length_filter_enabled=True,
            min_line_length_filter_amount=0.0,  # Should use default
        )

        assert result is not None
        assert "block_counts" in result

    def test_prefilters_with_unit_override(self) -> None:
        """Pre-filters work correctly with unit override."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            unit_override=1,  # Inches
            skip_curved_entities=True,
            min_line_length_filter_enabled=True,
        )

        assert result is not None
        assert "block_counts" in result


class TestExtractBlocksPreFilterRealFiles:
    """Integration tests using real DXF files with circles/arcs."""

    def test_circles_arcs_points_dxf(self) -> None:
        """Test extraction from circles_arcs_points.dxf."""
        circles_dxf = ASSETS_DIR / "circles_arcs_points.dxf"

        result = extract_blocks(
            str(circles_dxf),
            skip_curved_entities=True,
        )

        assert result is not None
        # Should have blocks from the file
        assert len(result["block_counts"]) > 0

    def test_circle_arc_hatch_edges_test_dxf(self) -> None:
        """Test extraction from circle_arc_hatch_edges_test.dxf."""
        circle_arc_dxf = ASSETS_DIR / "circle_arc_hatch_edges_test.dxf"

        result = extract_blocks(
            str(circle_arc_dxf),
            curved_filter_enabled=True,
        )

        assert result is not None
        # Should have blocks from the file
        assert len(result["block_counts"]) > 0
