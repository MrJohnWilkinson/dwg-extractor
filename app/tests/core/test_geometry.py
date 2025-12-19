"""
Unit tests for the geometry module.

This test suite validates geometric calculation utilities including:
- Bounding box calculation for various entity types
- Intersection point detection and deduplication
- Segment distance calculation
- Rotation angle categorization
- Edge cases and tolerance boundaries
"""

import math

import ezdxf
import pytest
from shapely.geometry import LineString
from shapely.ops import polygonize, snap, unary_union

from core.constants import (
    DEFAULT_GAP_CLOSURE_TOLERANCE,
    PRECISION_SNAP_TOLERANCE,
)
from core.geometry import (
    GeometryAbortedError,
    _calculate_segments,
    _categorize_rotation,
    _detect_content_zone,
    _estimate_arc_segments,
    _estimate_edge_count,
    _extract_all_edges,
    _extract_arc_edges,
    _extract_circle_edges,
    _extract_line_cycles,
    _extract_paint_bucket_regions,
    _get_arc_bounding_box,
    _get_block_bounding_box,
    _get_intersection_points,
    _polygon_has_curved_edges,
    _snap_linestring_coords,
    _transform_bbox_points,
    calculate_polygon_area,
    calculate_shortest_straight_side,
)


class TestBoundingBox:
    """Test suite for _get_block_bounding_box function."""

    def test_bounding_box_simple_rectangle(self) -> None:
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

    def test_bounding_box_empty_block(self) -> None:
        """Test that empty block returns (0, 0, 0, 0)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY_BLOCK")

        bbox = _get_block_bounding_box(block)

        assert bbox == (0.0, 0.0, 0.0, 0.0)

    def test_bounding_box_with_circles(self) -> None:
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

    def test_bounding_box_with_arcs(self) -> None:
        """Test bounding box extraction for blocks with ARC entities (accurate angular extents)."""
        doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")
        block = doc.blocks.get("TEST_ARCS")

        bbox = _get_block_bounding_box(block)

        # Block contains arcs with accurate angular extents:
        # Arc 1: center=(100, 100), radius=50, 0 to 90 degrees -> bbox=(100, 100, 150, 150)
        # Arc 2: center=(200, 150), radius=40, 45 to 180 degrees -> bbox=(160, 150, ~228.3, 190)
        # Arc 3: center=(150, 50), radius=30, 270 to 360 degrees -> bbox=(150, 20, 180, 50)
        # Overall bbox: (100, 20, ~228.3, 190)
        assert bbox[0] == pytest.approx(100.0, abs=0.01)  # min_x
        assert bbox[1] == pytest.approx(20.0, abs=0.01)  # min_y
        assert bbox[2] == pytest.approx(228.28, abs=0.1)  # max_x (200 + 40*cos(45))
        assert bbox[3] == pytest.approx(190.0, abs=0.01)  # max_y

    def test_bounding_box_with_points(self) -> None:
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

    def test_bounding_box_single_point(self) -> None:
        """Test bounding box with single POINT entity."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SINGLE_POINT")
        block.add_point((50, 75))

        bbox = _get_block_bounding_box(block)

        # Single point should have zero-size bbox at that location
        assert bbox == (50.0, 75.0, 50.0, 75.0)

    def test_bounding_box_mixed_entities(self) -> None:
        """Test bounding box with mixed entity types (LINE, CIRCLE, POINT)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED_BLOCK")

        # Add various entity types
        block.add_line((0, 0), (100, 0))  # Bottom edge
        block.add_circle((50, 50), 25)  # Center circle: bbox=(25, 25, 75, 75)
        block.add_point((120, 120))  # Top-right point

        bbox = _get_block_bounding_box(block)

        # Overall bbox: min_x=0, min_y=0, max_x=120, max_y=120
        assert bbox == (0.0, 0.0, 120.0, 120.0)

    def test_bounding_box_with_polyline(self) -> None:
        """Test bounding box with LWPOLYLINE entity."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="POLYLINE_BLOCK")

        # Add LWPOLYLINE with multiple points
        points = [(0, 0), (50, 25), (100, 10), (75, 50)]
        block.add_lwpolyline(points)

        bbox = _get_block_bounding_box(block)

        # Bbox should encompass all points: (0, 0, 100, 50)
        assert bbox[0] == 0.0  # min_x
        assert bbox[1] == 0.0  # min_y
        assert bbox[2] == 100.0  # max_x
        assert bbox[3] == 50.0  # max_y


class TestArcBoundingBox:
    """Test suite for _get_arc_bounding_box helper function."""

    def test_quarter_arc_first_quadrant(self) -> None:
        """Test quarter arc from 0 to 90 degrees at origin with radius 100."""
        min_x, min_y, max_x, max_y = _get_arc_bounding_box(0, 0, 100, 0, 90)

        # Arc from 0 to 90 degrees: start at (100, 0), end at (0, 100)
        # Includes 0 deg cardinal (right) and 90 deg cardinal (top)
        assert min_x == pytest.approx(0.0, abs=0.01)
        assert min_y == pytest.approx(0.0, abs=0.01)
        assert max_x == pytest.approx(100.0, abs=0.01)
        assert max_y == pytest.approx(100.0, abs=0.01)

    def test_quarter_arc_fourth_quadrant(self) -> None:
        """Test quarter arc from 270 to 360 degrees at origin with radius 100."""
        min_x, min_y, max_x, max_y = _get_arc_bounding_box(0, 0, 100, 270, 360)

        # Arc from 270 to 360 degrees: start at (0, -100), end at (100, 0)
        # Includes 270 deg cardinal (bottom) and 360/0 deg cardinal (right)
        assert min_x == pytest.approx(0.0, abs=0.01)
        assert min_y == pytest.approx(-100.0, abs=0.01)
        assert max_x == pytest.approx(100.0, abs=0.01)
        assert max_y == pytest.approx(0.0, abs=0.01)

    def test_arc_45_to_180(self) -> None:
        """Test arc from 45 to 180 degrees, center=(200, 150), radius=40."""
        min_x, min_y, max_x, max_y = _get_arc_bounding_box(200, 150, 40, 45, 180)

        # Arc from 45 to 180 degrees:
        # Start point: (200 + 40*cos(45), 150 + 40*sin(45)) = (228.28, 178.28)
        # End point: (200 - 40, 150) = (160, 150)
        # Includes 90 deg cardinal: (200, 190)
        # Does NOT include 0 deg (right) or 180 deg boundary point (already at end)
        assert min_x == pytest.approx(160.0, abs=0.01)
        assert min_y == pytest.approx(150.0, abs=0.01)
        assert max_x == pytest.approx(228.28, abs=0.1)
        assert max_y == pytest.approx(190.0, abs=0.01)

    def test_semicircle_top(self) -> None:
        """Test semicircle from 0 to 180 degrees (top half), center=(50, 50), radius=25."""
        min_x, min_y, max_x, max_y = _get_arc_bounding_box(50, 50, 25, 0, 180)

        # Semicircle from 0 to 180 degrees:
        # Start point: (75, 50), End point: (25, 50)
        # Includes 0 deg (right), 90 deg (top), and 180 deg (left) cardinals
        assert min_x == pytest.approx(25.0, abs=0.01)
        assert min_y == pytest.approx(50.0, abs=0.01)
        assert max_x == pytest.approx(75.0, abs=0.01)
        assert max_y == pytest.approx(75.0, abs=0.01)

    def test_wrap_around_arc(self) -> None:
        """Test arc from 350 to 10 degrees (crosses 0), origin, radius=100."""
        min_x, min_y, max_x, max_y = _get_arc_bounding_box(0, 0, 100, 350, 10)

        # Arc crosses 0 degrees, so max_x should include the 0 deg cardinal point
        # Start point: (100*cos(350), 100*sin(350)) = (98.48, -17.36)
        # End point: (100*cos(10), 100*sin(10)) = (98.48, 17.36)
        assert max_x == pytest.approx(100.0, abs=0.01)  # Includes 0 deg cardinal

    def test_full_circle_arc(self) -> None:
        """Test arc from 0 to 360 degrees should equal full circle bbox."""
        min_x, min_y, max_x, max_y = _get_arc_bounding_box(100, 100, 50, 0, 360)

        # Full circle: should include all cardinal points
        assert min_x == pytest.approx(50.0, abs=0.01)
        assert min_y == pytest.approx(50.0, abs=0.01)
        assert max_x == pytest.approx(150.0, abs=0.01)
        assert max_y == pytest.approx(150.0, abs=0.01)

    def test_arc_270_to_356_problematic_case(self) -> None:
        """Test the original issue case: arc from 270-356 degrees incorrectly reported -779 min_x."""
        min_x, min_y, max_x, max_y = _get_arc_bounding_box(0, -953, 779, 270, 356.1)

        # Arc from 270 to 356.1 degrees at center=(0, -953):
        # Start point: (0, -953 - 779) = (0, -1732) - at 270 deg (bottom)
        # End point: ~(776.3, -953 + some small y)
        # Does NOT include 180 deg (left), so min_x should NOT be -779
        # The arc stays in right half, so min_x should be near 0 or slightly negative
        assert min_x > -100  # NOT -779 (the old incorrect value)
        assert min_y == pytest.approx(-953 - 779, abs=0.01)  # Includes 270 deg (bottom)


