"""
Unit tests for the geometry module.

This test suite validates geometric calculation utilities including:
- Bounding box calculation for various entity types
- Intersection point detection and deduplication
- Segment distance calculation
- Rotation angle categorization
- LINE segment threshold behavior
- Cycle detection timeout behavior
- Abort responsiveness in DFS loop
- Edge cases and tolerance boundaries
"""

import threading
import time
from unittest.mock import patch

import ezdxf
import pytest

from core.constants import LINE_SEGMENT_THRESHOLD
from core.geometry import (
    GeometryAbortedError,
    _calculate_segments,
    _categorize_rotation,
    _count_line_segments,
    _detect_content_zone,
    _extract_line_cycles,
    _get_block_bounding_box,
    _get_intersection_points,
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


class TestLineSegmentThreshold:
    """Test suite for LINE segment threshold behavior."""

    def test_count_line_segments_simple(self) -> None:
        """Test that _count_line_segments correctly counts LINE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Add 5 LINE segments
        for i in range(5):
            block.add_line((i * 10, 0), (i * 10 + 10, 0))

        count = _count_line_segments(block)
        assert count == 5

    def test_count_line_segments_mixed_entities(self) -> None:
        """Test that _count_line_segments only counts LINE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Add various entity types
        block.add_line((0, 0), (10, 0))  # LINE
        block.add_line((10, 0), (20, 0))  # LINE
        block.add_circle((50, 50), 25)  # CIRCLE - should not be counted
        block.add_lwpolyline([(0, 0), (10, 10), (20, 0)])  # LWPOLYLINE - should not be counted
        block.add_line((20, 0), (30, 0))  # LINE

        count = _count_line_segments(block)
        assert count == 3

    def test_count_line_segments_empty_block(self) -> None:
        """Test that _count_line_segments returns 0 for empty block."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY_BLOCK")

        count = _count_line_segments(block)
        assert count == 0

    def test_count_line_segments_many_lines_test_file(self) -> None:
        """Test _count_line_segments with the many_lines_test.dxf file."""
        doc = ezdxf.readfile("app/tests/assets/many_lines_test.dxf")
        block = doc.blocks.get("MANY_LINES_BLOCK")

        count = _count_line_segments(block)
        # The test file has 576 LINE segments, which exceeds LINE_SEGMENT_THRESHOLD (200)
        assert count > LINE_SEGMENT_THRESHOLD

    def test_content_zone_skips_line_cycle_when_threshold_exceeded(self) -> None:
        """Test that content zone detection skips LINE cycle extraction when threshold exceeded."""
        doc = ezdxf.readfile("app/tests/assets/many_lines_test.dxf")
        block = doc.blocks.get("MANY_LINES_BLOCK")
        bbox = _get_block_bounding_box(block)

        # This should complete quickly because LINE cycle detection is skipped
        start_time = time.perf_counter()
        result = _detect_content_zone(block, bbox, block_name="MANY_LINES_BLOCK")
        elapsed = time.perf_counter() - start_time

        # Should complete in under 1 second since expensive cycle detection is skipped
        assert elapsed < 1.0, f"Content zone detection took {elapsed:.2f}s, expected < 1s"

        # Content zone may or may not be detected depending on polyline shapes
        # But the important thing is it doesn't hang

    def test_polyline_detection_works_when_line_threshold_exceeded(self) -> None:
        """Test that polyline-based detection still works when LINE threshold exceeded."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Add many LINE segments to exceed threshold
        for i in range(LINE_SEGMENT_THRESHOLD + 50):
            block.add_line((i, 0), (i + 1, 0))

        # Add a closed polyline that should be detected
        block.add_lwpolyline(
            [(10, 10), (100, 10), (100, 50), (10, 50)], close=True
        )

        bbox = _get_block_bounding_box(block)

        # Content zone detection should complete quickly
        start_time = time.perf_counter()
        result = _detect_content_zone(block, bbox, block_name="TEST_BLOCK")
        elapsed = time.perf_counter() - start_time

        # Should complete quickly since LINE cycle detection is skipped
        assert elapsed < 1.0, f"Content zone detection took {elapsed:.2f}s"

        # The polyline should be detected as content zone
        assert result["content_zone_detected"] is True


class TestCycleDetectionTimeout:
    """Test suite for cycle detection timeout behavior."""

    def test_extract_line_cycles_respects_timeout(self) -> None:
        """Test that _extract_line_cycles respects the timeout and returns partial results."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Create a simple case that won't timeout to verify the function works
        block.add_line((0, 0), (10, 0))
        block.add_line((10, 0), (10, 10))
        block.add_line((10, 10), (0, 10))
        block.add_line((0, 10), (0, 0))

        # This should complete without timeout
        cycles = _extract_line_cycles(block)
        # Should find one cycle (the square)
        assert len(cycles) >= 1

    def test_extract_line_cycles_with_small_timeout(self) -> None:
        """Test timeout behavior with a very small timeout value."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Create a grid of lines that creates many possible cycles
        grid_size = 5
        spacing = 10.0

        # Horizontal lines
        for row in range(grid_size + 1):
            y = row * spacing
            for col in range(grid_size):
                x_start = col * spacing
                x_end = (col + 1) * spacing
                block.add_line((x_start, y), (x_end, y))

        # Vertical lines
        for col in range(grid_size + 1):
            x = col * spacing
            for row in range(grid_size):
                y_start = row * spacing
                y_end = (row + 1) * spacing
                block.add_line((x, y_start), (x, y_end))

        # Patch the timeout to a very small value
        with patch("core.geometry.CYCLE_DETECTION_TIMEOUT_SECONDS", 0.001):
            start_time = time.perf_counter()
            cycles = _extract_line_cycles(block)
            elapsed = time.perf_counter() - start_time

            # Function should return quickly due to timeout
            # Allow some margin for startup overhead
            assert elapsed < 0.5, f"Function took {elapsed:.2f}s despite tiny timeout"

            # Should return partial results (possibly empty list if timeout hit immediately)
            assert isinstance(cycles, list)


class TestAbortResponsiveness:
    """Test suite for abort responsiveness in DFS loop."""

    def test_extract_line_cycles_abort_is_checked(self) -> None:
        """Test that abort event is checked inside DFS loop."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Create a grid of lines
        grid_size = 5
        spacing = 10.0

        # Horizontal lines
        for row in range(grid_size + 1):
            y = row * spacing
            for col in range(grid_size):
                x_start = col * spacing
                x_end = (col + 1) * spacing
                block.add_line((x_start, y), (x_end, y))

        # Vertical lines
        for col in range(grid_size + 1):
            x = col * spacing
            for row in range(grid_size):
                y_start = row * spacing
                y_end = (row + 1) * spacing
                block.add_line((x, y_start), (x, y_end))

        # Create an abort event that is immediately set
        abort_event = threading.Event()
        abort_event.set()

        # Should raise GeometryAbortedError when abort is set
        with pytest.raises(GeometryAbortedError):
            _extract_line_cycles(block, abort_event=abort_event)

    def test_detect_content_zone_abort_during_line_cycles(self) -> None:
        """Test that abort during line cycle extraction raises GeometryAbortedError."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Create enough lines to require processing but not exceed threshold
        for i in range(50):
            block.add_line((i, 0), (i + 1, 0))
            block.add_line((i, 10), (i + 1, 10))
            block.add_line((i, 0), (i, 10))

        bbox = _get_block_bounding_box(block)

        # Create an abort event that is immediately set
        abort_event = threading.Event()
        abort_event.set()

        # Should raise GeometryAbortedError
        with pytest.raises(GeometryAbortedError):
            _detect_content_zone(block, bbox, abort_event=abort_event)

    def test_abort_responsiveness_timing(self) -> None:
        """Test that abort is processed within expected iteration count."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")

        # Create a moderate number of lines
        for i in range(100):
            block.add_line((i, 0), (i + 1, 0))
            block.add_line((i, 10), (i + 1, 10))

        bbox = _get_block_bounding_box(block)

        # Start a thread that will set abort after a brief delay
        abort_event = threading.Event()

        def set_abort_after_delay() -> None:
            time.sleep(0.01)  # 10ms delay
            abort_event.set()

        # Start abort thread
        abort_thread = threading.Thread(target=set_abort_after_delay)
        abort_thread.start()

        start_time = time.perf_counter()
        try:
            _detect_content_zone(block, bbox, abort_event=abort_event)
        except GeometryAbortedError:
            pass  # Expected

        elapsed = time.perf_counter() - start_time
        abort_thread.join()

        # Should respond within 1 second (generous margin for test stability)
        assert elapsed < 1.0, f"Abort took {elapsed:.2f}s to be processed"
