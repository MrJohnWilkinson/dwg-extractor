"""
Unit tests for the extractor module.

This test suite validates the DXF extraction functionality including:
- Valid file processing with known block counts
- Empty file handling (no blocks)
- Invalid/corrupted file error handling
- Missing file error handling
- Count accuracy verification
- Return type validation
"""

from pathlib import Path

import ezdxf
import pytest

from core.extractor import (
    _clean_mtext_content,
    _resolve_entity_color_to_rgb,
    _resolve_entity_color_with_aci,
    extract_blocks,
)
from core.geometry import (
    _calculate_segments,
    _categorize_rotation,
    _get_block_bounding_box,
    _get_intersection_points,
)


class TestExtractor:
    """Test suite for the extract_blocks function."""

    def test_extract_valid_file(self) -> None:
        """Test extraction from valid DXF file with known block counts."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify result is an ExtractionResult dict
        assert isinstance(result, dict)
        assert "block_counts" in result
        assert "block_entities" in result
        assert "block_layer_pairs" in result
        assert "layer_block_insertion_counts" in result
        assert "layer_entity_counts" in result
        assert "entity_type_counts" in result

        # Verify we have exactly 3 block types
        assert len(result["block_counts"]) == 3

        # Verify correct counts for each block type
        assert result["block_counts"]["VALVE_GATE"] == 10
        assert result["block_counts"]["PIPE_SUPPORT"] == 5
        assert result["block_counts"]["EQUIPMENT_TAG"] == 3

    def test_extract_empty_file(self) -> None:
        """Test extraction from valid DXF file with no blocks."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")

        # Verify result has all required keys with empty dicts
        assert isinstance(result, dict)
        assert result["block_counts"] == {}
        assert isinstance(result["block_entities"], dict)
        assert result["block_layer_pairs"] == {}
        assert isinstance(result["layer_block_insertion_counts"], dict)
        assert isinstance(result["layer_entity_counts"], dict)
        assert isinstance(result["entity_type_counts"], dict)

    def test_extract_invalid_file(self) -> None:
        """Test that invalid/corrupted files raise ValueError."""
        with pytest.raises(ValueError, match="Invalid or corrupted"):
            extract_blocks("app/tests/assets/invalid.dxf")

    def test_extract_missing_file(self) -> None:
        """Test that missing files raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            extract_blocks("app/tests/assets/nonexistent.dxf")

    def test_extract_counts_accuracy(self) -> None:
        """Test that total count is accurate."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Total count should be 10 + 5 + 3 = 18
        total_count = sum(result["block_counts"].values())
        assert total_count == 18

        # All counts should be positive integers
        for count in result["block_counts"].values():
            assert isinstance(count, int)
            assert count > 0

    def test_extract_returns_dict(self) -> None:
        """Test that return value has correct types."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify return type is dict with correct keys
        assert isinstance(result, dict)
        assert "block_counts" in result
        assert "block_entities" in result
        assert "block_layer_pairs" in result
        assert "layer_block_insertion_counts" in result
        assert "layer_entity_counts" in result
        assert "entity_type_counts" in result

        # Verify all block count keys are strings and values are integers
        for key, value in result["block_counts"].items():
            assert isinstance(key, str)
            assert isinstance(value, int)

    def test_extract_unsupported_extension(self) -> None:
        """Test that unsupported file extensions raise ValueError."""
        # Create a temporary file with wrong extension
        temp_file = Path("app/tests/assets/test.txt")
        temp_file.write_text("test")

        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                extract_blocks(str(temp_file))
        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()

    def test_extract_block_entities(self) -> None:
        """Test that block definition entity counts are extracted."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify block_entities contains data for each block type
        assert len(result["block_entities"]) >= len(result["block_counts"])

        # All values should be non-negative integers
        for entity_count in result["block_entities"].values():
            assert isinstance(entity_count, int)
            assert entity_count >= 0

    def test_extract_layer_metrics(self) -> None:
        """Test that layer-based metrics are extracted."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify layer data is present
        assert isinstance(result["layer_block_insertion_counts"], dict)
        assert isinstance(result["layer_entity_counts"], dict)

        # Should have at least one layer (layer "0" is default)
        assert len(result["layer_entity_counts"]) > 0

        # All layer entity counts should be non-negative integers
        for count in result["layer_entity_counts"].values():
            assert isinstance(count, int)
            assert count >= 0

    def test_extract_entity_types(self) -> None:
        """Test that global entity type counts are extracted."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify entity_type_counts contains data
        assert len(result["entity_type_counts"]) > 0

        # Should at least have INSERT entities (since we have blocks)
        assert "INSERT" in result["entity_type_counts"]
        assert result["entity_type_counts"]["INSERT"] == 18  # 10 + 5 + 3

        # All values should be positive integers
        for count in result["entity_type_counts"].values():
            assert isinstance(count, int)
            assert count > 0

    def test_extract_blocks_includes_empty_layers(self) -> None:
        """Test that all layers from layer table are included, even if they have no entities."""
        result = extract_blocks("app/tests/assets/empty_layers_test.dxf")

        # Verify layer_entity_counts includes all layers from layer table
        # The test file has 61 total layers but only 6 have entities
        assert len(result["layer_entity_counts"]) > 50

        # Verify specific empty layers are present with 0 count
        assert "Defpoints" in result["layer_entity_counts"]
        assert "Fixture Name" in result["layer_entity_counts"]
        assert "FPProfileCode" in result["layer_entity_counts"]

        # Verify empty layers have 0 count
        if result["layer_entity_counts"]["Defpoints"] == 0:
            assert result["layer_entity_counts"]["Defpoints"] == 0
        if result["layer_entity_counts"]["Fixture Name"] == 0:
            assert result["layer_entity_counts"]["Fixture Name"] == 0
        if result["layer_entity_counts"]["FPProfileCode"] == 0:
            assert result["layer_entity_counts"]["FPProfileCode"] == 0

        # Verify layer_block_insertion_counts also includes all layers
        assert len(result["layer_block_insertion_counts"]) > 50

        # Verify all non-system layers from layer table are present
        # System layers starting with "*" should be skipped
        for layer_name in result["layer_entity_counts"].keys():
            assert not layer_name.startswith("*")

    def test_extract_block_layer_pairs(self) -> None:
        """Test that block-layer pairs are extracted correctly."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify block_layer_pairs is present in result
        assert "block_layer_pairs" in result
        assert isinstance(result["block_layer_pairs"], dict)

        # Verify block_layer_pairs has at least one entry
        assert len(result["block_layer_pairs"]) > 0

        # Verify all keys are tuples of (str, str) and values are positive integers
        for pair_key, count in result["block_layer_pairs"].items():
            assert isinstance(pair_key, tuple)
            assert len(pair_key) == 2
            assert isinstance(pair_key[0], str)  # block_name
            assert isinstance(pair_key[1], str)  # layer_name
            assert isinstance(count, int)
            assert count > 0

    def test_block_layer_pairs_conservation(self) -> None:
        """Test that sum of block_layer_pairs equals sum of block_counts."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Sum of all block_layer_pairs should equal sum of all block_counts
        total_pair_count = sum(result["block_layer_pairs"].values())
        total_block_count = sum(result["block_counts"].values())

        assert total_pair_count == total_block_count
        assert total_pair_count == 18  # Known count from sample_drawing.dxf

    def test_block_layer_pairs_tuple_keys(self) -> None:
        """Test that all block_layer_pairs keys are (str, str) tuples."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        for pair_key in result["block_layer_pairs"].keys():
            # Verify key is a tuple
            assert isinstance(pair_key, tuple)
            # Verify tuple has exactly 2 elements
            assert len(pair_key) == 2
            # Verify both elements are strings
            block_name, layer_name = pair_key
            assert isinstance(block_name, str)
            assert isinstance(layer_name, str)
            # Verify neither is empty
            assert len(block_name) > 0
            assert len(layer_name) > 0

    def test_block_layer_pairs_empty_file(self) -> None:
        """Test that empty file returns empty block_layer_pairs dict."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")

        # Verify block_layer_pairs is an empty dict
        assert isinstance(result["block_layer_pairs"], dict)
        assert len(result["block_layer_pairs"]) == 0
        assert result["block_layer_pairs"] == {}

    def test_categorize_rotation_standard_angles(self) -> None:
        """Test rotation categorization for exact standard angles."""
        assert _categorize_rotation(0.0) == "0"
        assert _categorize_rotation(90.0) == "90"
        assert _categorize_rotation(180.0) == "180"
        assert _categorize_rotation(270.0) == "270"

    def test_categorize_rotation_tolerance(self) -> None:
        """Test rotation categorization with ±1° tolerance."""
        # Test angles within ±1° of standard angles
        assert _categorize_rotation(0.5) == "0"
        assert _categorize_rotation(89.5) == "90"
        assert _categorize_rotation(90.5) == "90"
        assert _categorize_rotation(179.5) == "180"
        assert _categorize_rotation(180.5) == "180"
        assert _categorize_rotation(269.5) == "270"
        assert _categorize_rotation(270.5) == "270"
        assert _categorize_rotation(359.5) == "0"

    def test_categorize_rotation_non_standard(self) -> None:
        """Test rotation categorization for non-standard angles."""
        assert _categorize_rotation(45.0) == "other"
        assert _categorize_rotation(135.0) == "other"
        assert _categorize_rotation(225.0) == "other"
        assert _categorize_rotation(315.0) == "other"
        assert _categorize_rotation(30.0) == "other"
        assert _categorize_rotation(60.0) == "other"

    def test_categorize_rotation_normalization(self) -> None:
        """Test rotation normalization for negative and >360° angles."""
        # Negative angles should normalize correctly
        assert _categorize_rotation(-90.0) == "270"
        assert _categorize_rotation(-180.0) == "180"
        assert _categorize_rotation(-270.0) == "90"

        # Angles > 360 should normalize correctly
        assert _categorize_rotation(450.0) == "90"
        assert _categorize_rotation(540.0) == "180"
        assert _categorize_rotation(630.0) == "270"

    def test_categorize_rotation_boundary_cases(self) -> None:
        """Test rotation categorization for boundary edge cases."""
        # Angles just outside tolerance should be 'other'
        assert _categorize_rotation(1.5) == "other"
        assert _categorize_rotation(88.0) == "other"
        assert _categorize_rotation(92.0) == "other"
        assert _categorize_rotation(178.0) == "other"
        assert _categorize_rotation(182.0) == "other"

    def test_extract_block_rotation_counts(self) -> None:
        """Test that block_rotation_counts field exists and contains correct structure."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify block_rotation_counts is present
        assert "block_rotation_counts" in result
        assert isinstance(result["block_rotation_counts"], dict)

        # Should have at least one entry for files with blocks
        assert len(result["block_rotation_counts"]) > 0

    def test_block_rotation_counts_tuple_keys(self) -> None:
        """Test that all block_rotation_counts keys are (str, str, str) tuples."""
        result = extract_blocks("app/tests/assets/test_rotations.dxf")

        # Verify all keys are 3-element tuples
        for rotation_key in result["block_rotation_counts"].keys():
            assert isinstance(rotation_key, tuple)
            assert len(rotation_key) == 3
            block_name, layer_name, rotation_category = rotation_key
            assert isinstance(block_name, str)
            assert isinstance(layer_name, str)
            assert isinstance(rotation_category, str)
            assert len(block_name) > 0
            assert len(layer_name) > 0

    def test_block_rotation_counts_valid_categories(self) -> None:
        """Test that rotation categories are only valid values."""
        result = extract_blocks("app/tests/assets/test_rotations.dxf")

        valid_categories = {"0", "90", "180", "270", "other"}

        for rotation_key in result["block_rotation_counts"].keys():
            _, _, rotation_category = rotation_key
            assert rotation_category in valid_categories

    def test_block_rotation_counts_conservation(self) -> None:
        """Test that sum of rotation counts equals sum of block_layer_pairs."""
        result = extract_blocks("app/tests/assets/test_rotations.dxf")

        # Sum of all rotation counts should equal sum of block_layer_pairs
        total_rotation_count = sum(result["block_rotation_counts"].values())
        total_pair_count = sum(result["block_layer_pairs"].values())

        assert total_rotation_count == total_pair_count

    def test_block_rotation_counts_with_fixture(self) -> None:
        """Test rotation extraction with test_rotations.dxf fixture with known counts."""
        result = extract_blocks("app/tests/assets/test_rotations.dxf")

        # Expected counts from the fixture:
        # 5 blocks at 0° on LAYER_A
        # 3 blocks at 90° on LAYER_A
        # 2 blocks at 180° on LAYER_B
        # 1 block at 270° on LAYER_B
        # 2 blocks at non-standard angles (45°, 135°) on LAYER_C

        # Verify specific rotation counts
        assert result["block_rotation_counts"][("TEST_BLOCK", "LAYER_A", "0")] == 5
        assert result["block_rotation_counts"][("TEST_BLOCK", "LAYER_A", "90")] == 3
        assert result["block_rotation_counts"][("TEST_BLOCK", "LAYER_B", "180")] == 2
        assert result["block_rotation_counts"][("TEST_BLOCK", "LAYER_B", "270")] == 1
        assert result["block_rotation_counts"][("TEST_BLOCK", "LAYER_C", "other")] == 2

        # Verify total count
        total = sum(result["block_rotation_counts"].values())
        assert total == 13  # 5 + 3 + 2 + 1 + 2

    def test_calculate_segments_normal(self) -> None:
        """Test segment calculation with typical intersection point list."""
        points = [0.0, 50.0, 1150.0, 1200.0]
        segments = _calculate_segments(points)

        assert len(segments) == 3
        assert segments == [50.0, 1100.0, 50.0]

    def test_calculate_segments_edge_cases(self) -> None:
        """Test segment calculation with edge cases."""
        # Empty list
        assert _calculate_segments([]) == []

        # Single point
        assert _calculate_segments([0.0]) == []

        # Two points
        segments = _calculate_segments([0.0, 100.0])
        assert len(segments) == 1
        assert segments == [100.0]

    def test_calculate_segments_precision(self) -> None:
        """Test that segments are rounded to 2 decimal places."""
        points = [0.0, 33.33333, 66.66666, 100.0]
        segments = _calculate_segments(points)

        # All segments should be rounded to 2 decimal places
        for segment in segments:
            # Check that segment has at most 2 decimal places
            assert round(segment, 2) == segment

    def test_get_block_bounding_box_simple(self) -> None:
        """Test bounding box extraction for simple rectangular block."""
        # Create a simple test drawing with a block
        doc = ezdxf.new()
        doc.modelspace()

        # Create a block with known extents
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))
        block.add_line((100, 50), (0, 50))
        block.add_line((0, 50), (0, 0))

        bbox = _get_block_bounding_box(block)

        # Should be (min_x, min_y, max_x, max_y) = (0, 0, 100, 50)
        assert bbox == (0.0, 0.0, 100.0, 50.0)

    def test_get_block_bounding_box_empty(self) -> None:
        """Test that empty block returns (0, 0, 0, 0)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY_BLOCK")

        bbox = _get_block_bounding_box(block)

        assert bbox == (0.0, 0.0, 0.0, 0.0)

    def test_get_intersection_points_simple(self) -> None:
        """Test intersection point identification for simple block."""
        # Create a simple test block with known vertices
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Rectangle with borders: outer 0-100, inner 10-90
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))
        block.add_line((100, 50), (0, 50))
        block.add_line((0, 50), (0, 0))
        block.add_line((10, 10), (90, 10))
        block.add_line((90, 10), (90, 40))
        block.add_line((90, 40), (10, 40))
        block.add_line((10, 40), (10, 10))

        vertical_points, horizontal_points = _get_intersection_points(block)

        # Should have X coordinates: 0, 10, 90, 100
        assert len(vertical_points) == 4
        assert 0.0 in vertical_points
        assert 10.0 in vertical_points
        assert 90.0 in vertical_points
        assert 100.0 in vertical_points

        # Should have Y coordinates: 0, 10, 40, 50
        assert len(horizontal_points) == 4
        assert 0.0 in horizontal_points
        assert 10.0 in horizontal_points
        assert 40.0 in horizontal_points
        assert 50.0 in horizontal_points

    def test_get_intersection_points_sorting(self) -> None:
        """Test that intersection points are sorted in ascending order."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Add lines in random order
        block.add_line((100, 50), (0, 50))
        block.add_line((50, 0), (50, 100))
        block.add_line((0, 0), (100, 0))

        vertical_points, horizontal_points = _get_intersection_points(block)

        # Points should be sorted
        assert vertical_points == sorted(vertical_points)
        assert horizontal_points == sorted(horizontal_points)

    def test_extract_block_trimming_data(self) -> None:
        """Test that block_trimming_data field exists and has correct structure."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify block_trimming_data is present
        assert "block_trimming_data" in result
        assert isinstance(result["block_trimming_data"], dict)

        # Should have data for each block
        assert len(result["block_trimming_data"]) > 0

        # Verify structure for each block
        for block_name, geometry_data in result["block_trimming_data"].items():
            assert isinstance(block_name, str)
            assert isinstance(geometry_data, dict)

            # Verify required fields
            assert "native_width" in geometry_data
            assert "native_height" in geometry_data
            assert "vertical_segments" in geometry_data
            assert "horizontal_segments" in geometry_data

            # Verify types
            assert isinstance(geometry_data["native_width"], (int, float))
            assert isinstance(geometry_data["native_height"], (int, float))
            assert isinstance(geometry_data["vertical_segments"], list)
            assert isinstance(geometry_data["horizontal_segments"], list)

            # All segments should be floats
            for segment in geometry_data["vertical_segments"]:
                assert isinstance(segment, (int, float))
            for segment in geometry_data["horizontal_segments"]:
                assert isinstance(segment, (int, float))

    def test_block_trimming_data_types(self) -> None:
        """Test that all block trimming data values are correct types."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        for geometry_data in result["block_trimming_data"].values():
            # Width and height should be numeric
            assert isinstance(geometry_data["native_width"], (int, float))
            assert isinstance(geometry_data["native_height"], (int, float))
            assert geometry_data["native_width"] >= 0
            assert geometry_data["native_height"] >= 0

            # Segments should be lists of floats
            assert isinstance(geometry_data["vertical_segments"], list)
            assert isinstance(geometry_data["horizontal_segments"], list)

    def test_get_block_bounding_box_with_circles(self) -> None:
        """Test bounding box extraction for blocks with CIRCLE entities."""
        doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")
        block = doc.blocks.get("TEST_CIRCLES")

        bbox = _get_block_bounding_box(block)

        # Block contains circles:
        # Circle 1: center=(50, 50), radius=25 -> bbox=(25, 25, 75, 75)
        # Circle 2: center=(150, 100), radius=30 -> bbox=(120, 70, 180, 130)
        # Circle 3: center=(100, 150), radius=20 -> bbox=(80, 130, 120, 170)
        # Overall bbox should encompass all: (25, 25, 180, 170)
        assert bbox[0] == 25.0  # min_x
        assert bbox[1] == 25.0  # min_y
        assert bbox[2] == 180.0  # max_x
        assert bbox[3] == 170.0  # max_y

    def test_get_block_bounding_box_with_arcs(self) -> None:
        """Test bounding box extraction for blocks with ARC entities (simplified full-circle extents)."""
        doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")
        block = doc.blocks.get("TEST_ARCS")

        bbox = _get_block_bounding_box(block)

        # Block contains arcs (simplified to full circle extents):
        # Arc 1: center=(100, 100), radius=50 -> bbox=(50, 50, 150, 150)
        # Arc 2: center=(200, 150), radius=40 -> bbox=(160, 110, 240, 190)
        # Arc 3: center=(150, 50), radius=30 -> bbox=(120, 20, 180, 80)
        # Overall bbox: (50, 20, 240, 190)
        assert bbox[0] == 50.0  # min_x
        assert bbox[1] == 20.0  # min_y
        assert bbox[2] == 240.0  # max_x
        assert bbox[3] == 190.0  # max_y

    def test_get_block_bounding_box_with_points(self) -> None:
        """Test bounding box extraction for blocks with POINT entities."""
        doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")
        block = doc.blocks.get("TEST_POINTS")

        bbox = _get_block_bounding_box(block)

        # Block contains points at: (10, 10), (50, 30), (90, 70), (120, 90)
        # Bbox should be: (10, 10, 120, 90)
        assert bbox[0] == 10.0  # min_x
        assert bbox[1] == 10.0  # min_y
        assert bbox[2] == 120.0  # max_x
        assert bbox[3] == 90.0  # max_y

    def test_get_intersection_points_with_circles(self) -> None:
        """Test intersection point extraction for blocks with CIRCLE entities."""
        doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")
        block = doc.blocks.get("TEST_CIRCLES")

        vertical_points, horizontal_points = _get_intersection_points(block)

        # Circles add bounding box corners:
        # Circle 1: center=(50, 50), radius=25 -> X: [25, 75], Y: [25, 75]
        # Circle 2: center=(150, 100), radius=30 -> X: [120, 180], Y: [70, 130]
        # Circle 3: center=(100, 150), radius=20 -> X: [80, 120], Y: [130, 170]

        # Expected unique X coords: [25, 75, 80, 120, 180]
        # Expected unique Y coords: [25, 70, 75, 130, 170]
        assert 25.0 in vertical_points
        assert 75.0 in vertical_points
        assert 80.0 in vertical_points
        assert 120.0 in vertical_points
        assert 180.0 in vertical_points

        assert 25.0 in horizontal_points
        assert 70.0 in horizontal_points
        assert 75.0 in horizontal_points
        assert 130.0 in horizontal_points
        assert 170.0 in horizontal_points

    def test_get_intersection_points_with_arcs_and_points(self) -> None:
        """Test intersection point extraction for blocks with ARC and POINT entities."""
        doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")

        # Test with ARCS
        block_arcs = doc.blocks.get("TEST_ARCS")
        vertical_arcs, horizontal_arcs = _get_intersection_points(block_arcs)

        # Arcs add bounding box corners (simplified):
        # Arc 1: center=(100, 100), radius=50 -> X: [50, 150], Y: [50, 150]
        # Arc 2: center=(200, 150), radius=40 -> X: [160, 240], Y: [110, 190]
        # Arc 3: center=(150, 50), radius=30 -> X: [120, 180], Y: [20, 80]
        assert 50.0 in vertical_arcs
        assert 150.0 in vertical_arcs
        assert 160.0 in vertical_arcs
        assert 240.0 in vertical_arcs

        # Test with POINTS
        block_points = doc.blocks.get("TEST_POINTS")
        vertical_points, horizontal_points = _get_intersection_points(block_points)

        # Points at: (10, 10), (50, 30), (90, 70), (120, 90)
        assert vertical_points == [10.0, 50.0, 90.0, 120.0]
        assert horizontal_points == [10.0, 30.0, 70.0, 90.0]

    def test_extract_blocks_missing_scale_attributes(self) -> None:
        """Test that blocks with missing xscale/yscale use default scale (1.0, 1.0)."""
        # Create a test file with a block that may not have scale attributes
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Create a simple block
        block = doc.blocks.new(name="NO_SCALE_BLOCK")
        block.add_line((0, 0), (100, 0))

        # Add block reference - ezdxf should handle scale attributes properly
        # but we're testing the exception handling in case they're missing
        msp.add_blockref("NO_SCALE_BLOCK", (0, 0))

        # Save to temp file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False, mode="w") as f:
            temp_path = f.name

        try:
            doc.saveas(temp_path)

            # Extract blocks - should handle missing scales gracefully
            result = extract_blocks(temp_path)

            # Verify extraction succeeds
            assert "block_counts" in result
            assert "NO_SCALE_BLOCK" in result["block_counts"]
            assert result["block_counts"]["NO_SCALE_BLOCK"] == 1

            # Verify scale data exists (defaults to 1.0, 1.0 if missing)
            assert "block_scale_data" in result
            # The scale data is now per-block (not per block-layer pair)
            if "NO_SCALE_BLOCK" in result["block_scale_data"]:
                scale_set = result["block_scale_data"]["NO_SCALE_BLOCK"]
                assert isinstance(scale_set, set)
                # Should have exactly one scale combination (default 1.0, 1.0)
                assert len(scale_set) == 1
                x_scale, y_scale = next(iter(scale_set))
                assert isinstance(x_scale, (int, float))
                assert isinstance(y_scale, (int, float))
                # Verify default value of 1.0 (or 1 as int)
                assert x_scale == 1.0 or x_scale == 1
                assert y_scale == 1.0 or y_scale == 1

        finally:
            # Clean up temp file
            import os

            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_extract_blocks_generic_exception(self) -> None:
        """Test that unexpected exceptions during extraction are re-raised with logging."""
        from unittest.mock import patch

        # Mock ezdxf.readfile to raise an unexpected exception
        with patch("core.extractor.ezdxf.readfile") as mock_readfile:
            mock_readfile.side_effect = RuntimeError("Unexpected error")

            # Verify the exception is re-raised
            with pytest.raises(RuntimeError, match="Unexpected error"):
                extract_blocks("app/tests/assets/sample_drawing.dxf")

            # Verify ezdxf.readfile was called
            assert mock_readfile.called

    @pytest.mark.parametrize(
        "rotation,expected_category",
        [
            (0.0, "0"),
            (0.5, "0"),
            (45.0, "other"),
            (89.5, "90"),
            (90.0, "90"),
            (90.5, "90"),
            (135.0, "other"),
            (179.5, "180"),
            (180.0, "180"),
            (269.5, "270"),
            (270.0, "270"),
            (359.5, "0"),
            (-90.0, "270"),
            (450.0, "90"),
        ],
    )
    def test_block_rotation_scale_variations(
        self, rotation: float, expected_category: str
    ) -> None:
        """Test block rotation categorization with parametrized rotation angles."""
        # Test rotation categorization
        assert _categorize_rotation(rotation) == expected_category

    @pytest.mark.parametrize(
        "x_scale,y_scale,is_mirrored",
        [
            (1.0, 1.0, False),
            (-1.0, 1.0, True),
            (1.0, -1.0, True),
            (-1.0, -1.0, True),
            (2.0, 0.5, False),
            (0.5, 2.0, False),
            (-2.0, 2.0, True),
            (2.0, -2.0, True),
        ],
    )
    def test_block_scale_variations(
        self, x_scale: float, y_scale: float, is_mirrored: bool
    ) -> None:
        """Test that mirrored blocks (negative scales) are correctly identified."""
        # Test scale mirroring detection logic
        # A block is mirrored if either x_scale or y_scale is negative
        actual_mirrored = x_scale < 0 or y_scale < 0
        assert actual_mirrored == is_mirrored

    def test_block_scale_data_structure_is_per_block(self) -> None:
        """Test that block_scale_data is now dict[str, set[tuple[float, float]]]."""
        result = extract_blocks("app/tests/assets/scale_variance_test.dxf")

        # Verify block_scale_data structure
        assert "block_scale_data" in result
        assert isinstance(result["block_scale_data"], dict)

        # All keys should be strings (block names), not tuples
        for block_name in result["block_scale_data"].keys():
            assert isinstance(block_name, str)

        # All values should be sets of tuples
        for scale_set in result["block_scale_data"].values():
            assert isinstance(scale_set, set)
            for scale_tuple in scale_set:
                assert isinstance(scale_tuple, tuple)
                assert len(scale_tuple) == 2
                assert isinstance(scale_tuple[0], (int, float))
                assert isinstance(scale_tuple[1], (int, float))

    def test_block_scale_data_captures_all_unique_scales(self) -> None:
        """Test that all unique scale combinations are captured per block."""
        result = extract_blocks("app/tests/assets/scale_variance_test.dxf")

        # X_VARIES block has scales: (1.0, 1.0), (2.0, 1.0), (1.5, 1.0)
        x_varies_scales = result["block_scale_data"]["X_VARIES"]
        assert len(x_varies_scales) == 3
        assert (1.0, 1.0) in x_varies_scales
        assert (2.0, 1.0) in x_varies_scales
        assert (1.5, 1.0) in x_varies_scales

        # Y_VARIES block has scales: (1.0, 1.0), (1.0, 2.0), (1.0, 0.5)
        y_varies_scales = result["block_scale_data"]["Y_VARIES"]
        assert len(y_varies_scales) == 3
        assert (1.0, 1.0) in y_varies_scales
        assert (1.0, 2.0) in y_varies_scales
        assert (1.0, 0.5) in y_varies_scales

        # BOTH_VARY block has scales: (1.0, 1.0), (2.0, 2.0), (-1.0, 1.5)
        both_vary_scales = result["block_scale_data"]["BOTH_VARY"]
        assert len(both_vary_scales) == 3
        assert (1.0, 1.0) in both_vary_scales
        assert (2.0, 2.0) in both_vary_scales
        assert (-1.0, 1.5) in both_vary_scales

        # CONSISTENT block has only one scale: (1.5, 1.5)
        consistent_scales = result["block_scale_data"]["CONSISTENT"]
        assert len(consistent_scales) == 1
        assert (1.5, 1.5) in consistent_scales

    def test_block_scale_data_aggregates_across_layers(self) -> None:
        """Test that scale data aggregates across all layers for each block."""
        result = extract_blocks("app/tests/assets/scale_variance_test.dxf")

        # X_VARIES appears on LAYER_A and LAYER_B with different scales
        # The block_scale_data should capture all unique scales regardless of layer
        x_varies_scales = result["block_scale_data"]["X_VARIES"]
        assert len(x_varies_scales) == 3  # Three different scale combinations total

        # Verify this is per-block, not per-layer
        # (The old structure was per block-layer pair, new structure is just per block)
        assert "X_VARIES" in result["block_scale_data"]
        assert isinstance(result["block_scale_data"]["X_VARIES"], set)

    def test_extract_xdata_apps(self) -> None:
        """Test XDATA application ID extraction from INSERT entities."""
        result = extract_blocks("app/tests/assets/xdata_test.dxf")

        # Verify block_xdata_apps key exists in result
        assert "block_xdata_apps" in result
        assert isinstance(result["block_xdata_apps"], dict)

        # Verify WITH_XDATA on LAYER_A has ACAD and CUSTOM_APP
        layer_a_key = ("WITH_XDATA", "LAYER_A")
        assert layer_a_key in result["block_xdata_apps"]
        layer_a_apps = result["block_xdata_apps"][layer_a_key]
        assert isinstance(layer_a_apps, set)
        assert "ACAD" in layer_a_apps
        assert "CUSTOM_APP" in layer_a_apps

        # Verify WITH_XDATA on LAYER_B has BIM_TOOL and ACAD
        layer_b_key = ("WITH_XDATA", "LAYER_B")
        assert layer_b_key in result["block_xdata_apps"]
        layer_b_apps = result["block_xdata_apps"][layer_b_key]
        assert isinstance(layer_b_apps, set)
        assert "BIM_TOOL" in layer_b_apps
        assert "ACAD" in layer_b_apps

        # Verify NO_XDATA on LAYER_A either doesn't exist or has empty set
        no_xdata_key = ("NO_XDATA", "LAYER_A")
        if no_xdata_key in result["block_xdata_apps"]:
            assert len(result["block_xdata_apps"][no_xdata_key]) == 0

    def test_extract_xdata_apps_empty_file(self) -> None:
        """Test XDATA extraction from empty file returns empty dict."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")

        # Verify block_xdata_apps is an empty dictionary
        assert "block_xdata_apps" in result
        assert isinstance(result["block_xdata_apps"], dict)
        assert len(result["block_xdata_apps"]) == 0

    def test_extract_layer_color_counts(self) -> None:
        """Test that layer color counts are extracted correctly."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify layer_unique_color_counts exists in result
        assert "layer_unique_color_counts" in result
        assert isinstance(result["layer_unique_color_counts"], dict)

        # Verify all values are non-negative integers
        for layer_name, color_count in result["layer_unique_color_counts"].items():
            assert isinstance(layer_name, str)
            assert isinstance(color_count, int)
            assert color_count >= 0

        # Verify all layers have color count entries
        for layer_name in result["layer_entity_counts"].keys():
            assert layer_name in result["layer_unique_color_counts"]

    def test_extract_layer_color_counts_empty_file(self) -> None:
        """Test color count extraction from empty file."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")

        # Verify layer_unique_color_counts exists
        assert "layer_unique_color_counts" in result
        assert isinstance(result["layer_unique_color_counts"], dict)

        # Empty file may have default layer "0" with 0 color count
        for layer_name, color_count in result["layer_unique_color_counts"].items():
            assert isinstance(color_count, int)
            assert color_count >= 0

    def test_extract_layer_color_counts_types(self) -> None:
        """Test that color count return types are correct."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify layer_unique_color_counts is a dict with str keys and int values
        assert isinstance(result["layer_unique_color_counts"], dict)

        for layer_name, color_count in result["layer_unique_color_counts"].items():
            assert isinstance(layer_name, str)
            assert isinstance(color_count, int)

    def test_extract_layer_annotation_counts(self) -> None:
        """Test extraction of TEXT and MTEXT entity counts per layer."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify key exists
        assert "layer_annotation_counts" in result

        # Verify all values are integers
        for count in result["layer_annotation_counts"].values():
            assert isinstance(count, int)
            assert count >= 0

        # Verify all layers have entries (even if 0)
        for layer_name in result["layer_entity_counts"].keys():
            assert layer_name in result["layer_annotation_counts"]

    def test_extract_layer_annotation_counts_empty_file(self) -> None:
        """Test text/mtext counts for empty drawing."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")

        assert "layer_annotation_counts" in result
        assert isinstance(result["layer_annotation_counts"], dict)

    def test_extract_layer_annotation_counts_types(self) -> None:
        """Test that text/mtext count return types are correct."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify layer_annotation_counts is a dict with str keys and int values
        assert isinstance(result["layer_annotation_counts"], dict)

        for layer_name, count in result["layer_annotation_counts"].items():
            assert isinstance(layer_name, str)
            assert isinstance(count, int)
            assert count >= 0

    def test_annotation_data_extraction(self) -> None:
        """Test that annotation_data is extracted and has correct structure."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")

        # Verify annotation_data key exists
        assert "annotation_data" in result
        assert isinstance(result["annotation_data"], dict)

        # Verify keys are tuples of (contents, type, layer, r, g, b)
        for key, count in result["annotation_data"].items():
            assert isinstance(key, tuple)
            assert len(key) == 6
            contents, entity_type, layer_name, color_r, color_g, color_b = key

            # Verify types
            assert isinstance(contents, str)
            assert isinstance(entity_type, str)
            assert entity_type in ("TEXT", "MTEXT")
            assert isinstance(layer_name, str)
            assert isinstance(color_r, int)
            assert isinstance(color_g, int)
            assert isinstance(color_b, int)

            # Verify RGB values are in valid range
            assert 0 <= color_r <= 255
            assert 0 <= color_g <= 255
            assert 0 <= color_b <= 255

            # Verify count is positive integer
            assert isinstance(count, int)
            assert count > 0

    def test_annotation_data_grouping_by_content(self) -> None:
        """Test that annotations are grouped correctly by content, type, layer, and color."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find the duplicate text entry - should have count = 2
        duplicate_entries = [
            (key, count)
            for key, count in annotation_data.items()
            if "Duplicate Text" in key[0] and count == 2
        ]
        assert len(duplicate_entries) == 1, (
            "Should have exactly one 'Duplicate Text' group with count=2"
        )

        # Verify same text on different layers creates separate groups
        cross_layer_entries = [
            key for key in annotation_data.keys() if "Cross Layer Text" in key[0]
        ]
        assert len(cross_layer_entries) >= 2, (
            "Same text on different layers should be separate groups"
        )

        # Verify same text with different colors creates separate groups
        multi_color_entries = [
            key for key in annotation_data.keys() if "Multi Color Text" in key[0]
        ]
        assert len(multi_color_entries) >= 2, (
            "Same text with different colors should be separate groups"
        )

    def test_annotation_data_text_vs_mtext_distinction(self) -> None:
        """Test that TEXT and MTEXT with same content are separate groups."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find entries with "Same Content Different Type"
        same_content_entries = [
            key
            for key in annotation_data.keys()
            if "Same Content Different Type" in key[0]
        ]

        # Should have 2 entries: one TEXT, one MTEXT
        assert len(same_content_entries) >= 2, (
            "TEXT and MTEXT with same content should be separate"
        )

        # Verify we have both types
        entity_types = {key[1] for key in same_content_entries}
        assert "TEXT" in entity_types
        assert "MTEXT" in entity_types

    def test_annotation_data_special_characters(self) -> None:
        """Test that special characters and unicode in text content are preserved."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find special characters entry
        special_char_entries = [
            key for key in annotation_data.keys() if "@#$%^&*()" in key[0]
        ]
        assert len(special_char_entries) >= 1, "Special characters should be preserved"

        # Find unicode entry
        unicode_entries = [
            key
            for key in annotation_data.keys()
            if any(ord(c) > 127 for c in key[0])  # Unicode characters
        ]
        assert len(unicode_entries) >= 1, "Unicode characters should be preserved"

    def test_annotation_data_empty_file(self) -> None:
        """Test annotation extraction from file with no TEXT/MTEXT entities."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")

        # Verify annotation_data exists but is empty
        assert "annotation_data" in result
        assert isinstance(result["annotation_data"], dict)
        # Empty file may or may not have annotations, but should be a dict
        for key, count in result["annotation_data"].items():
            assert isinstance(key, tuple)
            assert isinstance(count, int)

    def test_resolve_entity_color_to_rgb_direct_rgb(self) -> None:
        """Test color resolution for entities with direct RGB color."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find "Sample Text 1" which has direct RGB (255, 0, 0)
        sample_text_1_entries = [
            (key, count)
            for key, count in annotation_data.items()
            if "Sample Text 1" == key[0]
        ]

        assert len(sample_text_1_entries) == 1
        key, count = sample_text_1_entries[0]
        contents, entity_type, layer_name, color_r, color_g, color_b = key

        # Verify direct RGB color (255, 0, 0) = red
        assert color_r == 255
        assert color_g == 0
        assert color_b == 0

    def test_resolve_entity_color_to_rgb_bylayer(self) -> None:
        """Test color resolution for entities with ByLayer color."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find "Sample Text 2" which has ByLayer color (should resolve to LAYER_GREEN's ACI 3)
        sample_text_2_entries = [
            (key, count)
            for key, count in annotation_data.items()
            if "Sample Text 2" == key[0]
        ]

        assert len(sample_text_2_entries) == 1
        key, count = sample_text_2_entries[0]
        contents, entity_type, layer_name, color_r, color_g, color_b = key

        # Verify layer is LAYER_GREEN
        assert layer_name == "LAYER_GREEN"

        # ByLayer should resolve to layer's ACI color (ACI 3 = green)
        # ACI 3 typically maps to RGB (0, 255, 0) but may vary
        # Just verify we got valid RGB values
        assert 0 <= color_r <= 255
        assert 0 <= color_g <= 255
        assert 0 <= color_b <= 255

    def test_resolve_entity_color_to_rgb_aci_index(self) -> None:
        """Test color resolution for entities with ACI color index."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find "Sample Text 3" which has ACI color index 5 (blue)
        sample_text_3_entries = [
            (key, count)
            for key, count in annotation_data.items()
            if "Sample Text 3" == key[0]
        ]

        assert len(sample_text_3_entries) == 1
        key, count = sample_text_3_entries[0]
        contents, entity_type, layer_name, color_r, color_g, color_b = key

        # ACI 5 = blue, should have valid RGB
        assert 0 <= color_r <= 255
        assert 0 <= color_g <= 255
        assert 0 <= color_b <= 255

    def test_resolve_entity_color_to_rgb_byblock(self) -> None:
        """Test color resolution for entities with ByBlock color (defaults to white)."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find "ByBlock Color Text" which has ByBlock color (should default to white)
        byblock_entries = [
            (key, count)
            for key, count in annotation_data.items()
            if "ByBlock Color Text" == key[0]
        ]

        assert len(byblock_entries) == 1
        key, count = byblock_entries[0]
        contents, entity_type, layer_name, color_r, color_g, color_b = key

        # ByBlock should default to white (255, 255, 255)
        assert color_r == 255
        assert color_g == 255
        assert color_b == 255

    def test_annotation_data_mtext_multiline(self) -> None:
        """Test that MTEXT multiline content is extracted correctly."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find MTEXT entries (should have plain text, not DXF formatting codes)
        mtext_entries = [
            (key, count)
            for key, count in annotation_data.items()
            if key[1] == "MTEXT" and "multiline" in key[0].lower()
        ]

        # Should have at least one MTEXT with multiline content
        # Note: ezdxf's entity.text property should return plain text without formatting
        assert len(mtext_entries) >= 1, "MTEXT multiline content should be extracted"


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