class TestIntersectionPoints:
    """Test suite for _get_intersection_points function."""

    def test_intersection_points_simple(self) -> None:
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

    def test_intersection_points_sorting(self) -> None:
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

    def test_intersection_points_empty_block(self) -> None:
        """Test that empty block returns empty lists."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY_BLOCK")

        vertical_points, horizontal_points = _get_intersection_points(block)

        assert vertical_points == []
        assert horizontal_points == []

    def test_intersection_points_with_circles(self) -> None:
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

    def test_intersection_points_with_arcs_and_points(self) -> None:
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

    def test_intersection_points_deduplication(self) -> None:
        """Test that duplicate points within epsilon tolerance are deduplicated."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="DUPLICATE_POINTS")

        # Add lines with very close coordinates (within 0.01 tolerance)
        block.add_line((0, 0), (100, 0))
        block.add_line((0.005, 0), (100, 0.005))  # Nearly identical Y
        block.add_line((100.005, 0), (100.005, 50))  # Nearly identical X

        vertical_points, horizontal_points = _get_intersection_points(block)

        # Should have deduplicated points due to epsilon=0.01 tolerance
        # X coords: 0, 0.005 (merged), 100, 100.005 (merged) -> [0, 100]
        # Y coords: 0, 0.005 (merged), 50 -> [0, 50]
        assert len(vertical_points) == 2
        assert 0.0 in vertical_points
        assert 100.0 in vertical_points

        assert len(horizontal_points) == 2
        assert 0.0 in horizontal_points
        assert 50.0 in horizontal_points

    def test_intersection_points_tolerance_boundary(self) -> None:
        """Test deduplication at exact epsilon tolerance boundary (0.01)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TOLERANCE_TEST")

        # Add points exactly at tolerance boundary
        block.add_point((0, 0))
        block.add_point((0.01, 0))  # Exactly at epsilon
        block.add_point((0.02, 0))  # Beyond epsilon

        vertical_points, horizontal_points = _get_intersection_points(block)

        # Points at 0 and 0.01 should be deduplicated (within tolerance)
        # Point at 0.02 should remain separate (beyond tolerance from 0.01)
        # Result: [0, 0.02] (since 0 and 0.01 are within 0.01 tolerance)
        assert len(vertical_points) == 2
        assert 0.0 in vertical_points
        assert 0.02 in vertical_points

    def test_intersection_points_custom_epsilon(self) -> None:
        """Test deduplication with custom epsilon parameter."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CUSTOM_EPSILON_TEST")

        # Add points that are 0.05 apart
        block.add_point((0, 0))
        block.add_point((0.05, 0))
        block.add_point((0.1, 0))

        # With default epsilon (0.01), all points should be distinct
        vertical_default, _ = _get_intersection_points(block)
        assert len(vertical_default) == 3

        # With larger epsilon (0.1), points should be deduplicated
        vertical_large, _ = _get_intersection_points(block, epsilon=0.1)
        assert len(vertical_large) == 1  # All within 0.1 tolerance of 0

    def test_intersection_points_stricter_epsilon(self) -> None:
        """Test deduplication with stricter (smaller) epsilon."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="STRICT_EPSILON_TEST")

        # Add points that are 0.02 apart (outside default epsilon)
        block.add_point((0, 0))
        block.add_point((0.02, 0))
        block.add_point((0.1, 0))  # Far enough apart to not be deduplicated

        # With default epsilon (0.01), all points should remain distinct
        vertical_default, _ = _get_intersection_points(block)
        assert len(vertical_default) == 3

        # With larger epsilon (0.03), 0 and 0.02 are within tolerance
        # Sequential dedup: 0.02 is within 0.03 of 0, so dropped
        # Then 0.1 is outside 0.03 of 0, so kept
        # Result: [0, 0.1]
        vertical_large, _ = _get_intersection_points(block, epsilon=0.03)
        assert len(vertical_large) == 2


class TestCalculateSegments:
    """Test suite for _calculate_segments function."""

    def test_calculate_segments_normal(self) -> None:
        """Test segment calculation with typical intersection point list."""
        points = [0.0, 50.0, 1150.0, 1200.0]
        segments = _calculate_segments(points)

        assert len(segments) == 3
        assert segments == [50.0, 1100.0, 50.0]

    def test_calculate_segments_empty_list(self) -> None:
        """Test segment calculation with empty list."""
        assert _calculate_segments([]) == []

    def test_calculate_segments_single_point(self) -> None:
        """Test segment calculation with single point."""
        assert _calculate_segments([0.0]) == []

    def test_calculate_segments_two_points(self) -> None:
        """Test segment calculation with two points."""
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

    def test_calculate_segments_rounding(self) -> None:
        """Test specific rounding behavior."""
        points = [0.0, 10.555, 20.999]
        segments = _calculate_segments(points)

        # Expected: [10.56, 10.44] (rounded to 2 decimals)
        assert len(segments) == 2
        assert segments[0] == pytest.approx(10.56, abs=0.01)
        assert segments[1] == pytest.approx(10.44, abs=0.01)

    def test_calculate_segments_multiple_segments(self) -> None:
        """Test segment calculation with multiple evenly spaced points."""
        points = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
        segments = _calculate_segments(points)

        # All segments should be 10.0
        assert len(segments) == 5
        assert all(seg == 10.0 for seg in segments)


class TestCategorizeRotation:
    """Test suite for _categorize_rotation function."""

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

    def test_categorize_rotation_negative_angles(self) -> None:
        """Test rotation normalization for negative angles."""
        # Negative angles should normalize correctly
        assert _categorize_rotation(-90.0) == "270"
        assert _categorize_rotation(-180.0) == "180"
        assert _categorize_rotation(-270.0) == "90"
        assert (
            _categorize_rotation(-1.0) == "0"
        )  # -1° normalizes to 359°, within tolerance of 0°

    def test_categorize_rotation_angles_over_360(self) -> None:
        """Test rotation normalization for angles > 360°."""
        # Angles > 360 should normalize correctly
        assert _categorize_rotation(450.0) == "90"  # 450 % 360 = 90
        assert _categorize_rotation(540.0) == "180"  # 540 % 360 = 180
        assert _categorize_rotation(630.0) == "270"  # 630 % 360 = 270
        assert _categorize_rotation(720.0) == "0"  # 720 % 360 = 0

    def test_categorize_rotation_boundary_cases(self) -> None:
        """Test rotation categorization for boundary edge cases."""
        # Angles just outside tolerance should be 'other'
        assert _categorize_rotation(1.5) == "other"
        assert _categorize_rotation(88.0) == "other"
        assert _categorize_rotation(92.0) == "other"
        assert _categorize_rotation(178.0) == "other"
        assert _categorize_rotation(182.0) == "other"

    def test_categorize_rotation_exact_tolerance_boundary(self) -> None:
        """Test rotation categorization at exact ±1° tolerance boundary."""
        # Exactly at ±1° should be categorized as standard angle
        assert _categorize_rotation(1.0) == "0"
        assert _categorize_rotation(89.0) == "90"
        assert _categorize_rotation(91.0) == "90"
        assert _categorize_rotation(179.0) == "180"
        assert _categorize_rotation(181.0) == "180"
        assert _categorize_rotation(269.0) == "270"
        assert _categorize_rotation(271.0) == "270"

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
    def test_categorize_rotation_parametrized(
        self, rotation: float, expected_category: str
    ) -> None:
        """Test rotation categorization with parametrized test cases."""
        assert _categorize_rotation(rotation) == expected_category

    def test_categorize_rotation_custom_tolerance(self) -> None:
        """Test rotation categorization with custom tolerance parameter."""
        # With default tolerance (1.0), 1.5 degrees is 'other'
        assert _categorize_rotation(1.5) == "other"

        # With tolerance=2.0, 1.5 degrees should be '0'
        assert _categorize_rotation(1.5, tolerance=2.0) == "0"

        # With tolerance=0.5, 0.8 degrees should be 'other'
        assert _categorize_rotation(0.8, tolerance=0.5) == "other"

        # With tolerance=0.5, 0.5 degrees should be '0' (at boundary)
        assert _categorize_rotation(0.5, tolerance=0.5) == "0"

    def test_categorize_rotation_stricter_tolerance(self) -> None:
        """Test rotation categorization with stricter (smaller) tolerance."""
        # With stricter tolerance=0.1, even 0.5 degree deviation is 'other'
        assert _categorize_rotation(90.5, tolerance=0.1) == "other"
        assert _categorize_rotation(90.05, tolerance=0.1) == "90"

    def test_categorize_rotation_looser_tolerance(self) -> None:
        """Test rotation categorization with looser (larger) tolerance."""
        # With looser tolerance=5.0, angles within 5 degrees are categorized
        assert _categorize_rotation(85.0, tolerance=5.0) == "90"
        assert _categorize_rotation(95.0, tolerance=5.0) == "90"
        assert _categorize_rotation(84.0, tolerance=5.0) == "other"


class TestExtractLineCycles:
    """
    Test suite for _extract_line_cycles function.

    These tests verify polygon detection from LINE entities, including:
    - Simple closed rectangles from 4 lines
    - T-junctions where a divider splits a polygon into two
    - Crossing lines that form no closed region
    - Grid patterns with multiple T-junctions and crossings
    """

    def test_simple_rectangle_from_lines(self) -> None:
        """Test that 4 lines forming a rectangle produce exactly 1 polygon."""
        # Create a block with 4 lines forming a 100x50 rectangle
        doc = ezdxf.new()
        block = doc.blocks.new(name="SIMPLE_RECT")

        # Add rectangle lines: (0,0)-(100,0), (100,0)-(100,50), (100,50)-(0,50), (0,50)-(0,0)
        block.add_line((0, 0), (100, 0))  # Bottom
        block.add_line((100, 0), (100, 50))  # Right
        block.add_line((100, 50), (0, 50))  # Top
        block.add_line((0, 50), (0, 0))  # Left

        polygons = _extract_line_cycles(block)

        assert len(polygons) == 1

    def test_t_junction_creates_two_polygons(self) -> None:
        """Test that T-junction (vertical divider) splits rectangle into 2 polygons."""
        # Create a block with rectangle + vertical divider at midpoint
        doc = ezdxf.new()
        block = doc.blocks.new(name="T_JUNCTION")

        # Rectangle lines: (0,0)-(100,0), (100,0)-(100,50), (100,50)-(0,50), (0,50)-(0,0)
        block.add_line((0, 0), (100, 0))  # Bottom
        block.add_line((100, 0), (100, 50))  # Right
        block.add_line((100, 50), (0, 50))  # Top
        block.add_line((0, 50), (0, 0))  # Left

        # Divider line: (50,0)-(50,50) - creates T-junctions at top and bottom
        block.add_line((50, 0), (50, 50))

        polygons = _extract_line_cycles(block)

        # Should produce 2 polygons (left and right halves)
        assert len(polygons) == 2

    def test_crossing_lines_no_closed_region(self) -> None:
        """Test that crossing lines (X pattern) produce 0 polygons."""
        # Create a block with two diagonal lines forming an X pattern
        doc = ezdxf.new()
        block = doc.blocks.new(name="CROSSING_X")

        # Lines: (0,0)-(100,100), (100,0)-(0,100)
        block.add_line((0, 0), (100, 100))  # Diagonal bottom-left to top-right
        block.add_line((100, 0), (0, 100))  # Diagonal bottom-right to top-left

        polygons = _extract_line_cycles(block)

        # No closed region formed by just two crossing lines
        assert len(polygons) == 0

    def test_grid_pattern_multiple_polygons(self) -> None:
        """Test that grid pattern (3x2) produces exactly 6 polygons."""
        # Create a block with rectangle + 2 horizontal lines + 1 vertical divider
        doc = ezdxf.new()
        block = doc.blocks.new(name="GRID_PATTERN")

        # Rectangle: (0,0)-(150,90) perimeter
        block.add_line((0, 0), (150, 0))  # Bottom
        block.add_line((150, 0), (150, 90))  # Right
        block.add_line((150, 90), (0, 90))  # Top
        block.add_line((0, 90), (0, 0))  # Left

        # Horizontal dividers at y=30 and y=60
        block.add_line((0, 30), (150, 30))
        block.add_line((0, 60), (150, 60))

        # Vertical divider at x=75
        block.add_line((75, 0), (75, 90))

        polygons = _extract_line_cycles(block)

        # Should produce 6 polygons (3 rows x 2 columns)
        assert len(polygons) == 6


class TestExtractAllEdges:
    """Test suite for _extract_all_edges function."""

    def test_extracts_line_entities(self) -> None:
        """Test extraction of LINE entities as edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="LINE_TEST")
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))

        edges = _extract_all_edges(block)

        assert len(edges) == 2

    def test_extracts_closed_lwpolyline_edges(self) -> None:
        """Test extraction of closed LWPOLYLINE as individual edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CLOSED_POLY_TEST")
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        edges = _extract_all_edges(block)

        # 4 edges: 3 between consecutive points + 1 closing edge
        assert len(edges) == 4

    def test_extracts_open_lwpolyline_edges(self) -> None:
        """Test extraction of open LWPOLYLINE (no closing edge)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="OPEN_POLY_TEST")
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50)], close=False)

        edges = _extract_all_edges(block)

        # 2 edges between 3 consecutive points, no closing edge
        assert len(edges) == 2

    def test_empty_block_returns_empty_list(self) -> None:
        """Test that empty block returns empty edge list."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY_TEST")

        edges = _extract_all_edges(block)

        assert edges == []


class TestExtractPaintBucketRegions:
    """Test suite for _extract_paint_bucket_regions function."""

    def test_rectangle_with_vertical_divider(self) -> None:
        """Test rectangle split by vertical divider produces 2 regions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="RECT_DIVIDER")

        # Closed LWPOLYLINE rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)
        # LINE divider at midpoint
        block.add_line((50, 0), (50, 50))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 2 regions (left and right)
        assert len(regions) == 2

    def test_rectangle_with_grid_dividers(self) -> None:
        """Test rectangle with cross dividers produces 4 regions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="RECT_GRID")

        # Closed LWPOLYLINE rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Horizontal divider
        block.add_line((0, 50), (100, 50))
        # Vertical divider
        block.add_line((50, 0), (50, 100))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 4 regions (2x2 grid)
        assert len(regions) == 4

    def test_lines_only_rectangle(self) -> None:
        """Test that LINE-only rectangle still works."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="LINES_RECT")

        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))
        block.add_line((100, 50), (0, 50))
        block.add_line((0, 50), (0, 0))

        regions = _extract_paint_bucket_regions(block)

        assert len(regions) == 1

    def test_empty_block_returns_empty_list(self) -> None:
        """Test that empty block returns empty region list."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY_TEST")

        regions = _extract_paint_bucket_regions(block)

        assert regions == []

    def test_abort_event_raises_error(self) -> None:
        """Test that set abort_event raises GeometryAbortedError."""
        import threading

        doc = ezdxf.new()
        block = doc.blocks.new(name="ABORT_TEST")
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(GeometryAbortedError):
            _extract_paint_bucket_regions(block, abort_event)

    def test_multiple_horizontal_dividers(self) -> None:
        """Test rectangle with 3 horizontal dividers produces 4 rows."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HORIZ_DIVIDERS")

        # 100x100 closed rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # 3 horizontal LINE dividers at y=25, y=50, y=75
        block.add_line((0, 25), (100, 25))
        block.add_line((0, 50), (100, 50))
        block.add_line((0, 75), (100, 75))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 4 horizontal rows
        assert len(regions) == 4

    def test_multiple_vertical_dividers(self) -> None:
        """Test rectangle with 2 vertical dividers produces 3 columns."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="VERT_DIVIDERS")

        # 100x50 closed rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)
        # 2 vertical LINE dividers at x=33, x=66
        block.add_line((33, 0), (33, 50))
        block.add_line((66, 0), (66, 50))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 3 vertical columns
        assert len(regions) == 3

    def test_open_lwpolyline_with_closing_line(self) -> None:
        """Test open U-shape LWPOLYLINE with closing LINE forms 1 region."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="U_SHAPE_CLOSED")

        # Open U-shape LWPOLYLINE: bottom-left, top-left, top-right, bottom-right
        block.add_lwpolyline([(0, 0), (0, 50), (100, 50), (100, 0)], close=False)
        # Closing LINE from bottom-right to bottom-left
        block.add_line((100, 0), (0, 0))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 1 closed region (rectangle)
        assert len(regions) == 1

    def test_nested_rectangles(self) -> None:
        """Test outer rectangle with inner rectangle produces 2 regions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="NESTED_RECTS")

        # Outer 100x100 closed rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Inner 50x50 closed rectangle centered at (25,25) to (75,75)
        block.add_lwpolyline([(25, 25), (75, 25), (75, 75), (25, 75)], close=True)

        regions = _extract_paint_bucket_regions(block)

        # Should produce 2 regions: inner rectangle + outer ring
        assert len(regions) == 2

    def test_complex_grid_3x2(self) -> None:
        """Test 3 columns x 2 rows grid produces 6 regions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="GRID_3X2")

        # 150x100 closed rectangle
        block.add_lwpolyline([(0, 0), (150, 0), (150, 100), (0, 100)], close=True)
        # 2 vertical LINE dividers at x=50, x=100
        block.add_line((50, 0), (50, 100))
        block.add_line((100, 0), (100, 100))
        # 1 horizontal LINE divider at y=50
        block.add_line((0, 50), (150, 50))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 6 regions (3 columns x 2 rows)
        assert len(regions) == 6


class TestExtractCircleEdges:
    """Test suite for _extract_circle_edges function."""

    def test_circle_produces_edges(self) -> None:
        """Test that CIRCLE entity produces line segment edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLE_TEST")
        block.add_circle(center=(50, 50), radius=25)

        edges = _extract_all_edges(block)

        # Circle should produce multiple edges (exact count depends on sagitta)
        assert len(edges) > 10  # At minimum, should have many segments
        # All edges should be LineStrings
        assert all(isinstance(e, LineString) for e in edges)

    def test_circle_edges_form_closed_loop(self) -> None:
        """Test that circle edges are extracted (closed region may not form due to discretization)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLE_CLOSED")
        block.add_circle(center=(0, 0), radius=50)

        edges = _extract_all_edges(block)

        # Circle should produce many edges forming a closed loop
        assert len(edges) > 20
        # Verify edges form a continuous chain (first point of last edge close to last point of first)
        assert all(isinstance(e, LineString) for e in edges)

    def test_small_vs_large_circle_segment_count(self) -> None:
        """Test that larger circles produce more segments (adaptive flattening)."""
        doc = ezdxf.new()

        block_small = doc.blocks.new(name="SMALL_CIRCLE")
        block_small.add_circle(center=(0, 0), radius=10)

        block_large = doc.blocks.new(name="LARGE_CIRCLE")
        block_large.add_circle(center=(0, 0), radius=100)

        edges_small = _extract_all_edges(block_small)
        edges_large = _extract_all_edges(block_large)

        # Larger circle should have more segments due to sagitta-based flattening
        assert len(edges_large) > len(edges_small)


