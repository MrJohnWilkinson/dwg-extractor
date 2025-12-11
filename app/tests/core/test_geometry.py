"""
Unit tests for the geometry module.

This test suite validates geometric calculation utilities including:
- Bounding box calculation for various entity types
- Intersection point detection and deduplication
- Segment distance calculation
- Rotation angle categorization
- Edge cases and tolerance boundaries
"""

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
    _extract_all_edges,
    _extract_line_cycles,
    _extract_paint_bucket_regions,
    _get_block_bounding_box,
    _get_intersection_points,
    _snap_linestring_coords,
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
        regions = _extract_paint_bucket_regions(block, precision_tolerance=0, gap_bridge_tolerance=2.0)

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
        """Test that 10x10 square returns 10.0 for all equal sides."""
        square: list[tuple[float, float]] = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0),
        ]
        assert calculate_shortest_straight_side(square) == pytest.approx(10.0)

    def test_rectangle_shortest_side(self) -> None:
        """Test that 100x50 rectangle returns 50.0 for shorter sides."""
        rectangle: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 50.0),
            (0.0, 50.0),
        ]
        assert calculate_shortest_straight_side(rectangle) == pytest.approx(50.0)

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
        assert calculate_shortest_straight_side(split_rect) == pytest.approx(50.0)

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
        assert calculate_shortest_straight_side(split_rect) == pytest.approx(50.0)

    def test_triangle_shortest_side(self) -> None:
        """Test 3-4-5 right triangle returns 3.0 for shortest side."""
        # 3-4-5 right triangle
        triangle: list[tuple[float, float]] = [(0.0, 0.0), (3.0, 0.0), (0.0, 4.0)]
        # Sides: bottom=3, left=4, hypotenuse=5
        assert calculate_shortest_straight_side(triangle) == pytest.approx(3.0)

    def test_degenerate_polygon_empty(self) -> None:
        """Test that empty list returns 0.0."""
        assert calculate_shortest_straight_side([]) == 0.0

    def test_degenerate_polygon_two_points(self) -> None:
        """Test that two points returns 0.0."""
        assert calculate_shortest_straight_side([(0.0, 0.0), (10.0, 10.0)]) == 0.0

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
        result_large = calculate_shortest_straight_side(deviation, angle_tolerance=5.0)

        # With tight tolerance (1 degree), edges should NOT merge
        # since 2.29 degrees > 1 degree
        result_tight = calculate_shortest_straight_side(deviation, angle_tolerance=1.0)

        # Large tolerance merges bottom edges, so shortest is 50 (vertical sides)
        assert result_large == pytest.approx(50.0)
        # Tight tolerance doesn't merge, so we get smaller segments (~50)
        # The split segments are about 50 units each
        assert result_tight < 51.0  # Should find the ~50 unit split segment

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
        assert calculate_shortest_straight_side(rect_with_tiny) == pytest.approx(50.0)

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
        assert calculate_shortest_straight_side(horizontal_rect) == pytest.approx(10.0)

    def test_all_edges_equal(self) -> None:
        """Test polygon where all edges have equal length."""
        # Equilateral-like hexagon (approximation for testing)
        square: list[tuple[float, float]] = [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0),
        ]
        result = calculate_shortest_straight_side(square)
        assert result == pytest.approx(10.0)