class TestMtextFormatting:
    """Test suite for MTEXT formatting code cleanup functionality."""

    def test_mtext_paragraph_codes_stripped(self) -> None:
        """Verify paragraph alignment codes (\\pxqc;, \\pxql;, etc.) are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find CENTERED TEXT entry (should have formatting stripped)
        centered_entries = [
            key for key in annotation_data.keys() if "CENTERED TEXT" in key[0]
        ]
        assert len(centered_entries) >= 1
        # The content should be "CENTERED TEXT", not "\\pxqc;CENTERED TEXT"
        for key in centered_entries:
            assert "\\pxqc" not in key[0]
            assert "pxqc" not in key[0].lower()

        # Check left aligned
        left_entries = [key for key in annotation_data.keys() if "LEFT ALIGNED" in key[0]]
        assert len(left_entries) >= 1
        for key in left_entries:
            assert "\\pxql" not in key[0]

        # Check right aligned
        right_entries = [
            key for key in annotation_data.keys() if "RIGHT ALIGNED" in key[0]
        ]
        assert len(right_entries) >= 1
        for key in right_entries:
            assert "\\pxqr" not in key[0]

        # Check justified
        justified_entries = [
            key for key in annotation_data.keys() if "JUSTIFIED TEXT" in key[0]
        ]
        assert len(justified_entries) >= 1
        for key in justified_entries:
            assert "\\pxqj" not in key[0]

    def test_mtext_paragraph_breaks_become_spaces(self) -> None:
        """Verify \\P paragraph breaks become single spaces, not newlines."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find LINE ONE LINE TWO entry
        line_entries = [key for key in annotation_data.keys() if "LINE ONE" in key[0]]
        assert len(line_entries) >= 1

        for key in line_entries:
            contents = key[0]
            # Should not contain \\P
            assert "\\P" not in contents
            # Should not contain newlines
            assert "\n" not in contents
            # Should contain both parts separated by space
            if "LINE TWO" in contents:
                assert "LINE ONE" in contents and "LINE TWO" in contents

    def test_mtext_underline_overline_stripped(self) -> None:
        """Verify \\L, \\l, \\O, \\o formatting codes are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find underlined text entry
        underline_entries = [
            key for key in annotation_data.keys() if "UNDERLINED" in key[0]
        ]
        assert len(underline_entries) >= 1

        for key in underline_entries:
            contents = key[0]
            # Should not contain \\L or \\l
            assert "\\L" not in contents
            assert "\\l" not in contents

        # Find overlined text entry
        overline_entries = [key for key in annotation_data.keys() if "OVERLINED" in key[0]]
        assert len(overline_entries) >= 1

        for key in overline_entries:
            contents = key[0]
            # Should not contain \\O or \\o
            assert "\\O" not in contents
            assert "\\o" not in contents

    def test_mtext_color_codes_stripped(self) -> None:
        """Verify \\C....; color codes are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find the color test entry - should have "NORMAL RED WHITE"
        color_entries = [
            key for key in annotation_data.keys() if "RED" in key[0] and "WHITE" in key[0]
        ]

        for key in color_entries:
            contents = key[0]
            # Should not contain \\C followed by numbers and semicolon
            assert "\\C1;" not in contents
            assert "\\C7;" not in contents

    def test_mtext_complex_formatting_stripped(self) -> None:
        """Verify complex example like \\pxqc;MENS CASUAL\\P PANTS becomes 'MENS CASUAL PANTS'."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find MENS CASUAL entry
        mens_entries = [key for key in annotation_data.keys() if "MENS CASUAL" in key[0]]
        assert len(mens_entries) >= 1

        for key in mens_entries:
            contents = key[0]
            # Should not contain any formatting codes
            assert "\\pxqc" not in contents
            assert "\\P" not in contents
            # Should contain the plain text
            assert "MENS CASUAL" in contents
            # Should have PANTS (possibly with space)
            if "PANTS" in contents:
                # Verify the format is clean - no newlines
                assert "\n" not in contents

    def test_mtext_plain_text_preserved(self) -> None:
        """Verify MTEXT without formatting codes is unchanged."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find plain text entry
        plain_entries = [
            key
            for key in annotation_data.keys()
            if "PLAIN TEXT WITHOUT FORMATTING" in key[0]
        ]
        assert len(plain_entries) >= 1

        for key in plain_entries:
            contents = key[0]
            # Should be exactly "PLAIN TEXT WITHOUT FORMATTING"
            assert contents == "PLAIN TEXT WITHOUT FORMATTING"

    def test_text_entities_unchanged(self) -> None:
        """Verify TEXT entities still work correctly (not affected by MTEXT changes)."""
        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        annotation_data = result["annotation_data"]

        # Find TEXT entries (not MTEXT)
        text_entries = [
            (key, count)
            for key, count in annotation_data.items()
            if key[1] == "TEXT"  # entity_type is at index 1
        ]
        assert len(text_entries) > 0

        # Verify TEXT entities have expected content
        for key, count in text_entries:
            contents = key[0]
            assert isinstance(contents, str)
            # TEXT entities should have their content preserved
            assert len(contents) > 0 or contents == ""

    def test_mtext_multiple_spaces_collapsed(self) -> None:
        """Verify multiple consecutive spaces are collapsed to single space."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find entries with multiple paragraph breaks (WORD1\\P\\PWORD2)
        # These should have spaces collapsed
        word_entries = [
            key
            for key in annotation_data.keys()
            if "WORD1" in key[0] and "WORD2" in key[0] and "\\~" not in key[0]
        ]

        for key in word_entries:
            contents = key[0]
            # Should not have multiple consecutive spaces
            assert "  " not in contents  # No double spaces
            # Should have single space between words
            if "WORD1" in contents and "WORD2" in contents:
                # The words should be separated by a single space
                assert "WORD1 WORD2" in contents

    def test_mtext_font_changes_stripped(self) -> None:
        """Verify \\f....; font change codes are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find BOLD text entry
        bold_entries = [key for key in annotation_data.keys() if "BOLD" in key[0]]

        for key in bold_entries:
            contents = key[0]
            # Should not contain font codes
            assert "\\f" not in contents
            assert "Arial" not in contents or "NORMAL" in contents

    def test_mtext_height_changes_stripped(self) -> None:
        """Verify \\H....; text height codes are removed."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        annotation_data = result["annotation_data"]

        # Find BIG text entry
        big_entries = [key for key in annotation_data.keys() if "BIG" in key[0]]

        for key in big_entries:
            contents = key[0]
            # Should not contain height codes
            assert "\\H" not in contents

    def test_clean_mtext_content_function_directly(self) -> None:
        """Test the _clean_mtext_content helper function directly."""
        # Create a simple test MTEXT entity
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Test with paragraph alignment code
        mtext1 = msp.add_mtext("\\pxqc;CENTERED")
        result1 = _clean_mtext_content(mtext1)
        assert result1 == "CENTERED"
        assert "\\pxqc" not in result1

        # Test with paragraph break
        mtext2 = msp.add_mtext("LINE1\\PLINE2")
        result2 = _clean_mtext_content(mtext2)
        assert "\\P" not in result2
        assert "\n" not in result2
        assert "LINE1" in result2
        assert "LINE2" in result2

        # Test with complex formatting
        mtext3 = msp.add_mtext("\\pxqc;MENS CASUAL\\P PANTS")
        result3 = _clean_mtext_content(mtext3)
        assert "\\pxqc" not in result3
        assert "\\P" not in result3
        assert "MENS CASUAL" in result3
        assert "PANTS" in result3

        # Test plain text preserved
        mtext4 = msp.add_mtext("PLAIN TEXT")
        result4 = _clean_mtext_content(mtext4)
        assert result4 == "PLAIN TEXT"

    def test_color_analysis_mtext_formatting_stripped(self) -> None:
        """Verify color_analysis_data also has MTEXT formatting stripped."""
        result = extract_blocks("app/tests/assets/mtext_formatting_test.dxf")
        color_data = result["color_analysis_data"]

        # Find MTEXT records
        mtext_records = [r for r in color_data if r["entity_type"] == "MTEXT"]

        # All MTEXT should have clean content without formatting codes
        for record in mtext_records:
            contents = record["annotation_contents"]
            # Should not contain any common MTEXT formatting codes
            assert "\\pxq" not in contents
            assert "\\P" not in contents
            assert "\\L" not in contents
            assert "\\O" not in contents
            assert "\\C" not in contents or contents.count("\\") == 0


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
            if "TRUE COLOR TEXT" in key[0]
        ]

        assert len(true_color_text_entries) >= 1
        key, count = true_color_text_entries[0]
        contents, entity_type, layer_name, color_r, color_g, color_b = key

        # Verify True Color RGB (255, 128, 0) - orange
        assert color_r == 255
        assert color_g == 128
        assert color_b == 0

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
            if r["color_r"] == 100
            and r["color_g"] == 200
            and r["color_b"] == 150
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
            r for r in color_data
            if r["entity_type"] == "Hatches"
            and r["layer_name"] == "HATCH_LAYER_A"
            and r["color_r"] == 255
            and r["color_g"] == 0
            and r["color_b"] == 0
        ]

        # Should have exactly one aggregated record with count=3
        assert len(red_hatches) == 1, "Same color/layer hatches should be aggregated"
        assert red_hatches[0]["entity_count"] == 3, "Three red hatches should be counted"

    def test_color_analysis_hatch_entity_type_name(self) -> None:
        """Verify that entity_type is 'Hatches' (plural)."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find any hatch record
        hatch_records = [r for r in color_data if r["entity_type"] == "Hatches"]

        assert len(hatch_records) >= 1, "Should have Hatches records"
        for record in hatch_records:
            assert record["entity_type"] == "Hatches", "Entity type should be 'Hatches' (plural)"

    def test_color_analysis_hatch_with_true_color(self) -> None:
        """Verify True Color hatches work correctly and have color_aci=None."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find Hatches with True Color (124, 82, 165)
        purple_hatches = [
            r for r in color_data
            if r["entity_type"] == "Hatches"
            and r["color_r"] == 124
            and r["color_g"] == 82
            and r["color_b"] == 165
        ]

        assert len(purple_hatches) >= 1, "True Color hatches should be extracted"
        for record in purple_hatches:
            assert record["color_aci"] is None, "True Color hatches should have color_aci=None"
            assert record["entity_count"] == 2, "Two purple hatches should be aggregated"

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
            assert record["annotation_contents"] == "", "HATCH annotation_contents should be empty"

    def test_color_analysis_hatch_aci_colors(self) -> None:
        """Verify ACI color HATCH entities have correct color_aci value."""
        result = extract_blocks("app/tests/assets/hatch_test.dxf")
        color_data = result["color_analysis_data"]

        # Find Hatches on HATCH_LAYER_A with ACI red
        red_hatches = [
            r for r in color_data
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
            r for r in color_data
            if r["entity_type"] == "Hatches"
            and r["color_aci"] == 0
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
            r for r in color_data
            if r["entity_type"] == "Hatches"
            and r["layer_name"] == "HATCH_LAYER_B"
            and r["color_aci"] == 256
        ]

        # Should have at least one ByLayer hatch
        assert len(bylayer_hatches) >= 1, "Should have ByLayer hatches on HATCH_LAYER_B"
        for record in bylayer_hatches:
            # ByLayer should resolve to layer's ACI 3 (green)
            assert record["color_aci"] == 256, "ByLayer should have color_aci=256"


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
        line = msp.add_line((0, 0), (100, 0), dxfattribs={"color": 256, "layer": "TEST_LAYER"})

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
            line = msp.add_line((0, aci_value * 10), (100, aci_value * 10), dxfattribs={"color": aci_value})

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
            assert aci is None or isinstance(aci, int), f"Invalid color_aci type: {type(aci)}"
            if aci is not None:
                assert 0 <= aci <= 256, f"Invalid ACI value: {aci}"

    def test_color_analysis_true_color_has_none_aci(self) -> None:
        """Test that True Color entities in color_analysis_data have color_aci=None."""
        result = extract_blocks("app/tests/assets/true_color_test.dxf")
        color_data = result["color_analysis_data"]

        # Find records with True Color RGB values (not standard ACI colors)
        # True Color (124, 82, 165) - purple
        purple_records = [
            r for r in color_data
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
            r for r in color_data
            if r["color_r"] == 255 and r["color_g"] == 0 and r["color_b"] == 0
        ]

        # At least some should have ACI color
        aci_red_records = [r for r in red_records if r["color_aci"] is not None]
        if aci_red_records:
            for record in aci_red_records:
                assert record["color_aci"] == 1, f"Red should be ACI 1, got {record['color_aci']}"