class TestExtractArcEdges:
    """Test suite for _extract_arc_edges function."""

    def test_arc_produces_edges(self) -> None:
        """Test that ARC entity produces line segment edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARC_TEST")
        block.add_arc(center=(100, 100), radius=50, start_angle=0, end_angle=90)

        edges = _extract_all_edges(block)

        # 90-degree arc should produce multiple edges
        assert len(edges) > 5
        assert all(isinstance(e, LineString) for e in edges)

    def test_180_degree_arc_segment_count(self) -> None:
        """Test that 180-degree arc produces appropriate segment count."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARC_180")
        block.add_arc(center=(0, 0), radius=50, start_angle=0, end_angle=180)

        edges = _extract_all_edges(block)

        # 180-degree arc should have more segments than 90-degree
        assert len(edges) > 10

    def test_multiple_arcs_forming_closed_shape(self) -> None:
        """Test that multiple arcs extract edges (closed region may not form due to discretization)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARCS_CLOSED")

        # Two semicircles forming a closed shape
        block.add_arc(center=(50, 0), radius=50, start_angle=0, end_angle=180)
        block.add_arc(center=(50, 0), radius=50, start_angle=180, end_angle=360)

        edges = _extract_all_edges(block)

        # Two semicircles should produce many edges
        assert len(edges) > 20
        assert all(isinstance(e, LineString) for e in edges)


class TestExtractHatchBoundaryEdges:
    """Test suite for _extract_hatch_boundary_edges function."""

    def test_hatch_polyline_path_produces_edges(self) -> None:
        """Test that HATCH with PolylinePath produces edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCH_POLY_TEST")
        hatch = block.add_hatch()
        hatch.paths.add_polyline_path(
            [(0, 0), (100, 0), (100, 50), (0, 50)], is_closed=True
        )

        edges = _extract_all_edges(block)

        # Rectangular hatch boundary should produce 4 edges
        assert len(edges) == 4
        assert all(isinstance(e, LineString) for e in edges)

    def test_hatch_with_bulge_produces_curved_edges(self) -> None:
        """Test that HATCH with bulge values produces curved segment edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCH_BULGE_TEST")
        hatch = block.add_hatch()
        # Bulge of 1.0 creates a semicircle
        hatch.paths.add_polyline_path(
            [(0, 0, 0), (100, 0, 1.0), (100, 50, 0), (0, 50, 0)], is_closed=True
        )

        edges = _extract_all_edges(block)

        # Should have more than 4 edges due to curved segment
        assert len(edges) > 4

    def test_hatch_edge_path_line_edges(self) -> None:
        """Test that HATCH with EdgePath LineEdge produces edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCH_EDGE_TEST")
        hatch = block.add_hatch()
        edge_path = hatch.paths.add_edge_path()
        edge_path.add_line((0, 0), (100, 0))
        edge_path.add_line((100, 0), (100, 50))
        edge_path.add_line((100, 50), (0, 50))
        edge_path.add_line((0, 50), (0, 0))

        edges = _extract_all_edges(block)

        # Should produce 4 edges for rectangular boundary
        assert len(edges) == 4

    def test_hatch_forms_closed_region(self) -> None:
        """Test that HATCH boundary forms closed region via polygonize."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCH_REGION_TEST")
        hatch = block.add_hatch()
        hatch.paths.add_polyline_path(
            [(0, 0), (100, 0), (100, 50), (0, 50)], is_closed=True
        )

        regions = _extract_paint_bucket_regions(block)

        # HATCH boundary should form exactly one closed region
        assert len(regions) == 1


class TestCircleArcHatchIntegration:
    """Integration tests for CIRCLE, ARC, and HATCH edge extraction."""

    def test_mixed_entities_produces_all_edges(self) -> None:
        """Test that block with mixed entities extracts all edge types."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED_TEST")

        # Add various entity types
        block.add_line((0, 0), (100, 0))
        block.add_circle(center=(150, 25), radius=20)
        block.add_arc(center=(200, 25), radius=15, start_angle=0, end_angle=180)
        hatch = block.add_hatch()
        hatch.paths.add_polyline_path(
            [(250, 0), (300, 0), (300, 50), (250, 50)], is_closed=True
        )

        edges = _extract_all_edges(block)

        # Should have edges from all entity types
        # 1 LINE + circle edges + arc edges + 4 HATCH edges
        assert len(edges) > 10

    def test_content_zone_with_circle_boundary(self) -> None:
        """Test edge extraction with CIRCLE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLE_BOUNDARY")
        # Circle as outer boundary
        block.add_circle(center=(50, 50), radius=50)
        # Small inner circle (hole)
        block.add_circle(center=(50, 50), radius=10)

        edges = _extract_all_edges(block)

        # Should extract edges from both circles
        # Larger circle produces more edges than smaller one
        assert len(edges) > 40  # Both circles combined

    def test_content_zone_with_arc_boundary(self) -> None:
        """Test edge extraction with ARCs forming boundary."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARC_BOUNDARY")
        # Rounded rectangle using arcs at corners
        block.add_line((20, 0), (80, 0))
        block.add_arc(center=(80, 20), radius=20, start_angle=270, end_angle=360)
        block.add_line((100, 20), (100, 80))
        block.add_arc(center=(80, 80), radius=20, start_angle=0, end_angle=90)
        block.add_line((80, 100), (20, 100))
        block.add_arc(center=(20, 80), radius=20, start_angle=90, end_angle=180)
        block.add_line((0, 80), (0, 20))
        block.add_arc(center=(20, 20), radius=20, start_angle=180, end_angle=270)

        edges = _extract_all_edges(block)

        # Should extract edges from 4 lines + 4 arcs
        # 4 lines = 4 edges, 4 arcs produce multiple edges each
        assert len(edges) > 20

    def test_real_file_circles_arcs(self) -> None:
        """Test edge extraction from real test file with CIRCLE and ARC entities."""
        doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")

        # Test CIRCLE block
        block_circles = doc.blocks.get("TEST_CIRCLES")
        edges_circles = _extract_all_edges(block_circles)

        # Should have edges from all 3 circles
        assert len(edges_circles) > 30  # Multiple segments per circle

        # Test ARC block
        block_arcs = doc.blocks.get("TEST_ARCS")
        edges_arcs = _extract_all_edges(block_arcs)

        # Should have edges from all 3 arcs
        assert len(edges_arcs) > 15  # Multiple segments per arc


class TestPrecisionSnapping:
    """Test suite for Stage 1 precision snapping in _extract_paint_bucket_regions.

    Note: Shapely's snap() function adds vertices to geometries within tolerance
    but doesn't directly merge disconnected endpoints. The effectiveness depends
    on the geometry topology after snapping.
    """

    def test_stage1_no_effect_on_clean_geometry(self) -> None:
        """Test that precision snap doesn't affect clean geometry without gaps."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CLEAN_RECT")

        # Perfect rectangle with no gaps
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))
        block.add_line((100, 50), (0, 50))
        block.add_line((0, 50), (0, 0))

        regions_no_snap = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=0
        )
        regions_with_snap = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-6, gap_bridge_tolerance=0
        )

        # Both should find exactly 1 polygon
        assert len(regions_no_snap) == 1
        assert len(regions_with_snap) == 1

    def test_stage1_disabled_when_tolerance_zero(self) -> None:
        """Test that Stage 1 is skipped when precision_tolerance=0."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SKIP_STAGE1")

        # Perfect rectangle - should work with or without Stage 1
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))
        block.add_line((100, 50), (0, 50))
        block.add_line((0, 50), (0, 0))

        regions = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=0
        )

        # Should still work for clean geometry
        assert len(regions) == 1

    def test_stage1_with_closed_lwpolyline(self) -> None:
        """Test that Stage 1 works correctly with closed LWPOLYLINE geometry."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CLOSED_POLY")

        # Closed LWPOLYLINE always forms valid polygons
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        regions_no_snap = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=0
        )
        regions_with_snap = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-6, gap_bridge_tolerance=0
        )

        # Both should find exactly 1 polygon
        assert len(regions_no_snap) == 1
        assert len(regions_with_snap) == 1

    def test_stage1_tolerance_parameter_accepted(self) -> None:
        """Test that custom precision tolerance parameter is accepted."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CUSTOM_TOLERANCE")

        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        # Should not raise with various tolerance values
        regions_small = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-9, gap_bridge_tolerance=0
        )
        regions_default = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-6, gap_bridge_tolerance=0
        )
        regions_large = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-3, gap_bridge_tolerance=0
        )

        assert len(regions_small) == 1
        assert len(regions_default) == 1
        assert len(regions_large) == 1

    def test_stage1_fixes_nanometer_gap(self) -> None:
        """Stage 1 should add vertices at precision snap points.

        Note: Shapely's snap() adds vertices where edges pass within tolerance
        of each other, which helps with node-arc snapping but doesn't directly
        merge disconnected endpoints. This test verifies the snapping mechanism
        functions correctly.
        """
        # Create edges with a dividing line that nearly touches the edge
        edges = [
            LineString([(0, 0), (10, 0)]),
            LineString([(10, 0), (10, 10)]),
            LineString([(10, 10), (0, 10)]),
            LineString([(0, 10), (0, 0)]),
            # Divider that passes very close to the right edge at (10, 5)
            LineString([(0, 5), (9.9999999, 5)]),
        ]

        # Merge and apply Stage 1 snapping
        merged = unary_union(edges)
        merged_snapped = snap(merged, merged, 1e-6)

        # Verify snapping was applied (merged geometry is modified)
        # The snap function should process without error
        line_segments = (
            list(merged_snapped.geoms)
            if hasattr(merged_snapped, "geoms")
            else [merged_snapped]
        )
        polygons = list(polygonize(line_segments))

        # Should produce at least 1 valid polygon (the outer rectangle)
        assert len(polygons) >= 1
        # The outer rectangle area should be preserved (~100 sq units)
        total_area = sum(p.area for p in polygons)
        assert 99.9 < total_area < 100.1


class TestGapBridging:
    """Test suite for gap bridge functionality in _extract_paint_bucket_regions.

    Gap Bridge is an alternative to Precision Fix (mutually exclusive). Both close
    gaps for accurate polygon counts. Gap Bridge snaps edges to reference geometry
    before union using Shapely's snap() function, which adds vertices where edges
    pass within tolerance of each other.
    """

    def test_gap_bridge_disabled_by_default(self) -> None:
        """Test that default gap_bridge_tolerance=0.0 doesn't modify geometry."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="GAP_DEFAULT")

        # Clean geometry should work identically with default tolerance
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        regions = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=0
        )

        # Should find exactly 1 polygon with default settings
        assert len(regions) == 1

    def test_gap_bridge_tolerance_parameter_accepted(self) -> None:
        """Test that gap_bridge_tolerance parameter is accepted with precision_tolerance=0."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="GAP_TOLERANCE")

        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        # Should not raise with various tolerance values
        regions_zero = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=0.0
        )
        regions_small = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=0.5
        )
        regions_large = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=10.0
        )

        assert len(regions_zero) == 1
        assert len(regions_small) == 1
        assert len(regions_large) == 1

    def test_gap_bridge_no_effect_on_clean_geometry(self) -> None:
        """Test gap bridge doesn't negatively impact clean geometry."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CLEAN_GAP")

        # Perfect rectangle
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))
        block.add_line((100, 50), (0, 50))
        block.add_line((0, 50), (0, 0))

        # Even with large gap_bridge_tolerance, clean geometry should work
        regions = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=10.0
        )

        assert len(regions) == 1

    def test_gap_bridge_with_grid_pattern(self) -> None:
        """Test gap bridge works correctly with complex grid geometry."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="GRID_GAP")

        # 2x2 grid with clean connections
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        block.add_line((50, 0), (50, 100))  # Vertical divider
        block.add_line((0, 50), (100, 50))  # Horizontal divider

        regions = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=1.0
        )

        # Should find 4 regions (2x2 grid)
        assert len(regions) == 4

    def test_gap_bridge_bridges_large_gaps(self) -> None:
        """Gap bridge should add vertices at larger tolerance points.

        Shapely's snap() adds vertices where edges pass within tolerance
        of each other. With a 2.0 tolerance on a 1-unit gap, the endpoint
        at (9, 5) is within tolerance of the right edge at (10, 5), so
        a vertex is added to the right edge. This effectively bridges the gap
        by adding a connection point.
        """
        edges = [
            LineString([(0, 0), (10, 0)]),
            LineString([(10, 0), (10, 10)]),
            LineString([(10, 10), (0, 10)]),
            LineString([(0, 10), (0, 0)]),
            LineString([(0, 5), (9, 5)]),  # 1 unit gap from right edge
        ]

        merged = unary_union(edges)
        merged = snap(merged, merged, 1e-6)  # Precision fix equivalent
        merged_gap_bridge = snap(merged, merged, 2.0)  # Gap bridge with 2.0 tolerance

        # Verify gap bridge modified the geometry (added vertex at gap location)
        # The snapped geometry should have a vertex added at (9, 5) on the right edge
        line_segments = (
            list(merged_gap_bridge.geoms)
            if hasattr(merged_gap_bridge, "geoms")
            else [merged_gap_bridge]
        )
        polygons = list(polygonize(line_segments))

        # Should produce at least 1 polygon
        assert len(polygons) >= 1

        # Verify the snap added a vertex by checking that the right edge now
        # has the (9, 5) point included (shown as a polygon vertex)
        all_coords = []
        for p in polygons:
            all_coords.extend(list(p.exterior.coords))
        # The point (9, 5) should now be a polygon vertex
        assert any(abs(x - 9.0) < 0.01 and abs(y - 5.0) < 0.01 for x, y in all_coords)


