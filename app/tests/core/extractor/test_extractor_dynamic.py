"""
Unit tests for the extractor module - dynamic block extraction functionality.

This module contains tests for dynamic block extraction and anonymous block resolution,
including both *U (standard) and A$C (alternate) anonymous block naming conventions,
handle-based XDATA resolution (tag code 1005), and orphaned handle detection.
"""

from core.extractor import (
    _is_anonymous_block,
    _resolve_dynamic_block_name,
    extract_blocks,
)


class TestIsAnonymousBlock:
    """Test suite for the _is_anonymous_block helper function."""

    def test_star_u_blocks_detected(self) -> None:
        """Test that *U blocks are detected as anonymous."""
        assert _is_anonymous_block("*U1") is True
        assert _is_anonymous_block("*U25") is True
        assert _is_anonymous_block("*U999") is True

    def test_a_dollar_c_blocks_detected(self) -> None:
        """Test that A$C blocks are detected as anonymous."""
        assert _is_anonymous_block("A$C7F63364D") is True
        assert _is_anonymous_block("A$C25B30886") is True
        assert _is_anonymous_block("A$CABC12345") is True

    def test_regular_blocks_not_detected(self) -> None:
        """Test that regular blocks are not detected as anonymous."""
        assert _is_anonymous_block("DOOR") is False
        assert _is_anonymous_block("WINDOW_UNIT") is False
        assert _is_anonymous_block("MY_BLOCK_123") is False

    def test_system_blocks_not_detected(self) -> None:
        """Test that system blocks are not detected as anonymous dynamic blocks."""
        assert _is_anonymous_block("*Model_Space") is False
        assert _is_anonymous_block("*Paper_Space") is False
        assert _is_anonymous_block("*D1") is False  # Dimension blocks


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
            # *U3 has no XDATA, so should report "No XDATA found" or similar
            assert "XDATA" in issue["details"] or "No" in issue["details"]

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


