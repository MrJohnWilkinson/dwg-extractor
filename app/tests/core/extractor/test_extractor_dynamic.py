"""
Unit tests for the extractor module - dynamic block extraction functionality.

This module contains tests for dynamic block extraction and anonymous block resolution.
"""

import ezdxf
import pytest

from core.extractor import extract_blocks


class TestDynamicBlockExtraction:
    """Test suite for dynamic block extraction and anonymous block resolution."""

    def test_extraction_issues_key_exists(self) -> None:
        """Test that extraction_issues key exists in extraction result."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        assert "extraction_issues" in result
        assert isinstance(result["extraction_issues"], list)

    def test_extraction_issues_empty_for_regular_files(self) -> None:
        """Test that extraction_issues is empty for files without anonymous blocks."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Regular DXF files should have no extraction issues
        assert len(result["extraction_issues"]) == 0

    def test_dynamic_block_resolution_with_xdata(self) -> None:
        """Test that anonymous blocks with AcDbBlockRepBTag XDATA are resolved."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        # DOOR_DYNAMIC should appear from resolved *U1 blocks
        assert "DOOR_DYNAMIC" in result["block_counts"]
        # *U1 insertions = 4 (3 on LAYER_A, 1 on LAYER_B)
        assert result["block_counts"]["DOOR_DYNAMIC"] == 4

        # WINDOW_DYNAMIC should appear from resolved *U2 blocks
        assert "WINDOW_DYNAMIC" in result["block_counts"]
        # *U2 insertions = 3 (1 on LAYER_A, 2 on LAYER_B)
        assert result["block_counts"]["WINDOW_DYNAMIC"] == 3

    def test_dynamic_block_resolution_preserves_regular_blocks(self) -> None:
        """Test that regular (non-anonymous) blocks are still extracted correctly."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        # REGULAR_BLOCK should still be counted normally
        assert "REGULAR_BLOCK" in result["block_counts"]
        assert result["block_counts"]["REGULAR_BLOCK"] == 3

    def test_unresolved_anonymous_blocks_reported(self) -> None:
        """Test that unresolved anonymous blocks appear in extraction_issues."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        # *U3 has no XDATA, should be in extraction_issues
        extraction_issues = result["extraction_issues"]
        assert len(extraction_issues) > 0

        # Find issues for *U3
        u3_issues = [
            issue for issue in extraction_issues if issue["block_name"] == "*U3"
        ]
        assert len(u3_issues) >= 1

        # Verify issue structure
        for issue in u3_issues:
            assert issue["issue_type"] == "Unresolved Anonymous Block"
            assert issue["block_name"] == "*U3"
            assert issue["layer_name"] in ("LAYER_A", "LAYER_B")
            assert issue["insertion_count"] > 0
            assert "AcDbBlockRepBTag" in issue["details"]

    def test_unresolved_anonymous_blocks_by_layer(self) -> None:
        """Test that unresolved anonymous blocks are tracked per layer."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        extraction_issues = result["extraction_issues"]
        u3_issues = [
            issue for issue in extraction_issues if issue["block_name"] == "*U3"
        ]

        # Should have separate entries for each layer
        layers_with_issues = {issue["layer_name"] for issue in u3_issues}
        assert "LAYER_A" in layers_with_issues
        assert "LAYER_B" in layers_with_issues

        # Verify counts per layer
        layer_a_issue = next(
            (i for i in u3_issues if i["layer_name"] == "LAYER_A"), None
        )
        layer_b_issue = next(
            (i for i in u3_issues if i["layer_name"] == "LAYER_B"), None
        )

        assert layer_a_issue is not None
        assert layer_b_issue is not None
        # *U3 has 2 insertions on LAYER_A, 3 on LAYER_B
        assert layer_a_issue["insertion_count"] == 2
        assert layer_b_issue["insertion_count"] == 3

    def test_extraction_issues_sorted_by_count(self) -> None:
        """Test that extraction_issues are sorted by insertion_count descending."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        extraction_issues = result["extraction_issues"]
        if len(extraction_issues) > 1:
            # Verify sorting - highest count first
            counts = [issue["insertion_count"] for issue in extraction_issues]
            assert counts == sorted(counts, reverse=True)

    def test_resolved_blocks_not_in_extraction_issues(self) -> None:
        """Test that successfully resolved blocks don't appear in extraction_issues."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        extraction_issues = result["extraction_issues"]

        # *U1 and *U2 were resolved, should not be in issues
        issue_block_names = {issue["block_name"] for issue in extraction_issues}
        assert "*U1" not in issue_block_names
        assert "*U2" not in issue_block_names

    def test_resolved_blocks_in_block_layer_pairs(self) -> None:
        """Test that resolved dynamic blocks appear in block_layer_pairs."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        # Find DOOR_DYNAMIC entries in block_layer_pairs
        door_pairs = [
            key
            for key in result["block_layer_pairs"].keys()
            if key.block_name == "DOOR_DYNAMIC"
        ]
        assert len(door_pairs) >= 1

        # Verify both layers have DOOR_DYNAMIC entries
        door_layers = {key.layer_name for key in door_pairs}
        assert "LAYER_A" in door_layers
        assert "LAYER_B" in door_layers

    def test_resolved_blocks_have_geometry_data(self) -> None:
        """Test that resolved dynamic blocks have geometry/trimming data."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        # Resolved blocks should have geometry data
        assert "DOOR_DYNAMIC" in result["block_trimming_data"]
        assert "WINDOW_DYNAMIC" in result["block_trimming_data"]

        # Verify geometry data structure
        door_geometry = result["block_trimming_data"]["DOOR_DYNAMIC"]
        assert "native_width" in door_geometry
        assert "native_height" in door_geometry

    def test_extraction_issue_structure(self) -> None:
        """Test that ExtractionIssue TypedDict has all required fields."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        extraction_issues = result["extraction_issues"]
        assert len(extraction_issues) > 0

        for issue in extraction_issues:
            # Verify all required fields exist
            assert "issue_type" in issue
            assert "block_name" in issue
            assert "layer_name" in issue
            assert "insertion_count" in issue
            assert "details" in issue

            # Verify field types
            assert isinstance(issue["issue_type"], str)
            assert isinstance(issue["block_name"], str)
            assert isinstance(issue["layer_name"], str)
            assert isinstance(issue["insertion_count"], int)
            assert isinstance(issue["details"], str)

    def test_anonymous_blocks_not_in_block_counts(self) -> None:
        """Test that unresolved anonymous block names don't appear in block_counts."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        # *U3 was not resolved, should not be in block_counts
        assert "*U3" not in result["block_counts"]

        # *U1 and *U2 were resolved to different names, originals shouldn't be there
        assert "*U1" not in result["block_counts"]
        assert "*U2" not in result["block_counts"]

    def test_total_insertions_conservation(self) -> None:
        """Test that total block insertions are conserved after resolution."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        # Count all tracked insertions
        resolved_count = sum(result["block_counts"].values())

        # Count unresolved insertions
        unresolved_count = sum(
            issue["insertion_count"] for issue in result["extraction_issues"]
        )

        # Total should equal 15 (3 REGULAR + 4 *U1 + 3 *U2 + 5 *U3)
        total = resolved_count + unresolved_count
        assert total == 15