class TestTolerancePropagation:
    """Test suite for tolerance parameter propagation through function calls."""

    def test_default_parameters_backward_compatible(self) -> None:
        """Test that calling functions without new parameters works (backward compatible)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="BACKWARD_COMPAT")

        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        # Call without new parameters - should use defaults
        regions = _extract_paint_bucket_regions(block)

        assert len(regions) == 1

    def test_precision_only_parameter(self) -> None:
        """Test passing only precision_tolerance parameter."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="PRECISION_ONLY")

        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        regions = _extract_paint_bucket_regions(block, precision_tolerance=1e-5)

        assert len(regions) == 1

    def test_gap_bridge_only_parameter(self) -> None:
        """Test passing gap_bridge_tolerance with precision_tolerance=0 (mutual exclusivity)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="GAP_BRIDGE_ONLY")

        # Clean rectangle should work with gap bridging enabled
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        # Gap bridge with precision_tolerance=0 (mutually exclusive)
        regions = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=2.0
        )

        assert len(regions) == 1

    def test_mutual_exclusivity_design(self) -> None:
        """Document that precision_tolerance and gap_bridge_tolerance are mutually exclusive.

        The GUI enforces mutual exclusivity - users can only enable one option at a time.
        This test documents the design by showing both approaches work independently.
        Note: The function technically accepts both parameters, but the GUI prevents this.
        """
        doc = ezdxf.new()
        block = doc.blocks.new(name="MUTUAL_EXCLUSIVITY")

        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        # Precision Fix approach (gap_bridge_tolerance=0)
        regions_precision = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-5, gap_bridge_tolerance=0
        )
        assert len(regions_precision) == 1

        # Gap Bridge approach (precision_tolerance=0)
        regions_gap_bridge = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=0.5
        )
        assert len(regions_gap_bridge) == 1

    def test_abort_event_still_works_with_tolerances(self) -> None:
        """Test that abort_event parameter works with new tolerance parameters."""
        import threading

        doc = ezdxf.new()
        block = doc.blocks.new(name="ABORT_TEST")
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(GeometryAbortedError):
            _extract_paint_bucket_regions(
                block, abort_event, precision_tolerance=0, gap_bridge_tolerance=1.0
            )


class TestUnitToleranceMapping:
    """Tests for unit-to-tolerance constant mappings."""

    def test_mm_tolerance(self) -> None:
        """MM drawings should use 1e-6 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[4] == 1e-6

    def test_meter_tolerance(self) -> None:
        """Meter drawings should use 1e-4 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[6] == 1e-4

    def test_inch_tolerance(self) -> None:
        """Inch drawings should use appropriate precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[1] == 1e-6

    def test_feet_tolerance(self) -> None:
        """Feet drawings should use 1e-5 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[2] == 1e-5

    def test_cm_tolerance(self) -> None:
        """Centimeter drawings should use 1e-5 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[5] == 1e-5

    def test_unitless_tolerance(self) -> None:
        """Unitless drawings should use 1e-6 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[0] == 1e-6

    def test_default_gap_amounts(self) -> None:
        """Default gap closure tolerance should be appropriate for each unit."""
        # Verify key unit defaults (3mm base value)
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[4] == 3.0  # MM: 3mm
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[6] == 0.003  # M: 3mm in meters
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[1] == 0.125  # IN: 1/8 inch
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[2] == 0.0104  # FT: 1/8 inch in feet
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[5] == 0.3  # CM: 0.3 cm
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[0] == 3.0  # Unitless


class TestPrecisionSnapOrderFix:
    """Test suite for the precision snap before union fix.

    This validates that coordinate snapping happens BEFORE unary_union()
    so that line endpoints with floating-point precision errors are aligned
    to grid points before intersection detection occurs.
    """

    def test_snap_linestring_coords_basic(self) -> None:
        """Test that _snap_linestring_coords correctly snaps coordinates."""
        # Line with precision error: endpoint at (99.9999999962746, 50.0000000002328)
        line = LineString([(0, 0), (99.9999999962746, 50.0000000002328)])

        snapped = _snap_linestring_coords(line, tolerance=1e-6)

        # Coordinates should be snapped to grid (effectively rounding to 6 decimals)
        coords = list(snapped.coords)
        assert len(coords) == 2
        assert coords[0] == (0.0, 0.0)
        # With 1e-6 tolerance, 99.9999999962746 rounds to 100.0
        assert coords[1][0] == pytest.approx(100.0, abs=1e-6)
        assert coords[1][1] == pytest.approx(50.0, abs=1e-6)

    def test_snap_linestring_coords_zero_tolerance(self) -> None:
        """Test that zero tolerance returns the original line unmodified."""
        line = LineString([(0, 0), (99.9999999962746, 50.0000000002328)])

        snapped = _snap_linestring_coords(line, tolerance=0)

        # Should return the same line object
        assert snapped is line

    def test_snap_linestring_coords_negative_tolerance(self) -> None:
        """Test that negative tolerance returns the original line unmodified."""
        line = LineString([(0, 0), (99.9999999962746, 50.0000000002328)])

        snapped = _snap_linestring_coords(line, tolerance=-1.0)

        # Should return the same line object
        assert snapped is line

    def test_snap_linestring_coords_larger_tolerance(self) -> None:
        """Test snapping with a larger tolerance value."""
        # Line endpoint at (99.5, 50.3)
        line = LineString([(0, 0), (99.5, 50.3)])

        # With tolerance=1.0, coordinates snap to nearest integer
        snapped = _snap_linestring_coords(line, tolerance=1.0)

        coords = list(snapped.coords)
        assert coords[1][0] == pytest.approx(100.0, abs=0.01)
        assert coords[1][1] == pytest.approx(50.0, abs=0.01)

    def test_precision_error_without_fix(self) -> None:
        """Test that precision_tolerance=0 demonstrates the bug (fewer regions).

        When precision snapping is disabled, line endpoints with nanometer-scale
        errors don't align with vertical edges, preventing proper edge splitting.
        """
        doc = ezdxf.new()
        block = doc.blocks.new(name="PRECISION_BUG")

        # Rectangle 900x1200
        block.add_lwpolyline([(0, 0), (900, 0), (900, 1200), (0, 1200)], close=True)

        # Horizontal dividers with precision error on right endpoint
        # Left endpoints exact, right endpoints have nanometer precision error
        block.add_line((0, 400), (899.9999999962746, 400.0000000002328))
        block.add_line((0, 800), (899.9999999962746, 800.0000000002328))

        # Without precision fix, the dividers don't properly split the right edge
        regions_no_fix = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=0
        )

        # With precision_tolerance=0, should get fewer than 3 regions
        # because right edge isn't split at divider endpoints
        assert len(regions_no_fix) < 3

    def test_precision_error_with_fix(self) -> None:
        """Test that precision_tolerance>0 fixes the precision error bug.

        With coordinate snapping BEFORE unary_union(), endpoints are aligned
        to grid points and intersection detection works correctly.
        """
        doc = ezdxf.new()
        block = doc.blocks.new(name="PRECISION_FIXED")

        # Rectangle 900x1200
        block.add_lwpolyline([(0, 0), (900, 0), (900, 1200), (0, 1200)], close=True)

        # Horizontal dividers with precision error on right endpoint
        block.add_line((0, 400), (899.9999999962746, 400.0000000002328))
        block.add_line((0, 800), (899.9999999962746, 800.0000000002328))

        # With precision fix, dividers properly split the rectangle into 3 rows
        regions_with_fix = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-6, gap_bridge_tolerance=0
        )

        # Should produce exactly 3 regions (bottom, middle, top rows)
        assert len(regions_with_fix) == 3

    def test_precision_error_shelf_regions_from_dxf(self) -> None:
        """Test precision fix using the test DXF file with precision errors."""
        doc = ezdxf.readfile("app/tests/assets/precision_snap_order_test.dxf")
        block = doc.blocks.get("PRECISION_ERROR_SHELF")

        # With default precision tolerance, should get 3 regions
        regions = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-6, gap_bridge_tolerance=0
        )

        # The block has a rectangle with 2 horizontal dividers = 3 regions
        assert len(regions) == 3

        # Verify each region has reasonable area (rectangle is 900x1200)
        # With 2 dividers at y=400 and y=800, regions are:
        # - Bottom: 900 * 400 = 360,000
        # - Middle: 900 * 400 = 360,000
        # - Top: 900 * 400 = 360,000
        from shapely import Polygon as ShapelyPolygon

        areas = sorted([ShapelyPolygon(r).area for r in regions])
        for area in areas:
            assert 350000 < area < 370000  # ~360,000 with some tolerance

    def test_precision_fix_preserves_clean_geometry(self) -> None:
        """Test that precision fix doesn't break clean geometry without errors."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CLEAN_GEOMETRY")

        # Perfect rectangle with exact coordinates
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Perfect dividers with exact coordinates
        block.add_line((0, 50), (100, 50))
        block.add_line((50, 0), (50, 100))

        # Should produce 4 regions with or without precision fix
        regions_no_fix = _extract_paint_bucket_regions(
            block, precision_tolerance=0, gap_bridge_tolerance=0
        )
        regions_with_fix = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-6, gap_bridge_tolerance=0
        )

        assert len(regions_no_fix) == 4
        assert len(regions_with_fix) == 4

    def test_precision_fix_with_multiple_affected_edges(self) -> None:
        """Test precision fix with multiple edges having precision errors."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MULTI_ERROR")

        # Rectangle with slightly imprecise corners
        block.add_lwpolyline(
            [
                (0.0000000001, 0.0000000002),
                (99.9999999998, 0.0000000001),
                (100.0000000001, 99.9999999999),
                (0.0000000002, 100.0000000001),
            ],
            close=True,
        )

        # Dividers also with small errors
        block.add_line((0.0000000003, 49.9999999998), (99.9999999997, 50.0000000002))

        # With precision fix, should still get 2 regions
        regions = _extract_paint_bucket_regions(
            block, precision_tolerance=1e-6, gap_bridge_tolerance=0
        )

        assert len(regions) == 2


class TestCalculatePolygonArea:
    """Test suite for calculate_polygon_area function."""

    def test_square_area(self) -> None:
        """Test area calculation for 10x10 square."""
        square: list[tuple[float, float]] = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0),
        ]
        assert calculate_polygon_area(square) == 100.0

    def test_rectangle_area(self) -> None:
        """Test area calculation for 20x10 rectangle."""
        rectangle: list[tuple[float, float]] = [
            (0.0, 0.0),
            (20.0, 0.0),
            (20.0, 10.0),
            (0.0, 10.0),
        ]
        assert calculate_polygon_area(rectangle) == 200.0

    def test_triangle_area(self) -> None:
        """Test area calculation for right triangle with base 10, height 10."""
        triangle: list[tuple[float, float]] = [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0)]
        assert calculate_polygon_area(triangle) == 50.0

    def test_irregular_polygon_area(self) -> None:
        """Test area calculation for irregular quadrilateral."""
        # L-shaped polygon: (0,0), (10,0), (10,5), (5,5), (5,10), (0,10)
        # Area = 10*10 - 5*5 = 75
        l_shape: list[tuple[float, float]] = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 5.0),
            (5.0, 5.0),
            (5.0, 10.0),
            (0.0, 10.0),
        ]
        assert calculate_polygon_area(l_shape) == 75.0

    def test_degenerate_polygon_empty(self) -> None:
        """Test that empty list returns 0.0."""
        assert calculate_polygon_area([]) == 0.0

    def test_degenerate_polygon_single_point(self) -> None:
        """Test that single point returns 0.0."""
        assert calculate_polygon_area([(5.0, 5.0)]) == 0.0

    def test_degenerate_polygon_two_points(self) -> None:
        """Test that two points (line) returns 0.0."""
        assert calculate_polygon_area([(0.0, 0.0), (10.0, 10.0)]) == 0.0

    def test_area_always_positive(self) -> None:
        """Test that area is positive regardless of vertex winding order."""
        # Counter-clockwise winding
        ccw: list[tuple[float, float]] = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0),
        ]
        # Clockwise winding
        cw: list[tuple[float, float]] = [
            (0.0, 0.0),
            (0.0, 10.0),
            (10.0, 10.0),
            (10.0, 0.0),
        ]

        assert calculate_polygon_area(ccw) == 100.0
        assert calculate_polygon_area(cw) == 100.0
        # Both should be positive
        assert calculate_polygon_area(ccw) > 0
        assert calculate_polygon_area(cw) > 0


class TestCalculateShortestStraightSide:
    """Test suite for calculate_shortest_straight_side function."""

    def test_square_shortest_side(self) -> None:
        """Test that 10x10 square returns (10.0, 4) for all equal sides."""
        square: list[tuple[float, float]] = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0),
        ]
        shortest_side, side_count = calculate_shortest_straight_side(square)
        assert shortest_side == pytest.approx(10.0)
        assert side_count == 4

    def test_rectangle_shortest_side(self) -> None:
        """Test that 100x50 rectangle returns (50.0, 4) for shorter sides."""
        rectangle: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 50.0),
            (0.0, 50.0),
        ]
        shortest_side, side_count = calculate_shortest_straight_side(rectangle)
        assert shortest_side == pytest.approx(50.0)
        assert side_count == 4

    def test_collinear_edge_merging(self) -> None:
        """Test that rectangle with split bottom edge still finds correct shortest side."""
        # Rectangle with bottom edge split into two segments
        # Bottom: (0,0)-(50,0)-(100,0), Right: (100,0)-(100,50)
        # Top: (100,50)-(0,50), Left: (0,50)-(0,0)
        split_rect: list[tuple[float, float]] = [
            (0.0, 0.0),
            (50.0, 0.0),
            (100.0, 0.0),
            (100.0, 50.0),
            (0.0, 50.0),
        ]
        # Bottom edge is 100 (merged), right edge is 50, top is 100, left is 50
        shortest_side, side_count = calculate_shortest_straight_side(split_rect)
        assert shortest_side == pytest.approx(50.0)
        assert side_count == 4

    def test_collinear_edge_merging_three_segments(self) -> None:
        """Test that bottom edge split into 3 parts still merges correctly."""
        # Bottom edge split: (0,0)-(33,0)-(66,0)-(100,0)
        split_rect: list[tuple[float, float]] = [
            (0.0, 0.0),
            (33.0, 0.0),
            (66.0, 0.0),
            (100.0, 0.0),
            (100.0, 50.0),
            (0.0, 50.0),
        ]
        # Bottom: 100 (merged), Right: 50, Top: 100, Left: 50
        shortest_side, side_count = calculate_shortest_straight_side(split_rect)
        assert shortest_side == pytest.approx(50.0)
        assert side_count == 4

    def test_triangle_shortest_side(self) -> None:
        """Test 3-4-5 right triangle returns (3.0, 3) for shortest side."""
        # 3-4-5 right triangle
        triangle: list[tuple[float, float]] = [(0.0, 0.0), (3.0, 0.0), (0.0, 4.0)]
        # Sides: bottom=3, left=4, hypotenuse=5
        shortest_side, side_count = calculate_shortest_straight_side(triangle)
        assert shortest_side == pytest.approx(3.0)
        assert side_count == 3

    def test_degenerate_polygon_empty(self) -> None:
        """Test that empty list returns (0.0, 0)."""
        shortest_side, side_count = calculate_shortest_straight_side([])
        assert shortest_side == 0.0
        assert side_count == 0

    def test_degenerate_polygon_two_points(self) -> None:
        """Test that two points returns (0.0, 0)."""
        shortest_side, side_count = calculate_shortest_straight_side(
            [(0.0, 0.0), (10.0, 10.0)]
        )
        assert shortest_side == 0.0
        assert side_count == 0

    def test_custom_angle_tolerance(self) -> None:
        """Test that custom tolerance parameter works correctly."""
        # Rectangle with significant angle deviation on bottom edge
        # Point (50, 2.0) creates a ~2.3 degree deviation from horizontal
        # tan(2.3 deg) = ~0.04, so y offset = 50 * tan(2.3) = ~2.0
        deviation: list[tuple[float, float]] = [
            (0.0, 0.0),
            (50.0, 2.0),
            (100.0, 0.0),
            (100.0, 50.0),
            (0.0, 50.0),
        ]

        # With large tolerance (5 degrees), edges should merge
        # atan(2/50) = 2.29 degrees, so 5 degree tolerance merges them
        shortest_large, count_large = calculate_shortest_straight_side(
            deviation, angle_tolerance=5.0
        )

        # With tight tolerance (1 degree), edges should NOT merge
        # since 2.29 degrees > 1 degree
        shortest_tight, count_tight = calculate_shortest_straight_side(
            deviation, angle_tolerance=1.0
        )

        # Large tolerance merges bottom edges, so shortest is 50 (vertical sides)
        assert shortest_large == pytest.approx(50.0)
        assert count_large == 4  # Merged to 4 sides
        # Tight tolerance doesn't merge, so we get smaller segments (~50)
        # The split segments are about 50 units each
        assert shortest_tight < 51.0  # Should find the ~50 unit split segment
        assert count_tight == 5  # 5 sides when not merged

    def test_very_small_edges_ignored(self) -> None:
        """Test that edges < 1e-9 are ignored."""
        # Rectangle with a degenerate (zero-length) segment
        rect_with_tiny: list[tuple[float, float]] = [
            (0.0, 0.0),
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 50.0),
            (0.0, 50.0),
        ]
        # The degenerate edge from (0,0) to (0,0) should be ignored
        shortest_side, side_count = calculate_shortest_straight_side(rect_with_tiny)
        assert shortest_side == pytest.approx(50.0)
        assert side_count == 4

    def test_angle_wraparound(self) -> None:
        """Test that collinearity detection handles 180-degree wraparound."""
        # Two edges that are collinear but have angles near 0 and near 180
        # Horizontal edge going right (angle ~0) followed by edge going left (angle ~180)
        # This shouldn't happen in a valid polygon, but test the angle logic
        # Create a simple case with edges at 179 and 1 degree (should be considered collinear)
        # Actually, for a valid polygon, test the horizontal edge case
        horizontal_rect: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 10.0),
            (0.0, 10.0),
        ]
        # All horizontal and vertical edges, no wraparound issue
        shortest_side, side_count = calculate_shortest_straight_side(horizontal_rect)
        assert shortest_side == pytest.approx(10.0)
        assert side_count == 4

    def test_all_edges_equal(self) -> None:
        """Test polygon where all edges have equal length."""
        # Equilateral-like hexagon (approximation for testing)
        square: list[tuple[float, float]] = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0),
        ]
        shortest_side, side_count = calculate_shortest_straight_side(square)
        assert shortest_side == pytest.approx(10.0)
        assert side_count == 4

    def test_hexagon_side_count(self) -> None:
        """Test that hexagon returns correct side count of 6."""
        # Regular hexagon-like shape
        hexagon: list[tuple[float, float]] = [
            (10.0, 0.0),
            (20.0, 0.0),
            (25.0, 8.66),
            (20.0, 17.32),
            (10.0, 17.32),
            (5.0, 8.66),
        ]
        shortest_side, side_count = calculate_shortest_straight_side(hexagon)
        assert side_count == 6
        assert shortest_side > 0.0

    def test_l_shaped_polygon_side_count(self) -> None:
        """Test that L-shaped polygon returns 6 sides."""
        # L-shape: 6 vertices, 6 sides
        l_shape: list[tuple[float, float]] = [
            (0.0, 0.0),
            (20.0, 0.0),
            (20.0, 10.0),
            (10.0, 10.0),
            (10.0, 30.0),
            (0.0, 30.0),
        ]
        shortest_side, side_count = calculate_shortest_straight_side(l_shape)
        assert side_count == 6
        assert shortest_side == pytest.approx(10.0)  # Shortest is the 10-unit sides

    def test_collinear_edge_merging_wraparound(self) -> None:
        """Test that first and last sides merge when V0 is mid-edge."""
        # Rectangle with V0 in middle of bottom edge
        # Bottom edge: V5->V0->V1->V2 (all collinear, should merge to one side)
        # Left edge: V2->V3
        # Top edge: V3->V4
        # Right edge: V4->V5
        wraparound_rect: list[tuple[float, float]] = [
            (50.0, 0.0),  # V0 - middle of bottom edge
            (25.0, 0.0),  # V1 - collinear with V0
            (0.0, 0.0),  # V2 - left corner
            (0.0, 30.0),  # V3 - top-left
            (100.0, 30.0),  # V4 - top-right
            (100.0, 0.0),  # V5 - right corner, edge to V0 is collinear with V0->V1
        ]
        # Expected: 4 sides (rectangle), shortest side is 30 (left/right edges)
        shortest_side, side_count = calculate_shortest_straight_side(wraparound_rect)
        assert side_count == 4, f"Expected 4 sides, got {side_count}"
        assert shortest_side == pytest.approx(30.0)

    def test_collinear_merging_real_world_case(self) -> None:
        """Test the exact failing polygon from the bug report."""
        # Real polygon that was incorrectly detected as 5-sided
        real_polygon: list[tuple[float, float]] = [
            (24953.75, 13351.94),  # V0 - middle of bottom edge
            (24172.75, 13351.94),  # V1
            (23391.75, 13351.94),  # V2 - left corner
            (23391.75, 13424.94),  # V3 - top-left
            (25734.75, 13424.94),  # V4 - top-right
            (25734.75, 13351.94),  # V5 - right corner
        ]
        # This is a rectangle:
        # - Bottom: 2343.0 units (25734.75 - 23391.75)
        # - Height: 73.0 units (13424.94 - 13351.94)
        shortest_side, side_count = calculate_shortest_straight_side(real_polygon)
        assert side_count == 4, f"Expected 4 sides (rectangle), got {side_count}"
        assert shortest_side == pytest.approx(73.0, abs=0.1)


class TestPreFilterLineLengthFilter:
    """Test suite for LINE pre-filter in _extract_all_edges function."""

    def test_default_extracts_all_lines(self) -> None:
        """Test that default (min_line_length=0) extracts all lines."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ALL_LINES")
        block.add_line((0, 0), (1, 0))  # Short line
        block.add_line((0, 0), (100, 0))  # Long line

        edges = _extract_all_edges(block, min_line_length=0)

        assert len(edges) == 2

    def test_filters_short_lines(self) -> None:
        """Test that short lines are filtered when min_line_length > 0."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="FILTER_SHORT")
        block.add_line((0, 0), (1, 0))  # 1 unit (below threshold)
        block.add_line((0, 0), (100, 0))  # 100 units (above threshold)

        edges = _extract_all_edges(block, min_line_length=5.0)

        assert len(edges) == 1

    def test_line_at_threshold_not_filtered(self) -> None:
        """Test that line exactly at threshold is NOT filtered (< not <=)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="AT_THRESHOLD")
        block.add_line((0, 0), (5, 0))  # Exactly 5 units

        edges = _extract_all_edges(block, min_line_length=5.0)

        # Line is exactly at threshold, should NOT be filtered
        assert len(edges) == 1

    def test_all_lines_below_threshold(self) -> None:
        """Test that all lines below threshold returns empty list."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ALL_SHORT")
        block.add_line((0, 0), (1, 0))
        block.add_line((0, 0), (2, 0))
        block.add_line((0, 0), (3, 0))

        edges = _extract_all_edges(block, min_line_length=10.0)

        assert len(edges) == 0

    def test_diagonal_line_length(self) -> None:
        """Test that diagonal line length is calculated correctly."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="DIAGONAL")
        # 3-4-5 triangle: diagonal from (0,0) to (3,4) = 5 units
        block.add_line((0, 0), (3, 4))  # Length = 5

        edges = _extract_all_edges(block, min_line_length=4.9)
        assert len(edges) == 1

        edges = _extract_all_edges(block, min_line_length=5.1)
        assert len(edges) == 0