class TestADollarCBlockExtraction:
    """Test suite for A$C anonymous block extraction and resolution."""

    def test_a_dollar_c_block_resolution_with_xdata(self) -> None:
        """Test that A$C blocks with AcDbBlockRepBTag XDATA are resolved."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        # SHELF_UNIT should appear from resolved A$C7F63364D blocks
        assert "SHELF_UNIT" in result["block_counts"]
        # A$C7F63364D insertions = 3 (2 on LAYER_A, 1 on LAYER_B)
        assert result["block_counts"]["SHELF_UNIT"] == 3

    def test_a_dollar_c_block_unresolved_uses_raw_name(self) -> None:
        """Test that unresolved A$C blocks appear in block_counts with raw name."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        # Unresolved A$C blocks should appear with raw names
        # A$C25B30886 (self-referencing XDATA) = 2 insertions
        assert "A$C25B30886" in result["block_counts"]
        assert result["block_counts"]["A$C25B30886"] == 2

        # A$C0c1c4685 (no XDATA) = 4 insertions
        assert "A$C0c1c4685" in result["block_counts"]
        assert result["block_counts"]["A$C0c1c4685"] == 4

        # A$CABC12345 (GUID-only XDATA) = 3 insertions
        assert "A$CABC12345" in result["block_counts"]
        assert result["block_counts"]["A$CABC12345"] == 3

    def test_a_dollar_c_block_unresolved_in_extraction_issues(self) -> None:
        """Test that unresolved A$C blocks are tracked in extraction_issues."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        extraction_issues = result["extraction_issues"]

        # Find issues for unresolved A$C blocks
        a_dollar_c_issues = [
            issue
            for issue in extraction_issues
            if issue["block_name"].startswith("A$C")
        ]

        # Should have issues for A$C25B30886, A$C0c1c4685, and A$CABC12345
        issue_block_names = {issue["block_name"] for issue in a_dollar_c_issues}
        assert "A$C25B30886" in issue_block_names
        assert "A$C0c1c4685" in issue_block_names
        assert "A$CABC12345" in issue_block_names

        # Verify each issue has meaningful details and correct issue type
        for issue in a_dollar_c_issues:
            # Details should explain why resolution failed (XDATA-related message)
            assert "XDATA" in issue["details"] or "Self-referencing" in issue["details"]
            assert issue["issue_type"] == "Unresolved Anonymous Block"

    def test_a_dollar_c_resolved_not_in_extraction_issues(self) -> None:
        """Test that resolved A$C blocks don't appear in extraction_issues."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        extraction_issues = result["extraction_issues"]
        issue_block_names = {issue["block_name"] for issue in extraction_issues}

        # A$C7F63364D was resolved to SHELF_UNIT, should not be in issues
        assert "A$C7F63364D" not in issue_block_names

    def test_a_dollar_c_block_in_block_layer_pairs(self) -> None:
        """Test that A$C blocks appear in block_layer_pairs correctly."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        # Find SHELF_UNIT (resolved from A$C7F63364D) entries
        shelf_pairs = [
            key
            for key in result["block_layer_pairs"].keys()
            if key.block_name == "SHELF_UNIT"
        ]
        assert len(shelf_pairs) >= 1

        # Verify both layers have SHELF_UNIT entries
        shelf_layers = {key.layer_name for key in shelf_pairs}
        assert "LAYER_A" in shelf_layers
        assert "LAYER_B" in shelf_layers

        # Unresolved A$C blocks should also appear in block_layer_pairs with raw name
        a_dollar_c_pairs = [
            key
            for key in result["block_layer_pairs"].keys()
            if key.block_name == "A$C0c1c4685"
        ]
        assert len(a_dollar_c_pairs) >= 1

    def test_a_dollar_c_block_in_rotations(self) -> None:
        """Test that A$C blocks appear in rotation data."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        # Find rotation entries for SHELF_UNIT (resolved A$C)
        shelf_rotations = [
            key
            for key in result["block_rotation_counts"].keys()
            if key.block_name == "SHELF_UNIT"
        ]
        assert len(shelf_rotations) >= 1

        # Find rotation entries for unresolved A$C block with different rotations
        a_dollar_c_rotations = [
            key
            for key in result["block_rotation_counts"].keys()
            if key.block_name == "A$C0c1c4685"
        ]
        # A$C0c1c4685 has rotation 0 and 180 insertions
        rotation_categories = {key.rotation_category for key in a_dollar_c_rotations}
        assert "0" in rotation_categories
        assert "180" in rotation_categories

    def test_a_dollar_c_block_in_scales(self) -> None:
        """Test that A$C blocks appear in scale data."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        # SHELF_UNIT should have scale data (resolved from A$C7F63364D with xscale=2.0)
        assert "SHELF_UNIT" in result["block_scale_data"]
        shelf_scales = result["block_scale_data"]["SHELF_UNIT"]
        # Should have both (1.0, 1.0) and (2.0, 1.0) scale combinations
        assert (1.0, 1.0) in shelf_scales
        assert (2.0, 1.0) in shelf_scales

        # A$C0c1c4685 should have scale data (with xscale=-1.0)
        assert "A$C0c1c4685" in result["block_scale_data"]
        a_dollar_c_scales = result["block_scale_data"]["A$C0c1c4685"]
        assert (-1.0, 1.0) in a_dollar_c_scales

    def test_a_dollar_c_block_in_trimming_data(self) -> None:
        """Test that A$C blocks have geometry/trimming data."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        # Resolved A$C block should have geometry data
        assert "SHELF_UNIT" in result["block_trimming_data"]
        shelf_geometry = result["block_trimming_data"]["SHELF_UNIT"]
        assert "native_width" in shelf_geometry
        assert "native_height" in shelf_geometry
        assert shelf_geometry["native_width"] > 0

        # Unresolved A$C blocks should also have geometry data (unlike *U)
        assert "A$C0c1c4685" in result["block_trimming_data"]
        assert "A$C25B30886" in result["block_trimming_data"]
        assert "A$CABC12345" in result["block_trimming_data"]

    def test_a_dollar_c_preserves_regular_blocks(self) -> None:
        """Test that regular blocks are still extracted correctly with A$C file."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        # REGULAR_BLOCK should still be counted normally
        assert "REGULAR_BLOCK" in result["block_counts"]
        assert result["block_counts"]["REGULAR_BLOCK"] == 3

    def test_a_dollar_c_total_insertions_conservation(self) -> None:
        """Test that total block insertions include both resolved and unresolved A$C blocks."""
        result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")

        # Count all tracked insertions (includes unresolved A$C blocks)
        total_block_insertions = sum(result["block_counts"].values())

        # Expected: 3 REGULAR + 3 SHELF_UNIT + 2 A$C25B30886 + 4 A$C0c1c4685 + 3 A$CABC12345 = 15
        assert total_block_insertions == 15

    def test_a_dollar_c_vs_star_u_handling_difference(self) -> None:
        """Test the key difference: A$C unresolved appear in block_counts, *U unresolved don't."""
        # Test *U behavior
        u_result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")
        # *U3 is unresolved and should NOT be in block_counts
        assert "*U3" not in u_result["block_counts"]

        # Test A$C behavior
        a_result = extract_blocks("app/tests/assets/a_dollar_c_block_test.dxf")
        # Unresolved A$C blocks SHOULD be in block_counts
        assert "A$C25B30886" in a_result["block_counts"]
        assert "A$C0c1c4685" in a_result["block_counts"]
        assert "A$CABC12345" in a_result["block_counts"]