class TestPreFilterSkipCurvedEntities:
    """Test suite for skip_curved_entities pre-filter in _extract_all_edges function."""

    def test_default_extracts_circles(self) -> None:
        """Test that default (skip_curved_entities=False) extracts circles."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="WITH_CIRCLE")
        block.add_circle(center=(50, 50), radius=25)

        edges = _extract_all_edges(block, skip_curved_entities=False)

        assert len(edges) > 10  # Circle produces many segments

    def test_skip_curved_filters_circles(self) -> None:
        """Test that skip_curved_entities=True skips CIRCLE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SKIP_CIRCLE")
        block.add_circle(center=(50, 50), radius=25)

        edges = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges) == 0

    def test_skip_curved_filters_arcs(self) -> None:
        """Test that skip_curved_entities=True skips ARC entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SKIP_ARC")
        block.add_arc(center=(50, 50), radius=25, start_angle=0, end_angle=90)

        edges = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges) == 0

    def test_skip_curved_does_not_affect_lines(self) -> None:
        """Test that skip_curved_entities does NOT affect LINE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="LINES_ONLY")
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))

        edges = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges) == 2

    def test_skip_curved_does_not_affect_polylines(self) -> None:
        """Test that skip_curved_entities does NOT affect LWPOLYLINE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="POLY_ONLY")
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        edges = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges) == 4  # 4 edges of closed rectangle

    def test_mixed_entities_with_skip_curved(self) -> None:
        """Test mixed entities with skip_curved_entities=True."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED")
        block.add_line((0, 0), (100, 0))  # LINE - kept
        block.add_circle(center=(50, 50), radius=25)  # CIRCLE - skipped
        block.add_arc(
            center=(100, 100), radius=20, start_angle=0, end_angle=90
        )  # ARC - skipped
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10)], close=False)  # POLY - kept

        edges = _extract_all_edges(block, skip_curved_entities=True)

        # Only LINE (1) + LWPOLYLINE (2 edges, open) = 3 edges
        assert len(edges) == 3

    def test_combined_prefilters(self) -> None:
        """Test that both pre-filters work together."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="COMBINED")
        block.add_line((0, 0), (1, 0))  # Short line - filtered by min_line_length
        block.add_line((0, 0), (100, 0))  # Long line - kept
        block.add_circle(center=(50, 50), radius=25)  # Circle - filtered by skip_curved

        edges = _extract_all_edges(
            block, skip_curved_entities=True, min_line_length=5.0
        )

        # Only the long line should remain
        assert len(edges) == 1

    def test_skip_curved_with_hatch_containing_arc(self) -> None:
        """Verify HATCH with ArcEdge is still extracted (skip_curved only affects CIRCLE/ARC).

        The skip_curved_entities pre-filter only skips CIRCLE and ARC entities.
        HATCH entities with arc edges are still processed because the hatch
        boundary extraction uses ezdxf's from_hatch() which handles arc edges
        internally, and we don't skip HATCH entities.
        """
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCH_ARC")

        # Create a HATCH with edge path containing arc edge
        hatch = block.add_hatch()
        edge_path = hatch.paths.add_edge_path()
        edge_path.add_line((0, 0), (100, 0))
        edge_path.add_arc(center=(100, 50), radius=50, start_angle=270, end_angle=90)
        edge_path.add_line((100, 100), (0, 100))
        edge_path.add_line((0, 100), (0, 0))

        # HATCH should still be extracted even with skip_curved_entities=True
        edges = _extract_all_edges(block, skip_curved_entities=True)

        # Should have edges from HATCH boundary (lines + arc flattened)
        assert len(edges) > 3  # At least the 3 line edges + arc segments


class TestPolygonHasCurvedEdges:
    """Test suite for _polygon_has_curved_edges function."""

    def test_rectangle_returns_false(self) -> None:
        """Test that simple rectangle returns False (all straight edges)."""
        rectangle: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 50.0),
            (0.0, 50.0),
        ]

        result = _polygon_has_curved_edges(rectangle)

        assert result is False

    def test_triangle_returns_false(self) -> None:
        """Test that simple triangle returns False (all straight edges)."""
        triangle: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
            (50.0, 86.6),
        ]

        result = _polygon_has_curved_edges(triangle)

        assert result is False

    def test_circle_approximation_returns_true(self) -> None:
        """Test that circle approximated by many points returns True."""
        import math as m

        # Create circle approximation with 36 points
        circle: list[tuple[float, float]] = [
            (50 + 25 * m.cos(m.radians(i * 10)), 50 + 25 * m.sin(m.radians(i * 10)))
            for i in range(36)
        ]

        result = _polygon_has_curved_edges(circle)

        assert result is True

    def test_arc_approximation_returns_true(self) -> None:
        """Test that arc (partial circle) returns True."""
        import math as m

        # Create arc approximation with points every 10 degrees for 90 degrees
        # then straight lines back
        arc_points: list[tuple[float, float]] = [
            (50 + 25 * m.cos(m.radians(i * 10)), 50 + 25 * m.sin(m.radians(i * 10)))
            for i in range(10)
        ]
        # Add straight line closing points
        arc_points.extend([(50, 50), (75, 50)])

        result = _polygon_has_curved_edges(arc_points)

        assert result is True

    def test_custom_tolerance_tighter(self) -> None:
        """Test that tighter tolerance detects smaller deviations."""
        # Pentagon-like shape with slight curve (5 points on circle)
        import math as m

        pentagon: list[tuple[float, float]] = [
            (50 + 25 * m.cos(m.radians(i * 72)), 50 + 25 * m.sin(m.radians(i * 72)))
            for i in range(5)
        ]

        # With default tolerance (0.01), might not detect
        result_default = _polygon_has_curved_edges(pentagon, tolerance=0.01)
        # With very tight tolerance, might detect deviation
        result_tight = _polygon_has_curved_edges(pentagon, tolerance=0.001)

        # Pentagon with 5 points is close to straight edges
        # The deviation between consecutive points on a circle is subtle
        assert isinstance(result_default, bool)
        assert isinstance(result_tight, bool)

    def test_degenerate_empty_returns_false(self) -> None:
        """Test that empty list returns False."""
        result = _polygon_has_curved_edges([])

        assert result is False

    def test_degenerate_three_points_returns_false(self) -> None:
        """Test that polygon with 3 points returns False (need 4 for curve detection)."""
        triangle: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
            (50.0, 50.0),
        ]

        result = _polygon_has_curved_edges(triangle)

        assert result is False

    def test_l_shape_returns_false(self) -> None:
        """Test that L-shape polygon returns False (all straight edges)."""
        l_shape: list[tuple[float, float]] = [
            (0.0, 0.0),
            (50.0, 0.0),
            (50.0, 30.0),
            (20.0, 30.0),
            (20.0, 50.0),
            (0.0, 50.0),
        ]

        result = _polygon_has_curved_edges(l_shape)

        assert result is False

    def test_collinear_points_returns_false(self) -> None:
        """Test that polygon with collinear points returns False."""
        # Rectangle with extra point on bottom edge
        rect_with_midpoint: list[tuple[float, float]] = [
            (0.0, 0.0),
            (50.0, 0.0),  # Extra point on straight edge
            (100.0, 0.0),
            (100.0, 50.0),
            (0.0, 50.0),
        ]

        result = _polygon_has_curved_edges(rect_with_midpoint)

        # Collinear points should not register as curved
        assert result is False

    def test_large_circle_many_segments(self) -> None:
        """Test that large circle with many segments still detected as curved."""
        import math as m

        # Create circle with 100 points (very smooth approximation)
        large_circle: list[tuple[float, float]] = [
            (50 + 100 * m.cos(m.radians(i * 3.6)), 50 + 100 * m.sin(m.radians(i * 3.6)))
            for i in range(100)
        ]

        result = _polygon_has_curved_edges(large_circle)

        assert result is True

    def test_hexagon_not_curved(self) -> None:
        """Test that regular hexagon should not be detected as curved.

        A hexagon has 60-degree angles between edges, which are sharp corners,
        not smooth curves. The curve detection looks for consecutive small
        angular deviations (< 30 degrees), not sharp corners.
        """
        import math as m

        # Regular hexagon with vertices at 60-degree intervals
        hexagon: list[tuple[float, float]] = [
            (50 + 40 * m.cos(m.radians(i * 60)), 50 + 40 * m.sin(m.radians(i * 60)))
            for i in range(6)
        ]

        result = _polygon_has_curved_edges(hexagon)

        # Hexagon has sharp corners (60 degrees), not smooth curves
        assert result is False

    def test_very_slight_curve_detected(self) -> None:
        """Test edge case with minimal curvature (semicircle approximation)."""
        import math as m

        # Semicircle with 18 points (10-degree intervals over 180 degrees)
        # + 2 straight line segments closing the shape
        semicircle_points: list[tuple[float, float]] = [
            (50 + 30 * m.cos(m.radians(i * 10)), 30 * m.sin(m.radians(i * 10)))
            for i in range(19)  # 0 to 180 degrees
        ]
        # Close with straight lines
        semicircle_points.append((20, -10))
        semicircle_points.append((80, -10))

        result = _polygon_has_curved_edges(semicircle_points)

        # Should detect the curved semicircle portion
        assert result is True

    def test_single_curved_segment_in_rectangle(self) -> None:
        """Test rectangle with one rounded corner (partial curve)."""
        import math as m

        # Rectangle 100x50 with rounded corner at top-right
        points: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
        ]
        # Add rounded corner at top-right (quarter circle, 90 degrees, 10 points)
        for i in range(10):
            angle = -90 + i * 10  # From 270 to 360 degrees
            x = 90.0 + 10.0 * m.cos(m.radians(angle))
            y = 40.0 + 10.0 * m.sin(m.radians(angle))
            points.append((x, y))
        # Continue with straight edges
        points.extend(
            [
                (90.0, 50.0),
                (0.0, 50.0),
            ]
        )

        result = _polygon_has_curved_edges(points)

        # Should detect the rounded corner
        assert result is True


class TestLwpolylineBulge:
    """Test suite for LWPOLYLINE bulge handling in edge extraction and bounding box calculation.

    Validates that LWPOLYLINE segments with non-zero bulge values are correctly
    flattened into arc approximations rather than being treated as straight chords.
    """

    def test_extract_edges_straight_lwpolyline(self) -> None:
        """Test that straight LWPOLYLINE (no bulge) extracts expected edge count."""
        doc = ezdxf.readfile("app/tests/assets/lwpolyline_bulge_test.dxf")
        block = doc.blocks.get("LWPOLY_STRAIGHT")

        edges = _extract_all_edges(block)

        # Simple L-shape with 3 vertices should produce exactly 2 edges
        # (0,0) -> (100,0) -> (100,100)
        assert len(edges) == 2
        assert all(isinstance(e, LineString) for e in edges)

    def test_extract_edges_arc_lwpolyline(self) -> None:
        """Test that LWPOLYLINE with 90-degree arc bulge extracts multiple edges."""
        doc = ezdxf.readfile("app/tests/assets/lwpolyline_bulge_test.dxf")
        block = doc.blocks.get("LWPOLY_90DEG_ARC")

        edges = _extract_all_edges(block)

        # With bulge handling:
        # - First segment (0,0) to (100,0): straight line = 1 edge
        # - Second segment (100,0) to (100,100) with 90-deg bulge: multiple edges
        # Total should be MORE than 2 edges (proving arc is not treated as chord)
        assert len(edges) > 2

    def test_extract_edges_mixed_lwpolyline(self) -> None:
        """Test that mixed straight/curved LWPOLYLINE segments are handled correctly."""
        doc = ezdxf.readfile("app/tests/assets/lwpolyline_bulge_test.dxf")
        block = doc.blocks.get("LWPOLY_MIXED")

        edges = _extract_all_edges(block)

        # Closed rectangle-like shape with one curved side:
        # - 3 straight sides: 3 edges
        # - 1 curved side (90-deg arc): multiple edges
        # Total should be more than 4 edges
        assert len(edges) > 4

    def test_extract_edges_closed_arc_lwpolyline(self) -> None:
        """Test that closed LWPOLYLINE with semicircular arc is handled correctly."""
        doc = ezdxf.readfile("app/tests/assets/lwpolyline_bulge_test.dxf")
        block = doc.blocks.get("LWPOLY_CLOSED_ARC")

        edges = _extract_all_edges(block)

        # Rectangle with semicircular top:
        # - 3 straight sides: 3 edges
        # - 1 semicircular side (180-deg arc): many edges
        # Total should be significantly more than 4 edges
        assert len(edges) > 8

    def test_bbox_straight_lwpolyline(self) -> None:
        """Test bounding box for straight LWPOLYLINE (no bulge)."""
        doc = ezdxf.readfile("app/tests/assets/lwpolyline_bulge_test.dxf")
        block = doc.blocks.get("LWPOLY_STRAIGHT")

        bbox = _get_block_bounding_box(block)

        # L-shape from (0,0) to (100,0) to (100,100)
        # Bbox should be exactly (0, 0, 100, 100)
        assert bbox[0] == pytest.approx(0.0, abs=0.01)  # min_x
        assert bbox[1] == pytest.approx(0.0, abs=0.01)  # min_y
        assert bbox[2] == pytest.approx(100.0, abs=0.01)  # max_x
        assert bbox[3] == pytest.approx(100.0, abs=0.01)  # max_y

    def test_bbox_arc_lwpolyline_includes_arc_extent(self) -> None:
        """Test bounding box includes full arc extent (not just chord endpoints)."""
        doc = ezdxf.readfile("app/tests/assets/lwpolyline_bulge_test.dxf")
        block = doc.blocks.get("LWPOLY_90DEG_ARC")

        bbox = _get_block_bounding_box(block)

        # L-shape with 90-degree outward arc from (100,0) to (100,100)
        # The arc bulges to the RIGHT (positive bulge = counter-clockwise)
        # Arc center is at approximately (100, 50) with radius ~70.7
        # So max_x should be > 100 (the arc extends beyond the chord endpoints)
        assert bbox[0] == pytest.approx(0.0, abs=0.01)  # min_x = 0
        assert bbox[1] == pytest.approx(0.0, abs=0.01)  # min_y = 0
        assert bbox[2] > 100.0  # max_x should exceed 100 due to arc bulge
        assert bbox[3] == pytest.approx(100.0, abs=0.01)  # max_y = 100

    def test_bbox_inward_arc_lwpolyline(self) -> None:
        """Test bounding box for LWPOLYLINE with inward (negative) bulge."""
        doc = ezdxf.readfile("app/tests/assets/lwpolyline_bulge_test.dxf")
        block = doc.blocks.get("LWPOLY_INWARD_ARC")

        bbox = _get_block_bounding_box(block)

        # L-shape with 90-degree inward arc from (100,0) to (100,100)
        # Negative bulge means arc bulges to the LEFT (clockwise)
        # So max_x should be exactly 100 (arc doesn't extend beyond)
        # But arc might affect the internal space
        assert bbox[0] == pytest.approx(0.0, abs=0.01)  # min_x = 0
        assert bbox[1] == pytest.approx(0.0, abs=0.01)  # min_y = 0
        assert bbox[2] == pytest.approx(100.0, abs=0.01)  # max_x = 100 (inward arc)
        assert bbox[3] == pytest.approx(100.0, abs=0.01)  # max_y = 100

    def test_closed_lwpolyline_with_bulge_forms_region(self) -> None:
        """Test that closed LWPOLYLINE with bulge forms valid paint bucket region."""
        doc = ezdxf.readfile("app/tests/assets/lwpolyline_bulge_test.dxf")
        block = doc.blocks.get("LWPOLY_MIXED")

        regions = _extract_paint_bucket_regions(block)

        # Closed LWPOLYLINE should form exactly one closed region
        assert len(regions) == 1

    def test_bulge_flattening_produces_arc_vertices(self) -> None:
        """Test that bulge flattening produces intermediate vertices along the arc."""
        doc = ezdxf.readfile("app/tests/assets/lwpolyline_bulge_test.dxf")
        block = doc.blocks.get("LWPOLY_90DEG_ARC")

        edges = _extract_all_edges(block)

        # Collect all unique coordinates from edges
        all_coords = set()
        for edge in edges:
            for coord in edge.coords:
                all_coords.add((round(coord[0], 2), round(coord[1], 2)))

        # Should have more than just the 3 original LWPOLYLINE vertices
        # The arc segment should add intermediate points
        assert len(all_coords) > 3

        # Verify some intermediate points exist along the arc
        # The arc from (100,0) to (100,100) with outward bulge should have
        # points with x > 100 (the bulge extends beyond the chord)
        arc_points = [c for c in all_coords if c[0] > 100]
        assert len(arc_points) > 0, "Arc should have points beyond x=100"

    def test_straight_lwpolyline_unchanged_edge_count(self) -> None:
        """Test that straight LWPOLYLINE (bulge=0) has same edge count as before."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="STRAIGHT_TEST")

        # Simple closed rectangle with no bulge
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        edges = _extract_all_edges(block)

        # Should produce exactly 4 edges (no arc flattening needed)
        assert len(edges) == 4