class TestDynamicBlockHandleResolution:
    """Test suite for dynamic block handle resolution via tag code 1005."""

    def test_handle_resolution_with_tag_1005(self) -> None:
        """Test that anonymous blocks with handle XDATA (tag 1005) are resolved."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        # DOOR_HANDLE_TEST should appear from resolved *U1 blocks via handle
        assert "DOOR_HANDLE_TEST" in result["block_counts"]
        # *U1 insertions = 3 (2 on LAYER_A, 1 on LAYER_B)
        assert result["block_counts"]["DOOR_HANDLE_TEST"] == 3

        # WINDOW_HANDLE_TEST should appear from resolved *U2 blocks via handle
        assert "WINDOW_HANDLE_TEST" in result["block_counts"]
        # *U2 insertions = 2 (1 on LAYER_A, 1 on LAYER_B)
        assert result["block_counts"]["WINDOW_HANDLE_TEST"] == 2

    def test_handle_resolution_invalid_handle(self) -> None:
        """Test graceful handling of invalid handles in XDATA."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        # *U3 has invalid handle, should be in extraction_issues
        extraction_issues = result["extraction_issues"]
        u3_issues = [
            issue for issue in extraction_issues if issue["block_name"] == "*U3"
        ]
        assert len(u3_issues) >= 1

        # Verify issue structure
        for issue in u3_issues:
            assert issue["issue_type"] == "Unresolved Anonymous Block"
            assert issue["block_name"] == "*U3"

        # *U3 should NOT be in block_counts (unresolved)
        assert "*U3" not in result["block_counts"]

    def test_handle_resolution_fallback_to_tag_1000(self) -> None:
        """Test that tag code 1000 (direct string) still works for backwards compatibility."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        # DIRECT_STRING_BLOCK should appear from *U4 which uses tag 1000
        assert "DIRECT_STRING_BLOCK" in result["block_counts"]
        # *U4 insertions = 4 (2 on LAYER_A, 2 on LAYER_B)
        assert result["block_counts"]["DIRECT_STRING_BLOCK"] == 4

    def test_handle_resolution_no_xdata(self) -> None:
        """Test that blocks without XDATA are reported as unresolved."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        # *U5 has no XDATA, should be in extraction_issues
        extraction_issues = result["extraction_issues"]
        u5_issues = [
            issue for issue in extraction_issues if issue["block_name"] == "*U5"
        ]
        assert len(u5_issues) >= 1

        # *U5 should NOT be in block_counts
        assert "*U5" not in result["block_counts"]

    def test_handle_resolved_blocks_in_block_layer_pairs(self) -> None:
        """Test that handle-resolved dynamic blocks appear in block_layer_pairs."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        # Find DOOR_HANDLE_TEST entries in block_layer_pairs
        door_pairs = [
            key
            for key in result["block_layer_pairs"].keys()
            if key.block_name == "DOOR_HANDLE_TEST"
        ]
        assert len(door_pairs) >= 1

        # Verify both layers have DOOR_HANDLE_TEST entries
        door_layers = {key.layer_name for key in door_pairs}
        assert "LAYER_A" in door_layers
        assert "LAYER_B" in door_layers

    def test_handle_resolved_blocks_have_geometry_data(self) -> None:
        """Test that handle-resolved dynamic blocks have geometry/trimming data."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        # Resolved blocks should have geometry data
        assert "DOOR_HANDLE_TEST" in result["block_trimming_data"]
        assert "WINDOW_HANDLE_TEST" in result["block_trimming_data"]

        # Verify geometry data structure
        door_geometry = result["block_trimming_data"]["DOOR_HANDLE_TEST"]
        assert "native_width" in door_geometry
        assert "native_height" in door_geometry
        assert door_geometry["native_width"] > 0

    def test_handle_resolution_total_insertions_conservation(self) -> None:
        """Test that total block insertions are conserved after handle resolution."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        # Count all tracked insertions
        resolved_count = sum(result["block_counts"].values())

        # Count unresolved insertions
        unresolved_count = sum(
            issue["insertion_count"] for issue in result["extraction_issues"]
        )

        # Total should equal 16:
        # 2 REGULAR + 3 DOOR_HANDLE_TEST + 2 WINDOW_HANDLE_TEST + 4 DIRECT_STRING_BLOCK
        # + 3 *U3 (invalid handle) + 2 *U5 (no XDATA)
        total = resolved_count + unresolved_count
        assert total == 16

    def test_handle_resolution_preserves_regular_blocks(self) -> None:
        """Test that regular (non-anonymous) blocks are still extracted correctly."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        # REGULAR_BLOCK should still be counted normally
        assert "REGULAR_BLOCK" in result["block_counts"]
        assert result["block_counts"]["REGULAR_BLOCK"] == 2

    def test_handle_resolved_not_in_extraction_issues(self) -> None:
        """Test that successfully resolved blocks don't appear in extraction_issues."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        extraction_issues = result["extraction_issues"]
        issue_block_names = {issue["block_name"] for issue in extraction_issues}

        # *U1, *U2, *U4 were resolved, should not be in issues
        assert "*U1" not in issue_block_names
        assert "*U2" not in issue_block_names
        assert "*U4" not in issue_block_names

    def test_anonymous_block_names_not_in_block_counts(self) -> None:
        """Test that anonymous block names (*U*) don't appear in block_counts."""
        result = extract_blocks("app/tests/assets/dynamic_block_handle_test.dxf")

        # No *U blocks should be in block_counts
        for block_name in result["block_counts"].keys():
            assert not block_name.startswith("*U"), (
                f"Found *U block in counts: {block_name}"
            )