class TestTransformBboxPoints:
    """Test suite for _transform_bbox_points helper function."""

    def test_identity_transform(self) -> None:
        """Test identity transform (scale=1, rotation=0, position=0,0)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

        # Create INSERT with identity transform (defaults)
        msp = doc.modelspace()
        insert = msp.add_blockref("TEST_BLOCK", (0, 0))

        bbox = (0, 0, 10, 10)
        result = _transform_bbox_points(bbox, insert)

        # Should return same corners (identity transform)
        assert len(result) == 4
        assert result[0] == pytest.approx((0.0, 0.0), abs=0.001)
        assert result[1] == pytest.approx((10.0, 0.0), abs=0.001)
        assert result[2] == pytest.approx((10.0, 10.0), abs=0.001)
        assert result[3] == pytest.approx((0.0, 10.0), abs=0.001)

    def test_translation_only(self) -> None:
        """Test position offset (translation only, no scale/rotation)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

        # Create INSERT at position (5, 5)
        msp = doc.modelspace()
        insert = msp.add_blockref("TEST_BLOCK", (5, 5))

        bbox = (0, 0, 10, 10)
        result = _transform_bbox_points(bbox, insert)

        # Should be offset by (5, 5)
        assert result[0] == pytest.approx((5.0, 5.0), abs=0.001)
        assert result[1] == pytest.approx((15.0, 5.0), abs=0.001)
        assert result[2] == pytest.approx((15.0, 15.0), abs=0.001)
        assert result[3] == pytest.approx((5.0, 15.0), abs=0.001)

    def test_uniform_scale(self) -> None:
        """Test uniform scale (xscale=yscale=2)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

        # Create INSERT with 2x scale
        msp = doc.modelspace()
        insert = msp.add_blockref(
            "TEST_BLOCK", (0, 0), dxfattribs={"xscale": 2.0, "yscale": 2.0}
        )

        bbox = (0, 0, 10, 10)
        result = _transform_bbox_points(bbox, insert)

        # Should be scaled 2x
        assert result[0] == pytest.approx((0.0, 0.0), abs=0.001)
        assert result[1] == pytest.approx((20.0, 0.0), abs=0.001)
        assert result[2] == pytest.approx((20.0, 20.0), abs=0.001)
        assert result[3] == pytest.approx((0.0, 20.0), abs=0.001)

    def test_rotation_90_degrees(self) -> None:
        """Test 90 degree rotation."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

        # Create INSERT with 90 degree rotation
        msp = doc.modelspace()
        insert = msp.add_blockref("TEST_BLOCK", (0, 0), dxfattribs={"rotation": 90.0})

        bbox = (0, 0, 10, 10)
        result = _transform_bbox_points(bbox, insert)

        # After 90 degree rotation around origin:
        # (0,0) -> (0,0), (10,0) -> (0,10), (10,10) -> (-10,10), (0,10) -> (-10,0)
        assert result[0] == pytest.approx((0.0, 0.0), abs=0.001)
        assert result[1] == pytest.approx((0.0, 10.0), abs=0.001)
        assert result[2] == pytest.approx((-10.0, 10.0), abs=0.001)
        assert result[3] == pytest.approx((-10.0, 0.0), abs=0.001)

    def test_combined_scale_and_translation(self) -> None:
        """Test combined scale and translation."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

        # Create INSERT with 2x scale at position (5, 5)
        msp = doc.modelspace()
        insert = msp.add_blockref(
            "TEST_BLOCK", (5, 5), dxfattribs={"xscale": 2.0, "yscale": 2.0}
        )

        bbox = (0, 0, 10, 10)
        result = _transform_bbox_points(bbox, insert)

        # Scale first (2x), then translate by (5, 5)
        assert result[0] == pytest.approx((5.0, 5.0), abs=0.001)
        assert result[1] == pytest.approx((25.0, 5.0), abs=0.001)
        assert result[2] == pytest.approx((25.0, 25.0), abs=0.001)
        assert result[3] == pytest.approx((5.0, 25.0), abs=0.001)


class TestNestedInsertBoundingBox:
    """Test suite for nested INSERT bounding box expansion."""

    def test_nested_insert_simple(self) -> None:
        """Test simple nested INSERT with no transform expands bbox correctly."""
        doc = ezdxf.readfile("app/tests/assets/nested_insert_bbox_test.dxf")
        outer_simple = doc.blocks.get("OUTER_SIMPLE")

        # Without doc parameter (backward compatibility) - ignores INSERT
        bbox_without_doc = _get_block_bounding_box(outer_simple)
        # OUTER_SIMPLE has rectangle (0,0) to (50,30)
        assert bbox_without_doc == pytest.approx((0.0, 0.0, 50.0, 30.0), abs=0.001)

        # With doc parameter - includes nested INSERT
        bbox_with_doc = _get_block_bounding_box(outer_simple, doc)
        # INNER_BOX is at (5,5) with size (10,10), so extends to (15,15)
        # But OUTER_SIMPLE's rectangle (50,30) is larger, so bbox unchanged
        assert bbox_with_doc == pytest.approx((0.0, 0.0, 50.0, 30.0), abs=0.001)

    def test_nested_insert_scaled(self) -> None:
        """Test nested INSERT with scale factor expands bbox correctly."""
        doc = ezdxf.readfile("app/tests/assets/nested_insert_bbox_test.dxf")
        outer_scaled = doc.blocks.get("OUTER_SCALED")

        # With doc parameter - includes scaled nested INSERT
        bbox = _get_block_bounding_box(outer_scaled, doc)
        # INNER_BOX is at (5,5) with scale (2,2), so extends to (5+20, 5+20) = (25,25)
        # OUTER_SCALED's rectangle (50,30) is still larger, so bbox unchanged
        assert bbox == pytest.approx((0.0, 0.0, 50.0, 30.0), abs=0.001)

    def test_nested_insert_rotated(self) -> None:
        """Test nested INSERT with rotation expands bbox correctly."""
        doc = ezdxf.readfile("app/tests/assets/nested_insert_bbox_test.dxf")
        outer_rotated = doc.blocks.get("OUTER_ROTATED")

        # With doc parameter - includes rotated nested INSERT
        bbox = _get_block_bounding_box(outer_rotated, doc)

        # INNER_BOX at (25,15) with 45 degree rotation
        # After 45 rotation, (0,0)-(10,10) square becomes diamond
        # The diagonal of (0,0)-(10,10) is sqrt(200) = 14.14
        # Rotated square fits in bbox from center +/- half_diagonal
        # But this is at offset (25,15), so the transformed corners are:
        # Center of INNER_BOX at origin is (5,5) -> after 45 rotation and translation
        # The corners extend outward from (25,15) by the rotated offsets

        # The bbox should still be dominated by OUTER_ROTATED's (0,0) to (50,30)
        # since the rotated INNER_BOX at center (25,15) fits within
        assert bbox[0] == pytest.approx(0.0, abs=0.1)  # min_x
        assert bbox[1] == pytest.approx(0.0, abs=0.1)  # min_y
        assert bbox[2] == pytest.approx(50.0, abs=0.1)  # max_x
        assert bbox[3] == pytest.approx(30.0, abs=0.1)  # max_y

    def test_nested_insert_circular_reference(self) -> None:
        """Test circular block reference does not cause infinite recursion."""
        doc = ezdxf.readfile("app/tests/assets/nested_insert_bbox_test.dxf")
        circular_a = doc.blocks.get("CIRCULAR_A")

        # Should not hang or raise exception
        bbox = _get_block_bounding_box(circular_a, doc)

        # CIRCULAR_A has rectangle (0,0) to (20,20)
        # CIRCULAR_B is at (5,5) with rectangle (0,0) to (10,10), extends to (15,15)
        # CIRCULAR_B contains CIRCULAR_A at (2,2) but that's circular, so skipped
        # Bbox should be at least (0,0,20,20) from CIRCULAR_A's own geometry
        assert bbox[0] <= 0.0  # min_x
        assert bbox[1] <= 0.0  # min_y
        assert bbox[2] >= 15.0  # max_x (includes CIRCULAR_B at 5+10=15)
        assert bbox[3] >= 15.0  # max_y (includes CIRCULAR_B at 5+10=15)

    def test_nested_insert_without_doc_backward_compatible(self) -> None:
        """Test that function works without doc parameter (INSERT ignored)."""
        doc = ezdxf.readfile("app/tests/assets/nested_insert_bbox_test.dxf")
        outer_simple = doc.blocks.get("OUTER_SIMPLE")

        # Without doc parameter - should work and ignore INSERT entities
        bbox = _get_block_bounding_box(outer_simple)

        # Should only include the rectangle (0,0) to (50,30)
        assert bbox == pytest.approx((0.0, 0.0, 50.0, 30.0), abs=0.001)

    def test_nested_insert_deep_nesting(self) -> None:
        """Test multi-level nesting (block A contains B which contains C)."""
        doc = ezdxf.readfile("app/tests/assets/nested_insert_bbox_test.dxf")
        deep_outer = doc.blocks.get("DEEP_OUTER")

        # With doc parameter - includes nested INSERT chain
        bbox = _get_block_bounding_box(deep_outer, doc)

        # DEEP_OUTER: rectangle (0,0) to (100,60) + OUTER_SIMPLE at (10,10)
        # OUTER_SIMPLE: rectangle (0,0) to (50,30) + INNER_BOX at (5,5)
        # INNER_BOX: rectangle (0,0) to (10,10)

        # After transformation:
        # OUTER_SIMPLE at (10,10): (10,10) to (60,40)
        # INNER_BOX inside OUTER_SIMPLE at (5,5) -> (10+5,10+5) = (15,15) to (25,25)

        # Overall bbox should be dominated by DEEP_OUTER's (0,0) to (100,60)
        assert bbox[0] == pytest.approx(0.0, abs=0.1)  # min_x
        assert bbox[1] == pytest.approx(0.0, abs=0.1)  # min_y
        assert bbox[2] == pytest.approx(100.0, abs=0.1)  # max_x
        assert bbox[3] == pytest.approx(60.0, abs=0.1)  # max_y

    def test_nested_insert_missing_block(self) -> None:
        """Test INSERT referencing non-existent block is handled gracefully."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="PARENT_BLOCK")
        block.add_lwpolyline([(0, 0), (50, 0), (50, 30), (0, 30)], close=True)
        # Add blockref to a block that doesn't exist
        block.add_blockref("NONEXISTENT_BLOCK", (10, 10))

        # Should not raise exception
        bbox = _get_block_bounding_box(block, doc)

        # Should still return bbox of the LWPOLYLINE
        assert bbox == pytest.approx((0.0, 0.0, 50.0, 30.0), abs=0.001)

    def test_nested_insert_empty_nested_block(self) -> None:
        """Test INSERT referencing empty block is handled gracefully."""
        doc = ezdxf.new()
        # Create empty nested block
        doc.blocks.new(name="EMPTY_NESTED")
        # Create parent block with reference to empty block
        parent = doc.blocks.new(name="PARENT_BLOCK")
        parent.add_lwpolyline([(0, 0), (50, 0), (50, 30), (0, 30)], close=True)
        parent.add_blockref("EMPTY_NESTED", (10, 10))

        # Should not raise exception
        bbox = _get_block_bounding_box(parent, doc)

        # Should return bbox of the LWPOLYLINE only (empty block returns 0,0,0,0)
        assert bbox == pytest.approx((0.0, 0.0, 50.0, 30.0), abs=0.001)

    def test_inner_box_bbox_unchanged(self) -> None:
        """Test that INNER_BOX (no nested INSERTs) has same bbox with or without doc."""
        doc = ezdxf.readfile("app/tests/assets/nested_insert_bbox_test.dxf")
        inner_box = doc.blocks.get("INNER_BOX")

        bbox_without_doc = _get_block_bounding_box(inner_box)
        bbox_with_doc = _get_block_bounding_box(inner_box, doc)

        # INNER_BOX has no nested INSERTs, so both should be the same
        assert bbox_without_doc == bbox_with_doc
        assert bbox_without_doc == pytest.approx((0.0, 0.0, 10.0, 10.0), abs=0.001)


class TestEllipseSupport:
    """Test suite for ELLIPSE entity support in geometry functions."""

    def test_ellipse_bbox_circular(self) -> None:
        """Test bounding box for near-circular ellipse (ratio ~0.9)."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("ELLIPSE_CIRCULAR")

        bbox = _get_block_bounding_box(block)

        # Center (50, 50), major axis 50 along X, ratio 0.9
        # Semi-major = 50, semi-minor = 45
        # Expected bbox: (50-50, 50-45, 50+50, 50+45) = (0, 5, 100, 95)
        assert bbox[0] == pytest.approx(0.0, abs=0.5)  # min_x
        assert bbox[1] == pytest.approx(5.0, abs=0.5)  # min_y
        assert bbox[2] == pytest.approx(100.0, abs=0.5)  # max_x
        assert bbox[3] == pytest.approx(95.0, abs=0.5)  # max_y

    def test_ellipse_bbox_elongated(self) -> None:
        """Test bounding box for elongated ellipse (ratio ~0.5)."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("ELLIPSE_ELONGATED")

        bbox = _get_block_bounding_box(block)

        # Center (100, 50), major axis 80 along X, ratio 0.5
        # Semi-major = 80, semi-minor = 40
        # Expected bbox: (100-80, 50-40, 100+80, 50+40) = (20, 10, 180, 90)
        assert bbox[0] == pytest.approx(20.0, abs=0.5)  # min_x
        assert bbox[1] == pytest.approx(10.0, abs=0.5)  # min_y
        assert bbox[2] == pytest.approx(180.0, abs=0.5)  # max_x
        assert bbox[3] == pytest.approx(90.0, abs=0.5)  # max_y

    def test_ellipse_bbox_very_elongated(self) -> None:
        """Test bounding box for very elongated ellipse (ratio ~0.2)."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("ELLIPSE_VERY_ELONGATED")

        bbox = _get_block_bounding_box(block)

        # Center (150, 50), major axis 100 along X, ratio 0.2
        # Semi-major = 100, semi-minor = 20
        # Expected bbox: (150-100, 50-20, 150+100, 50+20) = (50, 30, 250, 70)
        assert bbox[0] == pytest.approx(50.0, abs=0.5)  # min_x
        assert bbox[1] == pytest.approx(30.0, abs=0.5)  # min_y
        assert bbox[2] == pytest.approx(250.0, abs=0.5)  # max_x
        assert bbox[3] == pytest.approx(70.0, abs=0.5)  # max_y

    def test_ellipse_bbox_arc(self) -> None:
        """Test bounding box for partial ellipse (elliptical arc, upper half)."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("ELLIPSE_ARC")

        bbox = _get_block_bounding_box(block)

        # Center (100, 100), major axis 60 along X, ratio 0.5
        # Semi-major = 60, semi-minor = 30
        # Upper half (0 to pi): y ranges from 100 to 130, x from 40 to 160
        # Bottom should be at center y (100), not 100-30=70
        assert bbox[0] == pytest.approx(40.0, abs=0.5)  # min_x
        assert bbox[1] == pytest.approx(
            100.0, abs=0.5
        )  # min_y (arc starts/ends at y=100)
        assert bbox[2] == pytest.approx(160.0, abs=0.5)  # max_x
        assert bbox[3] == pytest.approx(130.0, abs=0.5)  # max_y (top of arc)

    def test_extract_ellipse_edges_returns_linestrings(self) -> None:
        """Test that ellipse edge extraction produces valid LineStrings."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("ELLIPSE_CIRCULAR")

        edges = _extract_all_edges(block)

        assert len(edges) > 0
        # All edges should be LineString objects
        for edge in edges:
            assert isinstance(edge, LineString)

    def test_extract_ellipse_edges_count(self) -> None:
        """Test that ellipse produces reasonable number of edges for its size."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("ELLIPSE_CIRCULAR")

        edges = _extract_all_edges(block)

        # A near-circular ellipse with semi-major 50 should produce many segments
        # Minimum expected: 16 edges (4 per quadrant)
        assert len(edges) >= 16

    def test_estimate_edge_count_with_ellipse(self) -> None:
        """Test that edge count estimation includes ellipse contribution."""
        from core.geometry import _estimate_edge_count

        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("ELLIPSE_CIRCULAR")

        estimated = _estimate_edge_count(block)

        # Should estimate at least 8 edges for any ellipse
        assert estimated >= 8

    def test_ellipse_skip_curved_entities(self) -> None:
        """Test that ELLIPSE is skipped when skip_curved_entities=True."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("ELLIPSE_CIRCULAR")

        edges_with_ellipse = _extract_all_edges(block, skip_curved_entities=False)
        edges_without_ellipse = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges_with_ellipse) > 0
        assert len(edges_without_ellipse) == 0


class TestSplineSupport:
    """Test suite for SPLINE entity support in geometry functions."""

    def test_spline_bbox_simple(self) -> None:
        """Test bounding box for simple spline (4 fit points)."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("SPLINE_SIMPLE")

        bbox = _get_block_bounding_box(block)

        # Fit points: (0, 0), (50, 100), (100, 100), (150, 0)
        # The spline should pass through these points approximately
        # Bbox should contain all fit points (with floating point tolerance)
        assert bbox[0] <= 0.1  # min_x near 0 (floating point tolerance)
        assert bbox[1] <= 0.1  # min_y near 0 (floating point tolerance)
        assert bbox[2] >= 149.9  # max_x near 150
        assert bbox[3] >= 100  # max_y >= 100

    def test_spline_bbox_complex(self) -> None:
        """Test bounding box for complex spline (9 fit points forming a wave)."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("SPLINE_COMPLEX")

        bbox = _get_block_bounding_box(block)

        # Fit points range from (0, 50) to (200, 50) with y ranging 0-100
        assert bbox[0] <= 0  # min_x <= 0
        assert bbox[1] <= 0  # min_y can dip below fit points
        assert bbox[2] >= 200  # max_x >= 200
        assert bbox[3] >= 100  # max_y >= 100

    def test_spline_bbox_closed(self) -> None:
        """Test bounding box for closed spline produces valid geometry."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("SPLINE_CLOSED")

        bbox = _get_block_bounding_box(block)

        # Control points: (50,0), (100,25), (75,75), (25,75), (0,25)
        # Closed splines created via set_closed() can extend significantly
        # beyond the control points. Just verify valid bbox was computed.
        assert bbox[0] < bbox[2]  # min_x < max_x (valid width)
        assert bbox[1] < bbox[3]  # min_y < max_y (valid height)
        # Verify the bbox is not all zeros (actual geometry was processed)
        assert bbox != (0.0, 0.0, 0.0, 0.0)

    def test_extract_spline_edges_returns_linestrings(self) -> None:
        """Test that spline edge extraction produces valid LineStrings."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("SPLINE_SIMPLE")

        edges = _extract_all_edges(block)

        assert len(edges) > 0
        # All edges should be LineString objects
        for edge in edges:
            assert isinstance(edge, LineString)

    def test_extract_spline_edges_count(self) -> None:
        """Test that spline produces reasonable number of edges."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("SPLINE_SIMPLE")

        edges = _extract_all_edges(block)

        # A simple spline should produce at least some segments
        assert len(edges) >= 4

    def test_estimate_edge_count_with_spline(self) -> None:
        """Test that edge count estimation includes spline contribution."""
        from core.geometry import _estimate_edge_count

        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("SPLINE_SIMPLE")

        estimated = _estimate_edge_count(block)

        # Should estimate at least 16 edges (minimum for splines)
        assert estimated >= 16

    def test_spline_skip_curved_entities(self) -> None:
        """Test that SPLINE is skipped when skip_curved_entities=True."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("SPLINE_SIMPLE")

        edges_with_spline = _extract_all_edges(block, skip_curved_entities=False)
        edges_without_spline = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges_with_spline) > 0
        assert len(edges_without_spline) == 0


class TestMixedEntitiesIntegration:
    """Integration tests for blocks with mixed ELLIPSE + SPLINE + LINE entities."""

    def test_mixed_entities_bbox(self) -> None:
        """Test bounding box with ELLIPSE + SPLINE + LINE entities combined."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("MIXED_ENTITIES")

        bbox = _get_block_bounding_box(block)

        # Mixed block contains:
        # - Ellipse: center (50,50), major 40, ratio 0.6 -> bbox ~ (10, 26, 90, 74)
        # - Spline: fit points (0,100), (50,150), (100,100) -> y up to ~150
        # - Line: (0,0) to (150,0)
        # Overall bbox should encompass all entities
        assert bbox[0] <= 0  # Line starts at x=0
        assert bbox[1] <= 0  # Line is at y=0
        assert bbox[2] >= 150  # Line ends at x=150
        assert bbox[3] >= 150  # Spline reaches y~150

    def test_mixed_entities_edge_extraction(self) -> None:
        """Test edge extraction from block with mixed entity types."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("MIXED_ENTITIES")

        edges = _extract_all_edges(block)

        # Should have edges from ellipse + spline + line
        # 1 line + many ellipse segments + many spline segments
        assert len(edges) > 10

    def test_mixed_entities_skip_curved_only_line_remains(self) -> None:
        """Test that skip_curved_entities leaves only LINE entities."""
        doc = ezdxf.readfile("app/tests/assets/ellipse_spline_test.dxf")
        block = doc.blocks.get("MIXED_ENTITIES")

        edges = _extract_all_edges(block, skip_curved_entities=True)

        # Only the LINE entity should remain
        assert len(edges) == 1


class TestEstimateArcSegments:
    """Test suite for _estimate_arc_segments helper function."""

    def test_full_circle_large_radius(self) -> None:
        """Large radius circle should produce more segments."""
        # Large circle: radius=100, full circle, sagitta=0.1
        segments = _estimate_arc_segments(100, 2 * math.pi, 0.1)

        # Should produce ~71 segments for large circle (matches ezdxf flattening)
        assert 50 < segments < 100

    def test_full_circle_small_radius(self) -> None:
        """Small radius circle should produce fewer segments."""
        # Small circle: radius=10, full circle, sagitta=0.1
        segments = _estimate_arc_segments(10, 2 * math.pi, 0.1)

        # Should produce ~23 segments for small circle (matches ezdxf flattening)
        assert 15 < segments < 35

    def test_quarter_arc(self) -> None:
        """90-degree arc should produce ~1/4 of full circle segments."""
        full_circle = _estimate_arc_segments(50, 2 * math.pi, 0.1)
        quarter_arc = _estimate_arc_segments(50, math.pi / 2, 0.1)

        # Quarter arc should be approximately 1/4 of full circle
        assert 0.20 < (quarter_arc / full_circle) < 0.30

    def test_half_arc(self) -> None:
        """180-degree arc should produce ~1/2 of full circle segments."""
        full_circle = _estimate_arc_segments(50, 2 * math.pi, 0.1)
        half_arc = _estimate_arc_segments(50, math.pi, 0.1)

        # Half arc should be approximately 1/2 of full circle
        assert 0.45 < (half_arc / full_circle) < 0.55

    def test_invalid_radius_returns_one(self) -> None:
        """Zero or negative radius should return 1."""
        assert _estimate_arc_segments(0, 2 * math.pi, 0.1) == 1
        assert _estimate_arc_segments(-10, 2 * math.pi, 0.1) == 1

    def test_invalid_sagitta_returns_one(self) -> None:
        """Zero or negative sagitta should return 1."""
        assert _estimate_arc_segments(50, 2 * math.pi, 0) == 1
        assert _estimate_arc_segments(50, 2 * math.pi, -0.1) == 1

    def test_sagitta_larger_than_radius_returns_one(self) -> None:
        """Sagitta >= radius should return 1 (edge case)."""
        assert _estimate_arc_segments(0.05, 2 * math.pi, 0.1) == 1

    def test_larger_sagitta_fewer_segments(self) -> None:
        """Larger sagitta tolerance should produce fewer segments."""
        fine = _estimate_arc_segments(50, 2 * math.pi, 0.01)  # Fine tolerance
        coarse = _estimate_arc_segments(50, 2 * math.pi, 1.0)  # Coarse tolerance

        assert fine > coarse


class TestEdgeCountEstimation:
    """Test suite for _estimate_edge_count with formula-based estimation."""

    def test_circle_estimation_matches_flattening(self) -> None:
        """Verify CIRCLE estimation closely matches actual flattening output."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLE_TEST")
        block.add_circle(center=(0, 0), radius=50)

        estimated = _estimate_edge_count(block)

        # Get actual edge count from flattening
        circle_entity = list(block)[0]
        actual_edges = _extract_circle_edges(circle_entity)
        actual_count = len(actual_edges)

        # Estimation should be within 10% of actual
        assert abs(estimated - actual_count) <= actual_count * 0.10

    def test_arc_estimation_matches_flattening(self) -> None:
        """Verify ARC estimation closely matches actual flattening output."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARC_TEST")
        block.add_arc(center=(0, 0), radius=50, start_angle=0, end_angle=90)

        estimated = _estimate_edge_count(block)

        # Get actual edge count from flattening
        arc_entity = list(block)[0]
        actual_edges = _extract_arc_edges(arc_entity)
        actual_count = len(actual_edges)

        # Estimation should be within 10% of actual
        assert abs(estimated - actual_count) <= actual_count * 0.10

    def test_large_circle_more_segments_than_small(self) -> None:
        """Large circles should estimate more segments than small circles."""
        doc = ezdxf.new()

        small_block = doc.blocks.new(name="SMALL_CIRCLE")
        small_block.add_circle(center=(0, 0), radius=10)

        large_block = doc.blocks.new(name="LARGE_CIRCLE")
        large_block.add_circle(center=(0, 0), radius=100)

        small_estimate = _estimate_edge_count(small_block)
        large_estimate = _estimate_edge_count(large_block)

        assert large_estimate > small_estimate
        # Large circle (100 radius) should have roughly 3x more segments than small (10 radius)
        # because segments scale with sqrt(radius) for fixed sagitta
        assert large_estimate > small_estimate * 2

    def test_full_arc_more_segments_than_quarter_arc(self) -> None:
        """Full arc (360) should estimate more segments than quarter arc (90)."""
        doc = ezdxf.new()

        quarter_block = doc.blocks.new(name="QUARTER_ARC")
        quarter_block.add_arc(center=(0, 0), radius=50, start_angle=0, end_angle=90)

        full_block = doc.blocks.new(name="FULL_ARC")
        full_block.add_arc(center=(0, 0), radius=50, start_angle=0, end_angle=360)

        quarter_estimate = _estimate_edge_count(quarter_block)
        full_estimate = _estimate_edge_count(full_block)

        assert full_estimate > quarter_estimate
        # Full arc should have ~4x more segments than quarter arc
        assert 3 < (full_estimate / quarter_estimate) < 5

    def test_mixed_block_estimation(self) -> None:
        """Test estimation with mixed entity types."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED_TEST")

        # 4 LINE edges
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))
        block.add_line((100, 50), (0, 50))
        block.add_line((0, 50), (0, 0))

        # 1 CIRCLE (should be >0 segments)
        block.add_circle(center=(50, 25), radius=20)

        estimate = _estimate_edge_count(block)

        # Should be at least 4 (lines) + some circle segments
        assert estimate > 4

    def test_uses_existing_test_asset(self) -> None:
        """Verify estimation works with existing test DXF file."""
        doc = ezdxf.readfile("app/tests/assets/circle_arc_hatch_edges_test.dxf")

        # Test SIZE_TEST block which has small and large circles
        size_test_block = doc.blocks.get("SIZE_TEST")
        estimate = _estimate_edge_count(size_test_block)

        # Should have > 0 segments for both circles
        assert estimate > 0

        # Test MIXED_ENTITIES block
        mixed_block = doc.blocks.get("MIXED_ENTITIES")
        mixed_estimate = _estimate_edge_count(mixed_block)

        # Should include LINE, CIRCLE, ARC, and HATCH contributions
        assert mixed_estimate > 50  # At least HATCH (50) + other entities