class TestOrphanedHandleResolution:
    """Test suite for orphaned handle detection and accurate reporting."""

    def test_orphaned_handle_reported_accurately(self) -> None:
        """Test that orphaned handles report accurate detail message with handle value."""
        result = extract_blocks("app/tests/assets/orphaned_handle_test.dxf")

        extraction_issues = result["extraction_issues"]

        # Find issues for *U999 (orphaned handle B0DE5)
        u999_issues = [
            issue for issue in extraction_issues if issue["block_name"] == "*U999"
        ]
        assert len(u999_issues) >= 1

        # All *U999 issues should mention the orphaned handle, NOT "No XDATA found"
        for issue in u999_issues:
            assert "B0DE5" in issue["details"], (
                f"Expected handle B0DE5 in details: {issue['details']}"
            )
            assert "orphaned" in issue["details"].lower(), (
                f"Expected 'orphaned' in details: {issue['details']}"
            )
            assert "No XDATA found" not in issue["details"], (
                f"Should not say 'No XDATA found': {issue['details']}"
            )

    def test_orphaned_handle_different_from_no_xdata(self) -> None:
        """Test that orphaned handles have different messages than blocks with no XDATA."""
        result = extract_blocks("app/tests/assets/orphaned_handle_test.dxf")

        extraction_issues = result["extraction_issues"]

        # Find issues for *U999 (orphaned handle) and *U777 (no XDATA)
        u999_issues = [
            issue for issue in extraction_issues if issue["block_name"] == "*U999"
        ]
        u777_issues = [
            issue for issue in extraction_issues if issue["block_name"] == "*U777"
        ]

        assert len(u999_issues) >= 1
        assert len(u777_issues) >= 1

        # *U999 should mention orphaned handle
        assert any(
            "Handle" in issue["details"] and "orphaned" in issue["details"].lower()
            for issue in u999_issues
        )

        # *U777 should mention no XDATA (different message)
        assert any(
            "No XDATA found" in issue["details"]
            or "No AcDbBlockRepBTag" in issue["details"]
            for issue in u777_issues
        )

    def test_orphaned_handle_in_extraction_issues(self) -> None:
        """Test that blocks with orphaned handles appear in extraction_issues."""
        result = extract_blocks("app/tests/assets/orphaned_handle_test.dxf")

        extraction_issues = result["extraction_issues"]
        issue_block_names = {issue["block_name"] for issue in extraction_issues}

        # Both orphaned handle blocks should be in issues
        assert "*U999" in issue_block_names  # orphaned handle B0DE5
        assert "*U888" in issue_block_names  # orphaned handle DEADBEEF

    def test_orphaned_handle_not_in_block_counts(self) -> None:
        """Test that blocks with orphaned handles don't appear in block_counts."""
        result = extract_blocks("app/tests/assets/orphaned_handle_test.dxf")

        # Orphaned blocks should NOT be in block_counts
        assert "*U999" not in result["block_counts"]
        assert "*U888" not in result["block_counts"]
        assert "*U777" not in result["block_counts"]

    def test_orphaned_handle_with_different_handles(self) -> None:
        """Test that different orphaned handles report their specific handle values."""
        result = extract_blocks("app/tests/assets/orphaned_handle_test.dxf")

        extraction_issues = result["extraction_issues"]

        # Find issues for *U888 (orphaned handle DEADBEEF)
        u888_issues = [
            issue for issue in extraction_issues if issue["block_name"] == "*U888"
        ]
        assert len(u888_issues) >= 1

        # Should mention the specific handle DEADBEEF
        for issue in u888_issues:
            assert "DEADBEEF" in issue["details"], (
                f"Expected handle DEADBEEF in details: {issue['details']}"
            )

    def test_valid_blocks_still_resolve_correctly(self) -> None:
        """Test that valid blocks still resolve correctly alongside orphaned ones."""
        result = extract_blocks("app/tests/assets/orphaned_handle_test.dxf")

        # VALID_ORIGINAL should appear from resolved *U1 blocks
        assert "VALID_ORIGINAL" in result["block_counts"]
        assert result["block_counts"]["VALID_ORIGINAL"] == 2

        # REGULAR_BLOCK should still be counted normally
        assert "REGULAR_BLOCK" in result["block_counts"]
        assert result["block_counts"]["REGULAR_BLOCK"] == 2

    def test_orphaned_handle_counted_by_layer(self) -> None:
        """Test that orphaned blocks are tracked per layer in extraction_issues."""
        result = extract_blocks("app/tests/assets/orphaned_handle_test.dxf")

        extraction_issues = result["extraction_issues"]
        u999_issues = [
            issue for issue in extraction_issues if issue["block_name"] == "*U999"
        ]

        # Should have separate entries for each layer
        layers_with_issues = {issue["layer_name"] for issue in u999_issues}
        assert "LAYER_A" in layers_with_issues
        assert "LAYER_B" in layers_with_issues

        # Verify counts per layer
        layer_a_issue = next(
            (i for i in u999_issues if i["layer_name"] == "LAYER_A"), None
        )
        layer_b_issue = next(
            (i for i in u999_issues if i["layer_name"] == "LAYER_B"), None
        )

        assert layer_a_issue is not None
        assert layer_b_issue is not None
        # *U999 has 2 insertions on LAYER_A, 1 on LAYER_B
        assert layer_a_issue["insertion_count"] == 2
        assert layer_b_issue["insertion_count"] == 1

    def test_total_insertions_conservation_with_orphaned(self) -> None:
        """Test that total block insertions are conserved with orphaned handles."""
        result = extract_blocks("app/tests/assets/orphaned_handle_test.dxf")

        # Count all tracked insertions
        resolved_count = sum(result["block_counts"].values())

        # Count unresolved insertions
        unresolved_count = sum(
            issue["insertion_count"] for issue in result["extraction_issues"]
        )

        # Total should equal:
        # 2 REGULAR + 2 VALID_ORIGINAL (from *U1) + 3 *U999 + 2 *U888 + 3 *U777 = 12
        total = resolved_count + unresolved_count
        assert total == 12

    def test_resolve_function_returns_tuple(self) -> None:
        """Test that _resolve_dynamic_block_name returns a tuple with details."""
        import ezdxf

        # Create a simple doc to test with
        doc = ezdxf.new("R2010")

        # Create a block without XDATA
        block = doc.blocks.new(name="TEST_BLOCK")
        block_record = block.block_record

        # Call the function
        result = _resolve_dynamic_block_name(block_record, doc, "TEST_BLOCK")

        # Should return a tuple
        assert isinstance(result, tuple)
        assert len(result) == 2

        # First element is resolved name (None for no XDATA)
        assert result[0] is None

        # Second element is details string
        assert isinstance(result[1], str)
        assert "No XDATA found" in result[1] or "No AcDbBlockRepBTag" in result[1]

    def test_resolve_function_with_orphaned_handle(self) -> None:
        """Test that _resolve_dynamic_block_name reports orphaned handle accurately."""
        import ezdxf

        # Create a doc with orphaned handle scenario
        doc = ezdxf.new("R2010")
        if "AcDbBlockRepBTag" not in doc.appids:
            doc.appids.new("AcDbBlockRepBTag")

        # Create an anonymous block with XDATA pointing to non-existent handle
        anon_block = doc.blocks.new(name="*U999")
        block_record = anon_block.block_record
        block_record.set_xdata("AcDbBlockRepBTag", [(1005, "NONEXISTENT")])

        # Call the function
        result = _resolve_dynamic_block_name(block_record, doc, "*U999")

        # Should return tuple with None and orphaned handle message
        assert result[0] is None
        assert "NONEXISTENT" in result[1]
        assert "orphaned" in result[1].lower()

    def test_resolve_function_with_valid_handle(self) -> None:
        """Test that _resolve_dynamic_block_name resolves valid handles correctly."""
        import ezdxf

        # Create a doc with valid handle scenario
        doc = ezdxf.new("R2010")
        if "AcDbBlockRepBTag" not in doc.appids:
            doc.appids.new("AcDbBlockRepBTag")

        # Create the original block
        original_block = doc.blocks.new(name="ORIGINAL_BLOCK")
        original_handle = original_block.block_record.dxf.handle

        # Create an anonymous block with XDATA pointing to valid handle
        anon_block = doc.blocks.new(name="*U1")
        block_record = anon_block.block_record
        block_record.set_xdata("AcDbBlockRepBTag", [(1005, original_handle)])

        # Call the function
        result = _resolve_dynamic_block_name(block_record, doc, "*U1")

        # Should return tuple with resolved name and success message
        assert result[0] == "ORIGINAL_BLOCK"
        assert "Resolved" in result[1]
        assert original_handle in result[1]