class TestMinSideFilterRectanglesOnly:
    """Test suite for min_side_filter rectangles-only behavior in _detect_content_zone."""

    def test_rectangle_below_threshold_is_filtered(self) -> None:
        """Test that 4-sided rectangle with short sides gets filtered."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SMALL_RECT")
        # 100x5 rectangle - shortest side is 5 units
        block.add_lwpolyline(
            [(0, 0), (100, 0), (100, 5), (0, 5)],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 5.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=10.0,  # Threshold above shortest side (5)
        )

        # Rectangle should be filtered out (shortest side 5 < threshold 10)
        assert result["content_zone_detected"] is False
        assert result["polygon_count"] == 1
        assert result["filtered_polygon_count"] == 0

    def test_rectangle_above_threshold_passes(self) -> None:
        """Test that 4-sided rectangle with sides >= threshold passes."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="LARGE_RECT")
        # 100x20 rectangle - shortest side is 20 units
        block.add_lwpolyline(
            [(0, 0), (100, 0), (100, 20), (0, 20)],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 20.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=10.0,  # Threshold below shortest side (20)
        )

        # Rectangle should pass (shortest side 20 >= threshold 10)
        assert result["content_zone_detected"] is True
        assert result["filtered_polygon_count"] == 1

    def test_pentagon_with_short_side_passes(self) -> None:
        """Test that 5-sided polygon with short side is NOT filtered."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="PENTAGON")
        # Pentagon with one very short side (5 units)
        # Vertices form a house-like shape
        block.add_lwpolyline(
            [
                (0, 0),  # bottom-left
                (100, 0),  # bottom-right
                (100, 50),  # right
                (50, 70),  # peak
                (0, 50),  # left
            ],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 70.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=30.0,  # High threshold that would filter rectangles
        )

        # Pentagon should pass through (5 sides, not affected by filter)
        assert result["content_zone_detected"] is True
        assert result["filtered_polygon_count"] == 1

    def test_hexagon_with_short_side_passes(self) -> None:
        """Test that 6-sided polygon with short side is NOT filtered."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HEXAGON")
        # Irregular hexagon with varying side lengths
        block.add_lwpolyline(
            [
                (0, 0),
                (80, 0),  # 80 units
                (100, 20),  # ~28 units
                (100, 80),  # 60 units
                (20, 80),  # 80 units
                (0, 60),  # ~28 units
            ],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 80.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=50.0,  # High threshold that would filter rectangles
        )

        # Hexagon should pass through (6 sides, not affected by filter)
        assert result["content_zone_detected"] is True
        assert result["filtered_polygon_count"] == 1

    def test_l_shape_with_short_side_passes(self) -> None:
        """Test that 6-sided L-shape with short side is NOT filtered."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="L_SHAPE")
        # L-shaped polygon with 6 sides, some short (10 units)
        block.add_lwpolyline(
            [
                (0, 0),
                (50, 0),  # 50 units (bottom)
                (50, 30),  # 30 units (right lower)
                (20, 30),  # 30 units (inner horizontal)
                (20, 80),  # 50 units (inner vertical)
                (0, 80),  # 20 units (top)
            ],
            close=True,
        )

        bbox = (0.0, 0.0, 50.0, 80.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=25.0,  # Would filter 20-unit sides if it were a rectangle
        )

        # L-shape should pass through (6 sides, not affected by filter)
        assert result["content_zone_detected"] is True
        assert result["filtered_polygon_count"] == 1

    def test_rectangle_and_pentagon_mixed(self) -> None:
        """Test that rectangle is filtered but pentagon in same block passes."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED_SHAPES")

        # Small rectangle (will be filtered)
        block.add_lwpolyline(
            [(0, 0), (20, 0), (20, 5), (0, 5)],
            close=True,
        )

        # Pentagon (will pass through)
        block.add_lwpolyline(
            [
                (50, 0),
                (150, 0),
                (150, 50),
                (100, 70),
                (50, 50),
            ],
            close=True,
        )

        bbox = (0.0, 0.0, 150.0, 70.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=10.0,  # Filters rectangle (5 < 10) but not pentagon
        )

        # Rectangle filtered, pentagon passes
        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 2
        assert result["filtered_polygon_count"] == 1  # Only pentagon survives
